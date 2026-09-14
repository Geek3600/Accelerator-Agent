import DM.Param._
import LayerNormQ.LayerNormQ
import QuantCommon.Precision._
import QuantCommon.FpBackend
import Softmax.Param.{WMEM_DEPTH => SM_WMEM_DEPTH, WMEM_WIDTH => SM_WMEM_WIDTH}
import QKVLinear.{QKVLinear, Param => QKVParam}
import OutLinear.{OutLinearFP32, Param => OutParam}
import ResAdd.ResAddFP32
import ResAdd.FP32Param.{DATA_WIDTH => RES_DATA_WIDTH, MEM_DEPTH => RES_MEM_DEPTH}
import FFNUp.{FFNUp, Param => FFNUpParam}
import FFNDown.{FFNDownFP32, Param => FFNDownParam}
import ResAdd2.ResAdd2FP32
import TempAdapter.LNAddrGen
import TempAdapter.Param.{MAX_SEQLEN => CORE_MAX_SEQLEN}
import chisel3._
import chisel3.util._
import java.nio.charset.StandardCharsets
import java.nio.file.{Files, Path, Paths, StandardCopyOption}

// 顶层模块：整合完整的 Transformer Block 流水线
// 数据流:
// 输入 -> LayerNorm -> QKVLinear -> Atten -> OutLinear -> ResAdd (S7)
//          └────────────────────────────────────────────────────────┘ 残差1
//                                                                    ↓
//                                              LayerNorm2 (S8) -> FFNUp(ReLU fused) -> FFNDown -> ResAdd2 -> 输出
//                                                                                                                  ↑
//                                                                                                            S7 输出
class Top extends Module{
  val io = IO(new Bundle() {
    val layer_st = Input(Bool())
    val cfg_seqlen = Input(UInt(log2Up(CORE_MAX_SEQLEN).W))
    val cfg_prefill = Input(Bool())
    val cfg_valid = Input(Bool())

    // Attention 单独配置口。
    // 默认可与整机 cfg_* 保持一致；后续做长序列 token-by-token 调度时，
    // 允许保持非 attention 路径按单 token 运行，而让 attention 单独看到历史长度。
    val attn_cfg_seqlen = Input(UInt(16.W))
    val attn_cfg_prefill = Input(Bool())
    val attn_cfg_valid = Input(Bool())
    val attn_cfg_single_query = Input(Bool())

    // 权重初始化模式控制
    val weight_init_mode = Input(Bool())  // true: 初始化模式, false: 计算模式
    val weight_active_bank = Input(Bool())
    val weight_preload_bank = Input(Bool())

    // 输入: 12 x FP32
    val data_in = Input(UInt(FP32_PACK_WIDTH.W))
    val data_in_ready = Input(Bool())
    val data_in_addr = Output(UInt(32.W))

    // 为后续 wrapper 侧 K/V history 捕获预留的内部 tap。
    // 这些口不改变外部 sample 工程接口，只把 QKV -> Attention 的原始流显式暴露出来。
    val attn_tap_data = Output(UInt(48.W))
    val attn_tap_head = Output(UInt(4.W))
    val attn_tap_addr = Output(UInt(32.W))
    val attn_tap_valid = Output(Bool())
    val attn_tap_last = Output(Bool())

    // 更细粒度的 long-seq history source 接口：
    // 不再要求 wrapper 接管整个 Attention 输入，
    // 而是只在真正需要外移长历史的消费者侧替换数据源。
    val attn_dm1_override_enable = Input(Bool())
    val attn_dm1_override_data = Input(UInt((2 * LOAD_VECNUM * DATAW).W))
    val attn_dm1_override_st = Input(Bool())
    val attn_dm1_override_addr = Input(UInt(log2Up(HEAD_VECNUM / LOAD_VECNUM * BATCHSIZE).W))
    val attn_dm1_override_valid = Input(Bool())
    val attn_dm1_override_last = Input(Bool())
    val attn_dm1_override_ready = Output(Bool())

    val attn_dm2_v_override_enable = Input(Bool())
    val attn_dm2_v_override_data = Input(UInt((DM2.Param.HEAD_VECNUM * DM2.Param.DATAW).W))
    val attn_dm2_v_override_valid = Input(Bool())
    val attn_dm2_v_override_ready = Output(Bool())

    // LayerNorm 权重输入
    val ln_w_in = Input(UInt(FP32_PACK_WIDTH.W))
    val ln_w_valid = Input(Bool())

    // 量化参数
    val ln1_out_inv_scale = Input(UInt(FP32_WIDTH.W))
    val ln1_out_zero_point = Input(SInt(INT8_WIDTH.W))
    val q_out_inv_scale = Input(UInt(FP32_WIDTH.W))
    val k_out_inv_scale = Input(UInt(FP32_WIDTH.W))
    val v_out_inv_scale = Input(UInt(FP32_WIDTH.W))
    val q_bias_scale = Input(UInt(FP32_WIDTH.W))
    val k_bias_scale = Input(UInt(FP32_WIDTH.W))
    val v_bias_scale = Input(UInt(FP32_WIDTH.W))
    val dm1_out_scale = Input(UInt(FP32_WIDTH.W))
    val dm2_ctx_inv_scale = Input(UInt(FP32_WIDTH.W))
    val dm2_ctx_zero_point = Input(UInt(UINT8_WIDTH.W))
    val dm2_out_inv_scale = Input(UInt(FP32_WIDTH.W))
    val out_out_scale = Input(UInt(FP32_WIDTH.W))
    val ln2_out_inv_scale = Input(UInt(FP32_WIDTH.W))
    val ln2_out_zero_point = Input(SInt(INT8_WIDTH.W))
    val ffnup_out_inv_scale = Input(UInt(FP32_WIDTH.W))
    val ffnup_bias_scale = Input(UInt(FP32_WIDTH.W))
    val ffndown_out_scale = Input(UInt(FP32_WIDTH.W))

    // QKVLinear 权重、bias输入/初始化
    val qkv_w_in = Input(UInt(QKVParam.WMEM_WIDTH.W))
    val qkv_w_addr = Output(UInt(log2Up(QKVParam.WMEM_DEPTH).W))
    val qkv_w_preload_valid = Input(Bool())
    val qkv_w_preload_addr = Input(UInt(log2Up(QKVParam.WMEM_DEPTH).W))
    val qkv_w_preload_data = Input(UInt(QKVParam.WMEM_WIDTH.W))
    val qkv_b_in = Input(UInt(QKVParam.MEM_WIDTH.W))
    val qkv_b_valid = Input(Bool())

    // Softmax 权重输入
    val sm_w_in = Input(UInt(SM_WMEM_WIDTH.W))
    val sm_w_addr = Output(UInt(log2Up(SM_WMEM_DEPTH).W))

    // OutLinear 权重输入/初始化
    val out_w_in = Input(UInt(OutParam.WMEM_WIDTH.W))
    val out_w_addr = Output(UInt(log2Up(OutParam.WMEM_DEPTH).W))
    val out_w_preload_valid = Input(Bool())
    val out_w_preload_addr = Input(UInt(log2Up(OutParam.WMEM_DEPTH).W))
    val out_w_preload_data = Input(UInt(OutParam.WMEM_WIDTH.W))
    val out_b_in = Input(UInt(FP32_PACK_WIDTH.W))
    val out_b_valid = Input(Bool())

    // LayerNorm2 权重输入
    val ln2_w_in = Input(UInt(FP32_PACK_WIDTH.W))
    val ln2_w_valid = Input(Bool())

    // FFNUp 权重输入/初始化
    val ffnup_w_in = Input(UInt(FFNUpParam.WMEM_WIDTH.W))
    val ffnup_w_addr = Output(UInt(log2Up(FFNUpParam.WMEM_DEPTH).W))
    val ffnup_w_preload_valid = Input(Bool())
    val ffnup_w_preload_addr = Input(UInt(log2Up(FFNUpParam.WMEM_DEPTH).W))
    val ffnup_w_preload_data = Input(UInt(FFNUpParam.WMEM_WIDTH.W))
    val ffnup_b_in = Input(UInt(FFNUpParam.MEM_WIDTH.W))
    val ffnup_b_valid = Input(Bool())

    // FFNDown 权重输入/初始化
    val ffndown_w_in = Input(UInt(FFNDownParam.WMEM_WIDTH.W))
    val ffndown_w_addr = Output(UInt(log2Up(FFNDownParam.WMEM_DEPTH).W))
    val ffndown_w_preload_valid = Input(Bool())
    val ffndown_w_preload_addr = Input(UInt(log2Up(FFNDownParam.WMEM_DEPTH).W))
    val ffndown_w_preload_data = Input(UInt(FFNDownParam.WMEM_WIDTH.W))
    val ffndown_b_in = Input(UInt(FP32_PACK_WIDTH.W))
    val ffndown_b_valid = Input(Bool())

    // 输出 (ResAdd2 输出格式: 96-bit)
    val res = Output(UInt(RES_DATA_WIDTH.W))
    val res_st = Output(Bool())
    val res_addr = Output(UInt(log2Up(RES_MEM_DEPTH).W))
    val res_valid = Output(Bool())
    val res_last = Output(Bool())
    val res_ready = Input(Bool())
  })

