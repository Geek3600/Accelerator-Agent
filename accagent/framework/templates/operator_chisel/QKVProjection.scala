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
  maxSeqLen: Int = 16,
  hasBias: Boolean = true,
  weightRole: String = "weight_qkv",
  biasRole: String = "weight_qkv_bias",
  computeArrayRows: Int = 0,
  computeArrayCols: Int = 0,
  cacheTileWords: Int = PhysicalImplementation.resolveCacheTileWords(256),
  cacheTileCount: Int = PhysicalImplementation.resolveCacheTileCount(2),
  refillDataWidthBits: Int = PhysicalImplementation.resolveRefillDataWidthBits(512),
  crossTokenReuseTokens: Int = PhysicalImplementation.resolveCrossTokenReuseTokens(16),
  weightBits: Int = 0,
  integerMode: Boolean = false,
  accBits: Int = 32
) {
  require(hiddenSize > 0, "hiddenSize must be positive")
  require(qHeads > 0 && kvHeads > 0, "attention head counts must be positive")
  require(qHeads % kvHeads == 0, "qHeads must be divisible by kvHeads")
  require(headDim > 0, "headDim must be positive")
  if (integerMode) {
    require(elemBits == 8, "integer QKV projection activations must be signed INT8")
    require((if (weightBits == 0) 4 else weightBits) == 4, "integer QKV projection matrix weights must be signed INT4")
    require(accBits == 32, "integer QKV projection accumulation must be signed INT32")
  } else {
    require(elemBits == 16, "the legacy attention boundary uses IEEE FP16 Q/K/V elements")
  }
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
    weightBits = if (integerMode) (if (weightBits == 0) 4 else weightBits) else elemBits,
    integerMode = integerMode,
    accBits = accBits,
    outputBits = elemBits,
    batchSize = batchSize,
    maxSeqLen = maxSeqLen,
    hasBias = hasBias,
    weightRole = weightRole,
    biasRole = biasRole,
    computeArrayRows = computeArrayRows,
    computeArrayCols = computeArrayCols,
    cacheTileWords = cacheTileWords,
    cacheTileCount = cacheTileCount,
    refillDataWidthBits = refillDataWidthBits,
    crossTokenReuseTokens = crossTokenReuseTokens
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
    val tile = new WeightTileServiceIO(p.linear.refillDataWidthBits)
    val qScale = Input(UInt(32.W))
    val qScaleShift = Input(SInt(8.W))
    val kScale = Input(UInt(32.W))
    val kScaleShift = Input(SInt(8.W))
    val vScale = Input(UInt(32.W))
    val vScaleShift = Input(SInt(8.W))
    // Matrix channel scales and their independent binary exponents are
    // checkpoint-derived operands. They remain separate from activation and
    // output calibration scales throughout the fused integer projection.
    val channelScale = Input(Vec(p.linear.outDim, UInt(32.W)))
    val channelScaleShift = Input(Vec(p.linear.outDim, SInt(8.W)))
    val activationScale = Input(UInt(32.W))
    val activationScaleShift = Input(SInt(8.W))
    val outputScale = Input(UInt(32.W))
    val outputScaleShift = Input(SInt(8.W))
    val in = Flipped(Decoupled(new StreamBeat(StreamSpec(p.linear.inputBeatBits, p.linear.inputAddrBits))))
    val out = Decoupled(new QKVStreamBeat(p))
  })

  val projection = Module(new Linear(p.linear))
  projection.io.start := io.start
  projection.io.cfg := io.cfg
  projection.io.cfgValid := io.cfgValid
  projection.io.weight <> io.weight
  projection.io.bias <> io.bias
  projection.io.tile <> io.tile
  // In the integer hierarchy the fused projection must first produce raw INT8
  // codes. Apply the independent Q/K/V Q31 requantizers after splitting the
  // fused stream, rather than scaling every output channel with qScale.
  projection.io.scale.outScale := (if (p.integerMode) io.outputScale else io.qScale)
  projection.io.scale.biasScale := (if (p.integerMode) "h80000000".U(32.W) else PhysicalMath.fp32One)
  projection.io.scale.channelScale := io.channelScale
  projection.io.scale.channelShift := io.channelScaleShift
  projection.io.scale.activationScale := io.activationScale
  projection.io.scale.activationShift := io.activationScaleShift
  projection.io.scale.outputShift := io.outputScaleShift
  projection.io.scale.biasShift := 0.S
  projection.io.in <> io.in

  // These ports are retained as part of the established template ABI. Linear
  // performs the immutable IEEE computation and therefore needs no quantizer
  // convention selected independently for Q, K, or V.
  dontTouch(io.kScale)
  dontTouch(io.vScale)

  val projectedMemory = Module(
    new PhysicalSimpleDualPortMemory(
      p.linear.outBeats,
      p.linear.outputBeatBits,
      "activation"
    )
  )
  val collectBeat = RegInit(0.U(log2Ceil(p.linear.outBeats max 2).W))
  val emitHead = RegInit(0.U(p.headBits.W))
  val emitBeat = RegInit(0.U(log2Ceil(p.headBeats max 2).W))
  val tokenStart = RegInit(false.B)
  val readField = RegInit(0.U(2.W))
  val readLane = RegInit(0.U(log2Ceil(p.qkvElemsPerBeat max 2).W))
  val qValues = Reg(Vec(p.qkvElemsPerBeat, UInt(p.elemBits.W)))
  val kValues = Reg(Vec(p.qkvElemsPerBeat, UInt(p.elemBits.W)))
  val vValues = Reg(Vec(p.qkvElemsPerBeat, UInt(p.elemBits.W)))
  val sCollect :: sReadIssue :: sReadCapture :: sEmit :: Nil = Enum(4)
  val state = RegInit(sCollect)

  projection.io.out.ready := state === sCollect
  projectedMemory.io.writeEn := projection.io.out.fire
  projectedMemory.io.writeAddr := collectBeat
  projectedMemory.io.writeData := projection.io.out.bits.data
  when(projection.io.out.fire) {
    when(collectBeat === 0.U) {
      tokenStart := projection.io.out.bits.st
    }
    when(projection.io.out.bits.last) {
      collectBeat := 0.U
      emitHead := 0.U
      emitBeat := 0.U
      readField := 0.U
      readLane := 0.U
      state := sReadIssue
    }.otherwise {
      collectBeat := collectBeat + 1.U
    }
  }

  val dimensionBase = emitBeat * p.qkvElemsPerBeat.U
  val mappedKvHead = emitHead / p.kvGroupSize.U
  val dimension = dimensionBase + readLane
  val qElement = emitHead * p.headDim.U + dimension
  val kElement = p.qDim.U + mappedKvHead * p.headDim.U + dimension
  val vElement = (p.qDim + p.kDim).U + mappedKvHead * p.headDim.U + dimension
  val selectedElement = MuxLookup(readField, qElement)(Seq(
    1.U -> kElement,
    2.U -> vElement
  ))
  val selectedBeat = selectedElement / p.lanes.U
  val selectedLane = selectedElement % p.lanes.U

  projectedMemory.io.readEn := state === sReadIssue
  projectedMemory.io.readAddr := selectedBeat

  when(state === sReadIssue) {
    state := sReadCapture
  }

  val readBeatValues = projectedMemory.io.readData.asTypeOf(Vec(p.lanes, UInt(p.elemBits.W)))
  val readValue = readBeatValues(AccMath.boundedIndex(selectedLane, p.lanes))
  when(state === sReadCapture) {
    when(readField === 0.U) {
      val qValue = if (p.integerMode) AccMath.requantizeQ31WithShift(readValue.asSInt, io.qScale, io.qScaleShift, 8) else readValue
      qValues(AccMath.boundedIndex(readLane, p.qkvElemsPerBeat)) := qValue
    }.elsewhen(readField === 1.U) {
      val kValue = if (p.integerMode) AccMath.requantizeQ31WithShift(readValue.asSInt, io.kScale, io.kScaleShift, 8) else readValue
      kValues(AccMath.boundedIndex(readLane, p.qkvElemsPerBeat)) := kValue
    }.otherwise {
      val vValue = if (p.integerMode) AccMath.requantizeQ31WithShift(readValue.asSInt, io.vScale, io.vScaleShift, 8) else readValue
      vValues(AccMath.boundedIndex(readLane, p.qkvElemsPerBeat)) := vValue
    }

    when(readLane === (p.qkvElemsPerBeat - 1).U) {
      readLane := 0.U
      when(readField === 2.U) {
        readField := 0.U
        state := sEmit
      }.otherwise {
        readField := readField + 1.U
        state := sReadIssue
      }
    }.otherwise {
      readLane := readLane + 1.U
      state := sReadIssue
    }
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
        readField := 0.U
        readLane := 0.U
        state := sReadIssue
      }
    }.otherwise {
      emitBeat := emitBeat + 1.U
      readField := 0.U
      readLane := 0.U
      state := sReadIssue
    }
  }
}

class QKVProjector(p: QKVProjectionParams) extends QKVProjection(p)
