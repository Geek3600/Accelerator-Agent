# Alveo U280 board input for the GPT-2 Medium seq32 experiment

Target board: AMD/Xilinx Alveo U280.
Exact FPGA part: `xcu280-fsvh2892-2L-e`.
Source: the user's `workspace/LoopQuant/hardware` U280 reference.
Use Vivado 2021.1 and VCS 2022.06 from the unchanged tool materials.
Discover the part's resource budget with the existing real Vivado probe.

## Read-only source reference

The frozen reference project is available on `hyyuan@10.12.133.23` at:
`/home/hyyuan/workspace/spatialaccagent_artifacts/board_references/cross_board_u280_20261114/hardware`.
It contains the original hardware source, simulation BFMs and project scripts.
Only read these references; generate all new files inside the current run.
The two attached source files are unchanged copies of the original U280 shell
and HBM IP generation script. The script is reference material: do not execute
its historical temporary-directory paths as the new experiment's workspace.

## Interface facts from the attached source

The reference top is `rtwsr_plan6_huginn_u280_hbm_shell`.
It exposes separate `core_clk` / active-low `core_rst_n` and `hbm_axi_clk` /
active-low `hbm_axi_rst_n` domains, an AXI-Lite control slave with 32-bit data
and 12-bit addresses, and external memory master ports.

Its parameterized `hbm_m_axi_*` interface defaults to 32 pseudo-channels.
Each physical HBM channel has 256-bit read data, 33-bit addresses, 6-bit IDs,
4-bit burst length, 3-bit size, 2-bit burst type, RRESP, RLAST and ready/valid.
The attached IP generation script enables all 32 SAXI ports, two 4GB stacks,
and specifies a 450 MHz HBM AXI clock and 100 MHz input clock.
These HBM clocks do not change the experiment's 150 MHz core timing target.

The shell also has a `gamma_m_axi_*` read interface with 512-bit data,
37-bit addresses, 5-bit IDs and 8-bit burst length. It is a distinct interface;
do not conflate its widths with the HBM channel widths. The shell's master
ports shown here are read ports, not evidence of a complete host/output-write
path or a physical PCIe/HBM-controller top. Derive any required complete
integration and output-writeback adaptation from the actual reference sources
and vendor interface evidence through the normal design agents.

## Experiment binding

Only the target board changes. The target workload remains GPT-2 Medium,
24 layers, batch 1, seq32, W4A8/I32, Transformer blocks only, upstream
GPT-6.1-Sol. LoopQuant's application-specific Huginn/ternary compute engine,
recurrence count, descriptors and weight format are not accelerator inputs.

Keep the core's 512-bit logical refill and bounded active/shadow caches;
derive a legal physical U280 memory binding at the board boundary. Preserve
next-layer prefetch, activation ping-pong, token/operator overlap and
ready/valid backpressure. Board-derived resources and legal DSE selections
are outputs of this experiment, not values copied from the VU9P result.

No U280 host runtime command, physical host address map, output address,
board device ID or board execution host is established by these materials.
Leave unknown runtime facts unknown; the EDA server is not a board host.
Do not inherit MIMIC/XDMA addresses or `c0_ddr4_s_axi_*` names from VU9P.
Use the same `vcs_compile_only` acceptance policy and source-bound OOC
post-synthesis timing/resource evidence as the existing seq32 experiments.