  // ========================================
  // 模块实例化 - 按流水级顺序
  // ========================================
  val ln_addr_gen = Module(new LNAddrGen)     // 地址生成
  val layernorm = Module(new LayerNormQ)       // S1: LayerNorm
  val qkvlinear = Module(new QKVLinear)       // S2: QKV 映射
  val atten = Module(new Atten)               // S3-6: Attention
  val outlinear = Module(new OutLinearFP32)       // S7: 输出映射
  val attnToOutQ = Module(new Queue(new Bundle {
    val data = UInt((DM2.Param.HEAD_VECNUM * DM2.Param.DATAW).W)
    val st = Bool()
    val addr = UInt(atten.io.res_addr.getWidth.W)
    val last = Bool()
  }, OutParam.HEAD_NUM, pipe = true, flow = false, useSyncReadMem = false))
  val resadd = Module(new ResAddFP32)             // S7-Res: 残差连接 1
  val layernorm2 = Module(new LayerNormQ)      // S8: LayerNorm2
  val ffnup = Module(new FFNUp)               // S9: FFN Up (H→4H, ReLU fused)
  val ffndown = Module(new FFNDownFP32)           // S10: FFN Down (4H→H)
  val resadd2 = Module(new ResAdd2FP32)           // S12: 残差连接 2

