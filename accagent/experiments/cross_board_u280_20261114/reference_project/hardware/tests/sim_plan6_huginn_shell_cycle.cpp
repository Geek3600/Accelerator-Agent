#include "Vrtwsr_plan6_huginn_9p_axi.h"
#include "Vrtwsr_plan6_huginn_9p_axi___024root.h"
#include "verilated.h"

#include <array>
#include <cstdint>
#include <cstring>
#include <deque>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>

namespace {

constexpr uint64_t DDR_WEIGHT_BASE = 0x0800000000ULL;
constexpr uint64_t DDR_CORE_WEIGHT_BASE = DDR_WEIGHT_BASE + 0x001000000ULL;
constexpr uint64_t DDR_GAMMA_BASE = 0x0a00000000ULL;
constexpr uint64_t DDR_CORE_GAMMA_BASE = DDR_GAMMA_BASE + 0x00100000ULL;
constexpr uint64_t CORE_CLOCK_HZ = 100000000ULL;
// Official fixed-latency DDR model setting for cycle-count simulations.
constexpr uint64_t DDR_READ_LATENCY = 1;
constexpr uint64_t MAX_SIM_CYCLES = 1000000000ULL;
constexpr uint32_t CONTEXT_TOKENS = 512;

struct Payload {
    std::string name;
    uint64_t base;
    size_t size;
    int fd;
    const uint8_t *data;

    Payload(const std::string &file_name, uint64_t address)
        : name(file_name), base(address), size(0), fd(-1), data(nullptr) {
        const std::filesystem::path path =
            std::filesystem::path("results/plan6/huginn_recurrent_core") / file_name;
        fd = open(path.c_str(), O_RDONLY);
        if (fd < 0)
            throw std::runtime_error("cannot open payload: " + path.string());
        struct stat info {};
        if (fstat(fd, &info) != 0 || info.st_size <= 0)
            throw std::runtime_error("cannot stat payload: " + path.string());
        size = static_cast<size_t>(info.st_size);
        void *mapping = mmap(nullptr, size, PROT_READ, MAP_PRIVATE, fd, 0);
        if (mapping == MAP_FAILED)
            throw std::runtime_error("cannot mmap payload: " + path.string());
        data = static_cast<const uint8_t *>(mapping);
    }

    ~Payload() {
        if (data)
            munmap(const_cast<uint8_t *>(data), size);
        if (fd >= 0)
            close(fd);
    }

    Payload(const Payload &) = delete;
    Payload &operator=(const Payload &) = delete;
};

struct Burst {
    uint64_t address;
    uint64_t ready_cycle;
    uint32_t beats;
    uint32_t beat_index;
};

struct StepResult {
    bool aw_handshake;
    bool w_handshake;
    bool b_valid;
    bool axil_ar_handshake;
    bool r_valid;
    uint32_t r_data;
};

struct CycleBreakdown {
    uint64_t total = 0;
    uint64_t compute = 0;
    uint64_t linear_drain = 0;
    uint64_t attention = 0;
    uint64_t norm = 0;
    uint64_t activation = 0;
    uint64_t rope = 0;
    uint64_t pool_stall = 0;
    uint64_t ddr_dma = 0;
    uint64_t control = 0;
    uint64_t dma_busy = 0;
    uint64_t dma_response_wait = 0;
    uint64_t dma_read_data = 0;
    uint64_t dma_sink_backpressure = 0;
    uint64_t dma_compute_overlap = 0;
    uint64_t dma_pool_stall_overlap = 0;
    uint64_t weight_engine_wait = 0;
    uint64_t nonlinear_attention = 0;
    uint64_t nonlinear_norm = 0;
    uint64_t nonlinear_activation = 0;
    uint64_t nonlinear_rope = 0;
    std::array<uint64_t, 13> shell_states{};
    std::array<uint64_t, 6> prefetch_states{};

