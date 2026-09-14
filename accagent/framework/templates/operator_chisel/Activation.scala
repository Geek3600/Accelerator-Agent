package spatialaccagent.templates

import chisel3._
import chisel3.util._
import chisel3.util.experimental.loadMemoryFromFileInline
import hardfloat._
import hardfloat.consts

final case class ActivationParams(
  hiddenSize: Int,
  lanes: Int = 12,
  elemBits: Int = 8,
  batchSize: Int = 16,
  maxSeqLen: Int = 16,
  kind: String = "relu"
) {
  require(hiddenSize % lanes == 0, "hiddenSize must be divisible by lanes")
  val beats: Int = hiddenSize / lanes
  val beatBits: Int = lanes * elemBits
  val addrBits: Int = log2Ceil(batchSize * beats max 2)
}

class Activation(p: ActivationParams) extends Module {
  val io = IO(new Bundle {
    val cfg = Input(new StageConfig(log2Ceil(p.maxSeqLen + 1 max 2)))
    val in = Flipped(Decoupled(new StreamBeat(StreamSpec(p.beatBits, p.addrBits))))
    val out = Decoupled(new StreamBeat(StreamSpec(p.beatBits, p.addrBits)))
  })

  private val SigmoidTablePath =
    "src/main/resources/spatialaccagent/numeric/sigmoid_pwl_q18.memh"
  private val Fp32ExpWidth = 8
  private val Fp32SigWidth = 24
  private val Q11Width = 16
  private val SigmoidFractionBits = 18

  private def fp32ToSignedQ11(value: UInt): SInt = {
    val scaled = IeeeMath.mulFp32(value, IeeeMath.fp32Constant(2048.0))
    val convert = Module(new RecFNToIN(Fp32ExpWidth, Fp32SigWidth, Q11Width))
    convert.io.in := recFNFromFN(Fp32ExpWidth, Fp32SigWidth, scaled)
    convert.io.roundingMode := consts.round_near_even
    convert.io.signedOut := true.B
    convert.io.out.asSInt
  }

  private def signedIntegerToFp32(value: SInt): UInt = {
    val convert = Module(new INToRecFN(value.getWidth, Fp32ExpWidth, Fp32SigWidth))
    convert.io.signedIn := true.B
    convert.io.in := value.asUInt
    convert.io.roundingMode := consts.round_near_even
    convert.io.detectTininess := consts.tininess_afterRounding
    fNFromRecFN(Fp32ExpWidth, Fp32SigWidth, convert.io.out)
  }

  io.in.ready := io.out.ready
  io.out.valid := io.in.valid
  io.out.bits.st := io.in.bits.st
  io.out.bits.addr := io.in.bits.addr
  io.out.bits.last := io.in.bits.last

  val inVec = io.in.bits.data.asTypeOf(Vec(p.lanes, SInt(p.elemBits.W)))
  val outVec = Wire(Vec(p.lanes, UInt(p.elemBits.W)))

  if (p.kind == "silu" || p.kind == "swish") {
    require(
      p.elemBits == 16 || p.elemBits == 32,
      "target-model SiLU requires IEEE fp16 or fp32 stream elements"
    )

    val sigmoidTable = Mem(129, UInt(19.W))
    loadMemoryFromFileInline(sigmoidTable, SigmoidTablePath)

    val minusEight = IeeeMath.fp32Constant(-8.0)
    val plusEight = IeeeMath.fp32Constant(8.0)
    val q18One = (BigInt(1) << SigmoidFractionBits).U(19.W)
    val productScale = IeeeMath.fp32Constant(math.pow(2.0, -29.0))

    for (i <- 0 until p.lanes) {
      val inputBits = inVec(i).asUInt
      val inputFp32 = IeeeMath.toFp32(inputBits, p.elemBits)
      val atOrBelowMinusEight = !IeeeMath.lessThanFp32(minusEight, inputFp32)
      val atOrAbovePlusEight = !IeeeMath.lessThanFp32(inputFp32, plusEight)
      val inputQ11 = fp32ToSignedQ11(inputFp32)

      val tableInputQ11 = Wire(SInt(Q11Width.W))
      tableInputQ11 := Mux(
        atOrBelowMinusEight,
        (-16384).S(Q11Width.W),
        Mux(atOrAbovePlusEight, 16383.S(Q11Width.W), inputQ11)
      )

      val biasedQ11 = (tableInputQ11.pad(18) + 16384.S(18.W)).asUInt
      val segment = biasedQ11(14, 8)
      val remainder = biasedQ11(7, 0)
      val nextSegment = segment +& 1.U
      val tableBase = sigmoidTable.read(segment)
      val tableNext = sigmoidTable.read(nextSegment)
      val tableDelta = tableNext.zext - tableBase.zext
      val remainderSigned = Cat(0.U(1.W), remainder).asSInt
      val interpolationProduct = tableDelta * remainderSigned
      val roundedDelta =
        (interpolationProduct + 128.S(interpolationProduct.getWidth.W)) >> 8
      val interpolatedWide = tableBase.zext + roundedDelta
      val interpolatedBits = interpolatedWide.asUInt
      val interpolatedQ18 = interpolatedBits(18, 0)

      val sigmoidQ18 = Wire(UInt(19.W))
      sigmoidQ18 := Mux(
        atOrBelowMinusEight,
        0.U,
        Mux(atOrAbovePlusEight, q18One, interpolatedQ18)
      )

      val siluProductQ29 = inputQ11 * sigmoidQ18.zext
      val productFp32 = signedIntegerToFp32(siluProductQ29)
      val siluFp32 = IeeeMath.mulFp32(productFp32, productScale)
      val boundedSilu = Mux(
        atOrBelowMinusEight,
        IeeeMath.fp32Zero,
        Mux(atOrAbovePlusEight, inputFp32, siluFp32)
      )
      outVec(i) := IeeeMath.fromFp32(boundedSilu, p.elemBits)
    }
  } else {
    for (i <- 0 until p.lanes) {
      val x = inVec(i)
      val y =
        if (p.kind == "relu") {
          Mux(x < 0.S, 0.S(p.elemBits.W), x)
        } else if (
          p.kind == "gelu" ||
          p.kind == "gelu_new" ||
          p.kind == "gelu_pytorch_tanh"
        ) {
          Mux(x < 0.S, (x >> 1).asSInt, x)
        } else {
          x
        }
      outVec(i) := AccMath.resizeSignedToUInt(y, p.elemBits)
    }
  }

  io.out.bits.data := outVec.asUInt
}

class ActivationReLU(p: ActivationParams) extends Activation(p.copy(kind = "relu"))
class ActivationGELUNew(p: ActivationParams) extends Activation(p.copy(kind = "gelu_new"))
class ActivationSiLU(p: ActivationParams) extends Activation(p.copy(kind = "silu"))
class ActivationGELUTanh(p: ActivationParams) extends Activation(p.copy(kind = "gelu_pytorch_tanh"))
