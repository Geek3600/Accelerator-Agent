import spatialaccagent.templates._

object GenerateLinearPipeline extends App {
  val destination = args(0)
  val cases = Seq(
    "grouped" -> LinearParams(128, 16, inLanes = 4, outLanes = 4, batchSize = 40, maxSeqLen = 40, computeArrayRows = 2, computeArrayCols = 1, outputBits = 32, refillDataWidthBits = 512, cacheTileWords = 3, cacheTileCount = 2, crossTokenReuseTokens = 8),
    "reduced" -> LinearParams(64, 12, inLanes = 8, outLanes = 4, batchSize = 40, maxSeqLen = 40, computeArrayRows = 4, computeArrayCols = 4, hasBias = false, refillDataWidthBits = 512),
    "output_groups" -> LinearParams(32, 32, inLanes = 16, outLanes = 16, batchSize = 40, maxSeqLen = 40, computeArrayRows = 8, computeArrayCols = 16, outputBits = 32, refillDataWidthBits = 512),
    "wide_input" -> LinearParams(128, 8, inLanes = 64, outLanes = 4, batchSize = 40, maxSeqLen = 40, computeArrayRows = 4, computeArrayCols = 16, outputBits = 32, refillDataWidthBits = 512),
    "single_term" -> LinearParams(4, 4, inLanes = 4, outLanes = 4, batchSize = 40, maxSeqLen = 40, computeArrayRows = 4, computeArrayCols = 4, fusedActivation = "relu", hasBias = false, refillDataWidthBits = 512),
    "wide_columns" -> LinearParams(128, 16, inLanes = 4, outLanes = 4, batchSize = 40, maxSeqLen = 40, computeArrayRows = 4, computeArrayCols = 16, outputBits = 32, refillDataWidthBits = 512, cacheTileWords = 5, cacheTileCount = 3, crossTokenReuseTokens = 4),
    // True W4A8: 8-bit activation stream, densely packed signed 4-bit
    // matrix values, signed 32-bit accumulation, and a 2048-bit matrix tile.
    "w4a8" -> LinearParams(128, 32, inLanes = 16, outLanes = 16, elemBits = 8, weightBits = 4, integerMode = true, accBits = 32, outputBits = 8, batchSize = 40, maxSeqLen = 40, computeArrayRows = 16, computeArrayCols = 32, refillDataWidthBits = 512, cacheTileWords = 3, cacheTileCount = 2, crossTokenReuseTokens = 8)
  )
  for ((name, params) <- cases) {
    circt.stage.ChiselStage.emitSystemVerilogFile(
      new Linear(params),
      Array("--target-dir", s"$destination/$name"),
      firtoolOpts = Array("--disable-all-randomization", "--preserve-values=named")
    )
    java.nio.file.Files.writeString(
      java.nio.file.Paths.get(destination, name, "params.json"),
      s"""{"in_dim":${params.inDim},"out_dim":${params.outDim},"in_lanes":${params.inLanes},"out_lanes":${params.outLanes},"elem_bits":${params.elemBits},"weight_bits":${params.matrixWeightBits},"integer_mode":${params.integerMode},"output_bits":${params.outputBits},"mac_rows":${params.macRows},"mac_cols":${params.macCols},"has_bias":${params.hasBias},"activation":"${params.fusedActivation}","batch_size":${params.batchSize},"refill_data_width_bits":${params.refillDataWidthBits},"cache_tile_words":${params.cacheTileWords},"cache_tile_count":${params.cacheTileCount},"cross_token_reuse_tokens":${params.crossTokenReuseTokens}}"""
    )
  }

  // The compile-only decoder tops inherit the real connected block modules;
  // they are not stubs and do not replace either legacy FP regression case.
  PhysicalImplementation.configureNumericPolicy(
    weightBits = 4,
    activationBits = 8,
    accumulatorBits = 32,
    scaleBits = 32,
    scaleShift = 31,
    rounding = "nearest_even",
    saturation = true
  )
  PhysicalImplementation.configureFpgaIp(
    "integer_dsp", "xpm_uram", "xpm_bram", "xpm_bram", "xpm_uram",
    fifoDepth = 16, weightBanks = 1, activationBanks = 2, roleWeightBanks = Map.empty,
    cacheTileWords = 3, cacheTileCount = 2, refillDataWidthBits = 512, crossTokenReuseTokens = 2
  )

  val layerNormParams = DecoderBlockParams(
    hiddenSize = 32, numHeads = 4, headDim = 8, intermediateSize = 64,
    lanes = 8, batchSize = 4, maxSeqLen = 4,
    inputBits = 8, elemBits = 8, outputBits = 8,
    computeArrayRows = 4, computeArrayCols = 4,
    cacheTileWords = 3, cacheTileCount = 2, refillDataWidthBits = 512,
    crossTokenReuseTokens = 2, mlpActivation = "gelu_new",
    weightBits = 4, integerMode = true, accBits = 32
  )
  class W4A8LayerNormDecoderCompileTop extends GPT2PreLNBlock(layerNormParams)
  circt.stage.ChiselStage.emitSystemVerilogFile(
    new W4A8LayerNormDecoderCompileTop,
    Array("--target-dir", s"$destination/w4a8_decoder_layernorm"),
    firtoolOpts = Array("--disable-all-randomization", "--preserve-values=named")
  )
  java.nio.file.Files.writeString(
    java.nio.file.Paths.get(destination, "w4a8_decoder_layernorm", "params.json"),
    """{"compile_only_top":"W4A8LayerNormDecoderCompileTop","integer_mode":true,"case":"w4a8_decoder_layernorm"}"""
  )

  val rmsNormParams = LlamaStyleBlockParams(
    hiddenSize = 32, qHeads = 4, kvHeads = 2, headDim = 8, intermediateSize = 64,
    lanes = 8, batchSize = 4, maxSeqLen = 4,
    inputBits = 8, elemBits = 8, outputBits = 8,
    computeArrayRows = 4, computeArrayCols = 4,
    cacheTileWords = 3, cacheTileCount = 2, refillDataWidthBits = 512,
    crossTokenReuseTokens = 2, ropeTheta = 10000.0,
    weightBits = 4, integerMode = true, accBits = 32
  )
  class W4A8RmsNormDecoderCompileTop extends Qwen2Block(rmsNormParams)
  circt.stage.ChiselStage.emitSystemVerilogFile(
    new W4A8RmsNormDecoderCompileTop,
    Array("--target-dir", s"$destination/w4a8_decoder_rmsnorm"),
    firtoolOpts = Array("--disable-all-randomization", "--preserve-values=named")
  )
  java.nio.file.Files.writeString(
    java.nio.file.Paths.get(destination, "w4a8_decoder_rmsnorm", "params.json"),
    """{"compile_only_top":"W4A8RmsNormDecoderCompileTop","integer_mode":true,"case":"w4a8_decoder_rmsnorm"}"""
  )
}
