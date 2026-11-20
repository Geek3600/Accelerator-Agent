import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERILATOR = Path("/usr/bin/verilator")
PAYLOAD_DIR = ROOT / "results/plan6/huginn_recurrent_core"


class Plan6HuginnPayloadDescriptorTests(unittest.TestCase):
    def test_all_weight_and_round_gamma_descriptors_match_payload_map(self):
        with tempfile.TemporaryDirectory(prefix="loopquant_plan6_dma_desc_") as directory:
            build_dir = Path(directory) / "obj_dir"
            build = subprocess.run(
                [
                    str(VERILATOR), "--binary", "--timing", "-Wno-fatal", "--build-jobs", "2",
                    "--top-module", "tb_rtwsr_huginn_payload_descriptor", "--Mdir", str(build_dir),
                    str(ROOT / "hardware/rtwsr_huginn_payload_descriptor.sv"),
                    str(ROOT / "hardware/tests/tb_rtwsr_huginn_payload_descriptor.sv"),
                ],
                cwd=directory,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            self.assertEqual(build.returncode, 0, "\n".join(build.stdout.splitlines()[-80:]))
            simulation = subprocess.run(
                [str(build_dir / "Vtb_rtwsr_huginn_payload_descriptor")],
                cwd=directory,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=120,
            )
            self.assertEqual(simulation.returncode, 0, simulation.stdout)

        descriptors = {}
        for line in simulation.stdout.splitlines():
            match = re.fullmatch(r"DESC (\d+) (\d+) (\d+) (\d+) (\d+) (\d+) (\d+) (\d+) (\d+) (\d+)", line)
            if match:
                values = tuple(map(int, match.groups()))
                descriptors[values[:3]] = values[3:]
        self.assertIn("PASS descriptors=63", simulation.stdout)

        operator_map = json.loads((PAYLOAD_DIR / "dma_operator_map.json").read_text())
        expected = {}
        for operator in operator_map["operators"]:
            command_id = operator["command_id"]
            block = max(operator["block_index"], 0)
            row_offset = operator["gamma_row_offset"] * 2
            for recurrence in (0, 7, 31):
                gamma_offset = operator["gamma_offset_bytes"] + row_offset + recurrence * operator[
                    "gamma_recurrence_stride_bytes"
                ]
                rows, columns = operator["shape"]
                expected[(command_id, block, recurrence)] = (
                    operator["weight_offset_bytes"],
                    operator["weight_bytes"],
                    gamma_offset,
                    operator["gamma_bytes_per_recurrence"],
                    operator["weight_bytes"] // 64,
                    operator["gamma_bytes_per_recurrence"] // 64,
                    (rows << 16) | columns,
                )

        self.assertEqual(len(descriptors), 63)
        for key, expected_values in expected.items():
            self.assertIn(key, descriptors)
            self.assertEqual(descriptors[key], expected_values, f"descriptor {key}")
        print(simulation.stdout, end="")


if __name__ == "__main__":
    unittest.main()
