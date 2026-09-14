package QKVLinear

import QKVLinear._
import QuantCommon.Precision._
import QuantCommon.{FpBackend, XilinxFpTargetConfig}
import chisel3._
import chisel3.util._
import QKVLinear.Param._

// QKVLinear: QKV 映射模块
// 功能: 将 LayerNorm 输出的 768 维向量映射为 Q/K/V 三个 768 维向量
// 输入: 96-bit/cycle (12 elements)，768 维向量
// 输出: 48-bit/cycle [V1,V0|K1,K0|Q1,Q0]，输出给 Attention
//
// 矩阵乘法: X(768) × W(768×2304) = [Q|K|V](2304)
// 然后提取 Q[0:63], K[64:127], V[128:191] 各 64 维给 Attention
class QKVLinear extends Module {
  val io = IO(new Bundle() {
    val layer_st = Input(Bool())

    // 权重初始化接口
    val weight_init_mode = Input(Bool())  // true: 初始化模式, false: 计算模式
    val weight_init_data = Input(UInt(WMEM_WIDTH.W))
    val weight_init_addr = Output(UInt(log2Up(WMEM_DEPTH).W))
    val weight_active_bank = Input(Bool())
    val weight_preload_bank = Input(Bool())
    val weight_preload_valid = Input(Bool())
    val weight_preload_addr = Input(UInt(log2Up(WMEM_DEPTH).W))
    val weight_preload_data = Input(UInt(WMEM_WIDTH.W))
    val bias_init_data = Input(UInt(MEM_WIDTH.W))
    val bias_init_valid = Input(Bool())
    val q_out_inv_scale = Input(UInt(FP32_WIDTH.W))
    val k_out_inv_scale = Input(UInt(FP32_WIDTH.W))
    val v_out_inv_scale = Input(UInt(FP32_WIDTH.W))
    val q_bias_scale = Input(UInt(FP32_WIDTH.W))
    val k_bias_scale = Input(UInt(FP32_WIDTH.W))
    val v_bias_scale = Input(UInt(FP32_WIDTH.W))

    // 来自 LayerNorm 的输入
    val data_in_st = Input(Bool())
    val data_in = Input(UInt(MEM_WIDTH.W))
    val data_addr = Input(UInt(log2Up(MEM_DEPTH).W))
    val data_valid = Input(Bool())
    val data_last = Input(Bool())
    val data_ready = Output(Bool())

    // 配置信号
    val cfg_prefill = Input(Bool())
    val cfg_seqlen = Input(UInt(log2Up(MAX_SEQLEN).W))
    val cfg_valid = Input(Bool())
    val cfg_single_query = Input(Bool())

    // 输出到 Attention (Load0 格式: 48-bit [V1,V0|K1,K0|Q1,Q0])
    val data_out = Output(UInt(48.W))
    val data_out_st = Output(Bool())
    val data_out_head = Output(UInt(log2Up(HEAD_NUM).W))
    val data_out_addr = Output(UInt(32.W))
    val data_out_valid = Output(Bool())
    val data_out_last = Output(Bool())
    val data_out_ready = Input(Bool())
  })

  // 锁存配置
  val is_prefill = RegEnable(io.cfg_prefill, io.cfg_valid)
  val seqlen = RegEnable(io.cfg_seqlen, io.cfg_valid)
  val is_single_query = RegEnable(io.cfg_single_query, false.B, io.cfg_valid)

  // ========================================
  // Linear 计算核心
  // ========================================
  val mem_inst = Module(new DataMem(MEM_DEPTH, MEM_WIDTH))
  val lu_inst = Module(new LoadUnit)
  val cu_inst = Module(new CUQuant)
  val su_inst = Module(new StoreUnit)
  val lw_inst = Module(new LoadWeight)
  val bias_mem = Reg(Vec(OUT_VECTOR / ROW, UInt(MEM_WIDTH.W)))
  val bias_init_cnt = RegInit(0.U(log2Up(OUT_VECTOR / ROW).W))

  when(io.bias_init_valid) {
    bias_mem(bias_init_cnt) := io.bias_init_data
    bias_init_cnt := Mux(bias_init_cnt === (OUT_VECTOR / ROW - 1).U, 0.U, bias_init_cnt + 1.U)
  }

