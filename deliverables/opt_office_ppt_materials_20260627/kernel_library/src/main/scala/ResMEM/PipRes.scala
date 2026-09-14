package ResMEM
import ResMEM.Param._
import chisel3._
import chisel3.util._
class VCache extends Module {
// 流水级5: VCache - 缓存V向量，等待与Softmax结果相乘
  private val LocalDepth = LOCAL_PRELEN * DATAOUTNUM / DATAINNUM
  val io = IO(new Bundle() {
    val cfg_seqlen = Input(UInt(log2Up(LOCAL_PRELEN).W))
    val cfg_prefill = Input(Bool())
    val cfg_valid = Input(Bool())
    val cfg_single_query = Input(Bool())

    val data_in_st = Input(Bool())
    val data_in = Input(UInt(DATAINW.W))
    val data_in_addr = Input(UInt(log2Up(LocalDepth).W))
    val data_in_valid = Input(Bool())
    val data_in_last = Input(Bool())
    val data_in_ready = Output(Bool())

    val res = Output(UInt((DATAOUTW).W))
    val res_st = Output(Bool())
    val res_addr = Output(UInt(log2Up(BATCHSIZE).W))
    val res_valid = Output(Bool())
    val res_last = Output(Bool())
    val res_ready = Input(Bool())

  })
  val lsu_inst = Module(new LSU)
  val mem_inst = Module(new DataMem(LocalDepth, DATAINW, 4))

  mem_inst.io.w_st := io.data_in_st
  mem_inst.io.w_last := io.data_in_last
  mem_inst.io.w_data := io.data_in
  mem_inst.io.w_addr := io.data_in_addr
  mem_inst.io.w_valid := io.data_in_valid
  mem_inst.io.r_last := lsu_inst.io.data_in_last
  mem_inst.io.r_addr := lsu_inst.io.data_in_addr
  mem_inst.io.r_en := lsu_inst.io.data_in_en

  lsu_inst.io.cfg_seqlen := io.cfg_seqlen
  lsu_inst.io.cfg_prefill := io.cfg_prefill
  lsu_inst.io.cfg_valid := io.cfg_valid
  lsu_inst.io.cfg_single_query := io.cfg_single_query
  lsu_inst.io.data_in := mem_inst.io.r_data
  lsu_inst.io.data_in_ready := mem_inst.io.r_ready
  lsu_inst.io.data_out_ready := io.res_ready


  io.data_in_ready := mem_inst.io.w_ready
  io.res := lsu_inst.io.data_out
  io.res_st := lsu_inst.io.data_out_start
  io.res_last := lsu_inst.io.data_out_last
  io.res_addr := lsu_inst.io.data_out_addr
  io.res_valid := lsu_inst.io.data_out_valid

}

object VCacheGen extends App {
  emitVerilog(new VCache, Array("--target-dir", "generated"))
}

