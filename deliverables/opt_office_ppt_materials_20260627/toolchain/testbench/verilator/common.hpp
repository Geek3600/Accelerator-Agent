#pragma once

#include "verilated.h"
#include <algorithm>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

struct PackedWords {
  std::size_t words_per_beat = 0;
  std::vector<uint32_t> words;

  std::size_t beats() const { return words_per_beat == 0 ? 0 : words.size() / words_per_beat; }
  const uint32_t* beat(std::size_t idx) const { return words.data() + idx * words_per_beat; }
};

inline std::unordered_map<std::string, std::string> read_cfg(const std::filesystem::path& path) {
  std::unordered_map<std::string, std::string> cfg;
  std::ifstream in(path);
  if (!in) {
    throw std::runtime_error("failed to open cfg: " + path.string());
  }
  std::string line;
  while (std::getline(in, line)) {
    if (line.empty()) {
      continue;
    }
    const auto pos = line.find('=');
    if (pos == std::string::npos) {
      continue;
    }
    cfg.emplace(line.substr(0, pos), line.substr(pos + 1));
  }
  return cfg;
}

inline int cfg_int(const std::unordered_map<std::string, std::string>& cfg, const std::string& key) {
  const auto it = cfg.find(key);
  if (it == cfg.end()) {
    throw std::runtime_error("missing cfg key: " + key);
  }
  return std::stoi(it->second);
}

inline uint32_t cfg_u32(const std::unordered_map<std::string, std::string>& cfg, const std::string& key) {
  const auto it = cfg.find(key);
  if (it == cfg.end()) {
    throw std::runtime_error("missing cfg key: " + key);
  }
  return static_cast<uint32_t>(std::stoul(it->second));
}

inline uint64_t cfg_u64(const std::unordered_map<std::string, std::string>& cfg, const std::string& key) {
  const auto it = cfg.find(key);
  if (it == cfg.end()) {
    throw std::runtime_error("missing cfg key: " + key);
  }
  return static_cast<uint64_t>(std::stoull(it->second));
}

inline PackedWords read_words(const std::filesystem::path& path, std::size_t words_per_beat) {
  std::ifstream in(path, std::ios::binary);
  if (!in) {
    throw std::runtime_error("failed to open binary: " + path.string());
  }
  in.seekg(0, std::ios::end);
  const std::streamsize size = in.tellg();
  in.seekg(0, std::ios::beg);
  if (size < 0 || (size % static_cast<std::streamsize>(sizeof(uint32_t))) != 0) {
    throw std::runtime_error("unexpected binary size: " + path.string());
  }
  PackedWords packed;
  packed.words_per_beat = words_per_beat;
  packed.words.resize(static_cast<std::size_t>(size) / sizeof(uint32_t));
  if (!in.read(reinterpret_cast<char*>(packed.words.data()), size)) {
    throw std::runtime_error("failed to read binary: " + path.string());
  }
  if ((packed.words.size() % words_per_beat) != 0) {
    throw std::runtime_error("binary does not align to beat width: " + path.string());
  }
  return packed;
}

inline void copy_words(uint32_t* dst, const uint32_t* src, std::size_t word_count) {
  std::memcpy(dst, src, word_count * sizeof(uint32_t));
}

inline void zero_words(uint32_t* dst, std::size_t word_count) {
  std::memset(dst, 0, word_count * sizeof(uint32_t));
}

inline std::string hex_words(const uint32_t* words, std::size_t word_count) {
  std::ostringstream oss;
  oss << "0x";
  for (std::size_t idx = 0; idx < word_count; ++idx) {
    const auto word = words[word_count - 1 - idx];
    oss << std::hex << std::setw(8) << std::setfill('0') << word;
  }
  return oss.str();
}

inline float u32_to_float(uint32_t bits) {
  float value = 0.0f;
  std::memcpy(&value, &bits, sizeof(value));
  return value;
}

inline std::vector<int> unpack_int8_lanes(const uint32_t* words, std::size_t lanes) {
  std::vector<int> values(lanes, 0);
  for (std::size_t lane = 0; lane < lanes; ++lane) {
    const std::size_t word_idx = lane / 4;
    const std::size_t byte_idx = lane % 4;
    const auto byte_val = static_cast<uint8_t>((words[word_idx] >> (byte_idx * 8)) & 0xffU);
    values[lane] = static_cast<int>(static_cast<int8_t>(byte_val));
  }
  return values;
}

inline std::vector<float> unpack_fp32_lanes(const uint32_t* words, std::size_t lanes) {
  std::vector<float> values(lanes, 0.0f);
  for (std::size_t lane = 0; lane < lanes; ++lane) {
    values[lane] = u32_to_float(words[lane]);
  }
  return values;
}

template <typename Dut>
inline void tick(Dut& dut) {
  dut.clock = 1;
  dut.eval();
  dut.clock = 0;
  dut.eval();
}

template <typename Dut>
inline void reset_dut(Dut& dut, int cycles = 5) {
  dut.reset = 1;
  for (int idx = 0; idx < cycles; ++idx) {
    tick(dut);
  }
  dut.reset = 0;
  tick(dut);
}

inline void require(bool condition, const std::string& message) {
  if (!condition) {
    throw std::runtime_error(message);
  }
}

inline void report_int8_mismatch(
    const std::string& stage,
    std::size_t beat_idx,
    const uint32_t* observed,
    const uint32_t* golden,
    std::size_t word_count,
    std::size_t lanes) {
  const auto obs = unpack_int8_lanes(observed, lanes);
  const auto exp = unpack_int8_lanes(golden, lanes);
  for (std::size_t lane = 0; lane < lanes; ++lane) {
    if (std::abs(obs[lane] - exp[lane]) > 2) {
      std::ostringstream oss;
      oss << stage << " mismatch at beat=" << beat_idx << " lane=" << lane
          << " observed=" << obs[lane] << " expected=" << exp[lane]
          << " observed_words=" << hex_words(observed, word_count)
          << " expected_words=" << hex_words(golden, word_count);
      throw std::runtime_error(oss.str());
    }
  }
}

inline void report_fp32_mismatch(
    const std::string& stage,
    std::size_t beat_idx,
    const uint32_t* observed,
    const uint32_t* golden,
    std::size_t lanes) {
  const auto obs = unpack_fp32_lanes(observed, lanes);
  const auto exp = unpack_fp32_lanes(golden, lanes);
  for (std::size_t lane = 0; lane < lanes; ++lane) {
    if (observed[lane] != golden[lane]) {
      const float abs_err = std::abs(obs[lane] - exp[lane]);
      if (abs_err <= 5.0e-4f) {
        continue;
      }
      std::ostringstream oss;
      oss << stage << " mismatch at beat=" << beat_idx << " lane=" << lane
          << " observed_bits=0x" << std::hex << observed[lane]
          << " expected_bits=0x" << golden[lane]
          << std::dec << " observed=" << obs[lane]
          << " expected=" << exp[lane]
          << " abs_err=" << abs_err;
      throw std::runtime_error(oss.str());
    }
  }
}