  // ========================================
  // LNAddrGen 连接
  // ========================================
  val input_adapter_ready = Wire(Bool())
  ln_addr_gen.io.cfg_seqlen := io.cfg_seqlen
  ln_addr_gen.io.cfg_prefill := io.cfg_prefill
  ln_addr_gen.io.cfg_valid := io.cfg_valid
  ln_addr_gen.io.data_ready := io.data_in_ready
  ln_addr_gen.io.adapter_ready := input_adapter_ready
  io.data_in_addr := ln_addr_gen.io.mem_addr

  // ========================================
  // LayerNorm 连接 (S1)
  // ========================================
  layernorm.io.data_in := io.data_in
  layernorm.io.data_in_st := ln_addr_gen.io.data_st
  layernorm.io.data_addr := ln_addr_gen.io.data_addr
  layernorm.io.data_valid := ln_addr_gen.io.data_valid
  layernorm.io.data_last := ln_addr_gen.io.data_last

  layernorm.io.w_in := io.ln_w_in
  layernorm.io.w_valid := io.ln_w_valid
  layernorm.io.out_inv_scale := io.ln1_out_inv_scale
  layernorm.io.out_zero_point := io.ln1_out_zero_point
  layernorm.io.res_ready := qkvlinear.io.data_ready

  // ========================================
  // QKVLinear 连接 (S2)
  // ========================================
  qkvlinear.io.layer_st := io.layer_st

  qkvlinear.io.data_in := layernorm.io.res
  qkvlinear.io.data_in_st := layernorm.io.res_st
  qkvlinear.io.data_addr := layernorm.io.res_addr
  qkvlinear.io.data_valid := layernorm.io.res_valid
  qkvlinear.io.data_last := layernorm.io.res_last

  // 权重初始化接口
  qkvlinear.io.weight_init_mode := io.weight_init_mode
  qkvlinear.io.weight_init_data := io.qkv_w_in
  qkvlinear.io.weight_active_bank := io.weight_active_bank
  qkvlinear.io.weight_preload_bank := io.weight_preload_bank
  qkvlinear.io.weight_preload_valid := io.qkv_w_preload_valid
  qkvlinear.io.weight_preload_addr := io.qkv_w_preload_addr
  qkvlinear.io.weight_preload_data := io.qkv_w_preload_data
  qkvlinear.io.bias_init_data := io.qkv_b_in
  qkvlinear.io.bias_init_valid := io.qkv_b_valid
  qkvlinear.io.q_out_inv_scale := io.q_out_inv_scale
  qkvlinear.io.k_out_inv_scale := io.k_out_inv_scale
  qkvlinear.io.v_out_inv_scale := io.v_out_inv_scale
  qkvlinear.io.q_bias_scale := io.q_bias_scale
  qkvlinear.io.k_bias_scale := io.k_bias_scale
  qkvlinear.io.v_bias_scale := io.v_bias_scale
  val qkvToAttnQ = Module(new Queue(new Bundle {
    val data = UInt(48.W)
    val st = Bool()
    val head = UInt(qkvlinear.io.data_out_head.getWidth.W)
    val addr = UInt(32.W)
    val last = Bool()
  }, 2, pipe = true, flow = false))
  qkvToAttnQ.suggestName("qkvToAttnQ")
  qkvlinear.io.data_out_ready := qkvToAttnQ.io.enq.ready
  qkvToAttnQ.io.enq.valid := qkvlinear.io.data_out_valid
  qkvToAttnQ.io.enq.bits.data := qkvlinear.io.data_out
  qkvToAttnQ.io.enq.bits.st := qkvlinear.io.data_out_st
  qkvToAttnQ.io.enq.bits.head := qkvlinear.io.data_out_head
  qkvToAttnQ.io.enq.bits.addr := qkvlinear.io.data_out_addr
  qkvToAttnQ.io.enq.bits.last := qkvlinear.io.data_out_last
  qkvToAttnQ.io.deq.ready := atten.io.data_ready

