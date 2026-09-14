package spatialaccagent.templates

import chisel3._
import chisel3.util._

final case class RoPEParams(
  qkv: QKVProjectionParams,
  theta: Double = 1000000.0,
  localTheta: Option[Double] = None
) {
  require(qkv.elemBits == 16, "captured RoPE tables and Q/K values use IEEE FP16")
  require(qkv.headDim % 2 == 0, "rotate-half RoPE requires an even head dimension")
  require(qkv.headDim % qkv.qkvElemsPerBeat == 0, "head dimension must divide the stream beat")

  val positionBits: Int = log2Ceil(qkv.maxSeqLen max 2)
  val positionWordOffset: Int = 0
  val cachePositionWordOffset: Int = qkv.maxSeqLen
  val cosineWordOffset: Int = 2 * qkv.maxSeqLen
  val tableScalarCount: Int = qkv.maxSeqLen * qkv.headDim
  val tableWordCount: Int = tableScalarCount / 2
  val sineWordOffset: Int = cosineWordOffset + tableWordCount
  val runtimeWordCount: Int = sineWordOffset + tableWordCount
  val runtimeAddrBits: Int = log2Ceil(runtimeWordCount max 2)
}

class RoPE(p: RoPEParams) extends Module {
  val io = IO(new Bundle {
    val cfg = Input(new StageConfig(log2Ceil(p.qkv.maxSeqLen + 1 max 2)))
    val cfgValid = Input(Bool())
    val position = Input(UInt(p.positionBits.W))
    val runtime = Flipped(Decoupled(new WeightWrite(32, p.runtimeAddrBits)))
    val runtimeLast = Input(Bool())
    val runtimeLoaded = Output(Bool())
    val in = Flipped(Decoupled(new QKVStreamBeat(p.qkv)))
    val out = Decoupled(new QKVStreamBeat(p.qkv))
  })

  val positionIds = Reg(Vec(p.qkv.maxSeqLen, UInt(32.W)))
  val cachePositions = Reg(Vec(p.qkv.maxSeqLen, UInt(32.W)))
  val cosine = Reg(Vec(p.tableScalarCount, UInt(16.W)))
  val sine = Reg(Vec(p.tableScalarCount, UInt(16.W)))

  val runtimeCount = RegInit(0.U(p.runtimeAddrBits.W))
  val constantsLoaded = RegInit(false.B)
  val expectedRuntimeLast = runtimeCount === (p.runtimeWordCount - 1).U
  val runtimeAddressMatches = io.runtime.bits.addr === runtimeCount
  val runtimeLastMatches = io.runtimeLast === expectedRuntimeLast

  io.runtime.ready := !constantsLoaded && runtimeAddressMatches && runtimeLastMatches
  io.runtimeLoaded := constantsLoaded

  when(io.runtime.fire) {
    when(runtimeCount < p.cachePositionWordOffset.U) {
      positionIds(runtimeCount) := io.runtime.bits.data
    }.elsewhen(runtimeCount < p.cosineWordOffset.U) {
      cachePositions(runtimeCount - p.cachePositionWordOffset.U) := io.runtime.bits.data
    }.elsewhen(runtimeCount < p.sineWordOffset.U) {
      val wordIndex = runtimeCount - p.cosineWordOffset.U
      val scalarIndex = wordIndex << 1
      cosine(scalarIndex) := io.runtime.bits.data(15, 0)
      cosine(scalarIndex + 1.U) := io.runtime.bits.data(31, 16)
    }.otherwise {
      val wordIndex = runtimeCount - p.sineWordOffset.U
      val scalarIndex = wordIndex << 1
      sine(scalarIndex) := io.runtime.bits.data(15, 0)
      sine(scalarIndex + 1.U) := io.runtime.bits.data(31, 16)
    }

    when(expectedRuntimeLast) {
      constantsLoaded := true.B
      runtimeCount := 0.U
    }.otherwise {
      runtimeCount := runtimeCount + 1.U
    }
  }

  // Qwen2 receives position_ids and cache_position together with already
  // materialized position embeddings. The attention operator consumes the
  // captured cosine/sine rows directly; it must not regenerate them from theta.
  dontTouch(positionIds)
  dontTouch(cachePositions)
  dontTouch(io.position)
  dontTouch(io.cfg)
  dontTouch(io.cfgValid)

  val qVector = Reg(Vec(p.qkv.headDim, UInt(p.qkv.elemBits.W)))
  val kVector = Reg(Vec(p.qkv.headDim, UInt(p.qkv.elemBits.W)))
  val vVector = Reg(Vec(p.qkv.headDim, UInt(p.qkv.elemBits.W)))
  val collectBeat = RegInit(0.U(log2Ceil(p.qkv.headBeats max 2).W))
  val emitBeat = RegInit(0.U(log2Ceil(p.qkv.headBeats max 2).W))
  val tokenIndex = RegInit(0.U(p.positionBits.W))
  val capturedToken = RegInit(0.U(p.positionBits.W))
  val capturedHead = RegInit(0.U(p.qkv.headBits.W))
  val capturedStart = RegInit(false.B)
  val capturedLast = RegInit(false.B)
  val sCollect :: sEmit :: Nil = Enum(2)
  val state = RegInit(sCollect)

