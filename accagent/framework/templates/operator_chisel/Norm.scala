package spatialaccagent.templates

import chisel3._
import chisel3.util._
import hardfloat._
import hardfloat.consts

final case class VectorNormParams(
  hiddenSize: Int,
  lanes: Int,
  inputBits: Int = 32,
  outputBits: Int = 16,
  batchSize: Int = 16,
  maxSeqLen: Int = 16,
  hasMeanSub: Boolean = true,
  hasBeta: Boolean = true,
  eps: Double = 1.0e-5
) {
  require(hiddenSize > 0, "hiddenSize must be positive")
  require(hiddenSize % lanes == 0, "hiddenSize must be divisible by lanes")
  require(inputBits == 16 || inputBits == 32, "VectorNorm input and affine weights must be FP16 or FP32")
  require(outputBits == 16 || outputBits == 32, "VectorNorm output must be FP16 or FP32")
  require(eps > 0.0, "normalization epsilon must be positive")
  val beats: Int = hiddenSize / lanes
  val inputBeatBits: Int = lanes * inputBits
  val outputBeatBits: Int = lanes * outputBits
  val addrBits: Int = log2Ceil(batchSize * beats max 2)
  val weightBeats: Int = if (hasBeta) beats * 2 else beats
}

class VectorNorm(p: VectorNormParams) extends Module {
  val io = IO(new Bundle {
    val cfg = Input(new StageConfig(log2Ceil(p.maxSeqLen + 1 max 2)))
    val cfgValid = Input(Bool())
    val weight = Flipped(Decoupled(UInt(p.inputBeatBits.W)))
    val quant = new Int8QuantPorts
    val in = Flipped(Decoupled(new StreamBeat(StreamSpec(p.inputBeatBits, p.addrBits))))
    val out = Decoupled(new StreamBeat(StreamSpec(p.outputBeatBits, p.addrBits)))
  })

  val gamma = Reg(Vec(p.beats, UInt(p.inputBeatBits.W)))
  val beta = if (p.hasBeta) Some(Reg(Vec(p.beats, UInt(p.inputBeatBits.W)))) else None
  val weightCnt = RegInit(0.U(log2Ceil(p.weightBeats max 2).W))
  val weightsLoaded = RegInit(false.B)

  io.weight.ready := !weightsLoaded
  when(io.weight.fire) {
    if (p.hasBeta) {
      when(weightCnt < p.beats.U) {
        beta.get(weightCnt) := io.weight.bits
      }.otherwise {
        gamma(weightCnt - p.beats.U) := io.weight.bits
      }
    } else {
      gamma(weightCnt) := io.weight.bits
    }
    when(weightCnt === (p.weightBeats - 1).U) {
      weightCnt := 0.U
      weightsLoaded := true.B
    }.otherwise {
      weightCnt := weightCnt + 1.U
    }
  }

  val inputData = Reg(Vec(p.beats, UInt(p.inputBeatBits.W)))
  val inputStart = Reg(Vec(p.beats, Bool()))
  val inputAddr = Reg(Vec(p.beats, UInt(p.addrBits.W)))
  val inputLast = Reg(Vec(p.beats, Bool()))

  val sLoad :: sPrepare :: sSqrtIssue :: sSqrtWait :: sRecipIssue :: sRecipWait :: sEmit :: Nil = Enum(7)
  val state = RegInit(sLoad)
  val inputCnt = RegInit(0.U(log2Ceil(p.beats max 2).W))
  val outputCnt = RegInit(0.U(log2Ceil(p.beats max 2).W))
  val sumReg = Reg(UInt(32.W))
  val squareSumReg = Reg(UInt(32.W))
  val meanReg = Reg(UInt(32.W))
  val varianceReg = Reg(UInt(32.W))
  val denominatorReg = Reg(UInt(32.W))
  val inverseReg = Reg(UInt(32.W))

