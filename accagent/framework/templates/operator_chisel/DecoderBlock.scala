package spatialaccagent.templates

import chisel3._
import chisel3.util._

final case class DecoderBlockParams(
  hiddenSize: Int = 768,
  numHeads: Int = 12,
  headDim: Int = 64,
  intermediateSize: Int = 3072,
  lanes: Int = 12,
  batchSize: Int = 16,
  maxSeqLen: Int = 16,
  inputBits: Int = 32,
  elemBits: Int = 16,
  outputBits: Int = 32,
  computeArrayRows: Int = 0,
  computeArrayCols: Int = 0,
  mlpActivation: String = "relu",
  qkvHasBias: Boolean = true,
  attentionOutHasBias: Boolean = true
) {
  require(inputBits == outputBits, "DecoderBlock inputBits and outputBits must match the residual stream width")
  val norm = VectorNormParams(hiddenSize, lanes, inputBits = inputBits, outputBits = elemBits, batchSize = batchSize, maxSeqLen = maxSeqLen)
  val qkv = QKVProjectionParams(
    hiddenSize, numHeads, numHeads, headDim, lanes = lanes, elemBits = elemBits,
    batchSize = batchSize, maxSeqLen = maxSeqLen, hasBias = qkvHasBias,
    computeArrayRows = computeArrayRows, computeArrayCols = computeArrayCols
  )
  val attn = AttentionParams(
    hiddenSize, numHeads, numHeads, headDim, maxSeqLen, lanes = lanes, elemBits = elemBits,
    batchSize = batchSize, outHasBias = attentionOutHasBias,
    computeArrayRows = computeArrayRows, computeArrayCols = computeArrayCols
  )
  val outLinear: LinearParams = attn.outLinear
  val residual = ResidualParams(hiddenSize, lanes = lanes, elemBits = outputBits, batchSize = batchSize, maxSeqLen = maxSeqLen)
  val ffn = DenseFFNParams(
    hiddenSize, intermediateSize, lanes = lanes, elemBits = elemBits, outputBits = outputBits,
    batchSize = batchSize, maxSeqLen = maxSeqLen, activation = mlpActivation,
    computeArrayRows = computeArrayRows, computeArrayCols = computeArrayCols
  )
}

class DecoderBlock(p: DecoderBlockParams) extends Module {
  val inSpec = StreamSpec(p.lanes * p.inputBits, log2Ceil(p.batchSize * (p.hiddenSize / p.lanes) max 2))
  val outSpec = inSpec

  val io = IO(new Bundle {
    val start = Input(Bool())
    val cfg = Input(new StageConfig(log2Ceil(p.maxSeqLen + 1 max 2)))
    val cfgValid = Input(Bool())
    val norm1Weight = Flipped(Decoupled(UInt(p.norm.inputBeatBits.W)))
    val qkvWeight = Flipped(Decoupled(new WeightWrite(p.qkv.linear.weightTileBits, p.qkv.linear.weightAddrBits)))
    val qkvBias = Flipped(Decoupled(new WeightWrite(p.qkv.linear.biasBeatBits, log2Ceil(p.qkv.linear.outBeats max 2))))
    val attentionOutWeight = Flipped(Decoupled(new WeightWrite(p.attn.outLinear.weightTileBits, p.attn.outLinear.weightAddrBits)))
    val attentionOutBias = Flipped(Decoupled(new WeightWrite(p.attn.outLinear.biasBeatBits, log2Ceil(p.attn.outLinear.outBeats max 2))))
    val norm2Weight = Flipped(Decoupled(UInt(p.norm.inputBeatBits.W)))
    val ffnUpWeight = Flipped(Decoupled(new WeightWrite(p.ffn.up.weightTileBits, p.ffn.up.weightAddrBits)))
    val ffnUpBias = Flipped(Decoupled(new WeightWrite(p.ffn.up.biasBeatBits, log2Ceil(p.ffn.up.outBeats max 2))))
    val ffnDownWeight = Flipped(Decoupled(new WeightWrite(p.ffn.down.weightTileBits, p.ffn.down.weightAddrBits)))
    val ffnDownBias = Flipped(Decoupled(new WeightWrite(p.ffn.down.biasBeatBits, log2Ceil(p.ffn.down.outBeats max 2))))
    val in = Flipped(Decoupled(new StreamBeat(inSpec)))
    val out = Decoupled(new StreamBeat(outSpec))
  })

