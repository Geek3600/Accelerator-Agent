# OPT Accelerator Architecture Hyperparameters&#x20;

本文基于当前 `src/main/scala` Chisel 代码重新整理加速器的主要架构参数，并给出它们到三个硬件目标的近似映射关系：

- `latency_cycles`：运行时延 / 吞吐相关的周期数；
- `DSP_total`：DSP48 / FP IP / MAC 资源的一阶规模；
- `storage_bits`：片上逻辑存储量，以及按 BRAM/URAM 粒度取整后的物理存储量。

结论分三类：

- **代码明确**：直接来自 `Param.scala`、`Top.scala`、`Attention.scala` 或模块实例化。
- **代码推导**：由循环计数、bank 组织、queue 深度、memory packing 推导。
- **需综合拟合**：Vivado 对 DSP、BRAM、URAM、LUT、FF 的最终映射受 IP 后端、约束和综合优化影响，公式只能作为一阶模型。

## 1. 当前流水线结构

当前 `Top.scala` 中的主数据流是一个 operator-level spatial pipeline：

```text
FP32 input
  -> LNAddrGen
  -> LayerNormQ
  -> QKVLinear
  -> Attention:
       DM1FP32
       SoftmaxPipFP32
       VCache
       DM2Quant
  -> OutLinearFP32
  -> ResAddFP32
  -> LayerNormQ
  -> FFNUp
  -> FFNDownFP32
  -> ResAdd2FP32
  -> FP32 output
```

当前代码已经明显偏向短序列 single-query / short-seq runtime：

- `DM/DM2/Softmax/TempAdapter` 活动路径的 `MAX_SEQLEN/SEQ_LEN/TILE_SEQLEN` 均为 `16`；
- `QuantCommon.Precision.SOFTMAX_LEN = 26` 当前只是打包常量定义，源码搜索未发现被活动实例化路径使用；
- 历史文档中的 `26/912` 目标要和当前实际编译参数区分。`S=912` 不是只改一个 `MAX_SEQLEN`，需要配套 tiled attention、DDR history 和 wrapper 调度重构。

## 2. 主要参数总表

