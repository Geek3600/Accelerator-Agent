package Softmax

import QuantCommon._
import QuantCommon.Precision._
import chisel3._
import chisel3.util._
import _root_.circt.stage.ChiselStage

class SoftmaxFP32 extends Module {
  import FP32Param._

  private def fp32Const(value: Float): UInt =
    java.lang.Integer.toUnsignedLong(java.lang.Float.floatToRawIntBits(value)).U(FP32_WIDTH.W)

  private val inputFrac = 9
  private val probFrac = 16
  private val inputWidth = FIXED_INT_WIDTH + inputFrac
  private val expLutWidth = probFrac + 2
  private val probWidth = probFrac + 2
  val io = IO(new Bundle {
    val in = Input(Vec(V, UInt(FP32_WIDTH.W)))
    val in_mask = Input(Vec(V, Bool()))
    val out = Output(Vec(V, UInt(FP32_WIDTH.W)))
  })

  val scaleUp = fp32Const((1 << inputFrac).toFloat)
  val scaleDown = fp32Const((1.0f / (1 << probFrac).toFloat))
  val zeroFp = 0.U(FP32_WIDTH.W)
  val negInf = (-(1 << (inputWidth - 1))).S(inputWidth.W)
  val log2e = Math.round(Math.log(Math.E) / Math.log(2.0) * (1 << inputFrac)).S(inputWidth.W)
  val exp2Lut = VecInit(
    (0 until (1 << inputFrac)).map { frac =>
      val value = Math.round(Math.pow(2.0, frac.toDouble / (1 << inputFrac)) * (1 << probFrac)).toLong
      value.U(expLutWidth.W)
    }
  )

  val inFixed = Wire(Vec(V, SInt(inputWidth.W)))
  for (i <- 0 until V) {
    val mul = Module(new Fp32Mul)
    val toInt = Module(new Fp32ToSInt(inputWidth))
    mul.io.a := io.in(i)
    mul.io.b := scaleUp
    toInt.io.in := mul.io.out
    inFixed(i) := Mux(io.in_mask(i), toInt.io.out.asSInt, negInf)
  }

  val maxVal = inFixed.reduceTree((a, b) => Mux(a > b, a, b))
  val shifted = Wire(Vec(V, SInt(inputWidth.W)))
  for (i <- 0 until V) {
    shifted(i) := inFixed(i) - maxVal
  }

  val xsMulLog2e = Wire(Vec(V, SInt(inputWidth.W)))
  for (i <- 0 until V) {
    val full = Wire(SInt((2 * inputWidth).W))
    full := shifted(i) * log2e
    xsMulLog2e(i) := (full >> inputFrac).asSInt
  }

  val anyValid = io.in_mask.reduce(_ || _)
  val expVals = Wire(Vec(V, UInt((probFrac + FIXED_INT_WIDTH + 2).W)))
  for (i <- 0 until V) {
    val intPart = xsMulLog2e(i) >> inputFrac
    val fracRaw = (xsMulLog2e(i) - (intPart << inputFrac)).asUInt
    val fracPart = fracRaw(inputFrac - 1, 0)
    val base = exp2Lut(fracPart)
    val shiftedBase = Mux(
      intPart >= 0.S,
      base << intPart.asUInt,
      base >> (-intPart).asUInt,
    )
    expVals(i) := Mux(io.in_mask(i), shiftedBase, 0.U)
  }

  val sumExp = expVals.reduceTree(_ +& _)
  for (i <- 0 until V) {
    val probFixed = WireDefault(0.U(probWidth.W))
    when(anyValid && io.in_mask(i) && sumExp =/= 0.U) {
      probFixed := ((expVals(i) << probFrac) / sumExp)(probWidth - 1, 0)
    }

    val toFp = Module(new UIntToFp32(probWidth))
    val mul = Module(new Fp32Mul)
    toFp.io.in := probFixed
    mul.io.a := toFp.io.out
    mul.io.b := scaleDown
    io.out(i) := Mux(anyValid && io.in_mask(i), mul.io.out, zeroFp)
  }
}

object SoftmaxFP32 extends App {
  ChiselStage.emitSystemVerilogFile(
    new SoftmaxFP32,
    firtoolOpts = Array("-disable-all-randomization", "-strip-debug-info")
  )
}