  val ln1 = Module(new VectorNorm(p.norm))
  val qkv = Module(new QKVProjection(p.qkv))
  val attn = Module(new Attention(p.attn))
  val add1 = Module(new ResidualAdd(p.residual))
  val ln2 = Module(new VectorNorm(p.norm))
  val ffn = Module(new DenseFFN(p.ffn))
  val add2 = Module(new ResidualAdd(p.residual))

  val res1Q = Module(new PhysicalStreamFifo(new StreamBeat(inSpec), p.batchSize * p.norm.beats))
  val res2Q = Module(new PhysicalStreamFifo(new StreamBeat(inSpec), p.batchSize * p.norm.beats))

  io.in.ready := ln1.io.in.ready && res1Q.io.enq.ready
  ln1.io.in.valid := io.in.valid && res1Q.io.enq.ready
  ln1.io.in.bits := io.in.bits
  res1Q.io.enq.valid := io.in.valid && ln1.io.in.ready
  res1Q.io.enq.bits := io.in.bits

  ln1.io.cfg := io.cfg
  ln1.io.cfgValid := io.cfgValid
  ln1.io.weight <> io.norm1Weight
  ln1.io.quant.outInvScale := PhysicalMath.fp32One
  ln1.io.quant.outZeroPoint := 0.S

  qkv.io.start := io.start
  qkv.io.cfg := io.cfg
  qkv.io.cfgValid := io.cfgValid
  qkv.io.weight <> io.qkvWeight
  qkv.io.bias <> io.qkvBias
  qkv.io.qScale := PhysicalMath.fp32One
  qkv.io.kScale := PhysicalMath.fp32One
  qkv.io.vScale := PhysicalMath.fp32One
  qkv.io.in <> ln1.io.out

  attn.io.cfg := io.cfg
  attn.io.cfgValid := io.cfgValid
  attn.io.mask := 0.U
  attn.io.scoreScale := PhysicalMath.fp32One
  attn.io.ctxInvScale := PhysicalMath.fp32One
  attn.io.ctxZeroPoint := 0.U
  attn.io.outInvScale := PhysicalMath.fp32One
  attn.io.outWeight <> io.attentionOutWeight
  attn.io.outBias <> io.attentionOutBias
  attn.io.in <> qkv.io.out

  add1.io.cfg := io.cfg
  add1.io.residual <> res1Q.io.deq
  add1.io.computed <> attn.io.out

  add1.io.out.ready := ln2.io.in.ready && res2Q.io.enq.ready
  ln2.io.in.valid := add1.io.out.valid && res2Q.io.enq.ready
  ln2.io.in.bits := add1.io.out.bits
  res2Q.io.enq.valid := add1.io.out.valid && ln2.io.in.ready
  res2Q.io.enq.bits := add1.io.out.bits

  ln2.io.cfg := io.cfg
  ln2.io.cfgValid := io.cfgValid
  ln2.io.weight <> io.norm2Weight
  ln2.io.quant.outInvScale := PhysicalMath.fp32One
  ln2.io.quant.outZeroPoint := 0.S

  ffn.io.start := io.start
  ffn.io.cfg := io.cfg
  ffn.io.cfgValid := io.cfgValid
  ffn.io.upWeight <> io.ffnUpWeight
  ffn.io.upBias <> io.ffnUpBias
  ffn.io.downWeight <> io.ffnDownWeight
  ffn.io.downBias <> io.ffnDownBias
  ffn.io.in <> ln2.io.out

  add2.io.cfg := io.cfg
  add2.io.residual <> res2Q.io.deq
  add2.io.computed <> ffn.io.out
  io.out <> add2.io.out
}

