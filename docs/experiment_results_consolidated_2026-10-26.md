# SpatialAccAgent 实验与数据总表

**数据截点：** 2026-10-26 20:53 +0800
**用途：** 论文实验章节的数据底稿。数值保留来源等级；估算、编译证据和综合数据不互相替代。
**范围：** 本项目 `accagent` 中可追溯的 W4A8 加速器设计 campaign、时序优化 history、ACCORD 机制 pilot、旧 campaign 状态及其原始证据索引。历史 OPT-125M 算子 bring-up 记录属于前期工程验证背景，见 `docs/context_2026-03-27.md`，不并入 SpatialAccAgent 论文的受控实验统计。

## 1. 总览

截至数据截点，可从绑定源码的 Vivado timing history 汇总出 5 条硬件设计线、77 条综合时序记录：

| 设计线 | 目标模型 | 上游 LLM | 时序记录数 | 可用结果 |
|---|---|---|---:|---|
| `w4a8_20261018_gpt2` | GPT-2 117M，12 层，hidden 768 | GPT-6.1-Sol | 21 | 有生成核综合 timing/resource；最高 source-calibrated 吞吐候选 890.832 token/s（估算） |
| `w4a8_20261018_qwen2` | Qwen2-0.5B，24 层，hidden 896 | GPT-6.1-Sol | 18 | 有生成核综合 timing/resource；最高 source-calibrated 吞吐候选 254.691 token/s（估算） |
| `w4a8_20261018_llama` | TinyLlama-1.1B，22 层，hidden 2048 | GPT-6.1-Sol | 18 | 有生成核综合 timing/resource；最高 source-calibrated 吞吐候选 78.452 token/s（估算） |
| `gemma3_gpt61_20261020` | Gemma 3 1B IT，26 层，hidden 1152 | GPT-6.1-Sol | 10 | Stage-6 compile-only 与 Stage-7 synthesis scope 有通过记录；最高 source-calibrated 吞吐候选 125.467 token/s（估算） |
| `gpt2_deepseek_v4pro_20261020` | GPT-2 117M，12 层，hidden 768 | DeepSeek-V4-Pro | 10 | Stage-6 compile-only 与 Stage-7 synthesis scope 有通过记录；最高 source-calibrated 吞吐候选 1,306.643 token/s（估算） |

另有一条 GPT-2/Claude Opus 5 run（目录名 `gpt2_claude_fable51_20261020`），截至截点仍未完成 Stage-6，也没有 Stage-7 timing/resource 数据。ACCORD 的正式 E2/E3 计分仍为 0；当前可用的是描述性 pilot 数据，不是原计划的完整重复对照实验。

## 2. 指标与证据口径

- **Fmax**：Vivado post-synthesis/generated-kernel timing 报告推得的频率，不是 post-route 时钟或上板频率。报告资源边界是 `GeneratedAxiDdrTop` / generated top with external ports，排除板卡 app-shell。
- **cycles**：源码 schedule 分析并结合 DSE DDR/refill 假设得到的周期估算。没有一条下表 TPS 使用 RTL 仿真计数器或板上计数器。
- **estimated token/s**：按 `processed_tokens × Fmax(MHz) × 1,000,000 / estimated_cycles` 计算。本批候选为 16 个处理 token；各模型对应其本身的层数与 workload。该吞吐量是“综合 Fmax + 源码校准周期估算”，不是实测端到端吞吐。
- **VCS compile-only pass**：仅证明指定源码闭包通过编译、展开和链接；不等同于 RTL 仿真、全层 DDR 权重消费、无死锁、数值正确或上板运行。
- **source archive**：所有被选出的结果都绑定独立源码归档。最佳 Fmax 与最佳估算吞吐可能来自不同源码，不能将一行的频率与另一行的周期拼接。
- 原始 CSV 中有 `post_synthesis_clock_and_dse_estimated_cycles`（未按当前源码校准）、`post_synthesis_clock_and_source_calibrated_dse_cycles`、`clock_only` 三类记录。最终吞吐只从 source-calibrated 记录中选择；早期未校准 TPS 留在逐轮表中供追溯，不用于最终候选排名。

这些 run 的主要参数均为 W4A8 integer DSP、512-bit DDR refill。`weight_memory=xpm_uram` 表示有界的片上 active/shadow weight-tile cache primitive；完整模型权重仍驻留 DDR，不表示将整个模型权重放入 URAM。资源数是对应综合候选实际报告值。

## 3. 吞吐最佳候选与最佳 Fmax 候选

### 3.1 各线保留的 source-calibrated 吞吐候选

| 设计线 | 源码归档 SHA-256 前缀 | Fmax MHz | cycles（估算） | token/s（估算） | LUT | FF | DSP | BRAM36 | BRAM18 | URAM |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| GPT-2 / GPT-6.1-Sol | `d2fd445acbc8` | 175.223410 | 3,147,140 | 890.832488 | 581,879 | 228,006 | 3,000 | 198 | 12 | 208 |
| Qwen2 / GPT-6.1-Sol | `f7574d9782b4` | 175.192712 | 11,005,830 | 254.690777 | 643,450 | 228,158 | 4,212 | 252 | 30 | 214 |
| TinyLlama / GPT-6.1-Sol | `25c799987415` | 175.346309 | 35,761,434 | 78.451578 | 524,392 | 179,324 | 4,012 | 215 | 14 | 150 |
| Gemma 3 1B / GPT-6.1-Sol | `256a109738f6` | 121.832359 | 15,536,482 | 125.467126 | 946,493 | 253,571 | 4,184 | 294 | 16 | 413 |
| GPT-2 / DeepSeek-V4-Pro | `a609699bd0b0` | 119.976005 | 1,469,121 | 1,306.642596 | 633,939 | 153,964 | 3,230 | 198 | 12 | 208 |

资源顺序为 LUT/FF/DSP/BRAM36/BRAM18/URAM。上述每行均来自单一源码归档；三个 2026-10-18 run 的归档位于 `backend_board/measurements/<sha>/`，两个 2026-10-20 run 同理。

**归档选择注意事项：** TinyLlama 的历史 timing CSV 中，吞吐最高的 source-calibrated 归档是第 17 条 `25c799...`；该 run 根目录最新 `qor_metrics.json` 指向第 18 条 `bc56eb...`，其 172.354361 MHz、38,907,434 cycles、70.877709 token/s 较低。论文若按此前“保留吞吐最佳候选”规则报告 78.451578，应使用第 17 条归档及其报告，不要称它为该 run 最后一次综合结果。GPT-2/DeepSeek 的最高吞吐也不是最高频率候选。

### 3.2 各线最高 Fmax 记录

| 设计线 | measurement index | SHA-256 前缀 | Fmax MHz | 同一归档 cycles / estimated token/s |
|---|---:|---|---:|---|
| GPT-2 / GPT-6.1-Sol | 18 | `56ca26d3548a` | 181.225082 | 3,519,680 / 823.825264 |
| Qwen2 / GPT-6.1-Sol | 18 | `f7574d9782b4` | 175.192712 | 11,005,830 / 254.690777 |
| TinyLlama / GPT-6.1-Sol | 16 | `c62eb4dd96c3` | 179.629962 | clock-only；无周期/吞吐 |
| Gemma 3 1B / GPT-6.1-Sol | 10 | `ae17b1422399` | 155.957580 | 22,432,826 / 111.235262 |
| GPT-2 / DeepSeek-V4-Pro | 10 | `4e31e8da95f9` | 152.835091 | 2,675,744 / 913.899631 |

### 3.3 设计参数快照

以下是各 run 绑定的主要参数，不代表所有模型采用相同硬件规模：

