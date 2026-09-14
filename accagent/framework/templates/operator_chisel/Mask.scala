package spatialaccagent.templates

import chisel3._
import chisel3.util._

final case class AttentionMaskParams(
  seqLen: Int,
  causal: Boolean = true,
  slidingWindow: Int = 0,
  globalEvery: Int = 0
) {
  require(seqLen > 0, "seqLen must be positive")
  require(slidingWindow >= 0, "slidingWindow must be non-negative")
  require(globalEvery >= 0, "globalEvery must be non-negative")
  val seqBits: Int = log2Ceil(seqLen + 1 max 2)
  val rowBits: Int = log2Ceil(seqLen max 2)
}

class AttentionMask(p: AttentionMaskParams) extends Module {
  val io = IO(new Bundle {
    val cfg = Input(new StageConfig(p.seqBits))
    val cfgValid = Input(Bool())
    val rowIndex = Input(UInt(p.rowBits.W))
    val mask = Output(UInt(p.seqLen.W))
  })

  val seqLimit = RegInit(p.seqLen.U(p.seqBits.W))
  when(io.cfgValid) {
    seqLimit := Mux(io.cfg.seqlen === 0.U || io.cfg.seqlen > p.seqLen.U, p.seqLen.U, io.cfg.seqlen)
  }

  val bits = Wire(Vec(p.seqLen, Bool()))
  val globalRow =
    if (p.globalEvery > 0) io.rowIndex % p.globalEvery.U === 0.U else false.B
  for (i <- 0 until p.seqLen) {
    val idx = i.U(p.rowBits.W)
    val active = i.U < seqLimit
    val causalKeep = if (p.causal) idx <= io.rowIndex else true.B
    val slidingKeep =
      if (p.slidingWindow > 0) (idx + p.slidingWindow.U) > io.rowIndex else true.B
    bits(i) := active && causalKeep && (slidingKeep || globalRow)
  }
  io.mask := bits.asUInt
}
