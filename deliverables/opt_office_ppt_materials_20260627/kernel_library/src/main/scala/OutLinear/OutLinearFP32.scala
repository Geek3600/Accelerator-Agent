package OutLinear

import OutLinear.Param._
import QuantCommon.Fp32VecAdd
import QuantCommon.Precision._
import chisel3._
import chisel3.util._

class OutLinearFP32 extends Module {
  val io = IO(new Bundle() {
    val layer_st = Input(Bool())

    val data_in_st = Input(Bool())
    val data_in = Input(UInt(HEAD_WIDTH.W))
    val data_in_addr = Input(UInt(log2Up(MEM_DEPTH).W))
    val data_in_valid = Input(Bool())
    val data_in_last = Input(Bool())
    val data_ready = Output(Bool())

    val weight_init_mode = Input(Bool())
    val weight_init_data = Input(UInt(WMEM_WIDTH.W))
    val weight_init_addr = Output(UInt(log2Up(WMEM_DEPTH).W))
    val weight_active_bank = Input(Bool())
    val weight_preload_bank = Input(Bool())
    val weight_preload_valid = Input(Bool())
    val weight_preload_addr = Input(UInt(log2Up(WMEM_DEPTH).W))
    val weight_preload_data = Input(UInt(WMEM_WIDTH.W))
    val bias_init_data = Input(UInt(FP32_PACK_WIDTH.W))
    val bias_init_valid = Input(Bool())

    val out_scale = Input(UInt(FP32_WIDTH.W))

    val cfg_prefill = Input(Bool())
    val cfg_seqlen = Input(UInt(log2Up(MAX_SEQLEN).W))
    val cfg_valid = Input(Bool())

    val data_out = Output(UInt(FP32_PACK_WIDTH.W))
    val data_out_st = Output(Bool())
    val data_out_addr = Output(UInt(log2Up(MEM_DEPTH).W))
    val data_out_valid = Output(Bool())
    val data_out_last = Output(Bool())
    val data_out_ready = Input(Bool())
  })

  val is_prefill = RegEnable(io.cfg_prefill, io.cfg_valid)
  val seqlen = RegEnable(io.cfg_seqlen, io.cfg_valid)
  val actual_batchsize = Mux(is_prefill, seqlen, (BATCHSIZE - 1).U)

  val head_buffer = Reg(Vec(BATCHSIZE, Vec(HEAD_NUM, UInt(HEAD_WIDTH.W))))
  val head_cnt = RegInit(0.U(log2Up(HEAD_NUM).W))
  val head_last = head_cnt === (HEAD_NUM - 1).U
  val captureHeadIdx = Wire(UInt(log2Up(HEAD_NUM).W))
  captureHeadIdx := Mux(io.data_in_st, 0.U, head_cnt)
  val captureHeadLast = captureHeadIdx === (HEAD_NUM - 1).U
  val feed_token_cnt = RegInit(0.U(log2Up(BATCHSIZE).W))
  val feed_chunk_cnt = RegInit(0.U(log2Up(ROWBLOCK).W))
  val feed_token_last = feed_token_cnt === actual_batchsize
  val feed_chunk_last = feed_chunk_cnt === (ROWBLOCK - 1).U
  val singleTokenMode = actual_batchsize === 0.U
  // Decode can leave stale Attention beats queued after one 12-head burst.
  // Wait for one input gap before accepting a new burst so those tail beats
  // do not become a fake partial token.
  val awaitInputGap = RegInit(false.B)
  // Keep cfg_valid local to this front-end instead of letting a one-cycle pulse
  // directly fan out through the head-buffer capture gating.
  val cfgRestartPending = RegInit(false.B)
  // In single-query mode each cfg pulse should produce exactly one 12-head burst.
  // Later beats observed under the same cfg are duplicates and must be ignored.
  val decodeBurstSeen = RegInit(false.B)
  val pendingFeed = RegInit(false.B)
  val pendingFeedWait = RegInit(0.U(9.W))
  val pendingFeedTimeout = 255.U(pendingFeedWait.getWidth.W)
  val bypassActive = RegInit(false.B)
  val bypassChunkCnt = RegInit(0.U(log2Up(ROWBLOCK).W))
  val bypassChunkLast = bypassChunkCnt === (ROWBLOCK - 1).U

