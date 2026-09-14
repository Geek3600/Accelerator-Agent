package DM

import DM.Param._
import chisel3.util._
import chisel3._

//class Top extends Module {
//  val io = IO(new Bundle() {
//    val cfg_seqlen = Input(UInt(log2Up(MAX_SEQLEN).W))
//    val cfg_prefill = Input(Bool())
//    val cfg_valid = Input(Bool())
//
//
//    val data_in = Input(UInt((2*LOAD_VECNUM * DATAW).W))
//    val data_in_addr = Output(UInt(log2Up(MEM_DEPTH).W))
//    val data_in_last = Output(Bool())
//    val data_in_ready = Input(Bool())
//
//
//    val data_out = Output(UInt((MAX_SEQLEN * DATAW * 4).W))
//    val data_out_valid = Output(Bool())
//
//
//    val data_out_ready = Input(Bool())
//    val data_out_start = Output(Bool())
//
//
//
//  })
//  val loadU = Module(new  LoadUnit)
//  val dm = Module(new DMCUPlus)
//  loadU.io.cfg_valid := io.cfg_valid
//  loadU.io.cfg_prefill := io.cfg_prefill
//  loadU.io.cfg_prelen := io.cfg_seqlen
//
//  loadU.io.data_in := io.data_in
//  loadU.io.data_in_ready := io.data_in_ready
//  loadU.io.data_out_ready := io.data_out_ready
//
//  dm.io.cfg_valid := io.cfg_valid
//  dm.io.cfg_prefill:= io.cfg_prefill
//  dm.io.cfg_seqlen := io.cfg_seqlen
//  dm.io.data_in := loadU.io.data_out
//  dm.io.data_in_valid := loadU.io.data_out_valid
//
//  io.data_in_addr := loadU.io.data_in_addr
//  io.data_in_last := loadU.io.data_in_last
//  io.data_out := dm.io.data_out
//  io.data_out_valid := dm.io.data_out_valid
//  io.data_out_start := loadU.io.data_out_start
//}
class DM1 extends Module {
// 流水级3: DM1 - 计算 Q·K 点积
  val io = IO(new Bundle() {
    val cfg_seqlen = Input(UInt(log2Up(MAX_SEQLEN).W))
    val cfg_prefill = Input(Bool())
    val cfg_valid = Input(Bool())


    val data_in_st = Input(Bool())
    val data_in = Input(UInt((2 * LOAD_VECNUM * DATAW).W))
    val data_addr = Input(UInt(log2Up(HEAD_VECNUM / LOAD_VECNUM * BATCHSIZE).W))
    val data_valid = Input(Bool())
    val data_last = Input(Bool())
    val data_ready = Output(Bool())


    val res = Output(UInt((MAX_SEQLEN * DATAW).W))
    val res_st = Output(Bool())
    val res_addr = Output(UInt(log2Up(BATCHSIZE).W))
    val res_valid = Output(Bool())
    val res_last = Output(Bool())
    val res_ready = Input(Bool())


  })
  val lu_inst = Module(new LoadUnit)
  val cu_inst = Module(new DMCUPlus)
  val su_inst = Module(new StoreUnit)
  val mem_inst = Module(new DataMem(HEAD_VECNUM / LOAD_VECNUM * BATCHSIZE, 2 * LOAD_VECNUM * DATAW))

  mem_inst.io.w_st := io.data_in_st
  mem_inst.io.w_last := io.data_last
  mem_inst.io.w_data := io.data_in
  mem_inst.io.w_addr := io.data_addr
  mem_inst.io.w_valid := io.data_valid
  mem_inst.io.r_last := lu_inst.io.data_in_last
  mem_inst.io.r_addr := lu_inst.io.data_in_addr

  lu_inst.io.cfg_prelen := io.cfg_seqlen
  lu_inst.io.cfg_prefill := io.cfg_prefill
  lu_inst.io.cfg_valid := io.cfg_valid
  lu_inst.io.data_in := mem_inst.io.r_data
  lu_inst.io.data_in_ready := mem_inst.io.r_ready
  lu_inst.io.data_out_ready := io.res_ready

  cu_inst.io.data_in := lu_inst.io.data_out
  cu_inst.io.data_in_valid := lu_inst.io.data_out_valid
  cu_inst.io.cfg_prefill := io.cfg_prefill
  cu_inst.io.cfg_valid := io.cfg_valid
  cu_inst.io.cfg_seqlen := io.cfg_seqlen


  su_inst.io.cfg_seqlen := io.cfg_seqlen
  su_inst.io.cfg_prefill := io.cfg_prefill
  su_inst.io.cfg_valid := io.cfg_valid
  su_inst.io.data_in := cu_inst.io.data_out
  su_inst.io.data_in_valid := cu_inst.io.data_out_valid

  io.data_ready := mem_inst.io.w_ready
  val inputFire = io.data_valid && io.data_ready
  lu_inst.io.launch := inputFire && io.data_in_st

  io.res := su_inst.io.data_out
  io.res_st := lu_inst.io.data_out_start
  io.res_addr := su_inst.io.data_out_addr
  io.res_valid := su_inst.io.data_out_valid
  io.res_last := su_inst.io.data_out_last
}
object DM1Gen extends App {
  emitVerilog(new DM1, Array("--target-dir", "generated"))
}

  // ┌─────────────────────────────────────────────────────────────────────────────┐
  // │                         握手信号交互                                          │
  // ├─────────────────────────────────────────────────────────────────────────────┤
  // │                                                                             │
  // │  DataMem ←→ LoadUnit:                                                          │
  // │  ┌──────────────────────────────────────────────────────────────────────┐   │
  // │  │  DataMem.r_ready ──────────────────────→ LoadUnit.data_in_ready         │   │
  // │  │  LoadUnit.data_in_addr ───────────────────→ DataMem.raddr               │   │
  // │  │  DataMem.rdata ────────────────────────→ LoadUnit.data_in               │   │
  // │  └──────────────────────────────────────────────────────────────────────┘   │
  // │                                                                             │
  // │  LoadUnit ←→ DMCUPlus:                                                         │
  // │  ┌──────────────────────────────────────────────────────────────────────┐   │
  // │  │  LoadUnit.data_out ───────────────────────→ DMCUPlus.data_in            │   │
  // │  │  LoadUnit.data_out_valid ─────────────────→ DMCUPlus.data_in_valid      │   │
  // │  │  LoadUnit.data_out_start ─────────────────→ DMCUPlus.data_in_start      │   │
  // │  │  (无反压信号，LoadU通过空转来等待DMCUPlus)                               │   │
  // │  └──────────────────────────────────────────────────────────────────────┘   │
  // │                                                                             │
  // │  DMCUPlus ←→ StoreUnit:                                                        │
  // │  ┌──────────────────────────────────────────────────────────────────────┐   │
  // │  │  DMCUPlus.res ─────────────────────────→ StoreUnit.data_in              │   │
  // │  │  DMCUPlus.res_valid ───────────────────→ StoreUnit.data_in_valid        │   │
  // │  │  StoreUnit.data_out_ready ────────────────→ DMCUPlus.res_ready          │   │
  // │  └──────────────────────────────────────────────────────────────────────┘   │
  // │                                                                             │
  // └─────────────────────────────────────────────────────────────────────────────┘
