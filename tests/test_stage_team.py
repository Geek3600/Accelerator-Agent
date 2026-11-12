from __future__ import annotations

import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from accagent.framework import stage_team
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


class TeamDecomposerWireApiTests(TestCase):
    def test_decomposer_and_json_repair_use_configured_chat_completions(self) -> None:
        llm = SimpleNamespace(
            mode="llm",
            enforce=True,
            configuration_error="",
            api_key="test-key",
            endpoint="https://example.invalid/v1/chat/completions",
            model="claude-opus-5",
            wire_api="chat/completions",
            stream=False,
            http_transport="urllib",
            reasoning_effort=None,
            store=False,
            text_verbosity=None,
            max_output_tokens=256,
            fallback_endpoint="",
            fallback_api_key="",
        )
        valid_result = json.dumps({
            "schema_version": "spatialaccagent.team_decomposition.v0",
            "stage": "input_preparation",
            "split_required": False,
            "reason": "The stage is atomic.",
            "subtasks": [],
        })
        observed = []

        def respond(request, timeout_sec, label, stream):
            observed.append((request.full_url, json.loads(request.data.decode("utf-8"))))
            return ("not-json" if len(observed) == 1 else valid_result), []

        with tempfile.TemporaryDirectory() as temporary, \
             patch.object(stage_team, "resolved_llm_cfg", return_value=llm), \
             patch.object(stage_team, "post_decomposer_json", side_effect=respond):
            result = stage_team.call_decomposer("test prompt", Path(temporary))

        self.assertEqual(result["output"]["reason"], "The stage is atomic.")
        self.assertEqual(len(observed), 2)
        for endpoint, payload in observed:
            self.assertEqual(endpoint, llm.endpoint)
            self.assertIn("messages", payload)
            self.assertNotIn("input", payload)
            self.assertIn("response_format", payload)
