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
