import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from accagent.framework.flow_action_handoff import (
    HANDOFF_SCHEMA_VERSION,
    action_record_path,
    mark_stage6_flow_handoff_consumed,
    pending_stage6_flow_handoff,
    validate_stage6_flow_handoff,
)


class FlowActionHandoffTest(TestCase):
    def write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def sha256(self, path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def materialize_event(
        self,
        run_dir: Path,
        state_path: Path,
        *,
        index: int,
        action: dict,
        requires_approval: bool = False,
    ) -> Path:
        action = {**action, "requires_approval": requires_approval}
        result_path = (
            run_dir
            / "agent"
            / "flow_controller"
            / f"{index:03d}_debug_loop"
            / "llm"
            / "flow_controller_agent_result.json"
        )
        result = {
            "schema_version": "spatialaccagent.stage_worker_record.v0",
            "agent": "flow_controller_agent",
            "stage": "flow_orchestration",
            "used_fallback": False,
            "error": None,
            "output": {
                "agent": "flow_controller_agent",
                "stage": "debug_loop",
                "status": "retry_current_stage",
                "summary": "run the current operator-leaf repair closure",
                "executable_actions": [action],
            },
        }
        self.write_json(result_path, result)
        event_path = run_dir / "debug_loop" / "flow_events" / f"{index:03d}_retry.json"
        event = {
            "schema_version": "spatialaccagent.flow_event_action_record.v0",
            "flow_event_index": index,
            "stage": "debug_loop",
            "decision": "retry",
            "sacg_state": str(state_path),
            "llm_flow_controller": {"agent_record": str(result_path)},
            "executable_actions": [action],
            "source_identities": {
                "source_sacg_state_sha256": self.sha256(state_path),
                "flow_controller_result_sha256": self.sha256(result_path),
            },
        }
        self.write_json(event_path, event)
        action_path = action_record_path(event_path, index, action)
        self.write_json(
            action_path,
            {
                "schema_version": "spatialaccagent.flow_action_record.v0",
                "source_flow_event": str(event_path),
                "action": action,
            },
        )
        return event_path

    def valid_action(self, identifier: str) -> dict:
        return {
            "id": identifier,
            "stage": "debug_loop",
            "action_type": "real_tool_execution",
            "acceptance_checkers": ["case_stage_leaf_static"],
            "tool_roles": ["case_stage_leaf_static"],
            "consumes": ["artifact.stage5.verification_artifact_contract"],
            "produces": ["verification/operator_leaf/leaf_static_report.json"],
            "rationale": "Run the current required operator-leaf static gate.",
            "on_failure": "Keep the current layer blocked and localize the failure.",
        }

    def test_current_handoff_is_consumed_once_and_new_source_is_eligible(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            state_path = run_dir / "verification_artifacts" / "sacg_state.json"
            self.write_json(state_path, {"artifacts": [], "transitions": [], "memory": {}})
            self.materialize_event(
                run_dir,
                state_path,
                index=1,
                action=self.valid_action("debug_loop.run_leaf_static"),
            )

            handoff = pending_stage6_flow_handoff(run_dir, state_path)
            self.assertEqual(handoff["schema_version"], HANDOFF_SCHEMA_VERSION)
            self.assertEqual(handoff["status"], "ready")
            self.assertEqual(validate_stage6_flow_handoff(handoff, run_dir), [])

            repair_plan = run_dir / "repair" / "repair_plan.json"
            self.write_json(repair_plan, {"status": "needs_repair"})
            mark_stage6_flow_handoff_consumed(run_dir, handoff, repair_plan)
            self.assertEqual(
                pending_stage6_flow_handoff(run_dir, state_path)["status"],
                "already_consumed",
            )

            self.write_json(
                state_path,
                {"artifacts": [{"id": "artifact.stage6.real_tool_results"}], "transitions": [], "memory": {}},
            )
            self.materialize_event(
                run_dir,
                state_path,
                index=2,
                action=self.valid_action("debug_loop.run_leaf_static_after_new_observation"),
            )
            refreshed = pending_stage6_flow_handoff(run_dir, state_path)
            self.assertEqual(refreshed["status"], "ready")
            self.assertNotEqual(refreshed["handoff_identity"], handoff["handoff_identity"])

    def test_latest_invalid_or_approval_only_handoff_fails_closed(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            state_path = run_dir / "verification_artifacts" / "sacg_state.json"
            self.write_json(state_path, {"artifacts": [], "transitions": [], "memory": {}})
            self.materialize_event(
                run_dir,
                state_path,
                index=1,
                action=self.valid_action("debug_loop.valid_old_action"),
            )
            self.materialize_event(
                run_dir,
                state_path,
                index=2,
                action=self.valid_action("debug_loop.approval_only_action"),
                requires_approval=True,
            )

            result = pending_stage6_flow_handoff(run_dir, state_path)
            self.assertEqual(result["status"], "blocked")
            self.assertIn("no auto-executable", result["summary"])

    def test_source_identity_drift_is_rejected(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            state_path = run_dir / "verification_artifacts" / "sacg_state.json"
            self.write_json(state_path, {"artifacts": [], "transitions": [], "memory": {}})
            self.materialize_event(
                run_dir,
                state_path,
                index=1,
                action=self.valid_action("debug_loop.source_bound_action"),
            )
            self.write_json(state_path, {"artifacts": [{"id": "changed"}], "transitions": [], "memory": {}})

            result = pending_stage6_flow_handoff(run_dir, state_path)
            self.assertEqual(result["status"], "blocked")
            self.assertIn("source SACG identity is stale", result["summary"])
