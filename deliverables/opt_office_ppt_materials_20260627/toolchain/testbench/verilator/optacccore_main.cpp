#include "Vopt_acc_core.h"
#include "Vopt_acc_core_Fp32DivSqrt.h"
#include "Vopt_acc_core_LayerNormQ.h"
#include "Vopt_acc_core___024root.h"
#include "common.hpp"
#include "verilated_save.h"
#include <algorithm>
#include <cstdlib>
#include <cstdint>
#include <cstring>
#include <deque>
#include <filesystem>
#include <vector>

namespace {

constexpr uint64_t C0_BASE_ADDR = 0x0000000800000000ULL;
constexpr int READ_ADDR_LATENCY_DEFAULT = 12;
constexpr int WRITE_RESP_LATENCY_DEFAULT = 8;
constexpr uint64_t MAX_CYCLES = 12000000000ULL;
constexpr uint64_t LN_WEIGHT_BEATS = 128;
constexpr uint64_t QKV_WEIGHT_BEATS = 49152;
constexpr uint64_t QKV_BIAS_BEATS = 192;
constexpr uint64_t SM_BEATS = 26;
constexpr uint64_t OUT_WEIGHT_BEATS = 16896;
constexpr uint64_t OUT_BIAS_BEATS = 64;
constexpr uint64_t FFNUP_WEIGHT_BEATS = 66048;
constexpr uint64_t FFNUP_BIAS_BEATS = 256;
constexpr uint64_t FFNDOWN_WEIGHT_BEATS = 67584;
constexpr uint64_t FFNDOWN_BIAS_BEATS = 64;
constexpr uint64_t OFF_INPUT_BEATS = 0;
constexpr uint64_t OFF_LN1_W_BEATS = 58368;
constexpr uint64_t OFF_QKV_W_BEATS = 58496;
constexpr uint64_t OFF_QKV_B_BEATS = 107648;
constexpr uint64_t OFF_SM_BEATS = 107840;
constexpr uint64_t OFF_OUT_W_BEATS = 107866;
constexpr uint64_t OFF_OUT_B_BEATS = 124762;
constexpr uint64_t OFF_LN2_W_BEATS = 124826;
constexpr uint64_t OFF_FFNUP_W_BEATS = 124954;
constexpr uint64_t OFF_FFNUP_B_BEATS = 191002;
constexpr uint64_t OFF_FFNDOWN_W_BEATS = 191258;
constexpr uint64_t OFF_FFNDOWN_B_BEATS = 258842;
constexpr uint64_t FIXED_WINDOW_TOTAL_BEATS = OFF_FFNDOWN_B_BEATS + FFNDOWN_BIAS_BEATS;

struct PendingRead {
  int cycles_left;
  uint64_t addr;
  uint8_t id;
};

void save_checkpoint(const char* path, uint64_t cycle, Vopt_acc_core& dut) {
  VerilatedSave os;
  os.open(path);
  os << cycle;
  os << dut;
}

void restore_checkpoint(const char* path, uint64_t& cycle, Vopt_acc_core& dut) {
  VerilatedRestore os;
  os.open(path);
  os >> cycle;
  os >> dut;
}

inline uint32_t& cfg_word(Vopt_acc_core& dut, std::size_t idx) {
  return dut.cfg_data[idx];
}

void tick(Vopt_acc_core& dut) {
  dut.c0_ddr4_s_axi_clk = 0;
  dut.clk_300M = 0;
  dut.clk_600M = 0;
  dut.eval();
  dut.c0_ddr4_s_axi_clk = 1;
  dut.clk_300M = 1;
  dut.clk_600M = 1;
  dut.eval();
}

int mem_word_index(uint64_t addr, std::size_t mem_words) {
  require(addr >= C0_BASE_ADDR, "address below C0 base");
  const uint64_t idx = (addr - C0_BASE_ADDR) >> 2;
  require(
      idx < mem_words,
      [&]() {
        std::ostringstream oss;
        oss << "memory index out of range addr=0x"
            << std::hex << addr << std::dec
            << " idx=" << idx
            << " mem_words=" << mem_words;
        return oss.str();
      }());
  return static_cast<int>(idx);
}

void fill_axi_rdata(Vopt_acc_core& dut, const std::vector<uint32_t>& mem, uint64_t addr) {
  const uint64_t aligned = addr & ~0x3FULL;
  const int base = mem_word_index(aligned, mem.size());
  for (int i = 0; i < 16; ++i) {
    dut.c0_ddr4_s_axi_rdata[i] = mem[base + i];
  }
}

void store_axi_wdata(
    std::vector<uint32_t>& mem,
    uint64_t addr,
    const WData* data,
    uint64_t strb) {
  const uint64_t aligned = addr & ~0x3FULL;
  const int base = mem_word_index(aligned, mem.size());
  for (int byte_idx = 0; byte_idx < 64; ++byte_idx) {
    if (((strb >> byte_idx) & 1ULL) == 0ULL) {
      continue;
    }
    const int word_sel = byte_idx / 4;
    const int byte_sel = byte_idx % 4;
    uint32_t cur = mem[base + word_sel];
    const uint8_t byte_val = static_cast<uint8_t>((data[word_sel] >> (byte_sel * 8)) & 0xFFU);
    cur &= ~(0xFFu << (byte_sel * 8));
    cur |= static_cast<uint32_t>(byte_val) << (byte_sel * 8);
    mem[base + word_sel] = cur;
  }
}

}  // namespace

