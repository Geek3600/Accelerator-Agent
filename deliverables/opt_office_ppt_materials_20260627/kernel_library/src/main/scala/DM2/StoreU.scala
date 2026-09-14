package DM2

import DM2.Param._
import chisel3._
import chisel3.util._
class StoreUnit extends Module{
  val io = IO(new Bundle() {
    val cfg_seqlen = Input(UInt(log2Up(TILE_SEQLEN).W))
    val cfg_prefill = Input(Bool()) //prefill 长度减去1
    val cfg_valid = Input(Bool())
    val cfg_single_query = Input(Bool())

    val data_in = Input(UInt((HEAD_VECNUM * DATAW).W))
    val data_in_valid = Input(Bool())

    val data_out = Output(UInt((HEAD_VECNUM * DATAW).W))
    val data_out_addr = Output(UInt(log2Up(MEM_DEPTH).W))
    val data_out_valid = Output(Bool())
    val data_out_last = Output(Bool())
  })

  val prefill = false.B
  val singleQuery = true.B
  val seqlen = RegEnable(io.cfg_seqlen, io.cfg_valid)

  val prefill_cnt = RegInit(0.U(log2Up(TILE_SEQLEN).W))
  val prefill_last = prefill_cnt === seqlen
  when(prefill && io.data_in_valid) {
    prefill_cnt := Mux(prefill_last, 0.U, prefill_cnt + 1.U)
  }

  val batch_cnt = RegInit(0.U(log2Up(BATCHSIZE).W))
  // single_query decode: 每次 DM2 处理一个 head，需要循环 SINGLE_QUERY_BATCH=12 次才结束
  // 旧逻辑 singleQuery ? 0 : BATCHSIZE-1 错误地让第1个 beat 就 last，导致 DM2 只输出1个 head
  val batch_last = batch_cnt === Mux(singleQuery, (SINGLE_QUERY_BATCH - 1).U(batch_cnt.getWidth.W), (BATCHSIZE - 1).U(batch_cnt.getWidth.W))
  when(!prefill && io.data_in_valid) {
    batch_cnt := Mux(batch_last, 0.U, batch_cnt + 1.U)
  }

  io.data_out := io.data_in
  io.data_out_addr := Mux(prefill,prefill_cnt ,batch_cnt)
  io.data_out_valid := io.data_in_valid
  io.data_out_last := (prefill && prefill_last || !prefill && batch_last) && io.data_in_valid




}