| 参数类别                 |                符号 |                       当前值 | 源码位置                               | 建议搜索范围                                 | 主要影响                                   |
| -------------------- | ----------------: | ------------------------: | ---------------------------------- | -------------------------------------- | -------------------------------------- |
| 隐藏维度                 |               `H` |                     `768` | `QKV/Out/FFN* Param`               | OPT-125M 固定；换模型才变                      | 线性层矩阵尺寸、buffer 深度                      |
| FFN 维度               |               `F` |                    `3072` | `FFNUp/FFNDown Param`              | 通常 `4H`                                | FFNUp/FFNDown 权重和时延                    |
| attention head 数     |               `A` |                      `12` | `HEAD_NUM`, `SINGLE_QUERY_BATCH`   | OPT-125M 固定                            | QKV 输出、head 拼接、single-query batch      |
| head 维度              |              `Dh` |                      `64` | `HEAD_DIM/HEAD_VECNUM`             | 通常固定                                   | DM1/DM2 点积长度                           |
| 基础 lane 数            |           `LANES` |                      `12` | `QuantCommon.Precision`            | `{8,12,16,24}`                         | FP32/INT8 打包宽度、LN/Res/Linear 吞吐        |
| 线性输入并行度              |           `R=ROW` |                      `12` | 四个 linear `Param.scala`            | `{8,12,16,24}`，最好整除 `768/3072`         | 线性 K 维循环约按 `1/R` 降低；DSP 约按 `R*C` 增加    |
| 线性输出并行度              |           `C=COL` |                      `36` | 四个 linear `Param.scala`            | `{24,36,48,72}`，注意 `C*8/72` 取整         | 线性 O 维循环约按 `1/C` 降低；DSP/权重读宽上升         |
| 数据位宽                 |               `W` | INT8/UINT8=`8`, FP32=`32` | `QuantCommon.Precision`            | INT8 是当前主线；INT4/FP16 需要重构              | DSP、存储、量化路径、FP IP                      |
| token/window 上限      |               `B` |                      `16` | linear/LN/Res params               | `{1,4,8,16,32}`                        | 数据 buffer、psum buffer、prefill frame 长度 |
| attention context 长度 |               `S` |                      `16` | `DM/DM2/Softmax/TempAdapter Param` | 当前 core-compatible `{16,26}`；大于 26 需重构 | attention 时延和 KV/ctx 存储线性增长            |
| Q/K/V 输入打包           |     `LOAD_VECNUM` |                       `2` | `DM.Param`, `TempAdapter.Param`    | `{1,2,4,8}`，需整除 `Dh=64`                | 每个 head 收集周期 `Dh/LOAD_VECNUM`          |
| DM1 QK 并行乘法器         |      `Pqk=MULNUM` |                      `32` | `DM.Param`                         | `{8,16,32,64}`                         | QK 点积周期 `S*ceil(Dh/Pqk)`；DSP 线性增加      |
| DM2/Softmax tile 并行  | `Ppv=TILE_SEQLEN` |                      `16` | `DM2.Param`, `Softmax.Param`       | `{8,16,32}`；当前 `S=16` 时 `>16` 无收益      | PV/softmax tile 数下降；DSP/queue width 上升 |
| 权重 bank              |              `Bw` |                       `2` | `WeightMem` active/shadow          | `{1,2}`                                | 权重存储线性增长；`2` 支持后台 preload              |
| 线性 data bank         |       `Bd_linear` |                       `2` | `QKV/Out/FFN* DataMem`             | `{2,3,4}`                              | 缓解读写重叠和 backpressure；存储线性增加            |
| ResAdd bank          |            `Bres` |                       `3` | `ResAdd/ResAdd2 DataMem`           | `{2,3,4}`                              | residual path 反压弹性；存储线性增加              |
| VCache bank          |              `Bv` |                       `4` | `ResMEM.VCache` / `DataMem(...,4)` | `{2,3,4}`                              | V 路 burst 吸收能力；存储线性增加                  |
| Attention queue 深度   |         `Qctx/Qv` |                  `256/64` | `Attention.scala`                  | `Qctx={64,128,256}`, `Qv={32,64,128}`  | 吸收 Softmax/VCache 与 DM2 速率差；BRAM/FF 增加 |
| Top queue 深度         |            `Qtop` |             `2,12,1024` 等 | `Top.scala`                        | `{2,16,64,128,1024}`                   | 跨 stage 解耦和反压；深队列可能推 BRAM              |

## 3. 四个主线性层

四个主线性层 `QKVLinear / OutLinear / FFNUp / FFNDown` 使用同构计算阵列：

```text
R = ROW = 12
C = COL = 36
DATAW = 8
每层 MAC 级数 = R * C = 432
四层合计 MAC 级数 = 4 * 432 = 1728
```

每个 `CU` 里实例化 `COL=36` 条 `SignedMacChain32(ROW=12)`。如果 Vivado 能稳定把每个 int8 MAC 级映射到 DSP cascade，线性层 DSP 的一阶理论量级就是 `sum(R*C)`。实际 DSP 会叠加 LayerNorm、Softmax、DM1、DM2、量化 epilogue 和 FP32 add/mul/div。

### 3.1 当前线性层尺寸与周期

定义：

```text
RB_i = ceil(K_i / R)
CB_i = ceil(O_i / C)
tile_steps_i = RB_i * CB_i
valid_output_beats_i = ceil(O_i / R)
physical_drain_slots_i = CB_i * ceil(C / R)
```

