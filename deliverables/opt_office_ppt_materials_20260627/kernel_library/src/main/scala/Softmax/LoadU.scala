// for 0 to 768 / 12
//  for 0 to 32

package Softmax

import chisel3._
import chisel3.util._
import Param._

class LoadUnit extends Module {
  val io = IO(new Bundle() {
    val cfg_seqlen = Input(UInt(log2Up(SEQ_LEN).W))
    val cfg_prefill = Input(Bool())
    val cfg_valid = Input(Bool())
    
    // QKT 输入
    val data_in = Input(UInt(MEM_WIDTH.W))
    val data_in_addr = Output(UInt(log2Up(MEM_DEPTH).W))
    val data_in_last = Output(Bool())
    val data_in_ready = Input(Bool())

    // QKT 输出
    val data_out = Output(UInt(MEM_WIDTH.W))
    val data_out_valid = Output(Bool())

    val data_out_ready = Input(Bool()) // 如果数据可以输出，需要一直保持有效
    val data_out_start = Output(Bool())
  })

  val seqlen = Mux(io.cfg_valid, io.cfg_seqlen, SEQ_LEN.U)
  val is_prefill = Mux(io.cfg_valid, io.cfg_prefill, false.B)
  // decode阶段，最大为32
  val decode_batchsize_cnt = Wire(UInt(log2Up(BATCHSIZE).W))
  val decode_batchsize_last = decode_batchsize_cnt === (BATCHSIZE - 1).U

 // prefill阶段，最大为26
  val prefill_batchsize_cnt = Wire(UInt(log2Up(SEQ_LEN).W))
  val prefill_batchsize_last = prefill_batchsize_cnt === (SEQ_LEN - 1).U

  val idle :: busy :: Nil = Enum(2)
  val state = RegInit(idle)
  val is_idle = state === idle
  val is_busy = state === busy
  val idle_mux = Mux(
    io.data_in_ready && io.data_out_ready,
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


  io.data_in_addr := Mux(is_prefill, prefill_batchsize_cnt, decode_batchsize_cnt)
  io.data_in_last := (is_prefill && prefill_batchsize_last) || (!is_prefill && decode_batchsize_last)

  io.data_out := io.data_in
  io.data_out_valid := RegNext(is_busy, false.B)

  
  val state_next = RegNext(state, idle)
  io.data_out_start := is_busy && state_next === idle

//  printf(p"""[LoadUnit]
//            seqlen = ${seqlen},
//            is_prefill = ${is_prefill},
//            is_busy = ${is_busy},
//            is_idle = ${is_idle},
//            data_in_ready = ${io.data_in_ready},
//            data_out_ready = ${io.data_out_ready},
//            data_out_start = ${io.data_out_start},
//            data_in_last = ${io.data_in_last}
//            prefill_batchsize_cnt = ${prefill_batchsize_cnt},
//            decode_batchsize_cnt  = ${decode_batchsize_cnt},
//            decode_batchsize_last = ${decode_batchsize_last},
//            prefill_batchsize_last = ${prefill_batchsize_last}
//            state = ${state}
//            state_next = ${state_next}
//          \n""")
}   
