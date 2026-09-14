package DM2

import DM2.Param._
import QuantCommon.{FpBackend, XilinxUramCompatMem}
import chisel3._
import chisel3.util._

class R1W1Mem(val depth: Int, val width: Int) extends Module{
  val addrw = log2Up(depth)
  val io = IO(new  Bundle() {
    val wen = Input(Bool())
    val waddr = Input(UInt(addrw.W))
    val wdata = Input(UInt(width.W))

    val ren = Input(Bool())
    val raddr = Input(UInt(addrw.W))
    val rdata = Output(UInt(width.W))

  })
  if (FpBackend.useVivadoIp && depth == 10944 && width == 512) {
    val mem = Module(new XilinxUramCompatMem(depth, width))
    mem.io.write_en := io.wen
    mem.io.write_addr := io.waddr
    mem.io.write_data := io.wdata
    mem.io.read_en := io.ren
    mem.io.read_addr := io.raddr
    io.rdata := mem.io.read_data
  } else {
    val mem = SyncReadMem(depth, UInt(width.W))
    io.rdata := mem.read(io.raddr, io.ren)
    when(io.wen ) {
      mem.write(io.waddr, io.wdata)
    }
  }
}

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



class Multiplier(val width: Int) extends Module {
  val io = IO(new Bundle() {
    val in0 = Input(UInt(width.W))
    val in1 = Input(UInt(width.W))
    val out = Output(UInt((width * 2).W))
  })
  // 2级流水线
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
        case Seq(a) => RegNext(a)
      }.toSeq
      recFNAddTree(next)
    }
  }
  io.out := recFNAddTree(io.ins)
}



class DM2CU extends Module {
//  val BATCHSIZE = 1
//  val LBANCHNUM = 1
//  val LBATCHSIZE = BATCHSIZE * LBANCHNUM
//  val HEAD_VECNUM = 2
//  val MAX_SEQLEN = 2
//  val MAX_PREFILL = 1
//  val MULNUM = 32 //要求
//  //  val SEND_VECNUM = 26
//  val DATAW = 8
//  //
//  val MEM_DEPTH = 512
  val io =IO(new Bundle() {
    val cfg_seqlen =Input(UInt(log2Up(MAX_SEQLEN).W))
//    val cfg_prelen = Input(UInt(log2Up(MAX_PREFILL).W)) //prefill 长度减去1
    val cfg_prefill = Input(Bool())
    val cfg_valid = Input(Bool())

    val data_in_v = Input(UInt((HEAD_VECNUM * DATAW ).W)) //
    val data_in_v_valid = Input(Bool())

    val data_in_ctx = Input(UInt((MAX_SEQLEN * DATAW ).W))
    val data_in_ctx_valid = Input(Bool())

    val data_out = Output(UInt((HEAD_VECNUM * DATAW ).W))
    val data_out_valid = Output(Bool())

  })
  // 锁存配置信号，直到下一次 cfg_valid
  val prefill = RegEnable(io.cfg_prefill,io.cfg_valid)
  val seqlen = RegEnable(io.cfg_seqlen,io.cfg_valid)

  // prefill模式下,V是从外部读取的
  // decode模式下,V是从VCache中读取的
  // 存储历史V向量,用于decode模式,与DM中的QKcache类似
  val VCache = Module(new R1W1Mem(LBATCHSIZE*MAX_SEQLEN,HEAD_VECNUM*DATAW))
  // 片上寄存器，存储当前计算需要的 26 个 V 向量
  val v_buf = Wire(Vec(MAX_SEQLEN,UInt((HEAD_VECNUM*DATAW).W)))

  // prefill模式下, 用于计数要写入VCache的V向量的数量, 用于生成地址
  val prefill_load_cnt = Wire(UInt(log2Up(MAX_PREFILL).W))
  val prefill_load_last = prefill_load_cnt === seqlen
  prefill_load_cnt := RegEnable(
    Mux(
      prefill_load_last,
      0.U,
      prefill_load_cnt + 1.U
    ),
    0.U,
    prefill && io.data_in_v_valid
  )

  // 区分不同用户的 V 数据
  val lbatch_cnt = Wire(UInt(log2Up(LBATCHSIZE).W))
  val lbatch_last = lbatch_cnt === (LBATCHSIZE - 1).U
  lbatch_cnt := RegEnable(
    Mux(
      lbatch_last,
      0.U,
      lbatch_cnt +1.U
    ),
    0.U,
    //  递增条件：
    // - Prefill： 当一个用户的所有 V 写完 (prefill_load_last)
    // - Decode： 每收到一个新 V
    prefill && io.data_in_v_valid && prefill_load_last || !prefill && io.data_in_v_valid
  )

