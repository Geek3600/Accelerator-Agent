package FFNDown

import FFNDown.Param._
import QuantCommon.Fp32VecAdd
import QuantCommon.Precision._
import chisel3._
import chisel3.util._

class FFNDownFP32 extends Module {
  val io = IO(new Bundle() {
    val layer_st = Input(Bool())

    val data_in_st = Input(Bool())
    val data_in = Input(UInt(MEM_WIDTH.W))
    val data_addr = Input(UInt(log2Up(MEM_DEPTH).W))
    val data_valid = Input(Bool())
    val data_last = Input(Bool())
    val data_ready = Output(Bool())

    val weight_init_mode = Input(Bool())
    val weight_init_data = Input(UInt(WMEM_WIDTH.W))
    val weight_init_addr = Output(UInt(log2Up(WMEM_DEPTH).W))
    val weight_active_bank = Input(Bool())
    val weight_preload_bank = Input(Bool())
    val weight_preload_valid = Input(Bool())
    val weight_preload_addr = Input(UInt(log2Up(WMEM_DEPTH).W))
    val weight_preload_data = Input(UInt(WMEM_WIDTH.W))
    val bias_init_data = Input(UInt(FP32_PACK_WIDTH.W))
    val bias_init_valid = Input(Bool())

    val out_scale = Input(UInt(FP32_WIDTH.W))

    val cfg_prefill = Input(Bool())
    val cfg_seqlen = Input(UInt(log2Up(MAX_SEQLEN).W))
    val cfg_valid = Input(Bool())

    val data_out = Output(UInt(FP32_PACK_WIDTH.W))
    val data_out_st = Output(Bool())
    val data_out_addr = Output(UInt(log2Up(MEM_DEPTH).W))
    val data_out_valid = Output(Bool())
    val data_out_last = Output(Bool())
    val data_out_ready = Input(Bool())
  })

  val mem_inst = Module(new DataMem(MEM_DEPTH, MEM_WIDTH))
  val lu_inst = Module(new LoadUnit)
  val cu_inst = Module(new CUFP32)
  val su_inst = Module(new StoreUnitFP32)
  val lw_inst = Module(new LoadWeight)
  val bias_mem = Reg(Vec(COL_W / ROW, UInt(FP32_PACK_WIDTH.W)))
  val bias_init_cnt = RegInit(0.U(log2Up(COL_W / ROW).W))

  when(io.bias_init_valid) {
    bias_mem(bias_init_cnt) := io.bias_init_data
    bias_init_cnt := Mux(bias_init_cnt === (COL_W / ROW - 1).U, 0.U, bias_init_cnt + 1.U)
  }

  mem_inst.io.w_st := io.data_in_st
  mem_inst.io.w_last := io.data_last
  mem_inst.io.w_data := io.data_in
  mem_inst.io.w_addr := io.data_addr
  mem_inst.io.w_valid := io.data_valid
  mem_inst.io.r_last := lu_inst.io.data_in_last
  mem_inst.io.r_addr := lu_inst.io.data_in_addr

  lu_inst.io.data_in := mem_inst.io.r_data
  lu_inst.io.data_in_ready := mem_inst.io.r_ready
  lu_inst.io.data_out_ready := io.data_out_ready
  lu_inst.io.cfg_prefill := io.cfg_prefill
  lu_inst.io.cfg_seqlen := io.cfg_seqlen
  lu_inst.io.cfg_valid := io.cfg_valid
  lu_inst.io.weight_ready := lw_inst.io.weight_ready

  cu_inst.io.data_in := lu_inst.io.data_out
  cu_inst.io.data_in_valid := lu_inst.io.data_out_valid
  cu_inst.io.w_data := lw_inst.io.data_out
  cu_inst.io.w_data_sel := lw_inst.io.data_out_sel
  cu_inst.io.w_valid := lw_inst.io.data_out_valid
  cu_inst.io.out_scale := io.out_scale
  cu_inst.io.cfg_prefill := io.cfg_prefill
  cu_inst.io.cfg_seqlen := io.cfg_seqlen
  cu_inst.io.cfg_valid := io.cfg_valid

  su_inst.io.data_in := cu_inst.io.data_out
  su_inst.io.data_in_valid := cu_inst.io.data_out_valid
  su_inst.io.cfg_prefill := io.cfg_prefill
  su_inst.io.cfg_seqlen := io.cfg_seqlen
  su_inst.io.cfg_valid := io.cfg_valid

  lw_inst.io.update := cu_inst.io.w_update
  lw_inst.io.st := io.layer_st
  lw_inst.io.init_mode := io.weight_init_mode
  lw_inst.io.init_data := io.weight_init_data
  lw_inst.io.active_bank := io.weight_active_bank
  lw_inst.io.preload_valid := io.weight_preload_valid
  lw_inst.io.preload_bank := io.weight_preload_bank
  lw_inst.io.preload_addr := io.weight_preload_addr
  lw_inst.io.preload_data := io.weight_preload_data

  io.data_ready := mem_inst.io.w_ready
  io.weight_init_addr := lw_inst.io.init_addr

  val bias_add = Module(new Fp32VecAdd)
  bias_add.io.a := su_inst.io.data_out
  bias_add.io.b := bias_mem(su_inst.io.data_out_addr(log2Up(COL_W / ROW) - 1, 0))

  io.data_out := bias_add.io.out
  io.data_out_valid := su_inst.io.data_out_valid
  io.data_out_addr := su_inst.io.data_out_addr
  io.data_out_st := su_inst.io.data_out_st
  io.data_out_last := su_inst.io.data_out_last
}

object FFNDownFP32Gen extends App {
  emitVerilog(new FFNDownFP32, Array("--target-dir", "generated"))
}
