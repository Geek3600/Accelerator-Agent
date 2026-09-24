"""Focused regressions for model-derived operator-leaf inventory evidence."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from accagent.framework.stage_repair import required_capability_repair_actions
from accagent.framework.stage_repair_execute import (
    check_operator_leaf_static_inventory_trace,
    operator_leaf_static_inventory_trace,
)
from accagent.framework.stage_verification_plan import (
    build_hierarchical_verification_plan,
    leaf_module_checks,
)


class OperatorLeafInventoryTraceTest(unittest.TestCase):
    def test_leaf_requirements_follow_model_semantics(self) -> None:
        qwen = {
            "norm": {"type": "rms_norm"},
            "attention": {"kind": "gqa", "position_encoding": {"type": "rope"}},
            "mlp": {"type": "gated"},
        }
        gpt2 = {
            "norm": {"type": "layer_norm"},
            "attention": {
                "kind": "mha",
                "position_encoding": {"type": "learned_absolute"},
            },
            "mlp": {"type": "dense"},
        }
        self.assertEqual(leaf_module_checks({"kind": "norm"}, qwen), ["RMSNorm"])
        self.assertEqual(
            leaf_module_checks({"kind": "attention"}, qwen),
            ["QKVProjection", "AttentionGQA", "RoPE", "Linear_1"],
        )
        self.assertEqual(
            leaf_module_checks({"kind": "residual"}, qwen),
            ["ResidualAdd", "PhysicalStreamFifo"],
        )
        self.assertEqual(leaf_module_checks({"kind": "norm"}, gpt2), ["VectorNorm"])
        self.assertEqual(
            leaf_module_checks({"kind": "attention"}, gpt2),
            ["QKVProjection", "Attention", "Linear_1"],
        )
        self.assertEqual(leaf_module_checks({"kind": "mlp"}, gpt2), ["DenseFFN"])
        self.assertEqual(leaf_module_checks({"kind": "activation"}, gpt2), ["Activation"])

    def test_hierarchy_uses_the_same_model_derived_requirements(self) -> None:
        model = {
            "norm": {"type": "layer_norm"},
            "attention": {
                "kind": "mha",
                "position_encoding": {"type": "learned_absolute"},
            },
            "mlp": {"type": "dense"},
        }
        hierarchy = build_hierarchical_verification_plan(
            {
                "stages": [
                    {"stage_id": "norm", "kind": "norm"},
                    {"stage_id": "attention", "kind": "attention"},
                    {"stage_id": "residual", "kind": "residual"},
                    {"stage_id": "mlp", "kind": "mlp"},
                ]
            },
            {},
            model,
        )
        checks = {
            row["stage_id"]: row["module_checks"]
            for row in hierarchy["stage_agents"]
        }
        self.assertEqual(checks["norm"], ["VectorNorm"])
        self.assertEqual(checks["attention"], ["QKVProjection", "Attention", "Linear_1"])
        self.assertEqual(checks["residual"], ["ResidualAdd", "PhysicalStreamFifo"])
        self.assertEqual(checks["mlp"], ["DenseFFN"])

    def test_read_only_inventory_classifies_stale_static_report(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            generated = run_dir / "generated" / "chisel"
            reports = run_dir / "verification" / "real_tools"
            out_dir = run_dir / "repair_execution"
            for path in (generated, reports, out_dir, run_dir / "input", run_dir / "pipeline_planning"):
                path.mkdir(parents=True, exist_ok=True)
            (run_dir / "input" / "model_config.json").write_text(
                json.dumps(
                    {
                        "norm": {"type": "rms_norm"},
                        "attention": {"kind": "gqa", "position_encoding": {"type": "rope"}},
                        "mlp": {"type": "gated"},
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "pipeline_planning" / "pipeline_plan.json").write_text(
                json.dumps(
                    {
                        "stages": [
                            {
                                "stage_id": "stage_02_residual_add_1",
                                "kind": "residual",
                                "op": "residual_add_1",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            for name in ("ResidualAdd", "PhysicalStreamFifo"):
                (generated / f"{name}.sv").write_text(
                    f"module {name}; endmodule\n", encoding="utf-8"
                )
            stale_report = reports / "case_stage_leaf_static__leaf_stage_stage_02_residual_add_1.json"
            stale_report.write_text(
                json.dumps({"status": "fail", "blockers": ["missing Queue"]}),
                encoding="utf-8",
            )

            trace = operator_leaf_static_inventory_trace(run_dir)
            result = check_operator_leaf_static_inventory_trace(
                run_dir=run_dir,
                out_dir=out_dir,
                step={
                    "id": "repair.inventory_check",
                    "action": {
                        "requested_capability_id": (
                            "planned_checker.operator_leaf_static_inventory_trace_check"
                        )
                    },
                },
            )
            package = json.loads(Path(result["context_package"]).read_text(encoding="utf-8"))

        self.assertEqual(trace["status"], "pass")
        self.assertEqual(
            trace["stage_requirements"][0]["missing_modules"], []
        )
        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["requires_agent_followup"])
        self.assertEqual(
            package["classification"]["cause_class"],
            "static_checker_inventory_inconsistency",
        )

    def test_inventory_capabilities_map_only_to_read_only_producers(self) -> None:
        capabilities = [
            {
                "capability_id": "planned_tool.operator_leaf_static_inventory_trace",
                "debug_layer": "operator_leaf_modules",
                "producer_scope": "operator_leaf_closure",
                "target_modules": ["residual_1"],
                "required_evidence": ["source hashes"],
                "rationale": "bind the generated RTL inventory",
            },
            {
                "capability_id": "planned_checker.operator_leaf_static_inventory_trace_check",
                "debug_layer": "operator_leaf_modules",
                "producer_scope": "operator_leaf_closure",
                "target_modules": ["residual_1"],
                "required_evidence": ["inventory classification"],
                "rationale": "classify the checker-visible inventory",
            },
        ]
        actions = required_capability_repair_actions(
            {
                "status": "blocked",
                "validation": {"status": "pass"},
                "required_capabilities": capabilities,
            }
        )

        self.assertEqual(
            [action["repair_kind"] for action in actions],
            [
                "operator_leaf_static_inventory_trace",
                "operator_leaf_static_inventory_trace_check",
            ],
        )
        self.assertTrue(all(action["approval_required"] is False for action in actions))
        self.assertTrue(all(action["read_only_generated_rtl_inventory"] for action in actions))


if __name__ == "__main__":
    unittest.main()
