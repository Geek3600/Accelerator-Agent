# Qwen2-Accelerator 当前架构与运行机制

更新时间：2026-04-02  
适用对象：后续需要直接阅读 RTL / Chisel / full-seq 验证代码并自行调试的人  
本文定位：当前代码事实文档，不是早期设计意图文档。若本文与旧文档、旧口头约定或旧脑内模型冲突，以当前代码为准。

---

## 1. 先说结论：这个工程现在到底是什么

当前工程已经不是“单个 stage 的概念验证集合”，而是一个围绕 **OPT-125M 单层 Transformer block** 搭起来的、能够跑 **真实数据** 和 **912 token 全序列验证** 的加速器系统。

当前工程可以拆成三层：

1. **Core RTL / Chisel 层**
   - 入口：`src/main/scala/Top.scala`
   - 职责：实现单层 block 主链
   - 主链为：
     - `LN1 -> QKVLinear -> Attention(DM1 -> Softmax -> VCache -> DM2) -> OutLinear -> ResAdd1 -> LN2 -> FFNUp -> FFNDown -> ResAdd2`

2. **System wrapper 层**
   - 入口：`verification/rtl/NinePSystemTop.sv`
   - 职责：把单层 core 包装成一个能从 DDR 取输入/权重、逐 token 调度、跑完整 912 token 的系统
   - 核心思想不是“让 core 原生支持 912 token 所有路径”，而是：
     - **非 attention 主链** 仍按单 token 运行
     - **attention 子系统** 单独看到完整历史长度

3. **真实数据验证工具层**
   - 入口：`scripts/verification/opt125m_e2e.py`
   - 职责：把 artifact 整理成验证 case，生成 DDR image / golden / window.cfg，并调用 Verilator 或 VCS

这三层现在是绑在一起工作的。只理解 `Top.scala` 已经不够；如果不理解 `NinePSystemTop.sv` 和 `opt125m_e2e.py`，就很难理解为什么 core 明明很多地方还是 `MAX_SEQLEN=26 / MAX_PREFILL=8`，却能跑 912 token full-seq。

---

## 2. 当前代码的真实状态

截至这份文档更新时，系统已经能做到：

1. 通过 `NinePSystemTop` 跑完 `912 token` 全序列
2. 输出 `58368 = 912 * 64` 个最终结果 beat
3. 不再卡在早期 runtime deadlock（历史上卡过 `token9`、`token11`、`token31`）

当前剩余问题已经不是“系统卡死”，而是“结果和 golden 尚未完全对齐”：

- full-seq 能跑完
- 当前 first mismatch 已经收敛到最终结果比对
- 这意味着当前主矛盾是 **数值对齐 / 精度边界 / 地址或配对细节**，不是主链走不通

这点很重要，因为它决定了后续调试方法：

- 现在不该优先猜“某个 stage 完全没工作”
- 而应该从 **首个 mismatch 的 token / beat / lane** 向前逐级回溯

---

## 3. 文档范围

本文覆盖四类内容：

1. 当前 accelerator core 的静态结构
2. 当前 runtime 的真实流动方式
3. full-seq 9P wrapper 如何调度 core
4. 后续调试时必须记住的关键实现细节

本文不追求：

1. 讲 transformer 数学原理
2. 重复早期版本的抽象图
3. 把每个模块逐行翻译成自然语言

本文追求的是：

1. 你读完以后能准确画出现在的模块关系
2. 你读完以后知道每一级的 `ready/valid/st/last/addr` 到底是什么意思
3. 你读完以后能自己从 mismatch 回溯到具体 stage

---

## 4. 全局分层视图

### 4.1 系统总视图

```text
opt125m_e2e.py
  ├─ 准备 DDR image / golden / window.cfg
  ├─ 编译 generated/Top.sv + NinePSystemTop.sv + testbench
  └─ 启动 VCS/Verilator full-seq 验证

NinePSystemTop.sv
  ├─ 从 DDR 把 input / weight / bias 装入本地数组
  ├─ 进行 core 权重初始化
  ├─ 逐 token 驱动 Top
  ├─ 非 attention 主链按单 token 运行
  └─ attention 独立看到完整历史长度

Top.scala
  ├─ LNAddrGen
  ├─ LayerNormQ (LN1)
  ├─ QKVLinear
  ├─ Atten
  │   ├─ DM1FP32
  │   ├─ SoftmaxPipFP32
  │   ├─ VCache
  │   └─ DM2Quant
  ├─ OutLinearFP32
  ├─ ResAddFP32
  ├─ LayerNormQ (LN2)
  ├─ FFNUp
  ├─ FFNDownFP32
  └─ ResAdd2FP32
```

### 4.2 Core 主链的真实顺序

当前 `Top.scala` 内的真实顺序如下：

1. `LNAddrGen`
2. `LayerNormQ`，作为 `LN1`
3. `QKVLinear`
4. `Atten`
   - `DM1FP32`
   - `SoftmaxPipFP32`
   - `VCache`
   - `DM2Quant`
5. `OutLinearFP32`
6. `Queue(outToResQ)`
7. `ResAddFP32`
8. `LayerNormQ`，作为 `LN2`
9. `FFNUp`
10. `FFNDownFP32`
11. `ResAdd2FP32`

注意两点：

1. `OutLinear` 后面不是直接进 `ResAdd`，中间有一个显式 queue
2. `ResAdd` 的输出同时喂给 `LN2` 和 `ResAdd2`，所以反压不是单路，而是双路共同约束

---

## 5. 统一术语、常量和数据格式

这一节很重要。后面所有地址、beat、token 的描述都基于这里。

### 5.1 基础向量尺寸

OPT-125M 单层 block 在当前实现里采用：

- hidden size = `768`
- head 数 = `12`
- 每个 head 维度 = `64`
- 每拍 lane 数 = `12`
- `768 / 12 = 64`，所以 **一个 768 维向量等于 64 个 beat**

也就是说：

- 任意 `768-dim FP32` 或 `768-dim INT8` 的 token 级向量
- 在当前主链里都天然对应 **64 beat / token**

### 5.2 常见 pack 宽度

当前代码里常见的数据宽度如下：

| 名称 | 宽度 | 含义 |
| --- | --- | --- |
| `FP32_PACK_WIDTH` | `12 * 32 = 384 bit` | 每拍 12 个 FP32 |
| `INT8_PACK_WIDTH` / `MEM_WIDTH` | `12 * 8 = 96 bit` | 每拍 12 个 INT8 |
| `HEAD_WIDTH` | `64 * 8 = 512 bit` | 一个完整 attention head 的 64 维 INT8 输出 |
| QKV 输出拍 | `48 bit` | 每拍 `[V1,V0|K1,K0|Q1,Q0]` |
| DM1 / Softmax ctx 行 | `912 * 32 bit` | 一整行 FP32 logits / probs |
| DM2 ctx 行量化后 | `912 * 8 bit` | 一整行 UINT8 / INT8 概率 |

### 5.3 顶层容量与长度常量

当前工程里最容易搞混的是：**不是所有模块都共享同一套长度常量**。

#### 主链短窗口常量

在大量主链模块中，仍保留的是早期短窗口常量：

- `BATCHSIZE = 32`
- `MAX_SEQLEN = 26`
- `MAX_PREFILL = 8`

典型模块：

- `TempAdapter.Param`
- `QKVLinear.Param`
- `OutLinear.Param`
- `FFNUp.Param`
- `FFNDown.Param`
- `ResAdd/ResAdd2`

#### Attention 长序列常量

Attention 子系统现在已经切到 full-seq 常量：

- `DM.Param.MAX_SEQLEN = 912`
- `DM.Param.MAX_PREFILL = 912`
- `Softmax.Param.SEQ_LEN = 912`
- `ResMEM.Param.MAX_PRELEN = 912`

这就是当前 full-seq 架构能成立的关键：

1. 非 attention 主链仍保持“短窗口 / 单 token”工作方式
2. attention 内部的 DM1 / Softmax / VCache / DM2 已经能接受 912 级别历史长度

### 5.4 地址语义

当前代码里最容易误解的是：**`addr` 不是全系统统一语义**。

常见 `addr` 语义如下：

