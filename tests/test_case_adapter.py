from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from accagent.framework.case_adapter import adapter_tool, build_case_adapter
from accagent.framework.stage_input import prepare_tool_protocols


class BuiltinTransformerCaseAdapterTest(unittest.TestCase):
    def test_supported_families_bind_only_their_explicit_checkpoint_and_run_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            adapters = {}
            for family in ("gpt2", "qwen2", "llama"):
                model_dir = root / family / "checkpoint"
                model_dir.mkdir(parents=True)
                run_dir = root / family / "run"
                adapter = build_case_adapter(
                    {
                        "model_type": family,
                        "model_id": f"test-{family}",
                        "model_dir": str(model_dir),
                    },
                    run_dir,
                    root / "tool_materials",
                )
                adapters[family] = adapter

                self.assertEqual(adapter["status"], "ready")
                self.assertEqual(adapter["model_family"], family)
                self.assertEqual(
                    adapter["model_semantic_adapter"]["checkpoint"]["model_dir"],
                    str(model_dir),
                )
                self.assertTrue(
                    adapter["model_semantic_adapter"]["path"].endswith(
                        f"{family}_transformer_block.json"
                    )
                )
                self.assertEqual(
                    adapter["paths"]["hierarchy_dir"],
                    str(run_dir / "verification" / "case_hierarchy"),
                )
                self.assertTrue(
                    all("qwen_real_weights" not in str(value) for value in adapter["paths"].values())
                )
                self.assertTrue(
                    all("qwen_hierarchy" not in str(value) for value in adapter["paths"].values())
                )
                self.assertTrue(
                    all(
                        "legacy_name" not in spec
                        for spec in adapter["tools"].values()
                        if isinstance(spec, dict)
                    )
                )
                weight_tool = adapter_tool(adapter, "weight_manifest_generate")
                self.assertIsNotNone(weight_tool)
                self.assertEqual(
                    weight_tool["argv"][weight_tool["argv"].index("--model-dir") + 1],
                    str(model_dir),
                )
                self.assertIn(
                    str(run_dir / "verification" / "model_weights" / "checkpoint_inventory.json"),
                    weight_tool["produces"],
                )

            self.assertNotEqual(
                adapters["gpt2"]["model_semantic_adapter"]["checkpoint"]["model_dir"],
                adapters["qwen2"]["model_semantic_adapter"]["checkpoint"]["model_dir"],
            )
            self.assertNotEqual(
                adapters["qwen2"]["model_semantic_adapter"]["checkpoint"]["model_dir"],
                adapters["llama"]["model_semantic_adapter"]["checkpoint"]["model_dir"],
            )

    def test_explicit_checkpoint_is_required_for_a_ready_builtin_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            adapter = build_case_adapter(
                {"model_type": "gpt2", "model_id": "test-gpt2"},
                root / "run",
                root / "tool_materials",
            )

        self.assertEqual(adapter["status"], "incomplete")
        self.assertTrue(any("checkpoint directory" in error for error in adapter["errors"]))

    def test_stage0_codegen_protocol_uses_only_model_independent_top_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "gpt2_run"
            input_dir = run_dir / "input"
            input_dir.mkdir(parents=True)
            checkpoint = root / "gpt2_checkpoint"
            checkpoint.mkdir()
            adapter = build_case_adapter(
                {
                    "model_type": "gpt2",
                    "model_id": "test-gpt2",
                    "model_dir": str(checkpoint),
                },
                run_dir,
                root / "tool_materials",
            )
            protocols = prepare_tool_protocols(
                {"runtime_interface": {}},
                {"tools": []},
                "",
                root / "tool_materials",
                input_dir,
                adapter,
            )

        tools = {item["name"]: item for item in protocols["tools"]}
        for name in ("chisel_generate", "chisel_compile"):
            item = tools[name]
            material = "\n".join(
                [
                    *map(str, item["execution"]["argv"]),
                    *map(str, item.get("consumes", [])),
                    *map(str, item.get("produces", [])),
                ]
            )
            self.assertIn("GeneratedAcceleratorTop.sv", material)
            self.assertIn("GeneratedAxiDdrTop.sv", material)
            self.assertNotIn("LlamaStyleBlock.sv", material)

    def test_unconfigured_legacy_liveness_tools_are_not_stage0_requirements(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "run"
            input_dir = run_dir / "input"
            input_dir.mkdir(parents=True)
            checkpoint = root / "checkpoint"
            checkpoint.mkdir()
            adapter = build_case_adapter(
                {"model_type": "gpt2", "model_id": "test-gpt2", "model_dir": str(checkpoint)},
                run_dir,
                root / "tool_materials",
            )
            protocols = prepare_tool_protocols(
                {"runtime_interface": {}},
                {"tools": []},
                "",
                root / "tool_materials",
                input_dir,
                adapter,
            )

        tools = {item["name"]: item for item in protocols["tools"]}
        self.assertFalse(tools["case_verilator_liveness"]["required"])
        self.assertFalse(tools["case_vcs_liveness"]["required"])


if __name__ == "__main__":
    unittest.main()
