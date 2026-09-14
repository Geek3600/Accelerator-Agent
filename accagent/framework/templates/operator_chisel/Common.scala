package spatialaccagent.templates

import chisel3._
import chisel3.util._
import hardfloat._
import hardfloat.consts

object AccMath {
  def ceilDiv(a: Int, b: Int): Int = (a + b - 1) / b

  def resizeSigned(x: SInt, width: Int): SInt = resizeSignedToUInt(x, width).asSInt

  def resizeSignedToUInt(x: SInt, width: Int): UInt = {
    val u = x.asUInt
    if (width <= x.getWidth) {
      u(width - 1, 0)
    } else {
      Cat(Fill(width - x.getWidth, u(x.getWidth - 1)), u)
    }
  }
}

object IeeeMath {
  private val fp16ExpWidth = 5
  private val fp16SigWidth = 11
  private val fp32ExpWidth = 8
  private val fp32SigWidth = 24

  val fp32Zero: UInt = 0.U(32.W)
  val fp32One: UInt = "h3f800000".U(32.W)

  def fp32Constant(value: Double): UInt = {
    val bits = java.lang.Float.floatToRawIntBits(value.toFloat)
    BigInt(bits.toLong & 0xffffffffL).U(32.W)
  }

  def toFp32(value: UInt, bits: Int): UInt = {
    require(bits == 16 || bits == 32, s"IEEE input width must be 16 or 32, got $bits")
    if (bits == 32) {
      value
    } else {
      val convert = Module(new RecFNToRecFN(fp16ExpWidth, fp16SigWidth, fp32ExpWidth, fp32SigWidth))
      convert.io.in := recFNFromFN(fp16ExpWidth, fp16SigWidth, value)
      convert.io.roundingMode := consts.round_near_even
      convert.io.detectTininess := consts.tininess_afterRounding
      fNFromRecFN(fp32ExpWidth, fp32SigWidth, convert.io.out)
    }
  }

  def fromFp32(value: UInt, bits: Int): UInt = {
    require(bits == 16 || bits == 32, s"IEEE output width must be 16 or 32, got $bits")
    if (bits == 32) {
      value
    } else {
      val convert = Module(new RecFNToRecFN(fp32ExpWidth, fp32SigWidth, fp16ExpWidth, fp16SigWidth))
      convert.io.in := recFNFromFN(fp32ExpWidth, fp32SigWidth, value)
      convert.io.roundingMode := consts.round_near_even
      convert.io.detectTininess := consts.tininess_afterRounding
      fNFromRecFN(fp16ExpWidth, fp16SigWidth, convert.io.out)
    }
  }

  def addFp32(a: UInt, b: UInt): UInt = {
    val add = Module(new AddRecFN(fp32ExpWidth, fp32SigWidth))
    add.io.subOp := false.B
    add.io.a := recFNFromFN(fp32ExpWidth, fp32SigWidth, a)
    add.io.b := recFNFromFN(fp32ExpWidth, fp32SigWidth, b)
    add.io.roundingMode := consts.round_near_even
    add.io.detectTininess := consts.tininess_afterRounding
    fNFromRecFN(fp32ExpWidth, fp32SigWidth, add.io.out)
  }

  def subFp32(a: UInt, b: UInt): UInt = {
    val sub = Module(new AddRecFN(fp32ExpWidth, fp32SigWidth))
    sub.io.subOp := true.B
    sub.io.a := recFNFromFN(fp32ExpWidth, fp32SigWidth, a)
    sub.io.b := recFNFromFN(fp32ExpWidth, fp32SigWidth, b)
    sub.io.roundingMode := consts.round_near_even
    sub.io.detectTininess := consts.tininess_afterRounding
    fNFromRecFN(fp32ExpWidth, fp32SigWidth, sub.io.out)
  }

  def mulFp32(a: UInt, b: UInt): UInt = {
    val mul = Module(new MulRecFN(fp32ExpWidth, fp32SigWidth))
    mul.io.a := recFNFromFN(fp32ExpWidth, fp32SigWidth, a)
    mul.io.b := recFNFromFN(fp32ExpWidth, fp32SigWidth, b)
    mul.io.roundingMode := consts.round_near_even
    mul.io.detectTininess := consts.tininess_afterRounding
    fNFromRecFN(fp32ExpWidth, fp32SigWidth, mul.io.out)
  }

  def lessThanFp32(a: UInt, b: UInt): Bool = {
    val compare = Module(new CompareRecFN(fp32ExpWidth, fp32SigWidth))
    compare.io.a := recFNFromFN(fp32ExpWidth, fp32SigWidth, a)
    compare.io.b := recFNFromFN(fp32ExpWidth, fp32SigWidth, b)
    compare.io.signaling := false.B
    compare.io.lt
  }

  def sumFp32(values: Seq[UInt]): UInt = {
    require(values.nonEmpty, "sumFp32 requires at least one value")
    values.reduce((a, b) => addFp32(a, b))
  }
}

final case class StreamSpec(dataBits: Int, addrBits: Int) {
  require(dataBits > 0, "dataBits must be positive")
  require(addrBits > 0, "addrBits must be positive")
}

class StageConfig(seqBits: Int) extends Bundle {
  val seqlen = UInt(seqBits.W)
  val prefill = Bool()
  val singleQuery = Bool()
}

class StreamBeat(spec: StreamSpec) extends Bundle {
  val data = UInt(spec.dataBits.W)
  val st = Bool()
  val addr = UInt(spec.addrBits.W)
  val last = Bool()
}

class WeightWrite(dataBits: Int, addrBits: Int) extends Bundle {
  val addr = UInt(addrBits.W)
  val data = UInt(dataBits.W)
}

class Int8QuantPorts extends Bundle {
  val outInvScale = Input(UInt(32.W))
  val outZeroPoint = Input(SInt(8.W))
}

class LinearScalePorts extends Bundle {
  val outScale = Input(UInt(32.W))
  val biasScale = Input(UInt(32.W))
}
