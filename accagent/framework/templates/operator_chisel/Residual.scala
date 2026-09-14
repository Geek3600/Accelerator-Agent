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
  val residualQ = Module(new Queue(
    new StreamBeat(streamSpec),
    p.streamCapacity,
    pipe = false,
    flow = false,
    useSyncReadMem = true
  ))
  val computedQ = Module(new Queue(
    new StreamBeat(streamSpec),
    p.streamCapacity,
    pipe = false,
    flow = false,
    useSyncReadMem = true
  ))
  val outputQ = Module(new Queue(
    new StreamBeat(streamSpec),
    2,
    pipe = true,
    flow = false
  ))

  io.residual <> residualQ.io.enq
  io.computed <> computedQ.io.enq
  io.out <> outputQ.io.deq

  val a = residualQ.io.deq.bits.data.asTypeOf(Vec(p.lanes, UInt(p.elemBits.W)))
  val b = computedQ.io.deq.bits.data.asTypeOf(Vec(p.lanes, UInt(p.elemBits.W)))
  val y = Wire(Vec(p.lanes, UInt(p.elemBits.W)))
  for (i <- 0 until p.lanes) {
    val sum = IeeeMath.addFp32(
      IeeeMath.toFp32(a(i), p.elemBits),
      IeeeMath.toFp32(b(i), p.elemBits)
    )
    y(i) := IeeeMath.fromFp32(sum, p.elemBits)
  }

  val joinedBeat = Wire(new StreamBeat(streamSpec))
  joinedBeat.data := y.asUInt
  joinedBeat.st := computedQ.io.deq.bits.st
  joinedBeat.addr := computedQ.io.deq.bits.addr
  joinedBeat.last := computedQ.io.deq.bits.last

  val heldBeat = Reg(new StreamBeat(streamSpec))
  val heldValid = RegInit(false.B)
  val beatInToken = RegInit(0.U(log2Ceil(p.beats max 2).W))
  val seqBits = log2Ceil(p.maxSeqLen + 1 max 2)
  val tokenInSequence = RegInit(0.U(seqBits.W))
  val configuredSeq = Mux(
    io.cfg.seqlen === 0.U || io.cfg.seqlen > p.maxSeqLen.U,
    p.maxSeqLen.U(seqBits.W),
    io.cfg.seqlen
  )
  val pairValid = residualQ.io.deq.valid && computedQ.io.deq.valid
  val tokenFinalBeat = beatInToken === (p.beats - 1).U
  val sequenceFinalBeat = tokenFinalBeat && (tokenInSequence === (configuredSeq - 1.U))

  residualQ.io.deq.ready := false.B
  computedQ.io.deq.ready := false.B
  outputQ.io.enq.valid := false.B
  outputQ.io.enq.bits := joinedBeat

  when(heldValid) {
    outputQ.io.enq.valid := pairValid
    outputQ.io.enq.bits := heldBeat
    when(outputQ.io.enq.fire) {
      heldValid := false.B
    }
  }.otherwise {
    when(pairValid) {
      when(tokenFinalBeat && !sequenceFinalBeat) {
        residualQ.io.deq.ready := computedQ.io.deq.valid
        computedQ.io.deq.ready := residualQ.io.deq.valid
        when(residualQ.io.deq.fire && computedQ.io.deq.fire) {
          heldBeat := joinedBeat
          heldValid := true.B
          beatInToken := 0.U
          tokenInSequence := tokenInSequence + 1.U
        }
      }.otherwise {
        outputQ.io.enq.valid := true.B
        residualQ.io.deq.ready := computedQ.io.deq.valid && outputQ.io.enq.ready
        computedQ.io.deq.ready := residualQ.io.deq.valid && outputQ.io.enq.ready
        when(outputQ.io.enq.fire) {
          when(tokenFinalBeat) {
            beatInToken := 0.U
            when(sequenceFinalBeat) {
              tokenInSequence := 0.U
            }.otherwise {
              tokenInSequence := tokenInSequence + 1.U
            }
          }.otherwise {
            beatInToken := beatInToken + 1.U
          }
        }
      }
    }
  }
}