  io.qkv_w_addr := qkvlinear.io.weight_init_addr
  val attnTapFire = qkvToAttnQ.io.deq.valid && atten.io.data_ready
  val attnTapDataReg = Reg(UInt(48.W))
  val attnTapHeadReg = Reg(UInt(qkvlinear.io.data_out_head.getWidth.W))
  val attnTapAddrReg = Reg(UInt(32.W))
  val attnTapLastReg = RegInit(false.B)
  val attnTapValidReg = RegInit(false.B)
  when(attnTapFire) {
    attnTapDataReg := qkvToAttnQ.io.deq.bits.data
    attnTapHeadReg := qkvToAttnQ.io.deq.bits.head
    attnTapAddrReg := qkvToAttnQ.io.deq.bits.addr
    attnTapLastReg := qkvToAttnQ.io.deq.bits.last
  }
  attnTapValidReg := attnTapFire
  io.attn_tap_data := attnTapDataReg
  io.attn_tap_head := attnTapHeadReg
  io.attn_tap_addr := attnTapAddrReg
  io.attn_tap_valid := attnTapValidReg
  io.attn_tap_last := attnTapLastReg && attnTapValidReg

  // ========================================
  // Attention 连接 (S3-6)
  // ========================================
  val coreCfgSeqlenWide = Wire(UInt(16.W))
  coreCfgSeqlenWide := io.cfg_seqlen
  val attnCfgValid = io.attn_cfg_valid || io.cfg_valid
  val attnCfgSeqlenFull = Mux(io.attn_cfg_valid, io.attn_cfg_seqlen, coreCfgSeqlenWide)
  val attnCfgPrefillNow = Mux(io.attn_cfg_valid, io.attn_cfg_prefill, io.cfg_prefill)
  val attnSingleQueryNow = Mux(io.attn_cfg_valid, io.attn_cfg_single_query, false.B)
  val attnCfgSeqlenHold = RegEnable(attnCfgSeqlenFull, 0.U(16.W), attnCfgValid)
  val attnCfgPrefillHold = RegEnable(attnCfgPrefillNow, false.B, attnCfgValid)
  val attnSingleQueryHold = RegEnable(attnSingleQueryNow, false.B, attnCfgValid)
  val attnCfgSeqlen =
    Mux(attnCfgValid, attnCfgSeqlenFull, attnCfgSeqlenHold)(log2Up(DM.Param.MAX_SEQLEN) - 1, 0)
  val attnCfgPrefill = Mux(attnCfgValid, attnCfgPrefillNow, attnCfgPrefillHold)
  val attnSingleQuery = Mux(attnCfgValid, attnSingleQueryNow, attnSingleQueryHold)

  qkvlinear.io.cfg_seqlen := attnCfgSeqlen
  qkvlinear.io.cfg_prefill := attnCfgPrefill
  qkvlinear.io.cfg_valid := attnCfgValid
  qkvlinear.io.cfg_single_query := attnSingleQuery

  atten.io.cfg_valid := attnCfgValid
  atten.io.cfg_prefill := attnCfgPrefill
  atten.io.cfg_seqlen := attnCfgSeqlen
  atten.io.cfg_single_query := attnSingleQuery
  atten.io.layer_st := io.layer_st
  atten.io.dm1_out_scale := io.dm1_out_scale
  atten.io.dm2_ctx_inv_scale := io.dm2_ctx_inv_scale
  atten.io.dm2_ctx_zero_point := io.dm2_ctx_zero_point
  atten.io.dm2_out_inv_scale := io.dm2_out_inv_scale
  atten.io.w_in := io.sm_w_in

  atten.io.data_in_st := qkvToAttnQ.io.deq.bits.st
  atten.io.data_in := qkvToAttnQ.io.deq.bits.data
  atten.io.data_addr := qkvToAttnQ.io.deq.bits.addr
  atten.io.data_valid := qkvToAttnQ.io.deq.valid
  atten.io.data_last := qkvToAttnQ.io.deq.bits.last
  atten.io.dm1_override_enable := io.attn_dm1_override_enable
  atten.io.dm1_override_data := io.attn_dm1_override_data
  atten.io.dm1_override_st := io.attn_dm1_override_st
  atten.io.dm1_override_addr := io.attn_dm1_override_addr
  atten.io.dm1_override_valid := io.attn_dm1_override_valid
  atten.io.dm1_override_last := io.attn_dm1_override_last
  atten.io.dm2_v_override_enable := io.attn_dm2_v_override_enable
  atten.io.dm2_v_override_data := io.attn_dm2_v_override_data
  atten.io.dm2_v_override_valid := io.attn_dm2_v_override_valid
  atten.io.res_ready := attnToOutQ.io.enq.ready
  io.attn_dm1_override_ready := atten.io.dm1_override_ready
  io.attn_dm2_v_override_ready := atten.io.dm2_v_override_ready

