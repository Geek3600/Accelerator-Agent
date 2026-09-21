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
  computeArrayCols: Int = 0
) {
  require(hiddenSize == qHeads * headDim, "attention hidden size must equal qHeads * headDim")
  require(qHeads > 0 && kvHeads > 0 && qHeads % kvHeads == 0, "invalid GQA head grouping")
  require(headDim > 0 && seqLen > 0, "attention dimensions must be positive")
  require(elemBits == 16, "the immutable attention internal element type is IEEE FP16")
  require(hiddenSize % lanes == 0, "hiddenSize must be divisible by output lanes")
  require(headDim % qkvElemsPerBeat == 0, "headDim must align to QKV stream beats")

  val qkv: QKVProjectionParams = QKVProjectionParams(
    hiddenSize, qHeads, kvHeads, headDim, lanes, elemBits, qkvElemsPerBeat, batchSize, seqLen,
    computeArrayRows = computeArrayRows, computeArrayCols = computeArrayCols
  )
  val qDim: Int = qHeads * headDim
  val kDim: Int = kvHeads * headDim
  val kvGroupSize: Int = qHeads / kvHeads
  val seqBits: Int = log2Ceil(seqLen + 1 max 2)
  val rowBits: Int = log2Ceil(seqLen max 2)
  val headVectorBits: Int = headDim * elemBits
  val headAddrBits: Int = log2Ceil(qHeads max 2)
  val softmax: SoftmaxParams = SoftmaxParams(seqLen, lanes = 1, elemBits = 32, batchSize = seqLen * qHeads, causal = true, slidingWindow = 0)
  val outLinear: LinearParams = LinearParams(
    qDim,
    hiddenSize,
    headDim,
    lanes,
    elemBits,
    32,
    32,
    seqLen,
    seqLen,
    hasBias = outHasBias,
    weightRole = outWeightRole,
    biasRole = outBiasRole,
    computeArrayRows = computeArrayRows,
    computeArrayCols = computeArrayCols
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
    val outBias = Flipped(Decoupled(new WeightWrite(p.outLinear.biasBeatBits, log2Ceil(p.outLinear.outBeats max 2))))
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
  val scoreDimension = RegInit(0.U(log2Ceil(p.headDim max 2).W))
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
  val selectedDimension = AccMath.boundedIndex(scoreDimension, p.headDim)
  val scoreMultiplier = Module(new PhysicalFp32Mul)
  scoreMultiplier.io.a := PhysicalMath.toFp32(qHeadValues(selectedDimension), p.elemBits)
  scoreMultiplier.io.b := PhysicalMath.toFp32(kHeadValues(selectedDimension), p.elemBits)
  scoreMultiplier.io.inValid := state === sScoreMulIssue && scoreMultiplier.io.inReady
  when(state === sScoreMulIssue && scoreMultiplier.io.inReady) { state := sScoreMulWait }
  when(state === sScoreMulWait && scoreMultiplier.io.outValid) {
    scoreProductReg := scoreMultiplier.io.out
    state := sScoreAccIssue
  }

  val scoreAdder = Module(new PhysicalFp32Add)
  scoreAdder.io.a := scoreAccReg
  scoreAdder.io.b := scoreProductReg
  scoreAdder.io.inValid := state === sScoreAccIssue && scoreAdder.io.inReady
  when(state === sScoreAccIssue && scoreAdder.io.inReady) { state := sScoreAccWait }
  when(state === sScoreAccWait && scoreAdder.io.outValid) {
    scoreAccReg := scoreAdder.io.out
    when(scoreDimension === (p.headDim - 1).U) { state := sScoreScaleIssue }
      .otherwise {
        scoreDimension := scoreDimension + 1.U
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
  outputProjection.io.scale.outScale := PhysicalMath.fp32One
  outputProjection.io.scale.biasScale := PhysicalMath.fp32One
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

class AttentionMHA(p: AttentionParams) extends Attention(p)
class AttentionGQA(p: AttentionParams) extends Attention(p)
class AttentionMQA(p: AttentionParams) extends Attention(p)
