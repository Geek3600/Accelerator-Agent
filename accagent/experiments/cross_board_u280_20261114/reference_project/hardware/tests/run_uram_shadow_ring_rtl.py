"""Run full-capacity and Huginn-geometry shadow-ring protocol simulations."""

import subprocess
import tempfile
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "results/plan5/uram_shadow_ring_rtl.txt"
VERILATOR_PATH = Path("/usr/bin/verilator")
CASES = [
    ("physical_capacity", 73728, 18, 1024, 4),
    ("huginn_per_bank_group", 73728, 165, 70, 4),
]


def run_case(name, depth, tile_slots, window_count, words_per_window):
    with tempfile.TemporaryDirectory(prefix=f"loopquant_shadow_{name}_") as temp_name:
        temp_dir = Path(temp_name)
        build_dir = temp_dir / "obj_dir"
        command = [
            str(VERILATOR_PATH), "--binary", "--timing", "-Wno-fatal",
            "--build-jobs", "1", "--top-module", "tb_uram_shadow_ring",
            "--Mdir", str(build_dir),
            f"-GDEPTH={depth}", f"-GTILE_SLOTS={tile_slots}",
            f"-GWINDOW_COUNT={window_count}",
            f"-GWORDS_PER_WINDOW={words_per_window}",
            str(ROOT / "hardware/uram_shadow_ring.sv"),
            str(ROOT / "hardware/tests/tb_uram_shadow_ring.sv"),
        ]
        build = subprocess.run(
            command, cwd=temp_dir, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, check=False,
        )
        if build.returncode:
            raise RuntimeError(f"{name} build failed:\n" + "\n".join(build.stdout.splitlines()[-40:]))
        simulation = subprocess.run(
            [str(build_dir / "Vtb_uram_shadow_ring")], cwd=temp_dir,
            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            check=False, timeout=600,
        )
        if simulation.returncode:
            raise RuntimeError(
                f"{name} simulation failed:\n" + "\n".join(simulation.stdout.splitlines()[-40:])
            )
        records_per_set = tile_slots * window_count * words_per_window
        total_records = 2 * records_per_set
        return [
            f"case: {name}",
            f"configuration: DEPTH={depth}, TILE_SLOTS={tile_slots}, "
            f"WINDOW_COUNT={window_count}, WORDS_PER_WINDOW={words_per_window}",
            f"complete tile set: {records_per_set} records",
            f"total streamed: {total_records} records",
            f"ring pointer wraps: {total_records // depth} write and {total_records // depth} read",
            "data checks: incomplete-tile gating, 512-bit payload, metadata order/stability, tile-last, occupancy drain, protocol_error",
            *simulation.stdout.splitlines(),
        ]


def main():
    lint = subprocess.run(
        [str(VERILATOR_PATH), "--lint-only", "-Wno-fatal", "--top-module",
         "uram_shadow_ring", str(ROOT / "hardware/uram_shadow_ring.sv")],
        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        check=False,
    )
    if lint.returncode:
        raise RuntimeError("shadow-ring lint failed:\n" + lint.stdout)
    results = []
    for case in CASES:
        results.extend(run_case(*case))
    with tempfile.TemporaryDirectory(prefix="loopquant_streaming_store_") as temp_name:
        temp_dir = Path(temp_name)
        build_dir = temp_dir / "obj_dir"
        command = [
            str(VERILATOR_PATH), "--binary", "--timing", "-Wno-fatal",
            "--build-jobs", "1", "--top-module", "tb_rtwsr_streaming_weight_store",
            "--Mdir", str(build_dir),
            str(ROOT / "hardware/uram_shadow_ring.sv"),
            str(ROOT / "hardware/rtwsr_streaming_weight_store.sv"),
            str(ROOT / "hardware/tests/tb_rtwsr_streaming_weight_store.sv"),
        ]
        build = subprocess.run(
            command, cwd=temp_dir, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, check=False,
        )
        if build.returncode:
            raise RuntimeError("full streaming-store build failed:\n" +
                               "\n".join(build.stdout.splitlines()[-50:]))
        simulation = subprocess.run(
            [str(build_dir / "Vtb_rtwsr_streaming_weight_store")], cwd=temp_dir,
            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            check=False, timeout=3600,
        )
        if simulation.returncode:
            raise RuntimeError("full streaming-store simulation failed:\n" +
                               "\n".join(simulation.stdout.splitlines()[-50:]))
        results.extend(simulation.stdout.splitlines())
    report = [
        f"created: {datetime.now().astimezone().isoformat()}",
        f"simulator: {subprocess.run([str(VERILATOR_PATH), '--version'], check=True, text=True, capture_output=True).stdout.strip()}",
        "build: Verilator --binary --timing, build jobs 1",
        f"static lint: Verilator --lint-only, exit code {lint.returncode}",
        "runner exit code: 0",
        "payload width: 512 bits (64 bytes)",
        "physical capacity: 73,728 records; raw-bit capacity equals 128 URAM blocks",
        "XPM data organization: 7x72-bit URAM lanes plus 8-bit BRAM tail; Vivado mapping not measured",
        "integrated Huginn geometry: 165 tiles x 32 channels x 70 windows = 369,600 records",
        "shared ring instantiated once for the complete 3-SLR operator stream",
        *results,
    ]
    temporary_report = REPORT_PATH.with_suffix(REPORT_PATH.suffix + ".tmp")
    temporary_report.write_text("\n".join(report) + "\n")
    temporary_report.replace(REPORT_PATH)
    print("\n".join(report))


if __name__ == "__main__":
    main()
