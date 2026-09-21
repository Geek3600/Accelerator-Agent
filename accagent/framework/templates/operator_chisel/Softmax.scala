package spatialaccagent.templates

import chisel3._
import chisel3.util._

final case class SoftmaxParams(
  seqLen: Int,
  lanes: Int = 16,
  elemBits: Int = 16,
  fracBits: Int = 8,
  batchSize: Int = 16,
  causal: Boolean = true,
  slidingWindow: Int = 0
) {
  require(seqLen > 0, "seqLen must be positive")
  require(lanes > 0, "lanes must be positive")
  require(elemBits == 16 || elemBits == 32, "softmax elements must be IEEE fp16 or fp32")
  require(fracBits >= 0, "fracBits must be non-negative")
  require(seqLen % lanes == 0, "softmax requires seqLen divisible by lanes")
  require(slidingWindow >= 0, "slidingWindow must be non-negative")

  val beats: Int = seqLen / lanes
  val beatBits: Int = lanes * elemBits
  val addrBits: Int = log2Ceil(batchSize * beats max 2)
  val rowBits: Int = log2Ceil(seqLen max 2)
  val seqBits: Int = log2Ceil(seqLen + 1 max 2)
}

class Softmax(p: SoftmaxParams) extends Module {
  val io = IO(new Bundle {
    val cfg = Input(new StageConfig(p.seqBits))
    val cfgValid = Input(Bool())
    val rowIndex = Input(UInt(p.rowBits.W))
    val mask = Input(UInt(p.seqLen.W))
    val in = Flipped(Decoupled(new StreamBeat(StreamSpec(p.beatBits, p.addrBits))))
    val out = Decoupled(new StreamBeat(StreamSpec(p.beatBits, p.addrBits)))
  })

  private val expTablePath = "src/main/resources/spatialaccagent/numeric/exp2_fraction_q24.mem"
  private val q11Width = 16
  private val expFractionBits = 24
  private val log2eFixed = 2955
  private val expBits = 26
  private val sumBits = expBits + log2Ceil(p.seqLen max 2)
  private val metaBits = p.addrBits + 1

  val scoreMemory = Module(new PhysicalSimpleDualPortMemory(p.beats, p.beatBits, "activation"))
  val keepMemory = Module(new PhysicalSimpleDualPortMemory(p.beats, p.lanes, "activation"))
  val expMemory = Module(new PhysicalSimpleDualPortMemory(p.beats, p.lanes * expBits, "activation"))
  val metaMemory = Module(new PhysicalSimpleDualPortMemory(p.beats, metaBits, "activation"))
  val expRom = Module(new PhysicalRom(2048, expBits, expTablePath))

  private val states = Enum(23)
  private val sCollect = states(0)
  private val sMaxRead = states(1)
  private val sMaxCapture = states(2)
  private val sMaxCompareIssue = states(3)
  private val sMaxCompareWait = states(4)
  private val sExpRead = states(5)
  private val sExpCapture = states(6)
  private val sShiftIssue = states(7)
  private val sShiftWait = states(8)
  private val sClassifyIssue = states(9)
  private val sClassifyWait = states(10)
  private val sConvertIssue = states(11)
  private val sConvertWait = states(12)
  private val sTableIssue = states(13)
  private val sTableCapture = states(14)
  private val sExpCommit = states(15)
  private val sEmitRead = states(16)
  private val sEmitCapture = states(17)
  private val sProbabilityConvertIssue = states(18)
  private val sProbabilityConvertWait = states(19)
  private val sProbabilityDivideIssue = states(20)
  private val sProbabilityDivideWait = states(21)
  private val sEmit = states(22)
  val state = RegInit(sCollect)

  val seqLimit = RegInit(p.seqLen.U(p.seqBits.W))
  val rowIndexReg = RegInit(0.U(p.rowBits.W))
  val maskReg = RegInit(0.U(p.seqLen.W))
  val activeBeats = RegInit(p.beats.U(log2Ceil(p.beats + 1 max 2).W))
  val collectBeat = RegInit(0.U(log2Ceil(p.beats max 2).W))
  val workBeat = RegInit(0.U(log2Ceil(p.beats max 2).W))
  val workLane = RegInit(0.U(log2Ceil(p.lanes max 2).W))
  val emitBeat = RegInit(0.U(log2Ceil(p.beats max 2).W))
  val emitLane = RegInit(0.U(log2Ceil(p.lanes max 2).W))