1. **外部输入 token beat 地址**
   - `0..63` 表示一个 token 的 64 个 beat
   - 系统级绝对地址常写成：
     - `token_idx * 64 + beat_idx`

2. **LayerNorm / FFN / OutLinear 这类 768-dim 路径地址**
   - 本质上是 token 内部的 64 拍地址，或者 token 索引和 beat 索引展开后的地址

3. **Attention 内 QKV 输出地址**
   - `QKVLinear` 输出的是每个 token、每个 head 的 32 拍地址
   - 因为一个 head 维度是 64，而每拍吐 2 个元素，所以：
     - `64 / 2 = 32 beat / head`

4. **DM1 / Softmax / DM2 行地址**
   - 这些模块很多时候的 `addr` 更像“当前 batch/token/head 行号”
   - 不是简单的 token 内 beat 地址

5. **系统最终输出地址**
   - `NinePSystemTop` 把 core 输出地址转换成系统级地址：
   - `sys_res_addr = (run_token_idx << 6) + core_res_addr`
   - 即：
     - 当前 token 号乘 64
     - 再加这个 token 内部的 64-beat 结果地址

### 5.5 `st`、`valid`、`last`、`ready` 的统一理解

全工程里这几个信号的含义大体一致，但不能想当然。

#### `valid`

- 表示这一拍输出/输入有效
- 不一定等于“本模块已经开始某个 token”

#### `ready`

- 表示接收方能接
- 有些地方是单一路 ready
- 有些地方是多路 ready 的与逻辑
- 有些地方中间经过 queue 解耦后，`ready` 已不是下游模块原生 ready

#### `st`

- 通常表示某一段输出窗口的起拍
- 它不是“全系统 token 0 的第一拍”这种统一概念
- 不同模块的 `st` 是局部语义

#### `last`

- 通常表示当前输出窗口最后一拍
- 但“窗口”是什么，取决于模块
- 例如：
  - LN 路 `last` 常是一个 token 的最后 beat
  - QKV 对 Attention 的 `last` 常是一个 head 的最后 beat
  - DM1 / Softmax 的 `last` 常是当前行的最后一个有效结果

---

## 6. 当前精度与量化契约

这一节以 `docs/opt_quan.md` 和当前 RTL 为准。

### 6.1 精度表

| Stage | 输入 | 权重/参数 | 输出 |
| --- | --- | --- | --- |
| `LN1` | FP32 | gamma/beta FP32 | INT8 |
| `QKVLinear` | INT8 | INT8 + INT8 bias | INT8 |
| `DM1 (Q·K)` | INT8 × INT8 | - | FP32 |
| `Softmax` | FP32 | mask / prefix | FP32 |
| `DM2 (P·V)` | 量化后的 probs × INT8 V | - | INT8 |
| `OutLinear` | INT8 | INT8 weight + FP32 bias | FP32 |
| `ResAdd1` | FP32 + FP32 | - | FP32 |
| `LN2` | FP32 | gamma/beta FP32 | INT8 |
| `FFNUp` | INT8 | INT8 weight + INT8 bias | INT8 |
| `FFNDown` | INT8 | INT8 weight + FP32 bias | FP32 |
| `ResAdd2` | FP32 + FP32 | - | FP32 |

### 6.2 最容易搞错的几个精度边界

1. **Softmax 本体是 FP32**
   - 它不输出 INT8
   - 真正把 probability 压成 8bit 的动作发生在 `DM2Quant` 入口

2. **OutLinear / FFNDown 输出都是 FP32**
   - 所以后面两级残差加法都在 FP32 域工作

3. **FFNUp 输出是 INT8**
   - 并且 ReLU 已经融合在 FFNUp 里

4. **ResAdd / ResAdd2 都不是 INT8 残差**
   - 它们是 FP32 加法
   - 出现最终 mismatch 时，默认先查两路输入，不要先怀疑 adder 本体

5. **DM2 ctx 是先量化再乘**
   - `Softmax FP32 -> Fp32QuantizeToUInt8Vec -> ctxmem`
   - 然后与 VCache 的 `INT8 V` 做乘加

---

## 7. 9P full-seq 运行机制

这一节讲的是：**系统为什么能跑完整 912 token**。

### 7.1 case 是怎么准备出来的

full-seq case 由 `scripts/verification/opt125m_e2e.py` 中的 `prepare_9p_fullseq_case()` 负责生成。

它做了几件事：

1. 从真实 artifact 读取：
   - `layernorm1` 输入/输出/gamma/beta
   - `layernorm2` 输入/输出/gamma/beta
   - `qkv_proj` 权重/bias/scale
   - `out_proj` 权重/bias/输出
   - `fc1` 权重/bias/scale
   - `fc2` 权重/bias/输出
   - `res_add1` 输出

2. 推导量化参数：
   - `ln1_inv_scale / zero_point`
   - `ln2_inv_scale / zero_point`
   - `out_out_scale`
   - `ffndown_out_scale`

3. 重新拼出硬件实际用的数据布局：
   - `qkv_weight = [Q;K;V]`
   - `qkv_bias_hw = [q_bias, k_bias, v_bias]`
   - 各种 weight / bias 会被打包成与硬件内存一致的 beat 流

4. 构造 DDR image
5. 构造最终结果 golden
6. 输出 `window.cfg`
7. 输出 `case.json`

### 7.2 full-seq DDR regions

当前 `prepare_9p_fullseq_case()` 构造的 DDR region 包括：

| region | 来源 | 说明 |
| --- | --- | --- |
| `input` | `layernorm1.input` | 全 912 token 输入 |
| `ln1_w` | `ln1 beta + gamma` | 注意顺序是 beta 在前、gamma 在后 |
| `qkv_w` | `qkv_proj` 权重 | 已按硬件 `[Q;K;V]` 拼接 |
| `qkv_b` | `qkv_proj` bias | 已按硬件顺序拼接 |
| `sm` | `pack_softmax_mask_rows(26,26)` | 当前 full-seq wrapper 实际并不依赖这块内容 |
| `out_w` | `out_proj` 权重 | attention output projection |
| `out_b` | `out_proj` bias | FP32 packed |
| `ln2_w` | `ln2 beta + gamma` | 同 LN1 |
| `ffnup_w` | `fc1` 权重 | 768 -> 3072 |
| `ffnup_b` | `fc1` bias | INT8 packed |
| `ffndown_w` | `fc2` 权重 | 3072 -> 768 |
| `ffndown_b` | `fc2` bias | FP32 packed |

### 7.3 final golden 是怎么来的

当前 full-seq case 的最终 golden 不是直接从“一个 top 输出 artifact”拷过来的，而是脚本现算的：

```text
top_out = resadd1_out + fc2_out
```

也就是：

- `resadd1_out` 作为第二条残差支路
- `fc2_out` 作为 FFNDown 输出
- 两者相加形成最终 `ResAdd2` golden

这和硬件当前实现是一致的。

### 7.4 `window.cfg` 里到底放了什么

`window.cfg` 里放的是 full-seq 运行所需的配置和基地址，典型包括：

1. `cfg_seqlen = 911`
2. `input_beats = 912 * 64`
3. `output_beats = 912 * 64`
4. 各 stage scale / zero_point 的 `u32` 比特表示
5. 各 DDR region 的 base address

这份 `window.cfg` 是 wrapper 和 testbench 的运行配置中心。

---

## 8. `NinePSystemTop.sv`：为什么 full-seq 能成立

`verification/rtl/NinePSystemTop.sv` 是当前 full-seq 验证最关键的系统包装层。

### 8.1 它不是简单 testbench glue

它做的不只是“把 Top 接出来”，而是负责：

1. DDR 读请求发起
2. DDR 返回数据装载到本地数组
3. core 权重初始化阶段调度
4. bias / LN 权重流输入
5. token-by-token 运行时配置
6. 把 core 局部输出地址变成系统级绝对输出地址

### 8.2 wrapper 内部维护的本地存储

它在 Verilog 中维护了一组本地数组，例如：

- `input_mem`
- `ln1_w_mem`
- `ln2_w_mem`
- `qkv_w_mem`
- `qkv_b_mem`
- `sm_w_mem`
- `out_w_mem`
- `out_b_mem`
- `ffnup_w_mem`
- `ffnup_b_mem`
- `ffndown_w_mem`
- `ffndown_b_mem`

