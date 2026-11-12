package spatialaccagent.templates

import chisel3._
import chisel3.util._

final case class LinearParams(
  inDim: Int,
  outDim: Int,
  inLanes: Int = 8,
  outLanes: Int = 8,
  elemBits: Int = 16,
  weightBits: Int = 0,
  integerMode: Boolean = false,
  accBits: Int = 32,
  outputBits: Int = 16,
  batchSize: Int = 16,
  maxSeqLen: Int = 16,
  hasBias: Boolean = true,
  fusedActivation: String = "none",
  weightRole: String = "weight",
  biasRole: String = "weight_bias",
  computeArrayRows: Int = 0,
  computeArrayCols: Int = 0,
  cacheTileWords: Int = PhysicalImplementation.resolveCacheTileWords(256),
  cacheTileCount: Int = PhysicalImplementation.resolveCacheTileCount(2),
  refillDataWidthBits: Int = PhysicalImplementation.resolveRefillDataWidthBits(512),
  crossTokenReuseTokens: Int = PhysicalImplementation.resolveCrossTokenReuseTokens(16)
) {
  require(inDim > 0 && outDim > 0, "linear dimensions must be positive")
  require(batchSize > 0, "batchSize must be positive")
  require(inDim % inLanes == 0, "inDim must be divisible by inLanes")
  require(outDim % outLanes == 0, "outDim must be divisible by outLanes")
  val matrixWeightBits: Int = if (weightBits == 0) elemBits else weightBits
  if (integerMode) {
    require(elemBits == 8, "integer Linear activations must be signed INT8")
    require(matrixWeightBits == 4, "integer Linear matrix weights must be signed INT4")
    require(accBits == 32, "integer Linear accumulation must be signed INT32")
    require(outputBits == 8 || outputBits == 32, "integer Linear output must be INT8 or INT32")
  } else {
    require(elemBits == 16 || elemBits == 32, "FP Linear inputs and weights must be IEEE FP16 or FP32")
    require(matrixWeightBits == elemBits, "FP Linear weight width must match its FP element width")
    require(accBits == 32, "FP Linear accumulation must use FP32")
    require(outputBits == 16 || outputBits == 32, "FP Linear output must be IEEE FP16 or FP32")
  }
  require(fusedActivation == "none" || fusedActivation == "relu", "unsupported fused activation")
  require(weightRole == "weight" || weightRole.startsWith("weight_"), s"invalid physical weight role: $weightRole")
  require(biasRole == "weight" || biasRole.startsWith("weight_"), s"invalid physical bias role: $biasRole")
  val macRows: Int = if (computeArrayRows == 0) outLanes else computeArrayRows
  val macCols: Int = if (computeArrayCols == 0) inLanes else computeArrayCols
  val wideInputArray: Boolean = macCols > inLanes
  require(macRows > 0 && macRows <= outLanes && outLanes % macRows == 0, "compute array rows must tile output lanes")
  require(macCols > 0 && (if (wideInputArray) macCols % inLanes == 0 else inLanes % macCols == 0), "compute array cols must tile or combine input lanes")
  require(isPow2(macCols), "compute array cols must be a power of two for the reduction tree")
  require(cacheTileWords > 0, "cacheTileWords must be positive")
  require(cacheTileCount > 0, "cacheTileCount must be positive")
  require(PhysicalImplementation.isSupportedRefillDataWidth(refillDataWidthBits), "refillDataWidthBits must be a physically supported full-beat payload")
  require(crossTokenReuseTokens > 0, "crossTokenReuseTokens must be positive")
  val inBeats: Int = inDim / inLanes
  val outBeats: Int = outDim / outLanes
  require(if (wideInputArray) inDim % macCols == 0 else true, "wide compute columns must divide the input dimension")
  val macTerms: Int = inDim / macCols
  val inputBeatBits: Int = inLanes * elemBits
  val outputBeatBits: Int = outLanes * outputBits
  val weightTileBits: Int = if (wideInputArray) macCols * macRows * matrixWeightBits else inLanes * outLanes * matrixWeightBits
  val weightDepth: Int = if (wideInputArray) macTerms * (outDim / macRows) else inBeats * outBeats
  val inputAddrBits: Int = log2Ceil(batchSize * inBeats max 2)
  val outputAddrBits: Int = log2Ceil(batchSize * outBeats max 2)
  val weightAddrBits: Int = log2Ceil(weightDepth max 2)
  val biasBeatBits: Int = outLanes * accBits
  // This bounded token chunk is both the compute-context capacity and the
  // real cross-token weight-reuse setting. Keep it strictly smaller than a
  // multi-token sequence so inputFull/outputFull never become a whole-sequence
  // barrier; the two ping-pong banks overlap next-chunk ingress and output drain.
  private val maximumNonBarrierChunk: Int = if (maxSeqLen > 1) (maxSeqLen / 2) max 1 else 1
  val tokenTileSize: Int = (batchSize min crossTokenReuseTokens) min maximumNonBarrierChunk
  val accumulatorContexts: Int = tokenTileSize
  val scheduleId: String = "token_interleaved_policy_mac_v3"
}

