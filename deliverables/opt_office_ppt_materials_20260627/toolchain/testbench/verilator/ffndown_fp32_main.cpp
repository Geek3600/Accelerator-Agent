#include "VFFNDownFP32.h"
#include "VFFNDownFP32___024root.h"
#include "common.hpp"
#include <array>
#include <cstdlib>
#include <deque>
#include <filesystem>
#include <sstream>
#include <string>
#include <vector>

namespace {

using Mem72 = VlUnpacked<VlWide<3>, 4096>;

std::array<const Mem72*, 68> weight_mem_views(const VFFNDownFP32& dut) {
  const auto* root = dut.rootp;
  return {
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_0_0_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_0_1_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_0_2_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_0_3_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_1_0_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_1_1_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_1_2_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_1_3_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_2_0_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_2_1_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_2_2_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_2_3_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_3_0_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_3_1_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_3_2_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_3_3_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_4_0_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_4_1_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_4_2_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_4_3_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_5_0_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_5_1_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_5_2_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_5_3_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_6_0_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_6_1_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_6_2_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_6_3_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_7_0_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_7_1_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_7_2_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_7_3_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_8_0_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_8_1_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_8_2_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_8_3_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_9_0_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_9_1_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_9_2_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_9_3_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_10_0_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_10_1_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_10_2_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_10_3_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_11_0_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_11_1_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_11_2_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_11_3_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_12_0_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_12_1_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_12_2_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_12_3_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_13_0_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_13_1_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_13_2_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_13_3_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_14_0_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_14_1_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_14_2_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_14_3_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_15_0_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_15_1_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_15_2_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_15_3_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_16_0_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_16_1_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_16_2_ext__DOT__Memory,
      &root->FFNDownFP32__DOT__lw_inst__DOT__weight_mem__DOT__weight_banks_16_3_ext__DOT__Memory,
  };
}

std::array<uint32_t, 3> expected_slice_words(const uint32_t* beat, std::size_t slice_idx) {
  std::array<uint8_t, 36> bytes{};
  for (std::size_t word_idx = 0; word_idx < 9; ++word_idx) {
    const uint32_t word = beat[word_idx];
    bytes[word_idx * 4 + 0] = static_cast<uint8_t>(word & 0xffU);
    bytes[word_idx * 4 + 1] = static_cast<uint8_t>((word >> 8) & 0xffU);
    bytes[word_idx * 4 + 2] = static_cast<uint8_t>((word >> 16) & 0xffU);
    bytes[word_idx * 4 + 3] = static_cast<uint8_t>((word >> 24) & 0xffU);
  }

  const std::size_t byte_base = slice_idx * 9;
  return {
      static_cast<uint32_t>(bytes[byte_base + 0]) |
          (static_cast<uint32_t>(bytes[byte_base + 1]) << 8) |
          (static_cast<uint32_t>(bytes[byte_base + 2]) << 16) |
          (static_cast<uint32_t>(bytes[byte_base + 3]) << 24),
      static_cast<uint32_t>(bytes[byte_base + 4]) |
          (static_cast<uint32_t>(bytes[byte_base + 5]) << 8) |
          (static_cast<uint32_t>(bytes[byte_base + 6]) << 16) |
          (static_cast<uint32_t>(bytes[byte_base + 7]) << 24),
      static_cast<uint32_t>(bytes[byte_base + 8]),
  };
}

std::array<uint32_t, 3> observed_slice_words(const VlWide<3>& slice_word) {
  return {slice_word[0], slice_word[1], slice_word[2] & 0xffU};
}

void probe_weight_memory(const VFFNDownFP32& dut, const PackedWords& weight_init) {
  const auto memories = weight_mem_views(dut);
  for (std::size_t addr = 0; addr < weight_init.beats(); ++addr) {
    const std::size_t bank = addr >> 12;
    const std::size_t bank_addr = addr & 0xfffU;
    for (std::size_t slice = 0; slice < 4; ++slice) {
      const auto expected = expected_slice_words(weight_init.beat(addr), slice);
      const auto observed = observed_slice_words((*(memories[bank * 4 + slice]))[bank_addr]);
      if (observed != expected) {
        std::ostringstream oss;
        oss << "FFNDownFP32 weight memory mismatch"
            << " addr=" << addr
            << " bank=" << bank
            << " bank_addr=" << bank_addr
            << " slice=" << slice
            << " observed=0x" << std::hex << observed[2] << "_" << observed[1] << "_" << observed[0]
            << " expected=0x" << expected[2] << "_" << expected[1] << "_" << expected[0];
        throw std::runtime_error(oss.str());
      }
    }
  }
  std::cout << "FFNDownFP32 weight memory probe PASS addresses=" << weight_init.beats() << std::endl;
}

std::array<uint32_t, 9> read_wide9(const VlWide<9>& wide) {
  std::array<uint32_t, 9> out{};
  for (std::size_t idx = 0; idx < out.size(); ++idx) {
    out[idx] = wide[idx];
  }
  return out;
}

std::array<uint32_t, 3> read_wide3(const VlWide<3>& wide) {
  std::array<uint32_t, 3> out{};
  for (std::size_t idx = 0; idx < out.size(); ++idx) {
    out[idx] = wide[idx];
  }
  return out;
}

std::array<uint32_t, 12> read_wide12(const VlWide<12>& wide) {
  std::array<uint32_t, 12> out{};
  for (std::size_t idx = 0; idx < out.size(); ++idx) {
    out[idx] = wide[idx];
  }
  return out;
}

int decode_i8_lane(const uint32_t* words, int lane) {
  const uint32_t word = words[lane / 4];
  const uint32_t byte = (word >> (8 * (lane % 4))) & 0xffU;
  return static_cast<int>(static_cast<int8_t>(byte));
}

std::string i8_prefix(const uint32_t* words, std::size_t lanes) {
  std::ostringstream oss;
  for (std::size_t i = 0; i < lanes; ++i) {
    if (i) {
      oss << ",";
    }
    oss << decode_i8_lane(words, static_cast<int>(i));
  }
  return oss.str();
}

template <std::size_t N>
std::array<uint32_t, N> read_wide(const VlWide<N>& wide) {
  std::array<uint32_t, N> out{};
  for (std::size_t idx = 0; idx < out.size(); ++idx) {
    out[idx] = wide[idx];
  }
  return out;
}

template <typename Dut>
void write_bias_and_data_then_preload(
    Dut& dut,
    const std::filesystem::path& window_dir,
    const std::unordered_map<std::string, std::string>& cfg,
    const PackedWords& data_in) {
  const auto bias_init = read_words(window_dir / "artifacts" / "bias_init.u32.bin", 12);
  const bool early_start = std::getenv("FFNDOWN_EARLY_START") != nullptr;
  const bool top_style_start = std::getenv("FFNDOWN_TOP_STYLE_START") != nullptr;
  const bool keep_ready_during_input = std::getenv("FFNDOWN_KEEP_READY_DURING_INPUT") != nullptr;
  int idle_before_input = 0;
  if (const char* env = std::getenv("FFNDOWN_IDLE_BEFORE_INPUT")) {
    idle_before_input = std::max(0, std::atoi(env));
  } else if (top_style_start) {
    idle_before_input = 64;
  }

  for (std::size_t beat = 0; beat < bias_init.beats(); ++beat) {
    copy_words(dut.io_bias_init_data, bias_init.beat(beat), 12);
    dut.io_bias_init_valid = 1;
    tick(dut);
  }
  dut.io_bias_init_valid = 0;
  zero_words(dut.io_bias_init_data, 12);

  if (top_style_start) {
    dut.io_cfg_valid = 1;
    tick(dut);
    dut.io_cfg_valid = 0;
    dut.io_layer_st = 1;
    tick(dut);
    dut.io_layer_st = 0;
    for (int cycle = 0; cycle < idle_before_input; ++cycle) {
      tick(dut);
    }
  } else if (early_start) {
    dut.io_layer_st = 1;
    tick(dut);
    dut.io_layer_st = 0;
    for (int cycle = 0; cycle < idle_before_input; ++cycle) {
      tick(dut);
    }
  }

  dut.io_data_out_ready = keep_ready_during_input ? 1 : 0;
  for (std::size_t beat = 0; beat < data_in.beats(); ++beat) {
    while (!dut.io_data_ready) {
      tick(dut);
    }
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

  if (!early_start && !top_style_start) {
    dut.io_layer_st = 1;
    tick(dut);
    dut.io_layer_st = 0;
  }

  if (top_style_start) {
    dut.io_data_out_ready = 1;
  }

  for (int cycle = 0; cycle < 24; ++cycle) {
    tick(dut);
  }

  if (!top_style_start) {
    dut.io_cfg_prefill = 1;
    dut.io_cfg_seqlen = cfg_int(cfg, "cfg_seqlen");
    dut.io_out_scale = cfg_u32(cfg, "out_scale_u32");
    dut.io_cfg_valid = 1;
    dut.io_data_out_ready = 1;
    tick(dut);
    dut.io_cfg_valid = 0;
  }
}

std::size_t find_exact_beat(const PackedWords& weight_init, const std::array<uint32_t, 9>& observed) {
  for (std::size_t beat = 0; beat < weight_init.beats(); ++beat) {
    bool match = true;
    for (std::size_t word = 0; word < observed.size(); ++word) {
      if (weight_init.beat(beat)[word] != observed[word]) {
        match = false;
        break;
      }
    }
    if (match) {
      return beat;
    }
  }
  return static_cast<std::size_t>(-1);
}

std::size_t find_exact_beat_words9(const PackedWords& weight_init, const VlWide<9>& observed_wide) {
  return find_exact_beat(weight_init, read_wide<9>(observed_wide));
}

std::size_t find_exact_beat_words3(const PackedWords& packed, const VlWide<3>& observed_wide) {
  const auto observed = read_wide<3>(observed_wide);
  for (std::size_t beat = 0; beat < packed.beats(); ++beat) {
    bool match = true;
    for (std::size_t word = 0; word < observed.size(); ++word) {
      if (packed.beat(beat)[word] != observed[word]) {
        match = false;
        break;
      }
    }
    if (match) {
      return beat;
    }
  }
  return static_cast<std::size_t>(-1);
}

void probe_load_sequence(VFFNDownFP32& dut, const PackedWords& weight_init) {
  dut.io_layer_st = 1;
  tick(dut);
  dut.io_layer_st = 0;

  std::size_t seen = 0;
  for (int cycle = 0; cycle < 256 && seen < 24; ++cycle) {
    tick(dut);
    if (!dut.rootp->FFNDownFP32__DOT__lw_inst__DOT__io_data_out_valid_REG) {
      continue;
    }
    const auto observed = read_wide9(dut.rootp->FFNDownFP32__DOT___lw_inst_io_data_out);
    const uint32_t* expected = weight_init.beat(seen);
    const std::size_t exact_match = find_exact_beat(weight_init, observed);
    for (std::size_t word = 0; word < observed.size(); ++word) {
      if (observed[word] != expected[word]) {
        std::ostringstream oss;
        oss << "FFNDownFP32 LoadWeight sequence mismatch"
            << " beat=" << seen
            << " word=" << word
            << " addr_reg=" << dut.rootp->FFNDownFP32__DOT__lw_inst__DOT__addr_reg
            << " state=" << static_cast<int>(dut.rootp->FFNDownFP32__DOT__lw_inst__DOT__state)
            << " row_cnt=" << static_cast<int>(dut.rootp->FFNDownFP32__DOT__lw_inst__DOT__row_cnt_r)
            << " rowblock_cnt=" << static_cast<int>(dut.rootp->FFNDownFP32__DOT__lw_inst__DOT__rowblock_cnt_r)
            << " colblock_cnt=" << static_cast<int>(dut.rootp->FFNDownFP32__DOT__lw_inst__DOT__colblock_cnt_r)
            << " observed=0x" << std::hex << observed[word]
            << " expected=0x" << expected[word];
        if (exact_match != static_cast<std::size_t>(-1)) {
          oss << " exact_match_beat=" << std::dec << exact_match;
        } else {
          oss << " exact_match_beat=none";
        }
        throw std::runtime_error(oss.str());
      }
    }
    ++seen;
  }
  require(seen == 24, "FFNDownFP32 LoadWeight probe did not observe first 24 weight beats");
  std::cout << "FFNDownFP32 LoadWeight probe PASS beats=" << seen << std::endl;
}

void trace_load_sequence(VFFNDownFP32& dut, const PackedWords& weight_init, std::size_t count) {
  dut.io_layer_st = 1;
  tick(dut);
  dut.io_layer_st = 0;

  std::size_t seen = 0;
  for (int cycle = 0; cycle < 256 && seen < count; ++cycle) {
    tick(dut);
    if (!dut.rootp->FFNDownFP32__DOT__lw_inst__DOT__io_data_out_valid_REG) {
      continue;
    }
    const auto observed = read_wide9(dut.rootp->FFNDownFP32__DOT___lw_inst_io_data_out);
    const std::size_t exact_match = find_exact_beat(weight_init, observed);
    std::cout << "FFNDownFP32 LoadWeight trace"
              << " sample=" << seen
              << " addr_reg=" << dut.rootp->FFNDownFP32__DOT__lw_inst__DOT__addr_reg
              << " state=" << static_cast<int>(dut.rootp->FFNDownFP32__DOT__lw_inst__DOT__state)
              << " row_cnt=" << static_cast<int>(dut.rootp->FFNDownFP32__DOT__lw_inst__DOT__row_cnt_r)
              << " rowblock_cnt=" << static_cast<int>(dut.rootp->FFNDownFP32__DOT__lw_inst__DOT__rowblock_cnt_r)
              << " colblock_cnt=" << static_cast<int>(dut.rootp->FFNDownFP32__DOT__lw_inst__DOT__colblock_cnt_r)
              << " exact_match_beat=";
    if (exact_match == static_cast<std::size_t>(-1)) {
      std::cout << "none";
    } else {
      std::cout << exact_match;
    }
    std::cout << " word0=0x" << std::hex << observed[0] << std::dec << std::endl;
    ++seen;
  }
  require(seen == count, "FFNDownFP32 LoadWeight trace did not observe enough valid beats");
}

void probe_prebias(const std::filesystem::path& window_dir, VFFNDownFP32& dut, const PackedWords& data_in) {
  const auto bias_init = read_words(window_dir / "artifacts" / "bias_init.u32.bin", 12);
  const auto cfg = read_cfg(window_dir / "window.cfg");
  write_bias_and_data_then_preload(dut, window_dir, cfg, data_in);

  for (int cycle = 0; cycle < 200000; ++cycle) {
    tick(dut);
    if (!dut.io_data_out_valid) {
      continue;
    }
    const auto su = read_wide12(dut.rootp->FFNDownFP32__DOT__su_inst__DOT__io_data_out_REG);
    const auto top = read_wide12(dut.io_data_out);
    std::ostringstream oss;
    oss << "FFNDownFP32 prebias probe"
        << " out_addr=" << dut.io_data_out_addr
        << " su_addr=" << dut.rootp->FFNDownFP32__DOT__su_inst__DOT__io_data_out_addr_REG
        << " su_lane0=0x" << std::hex << su[0]
        << " bias_lane0=0x" << bias_init.beat(dut.io_data_out_addr)[0]
        << " top_lane0=0x" << top[0];
    throw std::runtime_error(oss.str());
  }
  throw std::runtime_error("FFNDownFP32 prebias probe did not observe any output beat");
}

void probe_cu_state(const std::filesystem::path& window_dir, VFFNDownFP32& dut, const PackedWords& data_in) {
  const auto cfg = read_cfg(window_dir / "window.cfg");
  write_bias_and_data_then_preload(dut, window_dir, cfg, data_in);

  for (int cycle = 0; cycle < 200000; ++cycle) {
    tick(dut);
    if (!dut.io_data_out_valid) {
      continue;
    }
    const auto su = read_wide12(dut.rootp->FFNDownFP32__DOT__su_inst__DOT__io_data_out_REG);
    const auto to_fp = read_wide12(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT____Vcellinp__toFp__io_in);
    const auto indata = read_wide3(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__indata_pipreg__DOT__pipData_2_REG);
    const auto in_lanes = unpack_int8_lanes(indata.data(), 12);
    std::ostringstream oss;
    oss << "FFNDownFP32 cu probe"
        << " out_addr=" << dut.io_data_out_addr
        << " su_lane0=0x" << std::hex << su[0]
        << " toFp_lane0=0x" << to_fp[0]
        << " psums0_0_0=0x" << dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums0_0_0
        << " psums1_0_0=0x" << dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums1_0_0
        << " out_bank_sel=" << static_cast<int>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__out_bank_sel)
        << " w_r_sel=" << static_cast<int>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__weight_r_sel)
        << " w_w_sel=" << static_cast<int>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__weight_w_sel)
        << " batch_cnt=" << std::dec << static_cast<int>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__batchsize_cnt_r)
        << " block_cnt=" << static_cast<int>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__block_cnt_r)
        << " res_batch_cnt=" << static_cast<int>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__res_batchsize_cnt_r)
        << " res_vec_cnt=" << static_cast<int>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__res_vector_cnt_r)
        << " actual_batchsize=" << static_cast<int>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__actual_batchsize)
        << " in_lane0=" << in_lanes[0]
        << " in_lane11=" << in_lanes[11]
        << " mul00_w=0x" << static_cast<int>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT____Vcellinp__mul_list_0_0__io_in1)
        << " mul110_w=0x" << static_cast<int>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT____Vcellinp__mul_list_11_0__io_in1)
        << " mul00_out=0x" << dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__mul_list_0_0__DOT__io_out_REG
        << " mul110_out=0x" << dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__mul_list_11_0__DOT__io_out_REG
        << " psums0_0_1=0x" << dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums0_0_1
        << " psums0_0_2=0x" << dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums0_0_2
        << " psums0_0_3=0x" << dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums0_0_3
        << " psums0_0_11=0x" << dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums0_0_11
        << " toFp_lane1=0x" << to_fp[1]
        << " toFp_lane2=0x" << to_fp[2]
        << " toFp_lane3=0x" << to_fp[3]
        << " toFp_lane11=0x" << to_fp[11];
    throw std::runtime_error(oss.str());
  }
  throw std::runtime_error("FFNDownFP32 cu probe did not observe any output beat");
}