它们本质上是“DDR 装载后的片上镜像”。

### 8.3 wrapper 的状态机

wrapper 状态机如下：

1. `ST_IDLE`
2. `ST_LOAD_INPUT`
3. `ST_LOAD_LN1`
4. `ST_LOAD_QKV_W`
5. `ST_LOAD_QKV_B`
6. `ST_LOAD_SM`
7. `ST_LOAD_OUT_W`
8. `ST_LOAD_OUT_B`
9. `ST_LOAD_LN2`
10. `ST_LOAD_FFNUP_W`
11. `ST_LOAD_FFNUP_B`
12. `ST_LOAD_FFNDOWN_W`
13. `ST_LOAD_FFNDOWN_B`
14. `ST_WEIGHT_INIT`
15. `ST_CORE_RESET`
16. `ST_STREAM_LN1`
17. `ST_STREAM_LN2`
18. `ST_STREAM_QKV_B`
19. `ST_STREAM_OUT_B`
20. `ST_STREAM_FFNUP_B`
21. `ST_STREAM_FFNDOWN_B`
22. `ST_PRELOAD_PULSE`
23. `ST_PRELOAD_WAIT`
24. `ST_RUN_CFG`
25. `ST_RUN`
26. `ST_DONE`

### 8.4 各阶段的真实作用

#### `ST_LOAD_*`

作用：

1. 按 region 顺序从 DDR 取数据
2. 把返回 beat 写入本地数组

注意点：

1. `issue_count` 控制发了多少个 DDR 请求
2. `recv_count` 控制收到了多少个 beat
3. 只有在 `io_ddr_rd_data_valid` 时才真正把数据写进对应数组

#### `ST_WEIGHT_INIT`

作用：

1. 让 core 进入 `weight_init_mode`
2. 观察 core 内各个 weight loader 的地址计数是否把全部权重地址都走到

当前做法很“现实”：

1. wrapper 不自己把权重一拍拍推给 core 算法单元
2. 它只给 core 提供权重数组读取口
3. 然后盯着：
   - `core_qkv_w_addr`
   - `core_out_w_addr`
   - `core_ffnup_w_addr`
   - `core_ffndown_w_addr`
4. 当这几个地址分别到达各自最大值后，再额外等待 `128` 个 tail 周期
5. 然后进入 `ST_CORE_RESET`

也就是说：**当前 weight init 的完成判据不是“看某个 done 信号”，而是“看地址是否把整片权重空间扫完”**。

#### `ST_CORE_RESET`

作用：

1. 在权重初始化完成后对 core 做一次重新复位
2. 清掉残留状态

#### `ST_STREAM_*`

作用：

1. 顺序把 LN 权重和各种 bias 重新流式送入 core
2. 这些不是靠 `weight_init_mode` 做的，而是显式通过各模块的 `*_valid` 口灌进去

顺序为：

1. `ST_STREAM_LN1`
2. `ST_STREAM_LN2`
3. `ST_STREAM_QKV_B`
4. `ST_STREAM_OUT_B`
5. `ST_STREAM_FFNUP_B`
6. `ST_STREAM_FFNDOWN_B`

#### `ST_RUN_CFG`

作用：

1. 给本次 token 运行打一拍配置

#### `ST_PRELOAD_PULSE`

作用：

1. 给 core 打一次 `layer_st`
2. 这次脉冲既是本 token 的启动脉冲，也会驱动若干 load/weight 子模块复位到新一轮工作状态

#### `ST_PRELOAD_WAIT`

作用：

1. 在真正进入 `ST_RUN` 前再等一小段固定空档
2. 当前代码等 `64` 周期

这个阶段不是数学意义上的 prefill，而是 **为了让 core 内局部缓存 / 地址 / 流水准备好** 的工程性等待。

#### `ST_RUN`

作用：

1. 让当前 token 真正流经 core
2. 等待 `core_res_valid && core_res_last`
3. 看到当前 token 的 64-beat 最后一拍输出后：
   - 如果当前 token 不是最后一个 token，就 `run_token_idx++` 并回到 `ST_RUN_CFG`
   - 如果已经是最后一个 token，就进 `ST_DONE`

#### `ST_DONE`

作用：

1. 整个 full-seq 结束

### 8.5 为什么是“主链单 token + attention 长历史”

这一点是当前系统最关键、也最反直觉的地方。

wrapper 对 `Top` 的配置不是统一一套，而是拆成两套：

#### 主链配置

```text
core_cfg_seqlen   = 0
core_cfg_prefill  = 1
core_cfg_valid    = ST_RUN_CFG
```

这表示：

- 对 LN / QKV / OutLinear / FFN / ResAdd 这些非 attention 路径来说
- 当前每次只处理 **一个 token**
- 而且是用“prefill 1 token”的方式跑

#### Attention 配置

```text
core_attn_cfg_seqlen       = run_token_idx
core_attn_cfg_prefill      = 0
core_attn_cfg_valid        = ST_RUN_CFG
core_attn_cfg_single_query = 1
```

这表示：

- 对 Attention 子系统来说
- 当前不是 prefill，而是 **single-query decode**
- 当前 token 号 `run_token_idx` 就是历史长度上界

因此当前 full-seq 的真实运行方式是：

1. 外层系统每次只把一个 token 的 64 beat 输入主链
2. 但 attention 内部把这个 token 当成“当前 query”
3. 并访问之前所有历史 token 的 K/V / Softmax 行长度

这就是“为什么大部分主链参数还是 26/8，但全系统已经能跑 912”的根本原因。

### 8.6 Softmax mask 当前到底来自哪里

wrapper 里有两个看起来矛盾的事实：

1. `ST_LOAD_SM` 会把 softmax 相关 region 装进 `sm_w_mem`
2. 但真正送进 `Top.io_sm_w_in` 的不是 `sm_w_mem[...]`
3. 而是：
   - `make_softmax_prefix_mask(run_token_idx)`

也就是说：

- 当前 full-seq wrapper 实际采用的是 **动态 causal prefix mask**
- 不是用 DDR 里那块 `sm` region 作为最终 mask 来源

这块历史上是为了修掉 “Softmax 全零 mask 导致输出全零” 的问题而改成的。

因此目前要记住：

1. `sm_w_mem` 还会被加载
2. 但 full-seq 主路径实际使用的是 `make_softmax_prefix_mask(run_token_idx)`
3. 所以后续不要再把 `sm` DDR region 当成当前 full-seq attention mask 的唯一来源

### 8.7 系统输出地址

系统对外输出地址不是 core 原始地址，而是：

```text
io_res_addr = (run_token_idx << 6) + core_res_addr
```

含义：

1. `core_res_addr` 是当前 token 内 `0..63`
2. 外层再加上 `run_token_idx * 64`
3. 得到全序列结果线性地址

full-seq testbench 与 golden 的比对也是基于这个系统级地址完成的。

---

## 9. `Top.scala`：当前 core 顶层到底怎么连

`src/main/scala/Top.scala` 是当前 accelerator core 的事实入口。

### 9.1 `Top` 的角色

`Top` 做三件核心事情：

1. 串起单层 block 主链
2. 定义各 stage 配置和权重输入接口
3. 处理最关键的跨 stage backpressure / 缓冲 / 共享 ready

### 9.2 `Top` 最重要的两套配置口

#### 主链配置口

```text
io_cfg_seqlen
io_cfg_prefill
io_cfg_valid
```

给以下路径使用：

- `LNAddrGen`
- `LN1`
- `QKVLinear`
- `OutLinear`
- `ResAdd`
- `LN2`
- `FFNUp`
- `FFNDown`
- `ResAdd2`

#### Attention 配置口

```text
io_attn_cfg_seqlen
io_attn_cfg_prefill
io_attn_cfg_valid
io_attn_cfg_single_query
```

只给 `Atten` 使用。

这是当前架构里非常关键的一个分裂点：

- `Top` 不是把一套统一 `cfg_*` 广播到所有模块
- attention 是独立配置域

### 9.3 `Top` 输入口里最容易误解的一个信号