  val scoreBeatReg = Reg(UInt(p.beatBits.W))
  val keepBeatReg = Reg(UInt(p.lanes.W))
  val expBeatReg = Reg(Vec(p.lanes, UInt(expBits.W)))
  val emitExpReg = Reg(UInt((p.lanes * expBits).W))
  val emitMetaReg = Reg(UInt(metaBits.W))
  val outputBeatReg = Reg(Vec(p.lanes, UInt(p.elemBits.W)))
  val maxReg = Reg(UInt(32.W))
  val maxInitialized = RegInit(false.B)
  val expSumReg = RegInit(0.U(sumBits.W))
  val shiftedReg = Reg(UInt(32.W))
  val scaledReg = Reg(UInt(32.W))
  val q11Reg = Reg(SInt(q11Width.W))
  val geZeroReg = RegInit(false.B)
  val leMinusSixteenReg = RegInit(false.B)
  val probabilityNumeratorFpReg = Reg(UInt(32.W))
  val probabilityDenominatorFpReg = Reg(UInt(32.W))

  val normalizedCfgSeq = Mux(
    io.cfg.seqlen === 0.U || io.cfg.seqlen > p.seqLen.U,
    p.seqLen.U(p.seqBits.W),
    io.cfg.seqlen
  )
  when(io.cfgValid) {
    seqLimit := normalizedCfgSeq
  }

  val inputValues = io.in.bits.data.asTypeOf(Vec(p.lanes, UInt(p.elemBits.W)))
  val inputKeep = Wire(Vec(p.lanes, Bool()))
  val firstCollect = collectBeat === 0.U
  val collectRow = Mux(firstCollect, io.rowIndex, rowIndexReg)
  val collectLimit = Mux(firstCollect, Mux(io.cfgValid, normalizedCfgSeq, seqLimit), seqLimit)
  val collectMask = Mux(firstCollect, io.mask, maskReg)
  for (lane <- 0 until p.lanes) {
    val index = collectBeat * p.lanes.U + lane.U
    val inSequence = index < collectLimit
    val maskKeep = collectMask(AccMath.boundedIndex(index, p.seqLen))
    val causalKeep = if (p.causal) index <= collectRow else true.B
    val windowKeep = if (p.slidingWindow > 0) index + p.slidingWindow.U > collectRow else true.B
    inputKeep(lane) := inSequence && maskKeep && causalKeep && windowKeep
  }

  io.in.ready := state === sCollect
  scoreMemory.io.writeEn := io.in.fire
  scoreMemory.io.writeAddr := collectBeat
  scoreMemory.io.writeData := io.in.bits.data
  keepMemory.io.writeEn := io.in.fire
  keepMemory.io.writeAddr := collectBeat
  keepMemory.io.writeData := inputKeep.asUInt
  metaMemory.io.writeEn := io.in.fire
  metaMemory.io.writeAddr := collectBeat
  metaMemory.io.writeData := Cat(io.in.bits.addr, io.in.bits.st)
  expMemory.io.writeEn := state === sExpCommit
  expMemory.io.writeAddr := workBeat
  expMemory.io.writeData := expBeatReg.asUInt

  when(io.in.fire) {
    when(firstCollect) {
      rowIndexReg := io.rowIndex
      maskReg := io.mask
    }
    when(io.in.bits.last || collectBeat === (p.beats - 1).U) {
      activeBeats := collectBeat +& 1.U
      collectBeat := 0.U
      workBeat := 0.U
      workLane := 0.U
      maxInitialized := false.B
      expSumReg := 0.U
      state := sMaxRead
    }.otherwise {
      collectBeat := collectBeat + 1.U
    }
  }

  val readingMax = state === sMaxRead
  val readingExp = state === sExpRead
  val readingEmit = state === sEmitRead
  scoreMemory.io.readEn := readingMax || readingExp
  scoreMemory.io.readAddr := workBeat
  keepMemory.io.readEn := readingMax || readingExp
  keepMemory.io.readAddr := workBeat
  expMemory.io.readEn := readingEmit
  expMemory.io.readAddr := emitBeat
  metaMemory.io.readEn := readingEmit
  metaMemory.io.readAddr := emitBeat
  expRom.io.readEn := state === sTableIssue

  // XPM supplies the first requested beat on the capture cycle. Subsequent
  // lanes use the registered copy while the same beat is being scanned.
  val currentScoreBeat = Mux(workLane === 0.U, scoreMemory.io.readData, scoreBeatReg)
  val currentKeepBeat = Mux(workLane === 0.U, keepMemory.io.readData, keepBeatReg)
  val selectedLane = AccMath.boundedIndex(workLane, p.lanes)
  val selectedScore = if (p.lanes == 1) {
    currentScoreBeat.asTypeOf(Vec(1, UInt(p.elemBits.W)))(0)
  } else {
    currentScoreBeat.asTypeOf(Vec(p.lanes, UInt(p.elemBits.W)))(selectedLane)
  }
  val selectedScoreFp = PhysicalMath.toFp32(selectedScore, p.elemBits)
  val selectedKeep = if (p.lanes == 1) currentKeepBeat(0) else currentKeepBeat(selectedLane)

