"""Run the Plan 5 AXI read-DMA protocol test."""

import subprocess
import tempfile
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "results/plan5/rtwsr_dma_protocol_rtl.txt"
VERILATOR_PATH = Path("/usr/bin/verilator")


def main():
    with tempfile.TemporaryDirectory(prefix="loopquant_plan5_dma_") as temp_name:
        temp_dir = Path(temp_name)
        build_dir = temp_dir / "obj_dir"
        command = [
            str(VERILATOR_PATH), "--binary", "--timing", "-Wno-fatal", "--build-jobs", "1",
            "--top-module", "tb_rtwsr_weight_dma", "--Mdir", str(build_dir),
            str(ROOT / "hardware/rtwsr_weight_dma.sv"),
            str(ROOT / "hardware/tests/tb_rtwsr_weight_dma.sv"),
        ]
        build = subprocess.run(
            command, cwd=temp_dir, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, check=False
        )
        if build.returncode:
            raise RuntimeError("Verilator build failed:\n" + "\n".join(build.stdout.splitlines()[-50:]))

        simulation = subprocess.run(
            [str(build_dir / "Vtb_rtwsr_weight_dma")], cwd=temp_dir,
            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False
        )
        if simulation.returncode:
            raise RuntimeError("DMA protocol simulation failed:\n" + "\n".join(simulation.stdout.splitlines()[-50:]))

    metrics = [
        line.strip() for line in simulation.stdout.splitlines()
        if line.startswith("PASS:")
    ]
    if len(metrics) != 5:
        raise RuntimeError("the simulator did not report all AXI protocol checks")
    report = [
        f"created: {datetime.now().astimezone().isoformat()}",
        "simulator: Verilator 5.020, --binary --timing, build jobs 1",
        "data width: 512 bits",
        "command: address 0x0800000fc0, 130 beats",
        "stream ready: periodic backpressure",
        "fault checks: early RLAST, missing RLAST, and address overflow",
        *metrics,
    ]
    temporary_report = REPORT_PATH.with_suffix(REPORT_PATH.suffix + ".tmp")
    temporary_report.write_text("\n".join(report) + "\n")
    temporary_report.replace(REPORT_PATH)
    print("\n".join(report))


if __name__ == "__main__":
    main()
