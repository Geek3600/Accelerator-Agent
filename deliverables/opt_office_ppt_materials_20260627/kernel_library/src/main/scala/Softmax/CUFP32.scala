package Softmax

import QuantCommon.Precision._
import chisel3._

class CUFP32 extends Module {
  import FP32Param._

  val io = IO(new Bundle() {
    val data_in = Input(UInt(MEM_WIDTH.W))
    val data_in_valid = Input(Bool())

    val data_in_w = Input(UInt(WMEM_WIDTH.W))
    val data_in_w_valid = Input(Bool())

    val data_out = Output(UInt(MEM_WIDTH.W))
    val data_out_valid = Output(Bool())
  })

  val softmax = Module(new SoftmaxFP32)
  val inVec = io.data_in.asTypeOf(Vec(V, UInt(FP32_WIDTH.W)))
  val maskVec = io.data_in_w.asTypeOf(Vec(V, Bool()))

  softmax.io.in := Mux(io.data_in_valid, inVec, VecInit(Seq.fill(V)(0.U(FP32_WIDTH.W))))
  softmax.io.in_mask := Mux(io.data_in_w_valid, maskVec, VecInit(Seq.fill(V)(false.B)))

  io.data_out := softmax.io.out.asUInt
  io.data_out_valid := io.data_in_valid
}
