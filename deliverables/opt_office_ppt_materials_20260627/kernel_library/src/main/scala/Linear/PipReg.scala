package Linear

import Linear.Param.DATAW
import chisel3._
import chisel3.util._


class PipReg (val depth: Int, val width: Int) extends  Module{
  val io = IO(new Bundle() {
    val in = Input(UInt(width.W))
    val out = Output(UInt(width.W))
  })
  val pipData = Wire(Vec(depth + 1,UInt(width.W)))
  for (i <- 0 until depth){
    pipData(i+1):= RegNext(pipData(i), 0.U)

  }
  pipData(0) := io.in
  io.out := pipData(depth)
}