  val idle :: collecting :: feeding :: Nil = Enum(3)
  val state = RegInit(idle)
  val is_feeding = state === feeding
  val mem_inst = Module(new DataMem(MEM_DEPTH, MEM_WIDTH))
  val lu_inst = Module(new LoadUnit)
  val cu_inst = Module(new CUFP32)
  val su_inst = Module(new StoreUnitFP32)
  val lw_inst = Module(new LoadWeight)
  val bias_mem = Reg(Vec(COL_W / ROW, UInt(FP32_PACK_WIDTH.W)))
  val bias_init_cnt = RegInit(0.U(log2Up(COL_W / ROW).W))
  val token_addr = io.data_in_addr(log2Up(BATCHSIZE) - 1, 0)
  val captureTokenAddr = Mux(singleTokenMode, 0.U(token_addr.getWidth.W), token_addr)
  val captureHeadAddr = io.data_in_addr(log2Up(HEAD_NUM) - 1, 0)
  val captureWriteEnableReg = RegInit(false.B)
  captureWriteEnableReg.suggestName("captureWriteEnableReg")
  val captureDataReg = Reg(UInt(HEAD_WIDTH.W))
  captureDataReg.suggestName("captureDataReg")
  val captureTokenReg = Reg(UInt(captureTokenAddr.getWidth.W))
  captureTokenReg.suggestName("captureTokenReg")
  val captureSlotReg = Reg(UInt(log2Up(HEAD_NUM).W))
  captureSlotReg.suggestName("captureSlotReg")
  val decodeBurstAligned = !singleTokenMode || state =/= idle || io.data_in_st
  // The input-side head buffer is independent from the backend mem/LU drain.
  // Once the front-end collection state leaves `feeding`, the next token's
  // burst can start buffering immediately even if the previous token is still
  // retiring through LoadUnit/DataMem.
  val acceptReady = !is_feeding && !bypassActive
  // A new decode token can arrive back-to-back with no input bubble. Allow the
  // next cfg pulse / start beat to reopen capture immediately instead of
  // draining it as a stale duplicate under the previous token's gap guard.
  val captureWindowOpen = !awaitInputGap || cfgRestartPending || io.data_in_st
  val decodeBurstFresh = !singleTokenMode || !decodeBurstSeen || cfgRestartPending || io.data_in_st
  val decodeCaptureReady = decodeBurstAligned
  val captureReady = Mux(singleTokenMode, decodeCaptureReady, captureWindowOpen && decodeBurstFresh && decodeBurstAligned)
  val acceptInput = io.data_in_valid && acceptReady
  val captureInput = acceptInput && captureReady
  val captureSlot = Mux(singleTokenMode, captureHeadAddr, captureHeadIdx)
  val captureSlotLast = captureSlot === (HEAD_NUM - 1).U
  val captureBurstDone = captureInput && Mux(singleTokenMode, captureSlotLast, io.data_in_last && captureSlotLast)

  when(io.cfg_valid) {
    cfgRestartPending := true.B
  }.elsewhen(captureInput && io.data_in_st) {
    cfgRestartPending := false.B
  }

  when(cfgRestartPending || (singleTokenMode && io.data_in_valid && io.data_in_st)) {
    decodeBurstSeen := false.B
  }

  when(io.bias_init_valid) {
    bias_mem(bias_init_cnt) := io.bias_init_data
    bias_init_cnt := Mux(bias_init_cnt === (COL_W / ROW - 1).U, 0.U, bias_init_cnt + 1.U)
  }