`Top` 的 `io.data_in_ready` 是 **输入口**，不是输出口。

它的真实语义是：

- “外部输入源当前能不能提供数据”

在 full-seq wrapper 中，这个口被直接绑成：

```text
core_data_in_ready = (state == ST_RUN)
```

也就是说：

- 这个信号不是 core 对外宣告自己 ready
- 而是 wrapper 告诉 core：“现在处于 RUN，你可以把外部输入当成可读”

如果把它理解成普通 ready 输出，很容易在调试时完全看反。

### 9.4 顶层主链连接

当前连接关系可以压缩成下面这张图：

```text
wrapper input beat
  -> LNAddrGen
  -> LN1
  -> QKVLinear
  -> Atten
  -> OutLinearFP32
  -> outToResQ
  -> ResAddFP32
  -> LN2
  -> FFNUp
  -> FFNDownFP32
  -> ResAdd2FP32
  -> Top.io.res
```

同时还有两条残差缓存支路：

1. 原始输入 `io.data_in` 经过打拍后写入 `ResAddFP32.orig_in`
2. `ResAddFP32.res` 同时写入 `ResAdd2FP32.s7_in`

### 9.5 顶层最关键的反压点

当前 `Top` 里最关键的 ready 关系如下。

#### 输入分叉 ready

输入一份数据既要进 LN1，又要进 ResAdd1 residual cache，因此：

```text
input_adapter_ready = layernorm.io.data_ready && resadd.io.orig_ready
```

这是当前顶层最重要的一个保护点之一。

原因：

1. 原始输入会同时送到 `LN1` 和 `ResAdd`
2. 如果只看 `LN1` 的 ready，而不管 `ResAdd.orig_ready`
3. 那么当 residual cache 满时，这一路会悄悄丢 beat
4. 后面 `ResAdd` / `LN2` 再从未写地址读数据，就会出现 `x/NaN`

这不是理论问题，是当前实现里真实踩过的坑。

#### `OutLinear -> ResAdd` 解耦

`OutLinear` 后面有一个显式 queue：

```text
outToResQ
```

作用：

1. 吸收 `OutLinear` 和 `ResAdd` 之间的瞬时节奏差
2. 防止 `OutLinear` 因 residual path 配对而过早 backpressure

#### `ResAdd` 输出双路反压

`ResAdd` 输出既要给 `LN2`，又要给 `ResAdd2` 缓存，所以：

```text
resadd.io.res_ready = layernorm2.io.data_ready && resadd2.io.s7_ready
```

含义：

1. 只有 `LN2` 能接
2. 并且 `ResAdd2` 的 `s7` cache 也能写
3. 当前 beat 才允许从 `ResAdd` 往前推进

这同样是不能随便简化掉的共享 ready。

---

## 10. Stage-by-stage 详细说明

下面按数据流从前往后写。

### 10.1 `LNAddrGen`：把系统级输入变成 LayerNorm 本地地址

代码入口：

- `src/main/scala/TempAdapter/LNAddrGen.scala`

#### 作用

`LNAddrGen` 的任务不是算数据，而是把外部输入源的“token 序列流”翻译成 `LayerNormQ` 能接受的本地地址与控制信号。

它解决的本质问题是：

1. wrapper 从系统角度按 token 提供输入
2. `LayerNormQ` 只关心自己内部的 `0..63` beat 地址

#### 关键计数器

`LNAddrGen` 里有三层计数器：

1. `vec_cnt`
   - token 内 beat 计数
   - 一个 768-dim token 共有 64 拍

2. `prefill_cnt`
   - prefill 模式下的 token 计数

3. `batch_cnt`
   - decode 模式下的 batch 计数

#### 启动方式

`cfg_valid` 到来时不会立刻强制输出，而是先拉起：

```text
start_pending := true
```

只有当：

```text
fire = io.data_ready && io.adapter_ready
```

时，状态机才真正从 `idle` 进 `busy`。

这里的 `fire` 同时受：

1. 外部数据源 ready
2. core 内部 LN1 + ResAdd 共享 ready

约束。

#### 地址生成

外部地址：

```text
prefill: prefill_cnt * 64 + vec_cnt
decode : batch_cnt   * 64 + vec_cnt
```

输出给 `LayerNormQ` 的本地地址：

```text
data_addr = vec_cnt
```

#### 为什么 `st/valid/last` 都打一拍

`LNAddrGen` 把这些控制信号都 `RegNext` 一拍后再输出，目的是与真实取回的数据拍对齐。

如果不打拍，最容易出的问题是：

1. `data_st` 提前于数据
2. `data_last` 与最后一拍数据错位
3. `LayerNormQ` 开始或结束 token 的位置偏一拍

#### 当前调试时怎么判断它有问题

如果你怀疑输入根本没喂对，优先看：

1. `io.cfg_valid`
2. `start_pending`
3. `fire`
4. `vec_cnt`
5. `io.mem_addr`
6. `io.data_st / data_valid / data_last`

---

### 10.2 `LayerNormQ`：先缓存 token，再做 FP32 LayerNorm，再量化到 INT8

代码入口：

- `src/main/scala/LayerNormQ/LayerNormQ.scala`

#### 作用

当前 `LayerNormQ` 不是 fully streaming LN，而是一个“**先收完整 token，再顺序做统计和归一化**”的实现。

它的处理流程是：

1. 把输入 token 的 64 个 beat 写进 `inputMem`
2. 把权重流写进 `betaVec` 和 `gammaVec`
3. 对每个 token：
   - 先扫一遍求和与平方和
   - 算 mean / variance / invStd
   - 再扫一遍原始输入做 `(x - mean) * invStd * gamma + beta`
   - 再量化成 INT8

#### 权重流顺序

这里非常容易记反。

当前 `LayerNormQ` 约定：

1. 前 64 拍是 `beta`
2. 后 64 拍是 `gamma`

不是常见的 `gamma` 在前。

这和 `prepare_9p_fullseq_case()` 里拼 LN 权重的顺序是一致的。

#### 输入缓存

输入写入条件是：

```text
when(io.data_valid) {
  inputMem.write(io.data_addr, io.data_in)
}
```

直到看见 `io.data_last` 才把：

```text
inputLoaded := true
tokenCount := ...
```

置好。

因此当前 `LayerNormQ` 的节奏是典型的：

1. **先写满**
2. **再算**

#### 状态机

当前状态机为：

1. `idle`
2. `statRead`
3. `statDrain`
4. `meanVar`
5. `sqrtReq`
6. `sqrtWait`
7. `divReq`
8. `divWait`
9. `outRead`
10. `outDrain`

可以理解为两大阶段：

1. **统计阶段**
2. **输出阶段**

#### 统计阶段

在 `statRead` 中，逐 beat 从 `inputMem` 读出 12 个 FP32。

然后：

1. `Fp32LaneSum` 求这 12 个数的和
2. `Fp32LaneSquareSum` 求平方和
3. 累加到 `sumAcc` / `sqSumAcc`

最后：

1. `mean = sumAcc / 768`
2. `var = sqSumAcc / 768 - mean^2`
3. `var + eps`
4. `sqrt`
5. `1 / sqrt = invStd`

#### 输出阶段

在 `outRead` 中，再次逐 beat 读取原始输入：

1. 取对应位置的 `gammaVec(vecIdx)` / `betaVec(vecIdx)`
2. 调 `Fp32LayerNormApply`
3. 再进 `Fp32QuantizeToInt8Pack`

最终输出：

- `io.res`
- `io.res_valid`
- `io.res_st`
- `io.res_last`
- `io.res_addr`

#### 当前实现的重要现实点

1. `LayerNormQ` 只能在 `state == idle` 时接受新输入
   - 即：
     - `io.data_ready := state === idle`

2. 它对输入 token 是先缓存再算
   - 所以这一级天然会带来明显的阶段性停顿

3. 它既被用作 `LN1`，也被用作 `LN2`
   - 两份逻辑完全同类

#### 调试优先级

当怀疑 `LayerNormQ` 出错时，建议按这个顺序看：