  io.sm_w_addr := atten.io.w_addr

  attnToOutQ.io.enq.valid := atten.io.res_valid
  attnToOutQ.io.enq.bits.data := atten.io.res
  attnToOutQ.io.enq.bits.st := atten.io.res_st
  attnToOutQ.io.enq.bits.addr := atten.io.res_addr
  attnToOutQ.io.enq.bits.last := atten.io.res_last
  attnToOutQ.io.deq.ready := outlinear.io.data_ready

  // ========================================
  // OutLinear 连接 (S7)
  // ========================================
  outlinear.io.layer_st := io.layer_st
  outlinear.io.cfg_seqlen := io.cfg_seqlen
  outlinear.io.cfg_prefill := io.cfg_prefill
  outlinear.io.cfg_valid := io.cfg_valid

  outlinear.io.data_in := attnToOutQ.io.deq.bits.data
  outlinear.io.data_in_st := attnToOutQ.io.deq.bits.st
  outlinear.io.data_in_addr := attnToOutQ.io.deq.bits.addr
  outlinear.io.data_in_valid := attnToOutQ.io.deq.valid
  outlinear.io.data_in_last := attnToOutQ.io.deq.bits.last

  outlinear.io.weight_init_mode := io.weight_init_mode
  outlinear.io.weight_init_data := io.out_w_in
  outlinear.io.weight_active_bank := io.weight_active_bank
  outlinear.io.weight_preload_bank := io.weight_preload_bank
  outlinear.io.weight_preload_valid := io.out_w_preload_valid
  outlinear.io.weight_preload_addr := io.out_w_preload_addr
  outlinear.io.weight_preload_data := io.out_w_preload_data
  outlinear.io.bias_init_data := io.out_b_in
  outlinear.io.bias_init_valid := io.out_b_valid
  outlinear.io.out_scale := io.out_out_scale
  io.out_w_addr := outlinear.io.weight_init_addr

  val outToResQ = Module(new Queue(new Bundle {
    val data = UInt(FP32_PACK_WIDTH.W)
    val st = Bool()
    val addr = UInt(log2Up(RES_MEM_DEPTH).W)
    val last = Bool()
  }, RES_MEM_DEPTH, false, false, true))

  outToResQ.io.enq.valid := outlinear.io.data_out_valid
  outToResQ.io.enq.bits.data := outlinear.io.data_out
  outToResQ.io.enq.bits.st := outlinear.io.data_out_st
  outToResQ.io.enq.bits.addr := outlinear.io.data_out_addr(log2Up(RES_MEM_DEPTH) - 1, 0)
  outToResQ.io.enq.bits.last := outlinear.io.data_out_last
  outlinear.io.data_out_ready := outToResQ.io.enq.ready

  // ========================================
  // ResAdd 连接 (S7-Res: 残差连接 1)
  // ========================================
  resadd.io.cfg_seqlen := io.cfg_seqlen
  resadd.io.cfg_prefill := io.cfg_prefill
  resadd.io.cfg_valid := io.cfg_valid

  resadd.io.orig_in := RegNext(io.data_in, 0.U(FP32_PACK_WIDTH.W))
  resadd.io.orig_in_st := RegNext(ln_addr_gen.io.data_st, false.B)
  resadd.io.orig_in_addr := RegNext(ln_addr_gen.io.mem_addr(log2Up(RES_MEM_DEPTH) - 1, 0), 0.U)
  resadd.io.orig_in_valid := RegNext(ln_addr_gen.io.data_valid, false.B)
  resadd.io.orig_in_last := RegNext(ln_addr_gen.io.data_last, false.B)

  resadd.io.dm2_in := outToResQ.io.deq.bits.data
  resadd.io.dm2_in_st := outToResQ.io.deq.bits.st
  resadd.io.dm2_in_addr := outToResQ.io.deq.bits.addr
  resadd.io.dm2_in_valid := outToResQ.io.deq.valid
  resadd.io.dm2_in_last := outToResQ.io.deq.bits.last
  outToResQ.io.deq.ready := resadd.io.dm2_ready
  // ResAdd 输出需要同时送给 LayerNorm2 和 ResAdd2，反压信号取 AND
  resadd.io.res_ready := layernorm2.io.data_ready && resadd2.io.s7_ready
  // 原始输入会同时送到 LayerNorm 和 ResAdd residual-cache，两个分叉必须共享同一个 ready。
  // 否则当 ResAdd cache 满时，这一路会静默丢 beat，后续读到未写槽位并在 LN2 处放大成 NaN。
  // In short-seq/prefill mode we want LNAddrGen to keep streaming the full
  // sequence into the front-end staging memories instead of stopping after
  // LayerNorm leaves idle for the first token.
  input_adapter_ready := Mux(io.cfg_prefill, resadd.io.orig_ready, layernorm.io.data_ready && resadd.io.orig_ready)

