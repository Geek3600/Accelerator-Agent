package ResAdd

import ResAdd.Param._
import chisel3._
import chisel3.util._

// ResAdd: 残差连接模块
// 功能: 缓存 LayerNorm 前的原始输入，与 OutLinear 输出相加
// 直接用 dm2_in_addr 读取对应的原始数据，不需要自己的计数器
class ResAdd extends Module {
  val io = IO(new Bundle() {
    // 配置信号
    val cfg_seqlen = Input(UInt(log2Up(MAX_SEQLEN).W))
    val cfg_prefill = Input(Bool())
    val cfg_valid = Input(Bool())

    // 原始输入 (缓存到内存)
    val orig_in = Input(UInt(DATA_WIDTH.W))
    val orig_in_st = Input(Bool())
    val orig_in_addr = Input(UInt(log2Up(MEM_DEPTH).W))
    val orig_in_valid = Input(Bool())
    val orig_in_last = Input(Bool())
    val orig_ready = Output(Bool())

    // OutLinear 输出 (用于相加)
    val dm2_in = Input(UInt(DATA_WIDTH.W))
    val dm2_in_st = Input(Bool())
    val dm2_in_addr = Input(UInt(log2Up(MEM_DEPTH).W))
    val dm2_in_valid = Input(Bool())
    val dm2_in_last = Input(Bool())
    val dm2_ready = Output(Bool())

    // 输出
    val res = Output(UInt(DATA_WIDTH.W))
    val res_st = Output(Bool())
    val res_addr = Output(UInt(log2Up(MEM_DEPTH).W))
    val res_valid = Output(Bool())
    val res_last = Output(Bool())
    val res_ready = Input(Bool())
  })

  // 双缓冲存储器 (缓存原始输入)
  val mem = Module(new DataMem(MEM_DEPTH, DATA_WIDTH, 3))

  // 原始输入写入存储器
  mem.io.w_st := io.orig_in_st
  mem.io.w_last := io.orig_in_last
  mem.io.w_data := io.orig_in
  mem.io.w_addr := io.orig_in_addr
  mem.io.w_valid := io.orig_in_valid

  io.orig_ready := mem.io.w_ready

  // 状态机: idle / reading
  val idle :: reading :: Nil = Enum(2)
  val state = RegInit(idle)

  val is_idle = state === idle
  val is_reading = state === reading

  // 握手信号
  val fire = io.dm2_in_valid && io.res_ready
  // active: idle 状态下首次握手也算有效
  val active = (is_reading || (is_idle && mem.io.r_ready)) && fire

  // 状态机转换
  switch(state) {
    is(idle) {
      when(mem.io.r_ready && io.dm2_in_valid) {
        state := reading
      }
    }
    is(reading) {
      when(io.dm2_in_last && fire) {
        // 所有数据处理完毕
        when(mem.io.r_ready && io.dm2_in_valid) {
          state := reading  // 下一批立即开始
        }.otherwise {
          state := idle
        }
      }
    }
  }

  // 直接用 dm2_in_addr 读取对应的原始数据
  mem.io.r_addr := io.dm2_in_addr
  mem.io.r_en := active
  mem.io.r_last := active && io.dm2_in_last

  // DM2 输入缓存 (对齐 SyncReadMem 一拍延迟)
  val dm2_data_r = RegEnable(io.dm2_in, 0.U(DATA_WIDTH.W), active)
  val dm2_valid_r = RegNext(active, false.B)
  val dm2_st_r = RegEnable(io.dm2_in_st, false.B, active)
  val dm2_last_r = RegEnable(io.dm2_in_last, false.B, active)
  val dm2_addr_r = RegEnable(io.dm2_in_addr, 0.U(log2Up(MEM_DEPTH).W), active)

  // 相加运算 (逐元素饱和加法)
  val orig_vec = mem.io.r_data.asTypeOf(Vec(SUBVEC, SInt(DATAW.W)))
  val dm2_vec = dm2_data_r.asTypeOf(Vec(SUBVEC, SInt(DATAW.W)))
  val res_vec = Wire(Vec(SUBVEC, SInt(DATAW.W)))

  for (i <- 0 until SUBVEC) {
    val sum = orig_vec(i) +& dm2_vec(i)
    val maxVal = ((1 << (DATAW - 1)) - 1).S
    val minVal = (-(1 << (DATAW - 1))).S
    res_vec(i) := Mux(sum > maxVal, maxVal, Mux(sum < minVal, minVal, sum(DATAW - 1, 0).asSInt))
  }

  // 输出
  io.res := res_vec.asUInt
  io.res_valid := dm2_valid_r
  io.res_st := dm2_st_r
  io.res_last := dm2_last_r
  io.res_addr := dm2_addr_r

  // DM2 准备好信号
  io.dm2_ready := (is_reading || (is_idle && mem.io.r_ready)) && io.res_ready
}

object ResAddGen extends App {
  emitVerilog(new ResAdd, Array("--target-dir", "generated"))
}