| 设计线 | lanes × array | refill | tile cache | cross-token reuse | activation banks | FIFO depth |
|---|---:|---:|---:|---:|---:|---:|
| GPT-2 / GPT-6.1-Sol | 16 × 16×32 | 512 bit | 256 words × 2 | 8 tokens | 4 | 128 |
| Qwen2 / GPT-6.1-Sol | 16 × 16×32 | 512 bit | 256 words × 2 | 16 tokens | 4 | 64 |
| TinyLlama / GPT-6.1-Sol | 16 × 16×16 | 512 bit | 256 words × 2 | 16 tokens | 2 | 64 |
| Gemma 3 1B / GPT-6.1-Sol | 16 × 16×32 | 512 bit | 256 words × 2 | 16 tokens | 2 | 128 |
| GPT-2 / DeepSeek-V4-Pro | 16 × 16×32 | 512 bit | 256 words × 2 | 8 tokens | 4 | 128 |

## 4. 全部 timing-history 记录

下面逐条转录各 run 的 `history.csv` 核心字段。`DSE 未校准` 行仅保留历史值；`source 校准` 才是与该源码 schedule 重新分析绑定的周期/TPS；`clock-only` 没有 cycles/TPS。SHA 仅显示 12 位前缀，完整值在同表所链接的 CSV。

### 4.1 GPT-2 / GPT-6.1-Sol

原始记录：[history.csv](../accagent/runs/w4a8_20261018_gpt2/backend_board/timing_history/history.csv)

| i | Fmax MHz | cycles | token/s | 周期口径 | source SHA 前缀 |
|---:|---:|---:|---:|---|---|
| 1 | 16.944 | 1,588,268 | 170.691 | DSE 未校准；归档缺失 | `ffeeb1e35991` |
| 2 | 27.376 | 1,588,268 | 275.785 | DSE 未校准 | `633c17cd8dbc` |
| 3 | 45.339 | 1,588,268 | 456.740 | DSE 未校准 | `4cbef46dd5ac` |
| 4 | 16.944 | 1,588,268 | 170.691 | DSE 未校准 | `10ddeb70a337` |
| 5 | 27.376 | 1,588,268 | 275.785 | DSE 未校准 | `1a87b634aa6f` |
| 6 | 47.172 | 1,588,268 | 475.205 | DSE 未校准 | `25e0190a661b` |
| 7 | 82.878 | 1,588,268 | 834.897 | DSE 未校准 | `1a767e43e900` |
| 8 | 121.080 | 1,588,268 | 1,219.744 | DSE 未校准 | `d7283cfbc747` |
| 9 | 62.112 | 2,550,680 | 389.617 | source 校准 | `9fcc353d0f39` |
| 10 | 109.445 | 2,552,984 | 685.912 | source 校准 | `a59e497a505d` |
| 11 | 116.700 | 2,553,392 | 731.261 | source 校准 | `6ca129e967f9` |
| 12 | 119.976 | - | - | clock-only | `9aeb8684f2c3` |
| 13 | 128.849 | 3,101,828 | 664.637 | source 校准 | `9ba8793fd808` |
| 14 | 152.835 | 3,157,544 | 774.450 | source 校准 | `10ab7449451f` |
| 15 | 157.159 | 3,157,592 | 796.346 | source 校准 | `1f41b548ecbc` |
| 16 | 158.128 | 3,157,592 | 801.258 | source 校准 | `47e0ab2aee30` |
| 17 | 153.988 | - | - | clock-only | `8454acf2e34d` |
| 18 | 181.225 | 3,519,680 | 823.825 | source 校准 | `56ca26d3548a` |
| 19 | 174.672 | 7,750,880 | 360.573 | source 校准 | `473dcdd6eb4e` |
| 20 | 175.623 | 4,949,612 | 567.716 | source 校准 | `293a374cb960` |
| 21 | 175.223 | 3,147,140 | 890.832 | source 校准 | `d2fd445acbc8` |

第 8 条未校准周期模型给出的 1,219.744 token/s 不能作为该 campaign 的最佳吞吐结论；源码变化后周期模型已更新。按 source-calibrated 数据，最高是第 21 条 890.832 token/s。

### 4.2 Qwen2 / GPT-6.1-Sol

原始记录：[history.csv](../accagent/runs/w4a8_20261018_qwen2/backend_board/timing_history/history.csv)

| i | Fmax MHz | cycles | token/s | 周期口径 | source SHA 前缀 |
|---:|---:|---:|---:|---|---|
| 1 | 16.996 | 5,976,733 | 45.500 | DSE 未校准；归档缺失 | `d80583b33f6b` |
| 2 | 27.387 | 5,976,733 | 73.316 | DSE 未校准 | `0b81ad1c72fd` |
| 3 | 48.931 | 5,976,733 | 130.990 | DSE 未校准 | `2a01846fc8b1` |
| 4 | 61.508 | 5,976,733 | 164.660 | DSE 未校准 | `6425d57066c6` |
| 5 | 82.754 | 5,976,733 | 221.537 | DSE 未校准 | `f5e5890cb512` |
| 6 | 120.005 | - | - | clock-only | `04d444b1556c` |
| 7 | 144.865 | 13,876,974 | 167.027 | source 校准 | `42406be2a29c` |
| 8 | 145.138 | 12,258,054 | 189.443 | source 校准 | `a16d9d729f6d` |
| 9 | 152.672 | 14,068,518 | 173.632 | source 校准 | `c16a54abe167` |
| 10 | 157.629 | 14,003,694 | 180.100 | source 校准 | `7d8965ed0179` |
| 11 | 145.751 | 14,003,694 | 166.529 | source 校准 | `de4a20af5320` |
| 12 | 148.346 | 12,219,990 | 194.234 | source 校准 | `f1ae5aad84de` |
| 13 | 162.522 | 13,820,886 | 188.147 | source 校准 | `a273ad100496` |
| 14 | 163.586 | 13,820,886 | 189.378 | source 校准 | `956a88f95ed5` |
| 15 | 164.718 | 15,197,142 | 173.419 | source 校准 | `13ab8741ffd5` |
| 16 | 152.439 | 15,199,326 | 160.469 | source 校准 | `f44d9755021c` |
| 17 | 172.058 | 11,005,782 | 250.134 | source 校准 | `89ed85123efa` |
| 18 | 175.193 | 11,005,830 | 254.691 | source 校准 | `f7574d9782b4` |

### 4.3 TinyLlama / GPT-6.1-Sol

原始记录：[history.csv](../accagent/runs/w4a8_20261018_llama/backend_board/timing_history/history.csv)

| i | Fmax MHz | cycles | token/s | 周期口径 | source SHA 前缀 |
|---:|---:|---:|---:|---|---|
| 1 | 17.187 | 20,400,418 | 13.480 | DSE 未校准 | `d9d7cbbce19f` |
| 2 | 17.187 | 20,400,418 | 13.480 | DSE 未校准 | `03913f100d33` |
| 3 | 17.187 | 20,400,418 | 13.480 | DSE 未校准 | `f3f30324416b` |
| 4 | 27.376 | 20,400,418 | 21.471 | DSE 未校准 | `43128761dd0e` |
| 5 | 49.456 | 20,400,418 | 38.788 | DSE 未校准 | `bf87ee4f06a2` |
| 6 | 53.660 | 35,144,026 | 24.430 | source 校准 | `fffa10c55279` |
| 7 | 121.832 | 35,616,564 | 54.731 | source 校准 | `bff2f4759b06` |
| 8 | 157.580 | 38,090,354 | 66.192 | source 校准 | `66441d7ec56e` |
| 9 | 163.586 | 38,168,080 | 68.575 | source 校准 | `4a71062dceeb` |
| 10 | 170.999 | 38,556,116 | 70.961 | source 校准 | `987df9987fa6` |
| 11 | 161.264 | 38,663,278 | 66.736 | source 校准 | `d30141efbca1` |
| 12 | 165.235 | 38,663,278 | 68.379 | source 校准 | `628aa9c85e43` |
| 13 | 174.004 | 38,843,304 | 71.674 | source 校准 | `bc0b791f2b83` |
| 14 | 174.064 | 39,223,354 | 71.004 | source 校准 | `5d297e06c785` |
| 15 | 175.223 | 35,915,104 | 78.061 | source 校准 | `61ab06cbb50f` |
| 16 | 179.630 | - | - | clock-only | `c62eb4dd96c3` |
| 17 | 175.346 | 35,761,434 | 78.452 | source 校准 | `25c799987415` |
| 18 | 172.354 | 38,907,434 | 70.878 | source 校准 | `bc56eb368126` |