  mem_inst.io.w_st := io.data_in_st
  mem_inst.io.w_last := io.data_last
  mem_inst.io.w_data := io.data_in
  mem_inst.io.w_addr := io.data_addr
  mem_inst.io.w_valid := io.data_valid
  mem_inst.io.r_last := lu_inst.io.data_in_last
  mem_inst.io.r_addr := lu_inst.io.data_in_addr

  lu_inst.io.data_in := mem_inst.io.r_data
  lu_inst.io.data_in_ready := mem_inst.io.r_ready
  lu_inst.io.data_out_ready := io.data_out_ready
  lu_inst.io.cfg_prefill := io.cfg_prefill
  lu_inst.io.cfg_seqlen := io.cfg_seqlen
  lu_inst.io.cfg_valid := io.cfg_valid
  lu_inst.io.cfg_single_query := io.cfg_single_query
  lu_inst.io.weight_ready := lw_inst.io.weight_ready

  cu_inst.io.data_in := lu_inst.io.data_out
  cu_inst.io.data_in_valid := lu_inst.io.data_out_valid
  cu_inst.io.w_data := lw_inst.io.data_out
  cu_inst.io.w_data_sel := lw_inst.io.data_out_sel
  cu_inst.io.w_valid := lw_inst.io.data_out_valid
  cu_inst.io.cfg_prefill := io.cfg_prefill
  cu_inst.io.cfg_seqlen := io.cfg_seqlen
  cu_inst.io.cfg_valid := io.cfg_valid
  cu_inst.io.cfg_single_query := io.cfg_single_query

  su_inst.io.data_in := cu_inst.io.data_out
  su_inst.io.data_in_valid := cu_inst.io.data_out_valid
  su_inst.io.cfg_prefill := io.cfg_prefill
  su_inst.io.cfg_seqlen := io.cfg_seqlen
  su_inst.io.cfg_valid := io.cfg_valid
  su_inst.io.cfg_single_query := io.cfg_single_query

  lw_inst.io.update := cu_inst.io.w_update
  lw_inst.io.st := io.layer_st || (io.data_in_st && !mem_inst.io.r_ready)
  lw_inst.io.init_mode := io.weight_init_mode
  lw_inst.io.init_data := io.weight_init_data
  lw_inst.io.active_bank := io.weight_active_bank
  lw_inst.io.preload_valid := io.weight_preload_valid
  lw_inst.io.preload_bank := io.weight_preload_bank
  lw_inst.io.preload_addr := io.weight_preload_addr
  lw_inst.io.preload_data := io.weight_preload_data

  io.data_ready := mem_inst.io.w_ready
  io.weight_init_addr := lw_inst.io.init_addr

  // ========================================
  // 输出格式转换: 2304维 -> Q/K/V 各64维 -> 48-bit/cycle
  // ========================================
  // Linear 输出: 96-bit/cycle, 共 192 次 (2304/12=192)
  // 需要收集完整的 2304 维向量，然后提取 Q/K/V

  // 状态机
  val idle :: collecting :: priming :: outputting :: Nil = Enum(4)
  val state = RegInit(idle)

  val is_idle = state === idle
  val is_collecting = state === collecting
  val is_priming = state === priming
  val is_outputting = state === outputting
  val all_output_done = WireDefault(false.B)
  val collect_start = is_idle || (is_outputting && all_output_done && io.data_out_ready)
  val collect_fire = su_inst.io.data_out_valid && (is_collecting || collect_start)
  val epilogueLatency =
    if (FpBackend.useVivadoIp)
      XilinxFpTargetConfig.FixedToFloatLatency +
        XilinxFpTargetConfig.MulLatency +
        XilinxFpTargetConfig.AddLatency +
        XilinxFpTargetConfig.FloatToFixedLatency
    else
      0

