package DM2

import DM2.Param._
import QuantCommon._
import QuantCommon.Precision._
import chisel3._
import chisel3.util._

class UnsignedSignedMultiplierInt8 extends Module {
  val io = IO(new Bundle() {
    val in0 = Input(UInt(UINT8_WIDTH.W))
    val in1 = Input(SInt(INT8_WIDTH.W))
    val out = Output(SInt(16.W))
  })

  val in0Reg = RegNext(io.in0)
  val in1Reg = RegNext(io.in1)
  io.out := RegNext((in0Reg.zext * in1Reg).asSInt)
}

class SignedAddTreeInt32(val num: Int) extends Module {
  val io = IO(new Bundle() {
    val ins = Input(Vec(num, SInt(16.W)))
    val out = Output(SInt(INT32_WIDTH.W))
  })

  def recTree(vals: Seq[SInt]): SInt = {
    if (vals.length == 1) vals.head
    else {
      val next = vals.grouped(2).map {
        case Seq(a, b) => RegNext((a +& b).asSInt)
        case Seq(a) => RegNext(a)
      }.toSeq
      recTree(next)
    }
  }

  io.out := recTree(io.ins)
}

class DM2CUQuant extends Module {
  import QuantParam._

  val io = IO(new Bundle() {
    val cfg_seqlen = Input(UInt(log2Up(MAX_SEQLEN).W))
    val cfg_prefill = Input(Bool())
    val cfg_valid = Input(Bool())
    val cfg_single_query = Input(Bool())

    val out_inv_scale = Input(UInt(FP32_WIDTH.W))

    val data_in_v = Input(UInt((HEAD_VECNUM * DATAW).W))
    val data_in_v_valid = Input(Bool())
    val data_in_v_ready = Output(Bool())

    val data_in_ctx_st = Input(Bool())
    val data_in_ctx = Input(UInt(CTX_UINT8_WIDTH.W))
    val data_in_ctx_valid = Input(Bool())
    val data_in_ctx_ready = Output(Bool())

    val data_out = Output(UInt((HEAD_VECNUM * DATAW).W))
    val data_out_valid = Output(Bool())
  })

  val prefill = false.B
  val singleQuery = true.B
  val seqlen = RegEnable(io.cfg_seqlen, io.cfg_valid)

  // 当前最终 runtime 只保留 single-query attention 所需的逻辑 history batch。
  // 长序列仍由 MAX_SEQLEN=912 决定，但不再为旧 128-batch 片上 V history 付出面积。
  val historyBatches = SINGLE_QUERY_BATCH
  val vCacheDepth = historyBatches * MAX_SEQLEN
  val vCache = Module(new R1W1Mem(vCacheDepth, HEAD_VECNUM * DATAW))
  // 只保留一个固定 26-long 的片上 V tile buffer。
  val vBuf = RegInit(VecInit(Seq.fill(TILE_SEQLEN)(0.U((HEAD_VECNUM * DATAW).W))))

  val prefillLoadCnt = RegInit(0.U(log2Up(MAX_PREFILL).W))
  val prefillLoadLast = prefillLoadCnt === seqlen
  when(prefill && io.data_in_v_valid) {
    prefillLoadCnt := Mux(prefillLoadLast, 0.U, prefillLoadCnt + 1.U)
  }

  val lbatchCnt = RegInit(0.U(log2Up(historyBatches).W))
  // Single-query decode only delivers one V batch per token through VCache/LoadU.
  // Keep DM2's internal lbatch rotation aligned with that 1-batch contract; the old
  // 12-batch rotation can leave stale slots resident until the very end of a 912-token run.
  val lbatchLast = lbatchCnt === Mux(
    singleQuery,
    0.U(lbatchCnt.getWidth.W),
    (historyBatches - 1).U(lbatchCnt.getWidth.W)
  )
  when(prefill && io.data_in_v_valid && prefillLoadLast || !prefill && io.data_in_v_valid) {
    lbatchCnt := Mux(lbatchLast, 0.U, lbatchCnt + 1.U)
  }

  val vWriteAddr = Wire(UInt(log2Up(vCacheDepth).W))
  val vReadAddr = Wire(UInt(log2Up(vCacheDepth).W))
  vCache.io.wen := io.data_in_v_valid
  vWriteAddr := Mux(
    prefill,
    lbatchCnt * MAX_SEQLEN.U + prefillLoadCnt,
    lbatchCnt * MAX_SEQLEN.U + seqlen
  )
  vCache.io.waddr := vWriteAddr
  vCache.io.wdata := io.data_in_v

