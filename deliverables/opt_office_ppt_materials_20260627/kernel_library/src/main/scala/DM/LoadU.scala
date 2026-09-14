package DM

import DM.Param._
import chisel3._
import chisel3.util._

//   ┌─────────────┐         ┌─────────────┐         ┌─────────────┐
//   │  外部内存    │ ──────► │   LoadUnit     │ ──────► │    DM       │
//   │             │ data_in │  (地址生成)  │ data_out│  (计算单元)  │
//   │             │ ◄────── │             │         │             │
//   │             │  addr   │             │         │             │
//   └─────────────┘         └─────────────┘         └─────────────┘
// 负责生成地址，从MEM中读取数据, 并将数据传递给下游DM
class LoadUnit extends Module {
  val io = IO(new Bundle() {
    val cfg_prelen = Input(UInt(log2Up(MAX_PREFILL).W))
    val cfg_prefill = Input(Bool())
    val cfg_valid = Input(Bool())
    val cfg_single_query = Input(Bool())
    val launch = Input(Bool())

    // 与外部MEM的接口
    val data_in = Input(UInt((2*LOAD_VECNUM*DATAW).W)) // 输入数据
    val data_in_addr = Output(UInt(log2Up(BATCHSIZE*HEAD_VECNUM/LOAD_VECNUM).W)) // 请求地址
    val data_in_last = Output(Bool()) // 最后一个数据标志
    val data_in_ready = Input(Bool()) // 外部内存准备好

    // 与下游DM的接口
    val data_out = Output(UInt((2*LOAD_VECNUM*DATAW).W)) // 输出数据
    val data_out_valid = Output(Bool()) // 输出数据有效标志
    val data_out_ready = Input(Bool()) // 下游DM准备好
    val data_out_start = Output(Bool()) // 输出数据开始标志
  })
  val is_prefill = false.B
  val is_single_query = true.B
  val prelen = RegEnable(io.cfg_prelen , io.cfg_valid) // prefill 模式下的 token 数


  val idle :: buzy :: Nil = Enum(2)
  val state = RegInit(idle)
  val load_over = Wire(Bool())
  val is_idle = state === idle
  val is_buzy = state === buzy
  val launchPending = RegInit(false.B)
  val launchReq = io.launch || launchPending
  val start = is_idle && launchReq && io.data_in_ready && io.data_out_ready
  val idle_mux = Mux(
    start,
    buzy,
    idle
  )
  val buzy_mux = Mux(
    load_over,
    idle,
    buzy
  )
  state := Mux(is_idle, idle_mux, buzy_mux)

  when(io.cfg_valid) {
    launchPending := false.B
  }.elsewhen(start) {
    launchPending := false.B
  }.elsewhen(io.launch) {
    launchPending := true.B
  }


  // Decode 模式
  // vector_cnt: 0→1→2→...→51 (52次)
  // batch_cnt:  0→1→2→...→31 (32次，对应32个batch)

  // Prefill 模式
  // vector_cnt: 0→1→2→...→31 (32次，收集一个64维向量)
  // batch_cnt:  0→1→2→...→7  (8次，对应8个token)


  //  vector_decode_plus 的两个候选项

  //   val vector_decode_plus = math.max(vector_num, MAX_SEQLEN*HEAD_VECNUM/MULNUM)
  //   ┌──────────────────────────────────────┬─────┬─────────────────────────────────────────────────────────────────────────────┐
  //   │                候选项                │ 值  │                                    含义                                     │
  //   ├──────────────────────────────────────┼─────┼─────────────────────────────────────────────────────────────────────────────┤
  //   │ vector_num = HEAD_VECNUM/LOAD_VECNUM │ 32  │ 加载一个 64 维向量需要的周期数（每周期加载 2 个元素）                       │
  //   ├──────────────────────────────────────┼─────┼─────────────────────────────────────────────────────────────────────────────┤
  //   │ MAX_SEQLEN*HEAD_VECNUM/MULNUM        │ 52  │ DM 计算一个 Q 与所有 K 点积需要的周期数：26 个 K × 64 维 ÷ 32 个乘法器 = 52 │
  //   └──────────────────────────────────────┴─────┴─────────────────────────────────────────────────────────────────────────────┘
  //   Prefill 模式：vector_cnt 循环到 vector_num - 1 = 31
  //   - 每收集完一个 64 维向量（32 周期），就递增 batch_cnt（对应不同 token）
  //   - DM 会等所有 token 的 QK 收集完才开始计算
  //   Decode 模式：vector_cnt 循环到 vector_decode_plus - 1 = 51
  //   - 虽然只需要 32 周期收集向量，但要多等 20 周期
  //   - 这 20 周期是给 DM 计算 Q·K 点积的时间（一个 Q 要和 26 个历史 K 做点积）

