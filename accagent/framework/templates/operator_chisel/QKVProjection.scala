package spatialaccagent.templates

import chisel3._
import chisel3.util._

final case class QKVProjectionParams(
  hiddenSize: Int,
  qHeads: Int,
  kvHeads: Int,
  headDim: Int,
  lanes: Int = 8,
  elemBits: Int = 16,
  qkvElemsPerBeat: Int = 8,
  batchSize: Int = 16,
  maxSeqLen: Int = 16
) {
  require(hiddenSize > 0, "hiddenSize must be positive")
  require(qHeads > 0 && kvHeads > 0, "attention head counts must be positive")
  require(qHeads % kvHeads == 0, "qHeads must be divisible by kvHeads")
  require(headDim > 0, "headDim must be positive")
  require(hiddenSize == qHeads * headDim, "Qwen2 attention input size must equal qHeads * headDim")
  require(elemBits == 16, "the immutable attention boundary uses IEEE FP16 Q/K/V elements")
  require(qkvElemsPerBeat > 0, "qkvElemsPerBeat must be positive")
  require(headDim % qkvElemsPerBeat == 0, "headDim must be divisible by qkvElemsPerBeat")

  val qDim: Int = qHeads * headDim
  val kDim: Int = kvHeads * headDim
  val vDim: Int = kvHeads * headDim
  val outDim: Int = qDim + kDim + vDim
  val linear: LinearParams = LinearParams(
    hiddenSize,
    outDim,
    inLanes = lanes,
    outLanes = lanes,
    elemBits = elemBits,
    accBits = 32,
    outputBits = elemBits,
    batchSize = batchSize,
    maxSeqLen = maxSeqLen,
    hasBias = true
  )
  val headBeats: Int = headDim / qkvElemsPerBeat
  val qkvBeatBits: Int = 3 * qkvElemsPerBeat * elemBits
  val headBits: Int = log2Ceil(qHeads max 2)
  val addrBits: Int = log2Ceil(batchSize * headBeats max 2)
  val kvGroupSize: Int = qHeads / kvHeads
}

class QKVStreamBeat(p: QKVProjectionParams) extends Bundle {
  val data = UInt(p.qkvBeatBits.W)
  val st = Bool()
  val head = UInt(p.headBits.W)
  val addr = UInt(p.addrBits.W)
  val last = Bool()
}

class QKVProjection(p: QKVProjectionParams) extends Module {
  val io = IO(new Bundle {
    val start = Input(Bool())
    val cfg = Input(new StageConfig(log2Ceil(p.maxSeqLen + 1 max 2)))
    val cfgValid = Input(Bool())
    val weight = Flipped(Decoupled(new WeightWrite(p.linear.weightTileBits, p.linear.weightAddrBits)))
    val bias = Flipped(Decoupled(new WeightWrite(p.linear.biasBeatBits, log2Ceil(p.linear.outBeats max 2))))
    val qScale = Input(UInt(32.W))
    val kScale = Input(UInt(32.W))
    val vScale = Input(UInt(32.W))
    val in = Flipped(Decoupled(new StreamBeat(StreamSpec(p.linear.inputBeatBits, p.linear.inputAddrBits))))
    val out = Decoupled(new QKVStreamBeat(p))
  })

  val projection = Module(new Linear(p.linear))
  projection.io.start := io.start
  projection.io.cfg := io.cfg
  projection.io.cfgValid := io.cfgValid
  projection.io.weight <> io.weight
  projection.io.bias <> io.bias
  projection.io.scale.outScale := io.qScale
  projection.io.scale.biasScale := IeeeMath.fp32One
  projection.io.in <> io.in

  // These ports are retained as part of the established template ABI. Linear
  // performs the immutable IEEE computation and therefore needs no quantizer
  // convention selected independently for Q, K, or V.
  dontTouch(io.kScale)
  dontTouch(io.vScale)

  val projectedBeats = Reg(Vec(p.linear.outBeats, UInt(p.linear.outputBeatBits.W)))
  val collectBeat = RegInit(0.U(log2Ceil(p.linear.outBeats max 2).W))
  val emitHead = RegInit(0.U(p.headBits.W))
  val emitBeat = RegInit(0.U(log2Ceil(p.headBeats max 2).W))
  val tokenStart = RegInit(false.B)
  val sCollect :: sEmit :: Nil = Enum(2)
  val state = RegInit(sCollect)

  projection.io.out.ready := state === sCollect
  when(projection.io.out.fire) {
    projectedBeats(collectBeat) := projection.io.out.bits.data
    when(collectBeat === 0.U) {
      tokenStart := projection.io.out.bits.st
    }
    when(projection.io.out.bits.last) {
      collectBeat := 0.U
      emitHead := 0.U
      emitBeat := 0.U
      state := sEmit
    }.otherwise {
      collectBeat := collectBeat + 1.U
    }
  }

  val projected = Wire(Vec(p.outDim, UInt(p.elemBits.W)))
  for (beat <- 0 until p.linear.outBeats) {
    val laneValues = projectedBeats(beat).asTypeOf(Vec(p.lanes, UInt(p.elemBits.W)))
    for (lane <- 0 until p.lanes) {
      projected(beat * p.lanes + lane) := laneValues(lane)
    }
  }

  val dimensionBase = emitBeat * p.qkvElemsPerBeat.U
  val mappedKvHead = emitHead / p.kvGroupSize.U
  val qValues = Wire(Vec(p.qkvElemsPerBeat, UInt(p.elemBits.W)))
  val kValues = Wire(Vec(p.qkvElemsPerBeat, UInt(p.elemBits.W)))
  val vValues = Wire(Vec(p.qkvElemsPerBeat, UInt(p.elemBits.W)))

  for (lane <- 0 until p.qkvElemsPerBeat) {
    val dimension = dimensionBase + lane.U
    qValues(lane) := projected(emitHead * p.headDim.U + dimension)
    kValues(lane) := projected(p.qDim.U + mappedKvHead * p.headDim.U + dimension)
    vValues(lane) := projected((p.qDim + p.kDim).U + mappedKvHead * p.headDim.U + dimension)
  }

  io.out.valid := state === sEmit
  io.out.bits.data := Cat(vValues.reverse ++ kValues.reverse ++ qValues.reverse)
  io.out.bits.st := tokenStart && emitHead === 0.U && emitBeat === 0.U
  io.out.bits.head := emitHead
  io.out.bits.addr := emitBeat
  io.out.bits.last := emitHead === (p.qHeads - 1).U && emitBeat === (p.headBeats - 1).U

  when(io.out.fire) {
    when(emitBeat === (p.headBeats - 1).U) {
      emitBeat := 0.U
      when(emitHead === (p.qHeads - 1).U) {
        emitHead := 0.U
        state := sCollect
      }.otherwise {
        emitHead := emitHead + 1.U
      }
    }.otherwise {
      emitBeat := emitBeat + 1.U
    }
  }
}

class QKVProjector(p: QKVProjectionParams) extends QKVProjection(p)