    void sample(Vrtwsr_plan6_huginn_9p_axi &dut) {
        const auto *root = dut.rootp;
        const auto shell_state = root->rtwsr_plan6_huginn_9p_axi__DOT__state_q;
        const bool running = shell_state != 0 && shell_state != 11 && shell_state != 12 &&
                             !root->rtwsr_plan6_huginn_9p_axi__DOT__start_pulse_q;
        if (!running)
            return;

        const auto prefetch_state = root->rtwsr_plan6_huginn_9p_axi__DOT__prefetch_state_q;
        const auto linear_state = root->rtwsr_plan6_huginn_9p_axi__DOT__u_recurrent_core__DOT__u_linear_engine__DOT__state_q;
        const bool compute_cycle = root->rtwsr_plan6_huginn_9p_axi__DOT__u_recurrent_core__DOT__u_linear_engine__DOT__execute_valid;
        const bool linear_drain_cycle = linear_state == 2;
        const bool pool_stall_cycle = linear_state == 1 && !compute_cycle;
        const bool attention_active =
            root->rtwsr_plan6_huginn_9p_axi__DOT__u_recurrent_core__DOT__u_attention__DOT__state_q != 0;
        const bool norm_active =
            root->rtwsr_plan6_huginn_9p_axi__DOT__u_recurrent_core__DOT__u_rmsnorm_quant__DOT__state_q != 0;
        const auto ffn_state = root->rtwsr_plan6_huginn_9p_axi__DOT__u_recurrent_core__DOT__g_huginn_ffn_pipeline__DOT__u_ffn_pipeline__DOT__state_q;
        const bool activation_active =
            (ffn_state != 0 && ffn_state != 9) ||
            root->rtwsr_plan6_huginn_9p_axi__DOT__u_recurrent_core__DOT__g_huginn_ffn_pipeline__DOT__u_ffn_pipeline__DOT__u_swiglu__DOT__state_q != 0 ||
            root->rtwsr_plan6_huginn_9p_axi__DOT__u_recurrent_core__DOT__attention_quant_state_q != 0;
        const bool rope_active =
            root->rtwsr_plan6_huginn_9p_axi__DOT__u_recurrent_core__DOT__u_rope_kv_cache__DOT__state_q != 0;
        const bool dma_busy_cycle = root->rtwsr_plan6_huginn_9p_axi__DOT__u_payload_dma__DOT__busy_q;
        const bool blocking_dma_state = shell_state >= 3 && shell_state <= 9;
        const bool weight_engine_wait = shell_state == 2;

        ++total;
        ++shell_states[shell_state];
        ++prefetch_states[prefetch_state];
        if (weight_engine_wait)
            ++this->weight_engine_wait;
        if (compute_cycle)
            ++compute;
        else if (linear_drain_cycle)
            ++linear_drain;
        else if (attention_active)
            ++attention;
        else if (norm_active)
            ++norm;
        else if (activation_active)
            ++activation;
        else if (rope_active)
            ++rope;
        else if (pool_stall_cycle)
            ++pool_stall;
        else if (blocking_dma_state || dma_busy_cycle || weight_engine_wait)
            ++ddr_dma;
        else
            ++control;
        if (dma_busy_cycle) {
            ++dma_busy;
            if (compute_cycle)
                ++dma_compute_overlap;
            if (pool_stall_cycle)
                ++dma_pool_stall_overlap;
        }
        nonlinear_attention += attention_active;
        nonlinear_norm += norm_active;
        nonlinear_activation += activation_active;
        nonlinear_rope += rope_active;
    }

    void sample_dma_bus(Vrtwsr_plan6_huginn_9p_axi &dut) {
        const auto *root = dut.rootp;
        const bool dma_busy_cycle = root->rtwsr_plan6_huginn_9p_axi__DOT__u_payload_dma__DOT__busy_q;
        if (!dma_busy_cycle)
            return;
        if (root->rtwsr_plan6_huginn_9p_axi__DOT__u_payload_dma__DOT__response_pending_q &&
            !dut.m_axi_rvalid)
            ++dma_response_wait;
        if (dut.m_axi_rvalid && dut.m_axi_rready)
            ++dma_read_data;
        if (dut.m_axi_rvalid && !dut.m_axi_rready)
            ++dma_sink_backpressure;
    }
};

class ShellSimulation {
public:
    Vrtwsr_plan6_huginn_9p_axi dut;
    std::array<Payload *, 4> payloads;
    std::deque<Burst> bursts;
    uint64_t cycles = 0;
    uint64_t read_beats = 0;
    uint64_t read_bursts = 0;
    uint64_t read_bytes = 0;
    uint64_t unmapped_reads = 0;
    CycleBreakdown breakdown;

    explicit ShellSimulation(std::array<Payload *, 4> mapped_payloads)
        : payloads(mapped_payloads) {
        dut.s_axi_aclk = 0;
        dut.s_axi_aresetn = 0;
        dut.s_axi_awaddr = 0;
        dut.s_axi_awprot = 0;
        dut.s_axi_awvalid = 0;
        dut.s_axi_wdata = 0;
        dut.s_axi_wstrb = 0xf;
        dut.s_axi_wvalid = 0;
        dut.s_axi_bready = 0;
        dut.s_axi_araddr = 0;
        dut.s_axi_arprot = 0;
        dut.s_axi_arvalid = 0;
        dut.s_axi_rready = 0;
        dut.m_axi_arready = 1;
        dut.m_axi_rid = 0;
        dut.m_axi_rresp = 0;
        dut.m_axi_rlast = 0;
        dut.m_axi_rvalid = 0;
        clear_ddr_data();
    }

    void clear_ddr_data() {
        for (int index = 0; index < 16; ++index)
            dut.m_axi_rdata[index] = 0;
    }

