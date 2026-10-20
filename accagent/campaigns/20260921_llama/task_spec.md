# LLaMA FPGA Spatial Accelerator Campaign

Design a complete FPGA-runnable spatial accelerator for the supplied LLaMA-family checkpoint and its complete Transformer-block workload. The model architecture, tensor shapes, layer count, sequence length, numeric policy, and checkpoint tensor names must be derived from the supplied model source and checkpoint; do not substitute another model or use fixed LLaMA dimensions.

Run the complete public Stage 0--7 workflow. Stage 4 must enumerate and measure the complete legal FPGA-effective DSE candidate universe. Every admitted candidate must materially alter generated RTL, Vivado IP configuration, XPM topology, or XDC; analytical estimates and LLM reasoning may prioritize measurements but cannot supply QoR values.

Target the supplied VU9P board sample project and retain its real compute-slot, AXI, DDR, weight-loader, double-buffer, and runtime behavior. Use W4A8 with signed INT4 learned matrix weights, INT8 activations, INT32 accumulators and bias, and integer DSP MACs. QK/PV use INT8 activation operands. Use integer/fixed-point normalization, activations, Softmax, RoPE, residual scaling and requantization; the elaborated W4A8 accelerator must not depend on floating-point IP. Retain physical XPM working caches and FIFOs, and preserve the actual DSP/XPM interfaces and timing in VCS. Derive widths, scales, shifts and packed images from the numeric policy and real checkpoint; never just rename a floating-point datapath.

QoR objective: measured end-to-end throughput should approach 200 token/s. There is no minimum achieved clock frequency requirement; maximize throughput within the discovered VU9P resource budgets and continue throughput-first DSE if the target is missed. LUT, FF, BRAM, URAM, and DSP usage must remain within the discovered target board resource budget. Report estimates separately from measured QoR and never claim target attainment without source-bound implementation results. Measure and report power, but do not impose a power limit.

Weight storage requirement: keep the complete multi-layer Transformer weight set in external DDR. On-chip XPM memories are bounded working caches, not a requirement to keep an entire layer resident. Derive the feasible cache or tile size from the target board memory budget and numeric policy. Use model-derived DDR address mapping, bounded current/next weight buffers, prefetch/computation overlap, safe buffer switching, activation ping-pong, and final writeback. If a full layer cannot fit, implement intra-layer tiled weight streaming while preserving the complete computation and operator/token overlap. Do not substitute smaller PE arrays, truncated weights, reduced precision, or full-sequence serialization for the missing memory architecture. DSE may explore cache/tile parameters only after the template, loader, and scheduling implementation actually supports them; a declared DDR region alone is not evidence that the kernel streams weights.

Use the established hierarchical real verification policy. For Layer 3, run the actual board AXI/DDR wrapper and complete all real runtime/weight loading for one Transformer layer. This board-bringup completion is sufficient to proceed to Stage 7; complete token output and final DDR writeback remain diagnostic evidence, not a prerequisite for Vivado implementation.


<!-- wide-refill-user-policy -->
当前用户约束：新生成加速器禁止选择32-bit权重数据/refill通路，禁止默认或回退到32-bit串行填充。依据真实板卡AXI宽度，优先使用可持续工作的最大端到端宽度；512-bit板卡通路应贯通512-bit DDR loader、tile service与并行缓存写入。DSE联合选择带宽、阵列与token复用，以资源可容纳范围内最高端到端吞吐为目标。历史32-bit产物只保留为基线，不能作为新架构复用。


<!-- array-trial-user-policy -->
最新阵列试验要求：本轮重点尝试16×32（512个并行乘法位置）；暂不推进16×64、32×32、32×64等1024及以上规模。Qwen2当前已为16×32；GPT-2/TinyLlama在共享宽通路完成后由框架重新物化16×32候选、编译并综合评估。512-bit权重填充要求继续有效；资源是否可容纳必须以真实综合为准。通用模板仍保持参数化。


<!-- w4a8-user-restart-policy -->
Latest user instruction: restart this entire design from Stage-0 using the new W4A8 integer-DSP policy. Do not reuse prior floating-point parameter bindings, generated RTL, DDR images, numerical-policy snapshots, calibration ratios or verification evidence. Preserve old artifacts as historical baselines. Preserve the 512-bit DDR path and token-level spatial overlap; optimize cache packing and resource/timing headroom. The earlier mandatory floating-point IP policy is superseded. Throughput is the priority within actual board budgets, with useful placement and timing margin rather than filling all URAM.

Latest architecture constraint: except for W4A8 numeric representation and the scale/shift transport or interfaces strictly required by quantization, preserve the established OPT architecture and schedule. Do not change its pipeline, DDR weight placement/prefetch, active/shadow weight-cache behavior, activation ping-pong, ready/valid backpressure, operator/token overlap, or board AXI/DDR wrapper.

Latest QoR target: 200 token/s measured end-to-end throughput. Continue throughput-first DSE after measured candidates miss the target, within actual resource and physical implementation constraints.
