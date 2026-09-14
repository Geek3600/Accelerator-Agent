package Softmax

import QuantCommon._
import QuantCommon.Precision._
import chisel3._

class Fp32ExpApprox extends Module {
  import FP32Param._

  private def fp32Const(value: Float): UInt =
    java.lang.Integer.toUnsignedLong(java.lang.Float.floatToRawIntBits(value)).U(FP32_WIDTH.W)

  private val inputFrac = 9
  private val probFrac = 16
  private val inputWidth = FIXED_INT_WIDTH + inputFrac
  private val expLutWidth = probFrac + 2
  private val log2e = Math.round(Math.log(Math.E) / Math.log(2.0) * (1 << inputFrac)).S(inputWidth.W)

  val io = IO(new Bundle {
    val in = Input(UInt(FP32_WIDTH.W))
    val out = Output(UInt(FP32_WIDTH.W))
  })

  val scaleUp = fp32Const((1 << inputFrac).toFloat)
  val scaleDown = fp32Const(1.0f / (1 << probFrac).toFloat)
  val exp2Lut = VecInit(
    (0 until (1 << inputFrac)).map { frac =>
      val value = Math.round(Math.pow(2.0, frac.toDouble / (1 << inputFrac)) * (1 << probFrac)).toLong
      value.U(expLutWidth.W)
    }
  )

  val mulScale = Module(new Fp32Mul)
  mulScale.io.a := io.in
  mulScale.io.b := scaleUp

  val toInt = Module(new Fp32ToSInt(inputWidth))
  toInt.io.in := mulScale.io.out
  val xFixed = toInt.io.out.asSInt

  val full = Wire(SInt((2 * inputWidth).W))
  full := xFixed * log2e
  val xLog2e = (full >> inputFrac).asSInt

  val intPart = xLog2e >> inputFrac
  val fracRaw = (xLog2e - (intPart << inputFrac)).asUInt
  val fracPart = fracRaw(inputFrac - 1, 0)
  val base = exp2Lut(fracPart)
  val shiftedBase = Mux(
    intPart >= 0.S,
    base << intPart.asUInt,
    base >> (-intPart).asUInt,
  )

  val toFp = Module(new UIntToFp32(probFrac + FIXED_INT_WIDTH + 2))
  toFp.io.in := shiftedBase

  val mulDown = Module(new Fp32Mul)
  mulDown.io.a := toFp.io.out
  mulDown.io.b := scaleDown
  io.out := mulDown.io.out
}

class OnlineSoftmaxStats extends Module {
  private def fp32Const(value: Float): UInt =
    java.lang.Integer.toUnsignedLong(java.lang.Float.floatToRawIntBits(value)).U(FP32_WIDTH.W)

  val io = IO(new Bundle {
    val start = Input(Bool())
    val data_in = Input(UInt(FP32_WIDTH.W))
    val data_in_valid = Input(Bool())
    val data_in_last = Input(Bool())

    val max_out = Output(UInt(FP32_WIDTH.W))
    val denom_out = Output(UInt(FP32_WIDTH.W))
    val out_valid = Output(Bool())
  })

  val maxReg = RegInit(0.U(FP32_WIDTH.W))
  val denomReg = RegInit(0.U(FP32_WIDTH.W))
  val seenAny = RegInit(false.B)

  val cmp = Module(new Fp32Compare)
  cmp.io.a := io.data_in
  cmp.io.b := maxReg
  val useInputAsMax = !seenAny || cmp.io.gt
  val newMax = Mux(useInputAsMax, io.data_in, maxReg)

  val oldShift = Module(new Fp32Sub)
  oldShift.io.a := maxReg
  oldShift.io.b := newMax

  val curShift = Module(new Fp32Sub)
  curShift.io.a := io.data_in
  curShift.io.b := newMax

  val expOld = Module(new Fp32ExpApprox)
  expOld.io.in := Mux(seenAny, oldShift.io.out, 0.U)

  val expCur = Module(new Fp32ExpApprox)
  expCur.io.in := curShift.io.out

  val scaledOldDenom = Module(new Fp32Mul)
  scaledOldDenom.io.a := Mux(seenAny, denomReg, 0.U)
  scaledOldDenom.io.b := expOld.io.out

  val nextDenom = Module(new Fp32Add)
  nextDenom.io.a := scaledOldDenom.io.out
  nextDenom.io.b := expCur.io.out

  when(io.start) {
    seenAny := false.B
    maxReg := 0.U
    denomReg := 0.U
  }.elsewhen(io.data_in_valid) {
    maxReg := newMax
    denomReg := Mux(seenAny, nextDenom.io.out, fp32Const(1.0f))
    seenAny := true.B
  }

  io.max_out := maxReg
  io.denom_out := denomReg
  io.out_valid := RegNext(io.data_in_valid && io.data_in_last, false.B)
}