class Linear(p: LinearParams) extends Module {
  val io = IO(new Bundle {
    val start = Input(Bool())
    val cfg = Input(new StageConfig(log2Ceil(p.maxSeqLen + 1 max 2)))
    val cfgValid = Input(Bool())
    val weight = Flipped(Decoupled(new WeightWrite(p.weightTileBits, p.weightAddrBits)))
    val bias = Flipped(Decoupled(new WeightWrite(p.biasBeatBits, log2Ceil(p.outBeats max 2))))
    val scale = new LinearScalePorts(p.outDim)

    // Generic external-DDR tile service. The cache owns active/shadow tile
    // validity and only emits a request when a compute read misses. Route,
    // layer, base, and stride are runtime metadata supplied by the generated
    // top/board scheduler rather than model-specific constants.
    val tile = new WeightTileServiceIO(p.refillDataWidthBits)

    val in = Flipped(Decoupled(new StreamBeat(StreamSpec(p.inputBeatBits, p.inputAddrBits))))
    val out = Decoupled(new StreamBeat(StreamSpec(p.outputBeatBits, p.outputAddrBits)))
  })

  private val contextBits = log2Ceil(p.accumulatorContexts max 2)
  private val tokenBits = log2Ceil(p.tokenTileSize max 2)
  private val tokenCountBits = log2Ceil((p.tokenTileSize + 1) max 2)
  private val totalTokenBits = log2Ceil((p.batchSize + 1) max 2)
  private val inputWordLanes = if (p.wideInputArray) p.macCols else p.inLanes
  private val inputWords = if (p.wideInputArray) p.macTerms else p.inBeats
  private val inputPartsPerWord = if (p.wideInputArray) p.macCols / p.inLanes else 1
  private val inputChunkDepth = p.tokenTileSize * inputWords
  private val outputChunkDepth = p.tokenTileSize * p.outBeats
  val inputMem = Module(new PhysicalSimpleDualPortMemory(2 * inputChunkDepth, inputWordLanes * p.elemBits, "activation"))
  val outputMem = Module(new PhysicalSimpleDualPortMemory(2 * outputChunkDepth, p.outputBeatBits, "activation"))
  val weightMem = Module(new WeightTileCache(
    logicalDepth = p.weightDepth,
    width = p.weightTileBits,
    logicalAddrBits = p.weightAddrBits,
    cacheTileWords = p.cacheTileWords,
    cacheTileCount = p.cacheTileCount,
    role = p.weightRole,
    refillDataWidthBits = p.refillDataWidthBits
  ))
  val biasMem = if (p.hasBias) {
    Some(Module(new PhysicalSimpleDualPortMemory(p.outBeats, p.biasBeatBits, p.biasRole)))
  } else None

