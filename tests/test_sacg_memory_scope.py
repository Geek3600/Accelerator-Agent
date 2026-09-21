"""Stage-6 scoped SACG memory regressions."""

from __future__ import annotations

import unittest

from accagent.framework.sacg_utils import (
    hierarchy_memory_context,
    scoped_sacg_memory_summary,
)
from accagent.framework.stage_llm import stage_agent_memory_scope


class SacgMemoryScopeTest(unittest.TestCase):
    def test_current_scope_excludes_other_layer_history_from_hot_context(self) -> None:
        state = {
            "memory": {
                "failure_lessons": [
                    {"id": "leaf", "verification_scope": "operator_leaf_closure", "debug_layer": "operator_leaf_modules"},
                    {"id": "board", "verification_scope": "board_axi_ddr_closure", "debug_layer": "board_axi_ddr_wrapped_system"},
                ],
                "retry_requests": [
                    {"id": "leaf-retry", "status": "open", "verification_scope": "operator_leaf_closure", "debug_layer": "operator_leaf_modules"},
                    {"id": "board-retry", "status": "open", "verification_scope": "board_axi_ddr_closure", "debug_layer": "board_axi_ddr_wrapped_system"},
                ],
            }
        }

        summary = scoped_sacg_memory_summary(
            state,
            verification_scope="board_axi_ddr_closure",
            debug_layer="board_axi_ddr_wrapped_system",
        )

        self.assertEqual([row["id"] for row in summary["recent_failure_lessons"]], ["board"])
        self.assertEqual([row["id"] for row in summary["open_retry_requests"]], ["board-retry"])

    def test_prompt_scope_tracks_the_current_repair_step(self) -> None:
        scope = stage_agent_memory_scope(
            {"repair_step": {"action": {"debug_layer": "single_transformer_layer_kernel"}}}
        )

        self.assertEqual(scope["verification_scope"], "single_layer_closure")
        self.assertEqual(scope["debug_layer"], "single_transformer_layer_kernel")

    def test_hierarchy_context_normalizes_failed_gate_identity(self) -> None:
        context = hierarchy_memory_context(
            verification_scope="leaf",
            failed_gates=[{"name": "case_semantic_testbench", "status": "fail"}, "case_semantic_testbench"],
            source_fingerprint_sha256="A" * 64,
        )

        self.assertEqual(context["verification_scope"], "operator_leaf_closure")
        self.assertEqual(context["failed_gates"], ["case_semantic_testbench"])
        self.assertEqual(context["source_fingerprint_sha256"], "a" * 64)


if __name__ == "__main__":
    unittest.main()
