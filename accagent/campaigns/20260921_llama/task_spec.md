# LLaMA FPGA Spatial Accelerator Campaign

Design a complete FPGA-runnable spatial accelerator for the supplied LLaMA-family checkpoint and its complete Transformer-block workload. The model architecture, tensor shapes, layer count, sequence length, numeric policy, and checkpoint tensor names must be derived from the supplied model source and checkpoint; do not substitute another model or use fixed LLaMA dimensions.

Run the complete public Stage 0--7 workflow. Stage 4 must enumerate and measure the complete legal FPGA-effective DSE candidate universe. Every admitted candidate must materially alter generated RTL, Vivado IP configuration, XPM topology, or XDC; analytical estimates and LLM reasoning may prioritize measurements but cannot supply QoR values.

Target the supplied VU9P board sample project and retain its real compute-slot, AXI, DDR, weight-loader, double-buffer, and runtime behavior. Use the mandatory physical implementation contract: one DSP-backed Vivado multiplier IP per PE, Vivado floating-point IP for arithmetic, XPM URAM for weights and large cache/state, and XPM BRAM for activations and stream FIFOs. VCS must use the same physical-IP timing models as the final Vivado closure.

Hard QoR constraints: achieved clock frequency must be at least 250 MHz; measured performance must be strictly greater than 170 token/s; LUT, FF, BRAM, URAM, and DSP usage must remain within the discovered VU9P board resource budget. Measure and report power, but do not impose a power limit.

Use the established hierarchical real verification policy. For Layer 3, run the actual board AXI/DDR wrapper and complete all real runtime/weight loading for one Transformer layer. This board-bringup completion is sufficient to proceed to Stage 7; complete token output and final DDR writeback remain diagnostic evidence, not a prerequisite for Vivado implementation.
