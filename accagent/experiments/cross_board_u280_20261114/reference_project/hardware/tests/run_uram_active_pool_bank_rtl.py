"""Run the active-pool memory protocol test."""

import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERILATOR_PATH = Path("/usr/bin/verilator")


def main():
    with tempfile.TemporaryDirectory(prefix="loopquant_active_pool_") as temp_name:
        temp_dir = Path(temp_name)
        build_dir = temp_dir / "obj_dir"
        command = [
            str(VERILATOR_PATH), "--binary", "--timing", "-Wno-fatal",
            "--build-jobs", "1", "--top-module", "tb_uram_active_pool_bank",
            "--Mdir", str(build_dir),
            str(ROOT / "hardware/uram_active_pool_bank.sv"),
            str(ROOT / "hardware/tests/tb_uram_active_pool_bank.sv"),
        ]
        build = subprocess.run(
            command, cwd=temp_dir, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, check=False,
        )
        if build.returncode:
            raise RuntimeError("active-pool build failed:\n" +
                               "\n".join(build.stdout.splitlines()[-50:]))
        simulation = subprocess.run(
            [str(build_dir / "Vtb_uram_active_pool_bank")], cwd=temp_dir,
            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            check=False,
        )
        if simulation.returncode:
            raise RuntimeError("active-pool simulation failed:\n" +
                               "\n".join(simulation.stdout.splitlines()[-50:]))
        print(simulation.stdout, end="")


if __name__ == "__main__":
    main()
