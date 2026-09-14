package Softmax

import QuantCommon.{Fp32DivSqrt, Fp32Mul, Fp32MulComb, Fp32ToSInt, Fp32ToSIntComb, FpBackend, UIntToFp32, UIntToFp32Comb, XilinxFpTargetConfig}
import QuantCommon.Precision._
import chisel3._
import chisel3.util._

class SoftmaxTileKernel extends Module {
  import FP32Param._

  private def fp32Const(value: Float): UInt =
    java.lang.Integer.toUnsignedLong(java.lang.Float.floatToRawIntBits(value)).U(FP32_WIDTH.W)

  private val TileV = TILE_SEQLEN
  private val inputFrac = 9
  private val probFrac = 16
  private val inputWidth = FIXED_INT_WIDTH + inputFrac
  private val expLutWidth = probFrac + 2
  private val expValWidth = probFrac + FIXED_INT_WIDTH + 2
  private val sumWidth = expValWidth + log2Ceil(SEQ_LEN + 1)

  val io = IO(new Bundle {
    val in = Input(Vec(TileV, UInt(FP32_WIDTH.W)))
    val inMask = Input(Vec(TileV, Bool()))
    val refMax = Input(SInt(inputWidth.W))

    val localMax = Output(SInt(inputWidth.W))
    val tileSum = Output(UInt(sumWidth.W))
    val expVals = Output(Vec(TileV, UInt(expValWidth.W)))
  })

  val scaleUp = fp32Const((1 << inputFrac).toFloat)
  val negInf = (-(1 << (inputWidth - 1))).S(inputWidth.W)
  val log2e = Math.round(Math.log(Math.E) / Math.log(2.0) * (1 << inputFrac)).S(inputWidth.W)
  val exp2Lut = VecInit(
    (0 until (1 << inputFrac)).map { frac =>
      val value = Math.round(Math.pow(2.0, frac.toDouble / (1 << inputFrac)) * (1 << probFrac)).toLong
      value.U(expLutWidth.W)
    }
  )

  val rawFixed = Wire(Vec(TileV, SInt(inputWidth.W)))
  val inFixed = Wire(Vec(TileV, SInt(inputWidth.W)))
  for (i <- 0 until TileV) {
    val fixedVal = Wire(SInt(inputWidth.W))
    if (FpBackend.useVivadoIp) {
      val mul = Module(new Fp32Mul)
      val toInt = Module(new Fp32ToSInt(inputWidth))
      mul.io.a := io.in(i)
      mul.io.b := scaleUp
      toInt.io.in := mul.io.out
      fixedVal := toInt.io.out.asSInt
    } else {
      val mul = Module(new Fp32MulComb)
      val toInt = Module(new Fp32ToSIntComb(inputWidth))
      mul.io.a := io.in(i)
      mul.io.b := scaleUp
      toInt.io.in := mul.io.out
      fixedVal := toInt.io.out.asSInt
    }
    rawFixed(i) := fixedVal
    inFixed(i) := Mux(io.inMask(i), fixedVal, negInf)
  }

  io.localMax := inFixed.reduceTree((a, b) => Mux(a > b, a, b))

  val shifted = Wire(Vec(TileV, SInt(inputWidth.W)))
  for (i <- 0 until TileV) {
    shifted(i) := rawFixed(i) - io.refMax
  }

  val xsMulLog2e = Wire(Vec(TileV, SInt(inputWidth.W)))
  for (i <- 0 until TileV) {
    val full = Wire(SInt((2 * inputWidth).W))
    full := shifted(i) * log2e
    xsMulLog2e(i) := (full >> inputFrac).asSInt
  }

  val xsMulLog2eReg = RegInit(VecInit(Seq.fill(TileV)(0.S(inputWidth.W))))
  val expMaskReg = RegInit(VecInit(Seq.fill(TileV)(false.B)))
  xsMulLog2eReg := xsMulLog2e
  expMaskReg := io.inMask