  val stcVcache :: stcGetv :: stcWaitctx :: stcC :: stcDrain :: Nil = Enum(5)
  val state = RegInit(stcVcache)
  val isGetv = state === stcGetv
  val isWaitctx = state === stcWaitctx
  val isC = state === stcC
  val isVcache = state === stcVcache
  val isDrain = state === stcDrain
  val headOutDone = WireDefault(false.B)
  val headOutDoneD1 = WireDefault(false.B)
  val tileLoadCnt = RegInit(0.U(log2Up(TILE_SEQLEN).W))
  val tileLastIdx = seqlen(log2Up(TILE_SEQLEN) - 1, 0)
  when(isGetv) {
    tileLoadCnt := Mux(tileLoadCnt === tileLastIdx, 0.U, tileLoadCnt + 1.U)
  }

  val waitctxCnt = RegInit(0.U(log2Up(MAX_PREFILL).W))
  val waitctxLast = waitctxCnt === seqlen
  when(prefill && io.data_in_ctx_valid && io.data_in_ctx_st) {
    waitctxCnt := Mux(waitctxLast, 0.U, waitctxCnt + 1.U)
  }

  val mulCnt = RegInit(0.U(log2Up(HEAD_VECNUM).W))
  val mulLast = mulCnt === (HEAD_VECNUM - 1).U
  when(isC) {
    mulCnt := Mux(mulLast, 0.U, mulCnt + 1.U)
  }

  val stcVcacheMux = Mux(
    prefill,
    Mux(prefillLoadLast && io.data_in_v_valid, stcWaitctx, stcVcache),
    Mux(io.data_in_v_valid, stcWaitctx, stcVcache)
  )
  val lastGetvReq = isGetv && (tileLoadCnt === tileLastIdx)
  val tileLoadDone = RegNext(lastGetvReq, false.B)
  val stcGetvMux = Mux(tileLoadDone, stcC, stcGetv)
  val stcWaitctxMux = Mux(io.data_in_ctx_valid, stcGetv, stcWaitctx)
  val drainToVcache = RegInit(false.B)
  val postDrainHold = RegInit(false.B)
  val stcCMux = Mux(
    mulLast,
    stcDrain,
    stcC
  )
  val stcDrainMux = Mux(drainToVcache, stcVcache, stcWaitctx)

  state := MuxLookup(
    state,
    state
  )(
    List(
      stcVcache -> stcVcacheMux,
      stcGetv -> stcGetvMux,
      stcWaitctx -> stcWaitctxMux,
      stcC -> stcCMux,
      stcDrain -> Mux(headOutDoneD1, stcDrainMux, stcDrain)
    )
  )
  when(isC && mulLast) {
    drainToVcache := waitctxCnt === 0.U
  }
  when(state === stcDrain && headOutDoneD1 && drainToVcache) {
    postDrainHold := true.B
  }.elsewhen(isVcache && postDrainHold) {
    postDrainHold := false.B
  }

  val lbatchCntReg = RegEnable(
    lbatchCnt,
    prefill && io.data_in_v_valid && prefillLoadLast || !prefill && io.data_in_v_valid
  )
  val getvFire = isGetv && !tileLoadDone
  val getvFireD1 = RegNext(getvFire, false.B)
  val getvIdxD1 = RegEnable(tileLoadCnt, 0.U, getvFire)

  vCache.io.ren := getvFire
  vReadAddr := tileLoadCnt + lbatchCntReg * MAX_SEQLEN.U
  vCache.io.raddr := vReadAddr

  when(getvFireD1) {
    vBuf(getvIdxD1) := vCache.io.rdata
  }

  val vList = (0 until TILE_SEQLEN).map { i =>
    MuxLookup(
      mulCnt,
      0.U(DATAW.W)
    )(
      (0 until HEAD_VECNUM).map { j =>
        j.U -> vBuf(i)(DATAW * (j + 1) - 1, DATAW * j)
      }
    ).asSInt
  }

