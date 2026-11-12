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
  batchSize: Int = 16,
  outHasBias: Boolean = false,
  outWeightRole: String = "weight_attn_out",
  outBiasRole: String = "weight_attn_out_bias",
  computeArrayRows: Int = 0,
  computeArrayCols: Int = 0,
  cacheTileWords: Int = PhysicalImplementation.resolveCacheTileWords(256),
  cacheTileCount: Int = PhysicalImplementation.resolveCacheTileCount(2),
  refillDataWidthBits: Int = PhysicalImplementation.resolveRefillDataWidthBits(512),
  crossTokenReuseTokens: Int = PhysicalImplementation.resolveCrossTokenReuseTokens(16),
  outCrossTokenReuseTokens: Int = PhysicalImplementation.resolveAttentionOutputCrossTokenReuseTokens(1),
  weightBits: Int = 0,
  integerMode: Boolean = false,
  accBits: Int = 32
) {
  require(hiddenSize > 0, "attention hidden size must be positive")
  require(qHeads > 0 && kvHeads > 0 && qHeads % kvHeads == 0, "invalid GQA head grouping")
  require(headDim > 0 && seqLen > 0, "attention dimensions must be positive")
  if (integerMode) {
    require(elemBits == 8, "integer attention activations must be signed INT8")
    require((if (weightBits == 0) 4 else weightBits) == 4, "integer attention matrix weights must be signed INT4")
    require(accBits == 32, "integer attention accumulation must be signed INT32")
  } else {
    require(elemBits == 16, "the legacy attention internal element type is IEEE FP16")
    require(accBits == 32, "floating-point attention accumulation must use FP32")
  }
  require(hiddenSize % lanes == 0, "hiddenSize must be divisible by output lanes")
  require(headDim % qkvElemsPerBeat == 0, "headDim must align to QKV stream beats")
  require(outCrossTokenReuseTokens > 0, "attention output cross-token reuse must be positive")

  val qkv: QKVProjectionParams = QKVProjectionParams(
    hiddenSize, qHeads, kvHeads, headDim, lanes, elemBits, qkvElemsPerBeat, batchSize, seqLen,
    computeArrayRows = computeArrayRows, computeArrayCols = computeArrayCols,
    cacheTileWords = cacheTileWords,
    cacheTileCount = cacheTileCount,
    refillDataWidthBits = refillDataWidthBits,
    crossTokenReuseTokens = crossTokenReuseTokens,
    weightBits = weightBits,
    integerMode = integerMode,
    accBits = accBits
  )
  val qDim: Int = qHeads * headDim
  val kDim: Int = kvHeads * headDim
  val kvGroupSize: Int = qHeads / kvHeads
  val seqBits: Int = log2Ceil(seqLen + 1 max 2)
  val rowBits: Int = log2Ceil(seqLen max 2)
  val headVectorBits: Int = headDim * elemBits
  val headAddrBits: Int = log2Ceil(qHeads max 2)
  val scoreLanes: Int = Integer.highestOneBit(headDim min 32)
  val softmax: SoftmaxParams = SoftmaxParams(seqLen, lanes = 1, elemBits = 32, batchSize = seqLen * qHeads, causal = true, slidingWindow = 0)
  // Preserve independent activation, matrix-weight, and accumulator widths
  // through the output projection constructor. The integer attention datapath
  // still requires its own implementation before this policy can be accepted
  // as a complete W4A8 hierarchy.
  val outLinear: LinearParams = LinearParams(
    inDim = qDim,
    outDim = hiddenSize,
    inLanes = headDim,
    outLanes = lanes,
    elemBits = elemBits,
    weightBits = if (integerMode) (if (weightBits == 0) 4 else weightBits) else elemBits,
    integerMode = integerMode,
    accBits = accBits,
    outputBits = if (integerMode) 8 else 32,
    batchSize = seqLen,
    maxSeqLen = seqLen,
    hasBias = outHasBias,
    weightRole = outWeightRole,
    biasRole = outBiasRole,
    computeArrayRows = computeArrayRows,
    computeArrayCols = computeArrayCols,
    cacheTileWords = cacheTileWords,
    cacheTileCount = cacheTileCount,
    refillDataWidthBits = refillDataWidthBits,
    crossTokenReuseTokens = outCrossTokenReuseTokens
  )
  val addrBits: Int = outLinear.outputAddrBits
}

private class FloatingAttention(p: AttentionParams) extends Module {
  val io = IO(new Bundle {
    val outChannelScaleShift = Input(Vec(p.outLinear.outDim, SInt(8.W)))
    val outActivationScaleShift = Input(SInt(8.W))
    val outOutputScaleShift = Input(SInt(8.W))
    val cfg = Input(new StageConfig(p.seqBits))
    val cfgValid = Input(Bool())
    val in = Flipped(Decoupled(new QKVStreamBeat(p.qkv)))
    val mask = Input(UInt(p.seqLen.W))
    val scoreScale = Input(UInt(32.W))
    val ctxInvScale = Input(UInt(32.W))
    val ctxZeroPoint = Input(UInt(8.W))
    val outInvScale = Input(UInt(32.W))
    val outChannelScale = Input(Vec(p.outLinear.outDim, UInt(32.W)))
    val outActivationScale = Input(UInt(32.W))
    val outOutputScale = Input(UInt(32.W))
    val outWeight = Flipped(Decoupled(new WeightWrite(p.outLinear.weightTileBits, p.outLinear.weightAddrBits)))
    val outBias = Flipped(Decoupled(new WeightWrite(p.outLinear.biasBeatBits, log2Ceil(p.outLinear.outBeats max 2))))
    val tile = new WeightTileServiceIO(p.refillDataWidthBits)
    val out = Decoupled(new StreamBeat(StreamSpec(p.outLinear.outputBeatBits, p.outLinear.outputAddrBits)))
  })

  private val qHeadDepth = p.seqLen * p.qHeads
  private val kvHeadDepth = p.seqLen * p.kvHeads
  private val contextAccBits = p.headDim * 32