  val expVals = Wire(Vec(TileV, UInt(expValWidth.W)))
  for (i <- 0 until TileV) {
    val intPart = xsMulLog2eReg(i) >> inputFrac
    val fracRaw = (xsMulLog2eReg(i) - (intPart << inputFrac)).asUInt
    val fracPart = fracRaw(inputFrac - 1, 0)
    val base = exp2Lut(fracPart)
    val baseWide = Cat(0.U((expValWidth - expLutWidth).W), base)
    val shiftedBase = Wire(UInt(expValWidth.W))
    shiftedBase := Mux(
      intPart >= 0.S,
      (baseWide << intPart.asUInt)(expValWidth - 1, 0),
      baseWide >> (-intPart).asUInt
    )
    expVals(i) := Mux(expMaskReg(i), shiftedBase, 0.U)
    io.expVals(i) := expVals(i)
  }

  val tileSumWide = expVals.map(_.zext).reduceLeft(_ +& _)
  io.tileSum := tileSumWide.asUInt
}

class SoftmaxTileNormalize extends Module {
  import FP32Param._

  private val TileV = TILE_SEQLEN
  private val probFrac = 16
  private val expValWidth = probFrac + FIXED_INT_WIDTH + 2
  private val zeroFp = 0.U(FP32_WIDTH.W)

  val io = IO(new Bundle {
    val expVals = Input(Vec(TileV, UInt(expValWidth.W)))
    val inMask = Input(Vec(TileV, Bool()))
    val invSum = Input(UInt(FP32_WIDTH.W))
    val out = Output(Vec(TileV, UInt(FP32_WIDTH.W)))
  })

  for (i <- 0 until TileV) {
    val outVal = Wire(UInt(FP32_WIDTH.W))
    if (FpBackend.useVivadoIp) {
      val toFp = Module(new UIntToFp32(expValWidth))
      val mul = Module(new Fp32Mul)
      toFp.io.in := io.expVals(i)
      mul.io.a := toFp.io.out
      mul.io.b := io.invSum
      outVal := mul.io.out
    } else {
      val toFp = Module(new UIntToFp32Comb(expValWidth))
      val mul = Module(new Fp32MulComb)
      toFp.io.in := io.expVals(i)
      mul.io.a := toFp.io.out
      mul.io.b := io.invSum
      outVal := mul.io.out
    }
    io.out(i) := Mux(io.inMask(i), outVal, zeroFp)
  }
}

class SoftmaxPipFP32 extends Module {
  import FP32Param._

  private def fp32Const(value: Float): UInt =
    java.lang.Integer.toUnsignedLong(java.lang.Float.floatToRawIntBits(value)).U(FP32_WIDTH.W)

  private val TileV = TILE_SEQLEN
  private val inputFrac = 9
  private val probFrac = 16
  private val inputWidth = FIXED_INT_WIDTH + inputFrac
  private val expValWidth = probFrac + FIXED_INT_WIDTH + 2
  private val sumWidth = expValWidth + log2Ceil(SEQ_LEN + 1)

  val io = IO(new Bundle() {
    val cfg_seqlen = Input(UInt(log2Up(SEQ_LEN).W))
    val cfg_prefill = Input(Bool())
    val cfg_valid = Input(Bool())
    val cfg_single_query = Input(Bool())

    val layer_st = Input(Bool())
    val data_in_st = Input(Bool())
    val data_in = Input(UInt(MEM_WIDTH.W))
    val data_addr = Input(UInt(log2Up(SEQ_LEN).W))
    val data_valid = Input(Bool())
    val data_last = Input(Bool())
    val data_ready= Output(Bool())

    val w_in = Input(UInt(WMEM_WIDTH.W))
    val w_addr = Output(UInt(log2Up(WMEM_DEPTH).W))

    val res = Output(UInt(MEM_WIDTH.W))
    val res_st = Output(Bool())
    val res_addr = Output(UInt(log2Up(SEQ_LEN).W))
    val res_valid = Output(Bool())
    val res_last = Output(Bool())
    val res_ready = Input(Bool())
  })

