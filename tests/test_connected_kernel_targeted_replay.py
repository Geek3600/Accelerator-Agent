import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from accagent.framework.connected_kernel_targeted_replay import (
    direct_observation_records,
    immutable_semantic_replay_inputs,
    materialize_connected_kernel_replay_testbench,
    materialize_connected_kernel_targeted_replay_evidence,
    read_json,
)
from accagent.framework.stage_repair_execute import execute_causal_slice_repair


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, text: str = "data\n") -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return {"path": str(path), "sha256": sha256(path)}


class ConnectedKernelTargetedReplayTest(TestCase):
    def _run_dir(self, root: Path) -> tuple[Path, dict]:
        run_dir = root / "run"
        input_memh = write(run_dir / "verification" / "semantic_testbench" / "single_layer" / "input.memh")
        output_memh = write(run_dir / "verification" / "semantic_testbench" / "single_layer" / "expected.memh")
        weight_memh = write(run_dir / "verification" / "semantic_testbench" / "single_layer" / "weights.memh")
        runtime_memh = write(run_dir / "verification" / "semantic_testbench" / "single_layer" / "runtime.memh")
        numeric = write(run_dir / "input" / "numeric_policy.json", "{}\n")
        binding = write(run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json", "{}\n")
        requirements = write(run_dir / "verification" / "semantic_testbench" / "dut_weight_binding_requirements.json", "{}\n")
        core = write(
            run_dir / "generated" / "Core.sv",
            """module Core(input io_in_valid, output io_in_ready, input [1:0] io_in_bits_addr,
input io_in_bits_st, input io_in_bits_last, input io_out_ready, output io_out_valid);
wire mlp_mul_io_out_valid__bore, mlp_mul_io_out_ready__bore, mlp_mul_io_out_bits_st__bore, mlp_mul_io_out_bits_last__bore;
wire [1:0] mlp_mul_io_out_bits_addr__bore;
wire mlp_down_io_out_valid__bore, mlp_down_io_out_ready__bore, mlp_down_io_out_bits_st__bore, mlp_down_io_out_bits_last__bore;
wire [1:0] mlp_down_io_out_bits_addr__bore;
wire _add2_io_out_valid, _add2_io_computed_ready;
endmodule
""",
        )
        harness = write(
            run_dir / "generated" / "Harness.sv",
            """module Harness;
Core core (
 .io_in_valid(), .io_in_ready(), .io_in_bits_addr(), .io_in_bits_st(), .io_in_bits_last(),
 .io_out_ready(), .io_out_valid()
);
endmodule
""",
        )
        tb = write(
            run_dir / "verification" / "semantic_testbench" / "single_layer" / "semantic_tb.sv",
            """module semantic_single_transformer_layer_kernel_tb;
reg clock; reg reset; reg start;
Harness dut();
endmodule
""",
        )
        section = {
            "status": "ready",
            "real_weight_binding_verified": True,
            "testbench": tb["path"],
            "testbench_sha256": tb["sha256"],
            "input_vectors": [input_memh],
            "expected_output": output_memh,
            "real_weight_stream": weight_memh,
            "runtime_constant_stream": runtime_memh,
            "rtl_output_capture": str(run_dir / "verification" / "semantic_testbench" / "single_layer" / "rtl_output.memh"),
            "dut_harness": {"top_module": "Harness", "source_files": [harness, core]},
            "pipeline_overlap_contract": {
                "contract_sha256": "c" * 64,
                "token_count": 2,
                "beats_per_token": 2,
                "required_boundaries": ["edge.input", "edge.output"],
            },
        }
        manifest = {
            "status": "ready",
            "numeric_policy": numeric["path"],
            "numeric_policy_sha256": numeric["sha256"],
            "dut_weight_binding_manifest": binding["path"],
            "dut_weight_binding_requirements": requirements["path"],
            "dut_weight_binding_requirements_sha256": requirements["sha256"],
            "single_layer": section,
        }
        manifest_path = run_dir / "verification" / "semantic_testbench" / "semantic_testbench_manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        return run_dir, section

    def test_materializes_hash_bound_read_only_direct_probe(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir, section = self._run_dir(Path(temp_dir))
            canonical = Path(section["testbench"])
            canonical_sha = sha256(canonical)
            _, immutable = immutable_semantic_replay_inputs(run_dir)
            replay_path, replay = materialize_connected_kernel_replay_testbench(run_dir, section)

            self.assertEqual(immutable["status"], "pass")
            self.assertEqual(replay["status"], "pass")
            self.assertEqual(canonical_sha, sha256(canonical))
            self.assertIsNotNone(replay_path)
            self.assertIn("SPATIALACC_CONNECTED_KERNEL_DIRECT", replay_path.read_text())
            self.assertTrue(replay["policy"]["probe_is_read_only"])

    def test_direct_observation_requires_every_lifecycle_kind(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir, section = self._run_dir(Path(temp_dir))
            immutable_semantic_replay_inputs(run_dir)
            materialize_connected_kernel_replay_testbench(run_dir, section)
            sim_log = run_dir / "sim.log"
            rows = [
                "start 1 0 0 0 0 -1 -1 0 0",
                "core_ingress 2 1 1 1 4 1 1 0 1",
                "mlp_mul_tail 3 1 1 1 4 -1 -1 0 1",
                "mlp_down_tail 4 1 1 1 4 -1 -1 0 1",
                "residual2_frontier 5 1 1 1 0 -1 -1 0 0",
                "core_egress 6 1 1 1 4 1 1 0 1",
            ]
            sim_log.write_text(
                "\n".join(
                    "SPATIALACC_CONNECTED_KERNEL_DIRECT kind=%s cycle=%s valid=%s ready=%s fire=%s accepted=%s token=%s beat=%s st=%s last=%s"
                    % tuple(row.split())
                    for row in rows
                ) + "\n",
                encoding="utf-8",
            )
            execution = {
                "status": "pass", "simulator": "vcs", "tool_scope": "remote",
                "fresh_remote_vcs_execution_required": True,
                "remote_job_reuse": {"real_tool_was_not_relaunched": False},
                "run": {"status": "pass"}, "sim_log": str(sim_log),
            }
            cctg = {"status": "pass", "fresh_remote_vcs_execution_observed": True, "boundary_liveness_status": "pass"}
            evidence = materialize_connected_kernel_targeted_replay_evidence(run_dir, execution, cctg)
            self.assertEqual(evidence["trace"]["status"], "pass")
            self.assertTrue(evidence["trace"]["lifecycle"]["ingress_complete"])
            self.assertEqual(evidence["trace"]["lifecycle"]["egress_accepted_count"], 4)
            self.assertEqual(read_json(evidence["context_path"])["direct_observation_sufficiency_status"], "pass")

    def test_first_accepted_core_ingress_is_start_witness(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir, section = self._run_dir(Path(temp_dir))
            immutable_semantic_replay_inputs(run_dir)
            materialize_connected_kernel_replay_testbench(run_dir, section)
            sim_log = run_dir / "sim.log"
            rows = [
                "core_ingress 2 1 1 1 1 0 0 1 0",
                "core_ingress 3 1 1 1 4 1 1 0 1",
                "mlp_mul_tail 4 1 1 1 4 -1 -1 0 1",
                "mlp_down_tail 5 1 1 1 4 -1 -1 0 1",
                "residual2_frontier 6 1 1 1 0 -1 -1 0 0",
                "core_egress 7 1 1 1 4 1 1 0 1",
            ]
            sim_log.write_text(
                "\n".join(
                    "SPATIALACC_CONNECTED_KERNEL_DIRECT kind=%s cycle=%s valid=%s ready=%s fire=%s accepted=%s token=%s beat=%s st=%s last=%s"
                    % tuple(row.split())
                    for row in rows
                )
                + "\n",
                encoding="utf-8",
            )
            execution = {
                "status": "pass", "simulator": "vcs", "tool_scope": "remote",
                "fresh_remote_vcs_execution_required": True,
                "remote_job_reuse": {"real_tool_was_not_relaunched": False},
                "run": {"status": "pass"}, "sim_log": str(sim_log),
            }
            cctg = {"status": "pass", "fresh_remote_vcs_execution_observed": True, "boundary_liveness_status": "pass"}
            evidence = materialize_connected_kernel_targeted_replay_evidence(run_dir, execution, cctg)
            self.assertEqual(evidence["trace"]["status"], "pass")
            self.assertEqual(evidence["trace"]["start_witness"]["source"], "first_accepted_core_ingress")
            self.assertEqual(evidence["trace"]["start_witness"]["record"]["token"], 0)

    def test_invalid_first_core_ingress_does_not_replace_start_witness(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir, section = self._run_dir(Path(temp_dir))
            immutable_semantic_replay_inputs(run_dir)
            materialize_connected_kernel_replay_testbench(run_dir, section)
            sim_log = run_dir / "sim.log"
            rows = [
                "core_ingress 2 1 1 1 2 0 0 1 0",
                "core_ingress 3 1 1 1 4 1 1 0 1",
                "mlp_mul_tail 4 1 1 1 4 -1 -1 0 1",
                "mlp_down_tail 5 1 1 1 4 -1 -1 0 1",
                "residual2_frontier 6 1 1 1 0 -1 -1 0 0",
                "core_egress 7 1 1 1 4 1 1 0 1",
            ]
            sim_log.write_text(
                "\n".join(
                    "SPATIALACC_CONNECTED_KERNEL_DIRECT kind=%s cycle=%s valid=%s ready=%s fire=%s accepted=%s token=%s beat=%s st=%s last=%s"
                    % tuple(row.split())
                    for row in rows
                )
                + "\n",
                encoding="utf-8",
            )
            execution = {
                "status": "pass", "simulator": "vcs", "tool_scope": "remote",
                "fresh_remote_vcs_execution_required": True,
                "remote_job_reuse": {"real_tool_was_not_relaunched": False},
                "run": {"status": "pass"}, "sim_log": str(sim_log),
            }
            cctg = {"status": "pass", "fresh_remote_vcs_execution_observed": True, "boundary_liveness_status": "pass"}
            evidence = materialize_connected_kernel_targeted_replay_evidence(run_dir, execution, cctg)
            self.assertEqual(evidence["trace"]["status"], "fail")
            self.assertIn(
                "connected-kernel direct observation is missing start and has no first accepted core-ingress handshake",
                evidence["trace"]["blockers"],
            )

    def test_parser_rejects_malformed_direct_marker(self) -> None:
        with TemporaryDirectory() as temp_dir:
            log = Path(temp_dir) / "sim.log"
            log.write_text("SPATIALACC_CONNECTED_KERNEL_DIRECT kind=bad\n", encoding="utf-8")
            records, unparsed = direct_observation_records({"sim_log": str(log)})
        self.assertEqual(records, [])
        self.assertEqual(unparsed, 1)

    def test_stage8_returns_direct_replay_package_to_agent(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_state = root / "sacg_state.json"
            source_state.write_text("{}\n", encoding="utf-8")
            cctg_path = root / "cctg.json"
            cctg_path.write_text(
                json.dumps({"schema_version": "spatialaccagent.cctg_boundary_replay.v1", "status": "pass"}),
                encoding="utf-8",
            )
            direct = {
                "immutable_semantic_replay_input_manifest": {"path": "immutable", "status": "pass"},
                "connected_kernel_targeted_replay_trace": {"path": "trace", "status": "pass"},
                "connected_kernel_targeted_replay_causal_context": {"path": "context", "status": "pass"},
                "connected_kernel_targeted_replay_manifest": {"path": "manifest", "status": "pass"},
                "connected_kernel_cctg_contradiction_reconciliation": {"path": "reconciliation", "status": "pass"},
            }
            replay = {
                "status": "pass",
                "log_path": str(root / "replay.json"),
                "cctg_boundary_replay": {"path": str(cctg_path), "status": "pass"},
                "connected_kernel_targeted_replay": direct,
            }
            step = {
                "id": "repair_step.direct_cctg",
                "scope": "causal_slice_repair",
                "debug_layer": "single_transformer_layer_kernel",
                "action": {"repair_kind": "connected_kernel_cctg_contradiction_targeted_replay"},
            }
            with patch(
                "accagent.framework.stage_repair_execute.run_current_layer_causal_replay",
                return_value=replay,
            ):
                result = execute_causal_slice_repair(step, source_state, root, root / "out", 1)
            package = json.loads(Path(result["context_package"]).read_text())

        self.assertTrue(result["requires_agent_followup"])
        self.assertFalse(result["stage_passed"])
        self.assertEqual(
            package["connected_kernel_cctg_targeted_replay_trace"]["path"],
            "trace",
        )
        self.assertTrue(package["policy"]["direct_lifecycle_observation_required"])
