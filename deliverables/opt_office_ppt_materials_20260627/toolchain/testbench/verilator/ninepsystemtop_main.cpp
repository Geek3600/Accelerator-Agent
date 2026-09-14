#include "VNinePSystemTop.h"
#include "VNinePSystemTop___024root.h"
#include "common.hpp"
#include <algorithm>
#include <cstdint>
#include <deque>
#include <cstdlib>
#include <filesystem>
#include <vector>

namespace {

struct PendingRead {
  int cycles_left;
  std::size_t addr;
};

void drive_ddr_idle(VNinePSystemTop& dut) {
  dut.io_ddr_rdy = 1;
  dut.io_ddr_init_done = 1;
  dut.io_ddr_rd_data_valid = 0;
  dut.io_ddr_rd_data_end = 0;
  zero_words(dut.io_ddr_rd_data, 16);
}

}  // namespace

int main(int argc, char** argv) {
  try {
    Verilated::commandArgs(argc, argv);
    require(argc == 2, "usage: VNinePSystemTop <window_dir>");
    const std::filesystem::path window_dir = argv[1];
    const auto cfg = read_cfg(window_dir / "window.cfg");
    const auto ddr_image = read_words(window_dir / "artifacts" / "ddr_image.u32.bin", 16);
    const auto golden = read_words(window_dir / "artifacts" / "golden.u32.bin", 12);
    const bool debug = std::getenv("SYSTEM_DEBUG") != nullptr;
    const bool allow_mismatch = std::getenv("SYSTEM_ALLOW_MISMATCH") != nullptr;
    const int debug_stride = []() {
      if (const char* raw = std::getenv("SYSTEM_DEBUG_STRIDE")) {
        const int parsed = std::atoi(raw);
        if (parsed > 0) {
          return parsed;
        }
      }
      return 100000;
    }();
    const int ddr_latency = 4;

    VNinePSystemTop dut;
    dut.io_start = 0;
    dut.io_cfg_seqlen = cfg_int(cfg, "cfg_seqlen");
    dut.io_cfg_prefill = 1;
    dut.io_attn_cfg_seqlen = cfg_int(cfg, "cfg_seqlen");
    dut.io_attn_cfg_prefill = 1;
    dut.io_attn_cfg_valid = 1;
    dut.io_attn_cfg_single_query = 0;
    dut.io_ln1_out_inv_scale = cfg_u32(cfg, "ln1_out_inv_scale_u32");
    dut.io_ln1_out_zero_point = static_cast<uint8_t>(cfg_int(cfg, "ln1_out_zero_point_s8"));
    dut.io_q_out_inv_scale = cfg_u32(cfg, "q_out_inv_scale_u32");
    dut.io_k_out_inv_scale = cfg_u32(cfg, "k_out_inv_scale_u32");
    dut.io_v_out_inv_scale = cfg_u32(cfg, "v_out_inv_scale_u32");
    dut.io_q_bias_scale = cfg_u32(cfg, "q_bias_scale_u32");
    dut.io_k_bias_scale = cfg_u32(cfg, "k_bias_scale_u32");
    dut.io_v_bias_scale = cfg_u32(cfg, "v_bias_scale_u32");
    dut.io_dm1_out_scale = cfg_u32(cfg, "dm1_out_scale_u32");
    dut.io_dm2_ctx_inv_scale = cfg_u32(cfg, "dm2_ctx_inv_scale_u32");
    dut.io_dm2_ctx_zero_point = static_cast<uint8_t>(cfg_int(cfg, "dm2_ctx_zero_point_u8"));
    dut.io_dm2_out_inv_scale = cfg_u32(cfg, "dm2_out_inv_scale_u32");
    dut.io_out_out_scale = cfg_u32(cfg, "out_out_scale_u32");
    dut.io_ln2_out_inv_scale = cfg_u32(cfg, "ln2_out_inv_scale_u32");
    dut.io_ln2_out_zero_point = static_cast<uint8_t>(cfg_int(cfg, "ln2_out_zero_point_s8"));
    dut.io_ffnup_out_inv_scale = cfg_u32(cfg, "ffnup_out_inv_scale_u32");
    dut.io_ffnup_bias_scale = cfg_u32(cfg, "ffnup_bias_scale_u32");
    dut.io_ffndown_out_scale = cfg_u32(cfg, "ffndown_out_scale_u32");
    dut.io_input_base_addr = cfg_u32(cfg, "ddr_input_base_addr");
    dut.io_ln1_w_base_addr = cfg_u32(cfg, "ddr_ln1_w_base_addr");
    dut.io_qkv_w_base_addr = cfg_u32(cfg, "ddr_qkv_w_base_addr");
    dut.io_qkv_b_base_addr = cfg_u32(cfg, "ddr_qkv_b_base_addr");
    dut.io_sm_base_addr = cfg_u32(cfg, "ddr_sm_base_addr");
    dut.io_out_w_base_addr = cfg_u32(cfg, "ddr_out_w_base_addr");
    dut.io_out_b_base_addr = cfg_u32(cfg, "ddr_out_b_base_addr");
    dut.io_ln2_w_base_addr = cfg_u32(cfg, "ddr_ln2_w_base_addr");
    dut.io_ffnup_w_base_addr = cfg_u32(cfg, "ddr_ffnup_w_base_addr");
    dut.io_ffnup_b_base_addr = cfg_u32(cfg, "ddr_ffnup_b_base_addr");
    dut.io_ffndown_w_base_addr = cfg_u32(cfg, "ddr_ffndown_w_base_addr");
    dut.io_ffndown_b_base_addr = cfg_u32(cfg, "ddr_ffndown_b_base_addr");
    dut.io_res_ready = 1;
    drive_ddr_idle(dut);

    reset_dut(dut);
    drive_ddr_idle(dut);
    dut.io_start = 1;
    tick(dut);
    dut.io_start = 0;

    std::deque<PendingRead> pending_reads;
    std::vector<uint32_t> observed(golden.words.size(), 0);
    std::vector<bool> seen(golden.beats(), false);
    bool saw_st = false;
    bool saw_last = false;
    std::size_t seen_count = 0;
    int prev_evt_run_token = -1;
    int prev_evt_soft_state = -1;
    int prev_evt_soft_tiles = -1;
    int prev_evt_soft_tile_idx = -1;
    int prev_evt_dm2_state = -1;
    int prev_evt_dm2_tile_base = -1;
    int prev_evt_dm2_tile_cnt = -1;
    int prev_evt_ctxq_enq = -1;
    int prev_evt_ctxq_deq = -1;
    int prev_evt_ctxq_full = -1;
    int prev_evt_ctxq_do_enq = -1;
    int prev_evt_ctxq_do_deq = -1;
    int prev_evt_ctxq_enq_ready = -1;
    int prev_evt_vq_enq = -1;
    int prev_evt_vq_deq = -1;
    int prev_evt_vq_full = -1;
    int prev_evt_vq_do_enq = -1;
    int prev_evt_vq_do_deq = -1;
    int prev_evt_dm2_ctx_ready = -1;
    int prev_evt_dm2_ctx_valid = -1;
    int prev_evt_out_state = -1;
    int prev_evt_out_head = -1;

    for (int cycle = 0; cycle < 50000000 &&
                            !std::all_of(seen.begin(), seen.end(), [](bool v) { return v; });
         ++cycle) {
      if (dut.io_ddr_en && dut.io_ddr_rdy && dut.io_ddr_cmd == 1) {
        require(dut.io_ddr_addr < ddr_image.beats(), "DDR read addr out of range");
        pending_reads.push_back(PendingRead{ddr_latency, static_cast<std::size_t>(dut.io_ddr_addr)});
      }

      drive_ddr_idle(dut);
      if (!pending_reads.empty() && pending_reads.front().cycles_left <= 0) {
        copy_words(dut.io_ddr_rd_data, ddr_image.beat(pending_reads.front().addr), 16);
        dut.io_ddr_rd_data_valid = 1;
        dut.io_ddr_rd_data_end = 1;
        pending_reads.pop_front();
      }

      tick(dut);

      for (auto& req : pending_reads) {
        --req.cycles_left;
      }

      if (dut.io_res_valid) {
        const std::size_t addr = dut.io_res_addr;
        require(addr < golden.beats(), "NinePSystemTop output addr out of range");
        copy_words(observed.data() + addr * 12, dut.io_res, 12);
        if (!seen[addr]) {
          seen[addr] = true;
          ++seen_count;
        }
        saw_st = saw_st || dut.io_res_st;
        saw_last = saw_last || dut.io_res_last;
      }

      if (debug && cycle > 0 && (cycle % debug_stride) == 0) {
        std::cerr << "SystemTop progress"
                  << " cycle=" << cycle
                  << " state=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__state)
                  << " ddr_en=" << static_cast<int>(dut.io_ddr_en)
                  << " ddr_addr=" << dut.io_ddr_addr
                  << " pending=" << pending_reads.size()
                  << " res_valid=" << static_cast<int>(dut.io_res_valid)
                  << " res_addr=" << dut.io_res_addr
                  << " seen=" << seen_count << "/" << golden.beats()
                  << " saw_st=" << static_cast<int>(saw_st)
                  << " saw_last=" << static_cast<int>(saw_last)
                  << std::endl;
        if (dut.rootp->NinePSystemTop__DOT__state == 13) {
          std::cerr << "SystemTop weight_init"
                    << " max_qkv_addr=" << static_cast<unsigned>(dut.rootp->NinePSystemTop__DOT__max_qkv_addr)
                    << " max_out_addr=" << static_cast<unsigned>(dut.rootp->NinePSystemTop__DOT__max_out_addr)
                    << " max_ffnup_addr=" << static_cast<unsigned>(dut.rootp->NinePSystemTop__DOT__max_ffnup_addr)
                    << " max_ffndown_addr=" << static_cast<unsigned>(dut.rootp->NinePSystemTop__DOT__max_ffndown_addr)
                    << " tail=" << static_cast<unsigned>(dut.rootp->NinePSystemTop__DOT__weight_init_tail)
                    << std::endl;
        }
        if (dut.rootp->NinePSystemTop__DOT__state == 24 &&
            dut.rootp->NinePSystemTop__DOT__run_token_idx >= 20) {
          std::cerr << "SystemTop core"
                    << " run_token=" << dut.rootp->NinePSystemTop__DOT__run_token_idx
                    << " qkv_state=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__u_core__DOT__qkvlinear__DOT__state)
                    << " qkv_head=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__u_core__DOT__qkvlinear__DOT__head_cnt_r)
                    << " qkv_out=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__u_core__DOT__qkvlinear__DOT__output_cnt_r)
                    << " attn_rdy=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__u_core__DOT___atten_io_data_ready)
                    << " dm1_state=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__dm1__DOT__cu_inst__DOT__state)
                    << " dm1_lbatch=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__dm1__DOT__cu_inst__DOT__lbatch_cnt)
                    << " soft_state=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__softmax__DOT__state)
                    << " soft_tiles=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__softmax__DOT__rowTileCountReg)
                    << " soft_tileIdx=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__softmax__DOT__tileIdxReg)
                    << " soft_outV=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__softmax__DOT__outValidReg)
                    << " soft_outLast=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__softmax__DOT__outLastReg)
                    << " dm2_state=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__dm2__DOT__dmInst__DOT__state)
                    << " dm2_lbatch=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__dm2__DOT__dmInst__DOT__lbatchCnt)
                    << " dm2_tileBase=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__dm2__DOT__dmInst__DOT__tileBase)
                    << " dm2_tileCnt=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__dm2__DOT__dmInst__DOT__tileLoadCnt)
                    << " dm2_waitctx=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__dm2__DOT__dmInst__DOT__waitctxCnt)
                    << " dm2_mul=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__dm2__DOT__dmInst__DOT__mulCnt)
                    << " vcache_full=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__vcache__DOT__mem_inst__DOT__full_cnt)
                    << " vcache_busy=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__vcache__DOT__mem_inst__DOT__buzy_cnt)
                    << " vcache_wptr=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__vcache__DOT__mem_inst__DOT__w_ptr)
                    << " vcache_rptr=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__vcache__DOT__mem_inst__DOT__r_ptr)
                    << " ctxq_full=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__ctxToDm2Q__DOT__maybe_full)
                    << " ctxq_enq=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__ctxToDm2Q__DOT__enq_ptr_value)
                    << " ctxq_deq=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__ctxToDm2Q__DOT__deq_ptr_value)
                    << " vq_full=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__vToDm2Q__DOT__maybe_full)
                    << " vq_enq=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__vToDm2Q__DOT__enq_ptr_value)
                    << " vq_deq=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__vToDm2Q__DOT__deq_ptr_value)
                    << " aq_full=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__u_core__DOT__attnToOutQ__DOT__maybe_full)
                    << " out_state=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__u_core__DOT__outlinear__DOT__state)
                    << " out_head=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__u_core__DOT__outlinear__DOT__head_cnt)
                    << " out_rdy=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__u_core__DOT___outlinear_io_data_ready)
                    << std::endl;
        }
      }

      if (debug && dut.rootp->NinePSystemTop__DOT__state == 24 &&
          dut.rootp->NinePSystemTop__DOT__run_token_idx >= 25) {
        const int run_token = dut.rootp->NinePSystemTop__DOT__run_token_idx;
        const int soft_state = dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__softmax__DOT__state;
        const int soft_tiles = dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__softmax__DOT__rowTileCountReg;
        const int soft_tile_idx = dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__softmax__DOT__tileIdxReg;
        const int dm2_state = dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__dm2__DOT__dmInst__DOT__state;
        const int dm2_tile_base = dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__dm2__DOT__dmInst__DOT__tileBase;
        const int dm2_tile_cnt = dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__dm2__DOT__dmInst__DOT__tileLoadCnt;
        const int ctxq_enq = dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__ctxToDm2Q__DOT__enq_ptr_value;
        const int ctxq_deq = dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__ctxToDm2Q__DOT__deq_ptr_value;
        const int ctxq_full = dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__ctxToDm2Q__DOT__maybe_full;
        const int ctxq_do_enq = dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__ctxToDm2Q__DOT__do_enq;
        const int ctxq_do_deq =
            dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__ctxToDm2Q__DOT__unnamedblk1__DOT__do_deq;
        const int ctxq_enq_ready = dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT___ctxToDm2Q_io_enq_ready;
        const int vq_enq = dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__vToDm2Q__DOT__enq_ptr_value;
        const int vq_deq = dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__vToDm2Q__DOT__deq_ptr_value;
        const int vq_full = dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__vToDm2Q__DOT__maybe_full;
        const int vq_do_enq = dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__vToDm2Q__DOT__do_enq;
        const int vq_do_deq =
            dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__vToDm2Q__DOT__unnamedblk1__DOT__do_deq;
        const int dm2_ctx_ready = dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__dm2__DOT___dmInst_io_data_in_ctx_ready;
        const int dm2_ctx_valid = dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__dm2__DOT____Vcellinp__dmInst__io_data_in_ctx_valid;
        const int out_state = dut.rootp->NinePSystemTop__DOT__u_core__DOT__outlinear__DOT__state;
        const int out_head = dut.rootp->NinePSystemTop__DOT__u_core__DOT__outlinear__DOT__head_cnt;
        const bool changed =
            run_token != prev_evt_run_token ||
            soft_state != prev_evt_soft_state ||
            soft_tiles != prev_evt_soft_tiles ||
            soft_tile_idx != prev_evt_soft_tile_idx ||
            dm2_state != prev_evt_dm2_state ||
            dm2_tile_base != prev_evt_dm2_tile_base ||
            dm2_tile_cnt != prev_evt_dm2_tile_cnt ||
            ctxq_enq != prev_evt_ctxq_enq ||
            ctxq_deq != prev_evt_ctxq_deq ||
            ctxq_full != prev_evt_ctxq_full ||
            ctxq_do_enq != prev_evt_ctxq_do_enq ||
            ctxq_do_deq != prev_evt_ctxq_do_deq ||
            ctxq_enq_ready != prev_evt_ctxq_enq_ready ||
            vq_enq != prev_evt_vq_enq ||
            vq_deq != prev_evt_vq_deq ||
            vq_full != prev_evt_vq_full ||
            vq_do_enq != prev_evt_vq_do_enq ||
            vq_do_deq != prev_evt_vq_do_deq ||
            dm2_ctx_ready != prev_evt_dm2_ctx_ready ||
            dm2_ctx_valid != prev_evt_dm2_ctx_valid ||
            out_state != prev_evt_out_state ||
            out_head != prev_evt_out_head;
        if (changed) {
          std::cerr << "SystemTop event"
                    << " cycle=" << cycle
                    << " run_token=" << run_token
                    << " soft_state=" << soft_state
                    << " soft_tiles=" << soft_tiles
                    << " soft_tileIdx=" << soft_tile_idx
                    << " soft_outV=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__softmax__DOT__outValidReg)
                    << " soft_outLast=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__softmax__DOT__outLastReg)
                    << " dm2_state=" << dm2_state
                    << " dm2_tileBase=" << dm2_tile_base
                    << " dm2_tileCnt=" << dm2_tile_cnt
                    << " dm2_waitctx=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__dm2__DOT__dmInst__DOT__waitctxCnt)
                    << " dm2_mul=" << static_cast<int>(dut.rootp->NinePSystemTop__DOT__u_core__DOT__atten__DOT__dm2__DOT__dmInst__DOT__mulCnt)
                    << " ctxq_full=" << ctxq_full
                    << " ctxq_enq=" << ctxq_enq
                    << " ctxq_deq=" << ctxq_deq
                    << " ctxq_do_enq=" << ctxq_do_enq
                    << " ctxq_do_deq=" << ctxq_do_deq
                    << " ctxq_enq_ready=" << ctxq_enq_ready
                    << " vq_full=" << vq_full
                    << " vq_enq=" << vq_enq
                    << " vq_deq=" << vq_deq
                    << " vq_do_enq=" << vq_do_enq
                    << " vq_do_deq=" << vq_do_deq
                    << " dm2_ctx_ready=" << dm2_ctx_ready
                    << " dm2_ctx_valid=" << dm2_ctx_valid
                    << " out_state=" << out_state
                    << " out_head=" << out_head
                    << std::endl;
        }
        prev_evt_run_token = run_token;
        prev_evt_soft_state = soft_state;
        prev_evt_soft_tiles = soft_tiles;
        prev_evt_soft_tile_idx = soft_tile_idx;
        prev_evt_dm2_state = dm2_state;
        prev_evt_dm2_tile_base = dm2_tile_base;
        prev_evt_dm2_tile_cnt = dm2_tile_cnt;
        prev_evt_ctxq_enq = ctxq_enq;
        prev_evt_ctxq_deq = ctxq_deq;
        prev_evt_ctxq_full = ctxq_full;
        prev_evt_ctxq_do_enq = ctxq_do_enq;
        prev_evt_ctxq_do_deq = ctxq_do_deq;
        prev_evt_ctxq_enq_ready = ctxq_enq_ready;
        prev_evt_vq_enq = vq_enq;
        prev_evt_vq_deq = vq_deq;
        prev_evt_vq_full = vq_full;
        prev_evt_vq_do_enq = vq_do_enq;
        prev_evt_vq_do_deq = vq_do_deq;
        prev_evt_dm2_ctx_ready = dm2_ctx_ready;
        prev_evt_dm2_ctx_valid = dm2_ctx_valid;
        prev_evt_out_state = out_state;
        prev_evt_out_head = out_head;
      }
    }

    if (!std::all_of(seen.begin(), seen.end(), [](bool v) { return v; })) {
      std::cerr << "SystemTop missing beats summary";
      std::size_t dumped = 0;
      for (std::size_t beat = 0; beat < seen.size() && dumped < 16; ++beat) {
        if (!seen[beat]) {
          std::cerr << " beat=" << beat;
          ++dumped;
        }
      }
      std::cerr << " seen=" << seen_count << "/" << golden.beats() << std::endl;
    }

    require(
        std::all_of(seen.begin(), seen.end(), [](bool v) { return v; }),
        "missing NinePSystemTop output beats");
    require(saw_st, "NinePSystemTop never asserted io_res_st");
    require(saw_last, "NinePSystemTop never asserted io_res_last");
    if (allow_mismatch) {
      std::size_t first_bad_beat = golden.beats();
      std::size_t first_bad_lane = 0;
      float first_bad_obs = 0.0f;
      float first_bad_exp = 0.0f;
      std::size_t bad_count = 0;
      for (std::size_t beat = 0; beat < golden.beats(); ++beat) {
        const auto obs = unpack_fp32_lanes(observed.data() + beat * 12, 12);
        const auto exp = unpack_fp32_lanes(golden.beat(beat), 12);
        for (std::size_t lane = 0; lane < 12; ++lane) {
          if (observed[beat * 12 + lane] != golden.words[beat * 12 + lane]) {
            const float abs_err = std::abs(obs[lane] - exp[lane]);
            if (abs_err > 5.0e-4f) {
              if (first_bad_beat == golden.beats()) {
                first_bad_beat = beat;
                first_bad_lane = lane;
                first_bad_obs = obs[lane];
                first_bad_exp = exp[lane];
              }
              ++bad_count;
            }
          }
        }
      }
      if (first_bad_beat != golden.beats()) {
        std::cerr << "NinePSystemTop relaxed-check"
                  << " mismatches=" << bad_count
                  << " first_bad_beat=" << first_bad_beat
                  << " first_bad_lane=" << first_bad_lane
                  << " observed=" << first_bad_obs
                  << " expected=" << first_bad_exp
                  << std::endl;
      }
    } else {
      for (std::size_t beat = 0; beat < golden.beats(); ++beat) {
        report_fp32_mismatch("NinePSystemTop", beat, observed.data() + beat * 12, golden.beat(beat), 12);
      }
    }
    std::cout << "NinePSystemTop PASS beats=" << golden.beats() << std::endl;
    return 0;
  } catch (const std::exception& ex) {
    std::cerr << ex.what() << std::endl;
    return 1;
  }
}