  def advanceMax(): Unit = {
    when(workLane === (p.lanes - 1).U) {
      workLane := 0.U
      when(workBeat === activeBeats - 1.U) {
        workBeat := 0.U
        state := sExpRead
      }.otherwise {
        workBeat := workBeat + 1.U
        state := sMaxRead
      }
    }.otherwise {
      workLane := workLane + 1.U
      state := sMaxCapture
    }
  }

  when(state === sMaxRead) {
    state := sMaxCapture
  }
  when(state === sMaxCapture) {
    when(workLane === 0.U) {
      scoreBeatReg := scoreMemory.io.readData
      keepBeatReg := keepMemory.io.readData
    }
    when(!selectedKeep) {
      advanceMax()
    }.elsewhen(!maxInitialized) {
      maxReg := selectedScoreFp
      maxInitialized := true.B
      advanceMax()
    }.otherwise {
      state := sMaxCompareIssue
    }
  }

  val maxCompare = Module(new PhysicalFp32CompareLt)
  maxCompare.io.a := maxReg
  maxCompare.io.b := selectedScoreFp
  maxCompare.io.inValid := state === sMaxCompareIssue && maxCompare.io.inReady
  when(state === sMaxCompareIssue && maxCompare.io.inReady) {
    state := sMaxCompareWait
  }
  when(state === sMaxCompareWait && maxCompare.io.outValid) {
    maxReg := Mux(maxCompare.io.out(0), selectedScoreFp, maxReg)
    advanceMax()
  }

  def advanceExp(): Unit = {
    when(workLane === (p.lanes - 1).U) {
      workLane := 0.U
      state := sExpCommit
    }.otherwise {
      workLane := workLane + 1.U
      state := sExpCapture
    }
  }

  when(state === sExpRead) {
    state := sExpCapture
  }
  when(state === sExpCapture) {
    when(workLane === 0.U) {
      scoreBeatReg := scoreMemory.io.readData
      keepBeatReg := keepMemory.io.readData
      for (lane <- 0 until p.lanes) {
        expBeatReg(lane) := 0.U
      }
    }
    when(!selectedKeep) {
      expBeatReg(AccMath.boundedIndex(workLane, p.lanes)) := 0.U
      advanceExp()
    }.otherwise {
      state := sShiftIssue
    }
  }

  val subtract = Module(new PhysicalFp32Sub)
  subtract.io.a := selectedScoreFp
  subtract.io.b := maxReg
  subtract.io.inValid := state === sShiftIssue && subtract.io.inReady
  when(state === sShiftIssue && subtract.io.inReady) {
    state := sShiftWait
  }
  when(state === sShiftWait && subtract.io.outValid) {
    shiftedReg := subtract.io.out
    state := sClassifyIssue
  }

  val scaleForQ11 = Module(new PhysicalFp32Mul)
  val compareZero = Module(new PhysicalFp32CompareLt)
  val compareMinusSixteen = Module(new PhysicalFp32CompareLt)
  scaleForQ11.io.a := shiftedReg
  scaleForQ11.io.b := PhysicalMath.fp32Constant(2048.0)
  compareZero.io.a := shiftedReg
  compareZero.io.b := PhysicalMath.fp32Zero
  compareMinusSixteen.io.a := PhysicalMath.fp32Constant(-16.0)
  compareMinusSixteen.io.b := shiftedReg
  val classifyReady = scaleForQ11.io.inReady && compareZero.io.inReady && compareMinusSixteen.io.inReady
  val classifyIssue = state === sClassifyIssue && classifyReady
  scaleForQ11.io.inValid := classifyIssue
  compareZero.io.inValid := classifyIssue
  compareMinusSixteen.io.inValid := classifyIssue
  when(classifyIssue) {
    state := sClassifyWait
  }
  when(state === sClassifyWait && scaleForQ11.io.outValid && compareZero.io.outValid && compareMinusSixteen.io.outValid) {
    scaledReg := scaleForQ11.io.out
    geZeroReg := !compareZero.io.out(0)
    leMinusSixteenReg := !compareMinusSixteen.io.out(0)
    state := sConvertIssue
  }