  val qMemory = Module(new PhysicalSimpleDualPortMemory(qHeadDepth, p.headVectorBits, "cache"))
  val kMemory = Module(new PhysicalSimpleDualPortMemory(kvHeadDepth, p.headVectorBits, "cache"))
  val vMemory = Module(new PhysicalSimpleDualPortMemory(kvHeadDepth, p.headVectorBits, "cache"))
  val scoreMemory = Module(new PhysicalSimpleDualPortMemory(p.seqLen, 32, "activation"))
  // XPM requires at least two addressable words even for a single logical
  // accumulator. Only address zero is used; the second word keeps the RAM
  // primitive legal and does not change the datapath contract.
  val contextAccMemory = Module(new PhysicalSimpleDualPortMemory(2, contextAccBits, "activation"))
  val contextMemory = Module(new PhysicalSimpleDualPortMemory(qHeadDepth, p.headVectorBits, "activation"))

  val seqLimit = RegInit(p.seqLen.U(p.seqBits.W))
  val normalizedSeq = Mux(io.cfg.seqlen === 0.U || io.cfg.seqlen > p.seqLen.U, p.seqLen.U(p.seqBits.W), io.cfg.seqlen)
  when(io.cfgValid) { seqLimit := normalizedSeq }
  val activeSeq = Mux(io.cfgValid, normalizedSeq, seqLimit)

  val qCollectReg = RegInit(0.U(p.headVectorBits.W))
  val kCollectReg = RegInit(0.U(p.headVectorBits.W))
  val vCollectReg = RegInit(0.U(p.headVectorBits.W))
  val qCollect = qCollectReg.asTypeOf(Vec(p.headDim, UInt(p.elemBits.W)))
  val kCollect = kCollectReg.asTypeOf(Vec(p.headDim, UInt(p.elemBits.W)))
  val vCollect = vCollectReg.asTypeOf(Vec(p.headDim, UInt(p.elemBits.W)))
  val nextQCollect = Wire(Vec(p.headDim, UInt(p.elemBits.W)))
  val nextKCollect = Wire(Vec(p.headDim, UInt(p.elemBits.W)))
  val nextVCollect = Wire(Vec(p.headDim, UInt(p.elemBits.W)))
  nextQCollect := qCollect
  nextKCollect := kCollect
  nextVCollect := vCollect

  private val states = Enum(32)
  private val sWait = states(0)
  private val sScoreRead = states(1)
  private val sScoreCapture = states(2)
  private val sScoreMulIssue = states(3)
  private val sScoreMulWait = states(4)
  private val sScoreAccIssue = states(5)
  private val sScoreAccWait = states(6)
  private val sScoreScaleIssue = states(7)
  private val sScoreScaleWait = states(8)
  private val sScoreWrite = states(9)
  private val sContextInit = states(10)
  private val sSoftmaxRead = states(11)
  private val sSoftmaxCapture = states(12)
  private val sSoftmaxFeed = states(13)
  private val sSoftmaxDrain = states(14)
  private val sContextRead = states(15)
  private val sContextCapture = states(16)
  private val sContextMulIssue = states(17)
  private val sContextMulWait = states(18)
  private val sContextAccRead = states(19)
  private val sContextAccCapture = states(20)
  private val sContextAccIssue = states(21)
  private val sContextAccWait = states(22)
  private val sContextAccWrite = states(23)
  private val sContextFinalizeRead = states(24)
  private val sContextFinalizeCapture = states(25)
  private val sContextWrite = states(26)
  private val sProjectWait = states(27)
  private val sProjectRead = states(28)
  private val sProjectCapture = states(29)
  private val sProjectFeed = states(30)
  private val sProjectDrain = states(31)
  val state = RegInit(sWait)

  val collectToken = RegInit(0.U(p.rowBits.W))
  val workRow = RegInit(0.U(p.rowBits.W))
  val workHead = RegInit(0.U(p.qkv.headBits.W))
  val keyToken = RegInit(0.U(p.rowBits.W))
  val scoreDimension = RegInit(0.U(log2Ceil(p.headDim + 1 max 2).W))
  val scoreReadIndex = RegInit(0.U(p.rowBits.W))
  val softmaxOutIndex = RegInit(0.U(p.rowBits.W))
  val valueToken = RegInit(0.U(p.rowBits.W))
  val projectToken = RegInit(0.U(p.rowBits.W))
  val projectBeat = RegInit(0.U(p.headAddrBits.W))
  val tokenReady = RegInit(0.U(p.seqLen.W))
  val collectionClosed = RegInit(false.B)

  val qHeadReg = Reg(UInt(p.headVectorBits.W))
  val kHeadReg = Reg(UInt(p.headVectorBits.W))
  val vHeadReg = Reg(UInt(p.headVectorBits.W))
  val scoreAccReg = Reg(UInt(32.W))
  val scoreProductReg = Reg(UInt(32.W))
  val scoreValueReg = Reg(UInt(32.W))
  val scoreFeedReg = Reg(UInt(32.W))
  val probabilityReg = Reg(UInt(32.W))
  val contextProductReg = Reg(UInt(contextAccBits.W))
  val contextAccReg = Reg(UInt(contextAccBits.W))
  val projectionWord = Reg(UInt(p.headVectorBits.W))

  io.in.ready := !collectionClosed
  val inputFields = io.in.bits.data.asTypeOf(Vec(3 * p.qkvElemsPerBeat, UInt(p.elemBits.W)))
  val inputKvHead = io.in.bits.head / p.kvGroupSize.U
  val finalHeadBeat = io.in.bits.addr === (p.qkv.headBeats - 1).U
  for (lane <- 0 until p.qkvElemsPerBeat) {
    val dimension = io.in.bits.addr * p.qkvElemsPerBeat.U + lane.U
    val boundedDimension = AccMath.boundedIndex(dimension, p.headDim)
    nextQCollect(boundedDimension) := inputFields(lane)
    nextKCollect(boundedDimension) := inputFields(p.qkvElemsPerBeat + lane)
    nextVCollect(boundedDimension) := inputFields(2 * p.qkvElemsPerBeat + lane)
  }

  qMemory.io.writeEn := io.in.fire && finalHeadBeat
  qMemory.io.writeAddr := AccMath.boundedIndex(collectToken * p.qHeads.U + io.in.bits.head, qHeadDepth)
  qMemory.io.writeData := nextQCollect.asUInt
  kMemory.io.writeEn := io.in.fire && finalHeadBeat
  kMemory.io.writeAddr := AccMath.boundedIndex(collectToken * p.kvHeads.U + inputKvHead, kvHeadDepth)
  kMemory.io.writeData := nextKCollect.asUInt
  vMemory.io.writeEn := io.in.fire && finalHeadBeat
  vMemory.io.writeAddr := AccMath.boundedIndex(collectToken * p.kvHeads.U + inputKvHead, kvHeadDepth)
  vMemory.io.writeData := nextVCollect.asUInt