### 4.4 Gemma 3 1B / GPT-6.1-Sol

原始记录：[history.csv](../accagent/runs/gemma3_gpt61_20261020/backend_board/timing_history/history.csv)

| i | Fmax MHz | cycles | token/s | 周期口径 | source SHA 前缀 |
|---:|---:|---:|---:|---|---|
| 1 | 17.247 | 11,651,872 | 23.683 | DSE 未校准 | `2d2b1c73add3` |
| 2 | 27.397 | - | - | clock-only | `7cb14feff16d` |
| 3 | 27.380 | 15,407,028 | 28.434 | source 校准 | `947edac81e85` |
| 4 | 47.755 | 15,330,042 | 49.843 | source 校准 | `1a655adf9f7d` |
| 5 | 47.755 | 15,125,682 | 50.516 | source 校准 | `acf40f02611d` |
| 6 | 118.765 | 15,330,042 | 123.955 | source 校准 | `435eb9c2d740` |
| 7 | 121.832 | 15,536,482 | 125.467 | source 校准 | `256a109738f6` |
| 8 | 141.084 | 22,309,612 | 101.182 | source 校准 | `651f08266f87` |
| 9 | 149.120 | 19,538,376 | 122.115 | source 校准 | `32c10bf4b4e8` |
| 10 | 155.958 | 22,432,826 | 111.235 | source 校准 | `ae17b1422399` |

### 4.5 GPT-2 / DeepSeek-V4-Pro

原始记录：[history.csv](../accagent/runs/gpt2_deepseek_v4pro_20261020/backend_board/timing_history/history.csv)

| i | Fmax MHz | cycles | token/s | 周期口径 | source SHA 前缀 |
|---:|---:|---:|---:|---|---|
| 1 | 16.944 | 1,588,268 | 170.691 | DSE 未校准 | `a7d9cd3b9ef5` |
| 2 | 27.376 | 2,171,396 | 201.723 | source 校准 | `c73acfd9a2a9` |
| 3 | 47.219 | 2,570,252 | 293.940 | source 校准 | `882cc1dcbaac` |
| 4 | 52.521 | 2,588,684 | 324.619 | source 校准 | `c77258dc3089` |
| 5 | 95.383 | 2,588,684 | 589.541 | source 校准 | `a0624585612d` |
| 6 | 109.445 | 1,743,332 | 1,004.468 | source 校准 | `78a3d2b6f44e` |
| 7 | 115.794 | 1,743,380 | 1,062.711 | source 校准 | `b8ef325b29e9` |
| 8 | 119.976 | 1,469,121 | 1,306.643 | source 校准 | `a609699bd0b0` |
| 9 | 128.386 | 2,660,192 | 772.192 | source 校准 | `bf68c674770f` |
| 10 | 152.835 | 2,675,744 | 913.900 | source 校准 | `4e31e8da95f9` |

## 5. ACCORD 机制实验与 compile-only pilots

完整实验计划及逐次 checkpoint 见 [`plan.md`](plan.md)；当前 pilot 的文件级结果汇总见 [`accord_experiment_results_compile_only_2026-10-26.md`](accord_experiment_results_compile_only_2026-10-26.md)。本节合并其主要数据，避免将同一实验在多份进展记录里重复计数。

### 5.1 E2：跨阶段参数修订

三项 GPT-2 W4A8 revision 均从配对 checkpoint 启动，分别运行 ACCORD 与 B0：

| revision | 修改 | ACCORD/B0 观察 | 实际工具证据 |
|---|---|---|---|
| cache tile | `cache_tile_words: 256 -> 512` | 两组均绑定 512；Stage-4 参数检查各 6/6 pass；Stage-5 Chisel compile/elaboration 各 6/6 命令 pass；134 个生成源文件 SHA 一致 | 无 VCS；无 Vivado/QoR |
| activation banks | `activation_banks: 4 -> 2` | 两组均绑定 2；Stage-4 各 6/6；Stage-5 各 6/6 命令 pass；121 个生成源文件 SHA 一致 | 无 VCS；无 Vivado/QoR |
| cross-token reuse | `cross_token_reuse_tokens: 8 -> 4` | 两组均绑定 4；Stage-4 各 6/6；Stage-5 各 6/6 命令 pass | 两组 exact-board VCS compile/elaboration/link compile-only pass，2/2；未仿真 |

共同配置包括 lanes=8、8×8 array、512-bit refill、W4A8 integer DSP。ACCORD 与 B0 在这三项案例中的参数选择及已检查产物相同。结论限于“该参数修改在当前 pilot 中跨阶段物化并通过对应编译检查”；目前没有 ACCORD 的准确率/QoR/性能优势证据。

补充的 lanes=8 Stage-4/5 配对 pilot：

| case | ACCORD / B0 检查 | Stage-5 Chisel 编译耗时 | VCS 与 QoR |
|---|---|---:|---|
| `dcg_lanes8_case_20261023T193854+0800` | 两侧参数 6/6、编译/展开 6/6；均选 lanes=8、array=8×8 | 136.781 s / 134.382 s | 未运行；无 QoR |
| `dcg_lanes8_inferred_20261023T2115+0800` | 两侧参数 6/6、编译/展开 6/6；均选同一候选 `arch_7ad3a71d15fd` | 161.203 s / 156.440 s | 未运行；无 QoR |

补充 case 仅作历史流程 pilot，不作为 E2 的独立正式重复。`dcg_lanes8_20261023T1926/` 的 VCS 输入 fingerprint 和 compile-log SHA 在 ACCORD/B0 相同且都指向旧 GPT-2 run，252 个合法候选的 DSE measurements 为 0；该目录不增加独立 VCS 或 QoR 样本。

### 5.2 Evidence Binding：证据失效与复用

在冻结 GPT-2 baseline 上运行四项确定性 mutation：

| mutation | 预期失效范围 | 结果 |
|---|---|---|
| RTL 行为变更 | functional 与 backend evidence 失效 | pass |
| XDC clock period 变更 | 仅 backend evidence 失效 | pass |
| 模型参数变更 | functional 与 backend evidence 失效 | pass |
| 与构建无关的文档变更 | 硬件 evidence 保留复用 | pass |

结果：4/4 pass、stale-evidence acceptance=0、false invalidation=0。这是框架确定性逻辑检查，没有 Agent/VCS/Vivado 执行，不应和硬件 QoR 样本合并。

### 5.3 E3：Gemma compile-time repair pilot

同一 Gemma compute-slot 编译故障由真实远端 VCS 触发：`write_busy`、`rstate`、`read_kind` 的声明晚于首次引用，报告 `Error-[IND] Identifier not declared`。Agent 将声明移至首次引用之前并移除重复声明；局部改动在 run-local `compute_slot.sv`。第一次 patch action 因对已有 weight-binding manifest 请求 `create` 被拒，未写入；随后改为 `replace`，源码 patch 才应用。

- 修复前源码 SHA-256：`2498988b15a09e7ea3a5342b9c088b754b8122f766969596f4cfa60af99a2648`
- 修复后源码 SHA-256：`6d2d3192a7628bde1956c5e39bb0076f4503cd9921e1df82872b2c5110fe12c0`
- 修复后 VCS：compile/elaboration/link return code 0，33 modules；CPU 时间 67.761/1.630/0.403 s；simulation=`not_run`。

这是一次直接编译器诊断驱动的 Agent compile fail-to-pass 案例。该 B2 profile 没有非空、hash-bound 的 CCTG causal slice，所以只能叫 compile-time repair pilot，不能说成 CCTG 图引导根因定位收益。

### 5.4 Gemma Stage-6 compile-only gate 与参考输入

