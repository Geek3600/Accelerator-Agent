package Softmax

import chisel3._
import chisel3.util._

class Exp2(val V: Int, val DW: Int = 8, val FW: Int = 16) extends Module {
  val io = IO(new Bundle {
    val in  = Input(Vec(V, SInt((DW+FW).W)))
    val out = Output(Vec(V, SInt((DW+FW).W)))
  })
    val intWidth = DW   // 整数部分位宽
    val fracWidth = FW   // 小数部分位宽

    for (i <- 0 until V) {
        val u = io.in(i) >> fracWidth                      // 整数部分
        val v = io.in(i).asUInt & ((1 << fracWidth) - 1).U // 小数部分
        val one_plus_v = (1.U << fracWidth) + v // 1.0 + v
        val isPositive = u > 0.S
        io.out(i) := Mux(isPositive, one_plus_v << u.asUInt, one_plus_v >> (-u).asUInt).asSInt // 用整数部分移位
        // printf(p"[EXP2] i=$i in=${Binary(io.in(i))} u=${Binary(u)} v=${Binary(v)} one_plus_v=${Binary(one_plus_v)} isPositive=${isPositive}\n")
    }
}