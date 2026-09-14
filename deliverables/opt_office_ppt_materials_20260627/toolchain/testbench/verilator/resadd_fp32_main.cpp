#include "VResAddFP32.h"
#include "common.hpp"
#include <filesystem>
#include <vector>

int main(int argc, char** argv) {
  try {
    Verilated::commandArgs(argc, argv);
    require(argc == 2, "usage: VResAddFP32 <window_dir>");
    const std::filesystem::path window_dir = argv[1];
    const auto cfg = read_cfg(window_dir / "window.cfg");
    const auto lhs = read_words(window_dir / "artifacts" / "lhs.u32.bin", 12);
    const auto rhs = read_words(window_dir / "artifacts" / "rhs.u32.bin", 12);
    const auto golden = read_words(window_dir / "artifacts" / "golden.u32.bin", 12);
    require(lhs.beats() == rhs.beats(), "lhs/rhs beat count mismatch");
    require(lhs.beats() == golden.beats(), "golden beat count mismatch");

    VResAddFP32 dut;
    dut.io_res_ready = 1;
    dut.io_orig_in_valid = 0;
    dut.io_orig_in_last = 0;
    dut.io_dm2_in_valid = 0;
    dut.io_dm2_in_last = 0;
    zero_words(dut.io_orig_in, 12);
    zero_words(dut.io_dm2_in, 12);

    reset_dut(dut);
    std::vector<uint32_t> observed(golden.words.size(), 0);
    std::vector<bool> seen(golden.beats(), false);
    bool saw_last = false;
    auto capture = [&]() {
      if (!dut.io_res_valid) {
        return;
      }
      const std::size_t addr = dut.io_res_addr;
      require(addr < golden.beats(), "observed res addr out of range");
      copy_words(observed.data() + addr * 12, dut.io_res, 12);
      seen[addr] = true;
      if (dut.io_res_last) {
        saw_last = true;
      }
    };

    for (std::size_t beat = 0; beat < lhs.beats(); ++beat) {
      copy_words(dut.io_orig_in, lhs.beat(beat), 12);
      dut.io_orig_in_addr = beat;
      dut.io_orig_in_valid = 1;
      dut.io_orig_in_last = (beat + 1 == lhs.beats());
      tick(dut);
      capture();
    }
    dut.io_orig_in_valid = 0;
    dut.io_orig_in_last = 0;
    zero_words(dut.io_orig_in, 12);

    for (std::size_t beat = 0; beat < rhs.beats(); ++beat) {
      copy_words(dut.io_dm2_in, rhs.beat(beat), 12);
      dut.io_dm2_in_addr = beat;
      dut.io_dm2_in_valid = 1;
      dut.io_dm2_in_last = (beat + 1 == rhs.beats());
      tick(dut);
      capture();
    }
    dut.io_dm2_in_valid = 0;
    dut.io_dm2_in_last = 0;
    zero_words(dut.io_dm2_in, 12);

    for (int cycle = 0; cycle < 256 && std::find(seen.begin(), seen.end(), false) != seen.end(); ++cycle) {
      tick(dut);
      capture();
    }

    require(std::find(seen.begin(), seen.end(), false) == seen.end(), "missing ResAddFP32 output beats");
    require(saw_last, "ResAddFP32 never asserted io_res_last");
    for (std::size_t beat = 0; beat < golden.beats(); ++beat) {
      report_fp32_mismatch("ResAddFP32", beat, observed.data() + beat * 12, golden.beat(beat), 12);
    }
    std::cout << "ResAddFP32 PASS beats=" << golden.beats() << std::endl;
    return 0;
  } catch (const std::exception& ex) {
    std::cerr << ex.what() << std::endl;
    return 1;
  }
}
