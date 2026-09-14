package ResAdd

import ResAdd.Param._
import chisel3._
import chisel3.util._

// 双缓冲存储器 (与 ResMEM 类似)
class R1W1Mem(val depth: Int, val width: Int) extends Module {
  val addrw = log2Up(depth)
  val io = IO(new Bundle() {
    val wen = Input(Bool())
    val waddr = Input(UInt(addrw.W))
    val wdata = Input(UInt(width.W))

    val ren = Input(Bool())
    val raddr = Input(UInt(addrw.W))
    val rdata = Output(UInt(width.W))
  })
  val mem = SyncReadMem(depth, UInt(width.W))
  io.rdata := mem.read(io.raddr, io.ren)
  when(io.wen) {
    mem.write(io.waddr, io.wdata)
  }
}

// 双缓冲管理器
class DataMem(val depth: Int, val width: Int, val num: Int) extends Module {
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

  val buzy_cnt = RegInit(0.U(log2Up(num + 1).W))
  val full_cnt = RegInit(0.U(log2Up(num + 1).W))
  val w_ptr = RegInit(0.U(log2Up(num).W))
  val r_ptr = RegInit(0.U(log2Up(num).W))

  // A bank is unavailable once it is either full or currently being written.
  io.w_ready := (full_cnt + buzy_cnt) < num.U
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

  val w_ptr_last = w_ptr === (num - 1).U
  val r_ptr_last = r_ptr === (num - 1).U

  when(w_done) {
    w_ptr := Mux(w_ptr_last, 0.U, w_ptr + 1.U)
  }

  when(r_fire) {
    r_ptr := Mux(r_ptr_last, 0.U, r_ptr + 1.U)
  }

  val mem_list = List.fill(num)(Module(new R1W1Mem(depth, width)))

  for (i <- 0 until num) {
    mem_list(i).io.wen := w_ptr === i.U && w_fire
    mem_list(i).io.waddr := io.w_addr
    mem_list(i).io.wdata := io.w_data

    mem_list(i).io.ren := r_ptr === i.U && io.r_en
    mem_list(i).io.raddr := io.r_addr
  }

  val r_sel = RegEnable(r_ptr, 0.U, io.r_en)

  io.r_data := MuxLookup(
    r_sel,
    0.U
  )(
    (0 until num).map { i => i.U -> mem_list(i).io.rdata }
  )
}
