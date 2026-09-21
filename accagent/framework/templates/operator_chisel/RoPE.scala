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

  val runtimeMemory = Module(new PhysicalSimpleDualPortMemory(p.runtimeWordCount, 32, "activation"))
  val qMemory = Module(new PhysicalSimpleDualPortMemory(p.qkv.headBeats, p.qkv.qkvElemsPerBeat * p.qkv.elemBits, "cache"))
  val qPartnerMemory = Module(new PhysicalSimpleDualPortMemory(p.qkv.headBeats, p.qkv.qkvElemsPerBeat * p.qkv.elemBits, "cache"))
  val kMemory = Module(new PhysicalSimpleDualPortMemory(p.qkv.headBeats, p.qkv.qkvElemsPerBeat * p.qkv.elemBits, "cache"))
  val kPartnerMemory = Module(new PhysicalSimpleDualPortMemory(p.qkv.headBeats, p.qkv.qkvElemsPerBeat * p.qkv.elemBits, "cache"))
  val vMemory = Module(new PhysicalSimpleDualPortMemory(p.qkv.headBeats, p.qkv.qkvElemsPerBeat * p.qkv.elemBits, "cache"))

  val runtimeCount = RegInit(0.U(p.runtimeAddrBits.W))
  val constantsLoaded = RegInit(false.B)
  val expectedRuntimeLast = runtimeCount === (p.runtimeWordCount - 1).U
  io.runtime.ready := !constantsLoaded && io.runtime.bits.addr === runtimeCount && io.runtimeLast === expectedRuntimeLast
  io.runtimeLoaded := constantsLoaded
  runtimeMemory.io.writeEn := io.runtime.fire
  runtimeMemory.io.writeAddr := runtimeCount
  runtimeMemory.io.writeData := io.runtime.bits.data
  when(io.runtime.fire) {
    when(expectedRuntimeLast) {
      constantsLoaded := true.B
      runtimeCount := 0.U
    }.otherwise {
      runtimeCount := runtimeCount + 1.U
    }
  }

  private val states = Enum(12)
  private val sCollect = states(0)
  private val sElementReadIssue = states(1)
  private val sElementReadCapture = states(2)
  private val sCosReadIssue = states(3)
  private val sCosReadCapture = states(4)
  private val sSinReadIssue = states(5)
  private val sSinReadCapture = states(6)
  private val sMulIssue = states(7)
  private val sMulWait = states(8)
  private val sAddIssue = states(9)
  private val sAddWait = states(10)
  private val sEmit = states(11)
  val state = RegInit(sCollect)

  val collectBeat = RegInit(0.U(log2Ceil(p.qkv.headBeats max 2).W))
  val emitBeat = RegInit(0.U(log2Ceil(p.qkv.headBeats max 2).W))
  val emitLane = RegInit(0.U(log2Ceil(p.qkv.qkvElemsPerBeat max 2).W))
  val tokenIndex = RegInit(0.U(p.positionBits.W))
  val capturedToken = RegInit(0.U(p.positionBits.W))
  val capturedHead = RegInit(0.U(p.qkv.headBits.W))
  val capturedStart = RegInit(false.B)
  val capturedLast = RegInit(false.B)
  val laneQ = Reg(UInt(p.qkv.elemBits.W))
  val laneQPartner = Reg(UInt(p.qkv.elemBits.W))
  val laneK = Reg(UInt(p.qkv.elemBits.W))
  val laneKPartner = Reg(UInt(p.qkv.elemBits.W))
  val laneV = Reg(UInt(p.qkv.elemBits.W))
  val cosineWord = Reg(UInt(32.W))
  val sineWord = Reg(UInt(32.W))
  val qDirectReg = Reg(UInt(32.W))
  val qQuadratureReg = Reg(UInt(32.W))
  val kDirectReg = Reg(UInt(32.W))
  val kQuadratureReg = Reg(UInt(32.W))
  val qOutput = Reg(Vec(p.qkv.qkvElemsPerBeat, UInt(p.qkv.elemBits.W)))
  val kOutput = Reg(Vec(p.qkv.qkvElemsPerBeat, UInt(p.qkv.elemBits.W)))
  val vOutput = Reg(Vec(p.qkv.qkvElemsPerBeat, UInt(p.qkv.elemBits.W)))

  val inputChunkBits = p.qkv.qkvElemsPerBeat * p.qkv.elemBits
  val qChunk = io.in.bits.data(inputChunkBits - 1, 0)
  val kChunk = io.in.bits.data(2 * inputChunkBits - 1, inputChunkBits)
  val vChunk = io.in.bits.data(3 * inputChunkBits - 1, 2 * inputChunkBits)
  io.in.ready := constantsLoaded && state === sCollect
  qMemory.io.writeEn := io.in.fire
  qMemory.io.writeAddr := collectBeat
  qMemory.io.writeData := qChunk
  qPartnerMemory.io.writeEn := io.in.fire
  qPartnerMemory.io.writeAddr := collectBeat
  qPartnerMemory.io.writeData := qChunk
  kMemory.io.writeEn := io.in.fire
  kMemory.io.writeAddr := collectBeat
  kMemory.io.writeData := kChunk
  kPartnerMemory.io.writeEn := io.in.fire
  kPartnerMemory.io.writeAddr := collectBeat
  kPartnerMemory.io.writeData := kChunk
  vMemory.io.writeEn := io.in.fire
  vMemory.io.writeAddr := collectBeat
  vMemory.io.writeData := vChunk

  when(io.in.fire) {
    when(collectBeat === 0.U) {
      capturedToken := tokenIndex
      capturedHead := io.in.bits.head
      capturedStart := io.in.bits.st
    }
    when(collectBeat === (p.qkv.headBeats - 1).U) {
      capturedLast := io.in.bits.last
      collectBeat := 0.U
      emitBeat := 0.U
      emitLane := 0.U
      state := sElementReadIssue
      when(io.in.bits.last) {
        tokenIndex := Mux(tokenIndex === (p.qkv.maxSeqLen - 1).U, 0.U, tokenIndex + 1.U)
      }
    }.otherwise {
      collectBeat := collectBeat + 1.U
    }
  }

  val dimension = emitBeat * p.qkv.qkvElemsPerBeat.U + emitLane
  val firstHalf = dimension < (p.qkv.headDim / 2).U
  val partnerDimension = Mux(
    firstHalf,
    dimension + (p.qkv.headDim / 2).U,
    dimension - (p.qkv.headDim / 2).U
  )
  val partnerBeat = partnerDimension / p.qkv.qkvElemsPerBeat.U
  val partnerLane = partnerDimension % p.qkv.qkvElemsPerBeat.U
  val tableScalarIndex = capturedToken * p.qkv.headDim.U + dimension
  val tableWordOffset = tableScalarIndex >> 1
  val tableOdd = tableScalarIndex(0)

  qMemory.io.readEn := state === sElementReadIssue
  qMemory.io.readAddr := emitBeat
  qPartnerMemory.io.readEn := state === sElementReadIssue
  qPartnerMemory.io.readAddr := AccMath.boundedIndex(partnerBeat, p.qkv.headBeats)
  kMemory.io.readEn := state === sElementReadIssue
  kMemory.io.readAddr := emitBeat
  kPartnerMemory.io.readEn := state === sElementReadIssue
  kPartnerMemory.io.readAddr := AccMath.boundedIndex(partnerBeat, p.qkv.headBeats)
  vMemory.io.readEn := state === sElementReadIssue
  vMemory.io.readAddr := emitBeat
  runtimeMemory.io.readEn := state === sCosReadIssue || state === sSinReadIssue
  runtimeMemory.io.readAddr := Mux(
    state === sCosReadIssue,
    p.cosineWordOffset.U + tableWordOffset,
    p.sineWordOffset.U + tableWordOffset
  )

  when(state === sElementReadIssue) {
    state := sElementReadCapture
  }
  val qValues = qMemory.io.readData.asTypeOf(Vec(p.qkv.qkvElemsPerBeat, UInt(p.qkv.elemBits.W)))
  val qPartnerValues = qPartnerMemory.io.readData.asTypeOf(Vec(p.qkv.qkvElemsPerBeat, UInt(p.qkv.elemBits.W)))
  val kValues = kMemory.io.readData.asTypeOf(Vec(p.qkv.qkvElemsPerBeat, UInt(p.qkv.elemBits.W)))
  val kPartnerValues = kPartnerMemory.io.readData.asTypeOf(Vec(p.qkv.qkvElemsPerBeat, UInt(p.qkv.elemBits.W)))
  val vValues = vMemory.io.readData.asTypeOf(Vec(p.qkv.qkvElemsPerBeat, UInt(p.qkv.elemBits.W)))
  when(state === sElementReadCapture) {
    laneQ := qValues(AccMath.boundedIndex(emitLane, p.qkv.qkvElemsPerBeat))
    laneQPartner := qPartnerValues(AccMath.boundedIndex(partnerLane, p.qkv.qkvElemsPerBeat))
    laneK := kValues(AccMath.boundedIndex(emitLane, p.qkv.qkvElemsPerBeat))
    laneKPartner := kPartnerValues(AccMath.boundedIndex(partnerLane, p.qkv.qkvElemsPerBeat))
    laneV := vValues(AccMath.boundedIndex(emitLane, p.qkv.qkvElemsPerBeat))
    state := sCosReadIssue
  }

  when(state === sCosReadIssue) {
    state := sCosReadCapture
  }
  when(state === sCosReadCapture) {
    cosineWord := runtimeMemory.io.readData
    state := sSinReadIssue
  }
  when(state === sSinReadIssue) {
    state := sSinReadCapture
  }
  when(state === sSinReadCapture) {
    sineWord := runtimeMemory.io.readData
    state := sMulIssue
  }

  private def flipSign(value: UInt): UInt = Cat(~value(p.qkv.elemBits - 1), value(p.qkv.elemBits - 2, 0))
  val cosineScalar = Mux(tableOdd, cosineWord(31, 16), cosineWord(15, 0))
  val sineScalar = Mux(tableOdd, sineWord(31, 16), sineWord(15, 0))
  val rotatedQ = Mux(firstHalf, flipSign(laneQPartner), laneQPartner)
  val rotatedK = Mux(firstHalf, flipSign(laneKPartner), laneKPartner)
  val qDirect = Module(new PhysicalFp32Mul)
  val qQuadrature = Module(new PhysicalFp32Mul)
  val kDirect = Module(new PhysicalFp32Mul)
  val kQuadrature = Module(new PhysicalFp32Mul)
  qDirect.io.a := PhysicalMath.toFp32(laneQ, p.qkv.elemBits)
  qDirect.io.b := PhysicalMath.toFp32(cosineScalar, 16)
  qQuadrature.io.a := PhysicalMath.toFp32(rotatedQ, p.qkv.elemBits)
  qQuadrature.io.b := PhysicalMath.toFp32(sineScalar, 16)
  kDirect.io.a := PhysicalMath.toFp32(laneK, p.qkv.elemBits)
  kDirect.io.b := PhysicalMath.toFp32(cosineScalar, 16)
  kQuadrature.io.a := PhysicalMath.toFp32(rotatedK, p.qkv.elemBits)
  kQuadrature.io.b := PhysicalMath.toFp32(sineScalar, 16)
  val allMulReady = qDirect.io.inReady && qQuadrature.io.inReady && kDirect.io.inReady && kQuadrature.io.inReady
  val mulIssue = state === sMulIssue && allMulReady
  qDirect.io.inValid := mulIssue
  qQuadrature.io.inValid := mulIssue
  kDirect.io.inValid := mulIssue
  kQuadrature.io.inValid := mulIssue
  when(mulIssue) {
    state := sMulWait
  }
  when(state === sMulWait && qDirect.io.outValid && qQuadrature.io.outValid && kDirect.io.outValid && kQuadrature.io.outValid) {
    qDirectReg := qDirect.io.out
    qQuadratureReg := qQuadrature.io.out
    kDirectReg := kDirect.io.out
    kQuadratureReg := kQuadrature.io.out
    state := sAddIssue
  }

  val qAdd = Module(new PhysicalFp32Add)
  val kAdd = Module(new PhysicalFp32Add)
  qAdd.io.a := qDirectReg
  qAdd.io.b := qQuadratureReg
  kAdd.io.a := kDirectReg
  kAdd.io.b := kQuadratureReg
  val addIssue = state === sAddIssue && qAdd.io.inReady && kAdd.io.inReady
  qAdd.io.inValid := addIssue
  kAdd.io.inValid := addIssue
  when(addIssue) {
    state := sAddWait
  }
  when(state === sAddWait && qAdd.io.outValid && kAdd.io.outValid) {
    qOutput(AccMath.boundedIndex(emitLane, p.qkv.qkvElemsPerBeat)) := PhysicalMath.fromFp32(qAdd.io.out, p.qkv.elemBits)
    kOutput(AccMath.boundedIndex(emitLane, p.qkv.qkvElemsPerBeat)) := PhysicalMath.fromFp32(kAdd.io.out, p.qkv.elemBits)
    vOutput(AccMath.boundedIndex(emitLane, p.qkv.qkvElemsPerBeat)) := laneV
    when(emitLane === (p.qkv.qkvElemsPerBeat - 1).U) {
      emitLane := 0.U
      state := sEmit
    }.otherwise {
      emitLane := emitLane + 1.U
      state := sElementReadIssue
    }
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
      emitLane := 0.U
      state := sElementReadIssue
    }
  }

  dontTouch(io.cfg)
  dontTouch(io.cfgValid)
  dontTouch(io.position)
}

class RoPEApply(p: RoPEParams) extends RoPE(p)
