package LayerNorm

import LayerNorm.Param._
import chisel3._
import chisel3.util._

// ==============================================================================
// 基础组件定义 (保持原风格)
// ==============================================================================

class PipReg(val depth: Int, val width: Int) extends Module {
  val io = IO(new Bundle() {
    val in = Input(UInt(width.W))
    val out = Output(UInt(width.W))
  })
  // 使用 ShiftRegister 简化代码，逻辑与原本一致
  if (depth > 0) {
    io.out := ShiftRegister(io.in, depth)
  } else {
    io.out := io.in
  }
}

// 无符号乘法器 (用于第一阶段：求平方、求和)
class Multiplier(val width: Int) extends Module {
  val io = IO(new Bundle() {
    val in0 = Input(UInt(width.W))
    val in1 = Input(UInt(width.W))
    val out = Output(UInt((width * 2).W))
  })
  // 2级流水线
  io.out := RegNext(RegNext(io.in0) * RegNext(io.in1))
}

// 有符号乘法器 (新增！用于第二阶段：归一化、Scaling)
// 必须区分有符号和无符号，否则负数计算会出错
class SignedMultiplier(val width: Int) extends Module {
  val io = IO(new Bundle() {
    val in0 = Input(SInt(width.W))
    val in1 = Input(SInt(width.W))
    val out = Output(SInt((width * 2).W))
  })
  io.out := RegNext(RegNext(io.in0) * RegNext(io.in1))
}

class AddTree(val num: Int, val width: Int) extends Module {
  val io = IO(new Bundle() {
    val ins = Input(Vec(num, UInt(width.W)))
    val out = Output(UInt(width.W))
  })

  def recFNAddTree(vals: Seq[UInt]): UInt = {
    if (vals.length == 1) vals.head
    else {
      val next = vals.grouped(2).map {
        case Seq(a, b) => RegNext(a + b)
        case Seq(a) => a
      }.toSeq
      recFNAddTree(next)
    }
  }
  io.out := recFNAddTree(io.ins)
}

class InvSqrtLUT(val width: Int) extends Module {
  val io = IO(new Bundle() {
    val in_var = Input(UInt(width.W))    // 输入方差 (Qx.16)
    val out_inv_std = Output(UInt(8.W))  // 输出 (Q2.6)
  })

  // 【关键修正 1】方差的小数位现在是 16 位 (因为 mean 是 8位, mean^2 就是 16位)
  val P_VAR = 16

  val LUT_SIZE = 256

  // 【关键修正 2】计算移位量
  // 我们希望覆盖 0 ~ 4.0 的方差范围
  // 4.0 在 Qx.16 中 = 4 * 65536 = 262144
  // 262144 >> SHIFT = 256
  // 所以 SHIFT = 10
  val SHIFT_BITS = 10

  val raw_index = (io.in_var >> SHIFT_BITS).asUInt

  // 饱和保护：超过 4.0 的方差都当做 4.0 处理
  val lut_index = Mux(raw_index > (LUT_SIZE - 1).U, (LUT_SIZE - 1).U, raw_index)

  // 生成表内容
  val table = (0 until LUT_SIZE).map { i =>
    // 反推真实值: (i << 10) / 2^16
    val real_var = (i << SHIFT_BITS).toDouble / math.pow(2, P_VAR)

    // 加上 epsilon 防止除以 0 (当输入方差为0时)
    val epsilon = 1e-5
    val real_inv_sqrt = 1.0 / math.sqrt(real_var + epsilon)

    // 输出量化 Q2.6 (x64)
    // 假设 inv_sqrt 最大不会超过 4.0 (即方差不小于 0.0625)
    // 如果方差很小，这个值会饱和到 255
    val out_scale = 64.0
    val hw_val = math.round(real_inv_sqrt * out_scale).toInt
    val saturated = if (hw_val > 255) 255 else if (hw_val < 0) 0 else hw_val
    i.U -> saturated.U(8.W)
  }

  // 输出打一拍，Delay = 1
  io.out_inv_std := RegNext(MuxLookup(lut_index, 255.U)(table))
}

// ==============================================================================
// 主逻辑模块
// ==============================================================================
//先划分一下流水线级
/*inmul	addtree	acc	div	meansave	pow	lut	norm	Gamma	res
2	log2Up(SUBVECTOR)	1	2	1	2	1	2	2	1*/
class LayerNormCU extends Module {
  // 配置参数
//  val MEM_WIDTH = 8*8 // 示例
//  val DATAW = 8
//  val VECTOR = 768
//  val SUBVECTOR = 8 // 假设 8

