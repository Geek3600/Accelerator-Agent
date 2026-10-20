package spatialaccagent.templates

import chisel3._
import chisel3.util._

final case class ActivationParams(
  hiddenSize: Int,
  lanes: Int = 12,
  elemBits: Int = 8,
  batchSize: Int = 16,
  maxSeqLen: Int = 16,
  kind: String = "relu",
  outputBits: Int = 16,
  integerMode: Boolean = false
) {
  require(hiddenSize % lanes == 0, "hiddenSize must be divisible by lanes")
  if (integerMode) {
    require(elemBits == 8, "integer activations require signed INT8 inputs")
    require(outputBits == 8, "integer activation output must be signed INT8")
    require(
      Set("relu", "silu", "swish", "gelu", "gelu_new", "gelu_pytorch_tanh", "gelu_tanh").contains(kind),
      s"unsupported integer activation kind: $kind"
    )
  } else {
    require(elemBits == 16 || elemBits == 32, "floating-point activations require IEEE FP16 or FP32")
    require(outputBits == 16 || outputBits == 32, "floating-point activation output requires IEEE FP16 or FP32")
  }
  val beats: Int = hiddenSize / lanes
  val beatBits: Int = lanes * elemBits
  val outputBeatBits: Int = lanes * outputBits
  val addrBits: Int = log2Ceil(batchSize * beats max 2)
}

class Activation(p: ActivationParams) extends Module {
  val io = IO(new Bundle {
    val cfg = Input(new StageConfig(log2Ceil(p.maxSeqLen + 1 max 2)))
    val in = Flipped(Decoupled(new StreamBeat(StreamSpec(p.beatBits, p.addrBits))))
    val out = Decoupled(new StreamBeat(StreamSpec(p.outputBeatBits, p.addrBits)))
  })