  // 收集计数器 (192 次收集 2304 维)
  val COLLECT_NUM = OUT_VECTOR / ROW  // = 2304 / 12 = 192
  val collect_addr = su_inst.io.data_out_addr
  val collect_done = su_inst.io.data_out_last
  val collect_commit = Wire(Bool())
  val collect_addr_d = Wire(UInt(collect_addr.getWidth.W))
  val collect_done_d = Wire(Bool())
  if (epilogueLatency == 0) {
    collect_commit := collect_fire
    collect_addr_d := collect_addr
    collect_done_d := collect_done && collect_fire
  } else {
    val collect_valid_pipe = RegInit(VecInit(Seq.fill(epilogueLatency)(false.B)))
    val collect_addr_pipe = RegInit(VecInit(Seq.fill(epilogueLatency)(0.U(collect_addr.getWidth.W))))
    val collect_done_pipe = RegInit(VecInit(Seq.fill(epilogueLatency)(false.B)))
    collect_valid_pipe(0) := collect_fire
    collect_addr_pipe(0) := collect_addr
    collect_done_pipe(0) := collect_done && collect_fire
    for (i <- 1 until epilogueLatency) {
      collect_valid_pipe(i) := collect_valid_pipe(i - 1)
      collect_addr_pipe(i) := collect_addr_pipe(i - 1)
      collect_done_pipe(i) := collect_done_pipe(i - 1)
    }
    collect_commit := collect_valid_pipe.last
    collect_addr_d := collect_addr_pipe.last
    collect_done_d := collect_done_pipe.last
  }
  val collect_token = (collect_addr_d / COLLECT_NUM.U)(log2Up(BATCHSIZE) - 1, 0)
  val collect_vec = collect_addr_d % COLLECT_NUM.U

  // 缓存所有 token 的 2304 维向量。这里必须用同步 RAM；寄存器大阵列会展开
  // 成约 295 kbit FF/选择网络，是当前 CLB site 和 QKV route delay 的主来源。
  val VEC_BUFFER_DEPTH = BATCHSIZE * COLLECT_NUM
  val vecBufferMem = SyncReadMem(VEC_BUFFER_DEPTH, UInt(MEM_WIDTH.W))
  vecBufferMem.suggestName("vecBufferMem")
  def vecBufferAddr(token: UInt, word: UInt): UInt =
    (token * COLLECT_NUM.U + word)(log2Up(VEC_BUFFER_DEPTH) - 1, 0)
  val collectWriteEnableReg = RegInit(false.B)
  collectWriteEnableReg.suggestName("collectWriteEnableReg")
  val collectTokenReg = Reg(UInt(collect_token.getWidth.W))
  collectTokenReg.suggestName("collectTokenReg")
  val collectVecReg = Reg(UInt(collect_vec.getWidth.W))
  collectVecReg.suggestName("collectVecReg")
  val collectDataReg = Reg(UInt(MEM_WIDTH.W))
  collectDataReg.suggestName("collectDataReg")
  val collect_vec_now = collect_addr % COLLECT_NUM.U
  val scale_sel = Mux(
    collect_vec_now < (768 / ROW).U,
    io.q_out_inv_scale,
    Mux(collect_vec_now < (2 * 768 / ROW).U, io.k_out_inv_scale, io.v_out_inv_scale)
  )
  val bias_scale_sel = Mux(
    collect_vec_now < (768 / ROW).U,
    io.q_bias_scale,
    Mux(collect_vec_now < (2 * 768 / ROW).U, io.k_bias_scale, io.v_bias_scale)
  )
  val epilogue_inst = Module(new Int32VecScaleBiasToSInt32(ROW))
  epilogue_inst.io.in := Mux(collect_fire, su_inst.io.data_out, 0.U(su_inst.io.data_out.getWidth.W))
  epilogue_inst.io.accScale := Mux(collect_fire, scale_sel, 0.U(FP32_WIDTH.W))
  epilogue_inst.io.bias := Mux(collect_fire, bias_mem(collect_vec_now), 0.U(MEM_WIDTH.W))
  epilogue_inst.io.biasScale := Mux(collect_fire, bias_scale_sel, 0.U(FP32_WIDTH.W))

  val su_vec = epilogue_inst.io.out.asTypeOf(Vec(ROW, SInt(INT32_WIDTH.W)))
  val biased_vec = Wire(Vec(ROW, SInt(DATAW.W)))
  for (i <- 0 until ROW) {
    val maxVal = ((1 << (DATAW - 1)) - 1).S
    val minVal = (-(1 << (DATAW - 1))).S
    biased_vec(i) := Mux(
      su_vec(i) > maxVal,
      maxVal,
      Mux(su_vec(i) < minVal, minVal, su_vec(i)(DATAW - 1, 0).asSInt)
    )
  }
  collectWriteEnableReg := collect_commit
  when(collect_commit) {
    collectTokenReg := collect_token
    collectVecReg := collect_vec
    collectDataReg := biased_vec.asUInt
  }
  when(collectWriteEnableReg) {
    vecBufferMem.write(vecBufferAddr(collectTokenReg, collectVecReg), collectDataReg)
  }