  // 向量内元素计数器
  val vector_num = HEAD_VECNUM/LOAD_VECNUM // 64/2=32
  val vector_decode_plus = math.max(vector_num, MAX_SEQLEN*HEAD_VECNUM/MULNUM)
  // In single-query mode we still need to leave enough idle cycles for DM1's
  // Q·K accumulation to finish before launching the next head. A fixed 32-cycle
  // window works for short histories, but once seqlen grows (e.g. token31),
  // the compute path needs roughly 2 * (seqlen + 1) cycles and every other
  // head gets dropped. Keep the window dynamic while staying minimal.
  // DM1 result valid trails the pure MAC loop by several pipeline stages
  // (multiplier/add-tree/accumulate/fp conversion). Without a small guard,
  // token31 is the first case where the next single-query batch restarts just
  // early enough to clobber every other head.
  val decode_pipeline_guard = (1 + 2 + log2Up(MULNUM) + 1).U(vector_decode_plus.W)
  val decode_compute_cycles = (prelen + 1.U) * (HEAD_VECNUM / MULNUM).U + decode_pipeline_guard
  val single_query_vector_limit = Mux(
    decode_compute_cycles > vector_num.U(vector_decode_plus.W),
    decode_compute_cycles - 1.U,
    (vector_num - 1).U(vector_decode_plus.W)
  )
  val decode_vector_limit = Mux(
    is_single_query,
    single_query_vector_limit,
    (vector_decode_plus - 1).U
  )
  // 为什么在 vector_cnt 层空转：因为 Decode 模式下，每个 batch 只有一个 Q，LoadUnit 发完 32 周期数据后，需要等 DM 完成计算才能处理下一个 batch。
  val vector_cnt = RegInit(0.U(log2Up(vector_decode_plus).W))
  val dataWindowActive = Wire(Bool())
  val loadStep = Wire(Bool())
  val waitStep = Wire(Bool())
  val vectorStep = Wire(Bool())
  val vector_last =vector_cnt ===  Mux(is_prefill, 
      (vector_num - 1).U , // prefill 32
      decode_vector_limit
    )
  when(vectorStep) {
    vector_cnt := Mux(vector_last, 0.U, vector_cnt + 1.U)
  }

  //  batch_prefill_plus 的两个候选项
  //   val batch_prefill_plus = math.max(LOCAL_PREFILL, LOCAL_PREFILL*LOCAL_PREFILL*LOAD_VECNUM/MULNUM)
  //   ┌────────────────────────────────────────────┬─────┬───────────────────────────────────────────────────────────────────────┐
  //   │                   候选项                   │ 值  │                                 含义                                  │
  //   ├────────────────────────────────────────────┼─────┼───────────────────────────────────────────────────────────────────────┤
  //   │ LOCAL_PREFILL                              │ 26  │ 本地 prefill 窗口上限（保持原始固定规模）                              │
  //   ├────────────────────────────────────────────┼─────┼───────────────────────────────────────────────────────────────────────┤
  //   │ LOCAL_PREFILL*LOCAL_PREFILL*LOAD_VECNUM/MULNUM │ 42 │ 26-token 局部窗口下 DM1 计算所需的额外时间                              │
  //   └────────────────────────────────────────────┴─────┴───────────────────────────────────────────────────────────────────────┘
  //   Prefill 模式：batch_cnt 循环到 batch_prefill_plus - 1 = 7
  //   - 对应 8 个 token（seqlen=0~7）
  //   Decode 模式：batch_cnt 循环到 BATCHSIZE - 1 = 31
  //   - 对应 32 个 batch

  val batch_prefill_plus = math.max(LOCAL_PREFILL, LOCAL_PREFILL*LOCAL_PREFILL*LOAD_VECNUM/MULNUM)
  val batch_cnt = RegInit(0.U(log2Up(math.max(BATCHSIZE, batch_prefill_plus)).W))
  val decode_batch_last = Mux(is_single_query, 0.U(batch_cnt.getWidth.W), (BATCHSIZE - 1).U(batch_cnt.getWidth.W))
  val batch_cnt_last = batch_cnt === Mux(is_prefill,
      (batch_prefill_plus -1).U , // prefill
      decode_batch_last           // decode
    )
  dataWindowActive := is_prefill && batch_cnt <= prelen || !is_prefill && vector_cnt < vector_num.U
  loadStep := is_buzy && dataWindowActive && io.data_in_ready && io.data_out_ready
  waitStep := is_buzy && !dataWindowActive
  vectorStep := loadStep || waitStep
  when(vectorStep && vector_last) {
    batch_cnt := Mux(batch_cnt_last, 0.U, batch_cnt + 1.U)
  }

  load_over := is_buzy && vector_last && batch_cnt_last

  io.data_in_addr := batch_cnt * vector_num.U + vector_cnt
  io.data_in_last := is_buzy && vector_last && batch_cnt_last


  io.data_out := io.data_in
  // 
  io.data_out_valid := RegNext(loadStep,
      false.B)
  io.data_out_start := is_buzy && vector_cnt === 0.U && batch_cnt === 0.U
}