1. 输入 64 beat 是否完整写满
2. `tokenCount` 是否正确
3. `sumAcc` / `sqSumAcc` 是否异常
4. `meanReg` / `varReg` / `invStdReg` 是否异常
5. `out_inv_scale / zero_point` 是否正确

如果在 `LN2` 看见 `var=x` 或输出 NaN，默认先回看前一级 residual cache 是否已经喂坏，而不是先怪 LN2 算法本体。

---

### 10.3 `QKVLinear`：先做 768 -> 2304 GEMM，再重排成 head 级 Q/K/V 流

代码入口：

- `src/main/scala/QKVLinear/QKVLinear.scala`

#### 作用

`QKVLinear` 不是简单的“来一拍出一拍”线性层。

它的真实流程是：

1. 把 LN1 输出写入本地 `DataMem`
2. 用 `LoadUnit + CUQuant + StoreUnit + LoadWeight` 跑 768 -> 2304 的 GEMM
3. 先把整个 `2304-dim` 结果收齐
4. 再把结果重排成按 head 组织的 `Q/K/V` 流输出给 Attention

#### 内部子模块

1. `DataMem`
2. `LoadUnit`
3. `CUQuant`
4. `StoreUnit`
5. `LoadWeight`
6. `bias_mem`

#### 为什么必须先“收齐 2304 维”

因为 Attention 不吃一个平铺的 2304 维向量，它吃的是：

- 每个 head 的 Q
- 每个 head 的 K
- 每个 head 的 V
- 并且按 2 元素一拍送出去

所以 `QKVLinear` 先在 `vec_buffer` 里收齐整 token 的所有输出，再二次组织输出。

#### 收集阶段

`collecting` 阶段里：

1. `su_inst` 输出 96-bit / 12 lane 的结果
2. `collect_addr` 被拆成：
   - `collect_token`
   - `collect_vec`
3. 依据 `collect_vec` 所在区间选择：
   - Q scale / bias scale
   - K scale / bias scale
   - V scale / bias scale

然后：

1. `Int32VecScaleBiasToSInt32`
2. 再做 INT8 饱和裁剪
3. 写入 `vec_buffer(token)(collect_vec)`

#### 输出阶段

输出阶段里：

1. `full_vec` 表示当前 token 的 2304 个 INT8 输出
2. 再按 `head_cnt` 动态选出：
   - `Q_vec`
   - `K_vec`
   - `V_vec`
3. 每拍取两个元素，打包成：
   - `[V1,V0|K1,K0|Q1,Q0]`

#### 地址和节奏

关键计数器：

1. `head_cnt`
2. `output_cnt`
3. `prefill_cnt`
4. `batch_cnt`

其中：

1. `head_cnt` 走 `0..11`
2. `output_cnt` 走 `0..31`
3. 因为一个 head 64 维，每拍出 2 个元素，所以每 head 32 拍

输出定义：

1. `io.data_out_valid = is_outputting`
2. `io.data_out_st`：
   - 当前 head 的第一个 token 的第一个输出拍
3. `io.data_out_last`：
   - 当前 head 的所有 token 输出完毕

#### 当前实现和 Attention 的关系

Attention 接收的不是“完整 Q/K/V 向量”，而是：

1. 每个 token
2. 每个 head
3. 每拍 2 个 Q + 2 个 K + 2 个 V

这解释了为什么 DM1 / VCache 的输入格式和普通线性层不一样。

#### 调试优先级

当怀疑 `QKVLinear` 出错时，先分清是哪一层：

1. GEMM 本体错
2. scale / bias epilogue 错
3. 2304 维结果收集错
4. Q/K/V 重排错
5. head 输出节奏错

如果 `QKV` 总拍数对，但 Attention 输入看起来乱，通常更应先查重排和 `head_cnt/output_cnt`。

---

### 10.4 `Atten` 顶层：DM1 -> Softmax -> VCache -> DM2

代码入口：

- `src/main/scala/Attention.scala`

#### 作用

`Atten` 是当前 attention 子系统的整合模块，内部串起：

1. `DM1FP32`
2. `SoftmaxPipFP32`
3. `VCache`
4. `DM2Quant`
5. `ctxToDm2Q`
6. `vToDm2Q`

#### 当前 Attention 最重要的事实

当前问题往往不是“乘法器算错”，而是：

1. `ctx` 路和 `v` 路配对错
2. `st/addr/last` 语义错
3. single-query decode 边界错
4. 某一拍因 backpressure 丢失

#### 输入 ready

当前 Attention 输入 ready 是：

```text
input_ready = vcache.io.data_in_ready && dm1.io.data_ready
```

也就是说：

1. 只有 VCache 能接
2. 且 DM1 也能接
3. 才允许 QKV 输出这拍进入 Attention

这保证了 Q/K 和 V 两条支路不会从入口处就失配。

#### `ctxToDm2Q` 和 `vToDm2Q`

当前 Attention 顶层显式插了两个 queue：

1. `ctxToDm2Q = Queue(Dm2CtxBeat, 16)`
2. `vToDm2Q   = Queue(Dm2Beat,    16)`

它们都不是装饰，而是当前 full-seq 稳定运行所需的关键缓冲。

`ctxToDm2Q` 的意义：

1. `Softmax -> DM2(ctx)` 之间曾出现短暂 backpressure
2. 如果直接相连，ctx 路会丢拍或错拍
3. 队列用于把 `softmax.io.res_*` 重新整形成一条稳定流

`vToDm2Q` 的意义：

1. VCache 在 decode/single-query 下可能 burst 出一整批 V
2. DM2 不一定同拍都吃得下
3. 队列用于吸收 burst

#### 当前 Attention 内对 Softmax 输入语义的修正

`DM1.io.res_st` 来自内部 load unit 起拍，它早于真正 logits 到达 Softmax data mem 的时刻。

因此当前代码显式修正为：

1. `dm1OutStart = dm1.io.res_valid && dm1.io.res_addr === 0`
2. `dm1OutDone = dm1.io.res_valid && dm1.io.res_last`
3. `softmax.io.layer_st = dm1OutDoneD1`
4. `softmax.io.data_in_st = dm1OutStart`

目的是让 top 集成时的 Softmax 语义与 standalone harness 一致：

1. logits 第一拍真正写到 Softmax 时再认为 data_in start
2. mask/load 启动在整行 logits 写完后的下一拍

这不是无关紧要的细节，而是当前 attention 正确性的关键。

#### 当前 Attention 内的显式 mask

虽然 wrapper 还会给 Softmax 送 prefix mask，但 `Attention.scala` 里仍会对 `DM1` 输出再做一次显式 future mask：

1. `prefill` 时，屏蔽未来 token
2. `single_query` 时，屏蔽 `i > cfg_seqlen`

屏蔽方式是把未来位置写成一个负无穷近似值：

```text
softmaxNegInf = 0xff7fff8b
```

这和验证数据里“未来位置直接写成负无穷近似值”的口径保持一致。

因此当前 top 集成里，softmax 输入不是“原始未 mask logits”。

---

### 10.5 `DM1FP32`：Q·K，输入 INT8，输出一整行 FP32 logits

代码入口：

- `src/main/scala/DM/DMFP32.scala`
- `src/main/scala/DM/LoadU.scala`

#### 作用

`DM1FP32` 完成：

```text
INT8 Q × INT8 K -> FP32 logits
```

输出是一整行 logits，不是一个个单独 scalar。

#### 内部结构

`DM1FP32` 由这些部分组成：

1. `DataMem`
2. `LoadUnit`
3. `DMCUPlusFP32`
4. `StoreUnitFP32`

#### `LoadUnit` 为什么是当前最关键的模块之一

当前 full-seq runtime 稳定性的一个关键点就在 `DM/LoadU.scala`。

它的作用不是只生成地址，而是决定：

1. 什么时候开始装下一组 Q/K
2. decode / single-query 下要空等多久，才能保证上一组计算已经真的完成

#### 当前 `LoadUnit` 的 decode guard

当前代码里有一段非常关键的现实补丁：

```text
decode_pipeline_guard = 1 + 2 + log2Up(MULNUM) + 1
decode_compute_cycles = (prelen + 1) * (HEAD_VECNUM / MULNUM) + decode_pipeline_guard
single_query_vector_limit = ...
```

