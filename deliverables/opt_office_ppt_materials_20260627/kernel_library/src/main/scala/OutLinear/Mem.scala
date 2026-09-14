package OutLinear

import OutLinear.Param._
import chisel3._
import chisel3.util._

// 双缓冲存储器。
// 与 DM2/ResMEM 一样，bank 占用只能按真实 fire 语义推进；
// 否则 full-seq backpressure 下会把同一帧的后续 beat 误当成“重新申请新 bank”，
// 提前释放/切换读写 bank，最终把读侧在半帧处打空。
class DataMem(depth: Int, width: Int) extends Module {
  val io = IO(new Bundle() {
    val w_st = Input(Bool())
    val w_last = Input(Bool())
    val w_data = Input(UInt(width.W))
    val w_addr = Input(UInt(log2Up(depth).W))
    val w_valid = Input(Bool())
    val w_ready = Output(Bool())

    val r_last = Input(Bool())
    val r_addr = Input(UInt(log2Up(depth).W))
    val r_en = Input(Bool())
    val r_data = Output(UInt(width.W))
    val r_ready = Output(Bool())
  })

  val buzy_cnt = RegInit(0.U(3.W))
  val full_cnt = RegInit(0.U(3.W))
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
  }.elsewhen(!w_start && w_done && buzy_cnt =/= 0.U) {
    buzy_cnt := buzy_cnt - 1.U
  }

  when(w_done && !r_fire) {
    full_cnt := full_cnt + 1.U
  }.elsewhen(!w_done && r_fire && full_cnt =/= 0.U) {
    full_cnt := full_cnt - 1.U
  }

  when(w_done) {
    w_sel := ~w_sel
  }
  when(r_fire) {
    r_sel := ~r_sel
  }

  val mem0 = SyncReadMem(depth, UInt(width.W))
  val mem1 = SyncReadMem(depth, UInt(width.W))

  when(w_fire && !w_sel) {
    mem0.write(io.w_addr, io.w_data)
  }
  when(w_fire && w_sel) {
    mem1.write(io.w_addr, io.w_data)
  }

  val mem0_r = mem0.read(io.r_addr, io.r_en && !r_sel)
  val mem1_r = mem1.read(io.r_addr, io.r_en && r_sel)
  val r_sel_d = RegEnable(r_sel, false.B, io.r_en)
  io.r_data := Mux(r_sel_d, mem1_r, mem0_r)
}
