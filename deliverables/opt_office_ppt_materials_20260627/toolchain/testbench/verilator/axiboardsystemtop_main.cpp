#include "VAxiBoardSystemTop.h"
#include "VAxiBoardSystemTop___024root.h"
#include "common.hpp"
#include <algorithm>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

constexpr int kReadAddrLatency = 10;
constexpr int kWriteRespLatency = 8;
constexpr std::size_t kAxiBeatBytes = 32;

struct ReadBurst {
  int latency = 0;
  uint64_t addr = 0;
  uint8_t beats_total = 0;
  uint8_t beat_idx = 0;
  bool active = false;
};

struct WriteBurst {
  uint64_t addr = 0;
  uint8_t beats_total = 0;
  uint8_t beat_idx = 0;
  bool active = false;
};

struct PendingBResp {
  int latency = 0;
  bool active = false;
};

struct ByteMemory {
  uint64_t base_addr = 0;
  std::vector<uint8_t> bytes;

  std::size_t offset_of(uint64_t addr, std::size_t width) const {
    require(addr >= base_addr, "AXI address below c0 window base");
    const uint64_t off = addr - base_addr;
    require(off + width <= bytes.size(), "AXI address out of range");
    return static_cast<std::size_t>(off);
  }

  void load_64b_lines(const PackedWords& image) {
    require(image.words_per_beat == 16, "expected 64-byte packed DDR image");
    const std::size_t total_bytes = image.words.size() * sizeof(uint32_t);
    require(bytes.size() >= total_bytes, "memory image does not fit allocated c0 window");
    for (std::size_t idx = 0; idx < image.words.size(); ++idx) {
      const auto word = image.words[idx];
      std::memcpy(bytes.data() + idx * sizeof(uint32_t), &word, sizeof(uint32_t));
    }
  }

  void read_axi_beat(uint64_t addr, uint32_t* dst_words) const {
    const std::size_t off = offset_of(addr, kAxiBeatBytes);
    std::memcpy(dst_words, bytes.data() + off, kAxiBeatBytes);
  }

  void write_axi_beat(uint64_t addr, const uint32_t* src_words, uint32_t wstrb) {
    const std::size_t off = offset_of(addr, kAxiBeatBytes);
    for (std::size_t byte_idx = 0; byte_idx < kAxiBeatBytes; ++byte_idx) {
      if ((wstrb >> byte_idx) & 0x1U) {
        const std::size_t word_idx = byte_idx / 4;
        const std::size_t lane_byte = byte_idx % 4;
        bytes[off + byte_idx] = static_cast<uint8_t>((src_words[word_idx] >> (lane_byte * 8)) & 0xffU);
      }
    }
  }
};

void drive_axi_idle(VAxiBoardSystemTop& dut) {
  dut.io_m_axi_arready = 0;
  dut.io_m_axi_rdata[0] = 0;
  dut.io_m_axi_rdata[1] = 0;
  dut.io_m_axi_rdata[2] = 0;
  dut.io_m_axi_rdata[3] = 0;
  dut.io_m_axi_rdata[4] = 0;
  dut.io_m_axi_rdata[5] = 0;
  dut.io_m_axi_rdata[6] = 0;
  dut.io_m_axi_rdata[7] = 0;
  dut.io_m_axi_rresp = 0;
  dut.io_m_axi_rlast = 0;
  dut.io_m_axi_rvalid = 0;
  dut.io_m_axi_awready = 0;
  dut.io_m_axi_wready = 0;
  dut.io_m_axi_bresp = 0;
  dut.io_m_axi_bvalid = 0;
}

bool stall_pattern(int cycle, int period, int low_cycles = 1) {
  return (cycle % period) < low_cycles;
}

}  // namespace

