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
  fusedActivation: String = "none",
  weightRole: String = "weight",
  biasRole: String = "weight_bias",
  computeArrayRows: Int = 0,
  computeArrayCols: Int = 0
) {
  require(inDim > 0 && outDim > 0, "linear dimensions must be positive")
  require(inDim % inLanes == 0, "inDim must be divisible by inLanes")
  require(outDim % outLanes == 0, "outDim must be divisible by outLanes")
  require(elemBits == 16 || elemBits == 32, "Linear inputs and weights must be IEEE FP16 or FP32")
  require(accBits == 32, "Linear accumulation must use FP32")
  require(outputBits == 16 || outputBits == 32, "Linear output must be IEEE FP16 or FP32")
  require(fusedActivation == "none" || fusedActivation == "relu", "unsupported fused activation")
  require(weightRole == "weight" || weightRole.startsWith("weight_"), s"invalid physical weight role: $weightRole")
  require(biasRole == "weight" || biasRole.startsWith("weight_"), s"invalid physical bias role: $biasRole")
  val macRows: Int = if (computeArrayRows == 0) outLanes else computeArrayRows
  val macCols: Int = if (computeArrayCols == 0) inLanes else computeArrayCols
  require(macRows > 0 && macRows <= outLanes && outLanes % macRows == 0, "compute array rows must tile output lanes")
  require(macCols > 0 && macCols <= inLanes && inLanes % macCols == 0, "compute array cols must tile input lanes")
  require(isPow2(macCols), "compute array cols must be a power of two for the reduction tree")
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

  require(isPow2(p.inLanes), "Linear inLanes must be a power of two for the pipelined reduction tree")

  val inputMem = Module(new PhysicalSimpleDualPortMemory(p.inBeats, p.inputBeatBits, "activation"))
  val weightMem = Module(new PhysicalSimpleDualPortMemory(p.weightDepth, p.weightTileBits, p.weightRole))
  val biasMem = if (p.hasBias) {
    Some(Module(new PhysicalSimpleDualPortMemory(p.outBeats, p.biasBeatBits, p.biasRole)))
  } else None

  val weightLoadCnt = RegInit(0.U(p.weightAddrBits.W))
  val weightLoaded = RegInit(false.B)
  io.weight.ready := !weightLoaded && io.weight.bits.addr === weightLoadCnt
  weightMem.io.writeEn := io.weight.fire
  weightMem.io.writeAddr := weightLoadCnt
  weightMem.io.writeData := io.weight.bits.data
  when(io.weight.fire) {
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
  biasMem.foreach { mem =>
    mem.io.writeEn := false.B
    mem.io.writeAddr := biasLoadCnt
    mem.io.writeData := io.bias.bits.data
  }
  if (p.hasBias) {
    io.bias.ready := !biasLoaded && io.bias.bits.addr === biasLoadCnt
    biasMem.get.io.writeEn := io.bias.fire
    when(io.bias.fire) {
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
  val sLoad :: sBiasRead :: sBiasCapture :: sRowRead :: sMulIssue :: sMulWait :: sAccIssue :: sAccWait :: sReluIssue :: sReluWait :: sEmit :: Nil = Enum(11)
  val state = RegInit(sLoad)
  val inCnt = RegInit(0.U(log2Ceil(p.inBeats max 2).W))
  val rowCnt = RegInit(0.U(log2Ceil(p.inBeats max 2).W))
  val outCnt = RegInit(0.U(log2Ceil(p.outBeats max 2).W))
  val tokenCnt = RegInit(0.U(log2Ceil(p.batchSize max 2).W))
  val vectorStart = RegInit(false.B)
  val acc = Reg(Vec(p.outLanes, UInt(32.W)))
  val dotReg = Reg(Vec(p.macRows, UInt(32.W)))
  val macInputGroup = RegInit(0.U(log2Ceil((p.inLanes / p.macCols) max 2).W))
  val macOutputGroup = RegInit(0.U(log2Ceil((p.outLanes / p.macRows) max 2).W))

  inputMem.io.writeEn := io.in.fire
  inputMem.io.writeAddr := inCnt
  inputMem.io.writeData := io.in.bits.data
  inputMem.io.readEn := state === sRowRead
  inputMem.io.readAddr := rowCnt

  val weightAddr = (outCnt * p.inBeats.U + rowCnt)(p.weightAddrBits - 1, 0)
  weightMem.io.readEn := state === sRowRead
  weightMem.io.readAddr := weightAddr

  biasMem.foreach { mem =>
    mem.io.readEn := state === sBiasRead
    mem.io.readAddr := outCnt
  }

  when(io.start && parametersLoaded) {
    state := sLoad
    inCnt := 0.U
    rowCnt := 0.U
    outCnt := 0.U
    tokenCnt := 0.U
    macInputGroup := 0.U
    macOutputGroup := 0.U
  }

  io.in.ready := state === sLoad && parametersLoaded
  when(io.in.fire) {
    when(inCnt === 0.U) {
      vectorStart := io.in.bits.st
    }
    when(inCnt === (p.inBeats - 1).U) {
      inCnt := 0.U
      outCnt := 0.U
      state := sBiasRead
    }.otherwise {
      inCnt := inCnt + 1.U
    }
  }

  when(state === sBiasRead) {
    rowCnt := 0.U
    if (p.hasBias) {
      state := sBiasCapture
    } else {
      for (o <- 0 until p.outLanes) {
        acc(o) := PhysicalMath.fp32Zero
      }
      state := sRowRead
    }
  }

  val biasVec = biasMem
    .map(_.io.readData.asTypeOf(Vec(p.outLanes, UInt(32.W))))
    .getOrElse(VecInit(Seq.fill(p.outLanes)(PhysicalMath.fp32Zero)))
  when(state === sBiasCapture) {
    for (o <- 0 until p.outLanes) {
      acc(o) := biasVec(o)
    }
    state := sRowRead
  }

  when(state === sRowRead) {
    state := sMulIssue
  }

  val inVec = inputMem.io.readData.asTypeOf(Vec(p.inLanes, UInt(p.elemBits.W)))
  val weightTile = weightMem.io.readData.asTypeOf(Vec(p.outLanes, Vec(p.inLanes, UInt(p.elemBits.W))))
  // One DSP-backed Vivado multiplier IP per MAC PE. The two group counters
  // time-multiplex this fixed PE array across the full logical vector tile.
  // The IP generator pins fp_mul_sp_* to C_Mult_Usage=Full_Usage; exact
  // DSP48 consumption is measured only from the target-board Vivado report.
  val multipliers = Seq.tabulate(p.macRows, p.macCols) { (o, i) =>
    val mul = Module(new PhysicalFp32Mul)
    val inputIndex = macInputGroup * p.macCols.U + i.U
    val outputIndex = macOutputGroup * p.macRows.U + o.U
    val selectedInput = inVec(AccMath.boundedIndex(inputIndex, p.inLanes))
    val selectedWeights = weightTile(AccMath.boundedIndex(outputIndex, p.outLanes))
    mul.io.a := PhysicalMath.toFp32(selectedInput, p.elemBits)
    mul.io.b := PhysicalMath.toFp32(selectedWeights(AccMath.boundedIndex(inputIndex, p.inLanes)), p.elemBits)
    mul
  }
  val allMulReady = multipliers.flatten.map(_.io.inReady).reduce(_ && _)
  val mulIssue = state === sMulIssue && allMulReady
  multipliers.flatten.foreach(_.io.inValid := mulIssue)

  def reduceFp32(values: Seq[(UInt, Bool)]): (UInt, Bool) = {
    var level = values
    while (level.size > 1) {
      level = level.grouped(2).map { pair =>
        val add = Module(new PhysicalFp32Add)
        add.io.a := pair(0)._1
        add.io.b := pair(1)._1
        add.io.inValid := pair(0)._2 && pair(1)._2
        (add.io.out, add.io.outValid)
      }.toSeq
    }
    level.head
  }

  val dotProducts = Wire(Vec(p.macRows, UInt(32.W)))
  val dotValids = Wire(Vec(p.macRows, Bool()))
  for (o <- 0 until p.macRows) {
    val reduced = reduceFp32(
      multipliers(o).map(mul => (mul.io.out, mul.io.outValid)).toSeq
    )
    dotProducts(o) := reduced._1
    dotValids(o) := reduced._2
  }
  val allDotsValid = dotValids.asUInt.andR

  when(state === sMulIssue && allMulReady) {
    state := sMulWait
  }

  when(state === sMulWait && allDotsValid) {
    for (o <- 0 until p.macRows) {
      dotReg(o) := dotProducts(o)
    }
    state := sAccIssue
  }

  val accumulatorAdds = Seq.tabulate(p.macRows) { o =>
    val add = Module(new PhysicalFp32Add)
    val outputIndex = macOutputGroup * p.macRows.U + o.U
    add.io.a := acc(AccMath.boundedIndex(outputIndex, p.outLanes))
    add.io.b := dotReg(o)
    add
  }
  val allAccReady = accumulatorAdds.map(_.io.inReady).reduce(_ && _)
  val accIssue = state === sAccIssue && allAccReady
  accumulatorAdds.foreach(_.io.inValid := accIssue)

  when(state === sAccIssue && allAccReady) {
    state := sAccWait
  }

  val allAccValid = VecInit(accumulatorAdds.map(_.io.outValid)).asUInt.andR
  when(state === sAccWait && allAccValid) {
    for (o <- 0 until p.macRows) {
      val outputIndex = macOutputGroup * p.macRows.U + o.U
      acc(AccMath.boundedIndex(outputIndex, p.outLanes)) := accumulatorAdds(o).io.out
    }
    when(rowCnt === (p.inBeats - 1).U) {
      when(macInputGroup === (p.inLanes / p.macCols - 1).U) {
        macInputGroup := 0.U
        when(macOutputGroup === (p.outLanes / p.macRows - 1).U) {
          macOutputGroup := 0.U
          state := (if (p.fusedActivation == "relu") sReluIssue else sEmit)
        }.otherwise {
          macOutputGroup := macOutputGroup + 1.U
          state := sRowRead
        }
      }.otherwise {
        macInputGroup := macInputGroup + 1.U
        state := sRowRead
      }
    }.otherwise {
      rowCnt := rowCnt + 1.U
      macInputGroup := 0.U
      macOutputGroup := 0.U
      state := sRowRead
    }
  }

  val reluComparators = if (p.fusedActivation == "relu") {
    Seq.tabulate(p.outLanes) { o =>
      val compare = Module(new PhysicalFp32CompareLt)
      compare.io.a := acc(o)
      compare.io.b := PhysicalMath.fp32Zero
      compare
    }
  } else Seq.empty
  val reluReady = if (p.fusedActivation == "relu") reluComparators.map(_.io.inReady).reduce(_ && _) else true.B
  val reluIssue = state === sReluIssue && reluReady
  reluComparators.foreach(_.io.inValid := reluIssue)
  when(reluIssue) {
    state := sReluWait
  }
  if (p.fusedActivation == "relu") {
    val reluValid = VecInit(reluComparators.map(_.io.outValid)).asUInt.andR
    when(state === sReluWait && reluValid) {
      for (o <- 0 until p.outLanes) {
        acc(o) := Mux(reluComparators(o).io.out(0), PhysicalMath.fp32Zero, acc(o))
      }
      state := sEmit
    }
  }

  val outVec = Wire(Vec(p.outLanes, UInt(p.outputBits.W)))
  for (o <- 0 until p.outLanes) {
    outVec(o) := PhysicalMath.fromFp32(acc(o), p.outputBits)
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
      macInputGroup := 0.U
      macOutputGroup := 0.U
      tokenCnt := Mux(tokenCnt === (p.batchSize - 1).U, 0.U, tokenCnt + 1.U)
    }.otherwise {
      outCnt := outCnt + 1.U
      state := sBiasRead
    }
  }
}

class ParametricLinearInt8ToInt8(p: LinearParams) extends Linear(p)

class ParametricLinearInt8ToFP32(p: LinearParams)
    extends Linear(p.copy(outputBits = 32))
