import DM.Param._
import DM.DM1FP32
import DM2.DM2Quant
import DM2.Param.{HEAD_VECNUM => DM2_HEAD_VECNUM, MEM_DEPTH => DM2_MEM_DEPTH}
import DM2.QuantParam.CTX_FP32_WIDTH
import QuantCommon.Precision.FP32_WIDTH
import QuantCommon.Precision.UINT8_WIDTH
import ResMEM.VCache
import Softmax.Param.{WMEM_DEPTH, WMEM_WIDTH}
import Softmax.SoftmaxPipFP32
import chisel3._
import chisel3.util._

// Attention 模块：整合 DM1 -> Softmax -> VCache -> DM2 流水线
class Atten extends Module {
  class Dm2Beat extends Bundle {
    val data = UInt((DM2_HEAD_VECNUM * DATAW).W)
    val st = Bool()
    val addr = UInt(log2Up(MEM_DEPTH).W)
    val last = Bool()
  }

  class Dm2CtxBeat extends Bundle {
    val data = UInt(CTX_FP32_WIDTH.W)
    val st = Bool()
    val addr = UInt(log2Up(MEM_DEPTH).W)
    val last = Bool()
  }

  val io = IO(new Bundle() {
    val layer_st = Input(Bool())
    val cfg_seqlen = Input(UInt(log2Up( MAX_SEQLEN).W))
    val cfg_prefill = Input(Bool())
    val cfg_valid = Input(Bool())
    val cfg_single_query = Input(Bool())

  val dm1_out_scale = Input(UInt(FP32_WIDTH.W))
  val dm2_ctx_inv_scale = Input(UInt(FP32_WIDTH.W))
  val dm2_ctx_zero_point = Input(UInt(UINT8_WIDTH.W))
  val dm2_out_inv_scale = Input(UInt(FP32_WIDTH.W))

  val w_in = Input(UInt(WMEM_WIDTH.W))
  val w_addr = Output(UInt(log2Up(WMEM_DEPTH).W))

  val data_in_st = Input(Bool())
  val data_in = Input(UInt((3 * LOAD_VECNUM * DATAW).W))
  val data_addr = Input(UInt(log2Up(HEAD_VECNUM / LOAD_VECNUM * BATCHSIZE).W))
  val data_valid = Input(Bool())
  val data_last = Input(Bool())
  val data_ready = Output(Bool())

  // 长序列场景下，允许 wrapper/DDR 在不接管整条 Attention 主路径的前提下，
  // 只替换真正的历史数据源：
  // 1. DM1 侧的 QK 输入（例如 current-Q + external-history-K）
  // 2. DM2 侧的 V 输入（external-history-V）
  val dm1_override_enable = Input(Bool())
  val dm1_override_data = Input(UInt((2 * LOAD_VECNUM * DATAW).W))
  val dm1_override_st = Input(Bool())
  val dm1_override_addr = Input(UInt(log2Up(HEAD_VECNUM / LOAD_VECNUM * BATCHSIZE).W))
  val dm1_override_valid = Input(Bool())
  val dm1_override_last = Input(Bool())
  val dm1_override_ready = Output(Bool())

  val dm2_v_override_enable = Input(Bool())
  val dm2_v_override_data = Input(UInt((DM2_HEAD_VECNUM * DATAW).W))
  val dm2_v_override_valid = Input(Bool())
  val dm2_v_override_ready = Output(Bool())

  // DM2 输出: 512-bit (64 elements * 8-bit)
  val res = Output(UInt((DM2_HEAD_VECNUM * DATAW).W))
  val res_st = Output(Bool())
  val res_addr = Output(UInt(log2Up(MEM_DEPTH).W))
  val res_valid = Output(Bool())
  val res_last = Output(Bool())
  val res_ready = Input(Bool())
})