`e3_gemma_exact_runtime_20261026/run/` 的一次 Stage-6 gate evaluation 使用明确 `vcs_compile_only` policy：远端 VCS 编译、展开、链接 return code 0；约 108.313 s wall time，VCS compile/elaboration/link CPU 时间 72.041/1.610/0.431 s。输入 manifest 含 51 个 source IDs，VCS 报告编译 34 个 modules，top=`sacg_board_compile_tb`，mode=`compute_slot_axi`。Operator-leaf、single-layer 与 board AXI compile-only promotion 证据在该次 gate report 中标为 pass。

该 run 的模型参考捕获包含 26 层、338 个 tensor catalog 项、42 个 module records 和 16-token 随机输入/参考输出 shape `[1,16,1152]`。它们是参考模型及输入材料，不代表 DUT 消费权重。VCS compile report 显示 `compiled_sample_source_ids=0`、`artifacts={}`；没有完整 DDR runtime、非零 DDR 事件、仿真数值比较、无死锁证据或板上运行。

21:01 +0800 对该门禁产物再次核验：`verification_result.json`、`debug_loop_report.json` 与 board promotion certificate 均为 pass；本次 compile-only gate 使用 51 个 source IDs，真实远端 VCS 编译 34 个模块，compile 返回码 0，compile/elaboration/link CPU 时间为 72.041/1.610/0.431 s。VCS log SHA-256=`1aaf7583c1846f5c49172401ff3933c33b381528acb9691383e188f0084952bb`，输入 fingerprint=`cef34ae9169b3c402c6cc37fcf2f244ed41fa2dd4533237d3907d736934cd686`，board source identity SHA-256=`c8593caa82f9814f18be0f7dc5a4fca139920d9fa32566fe95ebb2d63f7f6a65`。`simulation_skipped=true` 且 `exact_board_acceptance_passed=false`；这是 exact-board 编译、展开、链接闭合，不是 runtime/DDR 权重消费或数值正确证据，也不增加新的 repair episode。

## 6. 其他 campaign 与排除项

| campaign | 观察到的产物/状态 | 在本文中的处理 |
|---|---|---|
| `gpt2_claude_fable51_20261020` | run metadata 的上游模型为 `claude-opus-5`；Stage-6 board/multilayer harness closure 未通过，Stage-7 未开始；没有 QoR | 作为未完成的上游模型泛化臂报告，不填充硬件性能数据；目录名中的 `fable51` 是历史名称 |
| `formal_20260922_r432_qwen2`、`formal_20260922_r434_gpt2`、`formal_20260922_r434_llama` | 旧流程/旧阶段运行报告仍为 running，backend Stage-7 incomplete；没有可用于本文的最终 source-bound QoR 汇总 | 作为历史/被后续 W4A8 campaign 替代的记录，不并入最终硬件表或 ACCORD 统计 |
| `wide512_20261018_gpt2/qwen2/llama` | 没有可核实的 timing history 与最终 QoR；Qwen2 参数绑定经历失败后仍停在旧 run 流程 | 不计作宽带宽硬件结果。本文可报告的 512-bit 数据来自后续 W4A8 campaign，而非该未完成试跑 |
| 2026-10-18 GPT-2/Qwen2/TinyLlama Stage-6/7 repair iterations | 有多轮 compile-only 与 Vivado source-bound timing history；根报告尚保留 `running`/backend `incomplete` 状态，未完成 RTL runtime、P&R 或 bitstream | 使用每条 source archive 的真实综合/估算记录；不把 run-level incomplete 改写为全流程成功 |
| 早期 OPT-125M FP32/FP16 operator 与 seq=26/912 pipeline bring-up | 保存在项目上下文文档前部的功能调试轨迹，与后续 W4A8 agent runs 使用不同 RTL/数值架构和验证目标 | 仅作为前期工程背景，不混进 SpatialAccAgent 的 W4A8 结果或机制对照分母 |
| ACCORD 早期无效/重复目录 | 包括 cache/reuse 首版输入、`dcg_cross_token_reuse_revision_20261024T132813+0800` 错误限制、重复绑定 lanes8 VCS | 按 manifest、输入 fingerprint 与 source identity 排除；不是独立实验样本 |

### 6.1 自动化/框架回归测试（非论文硬件实验）

已记录的定向测试包括：`test_accord_experiment_profile.py` 5/5、`test_verification_evidence_contract.py` 26/26、`test_debug_loop_resume.py` 27/27、Gemma reference regeneration 5/5、`tests.test_stage_agent` 34/34、`tests.test_repair_execution_feedback` 30/30。另一次 `tests.test_repair_patch_execution` 共 46 项中 44 项通过、2 项 board-manifest fixture 用例失败（fixture 缺 board source identity/tool profile）。这些是框架回归测试，不构成 agent 硬件设计成功率或 QoR 数据；不能写成全仓测试全部通过。

## 7. 论文结果的可支持表述

1. 对 2026-10-18 的 GPT-2、Qwen2、TinyLlama 三条 W4A8 campaign，已有多轮 Vivado post-synthesis Fmax 记录；source-calibrated 吞吐候选分别为 890.832、254.691、78.452 token/s。三者均是解析周期估算与综合频率换算值，不是 RTL/板上实测。
2. Gemma/GPT-6.1-Sol 与 GPT-2/DeepSeek 两条 run 各有10条 source-bound synthesis history。最佳吞吐候选分别为125.467 token/s @ 121.832 MHz（15,536,482 cycles）和1,306.643 token/s @ 119.976 MHz（1,469,121 cycles）；两者都来自不同于最高时钟点的源码归档。对应最高时钟点分别为155.958 MHz / 111.235 token/s（22,432,826 cycles）和152.835 MHz / 913.900 token/s（2,675,744 cycles），因此两条线均曾达到150 MHz以上。频率和吞吐结果都是 source-bound post-synthesis / source-calibrated estimates；Gemma为26层、DeepSeek目标为12层，不能据原始 token/s 直接比较模型效率。
3. 原 GPT-2 W4A8 timing history 的最高 Fmax 为181.225 MHz，而 source-calibrated best-throughput 候选为175.223 MHz / 890.832 token/s。最大频率和最高估算吞吐不是同一个点；各条线论文表应分别报告 best-clock 与 best-throughput 候选，不得拼接不同 source SHA 的频率、周期、资源。
4. ACCORD/B0 在 3 项主要参数修订和 2 项补充 lanes=8 pilot 中观察到相同参数结果与编译通过；当前材料支持跨阶段物化 pilot，不支持 DCG 优于 B0。
5. Evidence Binding 的 4/4 deterministic mutation 检查支持其 evidence invalidation/reuse 逻辑在这些测试输入上的行为。
6. Gemma compile repair 可作为一次真实编译器错误到局部修改再到 VCS compile-only pass 的案例；没有有效 CCTG causal slice，不能把它包装成 graph-guided diagnosis 的直接证据。

不应声称：全层 RTL 仿真已通过、完整 DDR 权重已被 DUT 消费、三线已上板、token/s 为实测、时序达到 post-route 闭合、ACCORD 获得统计显著优势、DSE 找到全局最优、Claude 上游臂完成，或正式 E2/E3 扩展评分已经完成。现有 source-bound Vivado Fmax/resource 报告也不包含 P&R、bitstream、板上功耗或板上计数器证据。

## 8. 原始证据索引

- 方法、架构、Stage 描述和 Gemma/DeepSeek 两条优化曲线：[`agent_framework_design.md`](agent_framework_design.md)，第 20 节。
- ACCORD 计划和逐次执行检查点：[`plan.md`](plan.md)。
- E2/Evidence Binding/E3 compile-only pilot 报告：[`accord_experiment_results_compile_only_2026-10-26.md`](accord_experiment_results_compile_only_2026-10-26.md)。
- 三条早期 W4A8 设计线：`accagent/runs/w4a8_20261018_{gpt2,qwen2,llama}/backend_board/timing_history/history.csv` 与相应 `backend_board/measurements/<source_sha>/`。
- 新增模型/上游 LLM 两条设计线：`accagent/runs/gemma3_gpt61_20261020/backend_board/timing_history/history.csv`、`accagent/runs/gpt2_deepseek_v4pro_20261020/backend_board/timing_history/history.csv`。
- 当前 hardware snapshots：各 W4A8/Gemma/DeepSeek run 的 `backend_board/qor/qor_metrics.json`、`backend_board/backend_board_report.json` 和绑定的 `parameter_binding/selected_architecture.json`。
- Evidence Binding：`accagent/experiments/accord/results/evidence_binding_20261026_compile_policy/summary.json`。
- Gemma fail-to-pass 与 compile-only gate：`accagent/experiments/accord/results/cctg_b2_prompt_clean_20261024T1105+0800/`、`accagent/experiments/accord/results/e3_gemma_exact_runtime_20261026/run/`。
- 详细历史交互和 OPT-125M bring-up：[`context_2026-03-27.md`](context_2026-03-27.md)。

