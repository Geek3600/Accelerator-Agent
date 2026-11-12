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

  /** Compose independent unsigned Q31 matrix, activation, and output scales.
    * Each input is a positive unsigned fixed-point multiplier. The two
    * products are reduced after every Q31 multiplication so the result remains
    * a usable Q31 multiplier for the real integer requantizer.
    */
  def composeQ31Scales(matrixScale: UInt, activationScale: UInt, outputScale: UInt): UInt = {
    require(matrixScale.getWidth == 32 && activationScale.getWidth == 32 && outputScale.getWidth == 32,
      "W4A8 scale composition requires three 32-bit Q31 multipliers")
    val matrixProduct = Cat(0.U(1.W), matrixScale) * Cat(0.U(1.W), activationScale)
    val matrixActivation = (matrixProduct >> 31).pad(66)
    val outputProduct = matrixActivation * Cat(0.U(1.W), outputScale)
    val composed = outputProduct >> 31
    Mux(composed > "hffffffff".U, "hffffffff".U(32.W), composed(31, 0))
  }

  /** Round a signed fixed-point value after a constant arithmetic right shift.
    * The discarded magnitude is compared with the half-way point and exact
    * ties increment only an odd retained result (nearest-even for either sign).
    */
  def roundShiftRightNearestEven(value: SInt, shift: Int): SInt = {
    require(shift > 0 && shift < value.getWidth,
      s"nearest-even shift must be in 1..${value.getWidth - 1}, got $shift")
    // Round the magnitude, then restore the sign. Rounding a negative value's
    // two's-complement low bits directly is incorrect at exact ties (for
    // example, -3 >> 1 must round to -2, not -1). Widen before negation so the
    // most-negative input is representable as a positive magnitude.
    val negative = value < 0.S
    val widened = value.pad(value.getWidth + 1)
    val magnitude = Mux(negative, (-widened).asUInt, widened.asUInt)
    val quotient = magnitude >> shift
    val remainder = magnitude(shift - 1, 0)
    val halfway = (BigInt(1) << (shift - 1)).U(shift.W)
    val roundUp = remainder > halfway || (remainder === halfway && quotient(0))
    val roundedMagnitude = quotient.pad(widened.getWidth) + roundUp.asUInt
    val roundedSigned = Mux(negative, -roundedMagnitude.asSInt, roundedMagnitude.asSInt)
    resizeSigned(roundedSigned, value.getWidth)
  }

  /** Apply an unsigned Q31 scale to a signed accumulator, round to nearest-even,
    * then saturate to a signed output element. The multiplier is widened before
    * multiplication so 0x80000000 represents exact unity rather than -1.0.
    */
  def requantizeQ31(value: SInt, multiplier: UInt, outputBits: Int): UInt = {
    require(outputBits > 0 && outputBits <= 32, "Q31 requantization output width must be in 1..32")
    require(multiplier.getWidth == 32, "Q31 requantization multiplier must be 32 bits")
    val positiveMultiplier = Cat(0.U(1.W), multiplier).asSInt
    val product = value * positiveMultiplier
    val quotient = (product >> 31).asSInt
    val remainder = product.asUInt(30, 0)
    val halfway = (BigInt(1) << 30).U(31.W)
    val roundUp = remainder > halfway || (remainder === halfway && quotient.asUInt(0))
    val rounded = quotient + roundUp.asUInt.zext
    val maximum = (BigInt(1) << (outputBits - 1)) - 1
    val minimum = -(BigInt(1) << (outputBits - 1))
    val saturated = Mux(
      rounded > maximum.S(rounded.getWidth.W),
      maximum.S(rounded.getWidth.W),
      Mux(rounded < minimum.S(rounded.getWidth.W), minimum.S(rounded.getWidth.W), rounded)
    )
    resizeSignedToUInt(saturated, outputBits)
  }

  /** Apply the Q31 multiplier and its independent signed binary exponent.
    * Checkpoint quantization scales are represented as an unsigned Q31
    * mantissa times 2^binaryShift. Keep the full signed accumulator product
    * until both the exponent and nearest-even rounding have been applied.
    */
  def requantizeQ31WithShift(value: SInt, multiplier: UInt, binaryShift: SInt, outputBits: Int): UInt = {
    require(outputBits > 0 && outputBits <= 32, "Q31 requantization output width must be in 1..32")
    require(multiplier.getWidth == 32, "Q31 requantization multiplier must be 32 bits")
    // Linear composes independent signed 8-bit matrix, activation, and output
    // exponents before requantization. The resulting signed sum is 10 bits;
    // accepting that explicit width preserves the independent scale contract.
    require(binaryShift.getWidth <= 10, "Q31 binary exponent input must be at most 10 bits")
    val positiveMultiplier = Cat(0.U(1.W), multiplier).asSInt
    val product = value * positiveMultiplier
    val negative = product < 0.S
    val magnitude = Mux(negative, (-product).asUInt, product.asUInt)
    val effectiveShift = 31.S(10.W) - binaryShift.pad(10)
    val tooFarRight = effectiveShift > 63.S
    val rightShift = Mux(
      effectiveShift <= 0.S,
      0.U(6.W),
      Mux(effectiveShift > 63.S, 63.U(6.W), effectiveShift.asUInt(5, 0))
    )
    val leftMagnitude = Mux(effectiveShift < 0.S, -effectiveShift, 0.S(10.W))
    val leftShift = Mux(leftMagnitude > 63.S, 63.U(6.W), leftMagnitude.asUInt(5, 0))
    val quotient = magnitude >> rightShift
    val restored = (quotient << rightShift)(64, 0)
    val remainder = magnitude - restored
    val halfway = (1.U(65.W) << Mux(rightShift === 0.U, 0.U, rightShift - 1.U))(64, 0)
    val roundUp = rightShift =/= 0.U &&
      (remainder > halfway || (remainder === halfway && quotient(0)))
    val roundedRight = quotient + roundUp.asUInt
    val scaledMagnitude = Mux(
      tooFarRight,
      0.U(128.W),
      Mux(
        effectiveShift < 0.S,
        magnitude.pad(128) << leftShift,
        roundedRight.pad(128)
      )
    )
    if (value.getWidth <= 32) {
      // For a signed <=32-bit input and unsigned Q31 mantissa, the product
      // magnitude is strictly below 2^63. The bounded left shift is <=63,
      // so the scaled magnitude is below 2^126 and cannot set the sign bit
      // of the original wide signedResult. Saturation can therefore compare
      // magnitudes first, then restore the sign at the output width. This
      // removes the wide negate/compare carry chain inside the requantizer;
      // multiplication, exponent handling and nearest-even rounding above
      // retain their original widths and truncation behavior.
      val positiveLimit = ((BigInt(1) << (outputBits - 1)) - 1).U(outputBits.W)
      val negativeLimit = (BigInt(1) << (outputBits - 1)).U(outputBits.W)
      val limit = Mux(negative, negativeLimit, positiveLimit)
      // Split saturation into an upper-bit overflow test and a narrow
      // low-part comparison. The result is identical to comparing the full
      // 128-bit magnitude against the output-width limit, but avoids a wide
      // magnitude comparator in the requantization cone.
      val upperOverflow = scaledMagnitude(127, outputBits).orR
      val lowMagnitude = scaledMagnitude(outputBits - 1, 0)
      val clipped = Mux(upperOverflow || lowMagnitude > limit, limit, lowMagnitude)
      val code = clipped(outputBits - 1, 0)
      Mux(negative, 0.U(outputBits.W) - code, code)
    } else {
      // Retain the original semantics for wider callers, for which the
      // <=32-bit magnitude bound used by the optimized path does not apply.
      val signedResult = Mux(negative, -scaledMagnitude.asSInt, scaledMagnitude.asSInt)
      val maximum = ((BigInt(1) << (outputBits - 1)) - 1).S(128.W)
      val minimum = (-(BigInt(1) << (outputBits - 1))).S(128.W)
      val saturated = Mux(signedResult > maximum, maximum, Mux(signedResult < minimum, minimum, signedResult))
      resizeSignedToUInt(saturated, outputBits)
    }
  }

  /** Bounded restoring square root. The implementation uses one fixed
    * compare/subtract stage per input bit-pair and no variable divider.
    * The result is floor(sqrt(value)); the caller owns the Q-format contract.
    */
  def integerSqrt(value: UInt, width: Int): UInt = {
    require(width >= 2, "integer square-root width must be at least two bits")
    val n = value.pad(width)(width - 1, 0)
    val pairCount = (width + 1) / 2
    val padded = n.pad(pairCount * 2)
    val remWidth = 2 * pairCount + 2
    var remainder: UInt = 0.U(remWidth.W)
    var root: UInt = 0.U((pairCount + 1).W)
    for (pair <- (0 until pairCount).reverse) {
      val shiftedRemainder = Cat(remainder(2 * pairCount - 1, 0), padded(2 * pair + 1, 2 * pair))
      val trialNarrow = Cat(root(pairCount - 1, 0), 0.U(2.W)) | 1.U((pairCount + 2).W)
      val trial = trialNarrow.pad(remWidth)
      val takeRootBit = shiftedRemainder >= trial
      val nextRemainder = Wire(UInt(remWidth.W))
      nextRemainder := Mux(takeRootBit, shiftedRemainder - trial, shiftedRemainder)
      remainder = nextRemainder
      root = Cat(root(pairCount - 1, 0), takeRootBit)
    }
    root(pairCount - 1, 0)
  }

  /** Unsigned restoring division with statically bounded numerator work.
    * This elaborates as a fixed chain of compare/subtract stages, not a
    * variable-width `/` operator. The quotient is saturated to all ones for
    * a zero denominator; callers normally guard that case explicitly.
    */
  def unsignedDivideFixed(
    numerator: UInt,
    denominator: UInt,
    numeratorBits: Int,
    denominatorBits: Int
  ): UInt = {
    require(numeratorBits > 0 && denominatorBits > 0, "fixed divider widths must be positive")
    val n = numerator.pad(numeratorBits)(numeratorBits - 1, 0)
    val d = denominator.pad(denominatorBits)(denominatorBits - 1, 0)
    val quotientBits = Wire(Vec(numeratorBits, Bool()))
    val remWidth = denominatorBits + 1
    val denominatorWide = Cat(0.U(1.W), d)
    var remainder: UInt = 0.U(remWidth.W)
    for (bit <- (0 until numeratorBits).reverse) {
      val shiftedRemainder = Cat(remainder(denominatorBits - 1, 0), n(bit))
      val takeQuotientBit = shiftedRemainder >= denominatorWide
      val nextRemainder = Wire(UInt(remWidth.W))
      nextRemainder := Mux(takeQuotientBit, shiftedRemainder - denominatorWide, shiftedRemainder)
      remainder = nextRemainder
      quotientBits(bit) := takeQuotientBit
    }
    Mux(d === 0.U, Fill(numeratorBits, 1.B), quotientBits.asUInt)
  }
}