| Stage     | `K_i` 输入维 | `O_i` 输出维 | `RB_i` | `CB_i` | `tile_steps/token` | valid output beats | physical drain slots |
| --------- | --------: | --------: | -----: | -----: | -----------------: | -----------------: | -------------------: |
| QKVLinear |       768 |      2304 |     64 |     64 |               4096 |                192 |                  192 |
| OutLinear |       768 |       768 |     64 |     22 |               1408 |                 64 |                   66 |
| FFNUp     |       768 |      3072 |     64 |     86 |               5504 |                256 |                  258 |
| FFNDown   |      3072 |       768 |    256 |     22 |               5632 |                 64 |                   66 |

说明：

- `tile_steps/token` 是主计算循环的一阶周期数，真实时延还要加 input staging、MAC chain latency、psum 输出、epilogue、store/drain。
- `physical_drain_slots` 可能大于 `valid_output_beats`，因为 `COL=36`、`ROW=12` 时每个 output col block 分 3 个 12-lane beat 输出；最后一个 col block 可能包含 padding。
- 当前 `12x36` 阵列下，单 token 线性层瓶颈通常是 `FFNDown/FFNUp`，不是 `QKV/Out`。

### 3.2 权重存储组织

四个线性层的 `WeightMem` 使用 active/shadow 双 bank，每个 bank 内按 `ROW` 行和 72-bit URAM slice 组织：

```text
TILE_DEPTH_i = RB_i * CB_i
NUM_SLICES = ceil(C * W / 72)
URAM_weight_i = Bw * R * NUM_SLICES * ceil(TILE_DEPTH_i / 4096)
logical_weight_bits_i = Bw * (R * RB_i * CB_i) * (C * W)
physical_weight_bits_i ~= URAM_weight_i * 4096 * 72
```

当前 `Bw=2, R=12, C=36, W=8`，所以 `NUM_SLICES=ceil(288/72)=4`。

| Stage     | `WMEM_DEPTH` | `WMEM_WIDTH` |    logical bits | logical MiB | physical URAM | physical MiB approx |
| --------- | -----------: | -----------: | --------------: | ----------: | ------------: | ------------------: |
| QKVLinear |       49,152 |          288 |      28,311,552 |       3.375 |            96 |               3.375 |
| OutLinear |       16,896 |          288 |       9,732,096 |       1.160 |            96 |               3.375 |
| FFNUp     |       66,048 |          288 |      38,043,648 |       4.535 |           192 |               6.750 |
| FFNDown   |       67,584 |          288 |      38,928,384 |       4.641 |           192 |               6.750 |
| **Total** |            - |            - | **115,015,680** |  **13.711** |       **576** |          **20.250** |

注意：OutLinear 的逻辑权重只有约 1.16 MiB，但物理 URAM 仍为 96 个，因为 `TILE_DEPTH=1408` 被每个 URAM slice 的 4096 深度粒度取整。架构搜索时不能只看逻辑 bit 数，必须看物理 memory primitive 取整。

### 3.3 线性层内部 buffer

当前四个线性层的输入 `DataMem` 都是双 buffer：

```text
linear_data_bits_i ~= Bd_linear * MEM_DEPTH * MEM_WIDTH
                  = 2 * 2048 * (R * W)
                  = 393,216 bits per linear stage
```

此外每个 `CU` 有两套 psum buffer：

```text
psum_bits_i ~= 2 * B * C * 32
            = 2 * 16 * 36 * 32
            = 36,864 bits per linear CU
```

`OutLinear` 还有 `head_buffer`：

```text
head_buffer_bits = B * A * Dh * W
                 = 16 * 12 * 64 * 8
                 = 98,304 bits
```

## 4. Attention / Softmax / KV 路径

### 4.1 当前参数

