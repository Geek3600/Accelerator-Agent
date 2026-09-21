import hashlib
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from accagent.framework.semantic_simulator import (
    SCHEMA_VERSION,
    recover_archived_semantic_execution,
    run_configured_semantic_harness,
    sha256_file,
)


class HistoricalSemanticExecutionRecoveryTest(TestCase):
    stage_id = "single_transformer_layer_kernel"

    def write(self, path: Path, text: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def fixture(self, root: Path, *, historical_only_module_is_referenced: bool = False) -> tuple[Path, dict]:
        run_dir = root / "run"
        payload = run_dir / "payload"
        tool_profile = run_dir / "input" / "tool_profile.json"
        top = self.write(
            payload / "semantic_tb.sv",
            "module semantic_single_transformer_layer_kernel_tb;\n"
            "  Harness dut();\n"
            "endmodule\n",
        )
        harness_body = (
            "module Harness;\n"
            "  Keep keep();\n"
            + ("  HistoricalOnly old();\n" if historical_only_module_is_referenced else "")
            + "endmodule\n"
        )
        harness = self.write(payload / "Harness.sv", harness_body)
        keep = self.write(payload / "Keep.sv", "module Keep; endmodule\n")
        historical_only = self.write(
            payload / "HistoricalOnly.sv", "module HistoricalOnly; endmodule\n"
        )
        input_vector = self.write(payload / "input.memh", "00000001\n")
        weight = self.write(payload / "weight.memh", "00000002\n")
        runtime = self.write(payload / "runtime.memh", "00000003\n")
        output = self.write(payload / "historic_output.memh", "00000004\n")
        vcs_log = self.write(payload / "historic_vcs.log", "VCS compile pass\n")
        sim_log = self.write(payload / "historic_sim.log", "PASS semantic harness real-weight execution beats=1 cycles=1\n")
        sim_stderr = self.write(payload / "historic_sim.stderr.log", "")
        self.write(
            tool_profile,
            json.dumps(
                {
                    "tools": [
                        {
                            "name": "vcs",
                            "role": "functional_verification",
                            "scope": "remote",
                            "host": "builder@example",
                            "port": 22,
                            "executable": "/eda/vcs/bin/vcs",
                        }
                    ]
                }
            ),
        )
        contract = {
            "testbench": str(top),
            "testbench_sha256": sha256_file(top),
            "dut_harness": {
                "source_files": [
                    {"path": str(harness), "sha256": sha256_file(harness)},
                    {"path": str(keep), "sha256": sha256_file(keep)},
                ]
            },
            "input_vectors": [{"path": str(input_vector), "sha256": sha256_file(input_vector)}],
            "real_weight_stream": {"path": str(weight), "sha256": sha256_file(weight)},
            "runtime_constant_stream": {"stream": {"path": str(runtime), "sha256": sha256_file(runtime)}},
            "rtl_output_capture": str(run_dir / "verification" / "semantic_testbench" / "single_layer" / "rtl_output.memh"),
        }

        historic_fingerprint = "a" * 64
        artifact_dir = (
            run_dir
            / "verification"
            / "remote_artifacts"
            / "semantic_vcs_single_transformer_layer_kernel"
            / historic_fingerprint
        )
        job = {
            "schema_version": "spatialaccagent.remote_semantic_job.v1",
            "stage_id": self.stage_id,
            "top_module": "semantic_single_transformer_layer_kernel_tb",
            "input_fingerprint_sha256": historic_fingerprint,
            "tool_profile": {
                "name": "vcs",
                "role": "functional_verification",
                "scope": "remote",
                "host": "builder@example",
                "port": 22,
                "executable": "/eda/vcs/bin/vcs",
                "vcs_target_arch": "linux64",
                "compile_jobs": 1,
            },
            "compile_defines": [],
            "source_names": ["Harness.sv", "Keep.sv", "HistoricalOnly.sv"],
            "plusargs": [
                "+INPUT_0_MEMH=input_0.memh",
                "+WEIGHT_MEMH=weight.memh",
                "+RUNTIME_MEMH=runtime.memh",
                "+OUTPUT_MEMH=rtl_output.memh",
            ],
            "payload": [
                {"path": "Harness.sv", "sha256": sha256_file(harness)},
                {"path": "Keep.sv", "sha256": sha256_file(keep)},
                {"path": "HistoricalOnly.sv", "sha256": sha256_file(historical_only)},
                {"path": "semantic_tb.sv", "sha256": sha256_file(top)},
                {"path": "input_0.memh", "sha256": sha256_file(input_vector)},
                {"path": "weight.memh", "sha256": sha256_file(weight)},
                {"path": "runtime.memh", "sha256": sha256_file(runtime)},
            ],
        }
        job_path = self.write(artifact_dir / "job_contract.json", json.dumps(job))
        snapshot = self.write(
            artifact_dir / "source_snapshots" / "000_HistoricalOnly.sv",
            historical_only.read_text(encoding="utf-8"),
        )
        receipt = {
            "schema_version": "spatialaccagent.remote_artifact_receipt.v1",
            "status": "pass",
            "input_fingerprint_sha256": historic_fingerprint,
            "remote_workdir": "/remote/historical_job",
            "job_contract": {"path": str(job_path), "sha256": sha256_file(job_path)},
            "evidence_files": [
                {"path": str(vcs_log), "sha256": sha256_file(vcs_log), "source_relative_path": "verification/operator_leaf_vcs/single_transformer_layer_kernel/vcs.log"},
                {"path": str(sim_log), "sha256": sha256_file(sim_log), "source_relative_path": "verification/operator_leaf_vcs/single_transformer_layer_kernel/sim.log"},
                {"path": str(sim_stderr), "sha256": sha256_file(sim_stderr), "source_relative_path": "verification/operator_leaf_vcs/single_transformer_layer_kernel/sim.stderr.log"},
                {"path": str(output), "sha256": sha256_file(output), "source_relative_path": "verification/semantic_testbench/single_layer/rtl_output.memh"},
            ],
            "source_snapshots": [
                {
                    "source_path": str(historical_only),
                    "snapshot_path": str(snapshot),
                    "sha256": sha256_file(snapshot),
                }
            ],
        }
        receipt_path = self.write(artifact_dir / "receipt.json", json.dumps(receipt))
        stats = {
            "schema_version": SCHEMA_VERSION,
            "status": "pass",
            "stage_id": self.stage_id,
            "input_fingerprint_sha256": historic_fingerprint,
            "tool_profile": job["tool_profile"],
            "compile": {"status": "pass"},
            "run": {"status": "pass", "returncode": 0, "remote_state": "done"},
            "remote_artifact_persistence": {"status": "pass", "receipt": str(receipt_path)},
            "rtl_output_sha256": sha256_file(output),
            "source_files": [str(harness), str(keep), str(historical_only)],
        }
        historic_report = {
            "schema_version": "spatialaccagent.single_layer_functional_sim.v1",
            "status": "pass",
            "output_sha256": sha256_file(output),
            "real_weight_execution": {"verified": True},
            "stats": stats,
        }
        iteration_dir = run_dir / "repair_execution" / "loop" / "iteration_0042"
        report_path = self.write(iteration_dir / "capability_report.json", json.dumps(historic_report))
        record = {
            "schema_version": "spatialaccagent.stage6_repair_loop_iteration.v1",
            "iteration": 42,
            "disposition": {"status": "complete"},
            "repair_execution_report": {
                "step_results": [{"result": {"stage_passed": True}}]
            },
            "evidence_snapshots": [
                {
                    "role": "capability_report",
                    "source_path": str(run_dir / "verification" / "single_layer" / "single_layer_functional_report.json"),
                    "source_sha256": sha256_file(report_path),
                    "snapshot_path": str(report_path),
                }
            ],
        }
        self.write(iteration_dir / "iteration_record.json", json.dumps(record))
        return run_dir, contract

    def test_recovers_completed_vcs_execution_when_only_unreachable_old_source_was_removed(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir, contract = self.fixture(Path(temp_dir))

            recovered = recover_archived_semantic_execution(
                run_dir, self.stage_id, contract, timeout_sec=1
            )

            self.assertIsNotNone(recovered)
            self.assertTrue(recovered["historical_semantic_execution_recovery"]["real_tool_was_not_relaunched"])
            output = Path(contract["rtl_output_capture"])
            self.assertEqual(output.read_text(encoding="utf-8"), "00000004\n")
            proof = Path(recovered["historical_semantic_execution_recovery"]["proof"])
            proof_data = json.loads(proof.read_text(encoding="utf-8"))
            self.assertEqual(proof_data["status"], "pass")
            self.assertEqual(
                proof_data["static_source_closure"]["historical_only_modules_referenced_by_current_closure"],
                [],
            )
            self.assertNotIn(
                str(run_dir / "payload" / "HistoricalOnly.sv"),
                recovered["source_files"],
            )
            self.assertEqual(
                sorted(recovered["source_files"]),
                sorted(
                    [
                        str(run_dir / "payload" / "Harness.sv"),
                        str(run_dir / "payload" / "Keep.sv"),
                    ]
                ),
            )
            self.assertIn(
                str(run_dir / "payload" / "HistoricalOnly.sv"),
                recovered["historical_compile_source_files"],
            )

    def test_runner_reuses_recovered_execution_without_invoking_remote_vcs(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir, contract = self.fixture(Path(temp_dir))

            with patch(
                "accagent.framework.semantic_simulator.run_remote_vcs_semantic_harness"
            ) as remote:
                recovered = run_configured_semantic_harness(
                    run_dir, self.stage_id, contract, timeout_sec=1
                )

            remote.assert_not_called()
            self.assertEqual(recovered["status"], "pass")
            self.assertEqual(
                recovered["remote_job_reuse"]["identity_source"],
                "completed_stage6_historical_execution",
            )

    def test_targeted_replay_bypasses_historical_execution_recovery(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir, contract = self.fixture(Path(temp_dir))
            fresh = {"status": "pass", "summary": "fresh remote VCS replay"}

            with patch.dict(
                os.environ,
                {"SPATIALACC_FORCE_FRESH_REMOTE_VCS": "1"},
                clear=False,
            ), patch(
                "accagent.framework.semantic_simulator.run_remote_vcs_semantic_harness",
                return_value=fresh,
            ) as remote:
                result = run_configured_semantic_harness(
                    run_dir, self.stage_id, contract, timeout_sec=1
                )

            remote.assert_called_once()
            self.assertEqual(result, fresh)

    def test_rejects_removed_source_when_current_closure_still_references_it(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir, contract = self.fixture(
                Path(temp_dir), historical_only_module_is_referenced=True
            )

            recovered = recover_archived_semantic_execution(
                run_dir, self.stage_id, contract, timeout_sec=1
            )

            self.assertIsNone(recovered)
            self.assertFalse(Path(contract["rtl_output_capture"]).exists())

    def test_source_hash_change_returns_recovery_miss_instead_of_key_error(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir, contract = self.fixture(Path(temp_dir))
            source = Path(contract["dut_harness"]["source_files"][0]["path"])
            source.write_text(source.read_text(encoding="utf-8") + "// changed\n", encoding="utf-8")

            recovered = recover_archived_semantic_execution(
                run_dir, self.stage_id, contract, timeout_sec=1
            )

            self.assertIsNone(recovered)
