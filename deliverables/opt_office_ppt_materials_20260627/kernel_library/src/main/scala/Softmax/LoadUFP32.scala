package Softmax

import chisel3._
import chisel3.util._

class LoadUnitFP32 extends Module {
  import FP32Param._

  val io = IO(new Bundle() {
    val cfg_seqlen = Input(UInt(log2Up(SEQ_LEN).W))
    val cfg_prefill = Input(Bool())
    val cfg_valid = Input(Bool())
    val cfg_single_query = Input(Bool())

    val data_in = Input(UInt(MEM_WIDTH.W))
    val data_in_addr = Output(UInt(log2Up(MEM_DEPTH).W))
    val data_in_last = Output(Bool())
    val data_in_ready = Input(Bool())

    val data_out = Output(UInt(MEM_WIDTH.W))
    val data_out_valid = Output(Bool())

    val data_out_ready = Input(Bool())
    val data_out_start = Output(Bool())
  })

  val seqlen = RegEnable(io.cfg_seqlen, 0.U, io.cfg_valid)
  val is_prefill = RegEnable(io.cfg_prefill, false.B, io.cfg_valid)
  val is_single_query = RegEnable(io.cfg_single_query, false.B, io.cfg_valid)

  val decodeBatchCnt = Wire(UInt(log2Up(BATCHSIZE).W))
  val decodeBatchLast = decodeBatchCnt === Mux(is_single_query, 0.U(decodeBatchCnt.getWidth.W), (BATCHSIZE - 1).U(decodeBatchCnt.getWidth.W))

  val prefillBatchCnt = Wire(UInt(log2Up(SEQ_LEN).W))
  val prefillBatchLast = prefillBatchCnt === (SEQ_LEN - 1).U

  val idle :: busy :: Nil = Enum(2)
  val state = RegInit(idle)
  val isIdle = state === idle
  val isBusy = state === busy
  state := Mux(
    isIdle,
    Mux(io.data_in_ready && io.data_out_ready, busy, idle),
    Mux(decodeBatchLast || prefillBatchLast, idle, busy)
  )

  decodeBatchCnt := RegEnable(
    Mux(decodeBatchLast, 0.U, decodeBatchCnt + 1.U),
    0.U,
    isBusy && !is_prefill
  )

  prefillBatchCnt := RegEnable(
    Mux(prefillBatchLast, 0.U, prefillBatchCnt + 1.U),
    0.U,
    isBusy && is_prefill
  )

  io.data_in_addr := Mux(is_prefill, prefillBatchCnt, decodeBatchCnt)
  io.data_in_last := (is_prefill && prefillBatchLast) || (!is_prefill && decodeBatchLast)

  io.data_out := io.data_in
  io.data_out_valid := RegNext(isBusy, false.B)

  val stateNext = RegNext(state, idle)
  io.data_out_start := isBusy && stateNext === idle
}