| 模块                       | 当前参数                                     | 一阶行为                                                  |
| ------------------------ | ---------------------------------------- | ----------------------------------------------------- |
| QKV -> Attention ingress | `LOAD_VECNUM=2`, `Dh=64`                 | 每个 head 的 Q/K/V 输入收集约 `Dh/LOAD_VECNUM = 32` beat      |
| DM1FP32                  | `Pqk=32`, `S=16`, `Dh=64`                | 每个 query/head 对所有 key 计算，核心循环约 `S * ceil(Dh/Pqk)`     |
| SoftmaxPipFP32           | `TILE_SEQLEN=16`, `SEQ_LEN=16`           | 当前单 tile；有 max/sum/reciprocal/normalize 状态机和 FP IP 延迟 |
| VCache                   | `DATAINNUM=2`, `DATAOUTNUM=64`, bank=`4` | V 从 2-lane 收集成 64-lane 输出                             |
| DM2Quant                 | `Ppv=TILE_SEQLEN=16`, `Dh=64`, `S=16`    | 对每个输出维度循环，单 tile PV reduction；输出 64-lane int8         |
| Attention queues         | `ctxToDm2Q=256`, `vToDm2Q=64`            | 吸收 Softmax/VCache 与 DM2 的速率不匹配                        |

### 4.2 Attention 时延模型

定义：

```text
S    = attention context 长度
Dh   = head_dim
Lv   = LOAD_VECNUM
Pqk  = DM1 MULNUM
Ppv  = TILE_SEQLEN
T    = ceil(S / Ppv)
```

DM1 single-query QK 一阶周期：

```text
L_DM1_collect ~= Dh / Lv
L_DM1_compute ~= S * ceil(Dh / Pqk)
L_DM1_emit    ~= T
L_DM1 ~= L_DM1_collect + L_DM1_compute + L_DM1_emit + L_dm1_pipe
```

当前 `S=16, Dh=64, Lv=2, Pqk=32`：

```text
L_DM1_collect ~= 32
L_DM1_compute ~= 16 * 2 = 32
```

Softmax 一阶周期：

```text
L_softmax ~= T * L_tile_collect
          + L_max_sum
          + L_recip_div
          + T * L_normalize
```

当前 `T=1`，所以主要由固定 FP32 reciprocal/div 和 normalize pipeline 决定；若 `S` 变大，`T=ceil(S/Ppv)` 会线性增加。

DM2 PV 一阶周期：

```text
L_DM2_vload ~= S
L_DM2_compute ~= Dh * ceil(S / Ppv)
L_DM2_quant ~= L_fixed_to_float + L_mul + L_float_to_fixed
L_DM2 ~= L_DM2_vload + L_DM2_compute + L_DM2_quant + L_dm2_pipe
```

当前 `S=16, Ppv=16, Dh=64`：

```text
L_DM2_compute ~= 64
```

如果 `S=912` 且 `Ppv=16`，则：

```text
ceil(912/16) = 57
L_DM2_compute ~= 64 * 57 = 3648 cycles per head/request
```

这说明长序列下 attention 会从非瓶颈变成主要瓶颈之一；不能只修改 `MAX_SEQLEN` 而不重构 DDR history/tile schedule。

### 4.3 Attention 存储模型

当前 DM1/DM2 内部仍保留小规模 history cache：

```text
DM1 kCache bits = A * S * Dh * W = 12 * 16 * 64 * 8 = 98,304
DM1 qCache bits = S * Dh * W = 16 * 64 * 8 = 8,192
DM2 vCache bits = A * S * Dh * W = 98,304
DM2 vBuf bits   = S * Dh * W = 8,192
```

如果未来把 `S` 扩到 912 且仍然把 K/V history 放片上：

```text
bits_KV ~= 2 * A * S * Dh * W
        = 2 * 12 * 912 * 64 * 8
        = 11,206,656 bits ~= 1.34 MiB
```

这还没有包括 softmax ctx queue、DDR staging、bank 取整和 wrapper buffer。

Attention Top 级 queue 当前约为：

