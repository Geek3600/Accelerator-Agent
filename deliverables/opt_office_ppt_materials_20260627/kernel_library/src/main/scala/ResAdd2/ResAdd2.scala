package ResAdd2

import ResAdd2.Param._
import chisel3._
import chisel3.util._

// ResAdd2: 第二个残差连接模块
// 功能: 将 FFNDown 输出与 S7-ResAdd 输出相加
// 输入1: S7-ResAdd 输出（需要缓存）
// 输入2: FFNDown 输出
// 输出: 两者逐元素相加
class ResAdd2 extends Module {
  val io = IO(new Bundle() {
    // 配置信号
    val cfg_seqlen = Input(UInt(log2Up(MAX_SEQLEN).W))
    val cfg_prefill = Input(Bool())
    val cfg_valid = Input(Bool())

    // S7-ResAdd 输出（需要缓存）
    val s7_in = Input(UInt(DATA_WIDTH.W))
    val s7_in_st = Input(Bool())
    val s7_in_addr = Input(UInt(log2Up(MEM_DEPTH).W))
    val s7_in_valid = Input(Bool())
    val s7_in_last = Input(Bool())
    val s7_ready = Output(Bool())

    // FFNDown 输出
    val ffn_in = Input(UInt(DATA_WIDTH.W))
    val ffn_in_st = Input(Bool())
    val ffn_in_addr = Input(UInt(log2Up(MEM_DEPTH).W))
    val ffn_in_valid = Input(Bool())
    val ffn_in_last = Input(Bool())
    val ffn_ready = Output(Bool())

    // 输出
    val res = Output(UInt(DATA_WIDTH.W))
    val res_st = Output(Bool())
    val res_addr = Output(UInt(log2Up(MEM_DEPTH).W))
    val res_valid = Output(Bool())
    val res_last = Output(Bool())
    val res_ready = Input(Bool())
  })

  // 双缓冲存储器（缓存 S7-ResAdd 输出）
  val mem = Module(new DataMem(MEM_DEPTH, DATA_WIDTH, 3))

  // S7-ResAdd 输出写入存储器
  mem.io.w_st := io.s7_in_st
  mem.io.w_last := io.s7_in_last
  mem.io.w_data := io.s7_in
  mem.io.w_addr := io.s7_in_addr
  mem.io.w_valid := io.s7_in_valid

  io.s7_ready := mem.io.w_ready

  // 状态机: idle / reading
  val idle :: reading :: Nil = Enum(2)
  val state = RegInit(idle)

  val is_idle = state === idle
  val is_reading = state === reading

  // 握手信号
  val fire = io.ffn_in_valid && io.res_ready
  // active: idle 状态下首次握手也算有效
  val active = (is_reading || (is_idle && mem.io.r_ready)) && fire

  // 状态机转换
  switch(state) {
    is(idle) {
      when(mem.io.r_ready && io.ffn_in_valid) {
        state := reading
      }
    }
    is(reading) {
      when(io.ffn_in_last && fire) {
        // 所有数据处理完毕
        when(mem.io.r_ready && io.ffn_in_valid) {
          state := reading  // 下一批立即开始
        }.otherwise {
          state := idle
        }
      }
    }
  }

  // 直接用 ffn_in_addr 读取对应的 S7 数据
  mem.io.r_addr := io.ffn_in_addr
  mem.io.r_en := active
  mem.io.r_last := active && io.ffn_in_last

  // FFN 输入缓存（对齐 SyncReadMem 一拍延迟）
  val ffn_data_r = RegEnable(io.ffn_in, 0.U(DATA_WIDTH.W), active)
  val ffn_valid_r = RegNext(active, false.B)
  val ffn_st_r = RegEnable(io.ffn_in_st, false.B, active)
  val ffn_last_r = RegEnable(io.ffn_in_last, false.B, active)
  val ffn_addr_r = RegEnable(io.ffn_in_addr, 0.U(log2Up(MEM_DEPTH).W), active)

  // 相加运算（逐元素饱和加法）
  val s7_vec = mem.io.r_data.asTypeOf(Vec(SUBVEC, SInt(DATAW.W)))
  val ffn_vec = ffn_data_r.asTypeOf(Vec(SUBVEC, SInt(DATAW.W)))
  val res_vec = Wire(Vec(SUBVEC, SInt(DATAW.W)))

  for (i <- 0 until SUBVEC) {
    val sum = s7_vec(i) +& ffn_vec(i)
    val maxVal = ((1 << (DATAW - 1)) - 1).S
    val minVal = (-(1 << (DATAW - 1))).S
    res_vec(i) := Mux(sum > maxVal, maxVal, Mux(sum < minVal, minVal, sum(DATAW - 1, 0).asSInt))
  }

  // 输出
  io.res := res_vec.asUInt
  io.res_valid := ffn_valid_r
  io.res_st := ffn_st_r
  io.res_last := ffn_last_r
  io.res_addr := ffn_addr_r

  // FFN 准备好信号
  io.ffn_ready := (is_reading || (is_idle && mem.io.r_ready)) && io.res_ready
}

object ResAdd2Gen extends App {
  emitVerilog(new ResAdd2, Array("--target-dir", "generated"))
}
