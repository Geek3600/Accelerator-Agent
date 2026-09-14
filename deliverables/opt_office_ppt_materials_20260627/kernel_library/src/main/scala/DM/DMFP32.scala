package DM

import DM.FP32Param._
import QuantCommon.{Fp32Mul, Fp32MulComb, FpBackend, Int32ToFp32, Int32ToFp32Comb}
import QuantCommon.Precision._
import chisel3._
import chisel3.util._

class SignedMultiplierInt8 extends Module {
  val io = IO(new Bundle() {
    val in0 = Input(SInt(DATAW.W))
    val in1 = Input(SInt(DATAW.W))
    val out = Output(SInt(16.W))
  })
  io.out := RegNext(RegNext(io.in0 * io.in1))
}

class SignedAddTree32(val num: Int) extends Module {
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

class StoreUnitFP32 extends Module {
  val io = IO(new Bundle() {
    val cfg_seqlen = Input(UInt(log2Up(LOCAL_PREFILL).W))
    val cfg_prefill = Input(Bool())
    val cfg_valid = Input(Bool())
    val cfg_single_query = Input(Bool())

    val data_in = Input(UInt(OUT_WIDTH.W))
    val data_in_st = Input(Bool())
    val data_in_tile_last = Input(Bool())
    val data_in_valid = Input(Bool())
    val data_in_ready = Input(Bool())

    val data_out = Output(UInt(OUT_WIDTH.W))
    val data_out_st = Output(Bool())
    val data_out_addr = Output(UInt(log2Up(BATCHSIZE).W))
    val data_out_valid = Output(Bool())
    val data_out_last = Output(Bool())
  })

  val seqlen = RegEnable(io.cfg_seqlen, io.cfg_valid)
  val is_prefill = false.B
  val is_single_query = true.B

  val batch_cnt = RegInit(0.U(log2Up(math.max(BATCHSIZE, LOCAL_PREFILL)).W))
  val decode_batch_last = Mux(is_single_query, 0.U(batch_cnt.getWidth.W), (BATCHSIZE - 1).U(batch_cnt.getWidth.W))
  val batch_last = batch_cnt === Mux(is_prefill, seqlen, decode_batch_last)
  val fire = io.data_in_valid && io.data_in_ready

  when(fire && io.data_in_tile_last) {
    batch_cnt := Mux(batch_last, 0.U, batch_cnt + 1.U)
  }

  io.data_out := io.data_in
  io.data_out_st := io.data_in_st
  io.data_out_addr := batch_cnt
  io.data_out_valid := io.data_in_valid
  io.data_out_last := io.data_in_tile_last && io.data_in_valid
}

// DM1 的 FP32 版本
// 输入仍为 INT8 Q/K，输出改为 FP32 logits
class DMCUPlusFP32 extends Module {
  val io = IO(new Bundle() {
    val cfg_seqlen = Input(UInt(log2Up(MAX_SEQLEN).W))
    val cfg_prefill = Input(Bool())
    val cfg_valid = Input(Bool())
    val cfg_single_query = Input(Bool())

    val out_scale = Input(UInt(FP32_WIDTH.W))

    val data_in = Input(UInt((LOAD_VECNUM * DATAW * 2).W))
    val data_in_valid = Input(Bool())
    val data_in_ready = Output(Bool())

    val data_out = Output(UInt(OUT_WIDTH.W))
    val data_out_st = Output(Bool())
    val data_out_last = Output(Bool())
    val data_out_valid = Output(Bool())
    val data_out_ready = Input(Bool())
  })

  val is_prefill = false.B
  val is_single_query = true.B
  val seqlen = RegEnable(io.cfg_seqlen, io.cfg_valid)

  val headvec_num = HEAD_VECNUM / LOAD_VECNUM
  val headvec_cnt = RegInit(0.U(log2Up(headvec_num).W))
  val headvec_last = headvec_cnt === (headvec_num - 1).U

  val inputFire = io.data_in_valid && io.data_in_ready

  when(inputFire) {
    headvec_cnt := Mux(headvec_last, 0.U, headvec_cnt + 1.U)
  }

  val in_q = io.data_in(LOAD_VECNUM * DATAW - 1, 0)
  val in_k = io.data_in(LOAD_VECNUM * DATAW * 2 - 1, LOAD_VECNUM * DATAW)