撰写图表时，建议将表 3.1 作为“source-calibrated estimated performance”表，将逐轮 Fmax 单独画线；资源取对应 best-throughput SHA 的 QoR 文件。若展示 best-clock 点，则另列其周期/TPS，不能将两个归档拼成一个候选。


## GPT-2 Medium 重跑进度（2026-10-27 00:11 更新）

当前所有 GPT-2 新实验统一使用 Medium：24层、hidden1024、16 heads、MLP4096、batch1/seq16、W4A8/I32、VU9P；下文既有12层GPT-2数据为Small历史，不能作为Medium结果。当前Medium没有Vivado Fmax、资源或吞吐值。

| 实验线 | 已完成 | 当前运行 / 仍缺少 |
| --- | --- | --- |
| Medium / GPT-6.1-Sol | Stage-1至5；Stage-6连接单层VCS compile-only闭环 | exact-board selector 29/29；源码排他审查7/7块、119/119 segments；domain agent的AXI contract有三项确定性校验错误，正在同阶段修复；完整AXI/DDR编译和综合未完成 |
| Medium / DeepSeek-V4-Pro | Stage-1至5；Stage-6 operator-leaf及连接单层compile-only闭环 | exact-board selector map 18/29；尚无Medium Vivado QoR |
| Medium / Claude Opus 5 | Stage-1至5；Stage-6 operator leaf 8/8与连接单层VCS compile-only闭环 | 29/29 map chunk已完成，但最终selector收到HTTP 400；已移除请求schema中407项动态source-ID枚举，当前同run重试仍未重跑selector；完整AXI/DDR编译和综合未完成 |
| Medium / ACCORD-B0机制配对 | activation-banks、lanes-explicit、lanes-inferred、cross-token-reuse双方Stage-4/5均通过；每侧6条Chisel工具命令返回0 | cache-tile缺合法alternative而跳过；没有VCS或QoR对比 |
| Medium / Stream-HLS | 全24层FP32 native lowering、C++导出、远端syntax compile返回0；共享W4A8 payload已通过校验 | 正在构造native integer graph；板级接口、HLS/Vivado综合和可比QoR仍缺 |
| Medium / Allo | 有界环境审计完成；共享W4A8 payload已通过校验 | 匹配的pinned LLVM/MLIR后端仍不可用，无编译或QoR |

lanes-explicit配对两侧同选合法的`arch_f37280b242a9`（8 lanes、8x32、FIFO128），Chisel工具耗时ACCORD为131.308秒、B0为134.557秒；这是单对工具耗时，不能当作端到端耗时或机制优势。lanes-inferred和cross-token-reuse也已完成Stage-4/5配对，但同样没有QoR。cache-tile不沿用Small的256->512：当前Medium合法域仅256，因而没有可计分revision。

验证口径统一为`vcs_compile_only`。连接单层编译通过不等于完整AXI/DDR编译、仿真、运行周期或上板正确；所有新性能结果等待当前源码对应的工具证据。可恢复运行状态见`accagent/experiments/gpt2_medium_20261026/monitor_status.json`。

截至00:11，三条run的前置阶段均未回退，完整AXI/DDR VCS compile-only closure均未完成，Medium Fmax、资源和吞吐仍为空。Stream-HLS量化/板级适配及Allo工具链尚未形成可比较QoR；FP32 syntax compile不计作W4A8硬件结果。

编译器对照的共同校准输入、288个模块边界activation ranges和checkpoint-bound W4A8/I32/Q7 payload均已物化并通过payload validator。64个seq16样本来自固定WikiText-2 raw-v1和Medium tokenizer。当前`activation_ranges.json` SHA-256=`0e0733d561ada571dfe8ba1359150b81d65c03be2b28ab25f3c7ba83e88bccd6`；payload manifest SHA-256=`85adf0f4ab1e8b65d2fcdad29c2025b9dfe11696864af3fae27dcd944ef60375`。validator逐项确认301,989,888个矩阵权重码、221,184个bias码、98,304个LayerNorm码和221,184个Q31 scale；矩阵权重和bias无饱和，LayerNorm有30个饱和向量。Stream-HLS native integer lowering尚未完成，Allo尚无匹配工具链；当前仍无可比较W4A8综合结果。

本轮框架修复删除了最终exact-board selector schema中按407个source ID展开的动态`enum`。输出仍由同一run的sample catalog、progressive evidence和replacement-boundary checker做严格后验验证；board-discovery定向测试28/28通过。该改动尚未被Claude正在运行的旧进程消费，Claude需要在当前Stage-6内从已有map checkpoint恢复selector调用。所有三条Medium设计线仍无source-bound Vivado QoR；当前数值不能作为Fmax或token/s论文结果。

## GPT-2 Medium 最新状态（2026-10-27 01:03）

三条新线的共享目标仍是 GPT-2 Medium 24层、W4A8/I32、VU9P、`vcs_compile_only`，150 MHz 为综合频率目标。当前没有已完成的Medium Fmax、资源或吞吐结果。

| 实验线 | 当前进度 | 尚缺少 |
| --- | --- | --- |
| GPT-6.1-Sol | 完整 exact-board AXI/DDR VCS compile/elaboration/link 返回码0；Stage-6晋级证书通过；Stage-7远端Vivado仍运行，日志已到Timing Optimization | synthesis报告、Fmax、最终资源、DSE周期校准及吞吐量 |
| DeepSeek-V4-Pro | Stage-6单层compile-only pass；selector map checkpoint 29/29通过，source-map review 000正在原worker中运行 | source-map review完成、board VCS、Stage-7综合与时序优化 |
| Claude Opus 5 | leaf和single-layer compile-only pass；board identity与29/29 source map已完成 | multi-layer harness缺失；最新644,708字节generation请求再次HTTP 400 `invalid_request`。根因未证实；board VCS与综合均未完成 |

GPT-6.1的VCS修复先将 `tile_request_ready` 声明为过程赋值可用的 `logic`，并修正MLP down权重route offset。Stage-7 adapter generator之后发现direct adapter没有实例化当前生成top；run-local repair已应用，Stage-6 VCS evidence已刷新，Vivado synthesis已启动。01:03远端日志已越过映射并进入Timing Optimization，仍无综合结束报告、Fmax或最终资源数据。过程与当前run状态见 `accagent/experiments/gpt2_medium_20261026/monitor_status.json`。

DeepSeek的29/29是selector map checkpoint状态，不代表board VCS通过；source-map review 000仍在同一个discovery进程中inflight。Claude的最新HTTP 400响应仍未指出拒绝原因，不能据此断言是请求体大小、schema或路由问题。两条线都保持在当前Stage-6，不启动重复writer或重跑前置阶段。

其他论文实验的边界保持明确：Gemma E3 exact-board Stage-6 compile-only闭环确实返回pass/0，但跳过runtime，board bring-up readiness为`not_run`，没有CCTG causal slice，正式E3机制分数仍为0。Evidence Binding 4/4 deterministic mutation cases通过，0次stale-evidence acceptance、0次false invalidation；该项不是Agent/VCS/Vivado硬件运行。Medium ACCORD/B0机制配对仍只有Stage-4/5 pilot，两侧结果相同，不能声称DCG性能收益。