它的意义是：

1. 单 query decode 并不是把 32 拍 Q/K 数据发完就可以立刻切下一组
2. 还必须给 DM1 的乘法树、累加、结果转 FP32 留出尾部计算时间
3. 若这个 guard 太小，下一组会过早重启，覆盖或打乱上一组 head 的结果

这段逻辑就是历史上把 runtime 从 `token31` 卡死往后推过去的关键修正之一。

后续除非非常清楚后果，否则不要轻易动它。

#### `DMCUPlusFP32` 内部做了什么

它的内部逻辑可以概括成：

1. 把每拍的 2 个 Q / 2 个 K 收集到 `qVec` / `kVec`
2. 写入：
   - `qCache`
   - `kCache`
3. 等一个 query 所需向量收齐后，进入 `st_compute`
4. 用 32 个 INT8 乘法器和加法树做分块乘加
5. 累加到 `acc`
6. 每个 key 位置的结果写到 `res_cache`
7. 当前行全部完成后，再统一转换成 FP32 行输出

其中很关键的是：

1. `qCache` 深度按 query/token 组织
2. `kCache` 深度按历史 K 展开组织
3. 输出有效信号 `resIntValid` 要等到整行最后一个 key 位置写完

#### 调试 DM1 的正确方法

建议先看“拍数和窗口”，再看数值。

优先看：

1. `LoadUnit` 的 `vector_cnt / batch_cnt`
2. `decode_compute_cycles`
3. `qkVecValid`
4. `state == st_compute` 是否按预期持续
5. `acc_valid`
6. `resIntValid`

如果是“少一半拍”这类现象，通常优先怀疑 `LoadUnit` 窗口限制，而不是乘法器本体。

---

### 10.6 `SoftmaxPipFP32`：当前 single-query 路径是直通，不再走内部 data mem

代码入口：

- `src/main/scala/Softmax/TopFP32.scala`

#### 作用

`SoftmaxPipFP32` 负责把一整行 logits 变成一整行 probability。

#### 当前 single-query 的真实行为

这是当前最容易讲错的一点。

在 `isSingleQuery` 下，`SoftmaxPipFP32` 会做这些事：

1. **禁用内部 `memInst` 写入**
   - `memInst.io.w_valid := false`
2. `cuInst.io.data_in` 直接取 `io.data_in`
3. `cuInst.io.data_in_w` 直接取 `Fill(V, 1)`
4. `io.data_ready := io.res_ready`
5. `io.res_st := io.data_in_st`

这意味着：

1. single-query softmax 当前不是“先把整行写进内部 mem，再读出处理”
2. 而是 **直接消费上游提供的完整 FP32 行**
3. mask 权重大部分情况下已经通过上游 future-mask 和 wrapper prefix 语义折叠掉了

#### full-seq 当前如何使用 Softmax

结合 `Attention.scala` 的连接，当前 full-seq 的 softmax 语义是：

1. DM1 输出一整行 FP32 logits
2. 上游先把未来位置处理成负无穷近似值
3. softmax 在 single-query 模式下直接接收这行数据

因此现在再去把 softmax 当成“必须依赖独立 mask SRAM 的模块”来理解，很容易走偏。

#### 调试优先级

1. 看 DM1 给 softmax 的行是否完整
2. 看 `io.data_in_st`
3. 看 single-query 下 `io.data_ready`
4. 看输出行拍数是否完整

---

### 10.7 `VCache`：把每拍 2 个 V 元素收集成完整 64 维向量

代码入口：

- `src/main/scala/ResMEM/PipRes.scala`
- `src/main/scala/ResMEM/LSU.scala`
- `src/main/scala/ResMEM/Mem.scala`

#### 作用

`VCache` 的工作不是算数，而是：

1. 接收 `QKVLinear` 输出中的 V 分量
2. 按 token / head 顺序写入本地 `DataMem`
3. 在需要时把每拍 2 元素的 V 数据重新拼成完整 `64-dim` 向量
4. 按 `DM2` 需要的顺序回放

#### 内部结构

1. `DataMem(depth, width, 3)`
2. `LSU`

其中 `DataMem(..., 3)` 表示 3 bank 结构，用来允许：

1. 一边写
2. 一边读
3. 另一 bank 保持 full 或待切换

#### `ResMEM.DataMem` 当前的一个关键保护

它的 `w_ready` 不是简单看 `full_cnt < num`，而是：

```text
w_ready := (full_cnt + buzy_cnt) < num
```

原因是：

1. 3-bank 结构下，“正在写”的 bank 也不能算可用 bank
2. 如果只看 full bank 数，会错误地认为还有空 bank
3. 结果就是 bank 冲突或旧数据重放

#### `LSU` 的真实职责

`LSU` 负责：

1. 逐拍读取每个 V 向量的 32 个 2-lane 切片
2. 收集成一个完整 64 维向量
3. 等下游真正消费后再切到下一向量

它的状态是：

1. `idle`
2. `buzy`
3. `hold`

当前实现中的一个关键细节是：

1. 读完一个完整向量后会先进 `hold`
2. 等 `io.data_out_ready`
3. 然后再回 `idle`
4. **不会直接 `hold -> buzy`**

代码注释里已经说明原因：

1. 需要插一个 idle bubble
2. 给 DataMem full/r_ptr 更新留时间
3. 否则下一个 head 边界可能会重放上一个 head 的 `addr0` 切片

这同样是当前 full-seq 稳定性的一个关键现实保护。

#### 地址与输出

`LSU` 输出：

1. `data_out`：完整 64 维 V 向量
2. `data_out_addr`：token / batch 地址
3. `data_out_start`
4. `data_out_last`

也就是说，`VCache` 对 DM2 来说看到的是：

- 一次一个完整 head 的 `V[0:63]`

#### 调试优先级

1. 先数 VCache 写入拍数
2. 再数拼完后的 64-dim 输出次数
3. 再看 head 边界是否会重放旧 `addr0` 切片
4. 再看 `res_valid / res_last / res_addr`

---

### 10.8 `DM2Quant`：概率行与 V 向量的配对乘加

代码入口：

- `src/main/scala/DM2/TopQuant.scala`
- `src/main/scala/DM2/LoadU.scala`

#### 作用

`DM2Quant` 完成：

```text
Softmax probs (FP32 -> quantized 8bit) × V(INT8) -> attention output(INT8)
```

#### 内部结构

1. `Fp32QuantizeToUInt8Vec(MAX_SEQLEN)`：量化 ctx
2. `vmemInst`：缓存 V
3. `ctxmemInst`：缓存量化后的 ctx 行
4. `loaduInst`
5. `dmInst`
6. `suInst`

#### 当前 DM2 的核心难点

不是算术本身，而是：

1. `ctx` 和 `v` 是两条独立输入流
2. 二者必须在 **同一 token / 同一 head / 同一窗口** 上配对
3. decode/single-query 下尤其容易出现一条路先走一步

#### `loaduInst` 的状态

`DM2/LoadU.scala` 的状态机有两层：

1. 外层：
   - `idle`
   - `buzy`

2. 内层：
   - `stc_vcache`
   - `stc_getv`
   - `stc_waitctx`
   - `stc_c`

#### 当前 decode 配对保护

代码里有一个很重要的信号：

```text
decodePairReady = io.data_in_v_ready && io.data_in_ctx_ready
```

以及：

```text
vIssue = ... decodePairReady
ctxIssue = is_waitctx && io.data_in_ctx_ready
```

含义是：

1. 在 decode 下，不允许 V 路先独自往前冲
2. 必须保证 ctx 路也能跟上
3. 否则 V 会比 ctx 领先一个 batch，后面整体配对全部错位

#### 当前状态机还有一个关键现实修正

在 `stc_c` 结束且 decode 一个 batch 完成后，代码显式回到：

```text
stc_vcache
```

而不是走一个更“优雅”的组合跳转。

原因是：

1. 如果直接借组合路径复用当前 busy/valid 输入
2. 有机会跳过下一 token 的 V fetch
3. 于是 DM2 会拿上一轮残留 V 或干脆少一组 V

这同样是历史上修 runtime 时留下的关键保护。

#### `res_st` 的来源