  val inputTokenDone = io.in.fire && io.in.bits.last
  val outputTokenDone = io.out.fire && io.out.bits.last
  val tokenSetMask = Wire(UInt(p.seqLen.W))
  val tokenClearMask = Wire(UInt(p.seqLen.W))
  tokenSetMask := 1.U << collectToken
  tokenClearMask := 1.U << projectToken
  val tokenReadyAfterInput = Mux(inputTokenDone, tokenReady | tokenSetMask, tokenReady)
  tokenReady := Mux(outputTokenDone, tokenReadyAfterInput & ~tokenClearMask, tokenReadyAfterInput)

  when(io.in.fire) {
    qCollectReg := nextQCollect.asUInt
    kCollectReg := nextKCollect.asUInt
    vCollectReg := nextVCollect.asUInt
    when(io.in.bits.last) {
      when(collectToken === activeSeq - 1.U) { collectionClosed := true.B }
        .otherwise { collectToken := collectToken + 1.U }
    }
  }

  when(state === sWait && tokenReady(workRow)) {
    workHead := 0.U
    keyToken := 0.U
    state := sScoreRead
  }

  val selectedKvHead = workHead / p.kvGroupSize.U
  val qReadAddr = AccMath.boundedIndex(workRow * p.qHeads.U + workHead, qHeadDepth)
  val kvReadAddr = AccMath.boundedIndex(keyToken * p.kvHeads.U + selectedKvHead, kvHeadDepth)
  qMemory.io.readEn := state === sScoreRead
  qMemory.io.readAddr := qReadAddr
  kMemory.io.readEn := state === sScoreRead
  kMemory.io.readAddr := kvReadAddr
  when(state === sScoreRead) { state := sScoreCapture }
  when(state === sScoreCapture) {
    qHeadReg := qMemory.io.readData
    kHeadReg := kMemory.io.readData
    scoreDimension := 0.U
    scoreAccReg := PhysicalMath.fp32Zero
    state := sScoreMulIssue
  }

  val qHeadValues = qHeadReg.asTypeOf(Vec(p.headDim, UInt(p.elemBits.W)))
  val kHeadValues = kHeadReg.asTypeOf(Vec(p.headDim, UInt(p.elemBits.W)))
  val scoreMultipliers = Seq.tabulate(p.scoreLanes) { lane =>
    val mul = Module(new PhysicalFp32MulPipeline(1))
    val dimension = scoreDimension + lane.U
    val index = AccMath.boundedIndex(dimension, p.headDim)
    val active = dimension < p.headDim.U
    mul.io.in.bits.a := Mux(active, PhysicalMath.toFp32(qHeadValues(index), p.elemBits), PhysicalMath.fp32Zero)
    mul.io.in.bits.b := Mux(active, PhysicalMath.toFp32(kHeadValues(index), p.elemBits), PhysicalMath.fp32Zero)
    mul.io.in.bits.tag := 0.U
    mul
  }
  val scoreMulReady = scoreMultipliers.map(_.io.in.ready).reduce(_ && _)
  scoreMultipliers.foreach(_.io.in.valid := state === sScoreMulIssue && scoreMulReady)
  def reduceScore(values: Seq[DecoupledIO[TaggedFp32Result]]): DecoupledIO[TaggedFp32Result] = {
    if (values.size == 1) values.head
    else reduceScore(values.grouped(2).map { pair =>
      val add = Module(new PhysicalFp32AddPipeline(1))
      add.io.in.valid := pair(0).valid && pair(1).valid
      add.io.in.bits.a := pair(0).bits.value
      add.io.in.bits.b := pair(1).bits.value
      add.io.in.bits.tag := 0.U
      pair(0).ready := add.io.in.ready && pair(1).valid
      pair(1).ready := add.io.in.ready && pair(0).valid
      add.io.out
    }.toSeq)
  }
  val scoreTree = reduceScore(scoreMultipliers.map(_.io.out))
  scoreTree.ready := state === sScoreMulWait
  when(state === sScoreMulIssue && scoreMulReady) { state := sScoreMulWait }
  when(scoreTree.fire) {
    scoreProductReg := scoreTree.bits.value
    state := sScoreAccIssue
  }

  val scoreAdder = Module(new PhysicalFp32Add)
  scoreAdder.io.a := scoreAccReg
  scoreAdder.io.b := scoreProductReg
  scoreAdder.io.inValid := state === sScoreAccIssue && scoreAdder.io.inReady
  when(state === sScoreAccIssue && scoreAdder.io.inReady) { state := sScoreAccWait }
  when(state === sScoreAccWait && scoreAdder.io.outValid) {
    scoreAccReg := scoreAdder.io.out
    when(scoreDimension + p.scoreLanes.U >= p.headDim.U) { state := sScoreScaleIssue }
      .otherwise {
        scoreDimension := scoreDimension + p.scoreLanes.U
        state := sScoreMulIssue
      }
  }

  val scoreScale = Module(new PhysicalFp32Mul)
  scoreScale.io.a := scoreAccReg
  scoreScale.io.b := PhysicalMath.fp32Constant(math.pow(p.headDim.toDouble, -0.5))
  scoreScale.io.inValid := state === sScoreScaleIssue && scoreScale.io.inReady
  when(state === sScoreScaleIssue && scoreScale.io.inReady) { state := sScoreScaleWait }
  when(state === sScoreScaleWait && scoreScale.io.outValid) {
    scoreValueReg := scoreScale.io.out
    state := sScoreWrite
  }

  scoreMemory.io.writeEn := state === sScoreWrite
  scoreMemory.io.writeAddr := keyToken
  scoreMemory.io.writeData := scoreValueReg
  scoreMemory.io.readEn := state === sSoftmaxRead && scoreReadIndex <= workRow
  scoreMemory.io.readAddr := scoreReadIndex
  when(state === sScoreWrite) {
    when(keyToken === workRow) {
      scoreReadIndex := 0.U
      state := sContextInit
    }.otherwise {
      keyToken := keyToken + 1.U
      state := sScoreRead
    }
  }