Stream-HLS当前新增的是一个packed-W4/I32 `h.0.mlp.c_fc`单算子native-MLIR frontend adaptation，pipeline、translation和远端语法编译通过；不是完整24层W4A8/DDR设计，也无HLS/Vivado QoR。Allo仍缺兼容固定LLVM/MLIR工具链。旧 GPT-2 Small 和既有模型上的source-bound QoR仍保留为其各自结果，不得转记为 Medium。

## GPT-2 Medium 最新增量（2026-10-27 09:06）

本节覆盖前述01:03检查点，模型与实验口径不变：GPT-2 Medium 24层、hidden 1024、W4A8/I32、VU9P、`vcs_compile_only`；Stage-7目标频率150 MHz。

| 实验线 | 当前进度 | 当前可报告结果 / 阻塞 |
| --- | --- | --- |
| GPT-6.1-Sol | Stage-6 exact-board VCS compile/elaboration通过；Stage-7最新候选已综合，下一次source-cycle分析和时序优化运行中 | 归档`1120a8fd0d15`：Fmax 61.4968 MHz、WNS -12.261 ns；DSE估算10,014,364 cycles / 16 tokens / 24层，对应98.2538 token/s；150 MHz未达到 |
| DeepSeek-V4-Pro | Stage-6 debug/repair loop运行中，event 1918 | 最新请求HTTP 402 `Insufficient Balance`；没有exact-board VCS或Vivado QoR |
| Claude Opus 5 | Stage-6 board harness repair重试中 | 多次HTTP 403 `insufficient_user_quota`，此前有HTTP 400 `invalid_request`；没有exact-board VCS或Vivado QoR |
| Stream-HLS | 单个packed-W4 Linear native-MLIR适配已编译 | 没有完整24层W4A8/DDR图或VU9P QoR |
| Allo | 工具链审计完成 | 缺兼容pinned LLVM/MLIR后端；无编译或QoR |

GPT-6.1候选run-local timing change把`IntegerAttention`的16-score softmax maximum串行归约切为两个平衡寄存器阶段，名义上每个16-token/16-head pass增加256周期。该版本的Chisel compile、GeneratedContractCheck、完整AxiDdrTop/Vivado top elaboration与exact-board VCS compile-only均通过；VCS输入fingerprint为`aa6468cb58468d3e98b3398f83051efcf6275fc3637feb5e1cd2bdf424c20d34`，仿真按策略跳过。

该归档的资源为LUT 604,763、FF 132,887、DSP 2,842、URAM 208、RAMB36 198、RAMB18 16。源码schedule为9,810,600 cycles；周期模型叠加DSE DDR refill service后为10,014,364 cycles，得到98.2538 token/s。吞吐是源码/DSE校准估算，不是RTL周期或板卡实测；没有建模外部停顿和板壳开销。Fmax是OOC post-synthesis估计，不是place-and-route或上板频率。证据位于`accagent/runs/gpt2_medium_gpt61_20261026/backend_board/measurements/1120a8fd0d158d1ee4eddab04c1499a15f2af765275c446565f205b7c1f3e4f0/`。旧归档`fc553c...`的5,067,064 cycles / 86.445 token/s不适用于该候选；旧`43042dd...`的47.483 MHz综合点只作历史比较。

150 MHz目标仍未达到，当前GPT-6.1 run继续时序优化。DeepSeek/Claude的API错误是当前实际阻塞，不因其retry次数计为实验进展，也未变更模型或路由。当前监控与上下文恢复点见`accagent/experiments/gpt2_medium_20261026/monitor_status.json`及`docs/context_2026-03-27.md`。

## GPT-2 Medium 最新结果（2026-10-27 12:08）

本节更新09:06检查点。实验口径保持 GPT-2 Medium 24层、hidden1024、W4A8/I32、VU9P、batch1/seq16、`vcs_compile_only`，时序优化目标150MHz。不同源码归档与XDC的QoR/周期不得拼接。

| 实验线 | 最新完成的source-bound结果 | 当前源码/阶段 |
| --- | --- | --- |
| GPT-6.1-Sol | archive `4e834fa2...`：Fmax 116.836079MHz，WNS -4.559ns（4ns/250MHz XDC）；LUT573403、FF171385、DSP2842、URAM208、BRAM36 198、BRAM18 16；8721748估算cycles/16 tokens，214.335161 estimated token/s | 后续run-local `Norm.scala` reduction balancing patch通过增量Chisel/top elaboration及exact-board VCS compile-only。新 attempt `3106621_1793072916845356419` 已按6.666667ns/150MHz约束进入Vivado Timing Optimization；尚无当前源码QoR |
| DeepSeek-V4-Pro | archive `44b432c5...`：Fmax 24.274791MHz，WNS -34.528ns（6.666667ns/150MHz XDC）；LUT635454、FF126891、DSP4158、URAM208、BRAM36 198、BRAM18 12；5067064估算cycles/16 tokens，76.651222 estimated token/s | 最新 `Common.scala`/`Attention.scala` 以32-cycle sequential restoring divider替代softmax reciprocal的组合除法（每次增加31 cycles）。增量编译/top elaboration及exact-board VCS compile-only通过，verification report pass；该源码的DSE周期重算和fresh synthesis待Stage-7继续 |
| Claude Opus 5 | 无完整AXI/DDR VCS或Vivado QoR | Stage-6 board harness repair持续HTTP403 `insufficient_user_quota`；截至11:54为第32次请求，reported balance -$0.389920。原模型/API route保持不变 |

GPT与DeepSeek上述最新QoR都属于此前完成归档，不代表各自当前源码。GPT下一次综合正在远端运行；DeepSeek当前patch刚通过compile-only且需要周期重估后综合。两线均未达到150MHz。所有Fmax/resource数据为generated-top OOC post-synthesis，不是place-and-route、bitstream或上板结果；token/s为source-calibrated DSE estimate，不是RTL仿真或板卡吞吐。

其他组保持此前证据：Medium ACCORD/B0机制配对已有Stage-4/5及部分compile-only结果，但E2 cross-token-reuse board discovery被W8API HTTP503阻塞、尚无board AXI/DDR VCS或机制QoR；Allo缺兼容pinned LLVM/MLIR工具链；Stream-HLS只有单Linear packed-W4 probe，没有完整24层可比QoR。Gemma E3仍无runtime/CCTG causal slice，Evidence Binding 4/4结果仍为synthetic fixture tests。

## GPT-2 Medium 续跑检查点（2026-10-27 12:16）

- GPT-6.1-Sol的最新完整source-bound结果仍是archive `4e834fa2...`：116.836079 MHz、WNS -4.559 ns（4 ns/250 MHz XDC）、8721748估算cycles和214.335161 DSE-estimated token/s。当前Norm patch的exact-board VCS compile-only已于11:37通过；Vivado attempt `3106621_1793072916845356419`仍在6.666667 ns/150 MHz约束下做Timing Optimization，尚无新报告。核对发现远端 `GeneratedAxiDdrTop.sv`、`IntegerAttention.sv`和`VectorNorm.sv`与本地当前综合输入哈希一致，旧archive指标仍不能归给新源码。
- DeepSeek-V4-Pro的最新完整source-bound结果仍为archive `44b432c5...`：24.274791 MHz、WNS -34.528 ns（150 MHz XDC）、5067064估算cycles和76.651222 DSE-estimated token/s。DDR response-valid adapter最新修复后，exact-board compile-only于12:13:35通过；Vivado attempt `3114237_1793074417883987844`于12:13:37在150 MHz约束下启动并仍在运行。远端 `GeneratedAxiDdrTop.sv`和`IntegerAttention.sv`与当前核心输入匹配；周期重估和当前源码QoR未完成。
- Claude Opus 5保持原run/model/API；最新generation transaction attempt 35仍收到W8API HTTP 403 `insufficient_user_quota`，沿原退避重试。没有exact-board VCS或QoR。
- ACCORD/B0 E2 cross-token-reuse两个现有repair transaction到attempt 102仍遇HTTP 503 `No available channel for gpt-6.1-sol`。sample-project-index已交接，但board discovery未刷新；没有board-wrapper VCS或机制QoR。没有重跑Stage-4/5。
- Allo/Stream-HLS、Gemma E3与Evidence Binding没有新结果：Allo无兼容pinned LLVM/MLIR；Stream-HLS仅有单Linear packed-W4 probe；Gemma E3缺runtime/CCTG causal slice；E1-E4的4/4为synthetic fixture结果。