  val q11Convert = Module(new PhysicalFp32ToSigned(q11Width))
  q11Convert.io.in := scaledReg
  q11Convert.io.inValid := state === sConvertIssue && q11Convert.io.inReady
  when(state === sConvertIssue && q11Convert.io.inReady) {
    state := sConvertWait
  }
  when(state === sConvertWait && q11Convert.io.outValid) {
    q11Reg := q11Convert.io.out
    state := sTableIssue
  }

  val logProduct = q11Reg * log2eFixed.S(13.W)
  val logBits = logProduct.asUInt
  expRom.io.readAddr := logBits(21, 11)
  val integerFloor = logProduct >> 22
  val shiftMagnitude = (0.S(logProduct.getWidth.W) - integerFloor).asUInt
  when(state === sTableIssue) {
    state := sTableCapture
  }
  val expOne = (BigInt(1) << expFractionBits).U(expBits.W)
  val tableExp = expRom.io.readData >> shiftMagnitude
  val boundedExp = Mux(geZeroReg, expOne, Mux(leMinusSixteenReg, 0.U(expBits.W), tableExp))
  when(state === sTableCapture) {
    expBeatReg(AccMath.boundedIndex(workLane, p.lanes)) := boundedExp
    expSumReg := expSumReg + boundedExp
    advanceExp()
  }
  when(state === sExpCommit) {
    when(workBeat === activeBeats - 1.U) {
      emitBeat := 0.U
      emitLane := 0.U
      state := sEmitRead
    }.otherwise {
      workBeat := workBeat + 1.U
      state := sExpRead
    }
  }

  when(state === sEmitRead) {
    state := sEmitCapture
  }
  when(state === sEmitCapture) {
    emitExpReg := expMemory.io.readData
    emitMetaReg := metaMemory.io.readData
    emitLane := 0.U
    state := sProbabilityConvertIssue
  }

  val emitExpValues = emitExpReg.asTypeOf(Vec(p.lanes, UInt(expBits.W)))
  val safeExpSum = Mux(expSumReg === 0.U, 1.U(sumBits.W), expSumReg)
  val probabilityNumerator = Module(new PhysicalUIntToFp32(expBits))
  val probabilityDenominator = Module(new PhysicalUIntToFp32(sumBits))
  val probabilityDivide = Module(new PhysicalFp32Div)
  probabilityNumerator.io.in := emitExpValues(AccMath.boundedIndex(emitLane, p.lanes))
  probabilityDenominator.io.in := safeExpSum
  val probabilityConvertReady = probabilityNumerator.io.inReady && probabilityDenominator.io.inReady
  val probabilityConvertIssue = state === sProbabilityConvertIssue && probabilityConvertReady
  probabilityNumerator.io.inValid := probabilityConvertIssue
  probabilityDenominator.io.inValid := probabilityConvertIssue
  when(probabilityConvertIssue) {
    state := sProbabilityConvertWait
  }
  when(
    state === sProbabilityConvertWait &&
      probabilityNumerator.io.outValid &&
      probabilityDenominator.io.outValid
  ) {
    probabilityNumeratorFpReg := probabilityNumerator.io.out
    probabilityDenominatorFpReg := probabilityDenominator.io.out
    state := sProbabilityDivideIssue
  }

  probabilityDivide.io.a := probabilityNumeratorFpReg
  probabilityDivide.io.b := probabilityDenominatorFpReg
  probabilityDivide.io.inValid := state === sProbabilityDivideIssue && probabilityDivide.io.inReady
  when(state === sProbabilityDivideIssue && probabilityDivide.io.inReady) {
    state := sProbabilityDivideWait
  }
  when(state === sProbabilityDivideWait && probabilityDivide.io.outValid) {
    outputBeatReg(AccMath.boundedIndex(emitLane, p.lanes)) := PhysicalMath.fromFp32(probabilityDivide.io.out, p.elemBits)
    when(emitLane === (p.lanes - 1).U) {
      emitLane := 0.U
      state := sEmit
    }.otherwise {
      emitLane := emitLane + 1.U
      state := sProbabilityConvertIssue
    }
  }

  io.out.valid := state === sEmit
  io.out.bits.data := outputBeatReg.asUInt
  io.out.bits.st := emitMetaReg(0)
  io.out.bits.addr := emitMetaReg(metaBits - 1, 1)
  io.out.bits.last := emitBeat === activeBeats - 1.U
  when(io.out.fire) {
    when(io.out.bits.last) {
      emitBeat := 0.U
      state := sCollect
    }.otherwise {
      emitBeat := emitBeat + 1.U
      state := sEmitRead
    }
  }

  dontTouch(io.cfg)
}
