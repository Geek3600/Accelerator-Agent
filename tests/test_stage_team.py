from __future__ import annotations

from unittest import TestCase

from accagent.framework.stage_team import acceptance_checkers_for, compact_backend_board_for_prompt, normalize_llm_subtasks


class StageTeamAcceptanceCheckersTests(TestCase):
    def test_role_names_cannot_create_nested_artifact_paths(self) -> None:
        tasks = normalize_llm_subtasks("backend_board", [
            {"role": "runtime", "agent": "Data/memory/runtime specialist"},
            {"role": "review", "agent": "data_memory_runtime_specialist"},
        ])
        names = [task["agent"] for task in tasks]
        self.assertEqual(len(set(names)), 2)
        self.assertTrue(all("/" not in name and " " not in name for name in names))

    def test_backend_prompt_keeps_validated_unchanged_stage6_selection(self) -> None:
        selection = {"status": "pass", "human_approval_claimed": False, "source": "current-board-identity.json"}
        compacted = compact_backend_board_for_prompt({
            "stage": "backend_board", "llm_decision_packet": {"validated_stage6_selection": selection},
        })
        self.assertEqual(compacted["validated_stage6_selection"], selection)

    def test_board_work_uses_the_registered_real_tool_evidence_gate(self) -> None:
        checkers = acceptance_checkers_for([], ["exact board AXI/DDR functional verification"])

        self.assertIn("required_real_tool_evidence_check", checkers)
        self.assertNotIn("real_tool_evidence_check", checkers)

    def test_backend_prompt_keeps_real_tool_failure_diagnostics(self) -> None:
        diagnostic = "ERROR: [DRC MDRV-1] Multiple Driver Nets on cnn_core_0/<const0>."
        candidate = {
            "stage": "backend_board",
            "llm_decision_packet": {
                "selected_real_tools": [
                    {
                        "checker": "real_tool.app_shell_runtime_bitstream",
                        "status": "fail",
                        "tool_report_digest": {
                            "status": "fail",
                            "failure_diagnostics": [diagnostic],
                        },
                    }
                ]
            },
        }

        compacted = compact_backend_board_for_prompt(candidate)

        self.assertIn(
            diagnostic,
            compacted["selected_real_tools"][0]["tool_report_digest"]["failure_diagnostics"],
        )