  contextAccMemory.io.writeEn := state === sContextInit || state === sContextAccWrite
  contextAccMemory.io.writeAddr := 0.U
  contextAccMemory.io.writeData := Mux(state === sContextInit, 0.U(contextAccBits.W), contextAccReg)
  contextAccMemory.io.readEn := state === sContextAccRead || state === sContextFinalizeRead
  contextAccMemory.io.readAddr := 0.U
  when(state === sContextInit) { state := sSoftmaxRead }

  val softmax = Module(new Softmax(p.softmax))
  val activeMaskBits = Wire(Vec(p.seqLen, Bool()))
  for (token <- 0 until p.seqLen) { activeMaskBits(token) := token.U < seqLimit }
  softmax.io.cfg := io.cfg
  softmax.io.cfgValid := io.cfgValid
  softmax.io.rowIndex := workRow
  softmax.io.mask := activeMaskBits.asUInt
  softmax.io.in.valid := state === sSoftmaxFeed
  softmax.io.in.bits.data := scoreFeedReg
  softmax.io.in.bits.st := scoreReadIndex === 0.U
  softmax.io.in.bits.addr := scoreReadIndex
  softmax.io.in.bits.last := scoreReadIndex === seqLimit - 1.U
  softmax.io.out.ready := state === sSoftmaxDrain

  when(state === sSoftmaxRead) {
    when(scoreReadIndex <= workRow) { state := sSoftmaxCapture }
      .otherwise {
        scoreFeedReg := PhysicalMath.fp32Zero
        state := sSoftmaxFeed
      }
  }
  when(state === sSoftmaxCapture) {
    scoreFeedReg := scoreMemory.io.readData
    state := sSoftmaxFeed
  }
  when(softmax.io.in.fire) {
    when(scoreReadIndex === seqLimit - 1.U) {
      softmaxOutIndex := 0.U
      state := sSoftmaxDrain
    }.otherwise {
      scoreReadIndex := scoreReadIndex + 1.U
      state := sSoftmaxRead
    }
  }

  vMemory.io.readEn := state === sContextRead
  vMemory.io.readAddr := AccMath.boundedIndex(valueToken * p.kvHeads.U + selectedKvHead, kvHeadDepth)
  when(softmax.io.out.fire) {
    when(softmaxOutIndex <= workRow) {
      probabilityReg := softmax.io.out.bits.data
      valueToken := softmaxOutIndex
      state := sContextRead
    }.elsewhen(softmaxOutIndex === seqLimit - 1.U) {
      state := sContextFinalizeRead
    }.otherwise {
      softmaxOutIndex := softmaxOutIndex + 1.U
    }
  }
  when(state === sContextRead) { state := sContextCapture }
  when(state === sContextCapture) {
    vHeadReg := vMemory.io.readData
    state := sContextMulIssue
  }

  val vHeadValues = vHeadReg.asTypeOf(Vec(p.headDim, UInt(p.elemBits.W)))
  val contextMultipliers = Seq.tabulate(p.headDim) { dimension =>
    val mul = Module(new PhysicalFp32Mul)
    mul.io.a := probabilityReg
    mul.io.b := PhysicalMath.toFp32(vHeadValues(dimension), p.elemBits)
    mul
  }
  val allContextMulReady = contextMultipliers.map(_.io.inReady).reduce(_ && _)
  val contextMulIssue = state === sContextMulIssue && allContextMulReady
  contextMultipliers.foreach(_.io.inValid := contextMulIssue)
  when(contextMulIssue) { state := sContextMulWait }
  val allContextMulValid = VecInit(contextMultipliers.map(_.io.outValid)).asUInt.andR
  when(state === sContextMulWait && allContextMulValid) {
    contextProductReg := VecInit(contextMultipliers.map(_.io.out)).asUInt
    state := sContextAccRead
  }

  when(state === sContextAccRead) { state := sContextAccCapture }
  when(state === sContextAccCapture) {
    contextAccReg := contextAccMemory.io.readData
    state := sContextAccIssue
  }
  val contextAccValues = contextAccReg.asTypeOf(Vec(p.headDim, UInt(32.W)))
  val contextProductValues = contextProductReg.asTypeOf(Vec(p.headDim, UInt(32.W)))
  val contextAdders = Seq.tabulate(p.headDim) { dimension =>
    val add = Module(new PhysicalFp32Add)
    add.io.a := contextAccValues(dimension)
    add.io.b := contextProductValues(dimension)
    add
  }
  val allContextAccReady = contextAdders.map(_.io.inReady).reduce(_ && _)
  val contextAccIssue = state === sContextAccIssue && allContextAccReady
  contextAdders.foreach(_.io.inValid := contextAccIssue)
  when(contextAccIssue) { state := sContextAccWait }
  val allContextAccValid = VecInit(contextAdders.map(_.io.outValid)).asUInt.andR
  when(state === sContextAccWait && allContextAccValid) {
    contextAccReg := VecInit(contextAdders.map(_.io.out)).asUInt
    state := sContextAccWrite
  }
  when(state === sContextAccWrite) {
    when(valueToken === seqLimit - 1.U) { state := sContextFinalizeRead }
      .otherwise {
        softmaxOutIndex := valueToken + 1.U
        state := sSoftmaxDrain
      }
  }

  when(state === sContextFinalizeRead) { state := sContextFinalizeCapture }
  when(state === sContextFinalizeCapture) {
    contextAccReg := contextAccMemory.io.readData
    state := sContextWrite
  }
  val contextAccFinalValues = contextAccReg.asTypeOf(Vec(p.headDim, UInt(32.W)))
  val contextWriteVector = Wire(Vec(p.headDim, UInt(p.elemBits.W)))
  for (dimension <- 0 until p.headDim) {
    contextWriteVector(dimension) := PhysicalMath.fromFp32(contextAccFinalValues(dimension), p.elemBits)
  }
  contextMemory.io.writeEn := state === sContextWrite
  contextMemory.io.writeAddr := AccMath.boundedIndex(workRow * p.qHeads.U + workHead, qHeadDepth)
  contextMemory.io.writeData := contextWriteVector.asUInt
  contextMemory.io.readEn := state === sProjectRead
  contextMemory.io.readAddr := AccMath.boundedIndex(projectToken * p.qHeads.U + projectBeat, qHeadDepth)
  when(state === sContextWrite) {
    when(workHead === (p.qHeads - 1).U) {
      workHead := 0.U
      projectToken := workRow
      projectBeat := 0.U
      state := sProjectWait
    }.otherwise {
      workHead := workHead + 1.U
      keyToken := 0.U
      state := sScoreRead
    }
  }

