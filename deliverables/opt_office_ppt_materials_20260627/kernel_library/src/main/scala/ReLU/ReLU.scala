package ReLU

import ReLU.Param._
import chisel3._
import chisel3.util._

// ReLU 激活函数模块
// 功能: 对 3072 维向量应用 ReLU 激活函数
// 输入: 96-bit/cycle (12 elements) from FFNUp
// 输出: 96-bit/cycle (12 elements) to FFNDown
class ReLU extends Module {
  val io = IO(new Bundle() {
    // 来自 FFNUp 的输入
    val data_in_st = Input(Bool())
    val data_in = Input(UInt(MEM_WIDTH.W))
    val data_in_addr = Input(UInt(log2Up(MEM_DEPTH).W))
    val data_in_valid = Input(Bool())
    val data_in_last = Input(Bool())
    val data_ready = Output(Bool())

    // 配置信号
    val cfg_prefill = Input(Bool())
    val cfg_seqlen = Input(UInt(log2Up(MAX_SEQLEN).W))
    val cfg_valid = Input(Bool())

    // 输出到 FFNDown
    val data_out = Output(UInt(MEM_WIDTH.W))
    val data_out_st = Output(Bool())
    val data_out_addr = Output(UInt(log2Up(MEM_DEPTH).W))
    val data_out_valid = Output(Bool())
    val data_out_last = Output(Bool())
    val data_out_ready = Input(Bool())
  })

  // 锁存配置
  val is_prefill = RegEnable(io.cfg_prefill, false.B, io.cfg_valid)
  val seqlen = RegEnable(io.cfg_seqlen, 0.U, io.cfg_valid)

  // ========================================
  // 双缓冲存储器
  // ========================================
  val mem = Module(new DataMem(MEM_DEPTH, MEM_WIDTH, 3))

  mem.io.w_st := io.data_in_st
  mem.io.w_last := io.data_in_last
  mem.io.w_data := io.data_in
  mem.io.w_addr := io.data_in_addr
  mem.io.w_valid := io.data_in_valid

  io.data_ready := mem.io.w_ready

  // ========================================
  // 激活函数计算单元
  // ========================================
  val cu = Module(new CU)

  // 状态机：idle / processing
  val idle :: processing :: Nil = Enum(2)
  val state = RegInit(idle)

  val actual_batchsize = Mux(is_prefill, seqlen, (BATCHSIZE - 1).U)
  val vecnumPerToken = DATA_DIM / VECNUM

  val batchsize_cnt = Wire(UInt(log2Up(BATCHSIZE).W))
  val vector_cnt = Wire(UInt(log2Up(vecnumPerToken + 1).W))

  val batchsize_last = batchsize_cnt === actual_batchsize
  val vector_last = vector_cnt === (vecnumPerToken - 1).U

  batchsize_cnt := RegEnable(
    Mux(batchsize_last, 0.U, batchsize_cnt + 1.U),
    0.U,
    state === processing
  )

  vector_cnt := RegEnable(
    Mux(vector_last, 0.U, vector_cnt + 1.U),
    0.U,
    state === processing && batchsize_last
  )

  switch(state) {
    is(idle) {
      when(mem.io.r_ready && io.data_out_ready) {
        state := processing
      }
    }
    is(processing) {
      when(vector_last && batchsize_last) {
        when(mem.io.r_ready && io.data_out_ready) {
          state := processing
        }.otherwise {
          state := idle
        }
      }
    }
  }

  val read_addr = batchsize_cnt * vecnumPerToken.U + vector_cnt
  mem.io.r_addr := read_addr
  mem.io.r_last := state === processing && vector_last && batchsize_last

  cu.io.data_in := mem.io.r_data
  cu.io.data_in_valid := state === processing

  val out_st = state === processing && batchsize_cnt === 0.U && vector_cnt === 0.U
  val out_last = state === processing && vector_last && batchsize_last

  io.data_out := cu.io.data_out
  io.data_out_valid := cu.io.data_out_valid
  io.data_out_addr := RegNext(read_addr)
  io.data_out_st := RegNext(out_st, false.B)
  io.data_out_last := RegNext(out_last, false.B)
}

object ReLUGen extends App {
  emitVerilog(new ReLU, Array("--target-dir", "generated"))
}