  // ========================================
  // LayerNorm2 连接 (S8: 第二个层归一化)
  // ========================================
  layernorm2.io.data_in := resadd.io.res
  layernorm2.io.data_in_st := resadd.io.res_st
  layernorm2.io.data_addr := resadd.io.res_addr
  layernorm2.io.data_valid := resadd.io.res_valid
  layernorm2.io.data_last := resadd.io.res_last

  layernorm2.io.w_in := io.ln2_w_in
  layernorm2.io.w_valid := io.ln2_w_valid
  layernorm2.io.out_inv_scale := io.ln2_out_inv_scale
  layernorm2.io.out_zero_point := io.ln2_out_zero_point
  layernorm2.io.res_ready := ffnup.io.data_ready

  // ========================================
  // FFNUp 连接 (S9: H→4H 线性投影)
  // ========================================
  ffnup.io.layer_st := io.layer_st
  ffnup.io.cfg_seqlen := io.cfg_seqlen
  ffnup.io.cfg_prefill := io.cfg_prefill
  ffnup.io.cfg_valid := io.cfg_valid

  ffnup.io.data_in := layernorm2.io.res
  ffnup.io.data_in_st := layernorm2.io.res_st
  ffnup.io.data_addr := layernorm2.io.res_addr
  ffnup.io.data_valid := layernorm2.io.res_valid
  ffnup.io.data_last := layernorm2.io.res_last

  ffnup.io.weight_init_mode := io.weight_init_mode
  ffnup.io.weight_init_data := io.ffnup_w_in
  ffnup.io.weight_active_bank := io.weight_active_bank
  ffnup.io.weight_preload_bank := io.weight_preload_bank
  ffnup.io.weight_preload_valid := io.ffnup_w_preload_valid
  ffnup.io.weight_preload_addr := io.ffnup_w_preload_addr
  ffnup.io.weight_preload_data := io.ffnup_w_preload_data
  ffnup.io.bias_init_data := io.ffnup_b_in
  ffnup.io.bias_init_valid := io.ffnup_b_valid
  ffnup.io.out_inv_scale := io.ffnup_out_inv_scale
  ffnup.io.bias_scale := io.ffnup_bias_scale
  val ffnUpToDownQ = Module(new Queue(new Bundle {
    val data = UInt(FFNUpParam.MEM_WIDTH.W)
    val st = Bool()
    val addr = UInt(ffnup.io.data_out_addr.getWidth.W)
    val last = Bool()
  }, 2, pipe = true, flow = false))
  ffnUpToDownQ.suggestName("ffnUpToDownQ")
  ffnup.io.data_out_ready := ffnUpToDownQ.io.enq.ready
  ffnUpToDownQ.io.enq.valid := ffnup.io.data_out_valid
  ffnUpToDownQ.io.enq.bits.data := ffnup.io.data_out
  ffnUpToDownQ.io.enq.bits.st := ffnup.io.data_out_st
  ffnUpToDownQ.io.enq.bits.addr := ffnup.io.data_out_addr
  ffnUpToDownQ.io.enq.bits.last := ffnup.io.data_out_last
  ffnUpToDownQ.io.deq.ready := ffndown.io.data_ready

  io.ffnup_w_addr := ffnup.io.weight_init_addr

  // ========================================
  // FFNDown 连接 (ReLU 已融合进 FFNUp)
  // ========================================
  ffndown.io.layer_st := io.layer_st
  ffndown.io.cfg_seqlen := io.cfg_seqlen
  ffndown.io.cfg_prefill := io.cfg_prefill
  ffndown.io.cfg_valid := io.cfg_valid

  ffndown.io.data_in := ffnUpToDownQ.io.deq.bits.data
  ffndown.io.data_in_st := ffnUpToDownQ.io.deq.bits.st
  ffndown.io.data_addr := ffnUpToDownQ.io.deq.bits.addr
  ffndown.io.data_valid := ffnUpToDownQ.io.deq.valid
  ffndown.io.data_last := ffnUpToDownQ.io.deq.bits.last

  ffndown.io.weight_init_mode := io.weight_init_mode
  ffndown.io.weight_init_data := io.ffndown_w_in
  ffndown.io.weight_active_bank := io.weight_active_bank
  ffndown.io.weight_preload_bank := io.weight_preload_bank
  ffndown.io.weight_preload_valid := io.ffndown_w_preload_valid
  ffndown.io.weight_preload_addr := io.ffndown_w_preload_addr
  ffndown.io.weight_preload_data := io.ffndown_w_preload_data
  ffndown.io.bias_init_data := io.ffndown_b_in
  ffndown.io.bias_init_valid := io.ffndown_b_valid
  ffndown.io.out_scale := io.ffndown_out_scale