class OPTPreLNBlock(p: DecoderBlockParams) extends DecoderBlock(p.copy(mlpActivation = "relu"))
class GPT2PreLNBlock(p: DecoderBlockParams) extends DecoderBlock(p.copy(mlpActivation = "gelu_new"))

final case class LlamaStyleBlockParams(
  hiddenSize: Int = 2048,
  qHeads: Int = 32,
  kvHeads: Int = 4,
  headDim: Int = 64,
  intermediateSize: Int = 5632,
  lanes: Int = 16,
  batchSize: Int = 16,
  maxSeqLen: Int = 16,
  inputBits: Int = 32,
  elemBits: Int = 16,
  outputBits: Int = 32,
  computeArrayRows: Int = 0,
  computeArrayCols: Int = 0,
  ropeTheta: Double = 10000.0,
  qkvHasBias: Boolean = false
) {
  require(inputBits == outputBits, "LlamaStyleBlock inputBits and outputBits must match the residual stream width")
  val inSpec = StreamSpec(lanes * inputBits, log2Ceil(batchSize * (hiddenSize / lanes) max 2))
  val rms = RMSNormParams(hiddenSize, lanes, inputBits = inputBits, outputBits = elemBits, batchSize = batchSize, maxSeqLen = maxSeqLen)
  val qkv = QKVProjectionParams(
    hiddenSize, qHeads, kvHeads, headDim, lanes = lanes, elemBits = elemBits,
    batchSize = batchSize, maxSeqLen = maxSeqLen, hasBias = qkvHasBias,
    computeArrayRows = computeArrayRows, computeArrayCols = computeArrayCols
  )
  val rope = RoPEParams(qkv, theta = ropeTheta)
  val attn = AttentionParams(
    hiddenSize, qHeads, kvHeads, headDim, maxSeqLen, lanes = lanes, elemBits = elemBits, batchSize = batchSize,
    computeArrayRows = computeArrayRows, computeArrayCols = computeArrayCols
  )
  val outLinear: LinearParams = attn.outLinear
  val residual = ResidualParams(hiddenSize, lanes = lanes, elemBits = outputBits, batchSize = batchSize, maxSeqLen = maxSeqLen)
  val mlp = GatedMLPParams(
    hiddenSize, intermediateSize, lanes = lanes, elemBits = elemBits, outputBits = outputBits,
    batchSize = batchSize, maxSeqLen = maxSeqLen, activation = "silu", hasBias = false,
    computeArrayRows = computeArrayRows, computeArrayCols = computeArrayCols
  )
}

class LlamaStyleBlock(p: LlamaStyleBlockParams) extends Module {
  val io = IO(new Bundle {
    val start = Input(Bool())
    val cfg = Input(new StageConfig(log2Ceil(p.maxSeqLen + 1 max 2)))
    val cfgValid = Input(Bool())
    val position = Input(UInt(log2Ceil(p.maxSeqLen max 2).W))
    val rms1Weight = Flipped(Decoupled(UInt(p.rms.vector.inputBeatBits.W)))
    val qkvWeight = Flipped(Decoupled(new WeightWrite(p.qkv.linear.weightTileBits, p.qkv.linear.weightAddrBits)))
    val qkvBias = Flipped(Decoupled(new WeightWrite(p.qkv.linear.biasBeatBits, log2Ceil(p.qkv.linear.outBeats max 2))))
    val ropeRuntime = Flipped(Decoupled(new WeightWrite(32, p.rope.runtimeAddrBits)))
    val ropeRuntimeLast = Input(Bool())
    val ropeRuntimeLoaded = Output(Bool())
    val attentionOutWeight = Flipped(Decoupled(new WeightWrite(p.attn.outLinear.weightTileBits, p.attn.outLinear.weightAddrBits)))
    val rms2Weight = Flipped(Decoupled(UInt(p.rms.vector.inputBeatBits.W)))
    val mlpGateWeight = Flipped(Decoupled(new WeightWrite(p.mlp.gate.weightTileBits, p.mlp.gate.weightAddrBits)))
    val mlpUpWeight = Flipped(Decoupled(new WeightWrite(p.mlp.up.weightTileBits, p.mlp.up.weightAddrBits)))
    val mlpDownWeight = Flipped(Decoupled(new WeightWrite(p.mlp.down.weightTileBits, p.mlp.down.weightAddrBits)))
    val in = Flipped(Decoupled(new StreamBeat(p.inSpec)))
    val out = Decoupled(new StreamBeat(p.inSpec))
  })

