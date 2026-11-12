package spatialaccagent.templates

import chisel3._
import chisel3.util._

final case class DenseFFNParams(
  hiddenSize: Int,
  intermediateSize: Int,
  lanes: Int = 12,
  elemBits: Int = 16,
  outputBits: Int = 32,
  batchSize: Int = 16,
  maxSeqLen: Int = 16,
  activation: String = "relu",
  upWeightRole: String = "weight_mlp_up",
  upBiasRole: String = "weight_mlp_up_bias",
  downWeightRole: String = "weight_mlp_down",
  downBiasRole: String = "weight_mlp_down_bias",
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
  if (integerMode) require(elemBits == 8 && outputBits == 8 && (if (weightBits == 0) 4 else weightBits) == 4 && accBits == 32, "integer DenseFFN requires W4A8/INT32")
  else require(elemBits == 16 || elemBits == 32, "DenseFFN elements must use an IEEE boundary type")
  val up = LinearParams(
    hiddenSize,
    intermediateSize,
    inLanes = lanes,
    outLanes = lanes,
    elemBits = elemBits,
    weightBits = if (integerMode) (if (weightBits == 0) 4 else weightBits) else elemBits,
    integerMode = integerMode,
    accBits = accBits,
    outputBits = elemBits,
    batchSize = batchSize,
    maxSeqLen = maxSeqLen,
    hasBias = true,
    fusedActivation = "none",
    weightRole = upWeightRole,
    biasRole = upBiasRole,
    computeArrayRows = computeArrayRows,
    computeArrayCols = computeArrayCols,
    cacheTileWords = cacheTileWords,
    cacheTileCount = cacheTileCount,
    refillDataWidthBits = refillDataWidthBits,
    crossTokenReuseTokens = crossTokenReuseTokens
  )
  val down = LinearParams(
    intermediateSize,
    hiddenSize,
    inLanes = lanes,
    outLanes = lanes,
    elemBits = elemBits,
    weightBits = if (integerMode) (if (weightBits == 0) 4 else weightBits) else elemBits,
    integerMode = integerMode,
    accBits = accBits,
    outputBits = outputBits,
    batchSize = batchSize,
    maxSeqLen = maxSeqLen,
    hasBias = true,
    weightRole = downWeightRole,
    biasRole = downBiasRole,
    computeArrayRows = computeArrayRows,
    computeArrayCols = computeArrayCols,
    cacheTileWords = cacheTileWords,
    cacheTileCount = cacheTileCount,
    refillDataWidthBits = refillDataWidthBits,
    crossTokenReuseTokens = crossTokenReuseTokens
  )
}

class DenseFFN(p: DenseFFNParams) extends Module {
  val io = IO(new Bundle {
    val start = Input(Bool())
    val cfg = Input(new StageConfig(log2Ceil(p.maxSeqLen + 1 max 2)))
    val cfgValid = Input(Bool())
    val upWeight = Flipped(Decoupled(new WeightWrite(p.up.weightTileBits, p.up.weightAddrBits)))
    val upBias = Flipped(Decoupled(new WeightWrite(p.up.biasBeatBits, log2Ceil(p.up.outBeats max 2))))
    val downWeight = Flipped(Decoupled(new WeightWrite(p.down.weightTileBits, p.down.weightAddrBits)))
    val downBias = Flipped(Decoupled(new WeightWrite(p.down.biasBeatBits, log2Ceil(p.down.outBeats max 2))))
    val upChannelScale = Input(Vec(p.up.outDim, UInt(32.W)))
    val upChannelScaleShift = Input(Vec(p.up.outDim, SInt(8.W)))
    val upActivationScale = Input(UInt(32.W))
    val upActivationShift = Input(SInt(8.W))
    val upOutputScale = Input(UInt(32.W))
    val upOutputShift = Input(SInt(8.W))
    val downChannelScale = Input(Vec(p.down.outDim, UInt(32.W)))
    val downChannelScaleShift = Input(Vec(p.down.outDim, SInt(8.W)))
    val downActivationScale = Input(UInt(32.W))
    val downActivationShift = Input(SInt(8.W))
    val downOutputScale = Input(UInt(32.W))
    val downOutputShift = Input(SInt(8.W))
    val upTile = new WeightTileServiceIO(p.up.refillDataWidthBits)
    val downTile = new WeightTileServiceIO(p.down.refillDataWidthBits)
    val in = Flipped(Decoupled(new StreamBeat(StreamSpec(p.up.inputBeatBits, p.up.inputAddrBits))))
    val out = Decoupled(new StreamBeat(StreamSpec(p.down.outputBeatBits, p.down.outputAddrBits)))
  })