本检查点没有新增可用于论文的性能数值。现有Fmax为source-archive-bound generated-top OOC post-synthesis；token/s为DSE估算而非RTL或板卡实测。旧archive频率、资源和周期不得转配到当前修复源码。实时状态和重试证据见`accagent/experiments/gpt2_medium_20261026/monitor_status.json`。

### 12:24 工具进展

GPT attempt `3106621_1793072916845356419`完成Timing Optimization与Technology Mapping，当前在Final Netlist Cleanup；DeepSeek attempt `3114237_1793074417883987844`完成RTL Optimization Phase 1及timing-constraint validation/loading。尚无新Fmax或资源报告。Claude attempt_count为36，quota错误仍按900秒重试；ACCORD/B0 E2两条repair transaction到attempt 107，继续HTTP 503。没有新吞吐数据，当前DSE cycle估计仍绑定先前archive。

12:29更新：GPT attempt已完成IO insertion和instance renaming，正在Rebuilding User Hierarchy；DeepSeek已完成RTL Optimization Phase 2，进入Cross Boundary and Area Optimization。两条Vivado均活跃且无新timing/utilization报告。Claude仍在attempt_count 36的403退避中；ACCORD/B0 E2两边已到attempt 110并继续HTTP 503。没有新Fmax、资源或周期/吞吐配对结果。

12:31更新：GPT完成Rebuilding User Hierarchy与Renaming Generated Ports；DeepSeek完成Cross Boundary and Area Optimization及ROM/RAM/DSP/retiming reporting。两个Vivado job仍活跃，尚无timing/utilization报告。

12:35更新：GPT Vivado synthesis日志报告0 errors、0 critical warnings，写完synthesis report后仍在进行综合网表转换；正式timing/utilization文件尚未到达本地。DeepSeek已进入150 MHz约束下的Timing Optimization。还没有新Fmax、最终资源或当前源码周期/吞吐结果；中间cell tallies不作为最终utilization数据。

12:36新增GPT资源结果：attempt `3106621_1793072916845356419`的官方远端hierarchical utilization report显示 `GeneratedAxiDdrTop` 在器件 `xcvu9p_CIVflgb2104-2`上的LUT=564045（logic LUT=563805）、FF=172840、DSP=2842、URAM=208、RAMB36=198、RAMB18=16、SRL=240。该报告的XDC period为6.666667 ns（150 MHz），`synth_design`成功且0 errors/0 critical warnings。Report SHA-256=`138d749dffa6e5a4d63f7ba6918a0b41371fe493639b2ddb45737784b98e7a21`；核心生成RTL的三个关键文件哈希与本地当前综合输入一致。尚未拿到timing report；当前源码周期与token/s也未校准，故本项只先报告资源，不报Fmax或吞吐。该段为12:36的中间记录，下面更新报告完成后的结果。

## GPT-2 Medium 综合进展（2026-10-27 12:42）

GPT-6.1-Sol Stage-7 attempt `3106621_1793072916845356419`已完成source-bound报告归档。archive SHA-256=`4d5dd59f6b1b318913a1bdb3ba783201c2fdce1a3bf3938e36ce6718a2811c3b`；器件`xcvu9p_CIVflgb2104-2`，design top=`GeneratedAxiDdrTop`。Generated-top OOC post-synthesis Fmax估计119.9760048MHz，WNS=-1.668ns，period约束6.666667ns/150MHz，故150MHz目标仍未达到。资源为LUT564045（logic LUT563805）、FF172840、DSP2842、URAM208、RAMB36 198、RAMB18 16、SRL240。Timing报告SHA-256=`cc72e380896b3e88ab4566ed25d4f5cafb2f9291f0134ee88f47a191b21f177b`。

当前候选source-calibrated DSE周期为8,722,180 cycles/16 tokens/24层；按该archive的post-synthesis Fmax计算为220.084437 estimated token/s，是GPT-6.1线目前最高source-bound DSE吞吐候选。周期不是RTL仿真计数；频率和资源为综合后OOC结果，不是place-and-route或板卡数据。关键路径从QKV projected-memory RAMB36 `CLKARDCLK`到`vValues_0_reg[0]/S`，data path=8.226ns、35 logic levels。此source在综合前通过exact-board `vcs_compile_only`，不声称功能仿真或上板通过。

Agent已根据该路径启动下一轮run-local timing repair，LLM事务attempt 2仍inflight。修复候选必须重新compile-only、重新综合并校准自己的cycles，不能继承archive `4d5dd59f`的QoR。归档`4e834fa2...`继续作为历史结果保留；archive `4d5dd59f...`及对应源码证据独立保存。

其他组：DeepSeek attempt `3114237_1793074417883987844`仍在150MHz Vivado流程；当前sequential-divider源码已通过exact-board VCS compile-only，当前cycles与timing/utilization未返回，旧archive `44b432c5`不适用于该源码。Claude Opus 5 Stage-6事务到attempt 37，反复W8API HTTP 403 `insufficient_user_quota`，无exact-board VCS/QoR。ACCORD/B0 E2 cross-token-reuse两侧repair事务到attempt 119，持续HTTP 503 `No available channel for gpt-6.1-sol`，尚无board discovery刷新、board VCS或机制QoR。Allo/Stream-HLS仍无相同24层GPT-2 Medium、W4A8/I32、DDR和VU9P条件下的全模型QoR；Gemma E3缺runtime/CCTG causal slice，E1-E4的4/4是synthetic fixtures。

## 2026-10-27 12:54 续跑检查点

GPT-6.1当前run-local QKVProjection修复源码于12:51通过exact-board VCS compile/elaboration，仿真按`vcs_compile_only`跳过。Agent已重入Stage-7并请求当前源码周期重估，尚无新综合报告。该线最新完整候选仍为archive `4d5dd59f6b1b318913a1bdb3ba783201c2fdce1a3bf3938e36ce6718a2811c3b`：OOC post-synthesis Fmax=119.9760048MHz、WNS=-1.668ns（150MHz XDC）、资源LUT564045/FF172840/DSP2842/URAM208/BRAM36 198/BRAM18 16；source-calibrated DSE=8722180估算cycles/16 tokens，220.084437 estimated token/s。150MHz目标未达到，且这些指标不属于当前修复源码。

DeepSeek-V4-Pro attempt `3114237_1793074417883987844`仍在远端Vivado运行；12:52日志完成technology mapping/IO insertion并进入user-hierarchy rebuilding，时序与资源报告尚未生成。当前sequential-divider源码通过exact-board VCS compile-only，功能仿真跳过；当前源码cycles仍待重算。12:53核对`GeneratedAxiDdrTop.sv`和`IntegerAttention.sv`的本地/远端综合输入哈希一致。最后完整归档`44b432c5d3781fbb9c259d2f256b15bc6748eae906c71fdd90ec02b19454dc32`为24.274791MHz及76.651222 DSE-estimated token/s，仅对应其源归档，不归给后续改动。

Claude Opus 5 Stage-6继续在W8API HTTP 403 `insufficient_user_quota`后退避重试；ACCORD/B0 E2 cross-token-reuse两个既有controller截至12:52到attempt 127，仍收到HTTP 503 `No available channel for gpt-6.1-sol`，sample-project index虽已交接，但board discovery未刷新、board-wrapper VCS未运行。Allo缺兼容pinned LLVM/MLIR依赖；Stream-HLS无全模型W4A8/DDR/VU9P QoR；Gemma E3缺runtime/CCTG causal slice，E1-E4 evidence-binding 4/4仍为synthetic fixtures。该检查点没有新增可接受性能数据。

以上频率/资源是generated-top OOC post-synthesis，周期和token/s是DSE估算；没有RTL实测周期、place-and-route、bitstream或板上吞吐结果。