  // Keep the output counters as explicit state regs. The previous
  // self-referential RegEnable form lets Vivado sink "inactive => 0" logic
  // into local R pins, which creates the long recovery/reset paths now showing
  // up in routed timing.
  val headCntReg = RegInit(0.U(log2Up(HEAD_NUM + 1).W))
  val prefillCntReg = RegInit(0.U(log2Up(MAX_PREFILL + 1).W))
  val batchCntReg = RegInit(0.U(log2Up(BATCHSIZE).W))
  val head_cnt = headCntReg
  val head_last = head_cnt === (HEAD_NUM - 1).U
  val prefill_cnt = prefillCntReg
  val batch_cnt = batchCntReg
  val current_token = Mux(is_prefill, prefill_cnt, batch_cnt)
  val current_token_idx = current_token(log2Up(BATCHSIZE) - 1, 0)
  // 输出计数器 (32 次，每次输出 2 个 Q + 2 个 K + 2 个 V)
  val OUTPUT_NUM = HEAD_DIM / 2  // = 32
  val outputCntReg = RegInit(0.U(log2Up(OUTPUT_NUM).W))
  val output_cnt = outputCntReg
  val output_last = output_cnt === (OUTPUT_NUM - 1).U

  val output_fire = is_outputting && io.data_out_ready

  // Prefill 计数器
  val prefill_last = prefill_cnt === seqlen

  // Decode 计数器
  val decodeBatchLast = Mux(is_single_query, 0.U(batch_cnt.getWidth.W), (BATCHSIZE - 1).U(batch_cnt.getWidth.W))
  val batch_last = batch_cnt === decodeBatchLast

  // token 级别的 last（prefill 或 decode 的所有 token 输出完毕）
  val token_last = is_prefill && prefill_last || !is_prefill && batch_last
  val nextHeadCnt = Mux(head_last, 0.U(head_cnt.getWidth.W), headCntReg + 1.U)
  val nextPrefillCnt = Mux(prefill_last, 0.U(prefill_cnt.getWidth.W), prefillCntReg + 1.U)
  val nextBatchCnt = Mux(batch_last, 0.U(batch_cnt.getWidth.W), batchCntReg + 1.U)
  val nextTokenIdx = Mux(is_prefill, nextPrefillCnt, nextBatchCnt)(log2Up(BATCHSIZE) - 1, 0)
  val successorHeadIdx = Mux(token_last, nextHeadCnt, headCntReg)