int main(int argc, char** argv) {
  try {
    Verilated::commandArgs(argc, argv);
    require(argc == 2, "usage: Vopt_acc_core <window_dir>");
    const std::filesystem::path window_dir = argv[1];
    const auto cfg = read_cfg(window_dir / "window.cfg");
    const auto ddr_image = read_words(window_dir / "artifacts" / "ddr_image.u32.bin", 16);
    const auto golden = read_words(window_dir / "artifacts" / "golden.u32.bin", 12);
    const bool all_layers_mode =
        cfg.find("all_layers_mode") != cfg.end() && cfg_int(cfg, "all_layers_mode") != 0;
    const bool debug = std::getenv("OPTACC_DEBUG") != nullptr;
    const bool wavefront_debug =
        debug || (std::getenv("OPTACC_WAVEFRONT") != nullptr);
    const bool qkv_trace = std::getenv("OPTACC_TRACE_QKV") != nullptr;
    const char* save_checkpoint_path = std::getenv("OPTACC_SAVE_CHECKPOINT");
    const int save_checkpoint_layer = []() -> int {
      if (const char* raw = std::getenv("OPTACC_SAVE_CHECKPOINT_LAYER")) {
        return std::atoi(raw);
      }
      return -1;
    }();
    const char* restore_checkpoint_path = std::getenv("OPTACC_RESTORE_CHECKPOINT");
    const bool checkpoint_continue =
        std::getenv("OPTACC_CHECKPOINT_CONTINUE") != nullptr;
    const uint64_t wavefront_stride = []() -> uint64_t {
      if (const char* raw = std::getenv("OPTACC_WAVEFRONT_STRIDE")) {
        const long long parsed = std::atoll(raw);
        if (parsed > 0) return static_cast<uint64_t>(parsed);
      }
      return 50000ULL;
    }();
    const uint64_t debug_stride = []() -> uint64_t {
      if (const char* raw = std::getenv("OPTACC_DEBUG_STRIDE")) {
        const long long parsed = std::atoll(raw);
        if (parsed > 0) return static_cast<uint64_t>(parsed);
      }
      return 10000ULL;
    }();
    const int read_addr_latency = []() {
      if (const char* raw = std::getenv("OPTACC_READ_ADDR_LATENCY")) {
        const int parsed = std::atoi(raw);
        if (parsed >= 0) return parsed;
      }
      return READ_ADDR_LATENCY_DEFAULT;
    }();
    const int write_resp_latency = []() {
      if (const char* raw = std::getenv("OPTACC_WRITE_RESP_LATENCY")) {
        const int parsed = std::atoi(raw);
        if (parsed >= 0) return parsed;
      }
      return WRITE_RESP_LATENCY_DEFAULT;
    }();
    const uint64_t output_stride_bytes = cfg_u64(cfg, "axi_output_stride_bytes");
    const int output_beats_cfg = cfg_int(cfg, "output_beats");
    const uint64_t compact_total_beats = ddr_image.words.size() / 16ULL;
    const uint64_t input_base_addr = C0_BASE_ADDR;
    const uint64_t output_base_addr =
        C0_BASE_ADDR + ((all_layers_mode ? compact_total_beats : FIXED_WINDOW_TOTAL_BEATS) * 64ULL);
    const uint64_t token_count = static_cast<uint64_t>(cfg_int(cfg, "cfg_seqlen")) + 1ULL;
    const uint64_t output_bytes = static_cast<uint64_t>(output_beats_cfg) * output_stride_bytes;
    const uint64_t kv_hist_bytes = token_count * 768ULL * 2ULL;
    const std::size_t extra_words =
        static_cast<std::size_t>((output_bytes + kv_hist_bytes + 4096ULL + 3ULL) / 4ULL);

    const std::size_t fixed_window_words = static_cast<std::size_t>(FIXED_WINDOW_TOTAL_BEATS * 16ULL);
    const std::size_t image_words = ddr_image.words.size();
    std::vector<uint32_t> mem_words(
        std::max(fixed_window_words, image_words) + std::max<std::size_t>(extra_words, 262144),
        0U);
    std::copy(ddr_image.words.begin(), ddr_image.words.end(), mem_words.begin());
    std::vector<bool> seen(static_cast<std::size_t>(output_beats_cfg), false);

    const uint64_t compact_input_base_beat = all_layers_mode ? 0ULL : cfg_u64(cfg, "ddr_input_base_addr");
    const uint64_t compact_ln1_w_base_beat = all_layers_mode ? 0ULL : cfg_u64(cfg, "ddr_ln1_w_base_addr");
    const uint64_t compact_qkv_w_base_beat = all_layers_mode ? 0ULL : cfg_u64(cfg, "ddr_qkv_w_base_addr");
    const uint64_t compact_qkv_b_base_beat = all_layers_mode ? 0ULL : cfg_u64(cfg, "ddr_qkv_b_base_addr");
    const uint64_t compact_sm_base_beat = all_layers_mode ? 0ULL : cfg_u64(cfg, "ddr_sm_base_addr");
    const uint64_t compact_out_w_base_beat = all_layers_mode ? 0ULL : cfg_u64(cfg, "ddr_out_w_base_addr");
    const uint64_t compact_out_b_base_beat = all_layers_mode ? 0ULL : cfg_u64(cfg, "ddr_out_b_base_addr");
    const uint64_t compact_ln2_w_base_beat = all_layers_mode ? 0ULL : cfg_u64(cfg, "ddr_ln2_w_base_addr");
    const uint64_t compact_ffnup_w_base_beat = all_layers_mode ? 0ULL : cfg_u64(cfg, "ddr_ffnup_w_base_addr");
    const uint64_t compact_ffnup_b_base_beat = all_layers_mode ? 0ULL : cfg_u64(cfg, "ddr_ffnup_b_base_addr");
    const uint64_t compact_ffndown_w_base_beat = all_layers_mode ? 0ULL : cfg_u64(cfg, "ddr_ffndown_w_base_addr");
    const uint64_t compact_ffndown_b_base_beat = all_layers_mode ? 0ULL : cfg_u64(cfg, "ddr_ffndown_b_base_addr");
    const uint64_t compact_input_len = all_layers_mode ? 0ULL : (compact_ln1_w_base_beat - compact_input_base_beat);
    const uint64_t compact_ln1_w_len = all_layers_mode ? 0ULL : (compact_qkv_w_base_beat - compact_ln1_w_base_beat);
    const uint64_t compact_qkv_w_len = all_layers_mode ? 0ULL : (compact_qkv_b_base_beat - compact_qkv_w_base_beat);
    const uint64_t compact_qkv_b_len = all_layers_mode ? 0ULL : (compact_sm_base_beat - compact_qkv_b_base_beat);
    const uint64_t compact_sm_len = all_layers_mode ? 0ULL : (compact_out_w_base_beat - compact_sm_base_beat);
    const uint64_t compact_out_w_len = all_layers_mode ? 0ULL : (compact_out_b_base_beat - compact_out_w_base_beat);
    const uint64_t compact_out_b_len = all_layers_mode ? 0ULL : (compact_ln2_w_base_beat - compact_out_b_base_beat);
    const uint64_t compact_ln2_w_len = all_layers_mode ? 0ULL : (compact_ffnup_w_base_beat - compact_ln2_w_base_beat);
    const uint64_t compact_ffnup_w_len = all_layers_mode ? 0ULL : (compact_ffnup_b_base_beat - compact_ffnup_w_base_beat);
    const uint64_t compact_ffnup_b_len = all_layers_mode ? 0ULL : (compact_ffndown_w_base_beat - compact_ffnup_b_base_beat);
    const uint64_t compact_ffndown_w_len = all_layers_mode ? 0ULL : (compact_ffndown_b_base_beat - compact_ffndown_w_base_beat);
    const uint64_t compact_ffndown_b_len = all_layers_mode ? 0ULL : (compact_total_beats - compact_ffndown_b_base_beat);
    const uint64_t zero_pad_base_addr = output_base_addr;
    auto remap_window_read_addr = [&](uint64_t addr) -> uint64_t {
      if (all_layers_mode) {
        return addr;
      }
      if (addr < input_base_addr || addr >= output_base_addr) {
        return addr;
      }
      const uint64_t beat = (addr - input_base_addr) >> 6;
      struct RegionMap {
        uint64_t fixed_base;
        uint64_t fixed_len;
        uint64_t compact_base;
        uint64_t compact_len;
      };
      const RegionMap regions[] = {
          {OFF_INPUT_BEATS, compact_input_len, compact_input_base_beat, compact_input_len},
          {OFF_LN1_W_BEATS, LN_WEIGHT_BEATS, compact_ln1_w_base_beat, compact_ln1_w_len},
          {OFF_QKV_W_BEATS, QKV_WEIGHT_BEATS, compact_qkv_w_base_beat, compact_qkv_w_len},
          {OFF_QKV_B_BEATS, QKV_BIAS_BEATS, compact_qkv_b_base_beat, compact_qkv_b_len},
          {OFF_SM_BEATS, SM_BEATS, compact_sm_base_beat, compact_sm_len},
          {OFF_OUT_W_BEATS, OUT_WEIGHT_BEATS, compact_out_w_base_beat, compact_out_w_len},
          {OFF_OUT_B_BEATS, OUT_BIAS_BEATS, compact_out_b_base_beat, compact_out_b_len},
          {OFF_LN2_W_BEATS, LN_WEIGHT_BEATS, compact_ln2_w_base_beat, compact_ln2_w_len},
          {OFF_FFNUP_W_BEATS, FFNUP_WEIGHT_BEATS, compact_ffnup_w_base_beat, compact_ffnup_w_len},
          {OFF_FFNUP_B_BEATS, FFNUP_BIAS_BEATS, compact_ffnup_b_base_beat, compact_ffnup_b_len},
          {OFF_FFNDOWN_W_BEATS, FFNDOWN_WEIGHT_BEATS, compact_ffndown_w_base_beat, compact_ffndown_w_len},
          {OFF_FFNDOWN_B_BEATS, FFNDOWN_BIAS_BEATS, compact_ffndown_b_base_beat, compact_ffndown_b_len},
      };
      for (const auto& region : regions) {
        if (beat >= region.fixed_base && beat < region.fixed_base + region.fixed_len) {
          const uint64_t local = beat - region.fixed_base;
          const uint64_t mapped_beat =
              (local < region.compact_len) ? (region.compact_base + local)
                                           : ((zero_pad_base_addr - C0_BASE_ADDR) >> 6) + local;
          return C0_BASE_ADDR + (mapped_beat << 6);
        }
      }
      return addr;
    };

    Vopt_acc_core dut;
    dut.user_rst = 1;
    dut.sys_rst_n = 0;
    dut.c0_ddr4_s_axi_rst_n = 0;
    dut.c0_init_calib_complete = 0;
    dut.cfg_data_valid = 0;
    dut.cfg_done = 0;
    dut.cnn0_input_batch_set = 0;
    dut.cnn0_result_batch_clear = 0;
    dut.c0_ddr4_s_axi_awready = 0;
    dut.c0_ddr4_s_axi_wready = 0;
    dut.c0_ddr4_s_axi_bvalid = 0;
    dut.c0_ddr4_s_axi_bresp = 0;
    dut.c0_ddr4_s_axi_bid = 0;
    dut.c0_ddr4_s_axi_arready = 0;
    dut.c0_ddr4_s_axi_rvalid = 0;
    dut.c0_ddr4_s_axi_rlast = 0;
    dut.c0_ddr4_s_axi_rresp = 0;
    dut.c0_ddr4_s_axi_rid = 0;
    for (int i = 0; i < 16; ++i) {
      dut.c0_ddr4_s_axi_rdata[i] = 0;
    }
    for (int i = 0; i < 22; ++i) {
      cfg_word(dut, i) = 0U;
    }

    const uint64_t rel_window_base = input_base_addr - C0_BASE_ADDR;
    const uint64_t rel_output_base = output_base_addr - C0_BASE_ADDR;
    cfg_word(dut, 0) = static_cast<uint32_t>(cfg_int(cfg, "cfg_seqlen"));
    cfg_word(dut, 1) = static_cast<uint32_t>(output_stride_bytes);
    cfg_word(dut, 2) = static_cast<uint32_t>(rel_window_base & 0xFFFFFFFFULL);
    cfg_word(dut, 3) = static_cast<uint32_t>(rel_window_base >> 32);
    cfg_word(dut, 4) = static_cast<uint32_t>(rel_output_base & 0xFFFFFFFFULL);
    cfg_word(dut, 5) = static_cast<uint32_t>(rel_output_base >> 32);
    cfg_word(dut, 6) = static_cast<uint32_t>(cfg_int(cfg, "ln1_out_zero_point_s8")) & 0xFFU;
    cfg_word(dut, 6) |= (cfg_u32(cfg, "dm2_ctx_zero_point_u8") & 0xFFU) << 8;
    cfg_word(dut, 6) |= (static_cast<uint32_t>(cfg_int(cfg, "ln2_out_zero_point_s8")) & 0xFFU) << 16;
    if (cfg.find("all_layers_mode") != cfg.end() && cfg_int(cfg, "all_layers_mode") != 0) {
      cfg_word(dut, 6) |= 1u << 24;
    }
    cfg_word(dut, 7) = cfg_u32(cfg, "ln1_out_inv_scale_u32");
    cfg_word(dut, 8) = cfg_u32(cfg, "q_out_inv_scale_u32");
    cfg_word(dut, 9) = cfg_u32(cfg, "k_out_inv_scale_u32");
    cfg_word(dut, 10) = cfg_u32(cfg, "v_out_inv_scale_u32");
    cfg_word(dut, 11) = cfg_u32(cfg, "q_bias_scale_u32");
    cfg_word(dut, 12) = cfg_u32(cfg, "k_bias_scale_u32");
    cfg_word(dut, 13) = cfg_u32(cfg, "v_bias_scale_u32");
    cfg_word(dut, 14) = cfg_u32(cfg, "dm1_out_scale_u32");
    cfg_word(dut, 15) = cfg_u32(cfg, "dm2_ctx_inv_scale_u32");
    cfg_word(dut, 16) = cfg_u32(cfg, "dm2_out_inv_scale_u32");
    cfg_word(dut, 17) = cfg_u32(cfg, "out_out_scale_u32");
    cfg_word(dut, 18) = cfg_u32(cfg, "ln2_out_inv_scale_u32");
    cfg_word(dut, 19) = cfg_u32(cfg, "ffnup_out_inv_scale_u32");
    cfg_word(dut, 20) = cfg_u32(cfg, "ffnup_bias_scale_u32");
    cfg_word(dut, 21) = cfg_u32(cfg, "ffndown_out_scale_u32");

    for (int i = 0; i < 20; ++i) {
      tick(dut);
    }
    dut.user_rst = 0;
    dut.sys_rst_n = 1;
    dut.c0_ddr4_s_axi_rst_n = 1;
    for (int i = 0; i < 20; ++i) {
      tick(dut);
    }
    dut.c0_init_calib_complete = 1;
    tick(dut);

    dut.cfg_data_valid = 1;
    dut.cfg_done = 1;
    tick(dut);
    dut.cfg_data_valid = 0;
    dut.cfg_done = 0;
    for (int i = 0; i < 4; ++i) {
      tick(dut);
    }
    dut.cnn0_input_batch_set = 1;
    tick(dut);
    dut.cnn0_input_batch_set = 0;

    std::deque<PendingRead> pending_reads;
    bool wr_active = false;
    uint64_t wr_addr = 0;
    uint8_t wr_id = 0;
    bool b_pending = false;
    int b_latency = 0;
    uint64_t cycle = 0;
    std::size_t seen_count = 0;
    int prev_state = -1;
    int prev_layer = -1;
    int prev_run_token = -1;
    int prev_result_count = -1;
    uint64_t qkv_fire_count = 0;
    uint64_t qkv_last_count = 0;
    uint64_t qkvq_enq_count = 0;
    uint64_t qkvq_deq_count = 0;
    uint64_t ln_addr_fire_count = 0;
    uint64_t ln_addr_valid_count = 0;
    uint64_t ln1_in_count = 0;
    uint64_t ln1_out_count = 0;
    uint64_t qkv_collect_count = 0;
    uint64_t dm1_in_count = 0;
    uint64_t dm1_last_count = 0;
    uint64_t ctx_enq_count = 0;
    uint64_t v_enq_count = 0;
    uint64_t attn_out_count = 0;
    uint64_t outlinear_out_count = 0;
    bool checkpoint_saved = false;

    if (restore_checkpoint_path != nullptr && restore_checkpoint_path[0] != '\0') {
      restore_checkpoint(restore_checkpoint_path, cycle, dut);
      std::cerr << "optacc checkpoint-restored path=" << restore_checkpoint_path
                << " cycle=" << cycle
                << " state=" << static_cast<int>(dut.rootp->opt_acc_core__DOT__state)
                << " layer=" << static_cast<int>(dut.rootp->opt_acc_core__DOT__layer_idx)
                << std::endl;
    }

    while (dut.cnn0_result_count != 1 && cycle < MAX_CYCLES) {
      dut.c0_ddr4_s_axi_arready = 1;
      dut.c0_ddr4_s_axi_awready = ((cycle % 13) != 0);
      dut.c0_ddr4_s_axi_wready = ((cycle % 11) != 0);
      const bool r_fire_now = dut.c0_ddr4_s_axi_rvalid && dut.c0_ddr4_s_axi_rready;
      const bool w_fire_now = wr_active && dut.c0_ddr4_s_axi_wvalid && dut.c0_ddr4_s_axi_wready;
      const bool b_fire_now = dut.c0_ddr4_s_axi_bvalid && dut.c0_ddr4_s_axi_bready;

      if (dut.c0_ddr4_s_axi_arvalid && dut.c0_ddr4_s_axi_arready) {
        pending_reads.push_back(PendingRead{
            read_addr_latency,
            static_cast<uint64_t>(dut.c0_ddr4_s_axi_araddr),
            static_cast<uint8_t>(dut.c0_ddr4_s_axi_arid)});
      }

      if (!wr_active && dut.c0_ddr4_s_axi_awvalid && dut.c0_ddr4_s_axi_awready) {
        wr_active = true;
        wr_addr = dut.c0_ddr4_s_axi_awaddr;
        wr_id = static_cast<uint8_t>(dut.c0_ddr4_s_axi_awid);
      }

      if (!dut.c0_ddr4_s_axi_rvalid && !pending_reads.empty()) {
        if (pending_reads.front().cycles_left > 0) {
          --pending_reads.front().cycles_left;
        } else {
          fill_axi_rdata(dut, mem_words, remap_window_read_addr(pending_reads.front().addr));
          dut.c0_ddr4_s_axi_rid = pending_reads.front().id;
          dut.c0_ddr4_s_axi_rresp = 0;
          dut.c0_ddr4_s_axi_rvalid = 1;
          dut.c0_ddr4_s_axi_rlast = 1;
        }
      }

      if (b_pending) {
        if (b_latency > 0) {
          --b_latency;
        } else if (!dut.c0_ddr4_s_axi_bvalid) {
          dut.c0_ddr4_s_axi_bid = wr_id;
          dut.c0_ddr4_s_axi_bresp = 0;
          dut.c0_ddr4_s_axi_bvalid = 1;
        }
      }

      tick(dut);
      ++cycle;

      if (r_fire_now) {
        dut.c0_ddr4_s_axi_rvalid = 0;
        dut.c0_ddr4_s_axi_rlast = 0;
        if (!pending_reads.empty()) {
          pending_reads.pop_front();
        }
      }

      if (w_fire_now) {
        store_axi_wdata(mem_words, wr_addr, dut.c0_ddr4_s_axi_wdata, dut.c0_ddr4_s_axi_wstrb);
        if (wr_addr >= output_base_addr && wr_addr < output_base_addr + static_cast<uint64_t>(output_beats_cfg) * output_stride_bytes) {
          const auto beat_idx = static_cast<std::size_t>((wr_addr - output_base_addr) / output_stride_bytes);
          if (beat_idx < seen.size() && !seen[beat_idx]) {
            seen[beat_idx] = true;
            ++seen_count;
          }
        }
        wr_active = false;
        b_pending = true;
        b_latency = write_resp_latency;
      }

      if (b_fire_now) {
        dut.c0_ddr4_s_axi_bvalid = 0;
        b_pending = false;
      }

      {
        auto* root = dut.rootp;
        auto* ln1 = root->__PVT__opt_acc_core__DOT__u_core__DOT__layernorm;
        const bool ln_addr_fire =
            root->opt_acc_core__DOT__u_core__DOT__ln_addr_gen__DOT__unnamedblk1__DOT__fire;
        const bool ln_addr_valid =
            root->opt_acc_core__DOT__u_core__DOT__ln_addr_gen__DOT__io_data_valid_REG;
        const bool ln1_in = ln1->io_data_valid && ln1->io_data_ready;
        const bool ln1_out = ln1->io_res_valid;
        const bool qkv_collect =
            root->opt_acc_core__DOT__u_core__DOT__qkvlinear__DOT__collect_fire;
        const bool qkv_fire =
            root->opt_acc_core__DOT__u_core__DOT__qkvlinear__DOT__output_fire;
        const bool qkv_last =
            qkv_fire &&
            root->opt_acc_core__DOT__u_core__DOT__qkvlinear__DOT__outputCntReg == 31 &&
            root->opt_acc_core__DOT__u_core__DOT__qkvlinear__DOT__token_last;
        const bool qkvq_enq =
            root->opt_acc_core__DOT__u_core__DOT__qkvToAttnQ__DOT__do_enq;
        const bool qkvq_deq =
            root->opt_acc_core__DOT__u_core__DOT__qkvToAttnQ__DOT__unnamedblk1__DOT__do_deq;
        const bool dm1_in = qkvq_deq;
        const bool dm1_last =
            dm1_in &&
            root->opt_acc_core__DOT__u_core__DOT__atten__DOT____Vcellinp__dm1__io_data_last;
        const bool ctx_enq =
            root->opt_acc_core__DOT__u_core__DOT__atten__DOT__ctxToDm2Q__DOT__do_enq;
        const bool v_enq =
            root->opt_acc_core__DOT__u_core__DOT__atten__DOT__vToDm2Q__DOT__do_enq;
        const bool attn_out =
            root->opt_acc_core__DOT__u_core__DOT__attnToOutQ__DOT__do_enq;
        const bool outlinear_out =
            root->opt_acc_core__DOT__u_core__DOT__outToResQ__DOT__do_enq;

        qkv_fire_count += qkv_fire ? 1 : 0;
        qkv_last_count += qkv_last ? 1 : 0;
        qkvq_enq_count += qkvq_enq ? 1 : 0;
        qkvq_deq_count += qkvq_deq ? 1 : 0;
        ln_addr_fire_count += ln_addr_fire ? 1 : 0;
        ln_addr_valid_count += ln_addr_valid ? 1 : 0;
        ln1_in_count += ln1_in ? 1 : 0;
        ln1_out_count += ln1_out ? 1 : 0;
        qkv_collect_count += qkv_collect ? 1 : 0;
        dm1_in_count += dm1_in ? 1 : 0;
        dm1_last_count += dm1_last ? 1 : 0;
        ctx_enq_count += ctx_enq ? 1 : 0;
        v_enq_count += v_enq ? 1 : 0;
        attn_out_count += attn_out ? 1 : 0;
        outlinear_out_count += outlinear_out ? 1 : 0;

        if (qkv_trace &&
            (qkv_last || (qkv_fire && qkv_fire_count <= 8) || dm1_last ||
             attn_out || outlinear_out ||
             (ln_addr_fire && ln_addr_fire_count <= 8) ||
             (ln1_out && ln1_out_count <= 8) ||
             (cycle % wavefront_stride) == 0ULL)) {
          std::cerr << "optacc qkv-trace"
                    << " cycle=" << cycle
                    << " top_state=" << static_cast<int>(root->opt_acc_core__DOT__state)
                    << " layer=" << static_cast<int>(root->opt_acc_core__DOT__layer_idx)
                    << " run1=" << static_cast<int>(root->opt_acc_core__DOT__core_run_sync1)
                    << " run2=" << static_cast<int>(root->opt_acc_core__DOT__core_run_sync2)
                    << " cfg_p=" << static_cast<int>(root->opt_acc_core__DOT__core_cfg_valid_pulse_r)
                    << " layer_p=" << static_cast<int>(root->opt_acc_core__DOT__core_layer_st_pulse_r)
                    << " ln_addr_fire=" << static_cast<int>(ln_addr_fire)
                    << " ln_addr_fire_n=" << ln_addr_fire_count
                    << " ln_addr_valid_n=" << ln_addr_valid_count
                    << " ln_addr_state=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__ln_addr_gen__DOT__state)
                    << " ln_start_pending=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__ln_addr_gen__DOT__start_pending)
                    << " ln_vec_addr=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__ln_addr_gen__DOT__vec_cnt_r)
                    << " ln_pref=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__ln_addr_gen__DOT__prefill_cnt_r)
                    << " ln_batch=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__ln_addr_gen__DOT__batch_cnt_r)
                    << " ln_adapter_ready=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT____Vcellinp__ln_addr_gen__io_adapter_ready)
                    << " ln_in_n=" << ln1_in_count
                    << " ln_out_n=" << ln1_out_count
                    << " ln_state=" << static_cast<int>(ln1->__PVT__state)
                    << " ln_data_v=" << static_cast<int>(ln1->io_data_valid)
                    << " ln_data_r=" << static_cast<int>(ln1->io_data_ready)
                    << " ln_data_last=" << static_cast<int>(ln1->io_data_last)
                    << " ln_data_addr=" << static_cast<int>(ln1->io_data_addr)
                    << " ln_out=" << static_cast<int>(ln1_out)
                    << " ln_out_last=" << static_cast<int>(ln1->io_res_last)
                    << " ln_out_addr=" << static_cast<int>(ln1->io_res_addr)
                    << " ln_input_loaded=" << static_cast<int>(ln1->__PVT__inputLoaded)
                    << " ln_weights=" << static_cast<int>(ln1->__PVT__weightsLoaded)
                    << " ln_token=" << static_cast<int>(ln1->__PVT__tokenIdx)
                    << " ln_vec=" << static_cast<int>(ln1->__PVT__vecIdx)
                    << " ln_var=0x" << std::hex << ln1->__PVT__varReg << std::dec
                    << " ln_sqrt_reg=0x" << std::hex << ln1->__PVT__sqrtReg << std::dec
                    << " ln_invstd=0x" << std::hex << ln1->__PVT__invStdReg << std::dec
                    << " sqrt_v=" << static_cast<int>(ln1->__PVT__sqrt_io_inValid)
                    << " sqrt_r=" << static_cast<int>(ln1->__PVT__sqrt->io_inReady)
                    << " sqrt_ov=" << static_cast<int>(ln1->__PVT__sqrt->__PVT__io_outValidSqrt)
                    << " sqrt_cyc=" << static_cast<int>(
                           ln1->__PVT__sqrt->__PVT__sqrt__DOT__core__DOT__divSqrt__DOT__divSqrtRecFNToRaw__DOT__divSqrtRawFN__DOT__cycleNum)
                    << " sqrt_raw_ov=" << static_cast<int>(
                           ln1->__PVT__sqrt->__PVT__sqrt__DOT__core__DOT__divSqrt__DOT__divSqrtRecFNToRaw__DOT__divSqrtRawFN__DOT__rawOutValid)
                    << " sqrt_raw_r=" << static_cast<int>(
                           ln1->__PVT__sqrt->__PVT__sqrt__DOT__core__DOT__divSqrt__DOT__divSqrtRecFNToRaw__DOT__divSqrtRawFN__DOT__inReady)
                    << " div_v=" << static_cast<int>(ln1->__PVT__div_io_inValid)
                    << " div_r=" << static_cast<int>(ln1->__PVT__div->io_inReady)
                    << " div_ov=" << static_cast<int>(ln1->__PVT__div->io_outValidDiv)
                    << " div_cyc=" << static_cast<int>(
                           ln1->__PVT__div->__PVT__div__DOT__core__DOT__divSqrt__DOT__divSqrtRecFNToRaw__DOT__divSqrtRawFN__DOT__cycleNum)
                    << " div_raw_ov=" << static_cast<int>(
                           ln1->__PVT__div->__PVT__div__DOT__core__DOT__divSqrt__DOT__divSqrtRecFNToRaw__DOT__divSqrtRawFN__DOT__rawOutValid)
                    << " div_raw_r=" << static_cast<int>(
                           ln1->__PVT__div->__PVT__div__DOT__core__DOT__divSqrt__DOT__divSqrtRecFNToRaw__DOT__divSqrtRawFN__DOT__inReady)
                    << " qkv_collect=" << static_cast<int>(qkv_collect)
                    << " qkv_collect_n=" << qkv_collect_count
                    << " qkv_mem_full=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__qkvlinear__DOT__mem_inst__DOT__full_cnt_r)
                    << " qkv_fire=" << static_cast<int>(qkv_fire)
                    << " qkv_fire_n=" << qkv_fire_count
                    << " qkv_last_n=" << qkv_last_count
                    << " qkv_state=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__qkvlinear__DOT__state)
                    << " qkv_head=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__qkvlinear__DOT__headCntReg)
                    << " qkv_pref=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__qkvlinear__DOT__prefillCntReg)
                    << " qkv_batch=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__qkvlinear__DOT__batchCntReg)
                    << " qkv_out=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__qkvlinear__DOT__outputCntReg)
                    << " token_last=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__qkvlinear__DOT__token_last)
                    << " head_last=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__qkvlinear__DOT__head_last)
                    << " all_done=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__qkvlinear__DOT__all_output_done)
                    << " shadow=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__qkvlinear__DOT__shadowValidReg)
                    << " pf_busy=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__qkvlinear__DOT__prefetchBusyReg)
                    << " pf_step=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__qkvlinear__DOT__prefetchStepReg)
                    << " q_enq_n=" << qkvq_enq_count
                    << " q_deq_n=" << qkvq_deq_count
                    << " q_empty=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__qkvToAttnQ__DOT__empty)
                    << " q_full=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__qkvToAttnQ__DOT__maybe_full)
                    << " attn_rdy=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT___atten_io_data_ready)
                    << " ingress_valid=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__atten__DOT__ingress_valid)
                    << " attn_active=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__atten__DOT__attnRequestActive)
                    << " attn_done_heads=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__atten__DOT__attnHeadDoneCnt)
                    << " dm1_in_n=" << dm1_in_count
                    << " dm1_last_n=" << dm1_last_count
                    << " dm1_state=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__atten__DOT__dm1__DOT__cu_inst__DOT__state)
                    << " dm1_hvec=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__atten__DOT__dm1__DOT__cu_inst__DOT__headvec_cnt)
                    << " softmax_state=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__atten__DOT__softmax__DOT__state)
                    << " ctx_enq_n=" << ctx_enq_count
                    << " ctx_deq=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__atten__DOT__ctxToDm2Q__DOT__unnamedblk1__DOT__do_deq)
                    << " ctx_empty=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__atten__DOT__ctxToDm2Q__DOT__empty)
                    << " v_enq_n=" << v_enq_count
                    << " v_deq=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__atten__DOT__vToDm2Q__DOT__unnamedblk1__DOT__do_deq)
                    << " v_empty=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__atten__DOT__vToDm2Q__DOT__empty)
                    << " dm2_state=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__atten__DOT__dm2__DOT__dmInst__DOT__state)
                    << " dm2_mul=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__atten__DOT__dm2__DOT__dmInst__DOT__mulCnt)
                    << " attn_out_n=" << attn_out_count
                    << " outlinear_out_n=" << outlinear_out_count
                    << std::endl;
        }
      }

      if (!checkpoint_saved &&
          save_checkpoint_path != nullptr &&
          save_checkpoint_path[0] != '\0' &&
          dut.rootp->opt_acc_core__DOT__state == 13 &&
          (save_checkpoint_layer < 0 ||
           static_cast<int>(dut.rootp->opt_acc_core__DOT__layer_idx) == save_checkpoint_layer)) {
        require(pending_reads.empty(), "checkpoint boundary has pending AXI reads");
        require(!wr_active, "checkpoint boundary has an active AXI write address");
        require(!b_pending, "checkpoint boundary has a pending AXI write response");
        require(dut.c0_ddr4_s_axi_rvalid == 0, "checkpoint boundary has AXI rvalid asserted");
        require(dut.c0_ddr4_s_axi_bvalid == 0, "checkpoint boundary has AXI bvalid asserted");
        require(seen_count == 0, "checkpoint boundary is after output writes started");
        save_checkpoint(save_checkpoint_path, cycle, dut);
        checkpoint_saved = true;
        std::cerr << "optacc checkpoint-saved path=" << save_checkpoint_path
                  << " cycle=" << cycle
                  << " state=" << static_cast<int>(dut.rootp->opt_acc_core__DOT__state)
                  << " layer=" << static_cast<int>(dut.rootp->opt_acc_core__DOT__layer_idx)
                  << std::endl;
        if (!checkpoint_continue) {
          std::cout << "opt_acc_core CHECKPOINT saved cycle=" << cycle << std::endl;
          return 0;
        }
      }

      if (debug && (cycle % debug_stride) == 0ULL) {
        auto* root = dut.rootp;
        std::cerr << "optacc progress"
                  << " cycle=" << cycle
                  << " state=" << static_cast<int>(root->opt_acc_core__DOT__state)
                  << " layer=" << static_cast<int>(root->opt_acc_core__DOT__layer_idx)
                  << " run_token=" << static_cast<int>(root->opt_acc_core__DOT__run_token_idx)
                  << " result_count=" << static_cast<int>(dut.cnn0_result_count)
                  << " batch_count=" << static_cast<int>(dut.cnn0_batch_count)
                  << " seen=" << seen_count << "/" << output_beats_cfg
                  << " issue=" << root->opt_acc_core__DOT__issue_count
                  << " recv=" << root->opt_acc_core__DOT__recv_count
                  << " ar_v=" << static_cast<int>(dut.c0_ddr4_s_axi_arvalid)
                  << " ar_r=" << static_cast<int>(dut.c0_ddr4_s_axi_arready)
                  << " r_v=" << static_cast<int>(dut.c0_ddr4_s_axi_rvalid)
                  << " r_r=" << static_cast<int>(dut.c0_ddr4_s_axi_rready)
                  << " rd_q=" << pending_reads.size()
                  << " rd_lat=" << (pending_reads.empty() ? -1 : pending_reads.front().cycles_left)
                  << " aw_v=" << static_cast<int>(dut.c0_ddr4_s_axi_awvalid)
                  << " w_v=" << static_cast<int>(dut.c0_ddr4_s_axi_wvalid)
                  << " b_v=" << static_cast<int>(dut.c0_ddr4_s_axi_bvalid)
                  << " qkv_st=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__qkvlinear__DOT__state)
                  << " qkv_addr=" << root->opt_acc_core__DOT__u_core__DOT__qkvlinear__DOT___lu_inst_io_data_in_addr
                  << " out_st=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__outlinear__DOT__state)
                  << " out_addr=" << root->opt_acc_core__DOT__u_core__DOT__outlinear__DOT___lu_inst_io_data_in_addr
                  << " ffnup_st=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__ffnup__DOT__cu_inst__DOT__state)
                  << " ffnup_addr=" << root->opt_acc_core__DOT__u_core__DOT__ffnup__DOT___lu_inst_io_data_in_addr
                  << " ffndown_st=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__ffndown__DOT__cu_inst__DOT__state)
                  << " ffndown_addr=" << root->opt_acc_core__DOT__u_core__DOT__ffndown__DOT___lu_inst_io_data_in_addr
                  << std::endl;
      }

      if (wavefront_debug && !debug && (cycle % wavefront_stride) == 0ULL) {
        auto* root = dut.rootp;
        std::cerr << "optacc hb"
                  << " cycle=" << cycle
                  << " state=" << static_cast<int>(root->opt_acc_core__DOT__state)
                  << " layer=" << static_cast<int>(root->opt_acc_core__DOT__layer_idx)
                  << " seen=" << seen_count << "/" << output_beats_cfg
                  << " issue=" << root->opt_acc_core__DOT__issue_count
                  << " recv=" << root->opt_acc_core__DOT__recv_count
                  << " cur_len=" << root->opt_acc_core__DOT__cur_len
                  << " preload_wait=" << static_cast<int>(root->opt_acc_core__DOT__preload_full_wait)
                  << " preload_layer=" << static_cast<int>(root->opt_acc_core__DOT__preload_layer_idx)
                  << " pending_sw=" << static_cast<int>(root->opt_acc_core__DOT__pending_layer_switch)
                  << " pending_layer=" << static_cast<int>(root->opt_acc_core__DOT__pending_layer_idx)
                  << " wt_init_bank=" << static_cast<int>(root->opt_acc_core__DOT__weight_init_bank_sel)
                  << " wt_valid=" << static_cast<int>(root->opt_acc_core__DOT__weight_bank_valid)
                  << " wt_layer0=" << static_cast<int>(root->opt_acc_core__DOT__weight_bank_layer_idx[0])
                  << " wt_layer1=" << static_cast<int>(root->opt_acc_core__DOT__weight_bank_layer_idx[1])
                  << " bgp_act=" << static_cast<int>(root->opt_acc_core__DOT__bg_preload_active)
                  << " bgp_bank=" << static_cast<int>(root->opt_acc_core__DOT__bg_preload_bank_sel)
                  << " bgp_layer=" << static_cast<int>(root->opt_acc_core__DOT__bg_preload_layer_idx)
                  << " bgp_state=" << static_cast<int>(root->opt_acc_core__DOT__bg_preload_state)
                  << " bgp_issue=" << root->opt_acc_core__DOT__bg_issue_count
                  << " bgp_recv=" << root->opt_acc_core__DOT__bg_recv_count
                  << " rd_bg=" << static_cast<int>(root->opt_acc_core__DOT__rd_bg_preload_active)
                  << " act_bank=" << static_cast<int>(root->opt_acc_core__DOT__active_act_bank)
                  << " wt_bank=" << static_cast<int>(root->opt_acc_core__DOT__active_weight_bank)
                  << " attn_rdy=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT___atten_io_data_ready)
                  << " dm2_ctx_rdy=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__atten__DOT__dm2__DOT___dmInst_io_data_in_ctx_ready)
                  << " dm2_v_valid=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__atten__DOT__dm2__DOT____Vcellinp__dmInst__io_data_in_v_valid)
                  << " dm2_ctx_valid=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__atten__DOT__dm2__DOT____Vcellinp__dmInst__io_data_in_ctx_valid)
                  << " dm2_seq=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__atten__DOT__dm2__DOT__dmInst__DOT__seqlen)
                  << " dm2_outq_empty=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__atten__DOT__dm2__DOT__outQ__DOT__empty)
                  << " dm2_outq_full=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__atten__DOT__dm2__DOT__outQ__DOT__maybe_full)
                  << " dm2_outq_enq=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__atten__DOT__dm2__DOT__outQ__DOT__do_enq)
                  << " dm2_outq_deq=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__atten__DOT__dm2__DOT__outQ__DOT__unnamedblk1__DOT__do_deq)
                  << " dm2_state=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__atten__DOT__dm2__DOT__dmInst__DOT__state)
                  << " dm2_lbatch=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__atten__DOT__dm2__DOT__dmInst__DOT__lbatchCnt)
                  << " dm2_tileLoad=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__atten__DOT__dm2__DOT__dmInst__DOT__tileLoadCnt)
                  << " dm2_mul=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__atten__DOT__dm2__DOT__dmInst__DOT__mulCnt)
                  << " dm2_head=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__atten__DOT__dm2__DOT__decodeHeadCnt)
                  << " out_rdy=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT___outlinear_io_data_ready)
                  << " ffndown_rdy=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT___ffndown_io_data_ready)
                  << " qkv_st=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__qkvlinear__DOT__state)
                  << " qkv_head=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__qkvlinear__DOT__headCntReg)
                  << " qkv_batch=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__qkvlinear__DOT__batchCntReg)
                  << " qkv_pref=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__qkvlinear__DOT__prefillCntReg)
                  << " qkv_outcnt=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__qkvlinear__DOT__outputCntReg)
                  << " qkv_addr=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__qkvlinear__DOT___lu_inst_io_data_in_addr)
                  << " out_st=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__outlinear__DOT__state)
                  << " out_addr=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__outlinear__DOT___lu_inst_io_data_in_addr)
                  << " ffnup_st=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__ffnup__DOT__cu_inst__DOT__state)
                  << " ffnup_addr=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__ffnup__DOT___lu_inst_io_data_in_addr)
                  << " ffndown_st=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__ffndown__DOT__cu_inst__DOT__state)
                  << " ffndown_addr=" << static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__ffndown__DOT___lu_inst_io_data_in_addr)
                  << std::endl;
      }

      if (debug || wavefront_debug) {
        auto* root = dut.rootp;
        const int cur_state = static_cast<int>(root->opt_acc_core__DOT__state);
        const int cur_layer = static_cast<int>(root->opt_acc_core__DOT__layer_idx);
        const int cur_run_token = static_cast<int>(root->opt_acc_core__DOT__run_token_idx);
        const int cur_result_count = static_cast<int>(dut.cnn0_result_count);
        const int qkv_state = static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__qkvlinear__DOT__state);
        const int out_state = static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__outlinear__DOT__state);
        const int ffnup_state = static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__ffnup__DOT__cu_inst__DOT__state);
        const int ffndown_state = static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__ffndown__DOT__cu_inst__DOT__state);
        const int qkv_addr = static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__qkvlinear__DOT___lu_inst_io_data_in_addr);
        const int out_addr = static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__outlinear__DOT___lu_inst_io_data_in_addr);
        const int ffnup_addr = static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__ffnup__DOT___lu_inst_io_data_in_addr);
        const int ffndown_addr = static_cast<int>(root->opt_acc_core__DOT__u_core__DOT__ffndown__DOT___lu_inst_io_data_in_addr);
        if (cur_state != prev_state ||
            cur_layer != prev_layer ||
            cur_run_token != prev_run_token ||
            cur_result_count != prev_result_count) {
          if (debug) {
            std::cerr << "optacc event"
                      << " cycle=" << cycle
                      << " state=" << cur_state
                      << " layer=" << cur_layer
                      << " run_token=" << cur_run_token
                      << " result_count=" << cur_result_count
                      << " batch_count=" << static_cast<int>(dut.cnn0_batch_count)
                      << " seen=" << seen_count << "/" << output_beats_cfg
                      << std::endl;
          } else if (wavefront_debug &&
                     (cur_state != prev_state || cur_layer != prev_layer)) {
            std::cerr << "optacc state"
                      << " cycle=" << cycle
                      << " state=" << cur_state
                      << " layer=" << cur_layer
                      << " seen=" << seen_count << "/" << output_beats_cfg
                      << std::endl;
          }
          prev_state = cur_state;
          prev_layer = cur_layer;
          prev_run_token = cur_run_token;
          prev_result_count = cur_result_count;
        }

      }
    }

    require(dut.cnn0_result_count == 1, "opt_acc_core did not finish before cycle limit");
    require(seen_count == static_cast<std::size_t>(output_beats_cfg),
            "opt_acc_core finished without writing all output beats");
    std::cout << "opt_acc_core PASS runtime-only layers=12 beats=" << output_beats_cfg << std::endl;
    return 0;
  } catch (const std::exception& ex) {
    std::cerr << ex.what() << std::endl;
    return 1;
  }
}
