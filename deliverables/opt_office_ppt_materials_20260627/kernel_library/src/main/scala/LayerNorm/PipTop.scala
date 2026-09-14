package LayerNorm
import chisel3._
import chisel3.util._
import LayerNorm.Param._

class LayerNorm extends Module {
// 流水级1: LayerNorm - 对输入进行层归一化
  val io = IO(new Bundle() {

    val data_in_st = Input(Bool())
    val data_in = Input(UInt(MEM_WIDTH.W))
    val data_addr = Input(UInt(log2Up(MEM_DEPTH).W))
    val data_valid = Input(Bool())
    val data_last = Input(Bool())
    val data_ready = Output(Bool())


    val w_in = Input(UInt(MEM_WIDTH.W))
    val w_valid = Input(Bool())


    val res = Output(UInt(MEM_WIDTH.W))
    val res_st = Output(Bool())
    val res_addr = Output(UInt(log2Up(MEM_DEPTH).W))
    val res_valid = Output(Bool())
    val res_last = Output(Bool())
    val res_ready = Input(Bool())

  })
  val mem_inst = Module(new DataMem(MEM_DEPTH, MEM_WIDTH))

  val cu_inst = Module(new LayerNormCU)
  val su_inst = Module(new StoreUnit)
  val lu_inst = Module(new LoadUnit)

  mem_inst.io.w_st := io.data_in_st
  mem_inst.io.w_last := io.data_last
  mem_inst.io.w_data := io.data_in
  mem_inst.io.w_addr := io.data_addr
  mem_inst.io.w_valid := io.data_valid
  mem_inst.io.r_last := lu_inst.io.data_in_last
  mem_inst.io.r_addr := lu_inst.io.data_in_addr


  lu_inst.io.data_in := mem_inst.io.r_data
  lu_inst.io.data_in_ready := mem_inst.io.r_ready
  lu_inst.io.data_out_ready := io.res_ready


  cu_inst.io.data_in := lu_inst.io.data_out
  cu_inst.io.data_in_valid := lu_inst.io.data_out_valid
  cu_inst.io.w_data := io.w_in
  cu_inst.io.w_valid := io.w_valid


  su_inst.io.data_in := cu_inst.io.data_out
  su_inst.io.data_in_valid := cu_inst.io.data_out_valid

  io.data_ready := mem_inst.io.w_ready

  io.res := su_inst.io.data_out
  io.res_st := lu_inst.io.data_out_start
  io.res_addr := su_inst.io.data_out_addr
  io.res_valid := su_inst.io.data_out_valid
  io.res_last := su_inst.io.data_out_last



}

object LayerNormGen extends App {
  emitVerilog(new LayerNorm, Array("--target-dir", "generated"))
}