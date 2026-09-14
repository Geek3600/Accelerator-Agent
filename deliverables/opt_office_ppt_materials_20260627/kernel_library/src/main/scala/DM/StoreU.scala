package DM

import DM.Param._
import chisel3._
import chisel3.util._

class StoreUnit extends Module {
  val io = IO(new Bundle() {
    val cfg_seqlen = Input(UInt(log2Up(LOCAL_PREFILL).W))
    val cfg_prefill = Input(Bool())
    val cfg_valid = Input(Bool())


    val data_in = Input(UInt((MAX_SEQLEN*DATAW).W))
    val data_in_valid = Input(Bool())

    val data_out = Output(UInt((MAX_SEQLEN*DATAW).W))
    val data_out_addr = Output(UInt(log2Up(BATCHSIZE).W))
    val data_out_valid = Output(Bool())
    val data_out_last = Output(Bool())
  })

  val seqlen = RegEnable(io.cfg_seqlen,io.cfg_valid)
  val is_prefill = RegEnable(io.cfg_prefill,io.cfg_valid)
  val batch_cnt = Wire(UInt(log2Up(math.max(BATCHSIZE, LOCAL_PREFILL)).W))//prefill的时候是prelen，decode的时候是batchsize
  val batch_last = batch_cnt === Mux(is_prefill,seqlen, (BATCHSIZE - 1).U)
  batch_cnt := RegEnable(
    Mux(
      batch_last,
      0.U,
      batch_cnt +1.U
    ),
    0.U,
    io.data_in_valid
  )

  io.data_out := io.data_in
  io.data_out_addr := batch_cnt
  io.data_out_valid := io.data_in_valid
  io.data_out_last := batch_last && io.data_in_valid
}
