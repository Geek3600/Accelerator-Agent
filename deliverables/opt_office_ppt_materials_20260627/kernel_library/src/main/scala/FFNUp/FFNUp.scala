package FFNUp

import FFNUp._
import QuantCommon.{Fp32Add, Fp32Mul, Fp32ToSInt, Int32ToFp32, Int8ToFp32, XilinxFpTargetConfig}
import QuantCommon.Precision._
import chisel3._
import chisel3.util._
import FFNUp.Param._

// FFNUp: 前��网络上投影模块
// 功能: 将 768 维向量映射为 3072 维向量 (H → 4H)
// 输入: 96-bit/cycle (12 elements) from LayerNorm2
// 输出: 96-bit/cycle (12 elements) to FFNDown
//
// 矩阵乘法: X(768) × W(768×3072) = Y(3072)
class FFNUp extends Module {
  val io = IO(new Bundle() {
    val layer_st = Input(Bool())

    // 来自 LayerNorm2 的输入
    val data_in_st = Input(Bool())
    val data_in = Input(UInt(MEM_WIDTH.W))
    val data_addr = Input(UInt(log2Up(MEM_DEPTH).W))
    val data_valid = Input(Bool())
    val data_last = Input(Bool())
    val data_ready = Output(Bool())

    // 权重初始化接口
    val weight_init_mode = Input(Bool())
    val weight_init_data = Input(UInt(WMEM_WIDTH.W))
    val weight_init_addr = Output(UInt(log2Up(WMEM_DEPTH).W))
    val weight_active_bank = Input(Bool())
    val weight_preload_bank = Input(Bool())
    val weight_preload_valid = Input(Bool())
    val weight_preload_addr = Input(UInt(log2Up(WMEM_DEPTH).W))
    val weight_preload_data = Input(UInt(WMEM_WIDTH.W))
    val bias_init_data = Input(UInt(MEM_WIDTH.W))
    val bias_init_valid = Input(Bool())
    val out_inv_scale = Input(UInt(FP32_WIDTH.W))
    val bias_scale = Input(UInt(FP32_WIDTH.W))

    // 配置信号
    val cfg_prefill = Input(Bool())
    val cfg_seqlen = Input(UInt(log2Up(MAX_SEQLEN).W))
    val cfg_valid = Input(Bool())

    // 输出到 FFNDown (ReLU 已融合)
    val data_out = Output(UInt(MEM_WIDTH.W))
    val data_out_st = Output(Bool())
    val data_out_addr = Output(UInt(log2Up(MEM_DEPTH).W))
    val data_out_valid = Output(Bool())
    val data_out_last = Output(Bool())
    val data_out_ready = Input(Bool())
  })

  // ========================================
  // Linear 计算核心
  // ========================================
  val mem_inst = Module(new DataMem(MEM_DEPTH, MEM_WIDTH))
  val lu_inst = Module(new LoadUnit)
  val cu_inst = Module(new CUQuant)
  val su_inst = Module(new StoreUnit)
  val lw_inst = Module(new LoadWeight)
  val bias_mem = Reg(Vec(COL_W / ROW, UInt(MEM_WIDTH.W)))
  val bias_init_cnt = RegInit(0.U(log2Up(COL_W / ROW).W))

  when(io.bias_init_valid) {
    bias_mem(bias_init_cnt) := io.bias_init_data
    bias_init_cnt := Mux(bias_init_cnt === (COL_W / ROW - 1).U, 0.U, bias_init_cnt + 1.U)
  }

  mem_inst.io.w_st := io.data_in_st
  mem_inst.io.w_last := io.data_last
  mem_inst.io.w_data := io.data_in
  mem_inst.io.w_addr := io.data_addr
  mem_inst.io.w_valid := io.data_valid
  mem_inst.io.r_last := lu_inst.io.data_in_last
  mem_inst.io.r_addr := lu_inst.io.data_in_addr

  lu_inst.io.data_in := mem_inst.io.r_data
  lu_inst.io.data_in_ready := mem_inst.io.r_ready
  lu_inst.io.data_out_ready := io.data_out_ready
  lu_inst.io.cfg_prefill := io.cfg_prefill
  lu_inst.io.cfg_seqlen := io.cfg_seqlen
  lu_inst.io.cfg_valid := io.cfg_valid
  lu_inst.io.weight_ready := lw_inst.io.weight_ready

  cu_inst.io.data_in := lu_inst.io.data_out
  cu_inst.io.data_in_valid := lu_inst.io.data_out_valid
  cu_inst.io.w_data := lw_inst.io.data_out
  cu_inst.io.w_data_sel := lw_inst.io.data_out_sel
  cu_inst.io.w_valid := lw_inst.io.data_out_valid
  cu_inst.io.cfg_prefill := io.cfg_prefill
  cu_inst.io.cfg_seqlen := io.cfg_seqlen
  cu_inst.io.cfg_valid := io.cfg_valid