  // Weight ownership is selected by the cache at tile boundaries, not by
  // activation ping-pong parity. Keeping this state only as a compatibility
  // signal allows the generated top to retain the existing ABI while the
  // bounded cache safely hands ownership from active to shadow tiles.
  val computeBank = RegInit(false.B)
  val weightLoadCnt = RegInit(0.U(p.weightAddrBits.W))
  val weightLoaded = RegInit(false.B)
  io.weight.ready := !weightLoaded && io.weight.bits.addr === weightLoadCnt
  weightMem.io.writeEn := io.weight.fire
  weightMem.io.writeAddr := weightLoadCnt
  weightMem.io.writeData := io.weight.bits.data

  // The addressed legacy loader remains available for compatibility while
  // generated tops are being migrated to the generic DDR tile service. Keep
  // the cache request held under backpressure rather than accepting and
  // discarding a miss. These values are generic compatibility bindings, not
  // model-specific matrix constants; the connected generated DDR route will
  // replace them before full architecture promotion.
  weightMem.io.routeId := io.tile.routeId
  weightMem.io.layerIndex := io.tile.layerIndex
  weightMem.io.ddrBaseWord := io.tile.ddrBaseWord
  weightMem.io.routeWordOffset := io.tile.routeWordOffset
  weightMem.io.layerStrideWords := io.tile.layerStrideWords

  // Forward the live request/response channel without tying either side off.
  // The request remains held until the exact board scheduler accepts it, and
  // the cache accepts only ordered responses whose metadata matches the
  // outstanding tile.
  io.tile.request.valid := weightMem.io.tileRequest.valid
  io.tile.request.bits := weightMem.io.tileRequest.bits
  weightMem.io.tileRequest.ready := io.tile.request.ready
  weightMem.io.tileResponse.valid := io.tile.response.valid
  weightMem.io.tileResponse.bits := io.tile.response.bits
  io.tile.response.ready := weightMem.io.tileResponse.ready
  io.tile.tileComplete := weightMem.io.tileComplete
  io.tile.activeBank := weightMem.io.activeBank
  io.tile.shadowBank := weightMem.io.shadowBank
  io.tile.prefetchCommit := weightMem.io.prefetchCommit
  when(io.weight.fire) {
    when(weightLoadCnt === (p.weightDepth - 1).U) {
      weightLoaded := true.B
      weightLoadCnt := 0.U
    }.otherwise {
      weightLoadCnt := weightLoadCnt + 1.U
    }
  }

  val biasLoadCnt = RegInit(0.U(log2Ceil(p.outBeats max 2).W))
  val biasLoaded = RegInit((!p.hasBias).B)
  io.bias.ready := (if (p.hasBias) !biasLoaded && io.bias.bits.addr === biasLoadCnt else false.B)
  biasMem.foreach { memory =>
    memory.io.writeEn := io.bias.fire
    memory.io.writeAddr := biasLoadCnt
    memory.io.writeData := io.bias.bits.data
  }
  when(io.bias.fire) {
    when(biasLoadCnt === (p.outBeats - 1).U) {
      biasLoaded := true.B
      biasLoadCnt := 0.U
    }.otherwise {
      biasLoadCnt := biasLoadCnt + 1.U
    }
  }

