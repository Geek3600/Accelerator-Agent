package ResMEM

import ResMEM.Param._
import chisel3._
import chisel3.util._


//ResMem的作用：将Load0每周期输入的2个V元素，收集拼接成完整的64维向量后输出给DM2

// LSU的作用：负责生成地址，从DataMem读取数据，并输出
// 本质上是一个LoadU
class LSU extends Module {
  private val LocalDepth = LOCAL_PRELEN * DATAOUTNUM / DATAINNUM
  val io = IO(new Bundle() {
    val cfg_seqlen = Input(UInt(log2Up(LOCAL_PRELEN).W))
    val cfg_prefill = Input(Bool())
    val cfg_valid = Input(Bool())
    val cfg_single_query = Input(Bool())

    val data_in = Input(UInt((DATAINW).W))
    val data_in_addr = Output(UInt(log2Up(LocalDepth).W))
    val data_in_last = Output(Bool())
    val data_in_en = Output(Bool())
    val data_in_ready = Input(Bool())

    val data_out = Output(UInt((DATAOUTW).W))
    val data_out_valid = Output(Bool())
    val data_out_ready = Input(Bool()) // 下一级传回的数据接收信号，表示是否准备好接收数据
    val data_out_start = Output(Bool())

    val data_out_last = Output(Bool())
    val data_out_addr = Output(UInt(log2Up(BATCHSIZE).W))
  })

  val prefill = false.B
  val singleQuery = true.B
  val seqlen = RegEnable(io.cfg_seqlen,io.cfg_valid)

  // 状态机：
  // idle → buzy (当读侧可启动且下游可接收)
  // buzy 在收满 64-dim 向量后进入 hold，直到下游真正消费该输出
  // hold → idle/buzy (按是否已完成全部 batch 决定)
  val idle :: buzy :: hold :: Nil = Enum(3)
  val state = RegInit(idle)
  val load_over = Wire(Bool())
  val output_fire = Wire(Bool())
  val is_idle = state === idle
  val is_buzy = state === buzy
  val is_hold = state === hold
  output_fire := is_hold && io.data_out_ready
  load_over := false.B

  if(DATAOUTNUM > DATAINNUM) {
    val CATNUM = DATAOUTNUM/DATAINNUM // = 64/2 = 32，收集32次两个V元素，拼接成64维向量
    val v_cnt = RegInit(0.U(log2Up(CATNUM).W))
    val v_last =( CATNUM-1).U === v_cnt
    val read_step = is_buzy && io.data_in_ready
    val read_step_d1 = RegNext(read_step, false.B)
    val read_idx_d1 = RegEnable(v_cnt, 0.U, read_step)
    // 内层循环
    when(read_step) {
      v_cnt := Mux(v_last, 0.U, v_cnt + 1.U)
    }

    // prefill阶段外层循环
  val prefill_cnt = RegInit(0.U(log2Up(LOCAL_PRELEN).W))
    val prefill_last = prefill_cnt === seqlen
    when(read_step && v_last && prefill) {
      prefill_cnt := Mux(prefill_last, 0.U, prefill_cnt + 1.U)
    }

    //decode阶段的外层循环
    val batch_cnt = RegInit(0.U(log2Up(BATCHSIZE).W))
    // single_query decode: 需要输出 SINGLE_QUERY_BATCH=12 个 head 的 V
    // 旧逻辑 singleQuery ? 0 : BATCHSIZE-1 错误，只输出1个 head 就认为完成了
    val batch_last = batch_cnt === Mux(singleQuery, (SINGLE_QUERY_BATCH - 1).U(batch_cnt.getWidth.W), (BATCHSIZE -1 ).U(batch_cnt.getWidth.W))
    when(read_step && v_last && !prefill) {
      batch_cnt := Mux(batch_last, 0.U, batch_cnt + 1.U)
    }

    // 所有数据都已经加载完
    val load_over_req = read_step && v_last && (prefill && prefill_last || batch_last && !prefill)
    val pack_done = RegNext(read_step && v_last, false.B)
    val load_over_d1 = RegNext(load_over_req, false.B)
    val out_addr_req = RegEnable(Mux(prefill, prefill_cnt, batch_cnt), 0.U, read_step && v_last)
    val out_start_req = RegEnable(is_idle, false.B, read_step && v_last)
    load_over := load_over_d1

    state := MuxLookup(state, state)(
      Seq(
        idle -> Mux(io.data_in_ready && io.data_out_ready, buzy, idle),
        buzy -> Mux(pack_done, hold, buzy),
        // Insert an idle bubble between vectors so DataMem full/r_ptr updates settle
        // before issuing the next bank's addr=0 read. The old direct hold->buzy path
        // could speculate into the next bank early and replay the previous head's
        // first 2-lane slice at each new head boundary.
        hold -> Mux(output_fire, idle, hold)
      )
    )

    // 生成地址
    io.data_in_addr := v_cnt + Mux(prefill, prefill_cnt, batch_cnt) *(CATNUM).U
    // Release / rotate the backing bank on the final read request itself, just
    // like the stable DM LoadU implementation. Delaying `r_last` by one cycle
    // leaves the bank handoff one beat late and can replay the previous head's
    // addr0 slice into the next head.
    io.data_in_last := read_step && v_last
    io.data_in_en := read_step

    // rescache负责收集从DataMem读取的数据
    val rescache = RegInit(VecInit(Seq.fill(CATNUM)(0.U(DATAINW.W))))
    val rescacheNext = WireDefault(rescache)
    when(read_step_d1) {
      rescacheNext(read_idx_d1) := io.data_in
    }
    rescache := rescacheNext

    val out_data = RegEnable(rescacheNext.asUInt, pack_done)
    val out_last = RegEnable(load_over_d1, false.B, pack_done)
    val out_addr = RegEnable(out_addr_req, 0.U, pack_done)
    val out_start = RegEnable(out_start_req, false.B, pack_done)

    io.data_out := out_data
    io.data_out_valid := is_hold
    io.data_out_start := out_start && is_hold
    io.data_out_last := out_last
    io.data_out_addr := out_addr
  } else{
    val SLICENUM = DATAINNUM / DATAOUTNUM
    state := idle
    io.data_in_addr := 0.U
    io.data_in_last := false.B
    io.data_in_en := false.B
    io.data_out := 0.U
    io.data_out_valid := false.B
    io.data_out_start := false.B
    io.data_out_last := false.B
    io.data_out_addr := 0.U
  }
}