  // ========================================
  // 模块实例化 - 按流水级顺序
  // ========================================
  val dm1 = Module(new DM1FP32)           // 流水级3: Q·K 点积
  val softmax = Module(new SoftmaxPipFP32)   // 流水级4: Softmax归一化
  val vcache = Module(new VCache)     // 流水级5: V向量缓存
  val dm2 = Module(new DM2Quant)           // 流水级6: Ctx·V 点积
  // Single-query decode can burst a full batch window of V vectors before DM2
  // drains them. Keep enough slack to avoid dropping late lbatch entries.
  // In short-seq full-seq prefill, Softmax can burst a full head's ctx beats
  // long before DM2 finishes consuming the previous head. 32 entries is
  // enough for bring-up, but not enough to sustain the intended wavefront.
  // Keep a larger on-chip queue so ctx backpressure does not immediately
  // collapse the QKV->Attention pipeline.
  val ctxToDm2Q = Module(new Queue(new Dm2CtxBeat, 256))
  // Single-query decode can accumulate more than one token's V beats while DM2
  // waits on the matching ctx tile. Keep this queue deeper so VCache write-side
  // banks do not back up and stall the entire Attention input stream.
  val vToDm2Q = Module(new Queue(new Dm2Beat, 64))
  val input_ready = Wire(Bool())
  val stage_ready = Wire(Bool())
  val stage_fire = Wire(Bool())
  val ingress_data = Reg(UInt(io.data_in.getWidth.W))
  val ingress_st = RegInit(false.B)
  val ingress_addr = Reg(UInt(io.data_addr.getWidth.W))
  val ingress_last = RegInit(false.B)
  val ingress_valid = RegInit(false.B)
  // Register one QKV beat at the Attention ingress so the long
  // qkvlinear->DM1/VCache route is cut without changing beat order.
  val input_fire = io.data_valid && input_ready
  val dm1InputValid = Mux(io.dm1_override_enable, io.dm1_override_valid, stage_fire)
  val cfgSeqlen = RegInit(0.U(log2Up(MAX_SEQLEN).W))
  val cfgPrefill = RegInit(false.B)
  val cfgSingleQuery = RegInit(false.B)
  val attnRequestActive = RegInit(false.B)
  val attnHeadDoneCnt = RegInit(0.U(log2Up(SINGLE_QUERY_BATCH).W))
  // Top 已经把 attention cfg 保持住；这里只在真正接到下一次 attention 请求首拍时才提交，
  // 避免上游提前切 cfg，把前一批仍在 DM1/Softmax/DM2 里的数据误按新模式解释。
  val inputRequestStart = stage_fire && ingress_st && !attnRequestActive
  val inputHeadDone = stage_fire && ingress_last
  val inputRequestDone = inputHeadDone && attnHeadDoneCnt === (SINGLE_QUERY_BATCH - 1).U
  when(inputRequestStart) {
    cfgSeqlen := io.cfg_seqlen
    cfgPrefill := io.cfg_prefill
    cfgSingleQuery := io.cfg_single_query
    attnRequestActive := true.B
    attnHeadDoneCnt := 0.U
  }
  when(inputHeadDone) {
    attnHeadDoneCnt := Mux(inputRequestDone, 0.U, attnHeadDoneCnt + 1.U)
    when(inputRequestDone) {
      attnRequestActive := false.B
    }
  }
  val attnCfgValid = inputRequestStart
  val attnCfgSeqlen = Mux(attnCfgValid, io.cfg_seqlen, cfgSeqlen)
  val attnCfgPrefill = Mux(attnCfgValid, io.cfg_prefill, cfgPrefill)
  val attnCfgSingleQuery = Mux(attnCfgValid, io.cfg_single_query, cfgSingleQuery)

  // ========================================
  // DM1 连接 (Q·K 点积)
  // ========================================
  dm1.io.cfg_seqlen := attnCfgSeqlen
  dm1.io.cfg_valid := attnCfgValid
  dm1.io.cfg_prefill := attnCfgPrefill
  dm1.io.cfg_single_query := attnCfgSingleQuery
  dm1.io.out_scale := io.dm1_out_scale

  dm1.io.data_in_st := Mux(io.dm1_override_enable, io.dm1_override_st, stage_fire && ingress_st)
  dm1.io.data_in := Mux(io.dm1_override_enable, io.dm1_override_data, ingress_data(2*LOAD_VECNUM * DATAW - 1 , 0)) // QK数据
  dm1.io.data_addr := Mux(io.dm1_override_enable, io.dm1_override_addr, ingress_addr)
  dm1.io.data_valid := dm1InputValid
  dm1.io.data_last := Mux(io.dm1_override_enable, io.dm1_override_last, stage_fire && ingress_last)
  dm1.io.res_ready := softmax.io.data_ready
  io.dm1_override_ready := dm1.io.data_ready

  // Single-query replay can hold DM1 output valid while Softmax is busy.
  // Head-start / done bookkeeping must follow the real DM1->Softmax handshake,
  // not raw valid, otherwise a stalled beat can re-trigger Softmax mid-row.
  val dm1OutFire = dm1.io.res_valid && softmax.io.data_ready
  val dm1OutStart = dm1OutFire && dm1.io.res_st
  val dm1OutDone = dm1OutFire && dm1.io.res_last
  // DM1 already marks the first tile of each head with res_st. Once the
  // trigger is tied to the true DM1->Softmax handshake, the extra
  // "started" latch only re-introduces head-start races under backpressure.
  val softmaxHeadStart = attnCfgSingleQuery && dm1OutStart

