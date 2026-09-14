#include "VDM2Quant.h"
#include "VDM2Quant___024root.h"
#include "common.hpp"
#include <algorithm>
#include <cstdlib>
#include <filesystem>
#include <vector>

int main(int argc, char** argv) {
  try {
    Verilated::commandArgs(argc, argv);
    require(argc == 2, "usage: VDM2Quant <window_dir>");
    const std::filesystem::path window_dir = argv[1];
    const auto cfg = read_cfg(window_dir / "window.cfg");
    const auto ctx_in = read_words(window_dir / "artifacts" / "ctx_in.u32.bin", 26);
    const auto v_in = read_words(window_dir / "artifacts" / "v_in.u32.bin", 16);
    const auto golden = read_words(window_dir / "artifacts" / "golden.u32.bin", 16);
    const bool debug = std::getenv("DM2_DEBUG") != nullptr;
    const auto cfg_prefill = cfg.count("cfg_prefill") ? static_cast<uint32_t>(cfg_int(cfg, "cfg_prefill")) : 1U;
    const auto cfg_single_query =
        cfg.count("cfg_single_query") ? static_cast<uint32_t>(cfg_int(cfg, "cfg_single_query")) : 0U;

    VDM2Quant dut;
    dut.io_cfg_prefill = cfg_prefill;
    dut.io_cfg_seqlen = cfg_int(cfg, "cfg_seqlen");
    dut.io_cfg_single_query = cfg_single_query;
    dut.io_cfg_valid = 0;
    dut.io_ctx_inv_scale = cfg_u32(cfg, "ctx_inv_scale_u32");
    dut.io_ctx_zero_point = cfg_u32(cfg, "ctx_zero_point_u8");
    dut.io_out_inv_scale = cfg_u32(cfg, "out_inv_scale_u32");
    dut.io_data_in_v_valid = 0;
    dut.io_data_in_ctx_st = 0;
    dut.io_data_in_ctx_valid = 0;
    dut.io_res_ready = 1;
    zero_words(dut.io_data_in_v, 16);
    zero_words(dut.io_data_in_ctx, 26);

    reset_dut(dut);

    dut.io_cfg_valid = 1;
    tick(dut);
    dut.io_cfg_valid = 0;

    std::size_t v_beat = 0;
    std::size_t ctx_beat = 0;
    int feed_cycle = 0;
    while (v_beat < v_in.beats() || ctx_beat < ctx_in.beats()) {
      if (v_beat < v_in.beats()) {
        copy_words(dut.io_data_in_v, v_in.beat(v_beat), 16);
        dut.io_data_in_v_valid = 1;
      } else {
        dut.io_data_in_v_valid = 0;
        zero_words(dut.io_data_in_v, 16);
      }

      if (ctx_beat < ctx_in.beats()) {
        copy_words(dut.io_data_in_ctx, ctx_in.beat(ctx_beat), 26);
        dut.io_data_in_ctx_st = (ctx_beat == 0);
        dut.io_data_in_ctx_valid = 1;
      } else {
        dut.io_data_in_ctx_st = 0;
        dut.io_data_in_ctx_valid = 0;
        zero_words(dut.io_data_in_ctx, 26);
      }

      tick(dut);
      if (debug && ((feed_cycle < 96) || ((feed_cycle % 2000) == 0))) {
        auto* root = dut.rootp;
        std::cerr << "dm2_feed cycle=" << feed_cycle
                  << " v_beat=" << v_beat << "/" << v_in.beats()
                  << " ctx_beat=" << ctx_beat << "/" << ctx_in.beats()
                  << " v_ready=" << static_cast<unsigned>(dut.io_data_in_v_ready)
                  << " ctx_ready=" << static_cast<unsigned>(dut.io_data_in_ctx_ready)
                  << " state=" << static_cast<unsigned>(root->DM2Quant__DOT__dmInst__DOT__state)
                  << " tileBase=" << static_cast<unsigned>(root->DM2Quant__DOT__dmInst__DOT__tileBase)
                  << " tileLoadCnt=" << static_cast<unsigned>(root->DM2Quant__DOT__dmInst__DOT__tileLoadCnt)
                  << " waitctxCnt=" << static_cast<unsigned>(root->DM2Quant__DOT__dmInst__DOT__waitctxCnt)
                  << " ctxPipeLast=" << static_cast<unsigned>(root->DM2Quant__DOT__ctxQuantValidPipe_27)
                  << " realCtxFire=" << static_cast<unsigned>(root->DM2Quant__DOT__unnamedblk1__DOT__realCtxFire)
                  << std::endl;
      }
      if (v_beat < v_in.beats() && dut.io_data_in_v_ready) {
        ++v_beat;
      }
      if (ctx_beat < ctx_in.beats() && dut.io_data_in_ctx_ready) {
        ++ctx_beat;
      }
      ++feed_cycle;
    }
    dut.io_data_in_v_valid = 0;
    dut.io_data_in_ctx_st = 0;
    dut.io_data_in_ctx_valid = 0;
    zero_words(dut.io_data_in_v, 16);
    zero_words(dut.io_data_in_ctx, 26);

    dut.io_cfg_prefill = cfg_prefill;
    dut.io_cfg_seqlen = cfg_int(cfg, "cfg_seqlen");
    dut.io_cfg_single_query = cfg_single_query;
    dut.io_cfg_valid = 0;
    dut.io_ctx_inv_scale = cfg_u32(cfg, "ctx_inv_scale_u32");
    dut.io_ctx_zero_point = cfg_u32(cfg, "ctx_zero_point_u8");
    dut.io_out_inv_scale = cfg_u32(cfg, "out_inv_scale_u32");
    dut.io_res_ready = 1;

    std::vector<uint32_t> observed(golden.words.size(), 0);
    std::vector<bool> seen(golden.beats(), false);
    bool saw_last = false;
    std::size_t observed_seq_beats = 0;

    for (int cycle = 0; cycle < 200000 && std::find(seen.begin(), seen.end(), false) != seen.end(); ++cycle) {
      tick(dut);
      if (debug && ((cycle < 64) || ((cycle % 2000) == 0))) {
        auto* root = dut.rootp;
        std::cerr << "dm2_dbg cycle=" << cycle
                  << " state=" << static_cast<unsigned>(root->DM2Quant__DOT__dmInst__DOT__state)
                  << " tileBase=" << static_cast<unsigned>(root->DM2Quant__DOT__dmInst__DOT__tileBase)
                  << " tileLoadCnt=" << static_cast<unsigned>(root->DM2Quant__DOT__dmInst__DOT__tileLoadCnt)
                  << " tileCount=" << static_cast<unsigned>(root->DM2Quant__DOT__dmInst__DOT___tileCount_T_1)
                  << " tileFinal=" << static_cast<unsigned>(root->DM2Quant__DOT__dmInst__DOT__tileFinal)
                  << " waitctxCnt=" << static_cast<unsigned>(root->DM2Quant__DOT__dmInst__DOT__waitctxCnt)
                  << " mulCnt=" << static_cast<unsigned>(root->DM2Quant__DOT__dmInst__DOT__mulCnt)
                  << " v_valid=" << static_cast<unsigned>(dut.io_data_in_v_valid)
                  << " v_ready=" << static_cast<unsigned>(dut.io_data_in_v_ready)
                  << " ctx_valid=" << static_cast<unsigned>(dut.io_data_in_ctx_valid)
                  << " ctx_ready=" << static_cast<unsigned>(dut.io_data_in_ctx_ready)
                  << " realCtxFire=" << static_cast<unsigned>(root->DM2Quant__DOT__unnamedblk1__DOT__realCtxFire)
                  << " ctxQValid=" << static_cast<unsigned>(root->DM2Quant__DOT____Vcellinp__dmInst__io_data_in_ctx_valid)
                  << " vQValid=" << static_cast<unsigned>(root->DM2Quant__DOT____Vcellinp__dmInst__io_data_in_v_valid)
                  << " ctxPad=" << static_cast<unsigned>(root->DM2Quant__DOT__decodeCtxPadFire)
                  << " ctxPadWait=" << static_cast<unsigned>(root->DM2Quant__DOT__decodeCtxPadWait)
                  << " ctxPipeLast=" << static_cast<unsigned>(root->DM2Quant__DOT__ctxQuantValidPipe_27)
                  << " headDone=" << static_cast<unsigned>(root->DM2Quant__DOT__dmInst__DOT__headOutDone_REG)
                  << " res_valid=" << static_cast<unsigned>(dut.io_res_valid)
                  << " res_last=" << static_cast<unsigned>(dut.io_res_last)
                  << " res_addr=" << static_cast<unsigned>(dut.io_res_addr)
                  << std::endl;
      }
      if (debug && dut.io_res_valid) {
        const auto decode_lane = [](const uint32_t* words, int lane) {
          const uint32_t word = words[lane / 4];
          const uint32_t byte = (word >> (8 * (lane % 4))) & 0xffU;
          return static_cast<int>(static_cast<int8_t>(byte));
        };
        std::cerr << "DM2 res"
                  << " valid=" << static_cast<int>(dut.io_res_valid)
                  << " last=" << static_cast<int>(dut.io_res_last)
                  << " addr=" << static_cast<int>(dut.io_res_addr)
                  << " out0=" << decode_lane(dut.io_res, 0)
                  << std::endl;
      }
      if (!dut.io_res_valid) {
        continue;
      }
      if (cfg_single_query) {
        require(observed_seq_beats < golden.beats(), "DM2Quant emitted too many single-query output beats");
        copy_words(observed.data() + observed_seq_beats * 16, dut.io_res, 16);
        seen[observed_seq_beats] = true;
        ++observed_seq_beats;
      } else {
        const std::size_t addr = dut.io_res_addr;
        require(addr < golden.beats(), "DM2Quant output addr out of range");
        copy_words(observed.data() + addr * 16, dut.io_res, 16);
        seen[addr] = true;
      }
      if (dut.io_res_last) {
        saw_last = true;
      }
    }

    require(std::find(seen.begin(), seen.end(), false) == seen.end(), "missing DM2Quant output beats");
    require(saw_last, "DM2Quant never asserted io_res_last");
    if (debug && golden.beats() > 0) {
      const auto obs = unpack_int8_lanes(observed.data(), 64);
      const auto exp = unpack_int8_lanes(golden.beat(0), 64);
      bool exact_same = true;
      std::size_t diff_lane = 0;
      int diff_obs = 0;
      int diff_exp = 0;
      for (std::size_t lane = 0; lane < 64; ++lane) {
        if (obs[lane] != exp[lane]) {
          exact_same = false;
          diff_lane = lane;
          diff_obs = obs[lane];
          diff_exp = exp[lane];
          break;
        }
      }
      if (exact_same) {
        std::cerr << "DM2Quant beat0 exact match" << std::endl;
      } else {
        std::cerr << "DM2Quant beat0 tolerated diff"
                  << " lane=" << diff_lane
                  << " observed=" << diff_obs
                  << " expected=" << diff_exp
                  << std::endl;
      }
    }
    for (std::size_t beat = 0; beat < golden.beats(); ++beat) {
      report_int8_mismatch("DM2Quant", beat, observed.data() + beat * 16, golden.beat(beat), 16, 64);
    }
    std::cout << "DM2Quant PASS beats=" << golden.beats() << std::endl;
    return 0;
  } catch (const std::exception& ex) {
    std::cerr << ex.what() << std::endl;
    return 1;
  }
}