void probe_cu_start(const std::filesystem::path& window_dir, VFFNDownFP32& dut, const PackedWords& data_in) {
  const auto cfg = read_cfg(window_dir / "window.cfg");
  write_bias_and_data_then_preload(dut, window_dir, cfg, data_in);

  int prev_state = 0;
  for (int cycle = 0; cycle < 200000; ++cycle) {
    tick(dut);
    const int state = static_cast<int>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__state);
    if (!(prev_state == 0 && state == 1)) {
      prev_state = state;
      continue;
    }
    std::ostringstream oss;
    oss << "FFNDownFP32 cu-start probe"
        << " psum_sel=" << static_cast<int>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psum_sel_r)
        << " res_batch_cnt=" << static_cast<int>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__res_batchsize_cnt_r)
        << " res_vec_cnt=" << static_cast<int>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__res_vector_cnt_r)
        << " block_cnt=" << static_cast<int>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__block_cnt_r)
        << " psums0={"
        << std::hex
        << dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums0_0_0 << ","
        << dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums0_0_1 << ","
        << dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums0_0_2 << ","
        << dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums0_0_3 << ","
        << dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums0_0_4 << ","
        << dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums0_0_5 << ","
        << dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums0_0_6 << ","
        << dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums0_0_7 << ","
        << dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums0_0_8 << ","
        << dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums0_0_9 << ","
        << dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums0_0_10 << ","
        << dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums0_0_11 << "}"
        << " psums1={"
        << dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums1_0_0 << ","
        << dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums1_0_1 << ","
        << dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums1_0_2 << ","
        << dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums1_0_3 << ","
        << dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums1_0_4 << ","
        << dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums1_0_5 << ","
        << dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums1_0_6 << ","
        << dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums1_0_7 << ","
        << dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums1_0_8 << ","
        << dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums1_0_9 << ","
        << dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums1_0_10 << ","
        << dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums1_0_11 << "}";
    throw std::runtime_error(oss.str());
  }
  throw std::runtime_error("FFNDownFP32 cu-start probe did not observe idle->buzy transition");
}