  val ffnToRes2Q = Module(new Queue(new Bundle {
    val data = UInt(FP32_PACK_WIDTH.W)
    val st = Bool()
    val addr = UInt(log2Up(RES_MEM_DEPTH).W)
    val last = Bool()
  }, RES_MEM_DEPTH, false, false, true))

  ffnToRes2Q.io.enq.valid := ffndown.io.data_out_valid
  ffnToRes2Q.io.enq.bits.data := ffndown.io.data_out
  ffnToRes2Q.io.enq.bits.st := ffndown.io.data_out_st
  ffnToRes2Q.io.enq.bits.addr := ffndown.io.data_out_addr(log2Up(RES_MEM_DEPTH) - 1, 0)
  ffnToRes2Q.io.enq.bits.last := ffndown.io.data_out_last
  ffndown.io.data_out_ready := ffnToRes2Q.io.enq.ready

  io.ffndown_w_addr := ffndown.io.weight_init_addr

  // ========================================
  // ResAdd2 连接 (S12: 残差连接 2)
  // ========================================
  resadd2.io.cfg_seqlen := io.cfg_seqlen
  resadd2.io.cfg_prefill := io.cfg_prefill
  resadd2.io.cfg_valid := io.cfg_valid

  // S7-ResAdd 输出 -> ResAdd2 缓存
  resadd2.io.s7_in := resadd.io.res
  resadd2.io.s7_in_st := resadd.io.res_st
  resadd2.io.s7_in_addr := resadd.io.res_addr
  resadd2.io.s7_in_valid := resadd.io.res_valid
  resadd2.io.s7_in_last := resadd.io.res_last

  // FFNDown 输出 -> ResAdd2
  resadd2.io.ffn_in := ffnToRes2Q.io.deq.bits.data
  resadd2.io.ffn_in_st := ffnToRes2Q.io.deq.bits.st
  resadd2.io.ffn_in_addr := ffnToRes2Q.io.deq.bits.addr
  resadd2.io.ffn_in_valid := ffnToRes2Q.io.deq.valid
  resadd2.io.ffn_in_last := ffnToRes2Q.io.deq.bits.last
  ffnToRes2Q.io.deq.ready := resadd2.io.ffn_ready

  resadd2.io.res_ready := io.res_ready

  // ========================================
  // 输出连接（从 ResAdd2）
  // ========================================
  io.res := resadd2.io.res
  io.res_st := resadd2.io.res_st
  io.res_addr := resadd2.io.res_addr
  io.res_valid := resadd2.io.res_valid
  io.res_last := resadd2.io.res_last
}

object AttenTopGen extends App {
  val generatedDir = Paths.get("generated")
  val vivadoTmpDir = Paths.get("generated_vivado_tmp")
  val topFile = generatedDir.resolve("Top.sv")
  val topVivadoFile = generatedDir.resolve("Top_vivado.sv")
  val deliverableVivadoFile =
    Paths.get("deliverables", "vivado_opt_acc_core_ip", "hdl", "Top_vivado.sv")

  def ensureDir(path: Path): Unit = Files.createDirectories(path)

  def stripVerificationSections(src: Path, dst: Path): Unit = {
    val lines = Files.readAllLines(src, StandardCharsets.UTF_8)
    val kept = new java.util.ArrayList[String]()
    val it = lines.iterator()
    var stop = false
    while (it.hasNext && !stop) {
      val line = it.next()
      if (line.startsWith("// ----- 8< ----- FILE \"verification/")) {
        stop = true
      } else {
        kept.add(line)
      }
    }
    Files.write(dst, kept, StandardCharsets.UTF_8)
  }