/** A bounded, sequential restoring square root for fixed-point operators.
  * One input is accepted at a time; the radicand and output remain stable
  * across backpressure. The implementation performs one bit-pair iteration
  * per cycle instead of elaborating a long combinational compare/subtract chain.
  */
class PhysicalIntegerSqrt(width: Int) extends Module {
  require(width >= 2, "integer square-root input width must be at least two bits")

  private val pairCount = (width + 1) / 2
  private val paddedWidth = pairCount * 2
  private val rootBits = pairCount
  private val remainderBits = pairCount + 2
  private val iterationBits = log2Ceil(pairCount max 2)

  val io = IO(new Bundle {
    val in = Flipped(Decoupled(UInt(width.W)))
    val out = Decoupled(UInt(rootBits.W))
  })

  private val busy = RegInit(false.B)
  private val outValid = RegInit(false.B)
  private val radicand = Reg(UInt(paddedWidth.W))
  private val iteration = Reg(UInt(iterationBits.W))
  private val root = Reg(UInt(rootBits.W))
  private val remainder = Reg(UInt(remainderBits.W))
  private val result = Reg(UInt(rootBits.W))

  io.in.ready := !busy && !outValid
  io.out.valid := outValid
  io.out.bits := result

  private val pairShift = ((pairCount - 1).U(iterationBits.W) - iteration) << 1
  private val nextPair = (radicand >> pairShift)(1, 0)
  private val shiftedRemainder = Cat(remainder(remainderBits - 3, 0), nextPair)
  private val trial = Cat(root, 0.U(2.W)) | 1.U(remainderBits.W)
  private val takeRootBit = shiftedRemainder >= trial
  private val nextRemainder = Mux(
    takeRootBit,
    shiftedRemainder - trial,
    shiftedRemainder
  )
  private val nextRoot = ((root << 1) | takeRootBit.asUInt)(rootBits - 1, 0)

