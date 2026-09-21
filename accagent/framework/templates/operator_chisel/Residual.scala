package spatialaccagent.templates

import chisel3._
import chisel3.util._

final case class ResidualParams(
  hiddenSize: Int,
  lanes: Int = 8,
  elemBits: Int = 32,
  batchSize: Int = 16,
  maxSeqLen: Int = 16
) {
  require(hiddenSize % lanes == 0, "hiddenSize must be divisible by lanes")
  require(elemBits == 16 || elemBits == 32, "ResidualAdd elements must be IEEE FP16 or FP32")
  val beats: Int = hiddenSize / lanes
  val beatBits: Int = lanes * elemBits
  val addrBits: Int = log2Ceil(batchSize * beats max 2)
  val streamCapacity: Int = beats + 1
}

class ResidualAdd(p: ResidualParams) extends Module {
  val io = IO(new Bundle {
    val cfg = Input(new StageConfig(log2Ceil(p.maxSeqLen + 1 max 2)))
    val residual = Flipped(Decoupled(new StreamBeat(StreamSpec(p.beatBits, p.addrBits))))
    val computed = Flipped(Decoupled(new StreamBeat(StreamSpec(p.beatBits, p.addrBits))))
    val out = Decoupled(new StreamBeat(StreamSpec(p.beatBits, p.addrBits)))
  })

  val streamSpec = StreamSpec(p.beatBits, p.addrBits)
  val residualQ = Module(new PhysicalStreamFifo(new StreamBeat(streamSpec), p.streamCapacity))
  val computedQ = Module(new PhysicalStreamFifo(new StreamBeat(streamSpec), p.streamCapacity))
  val outputQ = Module(new PhysicalStreamFifo(new StreamBeat(streamSpec), 2))

  io.residual <> residualQ.io.enq
  io.computed <> computedQ.io.enq
  io.out <> outputQ.io.deq

  val a = residualQ.io.deq.bits.data.asTypeOf(Vec(p.lanes, UInt(p.elemBits.W)))
  val b = computedQ.io.deq.bits.data.asTypeOf(Vec(p.lanes, UInt(p.elemBits.W)))
  val adders = Seq.tabulate(p.lanes) { lane =>
    val add = Module(new PhysicalFp32Add)
    add.io.a := PhysicalMath.toFp32(a(lane), p.elemBits)
    add.io.b := PhysicalMath.toFp32(b(lane), p.elemBits)
    add
  }

  val sPair :: sWait :: sEmit :: Nil = Enum(3)
  val state = RegInit(sPair)
  val resultData = Reg(Vec(p.lanes, UInt(p.elemBits.W)))
  val resultMeta = Reg(new StreamBeat(streamSpec))
  val pairValid = residualQ.io.deq.valid && computedQ.io.deq.valid
  val allAddReady = adders.map(_.io.inReady).reduce(_ && _)
  val issue = state === sPair && pairValid && allAddReady
  val allAddValid = VecInit(adders.map(_.io.outValid)).asUInt.andR

  adders.foreach(_.io.inValid := issue)

  residualQ.io.deq.ready := state === sPair && computedQ.io.deq.valid && allAddReady
  computedQ.io.deq.ready := state === sPair && residualQ.io.deq.valid && allAddReady
  outputQ.io.enq.valid := state === sEmit
  outputQ.io.enq.bits := resultMeta
  outputQ.io.enq.bits.data := resultData.asUInt

  when(issue) {
    resultMeta.st := computedQ.io.deq.bits.st
    resultMeta.addr := computedQ.io.deq.bits.addr
    resultMeta.last := computedQ.io.deq.bits.last
    state := sWait
  }

  when(state === sWait && allAddValid) {
    for (lane <- 0 until p.lanes) {
      resultData(lane) := PhysicalMath.fromFp32(adders(lane).io.out, p.elemBits)
    }
    state := sEmit
  }

  when(outputQ.io.enq.fire) {
    state := sPair
  }

  dontTouch(io.cfg)
}