  def injectVivadoAttributes(path: Path): Unit = {
    val src = Files.readString(path, StandardCharsets.UTF_8)
    val signalLinePatterns = Seq(
      raw"(?m)^  reg\s+cfgRestartPending;\s*// src/main/scala/OutLinear/OutLinearFP32\.scala:\d+:\d+$$",
      raw"(?m)^  reg\s+captureWriteEnableReg;\s*// src/main/scala/OutLinear/OutLinearFP32\.scala:\d+:\d+$$",
      raw"(?m)^  reg\s+\[[^\n]+\]\s+captureTokenReg;\s*// src/main/scala/OutLinear/OutLinearFP32\.scala:\d+:\d+$$",
      raw"(?m)^  reg\s+\[[^\n]+\]\s+captureSlotReg;\s*// src/main/scala/OutLinear/OutLinearFP32\.scala:\d+:\d+$$",
      raw"(?m)^  reg\s+collectWriteEnableReg;\s*// src/main/scala/QKVLinear/QKVLinear\.scala:\d+:\d+$$",
      raw"(?m)^  reg\s+\[[^\n]+\]\s+collectTokenReg;\s*// src/main/scala/QKVLinear/QKVLinear\.scala:\d+:\d+$$",
      raw"(?m)^  reg\s+\[[^\n]+\]\s+collectVecReg;\s*// src/main/scala/QKVLinear/QKVLinear\.scala:\d+:\d+$$",
      raw"(?m)^  reg\s+out_bank_sel;\s*// src/main/scala/QKVLinear/CUQuant\.scala:\d+:\d+$$",
      raw"(?m)^  reg\s+out_bank_sel;\s*// src/main/scala/OutLinear/CUFP32\.scala:\d+:\d+$$",
      raw"(?m)^  reg\s+out_bank_sel;\s*// src/main/scala/FFNUp/CUQuant\.scala:\d+:\d+$$",
      raw"(?m)^  reg\s+out_bank_sel;\s*// src/main/scala/FFNDown/CUFP32\.scala:\d+:\d+$$",
      raw"(?m)^  reg\s+\[[^\n]+\]\s+headCntReg;\s*// src/main/scala/QKVLinear/QKVLinear\.scala:\d+:\d+$$",
      raw"(?m)^  reg\s+\[[^\n]+\]\s+prefillCntReg;\s*// src/main/scala/QKVLinear/QKVLinear\.scala:\d+:\d+$$",
      raw"(?m)^  reg\s+\[[^\n]+\]\s+batchCntReg;\s*// src/main/scala/QKVLinear/QKVLinear\.scala:\d+:\d+$$",
      raw"(?m)^  reg\s+\[[^\n]+\]\s+outputCntReg;\s*// src/main/scala/QKVLinear/QKVLinear\.scala:\d+:\d+$$",
      raw"(?m)^  reg\s+output_valid_reg;\s*// src/main/scala/QKVLinear/QKVLinear\.scala:\d+:\d+$$",
      raw"(?m)^  reg\s+\[[^\n]+\]\s+output_head_reg;\s*// src/main/scala/QKVLinear/QKVLinear\.scala:\d+:\d+$$",
      raw"(?m)^  reg\s+\[[^\n]+\]\s+output_addr_reg;\s*// src/main/scala/QKVLinear/QKVLinear\.scala:\d+:\d+$$",
      raw"(?m)^  reg\s+\[[^\n]+\]\s+batchsizeCntReg;\s*// src/main/scala/(QKVLinear/CUQuant|OutLinear/CUFP32|FFNUp/CUQuant|FFNDown/CUFP32)\.scala:\d+:\d+$$",
      raw"(?m)^  reg\s+\[[^\n]+\]\s+blockCntReg;\s*// src/main/scala/(QKVLinear/CUQuant|OutLinear/CUFP32|FFNUp/CUQuant|FFNDown/CUFP32)\.scala:\d+:\d+$$",
      raw"(?m)^  reg\s+psumSelReg;\s*// src/main/scala/(QKVLinear/CUQuant|OutLinear/CUFP32|FFNUp/CUQuant|FFNDown/CUFP32)\.scala:\d+:\d+$$",
      raw"(?m)^  reg\s+\[[^\n]+\]\s+resVectorCntReg;\s*// src/main/scala/(QKVLinear/CUQuant|OutLinear/CUFP32|FFNUp/CUQuant|FFNDown/CUFP32)\.scala:\d+:\d+$$",
      raw"(?m)^  reg\s+\[[^\n]+\]\s+resBatchsizeCntReg;\s*// src/main/scala/(QKVLinear/CUQuant|OutLinear/CUFP32|FFNUp/CUQuant|FFNDown/CUFP32)\.scala:\d+:\d+$$"
    )
    val fanoutPatched = signalLinePatterns.foldLeft(src) { (acc, pattern) =>
      pattern.r.replaceAllIn(acc, m => s"  (* max_fanout = 32 *) ${m.matched.trim}")
    }
    val qkvVecBufferMemPattern =
      raw"(?m)^  reg \[95:0\] Memory\[0:3071\];\s*// src/main/scala/QKVLinear/QKVLinear\.scala:\d+:\d+$$"
    val patched = qkvVecBufferMemPattern.r.replaceAllIn(
      fanoutPatched,
      m => s"""  (* ram_style = "block" *) ${m.matched.trim}"""
    )
    Files.writeString(path, patched, StandardCharsets.UTF_8)
  }

  ensureDir(generatedDir)
  ensureDir(vivadoTmpDir)
  ensureDir(deliverableVivadoFile.getParent)

  FpBackend.setHardFloatCompat()
  emitVerilog(new Top, Array("--target-dir", generatedDir.toString))

  FpBackend.setVivadoIp()
  emitVerilog(new Top, Array("--target-dir", vivadoTmpDir.toString))
  stripVerificationSections(vivadoTmpDir.resolve("Top.sv"), topVivadoFile)
  injectVivadoAttributes(topVivadoFile)
  Files.copy(topVivadoFile, deliverableVivadoFile, StandardCopyOption.REPLACE_EXISTING)

  FpBackend.setHardFloatCompat()
}
