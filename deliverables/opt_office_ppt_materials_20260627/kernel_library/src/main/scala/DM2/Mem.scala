package DM2

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
    val r_en = Input(Bool())
    val r_data = Output(UInt(width.W))
    val r_addr = Input(UInt(log2Up(depth).W))
    val r_ready = Output(Bool())
  })

  val buzy_cnt = RegInit(0.U(3.W))
  val full_cnt = RegInit(0.U(3.W))
  val w_ptr = RegInit(0.U(1.W))
  val r_ptr = RegInit(0.U(1.W))
  // A bank is unavailable once it is either already full or currently being
  // written. With only 2 banks, `full_cnt < 2` falsely reports ready when the
  // layout is "one full + one busy", which drops the next ctx/v beat under
  // sustained decode traffic. Count both categories when advertising space.
  io.w_ready := (full_cnt + buzy_cnt) < 2.U
  io.r_ready := full_cnt > 0.U

  val w_fire = io.w_valid && io.w_ready
  val r_fire = io.r_last && io.r_ready
  val w_start = w_fire && io.w_st
  val w_done = w_fire && io.w_last

  // Decode traffic writes DM2 as a sequence of single-beat records where
  // `last=1` is asserted on every beat, while `st` is only asserted on the
  // first beat of the token. Treat `w_done` without a matching open write as a
  // no-op; otherwise the counter underflows (observed as busy=7 in runtime
  // logs) and permanently drops write/read ready.
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
    w_ptr := ~w_ptr
  }
  when(r_fire) {
    r_ptr := ~r_ptr
  }

  val mem0 = SyncReadMem(depth, UInt(width.W))
  val mem1 = SyncReadMem(depth, UInt(width.W))

  when(w_fire && w_ptr === 0.U) {
    mem0.write(io.w_addr, io.w_data)
  }
  when(w_fire && w_ptr === 1.U) {
    mem1.write(io.w_addr, io.w_data)
  }

  val rdata0 = mem0.read(io.r_addr, io.r_en && r_ptr === 0.U)
  val rdata1 = mem1.read(io.r_addr, io.r_en && r_ptr === 1.U)

  // SyncReadMem returns data one cycle later, so latch the selected bank on the
  // read request itself instead of looking at the post-r_fire pointer.
  val r_sel = RegEnable(r_ptr, 0.U, io.r_en)
  io.r_data := Mux(r_sel === 1.U, rdata1, rdata0)


}

class Mem {

}
