# DAC 实验计划

实验必须证明 contract-preserving design closure 有用。性能重要，但主 claim 是 design closure productivity 和 robustness。

## 实验 A：End-to-End Design Closure

目标：证明 SpatialAccAgent 可以从 model/platform/precision specification 出发，生成 deployable accelerator artifacts，并通过分层验证。

| Task | 模型结构 | 变化点 | 目的 |
| --- | --- | --- | --- |
| T1 | OPT/GPT-2 block | LayerNorm + MHA + GELU/FFN | 最小 decoder-only baseline |
| T2 | LLaMA-like block | RMSNorm + RoPE + SwiGLU | 证明不是 GPT-only |
| T3 | Qwen-like block | GQA/KV-head + RoPE | 测试 KV-head/model-edge contracts |
| T4 | Quantized block | W8A8 到 W4A8 | 测试 numeric contracts |
| T5 | Platform variant | DDR width/bank/AXI window 变化 | 测试 deployment contracts |

最低可行集合：

- T1、T2、T3 是 DAC 故事必须做的。
- T4、T5 是时间允许时的强扩展。

每个 task 应报告：

- generated / modified Chisel modules；
- top-level connection；
- AXI/DDR wrapper；
- host/runtime scripts；
- stage/top/system verification scripts；
- real weights、activations、golden traces、DDR image；
- synthesis report；
- repair log。

## 实验 B：Ablation Study

目标：证明 SACG 和 contract-guided loop 确实有用。

| Ablation | 需要证明的结论 |
| --- | --- |
| No SACG | bug 更多、repair iterations 更多、system-level failure 更多 |
| No streaming contract | stream-order、missing-beat、deadlock 更容易逃逸 |
| No memory contract | DDR/AXI/runtime bug 增加 |
| No numeric contract | scale/rounding/zero-point mismatch 更难定位 |
| Single-agent baseline | 长上下文任务 success rate 更低，repair 更不稳定 |
| Free-form RTL generation | synthesizability、verifiability、QoR 更差 |
| No hierarchical verification | bug 逃到 system/board level，修复代价更高 |
| No evidence classifier | patch 更大，regression failure 更多 |

指标：

- success rate；
- average repair iterations；
- simulation 前抓到的 contract violations 数量；
- 逃到 top/system/board level 的 bugs 数量；
- human intervention count；
- wall-clock time；
- generated LOC vs. human LOC；
- patch size；
- regression pass rate。

## 实验 C：Fault Injection

目标：证明方法覆盖真实 failure space，而不是只靠 demo 跑通。

注入代表性错误：

- RoPE dimension offset error；
- GQA KV-head broadcast error；
- W4 scale stride error；
- stream tile order reversal；
- valid signal 少打一拍或错后一拍；
- FIFO depth 太小；
- residual bypass 接错；
- DDR base address offset error；
- AXI burst length error；
- output window size error；
- Chisel parameter mismatch；
- fanout-induced timing violation。

比较方法：

| Method | Detection rate | Localization accuracy | Repair success | Average iterations |
| --- | ---: | ---: | ---: | ---: |
| Single agent | TBD | TBD | TBD | TBD |
| Agent + tests only | TBD | TBD | TBD | TBD |
| SACG + checkers | TBD | TBD | TBD | TBD |
| Full SpatialAccAgent | TBD | TBD | TBD | TBD |

定义：

- Detection：系统能标出 failure 或 invariant violation。
- Localization：报告的 contract/node/edge 与注入 root cause 一致。
- Repair success：生成的 patch 通过要求的 regression。
- Average iterations：成功或超时前 classify/patch/regress loop 次数。

## 实验 D：QoR Sanity and Competitive Performance

目标：证明生成 accelerator 是真实、可部署、性能不离谱的。

报告：

- synthesis / implementation 后的 Fmax；
- LUT/FF/DSP/BRAM/URAM；
- stage/top/system latency；
- token/s 或 block/s throughput；
- DDR bandwidth efficiency；
- pipeline utilization 和 stage stall statistics；
- vendor report 或 board measurement 的 energy/power；
- end-to-end design time；
- automation rate。

定位：

```text
Performance is reported to demonstrate that the generated accelerators are deployable and competitive; the primary metric is design closure productivity, not peak accelerator performance.
```

除非设置严格公平，否则不要声称全面超过 Allo、StreamTensor、DFX、GPU baselines 或手工 FPGA LLM accelerators。

## 人类干预记录

每组实验都应记录：

- 哪些 artifact 是自动生成的；
- 哪些 artifact 是人工修改的；
- agent 修复了什么；
- checker 抓到了什么；
- 哪些 bug 逃到后续验证层级；
- 每次 repair 是否 minimal；
- regression 是否稳定。

这是避免被批评为 human-in-the-loop case study 的关键。