void probe_tiles(VFFNDownFP32& dut, const PackedWords& weight_init) {
  dut.io_layer_st = 1;
  tick(dut);
  dut.io_layer_st = 0;

  for (int cycle = 0; cycle < 64; ++cycle) {
    tick(dut);
  }

  std::ostringstream oss;
  oss << "FFNDownFP32 tile probe";
  oss << " w0={"
      << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_0_r) << ","
      << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_1_r) << ","
      << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_2_r) << ","
      << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_3_r) << ","
      << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_4_r) << ","
      << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_5_r) << ","
      << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_6_r) << ","
      << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_7_r) << ","
      << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_8_r) << ","
      << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_9_r) << ","
      << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_10_r) << ","
      << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_11_r) << "}";
  oss << " w1={"
      << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_0_r) << ","
      << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_1_r) << ","
      << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_2_r) << ","
      << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_3_r) << ","
      << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_4_r) << ","
      << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_5_r) << ","
      << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_6_r) << ","
      << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_7_r) << ","
      << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_8_r) << ","
      << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_9_r) << ","
      << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_10_r) << ","
      << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_11_r) << "}";
  throw std::runtime_error(oss.str());
}

void probe_data_trace(const std::filesystem::path& window_dir, VFFNDownFP32& dut, const PackedWords& data_in) {
  const auto cfg = read_cfg(window_dir / "window.cfg");
  write_bias_and_data_then_preload(dut, window_dir, cfg, data_in);

  std::size_t seen = 0;
  for (int cycle = 0; cycle < 512 && seen < 8; ++cycle) {
    tick(dut);
    if (!dut.rootp->FFNDownFP32__DOT__lu_inst__DOT__io_data_out_valid_REG) {
      continue;
    }
    const auto match1 = find_exact_beat_words3(data_in, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__indata_pipreg__DOT__pipData_1_REG);
    const auto match2 = find_exact_beat_words3(data_in, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__indata_pipreg__DOT__pipData_2_REG);
    std::cout << "FFNDownFP32 data trace"
              << " sample=" << seen
              << " lu_addr=" << dut.rootp->FFNDownFP32__DOT___lu_inst_io_data_in_addr
              << " match_p1=";
    if (match1 == static_cast<std::size_t>(-1)) std::cout << "none"; else std::cout << match1;
    std::cout << " match_p2=";
    if (match2 == static_cast<std::size_t>(-1)) std::cout << "none"; else std::cout << match2;
    std::cout << std::endl;
    ++seen;
  }
  require(seen == 8, "FFNDownFP32 data trace did not observe 8 valid beats");
}