  val HEAD_WORDS = (HEAD_DIM + ROW - 1) / ROW
  val PREFETCH_STEPS = HEAD_WORDS * 3
  val headOffsetWidth = log2Up(ROW)
  val activeHeadQWordReg = Reg(Vec(HEAD_WORDS, UInt(MEM_WIDTH.W)))
  val activeHeadKWordReg = Reg(Vec(HEAD_WORDS, UInt(MEM_WIDTH.W)))
  val activeHeadVWordReg = Reg(Vec(HEAD_WORDS, UInt(MEM_WIDTH.W)))
  val shadowHeadQWordReg = Reg(Vec(HEAD_WORDS, UInt(MEM_WIDTH.W)))
  val shadowHeadKWordReg = Reg(Vec(HEAD_WORDS, UInt(MEM_WIDTH.W)))
  val shadowHeadVWordReg = Reg(Vec(HEAD_WORDS, UInt(MEM_WIDTH.W)))
  val activeHeadOffsetReg = RegInit(0.U(headOffsetWidth.W))
  val shadowHeadOffsetReg = RegInit(0.U(headOffsetWidth.W))
  val shadowValidReg = RegInit(false.B)
  val prefetchBusyReg = RegInit(false.B)
  val prefetchDrainReg = RegInit(false.B)
  val prefetchToActiveReg = RegInit(false.B)
  val prefetchTokenIdxReg = Reg(UInt(log2Up(BATCHSIZE).W))
  val prefetchHeadIdxReg = Reg(UInt(head_cnt.getWidth.W))
  val prefetchStepReg = RegInit(0.U(log2Up(PREFETCH_STEPS).W))
  val prefetchSection = prefetchStepReg / HEAD_WORDS.U
  val prefetchChunk = prefetchStepReg % HEAD_WORDS.U
  val prefetchHeadElemBase = prefetchHeadIdxReg * HEAD_DIM.U
  val prefetchHeadWordBase = prefetchHeadElemBase / ROW.U
  val prefetchHeadOffset = prefetchHeadElemBase % ROW.U
  val prefetchWordIdx = prefetchSection * (768 / ROW).U + prefetchHeadWordBase + prefetchChunk
  val prefetchIssueFire = prefetchBusyReg && !prefetchDrainReg
  val prefetchReadWordIdx = prefetchWordIdx(log2Up(COLLECT_NUM) - 1, 0)
  val prefetchWord = vecBufferMem.read(
    vecBufferAddr(prefetchTokenIdxReg, prefetchReadWordIdx),
    prefetchIssueFire
  )
  val prefetchReadValidReg = RegNext(prefetchIssueFire, false.B)
  val prefetchReadLastReg = RegEnable(
    prefetchStepReg === (PREFETCH_STEPS - 1).U,
    false.B,
    prefetchIssueFire
  )
  val prefetchSectionReg = RegEnable(prefetchSection, 0.U(prefetchSection.getWidth.W), prefetchIssueFire)
  val prefetchChunkReg = RegEnable(prefetchChunk, 0.U(prefetchChunk.getWidth.W), prefetchIssueFire)
  val prefetchHeadOffsetReg = RegEnable(prefetchHeadOffset, 0.U(headOffsetWidth.W), prefetchIssueFire)
  val prefetchToActiveReadReg = RegEnable(prefetchToActiveReg, false.B, prefetchIssueFire)
  val startPriming = is_collecting && collectWriteEnableReg && collectVecReg === (COLLECT_NUM - 1).U
  val startShadowPrefetch =
    is_outputting &&
      io.data_out_ready &&
      output_cnt === 0.U &&
      !all_output_done &&
      !prefetchBusyReg &&
      !shadowValidReg

  when(prefetchReadValidReg) {
    switch(prefetchSectionReg) {
      is(0.U) {
        when(prefetchToActiveReadReg) {
          activeHeadQWordReg(prefetchChunkReg) := prefetchWord
        }.otherwise {
          shadowHeadQWordReg(prefetchChunkReg) := prefetchWord
        }
      }
      is(1.U) {
        when(prefetchToActiveReadReg) {
          activeHeadKWordReg(prefetchChunkReg) := prefetchWord
        }.otherwise {
          shadowHeadKWordReg(prefetchChunkReg) := prefetchWord
        }
      }
      is(2.U) {
        when(prefetchToActiveReadReg) {
          activeHeadVWordReg(prefetchChunkReg) := prefetchWord
        }.otherwise {
          shadowHeadVWordReg(prefetchChunkReg) := prefetchWord
        }
      }
    }
  }

  // 每周期输出 2 个元素
  val idx = (output_cnt << 1)(5, 0)
  val idx_plus1 = (idx + 1.U)(5, 0)
  def unpackHeadWords(words: Vec[UInt]): Vec[UInt] = {
    val elems = Wire(Vec(HEAD_WORDS * ROW, UInt(DATAW.W)))
    for (word <- 0 until HEAD_WORDS) {
      for (lane <- 0 until ROW) {
        elems(word * ROW + lane) := words(word)(DATAW * (lane + 1) - 1, DATAW * lane)
      }
    }
    elems
  }
  val qElems = unpackHeadWords(activeHeadQWordReg)
  val kElems = unpackHeadWords(activeHeadKWordReg)
  val vElems = unpackHeadWords(activeHeadVWordReg)
  val headWindowIdxWidth = log2Up(HEAD_WORDS * ROW)
  val elemIdx0 =
    (activeHeadOffsetReg.pad(headWindowIdxWidth) + idx.pad(headWindowIdxWidth))(headWindowIdxWidth - 1, 0)
  val elemIdx1 =
    (activeHeadOffsetReg.pad(headWindowIdxWidth) + idx_plus1.pad(headWindowIdxWidth))(headWindowIdxWidth - 1, 0)
  val out_data = Cat(
    vElems(elemIdx1), vElems(elemIdx0),      // V1, V0 (高 16 位)
    kElems(elemIdx1), kElems(elemIdx0),      // K1, K0 (中 16 位)
    qElems(elemIdx1), qElems(elemIdx0)       // Q1, Q0 (低 16 位)
  )