  val singleQueryCfg = true.B
  val prefillCfg = false.B
  val seqlenCfg = RegEnable(io.cfg_seqlen, 0.U, io.cfg_valid)
  val maskAddrReg = RegInit(0.U(log2Up(WMEM_DEPTH).W))
  val maskVec = io.w_in.asTypeOf(Vec(WMEM_WIDTH, Bool()))
  val inputTileReg =
    if (FpBackend.useVivadoIp) Reg(UInt(MEM_WIDTH.W))
    else RegInit(0.U(MEM_WIDTH.W))
  val maskReg =
    if (FpBackend.useVivadoIp) Reg(UInt(TILE_SEQLEN.W))
    else RegInit(0.U(TILE_SEQLEN.W))
  val rowStartReg = RegInit(false.B)
  val rowAddrReg = RegInit(0.U(log2Up(SEQ_LEN).W))
  val globalMaxReg = RegInit(0.S(inputWidth.W))
  val sumExpReg = RegInit(0.U(sumWidth.W))
  val invSumReg = RegInit(0.U(FP32_WIDTH.W))
  val expTileReg =
    if (FpBackend.useVivadoIp) Reg(Vec(TileV, UInt(expValWidth.W)))
    else RegInit(VecInit(Seq.fill(TileV)(0.U(expValWidth.W))))
  val outDataReg =
    if (FpBackend.useVivadoIp) Reg(UInt(MEM_WIDTH.W))
    else RegInit(0.U(MEM_WIDTH.W))
  val outValidReg = RegInit(false.B)
  val outStReg = RegInit(false.B)
  val outLastReg = RegInit(false.B)
  val outAddrReg = RegInit(0.U(log2Up(SEQ_LEN).W))

  val Seq(
    stCollect,
    stPassMaxEval,
    stPassSumEval,
    stPassSumCapture,
    stRecipStart,
    stRecipWait,
    stPassOutLaunch,
    stPassOutWait,
    stPassOutHold
  ) = Enum(9)
  val state = RegInit(stCollect)

  val kernel = Module(new SoftmaxTileKernel)
  val normalize = Module(new SoftmaxTileNormalize)
  val tileIn = inputTileReg.asTypeOf(Vec(TileV, UInt(FP32_WIDTH.W)))
  val tileMaskBits = maskReg.asBools
  val tileMask = Wire(Vec(TileV, Bool()))
  for (i <- 0 until TileV)
    tileMask(i) := tileMaskBits(i)

  kernel.io.in := tileIn
  kernel.io.inMask := tileMask
  kernel.io.refMax := globalMaxReg

  val outExpVals = expTileReg
  val outMaskBits = maskReg.asBools
  val outMask = Wire(Vec(TileV, Bool()))
  for (i <- 0 until TileV) {
    outMask(i) := outMaskBits(i)
    normalize.io.expVals(i) := outExpVals(i)
  }
  normalize.io.inMask := outMask
  normalize.io.invSum := invSumReg

