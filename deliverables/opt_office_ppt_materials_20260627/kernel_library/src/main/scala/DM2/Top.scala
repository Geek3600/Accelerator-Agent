package DM2

import DM2.Param._
import chisel3._
import chisel3.util._
class DM2 extends Module {
// 流水级6: DM2 - 计算 Softmax(Q·K)·V
  val io = IO(new Bundle() {
    val cfg_seqlen = Input(UInt(log2Up(MAX_SEQLEN).W))
    val cfg_prefill = Input(Bool())
    val cfg_valid = Input(Bool())

    val data_in_v_st = Input(Bool())
    val data_in_v = Input(UInt((HEAD_VECNUM * DATAW).W))
    val data_in_v_addr = Input(UInt(log2Up(MEM_DEPTH).W))
    val data_in_v_valid = Input(Bool())
    val data_in_v_last = Input(Bool())
    val data_in_v_ready = Output(Bool())

    val data_in_ctx_st = Input(Bool())
    val data_in_ctx = Input(UInt((MAX_SEQLEN * DATAW).W))
    val data_in_ctx_addr = Input(UInt(log2Up(MEM_DEPTH).W))
    val data_in_ctx_valid = Input(Bool())
    val data_in_ctx_last = Input(Bool())
    val data_in_ctx_ready = Output(Bool())

    val res = Output(UInt((HEAD_VECNUM*DATAW).W))
    val res_st = Output(Bool())
    val res_addr = Output(UInt(log2Up(BATCHSIZE).W))
    val res_valid = Output(Bool())
    val res_last = Output(Bool())
    val res_ready = Input(Bool())

  })

  val loadu_inst = Module(new LoadUnit)
  val dm_inst = Module(new DM2CU)
  val vmem_inst = Module(new DataMem(MEM_DEPTH,HEAD_VECNUM * DATAW))
  val ctxmem_inst =  Module(new DataMem(MEM_DEPTH,MAX_SEQLEN * DATAW))
  val su_inst = Module(new StoreUnit)

  vmem_inst.io.w_st := io.data_in_v_st
  vmem_inst.io.w_last := io.data_in_v_last
  vmem_inst.io.w_data := io.data_in_v
  vmem_inst.io.w_addr := io.data_in_v_addr
  vmem_inst.io.w_valid := io.data_in_v_valid

  vmem_inst.io.r_last := loadu_inst.io.data_in_v_last
  vmem_inst.io.r_addr := loadu_inst.io.data_in_v_addr

  ctxmem_inst.io.w_st := io.data_in_ctx_st
  ctxmem_inst.io.w_last := io.data_in_ctx_last
  ctxmem_inst.io.w_data := io.data_in_ctx
  ctxmem_inst.io.w_addr := io.data_in_ctx_addr
  ctxmem_inst.io.w_valid := io.data_in_ctx_valid

  ctxmem_inst.io.r_last := loadu_inst.io.data_in_v_last
  ctxmem_inst.io.r_addr := loadu_inst.io.data_in_v_addr

  loadu_inst.io.cfg_valid := io.cfg_valid
  loadu_inst.io.cfg_prefill := io.cfg_prefill
  loadu_inst.io.cfg_seqlen := io.cfg_seqlen

  loadu_inst.io.data_in_v := vmem_inst.io.r_data
  loadu_inst.io.data_in_v_ready := vmem_inst.io.r_ready
  loadu_inst.io.data_in_ctx := ctxmem_inst.io.r_data
  loadu_inst.io.data_in_ctx_ready := ctxmem_inst.io.r_ready
  loadu_inst.io.data_out_ready := io.res_ready

  dm_inst.io.cfg_seqlen := io.cfg_seqlen
  dm_inst.io.cfg_valid := io.cfg_valid
  dm_inst.io.cfg_prefill := io.cfg_prefill
  dm_inst.io.data_in_v := loadu_inst.io.data_out_v
  dm_inst.io.data_in_v_valid := loadu_inst.io.data_out_v_valid
  dm_inst.io.data_in_ctx := loadu_inst.io.data_out_ctx
  dm_inst.io.data_in_ctx_valid := loadu_inst.io.data_out_ctx_valid

  su_inst.io.cfg_seqlen := io.cfg_seqlen
  su_inst.io.cfg_valid := io.cfg_valid
  su_inst.io.cfg_prefill := io.cfg_prefill

  su_inst.io.data_in := dm_inst.io.data_out
  su_inst.io.data_in_valid := dm_inst.io.data_out_valid

  io.data_in_v_ready := vmem_inst.io.w_ready
  io.data_in_ctx_ready := ctxmem_inst.io.w_ready

  io.res := su_inst.io.data_out
  io.res_st := loadu_inst.io.data_out_start
  io.res_addr := su_inst.io.data_out_addr
  io.res_valid := su_inst.io.data_out_valid
  io.res_last := su_inst.io.data_out_last

}

object DM2Gen extends App {
  emitVerilog(new DM2, Array("--target-dir", "generated"))
}