import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from accagent.framework.stage_templates import (
    build_selection,
    implementation_contract_for_state,
    template_source_checks,
)
from tests.test_stage_pipeline import ROOT, adapter_path, state_for


TEMPLATES = ROOT / "accagent" / "framework" / "templates" / "operator_chisel"


def wrapper_check(family: str, root: Path) -> tuple[dict, dict]:
    root.mkdir(parents=True, exist_ok=True)
    state = state_for(family, root)
    contract = implementation_contract_for_state(state)
    checks, errors = template_source_checks(
        [
            {
                "role": "block_wrapper",
                "op": "decoder_block",
                "template_id": "decoder_block",
                "source": "DecoderBlock.scala",
                "required_params": [],
            }
        ],
        {"template_dir": str(TEMPLATES)},
        {"default_rules": {"activation_dtype": "BF16"}},
        contract,
    )
    if errors:
        raise AssertionError(errors)
    return contract, checks[0]


def stage2_selection(family: str, root: Path) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    state = state_for(family, root)
    metadata = json.loads((TEMPLATES / "template_metadata.json").read_text(encoding="utf-8"))
    template = next(
        item for item in state["constraints"] if item["id"] == "constraint.template.library"
    )["facts"]
    template.update(
        {
            "template_dir": str(TEMPLATES),
            "source_files": sorted(path.name for path in TEMPLATES.glob("*.scala")),
            "templates": metadata["templates"],
        }
    )
    return build_selection(state)


class SemanticTemplateBindingTest(TestCase):
    def test_gpt2_wrapper_uses_decoder_block_params_without_rope_or_gqa_requirements(self) -> None:
        with TemporaryDirectory() as temp:
            contract, check = wrapper_check("gpt2", Path(temp))
            selection = stage2_selection("gpt2", Path(temp) / "stage2")

        self.assertEqual(contract["params"]["class"], "DecoderBlockParams")
        self.assertEqual(check["case_class"], "DecoderBlockParams")
        self.assertEqual(check["constructor_requirement_source"], "implementation_contract")
        self.assertNotIn("kvHeads", check["constructor_binding_names"])
        self.assertNotIn("ropeTheta", check["constructor_binding_names"])
        self.assertEqual(check["status"], "pass")
        wrapper = next(item for item in selection["selected_templates"] if item["role"] == "block_wrapper")
        self.assertNotIn("num_kv_heads", wrapper["required_params"])
        self.assertNotIn("rope_theta", wrapper["required_params"])
        self.assertEqual(selection["implementation_contract"]["params"]["class"], "DecoderBlockParams")
        self.assertEqual(
            selection["implementation_contract"]["params"]["bindings"]["batchSize"],
            "token_count",
        )
        self.assertEqual(selection["status"], "ready")
        self.assertTrue(
            all(
                binding["bound_params"]["lanes"]["status"] == "candidate_bound"
                for binding in selection["parameter_bindings"]
                if "lanes" in binding["bound_params"]
            )
        )

    def test_qwen2_and_llama_wrappers_use_llama_style_params(self) -> None:
        with TemporaryDirectory() as temp:
            qwen_contract, qwen_check = wrapper_check("qwen2", Path(temp) / "qwen")
            llama_contract, llama_check = wrapper_check("llama", Path(temp) / "llama")
            qwen_selection = stage2_selection("qwen2", Path(temp) / "qwen_stage2")
            llama_selection = stage2_selection("llama", Path(temp) / "llama_stage2")

        self.assertEqual(qwen_contract["params"]["class"], "LlamaStyleBlockParams")
        self.assertEqual(llama_contract["params"]["class"], "LlamaStyleBlockParams")
        self.assertEqual(qwen_check["case_class"], "LlamaStyleBlockParams")
        self.assertEqual(llama_check["case_class"], "LlamaStyleBlockParams")
        self.assertIn("kvHeads", qwen_check["constructor_binding_names"])
        self.assertIn("kvHeads", llama_check["constructor_binding_names"])
        qwen_wrapper = next(item for item in qwen_selection["selected_templates"] if item["role"] == "block_wrapper")
        llama_wrapper = next(item for item in llama_selection["selected_templates"] if item["role"] == "block_wrapper")
        self.assertIn("num_kv_heads", qwen_wrapper["required_params"])
        self.assertIn("num_kv_heads", llama_wrapper["required_params"])
        self.assertIn("token_count", qwen_wrapper["required_params"])
        self.assertNotIn("batch_size", qwen_wrapper["required_params"])
        self.assertEqual(qwen_selection["status"], "ready")
        self.assertEqual(llama_selection["status"], "ready")

    def test_wrapper_parameter_class_comes_from_adapter_not_model_family(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            state = state_for("llama", root)
            model = next(
                item for item in state["constraints"] if item["id"] == "constraint.model.decoder"
            )["facts"]
            model["model_type"] = "arbitrary_future_decoder"

            semantic = json.loads(adapter_path("gpt2").read_text(encoding="utf-8"))
            semantic_path = root / "custom_semantic_adapter.json"
            semantic_path.write_text(json.dumps(semantic), encoding="utf-8")
            case_adapter_path = root / "case_adapter.json"
            case_adapter_path.write_text(
                json.dumps({"model_semantic_adapter": {"path": str(semantic_path)}}),
                encoding="utf-8",
            )
            state["artifacts"][1]["path"] = str(case_adapter_path)
            contract = implementation_contract_for_state(state)

        self.assertEqual(contract["top_class"], "GPT2PreLNBlock")
        self.assertEqual(contract["params"]["class"], "DecoderBlockParams")