void probe_mul_source(const std::filesystem::path& window_dir, VFFNDownFP32& dut, const PackedWords& data_in) {
  const auto weight_init = read_words(window_dir / "artifacts" / "weight_init.u32.bin", 9);
  const auto cfg = read_cfg(window_dir / "window.cfg");
  write_bias_and_data_then_preload(dut, window_dir, cfg, data_in);

  int last_match = -2;
  int seen = 0;
  for (int cycle = 0; cycle < 200000 && seen < 12; ++cycle) {
    tick(dut);
    const auto in_match = static_cast<int>(find_exact_beat_words3(data_in, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__indata_pipreg__DOT__pipData_2_REG));
    if (in_match < 0 || in_match == last_match) {
      continue;
    }
    last_match = in_match;
    const bool sel = dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__weight_r_sel;
    const auto row0_beat = sel
        ? find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_0_r)
        : find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_0_r);
    const auto row11_beat = sel
        ? find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_11_r)
        : find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_11_r);
    const auto w0_row0 = find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_0_r);
    const auto w1_row0 = find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_0_r);
    std::cout << "FFNDownFP32 mul source"
              << " in_match=" << in_match
              << " w_r_sel=" << static_cast<int>(sel)
              << " w_w_sel=" << static_cast<int>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__weight_w_sel)
              << " row0_beat=" << row0_beat
              << " row11_beat=" << row11_beat
              << " w0_row0=" << w0_row0
              << " w1_row0=" << w1_row0
              << " weights0={"
              << static_cast<int>(static_cast<int8_t>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT____Vcellinp__mul_list_0_0__io_in1)) << ","
              << static_cast<int>(static_cast<int8_t>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT____Vcellinp__mul_list_1_0__io_in1)) << ","
              << static_cast<int>(static_cast<int8_t>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT____Vcellinp__mul_list_2_0__io_in1)) << ","
              << static_cast<int>(static_cast<int8_t>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT____Vcellinp__mul_list_3_0__io_in1)) << ","
              << static_cast<int>(static_cast<int8_t>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT____Vcellinp__mul_list_4_0__io_in1)) << ","
              << static_cast<int>(static_cast<int8_t>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT____Vcellinp__mul_list_5_0__io_in1)) << ","
              << static_cast<int>(static_cast<int8_t>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT____Vcellinp__mul_list_6_0__io_in1)) << ","
              << static_cast<int>(static_cast<int8_t>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT____Vcellinp__mul_list_7_0__io_in1)) << ","
              << static_cast<int>(static_cast<int8_t>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT____Vcellinp__mul_list_8_0__io_in1)) << ","
              << static_cast<int>(static_cast<int8_t>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT____Vcellinp__mul_list_9_0__io_in1)) << ","
              << static_cast<int>(static_cast<int8_t>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT____Vcellinp__mul_list_10_0__io_in1)) << ","
              << static_cast<int>(static_cast<int8_t>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT____Vcellinp__mul_list_11_0__io_in1)) << "}"
              << std::endl;
    if (in_match == 0) {
      std::cout << "FFNDownFP32 mul source tiles"
                << " w0={"
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_0_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_1_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_2_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_3_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_4_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_5_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_6_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_7_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_8_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_9_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_10_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_11_r) << "}"
                << " w1={"
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_0_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_1_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_2_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_3_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_4_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_5_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_6_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_7_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_8_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_9_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_10_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_11_r) << "}"
                << std::endl;
    }
    if (in_match == 2) {
      std::cout << "FFNDownFP32 mul source selected tiles"
                << " w0={"
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_0_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_1_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_2_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_3_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_4_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_5_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_6_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_7_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_8_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_9_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_10_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_11_r) << "}"
                << " w1={"
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_0_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_1_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_2_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_3_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_4_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_5_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_6_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_7_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_8_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_9_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_10_r) << ","
                << find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_11_r) << "}"
                << std::endl;
    }
    ++seen;
  }
  require(seen == 12, "FFNDownFP32 mul source did not observe 12 distinct input beats");
}

