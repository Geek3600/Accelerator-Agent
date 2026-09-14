#include "VMigSystemTop.h"
#include "VMigSystemTop___024root.h"
#include "common.hpp"
#include <algorithm>
#include <cstdint>
#include <deque>
#include <filesystem>
#include <vector>

namespace {

struct PendingRead {
  int cycles_left;
  std::size_t addr;
};

void drive_mig_idle(VMigSystemTop& dut) {
  dut.io_app_rdy = 1;
  dut.io_init_calib_complete = 1;
  dut.io_app_rd_data_valid = 0;
  dut.io_app_rd_data_end = 0;
  zero_words(dut.io_app_rd_data, 16);
}

}  // namespace

int main(int argc, char** argv) {
  try {
    Verilated::commandArgs(argc, argv);
    require(argc == 2, "usage: VMigSystemTop <window_dir>");
    const std::filesystem::path window_dir = argv[1];
    const auto cfg = read_cfg(window_dir / "window.cfg");
    const auto ddr_image = read_words(window_dir / "artifacts" / "ddr_image.u32.bin", 16);
    const auto golden = read_words(window_dir / "artifacts" / "golden.u32.bin", 12);
    const bool debug = std::getenv("SYSTEM_DEBUG") != nullptr;
    const int ddr_latency = 4;

    VMigSystemTop dut;
    dut.io_start = 0;
    dut.io_cfg_seqlen = cfg_int(cfg, "cfg_seqlen");
    dut.io_cfg_prefill = 1;
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
    drive_mig_idle(dut);

    reset_dut(dut);
    drive_mig_idle(dut);
    dut.io_start = 1;
    tick(dut);
    dut.io_start = 0;

    std::deque<PendingRead> pending_reads;
    std::vector<uint32_t> observed(golden.words.size(), 0);
    std::vector<bool> seen(golden.beats(), false);
    bool saw_st = false;
    bool saw_last = false;

    for (int cycle = 0; cycle < 5000000 &&
                            !std::all_of(seen.begin(), seen.end(), [](bool v) { return v; });
         ++cycle) {
      if (dut.io_app_en && dut.io_app_rdy && dut.io_app_cmd == 1) {
        require(dut.io_app_addr < ddr_image.beats(), "MIG read addr out of range");
        pending_reads.push_back(PendingRead{ddr_latency, static_cast<std::size_t>(dut.io_app_addr)});
      }

      drive_mig_idle(dut);
      if (!pending_reads.empty() && pending_reads.front().cycles_left <= 0) {
        copy_words(dut.io_app_rd_data, ddr_image.beat(pending_reads.front().addr), 16);
        dut.io_app_rd_data_valid = 1;
        dut.io_app_rd_data_end = 1;
        pending_reads.pop_front();
      }

      tick(dut);

      for (auto& req : pending_reads) {
        --req.cycles_left;
      }

      if (dut.io_res_valid) {
        const std::size_t addr = dut.io_res_addr;
        require(addr < golden.beats(), "MigSystemTop output addr out of range");
        copy_words(observed.data() + addr * 12, dut.io_res, 12);
        seen[addr] = true;
        saw_st = saw_st || dut.io_res_st;
        saw_last = saw_last || dut.io_res_last;
      }

      if (debug && cycle > 0 && (cycle % 1000) == 0) {
        std::cerr << "SystemTop progress"
                  << " cycle=" << cycle
                  << " state=" << static_cast<int>(dut.rootp->MigSystemTop__DOT__state)
                  << " app_en=" << static_cast<int>(dut.io_app_en)
                  << " app_addr=" << dut.io_app_addr
                  << " pending=" << pending_reads.size()
                  << " res_valid=" << static_cast<int>(dut.io_res_valid)
                  << std::endl;
      }
    }

    require(
        std::all_of(seen.begin(), seen.end(), [](bool v) { return v; }),
        "missing MigSystemTop output beats");
    require(saw_st, "MigSystemTop never asserted io_res_st");
    require(saw_last, "MigSystemTop never asserted io_res_last");
    for (std::size_t beat = 0; beat < golden.beats(); ++beat) {
      report_fp32_mismatch("MigSystemTop", beat, observed.data() + beat * 12, golden.beat(beat), 12);
    }
    std::cout << "MigSystemTop PASS beats=" << golden.beats() << std::endl;
    return 0;
  } catch (const std::exception& ex) {
    std::cerr << ex.what() << std::endl;
    return 1;
  }
}
