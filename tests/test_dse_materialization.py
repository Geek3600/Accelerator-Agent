import json
import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from accagent.framework.dse_materialization import (
    validate_candidate_universe,
    validate_generated_params_source,
)
from accagent.framework.stage_artifacts import (
    generate_chisel_package,
    run_codegen_compile_gate,
)
from accagent.framework.stage_params import build_parameter_bindings
from tests.test_stage_artifacts import prepared_state


class DseMaterializationTest(unittest.TestCase):
    def materialize_candidate(
        self,
        root: Path,
        *,
        lanes: int,
        compute_array_rows: int,
        compute_array_cols: int,
        fifo_depth: int,
        activation_banks: int,
        weight_banks: int,
    ) -> tuple[dict, Path]:
        state, baseline = prepared_state("qwen2", root)
        role_names = sorted(baseline["global_params"]["weight_banks_by_role"])
        parameters = {
            **baseline["global_params"],
            "lanes": lanes,
            "compute_array_rows": compute_array_rows,
            "compute_array_cols": compute_array_cols,
            "fifo_depth": fifo_depth,
            "activation_banks": activation_banks,
            "weight_banks": weight_banks,
            "weight_banks_by_role": {name: weight_banks for name in role_names},
        }
        bindings = build_parameter_bindings(state, parameters)
        binding_path = Path(
            next(
                item["path"]
                for item in state["artifacts"]
                if item["id"] == "artifact.stage4.parameter_binding"
            )
        )
        binding_path.write_text(json.dumps(bindings), encoding="utf-8")
        package = generate_chisel_package(
            root,
            state,
            {"schema_version": "test", "generation_policy": "cross_candidate_materialization"},
        )
        compile_gate = run_codegen_compile_gate(Path(package["root"]))
        self.assertEqual(compile_gate["status"], "pass", compile_gate)
        return package, Path(package["root"])

    def test_candidate_universe_requires_all_physical_dimensions(self) -> None:
        report = validate_candidate_universe(
            [
                {
                    "candidate_id": "a",
                    "parameters": {
                    "lanes": 8,
                    "compute_array_rows": 4,
                    "compute_array_cols": 4,
                        "fifo_depth": 16,
                        "activation_banks": 2,
                        "weight_banks_by_role": {"weight_qkv": 1},
                    },
                }
            ]
        )
        self.assertEqual(report["status"], "pass")
        self.assertIn("GeneratedDesignParams.lanes", report["generated_fields"].values())

    def test_generated_source_forwards_candidate_into_fpga_ip_configuration(self) -> None:
        source = """
        val lanes: Int = 8
        val computeArrayRows: Int = 4
        val computeArrayCols: Int = 4
        val fifoDepth: Int = 32
        val activationBanks: Int = 4
        val weightBanksByRole: Map[String, Int] = Map.empty
        PhysicalImplementation.configureFpgaIp(
          GeneratedDesignParams.fifoDepth,
          GeneratedDesignParams.activationBanks,
          GeneratedDesignParams.weightBanksByRole
        )
        """
        report = validate_generated_params_source(
            source,
            {
                "lanes": 8,
                "compute_array_rows": 4,
                "compute_array_cols": 4,
                "fifo_depth": 32,
                "activation_banks": 4,
                "weight_banks_by_role": {},
            },
        )
        self.assertEqual(report["status"], "pass", report["errors"])

    def test_generated_source_rejects_dropped_fifo_binding(self) -> None:
        report = validate_generated_params_source(
            "val lanes: Int = 8\nval fifoDepth: Int = 16\nval activationBanks: Int = 2\n"
            "val computeArrayRows: Int = 4\nval computeArrayCols: Int = 4\n"
            "val weightBanksByRole: Map[String, Int] = Map.empty\n"
            ,
            {
                "lanes": 8,
                "compute_array_rows": 4,
                "compute_array_cols": 4,
                "fifo_depth": 16,
                "activation_banks": 2,
                "weight_banks_by_role": {},
            },
        )
        self.assertEqual(report["status"], "fail")
        self.assertTrue(any("configuration" in error for error in report["errors"]))

    def test_two_legal_candidates_change_emitted_fpga_implementation(self) -> None:
        """Every Stage-4 dimension must change real elaborated FPGA inputs."""

        with TemporaryDirectory() as temp:
            root = Path(temp)
            first, first_root = self.materialize_candidate(
                root / "candidate_a",
                lanes=8,
                compute_array_rows=2,
                compute_array_cols=2,
                fifo_depth=16,
                activation_banks=2,
                weight_banks=1,
            )
            second, second_root = self.materialize_candidate(
                root / "candidate_b",
                lanes=8,
                compute_array_rows=4,
                compute_array_cols=4,
                fifo_depth=16,
                activation_banks=2,
                weight_banks=1,
            )

            first_params = (
                first_root
                / "src/main/scala/spatialaccagent/generated/GeneratedDesignParams.scala"
            ).read_text(encoding="utf-8")
            second_params = (
                second_root
                / "src/main/scala/spatialaccagent/generated/GeneratedDesignParams.scala"
            ).read_text(encoding="utf-8")
            def elaborated_sv(root: Path) -> bytes:
                return b"".join(
                    path.read_bytes()
                    for path in sorted((root / "vivado").rglob("*.sv"))
                )

            first_sv = elaborated_sv(first_root)
            second_sv = elaborated_sv(second_root)
            first_closure = json.loads(
                Path(first["ip_simulation_closure"]).read_text(encoding="utf-8")
            )
            second_closure = json.loads(
                Path(second["ip_simulation_closure"]).read_text(encoding="utf-8")
            )
            first_manifest = Path(first_closure["ip_module_manifest"]).read_text(encoding="utf-8")
            second_manifest = Path(second_closure["ip_module_manifest"]).read_text(encoding="utf-8")

            for marker in (
                "val lanes: Int = 8",
                "val computeArrayRows: Int = 2",
                "val computeArrayCols: Int = 2",
                "val fifoDepth: Int = 16",
                "val activationBanks: Int = 2",
            ):
                self.assertIn(marker, first_params)
            for marker in (
                "val lanes: Int = 8",
                "val computeArrayRows: Int = 4",
                "val computeArrayCols: Int = 4",
                "val fifoDepth: Int = 16",
                "val activationBanks: Int = 2",
            ):
                self.assertIn(marker, second_params)
            self.assertNotEqual(first_params, second_params)
            self.assertNotEqual(first_sv, second_sv)
            self.assertEqual(first_closure["status"], "ready")
            self.assertEqual(second_closure["status"], "ready")
            self.assertTrue(first_manifest.strip())
            self.assertTrue(second_manifest.strip())

            def linear_pe_count(root: Path) -> int:
                return sum(
                    len(re.findall(rb"\bPhysicalFp32Mul\s+multipliers_[A-Za-z0-9_]+\s*\(", path.read_bytes()))
                    for path in (root / "vivado").glob("Linear*.sv")
                )

            first_pe_count = linear_pe_count(first_root)
            second_pe_count = linear_pe_count(second_root)
            self.assertGreater(first_pe_count, 0)
            self.assertGreater(
                second_pe_count,
                first_pe_count,
                "With all other DSE dimensions fixed, a larger global PE array must emit more DSP multiplier IP instances.",
            )
            self.assertEqual(
                first_closure["policy"],
                second_closure["policy"],
                "Both candidates must use the same physical Vivado IP/XPM timing closure.",
            )


if __name__ == "__main__":
    unittest.main()
