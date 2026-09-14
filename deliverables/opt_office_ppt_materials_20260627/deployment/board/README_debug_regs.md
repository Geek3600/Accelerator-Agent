# Board debug-regs bring-up helper

Use this helper on the real board host, not on server 79. Server 79 has no FPGA card.

## Build on board host

```bash
cd /path/to/Qwen2-Accelerator
cd scripts/board
gcc debug_regs_check.c \
  -I../../mimic_driver/src \
  -L../../mimic_driver/src \
  -lmimic_v6_api -lmimic_v6_sdk \
  -o debug_regs_check
```

If the binary cannot find shared libraries at runtime:

```bash
export LD_LIBRARY_PATH=/path/to/Qwen2-Accelerator/mimic_driver/src:$LD_LIBRARY_PATH
```

## Commands

```bash
./debug_regs_check magic      # read DBG_BASE+0x68, expect 0x0ACC2026
./debug_regs_check load_cfg   # write 22 cfg words, cfg_done=1, latch cfg
./debug_regs_check start 200  # start and poll status up to 200 times
./debug_regs_check poll 50    # only poll DBG_BASE+0x64
./debug_regs_check clear      # write result clear pulse
./debug_regs_check reset      # write user reset pulse
./debug_regs_check all 200    # magic + load_cfg + start/poll
```

The tool uses mimic SDK offsets, so `DBG_BASE=0x1000000000` is passed directly. Do not add the Aurora base `0x2000000000` when using this tool.

## Current pyjm12 board smoke flow

`run_pyjm12_smoke.sh` reproduces the manually validated board flow for the short-sequence real 12-layer `pyjm12_alllayers_9p_fullseq` case. It does not change RTL or the bitstream.

Copy it to the board host and run from any directory:

```bash
cd /home/test/mimic_driver_c6
bash /path/to/run_pyjm12_smoke.sh
```

Defaults match the validated `hadoop111` setup:

```text
MIMIC_DIR=/home/test/mimic_driver_c6
XDMA_ID=1
DDR_IMAGE=/home/test/pyjm12_alllayers_9p_fullseq/pyjm12_alllayers_9p_fullseq/artifacts/ddr_image.u32.bin
WRITE_DDR=0
RUNS=5
```

To rewrite the DDR image before running:

```bash
WRITE_DDR=1 bash /path/to/run_pyjm12_smoke.sh
```

The script intentionally uses the validated temporary safe output address:

```text
cfg word4 rel_output = 0x092f1000
absolute output       = 0x28092f1000
```

This avoids the observed failing boundary at `0x28092f1400`. It is a bring-up smoke-test workaround, not the final clean case layout.

## Latency measurement helper

`measure_pyjm12_latency.c` is a single-process board-side measurement tool. It avoids shell loops and repeated `dma_from_device` process startup overhead.

Build on the board host:

```bash
cd /home/test/mimic_driver_c6
gcc -O2 -Wall -Wextra /home/test/mimic_driver_c6/measure_pyjm12_latency.c -o /tmp/measure_pyjm12_latency
```

If the file is copied elsewhere, adjust the source path accordingly.

Run with the current validated bit:

```bash
sudo /tmp/measure_pyjm12_latency 20 1000 0 | tee /tmp/latency_old_bit.csv
```

Arguments:

```text
arg1 runs             default 20
arg2 poll_timeout_ms  default 1000
arg3 write_input_mode 0=no input write, 1=write first 64KB from DDR image, 2=write full DDR image
```

The tool prints CSV:

```text
run,host_start_to_result_ns,poll_reads,status_raw,input_status,result_status,hw_latency_cycles_reg31,output_hash32
```

Interpretation:

- `host_start_to_result_ns` is measured by `clock_gettime(CLOCK_MONOTONIC_RAW)` inside one C process, from just before the `reg25 bit0 start` pwrite to the first status read where `result_status != 0`.
- This host-side value includes PCIe/XDMA register write latency, polling read latency, Linux scheduling noise, and software overhead. It is useful for end-to-end host-observed latency, but it is not a pure hardware-cycle latency.
- `hw_latency_cycles_reg31` is only meaningful on the new debug-latency bit that maps `reg31/0x7c` to the start-to-result cycle counter. On the old successful bit this field may be an ordinary register value.
- For pure hardware latency/performance, use the new debug-only bit and convert `reg31` cycles with the AXI-lite clock. If `S_AXI_ACLK=100MHz`, latency seconds = `cycles / 100000000`.