void probe_psum_trace(const std::filesystem::path& window_dir, VFFNDownFP32& dut, const PackedWords& data_in) {
  const auto weight_init = read_words(window_dir / "artifacts" / "weight_init.u32.bin", 9);
  const auto cfg = read_cfg(window_dir / "window.cfg");
  const int detail_sample = std::getenv("FFNDOWN_DETAIL_SAMPLE") ? std::atoi(std::getenv("FFNDOWN_DETAIL_SAMPLE")) : -1;
  write_bias_and_data_then_preload(dut, window_dir, cfg, data_in);

  uint32_t prev0 = dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums0_0_0;
  uint32_t prev1 = dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums0_0_1;
  uint32_t prev2 = dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums0_0_2;
  uint32_t prev3 = dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums0_0_3;
  struct SourceEvent {
    std::size_t in_match;
    bool w_r_sel;
    std::size_t row0_beat;
    std::size_t row11_beat;
    std::array<int, 12> in_lanes;
    std::array<std::array<int, 12>, 4> w_cols;
    std::array<std::array<int, 12>, 4> prod_cols;
    std::array<int, 4> sum_cols;
  };
  std::deque<SourceEvent> src_hist;
  std::size_t seen = 0;
  for (int cycle = 0; cycle < 200000 && seen < 12; ++cycle) {
    tick(dut);
    const bool cur_sel = dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__weight_r_sel;
    const auto cur_in_match = find_exact_beat_words3(data_in, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__indata_pipreg__DOT__pipData_2_REG);
    const auto cur_row0 = cur_sel
        ? find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_0_r)
        : find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_0_r);
    const auto cur_row11 = cur_sel
        ? find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_11_r)
        : find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_11_r);
    const auto& in_words = dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__indata_pipreg__DOT__pipData_2_REG;
    const auto& row0_words = cur_sel
        ? dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_0_r
        : dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_0_r;
    const auto& row1_words = cur_sel
        ? dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_1_r
        : dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_1_r;
    const auto& row2_words = cur_sel
        ? dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_2_r
        : dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_2_r;
    const auto& row3_words = cur_sel
        ? dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_3_r
        : dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_3_r;
    const auto& row4_words = cur_sel
        ? dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_4_r
        : dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_4_r;
    const auto& row5_words = cur_sel
        ? dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_5_r
        : dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_5_r;
    const auto& row6_words = cur_sel
        ? dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_6_r
        : dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_6_r;
    const auto& row7_words = cur_sel
        ? dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_7_r
        : dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_7_r;
    const auto& row8_words = cur_sel
        ? dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_8_r
        : dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_8_r;
    const auto& row9_words = cur_sel
        ? dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_9_r
        : dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_9_r;
    const auto& row10_words = cur_sel
        ? dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_10_r
        : dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_10_r;
    const auto& row11_words = cur_sel
        ? dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_11_r
        : dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_11_r;
    const uint32_t* rows[] = {
        row0_words, row1_words, row2_words, row3_words, row4_words, row5_words,
        row6_words, row7_words, row8_words, row9_words, row10_words, row11_words};
    std::array<int, 12> in_lanes{};
    std::array<std::array<int, 12>, 4> w_cols{};
    std::array<std::array<int, 12>, 4> prod_cols{};
    std::array<int, 4> sum_cols{};
    for (int row = 0; row < 12; ++row) {
      in_lanes[row] = decode_i8_lane(in_words, row);
    }
    for (int col = 0; col < 4; ++col) {
      int sum = 0;
      for (int row = 0; row < 12; ++row) {
        const int in = in_lanes[row];
        const int w = decode_i8_lane(rows[11 - row], col);
        const int prod = in * w;
        w_cols[col][row] = w;
        prod_cols[col][row] = prod;
        sum += prod;
      }
      sum_cols[col] = sum;
    }
    src_hist.push_back(SourceEvent{cur_in_match, cur_sel, cur_row0, cur_row11, in_lanes, w_cols, prod_cols, sum_cols});
    if (src_hist.size() < 6) {
      continue;
    }
    while (src_hist.size() > 6) {
      src_hist.pop_front();
    }
    uint32_t cur0 = dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums0_0_0;
    uint32_t cur1 = dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums0_0_1;
    uint32_t cur2 = dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums0_0_2;
    uint32_t cur3 = dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__psums0_0_3;
    if (cur0 == prev0 && cur1 == prev1 && cur2 == prev2 && cur3 == prev3) {
      continue;
    }
    const auto& src = src_hist.front();
    std::cout << "FFNDownFP32 psum trace"
              << " sample=" << seen
              << " block_cnt=" << static_cast<int>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__block_cnt_r)
              << " batch_cnt=" << static_cast<int>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__batchsize_cnt_r)
              << " src_w_r_sel=" << static_cast<int>(src.w_r_sel)
              << " src_in_match=";
    if (src.in_match == static_cast<std::size_t>(-1)) std::cout << "none"; else std::cout << src.in_match;
    std::cout << " src_row0_beat=";
    if (src.row0_beat == static_cast<std::size_t>(-1)) std::cout << "none"; else std::cout << src.row0_beat;
    std::cout << " src_row11_beat=";
    if (src.row11_beat == static_cast<std::size_t>(-1)) std::cout << "none"; else std::cout << src.row11_beat;
    std::cout
              << " src_sum_cols={"
              << src.sum_cols[0] << ","
              << src.sum_cols[1] << ","
              << src.sum_cols[2] << ","
              << src.sum_cols[3] << "}"
              << " addTree={"
              << static_cast<int32_t>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT___addTreeList_0_io_out) << ","
              << static_cast<int32_t>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT___addTreeList_1_io_out) << ","
              << static_cast<int32_t>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT___addTreeList_2_io_out) << ","
              << static_cast<int32_t>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT___addTreeList_3_io_out) << "}"
              << " psums0={"
              << static_cast<int32_t>(cur0) << ","
              << static_cast<int32_t>(cur1) << ","
              << static_cast<int32_t>(cur2) << ","
              << static_cast<int32_t>(cur3) << "}"
              << std::endl;
    if (static_cast<int>(seen) == detail_sample) {
      std::cout << "FFNDownFP32 psum detail"
                << " sample=" << seen
                << " src_in={";
      for (int row = 0; row < 12; ++row) {
        if (row) std::cout << ",";
        std::cout << src.in_lanes[row];
      }
      std::cout << "}";
      for (int col = 0; col < 4; ++col) {
        std::ostringstream woss;
        std::ostringstream poss;
        for (int row = 0; row < 12; ++row) {
          if (row) {
            woss << ",";
            poss << ",";
          }
          woss << src.w_cols[col][row];
          poss << src.prod_cols[col][row];
        }
        std::cout << " w_col" << col << "={" << woss.str() << "}"
                  << " prod_col" << col << "={" << poss.str() << "}"
                  << " sum_col" << col << "=" << src.sum_cols[col];
      }
      std::cout << std::endl;
    }
    prev0 = cur0;
    prev1 = cur1;
    prev2 = cur2;
    prev3 = cur3;
    ++seen;
  }
  require(seen == 12, "FFNDownFP32 psum trace did not observe 12 psum updates");
}

