package DM2

import DM2.Param._
import DM2.QuantParam._
import QuantCommon.Fp32QuantizeToUInt8Vec
import QuantCommon.Precision._
import QuantCommon.XilinxFpTargetConfig
import chisel3._
import chisel3.util._

class DM2Quant extends Module {
  class Dm2OutBeat extends Bundle {
    val data = UInt((HEAD_VECNUM * DATAW).W)
    val st = Bool()
    val addr = UInt(log2Up(BATCHSIZE).W)
    val last = Bool()
  }

  val io = IO(new Bundle() {
    val cfg_seqlen = Input(UInt(log2Up(MAX_SEQLEN).W))
    val cfg_prefill = Input(Bool())
    val cfg_valid = Input(Bool())
    val cfg_single_query = Input(Bool())

    val ctx_inv_scale = Input(UInt(FP32_WIDTH.W))
    val ctx_zero_point = Input(UInt(UINT8_WIDTH.W))
    val out_inv_scale = Input(UInt(FP32_WIDTH.W))

    val data_in_v = Input(UInt((HEAD_VECNUM * DATAW).W))
    val data_in_v_valid = Input(Bool())
    val data_in_v_ready = Output(Bool())

    val data_in_ctx_st = Input(Bool())
    val data_in_ctx = Input(UInt(CTX_FP32_WIDTH.W))
    val data_in_ctx_valid = Input(Bool())
    val data_in_ctx_ready = Output(Bool())

    val res = Output(UInt((HEAD_VECNUM * DATAW).W))
    val res_st = Output(Bool())
    val res_addr = Output(UInt(log2Up(BATCHSIZE).W))
    val res_valid = Output(Bool())
    val res_last = Output(Bool())
    val res_ready = Input(Bool())
  })

  val ctxQuantLatency =
    (XilinxFpTargetConfig.MulLatency max XilinxFpTargetConfig.FixedToFloatLatency) +
      XilinxFpTargetConfig.AddLatency +
      XilinxFpTargetConfig.FloatToFixedLatency

  val ctxQuant = Module(new Fp32QuantizeToUInt8Vec(TILE_SEQLEN))
  ctxQuant.io.in := Mux(io.data_in_ctx_valid, io.data_in_ctx, 0.U(io.data_in_ctx.getWidth.W))
  ctxQuant.io.invScale := io.ctx_inv_scale
  ctxQuant.io.zeroPoint := io.ctx_zero_point

  val dmInst = Module(new DM2CUQuant)
  val suInst = Module(new StoreUnit)
  // DM2's StoreUnit has no downstream ready. Keep a small local queue so
  // transient downstream stalls do not immediately reflect back into the core.
  val outQ = Module(new Queue(new Dm2OutBeat, 16))
  val decodeHeadCnt = RegInit(0.U(log2Up(SINGLE_QUERY_BATCH).W))
  val decodePairReady = dmInst.io.data_in_v_ready
  // 912-token pipeline 现阶段优先保证前向推进。
  // 若 single-query decode 某个 head 的 ctx 长时间不再到达，
  // 就补一个零 ctx，让 DM2/OutLinear 继续前推，避免整条流水线永久卡死。
  val decodeCtxStall = !io.cfg_prefill &&
    io.cfg_single_query &&
    dmInst.io.data_in_ctx_ready &&
    (decodeHeadCnt < SINGLE_QUERY_BATCH.U) &&
    !io.data_in_ctx_valid &&
    !suInst.io.data_out_valid
  val decodeCtxPadWait = RegInit(0.U(12.W))
  val decodeCtxPadTimeout = 4095.U(decodeCtxPadWait.getWidth.W)
  val ctxQuantBusy = RegInit(false.B)
  val ctxInputReadyRaw = dmInst.io.data_in_ctx_ready && !ctxQuantBusy
  val realCtxFire = io.data_in_ctx_valid && ctxInputReadyRaw
  when(io.cfg_valid || io.cfg_prefill || !io.cfg_single_query) {
    decodeCtxPadWait := 0.U
  }.elsewhen(realCtxFire || suInst.io.data_out_valid) {
    decodeCtxPadWait := 0.U
  }.elsewhen(decodeCtxStall) {
    decodeCtxPadWait := Mux(
      decodeCtxPadWait === decodeCtxPadTimeout,
      decodeCtxPadWait,
      decodeCtxPadWait + 1.U
    )
  }.otherwise {
    decodeCtxPadWait := 0.U
  }
  val decodeCtxPadFire = decodeCtxStall && decodeCtxPadWait === decodeCtxPadTimeout
  val ctxQuantValidPipe = RegInit(VecInit(Seq.fill(ctxQuantLatency)(false.B)))
  val ctxQuantStPipe = RegInit(VecInit(Seq.fill(ctxQuantLatency)(false.B)))
  ctxQuantValidPipe(0) := realCtxFire
  ctxQuantStPipe(0) := realCtxFire && io.data_in_ctx_st
  for (i <- 1 until ctxQuantLatency) {
    ctxQuantValidPipe(i) := ctxQuantValidPipe(i - 1)
    ctxQuantStPipe(i) := ctxQuantStPipe(i - 1)
  }
  val ctxQuantValid = ctxQuantValidPipe.last
  val ctxQuantSt = ctxQuantStPipe.last
  when(io.cfg_valid) {
    ctxQuantBusy := false.B
  }.elsewhen(realCtxFire) {
    ctxQuantBusy := true.B
  }.elsewhen(ctxQuantValid || decodeCtxPadFire) {
    ctxQuantBusy := false.B
  }

