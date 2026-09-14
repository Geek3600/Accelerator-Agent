package spatialaccagent.templates

import chisel3._
import chisel3.util._

final case class AttentionParams(
  hiddenSize: Int,
  qHeads: Int,
  kvHeads: Int,
  headDim: Int,
  seqLen: Int,
  lanes: Int = 8,
  elemBits: Int = 16,
  qkvElemsPerBeat: Int = 8,
  batchSize: Int = 16
) {
  require(hiddenSize == qHeads * headDim, "attention hidden size must equal qHeads * headDim")
  require(qHeads > 0 && kvHeads > 0 && qHeads % kvHeads == 0, "invalid GQA head grouping")
  require(headDim > 0 && seqLen > 0, "attention dimensions must be positive")
  require(elemBits == 16, "the immutable attention internal element type is IEEE FP16")
  require(hiddenSize % lanes == 0, "hiddenSize must be divisible by output lanes")

  val qkv: QKVProjectionParams = QKVProjectionParams(
    hiddenSize,
    qHeads,
    kvHeads,
    headDim,
    lanes = lanes,
    elemBits = elemBits,
    qkvElemsPerBeat = qkvElemsPerBeat,
    batchSize = batchSize,
    maxSeqLen = seqLen
  )
  val qDim: Int = qHeads * headDim
  val kDim: Int = kvHeads * headDim
  val kvGroupSize: Int = qHeads / kvHeads
  val seqBits: Int = log2Ceil(seqLen + 1 max 2)
  val rowBits: Int = log2Ceil(seqLen max 2)
  val headVectorBits: Int = headDim * elemBits
  val headAddrBits: Int = log2Ceil(qHeads max 2)
  val softmax: SoftmaxParams = SoftmaxParams(
    seqLen = seqLen,
    lanes = seqLen,
    elemBits = 32,
    batchSize = seqLen * qHeads,
    causal = true,
    slidingWindow = 0
  )
  val outLinear: LinearParams = LinearParams(
    inDim = qDim,
    outDim = hiddenSize,
    inLanes = headDim,
    outLanes = lanes,
    elemBits = elemBits,
    accBits = 32,
    outputBits = 32,
    batchSize = seqLen,
    maxSeqLen = seqLen,
    hasBias = false
  )
  val addrBits: Int = outLinear.outputAddrBits
}

class Attention(p: AttentionParams) extends Module {
  val io = IO(new Bundle {
    val cfg = Input(new StageConfig(p.seqBits))
    val cfgValid = Input(Bool())
    val in = Flipped(Decoupled(new QKVStreamBeat(p.qkv)))
    val mask = Input(UInt(p.seqLen.W))
    val scoreScale = Input(UInt(32.W))
    val ctxInvScale = Input(UInt(32.W))
    val ctxZeroPoint = Input(UInt(8.W))
    val outInvScale = Input(UInt(32.W))
    val outWeight = Flipped(Decoupled(new WeightWrite(p.outLinear.weightTileBits, p.outLinear.weightAddrBits)))
    val out = Decoupled(new StreamBeat(StreamSpec(p.outLinear.outputBeatBits, p.outLinear.outputAddrBits)))
  })

  val qMemory = Reg(Vec(p.seqLen * p.qDim, UInt(p.elemBits.W)))
  val kMemory = Reg(Vec(p.seqLen * p.kDim, UInt(p.elemBits.W)))
  val vMemory = Reg(Vec(p.seqLen * p.kDim, UInt(p.elemBits.W)))
  val contextMemory = Reg(Vec(p.seqLen * p.qDim, UInt(p.elemBits.W)))

  val seqLimit = RegInit(p.seqLen.U(p.seqBits.W))
  val normalizedSeq = Mux(
    io.cfg.seqlen === 0.U || io.cfg.seqlen > p.seqLen.U,
    p.seqLen.U(p.seqBits.W),
    io.cfg.seqlen
  )
  when(io.cfgValid) {
    seqLimit := normalizedSeq
  }
  val activeSeq = Mux(io.cfgValid, normalizedSeq, seqLimit)