void probe_weight_write_trace(const std::filesystem::path& window_dir, VFFNDownFP32& dut, const PackedWords& data_in) {
  const auto weight_init = read_words(window_dir / "artifacts" / "weight_init.u32.bin", 9);
  const auto cfg = read_cfg(window_dir / "window.cfg");
  write_bias_and_data_then_preload(dut, window_dir, cfg, data_in);

  std::size_t seen = 0;
  for (int cycle = 0; cycle < 200000 && seen < 36; ++cycle) {
    tick(dut);
    if (!dut.rootp->FFNDownFP32__DOT__lw_inst__DOT__io_data_out_valid_REG) {
      continue;
    }
    const auto beat = find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT___lw_inst_io_data_out);
    const auto w0_row0 = find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w0_0_r);
    const auto w1_row0 = find_exact_beat_words9(weight_init, dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__w1_0_r);
    std::cout << "FFNDownFP32 weight write trace"
              << " sample=" << seen
              << " beat=" << beat
              << " w_w_sel=" << static_cast<int>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__weight_w_sel)
              << " w_w_cnt=" << static_cast<int>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__weight_w_cnt)
              << " w_r_sel=" << static_cast<int>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__weight_r_sel)
              << " w0_row0=" << w0_row0
              << " w1_row0=" << w1_row0
              << std::endl;
    ++seen;
  }
  require(seen == 36, "FFNDownFP32 weight write trace did not observe 36 runtime weight beats");
}

