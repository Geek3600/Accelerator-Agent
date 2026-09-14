package FFNDown

import FFNDown.Param._
import chisel3._
import chisel3.util._

// 双缓冲存储器
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
    val r_data = Output(UInt(width.W))
    val r_ready = Output(Bool())
  })

  val buzy_cnt = Wire(UInt(3.W))
  val full_cnt = Wire(UInt(3.W))

  buzy_cnt := RegEnable(
    Mux(
      io.w_st,
      Mux(io.w_last, buzy_cnt, buzy_cnt + 1.U),
      Mux(io.w_last, buzy_cnt - 1.U, buzy_cnt)
    ),
    0.U,
    io.w_st || io.w_last
  )

  full_cnt := RegEnable(
    Mux(
      io.w_last,
      Mux(io.r_last, full_cnt, full_cnt + 1.U),
      Mux(io.r_last, full_cnt - 1.U, full_cnt)
    ),
    0.U,
    io.w_last || io.r_last
  )

  val w_sel = Wire(Bool())
  w_sel := RegEnable(~w_sel, false.B, io.w_last)
  val r_sel = Wire(Bool())
  r_sel := RegEnable(~r_sel, false.B, io.r_last)

  val mem0 = SyncReadMem(depth, UInt(width.W))
  val mem1 = SyncReadMem(depth, UInt(width.W))

  when(io.w_valid && !w_sel) {
    mem0.write(io.w_addr, io.w_data)
  }
  when(io.w_valid && w_sel) {
    mem1.write(io.w_addr, io.w_data)
  }

  // r_sel points at the next buffer to consume; when false we need the buffer
  // that was just filled first (mem0), and after one full read it flips to mem1.
  io.r_data := Mux(r_sel, mem1.read(io.r_addr), mem0.read(io.r_addr))

  io.w_ready := (full_cnt + buzy_cnt) < 2.U
  io.r_ready := full_cnt > 0.U
}
