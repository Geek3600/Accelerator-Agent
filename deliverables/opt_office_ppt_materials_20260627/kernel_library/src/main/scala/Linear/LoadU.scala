package Linear
import Linear.Param._
import chisel3._
import chisel3.util._

class LoadUnit extends Module {
  val io = IO(new Bundle() {
    val data_in = Input(UInt(MEM_WIDTH.W))
    val data_in_addr = Output(UInt(log2Up(MEM_DEPTH).W))
    val data_in_last = Output(Bool())
    val data_in_ready = Input(Bool())

    val data_out = Output(UInt(MEM_WIDTH.W))
    val data_out_valid = Output(Bool())
    val data_out_ready = Input(Bool())
    val data_out_start = Output(Bool())

    // Prefill/Decode 模式配置
    val cfg_prefill = Input(Bool())
    val cfg_seqlen = Input(UInt(log2Up(MAX_SEQLEN).W))
    val cfg_valid = Input(Bool())
  })

  // 锁存配置
  val is_prefill = RegEnable(io.cfg_prefill, false.B, io.cfg_valid)
  val seqlen = RegEnable(io.cfg_seqlen, 0.U, io.cfg_valid)

  // 计算实际批次数：Prefill模式用seqlen，Decode模式用BATCHSIZE
  val actual_batchsize = Mux(is_prefill, seqlen, (BATCHSIZE - 1).U)
  val batchsize_cnt = Wire(UInt(log2Up(BATCHSIZE).W))
  val batchsize_last = batchsize_cnt === actual_batchsize
  val vector_num = ROWBLOCK
  val vector_cnt = Wire(UInt(log2Up(vector_num).W))
  val vector_last = vector_cnt === (vector_num - 1).U
  val block_cnt = Wire(UInt(log2Up(COLBLOCK).W))
  val block_last = block_cnt === (COLBLOCK - 1).U

  val idle :: buzy :: Nil = Enum(2)
  val state = RegInit(idle)
  val is_idle = state === idle
  val is_buzy = state === buzy
  val idle_mux = Mux(
    io.data_in_ready && io.data_out_ready,
    buzy,
    idle
  )
  val buzy_mux = Mux(
    vector_last && batchsize_last&&block_last,
    idle,
    buzy
  )
  state := Mux(is_idle,idle_mux,buzy_mux)

  batchsize_cnt:= RegEnable(
    Mux(
      batchsize_last,
      0.U,
      batchsize_cnt + 1.U
    ),
    0.U,
    is_buzy
  )

  vector_cnt := RegEnable(
    Mux(
      vector_last,
      0.U,
      vector_cnt + 1.U
    ),
    0.U,
    is_buzy && batchsize_last
  )

  block_cnt := RegEnable(
    Mux(
      block_last,
      0.U,
      block_cnt + 1.U
    ),
    0.U,
    is_buzy && batchsize_last && vector_last
  )

  val addr = vector_cnt + batchsize_cnt*vector_num.U
  io.data_in_addr := addr
  io.data_in_last := batchsize_last && vector_last && block_last

  io.data_out := io.data_in
  io.data_out_valid := RegNext(is_buzy,false.B)

  val state_next = RegNext(state,idle)
  io.data_out_start := is_buzy && state_next === idle

}
    

