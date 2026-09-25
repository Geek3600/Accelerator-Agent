import copy
import hashlib
import json
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from accagent.framework import stage_input, stage_llm, stage_team
from accagent.framework.llm_config import LlmCfg, resolve_llm_cfg


class LlmRetryPathTests(unittest.TestCase):
    def _transient_then_success(self) -> list[object]:
        return [urllib.error.URLError("temporary upstream error") for _ in range(3)] + ['{"ok":true}']

    def test_compaction_exposes_current_observation_frontier_lock(self) -> None:
        package = {
            "generation_phase_contract": {
                "status": "repair_existing_board_sources",
                "current_vcs_feedback_ready": True,
            },
            "current_board_vcs_feedback": {
                "status": "ready",
                "diagnosis": {
                    "value": {
                        "failure_evidence": {
                            "sacg_cctg_causal_slice": {
                                "sha256": "a" * 64,
                                "value": {
                                    "earliest_unproven_frontier": {
                                        "frontier_id": "kernel_output_stream_completion"
                                    }
                                },
                            }
                        }
                    }
                },
            },
            "adaptive_observation_routing": {
                "status": "complete_boundary_coverage_required"
            },
            "adaptive_observation_state": {
                "decision": {"frontier_id": "connected_kernel_input_to_output"}
            },
            "exact_board_repair_attempt_history": {
                "intervention_response_history": {
                    "transitions": [
                        {
                            "agent_hypothesis": {
                                "causal_prediction": {
                                    "target_frontier_id": "connected_kernel_input_to_output"
                                }
                            }
                        }
                    ]
                }
            },
        }

        compact = stage_llm.compact_verification_capability_repair_package(package)
        lock = compact["adaptive_observation_decision_lock"]

        self.assertEqual(
            lock["frontier_id"], "kernel_output_stream_completion"
        )
        self.assertEqual(
            lock["allowed_modes"],
            [
                "direct_executed_contradiction",
                "direct_tool_failure",
                "deepen_simulation_observation",
            ],
        )
        self.assertIn("Copy this current frontier_id exactly", lock["instruction"])
        self.assertEqual(
            stage_llm.compact_verification_capability_repair_package(compact)[
                "adaptive_observation_decision_lock"
            ],
            lock,
        )

    def test_dse_compact_retry_preserves_complete_selection_evidence(self) -> None:
        candidates = [
            {
                "candidate_id": f"candidate_{index}",
                "parameters": {"lanes": 8 + index},
                "feasible": True,
                "measurement_status": "unmeasured",
            }
            for index in range(24)
        ]
        prompt = stage_llm.compact_retry_prompt(
            "dse_parameter_agent",
            "parameter_binding",
            "Select one legal candidate.",
            {
                "dse_selection_evidence": {
                    "candidate_count": 100,
                    "eligible_candidates": candidates,
                    "measured_pareto_candidates": [],
                },
                "dse_constraint_report": {
                    "candidate_count": 100,
                    "infeasible_candidates": [
                        {"candidate_id": f"bad_{index}"} for index in range(100)
                    ],
                },
                "formal_dse_campaign": {"campaign_complete": False},
            },
            {"type": "object", "properties": {"status": {"type": "string"}}},
        )

        compact_block = prompt.split("<compact_inputs>\n", 1)[1].split(
            "\n</compact_inputs>", 1
        )[0]
        compact = json.loads(compact_block)

        self.assertEqual(
            [row["candidate_id"] for row in compact["dse_selection_evidence"]["eligible_candidates"]],
            [row["candidate_id"] for row in candidates],
        )
        self.assertNotIn("infeasible_candidates", compact["dse_constraint_report"])
        self.assertEqual(compact["formal_dse_campaign"]["campaign_complete"], False)

    def test_explicit_403_capacity_limit_retries_but_other_403_does_not(self) -> None:
        capacity = urllib.error.HTTPError(
            "https://example.invalid",
            403,
            'curl direct HTTP/1.1 response 403; response_body={"error":{"type":"billing_error","message":"daily usage limit exceeded"}}',
            None,
            None,
        )
        denied = urllib.error.HTTPError(
            "https://example.invalid", 403, "Forbidden", None, None
        )
        with patch.dict(
            os.environ, {"SPATIALACC_LLM_CAPACITY_RETRY_SEC": "123"}
        ):
            self.assertTrue(stage_llm.transient_llm_error(capacity))
            self.assertEqual(stage_llm.retry_sleep_seconds(capacity, 1), 123.0)
        self.assertFalse(stage_llm.transient_llm_error(denied))

    def test_gateway_errors_retry_within_team_decomposition(self) -> None:
        def http_error(code: int, reason: str) -> urllib.error.HTTPError:
            return urllib.error.HTTPError(
                "https://example.invalid/v1/responses", code, reason, None, None
            )

        redirect_loop = http_error(
            302, "The HTTP server returned a redirect error that would lead to an infinite loop."
        )
        gateway_timeout = http_error(524, "origin timeout")
        gateway_route = http_error(530, "domain not configured")
        for error in (redirect_loop, gateway_timeout, gateway_route):
            self.assertTrue(stage_llm.transient_llm_error(error))
        self.assertFalse(stage_llm.transient_llm_error(http_error(302, "Found")))

        with (
            patch.object(
                stage_team,
                "read_response_text",
                side_effect=[redirect_loop, gateway_timeout, gateway_route, '{"ok":true}'],
            ) as request,
            patch.object(stage_team, "retry_sleep_seconds", return_value=0.0),
            patch.object(stage_team.time, "sleep"),
        ):
            text, errors = stage_team.post_decomposer_json(
                object(), 1, "team_decomposition_json", True
            )

        self.assertEqual(text, '{"ok":true}')
        self.assertEqual(len(errors), 3)
        self.assertEqual(request.call_count, 4)

    def test_websocket_upgrade_transport_error_is_transient(self) -> None:
        error = urllib.error.HTTPError(
            "https://example.invalid/v1/responses",
            426,
            'Upgrade Required; response_body={"error":{"message":"WebSocket upgrade required (Upgrade: websocket)"}}',
            None,
            None,
        )

        self.assertTrue(stage_llm.transient_llm_error(error))
        self.assertTrue(stage_llm.stream_transport_fallback_error(error))

    def test_stage0_websocket_upgrade_switches_retry_to_json(self) -> None:
        error = urllib.error.HTTPError(
            "https://example.invalid/v1/responses",
            426,
            'Upgrade Required; response_body={"error":{"message":"WebSocket upgrade required (Upgrade: websocket)"}}',
            None,
            None,
        )
        stream_modes: list[bool] = []

        def request_factory(use_stream: bool) -> object:
            return {"stream": use_stream}

        def fake_read(request: object, timeout_sec: int, stream: bool) -> str:
            del request, timeout_sec
            stream_modes.append(stream)
            if len(stream_modes) == 1:
                raise error
            return '{"ok":true}'

        with (
            patch.dict(os.environ, {"SPATIALACC_LLM_TRANSIENT_RETRY_UNBOUNDED": "1"}),
            patch.object(stage_input, "read_response_text", side_effect=fake_read),
            patch.object(stage_input, "retry_sleep_seconds", return_value=0.0),
            patch.object(stage_input.time, "sleep"),
        ):
            text, errors = stage_input.post_llm_json(
                request_factory, 1, "test", True
            )

        self.assertEqual(text, '{"ok":true}')
        self.assertEqual(len(errors), 1)
        self.assertEqual(stream_modes, [True, False])

    def test_checkpoint_specialist_uses_a_lower_lossless_compaction_threshold(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop(
                "SPATIALACC_CHECKPOINT_SPECIALIST_COMPACT_MIN_PROMPT_BYTES",
                None,
            )
            threshold = (
                stage_llm.checkpoint_specialist_auto_compact_min_prompt_bytes()
            )

        self.assertEqual(threshold, 256_000)
        self.assertLess(threshold, stage_llm.llm_auto_compact_min_prompt_bytes())

    def test_team_decomposer_honors_unbounded_transient_retry(self) -> None:
        with (
            patch.dict(
                os.environ,
                {
                    "SPATIALACC_LLM_TRANSIENT_RETRY_UNBOUNDED": "1",
                    "SPATIALACC_LLM_TRANSIENT_ATTEMPTS": "2",
                },
            ),
            patch.object(stage_team, "read_response_text", side_effect=self._transient_then_success()),
            patch.object(stage_team, "retry_sleep_seconds", return_value=0.0),
            patch.object(stage_team.time, "sleep"),
        ):
            text, errors = stage_team.post_decomposer_json(object(), 1, "test", True)

        self.assertEqual(text, '{"ok":true}')
        self.assertEqual(len(errors), 3)

    def test_checkpoint_capability_gap_is_not_in_exact_board_prompt_context(self) -> None:
        gap = {
            "status": "ready_for_capability_repair",
            "atomic_manifest_merge": {
                "operation": "merge_json",
                "target_path": "/run/generated/memory/dut_weight_binding_manifest.json",
                "expected_sha256": "a" * 64,
                "json_pointer": (
                    "/board_simulation_preflight_plan/testbench/"
                    "simulation_checkpoint_contract"
                ),
                "human_approval_required": False,
            },
        }
        compact = stage_llm.compact_exact_board_integration_context(
            {
                "schema_version": (
                    "spatialaccagent.exact_board_integration_repair_context.v1"
                ),
                "adaptive_design_inputs": {
                    "simulation_checkpoint_capability_gap": gap
                },
            }
        )

        self.assertNotIn(
            "simulation_checkpoint_capability_gap",
            compact["adaptive_design_inputs"],
        )

    def test_checkpoint_repair_route_survives_full_retry_compaction(self) -> None:
        violated = (
            "simulation_checkpoint_contract_and_hook_must_pass_before_hardware_repair"
        )
        compact = stage_llm.compact_for_retry(
            {
                "stage": "repair_execution",
                "repair_step": {
                    "id": "repair_step.00",
                    "scope": "verification_capability_repair",
                    "status": "ready_for_agent_patch",
                    "debug_layer": "board_axi_ddr_wrapped_system",
                    "action": {
                        "repair_kind": "verification_capability",
                        "repair_gate": "checkpoint_contract_validation",
                        "target_modules": ["functional_sim"],
                        "violated_contract": violated,
                        "reason": "materialize the checkpoint contract and hook first",
                    },
                },
                "verification_capability_repair_package": {
                    "schema_version": (
                        "spatialaccagent.verification_capability_repair_package.v0"
                    ),
                    "violated_contract": violated,
                    "generation_phase_contract": {
                        "status": "repair_existing_board_sources",
                        "checkpoint_capability_repair_required": True,
                        "hardware_rtl_repair_deferred_until_checkpoint_preflight": True,
                    },
                },
            }
        )

        self.assertEqual(
            compact["repair_step"]["action"]["violated_contract"], violated
        )
        phase = compact["verification_capability_repair_package"][
            "generation_phase_contract"
        ]
        self.assertTrue(phase["checkpoint_capability_repair_required"])
        self.assertTrue(
            phase["hardware_rtl_repair_deferred_until_checkpoint_preflight"]
        )

    def test_checkpoint_specialist_compaction_preserves_complete_source_and_authority(
        self,
    ) -> None:
        source = "module current_tb;\n" + ("  wire observed;\n" * 96) + "endmodule\n"
        source_sha256 = stage_llm._hash_text(source)
        manifest_path = "/run/generated/memory/dut_weight_binding_manifest.json"
        testbench_path = "/run/generated/board/current_tb.sv"
        runtime_failure = {
            "status": "ready",
            "restored_semantic_suffix_materialization": {
                "status": "fail",
                "source_sha256": "a" * 64,
                "invalid_records": [
                    {"line_number": 1, "raw_preview": '"output_valid":x'}
                ],
            },
            "checkpoint_artifacts": {
                "status": "fail",
                "runtime_execution_failure": {"status": "stale_recursive_copy"},
            },
        }
        specialist = {
            "schema_version": (
                "spatialaccagent.checkpoint_hook_specialist_package.v1"
            ),
            "status": "ready",
            "objective": "repair the current checkpoint hook",
            "failure": {"runtime_checkpoint_failure": runtime_failure},
            "debug_episode": {
                "schema_version": "spatialaccagent.simulation_checkpoint_debug_episode.v1",
                "status": "active",
                "episode_id": "episode-1",
                "checkpoint": {"status": "pending_same_source_certification"},
            },
            "checkpoint_authority": {
                "required_manifest_contract": {"schema_version": "contract.v1"}
            },
            "capability_gap": {
                "status": "ready_for_capability_repair",
                "runtime_execution_failure": runtime_failure,
            },
            "current_testbench_source": {
                "path": testbench_path,
                "sha256": source_sha256,
                "content": source,
                "complete_current_source": True,
            },
            "atomic_edit_contract": {
                "all_or_nothing": True,
                "exact_edit_count": 2,
                "allowed_and_required_paths": [manifest_path, testbench_path],
                "manifest": {
                    "path": manifest_path,
                    "expected_sha256": "b" * 64,
                    "operation": "merge_json",
                    "required_patch_root": [
                        "board_simulation_preflight_plan",
                        "testbench",
                        "simulation_checkpoint_contract",
                    ],
                },
                "testbench": {
                    "path": testbench_path,
                    "expected_sha256": source_sha256,
                    "operation": "replace_text",
                    "one_or_more_nonoverlapping_unique_old_text_new_text_pairs": True,
                },
                "no_production_rtl_edit": True,
            },
            "blockers": [],
        }
        compact_inputs = stage_llm._deduplicate_compact_projection(
            stage_llm.compact_for_retry(
                {
                    "stage": "repair_execution",
                    "agent": "exact_board_integration_generation_agent",
                    "verification_capability_repair_package": specialist,
                }
            )
        )

        errors = stage_llm.exact_board_compact_request_errors(compact_inputs)
        resolved = stage_llm._resolve_compact_dedup_references(
            compact_inputs,
            compact_inputs["verification_capability_repair_package"],
        )

        self.assertEqual(errors, [])
        self.assertEqual(resolved["current_testbench_source"]["content"], source)
        self.assertEqual(resolved["debug_episode"]["episode_id"], "episode-1")
        self.assertNotIn(
            "runtime_execution_failure",
            resolved["capability_gap"]["runtime_execution_failure"][
                "checkpoint_artifacts"
            ],
        )
        self.assertEqual(
            resolved["capability_gap"]["runtime_execution_failure"][
                "restored_semantic_suffix_materialization"
            ]["invalid_records"][0]["raw_preview"],
            '"output_valid":x',
        )

        bad = json.loads(json.dumps(specialist))
        bad["current_testbench_source"]["sha256"] = "0" * 64
        bad_inputs = stage_llm._deduplicate_compact_projection(
            stage_llm.compact_for_retry(
                {
                    "verification_capability_repair_package": bad,
                }
            )
        )
        self.assertIn(
            "checkpoint specialist testbench content hash differs",
            stage_llm.exact_board_compact_request_errors(bad_inputs),
        )

    def test_layer3_execution_checkpoint_is_absent_from_compaction(self) -> None:
        execution = {
            "status": "pass",
            "enabled": True,
            "mode": "cold_capture",
            "request_sha256": "a" * 64,
        }
        artifacts = {
            "status": "fail",
            "mode": "cold_capture",
            "errors": [
                "checkpoint capture report checkpoint_trigger_observed is not true"
            ],
        }
        compact = stage_llm.compact_verification_capability_repair_package(
            {
                "current_board_vcs_feedback": {
                    "status": "ready",
                    "diagnosis": {
                        "path": "/run/diagnosis.json",
                        "sha256": "b" * 64,
                        "value": {
                            "failure_class": (
                                "simulation_checkpoint_capability_missing_or_invalid"
                            ),
                            "failure_evidence": {
                                "failure_class": (
                                    "simulation_checkpoint_capability_missing_or_invalid"
                                ),
                                "first_real_error": artifacts["errors"][0],
                                "checkpoint_execution": execution,
                                "checkpoint_artifacts": artifacts,
                            },
                        },
                    },
                    "runner_report": {
                        "path": "/run/runner.json",
                        "sha256": "c" * 64,
                        "value": {
                            "status": "fail",
                            "phase": "remote_vcs",
                            "checkpoint_execution": execution,
                            "checkpoint_artifacts": artifacts,
                        },
                    },
                }
            }
        )

        feedback = compact["current_board_vcs_feedback"]
        diagnosis = feedback["diagnosis"]["value"]["failure_evidence"]
        runner = feedback["runner_report"]["value"]
        self.assertNotIn("checkpoint_execution", diagnosis)
        self.assertNotIn("checkpoint_artifacts", diagnosis)
        self.assertNotIn("checkpoint_execution", runner)
        self.assertNotIn("checkpoint_artifacts", runner)

    def test_post_vcs_compaction_uses_only_current_signal_epoch(self) -> None:
        package = {
            "generation_phase_contract": {
                "status": "repair_existing_board_sources",
                "current_vcs_feedback_ready": True,
            },
            "current_board_vcs_feedback": {
                "status": "ready",
                "diagnosis": {
                    "value": {
                        "failure_evidence": {
                            "sacg_cctg_causal_slice": {
                                "sha256": "a" * 64,
                                "value": {
                                    "earliest_unproven_frontier": {
                                        "frontier_id": "kernel_output_stream_completion"
                                    }
                                },
                            }
                        }
                    }
                },
                "runner_report": {
                    "value": {
                        "status": "fail",
                        "checkpoint_execution": {
                            "enabled": True,
                            "mode": "fast_replay",
                        },
                        "live_progress": {
                            "latest": {
                                "observation_epoch": {"generation": 8},
                                "last_cycle": 1234,
                                "first_stalled_boundary": (
                                    "kernel_output_stream_completion"
                                ),
                                "extra_signal_snapshots": [
                                    {
                                        "signal": "core.final_output_valid",
                                        "value": 0,
                                    }
                                ],
                            }
                        },
                        "runtime_signal_trace": {
                            "status": "ready",
                            "raw_stage_record_count": 285327,
                            "distinct_signal_count": 4412,
                            "stage_summaries": [
                                {
                                    "stage_id": "stage_08_residual_add_2",
                                    "scalar_signals": [
                                        {
                                            "signal": "core.io_out_valid",
                                            "last_sample": {"value": 0},
                                        }
                                    ],
                                }
                            ],
                        },
                    }
                },
            },
            "adaptive_observation_state": {
                "decision": {"frontier_id": "runtime_loader_completion"},
                "failed_state_recheck": {
                    "boundary": {
                        "summary": {
                            "old_signal": "runtime_loader_completion"
                        }
                    }
                },
            },
            "current_fresh_exact_source_provenance_replay": {
                "status": "ready",
                "replay_status": "fast_replay",
            },
        }

        compact = stage_llm.compact_verification_capability_repair_package(package)
        feedback = compact["current_board_vcs_feedback"]
        current_epoch = feedback["current_signal_epoch"]
        serialized = json.dumps(compact, sort_keys=True)

        self.assertEqual(
            current_epoch["value"]["first_stalled_boundary"],
            "kernel_output_stream_completion",
        )
        self.assertEqual(
            current_epoch["value"]["extra_signal_snapshots"][0]["signal"],
            "core.final_output_valid",
        )
        self.assertEqual(
            current_epoch["value"]["runtime_signal_trace"]
            ["distinct_signal_count"],
            4412,
        )
        self.assertNotIn("adaptive_observation_state", compact)
        self.assertNotIn("runtime_loader_completion", serialized)
        self.assertNotIn("checkpoint_execution", serialized)
        self.assertNotIn("fast_replay", serialized)

    def test_stage0_honors_unbounded_transient_retry(self) -> None:
        with (
            patch.dict(
                os.environ,
                {
                    "SPATIALACC_LLM_TRANSIENT_RETRY_UNBOUNDED": "1",
                    "SPATIALACC_LLM_TRANSIENT_ATTEMPTS": "2",
                },
            ),
            patch.object(stage_input, "read_response_text", side_effect=self._transient_then_success()),
            patch.object(stage_input, "retry_sleep_seconds", return_value=0.0),
            patch.object(stage_input.time, "sleep"),
        ):
            text, errors = stage_input.post_llm_json(object(), 1, "test", True)

        self.assertEqual(text, '{"ok":true}')
        self.assertEqual(len(errors), 3)

    def test_context_length_failure_is_not_retried_as_transient(self) -> None:
        error = RuntimeError(
            "response.failed: context_length_exceeded: Your input exceeds the context window"
        )
        with (
            patch.dict(os.environ, {"SPATIALACC_LLM_TRANSIENT_RETRY_UNBOUNDED": "1"}),
            patch.object(stage_llm, "call_llm", side_effect=error) as call,
            patch.object(stage_llm.time, "sleep") as sleep,
        ):
            with self.assertRaisesRegex(RuntimeError, "context_length_exceeded"):
                stage_llm.call_llm_with_retry(
                    "https://example.invalid",
                    "key",
                    "model",
                    "prompt",
                    "schema",
                    {},
                    60,
                )

        self.assertEqual(call.call_count, 1)
        sleep.assert_not_called()

    def test_incomplete_stream_without_output_is_retried(self) -> None:
        incomplete = ValueError(
            "streaming LLM response returned no output text; "
            "events=response.created; response.in_progress; response.output_item.added"
        )
        with (
            patch.dict(
                os.environ,
                {"SPATIALACC_LLM_TRANSIENT_RETRY_UNBOUNDED": "1"},
            ),
            patch.object(
                stage_llm, "call_llm", side_effect=[incomplete, '{"ok":true}']
            ) as call,
            patch.object(stage_llm, "retry_sleep_seconds", return_value=0.0),
            patch.object(stage_llm.time, "sleep") as sleep,
        ):
            text, errors = stage_llm.call_llm_with_retry(
                "https://example.invalid",
                "key",
                "model",
                "prompt",
                "schema",
                {},
                60,
            )

        self.assertEqual(text, '{"ok":true}')
        self.assertEqual(len(errors), 1)
        self.assertEqual(call.call_count, 2)
        sleep.assert_called_once()

    def test_stage_agent_retries_truncated_provider_json_without_exiting(self) -> None:
        decode_error = stage_llm.ResponseDecodeError(
            "SSE event",
            json.JSONDecodeError("Unterminated string starting at", "{\"x\":\"", 5),
        )
        valid = '{"status":"ready_to_apply","file_edits":[]}'
        output_schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "file_edits": {"type": "array"},
            },
            "required": ["status", "file_edits"],
        }
        stream_modes: list[bool | None] = []

        def fake_call(*args, **kwargs):
            stream_modes.append(kwargs.get("stream_override"))
            if len(stream_modes) == 1:
                raise decode_error
            return valid

        resolve_llm_cfg.cache_clear()
        with tempfile.TemporaryDirectory() as tmp:
            with (
                patch.dict(
                    os.environ,
                    {
                        "SPATIALACC_LLM_TRANSIENT_RETRY_UNBOUNDED": "1",
                        "SPATIALACC_LLM_STREAM": "1",
                        "SPATIALACC_LLM_AUTO_COMPACT_RETRY": "0",
                    },
                ),
                patch.object(
                    stage_llm,
                    "resolved_llm_cfg",
                    return_value=LlmCfg(
                        model="test-model",
                        endpoint="https://example.invalid",
                        api_key="key",
                        stream=True,
                    ),
                ),
                patch.object(stage_llm, "call_llm", side_effect=fake_call) as call,
                patch.object(stage_llm, "retry_sleep_seconds", return_value=0.0),
                patch.object(stage_llm.time, "sleep") as sleep,
            ):
                resolve_llm_cfg.cache_clear()
                record = stage_llm.run_stage_agent(
                    agent="exact_board_integration_generation_agent",
                    stage="repair_execution",
                    task="return the next evidence-grounded board repair",
                    inputs={"verification_capability_repair_package": {}},
                    out_dir=Path(tmp),
                    fallback_summary="verification capability repair requires LLM analysis",
                    output_schema=output_schema,
                )

        self.assertEqual(record["output"]["status"], "ready_to_apply")
        self.assertNotEqual(record["output"]["status"], "llm_error")
        self.assertEqual(call.call_count, 2)
        self.assertEqual(call.call_args_list[0].args[3], call.call_args_list[1].args[3])
        self.assertEqual(stream_modes, [None, False])
        self.assertIn("malformed or truncated JSON", record["retry_errors"][0])
        sleep.assert_called_once()
        resolve_llm_cfg.cache_clear()

    def test_output_budget_incomplete_large_prompt_enters_compact_retry(self) -> None:
        incomplete = stage_llm.ResponseIncompleteError(
            {
                "response": {
                    "id": "resp-test",
                    "incomplete_details": {"reason": "max_output_tokens"},
                }
            }
        )
        with (
            patch.dict(
                os.environ,
                {
                    "SPATIALACC_LLM_TRANSIENT_RETRY_UNBOUNDED": "1",
                    "SPATIALACC_LLM_AUTO_COMPACT_MIN_PROMPT_BYTES": "16",
                    "SPATIALACC_LLM_AUTO_COMPACT_AFTER_ATTEMPTS": "1",
                },
            ),
            patch.object(stage_llm, "call_llm", side_effect=incomplete) as call,
            patch.object(stage_llm.time, "sleep") as sleep,
        ):
            with self.assertRaises(stage_llm.PromptCompactionNeeded):
                stage_llm.call_llm_with_retry(
                    "https://example.invalid",
                    "key",
                    "model",
                    "this prompt is intentionally large enough",
                    "schema",
                    {},
                    60,
                )

        self.assertEqual(call.call_count, 1)
        sleep.assert_not_called()

    def test_compact_retry_keeps_parent_reasoning_effort(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("SPATIALACC_COMPACT_RETRY_REASONING_EFFORT", None)
            self.assertEqual(
                stage_llm.compact_retry_reasoning_effort("xhigh"),
                "xhigh",
            )

    def test_streaming_upstream_error_retries_once_with_json_transport(self) -> None:
        error = urllib.error.HTTPError(
            "https://example.invalid",
            502,
            "Bad Gateway; response_body={\"error\":{\"type\":\"upstream_error\"}}",
            None,
            None,
        )
        stream_modes: list[bool | None] = []

        def fake_call(*args, **kwargs):
            stream_modes.append(kwargs.get("stream_override"))
            if len(stream_modes) == 1:
                raise error
            return '{"ok":true}'

        resolve_llm_cfg.cache_clear()
        with (
            patch.dict(
                os.environ,
                {
                    "SPATIALACC_LLM_TRANSIENT_RETRY_UNBOUNDED": "1",
                    "SPATIALACC_LLM_STREAM": "1",
                },
            ),
            patch.object(stage_llm, "call_llm", side_effect=fake_call),
            patch.object(stage_llm, "retry_sleep_seconds", return_value=0.0),
            patch.object(stage_llm.time, "sleep"),
        ):
            resolve_llm_cfg.cache_clear()
            text, errors = stage_llm.call_llm_with_retry(
                "https://example.invalid",
                "key",
                "model",
                "prompt",
                "schema",
                {},
                60,
            )

        self.assertEqual(text, '{"ok":true}')
        self.assertEqual(len(errors), 1)
        self.assertEqual(stream_modes, [None, False])
        resolve_llm_cfg.cache_clear()

    def test_retry_observer_records_transport_recovery_events(self) -> None:
        error = urllib.error.HTTPError(
            "https://example.invalid",
            502,
            "Bad Gateway; response_body={\"error\":{\"type\":\"upstream_error\"}}",
            None,
            None,
        )
        events: list[dict[str, object]] = []
        resolve_llm_cfg.cache_clear()
        with (
            patch.dict(
                os.environ,
                {
                    "SPATIALACC_LLM_TRANSIENT_RETRY_UNBOUNDED": "1",
                    "SPATIALACC_LLM_STREAM": "1",
                },
            ),
            patch.object(stage_llm, "call_llm", side_effect=[error, '{"ok":true}']),
            patch.object(stage_llm, "retry_sleep_seconds", return_value=0.0),
            patch.object(stage_llm.time, "sleep"),
        ):
            resolve_llm_cfg.cache_clear()
            text, errors = stage_llm.call_llm_with_retry(
                "https://example.invalid",
                "key",
                "model",
                "prompt",
                "schema",
                {},
                60,
                transaction_observer=events.append,
            )

        self.assertEqual(text, '{"ok":true}')
        self.assertEqual(len(errors), 1)
        self.assertEqual(
            [str(event["kind"]) for event in events],
            [
                "attempt_started",
                "attempt_failed",
                "retry_scheduled",
                "attempt_started",
                "response_received",
            ],
        )
        self.assertEqual(events[0]["transport"], "responses_sse_stream")
        self.assertEqual(events[2]["next_transport"], "responses_json")
        resolve_llm_cfg.cache_clear()

    def test_json_disconnect_switches_retry_back_to_streaming_transport(self) -> None:
        streaming_error = urllib.error.HTTPError(
            "https://example.invalid",
            502,
            "Bad Gateway; response_body={\"error\":{\"type\":\"upstream_error\"}}",
            None,
            None,
        )
        json_disconnect = RuntimeError(
            "Remote end closed connection without response"
        )
        stream_modes: list[bool | None] = []
        failures = [streaming_error, json_disconnect]

        def fake_call(*args, **kwargs):
            stream_modes.append(kwargs.get("stream_override"))
            if failures:
                raise failures.pop(0)
            return '{"ok":true}'

        resolve_llm_cfg.cache_clear()
        with (
            patch.dict(
                os.environ,
                {
                    "SPATIALACC_LLM_TRANSIENT_RETRY_UNBOUNDED": "1",
                    "SPATIALACC_LLM_STREAM": "1",
                },
            ),
            patch.object(stage_llm, "call_llm", side_effect=fake_call),
            patch.object(stage_llm, "retry_sleep_seconds", return_value=0.0),
            patch.object(stage_llm.time, "sleep"),
        ):
            resolve_llm_cfg.cache_clear()
            text, errors = stage_llm.call_llm_with_retry(
                "https://example.invalid",
                "key",
                "model",
                "prompt",
                "schema",
                {},
                60,
            )

        self.assertEqual(text, '{"ok":true}')
        self.assertEqual(len(errors), 2)
        self.assertEqual(stream_modes, [None, False, True])
        resolve_llm_cfg.cache_clear()

    def test_json_default_switches_retry_to_streaming_transport(self) -> None:
        json_error = urllib.error.HTTPError(
            "https://example.invalid",
            502,
            "Bad Gateway; response_body={\"error\":{\"type\":\"upstream_error\"}}",
            None,
            None,
        )
        stream_modes: list[bool | None] = []

        def fake_call(*args, **kwargs):
            stream_modes.append(kwargs.get("stream_override"))
            if len(stream_modes) == 1:
                raise json_error
            return '{"ok":true}'

        resolve_llm_cfg.cache_clear()
        with (
            patch.dict(
                os.environ,
                {
                    "SPATIALACC_LLM_TRANSIENT_RETRY_UNBOUNDED": "1",
                    "SPATIALACC_LLM_STREAM": "0",
                },
            ),
            patch.object(stage_llm, "call_llm", side_effect=fake_call),
            patch.object(stage_llm, "retry_sleep_seconds", return_value=0.0),
            patch.object(stage_llm.time, "sleep"),
        ):
            resolve_llm_cfg.cache_clear()
            text, errors = stage_llm.call_llm_with_retry(
                "https://example.invalid",
                "key",
                "model",
                "prompt",
                "schema",
                {},
                60,
            )

        self.assertEqual(text, '{"ok":true}')
        self.assertEqual(len(errors), 1)
        self.assertEqual(stream_modes, [None, True])
        resolve_llm_cfg.cache_clear()

    def test_large_prompt_transient_failures_trigger_compact_retry_signal(self) -> None:
        error = urllib.error.HTTPError("https://example.invalid", 502, "Bad Gateway", None, None)
        resolve_llm_cfg.cache_clear()
        with (
            patch.dict(
                os.environ,
                {
                    "SPATIALACC_LLM_TRANSIENT_RETRY_UNBOUNDED": "1",
                    "SPATIALACC_LLM_STREAM": "1",
                    "SPATIALACC_LLM_AUTO_COMPACT_MIN_PROMPT_BYTES": "16",
                    "SPATIALACC_LLM_AUTO_COMPACT_AFTER_ATTEMPTS": "2",
                },
            ),
            patch.object(stage_llm, "call_llm", side_effect=[error, error]),
            patch.object(stage_llm, "retry_sleep_seconds", return_value=0.0),
            patch.object(stage_llm.time, "sleep"),
        ):
            resolve_llm_cfg.cache_clear()
            with self.assertRaises(stage_llm.PromptCompactionNeeded):
                stage_llm.call_llm_with_retry(
                    "https://example.invalid",
                    "key",
                    "model",
                    "this prompt is intentionally large enough",
                    "schema",
                    {},
                    60,
                )
        resolve_llm_cfg.cache_clear()

    def test_stage_agent_compact_retry_keeps_custom_output_schema(self) -> None:
        custom_schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "file_edits": {"type": "array"},
            },
            "required": ["status", "file_edits"],
        }
        compact_output = '{"status":"ready_to_apply","file_edits":[]}'
        with tempfile.TemporaryDirectory() as tmp:
            with (
                patch.object(
                    stage_llm,
                    "resolved_llm_cfg",
                    return_value=LlmCfg(
                        model="test-model",
                        endpoint="https://example.invalid",
                        api_key="key",
                        stream=True,
                    ),
                ),
                patch.object(
                    stage_llm,
                    "call_llm_with_retry",
                    side_effect=[stage_llm.PromptCompactionNeeded("large prompt"), (compact_output, [])],
                ) as call,
            ):
                record = stage_llm.run_stage_agent(
                    agent="implementation_agent",
                    stage="repair_execution",
                    task="return implementation repair",
                    inputs={"verification_capability_repair_package": {"schema_version": "spatialaccagent.verification_capability_repair_package.v0"}},
                    out_dir=Path(tmp),
                    fallback_summary="fallback",
                    output_schema=custom_schema,
                )

        self.assertEqual(record["output"]["status"], "ready_to_apply")
        self.assertEqual(call.call_args_list[1].args[5], custom_schema)

    def test_stage_agent_direct_context_failure_enters_compact_retry(self) -> None:
        custom_schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "file_edits": {"type": "array"},
            },
            "required": ["status", "file_edits"],
        }
        context_error = RuntimeError(
            "response.failed: context_length_exceeded: input exceeds the context window"
        )
        compact_output = '{"status":"ready_to_apply","file_edits":[]}'
        with tempfile.TemporaryDirectory() as tmp:
            with (
                patch.object(
                    stage_llm,
                    "resolved_llm_cfg",
                    return_value=LlmCfg(
                        model="test-model",
                        endpoint="https://example.invalid",
                        api_key="key",
                        stream=True,
                    ),
                ),
                patch.object(
                    stage_llm,
                    "call_llm_with_retry",
                    side_effect=[context_error, (compact_output, [])],
                ) as call,
            ):
                record = stage_llm.run_stage_agent(
                    agent="implementation_agent",
                    stage="repair_execution",
                    task="return implementation repair",
                    inputs={"verification_capability_repair_package": {"schema_version": "test.package.v0"}},
                    out_dir=Path(tmp),
                    fallback_summary="fallback",
                    output_schema=custom_schema,
                )

        self.assertEqual(record["output"]["status"], "ready_to_apply")
        self.assertEqual(call.call_count, 2)
        self.assertIn("context_length_exceeded", record["compact_retry_after_error"])

    def test_stage_agent_retries_schema_repair_serially_until_valid(self) -> None:
        custom_schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "file_edits": {"type": "array"},
            },
            "required": ["status", "file_edits"],
        }
        valid = '{"status":"ready_to_apply","file_edits":[]}'
        with tempfile.TemporaryDirectory() as tmp:
            with (
                patch.dict(
                    os.environ,
                    {
                        "SPATIALACC_LLM_AUTO_COMPACT_RETRY": "0",
                        "SPATIALACC_LLM_SCHEMA_REPAIR_ATTEMPTS": "2",
                    },
                ),
                patch.object(
                    stage_llm,
                    "resolved_llm_cfg",
                    return_value=LlmCfg(
                        model="test-model",
                        endpoint="https://example.invalid",
                        api_key="key",
                        stream=True,
                    ),
                ),
                patch.object(
                    stage_llm,
                    "call_llm_with_retry",
                    side_effect=[
                        ('{"status":"ready_to_apply"}', []),
                        ('{"status":"still_invalid"}', []),
                        (valid, []),
                    ],
                ) as call,
            ):
                record = stage_llm.run_stage_agent(
                    agent="implementation_agent",
                    stage="repair_execution",
                    task="return implementation repair",
                    inputs={"verification_capability_repair_package": {}},
                    out_dir=Path(tmp),
                    fallback_summary="fallback",
                    output_schema=custom_schema,
                )

            repair_paths = [
                Path(row["output_path"])
                for row in record["schema_repair_attempts"]
            ]
            repair_artifacts_exist = all(path.is_file() for path in repair_paths)

        self.assertEqual(record["output"]["status"], "ready_to_apply")
        self.assertEqual(call.call_count, 3)
        self.assertEqual(
            [row["status"] for row in record["schema_repair_attempts"]],
            ["invalid", "pass"],
        )
        self.assertTrue(repair_artifacts_exist)

    def test_stage_agent_repair_names_missing_root_field_placement(self) -> None:
        custom_schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "operator_leaf_dag": {"type": "object"},
                "executable_actions": {"type": "array"},
                "approval_required_for": {"type": "array"},
            },
            "required": [
                "status",
                "executable_actions",
                "approval_required_for",
            ],
        }
        malformed = json.dumps(
            {
                "status": "blocked",
                "operator_leaf_dag": {
                    "executable_actions": [],
                    "approval_required_for": [],
                },
            }
        )
        valid = json.dumps(
            {
                "status": "blocked",
                "operator_leaf_dag": {},
                "executable_actions": [],
                "approval_required_for": [],
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            with (
                patch.dict(
                    os.environ,
                    {"SPATIALACC_LLM_AUTO_COMPACT_RETRY": "0"},
                ),
                patch.object(
                    stage_llm,
                    "resolved_llm_cfg",
                    return_value=LlmCfg(
                        model="test-model",
                        endpoint="https://example.invalid",
                        api_key="key",
                        stream=True,
                    ),
                ),
                patch.object(
                    stage_llm,
                    "call_llm_with_retry",
                    side_effect=[(malformed, []), (valid, [])],
                ) as call,
            ):
                record = stage_llm.run_stage_agent(
                    agent="verification_agent",
                    stage="verification_artifacts",
                    task="return verification plan",
                    inputs={"verification_contract": {}},
                    out_dir=Path(tmp),
                    fallback_summary="fallback",
                    output_schema=custom_schema,
                )

        repair_prompt = call.call_args_list[1].args[3]
        self.assertEqual(record["output"]["executable_actions"], [])
        self.assertIn("Top-level placement correction", repair_prompt)
        self.assertIn("executable_actions", repair_prompt)
        self.assertIn("approval_required_for", repair_prompt)
        self.assertIn("direct members of the returned root object", repair_prompt)

    def test_stage_agent_keeps_schema_repairing_after_configured_window(self) -> None:
        custom_schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "file_edits": {"type": "array"},
            },
            "required": ["status", "file_edits"],
        }
        invalid = '{"status":"still_invalid"}'
        valid = '{"status":"ready_to_apply","file_edits":[]}'
        with tempfile.TemporaryDirectory() as tmp:
            with (
                patch.dict(
                    os.environ,
                    {
                        "SPATIALACC_LLM_AUTO_COMPACT_RETRY": "0",
                        "SPATIALACC_LLM_SCHEMA_REPAIR_ATTEMPTS": "2",
                        "SPATIALACC_LLM_SCHEMA_REPAIR_RETRY_UNBOUNDED": "1",
                    },
                ),
                patch.object(
                    stage_llm,
                    "resolved_llm_cfg",
                    return_value=LlmCfg(
                        model="test-model",
                        endpoint="https://example.invalid",
                        api_key="key",
                        stream=True,
                    ),
                ),
                patch.object(
                    stage_llm,
                    "call_llm_with_retry",
                    side_effect=[
                        (invalid, []),
                        (invalid, []),
                        (invalid, []),
                        (valid, []),
                    ],
                ) as call,
                patch.object(stage_llm.time, "sleep") as sleep,
            ):
                record = stage_llm.run_stage_agent(
                    agent="implementation_agent",
                    stage="repair_execution",
                    task="return implementation repair",
                    inputs={"verification_capability_repair_package": {}},
                    out_dir=Path(tmp),
                    fallback_summary="fallback",
                    output_schema=custom_schema,
                )

        self.assertEqual(record["output"]["status"], "ready_to_apply")
        self.assertEqual(call.call_count, 4)
        self.assertEqual(
            [row["status"] for row in record["schema_repair_attempts"]],
            ["invalid", "invalid", "pass"],
        )
        sleep.assert_called_once()

    def test_stage_agent_repairs_flattened_file_edit_items(self) -> None:
        custom_schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "file_edits": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "operation": {"type": "string"},
                        },
                        "required": ["path", "operation"],
                    },
                },
            },
            "required": ["status", "file_edits"],
        }
        malformed = json.dumps(
            {
                "status": "ready_to_apply",
                "file_edits": [{"path": "a"}, "operation", "replace"],
            }
        )
        valid = json.dumps(
            {
                "status": "ready_to_apply",
                "file_edits": [{"path": "a", "operation": "replace"}],
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            with (
                patch.dict(
                    os.environ,
                    {"SPATIALACC_LLM_AUTO_COMPACT_RETRY": "0"},
                ),
                patch.object(
                    stage_llm,
                    "resolved_llm_cfg",
                    return_value=LlmCfg(
                        model="test-model",
                        endpoint="https://example.invalid",
                        api_key="key",
                        stream=True,
                    ),
                ),
                patch.object(
                    stage_llm,
                    "call_llm_with_retry",
                    side_effect=[(malformed, []), (valid, [])],
                ) as call,
            ):
                record = stage_llm.run_stage_agent(
                    agent="implementation_agent",
                    stage="repair_execution",
                    task="return implementation repair",
                    inputs={"verification_capability_repair_package": {}},
                    out_dir=Path(tmp),
                    fallback_summary="fallback",
                    output_schema=custom_schema,
                )

        self.assertEqual(call.call_count, 2)
        self.assertEqual(record["schema_repair_attempts"][0]["status"], "pass")
        self.assertIn("file_edits[0].operation is required", record["parse_error"])
        self.assertIn("never flatten", call.call_args_list[1].args[3])

    def test_cached_stage_worker_rejects_nested_schema_corruption(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "file_edits": {
                    "type": "array",
                    "items": {"type": "object"},
                },
            },
            "required": ["status", "file_edits"],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "record.json"
            path.write_text(
                json.dumps(
                    {
                        "prompt_hash": "hash",
                        "error": None,
                        "used_fallback": False,
                        "output": {
                            "status": "ready_to_apply",
                            "file_edits": [{"path": "a"}, "operation"],
                        },
                    }
                ),
                encoding="utf-8",
            )
            cached = stage_llm.cached_stage_worker_record(
                path,
                "hash",
                "implementation_agent",
                schema,
            )

        self.assertIsNone(cached)

    def test_checkpoint_hook_specialist_prompt_omits_broad_agent_memory(self) -> None:
        custom_schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "file_edits": {"type": "array"},
            },
            "required": ["status", "file_edits"],
        }
        output = '{"status":"ready_to_apply","file_edits":[]}'
        with tempfile.TemporaryDirectory() as tmp:
            with (
                patch.dict(
                    os.environ,
                    {"SPATIALACC_LLM_AUTO_COMPACT_RETRY": "0"},
                ),
                patch.object(
                    stage_llm,
                    "resolved_llm_cfg",
                    return_value=LlmCfg(
                        model="test-model",
                        endpoint="https://example.invalid",
                        api_key="key",
                        stream=True,
                    ),
                ),
                patch.object(stage_llm, "read_sacg_json", return_value={}),
                patch.object(
                    stage_llm,
                    "sacg_memory_summary",
                    return_value={"payload": "BROAD_MEMORY_SENTINEL"},
                ),
                patch.object(
                    stage_llm,
                    "sacg_memory_truth",
                    return_value={"payload": "BROAD_TRUTH_SENTINEL"},
                ),
                patch.object(
                    stage_llm,
                    "call_llm_with_retry",
                    return_value=(output, []),
                ) as call,
            ):
                stage_llm.run_stage_agent(
                    agent="exact_board_integration_generation_agent",
                    stage="repair_execution",
                    task="generate checkpoint hook",
                    inputs={
                        "source_sacg_state": "/run/sacg_state.json",
                        "verification_capability_repair_package": {
                            "schema_version": (
                                "spatialaccagent.checkpoint_hook_specialist_package.v1"
                            ),
                            "current_testbench_source": {
                                "content": "CURRENT_TESTBENCH_SENTINEL"
                            },
                        },
                    },
                    out_dir=Path(tmp),
                    fallback_summary="fallback",
                    output_schema=custom_schema,
                )
            prompt = call.call_args.args[3]

        self.assertIn("CURRENT_TESTBENCH_SENTINEL", prompt)
        self.assertNotIn("BROAD_MEMORY_SENTINEL", prompt)
        self.assertNotIn("BROAD_TRUTH_SENTINEL", prompt)
        self.assertNotIn("<action_grounding_registry>", prompt)
        self.assertIn("broad_sacg_history_omitted", prompt)

    def test_repair_agent_prompt_uses_only_current_hierarchy_memory(self) -> None:
        custom_schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "file_edits": {"type": "array"},
            },
            "required": ["status", "file_edits"],
        }
        output = '{"status":"ready_to_apply","file_edits":[]}'
        with tempfile.TemporaryDirectory() as tmp:
            with (
                patch.dict(os.environ, {"SPATIALACC_LLM_AUTO_COMPACT_RETRY": "0"}),
                patch.object(
                    stage_llm,
                    "resolved_llm_cfg",
                    return_value=LlmCfg(
                        model="test-model",
                        endpoint="https://example.invalid",
                        api_key="key",
                        stream=True,
                    ),
                ),
                patch.object(stage_llm, "read_sacg_json", return_value={}),
                patch.object(
                    stage_llm,
                    "sacg_memory_summary",
                    return_value={"payload": "BROAD_MEMORY_SENTINEL"},
                ),
                patch.object(
                    stage_llm,
                    "scoped_sacg_memory_summary",
                    return_value={"payload": "LEAF_MEMORY_SENTINEL"},
                ) as scoped,
                patch.object(
                    stage_llm,
                    "scoped_sacg_memory_truth",
                    return_value={"payload": "LEAF_TRUTH_SENTINEL"},
                ) as scoped_truth,
                patch.object(
                    stage_llm,
                    "sacg_memory_truth",
                    return_value={"payload": "BROAD_TRUTH_SENTINEL"},
                ),
                patch.object(
                    stage_llm,
                    "call_llm_with_retry",
                    return_value=(output, []),
                ) as call,
            ):
                stage_llm.run_stage_agent(
                    agent="verification_capability_repair_agent",
                    stage="repair_execution",
                    task="repair the current leaf harness binding",
                    inputs={
                        "source_sacg_state": "/run/sacg_state.json",
                        "repair_step": {
                            "action": {"debug_layer": "operator_leaf_modules"}
                        },
                        "verification_capability_repair_package": {
                            "schema_version": (
                                "spatialaccagent.verification_capability_repair_package.v0"
                            ),
                            "verification_scope": "operator_leaf_closure",
                            "debug_layer": "operator_leaf_modules",
                        },
                    },
                    out_dir=Path(tmp),
                    fallback_summary="fallback",
                    output_schema=custom_schema,
                )
            prompt = call.call_args.args[3]

        self.assertIn("LEAF_MEMORY_SENTINEL", prompt)
        self.assertIn("LEAF_TRUTH_SENTINEL", prompt)
        self.assertNotIn("BROAD_MEMORY_SENTINEL", prompt)
        self.assertNotIn("BROAD_TRUTH_SENTINEL", prompt)
        scoped.assert_called_once_with(
            {},
            verification_scope="operator_leaf_closure",
            debug_layer="operator_leaf_modules",
        )
        scoped_truth.assert_called_once_with(
            {},
            verification_scope="operator_leaf_closure",
            debug_layer="operator_leaf_modules",
        )

    def test_post_vcs_board_prompt_omits_broad_memory_and_action_catalogs(self) -> None:
        inputs = {
            "source_sacg_state": "/run/sacg_state.json",
            "repair_step": {"id": "redundant_hot_loop_step"},
            "verification_capability_repair_package": {
                "generation_phase_contract": {
                    "status": "repair_existing_board_sources",
                    "current_vcs_feedback_ready": True,
                },
                "current_board_vcs_feedback": {"status": "ready"},
            },
        }
        with (
            patch.object(stage_llm, "read_sacg_json", return_value={}),
            patch.object(
                stage_llm,
                "scoped_sacg_memory_summary",
                return_value={"payload": "BROAD_MEMORY_SENTINEL"},
            ) as broad_memory,
            patch.object(
                stage_llm,
                "scoped_sacg_memory_truth",
                return_value={"payload": "BROAD_TRUTH_SENTINEL"},
            ) as broad_truth,
            patch.object(
                stage_llm,
                "hierarchical_learning_context",
                return_value={"certified_invariant": "LOWER_LAYER_SENTINEL"},
            ),
        ):
            prompt_inputs, _, _ = stage_llm.build_stage_agent_prompt_inputs(inputs)

        broad_memory.assert_not_called()
        broad_truth.assert_not_called()
        self.assertNotIn("sacg_memory", prompt_inputs)
        self.assertNotIn("sacg_memory_truth", prompt_inputs)
        self.assertNotIn("action_grounding_registry", prompt_inputs)
        self.assertNotIn("action_contract_examples", prompt_inputs)
        self.assertNotIn("source_sacg_state", prompt_inputs)
        self.assertNotIn("repair_step", prompt_inputs)
        self.assertEqual(
            prompt_inputs["hierarchical_learning_context"]["certified_invariant"],
            "LOWER_LAYER_SENTINEL",
        )

    def test_post_vcs_board_prompt_omits_empty_lower_layer_status(self) -> None:
        inputs = {
            "source_sacg_state": "/run/sacg_state.json",
            "verification_capability_repair_package": {
                "generation_phase_contract": {
                    "status": "repair_existing_board_sources",
                    "current_vcs_feedback_ready": True,
                },
            },
        }
        with (
            patch.object(stage_llm, "read_sacg_json", return_value={}),
            patch.object(
                stage_llm,
                "hierarchical_learning_context",
                return_value={
                    "status": "no_validated_lower_layer_evidence",
                    "validated_lower_layer_certificates": [],
                },
            ),
        ):
            prompt_inputs, _, learning_context = stage_llm.build_stage_agent_prompt_inputs(
                inputs
            )

        self.assertNotIn("hierarchical_learning_context", prompt_inputs)
        self.assertEqual(learning_context, {})

    def test_current_board_contradiction_uses_focused_repair_context(self) -> None:
        inputs = {
            "source_sacg_state": "/run/sacg_state.json",
            "repair_step": {"id": "current_trace_route"},
            "verification_capability_repair_package": {
                "current_board_to_lower_layer_contradiction": {
                    "status": "proven",
                    "target_debug_layer": "single_transformer_layer_kernel",
                    "evidence": {
                        "source_binding": {"board_trace_sha256": "a" * 64},
                        "direct_kernel_boundary_observations": {
                            "kernel_start_accepted": True,
                            "kernel_ingress_complete": True,
                            "kernel_egress_ready": True,
                        },
                        "causal_localization": {
                            "named_contract_boundary_id": "kernel.mlp_down.output"
                        },
                    },
                }
            },
        }
        with patch.object(stage_llm, "read_sacg_json", return_value={}):
            prompt_inputs, _, _ = stage_llm.build_stage_agent_prompt_inputs(inputs)

        self.assertNotIn("source_sacg_state", prompt_inputs)
        package = prompt_inputs["verification_capability_repair_package"]
        self.assertEqual(
            package["current_board_to_lower_layer_contradiction"][
                "target_debug_layer"
            ],
            "single_transformer_layer_kernel",
        )
        self.assertEqual(package["repair_routing_priority"]["status"], "authoritative")

    def test_post_vcs_learning_context_keeps_timing_without_identity_catalogs(self) -> None:
        compact = stage_llm.compact_hierarchical_learning_context(
            {
                "status": "pass",
                "validated_lower_layer_certificates": [
                    {
                        "scope": "single_layer_closure",
                        "level_id": "single_layer_functional",
                        "required_gates": ["a", "b"],
                        "path": "/run/certificate.json",
                        "file_sha256": "a" * 64,
                        "evidence_binding_sha256": "b" * 64,
                    }
                ],
                "kernel_timing_knowledge": [
                    {
                        "kind": "connected_kernel_pipeline_timing",
                        "pipeline_semantics": "elastic_rate_insensitive_token_pipeline",
                        "accepted_trace_record_count": 416,
                        "planned_stage_count": 9,
                        "maximum_concurrent_stage_count": 9,
                        "all_planned_stages_same_cycle_concurrency_required": False,
                        "required_dependency_overlap_complete": True,
                        "required_direct_dependency_overlap_summary": {
                            "all_different_token_overlap_observed": True
                        },
                        "path": "/run/functional_report.json",
                        "trace_sha256": "c" * 64,
                    }
                ],
                "decision_policy": {
                    "lower_layer_reopen_requires_current_trace_named_contradiction": True
                },
                "resolved_evidence_lessons": [
                    {"lesson": "reuse the certified kernel", "path": "/first"},
                    {"lesson": "reuse the certified kernel", "path": "/second"},
                ],
            }
        )

        serialized = json.dumps(compact, sort_keys=True)
        timing = compact["connected_kernel_timing"][0]
        self.assertEqual(timing["accepted_trace_record_count"], 416)
        self.assertFalse(
            timing["all_planned_stages_same_cycle_concurrency_required"]
        )
        self.assertTrue(
            timing["required_direct_dependency_overlap_summary"][
                "all_different_token_overlap_observed"
            ]
        )
        self.assertNotIn("/run/", serialized)
        self.assertNotIn("sha256", serialized)
        self.assertEqual(len(compact["resolved_mechanism_lessons"]), 1)

    def test_post_vcs_compact_retry_keeps_validated_hardware_understanding(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "file_edits": {"type": "array"},
            },
            "required": ["status", "file_edits"],
        }
        inputs = {
            "source_sacg_state": "/run/sacg_state.json",
            "verification_capability_repair_package": {
                "generation_phase_contract": {
                    "status": "repair_existing_board_sources",
                    "current_vcs_feedback_ready": True,
                }
            },
        }
        with (
            patch.object(stage_llm, "read_sacg_json", return_value={}),
            patch.object(
                stage_llm,
                "hierarchical_learning_context",
                return_value={
                    "status": "pass",
                    "validated_lower_layer_certificates": [
                        {
                            "scope": "single_layer_closure",
                            "level_id": "single_layer_functional",
                            "required_gates": ["gate"],
                        }
                    ],
                    "kernel_timing_knowledge": [
                        {
                            "pipeline_semantics": "elastic_rate_insensitive_token_pipeline",
                            "all_planned_stages_same_cycle_concurrency_required": False,
                        }
                    ],
                },
            ),
            patch.object(
                stage_llm,
                "exact_board_compact_request_errors",
                return_value=[],
            ),
            patch.object(
                stage_llm,
                "compact_verification_capability_repair_package",
                wraps=stage_llm.compact_verification_capability_repair_package,
            ) as package_compactor,
        ):
            prompt = stage_llm.compact_retry_prompt(
                "exact_board_integration_generation_agent",
                "repair_execution",
                "repair current board sources",
                inputs,
                schema,
            )

        package_compactor.assert_called_once()
        compact_block = prompt.split("<compact_inputs>\n", 1)[1].split(
            "\n</compact_inputs>", 1
        )[0]
        compact_inputs = json.loads(compact_block)
        learning = compact_inputs["hierarchical_learning_context"]
        self.assertEqual(
            learning["validated_lower_layers"][0]["scope"],
            "single_layer_closure",
        )
        self.assertFalse(
            learning["connected_kernel_timing"][0][
                "all_planned_stages_same_cycle_concurrency_required"
            ]
        )

    def test_capability_compaction_keeps_complete_declared_source_authority(self) -> None:
        template_path = "/run/generated/templates/Linear.scala"
        harness_path = "/run/generated/semantic_harness/LeafHarness.scala"
        template_content = "template-head\n" + "t" * 20_000 + "\ntemplate-tail\n"
        harness_content = "harness-head\n" + "h" * 20_000 + "\nharness-tail\n"
        unrelated_content = "report-head\n" + "r" * 20_000 + "\nreport-tail\n"
        requirements_path = (
            "/run/verification/semantic_testbench/dut_weight_binding_requirements.json"
            "#operator_leaf_closure_requirements_projection"
        )
        requirements = {
            "stage_requirements": [
                {
                    "stage_id": "stage_00",
                    "required_tensor_sha256": ["a" * 64],
                    "weight_layout": {"contract_sha256": "b" * 64},
                    "runtime_constant_contract_sha256": "c" * 64,
                }
            ],
            "agent_manifest_schema": {"required": ["stage_harnesses"]},
        }
        execution_path = (
            "/run/verification/semantic_testbench/semantic_testbench_manifest.json"
            "#operator_leaf_closure_execution_projection"
        )
        execution = {
            "status": "incomplete",
            "stage_contracts": [
                {
                    "stage_id": "stage_00",
                    "weight_layout_contract_sha256": "b" * 64,
                }
            ],
        }
        package = {
            "schema_version": "spatialaccagent.verification_capability_repair_package.v0",
            "verification_scope": "operator_leaf_closure",
            "debug_layer": "operator_leaf_modules",
            "repair_source_bundle": {
                "schema_version": "test.bundle.v1",
                "status": "ready",
                "documents": [
                    {"path": template_path, "content": template_content},
                    {"path": harness_path, "content": harness_content},
                    {
                        "path": requirements_path,
                        "content": json.dumps(requirements, sort_keys=True),
                        "projection": True,
                    },
                    {
                        "path": execution_path,
                        "content": json.dumps(execution, sort_keys=True),
                        "projection": True,
                    },
                    {"path": "/run/old_board_report.txt", "content": unrelated_content},
                ],
                "editable_contract": {
                    "read_only_template_sources": [template_path],
                    "approved_bounded_template_repair_exact_files": [],
                    "allowed_exact_files": [],
                    "allowed_create_or_replace_roots": [
                        "/run/generated/semantic_harness"
                    ],
                },
            },
        }

        compact = stage_llm.compact_verification_capability_repair_package(package)
        rows = {
            row["path"]: row
            for row in compact["repair_source_bundle"]["documents"]
        }

        self.assertEqual(rows[template_path]["content"], template_content)
        self.assertEqual(rows[harness_path]["content"], harness_content)
        self.assertEqual(rows[requirements_path]["json_content"], requirements)
        self.assertEqual(rows[execution_path]["json_content"], execution)
        self.assertNotIn("content", rows["/run/old_board_report.txt"])
        self.assertEqual(rows["/run/old_board_report.txt"]["content_chars"], len(unrelated_content))

    def test_large_implementation_prompt_is_compacted_before_transport(self) -> None:
        custom_schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "file_edits": {"type": "array"},
            },
            "required": ["status", "file_edits"],
        }
        output = '{"status":"ready_to_apply","file_edits":[]}'
        with tempfile.TemporaryDirectory() as tmp:
            with (
                patch.dict(
                    os.environ,
                    {
                        "SPATIALACC_LLM_AUTO_COMPACT_RETRY": "1",
                        "SPATIALACC_LLM_AUTO_COMPACT_MIN_PROMPT_BYTES": "1",
                    },
                ),
                patch.object(
                    stage_llm,
                    "resolved_llm_cfg",
                    return_value=LlmCfg(
                        model="test-model",
                        endpoint="https://example.invalid",
                        api_key="key",
                        stream=True,
                    ),
                ),
                patch.object(
                    stage_llm,
                    "call_llm_with_retry",
                    return_value=(output, []),
                ) as call,
            ):
                record = stage_llm.run_stage_agent(
                    agent="implementation_agent",
                    stage="repair_execution",
                    task="return implementation repair",
                    inputs={
                        "verification_capability_repair_package": {
                            "schema_version": "spatialaccagent.verification_capability_repair_package.v1",
                            "repair_source_bundle": {"documents": []},
                        }
                    },
                    out_dir=Path(tmp),
                    fallback_summary="fallback",
                    output_schema=custom_schema,
                    prompt_rules=["CUSTOM_RULE_SURVIVES_COMPACTION"],
                )

        self.assertEqual(call.call_count, 1)
        self.assertTrue(record["proactive_prompt_compaction"])
        self.assertIn("compact_retry_prompt", record["request_path"])
        self.assertGreater(record["full_prompt_bytes"], record["prompt_bytes"])
        self.assertIn("CUSTOM_RULE_SURVIVES_COMPACTION", call.call_args.args[3])

    def test_compact_projection_bounds_long_source_text(self) -> None:
        source = "x" * 100_000
        projection = stage_llm._json_document_projection({"source": source})

        self.assertIsInstance(projection["source"], dict)
        self.assertEqual(projection["source"]["text_chars"], len(source))
        self.assertEqual(projection["source"]["text_sha256"], stage_llm._hash_text(source))
        self.assertNotIn(source, json.dumps(projection))

    def test_compact_projection_deduplicates_large_nested_values(self) -> None:
        repeated = {"payload": "x" * 2_000, "rows": list(range(100))}
        projection = stage_llm._deduplicate_compact_projection(
            {"first": repeated, "nested": {"second": repeated}}
        )

        self.assertEqual(projection["first"]["payload"], repeated["payload"])
        self.assertEqual(projection["nested"]["second"]["$ref"], "#/first")
        self.assertEqual(
            projection["nested"]["second"]["value_sha256"],
            stage_llm._canonical_json_sha256(repeated),
        )

    def test_compact_dedup_keeps_editable_json_content_literal(self) -> None:
        hashes = [str(index) * 64 for index in range(20)]
        projection = stage_llm._deduplicate_compact_projection(
            {
                "authority": {"hashes": hashes},
                "document": {"json_content": {"board_consumed_tensor_hashes": hashes}},
            }
        )

        self.assertEqual(
            projection["document"]["json_content"]["board_consumed_tensor_hashes"],
            hashes,
        )

    def test_fixture_pin_projection_materializes_width_bits(self) -> None:
        pin = stage_llm._fixture_provider_pin_semantics(
            {
                "object_id": "pin:any",
                "path": "/provider/data",
                "properties": {
                    "NAME": "data",
                    "DIR": "IO",
                    "LEFT": "7",
                    "RIGHT": "0",
                },
            }
        )

        self.assertEqual(pin["width_bits"], 8)

    def test_exact_board_compaction_uses_lossless_shared_source_index(self) -> None:
        source_rows = [
            {
                "source_id": "sample-source:one",
                "compile_order": 0,
                "path": "/workspace/run/sources/one.sv",
                "local_path": "/workspace/run/sources/one.sv",
                "language": "SystemVerilog",
                "library": "xil_defaultlib",
                "role": "wrapper",
                "sha256": "a" * 64,
            },
            {
                "source_id": "sample-source:two",
                "compile_order": 1,
                "path": "/workspace/run/sources/two.sv",
                "local_path": "/workspace/run/sources/two.sv",
                "language": "SystemVerilog",
                "library": "xil_defaultlib",
                "role": "simulation_source",
                "sha256": "b" * 64,
            },
        ]
        compile_rows = [
            {
                "source_id": row["source_id"],
                "compile_order": row["compile_order"],
                "remote_path": f"/remote/project/{index}.sv",
                "parent_composite_file": f"/remote/project/{index}.xci",
                "language": row["language"],
                "file_type": row["language"],
                "library": row["library"],
                "sha256": row["sha256"],
                "is_global_include": None,
            }
            for index, row in enumerate(source_rows)
        ]
        source_hashes = [
            {
                "source_id": row["source_id"],
                "path": compile_rows[index]["remote_path"],
                "role": row["role"],
                "sha256": row["sha256"],
            }
            for index, row in enumerate(source_rows)
        ]
        control_abi = {"signals": {"start": "ap_start"}}
        identity = {
            "schema_version": "spatialaccagent.board_source_identity.v1",
            "status": "pass",
            "compute_slot_abi": {
                "control_abi": control_abi,
                "replacement_boundary": {"retained_source_ids": ["sample-source:two"]},
            },
            "control_abi": control_abi,
            "timing_contract": {},
            "axi_interfaces": [],
            "source_hashes": source_hashes,
            "selected_simulation_source_roots": [row["source_id"] for row in source_rows],
            "selected_simulation_source_closure": {
                "root_source_ids": [row["source_id"] for row in source_rows],
                "source_files": source_rows,
            },
        }
        compile_authority = {
            "schema_version": "spatialaccagent.vivado_vcs_compile_authority.v1",
            "status": "pass",
            "compile_sources": compile_rows,
            "export_contexts": [
                {
                    "remote_path": "/remote/project/run.sh",
                    "sha256": "c" * 64,
                    "text": f"vlogan {compile_rows[0]['remote_path']}\nvlogan {compile_rows[1]['remote_path']}\n",
                }
            ],
        }
        context = {
            "schema_version": "spatialaccagent.exact_board_integration_repair_context.v0",
            "adaptive_design_inputs": {
                "exact_board_source_identity": {"path": "/identity.json", "sha256": "d" * 64, "value": identity},
                "vivado_vcs_compile_authority": {
                    "path": "/compile.json",
                    "sha256": "e" * 64,
                    "value": compile_authority,
                },
            },
        }

        compact = stage_llm.compact_exact_board_integration_context(context)
        adaptive = compact["adaptive_design_inputs"]
        self.assertEqual(adaptive["shared_board_source_index"]["row_count"], 2)
        self.assertEqual(
            adaptive["exact_board_source_identity"]["value"]["source_hashes"][
                "canonical_sha256"
            ],
            stage_llm._canonical_json_sha256(source_hashes),
        )
        self.assertTrue(
            adaptive["exact_board_source_identity"]["value"]["source_hashes"][
                "full_rows_are_integrity_metadata_bound_by_identity_artifact_sha256"
            ]
        )
        self.assertEqual(
            adaptive["vivado_vcs_compile_authority"]["value"]["compile_sources"]["view"],
            "compile_sources",
        )
        command_text = adaptive["vivado_vcs_compile_authority"]["value"]["export_contexts"][0]["command_text"]
        self.assertIn("@source:sample-source:one", command_text)

    def test_frozen_compute_slot_compaction_reuses_identity_source_index(self) -> None:
        source_rows = [
            {
                "source_id": f"sample-source:{name}",
                "compile_order": index,
                "path": f"/workspace/run/sources/{name}.sv",
                "local_path": f"/workspace/run/sources/{name}.sv",
                "remote_path": f"/remote/project/{name}.sv",
                "language": "SystemVerilog",
                "library": "xil_defaultlib",
                "role": "simulation_source",
                "sha256": digest * 64,
            }
            for index, (name, digest) in enumerate((("one", "a"), ("two", "b")))
        ]
        identity = {
            "schema_version": "spatialaccagent.board_source_identity.v1",
            "status": "pass",
            "source_hashes": [
                {
                    "source_id": row["source_id"],
                    "path": row["remote_path"],
                    "role": row["role"],
                    "sha256": row["sha256"],
                }
                for row in source_rows
            ],
            "selected_simulation_source_roots": [
                row["source_id"] for row in source_rows
            ],
            "selected_simulation_source_closure": {
                "root_source_ids": [row["source_id"] for row in source_rows],
                "source_files": source_rows,
            },
        }
        frozen_authority = {
            "schema_version": (
                "spatialaccagent.frozen_compute_slot_vcs_compile_authority.v1"
            ),
            "status": "pass",
            "source": "frozen_compute_slot_identity_attestation",
            "compile_authority": {
                "vivado_facts_sha256": "c" * 64,
                "simulator_export_context_sha256s": ["d" * 64],
            },
        }
        context = {
            "schema_version": "spatialaccagent.exact_board_integration_repair_context.v1",
            "adaptive_design_inputs": {
                "exact_board_source_identity": {
                    "path": "/identity.json",
                    "sha256": "e" * 64,
                    "value": identity,
                },
                "vivado_vcs_compile_authority": frozen_authority,
                "sample_project_vcs_input_projection": {
                    "compiler_input_source_ids": [
                        row["source_id"] for row in source_rows
                    ],
                    "runtime_auxiliary_files": [],
                },
            },
        }

        compact = stage_llm.compact_exact_board_integration_context(context)
        adaptive = compact["adaptive_design_inputs"]
        shared = adaptive["shared_board_source_index"]
        self.assertEqual(shared["row_count"], 2)
        self.assertEqual(
            shared["source_index_authority"],
            "frozen_compute_slot_identity_source_closure",
        )
        self.assertEqual(
            adaptive["exact_board_source_identity"]["value"]
            ["selected_simulation_source_closure"]["source_files"]["view"],
            "identity_source_files",
        )
        self.assertEqual(
            adaptive["sample_project_vcs_input_projection"]
            ["compiler_input_source_ids"]["view"],
            "compiler_input_source_ids",
        )
        self.assertNotIn(
            "compile_sources",
            adaptive["vivado_vcs_compile_authority"],
        )

    def test_identity_only_compaction_reuses_hash_bound_source_index(self) -> None:
        source_rows = [
            {
                "source_id": f"sample-source:{index}",
                "compile_order": index,
                "path": f"/workspace/source_{index}.sv",
                "local_path": f"/workspace/source_{index}.sv",
                "language": "SystemVerilog",
                "library": "xil_defaultlib",
                "role": "simulation_source",
                "sha256": str(index + 1) * 64,
            }
            for index in range(3)
        ]
        identity = {
            "schema_version": "spatialaccagent.board_source_identity.v1",
            "status": "pass",
            "source_hashes": [
                {
                    "source_id": row["source_id"],
                    "path": row["path"],
                    "role": row["role"],
                    "sha256": row["sha256"],
                }
                for row in source_rows
            ],
            "selected_simulation_source_roots": [
                row["source_id"] for row in source_rows
            ],
            "selected_simulation_source_closure": {
                "root_source_ids": [row["source_id"] for row in source_rows],
                "source_files": source_rows,
            },
        }
        context = {
            "adaptive_design_inputs": {
                "exact_board_source_identity": {
                    "path": "/identity.json",
                    "sha256": "e" * 64,
                    "value": identity,
                },
                "vivado_vcs_compile_authority": {},
                "sample_project_vcs_input_projection": {
                    "compiler_input_source_ids": [
                        row["source_id"] for row in source_rows
                    ]
                },
            }
        }

        compact = stage_llm.compact_exact_board_integration_context(context)
        adaptive = compact["adaptive_design_inputs"]
        shared = adaptive["shared_board_source_index"]

        self.assertEqual(shared["row_count"], 3)
        self.assertEqual(
            shared["source_index_authority"],
            "exact_board_identity_source_closure",
        )
        self.assertNotIn("compile_sources", shared["views"])
        self.assertEqual(
            adaptive["exact_board_source_identity"]["value"]
            ["selected_simulation_source_closure"]["source_files"]["view"],
            "identity_source_files",
        )

    def test_exact_board_compaction_preserves_debug_boundary_authority(self) -> None:
        boundary_authority = {
            "schema_version": "spatialaccagent.debug_boundary_contracts.v0",
            "boundaries": [
                {
                    "boundary_id": "boundary.adaptive_a_to_b",
                    "src_stage": "adaptive_a",
                    "dst_stage": "adaptive_b",
                    "trace_fields": ["cycle", "boundary_id"],
                }
            ],
            "instrumentation_contract": {
                "resource_policy": "testbench instrumentation only"
            },
        }
        context = {
            "schema_version": "spatialaccagent.exact_board_integration_repair_context.v1",
            "adaptive_design_inputs": {
                "debug_observability_authority": {
                    "path": "/run/verification/debug_closure/boundary_contracts.json",
                    "sha256": "a" * 64,
                    "value": boundary_authority,
                }
            },
        }

        compact = stage_llm.compact_exact_board_integration_context(context)

        retained = compact["adaptive_design_inputs"][
            "debug_observability_authority"
        ]
        self.assertEqual(retained["sha256"], "a" * 64)
        self.assertEqual(retained["value"], boundary_authority)

    def test_compact_retry_serializes_compact_inputs_without_indentation(self) -> None:
        schema = {
            "type": "object",
            "properties": {"status": {"type": "string"}, "file_edits": {"type": "array"}},
            "required": ["status", "file_edits"],
        }
        prompt = stage_llm.compact_retry_prompt(
            "implementation_agent",
            "repair_execution",
            "return files",
            {"verification_capability_repair_package": {"schema_version": "test.package.v0"}},
            schema,
            ["FRAMEWORK_MATERIALIZES_NEW_SOURCE_SHA256"],
        )
        compact_block = prompt.split("<compact_inputs>\n", 1)[1].split("\n</compact_inputs>", 1)[0]

        json.loads(compact_block)
        self.assertEqual(len(compact_block.splitlines()), 1)
        self.assertNotIn("<action_grounding_registry>", prompt)
        self.assertIn("FRAMEWORK_MATERIALIZES_NEW_SOURCE_SHA256", prompt)

    def test_compact_implementation_prompt_allows_hash_bound_text_replacements(self) -> None:
        schema = {
            "type": "object",
            "properties": {"file_edits": {"type": "array"}},
            "required": ["file_edits"],
        }
        prompt = stage_llm.compact_retry_prompt(
            "implementation_agent",
            "repair_execution",
            "return files",
            {"verification_capability_repair_package": {}},
            schema,
        )

        self.assertIn("operation=replace_text", prompt)
        self.assertIn("exact unique old_text/new_text anchors", prompt)
        self.assertNotIn("return complete file contents, never snippets", prompt)

    def test_exact_board_compaction_preserves_runtime_and_reuses_image_evidence(self) -> None:
        tensor_hash = "a" * 64
        image_manifest = {
            "schema_version": "spatialaccagent.full_weight_image_manifest.v1",
            "status": "pass",
            "accelerator_scope": "transformer_blocks_only",
            "scope_coverage_complete": True,
            "target_layer_count": 1,
            "packed_tensor_hashes": [tensor_hash],
            "image_sha256": "b" * 64,
            "path": "/run/generated/board_integration/data/weights.bin",
            "total_bytes": 64,
            "manifest_contract_sha256": "c" * 64,
            "layer_segments": [
                {
                    "layer_index": 0,
                    "byte_offset": 0,
                    "byte_count": 64,
                    "byte_end_exclusive": 64,
                    "tensor_hashes": [tensor_hash],
                    "stage_segments": [
                        {
                            "stage_index": 0,
                            "stage_id": "stage_any",
                            "target_segments": [
                                {
                                    "target_id": "target_any",
                                    "byte_offset": 0,
                                    "byte_count": 64,
                                    "byte_end_exclusive": 64,
                                    "source_tensors": [
                                        {
                                            "layer_index": 0,
                                            "parameter_suffix": "arbitrary.weight",
                                            "source_slice_sha256": tensor_hash,
                                            "shape": [4, 4],
                                            "dtype": "BF16",
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        runtime = {
            "schema_version": "spatialaccagent.board_memory_runtime_plan.v1",
            "status": "ready",
            "physical_cfg_bindings": [
                {"field_id": "arbitrary_cfg", "fact_port_id": "fact:any"}
            ],
            "weight_double_buffer": {"bank_count": 2, "layer_schedule": [{"layer_index": 0}]},
            "activation_ping_pong": {"bank_count": 2, "layer_schedule": [{"layer_index": 0}]},
            "workload_image": {
                "full_weight_image_manifest": image_manifest,
                "materialized_projection": {
                    "packed_tensor_hashes": [tensor_hash],
                    "layer_segments": image_manifest["layer_segments"],
                },
            },
        }
        context = {
            "schema_version": "spatialaccagent.exact_board_integration_repair_context.v1",
            "adaptive_design_inputs": {
                "transformer_block_weight_catalog": {
                    "path": "/catalog.json",
                    "sha256": "d" * 64,
                    "value": {
                        "schema_version": "spatialaccagent.transformer_block_weight_catalog.v1",
                        "tensors": [
                            {
                                "source_slice_sha256": tensor_hash,
                                "layer_index": 0,
                                "parameter_suffix": "arbitrary.weight",
                                "shape": [4, 4],
                                "dtype": "BF16",
                            }
                        ],
                    },
                },
                "board_memory_runtime_contract": {
                    "path": "/runtime.json",
                    "sha256": "e" * 64,
                    "value": runtime,
                },
                "full_weight_image_manifest": {
                    "path": "/manifest.json",
                    "sha256": "f" * 64,
                    "value": image_manifest,
                },
            },
        }

        compact = stage_llm.compact_exact_board_integration_context(context)
        adaptive = compact["adaptive_design_inputs"]
        compact_runtime = adaptive["board_memory_runtime_contract"]["value"]
        compact_manifest = adaptive["full_weight_image_manifest"]["value"]
        physical_cfg_bindings = stage_llm._decode_lossless_columnar_rows(
            compact_runtime["physical_cfg_bindings"]
        )
        layer_segments = stage_llm._decode_compact_weight_layer_segments(
            compact_manifest["layer_segments"],
            tensor_catalog=[
                {
                    "source_slice_sha256": tensor_hash,
                    "layer_index": 0,
                    "parameter_suffix": "arbitrary.weight",
                    "shape": [4, 4],
                    "dtype": "BF16",
                }
            ],
        )

        self.assertEqual(
            physical_cfg_bindings[0]["field_id"],
            "arbitrary_cfg",
        )
        self.assertEqual(compact_runtime["weight_double_buffer"]["bank_count"], 2)
        self.assertIn("$ref", compact_runtime["workload_image"]["full_weight_image_manifest"])
        self.assertNotIsInstance(compact_manifest["packed_tensor_hashes"], list)
        self.assertEqual(
            compact_manifest["layer_segments"]["catalog_source_reference_contract"][
                "factored_source_count"
            ],
            1,
        )
        source = layer_segments[0]["stage_segments"][0][
            "target_segments"
        ][0]["source_tensors"][0]
        self.assertEqual(source["source_slice_sha256"], tensor_hash)
        self.assertEqual(source["shape"], [4, 4])
        self.assertEqual(source["dtype"], "BF16")
        self.assertEqual(layer_segments, image_manifest["layer_segments"])

    def test_exact_board_compaction_preserves_runtime_constants_once_without_binary(self) -> None:
        runtime_manifest = {
            "schema_version": "spatialaccagent.board_runtime_image_manifest.v1",
            "status": "pass",
            "accelerator_scope": "transformer_blocks_only",
            "scope_coverage_complete": True,
            "target_layer_count": 2,
            "connected_runtime_stream_contract_sha256": "1" * 64,
            "path": "/run/data/runtime.u32.bin",
            "image_sha256": "2" * 64,
            "total_bytes": 32,
            "word_count": 8,
            "unique_segments": [
                {
                    "segment_id": "runtime_segment_0",
                    "byte_offset": 0,
                    "byte_count": 32,
                    "word_offset": 0,
                    "word_count": 8,
                    "sha256": "3" * 64,
                    "layer_indices": [0, 1],
                }
            ],
            "layer_bindings": [
                {
                    "layer_index": layer,
                    "segment_id": "runtime_segment_0",
                    "word_offset": 0,
                    "word_count": 8,
                    "sha256": "3" * 64,
                    "stage_bindings": [
                        {
                            "stage_id": "stage_any",
                            "consumer_op": "arbitrary_consumer",
                            "word_offset": 0,
                            "word_count": 8,
                        }
                    ],
                }
                for layer in range(2)
            ],
            "source_tensor_files": [
                {"path": "/capture/capture-only-provenance.pt", "file_sha256": "4" * 64}
            ],
            "deduplication_policy": {
                "cross_layer_sharing_is_never_assumed": True,
                "shared_segment_requires_equal_recomputed_bytes": True,
                "different_streams_remain_distinct": True,
            },
            "manifest_contract_sha256": "5" * 64,
        }
        runtime_plan = {
            "schema_version": "spatialaccagent.board_memory_runtime_plan.v1",
            "runtime_constants": {
                "enabled": True,
                "connected_runtime_stream_contract_sha256": "1" * 64,
                "loader_abi": {"data_port": "opaque_data"},
                "loader_protocol": {"complete_before_kernel_start": True},
                "load_schedule": [
                    {
                        "layer_index": layer,
                        "segment_id": "runtime_segment_0",
                        "word_count": 8,
                        "complete_before_kernel_start": True,
                    }
                    for layer in range(2)
                ],
                "trace_point_ids": ["runtime_load_start", "runtime_load_complete"],
                "full_runtime_image_manifest": runtime_manifest,
                "materialized_projection": {
                    "unique_segments": runtime_manifest["unique_segments"],
                    "layer_bindings": runtime_manifest["layer_bindings"],
                    "image_sha256": runtime_manifest["image_sha256"],
                },
            },
        }
        context = {
            "schema_version": "spatialaccagent.exact_board_integration_repair_context.v1",
            "adaptive_design_inputs": {
                "board_memory_runtime_contract": {
                    "path": "/runtime-plan.json",
                    "sha256": "6" * 64,
                    "value": runtime_plan,
                },
                "full_runtime_image_manifest": {
                    "path": "/runtime-manifest.json",
                    "sha256": "7" * 64,
                    "value": runtime_manifest,
                },
                "runtime_image_artifact": {
                    "path": "/run/data/runtime.u32.bin",
                    "sha256": "2" * 64,
                    "value": {
                        "path": "/run/data/runtime.u32.bin",
                        "sha256": "2" * 64,
                        "byte_count": 32,
                        "payload_base64": "BINARY-MUST-NOT-ENTER-PROMPT",
                        "words": [1, 2, 3, 4],
                    },
                },
            },
        }

        compact = stage_llm.compact_exact_board_integration_context(context)
        adaptive = compact["adaptive_design_inputs"]
        compact_plan = adaptive["board_memory_runtime_contract"]["value"]
        compact_constants = compact_plan["runtime_constants"]

        self.assertEqual(
            stage_llm._decode_compact_runtime_image_manifest(
                adaptive["full_runtime_image_manifest"]["value"]
            ),
            runtime_manifest,
        )
        self.assertEqual(compact_constants["loader_abi"]["data_port"], "opaque_data")
        self.assertEqual(
            len(stage_llm._decode_lossless_columnar_rows(compact_constants["load_schedule"])),
            2,
        )
        self.assertIn("$ref", compact_constants["full_runtime_image_manifest"])
        self.assertIn("$ref", compact_constants["materialized_projection"]["layer_bindings"])
        serialized = json.dumps(compact, sort_keys=True)
        self.assertEqual(serialized.count("capture-only-provenance.pt"), 1)
        self.assertNotIn("BINARY-MUST-NOT-ENTER-PROMPT", serialized)
        self.assertNotIn('"words"', serialized)

    def test_exact_board_compaction_keeps_complete_binding_and_lifecycle_source(self) -> None:
        binding = {
            "schema_version": "spatialaccagent.dut_weight_binding_manifest.v1",
            "status": "pass",
            "single_layer_harness": {
                "generated_dut_modules": ["CertifiedLifecycleKernel"],
                "interface": {"start_port": "launch_any"},
            },
            "stage_harnesses": {"stage_any": {"status": "pass"}},
        }
        lifecycle_source = (
            "class CertifiedLifecycleKernel extends Module {\n"
            "  val loaded = RegInit(false.B)\n"
            "}\n"
        )
        package = {
            "schema_version": "spatialaccagent.verification_capability_repair_package.v1",
            "exact_board_integration_repair_context": {
                "schema_version": "spatialaccagent.exact_board_integration_repair_context.v1",
                "adaptive_design_inputs": {
                    "certified_single_layer_binding": {
                        "path": "/run/dut_weight_binding_manifest.json",
                        "sha256": "a" * 64,
                        "value": binding,
                    }
                },
            },
            "repair_source_bundle": {
                "schema_version": "spatialaccagent.repair_source_bundle.v1",
                "status": "ready",
                "documents": [
                    {
                        "path": "/run/ConnectedKernel.scala",
                        "content": lifecycle_source,
                        "sha256": "b" * 64,
                    },
                    {
                        "path": "/run/unrelated.scala",
                        "content": "class Unrelated extends Module {}\n",
                        "sha256": "c" * 64,
                    },
                ],
            },
        }

        compact = stage_llm.compact_verification_capability_repair_package(package)
        adaptive = compact["exact_board_integration_repair_context"][
            "adaptive_design_inputs"
        ]
        self.assertEqual(
            stage_llm._decode_compact_binding_manifest(
                adaptive["certified_single_layer_binding"]["value"]
            ),
            binding,
        )
        documents = compact["repair_source_bundle"]["documents"]
        self.assertEqual(documents[0]["content"], lifecycle_source)
        self.assertNotIn("content", documents[1])

    def test_exact_board_compaction_keeps_lifecycle_generation_authority(self) -> None:
        authority = {
            "status": "ready",
            "kernel_interface": {"reset_port": "current_reset"},
            "accepted_output_beats_per_layer": 37,
            "generation_authorization": {
                "absence_of_prior_multi_invocation_simulation_does_not_block_generation": True
            },
            "validation_boundary": {
                "dynamic_validation": "pending",
                "hardware_pass_claimed": False,
            },
        }
        context = {
            "adaptive_design_inputs": {
                "connected_kernel_lifecycle_authority": {
                    "sha256": "3" * 64,
                    "value": authority,
                }
            }
        }

        compact = stage_llm.compact_exact_board_integration_context(context)

        self.assertEqual(
            compact["adaptive_design_inputs"]["connected_kernel_lifecycle_authority"]["value"],
            authority,
        )

    def test_board_vcs_feedback_compaction_preserves_causal_evidence(self) -> None:
        first_error = "Error-[SE] Syntax error"
        causal_log = (
            ("Parsing unrelated certified source\n" * 20_000)
            + first_error
            + "\n../sources/generated_board_adapter.sv, 417\n"
            + "token 'end' is unexpected\n"
            + ("downstream compile noise\n" * 20_000)
        )
        downstream_sentinel = "MISSING_SIMULATION_REPORT_IS_NOT_CAUSAL" * 10_000
        feedback = {
            "schema_version": "spatialaccagent.exact_board_vcs_feedback.v1",
            "status": "ready",
            "blockers": [],
            "diagnosis": {
                "path": "/run/verification/case_diagnostics/vcs_functional_diagnosis.json",
                "sha256": "a" * 64,
                "value": {
                    "schema_version": "spatialaccagent.case_vcs_functional_diagnosis.v2",
                    "status": "needs_repair",
                    "diagnosis_status": "ready",
                    "summary": f"vcs_compile_failure: {first_error}",
                    "failure_class": "vcs_compile_failure",
                    "runner_phase": "remote_vcs",
                    "failure_evidence": {
                        "failure_class": "vcs_compile_failure",
                        "first_real_error": first_error,
                        "compile": {"status": "fail", "returncode": 1},
                        "simulation": {"status": "not_run"},
                        "log_tail": causal_log,
                        "related_source_ids": ["generated-board-source:adapter"],
                        "live_progress": {
                            "history": downstream_sentinel,
                        },
                        "progress_event_summary": {
                            "schema_version": "spatialaccagent.board_live_progress_summary.v1",
                            "status": "observing",
                            "record_count": 41,
                            "semantic_progress_event_count": 17,
                            "heartbeat_event_count": 24,
                            "progress_epoch": 17,
                            "last_cycle": 9000,
                            "last_semantic_progress_cycle": 7000,
                            "silent_cycles": 2000,
                            "first_stalled_boundary": "boundary.current_a_to_b",
                            "terminal_event_seen": False,
                            "last_semantic_progress_event": {
                                "cycle": 7000,
                                "event_kind": "semantic_progress",
                                "stage_or_boundary": "boundary.current_a_to_b",
                                "token": 3,
                            },
                            "latest_stall_snapshot": {
                                "cycle": 9000,
                                "event_kind": "stall_snapshot",
                                "stalled_boundary": "boundary.current_a_to_b",
                                "payload_integrity": {"unknown": True},
                            },
                            "causal_event_tail": [
                                {
                                    "cycle": index,
                                    "event_kind": "semantic_progress",
                                    "stage_or_boundary": "boundary.current_a_to_b",
                                }
                                for index in range(40)
                            ],
                            "validation_errors": [],
                        },
                        "structured_failures": {
                            "exact_board_acceptance_checks": [
                                {
                                    "name": "dynamic_real_tool_evidence",
                                    "status": "fail",
                                    "blockers": [downstream_sentinel],
                                }
                            ]
                        },
                    },
                    "repair_handoff": {
                        "agent_should_apply_code_changes": True,
                        "failure_class": "vcs_compile_failure",
                        "first_real_error": first_error,
                        "repair_scope": "generated_source_or_compile_plan",
                        "must_rerun": ["case_vcs_functional_sim"],
                        "log_tail": causal_log,
                        "structured_failures": {"cascade": downstream_sentinel},
                    },
                    "sources": ["/run/verification/board_simulation/reports/vcs_compile.log"],
                },
            },
            "runner_report": {
                "path": "/run/verification/vcs/case_board_vcs_functional.json",
                "sha256": "b" * 64,
                "value": {
                    "schema_version": "spatialaccagent.board_vcs_functional_run.v1",
                    "status": "fail",
                    "phase": "remote_vcs",
                    "validation_mode": "compute_slot_axi",
                    "runner_implementation_sha256": "c" * 64,
                    "preflight_manifest_projection_sha256": "d" * 64,
                    "input_fingerprint_sha256": "e" * 64,
                    "vcs_compile_plan_sha256": "f" * 64,
                    "exact_board_preflight_passed": True,
                    "compile_log": "/run/reports/vcs_compile.log",
                    "sim_log": "/run/reports/vcs_simulation.log",
                    "compile": {
                        "status": "fail",
                        "returncode": 1,
                        "argv": [downstream_sentinel],
                    },
                    "run": {"status": "not_run"},
                    "exact_board_acceptance": downstream_sentinel,
                },
            },
        }

        compact = stage_llm.compact_verification_capability_repair_package(
            {
                "schema_version": "spatialaccagent.verification_capability_repair_package.v1",
                "current_board_vcs_feedback": feedback,
            }
        )
        compact_feedback = compact["current_board_vcs_feedback"]
        serialized = json.dumps(compact_feedback, sort_keys=True)

        self.assertLess(len(serialized), 40_000)
        self.assertIn(first_error, serialized)
        self.assertIn("../sources/generated_board_adapter.sv, 417", serialized)
        self.assertNotIn(downstream_sentinel, serialized)
        runner = compact_feedback["runner_report"]["value"]
        self.assertEqual(runner["validation_mode"], "compute_slot_axi")
        self.assertNotIn("runner_implementation_sha256", runner)
        self.assertNotIn("input_fingerprint_sha256", runner)
        evidence = compact_feedback["diagnosis"]["value"]["failure_evidence"]
        self.assertNotIn("progress_event_summary", evidence)
        self.assertNotIn("structured_failures", evidence)
        self.assertLess(len(evidence["causal_log_excerpt"]["excerpt"]), 5_000)

    def test_board_vcs_compaction_preserves_termination_provenance(self) -> None:
        provenance = {
            "schema_version": (
                "spatialaccagent.simulation_termination_provenance.v1"
            ),
            "status": "complete",
            "termination_source": "nonzero_process_exit",
            "exit_code": 1,
            "raw_terminal_log_tail": "TERMINATION_CAUSE_SENTINEL",
            "simulator_terminal_log": {
                "status": "observed",
                "matched_lines": ["Fatal: TERMINATION_CAUSE_SENTINEL"],
            },
            "runner_process_provenance": {
                "attribution": "runner_owned_simulator_process_signal_exit",
                "last_simulator_process_commands": ["simv"],
                "last_running_process_snapshot": {
                    "simulator_like_process_observed": True,
                    "processes": [{"pid": 75, "command": "simv"}],
                },
            },
        }
        compact = stage_llm._compact_board_vcs_feedback(
            {
                "diagnosis": {
                    "value": {
                        "failure_class": "vcs_runtime_failure",
                        "failure_evidence": {
                            "failure_class": "vcs_runtime_failure",
                            "termination_provenance": provenance,
                        },
                    }
                },
                "runner_report": {
                    "value": {
                        "status": "fail",
                        "phase": "remote_vcs",
                        "run": {
                            "status": "fail",
                            "returncode": 1,
                            "termination_provenance": provenance,
                        },
                        "termination_provenance": provenance,
                    }
                },
            }
        )

        diagnosis_provenance = compact["diagnosis"]["value"][
            "failure_evidence"
        ]["termination_provenance"]
        runner = compact["runner_report"]["value"]
        self.assertEqual(
            diagnosis_provenance["termination_source"],
            "nonzero_process_exit",
        )
        self.assertIn(
            "TERMINATION_CAUSE_SENTINEL",
            json.dumps(diagnosis_provenance),
        )
        self.assertEqual(
            runner["run"]["termination_provenance"]["exit_code"], 1
        )
        self.assertEqual(
            runner["termination_provenance"]["status"], "complete"
        )
        self.assertEqual(
            runner["termination_provenance"]["runner_process_provenance"][
                "last_simulator_process_commands"
            ],
            ["simv"],
        )

    def test_board_vcs_semantic_stall_compaction_preserves_state_not_repetition(self) -> None:
        first_error = (
            "semantic progress stopped at cycle 28835616 and cumulative state "
            "remained unchanged through cycle 1619275776"
        )
        stable_state = {
            "layer": 0,
            "scheduler_state": 30,
            "active_weight_bank": "weight_a",
            "preload_weight_bank": "weight_b",
            "prefetch_progress": {
                "accepted_beats": 466104,
                "target_beats": 466104,
            },
            "runtime_load_progress": {
                "accepted_words": 1055,
                "target_words": 1056,
            },
            "axi_read": {"beats": 1400170, "transactions": 1400170},
            "axi_write": {"beats": 933104, "transactions": 933104},
        }
        tail = [
            {
                **stable_state,
                "cycle": 1_600_000_000 + index * 4096,
                "event_kind": "stall_snapshot" if index % 5 == 0 else "heartbeat",
                "stage_or_boundary": "compute_slot_axi",
            }
            for index in range(64)
        ]
        last_semantic = {
            **stable_state,
            "cycle": 28_835_616,
            "event_kind": "semantic_progress",
            "stage_or_boundary": "trace.weight_prefetch_complete",
        }
        feedback = {
            "status": "ready",
            "diagnosis": {
                "path": "/run/diagnosis.json",
                "sha256": "a" * 64,
                "value": {
                    "status": "needs_repair",
                    "failure_class": "vcs_runtime_semantic_stall",
                    "failure_evidence": {
                        "failure_class": "vcs_runtime_semantic_stall",
                        "first_real_error": first_error,
                        "compile": {"status": "pass", "returncode": 0},
                        "simulation": {"status": "fail", "returncode": 86},
                        "log_tail": "repeated heartbeat\n" * 20_000,
                        "adaptive_semantic_stall_evidence": {
                            "schema_version": "spatialaccagent.adaptive_semantic_stall_evidence.v1",
                            "status": "proven_semantic_stall",
                            "reason": "cumulative state remained unchanged",
                            "last_semantic_event_cycle": 28_835_616,
                            "latest_cycle": 1_619_275_776,
                            "silent_cycles": 1_590_440_160,
                            "stable_state_start_cycle": 28_835_840,
                            "stable_state_cycles": 1_590_439_936,
                            "adaptive_silent_cycle_bound": 393_829_600,
                            "max_observed_semantic_gap": 12_307_175,
                            "max_target_work_units": 466_104,
                            "observed_heartbeat_interval": 4096,
                            "semantic_event_count": 7,
                            "stall_snapshot_count": 79_518,
                            "semantic_progress_field_schema_valid": False,
                            "fixed_cycle_timeout": False,
                            "fixed_wall_clock_timeout": False,
                            "last_semantic_progress_event": last_semantic,
                            "latest_stall_snapshot": tail[-2],
                            "latest_complete_event": tail[-1],
                        },
                        "progress_event_summary": {
                            "status": "observing",
                            "record_count": 493_000,
                            "semantic_progress_event_count": 0,
                            "heartbeat_event_count": 400_000,
                            "last_cycle": tail[-1]["cycle"],
                            "last_semantic_progress_cycle": 28_835_616,
                            "first_stalled_boundary": "compute_slot_axi",
                            "causal_event_tail": tail,
                            "validation_errors": [
                                f"record[{index}] heartbeat is incorrectly marked as semantic progress"
                                for index in range(128)
                            ],
                        },
                        "structured_failures": {
                            "exact_board_acceptance_checks": [
                                {
                                    "name": "terminal_report",
                                    "status": "fail",
                                    "blockers": ["terminal report missing" * 1000],
                                }
                            ]
                        },
                    },
                    "repair_handoff": {
                        "agent_should_apply_code_changes": True,
                        "failure_class": "vcs_runtime_semantic_stall",
                        "first_real_error": first_error,
                    },
                },
            },
        }

        compact = stage_llm.compact_verification_capability_repair_package(
            {"current_board_vcs_feedback": feedback}
        )["current_board_vcs_feedback"]
        serialized = json.dumps(compact, sort_keys=True)
        evidence = compact["diagnosis"]["value"]["failure_evidence"]

        self.assertLess(len(serialized), 20_000)
        self.assertIn(first_error, serialized)
        self.assertEqual(
            evidence["adaptive_semantic_stall_evidence"]["status"],
            "proven_semantic_stall",
        )
        self.assertEqual(
            evidence["adaptive_semantic_stall_evidence"]
            ["last_semantic_progress_event"]["scheduler_state"],
            30,
        )
        compact_tail = evidence["progress_event_summary"]["causal_event_tail"]
        self.assertEqual(compact_tail["row_count"], 64)
        self.assertEqual(compact_tail["event_kind_counts"]["heartbeat"], 51)
        self.assertTrue(compact_tail["stable_cumulative_state_repetitions_omitted"])
        self.assertEqual(
            evidence["progress_event_summary"]["validation_errors"]
            ["normalized_patterns"][0]["count"],
            128,
        )
        self.assertNotIn("structured_failures", evidence)
        self.assertTrue(evidence["causal_log_excerpt"]["repetitive_log_text_omitted"])
        self.assertNotIn("excerpt", evidence["causal_log_excerpt"])

    def test_exact_board_compaction_keeps_external_fixture_generation_semantics(self) -> None:
        source_rows = [
            {
                "source_id": f"fixture:{index}",
                "path": f"/run/fixture/source_{index}.sv",
                "remote_path": f"/remote/fixture/source_{index}.sv",
                "sha256": str(index) * 64,
                "compile_order": index,
                "library": "xil_defaultlib",
                "language": "SystemVerilog",
            }
            for index in range(1, 4)
        ]
        fixture = {
            "schema_version": "spatialaccagent.external_simulation_fixture.v2",
            "status": "pass",
            "authority_sha256": "a" * 64,
            "contract_sha256": "9" * 64,
            "providers": [
                {
                    "component_name": "dynamic_provider_component",
                    "group_id": "provider:any",
                    "ip_properties": {"CONFIG.ARBITRARY_WIDTH": "17"},
                    "filesets": [
                        {
                            "index": 0,
                            "status": "pass",
                            "top": "fixture_top",
                            "sources": source_rows,
                            "export_files": [
                                {
                                    "path": "/run/fixture/compile.sh",
                                    "sha256": "b" * 64,
                                }
                            ],
                        }
                    ],
                }
            ],
            "materialized_files": source_rows,
            "compile_authority": {
                "status": "pass",
                "compile_authority_sha256": "8" * 64,
                "compile_sources": source_rows,
                "compiler_inputs": source_rows[:2],
                "hdl_export_artifacts": source_rows[2:],
                "compile_invocations": [
                    {
                        "invocation_id": "fixture-invocation:any",
                        "driver": "vlogan",
                        "work_library": "xil_defaultlib",
                        "input_source_ids": [row["source_id"] for row in source_rows],
                        "input_artifact_ids": [f"artifact:{index}" for index in range(3)],
                        "include_directory_ids": ["fixture-include:any"],
                        "input_remote_paths": [row["remote_path"] for row in source_rows],
                        "argv": [
                            "vlogan",
                            "-work",
                            "xil_defaultlib",
                            "-sverilog",
                            "+incdir+/remote/fixture",
                            *[row["remote_path"] for row in source_rows],
                            "2>&1",
                            "|",
                            "tee",
                            "compile.log",
                        ],
                    }
                ],
                "include_directories": [
                    {
                        "include_dir_id": "fixture-include:any",
                        "staged_path": "fixture_include",
                        "member_source_ids": [row["source_id"] for row in source_rows],
                    }
                ],
                "runtime_auxiliary_files": [
                    {
                        "source_id": "fixture:runtime",
                        "sha256": "7" * 64,
                        "runtime_staged_path": "runtime/data.bin",
                    }
                ],
                "synopsys_sim_setup": {
                    "status": "pass",
                    "path": "/run/fixture/synopsys_sim.setup",
                    "sha256": "6" * 64,
                    "covered_compile_work_libraries": ["xil_defaultlib"],
                    "required_library_directories": [
                        {
                            "library": "xil_defaultlib",
                            "directory": "/compiled/xil_defaultlib",
                            "exists": True,
                        }
                    ],
                    "library_mappings": [
                        {
                            "library": "xil_defaultlib",
                            "resolved_directory": "/compiled/xil_defaultlib",
                        },
                        {
                            "library": "unrelated",
                            "resolved_directory": "$UNRELATED/path",
                        },
                    ],
                },
                "vivado_installation_hdl_authority": {
                    "status": "pass",
                    "selected_root": "/tools/vivado/current",
                    "input_remote_paths": ["/tools/vivado/current/xpm.sv"],
                    "authority_sha256": "5" * 64,
                },
                "export_artifacts": [],
                "export_contexts": [
                    {
                        "path": "/run/fixture/compile.sh",
                        "sha256": "b" * 64,
                        "text": "vlogan /remote/fixture/source_1.sv",
                    }
                ],
            },
            "blockers": [],
        }
        context = {
            "adaptive_design_inputs": {
                "sample_project_vcs_input_projection": {
                    "schema_version": "spatialaccagent.sample_project_vcs_input_projection.v1",
                    "compiler_input_source_ids": ["sample:one", "sample:two"],
                    "runtime_auxiliary_files": [
                        {"source_id": "sample:data", "file_type": "ELF"}
                    ],
                },
                "external_simulation_fixture": {
                    "path": "/run/external_simulation_fixture.json",
                    "sha256": "c" * 64,
                    "value": fixture,
                }
            }
        }

        compact = stage_llm.compact_exact_board_integration_context(context)
        bound = compact["adaptive_design_inputs"]["external_simulation_fixture"]

        self.assertEqual(bound["path"], "/run/external_simulation_fixture.json")
        self.assertEqual(bound["sha256"], "c" * 64)
        compact_fixture = bound["value"]
        compact_authority = compact_fixture["compile_authority"]
        compact_sources = stage_llm._decode_lossless_columnar_rows(
            compact_authority["compile_sources"]
        )
        self.assertEqual(
            [row["source_id"] for row in compact_sources],
            [row["source_id"] for row in source_rows],
        )
        self.assertTrue(all("sha256" not in row for row in compact_sources))
        self.assertEqual(
            [row["compile_order"] for row in compact_sources],
            [row["compile_order"] for row in source_rows],
        )
        self.assertEqual(
            compact_authority["complete_compile_source_rows_contract"][
                "canonical_sha256"
            ],
            stage_llm._canonical_json_sha256(source_rows),
        )
        self.assertEqual(compact_authority["compiler_inputs"]["row_indices"], [0, 1])
        self.assertEqual(compact_authority["hdl_export_artifacts"]["row_indices"], [2])
        invocations = stage_llm._decode_columnarized_record_lists(
            compact_authority["compile_invocations"]
        )
        source_ref = invocations[0]["input_source_ids"]
        source_indices = [
            index
            for first, last in source_ref["row_ranges_inclusive"]
            for index in range(first, last + 1)
        ]
        self.assertEqual(
            [compact_sources[index]["source_id"] for index in source_indices],
            [row["source_id"] for row in source_rows],
        )
        self.assertEqual(
            compact_authority["complete_compile_invocations_contract"][
                "canonical_sha256"
            ],
            stage_llm._canonical_json_sha256(
                fixture["compile_authority"]["compile_invocations"]
            ),
        )
        self.assertEqual(invocations[0]["compiler_options"], ["-sverilog"])
        providers = stage_llm._decode_columnarized_record_lists(
            compact_fixture["providers"]
        )
        self.assertEqual(providers[0]["component_name"], "dynamic_provider_component")
        self.assertEqual(providers[0]["ip_properties"]["CONFIG.ARBITRARY_WIDTH"], "17")
        self.assertEqual(
            providers[0]["filesets"][0]["sources"]["canonical_sha256"],
            stage_llm._canonical_json_sha256(source_rows),
        )
        setup = compact_authority["synopsys_sim_setup"]
        self.assertNotIn("library_mappings", setup)
        self.assertEqual(
            stage_llm._decode_columnarized_record_lists(
                setup["covered_library_mappings"]
            )[0]["library"],
            "xil_defaultlib",
        )
        self.assertEqual(
            compact_authority["vivado_installation_hdl_authority"]["selected_root"],
            "/tools/vivado/current",
        )
        self.assertEqual(compact_fixture["contract_sha256"], "9" * 64)
        self.assertTrue(
            bound["compaction_policy"]["complete_generation_semantics_preserved"]
        )
        self.assertLess(len(json.dumps(bound, separators=(",", ":"))), 50_000)
        self.assertEqual(
            compact["adaptive_design_inputs"]["sample_project_vcs_input_projection"][
                "compiler_input_source_ids"
            ],
            ["sample:one", "sample:two"],
        )

    def test_vcs_export_ast_removes_shell_transport(self) -> None:
        sources = [{"source_id": "sample:rtl"}]
        ast = stage_llm._vcs_export_semantic_ast(
            "vlogan -sverilog @source:sample:rtl 2>&1 | tee compile.log\n",
            sources,
        )
        commands = stage_llm._decode_lossless_columnar_rows(ast["commands"])

        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0]["source_count"], 1)
        self.assertNotIn("2>&1", commands[0]["command_skeleton"])
        self.assertNotIn("tee", commands[0]["command_skeleton"])

    def test_expanded_vcs_rewrite_authority_materializes_command_boundaries(self) -> None:
        sample_sources = [
            {
                "source_id": "sample:replace",
                "remote_path": "/sample/replace.v",
            },
            {
                "source_id": "sample:keep",
                "remote_path": "/sample/keep.sv",
            },
        ]
        sample = {
            "compile_sources": sample_sources,
            "export_contexts": [
                {
                    "remote_path": "/sample/run.sh",
                    "sha256": "a" * 64,
                    "text": (
                        "vcs_elab_opts=\"-full64 -debug_acc+pp+dmptf -t ps -licqueue\"\n"
                        "vlogan -work xil_defaultlib -sverilog "
                        "/sample/replace.v /sample/keep.sv 2>&1 | tee compile.log\n"
                        "vcs $vcs_elab_opts sample_top -o simv\n"
                    ),
                }
            ],
        }
        fixture = {
            "compile_authority": {
                "compile_invocations": [
                    {
                        "driver": "vlogan",
                        "work_library": "fixture_lib",
                        "input_source_ids": ["fixture:model"],
                        "input_remote_paths": ["/fixture/model.sv"],
                        "include_directory_ids": ["fixture:include"],
                        "script_artifact_id": "fixture:script",
                        "argv": [
                            "vlogan",
                            "-work",
                            "fixture_lib",
                            "-sverilog",
                            "/fixture/model.sv",
                            "2>&1",
                        ],
                    }
                ],
                "export_contexts": [
                    {"artifact_id": "fixture:script", "sha256": "b" * 64}
                ],
            }
        }
        manifest = {
            "board_simulation_preflight_plan": {
                "top_module": "sample_top",
                "source_replacements": [
                    {
                        "replaced_source_id": "sample:replace",
                        "generated_source_id": "generated:adapter",
                    }
                ],
                "external_simulation_fixture": {
                    "selected_source_ids": ["fixture:model"]
                },
            }
        }

        authority = stage_llm.expanded_vcs_command_rewrite_authority(
            sample,
            fixture,
            manifest,
            ["certified:kernel"],
            ["generated:adapter", "generated:testbench"],
        )

        self.assertEqual(authority["counts"]["total_sources"], 5)
        self.assertEqual(authority["counts"]["unique_sources"], 5)
        self.assertEqual(
            authority["sample"]["command_groups"][0]["source_ids"],
            ["generated:adapter", "sample:keep"],
        )
        self.assertEqual(
            authority["external_fixture"]["command_groups"][0]["source_ids"],
            ["fixture:model"],
        )
        self.assertEqual(
            authority["additional_generated_group"]["source_ids"],
            ["certified:kernel", "generated:testbench"],
        )
        elaboration = authority["manifest_ready_ordered_commands"][-1]
        self.assertEqual(
            elaboration["argv"][:6],
            ["-full64", "-debug_acc+pp+dmptf", "-t", "ps", "-licqueue", "sample_top"],
        )
        self.assertFalse(
            any(" " in token for token in elaboration["argv"] if isinstance(token, str))
        )

        compute_manifest = json.loads(json.dumps(manifest))
        compute_plan = compute_manifest["board_simulation_preflight_plan"]
        compute_plan["validation_mode"] = "compute_slot_axi"
        compute_plan.pop("external_simulation_fixture", None)
        compute_plan["testbench"] = {
            "debug_observability_contract": {
                "status": "ready",
                "implementation": "testbench_only",
                "format": "jsonl",
                "observational_only": True,
                "drives_dut_signals": False,
                "new_synthesizable_ports_or_state": False,
                "synthesis_impact": "none",
                "flush_after_each_event": True,
                "heartbeat_is_semantic_progress": False,
                "bounded_deep_trace": True,
                "fixed_cycle_timeout": False,
                "fixed_wall_clock_timeout": False,
                "probes": [{"probe_id": "scheduler", "read_only": True}],
                "progress_event_log": {
                    "format": "jsonl",
                    "path": "reports/progress_event_log.jsonl",
                },
            }
        }
        default_compute_authority = stage_llm.expanded_vcs_command_rewrite_authority(
            sample,
            fixture,
            compute_manifest,
            ["certified:kernel"],
            ["generated:adapter", "generated:testbench"],
            compiler_timescale="-timescale=1ns/1ps",
        )
        self.assertIn(
            "-debug_acc+pp+dmptf",
            default_compute_authority["manifest_ready_ordered_commands"][-1]["argv"],
        )
        self.assertNotIn("functional_elaboration_projection", default_compute_authority)
        compute_authority = default_compute_authority
        self.assertEqual(compute_authority["sample"]["command_groups"], [])
        self.assertEqual(
            compute_authority["external_fixture"]["command_groups"], []
        )
        self.assertEqual(
            compute_authority["additional_generated_group"]["source_ids"],
            ["certified:kernel", "generated:adapter", "generated:testbench"],
        )
        self.assertEqual(
            compute_authority["additional_generated_group"]["compiler_options"],
            [
                "-full64",
                "-sverilog",
                "-timescale=1ns/1ps",
                "+incdir+../sources",
            ],
        )
        self.assertIn(
            "-timescale=1ns/1ps",
            compute_authority["manifest_ready_ordered_commands"][0]["argv"],
        )
        self.assertIn(
            "+incdir+../sources",
            compute_authority["manifest_ready_ordered_commands"][0]["argv"],
        )
        compute_elaboration = compute_authority["manifest_ready_ordered_commands"][-1]
        self.assertIn("-debug_acc+pp+dmptf", compute_elaboration["argv"])
        self.assertEqual(compute_authority["counts"]["total_sources"], 3)

    def test_expanded_vcs_authority_preserves_fixture_global_source_order(self) -> None:
        sample = {
            "compile_sources": [{"source_id": "sample:keep", "remote_path": "/sample/keep.sv"}],
            "export_contexts": [
                {
                    "remote_path": "/sample/run.sh",
                    "sha256": "a" * 64,
                    "text": (
                        "vlogan -work xil_defaultlib -sverilog /sample/keep.sv\n"
                        "vcs sample_top -o simv\n"
                    ),
                }
            ],
        }
        fixture = {
            "compile_authority": {
                "compile_invocations": [
                    {
                        "driver": "vlogan",
                        "work_library": "fixture_lib",
                        "input_source_ids": ["fixture:model"],
                        "include_directory_ids": [],
                        "script_artifact_id": "fixture:model_script",
                        "argv": ["vlogan", "-work", "fixture_lib", "/fixture/model.sv"],
                    },
                    {
                        "driver": "vlogan",
                        "work_library": "xil_defaultlib",
                        "input_source_ids": ["fixture:global"],
                        "include_directory_ids": [],
                        "script_artifact_id": "fixture:global_script",
                        "argv": ["vlogan", "-work", "xil_defaultlib", "/fixture/global.v"],
                    },
                ],
                "hdl_export_artifacts": [
                    {"source_id": "fixture:global", "invoked_by_compile": True}
                ],
                "export_contexts": [
                    {"artifact_id": "fixture:model_script", "sha256": "b" * 64},
                    {"artifact_id": "fixture:global_script", "sha256": "c" * 64},
                ],
            }
        }
        manifest = {
            "board_simulation_preflight_plan": {
                "external_simulation_fixture": {
                    "selected_source_ids": ["fixture:model"]
                },
                "testbench": {"top_module": "dynamic_board_tb"},
            }
        }

        authority = stage_llm.expanded_vcs_command_rewrite_authority(
            sample,
            fixture,
            manifest,
            [],
            ["generated:testbench"],
        )

        self.assertEqual(
            authority["external_fixture"]["selected_source_ids"],
            ["fixture:model", "fixture:global"],
        )
        self.assertEqual(authority["counts"]["total_sources"], 4)
        self.assertIn(
            "xil_defaultlib.glbl",
            authority["manifest_ready_ordered_commands"][-1]["argv"],
        )

    def test_compact_board_authority_keeps_manifest_ready_vcs_plan_literal(self) -> None:
        commands = [
            {
                "order": 0,
                "phase": "compile",
                "tool_role": "functional_verification",
                "executable": "vlogan",
                "argv": ["-work", "xil_defaultlib", {"source_id": "dynamic:source"}],
                "source_ids": ["dynamic:source"],
                "cwd": "vcs_work",
                "env": {},
                "shell": False,
                "authority_refs": ["b" * 64],
            },
            {
                "order": 1,
                "phase": "elaborate",
                "tool_role": "functional_verification",
                "executable": "vcs",
                "argv": ["dynamic_tb", "-o", "simv"],
                "source_ids": [],
                "cwd": "vcs_work",
                "env": {},
                "shell": False,
                "authority_refs": ["b" * 64, "d" * 64],
            },
        ]
        plan = {
            "schema_version": "spatialaccagent.vcs_compile_plan.v1",
            "status": "ready",
            "tool_binding": {
                "role": "functional_verification",
                "name": "vcs",
                "host": "dynamic.test",
                "port": 22,
                "executable": "vcs",
                "env": {},
            },
            "compile_authority": {
                "vivado_facts_path": "/dynamic/vivado_facts.json",
                "vivado_facts_sha256": "a" * 64,
                "simulator_export_context_sha256s": ["b" * 64],
                "external_fixture_contract_sha256": "c" * 64,
                "external_fixture_export_context_sha256s": ["d" * 64],
            },
            "ordered_commands": commands,
            "top_module": "dynamic_tb",
            "output": "simv",
        }
        package = {
            "schema_version": "spatialaccagent.verification_capability_repair_package.v1",
            "verification_scope": "board_axi_ddr_closure",
            "repair_source_bundle": {
                "schema_version": "spatialaccagent.repair_source_bundle.v1",
                "documents": [
                    {
                        "path": "/dynamic/dut_weight_binding_manifest.json",
                        "content": '{"status":"incomplete"}',
                    }
                ],
                "document_count": 1,
                "document_chars": 23,
                "editable_contract": {
                    "current_board_manifest_file": {
                        "path": "/dynamic/dut_weight_binding_manifest.json",
                        "sha256": "e" * 64,
                    },
                    "board_manifest_rewrite_authority": {
                        "expanded_source_authority": {
                            "vcs_command_rewrite_authority": {
                                "manifest_ready_ordered_commands": commands,
                                "ordered_source_ids": ["dynamic:source"],
                                "manifest_ready_vcs_compile_plan": plan,
                                "counts": {"total_sources": 1},
                                "external_fixture": {
                                    "required_global_simulator_source_ids": []
                                },
                            }
                        }
                    }
                },
            },
        }

        compact = stage_llm._deduplicate_compact_projection(
            stage_llm.compact_for_retry(
                {
                    "stage": "repair_execution",
                    "agent": "dynamic_board_agent",
                    "verification_capability_repair_package": package,
                }
            )
        )
        compact_plan = compact["verification_capability_repair_package"][
            "repair_source_bundle"
        ]["editable_contract"]["board_manifest_rewrite_authority"][
            "expanded_source_authority"
        ]["vcs_command_rewrite_authority"]["manifest_ready_vcs_compile_plan"]

        self.assertEqual(compact_plan, plan)
        self.assertIsInstance(compact_plan["ordered_commands"], list)
        self.assertEqual(stage_llm.exact_board_compact_request_errors(compact), [])

        compute_package = json.loads(json.dumps(package))
        compute_authority = compute_package["repair_source_bundle"][
            "editable_contract"
        ]["board_manifest_rewrite_authority"]["expanded_source_authority"][
            "vcs_command_rewrite_authority"
        ]
        compute_authority["validation_mode"] = "compute_slot_axi"
        compute_plan = compute_authority["manifest_ready_vcs_compile_plan"]
        compute_plan["compile_authority"][
            "external_fixture_contract_sha256"
        ] = None
        compute_plan["compile_authority"][
            "external_fixture_export_context_sha256s"
        ] = []
        compute_compact = stage_llm._deduplicate_compact_projection(
            stage_llm.compact_for_retry(
                {
                    "stage": "repair_execution",
                    "agent": "dynamic_board_agent",
                    "verification_capability_repair_package": compute_package,
                }
            )
        )
        self.assertEqual(
            stage_llm.exact_board_compact_request_errors(compute_compact), []
        )

        package["repair_source_bundle"]["editable_contract"][
            "board_manifest_rewrite_authority"
        ]["executor_preservation_contract"] = {
            "vcs_compile_plan_binding": {
                "agent_must_not_copy_or_reconstruct_ordered_commands": True
            }
        }
        materialized_compact = stage_llm._deduplicate_compact_projection(
            stage_llm.compact_for_retry(
                {
                    "stage": "repair_execution",
                    "agent": "exact_board_integration_generation_agent",
                    "verification_capability_repair_package": package,
                }
            )
        )
        certificate = materialized_compact[
            "verification_capability_repair_package"
        ]["repair_source_bundle"]["editable_contract"][
            "board_manifest_rewrite_authority"
        ]["expanded_source_authority"]["vcs_command_rewrite_authority"][
            "manifest_ready_vcs_compile_plan"
        ]
        self.assertEqual(
            certificate["representation"],
            "framework_materialization_certificate",
        )
        self.assertEqual(certificate["ordered_command_count"], 2)
        self.assertEqual(certificate["compile_source_count"], 1)
        self.assertNotIn("ordered_commands", certificate)
        self.assertEqual(
            stage_llm.exact_board_compact_request_errors(materialized_compact), []
        )

    def test_post_vcs_board_compaction_keeps_only_current_repair_inputs(self) -> None:
        testbench = (
            "module dynamic_board_tb;\n"
            "  // Native checkpoint setup belongs to execution only.\n"
            "endmodule\n"
        )
        testbench_sha = hashlib.sha256(testbench.encode("utf-8")).hexdigest()
        sample = "module sample_compute_slot; endmodule\n"
        sample_sha = hashlib.sha256(sample.encode("utf-8")).hexdigest()
        manifest_text = '{"status":"incomplete"}\n'
        manifest_sha = hashlib.sha256(manifest_text.encode("utf-8")).hexdigest()
        manifest_path = "/run/dut_weight_binding_manifest.json"
        source_path = "/run/generated/board_integration/dynamic_board_tb.sv"
        sample_path = "/sample/sample_compute_slot.v"
        package = {
            "schema_version": "spatialaccagent.verification_capability_repair_package.v1",
            "generation_phase_contract": {
                "status": "repair_existing_board_sources",
                "current_vcs_feedback_ready": True,
            },
            "current_board_vcs_feedback": {
                "status": "ready",
                "summary": "VCS undefined system function",
                "diagnosis": {
                    "value": {
                        "failure_class": "vcs_compile_failure",
                        "failure_evidence": {
                            "failure_class": "vcs_compile_failure",
                            "first_real_error": "Undefined system function",
                            "compile": {"status": "fail", "returncode": 1},
                        },
                    }
                },
            },
            "exact_board_repair_attempt_history": {"attempts": ["old"]},
            "adaptive_observation_state": {"old_probe": True},
            "relevant_repair_experience": {"old_episode": True},
            "relevant_project_knowledge": {"unrelated": True},
            "exact_board_integration_repair_context": {
                "adaptive_design_inputs": {
                    "target_model": {"model_id": "dynamic/model"},
                    "exact_board_source_identity": {
                        "value": {
                            "selected_simulation_source_closure": {
                                "source_files": [
                                    {
                                        "closure_role": "exact_sample_top",
                                        "path": sample_path,
                                        "sha256": sample_sha,
                                    }
                                ]
                            }
                        }
                    },
                    "full_weight_image_manifest": {"large_duplicate": True},
                }
            },
            "repair_source_bundle": {
                "editable_contract": {
                    "current_board_manifest_file": {
                        "path": manifest_path,
                        "sha256": manifest_sha,
                    },
                    "current_board_source_files": [
                        {"path": source_path, "sha256": testbench_sha}
                    ],
                    "board_manifest_rewrite_authority": {
                        "expanded_source_authority": {"redundant": True}
                    },
                },
                "documents": [
                    {
                        "path": manifest_path,
                        "sha256": manifest_sha,
                        "content": manifest_text,
                    },
                    {
                        "path": source_path,
                        "sha256": testbench_sha,
                        "content": testbench,
                    },
                    {
                        "path": sample_path,
                        "sha256": sample_sha,
                        "content": sample,
                    },
                    {
                        "path": "/lower/ConnectedSingleLayerHarness.scala",
                        "sha256": "b" * 64,
                        "content": "class ConnectedSingleLayerHarness\n",
                    },
                ],
            },
        }

        compact = stage_llm.compact_verification_capability_repair_package(
            package
        )
        names = {
            Path(str(row.get("path") or "")).name
            for row in compact["repair_source_bundle"]["documents"]
        }

        self.assertEqual(
            names,
            {
                "dynamic_board_tb.sv",
            },
        )
        self.assertNotIn("exact_board_repair_attempt_history", compact)
        self.assertNotIn("adaptive_observation_state", compact)
        self.assertNotIn("relevant_repair_experience", compact)
        self.assertNotIn("relevant_project_knowledge", compact)
        self.assertNotIn(
            "full_weight_image_manifest",
            compact["exact_board_integration_repair_context"][
                "adaptive_design_inputs"
            ],
        )
        self.assertNotIn(
            "board_manifest_rewrite_authority",
            compact["repair_source_bundle"]["editable_contract"],
        )
        compact_inputs = {
            "verification_capability_repair_package": compact
        }
        self.assertEqual(
            stage_llm.exact_board_compact_request_errors(compact_inputs), []
        )
        self.assertFalse(
            compact["repair_source_bundle"]["manifest_content_required"]
        )
        runtime_package = copy.deepcopy(package)
        runtime_diagnosis = runtime_package["current_board_vcs_feedback"][
            "diagnosis"
        ]["value"]
        runtime_diagnosis["failure_class"] = "vcs_runtime_semantic_stall"
        runtime_diagnosis["failure_evidence"] = {
            "failure_class": "vcs_runtime_semantic_stall",
            "first_real_error": "semantic progress stopped",
            "compile": {"status": "pass", "returncode": 0},
            "simulation": {"status": "fail", "returncode": 1},
        }
        runtime_compact = stage_llm.compact_verification_capability_repair_package(
            runtime_package
        )
        runtime_names = {
            Path(str(row.get("path") or "")).name
            for row in runtime_compact["repair_source_bundle"]["documents"]
        }
        self.assertTrue(
            runtime_compact["repair_source_bundle"]["manifest_content_required"]
        )
        self.assertEqual(
            runtime_names,
            {"dut_weight_binding_manifest.json", "dynamic_board_tb.sv"},
        )
        runtime_testbench = next(
            row
            for row in runtime_compact["repair_source_bundle"]["documents"]
            if row["path"] == source_path
        )
        self.assertEqual(runtime_testbench["content"], testbench)
        runtime_manifest = next(
            row
            for row in runtime_compact["repair_source_bundle"]["documents"]
            if row["path"] == manifest_path
        )
        self.assertEqual(
            runtime_manifest["json_content"],
            {"status": "incomplete"},
        )
        self.assertEqual(
            stage_llm.exact_board_compact_request_errors(
                {"verification_capability_repair_package": runtime_compact}
            ),
            [],
        )
        runtime_compact_again = (
            stage_llm.compact_verification_capability_repair_package(
                runtime_compact
            )
        )
        runtime_manifest_again = next(
            row
            for row in runtime_compact_again["repair_source_bundle"]["documents"]
            if row["path"] == manifest_path
        )
        self.assertEqual(
            runtime_manifest_again["json_content"],
            {"status": "incomplete"},
        )
        self.assertEqual(
            stage_llm.exact_board_compact_request_errors(
                {
                    "verification_capability_repair_package": (
                        runtime_compact_again
                    )
                }
            ),
            [],
        )
        zero_time_package = copy.deepcopy(runtime_package)
        zero_time_diagnosis = zero_time_package["current_board_vcs_feedback"][
            "diagnosis"
        ]["value"]
        zero_time_diagnosis["failure_class"] = "vcs_runtime_zero_time_livelock"
        zero_time_diagnosis["failure_evidence"] = {
            "failure_class": "vcs_runtime_zero_time_livelock",
            "first_real_error": "simulation time stopped advancing",
            "compile": {"status": "pass", "returncode": 0},
            "simulation": {"status": "fail", "returncode": 87},
            "adaptive_semantic_stall_evidence": {},
            "zero_time_livelock_evidence": {
                "status": "proven_zero_time_livelock",
                "last_cycle": 123,
            },
            "supplemental_observation_artifacts": [
                {
                    "status": "ready",
                    "relative_path": "reports/payload_probe.jsonl",
                    "byte_count": 2048,
                    "summary": {
                        "record_count": 5,
                        "probe_ids": ["probe.payload"],
                        "probe_revisions": [7],
                        "last_scalar_record": {
                            "cycle": 123,
                            "same_time_index": 1,
                            "stage0.valid": 1,
                            "stage0.ready": 0,
                        },
                    },
                },
                {
                    "status": "ready",
                    "artifact_kind": "vcd_simulation_time_probe",
                    "relative_path": "reports/core_probe.vcd",
                    "byte_count": 4096,
                    "summary": {
                        "timescale": "1 ps",
                        "timestamp_count": 20,
                        "previous_timestamp": 100,
                        "last_timestamp": 104,
                        "simulation_time_advanced": True,
                    },
                },
            ],
            "vcs_native_loop_report": {
                "enabled": True,
                "native_loop_detected": False,
                "loop_detection_enabled_observed": True,
            },
            "structured_failures": {
                "elaborated_hierarchy": {"report_valid": False}
            },
            "sacg_cctg_causal_slice": {
                "path": "/run/causal_slice.json",
                "sha256": "c" * 64,
                "value": {
                    "status": "ready",
                    "failure_class": "vcs_runtime_zero_time_livelock",
                    "earliest_unproven_frontier": {
                        "frontier_id": "connected_kernel_input_to_output"
                    },
                    "causal_graph_slice": {
                        "cctg_causal_paths": [{"path_id": "active"}],
                        "sacg_nodes": [{"large": "duplicate"}],
                        "sacg_edges": [{"large": "duplicate"}],
                        "sacg_constraints": [{"large": "duplicate"}],
                    },
                    "runtime_evidence_projection": {
                        "semantic_event_tail": [{"large": "duplicate"}]
                    },
                },
            },
        }
        zero_time_package["current_board_vcs_feedback"]["runner_report"] = {
            "value": {
                "status": "fail",
                "vcs_native_loop_report": copy.deepcopy(
                    zero_time_diagnosis["failure_evidence"][
                        "vcs_native_loop_report"
                    ]
                ),
                "supplemental_observation_artifacts": copy.deepcopy(
                    zero_time_diagnosis["failure_evidence"][
                        "supplemental_observation_artifacts"
                    ]
                ),
            }
        }
        zero_time_compact = (
            stage_llm.compact_verification_capability_repair_package(
                zero_time_package
            )
        )
        zero_time_bundle = zero_time_compact["repair_source_bundle"]
        zero_time_names = {
            Path(str(row.get("path") or "")).name
            for row in zero_time_bundle["documents"]
        }
        zero_time_evidence = zero_time_compact["current_board_vcs_feedback"][
            "diagnosis"
        ]["value"]["failure_evidence"]
        compact_slice = zero_time_evidence["sacg_cctg_causal_slice"]["value"]
        self.assertFalse(zero_time_bundle["manifest_content_required"])
        self.assertEqual(zero_time_names, {"dynamic_board_tb.sv"})
        self.assertNotIn("adaptive_semantic_stall_evidence", zero_time_evidence)
        self.assertEqual(
            zero_time_evidence["zero_time_livelock_evidence"]["last_cycle"],
            123,
        )
        supplemental = zero_time_evidence[
            "supplemental_observation_artifacts"
        ][0]
        self.assertEqual(supplemental["summary"]["record_count"], 5)
        self.assertEqual(
            supplemental["summary"]["last_scalar_record"]["stage0.ready"],
            0,
        )
        runner_supplemental = zero_time_compact["current_board_vcs_feedback"][
            "runner_report"
        ]["value"]["supplemental_observation_artifacts"][0]
        self.assertEqual(
            runner_supplemental["summary"]["last_scalar_record"]["stage0.ready"],
            0,
        )
        self.assertEqual(
            zero_time_evidence["supplemental_observation_artifacts"][1]["summary"][
                "last_timestamp"
            ],
            104,
        )
        self.assertFalse(
            zero_time_evidence["vcs_native_loop_report"]["native_loop_detected"]
        )
        self.assertNotIn("structured_failures", zero_time_evidence)
        self.assertEqual(
            compact_slice["earliest_unproven_frontier"]["frontier_id"],
            "connected_kernel_input_to_output",
        )
        self.assertEqual(compact_slice["cctg_causal_paths"], [{"path_id": "active"}])
        self.assertNotIn("causal_graph_slice", compact_slice)
        self.assertNotIn("runtime_evidence_projection", compact_slice)
        self.assertEqual(
            stage_llm.exact_board_compact_request_errors(
                {
                    "verification_capability_repair_package": (
                        zero_time_compact
                    )
                }
            ),
            [],
        )
        cited_sample_package = copy.deepcopy(package)
        cited_sample_package["current_board_vcs_feedback"]["diagnosis"]["value"][
            "failure_evidence"
        ]["first_real_error"] = f"compile error in {Path(sample_path).name}:17"
        cited_sample_compact = (
            stage_llm.compact_verification_capability_repair_package(
                cited_sample_package
            )
        )
        cited_sample_names = {
            Path(str(row.get("path") or "")).name
            for row in cited_sample_compact["repair_source_bundle"]["documents"]
        }
        self.assertEqual(
            cited_sample_names,
            {"dynamic_board_tb.sv", "sample_compute_slot.v"},
        )
        compact["repair_source_bundle"]["documents"] = [
            row
            for row in compact["repair_source_bundle"]["documents"]
            if Path(str(row.get("path") or "")).name
            != "dynamic_board_tb.sv"
        ]
        self.assertIn(
            f"post-VCS board source is not complete: {source_path}",
            stage_llm.exact_board_compact_request_errors(compact_inputs),
        )

    def test_post_vcs_compaction_omits_historical_failed_interventions(self) -> None:
        history = {
            "intervention_response_history": {
                "transitions": [
                    {
                        "agent_hypothesis": {
                            "summary": (
                                "move lifecycle start; old evidence /run/old.json "
                                + "a" * 64
                            ),
                            "root_cause": "start and input overlapped",
                            "causal_prediction": {
                                "intervention_family": "defer_start",
                                "target_frontier_id": "kernel_input_to_output",
                            },
                        },
                        "observed_response": {
                            "failure_class": "vcs_runtime_zero_time_livelock",
                            "first_real_error": "time stopped at /remote/job",
                            "frontier_id": "kernel_input_to_output",
                            "zero_time_livelock": {
                                "last_cycle": 456,
                                "last_progress_event_count": 12,
                            },
                        },
                        "causal_prediction_evaluation": {
                            "status": "falsified",
                            "falsified_if": "no output appears",
                        },
                        "candidate_board_state_sha256": "b" * 64,
                    }
                ]
            }
        }
        compact = stage_llm.compact_verification_capability_repair_package(
            {
                "generation_phase_contract": {
                    "status": "repair_existing_board_sources",
                    "current_vcs_feedback_ready": True,
                },
                "current_board_vcs_feedback": {"status": "ready"},
                "exact_board_repair_attempt_history": history,
            }
        )
        serialized = json.dumps(compact, sort_keys=True)

        self.assertNotIn("exact_board_repair_attempt_history", compact)
        self.assertNotIn("failed_interventions", compact)
        self.assertNotIn("defer_start", serialized)
        self.assertNotIn("falsified", serialized)
        self.assertNotIn("/run/old.json", serialized)
        self.assertNotIn("/remote/job", serialized)
        self.assertNotIn("a" * 64, serialized)
        self.assertNotIn("b" * 64, serialized)

    def test_post_vcs_compaction_keeps_minimal_rejected_patch_feedback(self) -> None:
        compact = stage_llm.compact_verification_capability_repair_package(
            {
                "generation_phase_contract": {
                    "status": "repair_existing_board_sources",
                    "current_vcs_feedback_ready": True,
                },
                "current_board_vcs_feedback": {"status": "ready"},
                "current_patch_application_feedback": {
                    "status": "ready",
                    "summary": "candidate restores a prior failed source state",
                    "blockers": ["do not relaunch the rejected candidate"],
                    "patch_application": {
                        "path": "/run/agent_patch_application.json",
                        "sha256": "a" * 64,
                        "value": {
                            "rejected_prior_failed_board_attempt": {
                                "iteration": "recent:failed",
                                "board_source_edits": [
                                    {
                                        "path": "generated/board.v",
                                        "before_sha256": "b" * 64,
                                        "after_sha256": "c" * 64,
                                    }
                                ],
                                "candidate_board_source_state": {
                                    "canonical_sha256": "d" * 64,
                                    "candidate_changed_paths": ["generated/board.v"],
                                    "rows": [{"unneeded": "full state"}],
                                },
                                "behavior_signature": {
                                    "failure_class": "vcs_runtime_zero_time_livelock",
                                    "first_real_error": "simulation time stopped",
                                    "zero_time_livelock": {"last_cycle": 123},
                                    "runner_identity": {"unneeded": True},
                                },
                                "runner_identity": {"unneeded": True},
                            }
                        },
                    },
                },
            }
        )

        feedback = compact["current_patch_application_feedback"]
        self.assertEqual(feedback["status"], "ready")
        self.assertEqual(
            feedback["rejected_prior_failed_board_attempt"]["iteration"],
            "recent:failed",
        )
        self.assertEqual(
            feedback["rejected_prior_failed_board_attempt"]["real_tool_outcome"][
                "failure_class"
            ],
            "vcs_runtime_zero_time_livelock",
        )
        self.assertNotIn("patch_application", feedback)
        self.assertNotIn("runner_identity", json.dumps(feedback))
        compact_again = stage_llm.compact_verification_capability_repair_package(
            compact
        )
        self.assertEqual(
            compact_again["current_patch_application_feedback"],
            feedback,
        )

    def test_post_vcs_compaction_keeps_rejected_edit_for_mechanical_retry(self) -> None:
        transaction = {
            "status": "ready_for_agent_retry",
            "failure_class": "atomic_replace_text_contract",
            "blockers": ["old_text matched zero times"],
            "file_edits_were_not_applied": True,
            "real_tool_replay_required_before_retry": False,
            "rejected_file_edits": [
                {
                    "path": "generated/board_tb.sv",
                    "operation": "replace_text",
                    "rationale": "move only the read-only observation trigger",
                    "text_replacements": [
                        {"old_text": "old trigger", "new_text": "new trigger"}
                    ],
                }
            ],
        }
        compact = stage_llm.compact_verification_capability_repair_package(
            {
                "generation_phase_contract": {
                    "status": "repair_existing_board_sources",
                    "current_vcs_feedback_ready": True,
                },
                "current_board_vcs_feedback": {"status": "ready"},
                "current_patch_application_feedback": {
                    "status": "ready",
                    "summary": "replace_text anchor did not match",
                    "patch_application": {
                        "value": {"agent_transaction_rejection": transaction}
                    },
                },
            }
        )
        compact_again = stage_llm.compact_verification_capability_repair_package(
            compact
        )

        feedback = compact_again["current_patch_application_feedback"]
        self.assertEqual(feedback["agent_transaction_rejection"], transaction)
        self.assertNotIn("patch_application", feedback)

    def test_completed_fresh_replay_is_absent_from_layer3_prompt_projection(self) -> None:
        decision = {
            "schema_version": (
                "spatialaccagent.adaptive_observation_decision.v1"
            ),
            "mode": "fresh_exact_source_provenance_replay",
            "frontier_id": "connected_kernel_input_to_output",
            "field_observations": [
                {
                    "evidence_pointer": "/current_board_vcs_feedback/cycle",
                    "observed_value": 20788597,
                    "semantic_role": "counter",
                    "interpretation": "last committed progress cycle",
                }
            ],
            "rationale": "replay unchanged exact sources once",
        }
        compact = stage_llm.compact_verification_capability_repair_package(
            {
                "generation_phase_contract": {
                    "status": "repair_existing_board_sources",
                    "current_vcs_feedback_ready": True,
                },
                "current_board_vcs_feedback": {"status": "ready"},
                "current_fresh_exact_source_provenance_replay": {
                    "schema_version": (
                        "spatialaccagent.current_fresh_exact_source_provenance_replay.v1"
                    ),
                    "status": "ready",
                    "replay_status": "fail",
                    "summary": "VCS simulator process crashed",
                    "execution_generation_sha256": "9" * 64,
                    "decision": decision,
                    "real_tool_probe": {"raw_log": "x" * 1_000_000},
                    "path": "/run/fresh_exact_source_provenance_replay.json",
                },
            }
        )
        compact_again = stage_llm.compact_verification_capability_repair_package(
            compact
        )

        self.assertNotIn("current_fresh_exact_source_provenance_replay", compact_again)
        self.assertNotIn("fresh_exact_source_provenance_replay", json.dumps(compact_again))

    def test_post_vcs_exact_board_prompt_is_proactively_compacted(self) -> None:
        custom_schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "file_edits": {"type": "array"},
            },
            "required": ["status", "file_edits"],
        }
        output = '{"status":"ready_to_apply","file_edits":[]}'
        with tempfile.TemporaryDirectory() as tmp:
            with (
                patch.dict(
                    os.environ,
                    {
                        "SPATIALACC_LLM_AUTO_COMPACT_RETRY": "1",
                        "SPATIALACC_LLM_AUTO_COMPACT_MIN_PROMPT_BYTES": "2000000",
                    },
                ),
                patch.object(
                    stage_llm,
                    "resolved_llm_cfg",
                    return_value=LlmCfg(
                        model="test-model",
                        endpoint="https://example.invalid",
                        api_key="key",
                        stream=True,
                    ),
                ),
                patch.object(
                    stage_llm,
                    "call_llm_with_retry",
                    return_value=(output, []),
                ) as call,
                patch.object(
                    stage_llm,
                    "exact_board_compact_request_errors",
                    return_value=[],
                ),
            ):
                record = stage_llm.run_stage_agent(
                    agent="exact_board_integration_generation_agent",
                    stage="repair_execution",
                    task="repair current exact-board failure",
                    inputs={
                        "verification_capability_repair_package": {
                            "generation_phase_contract": {
                                "status": "repair_existing_board_sources",
                                "current_vcs_feedback_ready": True,
                            },
                            "current_board_vcs_feedback": {"status": "ready"},
                        }
                    },
                    out_dir=Path(tmp),
                    fallback_summary="fallback",
                    output_schema=custom_schema,
                    prompt_rules=["KEEP_CURRENT_CAUSAL_CONTEXT"],
                )

        self.assertEqual(call.call_count, 1)
        self.assertTrue(record["proactive_prompt_compaction"])
        self.assertTrue(record["request_path"].endswith("_prompt.md"))
        self.assertNotIn("compact_retry_prompt", record["request_path"])
        self.assertNotIn("full_prompt_path", record)
        self.assertNotIn("compact_retry_request_path", record)
        self.assertIn("KEEP_CURRENT_CAUSAL_CONTEXT", call.call_args.args[3])

    def test_rejected_exact_board_transaction_never_reuses_agent_cache(self) -> None:
        custom_schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "file_edits": {"type": "array"},
            },
            "required": ["status", "file_edits"],
        }
        output = '{"status":"ready_to_apply","file_edits":[]}'
        compact_package = stage_llm.compact_verification_capability_repair_package(
            {
                "generation_phase_contract": {
                    "status": "repair_existing_board_sources",
                    "current_vcs_feedback_ready": True,
                },
                "current_board_vcs_feedback": {"status": "ready"},
                "current_patch_application_feedback": {
                    "status": "ready",
                    "summary": "candidate restores a prior failed source state",
                },
            }
        )
        self.assertEqual(
            compact_package["current_patch_application_feedback"]["status"],
            "ready",
        )
        inputs = {"verification_capability_repair_package": compact_package}
        with tempfile.TemporaryDirectory() as tmp:
            with (
                patch.object(
                    stage_llm,
                    "resolved_llm_cfg",
                    return_value=LlmCfg(
                        model="test-model",
                        endpoint="https://example.invalid",
                        api_key="key",
                        stream=True,
                    ),
                ),
                patch.object(
                    stage_llm,
                    "call_llm_with_retry",
                    return_value=(output, []),
                ) as call,
                patch.object(
                    stage_llm,
                    "exact_board_compact_request_errors",
                    return_value=[],
                ),
            ):
                for _ in range(2):
                    stage_llm.run_stage_agent(
                        agent="exact_board_integration_generation_agent",
                        stage="repair_execution",
                        task="return a distinct board repair",
                        inputs=inputs,
                        out_dir=Path(tmp),
                        fallback_summary="fallback",
                        output_schema=custom_schema,
                    )

        self.assertEqual(call.call_count, 2)

    def test_post_vcs_repeated_compaction_decodes_current_board_source_rows(self) -> None:
        source_rows = [
            {
                "path": f"/run/generated/board_integration/board_{index}.sv",
                "sha256": hashlib.sha256(
                    f"module board_{index}; endmodule\n".encode("utf-8")
                ).hexdigest(),
            }
            for index in range(2)
        ]
        manifest_path = "/run/dut_weight_binding_manifest.json"
        manifest_text = '{"status":"incomplete"}\n'
        manifest_sha = hashlib.sha256(manifest_text.encode("utf-8")).hexdigest()
        package = {
            "schema_version": "spatialaccagent.verification_capability_repair_package.v1",
            "generation_phase_contract": {
                "status": "repair_existing_board_sources",
                "current_vcs_feedback_ready": True,
            },
            "current_board_vcs_feedback": {
                "status": "ready",
                "diagnosis": {
                    "value": {
                        "failure_class": "vcs_runtime_semantic_stall",
                        "failure_evidence": {
                            "failure_class": "vcs_runtime_semantic_stall",
                            "compile": {"status": "pass", "returncode": 0},
                            "simulation": {"status": "fail", "returncode": 86},
                        },
                    }
                },
            },
            "repair_source_bundle": {
                "editable_contract": {
                    "current_board_manifest_file": {
                        "path": manifest_path,
                        "sha256": manifest_sha,
                    },
                    "current_board_source_files": source_rows,
                },
                "documents": [
                    {
                        "path": manifest_path,
                        "sha256": manifest_sha,
                        "content": manifest_text,
                    },
                    *[
                        {
                            "path": row["path"],
                            "sha256": row["sha256"],
                            "content": f"module board_{index}; endmodule\n",
                        }
                        for index, row in enumerate(source_rows)
                    ],
                ],
            },
        }

        first = stage_llm.compact_verification_capability_repair_package(package)
        repeated = copy.deepcopy(first)
        repeated["repair_source_bundle"]["editable_contract"][
            "current_board_source_files"
        ] = stage_llm._lossless_columnar_rows(
            repeated["repair_source_bundle"]["editable_contract"][
                "current_board_source_files"
            ]
        )

        compact_again = stage_llm.compact_verification_capability_repair_package(
            repeated
        )
        compact_bundle = compact_again["repair_source_bundle"]
        self.assertEqual(
            compact_bundle["editable_contract"]["current_board_source_files"],
            source_rows,
        )
        self.assertEqual(
            {row["path"] for row in compact_bundle["documents"]},
            {manifest_path, *(row["path"] for row in source_rows)},
        )
        self.assertEqual(
            stage_llm.exact_board_compact_request_errors(
                {"verification_capability_repair_package": compact_again}
            ),
            [],
        )

    def test_semantic_rtl_compaction_does_not_require_board_manifest(self) -> None:
        source_path = "/run/generated/semantic_harness/ElementwiseMul.sv"
        source_text = "module ElementwiseMul; endmodule\n"
        source_sha = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
        package = {
            "generation_mode": "board_semantic_rtl_repair",
            "generation_phase_contract": {
                "status": "repair_existing_board_sources",
                "current_vcs_feedback_ready": True,
            },
            "board_semantic_rtl_repair_authority": {
                "current_source_closure": [
                    {"path": source_path, "sha256": source_sha}
                ]
            },
            "repair_source_bundle": {
                "editable_contract": {
                    "localized_allowed_exact_files": [source_path]
                },
                "documents": [
                    {
                        "path": "generated/semantic_harness/ElementwiseMul.sv",
                        "source_path": source_path,
                        "sha256": source_sha,
                        "content": source_text,
                    }
                ],
            },
        }

        compact = stage_llm.compact_verification_capability_repair_package(package)
        self.assertEqual(
            stage_llm.exact_board_compact_request_errors(
                {"verification_capability_repair_package": compact}
            ),
            [],
        )
        self.assertEqual(
            compact["repair_source_bundle"]["documents"][0]["content"],
            source_text,
        )

    def test_manifest_compaction_omits_mechanically_restored_lower_layers(self) -> None:
        manifest_path = "/run/dut_weight_binding_manifest.json"
        stage_harnesses = {"stage_0": {"source_files": [{"path": "/stage0.sv"}]}}
        single_layer_harness = {
            "top_module": "ConnectedKernel",
            "source_files": [{"path": "/connected.sv"}],
        }
        manifest = {
            "status": "pass",
            "stage_harnesses": stage_harnesses,
            "single_layer_harness": single_layer_harness,
            "multilayer_harness": {"top_module": "BoardKernel"},
            "board_simulation_preflight_plan": {
                "vcs_compile_plan": {"ordered_commands": []}
            },
        }
        preserved_hashes = {
            "stage_harnesses": stage_llm._canonical_json_sha256(stage_harnesses),
            "single_layer_harness": stage_llm._canonical_json_sha256(
                single_layer_harness
            ),
        }
        bundle = {
            "editable_contract": {
                "board_manifest_rewrite_authority": {
                    "executor_preservation_contract": {
                        "guard_satisfied": True,
                        "mechanically_preserved_fields": [
                            "stage_harnesses",
                            "single_layer_harness",
                        ],
                        "preserved_field_hashes": preserved_hashes,
                        "vcs_compile_plan_binding": {
                            "agent_must_not_copy_or_reconstruct_ordered_commands": True
                        },
                    },
                    "expanded_source_authority": {
                        "vcs_command_rewrite_authority": {
                            "manifest_ready_vcs_compile_plan": {
                                "ordered_commands": []
                            }
                        }
                    },
                }
            },
            "documents": [
                {
                    "path": manifest_path,
                    "sha256": "a" * 64,
                    "content": json.dumps(manifest),
                }
            ],
        }

        compact = stage_llm.compact_repair_source_bundle(
            bundle,
            preserve_full_text_paths={manifest_path},
        )
        document = compact["documents"][0]
        compact_manifest = document["json_content"]

        self.assertNotIn("stage_harnesses", compact_manifest)
        self.assertNotIn("single_layer_harness", compact_manifest)
        self.assertEqual(
            compact_manifest["multilayer_harness"]["top_module"], "BoardKernel"
        )
        self.assertIn(
            "vcs_compile_plan", compact_manifest["board_simulation_preflight_plan"]
        )
        omissions = {
            row["json_pointer"]: row
            for row in document["framework_materialized_json_omissions"]
        }
        self.assertEqual(
            omissions["/stage_harnesses"]["omitted_value_canonical_sha256"],
            preserved_hashes["stage_harnesses"],
        )
        self.assertEqual(
            omissions["/single_layer_harness"]["omitted_value_canonical_sha256"],
            preserved_hashes["single_layer_harness"],
        )

    def test_board_rewrite_compaction_reuses_bound_identity_without_semantic_loss(self) -> None:
        sample_rows = [
            {
                "source_id": "sample:keep",
                "compile_order": 0,
                "file_type": "SystemVerilog",
                "language": "SystemVerilog",
                "library": "work",
                "path": "/sample/keep.sv",
                "sha256": "1" * 64,
                "classification": "compiler_input",
                "transformed_disposition": "preserve",
            },
            {
                "source_id": "sample:replace",
                "compile_order": 1,
                "file_type": "Verilog",
                "language": "Verilog",
                "library": "work",
                "path": "/sample/replace.v",
                "sha256": "2" * 64,
                "classification": "compiler_input",
                "transformed_disposition": "replace",
            },
            {
                "source_id": "sample:header",
                "compile_order": 2,
                "file_type": "Verilog Header",
                "language": "Verilog Header",
                "library": "work",
                "path": "/sample/header.vh",
                "sha256": "3" * 64,
                "classification": "include_header",
                "transformed_disposition": "stage_only",
            },
        ]
        shared_index = stage_llm._lossless_columnar_rows(
            [
                {
                    "source_id": row["source_id"],
                    "language": row["language"],
                    "library": row["library"],
                }
                for row in sample_rows
            ]
        )
        shared_index["views"] = {
            "identity_source_files": {
                "columns": ["source_id", "language", "library"],
                "row_count": 3,
                "canonical_sha256": "4" * 64,
            },
            "compiler_input_source_ids": {
                "column": "source_id",
                "exclude_source_ids": ["sample:header"],
                "row_count": 2,
                "canonical_sha256": stage_llm._canonical_json_sha256(
                    ["sample:keep", "sample:replace"]
                ),
            },
        }
        external_rows = [
            {
                "source_id": f"fixture:{index}",
                "path": f"/fixture/{index}.sv",
                "staged_path": f"fixture/{index}.sv",
                "sha256": f"{index + 4:x}" * 64,
                "selection_role": "selected",
                "language": "SystemVerilog",
                "library": "fixture",
                "declared_design_units": [{"kind": "module", "name": f"m{index}"}],
            }
            for index in range(9)
        ]
        certified_rows = [
            {"source_id": f"certified:{index}", "path": f"/kernel/{index}.sv"}
            for index in range(9)
        ]
        tensor_hashes = ["a" * 64, "b" * 64]
        manifest = {"board_consumed_tensor_hashes": tensor_hashes}
        original_rewrite = {
            "expanded_source_authority": {
                "sample_sources": sample_rows,
                "external_fixture_sources": external_rows,
                "certified_kernel_sources": certified_rows,
                "current_generated_sources": [],
                "vcs_command_rewrite_authority": {
                    "manifest_ready_vcs_compile_plan": {"ordered_commands": []}
                },
            },
            "compile_source_coverage_authority": {
                "available_external_fixture_compile_source_ids": [
                    row["source_id"] for row in external_rows
                ],
                "certified_kernel_source_ids": [
                    row["source_id"] for row in certified_rows
                ],
                "current_generated_source_ids": ["generated:tb"],
                "preserved_sample_compile_source_ids": ["sample:keep"],
                "replaced_sample_source_ids": ["sample:replace"],
            },
            "complete_transformer_block_tensor_hashes": {
                "catalog": "/catalog.json",
                "count": 2,
                "hashes": tensor_hashes,
                "target_field": "board_consumed_tensor_hashes",
            },
        }
        original_bundle = {
            "editable_contract": {
                "board_manifest_rewrite_authority": original_rewrite,
            },
            "documents": [
                {
                    "path": "/run/dut_weight_binding_manifest.json",
                    "json_content": manifest,
                }
            ],
        }
        compact_bundle = json.loads(json.dumps(original_bundle))
        context_projection = {
            "adaptive_design_inputs": {
                "shared_board_source_index": shared_index,
                "external_simulation_fixture": {
                    "value": {
                        "compile_authority": {
                            "compile_sources": stage_llm._lossless_columnar_rows(
                                [
                                    {
                                        "source_id": row["source_id"],
                                        "language": row["language"],
                                        "library": row["library"],
                                    }
                                    for row in external_rows
                                ]
                            )
                        }
                    }
                },
                "sample_project_vcs_input_projection": {
                    "runtime_auxiliary_files": {
                        "source_ids": stage_llm._encoded_column(["sample:header"]),
                        "canonical_sha256": "5" * 64,
                    }
                },
            }
        }

        stage_llm._compact_board_rewrite_redundancy(
            compact_bundle, original_bundle, context_projection
        )
        compact_rewrite = compact_bundle["editable_contract"][
            "board_manifest_rewrite_authority"
        ]
        compact_expanded = compact_rewrite["expanded_source_authority"]
        root = {
            "verification_capability_repair_package": {
                "exact_board_integration_repair_context": context_projection,
                "repair_source_bundle": compact_bundle,
            }
        }

        sample_authority = compact_expanded["sample_sources"]
        self.assertEqual(
            sample_authority["encoding"],
            "spatialaccagent.sample_source_rewrite_join.v1",
        )
        self.assertNotIn(
            "path", sample_authority["source_semantic_fields"]["selected_fields"]
        )
        self.assertEqual(
            stage_llm._compact_source_id_selection(
                root, sample_authority["classification_views"]["compiler_input"]
            ),
            ["sample:keep", "sample:replace"],
        )
        self.assertEqual(
            stage_llm._compact_source_id_selection(
                root, sample_authority["transformed_disposition_views"]["preserve"]
            ),
            ["sample:keep"],
        )
        external_authority = compact_expanded["external_fixture_sources"]
        self.assertEqual(
            stage_llm._compact_source_id_selection(
                root,
                {
                    **external_authority["source_rows"],
                    "selected_field": "source_id",
                },
            ),
            [row["source_id"] for row in external_rows],
        )
        self.assertEqual(
            stage_llm._decode_encoded_column(external_authority["selection_roles"]),
            ["selected"] * len(external_rows),
        )
        coverage = compact_rewrite["compile_source_coverage_authority"]
        self.assertEqual(
            stage_llm._compact_source_id_selection(
                root, coverage["available_external_fixture_compile_source_ids"]
            ),
            [row["source_id"] for row in external_rows],
        )
        tensor_ref = compact_rewrite["complete_transformer_block_tensor_hashes"][
            "hashes"
        ]
        self.assertEqual(
            stage_llm._json_pointer_lookup(root, tensor_ref["$ref"]),
            (True, tensor_hashes),
        )
        self.assertNotIn(
            "source_ids",
            context_projection["adaptive_design_inputs"][
                "sample_project_vcs_input_projection"
            ]["runtime_auxiliary_files"],
        )
        self.assertIsInstance(
            coverage["certified_kernel_source_ids"], dict
        )
        self.assertIsInstance(tensor_ref, dict)

    def test_board_rewrite_compaction_keeps_external_ids_literal_without_fixture_context(self) -> None:
        external_rows = [
            {
                "source_id": f"fixture:{index}",
                "path": f"/fixture/{index}.sv",
                "selection_role": "identity_only",
            }
            for index in range(9)
        ]
        original_bundle = {
            "editable_contract": {
                "board_manifest_rewrite_authority": {
                    "expanded_source_authority": {
                        "external_fixture_sources": external_rows,
                        "vcs_command_rewrite_authority": {
                            "manifest_ready_vcs_compile_plan": {
                                "ordered_commands": []
                            }
                        },
                    },
                    "compile_source_coverage_authority": {
                        "available_external_fixture_compile_source_ids": [
                            row["source_id"] for row in external_rows
                        ],
                    },
                }
            },
            "documents": [],
        }
        compact_bundle = json.loads(json.dumps(original_bundle))
        context_projection = {"adaptive_design_inputs": {}}

        stage_llm._compact_board_rewrite_redundancy(
            compact_bundle,
            original_bundle,
            context_projection,
        )

        coverage = compact_bundle["editable_contract"][
            "board_manifest_rewrite_authority"
        ]["compile_source_coverage_authority"][
            "available_external_fixture_compile_source_ids"
        ]
        root = {
            "verification_capability_repair_package": {
                "exact_board_integration_repair_context": context_projection,
                "repair_source_bundle": compact_bundle,
            }
        }
        self.assertIsInstance(coverage, list)
        self.assertEqual(
            stage_llm._compact_source_id_selection(root, coverage),
            [row["source_id"] for row in external_rows],
        )

    def test_exact_board_compaction_preserves_semantic_board_reference_authority(self) -> None:
        authority = {
            "schema_version": "spatialaccagent.semantic_board_reference_artifacts.v1",
            "status": "ready",
            "board_input_artifact": {
                "path": "/run/input.memh",
                "sha256": "1" * 64,
                "source_tensor": {"tensor_sha256": "2" * 64, "dtype": "torch.float32"},
            },
            "board_expected_output_artifact": {
                "path": "/run/expected.memh",
                "sha256": "3" * 64,
                "source_tensor": {"tensor_sha256": "4" * 64, "dtype": "torch.float32"},
            },
        }
        bound = {"sha256": "5" * 64, "value": authority}

        compact = stage_llm.compact_exact_board_integration_context(
            {"adaptive_design_inputs": {"semantic_board_reference_artifacts": bound}}
        )

        self.assertEqual(
            compact["adaptive_design_inputs"]["semantic_board_reference_artifacts"],
            bound,
        )

    def test_compact_retry_keeps_fixture_top_and_other_hdl_headers(self) -> None:
        top_source = "module dynamic_fixture_top(input logic clk); endmodule\n"
        child_source = (
            "interface dynamic_bus_if; logic ready; endinterface\n"
            "module dynamic_fixture_child(dynamic_bus_if bus); endmodule\n"
        )
        package = {
            "schema_version": "spatialaccagent.verification_capability_repair_package.v1",
            "exact_board_integration_repair_context": {
                "adaptive_design_inputs": {
                    "external_simulation_fixture": {
                        "path": "/run/external_simulation_fixture.json",
                        "sha256": "d" * 64,
                        "value": {
                            "status": "pass",
                            "providers": [
                                {"filesets": [{"top": "dynamic_fixture_top"}]}
                            ],
                        },
                    }
                }
            },
            "repair_source_bundle": {
                "documents": [
                    {
                        "path": "/run/dynamic_fixture_top.sv",
                        "sha256": "e" * 64,
                        "content": top_source,
                        "external_fixture_example_tops": ["dynamic_fixture_top"],
                    },
                    {
                        "path": "/run/dynamic_fixture_child.sv",
                        "sha256": "f" * 64,
                        "content": child_source,
                        "external_fixture_example_tops": [],
                    },
                ]
            },
        }

        compact = stage_llm.compact_verification_capability_repair_package(package)
        documents = compact["repair_source_bundle"]["documents"]

        self.assertEqual(documents[0]["content"], top_source)
        self.assertNotIn("content", documents[1])
        self.assertEqual(
            documents[1]["module_headers"][0]["module"],
            "dynamic_fixture_child",
        )
        self.assertEqual(
            documents[1]["interface_headers"][0]["interface"],
            "dynamic_bus_if",
        )

    def test_exact_board_compaction_keeps_selected_sample_top_source(self) -> None:
        wrapper_path = "/run/current_sample_top.v"
        wrapper_hash = "4" * 64
        wrapper_source = "module current_sample_top(input wire clk); endmodule\n"
        package = {
            "schema_version": "spatialaccagent.verification_capability_repair_package.v1",
            "exact_board_integration_repair_context": {
                "adaptive_design_inputs": {
                    "exact_board_source_identity": {
                        "value": {
                            "selected_simulation_source_closure": {
                                "source_files": [
                                    {
                                        "source_id": "sample-source:current",
                                        "closure_role": "exact_sample_top",
                                        "path": wrapper_path,
                                        "sha256": wrapper_hash,
                                    }
                                ]
                            }
                        }
                    }
                }
            },
            "repair_source_bundle": {
                "documents": [
                    {
                        "path": wrapper_path,
                        "sha256": wrapper_hash,
                        "content": wrapper_source,
                    },
                    {
                        "path": "/run/unselected.v",
                        "sha256": "5" * 64,
                        "content": "module unselected; endmodule\n",
                    },
                ]
            },
        }

        compact = stage_llm.compact_verification_capability_repair_package(package)
        documents = compact["repair_source_bundle"]["documents"]

        self.assertEqual(documents[0]["content"], wrapper_source)
        self.assertNotIn("content", documents[1])

    def test_single_layer_compaction_keeps_complete_generation_authority(self) -> None:
        paths = {
            "harness": "/run/ConnectedSingleLayerHarness.scala",
            "block": "/run/DecoderBlock.scala",
            "generator": "/repo/scripts/verification/semantic_testbench_generator.py",
            "requirements": "/run/dut_weight_binding_requirements.json#single_layer_closure_requirements_projection",
            "binding": "/run/dut_weight_binding_manifest.json#single_layer_closure_binding_merge_authority",
            "report": "/run/single_layer_functional_report.json",
            "validation_feedback": "/run/agent_requested_validation.json",
        }
        documents = [
            {
                "path": path,
                "sha256": f"{index + 1:064x}",
                "content": (
                    json.dumps({"marker": name, "details": [1, 2, 3]})
                    if ".json" in path
                    else f"// {name}\nclass {name.title().replace('_', '')} {{}}\n"
                ),
            }
            for index, (name, path) in enumerate(paths.items())
        ]
        documents.append(
            {
                "path": "/run/unrelated.scala",
                "sha256": "f" * 64,
                "content": "class Unrelated { val omittedMiddle = 1 }\n" * 200,
            }
        )

        compact = stage_llm.compact_verification_capability_repair_package(
            {
                "verification_scope": "single_layer_closure",
                "repair_source_bundle": {"documents": documents},
            }
        )
        compact_documents = compact["repair_source_bundle"]["documents"]

        for document in compact_documents[:-1]:
            self.assertTrue(
                "content" in document or "json_content" in document,
                document["path"],
            )
        self.assertNotIn("content", compact_documents[-1])
        authority = compact["repair_source_bundle"][
            "single_layer_generation_authority"
        ]
        self.assertEqual(authority["status"], "complete")
        self.assertEqual(
            authority["binding_manifest_update_mode"], "hash_bound_merge_json"
        )

    def test_v5_tables_round_trip_realistic_layer_tensor_and_source_coverage(self) -> None:
        weight_layers = []
        runtime_layers = []
        runtime_bindings = []
        runtime_source_files = []
        for layer_index in range(24):
            stage_segments = []
            layer_tensor_hashes = []
            for stage_index in range(9):
                tensor_count = 2 if stage_index < 3 else 1
                sources = []
                for tensor_index in range(tensor_count):
                    tensor_hash = f"{layer_index * 100 + stage_index * 10 + tensor_index:064x}"
                    layer_tensor_hashes.append(tensor_hash)
                    sources.append(
                        {
                            "layer_index": layer_index,
                            "parameter_suffix": f"stage_{stage_index}.tensor_{tensor_index}",
                            "source_slice_sha256": tensor_hash,
                            "shape": [16, 16],
                            "dtype": "BF16",
                        }
                    )
                stage_segments.append(
                    {
                        "stage_index": stage_index,
                        "stage_id": f"stage_{stage_index:02d}",
                        "tensor_hashes": [row["source_slice_sha256"] for row in sources],
                        "target_segments": [
                            {
                                "target_id": f"target_{stage_index}",
                                "word_offset": stage_index * 256,
                                "word_count": 256,
                                "source_tensors": sources,
                            }
                        ],
                    }
                )
            weight_layers.append(
                {
                    "layer_index": layer_index,
                    "word_offset": layer_index * 2304,
                    "word_count": 2304,
                    "tensor_hashes": layer_tensor_hashes,
                    "stage_segments": stage_segments,
                }
            )

            capture_sources = []
            runtime_targets = []
            for source_index in range(4):
                tensor_hash = f"{10000 + source_index:064x}"
                file_hash = f"{20000 + layer_index * 4 + source_index:064x}"
                path = f"/capture/layers/layer_{layer_index}/source_{source_index}.pt"
                capture_sources.append(
                    {
                        "source_key": f"source_{source_index}",
                        "path": path,
                        "file_sha256": file_hash,
                        "tensor_sha256": tensor_hash,
                        "shape": [16],
                        "dtype": "torch.int64",
                    }
                )
                runtime_source_files.append(copy := capture_sources[-1].copy())
                runtime_targets.append(
                    {
                        "target_id": f"runtime_{source_index}",
                        "source_key": f"source_{source_index}",
                        "source_file_sha256": file_hash,
                        "source_tensor_sha256": tensor_hash,
                    }
                )
            runtime_layers.append(
                {
                    "layer_index": layer_index,
                    "stage_invocations": [
                        {
                            "stage_id": "stage_01",
                            "consumer_op": "self_attention",
                            "sources": capture_sources,
                        }
                    ],
                }
            )
            runtime_bindings.append(
                {
                    "layer_index": layer_index,
                    "segment_id": "runtime_segment_0",
                    "stage_bindings": [
                        {
                            "stage_id": "stage_01",
                            "consumer_op": "self_attention",
                            "targets": runtime_targets,
                        }
                    ],
                }
            )

        compact_weights = stage_llm._compact_weight_layer_segments(weight_layers)
        self.assertEqual(
            stage_llm._decode_compact_weight_layer_segments(compact_weights),
            weight_layers,
        )
        self.assertEqual(len(weight_layers), 24)
        self.assertEqual(sum(len(layer["stage_segments"]) for layer in weight_layers), 216)
        self.assertEqual(sum(len(layer["tensor_hashes"]) for layer in weight_layers), 288)

        capture_contract = {"status": "pass", "target_layer_count": 24, "layers": runtime_layers}
        compact_capture = stage_llm.compact_runtime_capture_contract({"value": capture_contract})["value"]
        self.assertEqual(
            stage_llm._decode_compact_runtime_capture_contract(compact_capture),
            capture_contract,
        )

        runtime_manifest = {
            "status": "pass",
            "target_layer_count": 24,
            "unique_segments": [{"segment_id": "runtime_segment_0", "layer_indices": list(range(24))}],
            "layer_bindings": runtime_bindings,
            "source_tensor_files": runtime_source_files,
        }
        compact_runtime = stage_llm.compact_full_runtime_image_manifest({"value": runtime_manifest})["value"]
        self.assertEqual(
            stage_llm._decode_compact_runtime_image_manifest(compact_runtime),
            runtime_manifest,
        )
        self.assertEqual(len(runtime_source_files), 96)


if __name__ == "__main__":
    unittest.main()