  val rms1 = Module(new RMSNorm(p.rms))
  val qkv = Module(new QKVProjection(p.qkv))
  val rope = Module(new RoPE(p.rope))
  val attn = Module(new AttentionGQA(p.attn))
  val add1 = Module(new ResidualAdd(p.residual))
  val rms2 = Module(new RMSNorm(p.rms))
  val mlp = Module(new GatedMLP(p.mlp))
  val add2 = Module(new ResidualAdd(p.residual))

  val res1Q = Module(new PhysicalStreamFifo(new StreamBeat(p.inSpec), p.batchSize * p.rms.vector.beats))
  val res2Q = Module(new PhysicalStreamFifo(new StreamBeat(p.inSpec), p.batchSize * p.rms.vector.beats))

  io.in.ready := rms1.io.in.ready && res1Q.io.enq.ready
  rms1.io.in.valid := io.in.valid && res1Q.io.enq.ready
  rms1.io.in.bits := io.in.bits
  res1Q.io.enq.valid := io.in.valid && rms1.io.in.ready
  res1Q.io.enq.bits := io.in.bits

  rms1.io.cfg := io.cfg
  rms1.io.cfgValid := io.cfgValid
  rms1.io.weight <> io.rms1Weight
  rms1.io.quant.outInvScale := PhysicalMath.fp32One
  rms1.io.quant.outZeroPoint := 0.S

  qkv.io.start := io.start
  qkv.io.cfg := io.cfg
  qkv.io.cfgValid := io.cfgValid
  qkv.io.weight <> io.qkvWeight
  qkv.io.bias <> io.qkvBias
  qkv.io.qScale := PhysicalMath.fp32One
  qkv.io.kScale := PhysicalMath.fp32One
  qkv.io.vScale := PhysicalMath.fp32One
  qkv.io.in <> rms1.io.out

  rope.io.cfg := io.cfg
  rope.io.cfgValid := io.cfgValid
  rope.io.position := io.position
  rope.io.runtime <> io.ropeRuntime
  rope.io.runtimeLast := io.ropeRuntimeLast
  io.ropeRuntimeLoaded := rope.io.runtimeLoaded
  rope.io.in <> qkv.io.out

  attn.io.cfg := io.cfg
  attn.io.cfgValid := io.cfgValid
  attn.io.mask := 0.U
  attn.io.scoreScale := PhysicalMath.fp32One
  attn.io.ctxInvScale := PhysicalMath.fp32One
  attn.io.ctxZeroPoint := 0.U
  attn.io.outInvScale := PhysicalMath.fp32One
  attn.io.outWeight <> io.attentionOutWeight
  attn.io.outBias.valid := false.B
  attn.io.outBias.bits.addr := 0.U
  attn.io.outBias.bits.data := 0.U
  attn.io.in <> rope.io.out

  add1.io.cfg := io.cfg
  add1.io.residual <> res1Q.io.deq
  add1.io.computed <> attn.io.out

  add1.io.out.ready := rms2.io.in.ready && res2Q.io.enq.ready
  rms2.io.in.valid := add1.io.out.valid && res2Q.io.enq.ready
  rms2.io.in.bits := add1.io.out.bits
  res2Q.io.enq.valid := add1.io.out.valid && rms2.io.in.ready
  res2Q.io.enq.bits := add1.io.out.bits

