import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from accagent.framework.runtime_observation import (
    build_compiled_signal_catalog,
    current_observation_selection_path,
    runtime_observation_selection,
)
from accagent.framework.simulation_checkpoint import simulation_execution_identity
from accagent.framework.stage_repair_execute import (
    runtime_only_observation_output,
    validate_adaptive_observation_decision,
)


class RuntimeObservationTest(unittest.TestCase):
    def _run_dir(self, root: Path) -> tuple[Path, Path]:
        run_dir = root / "run"
        testbench = (
            run_dir
            / "generated"
            / "board_integration"
            / "spatialacc_exact_board_multilayer_tb.sv"
        )
        testbench.parent.mkdir(parents=True)
        testbench.write_text(
            """module BoardTb;
wire sink_valid;
wire sink_ready;
assign sink_valid = dut.spatialacc_single_kernel.core.add2.io_out_valid;
assign sink_ready = dut.spatialacc_single_kernel.core.add2.io_out_ready;
assign current_dag_boundary_valid[0] = dut.spatialacc_single_kernel.core.rms1.io_in_valid;
assign current_dag_boundary_ready[0] = dut.spatialacc_single_kernel.core.rms1.io_in_ready;
assign current_dag_boundary_payload[0] = dut.spatialacc_single_kernel.core.rms1.io_in_bits_data;
function automatic string current_dag_boundary_name(input integer boundary_index);
  case (boundary_index)
    0: current_dag_boundary_name = "edge.data.block_input.to.stage_00_rms_norm_1.input";
    default: current_dag_boundary_name = "unknown";
  endcase
endfunction
endmodule
""",
            encoding="utf-8",
        )
        manifest = run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(
            json.dumps(
                {
                    "board_simulation_preflight_plan": {
                        "testbench": {"path": str(testbench)}
                    }
                }
            ),
            encoding="utf-8",
        )
        replay = run_dir / "verification" / "board_simulation" / "fast_replay_state.json"
        replay.parent.mkdir(parents=True)
        replay.write_text(
            json.dumps(
                {
                    "status": "ready",
                    "verified": True,
                    "identity": {
                        "compiled_model_sha256": "model-1",
                        "workload_sha256": "workload-1",
                        "cut": "after_weight_load_before_first_token",
                    },
                }
            ),
            encoding="utf-8",
        )
        board_manifest = (
            run_dir
            / "verification"
            / "board_simulation"
            / "board_simulation_manifest.json"
        )
        board_manifest.write_text(
            json.dumps(
                {
                    "top_module": "BoardTb",
                    "validation_mode": "compute_slot_axi",
                    "source_files": [
                        {
                            "source_id": "generated-board-source:testbench",
                            "sha256": hashlib.sha256(testbench.read_bytes()).hexdigest(),
                            "role": "testbench",
                        }
                    ],
                    "source_closure_sha256": "source-closure",
                    "compile_source_set_sha256": "source-set",
                    "vcs_compile_plan_sha256": "compile-plan",
                    "artifacts": {},
                }
            ),
            encoding="utf-8",
        )
        return run_dir, testbench

    def _current_model(self, run_dir: Path) -> str:
        manifest = json.loads(
            (
                run_dir
                / "verification"
                / "board_simulation"
                / "board_simulation_manifest.json"
            ).read_text(encoding="utf-8")
        )
        return simulation_execution_identity(manifest)["compiled_model_sha256"]

    def _decision(self, diagnosis_sha: str) -> dict:
        return {
            "schema_version": "spatialaccagent.adaptive_observation_decision.v1",
            "mode": "deepen_simulation_observation",
            "frontier_id": "frontier.current",
            "evidence_refs": [f"diagnosis#sha256={diagnosis_sha}"],
            "field_observations": [
                {
                    "evidence_pointer": "/current_board_vcs_feedback/diagnosis/value/runtime/output_count",
                    "observed_value": 0,
                    "semantic_role": "counter",
                    "interpretation": "the current output count has not identified the waiting stage",
                }
            ],
            "probe_plan": {
                "target_boundary": "frontier.current",
                "add_or_update_probe_ids": ["runtime.frontier.current"],
                "retire_probe_ids": [],
                "required_event_fields": ["valid", "ready"],
                "event_match": {"observational_only": True},
                "trigger_condition": "always",
                "bounded_window": "the complete restored run and its terminal record",
            },
            "observation_delta": {
                "missing_distinction": "whether final residual sends output while the sink is ready",
                "candidate_root_causes": ["final residual waits", "output sink waits"],
                "new_signal_expressions": [
                    "dut.spatialacc_single_kernel.core.add2.io_out_valid",
                    "dut.spatialacc_single_kernel.core.add2.io_out_ready",
                ],
                "expected_signal_patterns": ["valid low with ready high identifies an upstream wait"],
                "candidate_cause_checks": [
                    {
                        "cause": "final residual waits",
                        "signal_expressions": [
                            "dut.spatialacc_single_kernel.core.add2.io_out_valid",
                            "dut.spatialacc_single_kernel.core.add2.io_out_ready",
                        ],
                        "expected_pattern": "output valid remains low while ready is high",
                        "disambiguates": "an upstream wait from output backpressure",
                    }
                ],
            },
            "rationale": "select already compiled final-output signals without changing the testbench",
        }

    def test_runtime_selection_leaves_compiled_testbench_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir, testbench = self._run_dir(Path(temp_dir))
            before = hashlib.sha256(testbench.read_bytes()).hexdigest()
            catalog = build_compiled_signal_catalog(run_dir)
            selection = runtime_observation_selection(
                run_dir, self._decision("a" * 64)
            )
            after = hashlib.sha256(testbench.read_bytes()).hexdigest()

            self.assertEqual(
                catalog["compiled_model_sha256"], self._current_model(run_dir)
            )
            self.assertEqual(before, after)
            self.assertEqual(selection["status"], "ready")
            self.assertEqual(selection["selected_signal_count"], 2)
            self.assertTrue(current_observation_selection_path(run_dir).is_file())

    def test_consecutive_runtime_selections_keep_the_same_model(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir, testbench = self._run_dir(Path(temp_dir))
            before = hashlib.sha256(testbench.read_bytes()).hexdigest()
            selected_counts = []
            for suffix in ("a", "b", "c"):
                decision = self._decision("a" * 64)
                decision["observation_delta"]["new_signal_expressions"] = [
                    "dut.spatialacc_single_kernel.core.add2.io_out_valid"
                    if suffix != "c"
                    else "dut.spatialacc_single_kernel.core.rms1.io_in_valid"
                ]
                selection = runtime_observation_selection(run_dir, decision)
                selected_counts.append(selection["selected_signal_count"])
                self.assertEqual(
                    selection["compiled_model_sha256"],
                    self._current_model(run_dir),
                )

            self.assertEqual(hashlib.sha256(testbench.read_bytes()).hexdigest(), before)
            self.assertEqual(selected_counts, [2, 2, 3])

    def test_current_manifest_identity_wins_over_stale_replay_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir, _ = self._run_dir(Path(temp_dir))
            catalog = build_compiled_signal_catalog(run_dir)

            self.assertNotEqual(catalog["compiled_model_sha256"], "model-1")
            self.assertEqual(
                catalog["compiled_model_sha256"], self._current_model(run_dir)
            )

    def test_empty_file_edits_are_valid_for_catalog_observation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir, _ = self._run_dir(Path(temp_dir))
            diagnosis_sha = "a" * 64
            package = {
                "current_board_vcs_feedback": {
                    "status": "ready",
                    "runner_report": {"sha256": "b" * 64},
                    "diagnosis": {
                        "sha256": diagnosis_sha,
                        "value": {
                            "failure_evidence": {
                                "sacg_cctg_causal_slice": {
                                    "sha256": "c" * 64,
                                    "value": {
                                        "earliest_unproven_frontier": {
                                            "frontier_id": "frontier.current"
                                        }
                                    },
                                }
                            },
                            "runtime": {"output_count": 0},
                        },
                    },
                }
            }
            result = validate_adaptive_observation_decision(
                {
                    "status": "ready_to_apply",
                    "file_edits": [],
                    "adaptive_observation_decision": self._decision(diagnosis_sha),
                },
                package,
                run_dir,
            )

        self.assertEqual(result["status"], "pass")
        self.assertEqual(
            result["runtime_observation_selection"]["selected_signal_count"], 2
        )

    def test_observation_decision_drops_compiled_source_edits(self) -> None:
        output = {
            "status": "ready_to_apply",
            "adaptive_observation_decision": {
                "mode": "deepen_simulation_observation"
            },
            "file_edits": [
                {
                    "path": "/run/generated/board_integration/board_tb.sv",
                    "operation": "replace_text",
                },
                {
                    "path": "/run/generated/board_integration/axi_protocol_monitor.sv",
                    "operation": "replace_text",
                },
            ],
        }

        normalized = runtime_only_observation_output(output)

        self.assertEqual(normalized["file_edits"], [])
        self.assertIn(
            "observation-only source edits were replaced by runtime compiled-signal selection",
            normalized["execution_advisories"],
        )

    def test_functional_rtl_edit_is_not_hidden_by_runtime_observation(self) -> None:
        output = {
            "status": "ready_to_apply",
            "adaptive_observation_decision": {
                "mode": "deepen_simulation_observation"
            },
            "file_edits": [
                {
                    "path": "/run/generated/board_integration/SpatialKernel.sv",
                    "operation": "replace_text",
                },
                {
                    "path": "/run/generated/board_integration/board_tb.sv",
                    "operation": "replace_text",
                },
            ],
        }

        normalized = runtime_only_observation_output(output)

        self.assertEqual(
            [row["path"] for row in normalized["file_edits"]],
            ["/run/generated/board_integration/SpatialKernel.sv"],
        )


if __name__ == "__main__":
    unittest.main()