  when(io.in.fire) {
    radicand := io.in.bits.pad(paddedWidth)
    iteration := 0.U
    root := 0.U
    remainder := 0.U
    busy := true.B
  }

  when(busy) {
    remainder := nextRemainder
    root := nextRoot
    when(iteration === (pairCount - 1).U) {
      result := nextRoot
      busy := false.B
      outValid := true.B
    }.otherwise {
      iteration := iteration + 1.U
    }
  }

  when(io.out.fire) {
    outValid := false.B
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

class LinearScaleMetadata(channelCount: Int) extends Bundle {
  require(channelCount > 0, "scale metadata requires at least one output channel")
  val channelScale = Vec(channelCount, UInt(32.W))
  val channelShift = Vec(channelCount, SInt(8.W))
  val activationScale = UInt(32.W)
  val activationShift = SInt(8.W)
  val outputScale = UInt(32.W)
  val outputShift = SInt(8.W)
}

class LinearScalePorts(channelCount: Int) extends Bundle {
  require(channelCount > 0, "linear scale ports require at least one output channel")
  // outScale/biasScale remain part of the historical ABI. In integer mode
  // outScale is the output-domain Q31 multiplier and biasScale is the bias
  // requantizer; channelScale and activationScale are the new checkpoint /
  // calibration-bound operands.
  val outScale = Input(UInt(32.W))
  val biasScale = Input(UInt(32.W))
  val channelScale = Input(Vec(channelCount, UInt(32.W)))
  val channelShift = Input(Vec(channelCount, SInt(8.W)))
  val activationScale = Input(UInt(32.W))
  val activationShift = Input(SInt(8.W))
  val outputShift = Input(SInt(8.W))
  val biasShift = Input(SInt(8.W))
}
