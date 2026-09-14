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
  val lhsQ = Module(new Queue(
    new StreamBeat(inputSpec),
    4,
    pipe = true,
    flow = false
  ))
  val rhsQ = Module(new Queue(
    new StreamBeat(inputSpec),
    4,
    pipe = true,
    flow = false
  ))
  val outputQ = Module(new Queue(
    new StreamBeat(outputSpec),
    2,
    pipe = true,
    flow = false
  ))

  io.lhs <> lhsQ.io.enq
  io.rhs <> rhsQ.io.enq
  io.out <> outputQ.io.deq

  val a = lhsQ.io.deq.bits.data.asTypeOf(Vec(p.lanes, UInt(p.elemBits.W)))
  val b = rhsQ.io.deq.bits.data.asTypeOf(Vec(p.lanes, UInt(p.elemBits.W)))
  val y = Wire(Vec(p.lanes, UInt(p.outputBits.W)))
  for (i <- 0 until p.lanes) {
    val product = IeeeMath.mulFp32(
      IeeeMath.toFp32(a(i), p.elemBits),
      IeeeMath.toFp32(b(i), p.elemBits)
    )
    y(i) := IeeeMath.fromFp32(product, p.outputBits)
  }

  val productBeat = Wire(new StreamBeat(outputSpec))
  productBeat.data := y.asUInt
  productBeat.st := lhsQ.io.deq.bits.st
  productBeat.addr := lhsQ.io.deq.bits.addr
  productBeat.last := lhsQ.io.deq.bits.last

  val heldBeat = Reg(new StreamBeat(outputSpec))
  val heldValid = RegInit(false.B)
  val beatInToken = RegInit(0.U(log2Ceil(p.beats max 2).W))
  val tokenIndex = RegInit(0.U(log2Ceil(p.maxSeqLen + 1 max 2).W))
  val pairValid = lhsQ.io.deq.valid && rhsQ.io.deq.valid
  val tokenFinalBeat = beatInToken === (p.beats - 1).U
  val configuredTokenCount = Mux(io.cfg.seqlen === 0.U, 1.U, io.cfg.seqlen)
  val sequenceFinalToken = tokenIndex === (configuredTokenCount - 1.U)

  lhsQ.io.deq.ready := false.B
  rhsQ.io.deq.ready := false.B
  outputQ.io.enq.valid := false.B
  outputQ.io.enq.bits := productBeat

  when(heldValid) {
    outputQ.io.enq.valid := pairValid
    outputQ.io.enq.bits := heldBeat
    when(outputQ.io.enq.fire) {
      heldValid := false.B
    }
  }.otherwise {
    when(pairValid) {
      when(tokenFinalBeat && !sequenceFinalToken) {
        lhsQ.io.deq.ready := rhsQ.io.deq.valid
        rhsQ.io.deq.ready := lhsQ.io.deq.valid
        when(lhsQ.io.deq.fire && rhsQ.io.deq.fire) {
          heldBeat := productBeat
          heldValid := true.B
          beatInToken := 0.U
          tokenIndex := tokenIndex + 1.U
        }
      }.otherwise {
        outputQ.io.enq.valid := true.B
        lhsQ.io.deq.ready := rhsQ.io.deq.valid && outputQ.io.enq.ready
        rhsQ.io.deq.ready := lhsQ.io.deq.valid && outputQ.io.enq.ready
        when(outputQ.io.enq.fire) {
          when(tokenFinalBeat) {
            beatInToken := 0.U
            when(sequenceFinalToken) {
              tokenIndex := 0.U
            }.otherwise {
              tokenIndex := tokenIndex + 1.U
            }
          }.otherwise {
            beatInToken := beatInToken + 1.U
          }
        }
      }
    }
  }
}
