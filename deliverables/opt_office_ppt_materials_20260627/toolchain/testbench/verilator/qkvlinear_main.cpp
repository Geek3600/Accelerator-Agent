#include "VQKVLinear.h"
#include "VQKVLinear___024root.h"
#include "common.hpp"
#include <algorithm>
#include <cstdlib>
#include <filesystem>
#include <sstream>
#include <vector>

namespace {

int env_limit(const char* name, int default_value) {
  if (const char* value = std::getenv(name)) {
    return std::max(0, std::atoi(value));
  }
  return default_value;
}

bool is_probe_collect_addr(uint32_t addr) {
  switch (addr) {
    case 0:
    case 1:
    case 2:
    case 64:
    case 65:
    case 66:
    case 128:
    case 129:
    case 130:
    case 189:
    case 190:
    case 191:
      return true;
    default:
      return false;
  }
}

std::string format_int8_lane_list(const uint32_t* words, std::size_t lanes) {
  const auto values = unpack_int8_lanes(words, lanes);
  std::ostringstream oss;
  oss << "[";
  for (std::size_t idx = 0; idx < values.size(); ++idx) {
    if (idx != 0) {
      oss << ",";
    }
    oss << values[idx];
  }
  oss << "]";
  return oss.str();
}

std::string format_qkv_output_lanes(const uint32_t* words) {
  const auto lanes = unpack_int8_lanes(words, 6);
  std::ostringstream oss;
  oss << "q=[" << lanes[0] << "," << lanes[1] << "]"
      << " k=[" << lanes[2] << "," << lanes[3] << "]"
      << " v=[" << lanes[4] << "," << lanes[5] << "]";
  return oss.str();
}

std::string format_weight36(const uint32_t* words9) {
  const auto lanes = unpack_int8_lanes(words9, 36);
  std::ostringstream oss;
  oss << "[";
  for (std::size_t idx = 0; idx < lanes.size(); ++idx) {
    if (idx != 0) {
      oss << ",";
    }
    oss << lanes[idx];
  }
  oss << "]";
  return oss.str();
}

int find_weight_tile_index(const PackedWords& weight_init, const uint32_t* words9) {
  for (std::size_t idx = 0; idx < weight_init.beats(); ++idx) {
    const auto* beat = weight_init.beat(idx);
    bool same = true;
    for (std::size_t word = 0; word < 9; ++word) {
      if (beat[word] != words9[word]) {
        same = false;
        break;
      }
    }
    if (same) {
      return static_cast<int>(idx);
    }
  }
  return -1;
}

const uint32_t* vec_words(const VQKVLinear___024root* root, int idx) {
  (void)root;
  (void)idx;
  return nullptr;
}

std::string format_vec_samples(const VQKVLinear___024root* root) {
  static const int kProbeIdx[] = {0, 1, 2, 64, 65, 66, 128, 129, 130, 189, 190, 191};
  std::ostringstream oss;
  for (std::size_t idx = 0; idx < std::size(kProbeIdx); ++idx) {
    const int vec_idx = kProbeIdx[idx];
    const auto* words = vec_words(root, vec_idx);
    if (words == nullptr) {
      continue;
    }
    if (idx != 0) {
      oss << " ";
    }
    oss << "v" << vec_idx << "=" << hex_words(words, 3)
        << format_int8_lane_list(words, 12);
  }
  return oss.str();
}

const uint32_t* expected_vec_words(
    int idx,
    const PackedWords* q_rows,
    const PackedWords* k_rows,
    const PackedWords* v_rows) {
  if (idx < 64) {
    return (q_rows != nullptr && static_cast<std::size_t>(idx) < q_rows->beats()) ? q_rows->beat(idx) : nullptr;
  }
  if (idx < 128) {
    const int beat = idx - 64;
    return (k_rows != nullptr && static_cast<std::size_t>(beat) < k_rows->beats()) ? k_rows->beat(beat) : nullptr;
  }
  const int beat = idx - 128;
  return (v_rows != nullptr && static_cast<std::size_t>(beat) < v_rows->beats()) ? v_rows->beat(beat) : nullptr;
}

std::string format_vec_samples_compare(
    const VQKVLinear___024root* root,
    const PackedWords* q_rows,
    const PackedWords* k_rows,
    const PackedWords* v_rows) {
  static const int kProbeIdx[] = {0, 1, 2, 64, 65, 66, 128, 129, 130, 189, 190, 191};
  std::ostringstream oss;
  for (std::size_t idx = 0; idx < std::size(kProbeIdx); ++idx) {
    const int vec_idx = kProbeIdx[idx];
    const auto* obs = vec_words(root, vec_idx);
    if (obs == nullptr) {
      continue;
    }
    const auto* exp = expected_vec_words(vec_idx, q_rows, k_rows, v_rows);
    if (idx != 0) {
      oss << " ";
    }
    oss << "v" << vec_idx << "=" << hex_words(obs, 3);
    if (exp != nullptr) {
      oss << "/exp=" << hex_words(exp, 3);
    }
  }
  return oss.str();
}

}  // namespace