## 2026-10-27 13:05 增量

GPT-6.1当前源码分析已完成：source fingerprint=`80abbf69c952c1904ee9af70eb16dbd758e69fd13135df3c86958a83a873e268`，16 tokens、24层的compute-only source schedule为8,518,416估算cycles。该计数不是RTL仿真结果，尚未叠加DDR refill DSE项。新150MHz Vivado attempt `3151090_1793077231171175481`已在远端运行，尚无新QoR；旧archive `4d5dd59f...`的119.976MHz和220.084 estimated token/s不属于该当前源码。

DeepSeek attempt `3114237_1793074417883987844`远端已生成初步utilization：LUT637844、FF126696、DSP4158、URAM208、BRAM36 198、BRAM18 12；timing summary仍在生成，周期校准也未完成。`GeneratedAxiDdrTop.sv`与`IntegerAttention.sv`关键文件本地/远端哈希匹配。该部分资源尚未形成完整source-bound timing/cycle归档。

Claude Opus 5 attempt 37在13:03继续遇到W8API HTTP403 `insufficient_user_quota`；ACCORD/B0 E2两个既有controller于13:04到attempt 135仍收到HTTP503 `No available channel for gpt-6.1-sol`，没有board discovery或board-wrapper VCS结果。Allo/Stream-HLS、Gemma E3和E1-E4 evidence-binding本次无新增证据。

13:08复查：GPT-6.1新150MHz synthesis attempt `3151090_1793077231171175481`已进入RTL Optimization Phase 1。DeepSeek attempt仍在生成timing summary；其OOC报告日志提示未设置`HD.CLK_SRC`，因此clock-delay/skew估计有限。此时没有新的完整source-bound频率/周期/吞吐结果。

## GPT-2 Medium 最新增量（2026-10-27 13:40）

| 实验线 | 最新已完成证据 | 当前推进状态 |
| --- | --- | --- |
| GPT-6.1-Sol | 最近完整配对仍为archive `4d5dd59f...`：119.9760048MHz、WNS -1.668ns、8,722,180 DSE cycles/16 tokens、220.084437 estimated token/s；资源LUT564045/FF172840/DSP2842/URAM208/BRAM36 198/BRAM18 16 | 当前源码的compute-only source schedule为8,518,416估算cycles（未计DDR refill）。150MHz Vivado attempt `3151090_1793077231171175481`仍在远端，已推进到IO insertion/netlist reporting；新timing/utilization与DDR-adjusted cycles待归档 |
| DeepSeek-V4-Pro | 新完成archive `f5c993338b20f8a1974f5f6b458f864c79a4c87761050c128f3c79845ca674f0`：27.3762593MHz、WNS -29.861ns、5,067,064 DSE cycles/16 tokens、86.444566 estimated token/s；资源LUT637844/FF126696/DSP4158/URAM208/BRAM36 198/BRAM18 12 | 当前exact-board VCS compile-only执行失败，10个`Error-[IBLHS-NT]`指向生成的board wrapper将DDR AXI net型输出用于过程赋值。same-run Stage-6 repair loop iteration 4 active；归档指标不转配到修复源码 |
| Claude Opus 5 | 无exact-board VCS或QoR | 原Stage-6 run与W8API route保持不变；attempt 39于13:31遇HTTP403 `insufficient_user_quota`并进行900秒退避 |
| ACCORD/B0 E2 | 既有Stage-4/5、operator-leaf 8/8和single-layer compile/elaboration证据 | 两侧Stage-6 repair controllers于attempt 160遇HTTP503无可用`gpt-6.1-sol` channel，90秒后重试；尚无board-wrapper VCS或机制QoR |
| Allo / Stream-HLS | 无同条件全模型QoR | 固定环境缺兼容Allo LLVM/MLIR；Stream-HLS没有完整24层W4A8/DDR图 |

DeepSeek失败来自真实VCS compile/elaboration，不是`vcs_compile_only`将跳过的RTL仿真误判为失败。当前source仍在Agent修复闭环中。所有token/s是DSE估算，Fmax/资源是source-archive-bound generated-top OOC post-synthesis；未完成place-and-route、RTL实测周期或板卡吞吐。详细run与错误证据见`accagent/experiments/gpt2_medium_20261026/monitor_status.json`及各run目录。

## 2026-10-27 14:10 最新实验组状态

| 实验组 | 已有结果/证据 | 当前状态 |
| --- | --- | --- |
| GPT-6.1-Sol × GPT-2 Medium | 归档`6380be3bb847...`：145.8151MHz、WNS -0.191ns、资源LUT563358/FF172984/DSP2840/URAM208/BRAM36 198/BRAM18 16；DSE估算8,722,180 cycles/16 tokens、267.4838 token/s | 后续Linear FSM decode源码已通过Chisel/contract/顶层elaboration，待exact-board VCS及新综合。source-cycle Agent发现top-level `done`可能在token 0末拍提前结束16-token pass，当前不能将旧DSE数值视为有效全pass吞吐。时序修复attempt 2进行中 |
| DeepSeek-V4-Pro × GPT-2 Medium | 旧归档`f5c993338b20...`：27.3763MHz、WNS -29.861ns、资源LUT637844/FF126696/DSP4158/URAM208/BRAM36 198/BRAM18 12；DSE估算5,067,064 cycles/16 tokens、86.4446 token/s | 当前exact-board VCS compile-only失败，10个DDR AXI net型输出过程赋值错误。14:09重试已进入同run Agent repair loop。compact preflight误拒只读SHA绑定大源码投影的框架故障已修正；暂无新源码通过或新QoR |
| Claude Opus 5 × GPT-2 Medium | Stage-4/5与operator/single-layer compile-only证据保留 | Stage-6同一run等待W8API；attempt 41 HTTP 403 `insufficient_user_quota`，900秒退避，无board VCS/QoR |
| ACCORD/B0 E2 cross-token-reuse | Stage-4/5通过；operator-leaf 8/8，single-layer compile/elaboration 31模块通过 | 两个既有Stage-6 controller于14:08 attempt 180均遇HTTP 503 no-channel；无board discovery刷新、board VCS或机制QoR |
| Allo / Stream-HLS | 已完成工具链可行性审计 | 当前pinned环境没有相同24层GPT-2 Medium、W4A8/I32、DDR/VU9P全模型可比QoR |

框架修复验证：新增post-VCS只读源码投影哈希绑定回归测试通过；post-VCS compaction测试通过。`tests.test_compile_only_board_discovery` 24项中1项旧断言失败（`full_weight_image_manifest` compaction预期），与本修复无关；`git diff --check`通过。没有修改硬件源码或改变活动实验/API配置。

上述Fmax/资源仅是源绑定generated-top OOC post-synthesis，周期/吞吐为DSE估算。当前没有新的已接受QoR；无RTL实测周期、place-and-route或板上吞吐数据。

### 14:17 增量

GPT-6.1 Agent已在run-local `DecoderBlock.scala`修正block完成标记，使外部`last`只对应配置序列的最终token，并在`Linear.scala`寄存化cache compute-hold控制。增量Chisel与顶层elaboration通过，但`case_axi_ddr_interface`发现生成compute-slot adapter引用的认证kernel没有被纳入当前generated boundary closure；exact-board VCS compile-only因依赖gate未过而跳过。当前源码仍待同run Agent修复source closure并重新compile-only，然后才能综合。新的周期分析必须确认末token完成边界修复有效；旧archive的267.4838 token/s暂只作为历史DSE估值。

DeepSeek同run修复已越过compact-source preflight异常并接收到VCS compile日志；现有wrapper仍有10个`Error-[IBLHS-NT]`。Repair Agent当前拟重建generated compute-slot compile-source closure、保留认证kernel与exact-board wrapper，再运行compile-only。Claude与E2机制对照分别受W8API 403额度错误、W8API 503 no-channel影响，持续沿既有retry等待；Allo/Stream-HLS无同条件全模型QoR。无新的性能结果或QoR晋级。