  when(prefetchIssueFire) {
    when(prefetchStepReg === (PREFETCH_STEPS - 1).U) {
      prefetchDrainReg := true.B
    }.otherwise {
      prefetchStepReg := prefetchStepReg + 1.U
    }
  }
  when(prefetchReadValidReg && prefetchReadLastReg) {
    prefetchBusyReg := false.B
    prefetchDrainReg := false.B
    prefetchStepReg := 0.U
    when(prefetchToActiveReadReg) {
      activeHeadOffsetReg := prefetchHeadOffsetReg
      state := outputting
    }.otherwise {
      shadowHeadOffsetReg := prefetchHeadOffsetReg
      shadowValidReg := true.B
    }
  }

  when(startPriming) {
    state := priming
    prefetchBusyReg := true.B
    prefetchDrainReg := false.B
    prefetchToActiveReg := true.B
    prefetchTokenIdxReg := 0.U
    prefetchHeadIdxReg := 0.U
    prefetchStepReg := 0.U
    shadowValidReg := false.B
  }

  when(startShadowPrefetch) {
    prefetchBusyReg := true.B
    prefetchDrainReg := false.B
    prefetchToActiveReg := false.B
    prefetchTokenIdxReg := nextTokenIdx
    prefetchHeadIdxReg := successorHeadIdx
    prefetchStepReg := 0.U
  }

  when(output_fire) {
    outputCntReg := Mux(output_last, 0.U, outputCntReg + 1.U)
    when(output_last) {
      when(!all_output_done) {
        assert(shadowValidReg, "QKV shadow prefetch was not ready at token boundary")
        activeHeadQWordReg := shadowHeadQWordReg
        activeHeadKWordReg := shadowHeadKWordReg
        activeHeadVWordReg := shadowHeadVWordReg
        activeHeadOffsetReg := shadowHeadOffsetReg
        shadowValidReg := false.B
      }
      when(is_prefill) {
        prefillCntReg := Mux(prefill_last, 0.U, prefillCntReg + 1.U)
      }.otherwise {
        batchCntReg := Mux(batch_last, 0.U, batchCntReg + 1.U)
      }
      when(token_last) {
        headCntReg := Mux(head_last, 0.U, headCntReg + 1.U)
      }
    }
  }

  // 所有数据输出完毕（所有 head 的所有 token）
  all_output_done := output_last && token_last && head_last

  // 状态机转换
  switch(state) {
    is(idle) {
      when(su_inst.io.data_out_valid) {
        state := collecting
      }
    }
    is(collecting) {
      when(startPriming) {
        state := priming
      }
    }
    is(priming) {
      when(!prefetchBusyReg) {
        state := outputting
      }
    }
    is(outputting) {
      when(all_output_done && output_fire) {
        state := idle
      }
    }
  }

  // 输出信号
  io.data_out := out_data
  io.data_out_valid := is_outputting
  // data_out_st should mark the first beat of each head stream, not the first
  // beat of every token inside that head. Otherwise DM1/VCache open a new write
  // bank on each token while only closing once per head.
  io.data_out_st := is_outputting && output_cnt === 0.U && current_token === 0.U
  io.data_out_head := head_cnt
  // data_out_last: 每个 head 的所有 token 输出完毕（不是 12 个 head 全部结束）
  io.data_out_last := is_outputting && output_last && token_last

  // 地址生成
  io.data_out_addr := Mux(
    is_prefill,
    prefill_cnt * OUTPUT_NUM.U + output_cnt,
    batch_cnt * OUTPUT_NUM.U + output_cnt
  )
}

object QKVLinearGen extends App {
  emitVerilog(new QKVLinear, Array("--target-dir", "generated"))
}