  val finalProjectToken = projectToken === seqLimit - 1.U
  val successorIndex = Wire(UInt(p.rowBits.W))
  successorIndex := Mux(finalProjectToken, 0.U, projectToken + 1.U)
  when(state === sProjectWait && (finalProjectToken || tokenReady(successorIndex))) { state := sProjectRead }
  when(state === sProjectRead) { state := sProjectCapture }
  when(state === sProjectCapture) {
    projectionWord := contextMemory.io.readData
    state := sProjectFeed
  }

  val outputProjection = Module(new Linear(p.outLinear))
  outputProjection.io.start := false.B
  outputProjection.io.cfg := io.cfg
  outputProjection.io.cfgValid := io.cfgValid
  outputProjection.io.weight <> io.outWeight
  outputProjection.io.bias <> io.outBias
  outputProjection.io.tile <> io.tile
  outputProjection.io.scale.outScale := Mux(p.integerMode.B, io.outOutputScale, PhysicalMath.fp32One)
  outputProjection.io.scale.biasScale := Mux(p.integerMode.B, "h80000000".U(32.W), PhysicalMath.fp32One)
  outputProjection.io.scale.channelScale := io.outChannelScale
  outputProjection.io.scale.channelShift := io.outChannelScaleShift
  outputProjection.io.scale.activationScale := io.outActivationScale
  outputProjection.io.scale.activationShift := io.outActivationScaleShift
  outputProjection.io.scale.outputShift := io.outOutputScaleShift
  outputProjection.io.scale.biasShift := 0.S
  outputProjection.io.in.valid := state === sProjectFeed
  outputProjection.io.in.bits.data := projectionWord
  outputProjection.io.in.bits.st := projectBeat === 0.U
  outputProjection.io.in.bits.addr := projectToken * p.qHeads.U + projectBeat
  outputProjection.io.in.bits.last := projectBeat === (p.qHeads - 1).U
  when(outputProjection.io.in.fire) {
    when(projectBeat === (p.qHeads - 1).U) {
      projectBeat := 0.U
      state := sProjectDrain
    }.otherwise {
      projectBeat := projectBeat + 1.U
      state := sProjectRead
    }
  }

  io.out.valid := outputProjection.io.out.valid && state === sProjectDrain
  io.out.bits := outputProjection.io.out.bits
  outputProjection.io.out.ready := io.out.ready && state === sProjectDrain
  when(outputTokenDone) {
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

  dontTouch(io.mask)
  dontTouch(io.scoreScale)
  dontTouch(io.ctxInvScale)
  dontTouch(io.ctxZeroPoint)
  dontTouch(io.outInvScale)
}

class IntegerAttention(p: AttentionParams) extends Module {
  private val rowBits = log2Ceil(p.seqLen max 2)
  private val kvDepth = p.seqLen * p.kvHeads
  private val qDepth = p.seqLen * p.qHeads
  private val vectorBits = p.headDim * 8
  private val invSqrtQ16 = math.max(1, math.round(65536.0 / math.sqrt(p.headDim.toDouble)).toInt)
  private val expBits = 17
  // Summing N unsigned exp codes needs expBits + ceil(log2(N)) bits; do not
  // size the restoring divider from sequence storage volume (N * expBits).
  private val sumBits = expBits + log2Ceil(p.seqLen max 2)
  // Probabilities are requantized to signed INT8 Q7 before PV. Both PV
  // operands are therefore real signed INT8 values and the context uses the
  // declared INT32 accumulation domain.
  private val accBits = 32
  private val expTable = VecInit(Seq.tabulate(256) { index =>
    BigInt(math.max(0, math.min(65536, math.round(math.exp(-index.toDouble / 16.0) * 65536.0).toInt))).U(expBits.W)
  })

  val io = IO(new Bundle {
    val cfg = Input(new StageConfig(p.seqBits))
    val cfgValid = Input(Bool())
    val in = Flipped(Decoupled(new QKVStreamBeat(p.qkv)))
    val mask = Input(UInt(p.seqLen.W))
    val scoreScale = Input(UInt(32.W))
    val ctxInvScale = Input(UInt(32.W))
    val ctxZeroPoint = Input(UInt(8.W))
    val outInvScale = Input(UInt(32.W))
    val outChannelScale = Input(Vec(p.outLinear.outDim, UInt(32.W)))
    val outChannelScaleShift = Input(Vec(p.outLinear.outDim, SInt(8.W)))
    val outActivationScale = Input(UInt(32.W))
    val outActivationScaleShift = Input(SInt(8.W))
    val outOutputScale = Input(UInt(32.W))
    val outOutputScaleShift = Input(SInt(8.W))
    val outWeight = Flipped(Decoupled(new WeightWrite(p.outLinear.weightTileBits, p.outLinear.weightAddrBits)))
    val outBias = Flipped(Decoupled(new WeightWrite(p.outLinear.biasBeatBits, log2Ceil(p.outLinear.outBeats max 2))))
    val tile = new WeightTileServiceIO(p.refillDataWidthBits)
    val out = Decoupled(new StreamBeat(StreamSpec(p.outLinear.outputBeatBits, p.outLinear.outputAddrBits)))
  })

  private val qMemory = Module(new PhysicalSimpleDualPortMemory(qDepth, vectorBits, "cache"))
  private val kMemory = Module(new PhysicalSimpleDualPortMemory(kvDepth, vectorBits, "cache"))
  private val vMemory = Module(new PhysicalSimpleDualPortMemory(kvDepth, vectorBits, "cache"))
  private val contextMemory = Module(new PhysicalSimpleDualPortMemory(qDepth, vectorBits, "activation"))
  private val qCollectReg = RegInit(0.U(vectorBits.W))
  private val kCollectReg = RegInit(0.U(vectorBits.W))
  private val vCollectReg = RegInit(0.U(vectorBits.W))
  private val qCollect = qCollectReg.asTypeOf(Vec(p.headDim, UInt(8.W)))
  private val kCollect = kCollectReg.asTypeOf(Vec(p.headDim, UInt(8.W)))
  private val vCollect = vCollectReg.asTypeOf(Vec(p.headDim, UInt(8.W)))
  private val nextQ = Wire(Vec(p.headDim, UInt(8.W)))
  private val nextK = Wire(Vec(p.headDim, UInt(8.W)))
  private val nextV = Wire(Vec(p.headDim, UInt(8.W)))
  nextQ := qCollect
  nextK := kCollect
  nextV := vCollect