```text
ctxToDm2Q bits ~= 256 * (TILE_SEQLEN*32 + st/addr/last)
              ~= 256 * (512 + metadata) ~= 134 Kbits

vToDm2Q bits ~= 64 * (Dh*8 + st/addr/last)
            ~= 64 * (512 + metadata) ~= 33 Kbits
```

## 5. LayerNorm / ResAdd / FP32 路径

### 5.1 LayerNormQ

关键参数：

```text
VECTOR = 768
LANE_NUM = 12
VECTOR_BEATS = 64
MEM_DEPTH = 2048
BATCHSIZE = 16
```

LayerNormQ 使用 12-lane FP32 add/mul/div/sqrt/quantization 结构，时延包含：

- 64 beat 输入统计；
- FP32 lane sum / square sum tree；
- mean / variance / sqrt / reciprocal；
- 64 beat apply + quantize 输出。

FP32 IP latency 由 `XilinxFpTargetConfig` 给出：

```text
AddLatency = 12
MulLatency = 9
DivLatency = 29
SqrtLatency = 29
FixedToFloatLatency = 7
FloatToFixedLatency = 7
```

因此 LayerNorm 的固定 pipeline latency 较大，但在当前 `S=16` 与线性层 `FFNUp/FFNDown` 相比，主吞吐瓶颈通常仍然在大矩阵线性层。

### 5.2 ResAdd / ResAdd2

ResAdd/ResAdd2 使用 12-lane FP32 vector add，主要参数：

```text
DATA_WIDTH = 12 * 32 = 384 bits
ResAdd.MEM_DEPTH = BATCHSIZE * (VECTOR / SUBVEC) = 16 * 64 = 1024
ResAdd2.MEM_DEPTH = 2048
Bres = 3 banks
```

存储估算：

```text
ResAdd residual bits  ~= 3 * 1024 * 384 = 1,179,648 bits
ResAdd2 residual bits ~= 3 * 2048 * 384 = 2,359,296 bits
```

计算时延主要由 FP32 add latency 决定：

```text
L_resadd ~= XilinxFpTargetConfig.AddLatency = 12 cycles + memory read alignment
```

## 6. Top 级队列和缓冲

当前 `Top.scala` 里的主要 queue：

| Queue          |                     深度 |            数据宽度近似 | 作用                           |
| -------------- | ---------------------: | ----------------: | ---------------------------- |
| `qkvToAttnQ`   |                      2 |  `48b + metadata` | 切断 QKV -> Attention 长路径      |
| `attnToOutQ`   | `OutParam.HEAD_NUM=12` | `512b + metadata` | Attention head 输出到 OutLinear |
| `outToResQ`    |   `RES_MEM_DEPTH=1024` | `384b + metadata` | OutLinear 到 ResAdd 的整帧缓冲     |
| `ffnUpToDownQ` |                      2 |  `96b + metadata` | FFNUp 到 FFNDown              |
| `ffnToRes2Q`   |   `RES_MEM_DEPTH=1024` | `384b + metadata` | FFNDown 到 ResAdd2            |

大队列 `outToResQ/ffnToRes2Q` 明显增加存储，但它们是之前 full-seq/top 集成中用于吸收早到数据和跨 stage 反压的重要结构。减小这些 queue 可以省 BRAM/FF，但可能重新暴露首拍丢失、早到数据覆盖或 ready/valid 死锁。

## 7. 三个目标指标的映射关系

### 7.1 时延 / cycles

对第 `i` 个线性层：

```text
RB_i = ceil(K_i / R)
CB_i = ceil(O_i / C)

L_linear_compute_i(N) ~= N * RB_i * CB_i
L_linear_drain_i(N)   ~= N * CB_i * ceil(C / R)
L_linear_i(N)         ~= L_linear_compute_i(N)
                         + L_linear_drain_i(N)
                         + L_mac_pipe(R)
                         + L_epilogue_i
                         + L_mem_queue_i
```

对流水化系统吞吐：