  rms2.io.cfg := io.cfg
  rms2.io.cfgValid := io.cfgValid
  rms2.io.weight <> io.rms2Weight
  rms2.io.quant.outInvScale := PhysicalMath.fp32One
  rms2.io.quant.outZeroPoint := 0.S

  mlp.io.start := io.start
  mlp.io.cfg := io.cfg
  mlp.io.cfgValid := io.cfgValid
  mlp.io.gateWeight <> io.mlpGateWeight
  mlp.io.upWeight <> io.mlpUpWeight
  mlp.io.downWeight <> io.mlpDownWeight
  mlp.io.gateBias.valid := false.B
  mlp.io.gateBias.bits := 0.U.asTypeOf(mlp.io.gateBias.bits)
  mlp.io.upBias.valid := false.B
  mlp.io.upBias.bits := 0.U.asTypeOf(mlp.io.upBias.bits)
  mlp.io.downBias.valid := false.B
  mlp.io.downBias.bits := 0.U.asTypeOf(mlp.io.downBias.bits)
  mlp.io.in <> rms2.io.out

  add2.io.cfg := io.cfg
  add2.io.residual <> res2Q.io.deq
  add2.io.computed <> mlp.io.out
  io.out <> add2.io.out
}

class Qwen2Block(p: LlamaStyleBlockParams) extends LlamaStyleBlock(p.copy(qkvHasBias = true))

final case class Gemma3TextBlockParams(
  hiddenSize: Int = 1152,
  qHeads: Int = 4,
  kvHeads: Int = 1,
  headDim: Int = 256,
  intermediateSize: Int = 6912,
  lanes: Int = 16,
  batchSize: Int = 16,
  maxSeqLen: Int = 16,
  inputBits: Int = 32,
  elemBits: Int = 16,
  outputBits: Int = 32,
  ropeTheta: Double = 1000000.0,
  slidingWindow: Int = 512
) {
  require(inputBits == outputBits, "Gemma3TextBlock inputBits and outputBits must match the residual stream width")
  val inSpec = StreamSpec(lanes * inputBits, log2Ceil(batchSize * (hiddenSize / lanes) max 2))
  val rmsIn = RMSNormParams(hiddenSize, lanes, inputBits = inputBits, outputBits = elemBits, batchSize = batchSize, maxSeqLen = maxSeqLen)
  val rmsFp = RMSNormParams(hiddenSize, lanes, inputBits = outputBits, outputBits = outputBits, batchSize = batchSize, maxSeqLen = maxSeqLen)
  val qkv = QKVProjectionParams(hiddenSize, qHeads, kvHeads, headDim, lanes = lanes, elemBits = elemBits, batchSize = batchSize, maxSeqLen = maxSeqLen)
  val qkNorm = QKNormParams(qkv)
  val rope = RoPEParams(qkv, theta = ropeTheta, localTheta = Some(10000.0))
  val attn = AttentionParams(hiddenSize, qHeads, kvHeads, headDim, maxSeqLen, lanes = lanes, elemBits = elemBits, batchSize = batchSize)
  val outLinear: LinearParams = attn.outLinear
  val residual = ResidualParams(hiddenSize, lanes = lanes, elemBits = outputBits, batchSize = batchSize, maxSeqLen = maxSeqLen)
  val mlp = GatedMLPParams(hiddenSize, intermediateSize, lanes = lanes, elemBits = elemBits, outputBits = outputBits, batchSize = batchSize, maxSeqLen = maxSeqLen, activation = "gelu_pytorch_tanh", hasBias = false)
}