  su_inst.io.data_in := cu_inst.io.data_out
  su_inst.io.data_in_valid := cu_inst.io.data_out_valid
  su_inst.io.cfg_prefill := io.cfg_prefill
  su_inst.io.cfg_seqlen := io.cfg_seqlen
  su_inst.io.cfg_valid := io.cfg_valid

  lw_inst.io.update := cu_inst.io.w_update
  lw_inst.io.st := io.layer_st
  lw_inst.io.init_mode := io.weight_init_mode
  lw_inst.io.init_data := io.weight_init_data
  lw_inst.io.active_bank := io.weight_active_bank
  lw_inst.io.preload_valid := io.weight_preload_valid
  lw_inst.io.preload_bank := io.weight_preload_bank
  lw_inst.io.preload_addr := io.weight_preload_addr
  lw_inst.io.preload_data := io.weight_preload_data

  io.data_ready := mem_inst.io.w_ready
  io.weight_init_addr := lw_inst.io.init_addr

  val epilogueLatency =
    XilinxFpTargetConfig.FixedToFloatLatency +
      XilinxFpTargetConfig.MulLatency +
      XilinxFpTargetConfig.AddLatency +
      XilinxFpTargetConfig.FloatToFixedLatency
  val epilogueFire = su_inst.io.data_out_valid

  val su_vec = su_inst.io.data_out.asTypeOf(Vec(ROW, SInt(INT32_WIDTH.W)))
  val bias_vec = bias_mem(su_inst.io.data_out_addr(log2Up(COL_W / ROW) - 1, 0)).asTypeOf(Vec(ROW, SInt(DATAW.W)))
  val relu_vec = Wire(Vec(ROW, UInt(DATAW.W)))
  for (i <- 0 until ROW) {
    val accToFp = Module(new Int32ToFp32)
    val accMul = Module(new Fp32Mul)
    val biasToFp = Module(new Int8ToFp32)
    val biasMul = Module(new Fp32Mul)
    val add = Module(new Fp32Add)
    val toInt = Module(new Fp32ToSInt(INT32_WIDTH))

    accToFp.io.in := Mux(epilogueFire, su_vec(i), 0.S(INT32_WIDTH.W))
    accMul.io.a := accToFp.io.out
    accMul.io.b := Mux(epilogueFire, io.out_inv_scale, 0.U(FP32_WIDTH.W))
    biasToFp.io.in := Mux(epilogueFire, bias_vec(i), 0.S(DATAW.W))
    biasMul.io.a := biasToFp.io.out
    biasMul.io.b := Mux(epilogueFire, io.bias_scale, 0.U(FP32_WIDTH.W))
    add.io.a := accMul.io.out
    add.io.b := biasMul.io.out
    toInt.io.in := add.io.out

    val sum = toInt.io.out.asSInt
    val maxVal = ((1 << (DATAW - 1)) - 1).S
    val minVal = (-(1 << (DATAW - 1))).S
    val sat = Mux(sum > maxVal, maxVal, Mux(sum < minVal, minVal, sum(DATAW - 1, 0).asSInt))
    relu_vec(i) := Mux(sat < 0.S, 0.U, sat.asUInt)
  }

  val dataOutValidPipe = RegInit(VecInit(Seq.fill(epilogueLatency)(false.B)))
  val dataOutStPipe = Reg(Vec(epilogueLatency, Bool()))
  val dataOutLastPipe = Reg(Vec(epilogueLatency, Bool()))
  val dataOutAddrPipe = Reg(Vec(epilogueLatency, UInt(log2Up(MEM_DEPTH).W)))
  dataOutValidPipe(0) := su_inst.io.data_out_valid
  dataOutStPipe(0) := su_inst.io.data_out_st
  dataOutLastPipe(0) := su_inst.io.data_out_last
  dataOutAddrPipe(0) := su_inst.io.data_out_addr
  for (i <- 1 until epilogueLatency) {
    dataOutValidPipe(i) := dataOutValidPipe(i - 1)
    dataOutStPipe(i) := dataOutStPipe(i - 1)
    dataOutLastPipe(i) := dataOutLastPipe(i - 1)
    dataOutAddrPipe(i) := dataOutAddrPipe(i - 1)
  }

  // ========================================
  // 输出信号
  // ========================================
  io.data_out := relu_vec.asUInt
  io.data_out_valid := dataOutValidPipe.last
  io.data_out_addr := dataOutAddrPipe.last
  io.data_out_st := dataOutStPipe.last
  io.data_out_last := dataOutLastPipe.last
}

object FFNUpGen extends App {
  emitVerilog(new FFNUp, Array("--target-dir", "generated"))
}
