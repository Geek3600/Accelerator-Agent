# Linear pipeline regression

This regression uses the real Chisel template, VCS, generated Vivado floating-point
IPs, and XPM simulation libraries. The five configurations cover input/output
grouping, reduction trees, wide attention-projection inputs, no bias, and ReLU.

From this directory, generate RTL into a persistent diagnostic directory:

```sh
JVM_OPTS='-Xms256m -Xmx2304m -XX:ActiveProcessorCount=4' \
  sbt --no-server --batch 'runMain GenerateLinearPipeline /absolute/path/to/rtl'
python prepare.py /absolute/path/to/rtl
```

On the VCS server, generate the two IPs using the repository's current
`scripts/synthesis/gen_xilinx_fp_ips_23.tcl` and this directory's
`fpga_ip_modules.txt`. Old IPs without result-ready are not compatible.

Use a VCS version matching the precompiled libraries, then run:

```sh
bash run_vcs.sh /path/to/compiled_ip_context /path/to/rtl \
  /path/to/matching/synopsys_sim.setup /path/to/new/vivado_ip
```

The compiled IP context provides `fpga_ip/vcs_runtime.env`,
`fpga_ip/vcs_elab_args.txt`, and `vcs_work/synopsys_sim.setup`. Its precompiled
libraries are read-only; each case uses its own writable work library and home
directory, avoiding inherited mappings to another VCS version.

Every output word and its address/start/last metadata must match the complete
matrix reference. Input bubbles, prolonged output backpressure, work counts,
actual MAC acceptance bursts, and input/compute/output overlap are checked.
The run intentionally injects stalls: its elapsed cycles are not application
performance measurements or DSE calibration samples.
