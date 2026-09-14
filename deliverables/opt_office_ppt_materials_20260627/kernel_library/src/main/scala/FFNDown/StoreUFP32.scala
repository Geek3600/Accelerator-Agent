package FFNDown

import FFNDown.Param._
import QuantCommon.Precision._
import chisel3._
import chisel3.util._

class StoreUnitFP32 extends Module {
  val io = IO(new Bundle() {
    val data_in = Input(UInt(FP32_PACK_WIDTH.W))
    val data_in_valid = Input(Bool())

    val data_out = Output(UInt(FP32_PACK_WIDTH.W))
    val data_out_addr = Output(UInt(log2Up(MEM_DEPTH).W))
    val data_out_valid = Output(Bool())
    val data_out_last = Output(Bool())
    val data_out_st = Output(Bool())

    val cfg_prefill = Input(Bool())
    val cfg_seqlen = Input(UInt(log2Up(MAX_SEQLEN).W))
    val cfg_valid = Input(Bool())
  })

  val is_prefill = RegEnable(io.cfg_prefill, false.B, io.cfg_valid)
  val seqlen = RegEnable(io.cfg_seqlen, 0.U, io.cfg_valid)
  val actual_batchsize = Mux(is_prefill, seqlen, (BATCHSIZE - 1).U)

  val vector_valid_num = COL_W / ROW
  val vector_total_num = COLBLOCK * (COL / ROW)
  val subvector_num = COL / ROW

  val batchsize_cnt = Wire(UInt(log2Up(BATCHSIZE).W))
  val subvector_cnt = Wire(UInt(log2Up(subvector_num + 1).W))
  val block_cnt = Wire(UInt(log2Up(COLBLOCK + 1).W))

  val batchsize_last = batchsize_cnt === actual_batchsize
  batchsize_cnt := RegEnable(Mux(batchsize_last, 0.U, batchsize_cnt + 1.U), 0.U, io.data_in_valid)

  val subvector_last = subvector_cnt === (subvector_num - 1).U
  subvector_cnt := RegEnable(Mux(subvector_last, 0.U, subvector_cnt + 1.U), 0.U, io.data_in_valid && batchsize_last)

  val block_last = block_cnt === (COLBLOCK - 1).U
  block_cnt := RegEnable(Mux(block_last, 0.U, block_cnt + 1.U), 0.U, io.data_in_valid && batchsize_last && subvector_last)

  val vector_idx = block_cnt * subvector_num.U + subvector_cnt
  val out_addr = batchsize_cnt * vector_valid_num.U + vector_idx
  val out_valid = io.data_in_valid && (vector_idx < vector_valid_num.U)
  val out_last = out_valid && batchsize_last && (vector_idx === (vector_valid_num - 1).U)
  val out_st = out_valid && batchsize_cnt === 0.U && block_cnt === 0.U && subvector_cnt === 0.U

  io.data_out := RegNext(io.data_in)
  io.data_out_valid := RegNext(out_valid, false.B)
  io.data_out_addr := RegNext(out_addr)
  io.data_out_last := RegNext(out_last, false.B)
  io.data_out_st := RegNext(out_st, false.B)
}