  private val sWait :: sQRead :: sQCapture :: sScore :: sSoftmax :: sVRead :: sVCapture :: sPV :: sPVFinish :: sProjectRead :: sProjectCapture :: sProjectFeed :: sProjectDrain :: Nil = Enum(13)
  private val state = RegInit(sWait)
  private val collectToken = RegInit(0.U(rowBits.W))
  private val row = RegInit(0.U(rowBits.W))
  private val head = RegInit(0.U(p.qkv.headBits.W))
  private val key = RegInit(0.U(rowBits.W))
  private val projectHead = RegInit(0.U(p.qkv.headBits.W))
  private val tokenReady = RegInit(0.U(p.seqLen.W))
  private val collectionClosed = RegInit(false.B)
  private val qHeadReg = Reg(UInt(vectorBits.W))
  private val kHeadReg = Reg(UInt(vectorBits.W))
  private val vHeadReg = Reg(UInt(vectorBits.W))
  private val scores = Reg(Vec(p.seqLen, SInt(32.W)))
  private val probabilities = Reg(Vec(p.seqLen, UInt(8.W)))
  private val contextAcc = Reg(Vec(p.headDim, SInt(accBits.W)))
  private val valueToken = RegInit(0.U(rowBits.W))
  private val projectWord = Reg(UInt(vectorBits.W))
  private val seqLimit = RegInit(p.seqLen.U(p.seqBits.W))
  private val activeSeq = Mux(io.cfgValid && io.cfg.seqlen =/= 0.U && io.cfg.seqlen <= p.seqLen.U, io.cfg.seqlen, seqLimit)
  when(io.cfgValid) { seqLimit := activeSeq }

  val fields = io.in.bits.data.asTypeOf(Vec(3 * p.qkvElemsPerBeat, UInt(8.W)))
  val finalHeadBeat = io.in.bits.addr === (p.qkv.headBeats - 1).U
  val kvHead = io.in.bits.head / p.kvGroupSize.U
  for (lane <- 0 until p.qkvElemsPerBeat) {
    val dimension = io.in.bits.addr * p.qkvElemsPerBeat.U + lane.U
    val index = AccMath.boundedIndex(dimension, p.headDim)
    nextQ(index) := fields(lane)
    nextK(index) := fields(p.qkvElemsPerBeat + lane)
    nextV(index) := fields(2 * p.qkvElemsPerBeat + lane)
  }
  io.in.ready := !collectionClosed
  qMemory.io.writeEn := io.in.fire && finalHeadBeat
  qMemory.io.writeAddr := AccMath.boundedIndex(collectToken * p.qHeads.U + io.in.bits.head, qDepth)
  qMemory.io.writeData := nextQ.asUInt
  kMemory.io.writeEn := io.in.fire && finalHeadBeat
  kMemory.io.writeAddr := AccMath.boundedIndex(collectToken * p.kvHeads.U + kvHead, kvDepth)
  kMemory.io.writeData := nextK.asUInt
  vMemory.io.writeEn := io.in.fire && finalHeadBeat
  vMemory.io.writeAddr := AccMath.boundedIndex(collectToken * p.kvHeads.U + kvHead, kvDepth)
  vMemory.io.writeData := nextV.asUInt
  val tokenDone = io.in.fire && io.in.bits.last
  when(io.in.fire) {
    qCollectReg := nextQ.asUInt
    kCollectReg := nextK.asUInt
    vCollectReg := nextV.asUInt
    when(tokenDone) {
      tokenReady := tokenReady | (1.U(p.seqLen.W) << collectToken)
      when(collectToken === activeSeq - 1.U) { collectionClosed := true.B }
        .otherwise { collectToken := collectToken + 1.U }
    }
  }
  when(state === sWait && tokenReady(row)) {
    head := 0.U
    key := 0.U
    state := sQRead
  }

  private val computeKvHead = head / p.kvGroupSize.U
  qMemory.io.readEn := state === sQRead
  qMemory.io.readAddr := AccMath.boundedIndex(row * p.qHeads.U + head, qDepth)
  kMemory.io.readEn := state === sQRead
  kMemory.io.readAddr := AccMath.boundedIndex(key * p.kvHeads.U + computeKvHead, kvDepth)
  when(state === sQRead) { state := sQCapture }
  when(state === sQCapture) {
    qHeadReg := qMemory.io.readData
    kHeadReg := kMemory.io.readData
    state := sScore
  }

  val qValues = qHeadReg.asTypeOf(Vec(p.headDim, SInt(8.W)))
  val kValues = kHeadReg.asTypeOf(Vec(p.headDim, SInt(8.W)))
  val dotProducts = (0 until p.headDim).map { dimension =>
    (qValues(dimension) * kValues(dimension)).pad(32)
  }
  val dot = dotProducts.reduce(_ + _)
  val scaledDot = (dot * invSqrtQ16.S(32.W)) >> 16
  when(state === sScore) {
    scores(AccMath.boundedIndex(key, p.seqLen)) := scaledDot.asUInt(31, 0).asSInt
    when(key === row) { state := sSoftmax }
      .otherwise { key := key + 1.U; state := sQRead }
  }

  val minimumScore = (-2147483648L).S(32.W)
  // One transaction owns scores, row and head until probability commit.
  // Collection remains independent and can continue writing the Q/K/V caches.
  private val softmaxBusy = RegInit(false.B)
  private val softmaxLaunch = state === sSoftmax && !softmaxBusy
  private val explicitMaskEnabled = io.mask.orR
  private val keyAllowed = (0 until p.seqLen).map { index =>
    (index.U <= row) && (!explicitMaskEnabled || io.mask(index))
  }
  private val allowedReg = Reg(Vec(p.seqLen, Bool()))
  when(softmaxLaunch) {
    allowedReg := VecInit(keyAllowed)
    softmaxBusy := true.B
  }