  val recipToFpOut = Wire(UInt(FP32_WIDTH.W))
  if (FpBackend.useVivadoIp) {
    val recipToFp = Module(new UIntToFp32(sumWidth))
    recipToFp.io.in := sumExpReg
    recipToFpOut := recipToFp.io.out
  } else {
    val recipToFp = Module(new UIntToFp32Comb(sumWidth))
    recipToFp.io.in := sumExpReg
    recipToFpOut := recipToFp.io.out
  }
  val recipDiv = Module(new Fp32DivSqrt)
  recipDiv.io.sqrtOp := false.B
  recipDiv.io.a := fp32Const(1.0f)
  recipDiv.io.b := recipToFpOut
  val recipStart = state === stRecipStart && recipDiv.io.inReady
  val recipToFpValidRegs = RegInit(VecInit(Seq.fill(XilinxFpTargetConfig.FixedToFloatLatency)(false.B)))
  recipToFpValidRegs(0) := recipStart
  for (i <- 1 until XilinxFpTargetConfig.FixedToFloatLatency) {
    recipToFpValidRegs(i) := recipToFpValidRegs(i - 1)
  }
  val recipToFpValid = recipToFpValidRegs.last
  recipDiv.io.inValid := recipToFpValid
  val normLatency = XilinxFpTargetConfig.FixedToFloatLatency + XilinxFpTargetConfig.MulLatency
  val normStart = state === stPassOutLaunch
  val normValidRegs = RegInit(VecInit(Seq.fill(normLatency)(false.B)))
  normValidRegs(0) := normStart
  for (i <- 1 until normLatency) {
    normValidRegs(i) := normValidRegs(i - 1)
  }
  val normValid = normValidRegs.last

  val inputFire = state === stCollect && io.data_valid && io.data_ready
  val rowVisibleLimit = Mux(singleQueryCfg, seqlenCfg, io.data_addr)
  val collectMask = Wire(Vec(TileV, Bool()))
  for (i <- 0 until TileV) {
    val laneAbs = i.U
    val maskLaneIdx = laneAbs(log2Ceil(WMEM_WIDTH) - 1, 0)
    val inWindow = laneAbs <= seqlenCfg
    val visible = laneAbs <= rowVisibleLimit
    collectMask(i) := inWindow && visible && maskVec(maskLaneIdx)
  }

  when(io.cfg_valid || io.layer_st) {
    maskAddrReg := 0.U
  }

  when(inputFire) {
    inputTileReg := io.data_in
    maskReg := collectMask.asUInt
    when(io.data_in_st) {
      rowStartReg := true.B
      rowAddrReg := io.data_addr
    }
    when(io.data_last) {
      globalMaxReg := (-(1 << (inputWidth - 1))).S(inputWidth.W)
      sumExpReg := 0.U
      invSumReg := 0.U
      state := stPassMaxEval
    }
  }.elsewhen(state === stPassMaxEval) {
    globalMaxReg := kernel.io.localMax
    state := stPassSumEval
  }.elsewhen(state === stPassSumEval) {
    state := stPassSumCapture
  }.elsewhen(state === stPassSumCapture) {
    expTileReg := kernel.io.expVals
    sumExpReg := kernel.io.tileSum
    state := stRecipStart
  }.elsewhen(state === stRecipStart && recipDiv.io.inReady) {
    state := stRecipWait
  }.elsewhen(state === stRecipWait && recipDiv.io.outValidDiv) {
    invSumReg := recipDiv.io.out
    state := stPassOutLaunch
  }.elsewhen(state === stPassOutLaunch) {
    outStReg := rowStartReg
    outLastReg := true.B
    outAddrReg := rowAddrReg
    state := stPassOutWait
  }.elsewhen(state === stPassOutWait && normValid) {
    outDataReg := normalize.io.out.asUInt
    outValidReg := true.B
    state := stPassOutHold
  }.elsewhen(state === stPassOutHold && outValidReg && io.res_ready) {
    outValidReg := false.B
    state := stCollect
    rowStartReg := false.B
  }

  when(io.cfg_valid || io.layer_st) {
    outValidReg := false.B
  }

  when(state === stCollect && inputFire && io.data_last) {
    outValidReg := false.B
  }

  io.data_ready := state === stCollect
  io.w_addr := maskAddrReg
  io.res := outDataReg
  io.res_st := outStReg
  io.res_addr := outAddrReg
  io.res_valid := outValidReg
  io.res_last := outLastReg && outValidReg
}

object SoftmaxPipFP32Gen extends App {
  emitVerilog(new SoftmaxPipFP32, Array("--target-dir", "generated"))
}