  val io = IO(new Bundle() {
    val data_in = Input(UInt(MEM_WIDTH.W))
    val data_in_valid = Input(Bool())
    val data_out = Output(UInt(MEM_WIDTH.W))
    val data_out_valid = Output(Bool())

    val w_data = Input(UInt(MEM_WIDTH.W))
    val w_valid = Input(Bool())
  })

  // --------------------------------------------------------------------------
  // 1. 权重加载 (Bias / Scalas)
  // --------------------------------------------------------------------------
  val w_vector_num = VECTOR / SUBVECTOR

  // 使用 Reg 数组存储权重
  val bias_arr = Reg(Vec(w_vector_num, UInt(MEM_WIDTH.W)))
  val scalas_arr = Reg(Vec(w_vector_num, UInt(MEM_WIDTH.W)))

  val w_cnt = Wire(UInt(log2Up(w_vector_num).W))
  // 这里逻辑稍微调整，让计数器更稳健
  val w_cnt_reg = RegInit(0.U(log2Up(w_vector_num).W))
  w_cnt := w_cnt_reg

  val w_last = w_cnt === (w_vector_num - 1).U

  // 0: Bias, 1: Scalas
  val w_sel = RegInit(false.B)

  val w_update = io.w_valid

  w_cnt_reg := Mux(w_update, Mux(w_last, 0.U, w_cnt + 1.U), w_cnt)
  w_sel := Mux(w_update && w_last, ~w_sel, w_sel) // 写完一组切换

  // 写入逻辑 (使用 Mux 选择写入对象，保持你喜欢 Mux 的风格)
  // 注意：Reg 数组写入需要用 when 或者 Mux更新整个数组，这里用 when 比较标准，
  // 但为了贴近你的风格，我们假设这是 Memory 行为
  when(w_update) {
    when(w_sel) { scalas_arr(w_cnt) := io.w_data }
      .otherwise  { bias_arr(w_cnt)   := io.w_data }
  }

  // --------------------------------------------------------------------------
  // 2. 第一阶段：统计量计算 (Mean & Var)
  // --------------------------------------------------------------------------

  // [Step 1] 输入对齐与平方
  val delay_inmul = 2
  val indata_pipreg = Module(new PipReg(delay_inmul, MEM_WIDTH))
  indata_pipreg.io.in := io.data_in

  val mullist_sq = List.fill(SUBVECTOR)(Module(new Multiplier(DATAW))) // Input is 8 bit

  // 将输入切分成向量
  val data_in_vec = io.data_in.asTypeOf(Vec(SUBVECTOR, UInt(DATAW.W)))

  for(i <- 0 until SUBVECTOR){
    mullist_sq(i).io.in0 := data_in_vec(i)
    mullist_sq(i).io.in1 := data_in_vec(i)
  }

  // [Step 2] 加法树归约
  val addtree_sum = Module(new AddTree(SUBVECTOR, DATAW * 2)) // Sum x (实际不需要 *2 但为了对齐宽一点没事)
  val addtree_sq  = Module(new AddTree(SUBVECTOR, DATAW * 4)) // Sum x^2

  val indata_dly_vec = indata_pipreg.io.out.asTypeOf(Vec(SUBVECTOR, UInt(DATAW.W)))

  for(i <- 0 until SUBVECTOR){
    addtree_sum.io.ins(i) := indata_dly_vec(i)
    addtree_sq.io.ins(i)  := mullist_sq(i).io.out
  }

  val delay_addtree = log2Up(SUBVECTOR) // 加法树延迟

  // [Step 3] 累加器
  val indatavalid_pipreg = Module(new PipReg(delay_inmul + delay_addtree, 1))
  indatavalid_pipreg.io.in := io.data_in_valid
  val acc_en = indatavalid_pipreg.io.out.asBool

  val vector_cnt = RegInit(0.U(log2Up(w_vector_num).W))
  val vector_last = vector_cnt === (w_vector_num - 1).U
  val vector_first = vector_cnt === 0.U

  vector_cnt := Mux(acc_en, Mux(vector_last, 0.U, vector_cnt + 1.U), vector_cnt)

  val sum_val = RegInit(0.U((DATAW * 2).W)) //16位
  val sum_sq  = RegInit(0.U((DATAW * 4).W)) //32位

  val tree_sum_out = addtree_sum.io.out
  val tree_sq_out  = addtree_sq.io.out

  // 累加逻辑
  when(acc_en) {
    sum_val := Mux(vector_first, tree_sum_out, sum_val + tree_sum_out)
    sum_sq  := Mux(vector_first, tree_sq_out,  sum_sq  + tree_sq_out)
  }
  val delay_acc = 1

  // [Step 4] 均值计算 (乘 1/N)
  val M = 24 //被除数放大的2^M次方
  val P = 8 //保留的小数位
  val K = (math.pow(2, M) / VECTOR).toInt
  val K_W = M // 系数位宽

