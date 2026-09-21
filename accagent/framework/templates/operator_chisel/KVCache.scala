package spatialaccagent.templates

import chisel3._
import chisel3.util._

final case class KVCacheParams(
  kvHeads: Int,
  headDim: Int,
  seqLen: Int,
  elemsPerBeat: Int = 2,
  elemBits: Int = 8,
  batchSize: Int = 16
) {
  require(kvHeads > 0, "kvHeads must be positive")
  require(headDim % elemsPerBeat == 0, "headDim must be divisible by elemsPerBeat")
  val headBeats: Int = headDim / elemsPerBeat
  val depth: Int = batchSize * kvHeads * seqLen * headBeats
  val beatBits: Int = elemsPerBeat * elemBits
  val addrBits: Int = log2Ceil(depth max 2)
}

class KVCache(p: KVCacheParams) extends Module {
  val io = IO(new Bundle {
    val write = Flipped(Decoupled(new StreamBeat(StreamSpec(p.beatBits, p.addrBits))))
    val readAddr = Flipped(Decoupled(UInt(p.addrBits.W)))
    val read = Decoupled(new StreamBeat(StreamSpec(p.beatBits, p.addrBits)))
  })

  val dataMem = Module(new PhysicalSimpleDualPortMemory(p.depth, p.beatBits, "cache"))
  val stMem = Module(new PhysicalSimpleDualPortMemory(p.depth, 1, "cache"))
  val lastMem = Module(new PhysicalSimpleDualPortMemory(p.depth, 1, "cache"))
  val readData = Reg(UInt(p.beatBits.W))
  val readAddrReg = Reg(UInt(p.addrBits.W))
  val readSt = RegInit(false.B)
  val readLast = RegInit(false.B)
  val readValid = RegInit(false.B)
  val readPending = RegInit(false.B)

  io.write.ready := true.B
  dataMem.io.writeEn := io.write.fire
  dataMem.io.writeAddr := io.write.bits.addr
  dataMem.io.writeData := io.write.bits.data
  stMem.io.writeEn := io.write.fire
  stMem.io.writeAddr := io.write.bits.addr
  stMem.io.writeData := io.write.bits.st
  lastMem.io.writeEn := io.write.fire
  lastMem.io.writeAddr := io.write.bits.addr
  lastMem.io.writeData := io.write.bits.last

  dataMem.io.readEn := io.readAddr.fire
  dataMem.io.readAddr := io.readAddr.bits
  stMem.io.readEn := io.readAddr.fire
  stMem.io.readAddr := io.readAddr.bits
  lastMem.io.readEn := io.readAddr.fire
  lastMem.io.readAddr := io.readAddr.bits

  io.readAddr.ready := !readPending && (!readValid || io.read.ready)
  when(io.readAddr.fire) {
    readAddrReg := io.readAddr.bits
    readPending := true.B
  }
  when(readPending) {
    readData := dataMem.io.readData
    readSt := stMem.io.readData(0)
    readLast := lastMem.io.readData(0)
    readValid := true.B
    readPending := false.B
  }
  when(io.read.fire) {
    readValid := false.B
  }

  io.read.valid := readValid
  io.read.bits.data := readData
  io.read.bits.st := readSt
  io.read.bits.addr := readAddrReg
  io.read.bits.last := readLast
}