```text
II_pipeline ~= max_i(II_stage_i)
L_total(N_request) ~= L_fill + (N_request - 1) * II_pipeline
```

其中当前短序列 core 的 stage II 主要候选：

```text
II_QKV      ~= 4096
II_Out      ~= 1408
II_FFNUp    ~= 5504
II_FFNDown  ~= 5632
II_DM1      ~= S * ceil(Dh/Pqk)
II_DM2      ~= Dh * ceil(S/Ppv)
```

当前 `S=16` 时，线性 FFN 层通常是主瓶颈。若 `S` 增大，attention 项会线性上升。

### 7.2 DSP

线性层一阶 DSP 模型：

```text
DSP_linear ~= alpha_mac * sum_i(R_i * C_i)
```

当前：

```text
sum_i(R_i*C_i) = 4 * 12 * 36 = 1728
```

Attention 和 FP32 辅助路径：

```text
DSP_attention ~= alpha_qk * Pqk
                + alpha_pv * Ppv
                + alpha_softmax * Ppv

DSP_fp32 ~= beta_add * N_add
           + beta_mul * N_mul
           + beta_div * N_div
           + beta_sqrt * N_sqrt
           + beta_convert * N_convert

DSP_total ~= DSP_linear + DSP_attention + DSP_fp32 + DSP_fixed
```

更具体地说：

- `R*C` 增大通常直接增加 int8 MAC DSP 或 LUT 乘加规模；
- `Pqk` 增大直接增加 DM1 QK 乘法器；
- `Ppv/TILE_SEQLEN` 增大直接增加 DM2 PV 乘法器和 Softmax tile kernel/normalize lane；
- `LANES` 增大直接增加 LayerNorm、ResAdd、FFN epilogue 的 FP32 lane 数。

实际 `alpha/beta` 需要用 Vivado OOC 或整工程综合拟合。历史实现中全核 DSP 大致在 `~2.5k-2.7k` 量级，适合作为当前 `12x36` 附近的拟合锚点，而不是固定公式常数。

### 7.3 总存储量

逻辑存储一阶模型：

```text
storage_bits ~= sum_i(weight_bits_i)
              + sum_i(linear_data_bits_i)
              + sum_i(psum_bits_i)
              + bits_LN
              + bits_residual
              + bits_KV
              + bits_attention_queues
              + bits_top_queues
              + bits_regs

weight_bits_i      = Bw * R_i * ceil(K_i/R_i) * ceil(O_i/C_i) * C_i * W
linear_data_bits_i = Bd_linear * MEM_DEPTH_i * R_i * W
psum_bits_i        = 2 * B * C_i * 32
bits_KV            = 2 * A * S * Dh * W
```

权重 URAM 物理取整模型：

```text
URAM_weight_i = Bw * R_i * ceil(C_i*W/72) * ceil(ceil(K_i/R_i)*ceil(O_i/C_i)/4096)
```

BRAM/URAM/LUTRAM 选择还取决于 Vivado 推断、`SyncReadMem` 宽深、XPM wrapper 和约束。用于架构搜索时，建议同时记录：

```text
logical_bits
physical_URAM_estimate
physical_BRAM_estimate
Vivado reported URAM/BRAM/LUTRAM
```

## 8. 参数变化对三个指标的方向性影响

