import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from accagent.framework.stage_artifacts import build_memory_layout, generate_chisel_package, sbt_failure_markers
from accagent.framework.stage_params import build_parameter_bindings
from accagent.framework.stage_pipeline import build_pipeline_plan
from tests.test_stage_pipeline import ROOT, state_for


TEMPLATES = ROOT / "accagent" / "framework" / "templates" / "operator_chisel"


def prepared_state(family: str, root: Path) -> tuple[dict, dict]:
    root.mkdir(parents=True, exist_ok=True)
    state = state_for(family, root)
    model = next(item for item in state["constraints"] if item["id"] == "constraint.model.decoder")["facts"]
    model["model_type"] = {"gpt2": "gpt2", "qwen2": "qwen2", "llama": "llama"}[family]
    template = next(item for item in state["constraints"] if item["id"] == "constraint.template.library")["facts"]
    template["template_dir"] = str(TEMPLATES)
    template["source_files"] = sorted(path.name for path in TEMPLATES.glob("*.scala"))
    state["constraints"].append({"id": "constraint.deployment.board", "facts": {"board": {"fpga_part": "xcvu9p-flga2104-2L-e"}}})
    plan = build_pipeline_plan(state)
    plan_path = root / "pipeline_plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    state["artifacts"].append({"id": "artifact.stage3.pipeline_plan", "path": str(plan_path)})
    bindings = build_parameter_bindings(state)
    binding_path = root / "parameter_binding.json"
    binding_path.write_text(json.dumps(bindings), encoding="utf-8")
    state["artifacts"].append({"id": "artifact.stage4.parameter_binding", "path": str(binding_path)})
    return state, bindings


class SemanticCodeGenerationTest(TestCase):
    def test_sbt_background_exception_is_a_compile_gate_failure(self) -> None:
        self.assertIn("ExceptionInInitializerError", sbt_failure_markers("ExceptionInInitializerError", ""))
        self.assertFalse(sbt_failure_markers("[info] done compiling", ""))

    def test_generated_loader_ports_follow_model_semantics(self) -> None:
        with TemporaryDirectory() as temp:
            generated = {}
            for family in ("gpt2", "qwen2", "llama"):
                state, _ = prepared_state(family, Path(temp) / family)
                generated[family] = generate_chisel_package(
                    Path(temp) / family,
                    state,
                    {"schema_version": "test", "generation_policy": "test"},
                )
            texts = {
                family: (
                    Path(package["root"])
                    / "src/main/scala/spatialaccagent/generated/GeneratedAxiDdrTop.scala"
                ).read_text(encoding="utf-8")
                for family, package in generated.items()
            }

        self.assertEqual(generated["gpt2"]["top_class"], "GPT2PreLNBlock")
        self.assertIn("val attentionOutBias", texts["gpt2"])
        self.assertEqual(generated["qwen2"]["top_class"], "Qwen2Block")
        self.assertIn("val qkvBias", texts["qwen2"])
        self.assertEqual(generated["llama"]["top_class"], "LlamaStyleBlock")
        self.assertNotIn("val qkvBias", texts["llama"])
        self.assertIn("core.io.qkvBias.valid := false.B", texts["llama"])

    def test_codegen_uses_stage3_implementation_contract_not_model_name(self) -> None:
        with TemporaryDirectory() as temp:
            state, _ = prepared_state("qwen2", Path(temp))
            model = next(item for item in state["constraints"] if item["id"] == "constraint.model.decoder")["facts"]
            model["model_type"] = "arbitrary_future_decoder"
            package = generate_chisel_package(
                Path(temp), state, {"schema_version": "test", "generation_policy": "test"}
            )
            axi_top = (
                Path(package["root"])
                / "src/main/scala/spatialaccagent/generated/GeneratedAxiDdrTop.scala"
            ).read_text(encoding="utf-8")
            accelerator_top = (
                Path(package["root"])
                / "src/main/scala/spatialaccagent/generated/GeneratedAcceleratorTop.scala"
            ).read_text(encoding="utf-8")

        self.assertEqual(package["top_class"], "Qwen2Block")
        self.assertEqual(package["param_class"], "LlamaStyleBlockParams")
        self.assertIn("private val core = Module(new Qwen2Block(p))", accelerator_top)
        self.assertIn("val qkvBias", axi_top)

    def test_memory_layout_uses_stage3_semantic_region_sizes(self) -> None:
        with TemporaryDirectory() as temp:
            state, bindings = prepared_state("gpt2", Path(temp))
            package = generate_chisel_package(Path(temp), state, {"schema_version": "test", "generation_policy": "test"})
            layout = build_memory_layout(state, bindings, package)
            plan = json.loads(Path(next(item["path"] for item in state["artifacts"] if item["id"] == "artifact.stage3.pipeline_plan")).read_text(encoding="utf-8"))

        expected = {
            row["name"]: row["size_bytes"]
            for row in plan["memory_schedule"]["required_regions"]
        }
        actual = {row["name"]: row["meta"].get("stage3_size_bytes") for row in layout["regions"]}
        for name in ["input_tokens", "output_tokens", "activation_ping", "activation_pong", "weight_buffer_a", "weight_buffer_b"]:
            self.assertEqual(actual[name], expected[name])
        self.assertTrue(layout["weight_storage_terms"])