  if (p.integerMode) {
    // Integer GELU/SiLU approximation: a bounded linear sigmoid in Q7 followed
    // by a signed INT8 multiply and real Q31 nearest-even requantization.
    // GELU uses a steeper slope for the tanh-based approximation; SiLU uses
    // the unit sigmoid slope. The path contains no floating-point IP.
    io.in.ready := io.out.ready
    io.out.valid := io.in.valid
    io.out.bits.st := io.in.bits.st
    io.out.bits.addr := io.in.bits.addr
    io.out.bits.last := io.in.bits.last
    val input = io.in.bits.data.asTypeOf(Vec(p.lanes, SInt(8.W)))
    val result = Wire(Vec(p.lanes, UInt(8.W)))
    for (lane <- 0 until p.lanes) {
      val x = input(lane)
      val y = if (p.kind == "relu") {
        Mux(x < 0.S, 0.S(8.W), x)
      } else if (p.kind == "silu" || p.kind == "swish" || p.kind == "gelu" || p.kind == "gelu_new" || p.kind == "gelu_pytorch_tanh" || p.kind == "gelu_tanh") {
        // Explicit code-domain PWL approximation to sigmoid(x): unsigned
        // Q7 coefficient, centered at 0.5, clamped to [0, 1]. The Q31
        // multiplier below divides x*coefficient by 128. Zero-extend before
        // signed multiplication so the valid coefficient 128 is never
        // reinterpreted as -128.
        val slope = if (p.kind == "silu" || p.kind == "swish") 8 else 14
        val linear = 64.S(16.W) + (x * slope.S(5.W)).pad(16)
        val sigmoid = Mux(linear < 0.S, 0.U(8.W), Mux(linear > 128.S, 128.U(8.W), linear.asUInt(7, 0)))
        val coefficient = Cat(0.U(1.W), sigmoid).asSInt
        val product = x * coefficient
        AccMath.requantizeQ31(product, (BigInt(1) << 24).U(32.W), 8).asSInt
      } else {
        x
      }
      result(lane) := AccMath.resizeSignedToUInt(y, 8)
    }
    io.out.bits.data := result.asUInt
  } else {
  val sigmoidTablePath = "src/main/resources/spatialaccagent/numeric/sigmoid_pwl_q18.mem"
  val q11Width = 16
  val sigmoidFractionBits = 18

  if (p.kind == "silu" || p.kind == "swish") {
    require(p.elemBits == 16 || p.elemBits == 32, "target-model SiLU requires IEEE fp16 or fp32 stream elements")

    val streamSpec = StreamSpec(p.beatBits, p.addrBits)
    val inputBeat = Reg(new StreamBeat(streamSpec))
    val resultData = Reg(Vec(p.lanes, UInt(p.outputBits.W)))
    val laneIndex = RegInit(0.U(log2Ceil(p.lanes max 2).W))
    val inputFpReg = Reg(UInt(32.W))
    val scaledInputReg = Reg(UInt(32.W))
    val inputQ11Reg = Reg(SInt(q11Width.W))
    val belowMinusEightReg = RegInit(false.B)
    val abovePlusEightReg = RegInit(false.B)
    val productQ29Reg = Reg(SInt(36.W))
    val productFpReg = Reg(UInt(32.W))

    val states = Enum(12)
    val sAccept = states(0)
    val sClassifyIssue = states(1)
    val sClassifyWait = states(2)
    val sConvertIssue = states(3)
    val sConvertWait = states(4)
    val sTableIssue = states(5)
    val sTableCapture = states(6)
    val sProductConvertIssue = states(7)
    val sProductConvertWait = states(8)
    val sScaleProductIssue = states(9)
    val sScaleProductWait = states(10)
    val sEmit = states(11)
    val state = RegInit(sAccept)

    io.in.ready := state === sAccept
    when(io.in.fire) {
      inputBeat := io.in.bits
      laneIndex := 0.U
      state := sClassifyIssue
    }

    val inputValues = inputBeat.data.asTypeOf(Vec(p.lanes, UInt(p.elemBits.W)))
    val selectedInput = inputValues(AccMath.boundedIndex(laneIndex, p.lanes))
    val selectedFp32 = PhysicalMath.toFp32(selectedInput, p.elemBits)
    val inputScale = Module(new PhysicalFp32Mul)
    val belowCompare = Module(new PhysicalFp32CompareLt)
    val aboveCompare = Module(new PhysicalFp32CompareLt)
    inputScale.io.a := selectedFp32
    inputScale.io.b := PhysicalMath.fp32Constant(2048.0)
    belowCompare.io.a := PhysicalMath.fp32Constant(-8.0)
    belowCompare.io.b := selectedFp32
    aboveCompare.io.a := selectedFp32
    aboveCompare.io.b := PhysicalMath.fp32Constant(8.0)
    val classifyReady = inputScale.io.inReady && belowCompare.io.inReady && aboveCompare.io.inReady
    val classifyIssue = state === sClassifyIssue && classifyReady
    inputScale.io.inValid := classifyIssue
    belowCompare.io.inValid := classifyIssue
    aboveCompare.io.inValid := classifyIssue
    when(classifyIssue) {
      inputFpReg := selectedFp32
      state := sClassifyWait
    }
    when(state === sClassifyWait && inputScale.io.outValid && belowCompare.io.outValid && aboveCompare.io.outValid) {
      scaledInputReg := inputScale.io.out
      belowMinusEightReg := !belowCompare.io.out(0)
      abovePlusEightReg := !aboveCompare.io.out(0)
      state := sConvertIssue
    }

    val q11Convert = Module(new PhysicalFp32ToSigned(q11Width))
    q11Convert.io.in := scaledInputReg
    q11Convert.io.inValid := state === sConvertIssue && q11Convert.io.inReady
    when(state === sConvertIssue && q11Convert.io.inReady) {
      state := sConvertWait
    }
    when(state === sConvertWait && q11Convert.io.outValid) {
      inputQ11Reg := q11Convert.io.out
      state := sTableIssue
    }

    val boundedQ11 = Wire(SInt(q11Width.W))
    boundedQ11 := Mux(
      belowMinusEightReg,
      (-16384).S(q11Width.W),
      Mux(abovePlusEightReg, 16383.S(q11Width.W), inputQ11Reg)
    )
    val biasedQ11 = (boundedQ11.pad(18) + 16384.S(18.W)).asUInt
    val segment = biasedQ11(14, 8)
    val remainder = biasedQ11(7, 0)
    val baseRom = Module(new PhysicalRom(129, 19, sigmoidTablePath))
    val nextRom = Module(new PhysicalRom(129, 19, sigmoidTablePath))
    baseRom.io.readEn := state === sTableIssue
    baseRom.io.readAddr := segment
    nextRom.io.readEn := state === sTableIssue
    nextRom.io.readAddr := segment +& 1.U
    when(state === sTableIssue) {
      state := sTableCapture
    }

    val tableDelta = nextRom.io.readData.zext - baseRom.io.readData.zext
    val interpolationProduct = tableDelta * Cat(0.U(1.W), remainder).asSInt
    val roundedDelta = (interpolationProduct + 128.S(interpolationProduct.getWidth.W)) >> 8
    val interpolatedQ18 = (baseRom.io.readData.zext + roundedDelta).asUInt(18, 0)
    val q18One = (BigInt(1) << sigmoidFractionBits).U(19.W)
    val sigmoidQ18 = Mux(
      belowMinusEightReg,
      0.U(19.W),
      Mux(abovePlusEightReg, q18One, interpolatedQ18)
    )
    val rawProductQ29 = inputQ11Reg * sigmoidQ18.zext.asSInt
    when(state === sTableCapture) {
      productQ29Reg := rawProductQ29
      state := sProductConvertIssue
    }

    val productConvert = Module(new PhysicalSignedToFp32(36))
    productConvert.io.in := productQ29Reg
    productConvert.io.inValid := state === sProductConvertIssue && productConvert.io.inReady
    when(state === sProductConvertIssue && productConvert.io.inReady) {
      state := sProductConvertWait
    }
    when(state === sProductConvertWait && productConvert.io.outValid) {
      productFpReg := productConvert.io.out
      state := sScaleProductIssue
    }

    val productScale = Module(new PhysicalFp32Mul)
    productScale.io.a := productFpReg
    productScale.io.b := PhysicalMath.fp32Constant(math.pow(2.0, -29.0))
    productScale.io.inValid := state === sScaleProductIssue && productScale.io.inReady
    when(state === sScaleProductIssue && productScale.io.inReady) {
      state := sScaleProductWait
    }
    when(state === sScaleProductWait && productScale.io.outValid) {
      val selectedResult = Mux(
        belowMinusEightReg,
        PhysicalMath.fp32Zero,
        Mux(abovePlusEightReg, inputFpReg, productScale.io.out)
      )
      resultData(AccMath.boundedIndex(laneIndex, p.lanes)) := PhysicalMath.fromFp32(selectedResult, p.outputBits)
      when(laneIndex === (p.lanes - 1).U) {
        laneIndex := 0.U
        state := sEmit
      }.otherwise {
        laneIndex := laneIndex + 1.U
        state := sClassifyIssue
      }
    }

    io.out.valid := state === sEmit
    io.out.bits.data := resultData.asUInt
    io.out.bits.st := inputBeat.st
    io.out.bits.addr := inputBeat.addr
    io.out.bits.last := inputBeat.last
    when(io.out.fire) {
      state := sAccept
    }
  } else {
    io.in.ready := io.out.ready
    io.out.valid := io.in.valid
    io.out.bits.st := io.in.bits.st
    io.out.bits.addr := io.in.bits.addr
    io.out.bits.last := io.in.bits.last
    val inVec = io.in.bits.data.asTypeOf(Vec(p.lanes, SInt(p.elemBits.W)))
    val outVec = Wire(Vec(p.lanes, UInt(p.outputBits.W)))
    for (lane <- 0 until p.lanes) {
      val x = inVec(lane)
      val y = if (p.kind == "relu") {
        Mux(x < 0.S, 0.S(p.elemBits.W), x)
      } else if (p.kind == "gelu" || p.kind == "gelu_new" || p.kind == "gelu_pytorch_tanh") {
        Mux(x < 0.S, (x >> 1).asSInt, x)
      } else {
        x
      }
      outVec(lane) := AccMath.resizeSignedToUInt(y, p.outputBits)
    }
    io.out.bits.data := outVec.asUInt
  }

  dontTouch(io.cfg)
  }
}

class ActivationReLU(p: ActivationParams) extends Activation(p.copy(kind = "relu"))
class ActivationGELUNew(p: ActivationParams) extends Activation(p.copy(kind = "gelu_new"))
class ActivationSiLU(p: ActivationParams) extends Activation(p.copy(kind = "silu"))
class ActivationGELUTanh(p: ActivationParams) extends Activation(p.copy(kind = "gelu_pytorch_tanh"))
