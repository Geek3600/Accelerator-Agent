package spatialaccagent.templates

import chisel3._
import chisel3.util._

final case class ElementwiseMulParams(
  hiddenSize: Int,
  lanes: Int = 8,
  elemBits: Int = 16,
  outputBits: Int = 16,
  batchSize: Int = 16,
  maxSeqLen: Int = 16
) {
  require(hiddenSize % lanes == 0, "hiddenSize must be divisible by lanes")
  require(elemBits == 16 || elemBits == 32, "ElementwiseMul inputs must be IEEE FP16 or FP32")
  require(outputBits == 16 || outputBits == 32, "ElementwiseMul output must be IEEE FP16 or FP32")
  val beats: Int = hiddenSize / lanes
  val inputBeatBits: Int = lanes * elemBits
  val outputBeatBits: Int = lanes * outputBits
  val addrBits: Int = log2Ceil(batchSize * beats max 2)
}

class ElementwiseMul(p: ElementwiseMulParams) extends Module {
  val io = IO(new Bundle {
    val cfg = Input(new StageConfig(log2Ceil(p.maxSeqLen + 1 max 2)))
    val lhs = Flipped(Decoupled(new StreamBeat(StreamSpec(p.inputBeatBits, p.addrBits))))
    val rhs = Flipped(Decoupled(new StreamBeat(StreamSpec(p.inputBeatBits, p.addrBits))))
    val out = Decoupled(new StreamBeat(StreamSpec(p.outputBeatBits, p.addrBits)))
  })

  val inputSpec = StreamSpec(p.inputBeatBits, p.addrBits)
  val outputSpec = StreamSpec(p.outputBeatBits, p.addrBits)
  val lhsQ = Module(new PhysicalStreamFifo(new StreamBeat(inputSpec), 4))
  val rhsQ = Module(new PhysicalStreamFifo(new StreamBeat(inputSpec), 4))
  val outputQ = Module(new PhysicalStreamFifo(new StreamBeat(outputSpec), 2))

  io.lhs <> lhsQ.io.enq
  io.rhs <> rhsQ.io.enq
  io.out <> outputQ.io.deq

  val a = lhsQ.io.deq.bits.data.asTypeOf(Vec(p.lanes, UInt(p.elemBits.W)))
  val b = rhsQ.io.deq.bits.data.asTypeOf(Vec(p.lanes, UInt(p.elemBits.W)))
  val multipliers = Seq.tabulate(p.lanes) { lane =>
    val mul = Module(new PhysicalFp32Mul)
    mul.io.a := PhysicalMath.toFp32(a(lane), p.elemBits)
    mul.io.b := PhysicalMath.toFp32(b(lane), p.elemBits)
    mul
  }

  val sPair :: sWait :: sEmit :: Nil = Enum(3)
  val state = RegInit(sPair)
  val resultData = Reg(Vec(p.lanes, UInt(p.outputBits.W)))
  val resultMeta = Reg(new StreamBeat(outputSpec))
  val pairValid = lhsQ.io.deq.valid && rhsQ.io.deq.valid
  val allMulReady = multipliers.map(_.io.inReady).reduce(_ && _)
  val issue = state === sPair && pairValid && allMulReady
  val allMulValid = VecInit(multipliers.map(_.io.outValid)).asUInt.andR

  multipliers.foreach(_.io.inValid := issue)

  lhsQ.io.deq.ready := state === sPair && rhsQ.io.deq.valid && allMulReady
  rhsQ.io.deq.ready := state === sPair && lhsQ.io.deq.valid && allMulReady
  outputQ.io.enq.valid := state === sEmit
  outputQ.io.enq.bits := resultMeta
  outputQ.io.enq.bits.data := resultData.asUInt

  when(issue) {
    resultMeta.st := lhsQ.io.deq.bits.st
    resultMeta.addr := lhsQ.io.deq.bits.addr
    resultMeta.last := lhsQ.io.deq.bits.last
    state := sWait
  }

  when(state === sWait && allMulValid) {
    for (lane <- 0 until p.lanes) {
      resultData(lane) := PhysicalMath.fromFp32(multipliers(lane).io.out, p.outputBits)
    }
    state := sEmit
  }

  when(outputQ.io.enq.fire) {
    state := sPair
  }

  dontTouch(io.cfg)
}