  val ctxTile = RegInit(VecInit(Seq.fill(TILE_SEQLEN)(0.U(UINT8_WIDTH.W))))
  when(io.data_in_ctx_valid) {
    ctxTile := io.data_in_ctx.asTypeOf(Vec(TILE_SEQLEN, UInt(UINT8_WIDTH.W)))
  }
  val ctxList = (0 until TILE_SEQLEN).map { i =>
    Mux(i.U <= seqlen, ctxTile(i), 0.U(UINT8_WIDTH.W))
  }

  val mulList = List.fill(TILE_SEQLEN)(Module(new UnsignedSignedMultiplierInt8))
  val addTree = Module(new SignedAddTreeInt32(TILE_SEQLEN))
  for (i <- 0 until TILE_SEQLEN) {
    mulList(i).io.in0 := ctxList(i)
    mulList(i).io.in1 := vList(i)
    addTree.io.ins(i) := mulList(i).io.out
  }

  val delayMulCntToAddRes = 2 + log2Up(TILE_SEQLEN)
  val addresValidPipe = Module(new PipReg(delayMulCntToAddRes, 1))
  addresValidPipe.io.in := (state === stcC).asUInt
  val addresValid = addresValidPipe.io.out.asBool

  val addresCntPipe = Module(new PipReg(delayMulCntToAddRes, log2Up(HEAD_VECNUM)))
  addresCntPipe.io.in := mulCnt
  val addresCnt = addresCntPipe.io.out

  val quantOutLatency =
    XilinxFpTargetConfig.FixedToFloatLatency +
      XilinxFpTargetConfig.MulLatency +
      XilinxFpTargetConfig.FloatToFixedLatency
  val quantValidPipe = RegInit(VecInit(Seq.fill(quantOutLatency)(false.B)))
  val quantCntPipe = RegInit(VecInit(Seq.fill(quantOutLatency)(0.U(log2Up(HEAD_VECNUM).W))))
  quantValidPipe(0) := addresValid
  quantCntPipe(0) := addresCnt
  for (i <- 1 until quantOutLatency) {
    quantValidPipe(i) := quantValidPipe(i - 1)
    quantCntPipe(i) := quantCntPipe(i - 1)
  }
  val quantValid = quantValidPipe.last
  val quantCnt = quantCntPipe.last
  headOutDone := RegNext(quantValid && quantCnt === (HEAD_VECNUM - 1).U, false.B)
  headOutDoneD1 := RegNext(headOutDone, false.B)

  val partialSum = addTree.io.out

  val resAcc = RegInit(VecInit(Seq.fill(HEAD_VECNUM)(0.S(INT32_WIDTH.W))))
  val res = RegInit(VecInit(Seq.fill(HEAD_VECNUM)(0.U(DATAW.W))))
  val dataOutReg = RegInit(0.U((HEAD_VECNUM * DATAW).W))
  when(isWaitctx && io.data_in_ctx_valid && io.data_in_ctx_st) {
    tileLoadCnt := 0.U
    // data_out_valid is asserted one cycle after the final res write; keep res
    // intact here so the previous head's output beat is not clobbered.
    for (i <- 0 until HEAD_VECNUM) {
      resAcc(i) := 0.S
    }
  }.elsewhen(state === stcC && mulLast) {
    tileLoadCnt := 0.U
  }

  val toFp = Module(new Int32ToFp32)
  val mulScale = Module(new Fp32Mul)
  val toInt8 = Module(new Fp32ToInt8)
  val nextAcc = Wire(SInt(INT32_WIDTH.W))
  nextAcc := Mux(addresValid, resAcc(addresCnt) + partialSum, 0.S)
  toFp.io.in := nextAcc
  mulScale.io.a := toFp.io.out
  mulScale.io.b := io.out_inv_scale
  toInt8.io.in := mulScale.io.out

  when(addresValid) {
    resAcc(addresCnt) := nextAcc
  }
  val resSnapshot = Wire(Vec(HEAD_VECNUM, UInt(DATAW.W)))
  resSnapshot := res
  for (i <- 0 until HEAD_VECNUM) {
    when(quantValid && quantCnt === i.U) {
      res(i) := toInt8.io.out
      resSnapshot(i) := toInt8.io.out
    }
  }
  when(quantValid && quantCnt === (HEAD_VECNUM - 1).U) {
    dataOutReg := resSnapshot.asUInt
  }

  io.data_out := dataOutReg
  io.data_out_valid := headOutDone
  io.data_in_v_ready := isVcache && !postDrainHold
  io.data_in_ctx_ready := isWaitctx
}
