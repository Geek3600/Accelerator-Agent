#include "VFFNUp.h"
#include "VFFNUp___024root.h"
#include "common.hpp"
#include <cstdlib>
#include <filesystem>
#include <vector>

int main(int argc, char** argv) {
  try {
    Verilated::commandArgs(argc, argv);
    require(argc == 2, "usage: VFFNUp <window_dir>");
    const std::filesystem::path window_dir = argv[1];
    const auto cfg = read_cfg(window_dir / "window.cfg");
    const auto data_in = read_words(window_dir / "artifacts" / "data_in.u32.bin", 3);
    const auto weight_init = read_words(window_dir / "artifacts" / "weight_init.u32.bin", 9);
    const auto bias_init = read_words(window_dir / "artifacts" / "bias_init.u32.bin", 3);
    const auto golden = read_words(window_dir / "artifacts" / "golden.u32.bin", 3);
    const bool debug = std::getenv("FFNUP_DEBUG") != nullptr;
    int debug_left = 8;
    int debug_input_left = 8;

    VFFNUp dut;
    dut.io_data_in_st = 0;
    dut.io_data_valid = 0;
    dut.io_data_last = 0;
    dut.io_layer_st = 0;
    dut.io_weight_init_mode = 0;
    dut.io_bias_init_valid = 0;
    dut.io_cfg_prefill = 1;
    dut.io_cfg_seqlen = cfg_int(cfg, "cfg_seqlen");
    dut.io_cfg_valid = 0;
    dut.io_data_out_ready = 1;
    dut.io_out_inv_scale = cfg_u32(cfg, "out_inv_scale_u32");
    dut.io_bias_scale = cfg_u32(cfg, "bias_scale_u32");
    zero_words(dut.io_data_in, 3);
    zero_words(dut.io_weight_init_data, 9);
    zero_words(dut.io_bias_init_data, 3);

    reset_dut(dut);

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
    require(std::find(seen_weight.begin(), seen_weight.end(), false) == seen_weight.end(), "FFNUp weight init did not cover all addresses");
    dut.io_weight_init_mode = 0;
    dut.io_layer_st = 0;
    zero_words(dut.io_weight_init_data, 9);
    tick(dut);

    // Keep WeightMem contents, but clear the runtime FSM/counter state.
    reset_dut(dut);
    dut.io_layer_st = 0;
    dut.io_weight_init_mode = 0;
    dut.io_bias_init_valid = 0;
    dut.io_cfg_prefill = 1;
    dut.io_cfg_seqlen = cfg_int(cfg, "cfg_seqlen");
    dut.io_cfg_valid = 0;
    dut.io_data_out_ready = 0;
    dut.io_out_inv_scale = cfg_u32(cfg, "out_inv_scale_u32");
    dut.io_bias_scale = cfg_u32(cfg, "bias_scale_u32");
    dut.io_data_in_st = 0;
    dut.io_data_valid = 0;
    dut.io_data_last = 0;
    zero_words(dut.io_data_in, 3);
    zero_words(dut.io_weight_init_data, 9);
    zero_words(dut.io_bias_init_data, 3);

    for (std::size_t beat = 0; beat < bias_init.beats(); ++beat) {
      copy_words(dut.io_bias_init_data, bias_init.beat(beat), 3);
      dut.io_bias_init_valid = 1;
      tick(dut);
    }
    dut.io_bias_init_valid = 0;
    zero_words(dut.io_bias_init_data, 3);

    // Write input data to DataMem
    for (std::size_t beat = 0; beat < data_in.beats(); ++beat) {
      copy_words(dut.io_data_in, data_in.beat(beat), 3);
      dut.io_data_addr = beat;
      dut.io_data_in_st = (beat == 0);
      dut.io_data_valid = 1;
      dut.io_data_last = (beat + 1 == data_in.beats());
      tick(dut);
    }
    dut.io_data_in_st = 0;
    dut.io_data_valid = 0;
    dut.io_data_last = 0;
    zero_words(dut.io_data_in, 3);

    // Trigger LoadWeight preload (2 tiles = 24 beats)
    dut.io_layer_st = 1;
    tick(dut);
    dut.io_layer_st = 0;

    for (int cycle = 0; cycle < 28; ++cycle) {
      tick(dut);
    }

    // Enable config and start real run
    dut.io_cfg_prefill = 1;
    dut.io_cfg_seqlen = cfg_int(cfg, "cfg_seqlen");
    dut.io_out_inv_scale = cfg_u32(cfg, "out_inv_scale_u32");
    dut.io_bias_scale = cfg_u32(cfg, "bias_scale_u32");
    dut.io_cfg_valid = 1;
    dut.io_data_out_ready = 1;
    tick(dut);
    dut.io_cfg_valid = 0;

    std::vector<uint32_t> observed(golden.words.size(), 0);
    std::vector<bool> seen(golden.beats(), false);
    bool saw_last = false;
    auto capture = [&]() {
      if (!dut.io_data_out_valid) {
        return;
      }
      const std::size_t addr = dut.io_data_out_addr;
      require(addr < golden.beats(), "FFNUp output addr out of range");
      copy_words(observed.data() + addr * 3, dut.io_data_out, 3);
      seen[addr] = true;
      if (debug && debug_left > 0) {
        const auto* su_words = &dut.rootp->FFNUp__DOT__su_inst__DOT__io_data_out_REG[0];
        std::cerr << "FFNUp debug beat=" << addr
                  << " final=" << hex_words(dut.io_data_out, 3)
                  << " su=" << hex_words(su_words, 3)
                  << " golden=" << hex_words(golden.beat(addr), 3)
                  << " cu_block=" << static_cast<int>(dut.rootp->FFNUp__DOT__cu_inst__DOT__block_cnt_r)
                  << " lw_rowblock=" << static_cast<int>(dut.rootp->FFNUp__DOT__lw_inst__DOT__rowblock_cnt_r)
                  << " lw_colblock=" << static_cast<int>(dut.rootp->FFNUp__DOT__lw_inst__DOT__colblock_cnt_r)
                  << std::endl;
        --debug_left;
      }
      if (dut.io_data_out_last) {
        saw_last = true;
      }
    };

    for (int cycle = 0; cycle < 200000 && std::find(seen.begin(), seen.end(), false) != seen.end(); ++cycle) {
      tick(dut);
      if (debug && debug_input_left > 0 && dut.rootp->FFNUp__DOT__lu_inst__DOT__io_data_out_valid_REG) {
        const auto* pipe_words =
            &dut.rootp->FFNUp__DOT__cu_inst__DOT__indata_pipreg__DOT__pipData_2_REG[0];
        std::cerr << "FFNUp input sample=" << (8 - debug_input_left)
                  << " lu_addr=" << dut.rootp->FFNUp__DOT___lu_inst_io_data_in_addr
                  << " pipe2=" << hex_words(pipe_words, 3)
                  << " w_lane0=" << static_cast<int>(
                         static_cast<int8_t>(dut.rootp->FFNUp__DOT__cu_inst__DOT____Vcellinp__mul_list_0_0__io_in1))
                  << " lw_rowblock=" << static_cast<int>(dut.rootp->FFNUp__DOT__lw_inst__DOT__rowblock_cnt_r)
                  << " lw_colblock=" << static_cast<int>(dut.rootp->FFNUp__DOT__lw_inst__DOT__colblock_cnt_r)
                  << std::endl;
        --debug_input_left;
      }
      capture();
    }

    require(std::find(seen.begin(), seen.end(), false) == seen.end(), "missing FFNUp output beats");
    require(saw_last, "FFNUp never asserted io_data_out_last");
    bool reported_tolerated_diff = false;
    for (std::size_t beat = 0; beat < golden.beats(); ++beat) {
      if (!reported_tolerated_diff) {
        const auto obs = unpack_int8_lanes(observed.data() + beat * 3, 12);
        const auto exp = unpack_int8_lanes(golden.beat(beat), 12);
        for (std::size_t lane = 0; lane < 12; ++lane) {
          if (obs[lane] != exp[lane]) {
            std::cerr << "FFNUp tolerated diff"
                      << " beat=" << beat
                      << " lane=" << lane
                      << " observed=" << obs[lane]
                      << " expected=" << exp[lane]
                      << std::endl;
            reported_tolerated_diff = true;
            break;
          }
        }
      }
      report_int8_mismatch("FFNUp", beat, observed.data() + beat * 3, golden.beat(beat), 3, 12);
    }
    std::cout << "FFNUp PASS beats=" << golden.beats() << std::endl;
    return 0;
  } catch (const std::exception& ex) {
    std::cerr << ex.what() << std::endl;
    return 1;
  }
}
