package Softmax

import Param._
import chisel3._
import chisel3.util._

class SoftmaxPip extends Module {
// 流水级4: Softmax - 对注意力分数进行softmax归一化
  val io = IO (new Bundle() {
    val cfg_seqlen = Input(UInt(log2Up(SEQ_LEN).W))
    val cfg_prefill = Input(Bool())
    val cfg_valid = Input(Bool())

    val layer_st = Input(Bool())
    val data_in_st = Input(Bool())
    val data_in = Input(UInt(MEM_WIDTH.W))
    val data_addr = Input(UInt(log2Up(MEM_DEPTH).W))
    val data_valid = Input(Bool())
    val data_last = Input(Bool())
    val data_ready= Output(Bool())

    val w_in = Input(UInt(WMEM_WIDTH.W))
    val w_addr = Output(UInt(log2Up(WMEM_DEPTH).W))
    
    val res = Output(UInt(MEM_WIDTH.W))
    val res_st = Output(Bool())
    val res_addr = Output(UInt(log2Up(MEM_DEPTH).W))
    val res_valid = Output(Bool())
    val res_last = Output(Bool())
    val res_ready = Input(Bool())
  })

  val mem_inst = Module(new DataMem(MEM_DEPTH, MEM_WIDTH))
  val lu_inst = Module(new LoadUnit)
  val lw_inst = Module(new LoadWeight)
  val cu_inst = Module(new CU)
  val su_inst = Module(new StoreUnit)

  mem_inst.io.w_st:= io.data_in_st
  mem_inst.io.w_last := io.data_last
  mem_inst.io.w_data := io.data_in
  mem_inst.io.w_addr := io.data_addr
  mem_inst.io.w_valid := io.data_valid
  mem_inst.io.r_last := lu_inst.io.data_in_last
  mem_inst.io.r_addr := lu_inst.io.data_in_addr

  lu_inst.io.cfg_seqlen := io.cfg_seqlen
  lu_inst.io.cfg_prefill := io.cfg_prefill
  lu_inst.io.cfg_valid := io.cfg_valid
  lu_inst.io.data_in := mem_inst.io.r_data
  lu_inst.io.data_in_ready := mem_inst.io.r_ready
  lu_inst.io.data_out_ready := io.res_ready

  cu_inst.io.data_in := lu_inst.io.data_out
  cu_inst.io.data_in_valid := lu_inst.io.data_out_valid
  cu_inst.io.data_in_w := lw_inst.io.data_out
  cu_inst.io.data_in_w_valid := lw_inst.io.data_out_valid

  su_inst.io.cfg_seqlen := io.cfg_seqlen
  su_inst.io.cfg_prefill := io.cfg_prefill
  su_inst.io.cfg_valid := io.cfg_valid
  su_inst.io.data_in := cu_inst.io.data_out
  su_inst.io.data_in_valid := cu_inst.io.data_out_valid

  lw_inst.io.cfg_seqlen := io.cfg_seqlen
  lw_inst.io.cfg_prefill := io.cfg_prefill
  lw_inst.io.cfg_valid := io.cfg_valid
  lw_inst.io.data_in := io.w_in
  lw_inst.io.st := io.layer_st
  
  io.data_ready := mem_inst.io.w_ready
  io.w_addr := lw_inst.io.data_in_addr

  io.res := su_inst.io.data_out
  io.res_st := lu_inst.io.data_out_start
  io.res_addr := su_inst.io.data_out_addr
  io.res_valid := su_inst.io.data_out_valid
  io.res_last := su_inst.io.data_out_last
}
object SoftmaxPipGen extends App {
  emitVerilog(new SoftmaxPip, Array("--target-dir", "generated"))
}