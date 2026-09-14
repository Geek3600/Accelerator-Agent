package spatialaccagent.templates

import chisel3._
import chisel3.util._
import chisel3.util.experimental.loadMemoryFromFileInline
import hardfloat._
import hardfloat.consts

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

  private val ExpTablePath =
    "src/main/resources/spatialaccagent/numeric/exp2_fraction_q24.memh"
  private val Fp32ExpWidth = 8
  private val Fp32SigWidth = 24
  private val Q11Width = 16
  private val ExpFractionBits = 24
  private val Log2eFixed = 2955

  private def fp32ToSignedQ11(value: UInt): SInt = {
    val scaled = IeeeMath.mulFp32(value, IeeeMath.fp32Constant(2048.0))
    val convert = Module(new RecFNToIN(Fp32ExpWidth, Fp32SigWidth, Q11Width))
    convert.io.in := recFNFromFN(Fp32ExpWidth, Fp32SigWidth, scaled)
    convert.io.roundingMode := consts.round_near_even
    convert.io.signedOut := true.B
    convert.io.out.asSInt
  }

  private def unsignedQ24ToFp32(value: UInt): UInt = {
    val convert = Module(new INToRecFN(value.getWidth, Fp32ExpWidth, Fp32SigWidth))
    convert.io.signedIn := false.B
    convert.io.in := value
    convert.io.roundingMode := consts.round_near_even
    convert.io.detectTininess := consts.tininess_afterRounding
    val integerFp32 = fNFromRecFN(Fp32ExpWidth, Fp32SigWidth, convert.io.out)
    IeeeMath.mulFp32(integerFp32, IeeeMath.fp32Constant(math.pow(2.0, -24.0)))
  }

  val expTable = Mem(2048, UInt(26.W))
  loadMemoryFromFileInline(expTable, ExpTablePath)

  val scoreMem = Reg(Vec(p.seqLen, UInt(p.elemBits.W)))
  val keepMem = RegInit(VecInit(Seq.fill(p.seqLen)(false.B)))
  val addrMem = Reg(Vec(p.beats, UInt(p.addrBits.W)))
  val stMem = RegInit(VecInit(Seq.fill(p.beats)(false.B)))
  val rowIndexReg = RegInit(0.U(p.rowBits.W))
  val rowSeqLimitReg = RegInit(p.seqLen.U(p.seqBits.W))
  val maskReg = RegInit(0.U(p.seqLen.W))

  val sCollect :: sEmit :: Nil = Enum(2)
  val state = RegInit(sCollect)
  val collectCountBits = log2Ceil(p.beats max 2)
  val emitCountBits = log2Ceil(p.beats max 2)
  val emitBeatsBits = log2Ceil(p.beats + 1 max 2)
  val collectCnt = RegInit(0.U(collectCountBits.W))
  val emitCnt = RegInit(0.U(emitCountBits.W))
  val emitBeats = RegInit(p.beats.U(emitBeatsBits.W))
  val seqLimit = RegInit(p.seqLen.U(p.seqBits.W))

  val normalizedCfgSeq = Mux(
    io.cfg.seqlen === 0.U || io.cfg.seqlen > p.seqLen.U,
    p.seqLen.U(p.seqBits.W),
    io.cfg.seqlen
  )
  when(io.cfgValid) {
    seqLimit := normalizedCfgSeq
  }

  io.in.ready := state === sCollect

  val inputVec = io.in.bits.data.asTypeOf(Vec(p.lanes, UInt(p.elemBits.W)))
  val firstCollectBeat = collectCnt === 0.U
  val rowForCollect = Mux(firstCollectBeat, io.rowIndex, rowIndexReg)
  val seqForCollect = Mux(
    firstCollectBeat,
    Mux(io.cfgValid, normalizedCfgSeq, seqLimit),
    rowSeqLimitReg
  )
  val maskForCollect = Mux(firstCollectBeat, io.mask, maskReg)

  when(io.in.fire) {
    when(firstCollectBeat) {
      rowIndexReg := io.rowIndex
      rowSeqLimitReg := Mux(io.cfgValid, normalizedCfgSeq, seqLimit)
      maskReg := io.mask
    }

    addrMem(collectCnt) := io.in.bits.addr
    stMem(collectCnt) := io.in.bits.st

    for (i <- 0 until p.lanes) {
      val index = collectCnt * p.lanes.U + i.U
      val inActiveSequence = index < seqForCollect
      val externalKeep = maskForCollect(index)
      val causalKeep = if (p.causal) index <= rowForCollect else true.B
      val slidingKeep =
        if (p.slidingWindow > 0) {
          index + p.slidingWindow.U > rowForCollect
        } else {
          true.B
        }
      val keep = inActiveSequence && externalKeep && causalKeep && slidingKeep
      scoreMem(index) := inputVec(i)
      keepMem(index) := keep
    }

    val finalConfiguredBeat = collectCnt === (p.beats - 1).U
    when(io.in.bits.last || finalConfiguredBeat) {
      emitBeats := collectCnt +& 1.U
      emitCnt := 0.U
      collectCnt := 0.U
      state := sEmit
    }.otherwise {
      collectCnt := collectCnt + 1.U
    }
  }

  val negativeMaximumFp32 = "hff7fffff".U(32.W)
  val scoreFp32 = Wire(Vec(p.seqLen, UInt(32.W)))
  val maxCandidates = Wire(Vec(p.seqLen, UInt(32.W)))
  for (i <- 0 until p.seqLen) {
    scoreFp32(i) := IeeeMath.toFp32(scoreMem(i), p.elemBits)
    maxCandidates(i) := Mux(keepMem(i), scoreFp32(i), negativeMaximumFp32)
  }

  val maxScoreFp32 = (0 until p.seqLen)
    .map(i => maxCandidates(i))
    .reduce((a, b) => Mux(IeeeMath.lessThanFp32(a, b), b, a))

  val expQ24 = Wire(Vec(p.seqLen, UInt(26.W)))
  val minusSixteen = IeeeMath.fp32Constant(-16.0)
  val expOneQ24 = (BigInt(1) << ExpFractionBits).U(26.W)

  for (i <- 0 until p.seqLen) {
    val shiftedFp32 = IeeeMath.subFp32(scoreFp32(i), maxScoreFp32)
    val shiftedGeZero = !IeeeMath.lessThanFp32(shiftedFp32, IeeeMath.fp32Zero)
    val shiftedLeMinusSixteen = !IeeeMath.lessThanFp32(minusSixteen, shiftedFp32)
    val shiftedQ11 = fp32ToSignedQ11(shiftedFp32)
    val logProductQ22 = shiftedQ11 * Log2eFixed.S(13.W)
    val logProductBits = logProductQ22.asUInt
    val fractionalAddress = logProductBits(21, 11)
    val integerFloor = logProductQ22 >> 22
    val shiftMagnitude = (0.S(logProductQ22.getWidth.W) - integerFloor).asUInt
    val tableValue = expTable.read(fractionalAddress)
    val rangeReducedExp = tableValue >> shiftMagnitude
    val boundedExp = Mux(
      shiftedGeZero,
      expOneQ24,
      Mux(shiftedLeMinusSixteen, 0.U(26.W), rangeReducedExp)
    )
    expQ24(i) := Mux(keepMem(i), boundedExp, 0.U)
  }

  val sumBits = 26 + log2Ceil(p.seqLen max 2)
  val expSum = (0 until p.seqLen)
    .map(i => expQ24(i).pad(sumBits))
    .reduce((a, b) => a + b)
  val safeExpSum = Mux(expSum === 0.U, 1.U(sumBits.W), expSum)

  val probabilityBits = Wire(Vec(p.seqLen, UInt(p.elemBits.W)))
  for (i <- 0 until p.seqLen) {
    val scaledNumerator = Cat(expQ24(i), 0.U(ExpFractionBits.W))
    val quotientWide = scaledNumerator / safeExpSum
    val quotientQ24 = quotientWide(24, 0)
    val remainder = scaledNumerator % safeExpSum
    val doubledRemainder = remainder +& remainder
    val extendedSum = Cat(0.U(1.W), safeExpSum)
    val aboveHalf = doubledRemainder > extendedSum
    val exactlyHalf = doubledRemainder === extendedSum
    val roundUp = aboveHalf || (exactlyHalf && quotientQ24(0))
    val roundedWide = quotientQ24 +& roundUp.asUInt
    val roundedQ24 = roundedWide(24, 0)
    val normalizedQ24 = Mux(expSum === 0.U, 0.U(25.W), roundedQ24)
    val probabilityFp32 = unsignedQ24ToFp32(normalizedQ24)
    probabilityBits(i) := IeeeMath.fromFp32(probabilityFp32, p.elemBits)
  }

  val outputVec = Wire(Vec(p.lanes, UInt(p.elemBits.W)))
  for (i <- 0 until p.lanes) {
    val index = emitCnt * p.lanes.U + i.U
    outputVec(i) := probabilityBits(index)
  }

  io.out.valid := state === sEmit
  io.out.bits.data := outputVec.asUInt
  io.out.bits.st := stMem(emitCnt)
  io.out.bits.addr := addrMem(emitCnt)
  io.out.bits.last := emitCnt === (emitBeats - 1.U)

  when(io.out.fire) {
    when(io.out.bits.last) {
      emitCnt := 0.U
      state := sCollect
      for (i <- 0 until p.seqLen) {
        keepMem(i) := false.B
      }
    }.otherwise {
      emitCnt := emitCnt + 1.U
    }
  }
}
