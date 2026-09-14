package Softmax

import chisel3._
import chisel3.util._

class StoreUnitFP32 extends Module {
  import FP32Param._

  val io = IO(new Bundle() {
    val cfg_seqlen = Input(UInt(log2Up(SEQ_LEN).W))
    val cfg_prefill = Input(Bool())
    val cfg_valid = Input(Bool())
    val cfg_single_query = Input(Bool())

    val data_in = Input(UInt(MEM_WIDTH.W))
    val data_in_valid = Input(Bool())

    val data_out = Output(UInt(MEM_WIDTH.W))
    val data_out_addr = Output(UInt(log2Up(MEM_DEPTH).W))
    val data_out_valid = Output(Bool())
    val data_out_last = Output(Bool())
  })

  val seqlen = RegEnable(io.cfg_seqlen, 0.U, io.cfg_valid)
  val is_prefill = RegEnable(io.cfg_prefill, false.B, io.cfg_valid)
  val is_single_query = RegEnable(io.cfg_single_query, false.B, io.cfg_valid)

  val decodeBatchCnt = Wire(UInt(log2Up(BATCHSIZE).W))
  val decodeBatchLast = decodeBatchCnt === Mux(is_single_query, 0.U(decodeBatchCnt.getWidth.W), (BATCHSIZE - 1).U(decodeBatchCnt.getWidth.W))

  val prefillBatchCnt = Wire(UInt(log2Up(SEQ_LEN).W))
  val prefillBatchLast = prefillBatchCnt === seqlen

  prefillBatchCnt := RegEnable(
    Mux(prefillBatchLast, 0.U, prefillBatchCnt + 1.U),
    0.U,
    io.data_in_valid && is_prefill
  )

  decodeBatchCnt := RegEnable(
    Mux(decodeBatchLast, 0.U, decodeBatchCnt + 1.U),
    0.U,
    io.data_in_valid && !is_prefill
  )

  val outAddr = Mux(is_prefill, prefillBatchCnt, decodeBatchCnt)
  val outValid = io.data_in_valid
  val outLast = io.data_in_valid && Mux(is_prefill, prefillBatchLast, decodeBatchLast)

  io.data_out := RegNext(io.data_in, 0.U(MEM_WIDTH.W))
  io.data_out_valid := RegNext(outValid, false.B)
  io.data_out_addr := RegNext(outAddr, 0.U(log2Up(MEM_DEPTH).W))
  io.data_out_last := RegNext(outLast, false.B)
}
