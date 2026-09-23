import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from accagent.framework.stage_pipeline import PipelinePlanningError, build_pipeline_plan, normalize_attention_contract


ROOT = Path(__file__).resolve().parents[1]


def adapter_path(family: str) -> Path:
    return ROOT / "accagent" / "framework" / "case_adapters" / f"{family}_transformer_block.json"


def template_for_op(op: str) -> tuple[str, str]:
    if op == "self_attention":
        return "attention", "Attention.scala"
    if op.startswith("residual_add"):
        return "residual", "Residual.scala"
    if "norm" in op:
        return "norm", "Norm.scala"
    if op == "activation_mul":
        return "elementwise", "Elementwise.scala"
    if op == "activation":
        return "activation", "Activation.scala"
    return "ffn", "FFN.scala"


def model_spec(family: str) -> dict:
    if family == "gpt2":
        return {
            "operator_sequence": [
                "layer_norm_1",
                "self_attention",
                "residual_add_1",
                "layer_norm_2",
                "mlp_fc",
                "activation",
                "mlp_proj",
                "residual_add_2",
            ],
            "attention_kind": "mha",
            "num_layers": 12,
            "position_encoding": {"type": "learned_absolute"},
        }
    return {
        "operator_sequence": [
            "rms_norm_1",
            "self_attention",
            "residual_add_1",
            "rms_norm_2",
            "mlp_gate_proj",
            "mlp_up_proj",
            "activation_mul",
            "mlp_down_proj",
            "residual_add_2",
        ],
        "attention_kind": "gqa" if family == "llama" else "mqa",
        "num_layers": 24,
        "position_encoding": {"type": "rope"},
    }


def state_for(family: str, temp_dir: Path) -> dict:
    model = model_spec(family)
    selected = []
    bindings = []
    sources = set()
    for op in model["operator_sequence"]:
        template_id, source = template_for_op(op)
        sources.add(source)
        selected.append(
            {
                "role": "operator",
                "op": op,
                "template_id": template_id,
                "source": source,
                "required_params": ["lanes"],
                "constraints_emitted": [],
            }
        )
        bindings.append({"op": op, "bound_params": {"lanes": {"status": "bound", "value": 8}}})
    selection_path = temp_dir / "template_selection.json"
    selection_path.write_text(
        json.dumps({"selected_templates": selected, "parameter_bindings": bindings}), encoding="utf-8"
    )
    adapter = temp_dir / "case_adapter.json"
    adapter.write_text(
        json.dumps({"model_semantic_adapter": {"path": str(adapter_path(family))}}), encoding="utf-8"
    )
    model_config = temp_dir / "model_config.json"
    model_config.write_text(
        json.dumps(
            {
                "model_type": family,
                "mlp": {"type": "dense" if family == "gpt2" else "gated"},
                "norm": {"eps": 1.0e-5},
                "attention": {"causal": True},
            }
        ),
        encoding="utf-8",
    )
    return {
        "artifacts": [
            {"id": "artifact.stage2.template_selection", "path": str(selection_path)},
            {"id": "artifact.input.case_adapter", "path": str(adapter)},
            {"id": "artifact.input.model_config", "path": str(model_config)},
        ],
        "constraints": [
            {"id": "constraint.model.decoder", "facts": model},
            {
                "id": "constraint.shape.model",
                "facts": {
                    "target_max_seq_len": 16,
                    "hidden_size": 64,
                    "intermediate_size": 256,
                    "num_q_heads": 8,
                    "num_kv_heads": 8 if family == "gpt2" else (1 if family == "qwen2" else 2),
                    "head_dim": 8,
                },
            },
            {
                "id": "constraint.numeric.policy",
                "facts": {
                    "policy_id": "test-bf16",
                    "default_rules": {
                        "activation_dtype": "BF16",
                        "acc_dtype": "FP32",
                        "weight_dtype": "BF16",
                    },
                },
            },
            {
                "id": "constraint.arch.design_space",
                "facts": {
                    "search_params": {
                        "hardware_parameter_tuples": [
                            {
                                "lanes": 8,
                                "compute_array": {"rows": 4, "cols": 4},
                                "physical_fifo_depth_entries": 32,
                                "activation_bank_count": 2,
                            }
                        ]
                    }
                },
            },
            {
                "id": "constraint.memory.board",
                "facts": {
                    "memory_system": {
                        "axi_protocol": "AXI4",
                        "core_side_interface_name": "S00_AXI",
                        "axi_data_width_bits": 512,
                        "axi_data_bytes": 64,
                        "axi_addr_width_bits": 37,
                        "axi_id_width_bits": 4,
                        "axi_wstrb_width_bits": 64,
                        "ddr_channels": 1,
                    }
                },
            },
            {
                "id": "constraint.runtime.board",
                "facts": {"control_protocol": "xdma_raw_register_and_ddr", "xdma_id_default": 0},
            },
            {
                "id": "constraint.deployment.board",
                "facts": {"fpga_part": "xcvu9p-flga2104-2L-e", "deployment_mode": "app_shell"},
            },
            {
                "id": "constraint.cross_layer.input_consistency",
                "facts": {"model_shape_numeric_board_contract": "consistent"},
            },
            {
                "id": "constraint.template.library",
                "facts": {"source_files": sorted(sources), "policy": {"free_form_rtl_generation": False}},
            },
        ],
    }


