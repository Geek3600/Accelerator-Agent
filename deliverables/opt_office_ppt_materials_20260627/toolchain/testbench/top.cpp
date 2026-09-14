#include "VTop.h"
#include "VTop___024root.h"
#include "verilated.h"
#include "verilated_fst_c.h"
#include <iostream>
#include <cstdint>
#include <cstring>

// ============================================================
// Qwen2 加速器 Testbench (完整 12 级流水线)
// 数据模式：简单递增 (1,2,3...) 方便波形调试
// 包含 Attention + FFN 完整 Transformer Block
// ============================================================

static vluint64_t main_time = 0;
static VTop* top;
static VerilatedFstC* tfp;

// ---------- 时钟 ----------
static void tick() {
    top->clock = 1;
    top->eval();
    tfp->dump(main_time++);
    top->clock = 0;
    top->eval();
    tfp->dump(main_time++);
}

// ---------- 复位 ----------
static void do_reset(int cycles = 10) {
    top->reset = 1;
    for (int i = 0; i < cycles; i++) tick();
    top->reset = 0;
    tick();
}

// ---------- 打包 12 x INT8 -> 96-bit (3 x uint32) ----------
static void pack96(uint32_t dst[3], const uint8_t src[12]) {
    dst[0] = (uint32_t)src[0]  | ((uint32_t)src[1]  << 8)
           | ((uint32_t)src[2]  << 16) | ((uint32_t)src[3]  << 24);
    dst[1] = (uint32_t)src[4]  | ((uint32_t)src[5]  << 8)
           | ((uint32_t)src[6]  << 16) | ((uint32_t)src[7]  << 24);
    dst[2] = (uint32_t)src[8]  | ((uint32_t)src[9]  << 8)
           | ((uint32_t)src[10] << 16) | ((uint32_t)src[11] << 24);
}

// ---------- 打包 36 x INT8 -> 288-bit (9 x uint32) ----------
static void pack288(uint32_t dst[9], const uint8_t src[36]) {
    for (int w = 0; w < 9; w++) {
        dst[w] = (uint32_t)src[w*4]   | ((uint32_t)src[w*4+1] << 8)
               | ((uint32_t)src[w*4+2] << 16) | ((uint32_t)src[w*4+3] << 24);
    }
}

// ---------- 输入数据：递增模式 ----------
static void drive_data_in() {
    uint32_t addr = top->io_data_in_addr;
    uint8_t buf[12];
    for (int i = 0; i < 12; i++)
        buf[i] = (uint8_t)((addr * 12 + i + 1) & 0x7F);
    pack96(top->io_data_in, buf);
}

// ---------- QKV 权重：简单递增模式 ----------
static void drive_qkv_w() {
    uint16_t addr = top->io_qkv_w_addr;
    uint8_t buf[36];
    for (int i = 0; i < 36; i++)
        buf[i] = (uint8_t)((addr + i + 1) & 0x7F);
    pack288(top->io_qkv_w_in, buf);
}

// ---------- Softmax mask：全 0（不 mask） ----------
static void drive_sm_w() {
    top->io_sm_w_in = 0;
}

// ---------- OutLinear 权重：简单递增模式 ----------
static void drive_out_w() {
    uint32_t addr = top->io_out_w_addr;
    uint8_t buf[36];
    for (int i = 0; i < 36; i++)
        buf[i] = (uint8_t)((addr + i + 1) & 0x7F);
    pack288(top->io_out_w_in, buf);
}

// ---------- FFNUp 权重：简单递增模式 ----------
static void drive_ffnup_w() {
    uint32_t addr = top->io_ffnup_w_addr;
    uint8_t buf[36];
    for (int i = 0; i < 36; i++)
        buf[i] = (uint8_t)((addr + i + 1) & 0x7F);
    pack288(top->io_ffnup_w_in, buf);
}