    bool read_payload(uint64_t address, uint32_t words[16]) {
        for (const Payload *payload : payloads) {
            if (address >= payload->base && address + 64 <= payload->base + payload->size) {
                std::memcpy(words, payload->data + (address - payload->base), 64);
                return true;
            }
        }
        std::memset(words, 0, 64);
        return false;
    }

    StepResult step() {
        dut.s_axi_aclk = 0;
        dut.m_axi_rvalid = 0;
        dut.eval();
        breakdown.sample(dut);

        if (dut.m_axi_arvalid && dut.m_axi_arready) {
            bursts.push_back(Burst{dut.m_axi_araddr, cycles + DDR_READ_LATENCY,
                                   static_cast<uint32_t>(dut.m_axi_arlen) + 1, 0});
            ++read_bursts;
        }

        clear_ddr_data();
        dut.m_axi_rlast = 0;
        if (!bursts.empty() && cycles >= bursts.front().ready_cycle) {
            const Burst &burst = bursts.front();
            const uint64_t address = burst.address + uint64_t(burst.beat_index) * 64;
            uint32_t words[16];
            if (!read_payload(address, words))
                ++unmapped_reads;
            for (int index = 0; index < 16; ++index)
                dut.m_axi_rdata[index] = words[index];
            dut.m_axi_rvalid = 1;
            dut.m_axi_rlast = burst.beat_index + 1 == burst.beats;
        }
        breakdown.sample_dma_bus(dut);

        StepResult result{};
        result.aw_handshake = dut.s_axi_awvalid && dut.s_axi_awready;
        result.w_handshake = dut.s_axi_wvalid && dut.s_axi_wready;
        result.b_valid = dut.s_axi_bvalid;
        result.axil_ar_handshake = dut.s_axi_arvalid && dut.s_axi_arready;
        result.r_valid = dut.s_axi_rvalid;
        result.r_data = dut.s_axi_rdata;
        const bool ddr_handshake = dut.m_axi_rvalid && dut.m_axi_rready;

        dut.s_axi_aclk = 1;
        dut.eval();

        if (ddr_handshake) {
            ++read_beats;
            read_bytes += 64;
            if (++bursts.front().beat_index == bursts.front().beats)
                bursts.pop_front();
        }
        ++cycles;
        return result;
    }

    void reset() {
        for (int index = 0; index < 5; ++index)
            step();
        dut.s_axi_aresetn = 1;
        step();
    }

    void write_register(uint32_t address, uint32_t value) {
        dut.s_axi_awaddr = address;
        dut.s_axi_wdata = value;
        dut.s_axi_awvalid = 1;
        dut.s_axi_wvalid = 1;
        bool aw_done = false;
        bool w_done = false;
        for (int timeout = 0; timeout < 100; ++timeout) {
            const StepResult result = step();
            if (result.aw_handshake) {
                dut.s_axi_awvalid = 0;
                aw_done = true;
            }
            if (result.w_handshake) {
                dut.s_axi_wvalid = 0;
                w_done = true;
            }
            if (aw_done && w_done)
                break;
        }
        if (!aw_done || !w_done)
            throw std::runtime_error("AXI-Lite write address/data timeout");
        dut.s_axi_bready = 1;
        bool response_seen = false;
        for (int timeout = 0; timeout < 100; ++timeout) {
            const StepResult result = step();
            if (result.b_valid) {
                response_seen = true;
                break;
            }
        }
        dut.s_axi_bready = 0;
        if (!response_seen)
            throw std::runtime_error("AXI-Lite write response timeout");
    }

    uint32_t read_register(uint32_t address) {
        dut.s_axi_araddr = address;
        dut.s_axi_arvalid = 1;
        dut.s_axi_rready = 0;
        bool address_seen = false;
        for (int timeout = 0; timeout < 100; ++timeout) {
            const StepResult result = step();
            if (result.axil_ar_handshake) {
                address_seen = true;
                break;
            }
        }
        dut.s_axi_arvalid = 0;
        if (!address_seen)
            throw std::runtime_error("AXI-Lite read address timeout");
        dut.s_axi_rready = 1;
        uint32_t value = 0;
        bool response_seen = false;
        for (int timeout = 0; timeout < 100; ++timeout) {
            const StepResult result = step();
            if (result.r_valid) {
                value = result.r_data;
                response_seen = true;
                break;
            }
        }
        dut.s_axi_rready = 0;
        if (!response_seen)
            throw std::runtime_error("AXI-Lite read response timeout");
        return value;
    }
};

}  // namespace

