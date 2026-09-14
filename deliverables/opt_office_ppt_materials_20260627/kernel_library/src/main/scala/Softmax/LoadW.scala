package Softmax

import Param._
import chisel3._
import chisel3.util._

class LoadWeight extends Module {
  val io = IO(new Bundle() {
    val cfg_seqlen = Input(UInt(log2Up(SEQ_LEN).W))
    val cfg_prefill = Input(Bool())
    val cfg_valid = Input(Bool())
    val cfg_single_query = Input(Bool())

    val st = Input(Bool())

    val data_in = Input(UInt(WMEM_WIDTH.W))
    val data_in_addr = Output(UInt(log2Up(WMEM_DEPTH).W))
    // val data_in_last = Output(Bool())
    // val data_in_ready = Input(Bool())

    val data_out = Output(UInt(WMEM_WIDTH.W))
    val data_out_valid = Output(Bool())

    // val data_out_ready = Input(Bool()) // 如果数据可以输出，需要一直保持有效
    val data_out_start = Output(Bool())
  })

    val seqlen = RegEnable(io.cfg_seqlen, io.cfg_valid)
    val is_prefill = RegEnable(io.cfg_prefill, io.cfg_valid)
    val is_single_query = RegEnable(io.cfg_single_query, false.B, io.cfg_valid)

    // decode阶段，最大为32
    val decode_batchsize_cnt = Wire(UInt(log2Up(BATCHSIZE).W))
    val decode_batchsize_last = decode_batchsize_cnt === Mux(is_single_query, 0.U(decode_batchsize_cnt.getWidth.W), (BATCHSIZE - 1).U(decode_batchsize_cnt.getWidth.W))

    // prefill阶段，最大为26
    val prefill_batchsize_cnt = Wire(UInt(log2Up(SEQ_LEN).W))
    val prefill_batchsize_last = prefill_batchsize_cnt === (SEQ_LEN - 1).U

    val idle :: busy :: Nil = Enum(2)
    val state = RegInit(idle)
    val is_idle = state === idle
    val is_busy = state === busy
    val idle_mux = Mux(
        io.st,
        // io.data_in_ready && io.data_out_ready,
        busy,
        idle
    )
    val busy_mux = Mux(
        decode_batchsize_last || prefill_batchsize_last,
        idle,
        busy
    )
    state := Mux(is_idle, idle_mux, busy_mux)


    // decode: [B,1,N] -> [B, N] 一层循环 
    // 一次取N个token，所以取B次
    // for 0 to BATCHSIZE
    decode_batchsize_cnt:= RegEnable(
        Mux(
        decode_batchsize_last,
        0.U,
        decode_batchsize_cnt + 1.U
        ),
        0.U,
        is_busy && !is_prefill
    )

    // prefill: [N,N] 一层循环 
    // 一次取出N个token，所以取N次
    // for 0 to SEQ_LEN:
    prefill_batchsize_cnt := RegEnable(
        Mux(
        prefill_batchsize_last,
        0.U,
        prefill_batchsize_cnt + 1.U
        ),
        0.U,
        is_busy && is_prefill
    )

    io.data_in_addr := Mux(
      is_prefill,
      prefill_batchsize_cnt,
      Mux(is_single_query, seqlen, decode_batchsize_cnt)
    )

    io.data_out := io.data_in
    io.data_out_valid := RegNext(is_busy, false.B)

    
    val state_next = RegNext(state, idle)
    io.data_out_start := is_busy && state_next === idle
}

object LoadWGen extends App {
  emitVerilog(new LoadWeight, Array("--target-dir", "generated"))
}
