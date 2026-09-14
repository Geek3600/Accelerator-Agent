
package Softmax

import Param._
import chisel3._
import chisel3.util._

class Sum(val V: Int, val DW: Int = 8, val FW: Int = 8) extends Module {
  val io = IO(new Bundle {
    val in  = Input(Vec(V, SInt((DW + FW).W)))
    val out = Output(SInt((DW + FW).W))
  })
    val intWidth = DW.U // 整数部分位宽
    val fracWidth = FW.U   // 小数部分位宽
    val fixWidth = DW.U + FW.U // 固定点位宽

    val sum = io.in.reduceTree((a, b) => (a + b))
    io.out := sum
    // printf(p"[Sum] sum = ${io.out}\n")
}