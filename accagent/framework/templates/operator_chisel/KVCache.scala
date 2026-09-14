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

  val dataMem = Reg(Vec(p.depth, UInt(p.beatBits.W)))
  val stMem = RegInit(VecInit(Seq.fill(p.depth)(false.B)))
  val lastMem = RegInit(VecInit(Seq.fill(p.depth)(false.B)))
  val readData = Reg(UInt(p.beatBits.W))
  val readAddrReg = Reg(UInt(p.addrBits.W))
  val readSt = RegInit(false.B)
  val readLast = RegInit(false.B)
  val readValid = RegInit(false.B)

  io.write.ready := true.B
  when(io.write.fire) {
    dataMem(io.write.bits.addr) := io.write.bits.data
    stMem(io.write.bits.addr) := io.write.bits.st
    lastMem(io.write.bits.addr) := io.write.bits.last
  }

  io.readAddr.ready := !readValid || io.read.ready
  when(io.readAddr.fire) {
    readData := dataMem(io.readAddr.bits)
    readAddrReg := io.readAddr.bits
    readSt := stMem(io.readAddr.bits)
    readLast := lastMem(io.readAddr.bits)
    readValid := true.B
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