int main(int argc, char** argv) {
  try {
    Verilated::commandArgs(argc, argv);
    require(argc == 2, "usage: VAxiBoardSystemTop <window_dir>");
    const std::filesystem::path window_dir = argv[1];
    const auto cfg = read_cfg(window_dir / "window.cfg");
    const auto ddr_image = read_words(window_dir / "artifacts" / "ddr_image.u32.bin", 16);
    const auto golden = read_words(window_dir / "artifacts" / "golden.u32.bin", 12);
    const bool debug = std::getenv("SYSTEM_DEBUG") != nullptr;

    const uint64_t c0_base = cfg_u64(cfg, "axi_c0_window_base_addr");
    const uint64_t output_base = cfg_u64(cfg, "axi_output_base_addr");
    const uint64_t output_stride = cfg_u64(cfg, "axi_output_stride_bytes");
    const uint64_t memory_size = (output_base - c0_base) + golden.beats() * output_stride + 64;

    ByteMemory mem;
    mem.base_addr = c0_base;
    mem.bytes.resize(static_cast<std::size_t>(memory_size), 0);
    mem.load_64b_lines(ddr_image);

    VAxiBoardSystemTop dut;
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
    dut.io_input_base_addr = cfg_u64(cfg, "axi_input_base_addr");
    dut.io_ln1_w_base_addr = cfg_u64(cfg, "axi_ln1_w_base_addr");
    dut.io_qkv_w_base_addr = cfg_u64(cfg, "axi_qkv_w_base_addr");
    dut.io_qkv_b_base_addr = cfg_u64(cfg, "axi_qkv_b_base_addr");
    dut.io_sm_base_addr = cfg_u64(cfg, "axi_sm_base_addr");
    dut.io_out_w_base_addr = cfg_u64(cfg, "axi_out_w_base_addr");
    dut.io_out_b_base_addr = cfg_u64(cfg, "axi_out_b_base_addr");
    dut.io_ln2_w_base_addr = cfg_u64(cfg, "axi_ln2_w_base_addr");
    dut.io_ffnup_w_base_addr = cfg_u64(cfg, "axi_ffnup_w_base_addr");
    dut.io_ffnup_b_base_addr = cfg_u64(cfg, "axi_ffnup_b_base_addr");
    dut.io_ffndown_w_base_addr = cfg_u64(cfg, "axi_ffndown_w_base_addr");
    dut.io_ffndown_b_base_addr = cfg_u64(cfg, "axi_ffndown_b_base_addr");
    dut.io_output_base_addr = output_base;
    dut.io_output_stride_bytes = static_cast<uint32_t>(output_stride);
    drive_axi_idle(dut);

    reset_dut(dut);
    drive_axi_idle(dut);
    dut.io_start = 1;
    tick(dut);
    dut.io_start = 0;

    ReadBurst read_burst;
    WriteBurst write_burst;
    PendingBResp pending_b;
    std::vector<uint32_t> observed(golden.words.size(), 0);
    std::vector<bool> seen(golden.beats(), false);
    std::size_t seen_count = 0;
    bool saw_st = false;
    bool saw_last = false;

    for (int cycle = 0; cycle < 100000000 && !dut.io_done; ++cycle) {
      if (dut.io_m_axi_arvalid && dut.io_m_axi_arready) {
        require(!read_burst.active, "multiple outstanding AXI read bursts are not supported");
        require(dut.io_m_axi_arburst == 1, "only INCR AXI reads are supported");
        require(dut.io_m_axi_arsize == 5, "expected 32-byte AXI read beats");
        read_burst.active = true;
        read_burst.latency = kReadAddrLatency;
        read_burst.addr = dut.io_m_axi_araddr;
        read_burst.beats_total = static_cast<uint8_t>(dut.io_m_axi_arlen + 1);
        read_burst.beat_idx = 0;
      }

      if (dut.io_m_axi_awvalid && dut.io_m_axi_awready) {
        require(!write_burst.active, "multiple outstanding AXI write bursts are not supported");
        require(dut.io_m_axi_awburst == 1, "only INCR AXI writes are supported");
        require(dut.io_m_axi_awsize == 5, "expected 32-byte AXI write beats");
        write_burst.active = true;
        write_burst.addr = dut.io_m_axi_awaddr;
        write_burst.beats_total = static_cast<uint8_t>(dut.io_m_axi_awlen + 1);
        write_burst.beat_idx = 0;
      }

      if (dut.io_m_axi_wvalid && dut.io_m_axi_wready) {
        require(write_burst.active, "AXI W beat arrived without AW");
        mem.write_axi_beat(
            write_burst.addr + static_cast<uint64_t>(write_burst.beat_idx) * kAxiBeatBytes,
            dut.io_m_axi_wdata,
            dut.io_m_axi_wstrb);
        ++write_burst.beat_idx;
        if (dut.io_m_axi_wlast) {
          require(
              write_burst.beat_idx == write_burst.beats_total,
              "AXI WLAST arrived before all expected beats were written");
          write_burst.active = false;
          pending_b.active = true;
          pending_b.latency = kWriteRespLatency;
        }
      }

      if (dut.io_m_axi_bvalid && dut.io_m_axi_bready) {
        pending_b.active = false;
      }

      if (dut.io_m_axi_rvalid && dut.io_m_axi_rready) {
        require(read_burst.active, "AXI R beat arrived without AR");
        ++read_burst.beat_idx;
        if (dut.io_m_axi_rlast) {
          require(
              read_burst.beat_idx == read_burst.beats_total,
              "AXI RLAST arrived before all expected beats were returned");
          read_burst.active = false;
        }
      }

      drive_axi_idle(dut);

      dut.io_m_axi_arready = stall_pattern(cycle, 9) ? 0 : 1;
      dut.io_m_axi_awready = stall_pattern(cycle, 11) ? 0 : 1;
      dut.io_m_axi_wready = stall_pattern(cycle, 13) ? 0 : 1;

      if (read_burst.active) {
        if (read_burst.latency > 0) {
          --read_burst.latency;
        } else {
          mem.read_axi_beat(
              read_burst.addr + static_cast<uint64_t>(read_burst.beat_idx) * kAxiBeatBytes,
              dut.io_m_axi_rdata);
          dut.io_m_axi_rvalid = 1;
          dut.io_m_axi_rresp = 0;
          dut.io_m_axi_rlast = (read_burst.beat_idx + 1) == read_burst.beats_total;
        }
      }

      if (pending_b.active && pending_b.latency > 0) {
        --pending_b.latency;
      } else if (pending_b.active) {
        dut.io_m_axi_bvalid = 1;
        dut.io_m_axi_bresp = 0;
      }

      tick(dut);

      if (dut.io_res_valid) {
        const std::size_t addr = dut.io_res_addr;
        require(addr < golden.beats(), "AxiBoardSystemTop debug output addr out of range");
        copy_words(observed.data() + addr * 12, dut.io_res, 12);
        if (!seen[addr]) {
          seen[addr] = true;
          ++seen_count;
        }
        saw_st = saw_st || dut.io_res_st;
        saw_last = saw_last || dut.io_res_last;
      }

      if (debug && cycle > 0 && (cycle % 100000) == 0) {
        std::cerr << "AxiBoardSystemTop progress"
                  << " cycle=" << cycle
                  << " state=" << static_cast<int>(dut.rootp->AxiBoardSystemTop__DOT__state)
                  << " token=" << static_cast<int>(dut.rootp->AxiBoardSystemTop__DOT__run_token_idx)
                  << " arvalid=" << static_cast<int>(dut.io_m_axi_arvalid)
                  << " rvalid=" << static_cast<int>(dut.io_m_axi_rvalid)
                  << " awvalid=" << static_cast<int>(dut.io_m_axi_awvalid)
                  << " wvalid=" << static_cast<int>(dut.io_m_axi_wvalid)
                  << " bvalid=" << static_cast<int>(dut.io_m_axi_bvalid)
                  << " seen=" << seen_count << "/" << golden.beats()
                  << std::endl;
      }
    }

    require(!dut.io_error, "AxiBoardSystemTop flagged AXI error");
    require(dut.io_done, "AxiBoardSystemTop did not finish before cycle limit");

    for (std::size_t beat = 0; beat < golden.beats(); ++beat) {
      uint32_t written_words[12] = {0};
      const std::size_t off = mem.offset_of(output_base + beat * output_stride, 12 * sizeof(uint32_t));
      std::memcpy(written_words, mem.bytes.data() + off, 12 * sizeof(uint32_t));
      report_fp32_mismatch("AxiBoardSystemTop-writeback", beat, written_words, golden.beat(beat), 12);
    }

    require(saw_st, "AxiBoardSystemTop never asserted debug io_res_st");
    require(saw_last, "AxiBoardSystemTop never asserted debug io_res_last");
    for (std::size_t beat = 0; beat < golden.beats(); ++beat) {
      report_fp32_mismatch("AxiBoardSystemTop-debug", beat, observed.data() + beat * 12, golden.beat(beat), 12);
    }

    std::cout << "AxiBoardSystemTop PASS beats=" << golden.beats() << std::endl;
    return 0;
  } catch (const std::exception& ex) {
    std::cerr << ex.what() << std::endl;
    return 1;
  }
}