class SemanticPipelinePlanTest(TestCase):
    def test_gpt2_uses_single_branch_dense_gelu_mlp_and_mha(self) -> None:
        with TemporaryDirectory() as temp:
            plan = build_pipeline_plan(state_for("gpt2", Path(temp)))

        self.assertEqual(plan["status"], "ready")
        self.assertEqual(plan["attention_contract"]["attention_kind"], "mha")
        self.assertEqual(
            plan["attention_contract"]["position_encoding_scope"]["placement"],
            "pre_dut_input_boundary",
        )
        self.assertEqual(
            plan["attention_contract"]["position_encoding_scope"]["dut_weight_binding"],
            "forbidden",
        )
        self.assertEqual([stage["op"] for stage in plan["stages"]][4:7], ["mlp_fc", "activation", "mlp_proj"])
        self.assertEqual(len(plan["data_edges"]), 11)
        joins = {row["node"] for row in plan["branch_join_contracts"]["join_contracts"]}
        self.assertEqual(joins, {"stage_02_residual_add_1", "stage_07_residual_add_2"})
        self.assertFalse(any("activation_mul" in edge["edge_id"] for edge in plan["data_edges"]))
        terms = {row["id"] for row in plan["memory_schedule"]["weight_storage_terms"]}
        self.assertIn("mlp_c_fc_weight", terms)
        self.assertIn("mlp_c_proj_weight", terms)

    def test_qwen2_uses_gated_mlp_and_mqa_when_declared(self) -> None:
        with TemporaryDirectory() as temp:
            plan = build_pipeline_plan(state_for("qwen2", Path(temp)))

        self.assertEqual(plan["status"], "ready")
        self.assertEqual(plan["attention_contract"]["attention_kind"], "mqa")
        self.assertEqual(
            plan["attention_contract"]["position_encoding_scope"]["placement"],
            "self_attention_qk_transform",
        )
        self.assertEqual(len(plan["data_edges"]), 13)
        joins = {row["node"] for row in plan["branch_join_contracts"]["join_contracts"]}
        self.assertEqual(
            joins,
            {"stage_02_residual_add_1", "stage_06_activation_mul", "stage_08_residual_add_2"},
        )
        self.assertEqual(plan["stages"][4]["output_shape"]["width"], 256)
        self.assertEqual(plan["stages"][7]["input_shape"]["width"], 256)

    def test_llama_uses_gated_mlp_and_gqa(self) -> None:
        with TemporaryDirectory() as temp:
            plan = build_pipeline_plan(state_for("llama", Path(temp)))

        self.assertEqual(plan["status"], "ready")
        self.assertEqual(plan["attention_contract"]["attention_kind"], "gqa")
        self.assertEqual(plan["checker_summary"]["failed"], 0)

    def test_missing_dataflow_contract_is_a_configuration_error(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            state = state_for("gpt2", root)
            bad_adapter = root / "bad_adapter.json"
            bad_adapter.write_text(json.dumps({"model_semantic_adapter": {"path": str(bad_adapter)}}), encoding="utf-8")
            state["artifacts"][1]["path"] = str(bad_adapter)
            with self.assertRaises(PipelinePlanningError):
                build_pipeline_plan(state)

    def test_missing_implementation_contract_is_a_configuration_error(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            state = state_for("gpt2", root)
            semantic = json.loads(adapter_path("gpt2").read_text(encoding="utf-8"))
            semantic.pop("implementation_contract")
            semantic_path = root / "semantic_without_implementation.json"
            semantic_path.write_text(json.dumps(semantic), encoding="utf-8")
            case_adapter_path = root / "case_adapter.json"
            case_adapter_path.write_text(
                json.dumps({"model_semantic_adapter": {"path": str(semantic_path)}}),
                encoding="utf-8",
            )
            state["artifacts"][1]["path"] = str(case_adapter_path)

            with self.assertRaisesRegex(PipelinePlanningError, "implementation_contract"):
                build_pipeline_plan(state)

    def test_legacy_attention_contract_gets_read_only_model_derived_position_scope(self) -> None:
        legacy = {
            "position_encoding": {"type": "learned_absolute"},
            "stage_boundary": "logical self_attention stage covers model-declared QKV projection, positional encoding, causal attention, and output projection",
        }

        normalized = normalize_attention_contract(legacy)

        self.assertNotIn("position_encoding_scope", legacy)
        self.assertEqual(normalized["position_encoding_scope"]["placement"], "pre_dut_input_boundary")
        self.assertEqual(normalized["position_encoding_scope"]["dut_weight_binding"], "forbidden")
        self.assertNotIn("positional encoding", normalized["stage_boundary"])