`DM2Quant` 的输出 `res_st` 不是内部 compute 单元自己产生的，而是：

```text
io.res_st := loaduInst.io.data_out_start
```

也就是说，它跟 load / 配对窗口启动语义直接绑定。

#### 调试优先级

当 attention 看起来出错时，DM2 优先看：

1. `data_in_ctx_valid` 与 `data_in_v_valid` 拍数是否对齐
2. `data_in_ctx_ready` 与 `data_in_v_ready`
3. `ctxmem` / `vmem` 写入是否完整
4. `loaduInst` 的状态是否卡在 `waitctx`
5. `res_addr` 是否按期望递增

---

### 10.9 `OutLinearFP32`：先收齐 12 个 head，再做 768 -> 768 FP32 输出投影

代码入口：

- `src/main/scala/OutLinear/OutLinearFP32.scala`

#### 作用

Attention 的 `DM2` 输出给出来的是：

- 每次一个完整 head 的 `64-dim INT8`

但输出投影 `W_o` 需要的输入是：

- 整个 token 的 `768-dim INT8`

所以 `OutLinearFP32` 的第一步不是 GEMM，而是：

1. 把 12 个 head 全收齐
2. 按 hidden size 顺序重新拼成完整 token
3. 再写入自己的本地 `DataMem`
4. 再执行 `768 -> 768` 的 linear

#### 内部结构

1. `head_buffer(token)(head)`
2. `DataMem`
3. `LoadUnit`
4. `CUFP32`
5. `StoreUnitFP32`
6. `LoadWeight`
7. `bias_mem`

#### 状态机

1. `idle`
2. `collecting`
3. `feeding`

#### `collecting` 阶段

当 `io.data_in_valid && !is_feeding` 时：

1. 根据 `token_addr`
2. 把当前 head 的 `512-bit` 数据写入 `head_buffer(token_addr)(head_cnt)`

`io.data_in_last` 表示当前 head 的最后一拍。

当：

1. 最后一个 head 也到齐
2. 就转入 `feeding`

#### `feeding` 阶段

`feeding` 的动作是：

1. 从 `head_buffer(feed_token_cnt)` 拿出当前 token 的 12 个 head
2. 拼成完整 `768-dim` 向量
3. 再切成 64 个 `12-lane` chunk
4. 一拍拍写进本地 `DataMem`

写地址：

```text
mem_write_addr = feed_token_cnt * ROWBLOCK + feed_chunk_cnt
```

#### 然后才是常规 linear

在把完整 token 喂进 `DataMem` 后，后面才走：

1. `LoadUnit`
2. `CUFP32`
3. `StoreUnitFP32`
4. bias add

最终输出：

- 12 lane FP32 packed

#### 为什么 `OutLinear` 不是 attention 的简单后级

因为它承担了一个非常关键的格式转换：

1. Attention 输出是按 head 组织的 64 维向量
2. 输出投影要的是拼回 768 hidden 向量

如果这里的 head 收集和重排错了，后面看起来像 `ResAdd` 或 `LN2` 的错误，根因其实可能在 `OutLinear`。

---

### 10.10 `ResAddFP32`：把原始输入缓存起来，按 OutLinear 输出地址配对相加

代码入口：

- `src/main/scala/ResAdd/ResAddFP32.scala`

#### 作用

`ResAddFP32` 实现 attention 后的第一条残差：

```text
orig_in (FP32) + out_proj (FP32)
```

#### 当前实现方式

它不是双输入同拍相加，而是：

1. 原始输入 `orig_in` 先写进本地 `mem`
2. 当 `dm2_in`（其实现在已经是 out projection 输出）到来时
3. 用 `dm2_in_addr` 作为读地址从 `mem` 里取对应 beat
4. 再做 `Fp32VecAdd`

#### 为什么顶层要把原始输入打一拍

`Top.scala` 里连接是：

```text
resadd.io.orig_in      := RegNext(io.data_in)
resadd.io.orig_in_st   := RegNext(ln_addr_gen.io.data_st)
resadd.io.orig_in_addr := RegNext(ln_addr_gen.io.mem_addr(...))
resadd.io.orig_in_valid:= RegNext(ln_addr_gen.io.data_valid)
resadd.io.orig_in_last := RegNext(ln_addr_gen.io.data_last)
```

这表示：

1. residual 支路不是直接裸接原始输入
2. 而是显式打一拍与地址/控制对齐

#### 状态机

`ResAddFP32` 只有两个状态：

1. `idle`
2. `reading`

但它的本质是一个“读写配对器”而不是普通寄存器级。

#### 当前实现最重要的事实

`orig_ready` 和 `dm2_ready` 是两种不同的 ready：

1. `orig_ready` 表示 residual cache 还能不能继续写原始输入
2. `dm2_ready` 表示当前是否能拿 `dm2_in_addr` 去读出对应原始 beat 并完成相加

如果上游没有把 `orig_ready` 纳入输入共享 ready，最容易发生 silent data loss。

这也是顶层 `input_adapter_ready` 必须共享的根本原因。

---

### 10.11 `LayerNorm2`：实现上和 `LN1` 同类，但问题经常来自前级

代码入口：

- 仍然是 `src/main/scala/LayerNormQ/LayerNormQ.scala`

#### 作用

`LN2` 的输入是：

- `ResAdd1` 的 FP32 输出

输出是：

- `FFNUp` 所需的 INT8 激活

#### 当前调试上要记住的一点

`LN2` 出问题时，不要默认是 `LayerNormQ` 本体坏了。

历史上很多看起来像 `LN2 var=x`、`LN2 输出 NaN` 的问题，本质都是：

1. `ResAdd1` residual cache 没写完整
2. `OutLinear` 地址错位
3. `ResAdd1` 读到了未初始化 beat

然后在 LN 里被放大成明显异常。

所以查 LN2 时通常要倒着回到：

1. `ResAdd`
2. `OutLinear`
3. 原始 residual 支路

---

### 10.12 `FFNUp`：W8A8B8O8 + ReLU，输出仍然是 INT8

代码入口：

- `src/main/scala/FFNUp/FFNUp.scala`

#### 作用

`FFNUp` 完成：

```text
768 -> 3072
```

并且在本级内完成：

1. bias 融合
2. 量化
3. ReLU

#### 内部结构

和 `QKVLinear` 在骨架上很像：

1. `DataMem`
2. `LoadUnit`
3. `CUQuant`
4. `StoreUnit`
5. `LoadWeight`
6. `bias_mem`

#### 输出处理

当前 `FFNUp` 在 `su_inst` 输出后，会对每个 lane 做：

1. `INT32 -> FP32`
2. 乘 `out_inv_scale`
3. bias(INT8) -> FP32
4. 乘 `bias_scale`
5. 相加
6. `Fp32ToSInt`
7. INT8 饱和裁剪
8. ReLU（负数置零）

然后输出：

- 12 lane INT8 packed

这就是为什么当前 `FFNUp` 虽然内部有 FP32 epilogue 过程，但系统级上仍属于 `INT8 -> INT8` 模块。

#### 调试优先级

1. 看输入是否已是正确量化后的 LN2 输出
2. 看 `out_inv_scale` / `bias_scale`
3. 看 ReLU 前后值分布
4. 看 saturate 是否过多

---

### 10.13 `FFNDownFP32`：把 3072 维 INT8 激活投影回 768 维 FP32

代码入口：

- `src/main/scala/FFNDown/FFNDownFP32.scala`

#### 作用

`FFNDownFP32` 完成：

```text
3072 -> 768
```

输入是 `INT8`，输出是 `FP32`。

#### 内部结构

1. `DataMem`
2. `LoadUnit`
3. `CUFP32`
4. `StoreUnitFP32`
5. `LoadWeight`
6. `bias_mem`

#### bias 处理

这一级 bias 不是 INT8，而是：

- `FP32_PACK_WIDTH`

最后通过：

```text
bias_add = Fp32VecAdd(su_out, bias_mem(...))
```

完成最终输出。

因此这里的调试要点是：

1. GEMM 本体
2. `out_scale`
3. bias add

三者要分开看。

#### 当前在最终 mismatch 中的位置

因为 `FFNDown` 输出直接进入最终 `ResAdd2`，所以：

