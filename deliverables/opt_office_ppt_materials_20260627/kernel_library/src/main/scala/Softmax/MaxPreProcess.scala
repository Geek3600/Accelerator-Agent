package Softmax

import Param._
import chisel3._
import chisel3.util._

class MaxPreProcess(val V: Int, val DW: Int = 8, val FW: Int = 8) extends Module {
  val io = IO(new Bundle {
    val in  = Input(Vec(V, SInt((DW).W)))
    val out = Output(Vec(V, SInt((DW).W)))
    val maxScalar = Output(SInt((DW).W))
  })
    val intWidth = DW.U // 整数部分位宽
    val fracWidth = FW.U   // 小数部分位宽

    val maxVal = io.in.reduceTree((a, b) => Mux(a > b, a, b))
    io.out.zip(io.in).foreach { case (outElem, inElem) =>
        outElem := inElem - maxVal
    }
    io.maxScalar := maxVal
    // printf(p"[MaxPreProcess] maxVal = ${io.maxScalar}\n")
}