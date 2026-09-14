#include "VTop.h"
#include "common.hpp"
#include <algorithm>
#include <filesystem>
#include <vector>

namespace {

void drive_from_ddr(
    VTop& dut,
    const PackedWords& data_in,
    const PackedWords& qkv_weight_init,
    const PackedWords& sm_masks,
    const PackedWords& out_weight_init,
    const PackedWords& ffnup_weight_init,
    const PackedWords& ffndown_weight_init) {
  if (dut.io_data_in_addr < data_in.beats()) {
    copy_words(dut.io_data_in, data_in.beat(dut.io_data_in_addr), 12);
  } else {
    zero_words(dut.io_data_in, 12);
  }

  if (dut.io_qkv_w_addr < qkv_weight_init.beats()) {
    copy_words(dut.io_qkv_w_in, qkv_weight_init.beat(dut.io_qkv_w_addr), 9);
  } else {
    zero_words(dut.io_qkv_w_in, 9);
  }

  zero_words(dut.io_sm_w_in, 29);
  if (dut.io_sm_w_addr < sm_masks.beats()) {
    dut.io_sm_w_in[0] = sm_masks.beat(dut.io_sm_w_addr)[0];
  }

  if (dut.io_out_w_addr < out_weight_init.beats()) {
    copy_words(dut.io_out_w_in, out_weight_init.beat(dut.io_out_w_addr), 9);
  } else {
    zero_words(dut.io_out_w_in, 9);
  }

  if (dut.io_ffnup_w_addr < ffnup_weight_init.beats()) {
    copy_words(dut.io_ffnup_w_in, ffnup_weight_init.beat(dut.io_ffnup_w_addr), 9);
  } else {
    zero_words(dut.io_ffnup_w_in, 9);
  }

  if (dut.io_ffndown_w_addr < ffndown_weight_init.beats()) {
    copy_words(dut.io_ffndown_w_in, ffndown_weight_init.beat(dut.io_ffndown_w_addr), 9);
  } else {
    zero_words(dut.io_ffndown_w_in, 9);
  }
}

template <typename Dut>
void tick_with_ddr(
    Dut& dut,
    const PackedWords& data_in,
    const PackedWords& qkv_weight_init,
    const PackedWords& sm_masks,
    const PackedWords& out_weight_init,
    const PackedWords& ffnup_weight_init,
    const PackedWords& ffndown_weight_init) {
  drive_from_ddr(dut, data_in, qkv_weight_init, sm_masks, out_weight_init, ffnup_weight_init, ffndown_weight_init);
  tick(dut);
}

template <typename Dut>
void reset_with_ddr(
    Dut& dut,
    const PackedWords& data_in,
    const PackedWords& qkv_weight_init,
    const PackedWords& sm_masks,
    const PackedWords& out_weight_init,
    const PackedWords& ffnup_weight_init,
    const PackedWords& ffndown_weight_init,
    int cycles = 5) {
  dut.reset = 1;
  for (int idx = 0; idx < cycles; ++idx) {
    tick_with_ddr(dut, data_in, qkv_weight_init, sm_masks, out_weight_init, ffnup_weight_init, ffndown_weight_init);
  }
  dut.reset = 0;
  tick_with_ddr(dut, data_in, qkv_weight_init, sm_masks, out_weight_init, ffnup_weight_init, ffndown_weight_init);
}

template <typename Dut>
void stream_words(
    Dut& dut,
    uint32_t* port,
    CData& valid,
    const PackedWords& data,
    std::size_t words_per_beat,
    const PackedWords& data_in,
    const PackedWords& qkv_weight_init,
    const PackedWords& sm_masks,
    const PackedWords& out_weight_init,
    const PackedWords& ffnup_weight_init,
    const PackedWords& ffndown_weight_init) {
  for (std::size_t beat = 0; beat < data.beats(); ++beat) {
    copy_words(port, data.beat(beat), words_per_beat);
    valid = 1;
    tick_with_ddr(dut, data_in, qkv_weight_init, sm_masks, out_weight_init, ffnup_weight_init, ffndown_weight_init);
  }
  valid = 0;
  zero_words(port, words_per_beat);
}

bool all_seen(const std::vector<bool>& seen) {
  return std::find(seen.begin(), seen.end(), false) == seen.end();
}

}  // namespace