// ---------- FFNDown 权重：简单递增模式 ----------
static void drive_ffndown_w() {
    uint32_t addr = top->io_ffndown_w_addr;
    uint8_t buf[36];
    for (int i = 0; i < 36; i++)
        buf[i] = (uint8_t)((addr + i + 1) & 0x7F);
    pack288(top->io_ffndown_w_in, buf);
}

// ---------- 加载 LayerNorm 权重（流式推送） ----------
// 128 周期：前 64 = bias（全 0），后 64 = scale（全 1）
static void load_ln_weights() {
    std::cout << "[TB] 加载 LayerNorm 权重 (128 周期)..." << std::endl;
    for (int cyc = 0; cyc < 128; cyc++) {
        uint8_t buf[12];
        if (cyc < 64) {
            memset(buf, 0, 12);
        } else {
            for (int i = 0; i < 12; i++) buf[i] = 1;
        }
        pack96(top->io_ln_w_in, buf);
        top->io_ln_w_valid = 1;
        tick();
    }
    top->io_ln_w_valid = 0;
    memset(top->io_ln_w_in, 0, sizeof(uint32_t) * 3);
    std::cout << "[TB] LayerNorm 权重加载完成。" << std::endl;
}

// ---------- 加载 LayerNorm2 权重（流式推送） ----------
// 128 周期：前 64 = bias（全 0），后 64 = scale（全 1）
static void load_ln2_weights() {
    std::cout << "[TB] 加载 LayerNorm2 权重 (128 周期)..." << std::endl;
    for (int cyc = 0; cyc < 128; cyc++) {
        uint8_t buf[12];
        if (cyc < 64) {
            memset(buf, 0, 12);
        } else {
            for (int i = 0; i < 12; i++) buf[i] = 1;
        }
        pack96(top->io_ln2_w_in, buf);
        top->io_ln2_w_valid = 1;
        tick();
    }
    top->io_ln2_w_valid = 0;
    memset(top->io_ln2_w_in, 0, sizeof(uint32_t) * 3);
    std::cout << "[TB] LayerNorm2 权重加载完成。" << std::endl;
}

// ---------- 监控输出 ----------
static int res_count = 0;
static void monitor_output() {
    if (top->io_res_valid) {
        uint32_t* r = top->io_res;
        if (top->io_res_st) {
            std::cout << "[TB] === 输出 START ===" << std::endl;
        }
        // 只打印前 5 个和最后 5 个结果
        if (res_count < 5 || top->io_res_last) {
            std::cout << "[TB] res[" << res_count << "] addr="
                      << top->io_res_addr
                      << " data=0x" << std::hex
                      << r[2] << "_" << r[1] << "_" << r[0]
                      << std::dec << std::endl;
        } else if (res_count == 5) {
            std::cout << "[TB] ... (省略中间输出) ..." << std::endl;
        }
        res_count++;
        if (top->io_res_last) {
            std::cout << "[TB] === 输出 LAST (共 " << res_count << " 个) ===" << std::endl;
        }
    }
}

// ---------- 每周期驱动所有地址响应信号 ----------
static void drive_all() {
    drive_data_in();
    drive_qkv_w();
    drive_sm_w();
    drive_out_w();
    drive_ffnup_w();      // 新增：FFNUp 权重
    drive_ffndown_w();    // 新增：FFNDown 权重
}