- 一旦最终 top mismatch
- `FFNDown` 通常是很靠前的回溯节点之一

---

### 10.14 `ResAdd2FP32`：最终输出前的第二条残差

代码入口：

- `src/main/scala/ResAdd2/ResAdd2FP32.scala`

#### 作用

`ResAdd2FP32` 完成：

```text
s7_in (来自 ResAdd1 输出) + ffn_in (来自 FFNDown 输出)
```

#### 实现方式

和 `ResAddFP32` 对称：

1. `s7_in` 先写入本地 `mem`
2. 当 `ffn_in` 到来时，以 `ffn_in_addr` 为读地址取出对应 `s7` beat
3. 再做 `Fp32VecAdd`

#### 为什么 `ResAdd1` 输出要同时喂两处

`ResAdd1` 的输出有两条用途：

1. 一路送 `LN2`
2. 一路写进 `ResAdd2` 作为第二条残差支路

所以顶层才会有：

```text
resadd.io.res_ready = layernorm2.io.data_ready && resadd2.io.s7_ready
```

这不是“保守一些也没坏处”的写法，而是功能正确性必需。

#### 调试意义

最终 full-seq 比对的就是这一层的输出。

但要记住：

- `ResAdd2` 是最终收敛点
- 不是默认根因点

如果这里只有数值不对，通常要往前拆成：

1. `s7_in` 对不对
2. `ffn_in` 对不对
3. 地址配对对不对

---

## 11. 当前运行时最关键的“工程性保护逻辑”

下面这些不是理论上的优雅设计，而是当前代码能稳定跑起来的关键现实条件。

### 11.1 输入共享 ready

```text
input_adapter_ready = layernorm.io.data_ready && resadd.io.orig_ready
```

不能随便拆开。

### 11.2 `Softmax -> DM2(ctx)` 队列

`ctxToDm2Q` 不能轻易拿掉。它用来修正 ctx 路背压和配对问题。

### 11.3 `VCache -> DM2(v)` 队列

`vToDm2Q` 用来吸收 V 路 burst，也不能当成无关优化。

### 11.4 DM1 single-query decode guard

`DM/LoadU.scala` 里的：

- `decode_pipeline_guard`
- `decode_compute_cycles`

是防止下一组 head 过早重启的关键保护。

### 11.5 VCache 的 idle bubble

`ResMEM/LSU.scala` 里读完一个完整向量后会先进入 `hold -> idle`，再开始下一向量。

这个空泡是为了防止 head 边界重放旧 `addr0` 切片。

### 11.6 DM2 decode 显式回 `stc_vcache`

`DM2/LoadU.scala` 在 decode 一个 batch 完成后显式回到 `stc_vcache`，避免下一 token 的 V fetch 被跳过。

### 11.7 `ResAdd` 输出的双路 ready

`ResAdd` 输出既受 `LN2` 也受 `ResAdd2` 制约，这也是必须共享的。

---

## 12. full-seq 验证入口和结果比对

### 12.1 Python 入口

常用 full-seq 入口在：

- `prepare_9p_fullseq_case()`
- `validate_9p_fullseq()`
- `validate_9p_fullseq_vcs()`

其中当前主要使用的是：

- `validate_9p_fullseq_vcs()`

它会编译：

1. `generated/Top.sv`
2. `verification/rtl/NinePSystemTop.sv`
3. `testbench/vcs/ninepsystemtop_tb.sv`

然后运行：

```text
./simv +window_dir=<out_dir> -l run.log
```

### 12.2 testbench 最终比对什么

系统最终比对的是：

1. `io_res`
2. `io_res_addr`
3. `io_res_valid`
4. `io_res_last`

并按：

- beat
- lane

粒度与 `golden.u32.bin` 进行比较。

因此 full-seq mismatch 总能落到一个明确的位置：

1. 第几个 beat
2. 第几个 lane
3. observed / expected

这个点就是后续逐级回溯的锚点。

### 12.3 当前已知状态

截至本次文档更新：

1. full-seq 已能跑完 `token911`
2. 系统输出 beat 数已达到 `58368`
3. 主问题已从 runtime 卡死收敛到数值 mismatch

这说明：

1. 系统级调度已经基本打通
2. attention 长序列运行链路已经基本可用
3. 后续调试主线是“真实数据对齐”

---

## 13. 后续调试时的推荐回溯顺序

现在的系统已经能跑完 full-seq，所以调试思路要改。

### 13.1 如果是最终结果 mismatch

建议按这个顺序回溯：

1. `Top.io.res`
2. `ResAdd2`
   - `s7_in`
   - `ffn_in`
3. `FFNDown`
4. `FFNUp`
5. `LN2`
6. `ResAdd1`
7. `OutLinear`
8. `Attention`
9. `QKVLinear`
10. `LN1`

### 13.2 如果是 attention 区域 mismatch

建议按这个顺序查：

1. `DM2` 的 `ctx/v` 拍数是否一致
2. `VCache` 是否在 head 边界重放旧切片
3. `Softmax` 输入是否已经正确 future-mask
4. `DM1` 是否输出完整行
5. `QKV` 是否按正确 head 重排

### 13.3 如果是 runtime 卡住

当前历史经验表明优先看：

1. 哪一级 `valid` 停了
2. 哪一级 `ready` 拉低了
3. 是单路 backpressure，还是两路配对等待
4. 是窗口大小不够，还是地址/状态机切换少了一拍

### 13.4 如果看到 `x/NaN`

默认先怀疑：

1. residual cache 没写满
2. 某条分叉没有共享 ready，导致 silent beat drop
3. 读到了未初始化地址

而不是先怀疑浮点运算单元。

---

## 14. 文件地图：后续调试最该先看哪些文件

### 14.1 总入口

1. `src/main/scala/Top.scala`
2. `verification/rtl/NinePSystemTop.sv`
3. `scripts/verification/opt125m_e2e.py`

### 14.2 前端主链

1. `src/main/scala/TempAdapter/LNAddrGen.scala`
2. `src/main/scala/LayerNormQ/LayerNormQ.scala`
3. `src/main/scala/QKVLinear/QKVLinear.scala`

### 14.3 Attention

1. `src/main/scala/Attention.scala`
2. `src/main/scala/DM/DMFP32.scala`
3. `src/main/scala/DM/LoadU.scala`
4. `src/main/scala/Softmax/TopFP32.scala`
5. `src/main/scala/ResMEM/PipRes.scala`
6. `src/main/scala/ResMEM/LSU.scala`
7. `src/main/scala/DM2/TopQuant.scala`
8. `src/main/scala/DM2/LoadU.scala`

### 14.4 后端主链

1. `src/main/scala/OutLinear/OutLinearFP32.scala`
2. `src/main/scala/ResAdd/ResAddFP32.scala`
3. `src/main/scala/FFNUp/FFNUp.scala`
4. `src/main/scala/FFNDown/FFNDownFP32.scala`
5. `src/main/scala/ResAdd2/ResAdd2FP32.scala`

### 14.5 full-seq 工具与环境

1. `scripts/verification/opt125m_e2e.py`
2. `verification/rtl/NinePSystemTop.sv`
3. `testbench/vcs/ninepsystemtop_tb.sv`
4. `verification/cases/opt125m_9p_fullseq/`

---

## 15. 最后再强调一遍：后续千万别再按旧脑图理解这个工程

当前工程最容易因为“沿用旧理解”而出错的地方有四个：

1. **不是所有模块都跑 912**
   - 只有 attention 长序列子系统真正看 912 历史

2. **Softmax 当前 single-query 不是传统 mem-based 跑法**
   - 它更接近直接消费一整行 logits

3. **很多关键 bug 不是算子 bug，而是节奏 / 配对 / ready bug**
   - 特别是 `DM1 LoadU`
   - `VCache LSU`
   - `DM2 LoadU`
   - `ResAdd` 共享 ready

4. **最终 mismatch 不代表最终一级有 bug**
   - `ResAdd2` 只是最终汇合点
   - 真正根因常常在更早的量化边界或地址配对

如果后面继续调试，请优先按本文描述的“当前事实”来定位问题，而不是回到早期的简化版架构图。