  // Matrix weights are fetched by the bounded tile cache as compute requests
  // miss. Bias remains on the addressed legacy stream and is still required
  // before accepting activations when this Linear has a bias port.
  val parametersLoaded = biasLoaded
  val inputFull = RegInit(VecInit(Seq.fill(2)(false.B)))
  val outputFull = RegInit(VecInit(Seq.fill(2)(false.B)))
  val loadBank = RegInit(false.B)
  val writeBank = RegInit(false.B)
  val drainBank = RegInit(false.B)
  val loadBeat = RegInit(0.U(log2Ceil(p.inBeats max 2).W))
  val loadToken = RegInit(0.U(tokenBits.W))
  val loadedTokens = RegInit(0.U(totalTokenBits.W))
  val totalTokens = RegInit(p.batchSize.U(totalTokenBits.W))
  val loadChunkTokens = RegInit(p.tokenTileSize.U(tokenCountBits.W))
  val inputBaseToken = Reg(Vec(2, UInt(totalTokenBits.W)))
  val inputTokenCount = Reg(Vec(2, UInt(tokenCountBits.W)))
  val inputStart = Reg(Vec(2, Bool()))
  val outputBaseToken = Reg(Vec(2, UInt(totalTokenBits.W)))
  val outputTokenCount = Reg(Vec(2, UInt(tokenCountBits.W)))
  val outputStart = Reg(Vec(2, Bool()))
  val inputAssembly = Reg(Vec(inputWordLanes, UInt(p.elemBits.W)))
  val assembledInput = WireDefault(inputAssembly)
  if (p.wideInputArray) {
    val inputBeatValues = io.in.bits.data.asTypeOf(Vec(p.inLanes, UInt(p.elemBits.W)))
    val inputPart = loadBeat % inputPartsPerWord.U
    for (lane <- 0 until p.macCols) {
      when(inputPart === (lane / p.inLanes).U) {
        assembledInput(lane) := inputBeatValues(lane % p.inLanes)
      }
    }
  }

  val requestedTokens = Mux(
    io.cfg.seqlen === 0.U || io.cfg.seqlen > p.batchSize.U,
    p.batchSize.U(totalTokenBits.W),
    io.cfg.seqlen.pad(totalTokenBits)
  )
  val initialChunkTokens = Mux(requestedTokens > p.tokenTileSize.U, p.tokenTileSize.U, requestedTokens)
  val nextLoadedTokens = loadedTokens + loadChunkTokens
  val remainingTokens = totalTokens - nextLoadedTokens

  io.in.ready := parametersLoaded && loadChunkTokens =/= 0.U && !inputFull(loadBank) && !io.start
  inputMem.io.writeEn := io.in.fire && (!p.wideInputArray.B || loadBeat % inputPartsPerWord.U === (inputPartsPerWord - 1).U)
  inputMem.io.writeAddr := loadBank.asUInt * inputChunkDepth.U + loadToken * inputWords.U + loadBeat / inputPartsPerWord.U
  inputMem.io.writeData := (if (p.wideInputArray) assembledInput.asUInt else io.in.bits.data)
  when(io.in.fire) {
    if (p.wideInputArray) { inputAssembly := assembledInput }
    when(loadBeat === 0.U && loadToken === 0.U) { inputStart(loadBank) := io.in.bits.st }
    when(loadBeat === (p.inBeats - 1).U) {
      loadBeat := 0.U
      when(loadToken === loadChunkTokens - 1.U) {
        inputFull(loadBank) := true.B
        inputBaseToken(loadBank) := loadedTokens
        inputTokenCount(loadBank) := loadChunkTokens
        loadedTokens := nextLoadedTokens
        loadChunkTokens := Mux(remainingTokens > p.tokenTileSize.U, p.tokenTileSize.U, remainingTokens)
        loadBank := ~loadBank
        loadToken := 0.U
      }.otherwise { loadToken := loadToken + 1.U }
    }.otherwise { loadBeat := loadBeat + 1.U }
  }