void probe_output_trace(const std::filesystem::path& window_dir, VFFNDownFP32& dut, const PackedWords& data_in) {
  const auto golden = read_words(window_dir / "artifacts" / "golden.u32.bin", 12);
  const auto cfg = read_cfg(window_dir / "window.cfg");
  write_bias_and_data_then_preload(dut, window_dir, cfg, data_in);

  int seen = 0;
  for (int cycle = 0; cycle < 200000 && seen < 24; ++cycle) {
    tick(dut);
    if (!dut.io_data_out_valid) {
      continue;
    }
    std::cout << "FFNDownFP32 output trace"
              << " sample=" << seen
              << " addr=" << dut.io_data_out_addr
              << " res_vec=" << static_cast<int>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__res_vector_cnt_r)
              << " out_bank=" << static_cast<int>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT__out_bank_sel)
              << " toFp0=" << static_cast<int32_t>(dut.rootp->FFNDownFP32__DOT__cu_inst__DOT____Vcellinp__toFp__io_in[0])
              << " lane0_obs=" << u32_to_float(dut.io_data_out[0])
              << " lane0_exp=" << u32_to_float(golden.beat(dut.io_data_out_addr)[0])
              << " lane1_obs=" << u32_to_float(dut.io_data_out[1])
              << " lane1_exp=" << u32_to_float(golden.beat(dut.io_data_out_addr)[1])
              << " lane2_obs=" << u32_to_float(dut.io_data_out[2])
              << " lane2_exp=" << u32_to_float(golden.beat(dut.io_data_out_addr)[2])
              << std::endl;
    ++seen;
  }
  require(seen == 24, "FFNDownFP32 output trace did not observe 24 output beats");
}

}  // namespace