  val mean_val_mul = Module(new Multiplier(sum_val.getWidth)) // 确保位宽够
  val mean_sq_mul  = Module(new Multiplier(sum_sq.getWidth))

  mean_val_mul.io.in0 := sum_val
  mean_val_mul.io.in1 := K.U
  mean_sq_mul.io.in0  := sum_sq
  mean_sq_mul.io.in1  := K.U

  val delay_div = 2 // 累加1 + 乘法2
  val mean_valid_pipreg = Module(new PipReg(delay_acc + delay_div, 1))
  mean_valid_pipreg.io.in := acc_en && vector_last

  // 移位得到均值
  val mean_val = RegEnable(mean_val_mul.io.out >> (M - P), mean_valid_pipreg.io.out.asBool)
  val mean_sq_res = RegEnable(mean_sq_mul.io.out >> (M - P), mean_valid_pipreg.io.out.asBool)
  val delay_meansave = 1

  // [Step 5] 方差计算
  val mean_pow2_mul = Module(new Multiplier(mean_val.getWidth))
  mean_pow2_mul.io.in0 := mean_val
  mean_pow2_mul.io.in1 := mean_val
  val mean_pow2 = mean_pow2_mul.io.out // Qx.16
  val delay_pow = 2

//  val delay_for_square = 2
  val mean_sq_dly_pipe = Module(new PipReg(delay_pow, mean_sq_res.getWidth))
  mean_sq_dly_pipe.io.in := mean_sq_res

  // 对齐：mean_sq 是 Qx.8, mean_pow2 是 Qx.16 -> 左移 8 位
  val mean_sq_aligned = mean_sq_dly_pipe.io.out << P

  val var_val = Wire(UInt(mean_sq_aligned.getWidth.W))
  var_val := Mux(mean_sq_aligned.asUInt >= mean_pow2, mean_sq_aligned - mean_pow2, 0.U)

  // [Step 6] 查找表 InvSqrt
  val InvSqrtLUT_inst = Module(new InvSqrtLUT(var_val.getWidth))
  InvSqrtLUT_inst.io.in_var := var_val
  val inv_sqrt = InvSqrtLUT_inst.io.out_inv_std
  val delay_inv_sqrt = 1 // 查找表寄存了一拍

  // --------------------------------------------------------------------------
  // 3. 数据缓存 (Cache)
  // --------------------------------------------------------------------------

  // 计算写入地址
  val buffer_wr_ptr_pipe = Module(new PipReg(delay_acc + delay_div, log2Up(w_vector_num)))
  buffer_wr_ptr_pipe.io.in := vector_cnt  // 使用原始计数器，经过延迟对齐数据

  val datain_cache = Reg(Vec(w_vector_num, UInt(MEM_WIDTH.W)))
  val indata_pipreg1 = Module(new PipReg(delay_addtree + delay_acc + delay_div, MEM_WIDTH))
  indata_pipreg1.io.in := indata_pipreg.io.out
  val datainupdate_pipreg = Module(new PipReg(delay_acc + delay_div, 1))
  datainupdate_pipreg.io.in := acc_en
  // 写入缓存
  when(datainupdate_pipreg.io.out.asBool) {
    datain_cache(buffer_wr_ptr_pipe.io.out) := indata_pipreg1.io.out
  }

  // --------------------------------------------------------------------------
  // 4. 第二阶段：归一化流水线 (Normalization)
  // --------------------------------------------------------------------------

  // [控制状态机]
  val normstart_pipreg = Module(new PipReg(delay_acc + delay_div , 1))
  normstart_pipreg.io.in := vector_last // 均值准备好后，再等方差算完
  val norm_start = normstart_pipreg.io.out.asBool

  val norm_idle :: norm_busy :: Nil = Enum(2)
  val norm_state = RegInit(norm_idle)
  val vectnorm_cnt = RegInit(0.U(log2Up(w_vector_num).W))

  val norm_done = (vectnorm_cnt === (w_vector_num - 1).U) && (norm_state === norm_busy)

  norm_state := Mux(norm_state === norm_idle,
    Mux(norm_start, norm_busy, norm_idle),
    Mux(norm_done && !norm_start, norm_idle, norm_busy))

  vectnorm_cnt := Mux(norm_state === norm_busy,
    Mux(norm_done, 0.U, vectnorm_cnt + 1.U),
    0.U)

