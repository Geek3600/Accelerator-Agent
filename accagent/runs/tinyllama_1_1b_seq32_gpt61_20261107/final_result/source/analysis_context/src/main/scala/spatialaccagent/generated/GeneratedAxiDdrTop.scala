package spatialaccagent.generated

import chisel3._
import chisel3.util._
import spatialaccagent.templates._

class GeneratedAxiDdrTop extends Module {
  private val p = GeneratedDesignParams.params
  private val selectedRefillDataWidthBits = GeneratedDesignParams.materializedRefillDataWidthBits
  require(
    selectedRefillDataWidthBits == GeneratedDesignParams.boardAxiDataWidthBits,
    "generated AXI wrapper must use the discovered board AXI payload width"
  )
  private val core = Module(new GeneratedAcceleratorTop)
  private val dataBits = p.lanes * p.inputBits
  private val addrBits = log2Ceil(p.batchSize * (p.hiddenSize / p.lanes) max 2)
  private val cfgBits = log2Ceil(p.maxSeqLen + 1 max 2)
  private val posBits = log2Ceil(p.maxSeqLen max 2)

  val io = IO(new Bundle {
    val start = Input(Bool())
    val cfgSeqlen = Input(UInt(cfgBits.W))
    val cfgPrefill = Input(Bool())
    val cfgSingleQuery = Input(Bool())
    val position = Input(UInt(posBits.W))
    val tile = chiselTypeOf(core.io.tile)
    // Generic bounded DDR tile service. The board scheduler owns the AXI
    // conversion; this boundary carries route/layer/tile/bank/word metadata
    // and remains ready/valid under both request and response stalls.
    val responseValidWordsBits = log2Ceil((selectedRefillDataWidthBits / 32 + 1) max 2)
    val ddrTileRequest = Decoupled(new WeightTileRequest(16, 16, 16, 64, 32))
    val ddrTileResponse = Flipped(Decoupled(new WeightTileResponse(16, 16, 16, 64, 32, selectedRefillDataWidthBits, responseValidWordsBits)))

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


    val axiReadValid = Input(Bool())
    val axiReadReady = Output(Bool())
    val axiReadData = Input(UInt(dataBits.W))
    val axiReadAddr = Input(UInt(addrBits.W))
    val axiReadStart = Input(Bool())
    val axiReadLast = Input(Bool())

    val axiWriteValid = Output(Bool())
    val axiWriteReady = Input(Bool())
    val axiWriteData = Output(UInt(dataBits.W))
    val axiWriteAddr = Output(UInt(addrBits.W))
    val axiWriteStart = Output(Bool())
    val axiWriteLast = Output(Bool())

    val busy = Output(Bool())
    val done = Output(Bool())
    val performanceCycles = Output(UInt(64.W))
    val performanceValid = Output(Bool())
  })

  private val running = RegInit(false.B)
  private val latencyCycles = RegInit(0.U(64.W))
  private val latencyValid = RegInit(false.B)
  private val active = running || io.start

  when(io.start) {
    running := true.B
    latencyCycles := 0.U
    latencyValid := false.B
  }.elsewhen(running) {
    latencyCycles := latencyCycles + 1.U
    when(core.io.out.fire && core.io.out.bits.last) {
      running := false.B
      latencyValid := true.B
    }
  }

  core.io.start := io.start
  core.io.cfg.seqlen := io.cfgSeqlen
  core.io.cfg.prefill := io.cfgPrefill
  core.io.cfg.singleQuery := io.cfgSingleQuery
  core.io.cfgValid := active
  core.io.tile <> io.tile
  core.ddrTileRequest <> io.ddrTileRequest
  core.ddrTileResponse <> io.ddrTileResponse
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
  core.io.in.valid := io.axiReadValid && active
  core.io.in.bits.data := io.axiReadData
  core.io.in.bits.addr := io.axiReadAddr
  core.io.in.bits.st := io.axiReadStart
  core.io.in.bits.last := io.axiReadLast
  io.axiReadReady := core.io.in.ready && active

  core.io.out.ready := io.axiWriteReady
  io.axiWriteValid := core.io.out.valid
  io.axiWriteData := core.io.out.bits.data
  io.axiWriteAddr := core.io.out.bits.addr
  io.axiWriteStart := core.io.out.bits.st
  io.axiWriteLast := core.io.out.bits.last

  io.busy := active
  io.done := !active
  io.performanceCycles := latencyCycles
  io.performanceValid := latencyValid
}

object ElaborateGeneratedAxiDdrTop extends App {
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
    new GeneratedAxiDdrTop,
    firtoolOpts = Array("-disable-all-randomization", "-strip-debug-info")
  )
}

object ElaborateGeneratedAxiDdrTopVivado extends App {
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
    new GeneratedAxiDdrTop,
    args = Array("--target-dir", "vivado"),
    firtoolOpts = Array("-disable-all-randomization", "-strip-debug-info")
  )
}