int main(int argc, char** argv) {
  try {
    Verilated::commandArgs(argc, argv);
    require(argc == 2 || argc == 3, "usage: VFFNDownFP32 <window_dir> [probe-weight-mem|probe-load|probe-load-trace|probe-prebias|probe-cu|probe-cu-start|probe-tiles|probe-data-trace|probe-psum-trace|probe-mul-source|probe-weight-write|probe-output-trace]");
    const std::filesystem::path window_dir = argv[1];
    const std::string mode = argc == 3 ? argv[2] : "";
    const auto cfg = read_cfg(window_dir / "window.cfg");
    const auto data_in = read_words(window_dir / "artifacts" / "data_in.u32.bin", 3);
    const auto weight_init = read_words(window_dir / "artifacts" / "weight_init.u32.bin", 9);
    const auto bias_init = read_words(window_dir / "artifacts" / "bias_init.u32.bin", 12);
    const auto golden = read_words(window_dir / "artifacts" / "golden.u32.bin", 12);

    VFFNDownFP32 dut;
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
    dut.io_out_scale = cfg_u32(cfg, "out_scale_u32");
    zero_words(dut.io_data_in, 3);
    zero_words(dut.io_weight_init_data, 9);
    zero_words(dut.io_bias_init_data, 12);

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
    require(std::find(seen_weight.begin(), seen_weight.end(), false) == seen_weight.end(), "FFNDownFP32 weight init did not cover all addresses");
    dut.io_weight_init_mode = 0;
    dut.io_layer_st = 0;
    zero_words(dut.io_weight_init_data, 9);
    tick(dut);

    // Keep WeightMem contents, but clear the runtime FSM/counter state before the real run.
    reset_dut(dut);
    dut.io_layer_st = 0;
    dut.io_weight_init_mode = 0;
    dut.io_bias_init_valid = 0;
    dut.io_cfg_prefill = 1;
    dut.io_cfg_seqlen = cfg_int(cfg, "cfg_seqlen");
    dut.io_cfg_valid = 0;
    dut.io_data_out_ready = 1;
    dut.io_out_scale = cfg_u32(cfg, "out_scale_u32");
    dut.io_data_in_st = 0;
    dut.io_data_valid = 0;
    dut.io_data_last = 0;
    zero_words(dut.io_data_in, 3);
    zero_words(dut.io_weight_init_data, 9);
    zero_words(dut.io_bias_init_data, 12);

    if (mode == "probe-weight-mem") {
      probe_weight_memory(dut, weight_init);
      return 0;
    }
    if (mode == "probe-load") {
      probe_weight_memory(dut, weight_init);
      probe_load_sequence(dut, weight_init);
      return 0;
    }
    if (mode == "probe-load-trace") {
      probe_weight_memory(dut, weight_init);
      trace_load_sequence(dut, weight_init, 8);
      return 0;
    }
    if (mode == "probe-prebias") {
      probe_weight_memory(dut, weight_init);
      probe_prebias(window_dir, dut, data_in);
      return 0;
    }
    if (mode == "probe-cu") {
      probe_weight_memory(dut, weight_init);
      probe_cu_state(window_dir, dut, data_in);
      return 0;
    }
    if (mode == "probe-cu-start") {
      probe_weight_memory(dut, weight_init);
      probe_cu_start(window_dir, dut, data_in);
      return 0;
    }
    if (mode == "probe-tiles") {
      probe_weight_memory(dut, weight_init);
      probe_tiles(dut, weight_init);
      return 0;
    }
    if (mode == "probe-data-trace") {
      probe_data_trace(window_dir, dut, data_in);
      return 0;
    }
    if (mode == "probe-psum-trace") {
      probe_weight_memory(dut, weight_init);
      probe_psum_trace(window_dir, dut, data_in);
      return 0;
    }
    if (mode == "probe-mul-source") {
      probe_weight_memory(dut, weight_init);
      probe_mul_source(window_dir, dut, data_in);
      return 0;
    }
    if (mode == "probe-weight-write") {
      probe_weight_memory(dut, weight_init);
      probe_weight_write_trace(window_dir, dut, data_in);
      return 0;
    }
    if (mode == "probe-output-trace") {
      probe_weight_memory(dut, weight_init);
      probe_output_trace(window_dir, dut, data_in);
      return 0;
    }
    require(mode.empty(), "unknown mode, expected probe-weight-mem, probe-load, probe-load-trace, probe-prebias, probe-cu, probe-cu-start, probe-tiles, probe-data-trace, probe-psum-trace, probe-mul-source, probe-weight-write, or probe-output-trace");

    write_bias_and_data_then_preload(dut, window_dir, cfg, data_in);

    std::vector<uint32_t> observed(golden.words.size(), 0);
    std::vector<bool> seen(golden.beats(), false);
    bool saw_last = false;
    auto capture = [&]() {
      if (!dut.io_data_out_valid) {
        return;
      }
      const std::size_t addr = dut.io_data_out_addr;
      require(addr < golden.beats(), "FFNDownFP32 output addr out of range");
      copy_words(observed.data() + addr * 12, dut.io_data_out, 12);
      seen[addr] = true;
      if (dut.io_data_out_last) {
        saw_last = true;
      }
    };

    capture();

    for (int cycle = 0; cycle < 200000 && std::find(seen.begin(), seen.end(), false) != seen.end(); ++cycle) {
      tick(dut);
      capture();
    }

    require(std::find(seen.begin(), seen.end(), false) == seen.end(), "missing FFNDownFP32 output beats");
    require(saw_last, "FFNDownFP32 never asserted io_data_out_last");
    for (std::size_t beat = 0; beat < golden.beats(); ++beat) {
      report_fp32_mismatch("FFNDownFP32", beat, observed.data() + beat * 12, golden.beat(beat), 12);
    }
    std::cout << "FFNDownFP32 PASS beats=" << golden.beats() << std::endl;
    return 0;
  } catch (const std::exception& ex) {
    std::cerr << ex.what() << std::endl;
    return 1;
  }
}