  val qVec = Reg(Vec(headvec_num, UInt((LOAD_VECNUM * DATAW).W)))
  val kVec = Reg(Vec(headvec_num, UInt((LOAD_VECNUM * DATAW).W)))
  when(inputFire) {
    qVec(headvec_cnt) := in_q
    kVec(headvec_cnt) := in_k
  }

  val qkVecValid = RegNext(headvec_last && inputFire, false.B)

  val prefill_cnt = RegInit(0.U(log2Up(MAX_PREFILL).W))
  when(qkVecValid && is_prefill) {
    prefill_cnt := Mux(prefill_cnt === seqlen, 0.U, prefill_cnt + 1.U)
  }

  // 当前统一后的 runtime 路径只保留 single-query 所需的 12 组逻辑 history batch。
  // 这样保持 912 历史长度不变，但不再为旧的 32-batch attention 片上缓存付出面积。
  val historyBatches = SINGLE_QUERY_BATCH
  val lbatch_cnt = RegInit(0.U(log2Up(historyBatches).W))
  val lbatch_last = lbatch_cnt === (historyBatches - 1).U
  when(qkVecValid && (!is_prefill || prefill_cnt === seqlen)) {
    lbatch_cnt := Mux(lbatch_last, 0.U, lbatch_cnt + 1.U)
  }
  val lbatch_cnt_r = RegEnable(lbatch_cnt, qkVecValid && (!is_prefill || prefill_cnt === seqlen))

  val qCache = Module(new R1W1Mem(LOCAL_PREFILL, HEAD_VECNUM * DATAW))
  val kCacheDepth = historyBatches * MAX_SEQLEN
  val kCache = Module(new R1W1Mem(kCacheDepth, HEAD_VECNUM * DATAW))
  val resVec = RegInit(VecInit(Seq.fill(TILE_SEQLEN)(0.U(FP32_WIDTH.W))))
  val qWriteAddr = Wire(UInt(log2Up(LOCAL_PREFILL).W))
  val kWriteAddr = Wire(UInt(log2Up(kCacheDepth).W))
  qWriteAddr := Mux(
    prefill_cnt >= LOCAL_PREFILL.U,
    (LOCAL_PREFILL - 1).U,
    prefill_cnt(log2Up(LOCAL_PREFILL) - 1, 0)
  )
  kWriteAddr := Mux(
    is_prefill,
    lbatch_cnt * MAX_SEQLEN.U + prefill_cnt,
    lbatch_cnt * MAX_SEQLEN.U + seqlen
  )

  qCache.io.wen := qkVecValid
  qCache.io.wdata := qVec.asUInt
  qCache.io.waddr := Mux(is_prefill, qWriteAddr, 0.U)

  kCache.io.wen := qkVecValid
  kCache.io.wdata := kVec.asUInt
  kCache.io.waddr := kWriteAddr

  val st_load :: st_compute :: st_emit :: Nil = Enum(3)
  val state = RegInit(st_load)
  val is_comp = state === st_compute
  val is_emit = state === st_emit
  val computeDone = RegInit(false.B)

  when(state === st_load && qkVecValid && (!is_prefill || prefill_cnt === seqlen)) {
    for (lane <- 0 until TILE_SEQLEN) {
      resVec(lane) := 0.U
    }
    computeDone := false.B
    state := st_compute
  }

  val comp_headv_cnt = RegInit(0.U(log2Up(HEAD_VECNUM / MULNUM).W))
  val comp_key_cnt = RegInit(0.U(log2Up(MAX_SEQLEN).W))
  val comp_prefill_q_cnt = RegInit(0.U(log2Up(MAX_PREFILL).W))
  val qReadAddr = Wire(UInt(log2Up(LOCAL_PREFILL).W))
  val kReadAddr = Wire(UInt(log2Up(kCacheDepth).W))
  qReadAddr := Mux(
    comp_prefill_q_cnt >= LOCAL_PREFILL.U,
    (LOCAL_PREFILL - 1).U,
    comp_prefill_q_cnt(log2Up(LOCAL_PREFILL) - 1, 0)
  )
  kReadAddr := lbatch_cnt_r * MAX_SEQLEN.U + comp_key_cnt

  val comp_headv_last = comp_headv_cnt === (HEAD_VECNUM / MULNUM - 1).U
  val comp_key_last = comp_key_cnt === seqlen
  val comp_prefill_q_last = comp_prefill_q_cnt === seqlen

  val compFinalKey = comp_headv_last && comp_key_last
  val compFinalRow = compFinalKey && (!is_prefill || comp_prefill_q_last)
  val compActive = is_comp && !computeDone