  io.in.ready := state === sLoad && weightsLoaded
  val incoming = io.in.bits.data.asTypeOf(Vec(p.lanes, UInt(p.inputBits.W)))
  val incomingFp32 = (0 until p.lanes).map(i => IeeeMath.toFp32(incoming(i), p.inputBits))
  val incomingSquares = incomingFp32.map(x => IeeeMath.mulFp32(x, x))
  val beatSum = IeeeMath.sumFp32(incomingFp32)
  val beatSquareSum = IeeeMath.sumFp32(incomingSquares)

  when(io.in.fire) {
    inputData(inputCnt) := io.in.bits.data
    inputStart(inputCnt) := io.in.bits.st
    inputAddr(inputCnt) := io.in.bits.addr
    inputLast(inputCnt) := io.in.bits.last
    when(inputCnt === 0.U) {
      sumReg := beatSum
      squareSumReg := beatSquareSum
    }.otherwise {
      sumReg := IeeeMath.addFp32(sumReg, beatSum)
      squareSumReg := IeeeMath.addFp32(squareSumReg, beatSquareSum)
    }
    when(inputCnt === (p.beats - 1).U) {
      inputCnt := 0.U
      state := sPrepare
    }.otherwise {
      inputCnt := inputCnt + 1.U
    }
  }

  val reciprocalHiddenSize = IeeeMath.fp32Constant(1.0 / p.hiddenSize.toDouble)
  val meanValue = IeeeMath.mulFp32(sumReg, reciprocalHiddenSize)
  val meanSquareValue = IeeeMath.mulFp32(squareSumReg, reciprocalHiddenSize)
  val centeredVariance = if (p.hasMeanSub) {
    val squaredMean = IeeeMath.mulFp32(meanValue, meanValue)
    val rawVariance = IeeeMath.subFp32(meanSquareValue, squaredMean)
    Mux(IeeeMath.lessThanFp32(rawVariance, IeeeMath.fp32Zero), IeeeMath.fp32Zero, rawVariance)
  } else {
    meanSquareValue
  }
  val varianceWithEpsilon = IeeeMath.addFp32(centeredVariance, IeeeMath.fp32Constant(p.eps))

  when(state === sPrepare) {
    meanReg := (if (p.hasMeanSub) meanValue else IeeeMath.fp32Zero)
    varianceReg := varianceWithEpsilon
    state := sSqrtIssue
  }

  val divSqrt = Module(new DivSqrtRecFN_small(8, 24, 0))
  divSqrt.io.inValid := state === sSqrtIssue || state === sRecipIssue
  divSqrt.io.sqrtOp := state === sSqrtIssue
  divSqrt.io.a := recFNFromFN(8, 24, Mux(state === sSqrtIssue, varianceReg, IeeeMath.fp32One))
  divSqrt.io.b := recFNFromFN(8, 24, denominatorReg)
  divSqrt.io.roundingMode := consts.round_near_even
  divSqrt.io.detectTininess := consts.tininess_afterRounding
  val divSqrtResult = fNFromRecFN(8, 24, divSqrt.io.out)

  when(state === sSqrtIssue && divSqrt.io.inReady) {
    state := sSqrtWait
  }
  when(state === sSqrtWait && divSqrt.io.outValid_sqrt) {
    denominatorReg := divSqrtResult
    state := sRecipIssue
  }
  when(state === sRecipIssue && divSqrt.io.inReady) {
    state := sRecipWait
  }
  when(state === sRecipWait && divSqrt.io.outValid_div) {
    inverseReg := divSqrtResult
    outputCnt := 0.U
    state := sEmit
  }

