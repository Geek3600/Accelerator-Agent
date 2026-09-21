package spatialaccagent.templates

import chisel3._
import chisel3.util._

object AccMath {
  def ceilDiv(a: Int, b: Int): Int = (a + b - 1) / b

  /** Keep a valid parameter-bound dynamic index at the width expected by Vec. */
  def boundedIndex(index: UInt, size: Int): UInt = {
    require(size > 0, "dynamic index size must be positive")
    if (size == 1) 0.U
    else {
      val width = log2Ceil(size)
      if (index.getWidth > width) index(width - 1, 0) else index.pad(width)
    }
  }

  def resizeSigned(x: SInt, width: Int): SInt = resizeSignedToUInt(x, width).asSInt

  def resizeSignedToUInt(x: SInt, width: Int): UInt = {
    val u = x.asUInt
    if (width <= x.getWidth) u(width - 1, 0)
    else Cat(Fill(width - x.getWidth, u(x.getWidth - 1)), u)
  }
}

/**
  * Physical arithmetic facade used by all trusted templates. Each operation
  * instantiates the matching Vivado floating_point IP; there is no behavioral
  * floating-point or HardFloat implementation in the generated template set.
  */
object PhysicalMath {
  val fp32Zero: UInt = 0.U(32.W)
  val fp32One: UInt = "h3f800000".U(32.W)

  def fp32Constant(value: Double): UInt = {
    val bits = java.lang.Float.floatToRawIntBits(value.toFloat)
    BigInt(bits.toLong & 0xffffffffL).U(32.W)
  }

  def toFp32(value: UInt, bits: Int): UInt = {
    require(bits == 16 || bits == 32, s"IEEE input width must be 16 or 32, got $bits")
    if (bits == 32) value else {
      val convert = Module(new PhysicalFp16ToFp32)
      convert.io.in := value
      convert.io.out
    }
  }

  def fromFp32(value: UInt, bits: Int): UInt = {
    require(bits == 16 || bits == 32, s"IEEE output width must be 16 or 32, got $bits")
    if (bits == 32) value else {
      val convert = Module(new PhysicalFp32ToFp16)
      convert.io.in := value
      convert.io.out
    }
  }

  private def binary(a: UInt, b: UInt, op: String): UInt = op match {
    case "add" =>
      val unit = Module(new PhysicalFp32Add)
      unit.io.inValid := true.B
      unit.io.a := a
      unit.io.b := b
      unit.io.out
    case "sub" =>
      val unit = Module(new PhysicalFp32Sub)
      unit.io.inValid := true.B
      unit.io.a := a
      unit.io.b := b
      unit.io.out
    case "mul" =>
      val unit = Module(new PhysicalFp32Mul)
      unit.io.inValid := true.B
      unit.io.a := a
      unit.io.b := b
      unit.io.out
    case "div" =>
      val unit = Module(new PhysicalFp32Div)
      unit.io.inValid := true.B
      unit.io.a := a
      unit.io.b := b
      unit.io.out
    case other => throw new IllegalArgumentException(s"unsupported FP32 operation: $other")
  }

  def addFp32(a: UInt, b: UInt): UInt = binary(a, b, "add")
  def subFp32(a: UInt, b: UInt): UInt = binary(a, b, "sub")
  def mulFp32(a: UInt, b: UInt): UInt = binary(a, b, "mul")
  def divFp32(a: UInt, b: UInt): UInt = binary(a, b, "div")

  def lessThanFp32(a: UInt, b: UInt): Bool = {
    val compare = Module(new PhysicalFp32CompareLt)
    compare.io.inValid := true.B
    compare.io.a := a
    compare.io.b := b
    compare.io.out(0)
  }

  def sumFp32(values: Seq[UInt]): UInt = {
    require(values.nonEmpty, "sumFp32 requires at least one value")
    values.reduce((a, b) => addFp32(a, b))
  }

  def fp32ToSigned(value: UInt, width: Int): SInt = {
    val convert = Module(new PhysicalFp32ToSigned(width))
    convert.io.inValid := true.B
    convert.io.in := value
    convert.io.out
  }

  def signedToFp32(value: SInt): UInt = {
    val convert = Module(new PhysicalSignedToFp32(value.getWidth))
    convert.io.inValid := true.B
    convert.io.in := value
    convert.io.out
  }

  def unsignedToFp32(value: UInt): UInt = {
    val convert = Module(new PhysicalUIntToFp32(value.getWidth))
    convert.io.inValid := true.B
    convert.io.in := value
    convert.io.out
  }
}

/** Compatibility constants for already-materialized semantic harnesses. */
object IeeeMath {
  val fp32Zero: UInt = PhysicalMath.fp32Zero
  val fp32One: UInt = PhysicalMath.fp32One
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
