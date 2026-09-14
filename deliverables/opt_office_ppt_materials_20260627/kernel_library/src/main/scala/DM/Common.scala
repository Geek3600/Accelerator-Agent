package DM

import QuantCommon.{FpBackend, XilinxUramCompatMem}
import chisel3._
import chisel3.util._

class R1W1Mem(val depth: Int, val width: Int) extends Module{
  val addrw = log2Up(depth)
  val io = IO(new  Bundle() {
    val wen = Input(Bool())
    val waddr = Input(UInt(addrw.W))
    val wdata = Input(UInt(width.W))
    val ren = Input(Bool())
    val raddr = Input(UInt(addrw.W))
    val rdata = Output(UInt(width.W))
  })
  if (FpBackend.useVivadoIp && depth == 10944 && width == 512) {
    val mem = Module(new XilinxUramCompatMem(depth, width))
    mem.io.write_en := io.wen
    mem.io.write_addr := io.waddr
    mem.io.write_data := io.wdata
    mem.io.read_en := io.ren
    mem.io.read_addr := io.raddr
    io.rdata := mem.io.read_data
  } else {
    val mem = SyncReadMem(depth, UInt(width.W))
    io.rdata := mem.read(io.raddr, io.ren)
    when(io.wen ) {
      mem.write(io.waddr, io.wdata)
    }
  }
  // printf(p"[DM.R1W1Mem] wen = ${io.wen}, waddr = ${io.waddr}, ren = ${io.ren}, raddr = ${io.raddr}\n")
}

// 流水线寄存器，用于在数据通路上插入延迟
class PipReg(val depth: Int, val width: Int) extends Module {
  val io = IO(new Bundle() {
    val in = Input(UInt(width.W))
    val out = Output(UInt(width.W))
  })
  if (depth > 0) {
    io.out := ShiftRegister(io.in, depth) // 将输入延迟depth个周期后输出
  } else {
    io.out := io.in
  }
}

// 乘法器
class Multiplier(val width: Int) extends Module {
  val io = IO(new Bundle() {
    val in0 = Input(UInt(width.W))
    val in1 = Input(UInt(width.W))
    val out = Output(UInt((width * 2).W))
  })
  // 2级流水线
  io.out := RegNext(RegNext(io.in0) * RegNext(io.in1))
}

// 加法树
class AddTree(val num: Int, val width: Int) extends Module {
  val io = IO(new Bundle() {
    val ins = Input(Vec(num, UInt(width.W)))
    val out = Output(UInt(width.W))
  })

  def recFNAddTree(vals: Seq[UInt]): UInt = {
    if (vals.length == 1) vals.head
    else {
      val next = vals.grouped(2).map {
        case Seq(a, b) => RegNext(a + b)
        case Seq(a) => RegNext(a)
      }.toSeq
      recFNAddTree(next)
    }
  }

  io.out := recFNAddTree(io.ins)
}