  val sIdle :: sInit :: sRun :: sDrain :: sCapture :: sWrite :: Nil = Enum(6)
  val state = RegInit(sIdle)
  // Do not pin one physical weight bank for an entire matrix. The cache owns
  // the active/shadow handoff at completed tile boundaries, allowing a matrix
  // larger than both banks to stream through bounded storage while compute
  // continues to consume resident tiles.
  // Hold the cache's internally selected physical weight bank for the active
  // compute operation. The legacy computeBank signal tracks activation
  // ping-pong and is retained only for interface compatibility; it must not
  // choose the weight refill destination.
  weightMem.io.computeHold := (state === sRun || state === sDrain)
  weightMem.io.computeBank := computeBank
  val outBeat = RegInit(0.U(log2Ceil(p.outBeats max 2).W))
  val outputGroup = RegInit(0.U(log2Ceil((p.outLanes / p.macRows) max 2).W))
  val computeRows = if (p.wideInputArray) p.macTerms else p.inBeats
  val rowCnt = RegInit(0.U(log2Ceil(computeRows max 2).W))
  val inputGroup = RegInit(0.U(log2Ceil((p.inLanes / p.macCols) max 2).W))
  val scheduleToken = RegInit(0.U(tokenBits.W))
  val readContext = Reg(UInt(contextBits.W))
  val readInputGroup = Reg(UInt(log2Ceil((p.inLanes / p.macCols) max 2).W))
  val readValid = RegInit(false.B)
  val completedOps = RegInit(0.U(log2Ceil((p.tokenTileSize * p.macTerms) max 2).W))
  val computeTokens = Reg(UInt(tokenCountBits.W))
  val computeBaseToken = Reg(UInt(totalTokenBits.W))
  val writeToken = RegInit(0.U(tokenBits.W))
  val partials = Reg(Vec(p.tokenTileSize, Vec(p.macRows, UInt(32.W))))
  val beatValues = Reg(Vec(p.tokenTileSize, Vec(p.outLanes, UInt(32.W))))

  when(state === sIdle && inputFull(computeBank) && !outputFull(writeBank)) {
    computeTokens := inputTokenCount(computeBank)
    computeBaseToken := inputBaseToken(computeBank)
    outputStart(writeBank) := inputStart(computeBank)
    outputBaseToken(writeBank) := inputBaseToken(computeBank)
    outputTokenCount(writeBank) := inputTokenCount(computeBank)
    outBeat := 0.U
    outputGroup := 0.U
    writeToken := 0.U
    state := sInit
  }
  biasMem.foreach { memory =>
    memory.io.readEn := state === sInit
    memory.io.readAddr := outBeat
  }
  val biasValues = biasMem
    .map(_.io.readData.asTypeOf(Vec(p.outLanes, UInt(32.W))))
    .getOrElse(VecInit(Seq.fill(p.outLanes)(PhysicalMath.fp32Zero)))
  when(RegNext(state === sInit, false.B)) {
    for (token <- 0 until p.tokenTileSize; outputLane <- 0 until p.macRows) {
      val outputIndex = AccMath.boundedIndex(outputGroup * p.macRows.U + outputLane.U, p.outLanes)
      val rawBias = if (p.hasBias) biasValues(outputIndex) else 0.U(32.W)
      if (p.integerMode) {
        // Bias is stored in the INT32 accumulator domain. biasScale is an
        // unsigned Q31 multiplier so an exact unity conversion is 0x80000000.
        partials(token)(outputLane) := AccMath.requantizeQ31WithShift(
          rawBias.asSInt,
          io.scale.biasScale,
          io.scale.biasShift,
          p.accBits
        )
      } else {
        partials(token)(outputLane) := rawBias
      }
    }
    when(outputGroup === 0.U) {
      for (token <- 0 until p.tokenTileSize; outputLane <- 0 until p.outLanes) {
        beatValues(token)(outputLane) := 0.U
      }
    }
  }
  when(state === sInit) {
    rowCnt := 0.U
    inputGroup := 0.U
    scheduleToken := 0.U
    completedOps := 0.U
    state := sRun
  }

