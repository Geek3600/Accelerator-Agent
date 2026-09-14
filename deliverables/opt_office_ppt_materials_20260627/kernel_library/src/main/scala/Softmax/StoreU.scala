package Softmax

import Param._
import chisel3._
import chisel3.util._

class StoreUnit extends Module {
  val io = IO (new Bundle() {
    val cfg_seqlen = Input(UInt(log2Up(SEQ_LEN).W))
    val cfg_prefill = Input(Bool())
    val cfg_valid = Input(Bool())

    val data_in = Input(UInt(MEM_WIDTH.W))
    val data_in_valid = Input(Bool())

    val data_out = Output(UInt(MEM_WIDTH.W))
    val data_out_addr = Output(UInt(log2Up(MEM_DEPTH).W))
    val data_out_valid = Output(Bool())
    val data_out_last = Output(Bool())
  })

  val seqlen = Mux(io.cfg_valid, io.cfg_seqlen, SEQ_LEN.U)
  val is_prefill = Mux(io.cfg_valid, io.cfg_prefill, false.B)

  // decode阶段，最大为32
  val decode_batchsize_cnt = Wire(UInt(log2Up(BATCHSIZE).W))
  val decode_batchsize_last = decode_batchsize_cnt === (BATCHSIZE - 1).U

  // prefill阶段，最大为26
  val prefill_batchsize_cnt = Wire(UInt(log2Up(SEQ_LEN).W))
  val prefill_batchsize_last = prefill_batchsize_cnt === seqlen

  // 一层循环
  //for vector in 0..26:
  prefill_batchsize_cnt := RegEnable(
    Mux(
      prefill_batchsize_last,
      0.U,
      prefill_batchsize_cnt + 1.U
    ),
    0.U,
    io.data_in_valid && is_prefill
  )

  // 一层循环
  //for vector in 0..31:
  decode_batchsize_cnt := RegEnable(
    Mux(
      decode_batchsize_last,
      0.U,
      decode_batchsize_cnt + 1.U
    ),
    0.U,
    io.data_in_valid && !is_prefill
  )

  val out_addr = Mux(is_prefill, prefill_batchsize_cnt, decode_batchsize_cnt)
  val out_valid = io.data_in_valid
  val out_last = io.data_in_valid && Mux(is_prefill, prefill_batchsize_last, decode_batchsize_last)

  io.data_out := RegNext(io.data_in, 0.U(MEM_WIDTH.W))
  io.data_out_valid := RegNext(out_valid, false.B)
  io.data_out_addr := RegNext(out_addr, 0.U(log2Up(MEM_DEPTH).W))
  io.data_out_last := RegNext(out_last, false.B)
//   printf(p"[StoreUnit] data_out_valid = ${io.data_out_valid}, decode_batchsize_cnt = $decode_batchsize_cnt, out_addr = $out_addr, data_out = ${Binary(io.data_out)}\n \n")
}

object StoreUGen extends App {
  emitVerilog(new StoreUnit, Array("--target-dir", "generated"))
}