  captureWriteEnableReg := captureInput
  when(captureInput) {
    captureDataReg := io.data_in
    captureTokenReg := captureTokenAddr
    captureSlotReg := captureSlot
  }
  // Register the wide head-buffer write controls once before they fan out to
  // all token/head banks. This cuts the long CE path seen in post-route timing.
  when(captureWriteEnableReg) {
    head_buffer(captureTokenReg)(captureSlotReg) := captureDataReg
  }

  when(awaitInputGap && !io.data_in_valid) {
    awaitInputGap := false.B
  }

  when(io.cfg_valid) {
    pendingFeed := false.B
    pendingFeedWait := 0.U
  }.elsewhen(singleTokenMode && state === idle && pendingFeed && !captureInput) {
    pendingFeedWait := Mux(
      pendingFeedWait === pendingFeedTimeout,
      pendingFeedWait,
      pendingFeedWait + 1.U
    )
  }.elsewhen(captureInput || state === feeding || !pendingFeed) {
    pendingFeedWait := 0.U
  }

  switch(state) {
    is(idle) {
      when(singleTokenMode && pendingFeed && pendingFeedWait === pendingFeedTimeout && !io.data_in_valid) {
        bypassActive := true.B
        pendingFeed := false.B
        feed_token_cnt := 0.U
        feed_chunk_cnt := 0.U
        head_cnt := 0.U
      }.elsewhen(captureInput) {
        pendingFeed := false.B
        when(io.data_in_st) {
          head_cnt := 0.U
        }
        state := Mux(captureBurstDone, Mux(singleTokenMode, idle, feeding), collecting)
        when(captureBurstDone) {
          awaitInputGap := true.B
          when(singleTokenMode) {
            decodeBurstSeen := true.B
            pendingFeed := true.B
            pendingFeedWait := 0.U
            head_cnt := 0.U
          }.otherwise {
            head_cnt := 0.U
            feed_token_cnt := 0.U
            feed_chunk_cnt := 0.U
          }
        }.otherwise {
          head_cnt := captureSlot + 1.U
        }
      }
    }
    is(collecting) {
      when(captureInput) {
        when(captureBurstDone) {
          state := Mux(singleTokenMode, idle, feeding)
          awaitInputGap := true.B
          when(singleTokenMode) {
            decodeBurstSeen := true.B
            pendingFeed := true.B
            pendingFeedWait := 0.U
            head_cnt := 0.U
          }.otherwise {
            head_cnt := 0.U
            feed_token_cnt := 0.U
            feed_chunk_cnt := 0.U
          }
        }.otherwise {
          head_cnt := captureSlot + 1.U
        }
      }
    }
    is(feeding) {
      when(mem_inst.io.w_ready) {
        when(feed_chunk_last) {
          feed_chunk_cnt := 0.U
          when(feed_token_last) {
            state := idle
            feed_token_cnt := 0.U
          }.otherwise {
            feed_token_cnt := feed_token_cnt + 1.U
          }
        }.otherwise {
          feed_chunk_cnt := feed_chunk_cnt + 1.U
        }
      }
    }
  }

  when(bypassActive && io.data_out_ready) {
    when(bypassChunkLast) {
      bypassActive := false.B
      bypassChunkCnt := 0.U
    }.otherwise {
      bypassChunkCnt := bypassChunkCnt + 1.U
    }
  }

  val token_heads = head_buffer(feed_token_cnt)
  val full_token_vec = Wire(Vec(ROW_W, UInt(DATAW.W)))
  for (h <- 0 until HEAD_NUM) {
    val head_vec = token_heads(h).asTypeOf(Vec(HEAD_DIM, UInt(DATAW.W)))
    for (i <- 0 until HEAD_DIM) {
      full_token_vec(h * HEAD_DIM + i) := head_vec(i)
    }
  }

  val token_chunks = Wire(Vec(ROWBLOCK, UInt(MEM_WIDTH.W)))
  for (c <- 0 until ROWBLOCK) {
    token_chunks(c) := Cat((0 until ROW).reverse.map(i => full_token_vec(c * ROW + i)))
  }