// ---------- 运行一个阶段 ----------
static void run_phase(const char* name, bool prefill, int seqlen, int max_cycles) {
    std::cout << "\n========================================" << std::endl;
    std::cout << "[TB] 开始 " << name
              << " (prefill=" << prefill
              << ", seqlen=" << seqlen << ")" << std::endl;
    std::cout << "========================================" << std::endl;

    res_count = 0;

    // 步骤1：确保 data_in_ready=0，防止 LNAddrGen 提前启动
    top->io_data_in_ready = 0;
    top->io_res_ready     = 1;
    top->io_layer_st      = 0;

    // 步骤2：发送配置脉冲
    top->io_cfg_prefill = prefill ? 1 : 0;
    top->io_cfg_seqlen  = seqlen - 1;  // 硬件用 seqlen-1
    top->io_cfg_valid   = 1;
    tick();
    top->io_cfg_valid = 0;

    // 步骤3：发送 layer_st 脉冲（触发权重加载）
    top->io_layer_st = 1;
    tick();
    top->io_layer_st = 0;

    // 步骤4：拉高 data_in_ready，保持整个仿真过程
    top->io_data_in_ready = 1;

    // 主仿真循环
    for (int cyc = 0; cyc < max_cycles; cyc++) {
        drive_all();
        tick();

        // 调试：定期打印状态
        if (cyc < 3 || (cyc % 10000 == 0)) {
            auto* r = top->rootp;
            std::cout << "[DBG] cyc=" << cyc
                      << " rv=" << (int)top->io_res_valid
                      << " | QKV fl=" << (int)r->Top__DOT__qkvlinear__DOT__mem_inst__DOT__full_cnt_r
                      << " | OL fl=" << (int)r->Top__DOT__outlinear__DOT__mem_inst__DOT__full_cnt_r
                      << " ov=" << (int)r->Top__DOT___outlinear_io_data_out_valid
                      << " | RA st=" << (int)r->Top__DOT__resadd__DOT__state
                      << " fl=" << (int)r->Top__DOT__resadd__DOT__mem__DOT__full_cnt_r
                      << std::endl;
        }

        monitor_output();

        // 收到最后一个结果后提前退出
        if (top->io_res_valid && top->io_res_last) {
            std::cout << "[TB] " << name << " 在第 " << cyc << " 周期完成" << std::endl;
            for (int f = 0; f < 20; f++) {
                drive_all();
                tick();
                monitor_output();
            }
            return;
        }
    }
    std::cout << "[TB] 警告：" << name << " 在 "
              << max_cycles << " 周期内未完成！" << std::endl;
}

// ============================================================
int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    Verilated::traceEverOn(true);

    top = new VTop;
    tfp = new VerilatedFstC;
    top->trace(tfp, 99);
    tfp->open("wave.fst");

    // 初始化所有输入为 0
    top->io_cfg_valid     = 0;
    top->io_cfg_prefill   = 0;
    top->io_cfg_seqlen    = 0;
    top->io_layer_st      = 0;
    top->io_data_in_ready = 0;
    top->io_ln_w_valid    = 0;
    top->io_ln2_w_valid   = 0;  // 新增：LayerNorm2
    top->io_res_ready     = 0;
    memset(top->io_data_in, 0, sizeof(uint32_t) * 3);
    memset(top->io_ln_w_in, 0, sizeof(uint32_t) * 3);
    memset(top->io_ln2_w_in, 0, sizeof(uint32_t) * 3);  // 新增：LayerNorm2
    memset(top->io_qkv_w_in, 0, sizeof(uint32_t) * 9);
    top->io_sm_w_in = 0;
    memset(top->io_out_w_in, 0, sizeof(uint32_t) * 9);
    memset(top->io_ffnup_w_in, 0, sizeof(uint32_t) * 9);    // 新增：FFNUp
    memset(top->io_ffndown_w_in, 0, sizeof(uint32_t) * 9);  // 新增：FFNDown

    // 复位
    do_reset(10);

    // 加载 LayerNorm 权重
    load_ln_weights();

    // 加载 LayerNorm2 权重（新增）
    load_ln2_weights();

    // 阶段1：Prefill（8 个 token）— 完整 12 级流水线，需要更多周期
    std::cout << "\n[TB] ========================================" << std::endl;
    std::cout << "[TB] 测试完整 Transformer Block (12 级流水线)" << std::endl;
    std::cout << "[TB] Attention (S1-S7) + FFN (S8-S12)" << std::endl;
    std::cout << "[TB] ========================================" << std::endl;
    run_phase("Prefill", true, 8, 2000000);  // 增加周期数以适应更长的流水线

    // 结束
    std::cout << "\n[TB] 仿真结束，时间 " << main_time << std::endl;
    top->final();
    tfp->close();
    delete top;
    return 0;
}
