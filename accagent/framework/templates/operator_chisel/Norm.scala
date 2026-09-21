package spatialaccagent.templates

import chisel3._
import chisel3.util._

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

  val gammaMem = Module(new PhysicalSimpleDualPortMemory(p.beats, p.inputBeatBits, "weight"))
  val betaMem = if (p.hasBeta) {
    Some(Module(new PhysicalSimpleDualPortMemory(p.beats, p.inputBeatBits, "weight")))
  } else None
  val inputMem = Module(new PhysicalSimpleDualPortMemory(p.beats, p.inputBeatBits, "activation"))
  private val metaBits = p.addrBits + 2
  val inputMetaMem = Module(new PhysicalSimpleDualPortMemory(p.beats, metaBits, "activation"))

  val weightCnt = RegInit(0.U(log2Ceil(p.weightBeats max 2).W))
  val weightsLoaded = RegInit(false.B)
  io.weight.ready := !weightsLoaded

  gammaMem.io.writeEn := false.B
  gammaMem.io.writeAddr := 0.U
  gammaMem.io.writeData := io.weight.bits
  betaMem.foreach { mem =>
    mem.io.writeEn := false.B
    mem.io.writeAddr := 0.U
    mem.io.writeData := io.weight.bits
  }

  when(io.weight.fire) {
    if (p.hasBeta) {
      when(weightCnt < p.beats.U) {
        betaMem.get.io.writeEn := true.B
        betaMem.get.io.writeAddr := weightCnt
      }.otherwise {
        gammaMem.io.writeEn := true.B
        gammaMem.io.writeAddr := weightCnt - p.beats.U
      }
    } else {
      gammaMem.io.writeEn := true.B
      gammaMem.io.writeAddr := weightCnt
    }
    when(weightCnt === (p.weightBeats - 1).U) {
      weightCnt := 0.U
      weightsLoaded := true.B
    }.otherwise {
      weightCnt := weightCnt + 1.U
    }
  }

  private val states = Enum(32)
  private val sCollect = states(0)
  private val sAccumRead = states(1)
  private val sAccumCapture = states(2)
  private val sLaneIssue = states(3)
  private val sLaneWait = states(4)
  private val sSquareAddIssue = states(5)
  private val sSquareAddWait = states(6)
  private val sMeanIssue = states(7)
  private val sMeanWait = states(8)
  private val sMeanSquareIssue = states(9)
  private val sMeanSquareWait = states(10)
  private val sVarianceSubIssue = states(11)
  private val sVarianceSubWait = states(12)
  private val sVarianceCompareIssue = states(13)
  private val sVarianceCompareWait = states(14)
  private val sEpsilonIssue = states(15)
  private val sEpsilonWait = states(16)
  private val sSqrtIssue = states(17)
  private val sSqrtWait = states(18)
  private val sRecipIssue = states(19)
  private val sRecipWait = states(20)
  private val sEmitRead = states(21)
  private val sEmitCapture = states(22)
  private val sCenterIssue = states(23)
  private val sCenterWait = states(24)
  private val sNormalizeIssue = states(25)
  private val sNormalizeWait = states(26)
  private val sScaleIssue = states(27)
  private val sScaleWait = states(28)
  private val sBetaIssue = states(29)
  private val sBetaWait = states(30)
  private val sEmit = states(31)
  val state = RegInit(sCollect)
  val inputCnt = RegInit(0.U(log2Ceil(p.beats max 2).W))
  val accumBeat = RegInit(0.U(log2Ceil(p.beats max 2).W))
  val accumLane = RegInit(0.U(log2Ceil(p.lanes max 2).W))
  val outputCnt = RegInit(0.U(log2Ceil(p.beats max 2).W))

  val inputBeatReg = Reg(UInt(p.inputBeatBits.W))
  val inputMetaReg = Reg(UInt(metaBits.W))
  val gammaReg = Reg(UInt(p.inputBeatBits.W))
  val betaReg = Reg(UInt(p.inputBeatBits.W))
  val sumReg = RegInit(PhysicalMath.fp32Zero)
  val squareSumReg = RegInit(PhysicalMath.fp32Zero)
  val squareValueReg = Reg(UInt(32.W))
  val sumDone = RegInit(false.B)
  val squareDone = RegInit(false.B)
  val meanReg = Reg(UInt(32.W))
  val meanSquareReg = Reg(UInt(32.W))
  val centeredVarianceReg = Reg(UInt(32.W))
  val varianceReg = Reg(UInt(32.W))
  val denominatorReg = Reg(UInt(32.W))
  val inverseReg = Reg(UInt(32.W))
  val laneValueReg = Reg(Vec(p.lanes, UInt(32.W)))
  val outputDataReg = Reg(Vec(p.lanes, UInt(p.outputBits.W)))

  inputMem.io.writeEn := io.in.fire
  inputMem.io.writeAddr := inputCnt
  inputMem.io.writeData := io.in.bits.data
  inputMetaMem.io.writeEn := io.in.fire
  inputMetaMem.io.writeAddr := inputCnt
  inputMetaMem.io.writeData := Cat(io.in.bits.last, io.in.bits.addr, io.in.bits.st)

  io.in.ready := state === sCollect && weightsLoaded
  when(io.in.fire) {
    when(inputCnt === (p.beats - 1).U) {
      inputCnt := 0.U
      accumBeat := 0.U
      accumLane := 0.U
      sumReg := PhysicalMath.fp32Zero
      squareSumReg := PhysicalMath.fp32Zero
      state := sAccumRead
    }.otherwise {
      inputCnt := inputCnt + 1.U
    }
  }

  val readingAccum = state === sAccumRead
  val readingEmit = state === sEmitRead
  inputMem.io.readEn := readingAccum || readingEmit
  inputMem.io.readAddr := Mux(readingAccum, accumBeat, outputCnt)
  inputMetaMem.io.readEn := readingEmit
  inputMetaMem.io.readAddr := outputCnt
  gammaMem.io.readEn := readingEmit
  gammaMem.io.readAddr := outputCnt
  betaMem.foreach { mem =>
    mem.io.readEn := readingEmit
    mem.io.readAddr := outputCnt
  }

  when(state === sAccumRead) {
    state := sAccumCapture
  }
  when(state === sAccumCapture) {
    inputBeatReg := inputMem.io.readData
    accumLane := 0.U
    state := sLaneIssue
  }

  val accumValues = inputBeatReg.asTypeOf(Vec(p.lanes, UInt(p.inputBits.W)))
  val accumValueFp32 = PhysicalMath.toFp32(
    accumValues(AccMath.boundedIndex(accumLane, p.lanes)),
    p.inputBits
  )
  val squareMul = Module(new PhysicalFp32Mul)
  squareMul.io.a := accumValueFp32
  squareMul.io.b := accumValueFp32
  val sumAdd = Module(new PhysicalFp32Add)
  sumAdd.io.a := sumReg
  sumAdd.io.b := accumValueFp32
  val laneIssue = state === sLaneIssue && squareMul.io.inReady && sumAdd.io.inReady
  squareMul.io.inValid := laneIssue
  sumAdd.io.inValid := laneIssue

  when(laneIssue) {
    sumDone := false.B
    squareDone := false.B
    state := sLaneWait
  }
  when(state === sLaneWait) {
    when(sumAdd.io.outValid) {
      sumReg := sumAdd.io.out
      sumDone := true.B
    }
    when(squareMul.io.outValid) {
      squareValueReg := squareMul.io.out
      squareDone := true.B
    }
    when((sumDone || sumAdd.io.outValid) && (squareDone || squareMul.io.outValid)) {
      state := sSquareAddIssue
    }
  }

  val squareAdd = Module(new PhysicalFp32Add)
  squareAdd.io.a := squareSumReg
  squareAdd.io.b := squareValueReg
  squareAdd.io.inValid := state === sSquareAddIssue && squareAdd.io.inReady
  when(state === sSquareAddIssue && squareAdd.io.inReady) {
    state := sSquareAddWait
  }
  when(state === sSquareAddWait && squareAdd.io.outValid) {
    squareSumReg := squareAdd.io.out
    when(accumLane === (p.lanes - 1).U) {
      accumLane := 0.U
      when(accumBeat === (p.beats - 1).U) {
        accumBeat := 0.U
        state := sMeanIssue
      }.otherwise {
        accumBeat := accumBeat + 1.U
        state := sAccumRead
      }
    }.otherwise {
      accumLane := accumLane + 1.U
      state := sLaneIssue
    }
  }

  val reciprocalHiddenSize = PhysicalMath.fp32Constant(1.0 / p.hiddenSize.toDouble)
  val meanMul = Module(new PhysicalFp32Mul)
  meanMul.io.a := sumReg
  meanMul.io.b := reciprocalHiddenSize
  val meanSquareMul = Module(new PhysicalFp32Mul)
  meanSquareMul.io.a := squareSumReg
  meanSquareMul.io.b := reciprocalHiddenSize
  val meanReady = meanMul.io.inReady && meanSquareMul.io.inReady
  val meanIssue = state === sMeanIssue && meanReady
  meanMul.io.inValid := meanIssue
  meanSquareMul.io.inValid := meanIssue
  when(meanIssue) {
    state := sMeanWait
  }
  when(state === sMeanWait && meanMul.io.outValid && meanSquareMul.io.outValid) {
    meanReg := Mux(p.hasMeanSub.B, meanMul.io.out, PhysicalMath.fp32Zero)
    meanSquareReg := meanSquareMul.io.out
    state := Mux(p.hasMeanSub.B, sMeanSquareIssue, sEpsilonIssue)
  }

  val meanSquared = Module(new PhysicalFp32Mul)
  meanSquared.io.a := meanReg
  meanSquared.io.b := meanReg
  meanSquared.io.inValid := state === sMeanSquareIssue && meanSquared.io.inReady
  when(state === sMeanSquareIssue && meanSquared.io.inReady) {
    state := sMeanSquareWait
  }
  when(state === sMeanSquareWait && meanSquared.io.outValid) {
    centeredVarianceReg := meanSquared.io.out
    state := sVarianceSubIssue
  }

  val varianceSub = Module(new PhysicalFp32Sub)
  varianceSub.io.a := meanSquareReg
  varianceSub.io.b := centeredVarianceReg
  varianceSub.io.inValid := state === sVarianceSubIssue && varianceSub.io.inReady
  when(state === sVarianceSubIssue && varianceSub.io.inReady) {
    state := sVarianceSubWait
  }
  when(state === sVarianceSubWait && varianceSub.io.outValid) {
    centeredVarianceReg := varianceSub.io.out
    state := sVarianceCompareIssue
  }

  val varianceCompare = Module(new PhysicalFp32CompareLt)
  varianceCompare.io.a := centeredVarianceReg
  varianceCompare.io.b := PhysicalMath.fp32Zero
  varianceCompare.io.inValid := state === sVarianceCompareIssue && varianceCompare.io.inReady
  when(state === sVarianceCompareIssue && varianceCompare.io.inReady) {
    state := sVarianceCompareWait
  }
  when(state === sVarianceCompareWait && varianceCompare.io.outValid) {
    centeredVarianceReg := Mux(varianceCompare.io.out(0), PhysicalMath.fp32Zero, centeredVarianceReg)
    state := sEpsilonIssue
  }

  val epsilonAdd = Module(new PhysicalFp32Add)
  epsilonAdd.io.a := Mux(p.hasMeanSub.B, centeredVarianceReg, meanSquareReg)
  epsilonAdd.io.b := PhysicalMath.fp32Constant(p.eps)
  epsilonAdd.io.inValid := state === sEpsilonIssue && epsilonAdd.io.inReady
  when(state === sEpsilonIssue && epsilonAdd.io.inReady) {
    state := sEpsilonWait
  }
  when(state === sEpsilonWait && epsilonAdd.io.outValid) {
    varianceReg := epsilonAdd.io.out
    state := sSqrtIssue
  }

  val sqrtUnit = Module(new PhysicalFp32Sqrt)
  sqrtUnit.io.inValid := state === sSqrtIssue && sqrtUnit.io.inReady
  sqrtUnit.io.in := varianceReg
  when(state === sSqrtIssue && sqrtUnit.io.inReady) {
    state := sSqrtWait
  }
  when(state === sSqrtWait && sqrtUnit.io.outValid) {
    denominatorReg := sqrtUnit.io.out
    state := sRecipIssue
  }

  val reciprocalUnit = Module(new PhysicalFp32Div)
  reciprocalUnit.io.inValid := state === sRecipIssue && reciprocalUnit.io.inReady
  reciprocalUnit.io.a := PhysicalMath.fp32One
  reciprocalUnit.io.b := denominatorReg
  when(state === sRecipIssue && reciprocalUnit.io.inReady) {
    state := sRecipWait
  }
  when(state === sRecipWait && reciprocalUnit.io.outValid) {
    inverseReg := reciprocalUnit.io.out
    outputCnt := 0.U
    state := sEmitRead
  }

  when(state === sEmitRead) {
    state := sEmitCapture
  }
  when(state === sEmitCapture) {
    inputBeatReg := inputMem.io.readData
    inputMetaReg := inputMetaMem.io.readData
    gammaReg := gammaMem.io.readData
    betaReg := betaMem.map(_.io.readData).getOrElse(0.U(p.inputBeatBits.W))
    if (p.hasMeanSub) {
      state := sCenterIssue
    } else {
      val inputValues = inputMem.io.readData.asTypeOf(Vec(p.lanes, UInt(p.inputBits.W)))
      for (lane <- 0 until p.lanes) {
        laneValueReg(lane) := PhysicalMath.toFp32(inputValues(lane), p.inputBits)
      }
      state := sNormalizeIssue
    }
  }

  val emitInputs = inputBeatReg.asTypeOf(Vec(p.lanes, UInt(p.inputBits.W)))
  val emitGamma = gammaReg.asTypeOf(Vec(p.lanes, UInt(p.inputBits.W)))
  val emitBeta = betaReg.asTypeOf(Vec(p.lanes, UInt(p.inputBits.W)))

  val centerSubtractors = if (p.hasMeanSub) {
    Seq.tabulate(p.lanes) { lane =>
      val sub = Module(new PhysicalFp32Sub)
      sub.io.a := PhysicalMath.toFp32(emitInputs(lane), p.inputBits)
      sub.io.b := meanReg
      sub
    }
  } else Seq.empty
  val centerReady = if (p.hasMeanSub) centerSubtractors.map(_.io.inReady).reduce(_ && _) else true.B
  val centerIssue = state === sCenterIssue && centerReady
  centerSubtractors.foreach(_.io.inValid := centerIssue)
  when(centerIssue) {
    state := sCenterWait
  }
  if (p.hasMeanSub) {
    val centerValid = VecInit(centerSubtractors.map(_.io.outValid)).asUInt.andR
    when(state === sCenterWait && centerValid) {
      for (lane <- 0 until p.lanes) {
        laneValueReg(lane) := centerSubtractors(lane).io.out
      }
      state := sNormalizeIssue
    }
  }

  val normalizers = Seq.tabulate(p.lanes) { lane =>
    val mul = Module(new PhysicalFp32Mul)
    mul.io.a := laneValueReg(lane)
    mul.io.b := inverseReg
    mul
  }
  val normalizeReady = normalizers.map(_.io.inReady).reduce(_ && _)
  val normalizeIssue = state === sNormalizeIssue && normalizeReady
  normalizers.foreach(_.io.inValid := normalizeIssue)
  when(normalizeIssue) {
    state := sNormalizeWait
  }
  val normalizeValid = VecInit(normalizers.map(_.io.outValid)).asUInt.andR
  when(state === sNormalizeWait && normalizeValid) {
    for (lane <- 0 until p.lanes) {
      laneValueReg(lane) := normalizers(lane).io.out
    }
    state := sScaleIssue
  }

  val scalers = Seq.tabulate(p.lanes) { lane =>
    val mul = Module(new PhysicalFp32Mul)
    mul.io.a := laneValueReg(lane)
    mul.io.b := PhysicalMath.toFp32(emitGamma(lane), p.inputBits)
    mul
  }
  val scaleReady = scalers.map(_.io.inReady).reduce(_ && _)
  val scaleIssue = state === sScaleIssue && scaleReady
  scalers.foreach(_.io.inValid := scaleIssue)
  when(scaleIssue) {
    state := sScaleWait
  }
  val scaleValid = VecInit(scalers.map(_.io.outValid)).asUInt.andR
  when(state === sScaleWait && scaleValid) {
    for (lane <- 0 until p.lanes) {
      laneValueReg(lane) := scalers(lane).io.out
      if (!p.hasBeta) {
        outputDataReg(lane) := PhysicalMath.fromFp32(scalers(lane).io.out, p.outputBits)
      }
    }
    state := Mux(p.hasBeta.B, sBetaIssue, sEmit)
  }

  val betaAdders = if (p.hasBeta) {
    Seq.tabulate(p.lanes) { lane =>
      val add = Module(new PhysicalFp32Add)
      add.io.a := laneValueReg(lane)
      add.io.b := PhysicalMath.toFp32(emitBeta(lane), p.inputBits)
      add
    }
  } else Seq.empty
  val betaReady = if (p.hasBeta) betaAdders.map(_.io.inReady).reduce(_ && _) else true.B
  val betaIssue = state === sBetaIssue && betaReady
  betaAdders.foreach(_.io.inValid := betaIssue)
  when(betaIssue) {
    state := sBetaWait
  }
  if (p.hasBeta) {
    val betaValid = VecInit(betaAdders.map(_.io.outValid)).asUInt.andR
    when(state === sBetaWait && betaValid) {
      for (lane <- 0 until p.lanes) {
        outputDataReg(lane) := PhysicalMath.fromFp32(betaAdders(lane).io.out, p.outputBits)
      }
      state := sEmit
    }
  }

  io.out.valid := state === sEmit
  io.out.bits.data := outputDataReg.asUInt
  io.out.bits.st := inputMetaReg(0)
  io.out.bits.addr := inputMetaReg(p.addrBits, 1)
  io.out.bits.last := inputMetaReg(metaBits - 1)

  when(io.out.fire) {
    when(outputCnt === (p.beats - 1).U) {
      outputCnt := 0.U
      state := sCollect
    }.otherwise {
      outputCnt := outputCnt + 1.U
      state := sEmitRead
    }
  }

  dontTouch(io.cfg)
  dontTouch(io.cfgValid)
  dontTouch(io.quant)
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