  val currentInput = inputData(outputCnt).asTypeOf(Vec(p.lanes, UInt(p.inputBits.W)))
  val currentGamma = gamma(outputCnt).asTypeOf(Vec(p.lanes, UInt(p.inputBits.W)))
  val currentBeta = if (p.hasBeta) {
    beta.get(outputCnt).asTypeOf(Vec(p.lanes, UInt(p.inputBits.W)))
  } else {
    WireDefault(VecInit(Seq.fill(p.lanes)(0.U(p.inputBits.W))))
  }
  val outputData = Wire(Vec(p.lanes, UInt(p.outputBits.W)))
  for (lane <- 0 until p.lanes) {
    val x = IeeeMath.toFp32(currentInput(lane), p.inputBits)
    val centered = if (p.hasMeanSub) IeeeMath.subFp32(x, meanReg) else x
    val normalized = IeeeMath.mulFp32(centered, inverseReg)
    val scaled = IeeeMath.mulFp32(normalized, IeeeMath.toFp32(currentGamma(lane), p.inputBits))
    val affine = if (p.hasBeta) {
      IeeeMath.addFp32(scaled, IeeeMath.toFp32(currentBeta(lane), p.inputBits))
    } else {
      scaled
    }
    outputData(lane) := IeeeMath.fromFp32(affine, p.outputBits)
  }

  io.out.valid := state === sEmit
  io.out.bits.data := outputData.asUInt
  io.out.bits.st := inputStart(outputCnt)
  io.out.bits.addr := inputAddr(outputCnt)
  io.out.bits.last := inputLast(outputCnt)

  when(io.out.fire) {
    when(outputCnt === (p.beats - 1).U) {
      outputCnt := 0.U
      state := sLoad
    }.otherwise {
      outputCnt := outputCnt + 1.U
    }
  }
}

final case class RMSNormParams(
  hiddenSize: Int,
  lanes: Int,
  inputBits: Int = 32,
  outputBits: Int = 16,
  batchSize: Int = 16,
  maxSeqLen: Int = 16,
  eps: Double = 1.0e-6
) {
  val vector = VectorNormParams(
    hiddenSize = hiddenSize,
    lanes = lanes,
    inputBits = inputBits,
    outputBits = outputBits,
    batchSize = batchSize,
    maxSeqLen = maxSeqLen,
    hasMeanSub = false,
    hasBeta = false,
    eps = eps
  )
}

class RMSNorm(p: RMSNormParams) extends Module {
  val io = IO(new Bundle {
    val cfg = Input(new StageConfig(log2Ceil(p.vector.maxSeqLen + 1 max 2)))
    val cfgValid = Input(Bool())
    val weight = Flipped(Decoupled(UInt(p.vector.inputBeatBits.W)))
    val quant = new Int8QuantPorts
    val in = Flipped(Decoupled(new StreamBeat(StreamSpec(p.vector.inputBeatBits, p.vector.addrBits))))
    val out = Decoupled(new StreamBeat(StreamSpec(p.vector.outputBeatBits, p.vector.addrBits)))
  })

  val core = Module(new VectorNorm(p.vector))
  core.io.cfg := io.cfg
  core.io.cfgValid := io.cfgValid
  core.io.weight <> io.weight
  core.io.quant.outInvScale := io.quant.outInvScale
  core.io.quant.outZeroPoint := io.quant.outZeroPoint
  core.io.in <> io.in
  io.out <> core.io.out
}

class RMSNormQ(p: RMSNormParams) extends RMSNorm(p)

final case class QKNormParams(
  qkv: QKVProjectionParams,
  eps: Double = 1.0e-6
) {
  val weightBits: Int = qkv.qkvElemsPerBeat * qkv.elemBits
}

class QKNorm(p: QKNormParams) extends Module {
  val io = IO(new Bundle {
    val cfg = Input(new StageConfig(log2Ceil(p.qkv.maxSeqLen + 1 max 2)))
    val cfgValid = Input(Bool())
    val qWeight = Flipped(Decoupled(UInt(p.weightBits.W)))
    val kWeight = Flipped(Decoupled(UInt(p.weightBits.W)))
    val in = Flipped(Decoupled(new QKVStreamBeat(p.qkv)))
    val out = Decoupled(new QKVStreamBeat(p.qkv))
  })

  io.qWeight.ready := true.B
  io.kWeight.ready := true.B
  io.in.ready := io.out.ready
  io.out.valid := io.in.valid
  io.out.bits := io.in.bits
}
