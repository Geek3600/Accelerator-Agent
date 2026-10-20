# Gemma FPGA Spatial Accelerator Campaign

Design a complete FPGA-runnable spatial accelerator for the supplied Gemma checkpoint and its complete decoder Transformer-block workload. Derive the model architecture, tensor shapes, layer count, sequence length, checkpoint tensor names, and operator order from the supplied model source and checkpoint; do not substitute GPT-2 or fixed project dimensions.

Run the complete public Stage 0--7 workflow with real tools and the supplied VU9P board sample project. Preserve the established OPT-aligned architecture and schedule: W4A8 signed INT4 weights, INT8 activations, INT32 accumulation and integer DSP MACs; complete weights in external DDR; 512-bit DDR loader and refill; bounded active/shadow weight caches; prefetch of the next layer/tile; activation ping-pong; ready/valid backpressure; token-level operator overlap; and the exact board AXI/DDR wrapper and compute-slot behavior. Do not use floating-point IP for the elaborated W4A8 datapath.

Stage 4 must enumerate and measure the complete legal FPGA-effective DSE candidate universe with real synthesis evidence. Select for highest end-to-end throughput within discovered VU9P resource and timing limits, rather than minimum resource usage. Analytical estimates may prioritize candidates but cannot replace measured QoR. Report estimates separately from measured results.

Use the established hierarchical verification policy: real model weights and inputs, operator/leaf validation, connected single-layer validation, then the exact board AXI/DDR wrapper with real DDR weight loading, active/shadow switching, prefetch, activation ping-pong, and final writeback. Valid nonzero output and no deadlock satisfy the stated functional acceptance when the real tool gates pass; preserve full layer computation and pipeline overlap.

The upstream LLM for this experiment is gpt-6.1-sol. This experiment changes only the target model to Gemma; do not alter shared templates, numeric policy, board materials, or the generic agent workflow for this campaign.