  val weightValues = if (p.wideInputArray) {
    weightMem.io.readData.asTypeOf(Vec(p.macRows, Vec(p.macCols, UInt(p.matrixWeightBits.W))))
  } else {
    weightMem.io.readData.asTypeOf(Vec(p.outLanes, Vec(p.inLanes, UInt(p.matrixWeightBits.W))))
  }
  val inputValues = inputMem.io.readData.asTypeOf(Vec(inputWordLanes, UInt(p.elemBits.W)))
  val multipliers = Seq.tabulate(p.macRows, p.macCols) { (outputLane, inputLane) =>
    val multiply = Module(new PhysicalLinearMul(
      p.integerMode,
      contextBits,
      activationBits = p.elemBits,
      weightBits = p.matrixWeightBits
    ))
    val inputIndex = if (p.wideInputArray) inputLane.U else readInputGroup * p.macCols.U + inputLane.U
    val outputIndex = outputGroup * p.macRows.U + outputLane.U
    val selectedActivation = inputValues(AccMath.boundedIndex(inputIndex, inputWordLanes))
    val selectedWeight = if (p.wideInputArray) weightValues(outputLane)(inputLane)
      else weightValues(AccMath.boundedIndex(outputIndex, p.outLanes))(AccMath.boundedIndex(inputIndex, p.inLanes))
    if (p.integerMode) {
      multiply.io.in.bits.a := AccMath.resizeSignedToUInt(selectedActivation.asSInt, 32)
      multiply.io.in.bits.b := AccMath.resizeSignedToUInt(selectedWeight.asSInt, 32)
    } else {
      multiply.io.in.bits.a := PhysicalMath.toFp32(selectedActivation, p.elemBits)
      multiply.io.in.bits.b := PhysicalMath.toFp32(selectedWeight, p.matrixWeightBits)
    }
    multiply.io.in.bits.tag := readContext
    multiply
  }
  val allMulReady = multipliers.flatten.map(_.io.in.ready).reduce(_ && _)
  multipliers.flatten.foreach(_.io.in.valid := readValid && allMulReady)
  val advanceRead = !readValid || allMulReady
  val scheduleNeedsWeight = scheduleToken < computeTokens
  // Probe a missing tile to launch its DDR request, but do not advance the
  // token schedule until the requested resident word is actually readable.
  // Active-bank hits remain serviceable during a shadow refill.
  val weightProbe = state === sRun && advanceRead && scheduleNeedsWeight
  val scheduleAdvance = state === sRun && advanceRead &&
    (!scheduleNeedsWeight || weightMem.io.readReady)
  val issueRead = weightProbe && weightMem.io.readReady
  inputMem.io.readEn := issueRead
  inputMem.io.readAddr := computeBank.asUInt * inputChunkDepth.U + scheduleToken * inputWords.U + rowCnt
  weightMem.io.readEn := weightProbe
  weightMem.io.readAddr := (if (p.wideInputArray)
    outBeat * (p.outLanes / p.macRows).U * p.macTerms.U + outputGroup * p.macTerms.U + rowCnt
  else outBeat * p.inBeats.U + rowCnt)
  when(advanceRead) { readValid := issueRead }
  when(issueRead) {
    readContext := AccMath.boundedIndex(scheduleToken, p.tokenTileSize)
    readInputGroup := inputGroup
  }
  when(scheduleAdvance) {
    when(scheduleToken === AccMath.boundedIndex(computeTokens - 1.U, p.tokenTileSize)) {
      scheduleToken := 0.U
    if (p.wideInputArray) {
      when(rowCnt === (p.macTerms - 1).U) { state := sDrain }
        .otherwise { rowCnt := rowCnt + 1.U }
    } else when(inputGroup === (p.inLanes / p.macCols - 1).U) {
      inputGroup := 0.U
      when(rowCnt === (p.inBeats - 1).U) { state := sDrain }
        .otherwise { rowCnt := rowCnt + 1.U }
    }.otherwise { inputGroup := inputGroup + 1.U }
    }.otherwise { scheduleToken := scheduleToken + 1.U }
  }

