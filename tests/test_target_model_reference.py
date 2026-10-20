import unittest

from scripts.verification.target_model_reference import semantic_capture_plan


class TargetModelReferenceTest(unittest.TestCase):
    def test_capture_plan_uses_adapter_aliases_for_logical_stage_records(self) -> None:
        plan = semantic_capture_plan(
            {
                "reference_capture_modules": {
                    "input_layernorm": "ln_1",
                    "post_attention_layernorm": "ln_2",
                },
                "semantic_stages": {
                    "layer_norm_1": {
                        "expected": {"record": "input_layernorm", "value": "output"}
                    },
                    "residual_add_1": {
                        "inputs": [{"record": "input_layernorm", "value": "output"}],
                        "expected": {
                            "record": "post_attention_layernorm",
                            "value": "input",
                        },
                    },
                },
            }
        )

        self.assertEqual(plan["input_layernorm"], {"module_path": "ln_1", "values": {"output"}})
        self.assertEqual(
            plan["post_attention_layernorm"],
            {"module_path": "ln_2", "values": {"input"}},
        )

    def test_capture_plan_defaults_to_the_logical_module_path(self) -> None:
        plan = semantic_capture_plan(
            {
                "semantic_stages": {
                    "attention": {
                        "expected": {"record": "self_attn", "value": "output"}
                    }
                }
            }
        )

        self.assertEqual(plan["self_attn"], {"module_path": "self_attn", "values": {"output"}})

    def test_capture_plan_derives_legacy_adapter_aliases_from_weight_suffixes(self) -> None:
        plan = semantic_capture_plan(
            {
                "semantic_stages": {
                    "layer_norm_1": {
                        "expected": {"record": "input_layernorm", "value": "output"},
                        "required_weight_suffixes": ["ln_1.weight", "ln_1.bias"],
                    },
                    "self_attention": {
                        "expected": {"record": "attn", "value": "output"},
                        "required_weight_suffixes": [
                            "attn.c_attn.weight",
                            "attn.c_proj.weight",
                        ],
                    },
                }
            }
        )

        self.assertEqual(plan["input_layernorm"]["module_path"], "ln_1")
        self.assertEqual(plan["attn"]["module_path"], "attn")

    def test_capture_plan_rejects_invalid_selector(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid capture selector"):
            semantic_capture_plan(
                {
                    "semantic_stages": {
                        "attention": {
                            "expected": {"record": "self_attn", "value": "activation"}
                        }
                    }
                }
            )


if __name__ == "__main__":
    unittest.main()
