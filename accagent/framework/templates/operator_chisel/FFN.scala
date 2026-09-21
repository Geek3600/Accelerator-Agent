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
  computeArrayCols: Int = 0
) {
  require(elemBits == 16 || elemBits == 32, "DenseFFN elements must use an IEEE boundary type")
  val up = LinearParams(
    hiddenSize,
    intermediateSize,
    inLanes = lanes,
    outLanes = lanes,
    elemBits = elemBits,
    outputBits = elemBits,
    batchSize = batchSize,
    maxSeqLen = maxSeqLen,
    hasBias = true,
    fusedActivation = "none",
    weightRole = upWeightRole,
    biasRole = upBiasRole,
    computeArrayRows = computeArrayRows,
    computeArrayCols = computeArrayCols
  )
  val down = LinearParams(
    intermediateSize,
    hiddenSize,
    inLanes = lanes,
    outLanes = lanes,
    elemBits = elemBits,
    outputBits = outputBits,
    batchSize = batchSize,
    maxSeqLen = maxSeqLen,
    hasBias = true,
    weightRole = downWeightRole,
    biasRole = downBiasRole,
    computeArrayRows = computeArrayRows,
    computeArrayCols = computeArrayCols
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
    kind = p.activation
  )))
  val down = Module(new Linear(p.down))
  val q = Module(new PhysicalStreamFifo(new StreamBeat(StreamSpec(p.up.outputBeatBits, p.up.outputAddrBits)), 2))

  up.io.start := io.start
  up.io.cfg := io.cfg
  up.io.cfgValid := io.cfgValid
  up.io.weight <> io.upWeight
  up.io.bias <> io.upBias
  up.io.scale.outScale := PhysicalMath.fp32One
  up.io.scale.biasScale := PhysicalMath.fp32One
  up.io.in <> io.in
  act.io.cfg := io.cfg
  act.io.in <> up.io.out
  act.io.out <> q.io.enq

  down.io.start := io.start
  down.io.cfg := io.cfg
  down.io.cfgValid := io.cfgValid
  down.io.weight <> io.downWeight
  down.io.bias <> io.downBias
  down.io.scale.outScale := PhysicalMath.fp32One
  down.io.scale.biasScale := PhysicalMath.fp32One
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
  computeArrayCols: Int = 0
) {
  require(elemBits == 16 || elemBits == 32, "GatedMLP elements must use an IEEE boundary type")
  val gate = LinearParams(
    hiddenSize,
    intermediateSize,
    inLanes = lanes,
    outLanes = lanes,
    elemBits = elemBits,
    outputBits = elemBits,
    batchSize = batchSize,
    maxSeqLen = maxSeqLen,
    hasBias = hasBias,
    weightRole = gateWeightRole,
    biasRole = gateBiasRole,
    computeArrayRows = computeArrayRows,
    computeArrayCols = computeArrayCols
  )
  val up = LinearParams(
    hiddenSize,
    intermediateSize,
    inLanes = lanes,
    outLanes = lanes,
    elemBits = elemBits,
    outputBits = elemBits,
    batchSize = batchSize,
    maxSeqLen = maxSeqLen,
    hasBias = hasBias,
    weightRole = upWeightRole,
    biasRole = upBiasRole,
    computeArrayRows = computeArrayRows,
    computeArrayCols = computeArrayCols
  )
  val act = ActivationParams(
    intermediateSize,
    lanes = lanes,
    elemBits = elemBits,
    batchSize = batchSize,
    maxSeqLen = maxSeqLen,
    kind = activation
  )
  val mul = ElementwiseMulParams(
    intermediateSize,
    lanes = lanes,
    elemBits = elemBits,
    outputBits = elemBits,
    batchSize = batchSize,
    maxSeqLen = maxSeqLen
  )
  val down = LinearParams(
    intermediateSize,
    hiddenSize,
    inLanes = lanes,
    outLanes = lanes,
    elemBits = elemBits,
    outputBits = outputBits,
    batchSize = batchSize,
    maxSeqLen = maxSeqLen,
    hasBias = hasBias,
    weightRole = downWeightRole,
    biasRole = downBiasRole,
    computeArrayRows = computeArrayRows,
    computeArrayCols = computeArrayCols
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
  gate.io.scale.outScale := PhysicalMath.fp32One
  gate.io.scale.biasScale := PhysicalMath.fp32One

  up.io.start := io.start
  up.io.cfg := io.cfg
  up.io.cfgValid := io.cfgValid
  up.io.weight <> io.upWeight
  up.io.bias <> io.upBias
  up.io.scale.outScale := PhysicalMath.fp32One
  up.io.scale.biasScale := PhysicalMath.fp32One

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
  down.io.scale.outScale := PhysicalMath.fp32One
  down.io.scale.biasScale := PhysicalMath.fp32One
  down.io.in <> mul.io.out
  down.io.out <> io.out
}
