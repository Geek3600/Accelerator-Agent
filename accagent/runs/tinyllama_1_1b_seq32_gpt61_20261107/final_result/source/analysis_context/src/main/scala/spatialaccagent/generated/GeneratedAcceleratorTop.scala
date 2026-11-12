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
  private val core = Module(new LlamaStyleBlock(p))
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
    val rms1Weight = Flipped(Decoupled(chiselTypeOf(core.io.rms1Weight.bits)))
    val qkvWeight = Flipped(Decoupled(chiselTypeOf(core.io.qkvWeight.bits)))
    val ropeRuntime = Flipped(Decoupled(chiselTypeOf(core.io.ropeRuntime.bits)))
    val attentionOutWeight = Flipped(Decoupled(chiselTypeOf(core.io.attentionOutWeight.bits)))
    val rms2Weight = Flipped(Decoupled(chiselTypeOf(core.io.rms2Weight.bits)))
    val mlpGateWeight = Flipped(Decoupled(chiselTypeOf(core.io.mlpGateWeight.bits)))
    val mlpUpWeight = Flipped(Decoupled(chiselTypeOf(core.io.mlpUpWeight.bits)))
    val mlpDownWeight = Flipped(Decoupled(chiselTypeOf(core.io.mlpDownWeight.bits)))
    val ropeRuntimeLast = Input(Bool())
    val ropeRuntimeLoaded = Output(Bool())
    val qkvScale = Input(chiselTypeOf(core.io.qkvScale))
    val attentionOutScale = Input(chiselTypeOf(core.io.attentionOutScale))
    val mlpGateScale = Input(chiselTypeOf(core.io.mlpGateScale))
    val mlpUpScale = Input(chiselTypeOf(core.io.mlpUpScale))
    val mlpDownScale = Input(chiselTypeOf(core.io.mlpDownScale))
    val position = Input(UInt(log2Ceil(p.maxSeqLen max 2).W))
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
  core.io.position := io.position
  core.io.rms1Weight <> io.rms1Weight
  core.io.qkvWeight <> io.qkvWeight
  core.io.ropeRuntime <> io.ropeRuntime
  core.io.attentionOutWeight <> io.attentionOutWeight
  core.io.rms2Weight <> io.rms2Weight
  core.io.mlpGateWeight <> io.mlpGateWeight
  core.io.mlpUpWeight <> io.mlpUpWeight
  core.io.mlpDownWeight <> io.mlpDownWeight
  core.io.ropeRuntimeLast := io.ropeRuntimeLast
  io.ropeRuntimeLoaded := core.io.ropeRuntimeLoaded
  core.io.elements.get("qkvBias").foreach { disabledPort =>
    val channel = disabledPort.asInstanceOf[DecoupledIO[Data]]
    channel.valid := false.B
    channel.bits := 0.U.asTypeOf(channel.bits)
  }
  core.io.qkvScale := io.qkvScale
  core.io.attentionOutScale := io.attentionOutScale
  core.io.mlpGateScale := io.mlpGateScale
  core.io.mlpUpScale := io.mlpUpScale
  core.io.mlpDownScale := io.mlpDownScale
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
