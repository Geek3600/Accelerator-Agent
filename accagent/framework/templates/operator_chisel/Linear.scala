package spatialaccagent.templates

import chisel3._
import chisel3.util._

final case class LinearParams(
  inDim: Int,
  outDim: Int,
  inLanes: Int = 8,
  outLanes: Int = 8,
  elemBits: Int = 16,
  accBits: Int = 32,
  outputBits: Int = 16,
  batchSize: Int = 16,
  maxSeqLen: Int = 16,
  hasBias: Boolean = true,
  fusedActivation: String = "none"
) {
  require(inDim > 0 && outDim > 0, "linear dimensions must be positive")
  require(inDim % inLanes == 0, "inDim must be divisible by inLanes")
  require(outDim % outLanes == 0, "outDim must be divisible by outLanes")
  require(elemBits == 16 || elemBits == 32, "Linear inputs and weights must be IEEE FP16 or FP32")
  require(accBits == 32, "Linear accumulation must use FP32")
  require(outputBits == 16 || outputBits == 32, "Linear output must be IEEE FP16 or FP32")
  require(fusedActivation == "none" || fusedActivation == "relu", "unsupported fused activation")
  val inBeats: Int = inDim / inLanes
  val outBeats: Int = outDim / outLanes
  val inputBeatBits: Int = inLanes * elemBits
  val outputBeatBits: Int = outLanes * outputBits
  val weightTileBits: Int = inLanes * outLanes * elemBits
  val weightDepth: Int = inBeats * outBeats
  val inputAddrBits: Int = log2Ceil(batchSize * inBeats max 2)
  val outputAddrBits: Int = log2Ceil(batchSize * outBeats max 2)
  val weightAddrBits: Int = log2Ceil(weightDepth max 2)
  val biasBeatBits: Int = outLanes * accBits
}

class Linear(p: LinearParams) extends Module {
  val io = IO(new Bundle {
    val start = Input(Bool())
    val cfg = Input(new StageConfig(log2Ceil(p.maxSeqLen + 1 max 2)))
    val cfgValid = Input(Bool())
    val weight = Flipped(Decoupled(new WeightWrite(p.weightTileBits, p.weightAddrBits)))
    val bias = Flipped(Decoupled(new WeightWrite(p.biasBeatBits, log2Ceil(p.outBeats max 2))))
    val scale = new LinearScalePorts
    val in = Flipped(Decoupled(new StreamBeat(StreamSpec(p.inputBeatBits, p.inputAddrBits))))
    val out = Decoupled(new StreamBeat(StreamSpec(p.outputBeatBits, p.outputAddrBits)))
  })

  val inputMem = Reg(Vec(p.inBeats, UInt(p.inputBeatBits.W)))
  val weightMem = Reg(Vec(p.weightDepth, UInt(p.weightTileBits.W)))
  val biasMem = Reg(Vec(p.outBeats, UInt(p.biasBeatBits.W)))

  val weightLoadCnt = RegInit(0.U(p.weightAddrBits.W))
  val weightLoaded = RegInit(false.B)
  io.weight.ready := !weightLoaded && io.weight.bits.addr === weightLoadCnt
  when(io.weight.fire) {
    weightMem(weightLoadCnt) := io.weight.bits.data
    when(weightLoadCnt === (p.weightDepth - 1).U) {
      weightLoaded := true.B
      weightLoadCnt := 0.U
    }.otherwise {
      weightLoadCnt := weightLoadCnt + 1.U
    }
  }

  private val biasAddrBits = log2Ceil(p.outBeats max 2)
  val biasLoadCnt = RegInit(0.U(biasAddrBits.W))
  val biasLoaded = RegInit((!p.hasBias).B)
  if (p.hasBias) {
    io.bias.ready := !biasLoaded && io.bias.bits.addr === biasLoadCnt
    when(io.bias.fire) {
      biasMem(biasLoadCnt) := io.bias.bits.data
      when(biasLoadCnt === (p.outBeats - 1).U) {
        biasLoaded := true.B
        biasLoadCnt := 0.U
      }.otherwise {
        biasLoadCnt := biasLoadCnt + 1.U
      }
    }
  } else {
    io.bias.ready := false.B
  }