int main(int argc, char** argv) {
  try {
    Verilated::commandArgs(argc, argv);
    require(argc == 2, "usage: VTop <window_dir>");
    const std::filesystem::path window_dir = argv[1];
    const auto cfg = read_cfg(window_dir / "window.cfg");

    const auto data_in = read_words(window_dir / "artifacts" / "data_in.u32.bin", 12);
    const auto ln1_weights = read_words(window_dir / "artifacts" / "ln1_weights.u32.bin", 12);
    const auto ln2_weights = read_words(window_dir / "artifacts" / "ln2_weights.u32.bin", 12);
    const auto qkv_weight_init = read_words(window_dir / "artifacts" / "qkv_weight_init.u32.bin", 9);
    const auto qkv_bias_init = read_words(window_dir / "artifacts" / "qkv_bias_init.u32.bin", 3);
    const auto sm_masks = read_words(window_dir / "artifacts" / "sm_masks.u32.bin", 1);
    const auto out_weight_init = read_words(window_dir / "artifacts" / "out_weight_init.u32.bin", 9);
    const auto out_bias_init = read_words(window_dir / "artifacts" / "out_bias_init.u32.bin", 12);
    const auto ffnup_weight_init = read_words(window_dir / "artifacts" / "ffnup_weight_init.u32.bin", 9);
    const auto ffnup_bias_init = read_words(window_dir / "artifacts" / "ffnup_bias_init.u32.bin", 3);
    const auto ffndown_weight_init = read_words(window_dir / "artifacts" / "ffndown_weight_init.u32.bin", 9);
    const auto ffndown_bias_init = read_words(window_dir / "artifacts" / "ffndown_bias_init.u32.bin", 12);
    const auto golden = read_words(window_dir / "artifacts" / "golden.u32.bin", 12);

    VTop dut;
    dut.io_layer_st = 0;
    dut.io_cfg_valid = 0;
    dut.io_cfg_prefill = 1;
    dut.io_cfg_seqlen = cfg_int(cfg, "cfg_seqlen");
    dut.io_attn_cfg_valid = 0;
    dut.io_attn_cfg_prefill = 0;
    dut.io_attn_cfg_seqlen = cfg_int(cfg, "cfg_seqlen");
    dut.io_attn_cfg_single_query = 1;
    dut.io_weight_init_mode = 0;
    dut.io_weight_active_bank = 0;
    dut.io_weight_preload_bank = 1;
    dut.io_qkv_w_preload_valid = 0;
    dut.io_out_w_preload_valid = 0;
    dut.io_ffnup_w_preload_valid = 0;
    dut.io_ffndown_w_preload_valid = 0;
    dut.io_data_in_ready = 0;
    dut.io_ln_w_valid = 0;
    dut.io_qkv_b_valid = 0;
    dut.io_out_b_valid = 0;
    dut.io_ln2_w_valid = 0;
    dut.io_ffnup_b_valid = 0;
    dut.io_ffndown_b_valid = 0;
    dut.io_res_ready = 1;

    dut.io_ln1_out_inv_scale = cfg_u32(cfg, "ln1_out_inv_scale_u32");
    dut.io_ln1_out_zero_point = static_cast<int8_t>(cfg_int(cfg, "ln1_out_zero_point_s8"));
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
    dut.io_ln2_out_zero_point = static_cast<int8_t>(cfg_int(cfg, "ln2_out_zero_point_s8"));
    dut.io_ffnup_out_inv_scale = cfg_u32(cfg, "ffnup_out_inv_scale_u32");
    dut.io_ffnup_bias_scale = cfg_u32(cfg, "ffnup_bias_scale_u32");
    dut.io_ffndown_out_scale = cfg_u32(cfg, "ffndown_out_scale_u32");

    zero_words(dut.io_data_in, 12);
    zero_words(dut.io_ln_w_in, 12);
    zero_words(dut.io_qkv_w_in, 9);
    zero_words(dut.io_qkv_b_in, 3);
    zero_words(dut.io_sm_w_in, 29);
    zero_words(dut.io_out_w_in, 9);
    zero_words(dut.io_out_b_in, 12);
    zero_words(dut.io_ln2_w_in, 12);
    zero_words(dut.io_ffnup_w_in, 9);
    zero_words(dut.io_ffnup_b_in, 3);
    zero_words(dut.io_ffndown_w_in, 9);
    zero_words(dut.io_ffndown_b_in, 12);
    zero_words(dut.io_qkv_w_preload_data, 9);
    zero_words(dut.io_out_w_preload_data, 9);
    zero_words(dut.io_ffnup_w_preload_data, 9);
    zero_words(dut.io_ffndown_w_preload_data, 9);

    reset_with_ddr(dut, data_in, qkv_weight_init, sm_masks, out_weight_init, ffnup_weight_init, ffndown_weight_init);

    std::vector<bool> seen_qkv(qkv_weight_init.beats(), false);
    std::vector<bool> seen_out(out_weight_init.beats(), false);
    std::vector<bool> seen_ffnup(ffnup_weight_init.beats(), false);
    std::vector<bool> seen_ffndown(ffndown_weight_init.beats(), false);
    dut.io_weight_init_mode = 1;
    dut.io_layer_st = 1;
    const std::size_t max_weight_cycles =
        std::max({qkv_weight_init.beats(), out_weight_init.beats(), ffnup_weight_init.beats(), ffndown_weight_init.beats()}) * 6;
    for (std::size_t cycle = 0; cycle < max_weight_cycles; ++cycle) {
      if (dut.io_qkv_w_addr < qkv_weight_init.beats()) {
        seen_qkv[dut.io_qkv_w_addr] = true;
      }
      if (dut.io_out_w_addr < out_weight_init.beats()) {
        seen_out[dut.io_out_w_addr] = true;
      }
      if (dut.io_ffnup_w_addr < ffnup_weight_init.beats()) {
        seen_ffnup[dut.io_ffnup_w_addr] = true;
      }
      if (dut.io_ffndown_w_addr < ffndown_weight_init.beats()) {
        seen_ffndown[dut.io_ffndown_w_addr] = true;
      }
      tick_with_ddr(dut, data_in, qkv_weight_init, sm_masks, out_weight_init, ffnup_weight_init, ffndown_weight_init);
      if (all_seen(seen_qkv) && all_seen(seen_out) && all_seen(seen_ffnup) && all_seen(seen_ffndown)) {
        break;
      }
    }
    require(all_seen(seen_qkv), "Top qkv weight init did not cover all addresses");
    require(all_seen(seen_out), "Top out_proj weight init did not cover all addresses");
    require(all_seen(seen_ffnup), "Top ffnup weight init did not cover all addresses");
    require(all_seen(seen_ffndown), "Top ffndown weight init did not cover all addresses");
    dut.io_weight_init_mode = 0;
    dut.io_layer_st = 0;

    reset_with_ddr(dut, data_in, qkv_weight_init, sm_masks, out_weight_init, ffnup_weight_init, ffndown_weight_init);

    stream_words(dut, dut.io_ln_w_in, dut.io_ln_w_valid, ln1_weights, 12, data_in, qkv_weight_init, sm_masks, out_weight_init, ffnup_weight_init, ffndown_weight_init);
    stream_words(dut, dut.io_ln2_w_in, dut.io_ln2_w_valid, ln2_weights, 12, data_in, qkv_weight_init, sm_masks, out_weight_init, ffnup_weight_init, ffndown_weight_init);
    stream_words(dut, dut.io_qkv_b_in, dut.io_qkv_b_valid, qkv_bias_init, 3, data_in, qkv_weight_init, sm_masks, out_weight_init, ffnup_weight_init, ffndown_weight_init);
    stream_words(dut, dut.io_out_b_in, dut.io_out_b_valid, out_bias_init, 12, data_in, qkv_weight_init, sm_masks, out_weight_init, ffnup_weight_init, ffndown_weight_init);
    stream_words(dut, dut.io_ffnup_b_in, dut.io_ffnup_b_valid, ffnup_bias_init, 3, data_in, qkv_weight_init, sm_masks, out_weight_init, ffnup_weight_init, ffndown_weight_init);
    stream_words(dut, dut.io_ffndown_b_in, dut.io_ffndown_b_valid, ffndown_bias_init, 12, data_in, qkv_weight_init, sm_masks, out_weight_init, ffnup_weight_init, ffndown_weight_init);

    dut.io_cfg_valid = 1;
    dut.io_attn_cfg_valid = 1;
    tick_with_ddr(dut, data_in, qkv_weight_init, sm_masks, out_weight_init, ffnup_weight_init, ffndown_weight_init);
    dut.io_cfg_valid = 0;
    dut.io_attn_cfg_valid = 0;
    dut.io_layer_st = 1;
    tick_with_ddr(dut, data_in, qkv_weight_init, sm_masks, out_weight_init, ffnup_weight_init, ffndown_weight_init);
    dut.io_layer_st = 0;

    for (int cycle = 0; cycle < 64; ++cycle) {
      tick_with_ddr(dut, data_in, qkv_weight_init, sm_masks, out_weight_init, ffnup_weight_init, ffndown_weight_init);
    }

    dut.io_data_in_ready = 1;

    std::vector<uint32_t> observed(golden.words.size(), 0);
    std::vector<bool> seen(golden.beats(), false);
    bool saw_last = false;

    for (int cycle = 0; cycle < 2000000 && !all_seen(seen); ++cycle) {
      tick_with_ddr(dut, data_in, qkv_weight_init, sm_masks, out_weight_init, ffnup_weight_init, ffndown_weight_init);
      if ((cycle % 100000) == 0) {
        std::cerr << "Top progress"
                  << " cycle=" << cycle
                  << " in_addr=" << dut.io_data_in_addr
                  << " qkv_w_addr=" << dut.io_qkv_w_addr
                  << " sm_w_addr=" << dut.io_sm_w_addr
                  << " out_w_addr=" << dut.io_out_w_addr
                  << " ffnup_w_addr=" << dut.io_ffnup_w_addr
                  << " ffndown_w_addr=" << dut.io_ffndown_w_addr
                  << " res_valid=" << static_cast<int>(dut.io_res_valid)
                  << " res_addr=" << static_cast<int>(dut.io_res_addr)
                  << std::endl;
      }
      if (!dut.io_res_valid) {
        continue;
      }
      const std::size_t addr = dut.io_res_addr;
      require(addr < golden.beats(), "Top output addr out of range");
      copy_words(observed.data() + addr * 12, dut.io_res, 12);
      seen[addr] = true;
      if (dut.io_res_last) {
        saw_last = true;
      }
    }

    require(all_seen(seen), "missing Top output beats");
    require(saw_last, "Top never asserted io_res_last");
    for (std::size_t beat = 0; beat < golden.beats(); ++beat) {
      report_fp32_mismatch("Top", beat, observed.data() + beat * 12, golden.beat(beat), 12);
    }
    std::cout << "Top PASS beats=" << golden.beats() << std::endl;
    return 0;
  } catch (const std::exception& ex) {
    std::cerr << ex.what() << std::endl;
    return 1;
  }
}