  VCache.io.wen := io.data_in_v_valid
  VCache.io.waddr := Mux(prefill, 
      lbatch_cnt * MAX_SEQLEN.U + prefill_load_cnt,  // Prefill: 顺序写入
      lbatch_cnt * MAX_SEQLEN.U + seqlen             // Decode: 追加到末尾
  )
  VCache.io.wdata := io.data_in_v

  // 状态机
  // 四个状态：
  // - stc_vcache: 正在接收 V 数据，写入 VCache
  // - stc_getv: 从 VCache 读取历史 V (仅 Decode)
  // - stc_waitctx: 等待 ctx 输入
  // - stc_c: 计算状态 (ctx × V)
  val stc_vcache::stc_getv :: stc_waitctx  :: stc_c ::Nil = Enum(4)
  val state = RegInit(stc_vcache)

  val is_getv = state === stc_getv
  val is_waitctx = state === stc_waitctx
  val is_c= state === stc_c

  // getv计数器
  // 作用: Decode 模式下，从 VCache 读取历史 V 的计数器
  val gev_cnt = Wire(UInt(log2Up(MAX_SEQLEN).W))
  val gev_last = gev_cnt === seqlen
  gev_cnt := RegEnable(
    Mux(
      gev_last,
      0.U,
      gev_cnt +1.U
    ),
    0.U,
    is_getv
  )

  // waitctx 计数器
  // Prefill 模式下，记录已处理的 ctx 数量
  // prefill模式: 有多个ctx需要处理
  // decode模式: 只有一个ctx需要处理
  val waitctx_cnt = Wire(UInt(log2Up(MAX_PREFILL).W))
  val waitctx_last = waitctx_cnt === seqlen
  waitctx_cnt := RegEnable(
    Mux(
      waitctx_last,
      0.U,
      waitctx_cnt + 1.U
    ),
    0.U,
    prefill && io.data_in_ctx_valid
  )

  // 计算状态下，遍历 V 向量的 64 个维度
  val mul_cnt = Wire(UInt(log2Up(HEAD_VECNUM).W))
  val mul_last = mul_cnt === (HEAD_VECNUM - 1).U
  mul_cnt := RegEnable(
    Mux(
      mul_last,
      0.U,
      mul_cnt + 1.U
    ),
    0.U,
    is_c
  )

  // Prefill 模式： stc_vcache → stc_waitctx (当所有 V 收集完时)
  // Decode 模式： stc_vcache → stc_getv (当收到新 V时)
  val stc_vcache_mux = Mux(
    prefill,
    Mux(
      prefill_load_last && io.data_in_v_valid, // prefill:所有max_prefill个V都收集完,都存入了Vcache
      stc_waitctx,
      stc_vcache
    ),
    Mux(
      io.data_in_v_valid, // decode:收到一个新V
      stc_getv,
      stc_vcache
    )
  )

  // stc_getv → stc_waitctx (当所有历史 V 读取完时)
  val stc_getv_mux = Mux(
    gev_last,
    stc_waitctx,
    stc_getv
  )

  // stc_waitctx → stc_c (当收到 ctx 时)
  val stc_waitctx_mux = Mux(
    io.data_in_ctx_valid,
    stc_c,
    stc_waitctx
  )

  // 当 mul_last=1 (64维计算完)：
  // - Decode 或 Prefill 最后一个 ctx： → stc_vcache (回到初始状态)
  // - Prefill 还有 ctx 未处理： → stc_waitctx (等待下一个 ctx)
  val stc_c_mux = Mux(
    mul_last,
    Mux(
      waitctx_cnt === 0.U,
      // Return to the explicit V-cache state after each finished batch.
      // Feeding the transition through stc_vcache_mux can skip the next V-load
      // boundary under decode traffic.
      stc_vcache,
      stc_waitctx_mux
    ),
    stc_c
  )

  state := MuxLookup(
    state,
    state
  )(
    List(
      stc_vcache -> stc_vcache_mux,
      stc_getv -> stc_getv_mux,
      stc_waitctx -> stc_waitctx_mux,
      stc_c -> stc_c_mux
    )
  )

  // Vcache读取
  // 延迟一拍
  val lbatch_cnt_r = RegEnable(lbatch_cnt, prefill && io.data_in_v_valid && prefill_load_last || !prefill && io.data_in_v_valid)
  VCache.io.ren := is_getv
  VCache.io.raddr := gev_cnt + lbatch_cnt_r* MAX_SEQLEN.U