  val up = Module(new Linear(p.up))
  val act = Module(new Activation(ActivationParams(
    p.intermediateSize,
    lanes = p.lanes,
    elemBits = p.elemBits,
    batchSize = p.batchSize,
    maxSeqLen = p.maxSeqLen,
    kind = p.activation,
    outputBits = p.elemBits,
    integerMode = p.integerMode
  )))
  val down = Module(new Linear(p.down))
  val q = Module(new PhysicalStreamFifo(new StreamBeat(StreamSpec(p.up.outputBeatBits, p.up.outputAddrBits)), 2))

  up.io.start := io.start
  up.io.cfg := io.cfg
  up.io.cfgValid := io.cfgValid
  up.io.weight <> io.upWeight
  up.io.bias <> io.upBias
  up.io.tile <> io.upTile
  // Linear interprets these scale fields as unsigned Q31 in integer mode.
  // 0x80000000 is exact unity; the IEEE FP32 encoding of 1.0 is not.
  up.io.scale.outScale := (if (p.integerMode) io.upOutputScale else PhysicalMath.fp32One)
  up.io.scale.biasScale := (if (p.integerMode) "h80000000".U(32.W) else PhysicalMath.fp32One)
  up.io.scale.channelScale := io.upChannelScale
  up.io.scale.channelShift := io.upChannelScaleShift
  up.io.scale.activationScale := io.upActivationScale
  up.io.scale.activationShift := io.upActivationShift
  up.io.scale.outputShift := io.upOutputShift
  up.io.scale.biasShift := 0.S
  up.io.in <> io.in
  act.io.cfg := io.cfg
  act.io.in <> up.io.out
  act.io.out <> q.io.enq

  down.io.start := io.start
  down.io.cfg := io.cfg
  down.io.cfgValid := io.cfgValid
  down.io.weight <> io.downWeight
  down.io.bias <> io.downBias
  down.io.tile <> io.downTile
  down.io.scale.outScale := (if (p.integerMode) io.downOutputScale else PhysicalMath.fp32One)
  down.io.scale.biasScale := (if (p.integerMode) "h80000000".U(32.W) else PhysicalMath.fp32One)
  down.io.scale.channelScale := io.downChannelScale
  down.io.scale.channelShift := io.downChannelScaleShift
  down.io.scale.activationScale := io.downActivationScale
  down.io.scale.activationShift := io.downActivationShift
  down.io.scale.outputShift := io.downOutputShift
  down.io.scale.biasShift := 0.S
  down.io.in <> q.io.deq
  down.io.out <> io.out
}

class DenseMLP(p: DenseFFNParams) extends DenseFFN(p)

