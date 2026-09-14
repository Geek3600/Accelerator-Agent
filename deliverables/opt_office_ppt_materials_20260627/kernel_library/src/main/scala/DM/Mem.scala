package DM

import chisel3._
import chisel3.util._


class DataMem(val depth: Int, val width: Int)extends Module{
  val io = IO(new Bundle() {
    val w_st = Input(Bool())
    val w_last = Input(Bool())
    val w_data = Input(UInt(width.W))
    val w_addr = Input(UInt(log2Up(depth).W))
    val w_valid = Input(Bool())
    val w_ready = Output(Bool())


    val r_last = Input(Bool())
    val r_data = Output(UInt(width.W))
    val r_addr = Input(UInt(log2Up(depth).W))
    val r_ready = Output(Bool())
  })

  val buzy_cnt = RegInit(0.U(2.W))
  val full_cnt = RegInit(0.U(2.W))
  val w_sel = RegInit(false.B)
  val r_sel = RegInit(false.B)

  io.w_ready := (full_cnt + buzy_cnt) < 2.U
  io.r_ready := full_cnt > 0.U

  val w_fire = io.w_valid && io.w_ready
  val r_fire = io.r_last && io.r_ready
  val w_start = w_fire && io.w_st
  val w_done = w_fire && io.w_last

  when(w_start && !w_done) {
    buzy_cnt := buzy_cnt + 1.U
  }.elsewhen(!w_start && w_done) {
    buzy_cnt := buzy_cnt - 1.U
  }

  when(w_done && !r_fire) {
    full_cnt := full_cnt + 1.U
  }.elsewhen(!w_done && r_fire) {
    full_cnt := full_cnt - 1.U
  }

  when(w_done) {
    w_sel := ~w_sel
  }

  when(r_fire) {
    r_sel := ~r_sel
  }

  val mem = Module(new R1W1Mem(depth * 2, width))
  mem.io.wen := w_fire
  mem.io.waddr := Cat(w_sel, io.w_addr)
  mem.io.wdata := io.w_data
  mem.io.ren := true.B
  mem.io.raddr := Cat(r_sel, io.r_addr)
  io.r_data := mem.io.rdata


}

class Mem {

}