  // [Stage 1] 读缓存 & 减均值
  val cache_read_data =  RegNext(datain_cache(vectnorm_cnt)) // T=0 (Address)
  val cache_read_vec  = cache_read_data.asTypeOf(Vec(SUBVECTOR, UInt(DATAW.W))) // T=1 (Data)

//  // 锁存均值和方差，防止变动
//  val stable_mean  = RegEnable(mean_val, norm_start)
//  val stable_inv  = RegEnable(inv_sqrt, norm_start)
  val stable_mean = RegNext(mean_val)
//  val stable_inv = RegNext(inv_sqrt)
//  val mean
  val diff_list = Wire(Vec(SUBVECTOR, SInt((DATAW + P + 1).W))) // 必须是 SInt

  for(i <- 0 until SUBVECTOR) {
    // 关键：转为有符号数进行减法
    val x_sint = Cat(0.U(1.W), cache_read_vec(i)).asSInt
    val x_align = (x_sint << P).asSInt
    val mean_sint = Cat(0.U(1.W), stable_mean).asSInt

    // T=2 Diff result
    val diff_pipreg = Module(new PipReg(delay_pow + delay_inv_sqrt - 1,DATAW + P + 1))
    diff_pipreg.io.in := (x_align - mean_sint).asUInt
    diff_list(i) := diff_pipreg.io.out.asSInt
//    diff_list(i) := RegNext(x_align - mean_sint)
  }

  // [Stage 2] 乘 InvSqrt
  val P2 = 6 // InvSqrt 小数位
  val mul1_width = diff_list(0).getWidth
  val mullist_norm = List.fill(SUBVECTOR)(Module(new SignedMultiplier(mul1_width))) // 使用有符号乘法器

  val norm_res_vec = Wire(Vec(SUBVECTOR, SInt(mul1_width.W)))

  for(i <- 0 until SUBVECTOR) {
    mullist_norm(i).io.in0 := diff_list(i)
    mullist_norm(i).io.in1 := inv_sqrt.zext // UInt -> SInt
    // 输出 T=4. 右移 P2，保留 P 位小数
    norm_res_vec(i) := mullist_norm(i).io.out >> P2
  }
  val delay_norm = 2

  // [Stage 3] 乘 Gamma (Scalas)
  // 权重同步：需要 T=4 时刻的 scalas。
  // vectnorm_cnt 是 T=0。所以需要延迟 4 拍读取。
//  val delay_norm = 4
  val scalas_ptr_pipe = Module(new PipReg(delay_pow+ delay_inv_sqrt + delay_norm - 1, log2Up(w_vector_num)))
  scalas_ptr_pipe.io.in := vectnorm_cnt

  val current_scalas = RegNext(scalas_arr(scalas_ptr_pipe.io.out)).asTypeOf(Vec(SUBVECTOR, UInt(DATAW.W)))

  val mullist_scale = List.fill(SUBVECTOR)(Module(new SignedMultiplier(mul1_width)))
  val scaled_vec = Wire(Vec(SUBVECTOR, SInt(mul1_width.W)))

  for(i <- 0 until SUBVECTOR) {
    mullist_scale(i).io.in0 := norm_res_vec(i)
    mullist_scale(i).io.in1 := Cat(0.U(1.W), current_scalas(i)).asSInt
    // 输出 T=6
    scaled_vec(i) := mullist_scale(i).io.out
  }

  // [Stage 4] 加 Bias
  // Bias 需要在 T=6 到达
  val delay_gamma = 2
  val bias_ptr_pipe = Module(new PipReg(delay_gamma, log2Up(w_vector_num)))
  bias_ptr_pipe.io.in := scalas_ptr_pipe.io.out

  val current_bias = RegNext(bias_arr(bias_ptr_pipe.io.out)).asTypeOf(Vec(SUBVECTOR, UInt(DATAW.W)))

  val final_res = Wire(Vec(SUBVECTOR, UInt(DATAW.W)))

  for(i <- 0 until SUBVECTOR) {
    val scale_val = scaled_vec(i) // Qx.8
    val bias_val = Cat(0.U(1.W), current_bias(i)).asSInt
    val bias_align = (bias_val << P).asSInt

    // T=7 (RegNext for Add)
    val add_res = scale_val + bias_align

    // 移位回整数 + 饱和
    val res_int = (add_res >> P).asSInt
    final_res(i) := Mux(res_int < 0.S, 0.U,
      Mux(res_int > 255.S, 255.U, res_int.asUInt))
  }

  io.data_out := RegNext(final_res.asUInt)
  val delay_res = 1

  // Valid 信号： NormBusy(T=0) -> T=7
  val valid_pipe = Module(new PipReg(delay_pow + delay_inv_sqrt + delay_norm +delay_norm + delay_res, 1))
  valid_pipe.io.in := (norm_state === norm_busy)
  io.data_out_valid := valid_pipe.io.out.asBool
}

object LayerNormCUGen extends App {
  emitVerilog(new LayerNormCU, Array("--target-dir", "generated"))
}

