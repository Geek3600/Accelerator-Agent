import tempfile
import unittest
import json
from pathlib import Path

from accagent.framework.dse_materialization import (
    build_stage5_sv_manifest, validate_stage5_sv_manifest, sv_port_signature,
    parameter_module_dependencies,
)
from accagent.framework.stage_artifacts import (
    build_codegen_package_static_check,
    compact_codegen_manifest_for_review,
    stage5_parameters_from_codegen_manifest,
)


class Stage5ManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.params = dict(lanes=8, compute_array_rows=8, compute_array_cols=16,
                           fifo_depth=64, activation_banks=2, weight_banks_by_role={"weight": 1})
        (self.root / "A.sv").write_text("module A(input [7:0] a, b, output c); endmodule\n")
        (self.root / "GeneratedDesignParams.scala").write_text("val lanes: Int = 8")
        self.manifest = build_stage5_sv_manifest(self.root, self.params)

    def check(self):
        return validate_stage5_sv_manifest(self.root, self.params, self.manifest)

    def test_unchanged_passes_and_replacement_fails(self):
        self.assertEqual(self.check()["status"], "pass")
        (self.root / "A.sv").write_text("module A(input [3:0] a, b, output c); endmodule\n")
        result = self.check()
        self.assertEqual(result["changed_files"], ["A.sv"])
        self.assertEqual(result["port_signature_changes"], ["A.sv"])
        self.assertEqual(result["status"], "fail")

    def test_added_and_deleted_member_fail(self):
        (self.root / "B.sv").write_text("module B(); endmodule")
        self.assertEqual(self.check()["added_files"], ["B.sv"])
        (self.root / "A.sv").unlink()
        self.assertEqual(self.check()["missing_files"], ["A.sv"])

    def test_parameter_or_scala_change_fails(self):
        self.params["compute_array_rows"] = 4
        self.assertEqual(self.check()["status"], "fail")
        self.params["compute_array_rows"] = 8
        (self.root / "GeneratedDesignParams.scala").write_text("val lanes: Int = 4")
        self.assertEqual(self.check()["status"], "fail")

    def test_stage5_uses_materialized_physical_binding_not_top_params(self):
        codegen_manifest = {
            "generated_top": {"params": {"lanes": 8, "hidden_size": 768}},
            "dse_physical_binding_check": {
                "status": "pass",
                "parameters": self.params,
            },
        }

        expected = stage5_parameters_from_codegen_manifest(codegen_manifest)
        self.assertEqual(expected, self.params)
        self.assertEqual(
            validate_stage5_sv_manifest(self.root, expected, self.manifest)["status"],
            "pass",
        )

    def test_package_check_accepts_bound_array_geometry(self):
        required_files = [
            "generated/chisel/build.sbt",
            "generated/chisel/memory/memory_layout.json",
            "generated/chisel/runtime/runtime_config.json",
            "generated/chisel/simulation/fpga_ip_simulation_closure.json",
            "generated/chisel/simulation/fpga_ip_modules.txt",
            "generated/chisel/src/main/scala/spatialaccagent/generated/GeneratedAcceleratorTop.scala",
            "generated/chisel/src/main/scala/spatialaccagent/generated/GeneratedAxiDdrTop.scala",
            "generated/chisel/src/main/scala/spatialaccagent/generated/GeneratedContractCheck.scala",
            "generated/chisel/src/main/scala/spatialaccagent/generated/GeneratedDesignParams.scala",
            "generated/chisel/src/main/scala/spatialaccagent/generated/GeneratedSACGMetadata.scala",
        ]
        for relative in required_files:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("", encoding="utf-8")

        codegen_manifest = {
            "generated_package_root": str(self.root),
            "generated_files": required_files,
            "target_model_artifact_status": {"current_artifacts_match_target": True},
            "planned_code_outputs": [],
            "template_sources": [],
            "compile_gate": {"status": "pass"},
            "contract_check": {"status": "pass"},
            "generated_top": {"params": {"lanes": 8, "hidden_size": 768}},
            "dse_physical_binding_check": {
                "status": "pass",
                "parameters": self.params,
            },
            "stage5_sv_manifest": self.manifest,
        }

        result = build_codegen_package_static_check(
            codegen_manifest,
            self.root / "package_check.json",
        )
        self.assertEqual(result["status"], "pass", result["errors"])

    def test_comment_does_not_change_interface_but_changes_manifest(self):
        path = self.root / "A.sv"
        original = sv_port_signature(path.read_text())
        path.write_text(path.read_text() + "// note\n")
        self.assertEqual(sv_port_signature(path.read_text()), original)
        self.assertEqual(self.check()["status"], "fail")

    def test_inherited_port_width(self):
        ports = self.manifest["port_signatures"]["A.sv"][0]["ports"]
        self.assertEqual(ports[1], {"name": "b", "direction": "input", "packed_range": "[7:0]"})
        self.assertEqual(ports[2]["direction"], "output")
        self.assertEqual(ports[2]["packed_range"], "scalar")

    def test_rules_depend_on_names_not_observed_hashes(self):
        graph = parameter_module_dependencies("fifo_depth", ["PhysicalStreamFifo.sv", "Unrelated.sv"])
        self.assertEqual(graph["predicted_affected"], ["PhysicalStreamFifo.sv"])
        self.assertEqual(graph["predicted_unrelated"], ["Unrelated.sv"])

    def test_codegen_review_compacts_large_port_signatures_with_hashes(self):
        ports = [
            {"direction": "input", "name": f"io_data_{idx}", "packed_range": "[63:0]"}
            for idx in range(20000)
        ]
        manifest = {
            "generated_package_root": str(self.root / "generated" / "chisel"),
            "generated_files": ["generated/chisel/stage5_sv_manifest.json"],
            "stage5_sv_manifest": {
                "schema_version": "spatialaccagent.stage5_sv_manifest.v1",
                "generated_sv_count": 1,
                "parameter_signature": {"lanes": 8},
                "parameter_signature_sha256": "abc123",
                "port_signatures": {"Wide.sv": [{"module": "Wide", "ports": ports}]},
            },
        }
        original_signature_count = len(manifest["stage5_sv_manifest"]["port_signatures"]["Wide.sv"][0]["ports"])
        projected = compact_codegen_manifest_for_review(manifest, self.root / "candidate.json")
        summary = projected["stage5_sv_manifest"]["port_signatures_summary"]

        self.assertEqual(summary["source_file_count"], 1)
        self.assertEqual(summary["module_count"], 1)
        self.assertEqual(summary["port_count"], original_signature_count)
        self.assertEqual(summary["direction_counts"], {"input": original_signature_count})
        self.assertEqual(summary["full_manifest_path"], str(self.root / "candidate.json"))
        self.assertEqual(
            summary["full_signature_artifact_path"],
            str(self.root / "generated" / "chisel" / "stage5_sv_manifest.json"),
        )
        self.assertNotIn("port_signatures", projected["stage5_sv_manifest"])
        self.assertEqual(original_signature_count, len(manifest["stage5_sv_manifest"]["port_signatures"]["Wide.sv"][0]["ports"]))
        self.assertLess(
            len(json.dumps(projected, separators=(",", ":"))),
            len(json.dumps(manifest, separators=(",", ":"))) // 20,
        )


if __name__ == "__main__":
    unittest.main()
