package ReLU

import ReLU.Param._
import chisel3._
import chisel3.util._

// ReLU 激活函数计算单元
class CU extends Module {
  val io = IO(new Bundle() {
    val data_in = Input(UInt(MEM_WIDTH.W))
    val data_in_valid = Input(Bool())

    val data_out = Output(UInt(MEM_WIDTH.W))
    val data_out_valid = Output(Bool())
  })

  // 将输入拆分为 12 个 8-bit 有符号元素
  val in_elems = io.data_in.asTypeOf(Vec(VECNUM, SInt(DATAW.W)))
  val out_elems = Wire(Vec(VECNUM, UInt(DATAW.W)))

  // ReLU: x < 0 -> 0, x >= 0 -> x
  for (i <- 0 until VECNUM) {
    out_elems(i) := Mux(in_elems(i) < 0.S, 0.U, in_elems(i).asUInt)
  }

  // 输出打一拍
  io.data_out := RegNext(out_elems.asUInt)
  io.data_out_valid := RegNext(io.data_in_valid, false.B)
}