  val mem_write_valid = is_feeding && mem_inst.io.w_ready
  val mem_write_addr = feed_token_cnt * ROWBLOCK.U + feed_chunk_cnt
  val mem_write_last = feed_chunk_last && feed_token_last
  val mem_write_st = feed_token_cnt === 0.U && feed_chunk_cnt === 0.U

  mem_inst.io.w_st := mem_write_valid && mem_write_st
  mem_inst.io.w_last := mem_write_last
  mem_inst.io.w_data := token_chunks(feed_chunk_cnt)
  mem_inst.io.w_addr := mem_write_addr
  mem_inst.io.w_valid := mem_write_valid

  mem_inst.io.r_last := lu_inst.io.data_in_last
  mem_inst.io.r_addr := lu_inst.io.data_in_addr
  mem_inst.io.r_en := lu_inst.io.read_en

  lu_inst.io.data_in := mem_inst.io.r_data
  lu_inst.io.data_in_ready := mem_inst.io.r_ready
  lu_inst.io.data_out_ready := io.data_out_ready
  lu_inst.io.cfg_prefill := io.cfg_prefill
  lu_inst.io.cfg_seqlen := io.cfg_seqlen
  lu_inst.io.cfg_valid := io.cfg_valid
  lu_inst.io.weight_ready := lw_inst.io.weight_ready

  cu_inst.io.data_in := lu_inst.io.data_out
  cu_inst.io.data_in_valid := lu_inst.io.data_out_valid
  cu_inst.io.w_data := lw_inst.io.data_out
  cu_inst.io.w_data_sel := lw_inst.io.data_out_sel
  cu_inst.io.w_valid := lw_inst.io.data_out_valid
  cu_inst.io.out_scale := io.out_scale
  cu_inst.io.cfg_prefill := io.cfg_prefill
  cu_inst.io.cfg_seqlen := io.cfg_seqlen
  cu_inst.io.cfg_valid := io.cfg_valid

  su_inst.io.data_in := cu_inst.io.data_out
  su_inst.io.data_in_valid := cu_inst.io.data_out_valid
  su_inst.io.cfg_prefill := io.cfg_prefill
  su_inst.io.cfg_seqlen := io.cfg_seqlen
  su_inst.io.cfg_valid := io.cfg_valid

  lw_inst.io.update := cu_inst.io.w_update
  lw_inst.io.st := io.layer_st || lu_inst.io.data_out_start
  lw_inst.io.init_mode := io.weight_init_mode
  lw_inst.io.init_data := io.weight_init_data
  lw_inst.io.active_bank := io.weight_active_bank
  lw_inst.io.preload_valid := io.weight_preload_valid
  lw_inst.io.preload_bank := io.weight_preload_bank
  lw_inst.io.preload_addr := io.weight_preload_addr
  lw_inst.io.preload_data := io.weight_preload_data

  io.data_ready := acceptReady
  io.weight_init_addr := lw_inst.io.init_addr

  val bias_add = Module(new Fp32VecAdd)
  bias_add.io.a := su_inst.io.data_out
  bias_add.io.b := bias_mem(su_inst.io.data_out_addr(log2Up(COL_W / ROW) - 1, 0))

  io.data_out := Mux(bypassActive, 0.U(FP32_PACK_WIDTH.W), bias_add.io.out)
  io.data_out_valid := Mux(bypassActive, true.B, su_inst.io.data_out_valid)
  io.data_out_addr := Mux(bypassActive, bypassChunkCnt, su_inst.io.data_out_addr)
  io.data_out_st := Mux(bypassActive, bypassChunkCnt === 0.U, su_inst.io.data_out_st)
  io.data_out_last := Mux(bypassActive, bypassChunkLast, su_inst.io.data_out_last)
}

object OutLinearFP32Gen extends App {
  emitVerilog(new OutLinearFP32, Array("--target-dir", "generated"))
}
