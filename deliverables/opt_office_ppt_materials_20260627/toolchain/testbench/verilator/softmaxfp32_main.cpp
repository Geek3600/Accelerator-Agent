#include "VSoftmaxPipFP32.h"
#include "VSoftmaxPipFP32___024root.h"
#include "common.hpp"
#include <algorithm>
#include <cstdlib>
#include <filesystem>
#include <iomanip>
#include <vector>

int main(int argc, char** argv) {
  try {
    Verilated::commandArgs(argc, argv);
    require(argc == 2, "usage: VSoftmaxPipFP32 <window_dir>");
    const std::filesystem::path window_dir = argv[1];
    const auto cfg = read_cfg(window_dir / "window.cfg");
    const auto data_in = read_words(window_dir / "artifacts" / "data_in.u32.bin", 26);
    const auto masks = read_words(window_dir / "artifacts" / "masks.u32.bin", 1);
    const auto golden = read_words(window_dir / "artifacts" / "golden.u32.bin", 26);
    const char* force_beat_env = std::getenv("SOFTMAX_FORCE_BEAT_INDEX");
    const char* force_seqlen_env = std::getenv("SOFTMAX_FORCE_CFG_SEQLEN");
    const char* force_sq_env = std::getenv("SOFTMAX_FORCE_SINGLE_QUERY");
    const bool force_single_beat = (force_beat_env != nullptr);
    const std::size_t force_beat_idx = force_single_beat ? static_cast<std::size_t>(std::stoul(force_beat_env)) : 0;
    const auto cfg_single_query = force_sq_env
                                      ? static_cast<uint32_t>(std::stoul(force_sq_env))
                                      : (cfg.count("cfg_single_query") ? static_cast<uint32_t>(cfg_int(cfg, "cfg_single_query")) : 0U);
    const auto cfg_prefill = cfg.count("cfg_prefill") ? static_cast<uint32_t>(cfg_int(cfg, "cfg_prefill")) : 0U;

    VSoftmaxPipFP32 dut;
    dut.io_cfg_seqlen = force_seqlen_env ? static_cast<uint32_t>(std::stoul(force_seqlen_env))
                                         : cfg_int(cfg, "cfg_seqlen");
    dut.io_cfg_valid = 0;
    dut.io_cfg_prefill = cfg_prefill;
    dut.io_cfg_single_query = cfg_single_query;
    dut.io_layer_st = 0;
    dut.io_data_in_st = 0;
    dut.io_data_valid = 0;
    dut.io_data_last = 0;
    dut.io_res_ready = 1;
    zero_words(dut.io_data_in, 26);
    zero_words(dut.io_w_in, 29);

    reset_dut(dut);

    dut.io_cfg_valid = 1;
    tick(dut);
    dut.io_cfg_valid = 0;

    const std::size_t rows_to_feed = force_single_beat ? 1 : data_in.beats();
    std::size_t feed_idx = 0;
    while (feed_idx < rows_to_feed) {
      if (dut.io_data_ready) {
        const std::size_t src_idx = force_single_beat ? force_beat_idx : feed_idx;
        require(src_idx < data_in.beats(), "SOFTMAX_FORCE_BEAT_INDEX out of range");
        copy_words(dut.io_data_in, data_in.beat(src_idx), 26);
        zero_words(dut.io_w_in, 29);
        dut.io_w_in[0] = masks.beat(src_idx)[0];
        dut.io_data_addr = (force_single_beat || cfg_single_query) ? 0 : feed_idx;
        dut.io_data_in_st = (feed_idx == 0);
        dut.io_data_valid = 1;
        dut.io_data_last = (feed_idx + 1 == rows_to_feed);
        tick(dut);
        ++feed_idx;
      } else {
        dut.io_data_in_st = 0;
        dut.io_data_valid = 0;
        dut.io_data_last = 0;
        zero_words(dut.io_data_in, 26);
        zero_words(dut.io_w_in, 29);
        tick(dut);
      }
    }

    dut.io_data_in_st = 0;
    dut.io_data_valid = 0;
    dut.io_data_last = 0;
    zero_words(dut.io_data_in, 26);
    zero_words(dut.io_w_in, 29);

    const std::size_t golden_beats = force_single_beat ? 1 : golden.beats();
    std::vector<uint32_t> observed(golden_beats * 26, 0);
    std::vector<bool> seen(golden_beats, false);
    bool saw_last = false;
    std::size_t observed_seq_beats = 0;

    for (int cycle = 0; cycle < 200000 && std::find(seen.begin(), seen.end(), false) != seen.end(); ++cycle) {
      tick(dut);
      if ((cycle < 64) || ((cycle % 2000) == 0)) {
        auto* root = dut.rootp;
        std::cout << "softmax_dbg cycle=" << cycle
                  << " state=" << static_cast<unsigned>(root->SoftmaxPipFP32__DOT__state)
                  << " data_ready=" << static_cast<unsigned>(dut.io_data_ready)
                  << " data_valid=" << static_cast<unsigned>(dut.io_data_valid)
                  << " res_valid=" << static_cast<unsigned>(dut.io_res_valid)
                  << " res_last=" << static_cast<unsigned>(dut.io_res_last)
                  << " res_addr=" << static_cast<unsigned>(dut.io_res_addr)
                  << " maskAddr=" << static_cast<unsigned>(root->SoftmaxPipFP32__DOT__maskAddrReg)
                  << " rowTiles=" << static_cast<unsigned>(root->SoftmaxPipFP32__DOT__rowTileCountReg)
                  << " tileIdx=" << static_cast<unsigned>(root->SoftmaxPipFP32__DOT__tileIdxReg)
                  << " collectTileIdx=" << static_cast<unsigned>(root->SoftmaxPipFP32__DOT__collectTileIdx)
                  << " outValidReg=" << static_cast<unsigned>(root->SoftmaxPipFP32__DOT__outValidReg)
                  << " globalMax=0x" << std::hex << root->SoftmaxPipFP32__DOT__globalMaxReg
                  << " sumExp=0x" << root->SoftmaxPipFP32__DOT__sumExpReg
                  << " invSum=0x" << root->SoftmaxPipFP32__DOT__invSumReg
                  << std::dec
                  << std::endl;
      }
      if (!dut.io_res_valid) {
        continue;
      }
      if (cfg_single_query) {
        require(observed_seq_beats < golden_beats, "SoftmaxPipFP32 emitted too many single-query output beats");
        copy_words(observed.data() + observed_seq_beats * 26, dut.io_res, 26);
        seen[observed_seq_beats] = true;
        ++observed_seq_beats;
      } else {
        const std::size_t addr = dut.io_res_addr;
        require(addr < golden_beats, "SoftmaxPipFP32 output addr out of range");
        copy_words(observed.data() + addr * 26, dut.io_res, 26);
        seen[addr] = true;
      }
      if (dut.io_res_last) {
        saw_last = true;
      }
    }

    if (std::find(seen.begin(), seen.end(), false) != seen.end()) {
      auto* root = dut.rootp;
      std::cerr << "SoftmaxPipFP32 final state="
                << static_cast<unsigned>(root->SoftmaxPipFP32__DOT__state)
                << " maskAddr=" << static_cast<unsigned>(root->SoftmaxPipFP32__DOT__maskAddrReg)
                << " rowTiles=" << static_cast<unsigned>(root->SoftmaxPipFP32__DOT__rowTileCountReg)
                << " tileIdx=" << static_cast<unsigned>(root->SoftmaxPipFP32__DOT__tileIdxReg)
                << " collectTileIdx=" << static_cast<unsigned>(root->SoftmaxPipFP32__DOT__collectTileIdx)
                << " outValidReg=" << static_cast<unsigned>(root->SoftmaxPipFP32__DOT__outValidReg)
                << " globalMax=0x" << std::hex << root->SoftmaxPipFP32__DOT__globalMaxReg
                << " sumExp=0x" << root->SoftmaxPipFP32__DOT__sumExpReg
                << " invSum=0x" << root->SoftmaxPipFP32__DOT__invSumReg
                << std::dec
                << std::endl;
    }
    require(std::find(seen.begin(), seen.end(), false) == seen.end(), "missing SoftmaxPipFP32 output beats");
    require(saw_last, "SoftmaxPipFP32 never asserted io_res_last");
    for (std::size_t beat = 0; beat < golden_beats; ++beat) {
      const std::size_t golden_idx = force_single_beat ? force_beat_idx + beat : beat;
      report_fp32_mismatch("SoftmaxPipFP32", beat, observed.data() + beat * 26, golden.beat(golden_idx), 26);
    }
    std::cout << "SoftmaxPipFP32 PASS beats=" << golden_beats << std::endl;
    return 0;
  } catch (const std::exception& ex) {
    std::cerr << ex.what() << std::endl;
    return 1;
  }
}
