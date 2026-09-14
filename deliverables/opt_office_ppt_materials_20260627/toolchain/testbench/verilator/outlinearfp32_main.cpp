#include "VOutLinearFP32.h"
#include "VOutLinearFP32_Fp32Add.h"
#include "VOutLinearFP32___024root.h"
#include "common.hpp"
#include <algorithm>
#include <cstdlib>
#include <filesystem>
#include <vector>

int main(int argc, char** argv) {
  try {
    Verilated::commandArgs(argc, argv);
    require(argc == 2, "usage: VOutLinearFP32 <window_dir>");
    const std::filesystem::path window_dir = argv[1];
    const auto cfg = read_cfg(window_dir / "window.cfg");
    const auto data_in = read_words(window_dir / "artifacts" / "data_in.u32.bin", 16);
    const auto weight_init = read_words(window_dir / "artifacts" / "weight_init.u32.bin", 9);
    const auto bias_init = read_words(window_dir / "artifacts" / "bias_init.u32.bin", 12);
    const auto golden = read_words(window_dir / "artifacts" / "golden.u32.bin", 12);
    const bool debug = std::getenv("OUTLINEAR_DEBUG") != nullptr;
    int debug_left = 16;

    VOutLinearFP32 dut;
    dut.io_data_in_valid = 0;
    dut.io_data_in_last = 0;
    dut.io_layer_st = 0;
    dut.io_weight_init_mode = 0;
    dut.io_bias_init_valid = 0;
    dut.io_cfg_prefill = 1;
    dut.io_cfg_seqlen = cfg_int(cfg, "cfg_seqlen");
    dut.io_cfg_valid = 0;
    dut.io_out_scale = cfg_u32(cfg, "out_scale_u32");
    zero_words(dut.io_data_in, 16);
    zero_words(dut.io_weight_init_data, 9);
    zero_words(dut.io_bias_init_data, 12);

    const bool skip_post_weight_reset = std::getenv("OUTLINEAR_SKIP_POST_WEIGHT_RESET") != nullptr;
    if (!skip_post_weight_reset) {
      reset_dut(dut);
    }

    std::vector<bool> seen_weight(weight_init.beats(), false);
    dut.io_weight_init_mode = 1;
    dut.io_layer_st = 1;
    for (int cycle = 0; cycle < static_cast<int>(weight_init.beats() * 4); ++cycle) {
      const std::size_t addr = dut.io_weight_init_addr;
      if (addr < weight_init.beats()) {
        copy_words(dut.io_weight_init_data, weight_init.beat(addr), 9);
        seen_weight[addr] = true;
      } else {
        zero_words(dut.io_weight_init_data, 9);
      }
      tick(dut);
      if (std::find(seen_weight.begin(), seen_weight.end(), false) == seen_weight.end()) {
        break;
      }
    }
    require(
        std::find(seen_weight.begin(), seen_weight.end(), false) == seen_weight.end(),
        "OutLinearFP32 weight init did not cover all addresses");
    dut.io_weight_init_mode = 0;
    dut.io_layer_st = 0;
    zero_words(dut.io_weight_init_data, 9);
    tick(dut);

    reset_dut(dut);
    dut.io_cfg_prefill = 1;
    dut.io_cfg_seqlen = cfg_int(cfg, "cfg_seqlen");
    dut.io_cfg_valid = 0;
    dut.io_out_scale = cfg_u32(cfg, "out_scale_u32");
    for (std::size_t beat = 0; beat < bias_init.beats(); ++beat) {
      copy_words(dut.io_bias_init_data, bias_init.beat(beat), 12);
      dut.io_bias_init_valid = 1;
      tick(dut);
    }
    dut.io_bias_init_valid = 0;
    zero_words(dut.io_bias_init_data, 12);

    const std::size_t token_count = static_cast<std::size_t>(cfg_int(cfg, "token_count"));
    for (std::size_t beat = 0; beat < data_in.beats(); ++beat) {
      copy_words(dut.io_data_in, data_in.beat(beat), 16);
      dut.io_data_in_addr = beat % token_count;
      dut.io_data_in_valid = 1;
      dut.io_data_in_last = ((beat % token_count) + 1 == token_count);
      tick(dut);
    }
    dut.io_data_in_valid = 0;
    dut.io_data_in_last = 0;
    zero_words(dut.io_data_in, 16);

    const bool top_like_run_order = std::getenv("OUTLINEAR_TOP_LIKE_RUN_ORDER") != nullptr;
    if (top_like_run_order) {
      dut.io_cfg_prefill = 1;
      dut.io_cfg_seqlen = cfg_int(cfg, "cfg_seqlen");
      dut.io_out_scale = cfg_u32(cfg, "out_scale_u32");
      dut.io_cfg_valid = 1;
      tick(dut);
      dut.io_cfg_valid = 0;
      dut.io_layer_st = 1;
      tick(dut);
      dut.io_layer_st = 0;
      for (int cycle = 0; cycle < 64; ++cycle) {
        tick(dut);
      }
    } else {
      dut.io_layer_st = 1;
      tick(dut);
      dut.io_layer_st = 0;
      for (int cycle = 0; cycle < 28; ++cycle) {
        tick(dut);
      }

      dut.io_cfg_prefill = 1;
      dut.io_cfg_seqlen = cfg_int(cfg, "cfg_seqlen");
      dut.io_out_scale = cfg_u32(cfg, "out_scale_u32");
      dut.io_cfg_valid = 1;
      tick(dut);
      dut.io_cfg_valid = 0;
    }

    std::vector<uint32_t> observed(golden.words.size(), 0);
    std::vector<bool> seen(golden.beats(), false);
    bool saw_last = false;

    for (int cycle = 0; cycle < 200000 && std::find(seen.begin(), seen.end(), false) != seen.end(); ++cycle) {
      tick(dut);
      if (debug && debug_left > 0 && dut.io_data_out_valid) {
        const auto* pipe_words =
            &dut.rootp->OutLinearFP32__DOT__cu_inst__DOT__indata_pipreg__DOT__pipData_2_REG[0];
        const auto* su_words = &dut.rootp->OutLinearFP32__DOT__su_inst__DOT__io_data_out_REG[0];
        const auto* bias_words = &dut.rootp->OutLinearFP32__DOT____Vcellinp__bias_add__io_b[0];
        const auto final0 = dut.rootp->__PVT__OutLinearFP32__DOT__bias_add__DOT__add->io_out;
        const auto final1 = dut.rootp->__PVT__OutLinearFP32__DOT__bias_add__DOT__add_1->io_out;
        std::cerr << "OutLinear dbg"
                  << " lu_valid=" << static_cast<int>(dut.rootp->OutLinearFP32__DOT__lu_inst__DOT__io_data_out_valid_REG)
                  << " out_valid=" << static_cast<int>(dut.io_data_out_valid)
                  << " feed_token=" << static_cast<int>(dut.rootp->OutLinearFP32__DOT__feed_token_cnt)
                  << " feed_chunk=" << static_cast<int>(dut.rootp->OutLinearFP32__DOT__feed_chunk_cnt)
                  << " head_cnt=" << static_cast<int>(dut.rootp->OutLinearFP32__DOT__head_cnt)
                  << " w_lane0=" << static_cast<int>(
                         static_cast<int8_t>(dut.rootp->OutLinearFP32__DOT__cu_inst__DOT____Vcellinp__mul_list_0_0__io_in1))
                  << " pipe2=" << hex_words(pipe_words, 3)
                  << " su0=0x" << std::hex << su_words[0]
                  << " bias0=0x" << bias_words[0]
                  << " out_addr=" << dut.io_data_out_addr
                  << " final0=0x" << final0
                  << " final1=0x" << final1
                  << " out0=0x" << dut.io_data_out[0]
                  << " out1=0x" << dut.io_data_out[1]
                  << std::dec
                  << std::endl;
        --debug_left;
      }
      if (!dut.io_data_out_valid) {
        continue;
      }
      const std::size_t addr = dut.io_data_out_addr;
      require(addr < golden.beats(), "OutLinearFP32 output addr out of range");
      copy_words(observed.data() + addr * 12, dut.io_data_out, 12);
      seen[addr] = true;
      if (dut.io_data_out_last) {
        saw_last = true;
      }
    }

    require(std::find(seen.begin(), seen.end(), false) == seen.end(), "missing OutLinearFP32 output beats");
    require(saw_last, "OutLinearFP32 never asserted io_data_out_last");
    for (std::size_t beat = 0; beat < golden.beats(); ++beat) {
      report_fp32_mismatch("OutLinearFP32", beat, observed.data() + beat * 12, golden.beat(beat), 12);
    }
    std::cout << "OutLinearFP32 PASS beats=" << golden.beats() << std::endl;
    return 0;
  } catch (const std::exception& ex) {
    std::cerr << ex.what() << std::endl;
    return 1;
  }
}
