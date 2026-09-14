Target board profile for the Qwen spatial accelerator automation run:

- Remote tool host: hyyuan@10.12.133.23.
- Vivado: /home/EDA/Xilinx/Vivado/2021.1/bin/vivado.
- VCS: /home/EDA/Software/EDATools/Synopsys/VCSALL/v202109/bin/vcs.
- FPGA part for the synthesis/implementation target: xcvu9p-flga2104-2-i.
- Board/shell reference: reuse the OPT accelerator VU9P app_shell_9p board assumptions when a board wrapper is needed.
- The platform has external DDR and an AXI-accessible accelerator control interface in the OPT accelerator shell.
- For this Qwen run, a standalone Qwen generated core bitstream is required first. A board-runtime pass requires a later
  Qwen-specific AXI/DDR wrapper and must not be inferred from the OPT opt_acc_core wrapper.
- Vivado synthesis, implementation, bitstream generation, board runtime, and benchmark evidence are required before
  final design pass.
- If board commands are not configured yet, record them as pending evidence instead of pretending the board passed.