  // Register every balanced comparison level, including odd-node forwarding.
  // These are internal cuts in the maximum operator, not boundary delays.
  def maximumPipeline(values: Seq[SInt], valid: Bool): (SInt, Bool) = {
    if (values.size == 1) (values.head, valid)
    else {
      val next = values.grouped(2).map { pair =>
        RegNext(if (pair.size == 1) pair.head
          else Mux(pair(0) > pair(1), pair(0), pair(1)))
      }.toSeq
      maximumPipeline(next, RegNext(valid, false.B))
    }
  }
  val maskedScores = (0 until p.seqLen).map { index =>
    Mux(keyAllowed(index), scores(index), minimumScore)
  }
  val maximumStage = maximumPipeline(maskedScores, softmaxLaunch)
  val maximumScore = maximumStage._1
  val expValues = Reg(Vec(p.seqLen, UInt(expBits.W)))
  when(maximumStage._2) {
    for (index <- 0 until p.seqLen) {
      // Retain the original 32-bit subtraction and table-index clipping.
      val difference = Mux(allowedReg(index), (maximumScore - scores(index)).asUInt, 0.U(32.W))
      val tableIndexWide = difference >> 4
      val tableIndex = Mux(tableIndexWide > 255.U, 255.U(8.W), tableIndexWide(7, 0))
      expValues(index) := Mux(allowedReg(index), expTable(tableIndex), 0.U(expBits.W))
    }
  }
  val expValid = RegNext(maximumStage._2, false.B)

  def sumPipeline(values: Seq[UInt], valid: Bool): (UInt, Bool) = {
    if (values.size == 1) (values.head, valid)
    else {
      val next = values.grouped(2).map { pair =>
        RegNext(if (pair.size == 1) pair.head else pair(0) + pair(1))
      }.toSeq
      sumPipeline(next, RegNext(valid, false.B))
    }
  }
  val sumStage = sumPipeline((0 until p.seqLen).map(i => expValues(i).pad(sumBits)), expValid)
  val safeExpSum = Mux(sumStage._1 === 0.U, 1.U(sumBits.W), sumStage._1)

  // Fully spatial restoring division: one compare/subtract per register
  // stage. Exactly floor(2^31 / safeExpSum), with no serialized token loop.
  // The denominator and valid advance with the partial remainder/quotient.
  var divideDenominator: UInt = safeExpSum
  var divideRemainder: UInt = 0.U((sumBits + 1).W)
  var divideQuotient: UInt = 0.U(32.W)
  var divideValid: Bool = sumStage._2
  for (bit <- (0 until 32).reverse) {
    val numeratorBit = (if (bit == 31) 1 else 0).U(1.W)
    val shiftedRemainder = Cat(divideRemainder(sumBits - 1, 0), numeratorBit)
    val denominatorWide = Cat(0.U(1.W), divideDenominator)
    val takeBit = shiftedRemainder >= denominatorWide
    val nextRemainder = Mux(takeBit, shiftedRemainder - denominatorWide, shiftedRemainder)
    val nextQuotient = Cat(divideQuotient(30, 0), takeBit)
    divideRemainder = RegNext(nextRemainder)
    divideQuotient = RegNext(nextQuotient)
    divideDenominator = RegNext(divideDenominator)
    divideValid = RegNext(divideValid, false.B)
  }
  val reciprocalQ31 = divideQuotient
  // Exponentials remain owned by this transaction throughout division.
  val probabilityProducts = Reg(Vec(p.seqLen, UInt(49.W)))
  when(divideValid) {
    for (index <- 0 until p.seqLen) {
      probabilityProducts(index) := expValues(index) * reciprocalQ31
    }
  }
  val probabilityProductsValid = RegNext(divideValid, false.B)
  when(state === sSoftmax && probabilityProductsValid) {
    for (index <- 0 until p.seqLen) {
      // Preserve full Q31 product, nearest-even Q7 rounding and saturation.
      val product = probabilityProducts(index)
      val probabilityBase = product(48, 24)
      val probabilityRemainder = product(23, 0)
      val probabilityHalf = (BigInt(1) << 23).U(24.W)
      val probabilityRoundUp = probabilityRemainder > probabilityHalf ||
        (probabilityRemainder === probabilityHalf && probabilityBase(0))
      val probabilityRounded = probabilityBase.pad(26) + probabilityRoundUp.asUInt
      probabilities(index) := Mux(
        index.U <= row,
        Mux(probabilityRounded > 127.U, 127.U(8.W), probabilityRounded(7, 0)),
        0.U(8.W)
      )
    }
    softmaxBusy := false.B
    for (dimension <- 0 until p.headDim) { contextAcc(dimension) := 0.S(accBits.W) }
    valueToken := 0.U
    state := sVRead
  }

  vMemory.io.readEn := state === sVRead
  vMemory.io.readAddr := AccMath.boundedIndex(valueToken * p.kvHeads.U + computeKvHead, kvDepth)
  when(state === sVRead) { state := sVCapture }
  when(state === sVCapture) {
    vHeadReg := vMemory.io.readData
    state := sPV
  }
  val vValues = vHeadReg.asTypeOf(Vec(p.headDim, SInt(8.W)))
  when(state === sPV) {
    val probability = probabilities(AccMath.boundedIndex(valueToken, p.seqLen)).asSInt
    for (dimension <- 0 until p.headDim) {
      // Signed INT8 value times signed INT8 Q7 probability; sign-extend the
      // genuine 16-bit product into the INT32 context accumulator.
      val product = vValues(dimension) * probability
      contextAcc(dimension) := contextAcc(dimension) + product.pad(accBits)
    }
    when(valueToken === row) { state := sPVFinish }
      .otherwise { valueToken := valueToken + 1.U; state := sVRead }
  }

  val contextResult = Wire(Vec(p.headDim, UInt(8.W)))
  for (dimension <- 0 until p.headDim) {
    // PV accumulated in Q7. Round the arithmetic right shift to nearest-even
    // before signed INT8 saturation and storage in the activation domain.
    val value = contextAcc(dimension)
    val quotient = (value >> 7).asSInt
    val remainder = value.asUInt(6, 0)
    val halfway = 64.U(7.W)
    val roundUp = remainder > halfway || (remainder === halfway && quotient.asUInt(0))
    val rounded = quotient + roundUp.asUInt.zext
    val clipped = Mux(rounded > 127.S, 127.S(32.W), Mux(rounded < (-128).S, (-128).S(32.W), rounded))
    contextResult(dimension) := AccMath.resizeSignedToUInt(clipped, 8)
  }
  contextMemory.io.writeEn := state === sPVFinish
  contextMemory.io.writeAddr := AccMath.boundedIndex(row * p.qHeads.U + head, qDepth)
  contextMemory.io.writeData := contextResult.asUInt
  when(state === sPVFinish) {
    when(head === (p.qHeads - 1).U) {
      projectHead := 0.U
      state := sProjectRead
    }.otherwise {
      head := head + 1.U
      key := 0.U
      state := sQRead
    }
  }