class Gemma3TextBlock(p: Gemma3TextBlockParams) extends Module {
  val io = IO(new Bundle {
    val start = Input(Bool())
    val cfg = Input(new StageConfig(log2Ceil(p.maxSeqLen + 1 max 2)))
    val cfgValid = Input(Bool())
    val position = Input(UInt(log2Ceil(p.maxSeqLen max 2).W))
    val rmsInWeight = Flipped(Decoupled(UInt(p.rmsIn.vector.inputBeatBits.W)))
    val qkvWeight = Flipped(Decoupled(new WeightWrite(p.qkv.linear.weightTileBits, p.qkv.linear.weightAddrBits)))
    val qkvBias = Flipped(Decoupled(new WeightWrite(p.qkv.linear.biasBeatBits, log2Ceil(p.qkv.linear.outBeats max 2))))
    val qNormWeight = Flipped(Decoupled(UInt(p.qkNorm.weightBits.W)))
    val kNormWeight = Flipped(Decoupled(UInt(p.qkNorm.weightBits.W)))
    val ropeRuntime = Flipped(Decoupled(new WeightWrite(32, p.rope.runtimeAddrBits)))
    val ropeRuntimeLast = Input(Bool())
    val ropeRuntimeLoaded = Output(Bool())
    val attentionOutWeight = Flipped(Decoupled(new WeightWrite(p.attn.outLinear.weightTileBits, p.attn.outLinear.weightAddrBits)))
    val postAttentionNormWeight = Flipped(Decoupled(UInt(p.rmsFp.vector.inputBeatBits.W)))
    val preFfnNormWeight = Flipped(Decoupled(UInt(p.rmsIn.vector.inputBeatBits.W)))
    val mlpGateWeight = Flipped(Decoupled(new WeightWrite(p.mlp.gate.weightTileBits, p.mlp.gate.weightAddrBits)))
    val mlpUpWeight = Flipped(Decoupled(new WeightWrite(p.mlp.up.weightTileBits, p.mlp.up.weightAddrBits)))
    val mlpDownWeight = Flipped(Decoupled(new WeightWrite(p.mlp.down.weightTileBits, p.mlp.down.weightAddrBits)))
    val postFfnNormWeight = Flipped(Decoupled(UInt(p.rmsFp.vector.inputBeatBits.W)))
    val in = Flipped(Decoupled(new StreamBeat(p.inSpec)))
    val out = Decoupled(new StreamBeat(p.inSpec))
  })

  val rmsIn = Module(new RMSNorm(p.rmsIn))
  val qkv = Module(new QKVProjection(p.qkv))
  val qkNorm = Module(new QKNorm(p.qkNorm))
  val rope = Module(new RoPE(p.rope))
  val attn = Module(new AttentionMQA(p.attn))
  val postAttnNorm = Module(new RMSNorm(p.rmsFp))
  val add1 = Module(new ResidualAdd(p.residual))
  val preFfnNorm = Module(new RMSNorm(p.rmsIn))
  val mlp = Module(new GatedMLP(p.mlp))
  val postFfnNorm = Module(new RMSNorm(p.rmsFp))
  val add2 = Module(new ResidualAdd(p.residual))

  val res1Q = Module(new PhysicalStreamFifo(new StreamBeat(p.inSpec), p.batchSize * p.rmsIn.vector.beats))
  val res2Q = Module(new PhysicalStreamFifo(new StreamBeat(p.inSpec), p.batchSize * p.rmsIn.vector.beats))

  io.in.ready := rmsIn.io.in.ready && res1Q.io.enq.ready
  rmsIn.io.in.valid := io.in.valid && res1Q.io.enq.ready
  rmsIn.io.in.bits := io.in.bits
  res1Q.io.enq.valid := io.in.valid && rmsIn.io.in.ready
  res1Q.io.enq.bits := io.in.bits

  rmsIn.io.cfg := io.cfg
  rmsIn.io.cfgValid := io.cfgValid
  rmsIn.io.weight <> io.rmsInWeight
  rmsIn.io.quant.outInvScale := PhysicalMath.fp32One
  rmsIn.io.quant.outZeroPoint := 0.S

  qkv.io.start := io.start
  qkv.io.cfg := io.cfg
  qkv.io.cfgValid := io.cfgValid
  qkv.io.weight <> io.qkvWeight
  qkv.io.bias <> io.qkvBias
  qkv.io.qScale := PhysicalMath.fp32One
  qkv.io.kScale := PhysicalMath.fp32One
  qkv.io.vScale := PhysicalMath.fp32One
  qkv.io.in <> rmsIn.io.out