  val sWait :: sScore :: sProbability :: sProjectWait :: sProjectFeed :: sProjectDrain :: Nil = Enum(6)
  val state = RegInit(sWait)
  val collectToken = RegInit(0.U(p.rowBits.W))
  val workRow = RegInit(0.U(p.rowBits.W))
  val workHead = RegInit(0.U(p.qkv.headBits.W))
  val projectToken = RegInit(0.U(p.rowBits.W))
  val projectBeat = RegInit(0.U(log2Ceil(p.qHeads max 2).W))
  val tokenReady = RegInit(VecInit(Seq.fill(p.seqLen)(false.B)))
  val collectionClosed = RegInit(false.B)

  io.in.ready := !collectionClosed
  val inputFields = io.in.bits.data.asTypeOf(Vec(3 * p.qkvElemsPerBeat, UInt(p.elemBits.W)))
  val inputKvHead = io.in.bits.head / p.kvGroupSize.U

  when(io.in.fire) {
    for (lane <- 0 until p.qkvElemsPerBeat) {
      val dimension = io.in.bits.addr * p.qkvElemsPerBeat.U + lane.U
      val qIndex = collectToken * p.qDim.U + io.in.bits.head * p.headDim.U + dimension
      val kvIndex = collectToken * p.kDim.U + inputKvHead * p.headDim.U + dimension
      qMemory(qIndex) := inputFields(lane)
      kMemory(kvIndex) := inputFields(p.qkvElemsPerBeat + lane)
      vMemory(kvIndex) := inputFields(2 * p.qkvElemsPerBeat + lane)
    }

    when(io.in.bits.last) {
      tokenReady(collectToken) := true.B
      when(collectToken === activeSeq - 1.U) {
        collectionClosed := true.B
      }.otherwise {
        collectToken := collectToken + 1.U
      }
    }
  }

  when(state === sWait && tokenReady(workRow)) {
    workHead := 0.U
    state := sScore
  }

  val attentionScale = IeeeMath.fp32Constant(math.pow(p.headDim.toDouble, -0.5))
  val scoreValues = Wire(Vec(p.seqLen, UInt(32.W)))
  val selectedKvHead = workHead / p.kvGroupSize.U

  for (keyToken <- 0 until p.seqLen) {
    val products = (0 until p.headDim).map { dimension =>
      val qIndex = workRow * p.qDim.U + workHead * p.headDim.U + dimension.U
      val kIndex = keyToken.U * p.kDim.U + selectedKvHead * p.headDim.U + dimension.U
      IeeeMath.mulFp32(
        IeeeMath.toFp32(qMemory(qIndex), p.elemBits),
        IeeeMath.toFp32(kMemory(kIndex), p.elemBits)
      )
    }
    val scaledScore = IeeeMath.mulFp32(IeeeMath.sumFp32(products), attentionScale)
    scoreValues(keyToken) := Mux(
      keyToken.U(p.rowBits.W) <= workRow,
      scaledScore,
      IeeeMath.fp32Zero
    )
  }

  val softmax = Module(new Softmax(p.softmax))
  val activeMaskBits = Wire(Vec(p.seqLen, Bool()))
  for (token <- 0 until p.seqLen) {
    activeMaskBits(token) := token.U < seqLimit
  }

  softmax.io.cfg := io.cfg
  softmax.io.cfgValid := io.cfgValid
  softmax.io.rowIndex := workRow
  softmax.io.mask := activeMaskBits.asUInt
  softmax.io.in.valid := state === sScore
  softmax.io.in.bits.data := scoreValues.asUInt
  softmax.io.in.bits.st := workRow === 0.U && workHead === 0.U
  softmax.io.in.bits.addr := workRow * p.qHeads.U + workHead
  softmax.io.in.bits.last := true.B
  softmax.io.out.ready := state === sProbability

  when(softmax.io.in.fire) {
    state := sProbability
  }