  def reduceFp32(values: Seq[DecoupledIO[TaggedFp32Result]]): DecoupledIO[TaggedFp32Result] = {
    if (values.size == 1) values.head
    else reduceFp32(values.grouped(2).map { pair =>
      val add = Module(new PhysicalLinearAdd(p.integerMode, contextBits))
      add.io.in.valid := pair(0).valid && pair(1).valid
      add.io.in.bits.a := pair(0).bits.value
      add.io.in.bits.b := pair(1).bits.value
      add.io.in.bits.tag := pair(0).bits.tag
      pair(0).ready := add.io.in.ready && pair(1).valid
      pair(1).ready := add.io.in.ready && pair(0).valid
      add.io.out
    }.toSeq)
  }
  val dots = multipliers.map(row => reduceFp32(row.map(_.io.out)))
  val accumulatorAdds = Seq.fill(p.macRows)(Module(new PhysicalLinearAdd(p.integerMode, contextBits)))
  val allAccReady = accumulatorAdds.map(_.io.in.ready).reduce(_ && _)
  val allDotsValid = dots.map(_.valid).reduce(_ && _)
  val dotContext = AccMath.boundedIndex(dots.head.bits.tag, p.tokenTileSize)
  val accumulate = (state === sRun || state === sDrain) && allDotsValid && allAccReady
  for (outputLane <- 0 until p.macRows) {
    val add = accumulatorAdds(outputLane)
    dots(outputLane).ready := accumulate
    add.io.in.valid := accumulate
    add.io.in.bits.a := partials(dotContext)(outputLane)
    add.io.in.bits.b := dots(outputLane).bits.value
    add.io.in.bits.tag := dotContext
  }
  val allAccValid = accumulatorAdds.map(_.io.out.valid).reduce(_ && _)
  accumulatorAdds.foreach(_.io.out.ready := (state === sRun || state === sDrain) && allAccValid)
  when(allAccValid && (state === sRun || state === sDrain)) {
    val resultContext = AccMath.boundedIndex(accumulatorAdds.head.io.out.bits.tag, p.tokenTileSize)
    for (outputLane <- 0 until p.macRows) {
      partials(resultContext)(outputLane) := accumulatorAdds(outputLane).io.out.bits.value
    }
    completedOps := completedOps + 1.U
    when(completedOps === computeTokens * p.macTerms.U - 1.U) { state := sCapture }
  }
  val lastOutputGroup = outputGroup === (p.outLanes / p.macRows - 1).U
  when(state === sCapture) {
    for (token <- 0 until p.tokenTileSize; outputLane <- 0 until p.macRows) {
      val outputIndex = AccMath.boundedIndex(outputGroup * p.macRows.U + outputLane.U, p.outLanes)
      beatValues(token)(outputIndex) := partials(token)(outputLane)
    }
    when(lastOutputGroup) {
      writeToken := 0.U
      state := sWrite
    }.otherwise {
      outputGroup := outputGroup + 1.U
      state := sInit
    }
  }
  when(state === sWrite) {
    when(writeToken === computeTokens - 1.U) {
      writeToken := 0.U
      when(outBeat === (p.outBeats - 1).U) {
        inputFull(computeBank) := false.B
        computeBank := ~computeBank
        outputFull(writeBank) := true.B
        writeBank := ~writeBank
        state := sIdle
      }.otherwise {
        outBeat := outBeat + 1.U
        outputGroup := 0.U
        state := sInit
      }
    }.otherwise { writeToken := writeToken + 1.U }
  }
  val outputValues = Wire(Vec(p.outLanes, UInt(p.outputBits.W)))
  for (outputLane <- 0 until p.outLanes) {
    val value = if (p.tokenTileSize == 1) beatValues(0)(outputLane) else beatValues(writeToken)(outputLane)
    if (p.integerMode) {
      val activated = if (p.fusedActivation == "relu") Mux(value(31), 0.U(32.W), value) else value
      val channelIndex = AccMath.boundedIndex(outputGroup * p.macRows.U + outputLane.U, p.outDim)
      val channelMultiplier = Mux(
        io.scale.channelScale(channelIndex) === 0.U,
        "h80000000".U(32.W),
        io.scale.channelScale(channelIndex)
      )
      val activationMultiplier = Mux(
        io.scale.activationScale === 0.U,
        "h80000000".U(32.W),
        io.scale.activationScale
      )
      val outputMultiplier = Mux(io.scale.outScale === 0.U, "h80000000".U(32.W), io.scale.outScale)
      val combinedShift = io.scale.channelShift(channelIndex).pad(10) +
        io.scale.activationShift.pad(10) + io.scale.outputShift.pad(10)
      outputValues(outputLane) := AccMath.requantizeQ31WithShift(
        activated.asSInt,
        AccMath.composeQ31Scales(channelMultiplier, activationMultiplier, outputMultiplier),
        combinedShift,
        p.outputBits
      )
    } else {
      val isNan = value(30, 23).andR && value(22, 0).orR
      val activated = if (p.fusedActivation == "relu") Mux(value(31) && !isNan, PhysicalMath.fp32Zero, value) else value
      outputValues(outputLane) := PhysicalMath.fromFp32(activated, p.outputBits)
    }
  }
  outputMem.io.writeEn := state === sWrite
  outputMem.io.writeAddr := writeBank.asUInt * outputChunkDepth.U + writeToken * p.outBeats.U + outBeat
  outputMem.io.writeData := outputValues.asUInt

