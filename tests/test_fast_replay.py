import json
import tempfile
import unittest
from pathlib import Path

from accagent.framework.fast_replay import (
    classify_changed_sources,
    fast_replay_decision,
    fast_replay_request_path,
    fast_replay_state_path,
    restore_inputs,
    validate_fast_replay_state,
    stable_checkpoint_lifecycle,
    update_fast_replay_state,
    validate_stable_checkpoint,
)


class FastReplayTest(unittest.TestCase):
    def test_restore_inputs_ignore_current_source_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            manifest_path = (
                run_dir
                / "verification"
                / "simulation_checkpoints"
                / "checkpoint-1"
                / "manifest.json"
            )
            manifest_path.parent.mkdir(parents=True)
            manifest_path.write_text(
                '{"status":"pass","remote_acknowledgment_status":"pass",'
                '"remote_workdir":"/remote/replay","state_artifacts":['
                '{"kind":"native_vcs_snapshot",'
                '"remote_path":"checkpoint/native_state",'
                '"remote_files_path":"checkpoint/native_state.FILES"}]}'
                "\n",
                encoding="utf-8",
            )
            state_path = fast_replay_state_path(run_dir)
            state_path.parent.mkdir(parents=True)
            state_path.write_text(
                '{"status":"captured","remote_workdir":"/remote/replay",'
                '"simulator_path":"vcs_work/simv",'
                f'"checkpoint_manifest":"{manifest_path}"}}\n',
                encoding="utf-8",
            )
            result = restore_inputs(run_dir)

        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["native_snapshot_path"], "checkpoint/native_state")
        self.assertEqual(
            result["native_snapshot_files_path"],
            "checkpoint/native_state.FILES",
        )

    def test_compiled_board_testbench_change_requires_a_new_model_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            simv = root / "simv"
            checkpoint = root / "checkpoint.json"
            simv.write_bytes(b"simv")
            checkpoint.write_text("{}", encoding="utf-8")
            classification = classify_changed_sources(
                ["/run/generated/board_integration/board_tb.sv"]
            )
            decision = fast_replay_decision(
                enabled=True,
                source_classification=classification,
                compiled_model_sha256="model",
                workload_sha256="workload",
                cached_simv=simv,
                token_checkpoint_manifest=checkpoint,
                current_checkpoint_identity={
                    "compiled_model_sha256": "model",
                    "workload_sha256": "workload",
                },
            )
        self.assertEqual(classification["kind"], "functional")
        self.assertEqual(decision["status"], "cold_required_for_model_change")
        self.assertFalse(decision["reuse_compiled_simv"])
        self.assertTrue(decision["final_acceptance_requires_cold_run"])

    def test_runtime_observation_change_can_reuse_matching_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            simv = root / "simv"
            checkpoint = root / "checkpoint.json"
            simv.write_bytes(b"simv")
            checkpoint.write_text("{}", encoding="utf-8")
            classification = classify_changed_sources(
                ["/run/runtime_observation/board_observer.jsonl"]
            )
            decision = fast_replay_decision(
                enabled=True,
                source_classification=classification,
                compiled_model_sha256="model",
                workload_sha256="workload",
                cached_simv=simv,
                token_checkpoint_manifest=checkpoint,
                current_checkpoint_identity={
                    "compiled_model_sha256": "model",
                    "workload_sha256": "workload",
                },
            )
        self.assertEqual(decision["status"], "ready")
        self.assertTrue(decision["reuse_compiled_simv"])

    def test_functional_change_requires_cold_model_run(self) -> None:
        classification = classify_changed_sources(
            ["/run/sources/GatedMLP.sv"]
        )
        decision = fast_replay_decision(
            enabled=True,
            source_classification=classification,
            compiled_model_sha256="model",
            workload_sha256="workload",
            cached_simv=None,
            token_checkpoint_manifest=None,
        )
        self.assertEqual(classification["kind"], "functional")
        self.assertEqual(decision["status"], "cold_required_for_model_change")
        self.assertFalse(decision["reuse_compiled_simv"])

    def test_missing_observation_cache_is_preparation_not_cold_fallback(self) -> None:
        classification = classify_changed_sources(
            ["/run/runtime_observation/board_observer.jsonl"]
        )
        decision = fast_replay_decision(
            enabled=True,
            source_classification=classification,
            compiled_model_sha256="model",
            workload_sha256="workload",
            cached_simv=None,
            token_checkpoint_manifest=None,
        )
        self.assertEqual(decision["status"], "prepare_fast_replay")
        self.assertEqual(decision["mode"], "prepare_fast_replay")
        self.assertNotEqual(decision["mode"], "cold_vcs")

    def test_mixed_change_is_never_treated_as_observation_only(self) -> None:
        classification = classify_changed_sources(
            [
                "/run/generated/board_integration/board_tb.sv",
                "/run/sources/GatedMLP.sv",
            ]
        )
        self.assertEqual(classification["kind"], "functional")

    def test_checkpoint_is_captured_once_at_fixed_token_cut(self) -> None:
        identity = {"compiled_model_sha256": "model", "workload_sha256": "workload"}
        first = stable_checkpoint_lifecycle(
            enabled=True, identity=identity, checkpoint=None
        )
        self.assertEqual(first["action"], "capture_once")
        self.assertEqual(first["cut"], "after_weight_load_before_first_token")
        captured = {
            "identity": {
                "compiled_model_sha256": "model",
                "workload_sha256": "workload",
                "cut": "after_weight_load_before_first_token",
            },
            "status": "captured",
            "verified": False,
            "capture_attempts": 1,
            "restore_attempts": 0,
        }
        second = stable_checkpoint_lifecycle(
            enabled=True, identity=identity, checkpoint=captured
        )
        self.assertEqual(second["action"], "restore_once_and_check")
        exhausted = dict(captured, restore_attempts=1)
        third = stable_checkpoint_lifecycle(
            enabled=True, identity=identity, checkpoint=exhausted
        )
        self.assertEqual(third["action"], "repair_or_recapture")
        self.assertEqual(third["status"], "repair_required")

    def test_verified_checkpoint_is_reused_without_new_capture(self) -> None:
        identity = {"compiled_model_sha256": "model", "workload_sha256": "workload"}
        checkpoint = {
            "identity": {
                "compiled_model_sha256": "model",
                "workload_sha256": "workload",
                "cut": "after_weight_load_before_first_token",
            },
            "status": "ready",
            "verified": True,
            "capture_attempts": 1,
            "restore_attempts": 1,
        }
        decision = stable_checkpoint_lifecycle(
            enabled=True, identity=identity, checkpoint=checkpoint
        )
        self.assertEqual(decision["action"], "restore_and_run")
        self.assertEqual(decision["capture_attempts"], 1)

    def test_old_extra_fields_do_not_invalidate_current_checkpoint(self) -> None:
        result = validate_stable_checkpoint(
            {
                "identity": {
                    "compiled_model_sha256": "model",
                    "workload_sha256": "workload",
                    "cut": "after_weight_load_before_first_token",
                },
                "verified": True,
                "old_hash": "stale-value",
                "legacy_field": {"wrong": "shape"},
            },
            compiled_model_sha256="model",
            workload_sha256="workload",
        )
        self.assertEqual(result["status"], "ready")
        self.assertTrue(result["ignored_historical_fields"])

    def test_missing_or_old_checkpoint_is_not_a_framework_block(self) -> None:
        result = validate_stable_checkpoint(
            {"old_hash": "stale-value"},
            compiled_model_sha256="model",
            workload_sha256="workload",
        )
        self.assertEqual(result["status"], "not_reusable")
        self.assertFalse(result["selected"])
        self.assertNotEqual(result["status"], "blocked")

    def test_failed_checkpoint_requires_repair_for_one_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            state = update_fast_replay_state(
                run_dir,
                {
                    "simulation_execution_identity": {
                        "compiled_model_sha256": "model",
                        "workload_sha256": "workload",
                    },
                    "checkpoint_execution": {"mode": "cold_capture"},
                    "checkpoint_artifacts": {
                        "status": "fail",
                        "failure_class": "capture_failed",
                        "errors": ["capture report missing"],
                    },
                },
            )
            persisted = fast_replay_state_path(run_dir)
            self.assertTrue(persisted.is_file())
        self.assertEqual(state["status"], "repair_required")
        self.assertEqual(state["next_action"], "repair_or_recapture")
        self.assertEqual(state["capture_attempts"], 1)

    def test_failed_checkpoint_reuses_matching_compiled_simulator_for_recapture(self) -> None:
        identity = {"compiled_model_sha256": "model", "workload_sha256": "workload"}
        decision = stable_checkpoint_lifecycle(
            enabled=True,
            identity=identity,
            checkpoint={
                "identity": {
                    **identity,
                    "cut": "after_weight_load_before_first_token",
                },
                "status": "repair_required",
                "remote_workdir": "/remote/layer3",
                "simulator_path": "vcs_work/simv",
                "capture_attempts": 1,
            },
        )
        self.assertEqual(decision["status"], "recapture_required")
        self.assertEqual(decision["action"], "recapture_existing_simv")

    def test_legacy_restore_failure_retries_saved_snapshot_once(self) -> None:
        identity = {"compiled_model_sha256": "model", "workload_sha256": "workload"}
        decision = stable_checkpoint_lifecycle(
            enabled=True,
            identity=identity,
            checkpoint={
                "identity": {
                    **identity,
                    "cut": "after_weight_load_before_first_token",
                },
                "status": "repair_required",
                "checkpoint_manifest": "/checkpoint/manifest.json",
                "restore_attempts": 0,
                "capture_attempts": 1,
            },
        )

        self.assertEqual(decision["status"], "restore_check_required")
        self.assertEqual(decision["action"], "restore_once_and_check")

    def test_confirmed_capture_persists_one_reusable_remote_simulator(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            request_path = run_dir / "requests" / "capture.json"
            request_path.parent.mkdir(parents=True)
            request_path.write_text(
                '{"execution_identity":{"compiled_model_sha256":"model","workload_sha256":"workload"}}\n',
                encoding="utf-8",
            )
            manifest_path = (
                run_dir
                / "verification"
                / "simulation_checkpoints"
                / "checkpoint-1"
                / "manifest.json"
            )
            manifest_path.parent.mkdir(parents=True)
            manifest_path.write_text(
                '{"checkpoint_id":"checkpoint-1",'
                '"execution_identity":{"compiled_model_sha256":"model","workload_sha256":"workload"},'
                '"remote_workdir":"/remote/replay",'
                '"remote_acknowledgment_status":"pass",'
                '"state_artifacts":[{"kind":"native_vcs_snapshot",'
                '"remote_path":"checkpoint/native_state",'
                '"remote_files_path":"checkpoint/native_state.FILES"}]}\n',
                encoding="utf-8",
            )
            state = update_fast_replay_state(
                run_dir,
                {
                    "simulation_execution_identity": {
                        "compiled_model_sha256": "model",
                        "workload_sha256": "workload",
                    },
                    "remote_workdir": "/remote/replay",
                    "simulator_path": "vcs_work/simv",
                    "checkpoint_execution": {
                        "mode": "cold_capture",
                        "request_path": str(request_path),
                    },
                    "checkpoint_artifacts": {
                        "status": "pass",
                        "equivalence_status": "pass",
                        "remote_acknowledgment_status": "pass",
                        "manifest": str(manifest_path),
                    },
                },
            )
            validation = validate_fast_replay_state(
                run_dir,
                state,
                current_identity={
                    "compiled_model_sha256": "model",
                    "workload_sha256": "workload",
                },
            )

            self.assertEqual(state["status"], "captured")
            self.assertFalse(state["verified"])
            self.assertEqual(state["restore_attempts"], 0)
            self.assertEqual(state["next_action"], "restore_once_and_check")
            self.assertTrue(fast_replay_request_path(run_dir).is_file())
            pending = validate_fast_replay_state(
                run_dir,
                state,
                current_identity={
                    "compiled_model_sha256": "model",
                    "workload_sha256": "workload",
                },
                require_verified=False,
            )
            self.assertEqual(pending["status"], "ready")
            self.assertEqual(pending["remote_workdir"], "/remote/replay")
            self.assertEqual(pending["simulator_path"], "vcs_work/simv")

            state = update_fast_replay_state(
                run_dir,
                {
                    "simulation_execution_identity": {
                        "compiled_model_sha256": "model",
                        "workload_sha256": "workload",
                    },
                    "remote_workdir": "/remote/replay",
                    "simulator_path": "vcs_work/simv",
                    "checkpoint_execution": {
                        "mode": "native_exact_model",
                    },
                    "checkpoint_artifacts": {
                        "status": "pass",
                    },
                },
            )
            self.assertEqual(state["status"], "ready")
            self.assertTrue(state["verified"])
            self.assertEqual(state["next_action"], "restore_and_run")

    def test_recapture_completion_transitions_back_to_restore_check(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            request_path = run_dir / "requests" / "recapture.json"
            request_path.parent.mkdir(parents=True)
            request_path.write_text(
                '{"execution_identity":{"compiled_model_sha256":"model",'
                '"workload_sha256":"workload"}}\n',
                encoding="utf-8",
            )
            manifest_path = (
                run_dir / "verification" / "simulation_checkpoints" / "checkpoint-1" / "manifest.json"
            )
            manifest_path.parent.mkdir(parents=True)
            manifest_path.write_text(
                '{"checkpoint_id":"checkpoint-1",'
                '"execution_identity":{"compiled_model_sha256":"model",'
                '"workload_sha256":"workload"},'
                '"remote_workdir":"/remote/replay",'
                '"remote_acknowledgment_status":"pass",'
                '"state_artifacts":[{"kind":"native_vcs_snapshot",'
                '"remote_path":"checkpoint/native_state",'
                '"remote_files_path":"checkpoint/native_state.FILES"}]}\n',
                encoding="utf-8",
            )
            fast_replay_state_path(run_dir).parent.mkdir(parents=True)
            fast_replay_state_path(run_dir).write_text(
                '{"status":"repair_required","capture_attempts":1,'
                '"restore_attempts":4,'
                '"remote_workdir":"/remote/old",'
                '"simulator_path":"vcs_work/simv"}\n',
                encoding="utf-8",
            )
            state = update_fast_replay_state(
                run_dir,
                {
                    "simulation_execution_identity": {
                        "compiled_model_sha256": "model",
                        "workload_sha256": "workload",
                    },
                    "remote_workdir": "/remote/replay",
                    "simulator_path": "vcs_work/simv",
                    "checkpoint_execution": {
                        "mode": "cold_capture",
                        "request_path": str(request_path),
                    },
                    "checkpoint_artifacts": {
                        "status": "pass",
                        "remote_acknowledgment_status": "pass",
                        "manifest": str(manifest_path),
                    },
                },
            )

        self.assertEqual(state["status"], "captured")
        self.assertFalse(state["verified"])
        self.assertEqual(state["next_action"], "restore_once_and_check")

    def test_restore_progress_keeps_snapshot_reusable_after_hardware_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            fast_replay_state_path(run_dir).parent.mkdir(parents=True)
            fast_replay_state_path(run_dir).write_text(
                '{"status":"repair_required","capture_attempts":1,'
                '"restore_attempts":1}\n',
                encoding="utf-8",
            )
            state = update_fast_replay_state(
                run_dir,
                {
                    "status": "fail",
                    "simulation_execution_identity": {
                        "compiled_model_sha256": "model",
                        "workload_sha256": "workload",
                    },
                    "checkpoint_execution": {"mode": "native_exact_model"},
                    "checkpoint_artifacts": {
                        "status": "fail",
                        "native_restore_marker_seen": True,
                    },
                },
            )

        self.assertEqual(state["status"], "ready")
        self.assertTrue(state["verified"])
        self.assertTrue(state["last_replay"]["restore_confirmed"])

    def test_three_distinct_restores_increment_reuse_without_recapture(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            state_path = fast_replay_state_path(run_dir)
            state_path.parent.mkdir(parents=True)
            state_path.write_text(
                json.dumps(
                    {
                        "status": "ready",
                        "verified": True,
                        "capture_attempts": 1,
                        "restore_attempts": 1,
                        "reuse_count": 0,
                        "identity": {
                            "compiled_model_sha256": "model",
                            "workload_sha256": "workload",
                            "cut": "after_weight_load_before_first_token",
                        },
                    }
                ),
                encoding="utf-8",
            )
            for generation in (2, 3, 4):
                state = update_fast_replay_state(
                    run_dir,
                    {
                        "status": "fail",
                        "input_fingerprint_sha256": "stable-replay",
                        "remote_workdir": "/remote/replay",
                        "simulation_execution_identity": {
                            "compiled_model_sha256": "model",
                            "workload_sha256": "workload",
                        },
                        "observation_epoch": {"generation": generation},
                        "checkpoint_execution": {"mode": "native_exact_model"},
                        "checkpoint_artifacts": {
                            "status": "pass",
                            "native_restore_marker_seen": True,
                        },
                    },
                )
                self.assertEqual(state["status"], "ready")
                self.assertEqual(state["capture_attempts"], 1)

            duplicate = update_fast_replay_state(
                run_dir,
                {
                    "status": "fail",
                    "input_fingerprint_sha256": "stable-replay",
                    "remote_workdir": "/remote/replay",
                    "simulation_execution_identity": {
                        "compiled_model_sha256": "model",
                        "workload_sha256": "workload",
                    },
                    "observation_epoch": {"generation": 4},
                    "checkpoint_execution": {"mode": "native_exact_model"},
                    "checkpoint_artifacts": {
                        "status": "pass",
                        "native_restore_marker_seen": True,
                    },
                },
            )

        self.assertEqual(duplicate["capture_attempts"], 1)
        self.assertEqual(duplicate["reuse_count"], 3)

    def test_new_model_capture_does_not_inherit_old_snapshot_counters(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            request_path = run_dir / "requests" / "new-model.json"
            request_path.parent.mkdir(parents=True)
            request_path.write_text(
                '{"execution_identity":{"compiled_model_sha256":"new-model",'
                '"workload_sha256":"workload"}}\n',
                encoding="utf-8",
            )
            manifest_path = (
                run_dir
                / "verification"
                / "simulation_checkpoints"
                / "new-checkpoint"
                / "manifest.json"
            )
            manifest_path.parent.mkdir(parents=True)
            manifest_path.write_text(
                '{"checkpoint_id":"new-checkpoint",'
                '"execution_identity":{"compiled_model_sha256":"new-model",'
                '"workload_sha256":"workload"},'
                '"remote_workdir":"/remote/new",'
                '"remote_acknowledgment_status":"pass",'
                '"state_artifacts":[{"kind":"native_vcs_snapshot",'
                '"remote_path":"checkpoint/native_state"}]}\n',
                encoding="utf-8",
            )
            state_path = fast_replay_state_path(run_dir)
            state_path.parent.mkdir(parents=True)
            state_path.write_text(
                json.dumps(
                    {
                        "status": "ready",
                        "verified": True,
                        "capture_attempts": 7,
                        "restore_attempts": 11,
                        "reuse_count": 10,
                        "identity": {
                            "compiled_model_sha256": "old-model",
                            "workload_sha256": "workload",
                            "cut": "after_weight_load_before_first_token",
                        },
                    }
                ),
                encoding="utf-8",
            )

            state = update_fast_replay_state(
                run_dir,
                {
                    "simulation_execution_identity": {
                        "compiled_model_sha256": "new-model",
                        "workload_sha256": "workload",
                    },
                    "remote_workdir": "/remote/new",
                    "simulator_path": "vcs_work/simv",
                    "checkpoint_execution": {
                        "mode": "cold_capture",
                        "request_path": str(request_path),
                    },
                    "checkpoint_artifacts": {
                        "status": "pass",
                        "remote_acknowledgment_status": "pass",
                        "manifest": str(manifest_path),
                    },
                },
            )

        self.assertEqual(state["capture_attempts"], 1)
        self.assertEqual(state["restore_attempts"], 0)
        self.assertEqual(state["reuse_count"], 0)
        self.assertEqual(state["checkpoint_id"], "new-checkpoint")


if __name__ == "__main__":
    unittest.main()