  contextMemory.io.readEn := state === sProjectRead
  contextMemory.io.readAddr := AccMath.boundedIndex(row * p.qHeads.U + projectHead, qDepth)
  when(state === sProjectRead) { state := sProjectCapture }
  when(state === sProjectCapture) {
    projectWord := contextMemory.io.readData
    state := sProjectFeed
  }
  private val outputProjection = Module(new Linear(p.outLinear))
  outputProjection.io.start := false.B
  outputProjection.io.cfg := io.cfg
  outputProjection.io.cfgValid := io.cfgValid
  outputProjection.io.weight <> io.outWeight
  outputProjection.io.bias <> io.outBias
  outputProjection.io.tile <> io.tile
  outputProjection.io.scale.outScale := io.outOutputScale
  outputProjection.io.scale.biasScale := "h80000000".U
  outputProjection.io.scale.channelScale := io.outChannelScale
  outputProjection.io.scale.channelShift := io.outChannelScaleShift
  outputProjection.io.scale.activationScale := io.outActivationScale
  outputProjection.io.scale.activationShift := io.outActivationScaleShift
  outputProjection.io.scale.outputShift := io.outOutputScaleShift
  outputProjection.io.scale.biasShift := 0.S
  outputProjection.io.in.valid := state === sProjectFeed
  outputProjection.io.in.bits.data := projectWord
  outputProjection.io.in.bits.st := projectHead === 0.U
  outputProjection.io.in.bits.addr := row * p.qHeads.U + projectHead
  outputProjection.io.in.bits.last := projectHead === (p.qHeads - 1).U
  when(outputProjection.io.in.fire) {
    when(projectHead === (p.qHeads - 1).U) { state := sProjectDrain }
      .otherwise { projectHead := projectHead + 1.U; state := sProjectRead }
  }
  io.out.valid := outputProjection.io.out.valid
  io.out.bits := outputProjection.io.out.bits
  outputProjection.io.out.ready := io.out.ready
  when(io.out.fire && io.out.bits.last && state === sProjectDrain) {
    tokenReady := tokenReady & ~(1.U(p.seqLen.W) << row)
    when(row === activeSeq - 1.U) {
      row := 0.U
      collectToken := 0.U
      collectionClosed := false.B
      state := sWait
    }.otherwise {
      row := row + 1.U
      state := sWait
    }
  }
  dontTouch(io.mask)
  dontTouch(io.scoreScale)
  dontTouch(io.ctxInvScale)
  dontTouch(io.ctxZeroPoint)
  dontTouch(io.outInvScale)
}

class Attention(p: AttentionParams) extends Module {
  val io = IO(new Bundle {
    val outChannelScaleShift = Input(Vec(p.outLinear.outDim, SInt(8.W)))
    val outActivationScaleShift = Input(SInt(8.W))
    val outOutputScaleShift = Input(SInt(8.W))
    val cfg = Input(new StageConfig(p.seqBits))
    val cfgValid = Input(Bool())
    val in = Flipped(Decoupled(new QKVStreamBeat(p.qkv)))
    val mask = Input(UInt(p.seqLen.W))
    val scoreScale = Input(UInt(32.W))
    val ctxInvScale = Input(UInt(32.W))
    val ctxZeroPoint = Input(UInt(8.W))
    val outInvScale = Input(UInt(32.W))
    val outChannelScale = Input(Vec(p.outLinear.outDim, UInt(32.W)))
    val outActivationScale = Input(UInt(32.W))
    val outOutputScale = Input(UInt(32.W))
    val outWeight = Flipped(Decoupled(new WeightWrite(p.outLinear.weightTileBits, p.outLinear.weightAddrBits)))
    val outBias = Flipped(Decoupled(new WeightWrite(p.outLinear.biasBeatBits, log2Ceil(p.outLinear.outBeats max 2))))
    val tile = new WeightTileServiceIO(p.refillDataWidthBits)
    val out = Decoupled(new StreamBeat(StreamSpec(p.outLinear.outputBeatBits, p.outLinear.outputAddrBits)))
  })

  if (p.integerMode) {
    val core = Module(new IntegerAttention(p))
    core.io.outChannelScaleShift := io.outChannelScaleShift
    core.io.outActivationScaleShift := io.outActivationScaleShift
    core.io.outOutputScaleShift := io.outOutputScaleShift
    core.io.cfg := io.cfg
    core.io.cfgValid := io.cfgValid
    core.io.in <> io.in
    core.io.mask := io.mask
    core.io.scoreScale := io.scoreScale
    core.io.ctxInvScale := io.ctxInvScale
    core.io.ctxZeroPoint := io.ctxZeroPoint
    core.io.outInvScale := io.outInvScale
    core.io.outChannelScale := io.outChannelScale
    core.io.outActivationScale := io.outActivationScale
    core.io.outOutputScale := io.outOutputScale
    core.io.outWeight <> io.outWeight
    core.io.outBias <> io.outBias
    core.io.tile <> io.tile
    io.out <> core.io.out
  } else {
    val core = Module(new FloatingAttention(p))
    core.io.outChannelScaleShift := io.outChannelScaleShift
    core.io.outActivationScaleShift := io.outActivationScaleShift
    core.io.outOutputScaleShift := io.outOutputScaleShift
    core.io.cfg := io.cfg
    core.io.cfgValid := io.cfgValid
    core.io.in <> io.in
    core.io.mask := io.mask
    core.io.scoreScale := io.scoreScale
    core.io.ctxInvScale := io.ctxInvScale
    core.io.ctxZeroPoint := io.ctxZeroPoint
    core.io.outInvScale := io.outInvScale
    core.io.outChannelScale := io.outChannelScale
    core.io.outActivationScale := io.outActivationScale
    core.io.outOutputScale := io.outOutputScale
    core.io.outWeight <> io.outWeight
    core.io.outBias <> io.outBias
    core.io.tile <> io.tile
    io.out <> core.io.out
  }
}

class AttentionMHA(p: AttentionParams) extends Attention(p)
class AttentionGQA(p: AttentionParams) extends Attention(p)
class AttentionMQA(p: AttentionParams) extends Attention(p)