| 增大参数                  | `latency_cycles`                | `DSP_total`      | `storage_bits`                        | 主要风险                             |
| --------------------- | ------------------------------- | ---------------- | ------------------------------------- | -------------------------------- |
| `R`                   | 线性 `RB=ceil(K/R)` 降低，通常降时延      | 约按 `C*R` 上升      | data width、psum、权重组织受 `R` 影响；URAM 有取整 | fanout、route、DSP cascade 更难      |
| `C`                   | 线性 `CB=ceil(O/C)` 降低，通常降时延      | 约按 `R*C` 上升      | 权重读宽 `C*W` 上升；URAM 按 72b slice 取整     | `C/R` 非整数会增加 store/drain padding |
| `Pqk`                 | DM1 `ceil(Dh/Pqk)` 降低           | 线性上升             | 基本不影响大存储                              | `Pqk>Dh` 无收益，routing 增压          |
| `Ppv/TILE_SEQLEN`     | DM2/Softmax tile 数降低            | 线性上升             | ctx/v queue width、tile buffer 上升      | softmax reduction 和 FP lane 时序更难 |
| `S`                   | attention QK/PV/softmax 线性上升    | 并行度不变时 DSP 不变    | KV/ctx/cache/queue 容量线性上升             | 长序列需 DDR history/tiled schedule  |
| `Bw`                  | 可隐藏权重 preload，不降 compute cycles | 不变               | 权重存储线性上升                              | URAM 压力极大                        |
| `Bd/Bres/Bv`          | 降低 backpressure stall           | 不变               | buffer 存储线性上升                         | BRAM/FF 增加                       |
| queue depth           | 降低 burst 速率不匹配造成的 stall         | 不变               | queue bits 线性上升                       | 深队列可能变 BRAM，增加延迟                 |
| FP32 lane 数 / `LANES` | LN/Res/epilogue beat 数下降        | FP32 IP lane 数上升 | packed width 和 buffer width 上升        | FP IP、routing、control set 压力     |

## 9. 建议的搜索范围

当前 core-compatible 的第一阶段 sweep：

```text
R in {8, 12, 16, 24}
C in {24, 36, 48}
Pqk in {16, 32, 64}
Ppv in {8, 16, 32}
Bw in {1, 2}
Bd_linear in {2, 3}
Bres/Bv in {2, 3, 4}
Qctx in {64, 128, 256}
Qv in {32, 64, 128}
S in {16, 26}
```

不建议把 `S=128/256/512/912` 放进同一个简单参数 sweep。长序列需要单独建模：

```text
S_large in {128, 256, 512, 912}
requires:
  tiled attention schedule
  DDR-backed K/V history
  wrapper-side history fetch
  ctx/v stream pairing contract
  bandwidth model for DDR/AXI
```

## 10. 推荐的 Pareto 建模流程

对每个参数点，先由公式估计：

```text
latency_cycles_est
DSP_est
storage_bits_est
URAM_weight_est
```

再用 Vivado OOC/整工程报告拟合：

```text
DSP_report = a0 + a1*sum(R*C) + a2*Pqk + a3*Ppv + a4*LANES + residual
URAM_report ~= URAM_weight_est + URAM_other_est
BRAM_report ~= f(queue_bits, data_mem_bits, residual_bits)
latency_runtime = f(stage_II, stalls, DDR schedule, wrapper overhead)
```

最终比较时建议至少保留三类目标：

```text
minimize latency_cycles
minimize DSP_total
minimize total_storage_bits / URAM / BRAM
```

若用于上板实现，还必须附加约束：

```text
timing_WNS >= target
LUT/FF/CLB density below placement threshold
control-set and high-fanout nets acceptable
DDR/AXI bandwidth sufficient
```

## 11. 当前结论

当前实现点可以概括为：

```text
H=768, F=3072, A=12, Dh=64
R=12, C=36, W=8
B=16, S=16
Pqk=32, Ppv=16
Bw=2, Bd_linear=2, Bres=3, Bv=4
```

在这个点上：

- 线性层总 MAC 级数为 `1728`；
- 四个线性层逻辑权重约 `13.71 MiB`；
- 四个线性层权重物理估计约 `576 URAM`；
- 单 token 主计算 tile steps 为 `QKV=4096, Out=1408, FFNUp=5504, FFNDown=5632`；
- 当前短序列下 FFN 线性层是主要 compute 瓶颈；
- 如果扩到长序列，DM1/Softmax/DM2 的 `S` 线性项会快速变成主瓶颈，需要重新设计 attention history 数据流。