  val parametersLoaded = weightLoaded && biasLoaded
  val sLoad :: sPrep :: sCompute :: sEmit :: Nil = Enum(4)
  val state = RegInit(sLoad)
  val inCnt = RegInit(0.U(log2Ceil(p.inBeats max 2).W))
  val rowCnt = RegInit(0.U(log2Ceil(p.inBeats max 2).W))
  val outCnt = RegInit(0.U(log2Ceil(p.outBeats max 2).W))
  val tokenCnt = RegInit(0.U(log2Ceil(p.batchSize max 2).W))
  val vectorStart = RegInit(false.B)
  val acc = Reg(Vec(p.outLanes, UInt(32.W)))

  when(io.start && parametersLoaded) {
    state := sLoad
    inCnt := 0.U
    rowCnt := 0.U
    outCnt := 0.U
    tokenCnt := 0.U
  }

  io.in.ready := state === sLoad && parametersLoaded
  when(io.in.fire) {
    inputMem(inCnt) := io.in.bits.data
    when(inCnt === 0.U) {
      vectorStart := io.in.bits.st
    }
    when(inCnt === (p.inBeats - 1).U) {
      inCnt := 0.U
      outCnt := 0.U
      state := sPrep
    }.otherwise {
      inCnt := inCnt + 1.U
    }
  }

  val biasVec = biasMem(outCnt).asTypeOf(Vec(p.outLanes, UInt(32.W)))
  when(state === sPrep) {
    for (o <- 0 until p.outLanes) {
      if (p.hasBias) {
        acc(o) := biasVec(o)
      } else {
        acc(o) := IeeeMath.fp32Zero
      }
    }
    rowCnt := 0.U
    state := sCompute
  }

  val inVec = inputMem(rowCnt).asTypeOf(Vec(p.inLanes, UInt(p.elemBits.W)))
  val weightAddr = (outCnt * p.inBeats.U + rowCnt)(p.weightAddrBits - 1, 0)
  val weightTile = weightMem(weightAddr).asTypeOf(Vec(p.outLanes, Vec(p.inLanes, UInt(p.elemBits.W))))
  val dotProducts = Wire(Vec(p.outLanes, UInt(32.W)))
  for (o <- 0 until p.outLanes) {
    val products = (0 until p.inLanes).map { i =>
      val inputFp32 = IeeeMath.toFp32(inVec(i), p.elemBits)
      val weightFp32 = IeeeMath.toFp32(weightTile(o)(i), p.elemBits)
      IeeeMath.mulFp32(inputFp32, weightFp32)
    }
    dotProducts(o) := IeeeMath.sumFp32(products)
  }

  when(state === sCompute) {
    for (o <- 0 until p.outLanes) {
      acc(o) := IeeeMath.addFp32(acc(o), dotProducts(o))
    }
    when(rowCnt === (p.inBeats - 1).U) {
      state := sEmit
    }.otherwise {
      rowCnt := rowCnt + 1.U
    }
  }

  val outVec = Wire(Vec(p.outLanes, UInt(p.outputBits.W)))
  for (o <- 0 until p.outLanes) {
    val activated = if (p.fusedActivation == "relu") {
      Mux(IeeeMath.lessThanFp32(acc(o), IeeeMath.fp32Zero), IeeeMath.fp32Zero, acc(o))
    } else {
      acc(o)
    }
    outVec(o) := IeeeMath.fromFp32(activated, p.outputBits)
  }

  io.out.valid := state === sEmit
  io.out.bits.data := outVec.asUInt
  io.out.bits.st := vectorStart && outCnt === 0.U
  io.out.bits.addr := tokenCnt * p.outBeats.U + outCnt
  io.out.bits.last := outCnt === (p.outBeats - 1).U

  when(io.out.fire) {
    when(outCnt === (p.outBeats - 1).U) {
      state := sLoad
      outCnt := 0.U
      tokenCnt := Mux(tokenCnt === (p.batchSize - 1).U, 0.U, tokenCnt + 1.U)
    }.otherwise {
      outCnt := outCnt + 1.U
      state := sPrep
    }
  }
}

class ParametricLinearInt8ToInt8(p: LinearParams) extends Linear(p)

class ParametricLinearInt8ToFP32(p: LinearParams)
    extends Linear(p.copy(outputBits = 32))