int main(int argc, char** argv) {
  try {
    Verilated::commandArgs(argc, argv);
    require(argc == 2, "usage: VQKVLinear <window_dir>");
    const std::filesystem::path window_dir = argv[1];
    const auto cfg = read_cfg(window_dir / "window.cfg");
    const auto data_in = read_words(window_dir / "artifacts" / "data_in.u32.bin", 3);
    const auto weight_init = read_words(window_dir / "artifacts" / "weight_init.u32.bin", 9);
    const auto bias_init = read_words(window_dir / "artifacts" / "bias_init.u32.bin", 3);
    const auto golden = read_words(window_dir / "artifacts" / "golden.u32.bin", 2);
    const auto q_rows_path = window_dir / "artifacts" / "q_output_rows.u32.bin";
    const auto k_rows_path = window_dir / "artifacts" / "k_output_rows.u32.bin";
    const auto v_rows_path = window_dir / "artifacts" / "v_output_rows.u32.bin";
    const auto v_chunk0_path = window_dir / "artifacts" / "v_chunk0.u32.bin";
    const bool has_v_chunk0 = std::filesystem::exists(v_chunk0_path);
    const bool has_q_rows = std::filesystem::exists(q_rows_path);
    const bool has_k_rows = std::filesystem::exists(k_rows_path);
    const bool has_v_rows = std::filesystem::exists(v_rows_path);
    PackedWords v_chunk0;
    PackedWords q_rows;
    PackedWords k_rows;
    PackedWords v_rows;
    if (has_v_chunk0) {
      v_chunk0 = read_words(v_chunk0_path, 3);
    }
    if (has_q_rows) {
      q_rows = read_words(q_rows_path, 3);
    }
    if (has_k_rows) {
      k_rows = read_words(k_rows_path, 3);
    }
    if (has_v_rows) {
      v_rows = read_words(v_rows_path, 3);
    }
    const bool debug = std::getenv("QKV_DEBUG") != nullptr;
    const bool debug_full = std::getenv("QKV_DEBUG_FULL") != nullptr;
    int debug_input_left = env_limit("QKV_DEBUG_INPUT_LIMIT", debug_full ? 16 : 8);
    int debug_output_left = env_limit("QKV_DEBUG_OUTPUT_LIMIT", debug_full ? 32 : 12);
    int debug_state_left = env_limit("QKV_DEBUG_STATE_LIMIT", debug_full ? 64 : 24);
    int debug_collect_left = env_limit("QKV_DEBUG_COLLECT_LIMIT", debug_full ? 128 : 40);
    int debug_su_left = env_limit("QKV_DEBUG_SU_LIMIT", debug_full ? 128 : 32);
    int debug_weight_left = env_limit("QKV_DEBUG_WEIGHT_LIMIT", debug_full ? 24 : 8);
    int debug_psum_left = env_limit("QKV_DEBUG_PSUM_LIMIT", debug_full ? 24 : 8);
    int debug_mac_left = env_limit("QKV_DEBUG_MAC_LIMIT", debug_full ? 16 : 4);
    uint8_t prev_state = 0xff;

    VQKVLinear dut;
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
    dut.io_q_out_inv_scale = cfg_u32(cfg, "q_out_inv_scale_u32");
    dut.io_k_out_inv_scale = cfg_u32(cfg, "k_out_inv_scale_u32");
    dut.io_v_out_inv_scale = cfg_u32(cfg, "v_out_inv_scale_u32");
    dut.io_q_bias_scale = cfg_u32(cfg, "q_bias_scale_u32");
    dut.io_k_bias_scale = cfg_u32(cfg, "k_bias_scale_u32");
    dut.io_v_bias_scale = cfg_u32(cfg, "v_bias_scale_u32");
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
    require(
        std::find(seen_weight.begin(), seen_weight.end(), false) == seen_weight.end(),
        "QKVLinear weight init did not cover all addresses");
    dut.io_weight_init_mode = 0;
    dut.io_layer_st = 0;
    zero_words(dut.io_weight_init_data, 9);
    tick(dut);

    reset_dut(dut);
    dut.io_layer_st = 0;
    dut.io_weight_init_mode = 0;
    dut.io_bias_init_valid = 0;
    dut.io_cfg_prefill = 1;
    dut.io_cfg_seqlen = cfg_int(cfg, "cfg_seqlen");
    dut.io_cfg_valid = 0;
    dut.io_data_out_ready = 0;
    dut.io_q_out_inv_scale = cfg_u32(cfg, "q_out_inv_scale_u32");
    dut.io_k_out_inv_scale = cfg_u32(cfg, "k_out_inv_scale_u32");
    dut.io_v_out_inv_scale = cfg_u32(cfg, "v_out_inv_scale_u32");
    dut.io_q_bias_scale = cfg_u32(cfg, "q_bias_scale_u32");
    dut.io_k_bias_scale = cfg_u32(cfg, "k_bias_scale_u32");
    dut.io_v_bias_scale = cfg_u32(cfg, "v_bias_scale_u32");
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

    dut.io_layer_st = 1;
    tick(dut);
    dut.io_layer_st = 0;
    for (int cycle = 0; cycle < 28; ++cycle) {
      tick(dut);
    }

    dut.io_cfg_prefill = 1;
    dut.io_cfg_seqlen = cfg_int(cfg, "cfg_seqlen");
    dut.io_q_out_inv_scale = cfg_u32(cfg, "q_out_inv_scale_u32");
    dut.io_k_out_inv_scale = cfg_u32(cfg, "k_out_inv_scale_u32");
    dut.io_v_out_inv_scale = cfg_u32(cfg, "v_out_inv_scale_u32");
    dut.io_q_bias_scale = cfg_u32(cfg, "q_bias_scale_u32");
    dut.io_k_bias_scale = cfg_u32(cfg, "k_bias_scale_u32");
    dut.io_v_bias_scale = cfg_u32(cfg, "v_bias_scale_u32");
    dut.io_cfg_valid = 1;
    dut.io_data_out_ready = 1;
    tick(dut);
    dut.io_cfg_valid = 0;

    const std::size_t token_count = static_cast<std::size_t>(cfg_int(cfg, "token_count"));
    const std::size_t beats_per_token = 32;
    const std::size_t beats_per_head = token_count * beats_per_token;
    std::size_t seen_beats = 0;
    bool saw_st = false;
    int last_count = 0;
    bool reported_tolerated_exact = false;
    bool reported_qkv_internal[3] = {false, false, false};

    for (int cycle = 0; cycle < 200000 && seen_beats < golden.beats(); ++cycle) {
      tick(dut);
      if (debug && debug_state_left > 0 &&
          static_cast<uint8_t>(dut.rootp->QKVLinear__DOT__state) != prev_state) {
        std::cerr << "QKV state cycle=" << cycle
                  << " prev=" << static_cast<int>(prev_state)
                  << " now=" << static_cast<int>(dut.rootp->QKVLinear__DOT__state)
                  << " head=" << static_cast<int>(dut.rootp->QKVLinear__DOT__headCntReg)
                  << " outCnt=" << static_cast<int>(dut.rootp->QKVLinear__DOT__outputCntReg)
                  << " batch=" << static_cast<int>(dut.rootp->QKVLinear__DOT__batchCntReg)
                  << " prefill=" << static_cast<int>(dut.rootp->QKVLinear__DOT__prefillCntReg)
                  << " allDone=" << static_cast<int>(dut.rootp->QKVLinear__DOT__all_output_done)
                  << " tokenLast=" << static_cast<int>(dut.rootp->QKVLinear__DOT__token_last)
                  << " collectW=" << static_cast<int>(dut.rootp->QKVLinear__DOT__collectWriteEnableReg)
                  << " collectTok=" << static_cast<int>(dut.rootp->QKVLinear__DOT__collectTokenReg)
                  << " collectVec=" << static_cast<int>(dut.rootp->QKVLinear__DOT__collectVecReg)
                  << " collectData=" << hex_words(dut.rootp->QKVLinear__DOT__collectDataReg, 3)
                  << " lanes=" << format_int8_lane_list(dut.rootp->QKVLinear__DOT__collectDataReg, 12)
                  << " samples={" << format_vec_samples_compare(
                         dut.rootp,
                         has_q_rows ? &q_rows : nullptr,
                         has_k_rows ? &k_rows : nullptr,
                         has_v_rows ? &v_rows : nullptr) << "}"
                  << std::endl;
        prev_state = dut.rootp->QKVLinear__DOT__state;
        --debug_state_left;
      }
      if (debug && dut.rootp->QKVLinear__DOT__su_inst__DOT__io_data_out_valid_REG) {
        const uint32_t addr = dut.rootp->QKVLinear__DOT__su_inst__DOT__io_data_out_addr_REG;
        const bool su_last = ((addr % 192U) == 191U);
        int probe_idx = -1;
        if (addr == 0) {
          probe_idx = 0;
        } else if (addr == 64) {
          probe_idx = 1;
        } else if (addr == 128) {
          probe_idx = 2;
        }
        if (probe_idx >= 0 && !reported_qkv_internal[probe_idx]) {
          const auto* raw_words = &dut.rootp->QKVLinear__DOT__su_inst__DOT__io_data_out_REG[0];
          const auto* scaled_words = &dut.rootp->QKVLinear__DOT___epilogue_inst_io_out[0];
          const uint32_t* w0_words = &dut.rootp->QKVLinear__DOT__cu_inst__DOT__w0_0[0];
          const uint32_t* w1_words = &dut.rootp->QKVLinear__DOT__cu_inst__DOT__w1_0[0];
          const uint32_t* bias_words = nullptr;
          switch (addr) {
            case 0:
              bias_words = &dut.rootp->QKVLinear__DOT__bias_mem_0[0];
              break;
            case 64:
              bias_words = &dut.rootp->QKVLinear__DOT__bias_mem_64[0];
              break;
            case 128:
              bias_words = &dut.rootp->QKVLinear__DOT__bias_mem_128[0];
              break;
            default:
              break;
          }
          std::cerr << "QKV internal addr=" << addr
                    << " raw=" << hex_words(raw_words, 12)
                    << " scaled=" << hex_words(scaled_words, 12)
                    << " lw_sel=" << static_cast<int>(dut.rootp->QKVLinear__DOT__lw_inst__DOT__io_data_out_sel_REG)
                    << " w0_idx=" << find_weight_tile_index(weight_init, w0_words)
                    << " w1_idx=" << find_weight_tile_index(weight_init, w1_words);
          if (bias_words != nullptr) {
            std::cerr << " bias=" << hex_words(bias_words, 3);
          }
          std::cerr << std::endl;
          reported_qkv_internal[probe_idx] = true;
        }
        if (debug_su_left > 0 &&
            (debug_full || is_probe_collect_addr(addr) || su_last)) {
          std::cerr << "QKV su cycle=" << cycle
                    << " state=" << static_cast<int>(dut.rootp->QKVLinear__DOT__state)
                    << " addr=" << addr
                    << " last=" << static_cast<int>(su_last)
                    << " collectFire=" << static_cast<int>(dut.rootp->QKVLinear__DOT__collect_fire)
                    << " collectW=" << static_cast<int>(dut.rootp->QKVLinear__DOT__collectWriteEnableReg)
                    << " collectTok=" << static_cast<int>(dut.rootp->QKVLinear__DOT__collectTokenReg)
                    << " collectVec=" << static_cast<int>(dut.rootp->QKVLinear__DOT__collectVecReg)
                    << " raw=" << hex_words(&dut.rootp->QKVLinear__DOT__su_inst__DOT__io_data_out_REG[0], 12)
                    << " scaled=" << hex_words(&dut.rootp->QKVLinear__DOT___epilogue_inst_io_out[0], 12)
                    << " collectData=" << hex_words(dut.rootp->QKVLinear__DOT__collectDataReg, 3)
                    << " lanes=" << format_int8_lane_list(dut.rootp->QKVLinear__DOT__collectDataReg, 12)
                    << std::endl;
          --debug_su_left;
        }
      }
      if (debug && debug_collect_left > 0 &&
          (dut.rootp->QKVLinear__DOT__collectWriteEnableReg ||
           (dut.rootp->QKVLinear__DOT__state == 2 && dut.rootp->QKVLinear__DOT__outputCntReg == 0))) {
        std::cerr << "QKV collect cycle=" << cycle
                  << " state=" << static_cast<int>(dut.rootp->QKVLinear__DOT__state)
                  << " head=" << static_cast<int>(dut.rootp->QKVLinear__DOT__headCntReg)
                  << " outCnt=" << static_cast<int>(dut.rootp->QKVLinear__DOT__outputCntReg)
                  << " collectW=" << static_cast<int>(dut.rootp->QKVLinear__DOT__collectWriteEnableReg)
                  << " collectTok=" << static_cast<int>(dut.rootp->QKVLinear__DOT__collectTokenReg)
                  << " collectVec=" << static_cast<int>(dut.rootp->QKVLinear__DOT__collectVecReg)
                  << " collectData=" << hex_words(dut.rootp->QKVLinear__DOT__collectDataReg, 3)
                  << " lanes=" << format_int8_lane_list(dut.rootp->QKVLinear__DOT__collectDataReg, 12)
                  << " samples={" << format_vec_samples_compare(
                         dut.rootp,
                         has_q_rows ? &q_rows : nullptr,
                         has_k_rows ? &k_rows : nullptr,
                         has_v_rows ? &v_rows : nullptr) << "}"
                  << std::endl;
        --debug_collect_left;
      }
      if (debug && debug_weight_left > 0 &&
          (dut.rootp->QKVLinear__DOT__lw_inst__DOT__io_data_out_valid_REG ||
           dut.rootp->QKVLinear__DOT__cu_inst__DOT__io_data_out_valid_REG)) {
        const uint32_t tile_idx =
            static_cast<uint32_t>(dut.rootp->QKVLinear__DOT__su_inst__DOT__io_data_out_addr_REG) / 64U;
        const uint32_t exp_idx0 = std::min<uint32_t>(tile_idx, static_cast<uint32_t>(weight_init.beats() - 1));
        const uint32_t exp_idx1 = std::min<uint32_t>(tile_idx + 1U, static_cast<uint32_t>(weight_init.beats() - 1));
        std::cerr << "QKV weight cycle=" << cycle
                  << " lw_v=" << static_cast<int>(dut.rootp->QKVLinear__DOT__lw_inst__DOT__io_data_out_valid_REG)
                  << " lw_sel=" << static_cast<int>(dut.rootp->QKVLinear__DOT__lw_inst__DOT__io_data_out_sel_REG)
                  << " state=" << static_cast<int>(dut.rootp->QKVLinear__DOT__state)
                  << " q_block=" << static_cast<int>(dut.rootp->QKVLinear__DOT__cu_inst__DOT__blockCntReg)
                  << " w0_0=" << hex_words(dut.rootp->QKVLinear__DOT__cu_inst__DOT__w0_0, 9)
                  << format_weight36(dut.rootp->QKVLinear__DOT__cu_inst__DOT__w0_0)
                  << " w1_0=" << hex_words(dut.rootp->QKVLinear__DOT__cu_inst__DOT__w1_0, 9)
                  << format_weight36(dut.rootp->QKVLinear__DOT__cu_inst__DOT__w1_0)
                  << " expTile" << exp_idx0 << "=" << hex_words(weight_init.beat(exp_idx0), 9)
                  << format_weight36(weight_init.beat(exp_idx0))
                  << " expTile" << exp_idx1 << "=" << hex_words(weight_init.beat(exp_idx1), 9)
                  << format_weight36(weight_init.beat(exp_idx1))
                  << std::endl;
        --debug_weight_left;
      }
      if (debug && debug_psum_left > 0 &&
          static_cast<int>(dut.rootp->QKVLinear__DOT__cu_inst__DOT__blockCntReg) < 4 &&
          (dut.rootp->QKVLinear__DOT__cu_inst__DOT__psums0_0_0 != 0 ||
           dut.rootp->QKVLinear__DOT__cu_inst__DOT__psums0_0_1 != 0 ||
           dut.rootp->QKVLinear__DOT__cu_inst__DOT__psums0_0_2 != 0)) {
        std::cerr << "QKV psum cycle=" << cycle
                  << " q_block=" << static_cast<int>(dut.rootp->QKVLinear__DOT__cu_inst__DOT__blockCntReg)
                  << " psum_sel=" << static_cast<int>(dut.rootp->QKVLinear__DOT__cu_inst__DOT__psumSelReg)
                  << " out_bank=" << static_cast<int>(dut.rootp->QKVLinear__DOT__cu_inst__DOT__out_bank_sel)
                  << " psum0=["
                  << static_cast<int32_t>(dut.rootp->QKVLinear__DOT__cu_inst__DOT__psums0_0_0) << ","
                  << static_cast<int32_t>(dut.rootp->QKVLinear__DOT__cu_inst__DOT__psums0_0_1) << ","
                  << static_cast<int32_t>(dut.rootp->QKVLinear__DOT__cu_inst__DOT__psums0_0_2) << ","
                  << static_cast<int32_t>(dut.rootp->QKVLinear__DOT__cu_inst__DOT__psums0_0_3) << ","
                  << static_cast<int32_t>(dut.rootp->QKVLinear__DOT__cu_inst__DOT__psums0_0_4) << ","
                  << static_cast<int32_t>(dut.rootp->QKVLinear__DOT__cu_inst__DOT__psums0_0_5) << ","
                  << static_cast<int32_t>(dut.rootp->QKVLinear__DOT__cu_inst__DOT__psums0_0_6) << ","
                  << static_cast<int32_t>(dut.rootp->QKVLinear__DOT__cu_inst__DOT__psums0_0_7) << ","
                  << static_cast<int32_t>(dut.rootp->QKVLinear__DOT__cu_inst__DOT__psums0_0_8) << ","
                  << static_cast<int32_t>(dut.rootp->QKVLinear__DOT__cu_inst__DOT__psums0_0_9) << ","
                  << static_cast<int32_t>(dut.rootp->QKVLinear__DOT__cu_inst__DOT__psums0_0_10) << ","
                  << static_cast<int32_t>(dut.rootp->QKVLinear__DOT__cu_inst__DOT__psums0_0_11) << "]"
                  << " psum1=["
                  << static_cast<int32_t>(dut.rootp->QKVLinear__DOT__cu_inst__DOT__psums1_0_0) << ","
                  << static_cast<int32_t>(dut.rootp->QKVLinear__DOT__cu_inst__DOT__psums1_0_1) << ","
                  << static_cast<int32_t>(dut.rootp->QKVLinear__DOT__cu_inst__DOT__psums1_0_2) << ","
                  << static_cast<int32_t>(dut.rootp->QKVLinear__DOT__cu_inst__DOT__psums1_0_3) << ","
                  << static_cast<int32_t>(dut.rootp->QKVLinear__DOT__cu_inst__DOT__psums1_0_4) << ","
                  << static_cast<int32_t>(dut.rootp->QKVLinear__DOT__cu_inst__DOT__psums1_0_5) << ","
                  << static_cast<int32_t>(dut.rootp->QKVLinear__DOT__cu_inst__DOT__psums1_0_6) << ","
                  << static_cast<int32_t>(dut.rootp->QKVLinear__DOT__cu_inst__DOT__psums1_0_7) << ","
                  << static_cast<int32_t>(dut.rootp->QKVLinear__DOT__cu_inst__DOT__psums1_0_8) << ","
                  << static_cast<int32_t>(dut.rootp->QKVLinear__DOT__cu_inst__DOT__psums1_0_9) << ","
                  << static_cast<int32_t>(dut.rootp->QKVLinear__DOT__cu_inst__DOT__psums1_0_10) << ","
                  << static_cast<int32_t>(dut.rootp->QKVLinear__DOT__cu_inst__DOT__psums1_0_11) << "]"
                  << std::endl;
        --debug_psum_left;
      }
      (void)has_v_chunk0;
      (void)v_chunk0;
      if (debug && debug_input_left > 0 && dut.rootp->QKVLinear__DOT__lu_inst__DOT__io_data_out_valid_REG) {
        const auto* pipe_words =
            &dut.rootp->QKVLinear__DOT__cu_inst__DOT__indata_pipreg__DOT__pipData_2_REG[0];
        std::cerr << "QKV input sample=" << (8 - debug_input_left)
                  << " lu_block=" << static_cast<int>(dut.rootp->QKVLinear__DOT__lu_inst__DOT__block_cnt_r)
                  << " lu_addr=" << dut.io_data_addr
                  << " pipe2=" << hex_words(pipe_words, 3)
                  << " cu_block=" << static_cast<int>(dut.rootp->QKVLinear__DOT__cu_inst__DOT__blockCntReg)
                  << std::endl;
        --debug_input_left;
      }
      if (!dut.io_data_out_valid) {
        continue;
      }
      require(seen_beats < golden.beats(), "QKVLinear produced too many output beats");
      uint32_t observed_words[2] = {
          static_cast<uint32_t>(dut.io_data_out & 0xffffffffULL),
          static_cast<uint32_t>((dut.io_data_out >> 32) & 0xffffULL),
      };
      if (debug && debug_output_left > 0) {
        std::cerr << "QKV output beat=" << seen_beats
                  << " out=" << hex_words(observed_words, 2)
                  << " golden=" << hex_words(golden.beat(seen_beats), 2)
                  << " outLanes=" << format_qkv_output_lanes(observed_words)
                  << " goldLanes=" << format_qkv_output_lanes(golden.beat(seen_beats))
                  << " state=" << static_cast<int>(dut.rootp->QKVLinear__DOT__state)
                  << " head_cnt=" << static_cast<int>(dut.rootp->QKVLinear__DOT__headCntReg)
                  << " output_cnt=" << static_cast<int>(dut.rootp->QKVLinear__DOT__outputCntReg)
                  << " collectW=" << static_cast<int>(dut.rootp->QKVLinear__DOT__collectWriteEnableReg)
                  << " collectTok=" << static_cast<int>(dut.rootp->QKVLinear__DOT__collectTokenReg)
                  << " collectVec=" << static_cast<int>(dut.rootp->QKVLinear__DOT__collectVecReg)
                  << " qExp0="
                  << (has_q_rows ? hex_words(q_rows.beat(0), 3) + format_int8_lane_list(q_rows.beat(0), 12) : "n/a")
                  << " kExp0="
                  << (has_k_rows ? hex_words(k_rows.beat(0), 3) + format_int8_lane_list(k_rows.beat(0), 12) : "n/a")
                  << " vExp0="
                  << (has_v_rows ? hex_words(v_rows.beat(0), 3) + format_int8_lane_list(v_rows.beat(0), 12) : "n/a")
                  << " samples={" << format_vec_samples_compare(
                         dut.rootp,
                         has_q_rows ? &q_rows : nullptr,
                         has_k_rows ? &k_rows : nullptr,
                         has_v_rows ? &v_rows : nullptr) << "}"
                  << std::endl;
        --debug_output_left;
      }
      report_int8_mismatch("QKVLinear", seen_beats, observed_words, golden.beat(seen_beats), 2, 6);
      if (debug && !reported_tolerated_exact) {
        const auto obs = unpack_int8_lanes(observed_words, 6);
        const auto exp = unpack_int8_lanes(golden.beat(seen_beats), 6);
        for (std::size_t lane = 0; lane < 6; ++lane) {
          if (obs[lane] != exp[lane]) {
            std::cerr << "QKVLinear tolerated diff"
                      << " beat=" << seen_beats
                      << " lane=" << lane
                      << " observed=" << obs[lane]
                      << " expected=" << exp[lane]
                      << std::endl;
            reported_tolerated_exact = true;
            break;
          }
        }
      }

      const std::size_t beat_in_head = seen_beats % beats_per_head;
      const std::size_t expected_addr = beat_in_head;
      require(
          dut.io_data_out_addr == expected_addr,
          "QKVLinear output addr mismatch at sequence beat=" + std::to_string(seen_beats));

      const bool expected_last = (beat_in_head + 1 == beats_per_head);
      require(
          static_cast<bool>(dut.io_data_out_last) == expected_last,
          "QKVLinear output last mismatch at sequence beat=" + std::to_string(seen_beats));

      const bool expected_st = (beat_in_head == 0);
      require(
          static_cast<bool>(dut.io_data_out_st) == expected_st,
          "QKVLinear output st mismatch at sequence beat=" + std::to_string(seen_beats));

      saw_st = saw_st || dut.io_data_out_st;
      last_count += dut.io_data_out_last ? 1 : 0;
      ++seen_beats;
    }

    require(
        seen_beats == golden.beats(),
        "missing QKVLinear output beats observed=" + std::to_string(seen_beats) +
            " expected=" + std::to_string(golden.beats()));
    require(saw_st, "QKVLinear never asserted io_data_out_st");
    require(last_count == 12, "QKVLinear unexpected io_data_out_last count");
    std::cout << "QKVLinear PASS beats=" << seen_beats << std::endl;
    return 0;
  } catch (const std::exception& ex) {
    std::cerr << ex.what() << std::endl;
    return 1;
  }
}