  val drainBeat = RegInit(0.U(log2Ceil(p.outBeats max 2).W))
  val drainToken = RegInit(0.U(tokenBits.W))
  val drainLastIssued = RegInit(false.B)
  val outputValid = RegInit(false.B)
  val outputMeta = Reg(new StreamBeat(StreamSpec(p.outputBeatBits, p.outputAddrBits)))
  val advanceOutput = !outputValid || io.out.ready
  val issueOutputRead = outputFull(drainBank) && !drainLastIssued && advanceOutput
  outputMem.io.readEn := issueOutputRead
  outputMem.io.readAddr := drainBank.asUInt * outputChunkDepth.U + drainToken * p.outBeats.U + drainBeat
  io.out.valid := outputValid
  io.out.bits := outputMeta
  io.out.bits.data := outputMem.io.readData
  when(advanceOutput) { outputValid := issueOutputRead }
  when(issueOutputRead) {
    outputMeta.st := outputStart(drainBank) && outputBaseToken(drainBank) + drainToken === 0.U && drainBeat === 0.U
    outputMeta.addr := (outputBaseToken(drainBank) + drainToken) * p.outBeats.U + drainBeat
    outputMeta.last := drainBeat === (p.outBeats - 1).U
    when(drainBeat === (p.outBeats - 1).U) {
      drainBeat := 0.U
      when(drainToken === outputTokenCount(drainBank) - 1.U) {
        drainToken := 0.U
        drainLastIssued := true.B
      }.otherwise { drainToken := drainToken + 1.U }
    }.otherwise { drainBeat := drainBeat + 1.U }
  }
  when(io.out.fire && io.out.bits.last && drainLastIssued) {
    outputFull(drainBank) := false.B
    drainBank := ~drainBank
    drainBeat := 0.U
    drainToken := 0.U
    drainLastIssued := false.B
  }
  when(io.start && parametersLoaded) {
    inputFull.foreach(_ := false.B)
    outputFull.foreach(_ := false.B)
    totalTokens := requestedTokens
    loadedTokens := 0.U
    loadChunkTokens := initialChunkTokens
    loadBank := false.B
    computeBank := false.B
    writeBank := false.B
    drainBank := false.B
    loadBeat := 0.U
    loadToken := 0.U
    drainToken := 0.U
    drainBeat := 0.U
    drainLastIssued := false.B
    outputValid := false.B
    readValid := false.B
    state := sIdle
  }
}

class ParametricLinearInt8ToInt8(p: LinearParams) extends Linear(p)

class ParametricLinearInt8ToFP32(p: LinearParams)
    extends Linear(p.copy(outputBits = 32))