  when(compActive) {
    when(comp_headv_last) {
      comp_headv_cnt := 0.U
      when(comp_key_last) {
        comp_key_cnt := 0.U
        when(is_prefill) {
          when(comp_prefill_q_last) {
            comp_prefill_q_cnt := 0.U
            computeDone := true.B
          }.otherwise {
            comp_prefill_q_cnt := comp_prefill_q_cnt + 1.U
          }
        }.otherwise {
          computeDone := true.B
        }
      }.otherwise {
        comp_key_cnt := comp_key_cnt + 1.U
      }
    }.otherwise {
      comp_headv_cnt := comp_headv_cnt + 1.U
    }
  }

  qCache.io.ren := compActive
  qCache.io.raddr := Mux(is_prefill, qReadAddr, 0.U)
  kCache.io.ren := compActive
  kCache.io.raddr := kReadAddr

  val qSel = MuxLookup(
    RegNext(comp_headv_cnt),
    0.U
  )(
    (0 until HEAD_VECNUM / MULNUM).map { i =>
      i.U -> qCache.io.rdata((i + 1) * MULNUM * DATAW - 1, i * MULNUM * DATAW)
    }
  )
  val kSel = MuxLookup(
    RegNext(comp_headv_cnt),
    0.U
  )(
    (0 until HEAD_VECNUM / MULNUM).map { i =>
      i.U -> kCache.io.rdata((i + 1) * MULNUM * DATAW - 1, i * MULNUM * DATAW)
    }
  )

  val mullist = List.fill(MULNUM)(Module(new SignedMultiplierInt8))
  for (i <- 0 until MULNUM) {
    val qElem = qSel((i + 1) * DATAW - 1, i * DATAW).asSInt
    val kElem = kSel((i + 1) * DATAW - 1, i * DATAW).asSInt
    mullist(i).io.in0 := qElem
    mullist(i).io.in1 := kElem
  }

  val addtree = Module(new SignedAddTree32(MULNUM))
  for (i <- 0 until MULNUM) {
    addtree.io.ins(i) := mullist(i).io.out
  }

  val acc_first = comp_headv_cnt === 0.U
  val acc_first_pipreg = Module(new PipReg(1 + 2 + log2Up(MULNUM), 1))
  acc_first_pipreg.io.in := acc_first.asUInt

  val acc_update = compActive
  val acc_update_pipreg = Module(new PipReg(1 + 2 + log2Up(MULNUM), 1))
  acc_update_pipreg.io.in := acc_update.asUInt

  val acc = RegInit(0.S(INT32_WIDTH.W))
  when(acc_update_pipreg.io.out.asBool) {
    acc := Mux(
      acc_first_pipreg.io.out.asBool,
      addtree.io.out,
      acc + addtree.io.out
    )
  }

  val acc_valid = comp_headv_last && compActive
  val acc_valid_pipreg = Module(new PipReg(1 + 2 + log2Up(MULNUM) + 1, 1))
  acc_valid_pipreg.io.in := acc_valid.asUInt

  val res_ksel = comp_key_cnt
  val res_ksel_pipreg = Module(new PipReg(1 + 2 + log2Up(MULNUM) + 1, log2Up(MAX_SEQLEN)))
  res_ksel_pipreg.io.in := res_ksel
  val resIdx = res_ksel_pipreg.io.out
  val resTileLane = resIdx % TILE_SEQLEN.U
  val scalarMulOut = Wire(UInt(FP32_WIDTH.W))
  if (FpBackend.useVivadoIp) {
    val scalarToFp = Module(new Int32ToFp32)
    val scalarMul = Module(new Fp32Mul)
    scalarToFp.io.in := acc
    scalarMul.io.a := scalarToFp.io.out
    scalarMul.io.b := io.out_scale
    scalarMulOut := scalarMul.io.out
  } else {
    val scalarToFp = Module(new Int32ToFp32Comb)
    val scalarMul = Module(new Fp32MulComb)
    scalarToFp.io.in := acc
    scalarMul.io.a := scalarToFp.io.out
    scalarMul.io.b := io.out_scale
    scalarMulOut := scalarMul.io.out
  }

  for (lane <- 0 until TILE_SEQLEN) {
    when(acc_valid_pipreg.io.out.asBool && resTileLane === lane.U) {
      resVec(lane) := scalarMulOut
    }
  }