  // v_buf 填充
  // prefill阶段: 是用外部加载v向量, 存入v buf
  // decode阶段: 是从Vcache中读取历史V, 存入v buf
  for(i <- 0 until MAX_SEQLEN){
    val valid_decode = RegNext(is_getv && gev_cnt === i.U)
    val data_decode = VCache.io.rdata

    val valid_prefill = prefill && io.data_in_v_valid && prefill_load_cnt === i.U
    val data_prefill = io.data_in_v

    v_buf(i):= RegEnable(
      Mux(
        prefill,
        data_prefill,
        data_decode
      ),
      valid_prefill || valid_decode
    )
  }

  // v_list 提取
  // 作用： 从 v_buf 中提取第 mul_cnt 维的所有元素,相当于将V矩阵中的第mul_cnt列的元素提取出来,用于与ctx的某一行做点积
  val v_list = (0 until MAX_SEQLEN).map{
    i => MuxLookup(
      mul_cnt,
      0.U
    )(
      (0 until HEAD_VECNUM).map{j =>
        j.U -> v_buf(i)(DATAW*(j+ 1)- 1, DATAW*j)
      }
    )
  }

  // ctx 提取
  // 作用：将ctx拆分成26个8-bit元素
  val ctx = RegEnable(io.data_in_ctx, io.data_in_ctx_valid)
  val ctx_list = (0 until MAX_SEQLEN).map { i => Mux(seqlen >= i.U, ctx((i + 1) * DATAW - 1, i * DATAW), 0.U) }

  // 乘法器阵列
  val mul_list = List.fill(MAX_SEQLEN)(Module(new Multiplier(DATAW)))
  // 加法树
  val addrtree = Module(new AddTree(MAX_SEQLEN,DATAW*2))
  // 点积运算
  for( i <- 0 until MAX_SEQLEN){
    mul_list(i).io.in0 := ctx_list(i)
    mul_list(i).io.in1 := v_list(i)
    addrtree.io.ins(i) := mul_list(i).io.out
  }

  // 结果收集
  // 作用： 将加法树的输出收集到 res 向量
  val delay_mulcnt_to_addtres = 2+log2Up(MAX_SEQLEN)
  val addresvalid_pipreg = Module(new PipReg(delay_mulcnt_to_addtres,1))
  addresvalid_pipreg.io.in := state === stc_c
  val addres_valid = addresvalid_pipreg.io.out.asBool

  val addrescnt_pipreg = Module(new PipReg(delay_mulcnt_to_addtres,log2Up(HEAD_VECNUM)))
  addrescnt_pipreg.io.in := mul_cnt
  val addrescnt = addrescnt_pipreg.io.out

  val res = Wire(Vec(HEAD_VECNUM,UInt(DATAW.W)))
  for( i <- 0 until HEAD_VECNUM){
    res(i) := RegEnable(addrtree.io.out , addres_valid && addrescnt === i.U)
  }
  io.data_out := res.asTypeOf(UInt((DATAW*HEAD_VECNUM).W))
  io.data_out_valid := RegNext(addres_valid && (addrescnt === (HEAD_VECNUM - 1).U) ,false.B)


}

// 主要工作方式
// Prefill 模式
// 1. 将 V 写入 VCache，同时写入 v_buf
// 2. 等待 ctx 输入
// 3. ctx 和 v_buf 中的 V 相乘
// 4. 输出结果
// 5. 等待下一个 ctx (因为 Prefill 有多个 Q，所以有多个 ctx)

// Decode 模式
// 1. 将新的 V 写入 VCache
// 2. 从 VCache 读出该用户的历史所有 V，写入 v_buf
// 3. 等待 ctx 输入
// 4. ctx 和 v_buf 中的 V 相乘
// 5. 输出结果

//  四、完整时序图 (Decode 模式, seqlen=2)

//   周期   state        计数器                    操作
//          状态         mul_cnt  gev_cnt  lbatch
//   ─────────────────────────────────────────────────────────────
//   0      stc_vcache   -        -        0       等待 V 输入
//   1      stc_vcache   -        -        0       收到新 V, 写入 VCache[2]
//   2      stc_getv     -        0        0       读 VCache[0] → v_buf[0]
//   3      stc_getv     -        1        0       读 VCache[1] → v_buf[1]
//   4      stc_getv     -        2        0       读 VCache[2] → v_buf[2]
//   5      stc_waitctx  -        -        0       等待 ctx
//   6      stc_waitctx  -        -        0       收到 ctx!
//   7      stc_c        0        -        0       计算 Output[0]
//   8      stc_c        1        -        0       计算 Output[1]
//   9      stc_c        2        -        0       计算 Output[2]
//   ...
//   70     stc_c        63       -        0       计算 Output[63]
//   71     stc_vcache   -        -        0       回到初始状态
//   ...
//   77     -            -        -        0       输出 Output[0] (延迟7周期)
//   78     -            -        -        0       输出 Output[1]
//   ...
//   140    -            -        -        0       输出 Output[63]
//                                                data_out_valid=1
