#include "VLayerNormQ.h"
#include "common.hpp"
#include <filesystem>
#include <vector>

int main(int argc, char** argv) {
  try {
    Verilated::commandArgs(argc, argv);
    require(argc == 2, "usage: VLayerNormQ <window_dir>");
    const std::filesystem::path window_dir = argv[1];
    const auto cfg = read_cfg(window_dir / "window.cfg");
    const auto data_in = read_words(window_dir / "artifacts" / "data_in.u32.bin", 12);
    const auto weights = read_words(window_dir / "artifacts" / "weights.u32.bin", 12);
    const auto golden = read_words(window_dir / "artifacts" / "golden.u32.bin", 3);
    require(weights.beats() == 128, "LayerNormQ expects 128 weight beats");
    require(data_in.beats() == golden.beats(), "LayerNormQ input/output beat count mismatch");

    VLayerNormQ dut;
    dut.io_data_valid = 0;
    dut.io_data_last = 0;
    dut.io_w_valid = 0;
    dut.io_out_inv_scale = cfg_u32(cfg, "out_inv_scale_u32");
    dut.io_out_zero_point = static_cast<uint8_t>(cfg_int(cfg, "out_zero_point_s8"));
    zero_words(dut.io_data_in, 12);
    zero_words(dut.io_w_in, 12);

    reset_dut(dut);

    for (std::size_t beat = 0; beat < weights.beats(); ++beat) {
      copy_words(dut.io_w_in, weights.beat(beat), 12);
      dut.io_w_valid = 1;
      tick(dut);
    }
    dut.io_w_valid = 0;
    zero_words(dut.io_w_in, 12);

    std::vector<uint32_t> observed(golden.words.size(), 0);
    std::vector<bool> seen(golden.beats(), false);
    bool saw_last = false;
    auto capture = [&]() {
      if (!dut.io_res_valid) {
        return;
      }
      const std::size_t addr = dut.io_res_addr;
      require(addr < golden.beats(), "observed res addr out of range");
      copy_words(observed.data() + addr * 3, dut.io_res, 3);
      seen[addr] = true;
      if (dut.io_res_last) {
        saw_last = true;
      }
    };

    for (std::size_t beat = 0; beat < data_in.beats(); ++beat) {
      copy_words(dut.io_data_in, data_in.beat(beat), 12);
      dut.io_data_addr = beat;
      dut.io_data_valid = 1;
      dut.io_data_last = (beat + 1 == data_in.beats());
      tick(dut);
      capture();
    }
    dut.io_data_valid = 0;
    dut.io_data_last = 0;
    zero_words(dut.io_data_in, 12);

    for (int cycle = 0; cycle < 20000 && std::find(seen.begin(), seen.end(), false) != seen.end(); ++cycle) {
      tick(dut);
      capture();
    }

    require(std::find(seen.begin(), seen.end(), false) == seen.end(), "missing LayerNormQ output beats");
    require(saw_last, "LayerNormQ never asserted io_res_last");
    for (std::size_t beat = 0; beat < golden.beats(); ++beat) {
      report_int8_mismatch("LayerNormQ", beat, observed.data() + beat * 3, golden.beat(beat), 3, 12);
    }
    std::cout << "LayerNormQ PASS beats=" << golden.beats() << std::endl;
    return 0;
  } catch (const std::exception& ex) {
    std::cerr << ex.what() << std::endl;
    return 1;
  }
}