final case class GatedMLPParams(
  hiddenSize: Int,
  intermediateSize: Int,
  lanes: Int = 12,
  elemBits: Int = 16,
  outputBits: Int = 32,
  batchSize: Int = 16,
  maxSeqLen: Int = 16,
  activation: String = "silu",
  hasBias: Boolean = false,
  gateWeightRole: String = "weight_mlp_gate",
  gateBiasRole: String = "weight_mlp_gate_bias",
  upWeightRole: String = "weight_mlp_up",
  upBiasRole: String = "weight_mlp_up_bias",
  downWeightRole: String = "weight_mlp_down",
  downBiasRole: String = "weight_mlp_down_bias",
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
  if (integerMode) require(elemBits == 8 && outputBits == 8 && (if (weightBits == 0) 4 else weightBits) == 4 && accBits == 32, "integer GatedMLP requires W4A8/INT32")
  else require(elemBits == 16 || elemBits == 32, "GatedMLP elements must use an IEEE boundary type")
  val gate = LinearParams(
    hiddenSize,
    intermediateSize,
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
    weightRole = gateWeightRole,
    biasRole = gateBiasRole,
    computeArrayRows = computeArrayRows,
    computeArrayCols = computeArrayCols,
    cacheTileWords = cacheTileWords,
    cacheTileCount = cacheTileCount,
    refillDataWidthBits = refillDataWidthBits,
    crossTokenReuseTokens = crossTokenReuseTokens
  )
  val up = LinearParams(
    hiddenSize,
    intermediateSize,
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
    weightRole = upWeightRole,
    biasRole = upBiasRole,
    computeArrayRows = computeArrayRows,
    computeArrayCols = computeArrayCols,
    cacheTileWords = cacheTileWords,
    cacheTileCount = cacheTileCount,
    refillDataWidthBits = refillDataWidthBits,
    crossTokenReuseTokens = crossTokenReuseTokens
  )
  val act = ActivationParams(
    intermediateSize,
    lanes = lanes,
    elemBits = elemBits,
    batchSize = batchSize,
    maxSeqLen = maxSeqLen,
    kind = activation,
    outputBits = elemBits,
    integerMode = integerMode
  )
  val mul = ElementwiseMulParams(
    intermediateSize,
    lanes = lanes,
    elemBits = elemBits,
    outputBits = elemBits,
    batchSize = batchSize,
    maxSeqLen = maxSeqLen,
    integerMode = integerMode
  )
  val down = LinearParams(
    intermediateSize,
    hiddenSize,
    inLanes = lanes,
    outLanes = lanes,
    elemBits = elemBits,
    weightBits = if (integerMode) (if (weightBits == 0) 4 else weightBits) else elemBits,
    integerMode = integerMode,
    accBits = accBits,
    outputBits = outputBits,
    batchSize = batchSize,
    maxSeqLen = maxSeqLen,
    hasBias = hasBias,
    weightRole = downWeightRole,
    biasRole = downBiasRole,
    computeArrayRows = computeArrayRows,
    computeArrayCols = computeArrayCols,
    cacheTileWords = cacheTileWords,
    cacheTileCount = cacheTileCount,
    refillDataWidthBits = refillDataWidthBits,
    crossTokenReuseTokens = crossTokenReuseTokens
  )
}

class GatedMLP(p: GatedMLPParams) extends Module {
  val io = IO(new Bundle {
    val start = Input(Bool())
    val cfg = Input(new StageConfig(log2Ceil(p.maxSeqLen + 1 max 2)))
    val cfgValid = Input(Bool())
    val gateWeight = Flipped(Decoupled(new WeightWrite(p.gate.weightTileBits, p.gate.weightAddrBits)))
    val gateBias = Flipped(Decoupled(new WeightWrite(p.gate.biasBeatBits, log2Ceil(p.gate.outBeats max 2))))
    val upWeight = Flipped(Decoupled(new WeightWrite(p.up.weightTileBits, p.up.weightAddrBits)))
    val upBias = Flipped(Decoupled(new WeightWrite(p.up.biasBeatBits, log2Ceil(p.up.outBeats max 2))))
    val downWeight = Flipped(Decoupled(new WeightWrite(p.down.weightTileBits, p.down.weightAddrBits)))
    val downBias = Flipped(Decoupled(new WeightWrite(p.down.biasBeatBits, log2Ceil(p.down.outBeats max 2))))
    val gateChannelScale = Input(Vec(p.gate.outDim, UInt(32.W)))
    val gateChannelScaleShift = Input(Vec(p.gate.outDim, SInt(8.W)))
    val gateActivationScale = Input(UInt(32.W))
    val gateActivationShift = Input(SInt(8.W))
    val gateOutputScale = Input(UInt(32.W))
    val gateOutputShift = Input(SInt(8.W))
    val upChannelScale = Input(Vec(p.up.outDim, UInt(32.W)))
    val upChannelScaleShift = Input(Vec(p.up.outDim, SInt(8.W)))
    val upActivationScale = Input(UInt(32.W))
    val upActivationShift = Input(SInt(8.W))
    val upOutputScale = Input(UInt(32.W))
    val upOutputShift = Input(SInt(8.W))
    val downChannelScale = Input(Vec(p.down.outDim, UInt(32.W)))
    val downChannelScaleShift = Input(Vec(p.down.outDim, SInt(8.W)))
    val downActivationScale = Input(UInt(32.W))
    val downActivationShift = Input(SInt(8.W))
    val downOutputScale = Input(UInt(32.W))
    val downOutputShift = Input(SInt(8.W))
    val gateTile = new WeightTileServiceIO(p.gate.refillDataWidthBits)
    val upTile = new WeightTileServiceIO(p.up.refillDataWidthBits)
    val downTile = new WeightTileServiceIO(p.down.refillDataWidthBits)
    val in = Flipped(Decoupled(new StreamBeat(StreamSpec(p.gate.inputBeatBits, p.gate.inputAddrBits))))
    val out = Decoupled(new StreamBeat(StreamSpec(p.down.outputBeatBits, p.down.outputAddrBits)))
  })

