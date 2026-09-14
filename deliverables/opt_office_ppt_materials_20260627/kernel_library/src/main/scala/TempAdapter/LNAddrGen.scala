package TempAdapter

import TempAdapter.Param._
import chisel3._
import chisel3.util._

// LayerNorm 地址生成器
// 功能：为 LayerNorm 模块生成地址和控制信号
// 支持 Prefill 和 Decode 两种模式
class LNAddrGen extends Module {
  val io = IO(new Bundle() {
    // 配置信号
    val cfg_seqlen  = Input(UInt(log2Up(MAX_SEQLEN).W))
    val cfg_prefill = Input(Bool())
    val cfg_valid   = Input(Bool())

    // 握手信号
    val data_ready    = Input(Bool())   // 外部内存准备好
    val adapter_ready = Input(Bool())   // TempAdapter 准备好

    // 输出到外部内存
    val mem_addr = Output(UInt(32.W))   // 外部内存地址

    // 输出到 LayerNorm
    val data_st    = Output(Bool())     // 开始信号
    val data_addr  = Output(UInt(log2Up(LN_DEPTH).W))  // LayerNorm ��部地址
    val data_valid = Output(Bool())     // 数据有效
    val data_last  = Output(Bool())     // 结束信号
  })

  // 锁存配置
  val is_prefill = RegEnable(io.cfg_prefill, io.cfg_valid)
  val seqlen = RegEnable(io.cfg_seqlen, io.cfg_valid)

  // 状态机
  val idle :: busy :: Nil = Enum(2)
  val state = RegInit(idle)
  val is_idle = state === idle
  val is_busy = state === busy

  // 握手信号
  val fire = io.data_ready && io.adapter_ready
  val start_pending = RegInit(false.B)

  when(io.cfg_valid) {
    start_pending := true.B
  }

  // ========================================
  // 三层计数器
  // ========================================

  // 内层循环：收集 768 维向量（64 次，每次 12 个元素）
  val vec_cnt = Wire(UInt(log2Up(COLLECT_NUM).W))
  val vec_last = vec_cnt === (COLLECT_NUM - 1).U
  vec_cnt := RegEnable(
    Mux(vec_last, 0.U, vec_cnt + 1.U),
    0.U,
    is_busy && fire
  )

  // 中层循环：Prefill 模式的序列计数
  val prefill_cnt = Wire(UInt(log2Up(MAX_PREFILL).W))
  val prefill_last = prefill_cnt === seqlen
  prefill_cnt := RegEnable(
    Mux(prefill_last, 0.U, prefill_cnt + 1.U),
    0.U,
    is_busy && vec_last && is_prefill && fire
  )

  // 外层循环：Decode 模式的 batch 计数
  val batch_cnt = Wire(UInt(log2Up(BATCHSIZE).W))
  val batch_last = batch_cnt === (BATCHSIZE - 1).U
  batch_cnt := RegEnable(
    Mux(batch_last, 0.U, batch_cnt + 1.U),
    0.U,
    is_busy && vec_last && !is_prefill && fire
  )

  // ========================================
  // 状态机转换
  // ========================================
  val load_over = vec_last && (is_prefill && prefill_last || !is_prefill && batch_last)

  val idle_mux = Mux(start_pending && fire, busy, idle)
  val busy_mux = Mux(load_over && fire, idle, busy)

  state := Mux(is_idle, idle_mux, busy_mux)

  when(is_idle && start_pending && fire) {
    start_pending := false.B
  }

  // ========================================
  // 地址生成
  // ========================================

  // 外部内存地址
  // Prefill: prefill_cnt × 64 + vec_cnt
  // Decode:  batch_cnt × 64 + vec_cnt
  io.mem_addr := Mux(
    is_prefill,
    prefill_cnt * COLLECT_NUM.U + vec_cnt,
    batch_cnt * COLLECT_NUM.U + vec_cnt
  )

  // LayerNorm 内部地址（0-63）
  io.data_addr := vec_cnt

  // ========================================
  // 控制信号（打一拍对齐数据）
  // ========================================
  io.data_valid := RegNext(is_busy && fire, false.B)

  io.data_st := RegNext(
    is_busy && vec_cnt === 0.U && prefill_cnt === 0.U && batch_cnt === 0.U && fire,
    false.B
  )

  io.data_last := RegNext(
    is_busy && load_over && fire,
    false.B
  )
}

object LNAddrGenGen extends App {
  emitVerilog(new LNAddrGen, Array("--target-dir", "generated"))
}
