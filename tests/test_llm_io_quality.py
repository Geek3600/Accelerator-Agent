from unittest import TestCase

from accagent.framework.llm_io_quality import build_quality_report, rows_from_stage_records
from accagent.framework.stage_verification_plan import build_stage5_action_materialization_coverage


class LlmIoQualityTest(TestCase):
    def test_ready_planner_noop_is_valid_when_team_supplies_actions(self) -> None:
        rows = rows_from_stage_records(
            {
                "agent": "verification_planner_agent",
                "output": {"status": "ready", "executable_actions": []},
                "prompt_bytes": 100,
                "duration_sec": 1,
            },
            {
                "results": [
                    {
                        "subtask": {"agent": "leaf_engineer"},
                        "output": {"status": "ready"},
                        "used_fallback": False,
                        "llm_io": {"executable_action_count": 1},
                    }
                ]
            },
        )

        report = build_quality_report(rows)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(
            report["agents"][0]["action_requirement_note"],
            "ready planner supplied a complete plan and downstream actions",
        )

    def test_ready_planner_noop_is_valid_without_team_actions(self) -> None:
        report = build_quality_report(
            rows_from_stage_records(
                {
                    "agent": "verification_planner_agent",
                    "output": {
                        "status": "ready",
                        "summary": "All current-stage plan and contract checks passed.",
                        "proposed_actions": ["Execute the planned verification gates in the next stage."],
                        "executable_actions": [],
                    },
                },
                {"results": []},
            )
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["agents"][0]["executable_action_count"], 0)

    def test_actionable_planner_still_requires_actions(self) -> None:
        report = build_quality_report(
            rows_from_stage_records(
                {
                    "agent": "planner",
                    "output": {"status": "needs_repair", "executable_actions": []},
                },
                {"results": []},
            )
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("LLM produced no executable_actions", report["summary"]["errors"])

    def test_empty_refinement_set_is_ready_only_when_materialized_contracts_are_ready(self) -> None:
        ready = build_stage5_action_materialization_coverage(
            [],
            {"gate_selector": {"status": "ready"}, "semantic_contract": {"status": "pass"}},
        )
        incomplete = build_stage5_action_materialization_coverage(
            [],
            {"gate_selector": {"status": "incomplete"}},
        )

        self.assertEqual(ready["status"], "ready")
        self.assertEqual(ready["fulfillment"], "no_stage5_refinement_required")
        self.assertEqual(incomplete["status"], "incomplete")
