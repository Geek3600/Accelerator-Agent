package DM2

import DM2.Param._
import chisel3._
import chisel3.util._
class LoadUnit extends Module{
  val io = IO(new Bundle() {
    val cfg_seqlen = Input(UInt(log2Up(MAX_SEQLEN).W))
    val cfg_prefill = Input(Bool())
    val cfg_valid = Input(Bool())
    val cfg_single_query = Input(Bool())

    val data_in_v = Input(UInt((HEAD_VECNUM * DATAW).W))
    val data_in_v_en = Output(Bool())
    val data_in_v_addr = Output(UInt(log2Up(MEM_DEPTH).W))
    val data_in_v_last = Output(Bool())
    val data_in_v_ready = Input(Bool())

    val data_in_ctx = Input(UInt((MAX_SEQLEN * DATAW).W))
    val data_in_ctx_en = Output(Bool())
    val data_in_ctx_addr = Output(UInt(log2Up(MEM_DEPTH).W))
    val data_in_ctx_last = Output(Bool())
    val data_in_ctx_ready = Input(Bool())


    val data_out_v = Output(UInt((HEAD_VECNUM * DATAW).W))
    val data_out_v_valid = Output(Bool())
    val data_out_ctx = Output(UInt((MAX_SEQLEN * DATAW).W))
    val data_out_ctx_valid = Output(Bool())
    val data_out_ready = Input(Bool())
    val data_out_start = Output(Bool())
  })

  val seqlen = RegEnable(io.cfg_seqlen,io.cfg_valid)
  val prefill = RegEnable(io.cfg_prefill,io.cfg_valid)
  val singleQuery = RegEnable(io.cfg_single_query, false.B, io.cfg_valid)

  val idle :: buzy :: Nil = Enum(2)
  val state = RegInit(idle)
  val over = Wire(Bool())
  val is_idle = state === idle
  val is_buzy = state === buzy
  val idle_mux = Mux(io.data_out_ready, buzy, idle)
  val buzy_mux = Mux(
    over,
    idle,
    buzy
  )
  state := Mux(is_idle, idle_mux, buzy_mux)


  val stc_vcache :: stc_getv :: stc_waitctx :: stc_c :: Nil = Enum(4)
  val st_state = RegInit(stc_vcache)
  val is_vcache = st_state === stc_vcache
  val is_getv = st_state === stc_getv
  val is_waitctx = st_state === stc_waitctx
  val is_c = st_state === stc_c
  // Decode consumes V and ctx as a paired batch. Letting V advance when ctx
  // has not produced a bank yet causes the V side to get one batch ahead.
  val decodePairReady = io.data_in_v_ready && io.data_in_ctx_ready
  val vIssue = is_vcache && is_buzy && Mux(prefill, io.data_in_v_ready, decodePairReady)
  val ctxIssue = is_waitctx && io.data_in_ctx_ready

  val prefill_load_cnt = Wire(UInt(log2Up(MAX_PREFILL).W))
  val prefill_load_last = prefill_load_cnt === seqlen
  prefill_load_cnt := RegEnable(
    Mux(
      prefill_load_last,
      0.U,
      prefill_load_cnt + 1.U
    ),
    0.U,
    prefill && vIssue
  )

  val gev_cnt = Wire(UInt(log2Up(MAX_SEQLEN).W))
  val gev_last = gev_cnt === seqlen
  gev_cnt := RegEnable(
    Mux(
      gev_last,
      0.U,
      gev_cnt + 1.U
    ),
    0.U,
    is_getv
  )

  val waitctx_cnt = Wire(UInt(log2Up(MAX_PREFILL).W))
  val waitctx_last = waitctx_cnt === seqlen
  waitctx_cnt := RegEnable(
    Mux(
      waitctx_last,
      0.U,
      waitctx_cnt + 1.U
    ),
    0.U,
    prefill && ctxIssue
  )

  val mul_cnt = Wire(UInt(log2Up(HEAD_VECNUM).W))
  val mul_last = mul_cnt === (HEAD_VECNUM - 1).U
  mul_cnt := RegEnable(
    Mux(
      mul_last,
      0.U,
      mul_cnt + 1.U
    ),
    0.U,
    is_c
  )

  val batch_cnt = Wire(UInt(log2Up(BATCHSIZE).W))
  val batch_last = batch_cnt === Mux(singleQuery, 0.U(batch_cnt.getWidth.W), (BATCHSIZE - 1).U(batch_cnt.getWidth.W))
  batch_cnt := RegEnable(
    Mux(
      batch_last,
      0.U,
      batch_cnt + 1.U
    ),
    0.U,
    is_c && mul_last && !prefill
  )


  val stc_vcache_mux = Mux(
    prefill,
    Mux(
      prefill_load_last && vIssue,
      stc_waitctx,
      stc_vcache
    ),
    Mux(
      vIssue,
      stc_getv,
      stc_vcache
    )
  )
  val stc_getv_mux = Mux(
    gev_last,
    stc_waitctx,
    stc_getv
  )
  val stc_waitctx_mux = Mux(ctxIssue, stc_c, stc_waitctx)

  val stc_c_mux = Mux(
    mul_last,
    Mux(
      waitctx_cnt === 0.U,
      // After one decode batch finishes, restart from the explicit V-load
      // state. Jumping through stc_vcache_mux uses the current-cycle busy/valid
      // inputs and can skip the next token's V fetch altogether.
      stc_vcache,
      stc_waitctx
    ),
    stc_c
  )

  st_state := MuxLookup(
    st_state,
    st_state
  )(
    List(
      stc_vcache -> stc_vcache_mux,
      stc_getv -> stc_getv_mux,
      stc_waitctx -> stc_waitctx_mux,
      stc_c -> stc_c_mux
    )
  )

  over := mul_last && waitctx_cnt === 0.U && is_c &&(prefill || !prefill && batch_last)

  io.data_in_v_en := vIssue
  io.data_in_v_addr := Mux(prefill,prefill_load_cnt ,batch_cnt)
  io.data_in_v_last := vIssue
  io.data_out_v := io.data_in_v
  io.data_out_v_valid := RegNext(vIssue,false.B)

  io.data_in_ctx_en := ctxIssue
  io.data_in_ctx_addr := Mux(prefill,waitctx_cnt ,batch_cnt)
  io.data_in_ctx_last := ctxIssue
  io.data_out_ctx := io.data_in_ctx
  io.data_out_ctx_valid := RegNext(ctxIssue,false.B)

  io.data_out_start := RegNext(vIssue && prefill_load_cnt === 0.U, false.B)


}