  val rowDone = RegNext(res_ksel_pipreg.io.out === seqlen && acc_valid_pipreg.io.out.asBool, false.B)

  when(rowDone) {
    computeDone := false.B
    state := st_emit
  }.elsewhen(is_emit && io.data_out_ready) {
    state := st_load
  }

  io.data_in_ready := state === st_load
  io.data_out := resVec.asUInt
  io.data_out_st := is_emit
  io.data_out_last := is_emit
  io.data_out_valid := is_emit
}

class DM1FP32 extends Module {
  val io = IO(new Bundle() {
    val cfg_seqlen = Input(UInt(log2Up(MAX_SEQLEN).W))
    val cfg_prefill = Input(Bool())
    val cfg_valid = Input(Bool())
    val cfg_single_query = Input(Bool())

    val out_scale = Input(UInt(FP32_WIDTH.W))

    val data_in_st = Input(Bool())
    val data_in = Input(UInt((2 * LOAD_VECNUM * DATAW).W))
    val data_addr = Input(UInt(log2Up(HEAD_VECNUM / LOAD_VECNUM * BATCHSIZE).W))
    val data_valid = Input(Bool())
    val data_last = Input(Bool())
    val data_ready = Output(Bool())

    val res = Output(UInt(OUT_WIDTH.W))
    val res_st = Output(Bool())
    val res_addr = Output(UInt(log2Up(BATCHSIZE).W))
    val res_valid = Output(Bool())
    val res_last = Output(Bool())
    val res_ready = Input(Bool())
  })

  val lu_inst = Module(new LoadUnit)
  val cu_inst = Module(new DMCUPlusFP32)
  val su_inst = Module(new StoreUnitFP32)
  val mem_inst = Module(new DataMem(HEAD_VECNUM / LOAD_VECNUM * BATCHSIZE, 2 * LOAD_VECNUM * DATAW))

  mem_inst.io.w_st := io.data_in_st
  mem_inst.io.w_last := io.data_last
  mem_inst.io.w_data := io.data_in
  mem_inst.io.w_addr := io.data_addr
  mem_inst.io.w_valid := io.data_valid
  mem_inst.io.r_last := lu_inst.io.data_in_last
  mem_inst.io.r_addr := lu_inst.io.data_in_addr

  lu_inst.io.cfg_prelen := io.cfg_seqlen
  lu_inst.io.cfg_prefill := io.cfg_prefill
  lu_inst.io.cfg_valid := io.cfg_valid
  lu_inst.io.cfg_single_query := io.cfg_single_query
  lu_inst.io.data_in := mem_inst.io.r_data
  lu_inst.io.data_in_ready := mem_inst.io.r_ready
  lu_inst.io.data_out_ready := cu_inst.io.data_in_ready

  cu_inst.io.cfg_prefill := io.cfg_prefill
  cu_inst.io.cfg_valid := io.cfg_valid
  cu_inst.io.cfg_seqlen := io.cfg_seqlen
  cu_inst.io.cfg_single_query := io.cfg_single_query
  cu_inst.io.out_scale := io.out_scale
  cu_inst.io.data_in := lu_inst.io.data_out
  cu_inst.io.data_in_valid := lu_inst.io.data_out_valid
  cu_inst.io.data_out_ready := io.res_ready

  su_inst.io.cfg_seqlen := io.cfg_seqlen
  su_inst.io.cfg_prefill := io.cfg_prefill
  su_inst.io.cfg_valid := io.cfg_valid
  su_inst.io.cfg_single_query := io.cfg_single_query
  su_inst.io.data_in := cu_inst.io.data_out
  su_inst.io.data_in_st := cu_inst.io.data_out_st
  su_inst.io.data_in_tile_last := cu_inst.io.data_out_last
  su_inst.io.data_in_valid := cu_inst.io.data_out_valid
  su_inst.io.data_in_ready := io.res_ready

  io.data_ready := mem_inst.io.w_ready
  val inputFire = io.data_valid && io.data_ready
  lu_inst.io.launch := inputFire && io.data_in_st
  io.res := su_inst.io.data_out
  io.res_st := su_inst.io.data_out_st
  io.res_addr := su_inst.io.data_out_addr
  io.res_valid := su_inst.io.data_out_valid
  io.res_last := su_inst.io.data_out_last
}

object DM1FP32Gen extends App {
  emitVerilog(new DM1FP32, Array("--target-dir", "generated"))
}
