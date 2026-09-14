package LayerNorm

import LayerNorm.Param._
import chisel3._
import chisel3.util._

class StoreUnit extends Module {
  val io = IO (new Bundle() {
    val data_in = Input(UInt(MEM_WIDTH.W))
    val data_in_valid = Input(Bool())

    val data_out = Output(UInt(MEM_WIDTH.W))
    val data_out_addr = Output(UInt(log2Up(MEM_DEPTH).W))
    val data_out_valid = Output(Bool())
    val data_out_last = Output(Bool())
  })

  val vector_num = VECTOR/SUBVECTOR
  val vector_cnt =Wire(UInt( log2Up(vector_num).W))
  val vector_last = vector_cnt === (vector_num - 1).U
  vector_cnt := RegEnable(
    Mux(
      vector_last,
      0.U,
      vector_cnt + 1.U
    ),
    0.U,
    io.data_in_valid
  )


  val batchsize_cnt = Wire(UInt(log2Up(BATCHSIZE).W))

  val batchsize_last =  batchsize_cnt === (BATCHSIZE - 1).U
  batchsize_cnt := RegEnable(
    Mux(
      batchsize_last,
      0.U,
      batchsize_cnt + 1.U
    ),
    0.U,
    io.data_in_valid && vector_last
  )



  val out_addr=  batchsize_cnt*vector_num.U + vector_cnt
  val out_valid = io.data_in_valid
  val out_last = batchsize_last && vector_last

  io.data_out  := RegNext(io.data_in)
  io.data_out_valid := RegNext(out_valid,false.B)
  io.data_out_addr := RegNext(out_addr)
  io.data_out_last := RegNext(out_last,false.B)
}

object StoreUGen extends App {
  emitVerilog(new StoreUnit, Array("--target-dir", "generated"))
}