  val gate = Module(new Linear(p.gate))
  val up = Module(new Linear(p.up))
  val act = Module(new Activation(p.act))
  val actQ = Module(new PhysicalStreamFifo(new StreamBeat(StreamSpec(p.mul.inputBeatBits, p.mul.addrBits)), 4))
  val upQ = Module(new PhysicalStreamFifo(new StreamBeat(StreamSpec(p.mul.inputBeatBits, p.mul.addrBits)), 4))
  val mul = Module(new ElementwiseMul(p.mul))
  val down = Module(new Linear(p.down))

  gate.io.start := io.start
  gate.io.cfg := io.cfg
  gate.io.cfgValid := io.cfgValid
  gate.io.weight <> io.gateWeight
  gate.io.bias <> io.gateBias
  gate.io.tile <> io.gateTile
  gate.io.scale.outScale := (if (p.integerMode) io.gateOutputScale else PhysicalMath.fp32One)
  gate.io.scale.biasScale := (if (p.integerMode) "h80000000".U(32.W) else PhysicalMath.fp32One)
  gate.io.scale.channelScale := io.gateChannelScale
  gate.io.scale.channelShift := io.gateChannelScaleShift
  gate.io.scale.activationScale := io.gateActivationScale
  gate.io.scale.activationShift := io.gateActivationShift
  gate.io.scale.outputShift := io.gateOutputShift
  gate.io.scale.biasShift := 0.S

  up.io.start := io.start
  up.io.cfg := io.cfg
  up.io.cfgValid := io.cfgValid
  up.io.weight <> io.upWeight
  up.io.bias <> io.upBias
  up.io.tile <> io.upTile
  up.io.scale.outScale := (if (p.integerMode) io.upOutputScale else PhysicalMath.fp32One)
  up.io.scale.biasScale := (if (p.integerMode) "h80000000".U(32.W) else PhysicalMath.fp32One)
  up.io.scale.channelScale := io.upChannelScale
  up.io.scale.channelShift := io.upChannelScaleShift
  up.io.scale.activationScale := io.upActivationScale
  up.io.scale.activationShift := io.upActivationShift
  up.io.scale.outputShift := io.upOutputShift
  up.io.scale.biasShift := 0.S

  io.in.ready := gate.io.in.ready && up.io.in.ready
  gate.io.in.valid := io.in.valid && up.io.in.ready
  gate.io.in.bits := io.in.bits
  up.io.in.valid := io.in.valid && gate.io.in.ready
  up.io.in.bits := io.in.bits

  act.io.cfg := io.cfg
  act.io.in <> gate.io.out
  act.io.out <> actQ.io.enq

  up.io.out <> upQ.io.enq
  mul.io.cfg := io.cfg
  mul.io.lhs <> actQ.io.deq
  mul.io.rhs <> upQ.io.deq

  down.io.start := io.start
  down.io.cfg := io.cfg
  down.io.cfgValid := io.cfgValid
  down.io.weight <> io.downWeight
  down.io.bias <> io.downBias
  down.io.tile <> io.downTile
  down.io.scale.outScale := (if (p.integerMode) io.downOutputScale else PhysicalMath.fp32One)
  down.io.scale.biasScale := (if (p.integerMode) "h80000000".U(32.W) else PhysicalMath.fp32One)
  down.io.scale.channelScale := io.downChannelScale
  down.io.scale.channelShift := io.downChannelScaleShift
  down.io.scale.activationScale := io.downActivationScale
  down.io.scale.activationShift := io.downActivationShift
  down.io.scale.outputShift := io.downOutputShift
  down.io.scale.biasShift := 0.S
  down.io.in <> mul.io.out
  down.io.out <> io.out
}