  val probabilities = softmax.io.out.bits.data.asTypeOf(Vec(p.seqLen, UInt(32.W)))
  val contextValues = Wire(Vec(p.headDim, UInt(32.W)))
  for (dimension <- 0 until p.headDim) {
    val products = (0 until p.seqLen).map { valueToken =>
      val vIndex = valueToken.U * p.kDim.U + selectedKvHead * p.headDim.U + dimension.U
      val product = IeeeMath.mulFp32(
        probabilities(valueToken),
        IeeeMath.toFp32(vMemory(vIndex), p.elemBits)
      )
      Mux(
        valueToken.U(p.rowBits.W) <= workRow,
        product,
        IeeeMath.fp32Zero
      )
    }
    contextValues(dimension) := IeeeMath.sumFp32(products)
  }

  when(softmax.io.out.fire) {
    for (dimension <- 0 until p.headDim) {
      val contextIndex = workRow * p.qDim.U + workHead * p.headDim.U + dimension.U
      contextMemory(contextIndex) := IeeeMath.fromFp32(contextValues(dimension), p.elemBits)
    }

    when(workHead === (p.qHeads - 1).U) {
      workHead := 0.U
      projectToken := workRow
      projectBeat := 0.U
      state := sProjectWait
    }.otherwise {
      workHead := workHead + 1.U
      state := sScore
    }
  }

  val finalProjectToken = projectToken === seqLimit - 1.U
  val successorIndex = Wire(UInt(p.rowBits.W))
  successorIndex := Mux(finalProjectToken, 0.U, projectToken + 1.U)
  when(state === sProjectWait && (finalProjectToken || tokenReady(successorIndex))) {
    state := sProjectFeed
  }

  val outputProjection = Module(new Linear(p.outLinear))
  outputProjection.io.start := false.B
  outputProjection.io.cfg := io.cfg
  outputProjection.io.cfgValid := io.cfgValid
  outputProjection.io.weight <> io.outWeight
  outputProjection.io.bias.valid := false.B
  outputProjection.io.bias.bits.addr := 0.U
  outputProjection.io.bias.bits.data := 0.U
  outputProjection.io.scale.outScale := IeeeMath.fp32One
  outputProjection.io.scale.biasScale := IeeeMath.fp32One

  val projectionInput = Wire(Vec(p.headDim, UInt(p.elemBits.W)))
  for (dimension <- 0 until p.headDim) {
    val contextIndex = projectToken * p.qDim.U + projectBeat * p.headDim.U + dimension.U
    projectionInput(dimension) := contextMemory(contextIndex)
  }

  outputProjection.io.in.valid := state === sProjectFeed
  outputProjection.io.in.bits.data := projectionInput.asUInt
  outputProjection.io.in.bits.st := projectBeat === 0.U
  outputProjection.io.in.bits.addr := projectToken * p.qHeads.U + projectBeat
  outputProjection.io.in.bits.last := projectBeat === (p.qHeads - 1).U

  when(outputProjection.io.in.fire) {
    when(projectBeat === (p.qHeads - 1).U) {
      projectBeat := 0.U
      state := sProjectDrain
    }.otherwise {
      projectBeat := projectBeat + 1.U
    }
  }

  io.out.valid := outputProjection.io.out.valid && state === sProjectDrain
  io.out.bits := outputProjection.io.out.bits
  outputProjection.io.out.ready := io.out.ready && state === sProjectDrain

  when(io.out.fire && io.out.bits.last) {
    tokenReady(projectToken) := false.B
    when(projectToken === seqLimit - 1.U) {
      projectToken := 0.U
      workRow := 0.U
      collectToken := 0.U
      collectionClosed := false.B
      state := sWait
    }.otherwise {
      workRow := projectToken + 1.U
      projectToken := projectToken + 1.U
      projectBeat := 0.U
      state := sWait
    }
  }

  // The captured reference uses no explicit attention mask and applies the
  // immutable headDim^-0.5 scaling. Legacy quantization/configuration ports are
  // retained for ABI compatibility but cannot select another model convention.
  dontTouch(io.mask)
  dontTouch(io.scoreScale)
  dontTouch(io.ctxInvScale)
  dontTouch(io.ctxZeroPoint)
  dontTouch(io.outInvScale)
}

class AttentionMHA(p: AttentionParams) extends Attention(p)
class AttentionGQA(p: AttentionParams) extends Attention(p)
class AttentionMQA(p: AttentionParams) extends Attention(p)
