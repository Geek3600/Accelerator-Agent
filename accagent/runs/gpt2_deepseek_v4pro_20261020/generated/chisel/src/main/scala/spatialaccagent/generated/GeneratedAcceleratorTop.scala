package spatialaccagent.generated

import chisel3._
import chisel3.util._
import spatialaccagent.templates._

class GeneratedAcceleratorTop extends Module {
  private val p = GeneratedDesignParams.params
  // The generated configuration is the authoritative physical-width binding.
  // Do not infer the refill width from a model-specific parameter-family
  // member: older family contracts may not expose that field even though the
  // shared WideRefillParams ABI is selected by the generator.
  private val selectedRefillDataWidthBits: Int = GeneratedDesignParams.materializedRefillDataWidthBits
  private val selectedCrossTokenReuseTokens: Int = GeneratedDesignParams.materializedCrossTokenReuseTokens
  require(selectedCrossTokenReuseTokens > 0, "generated accelerator reuse context must be positive")
  require(
    selectedRefillDataWidthBits == GeneratedDesignParams.boardAxiDataWidthBits,
    "generated tile service must use the discovered board AXI payload width"
  )
  private val core = Module(new GPT2PreLNBlock(p))
  private val tileClientCount: Int = core.io.tile.length
  require(tileClientCount > 0, "generated accelerator must expose at least one tile-service client")
  private val tileService = Module(new WeightTileServiceMux(tileClientCount, selectedRefillDataWidthBits))

  // Preserve the per-kernel tile metadata ports while exposing one generic
  // request/response service to the board scheduler. The mux owns response
  // routing until the final accepted word of a tile, so multiple child
  // kernels cannot interleave or lose loader ownership under backpressure.
  private val responseValidWordsBits = log2Ceil((selectedRefillDataWidthBits / 32 + 1) max 2)
  val ddrTileRequest = IO(Decoupled(new WeightTileRequest(16, 16, 16, 64, 32)))
  val ddrTileResponse = IO(Flipped(Decoupled(new WeightTileResponse(16, 16, 16, 64, 32, selectedRefillDataWidthBits, responseValidWordsBits))))

  val io = IO(new Bundle {
    val start = Input(Bool())
    val cfg = Input(new StageConfig(log2Ceil(p.maxSeqLen + 1 max 2)))
    val cfgValid = Input(Bool())
    val norm1Weight = Flipped(Decoupled(chiselTypeOf(core.io.norm1Weight.bits)))
    val qkvWeight = Flipped(Decoupled(chiselTypeOf(core.io.qkvWeight.bits)))
    val qkvBias = Flipped(Decoupled(chiselTypeOf(core.io.qkvBias.bits)))
    val attentionOutWeight = Flipped(Decoupled(chiselTypeOf(core.io.attentionOutWeight.bits)))
    val attentionOutBias = Flipped(Decoupled(chiselTypeOf(core.io.attentionOutBias.bits)))
    val norm2Weight = Flipped(Decoupled(chiselTypeOf(core.io.norm2Weight.bits)))
    val ffnUpWeight = Flipped(Decoupled(chiselTypeOf(core.io.ffnUpWeight.bits)))
    val ffnUpBias = Flipped(Decoupled(chiselTypeOf(core.io.ffnUpBias.bits)))
    val ffnDownWeight = Flipped(Decoupled(chiselTypeOf(core.io.ffnDownWeight.bits)))
    val ffnDownBias = Flipped(Decoupled(chiselTypeOf(core.io.ffnDownBias.bits)))
    val qkvScale = Input(chiselTypeOf(core.io.qkvScale))
    val attentionOutScale = Input(chiselTypeOf(core.io.attentionOutScale))
    val ffnUpScale = Input(chiselTypeOf(core.io.ffnUpScale))
    val ffnDownScale = Input(chiselTypeOf(core.io.ffnDownScale))
    // Scale metadata is a connected generic transport boundary. The
    // exact LinearScaleMetadata channel dimensions come from the selected
    // decoder core and are forwarded without checkpoint-specific constants.
    // Only route/layer/address metadata is otherwise exposed at this boundary. The
    // ready/valid tile clients remain internal to this wrapper and are wired
    // directly into the shared service mux, avoiding duplicate drivers on
    // child response inputs while retaining the exact board metadata ABI.
    val tile = Input(Vec(tileClientCount, new Bundle {
      val routeId = UInt(16.W)
      val layerIndex = UInt(16.W)
      val ddrBaseWord = UInt(64.W)
      val routeWordOffset = UInt(64.W)
      val layerStrideWords = UInt(64.W)
    }))
    val in = Flipped(Decoupled(chiselTypeOf(core.io.in.bits)))
    val out = Decoupled(chiselTypeOf(core.io.out.bits))
  })