  // ========================================
  // Softmax 连接
  // ========================================
  softmax.io.cfg_seqlen := attnCfgSeqlen
  softmax.io.cfg_valid := attnCfgValid
  softmax.io.cfg_prefill := attnCfgPrefill
  softmax.io.cfg_single_query := attnCfgSingleQuery
  softmax.io.layer_st := Mux(attnCfgSingleQuery, softmaxHeadStart, inputRequestStart)
  softmax.io.data_in_st := Mux(attnCfgSingleQuery, softmaxHeadStart, dm1.io.res_st)
  softmax.io.data_in := dm1.io.res
  softmax.io.data_addr := dm1.io.res_addr
  softmax.io.data_valid := dm1.io.res_valid
  softmax.io.data_last := dm1.io.res_last
  softmax.io.res_ready := ctxToDm2Q.io.enq.ready

  ctxToDm2Q.io.enq.valid := softmax.io.res_valid
  ctxToDm2Q.io.enq.bits.data := softmax.io.res
  ctxToDm2Q.io.enq.bits.st := softmax.io.res_st
  ctxToDm2Q.io.enq.bits.addr := softmax.io.res_addr
  ctxToDm2Q.io.enq.bits.last := softmax.io.res_last

  softmax.io.w_in := io.w_in
  io.w_addr := softmax.io.w_addr

  // ========================================
  // VCache 连接 (V向量缓存)
  // ========================================
  vcache.io.cfg_valid := attnCfgValid
  vcache.io.cfg_seqlen := attnCfgSeqlen
  vcache.io.cfg_prefill := attnCfgPrefill
  vcache.io.cfg_single_query := attnCfgSingleQuery
  vcache.io.data_in_st := stage_fire && ingress_st
  vcache.io.data_in := ingress_data(3 * LOAD_VECNUM * DATAW - 1, 2 * LOAD_VECNUM * DATAW) // V数据
  vcache.io.data_in_addr := ingress_addr
  vcache.io.data_in_valid := stage_fire
  vcache.io.data_in_last := stage_fire && ingress_last
  vcache.io.res_ready := Mux(io.dm2_v_override_enable, true.B, vToDm2Q.io.enq.ready)

  vToDm2Q.io.enq.valid := !io.dm2_v_override_enable && vcache.io.res_valid
  vToDm2Q.io.enq.bits.data := vcache.io.res
  vToDm2Q.io.enq.bits.st := vcache.io.res_st
  vToDm2Q.io.enq.bits.addr := vcache.io.res_addr
  vToDm2Q.io.enq.bits.last := vcache.io.res_last

  // ========================================
  // DM2 连接 (Ctx·V 点积)
  // ========================================
  dm2.io.cfg_valid := attnCfgValid
  dm2.io.cfg_seqlen := attnCfgSeqlen
  dm2.io.cfg_prefill := attnCfgPrefill
  dm2.io.cfg_single_query := attnCfgSingleQuery
  dm2.io.ctx_inv_scale := io.dm2_ctx_inv_scale
  dm2.io.ctx_zero_point := io.dm2_ctx_zero_point
  dm2.io.out_inv_scale := io.dm2_out_inv_scale

  // Softmax 结果 -> DM2 ctx 输入
  dm2.io.data_in_ctx_st := ctxToDm2Q.io.deq.valid && ctxToDm2Q.io.deq.bits.st
  dm2.io.data_in_ctx := ctxToDm2Q.io.deq.bits.data
  dm2.io.data_in_ctx_valid := ctxToDm2Q.io.deq.valid
  ctxToDm2Q.io.deq.ready := dm2.io.data_in_ctx_ready

  // VCache 结果 -> DM2 v 输入
  dm2.io.data_in_v := Mux(io.dm2_v_override_enable, io.dm2_v_override_data, vToDm2Q.io.deq.bits.data)
  dm2.io.data_in_v_valid := Mux(io.dm2_v_override_enable, io.dm2_v_override_valid, vToDm2Q.io.deq.valid)
  vToDm2Q.io.deq.ready := !io.dm2_v_override_enable && dm2.io.data_in_v_ready
  dm2.io.res_ready := io.res_ready
  io.dm2_v_override_ready := dm2.io.data_in_v_ready

  // ========================================
  // 输出连接
  // ========================================
  stage_ready := vcache.io.data_in_ready && Mux(io.dm1_override_enable, true.B, dm1.io.data_ready)
  stage_fire := ingress_valid && stage_ready
  input_ready := !ingress_valid || stage_ready
  when(input_ready) {
    ingress_valid := io.data_valid
  }
  when(input_fire) {
    ingress_data := io.data_in
    ingress_st := io.data_in_st
    ingress_addr := io.data_addr
    ingress_last := io.data_last
  }
  io.data_ready := input_ready

  io.res := dm2.io.res
  io.res_st := dm2.io.res_st
  io.res_addr := dm2.io.res_addr
  io.res_valid := dm2.io.res_valid
  io.res_last := dm2.io.res_last
}