  qkNorm.io.cfg := io.cfg
  qkNorm.io.cfgValid := io.cfgValid
  qkNorm.io.qWeight <> io.qNormWeight
  qkNorm.io.kWeight <> io.kNormWeight
  qkNorm.io.in <> qkv.io.out

  rope.io.cfg := io.cfg
  rope.io.cfgValid := io.cfgValid
  rope.io.position := io.position
  rope.io.runtime <> io.ropeRuntime
  rope.io.runtimeLast := io.ropeRuntimeLast
  io.ropeRuntimeLoaded := rope.io.runtimeLoaded
  rope.io.in <> qkNorm.io.out

  attn.io.cfg := io.cfg
  attn.io.cfgValid := io.cfgValid
  attn.io.mask := 0.U
  attn.io.scoreScale := PhysicalMath.fp32One
  attn.io.ctxInvScale := PhysicalMath.fp32One
  attn.io.ctxZeroPoint := 0.U
  attn.io.outInvScale := PhysicalMath.fp32One
  attn.io.outWeight <> io.attentionOutWeight
  attn.io.outBias.valid := false.B
  attn.io.outBias.bits.addr := 0.U
  attn.io.outBias.bits.data := 0.U
  attn.io.in <> rope.io.out

  postAttnNorm.io.cfg := io.cfg
  postAttnNorm.io.cfgValid := io.cfgValid
  postAttnNorm.io.weight <> io.postAttentionNormWeight
  postAttnNorm.io.quant.outInvScale := PhysicalMath.fp32One
  postAttnNorm.io.quant.outZeroPoint := 0.S
  postAttnNorm.io.in <> attn.io.out

  add1.io.cfg := io.cfg
  add1.io.residual <> res1Q.io.deq
  add1.io.computed <> postAttnNorm.io.out

  add1.io.out.ready := preFfnNorm.io.in.ready && res2Q.io.enq.ready
  preFfnNorm.io.in.valid := add1.io.out.valid && res2Q.io.enq.ready
  preFfnNorm.io.in.bits := add1.io.out.bits
  res2Q.io.enq.valid := add1.io.out.valid && preFfnNorm.io.in.ready
  res2Q.io.enq.bits := add1.io.out.bits

  preFfnNorm.io.cfg := io.cfg
  preFfnNorm.io.cfgValid := io.cfgValid
  preFfnNorm.io.weight <> io.preFfnNormWeight
  preFfnNorm.io.quant.outInvScale := PhysicalMath.fp32One
  preFfnNorm.io.quant.outZeroPoint := 0.S

  mlp.io.start := io.start
  mlp.io.cfg := io.cfg
  mlp.io.cfgValid := io.cfgValid
  mlp.io.gateWeight <> io.mlpGateWeight
  mlp.io.upWeight <> io.mlpUpWeight
  mlp.io.downWeight <> io.mlpDownWeight
  mlp.io.gateBias.valid := false.B
  mlp.io.gateBias.bits := 0.U.asTypeOf(mlp.io.gateBias.bits)
  mlp.io.upBias.valid := false.B
  mlp.io.upBias.bits := 0.U.asTypeOf(mlp.io.upBias.bits)
  mlp.io.downBias.valid := false.B
  mlp.io.downBias.bits := 0.U.asTypeOf(mlp.io.downBias.bits)
  mlp.io.in <> preFfnNorm.io.out

  postFfnNorm.io.cfg := io.cfg
  postFfnNorm.io.cfgValid := io.cfgValid
  postFfnNorm.io.weight <> io.postFfnNormWeight
  postFfnNorm.io.quant.outInvScale := PhysicalMath.fp32One
  postFfnNorm.io.quant.outZeroPoint := 0.S
  postFfnNorm.io.in <> mlp.io.out

  add2.io.cfg := io.cfg
  add2.io.residual <> res2Q.io.deq
  add2.io.computed <> postFfnNorm.io.out
  io.out <> add2.io.out
}