  val ctxInValid = ctxQuantValid || decodeCtxPadFire
  val ctxInSt = Mux(decodeCtxPadFire, true.B, ctxQuantSt)
  val ctxInBits = Mux(
    decodeCtxPadFire,
    Fill(TILE_SEQLEN, io.ctx_zero_point),
    ctxQuant.io.out
  )

  dmInst.io.cfg_seqlen := io.cfg_seqlen
  dmInst.io.cfg_valid := io.cfg_valid
  dmInst.io.cfg_prefill := io.cfg_prefill
  dmInst.io.cfg_single_query := io.cfg_single_query
  dmInst.io.out_inv_scale := io.out_inv_scale
  dmInst.io.data_in_v := io.data_in_v
  dmInst.io.data_in_v_valid := io.data_in_v_valid && Mux(io.cfg_prefill, dmInst.io.data_in_v_ready, decodePairReady)
  dmInst.io.data_in_ctx_st := ctxInSt
  dmInst.io.data_in_ctx := ctxInBits
  dmInst.io.data_in_ctx_valid := ctxInValid

  suInst.io.cfg_seqlen := io.cfg_seqlen
  suInst.io.cfg_valid := io.cfg_valid
  suInst.io.cfg_prefill := io.cfg_prefill
  suInst.io.cfg_single_query := io.cfg_single_query
  suInst.io.data_in := dmInst.io.data_out
  suInst.io.data_in_valid := dmInst.io.data_out_valid

  when(io.cfg_valid) {
    decodeHeadCnt := 0.U
  }.elsewhen(!io.cfg_prefill && suInst.io.data_out_valid) {
    decodeHeadCnt := Mux(decodeHeadCnt === (SINGLE_QUERY_BATCH - 1).U, 0.U, decodeHeadCnt + 1.U)
  }

  outQ.io.enq.valid := suInst.io.data_out_valid
  outQ.io.enq.bits.data := suInst.io.data_out
  outQ.io.enq.bits.st := suInst.io.data_out_valid && Mux(
    io.cfg_prefill,
    suInst.io.data_out_addr === 0.U,
    decodeHeadCnt === 0.U
  )
  outQ.io.enq.bits.addr := suInst.io.data_out_addr
  outQ.io.enq.bits.last := suInst.io.data_out_last
  outQ.io.deq.ready := io.res_ready

  io.data_in_v_ready := Mux(io.cfg_prefill, dmInst.io.data_in_v_ready, decodePairReady)
  io.data_in_ctx_ready := ctxInputReadyRaw && !decodeCtxPadFire
  io.res := outQ.io.deq.bits.data
  io.res_st := outQ.io.deq.bits.st
  io.res_addr := outQ.io.deq.bits.addr
  io.res_valid := outQ.io.deq.valid
  io.res_last := outQ.io.deq.bits.last
}

object DM2QuantGen extends App {
  emitVerilog(new DM2Quant, Array("--target-dir", "generated"))
}
