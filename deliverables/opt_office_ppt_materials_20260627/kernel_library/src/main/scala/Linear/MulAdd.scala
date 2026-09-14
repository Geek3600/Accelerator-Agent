package Linear

import Linear.Param.DATAW
import chisel3._
import chisel3.util._

class Multiplier extends Module{
  val io = IO (new Bundle() {
    val in0 = Input(UInt(DATAW.W))
    val in1 = Input(UInt(DATAW.W))

    val out = Output(UInt(DATAW.W))
  })
  io.out := RegNext(io.in0 * io.in1)

}

class AddTree (val num : Int )extends Module{
  val io = IO(new Bundle() {
    val ins = Input(Vec(num,UInt(DATAW.W)))
    val out = Output(UInt(DATAW.W))
  })


  def recFNAddTree(vals: Seq[UInt]): UInt = {
    if (vals.length == 1) vals.head
    else {
      val next = vals.grouped(2).map {
        case Seq(a, b) =>
          RegNext(a+b)
        case Seq(a) => RegNext(a) 
      }.toSeq
      recFNAddTree(next)
    }
  }
  io.out := recFNAddTree(io.ins)

}