  io.in.ready := constantsLoaded && state === sCollect
  val inputFields = io.in.bits.data.asTypeOf(Vec(3 * p.qkv.qkvElemsPerBeat, UInt(p.qkv.elemBits.W)))

  when(io.in.fire) {
    when(collectBeat === 0.U) {
      capturedToken := tokenIndex
      capturedHead := io.in.bits.head
      capturedStart := io.in.bits.st
    }
    for (lane <- 0 until p.qkv.qkvElemsPerBeat) {
      val dimension = collectBeat * p.qkv.qkvElemsPerBeat.U + lane.U
      qVector(dimension) := inputFields(lane)
      kVector(dimension) := inputFields(p.qkv.qkvElemsPerBeat + lane)
      vVector(dimension) := inputFields(2 * p.qkv.qkvElemsPerBeat + lane)
    }
    when(collectBeat === (p.qkv.headBeats - 1).U) {
      capturedLast := io.in.bits.last
      collectBeat := 0.U
      emitBeat := 0.U
      state := sEmit
      when(io.in.bits.last) {
        tokenIndex := Mux(tokenIndex === (p.qkv.maxSeqLen - 1).U, 0.U, tokenIndex + 1.U)
      }
    }.otherwise {
      collectBeat := collectBeat + 1.U
    }
  }

  private def flipSign(value: UInt): UInt =
    Cat(~value(p.qkv.elemBits - 1), value(p.qkv.elemBits - 2, 0))

  private def applyRotary(value: UInt, rotated: UInt, cosValue: UInt, sinValue: UInt): UInt = {
    val valueFp32 = IeeeMath.toFp32(value, p.qkv.elemBits)
    val rotatedFp32 = IeeeMath.toFp32(rotated, p.qkv.elemBits)
    val cosFp32 = IeeeMath.toFp32(cosValue, 16)
    val sinFp32 = IeeeMath.toFp32(sinValue, 16)
    val direct = IeeeMath.mulFp32(valueFp32, cosFp32)
    val quadrature = IeeeMath.mulFp32(rotatedFp32, sinFp32)
    IeeeMath.fromFp32(IeeeMath.addFp32(direct, quadrature), p.qkv.elemBits)
  }

  val qOutput = Wire(Vec(p.qkv.qkvElemsPerBeat, UInt(p.qkv.elemBits.W)))
  val kOutput = Wire(Vec(p.qkv.qkvElemsPerBeat, UInt(p.qkv.elemBits.W)))
  val vOutput = Wire(Vec(p.qkv.qkvElemsPerBeat, UInt(p.qkv.elemBits.W)))

  for (lane <- 0 until p.qkv.qkvElemsPerBeat) {
    val dimension = emitBeat * p.qkv.qkvElemsPerBeat.U + lane.U
    val inFirstHalf = dimension < (p.qkv.headDim / 2).U
    val partnerDimension = Mux(
      inFirstHalf,
      dimension + (p.qkv.headDim / 2).U,
      dimension - (p.qkv.headDim / 2).U
    )
    val rotatedQ = Mux(inFirstHalf, flipSign(qVector(partnerDimension)), qVector(partnerDimension))
    val rotatedK = Mux(inFirstHalf, flipSign(kVector(partnerDimension)), kVector(partnerDimension))
    val tableIndex = capturedToken * p.qkv.headDim.U + dimension

    qOutput(lane) := applyRotary(qVector(dimension), rotatedQ, cosine(tableIndex), sine(tableIndex))
    kOutput(lane) := applyRotary(kVector(dimension), rotatedK, cosine(tableIndex), sine(tableIndex))
    vOutput(lane) := vVector(dimension)
  }

  io.out.valid := state === sEmit
  io.out.bits.data := Cat(vOutput.reverse ++ kOutput.reverse ++ qOutput.reverse)
  io.out.bits.st := capturedStart && emitBeat === 0.U
  io.out.bits.head := capturedHead
  io.out.bits.addr := emitBeat
  io.out.bits.last := capturedLast && emitBeat === (p.qkv.headBeats - 1).U

  when(io.out.fire) {
    when(emitBeat === (p.qkv.headBeats - 1).U) {
      emitBeat := 0.U
      state := sCollect
    }.otherwise {
      emitBeat := emitBeat + 1.U
    }
  }
}

class RoPEApply(p: RoPEParams) extends RoPE(p)
