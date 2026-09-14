package OutLinear

import OutLinear.Param._
import chisel3._
import chisel3.util._

class StoreUnit extends Module {
  val io = IO(new Bundle() {
    val data_in = Input(UInt(MEM_WIDTH.W))
    val data_in_valid = Input(Bool())

    val data_out = Output(UInt(MEM_WIDTH.W))
    val data_out_addr = Output(UInt(log2Up(MEM_DEPTH).W))
    val data_out_valid = Output(Bool())
    val data_out_last = Output(Bool())
    val data_out_st = Output(Bool())

    // Prefill/Decode 模式配置
    val cfg_prefill = Input(Bool())
    val cfg_seqlen = Input(UInt(log2Up(MAX_SEQLEN).W))
    val cfg_valid = Input(Bool())
  })

  // 锁存配置
  val is_prefill = RegEnable(io.cfg_prefill, false.B, io.cfg_valid)
  val seqlen = RegEnable(io.cfg_seqlen, 0.U, io.cfg_valid)

  // 计算实际批次数
  val actual_batchsize = Mux(is_prefill, seqlen, (BATCHSIZE - 1).U)

  // 输出向量数: 768 / 12 = 64 个有效向量
  val vector_valid_num = COL_W / ROW  // = 64
  // CU 输出的总向量数: COLBLOCK * (COL / ROW) = 22 * 3 = 66
  val vector_total_num = COLBLOCK * (COL / ROW)

  val batchsize_cnt = Wire(UInt(log2Up(BATCHSIZE).W))
  val vector_cnt = Wire(UInt(log2Up(vector_total_num + 1).W))

  // vector_cnt 每次 data_in_valid 时递增（遍历一个 token 的所有输出）
  val vector_last = vector_cnt === (vector_total_num - 1).U
  vector_cnt := RegEnable(
    Mux(vector_last, 0.U, vector_cnt + 1.U),
    0.U,
    io.data_in_valid
  )

  // batchsize_cnt 在 vector_last 时递增（完成一个 token 后切换到下一个）
  val batchsize_last = batchsize_cnt === actual_batchsize
  batchsize_cnt := RegEnable(
    Mux(batchsize_last, 0.U, batchsize_cnt + 1.U),
    0.U,
    io.data_in_valid && vector_last
  )

  val out_addr = batchsize_cnt * vector_valid_num.U + vector_cnt
  val out_valid = io.data_in_valid && (vector_cnt < vector_valid_num.U)

  val out_last = out_valid && batchsize_last && (vector_cnt === (vector_valid_num - 1).U)

  val out_st = out_valid && batchsize_cnt === 0.U && vector_cnt === 0.U

  io.data_out := RegNext(io.data_in)
  io.data_out_valid := RegNext(out_valid, false.B)
  io.data_out_addr := RegNext(out_addr)
  io.data_out_last := RegNext(out_last, false.B)
  io.data_out_st := RegNext(out_st, false.B)
}