int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    try {
        Payload adapter_weight("adapter.usw512", DDR_WEIGHT_BASE);
        Payload core_weight("weights.usw512", DDR_CORE_WEIGHT_BASE);
        Payload adapter_gamma("adapter_gamma.fp16", DDR_GAMMA_BASE);
        Payload core_gamma("gamma.fp16", DDR_CORE_GAMMA_BASE);
        ShellSimulation sim({&adapter_weight, &core_weight, &adapter_gamma, &core_gamma});

        sim.reset();
        sim.write_register(0x18, CONTEXT_TOKENS);
        sim.write_register(0x00, 1);
        const uint64_t start_cycle = sim.cycles;
        uint64_t next_progress = 1000000ULL;
        uint32_t status = 0;
        for (; sim.cycles - start_cycle < MAX_SIM_CYCLES;) {
            sim.step();
            if (sim.cycles - start_cycle >= next_progress) {
                status = sim.read_register(0x04);
                std::cerr << "progress cycles=" << sim.cycles - start_cycle
                          << " status=0x" << std::hex << status << std::dec
                          << " ddr_bytes=" << sim.read_bytes
                          << " read_bursts=" << sim.read_bursts << std::endl;
                if ((status & 0x5U) != 0)
                    break;
                next_progress += 1000000ULL;
            }
        }

        status = sim.read_register(0x04);
        const uint64_t cycles_low = sim.read_register(0x08);
        const uint64_t cycles_high = sim.read_register(0x0c);
        const uint64_t shell_cycles = (cycles_high << 32) | cycles_low;
        const uint32_t nonzero_chunks = sim.read_register(0x10);
        const uint32_t digest = sim.read_register(0x14);
        const uint32_t context = sim.read_register(0x18);
        const double latency_ms = static_cast<double>(shell_cycles) * 1000.0 /
                                  static_cast<double>(CORE_CLOCK_HZ);

        std::cout << "RESULT model=Huginn-3.5B scope=recurrent_core blocks=4 recurrences=32"
                  << " context_tokens=" << context
                  << " ddr_latency_cycles=" << DDR_READ_LATENCY
                  << " core_clock_hz=" << CORE_CLOCK_HZ
                  << " status=0x" << std::hex << status << std::dec
                  << " shell_cycles=" << shell_cycles
                  << " simulation_cycles=" << sim.cycles - start_cycle
                  << " latency_ms=" << latency_ms
                  << " nonzero_chunks=" << nonzero_chunks
                  << " digest=0x" << std::hex << digest << std::dec
                  << " ddr_read_bytes=" << sim.read_bytes
                  << " ddr_read_bursts=" << sim.read_bursts
                  << " ddr_read_beats=" << sim.read_beats
                  << " unmapped_reads=" << sim.unmapped_reads << std::endl;

        const auto &b = sim.breakdown;
        std::cout << "BREAKDOWN_EXCLUSIVE total=" << b.total
                  << " compute=" << b.compute
                  << " linear_pipeline_drain=" << b.linear_drain
                  << " attention=" << b.attention
                  << " norm=" << b.norm
                  << " activation=" << b.activation
                  << " rope=" << b.rope
                  << " uram_ring_stall=" << b.pool_stall
                  << " ddr_dma=" << b.ddr_dma
                  << " control_wait=" << b.control
                  << " sum=" << b.compute + b.linear_drain + b.attention + b.norm +
                                  b.activation + b.rope + b.pool_stall + b.ddr_dma + b.control
                  << std::endl;
        std::cout << "BREAKDOWN_OVERLAP dma_busy=" << b.dma_busy
                  << " dma_response_wait=" << b.dma_response_wait
                  << " dma_read_data=" << b.dma_read_data
                  << " dma_sink_backpressure=" << b.dma_sink_backpressure
                  << " dma_with_compute=" << b.dma_compute_overlap
                  << " dma_with_pool_stall=" << b.dma_pool_stall_overlap
                  << " weight_engine_wait=" << b.weight_engine_wait
                  << " attention_fsm=" << b.nonlinear_attention
                  << " norm_fsm=" << b.nonlinear_norm
                  << " activation_fsm=" << b.nonlinear_activation
                  << " rope_fsm=" << b.nonlinear_rope
                  << std::endl;
        std::cout << "BREAKDOWN_SHELL_STATES";
        for (size_t i = 0; i < b.shell_states.size(); ++i)
            std::cout << " s" << i << "=" << b.shell_states[i];
        std::cout << std::endl;
        std::cout << "BREAKDOWN_PREFETCH_STATES";
        for (size_t i = 0; i < b.prefetch_states.size(); ++i)
            std::cout << " p" << i << "=" << b.prefetch_states[i];
        std::cout << std::endl;

        if ((status & 0x1U) == 0 || (status & 0x8U) == 0 ||
            nonzero_chunks == 0 || sim.unmapped_reads != 0)
            return 2;
        return 0;
    } catch (const std::exception &error) {
        std::cerr << "SIMULATION_ERROR " << error.what() << std::endl;
        return 1;
    }
}