  core.io.start := io.start
  core.io.cfg := io.cfg
  core.io.cfgValid := io.cfgValid
  core.io.norm1Weight <> io.norm1Weight
  core.io.qkvWeight <> io.qkvWeight
  core.io.qkvBias <> io.qkvBias
  core.io.attentionOutWeight <> io.attentionOutWeight
  core.io.attentionOutBias <> io.attentionOutBias
  core.io.norm2Weight <> io.norm2Weight
  core.io.ffnUpWeight <> io.ffnUpWeight
  core.io.ffnUpBias <> io.ffnUpBias
  core.io.ffnDownWeight <> io.ffnDownWeight
  core.io.ffnDownBias <> io.ffnDownBias
  core.io.qkvScale := io.qkvScale
  core.io.attentionOutScale := io.attentionOutScale
  core.io.ffnUpScale := io.ffnUpScale
  core.io.ffnDownScale := io.ffnDownScale
  core.io.in <> io.in
  io.out <> core.io.out
  for (index <- 0 until tileClientCount) {
    core.io.tile(index).routeId := io.tile(index).routeId
    core.io.tile(index).layerIndex := io.tile(index).layerIndex
    core.io.tile(index).ddrBaseWord := io.tile(index).ddrBaseWord
    core.io.tile(index).routeWordOffset := io.tile(index).routeWordOffset
    core.io.tile(index).layerStrideWords := io.tile(index).layerStrideWords
    tileService.io.clientRequests(index) <> core.io.tile(index).request
    core.io.tile(index).response <> tileService.io.clientResponses(index)
    tileService.io.clientTileComplete(index) := core.io.tile(index).tileComplete
    tileService.io.clientPrefetchCommit(index) := core.io.tile(index).prefetchCommit
  }
  tileService.io.request <> ddrTileRequest
  tileService.io.response <> ddrTileResponse
}

object ElaborateGeneratedAccelerator extends App {
  PhysicalImplementation.configureFpgaIp(
    GeneratedDesignParams.computeBackend,
    GeneratedDesignParams.weightMemory,
    GeneratedDesignParams.activationMemory,
    GeneratedDesignParams.fifoMemory,
    GeneratedDesignParams.largeCacheMemory,
    GeneratedDesignParams.fifoDepth,
    GeneratedDesignParams.weightBanks,
    GeneratedDesignParams.activationBanks,
    GeneratedDesignParams.weightBanksByRole,
    GeneratedDesignParams.cacheTileWords,
    GeneratedDesignParams.cacheTileCount,
    GeneratedDesignParams.cacheRefillDataWidthBits,
    GeneratedDesignParams.crossTokenReuseTokens
  )
  _root_.circt.stage.ChiselStage.emitSystemVerilogFile(
    new GeneratedAcceleratorTop,
    firtoolOpts = Array("-disable-all-randomization", "-strip-debug-info")
  )
}

object ElaborateGeneratedAcceleratorVivado extends App {
  PhysicalImplementation.configureFpgaIp(
    GeneratedDesignParams.computeBackend,
    GeneratedDesignParams.weightMemory,
    GeneratedDesignParams.activationMemory,
    GeneratedDesignParams.fifoMemory,
    GeneratedDesignParams.largeCacheMemory,
    GeneratedDesignParams.fifoDepth,
    GeneratedDesignParams.weightBanks,
    GeneratedDesignParams.activationBanks,
    GeneratedDesignParams.weightBanksByRole,
    GeneratedDesignParams.cacheTileWords,
    GeneratedDesignParams.cacheTileCount,
    GeneratedDesignParams.cacheRefillDataWidthBits,
    GeneratedDesignParams.crossTokenReuseTokens
  )
  _root_.circt.stage.ChiselStage.emitSystemVerilogFile(
    new GeneratedAcceleratorTop,
    args = Array("--target-dir", "vivado"),
    firtoolOpts = Array("-disable-all-randomization", "-strip-debug-info")
  )
}
