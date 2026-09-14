import hashlib
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

import torch

from accagent.framework.weight_layout import (
    build_stage_weight_layout,
    materialize_composite_weight_stream,
    materialize_stage_weight_stream,
    sha256_json,
)


NUMERIC_POLICY = {
    "policy_id": "test",
    "default_rules": {
        "weight_dtype": "fp16",
        "activation_dtype": "fp16",
        "acc_dtype": "fp32",
        "rounding": "nearest_even",
        "saturation": False,
    },
}


def stage(stage_id: str, op: str, **params: int) -> dict:
    return {
        "stage_id": stage_id,
        "op": op,
        "template_id": "attention" if op == "self_attention" else "linear",
        "bound_params": {
            name: {"status": "bound", "value": value}
            for name, value in params.items()
        },
        "numeric_contract": {
            "weight_bits": 16,
            "accumulator_bits": 32,
        },
    }


def binding(suffix: str, shape: list[int], path: Path | None = None) -> dict:
    row = {
        "tensor": f"model.layers.0.{suffix}",
        "parameter_suffix": suffix,
        "shape": shape,
        "sha256": hashlib.sha256(suffix.encode("ascii")).hexdigest(),
        "source_dtype": "BF16",
    }
    if path is not None:
        row.update(
            {
                "path": str(path),
                "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    return row


class WeightLayoutTest(TestCase):
    def test_attention_contract_fuses_qkv_and_keeps_output_projection_separate(self) -> None:
        rows = [
            binding("self_attn.q_proj.weight", [4, 4]),
            binding("self_attn.q_proj.bias", [4]),
            binding("self_attn.k_proj.weight", [2, 4]),
            binding("self_attn.k_proj.bias", [2]),
            binding("self_attn.v_proj.weight", [2, 4]),
            binding("self_attn.v_proj.bias", [2]),
            binding("self_attn.o_proj.weight", [4, 4]),
        ]

        contract = build_stage_weight_layout(
            stage("attention", "self_attention", lanes=2, head_dim=2),
            {},
            rows,
            NUMERIC_POLICY,
        )

        targets = contract["storage_targets"]
        self.assertEqual(
            [row["target_id"] for row in targets],
            ["attention.qkv.weight", "attention.qkv.bias", "attention.out_proj.weight"],
        )
        self.assertEqual(targets[0]["logical_shape"], [8, 4])
        self.assertEqual(
            targets[0]["compose"]["source_order"],
            [
                "self_attn.q_proj.weight",
                "self_attn.k_proj.weight",
                "self_attn.v_proj.weight",
            ],
        )
        self.assertEqual(targets[0]["stream_range"], {"word_offset": 0, "word_count": 16, "word_end_exclusive": 16})
        self.assertEqual(targets[1]["stream_range"]["word_offset"], 16)
        self.assertEqual(targets[1]["storage_scalar_dtype"], "fp32")
        self.assertEqual(targets[2]["port"]["data_width_bits"], 64)
        self.assertEqual(contract["stream_word_count"], 32)

    def test_linear_stream_is_port_tile_major_and_lsb_first(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            tensor_path = root / "weight.pt"
            tensor = torch.tensor([[1.0, 2.0, 3.0, 4.0], [5.0, 6.0, 7.0, 8.0]])
            torch.save(tensor, tensor_path)
            row = binding("mlp.gate_proj.weight", [2, 4], tensor_path)
            contract = build_stage_weight_layout(
                stage("gate", "mlp_gate_proj", lanes=2),
                {},
                [row],
                NUMERIC_POLICY,
            )

            stream = materialize_stage_weight_stream(root / "weight.memh", contract, [row])
            actual = [int(line, 16) for line in Path(stream["path"]).read_text().splitlines()]
            ordered = torch.tensor([1.0, 2.0, 5.0, 6.0, 3.0, 4.0, 7.0, 8.0]).half()
            bits = [int(value) & 0xFFFF for value in ordered.view(torch.int16).tolist()]
            expected = [bits[index] | (bits[index + 1] << 16) for index in range(0, len(bits), 2)]

            self.assertEqual(actual, expected)
            self.assertEqual(stream["word_count"], 4)
            self.assertEqual(stream["layout_contract_sha256"], contract["contract_sha256"])

    def test_norm_stream_rounds_to_fp16_then_casts_to_fp32(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            tensor_path = root / "norm.pt"
            tensor = torch.tensor([0.1, 0.2, 0.3, 0.4], dtype=torch.float32)
            torch.save(tensor, tensor_path)
            row = binding("input_layernorm.weight", [4], tensor_path)
            contract = build_stage_weight_layout(
                stage("norm", "rms_norm_1", lanes=2, input_bits=32),
                {},
                [row],
                NUMERIC_POLICY,
            )

            target = contract["storage_targets"][0]
            stream = materialize_stage_weight_stream(root / "norm.memh", contract, [row])
            actual = [int(line, 16) for line in Path(stream["path"]).read_text().splitlines()]
            expected = [int(value) & 0xFFFFFFFF for value in tensor.half().float().view(torch.int32).tolist()]

            self.assertEqual(target["port"]["data_width_bits"], 64)
            self.assertEqual(target["value_conversion"]["kind"], "ieee754_value_preserving_cast")
            self.assertEqual(actual, expected)

    def test_unknown_weighted_op_requires_explicit_adapter_layout(self) -> None:
        with self.assertRaisesRegex(ValueError, "no explicit adapter weight_layout"):
            build_stage_weight_layout(
                stage("custom", "custom_weighted_op", lanes=2),
                {},
                [binding("custom.weight", [2, 2])],
                NUMERIC_POLICY,
            )

    def test_composite_stream_preserves_stage_order_and_translates_ranges(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            linear_path = root / "linear.pt"
            norm_path = root / "norm.pt"
            torch.save(torch.tensor([[1.0, 2.0, 3.0, 4.0], [5.0, 6.0, 7.0, 8.0]]), linear_path)
            torch.save(torch.tensor([0.25, 0.5, 0.75, 1.0]), norm_path)

            linear_binding = binding("mlp.gate_proj.weight", [2, 4], linear_path)
            linear_layout = build_stage_weight_layout(
                stage("linear", "mlp_gate_proj", lanes=2), {}, [linear_binding], NUMERIC_POLICY
            )
            linear_stream = materialize_stage_weight_stream(
                root / "linear.memh", linear_layout, [linear_binding]
            )
            empty_layout = build_stage_weight_layout(
                stage("empty", "residual_add", lanes=2), {}, [], NUMERIC_POLICY
            )
            empty_stream = materialize_stage_weight_stream(root / "empty.memh", empty_layout, [])
            norm_binding = binding("input_layernorm.weight", [4], norm_path)
            norm_layout = build_stage_weight_layout(
                stage("norm", "rms_norm_1", lanes=2, input_bits=32), {}, [norm_binding], NUMERIC_POLICY
            )
            norm_stream = materialize_stage_weight_stream(root / "norm.memh", norm_layout, [norm_binding])

            descriptors = [
                {"stage_id": "linear", "op": "mlp_gate_proj", "layout": linear_layout, "stream": linear_stream},
                {"stage_id": "empty", "op": "residual_add", "layout": empty_layout, "stream": empty_stream},
                {"stage_id": "norm", "op": "rms_norm_1", "layout": norm_layout, "stream": norm_stream},
            ]
            composite = materialize_composite_weight_stream(root / "composite.memh", descriptors)

            self.assertEqual(composite["stage_order"], ["linear", "empty", "norm"])
            self.assertEqual(composite["word_count"], 8)
            self.assertEqual(
                Path(composite["path"]).read_bytes(),
                Path(linear_stream["path"]).read_bytes() + Path(norm_stream["path"]).read_bytes(),
            )
            segments = composite["stage_segments"]
            self.assertEqual(
                [row["global_stream_range"] for row in segments],
                [
                    {"word_offset": 0, "word_count": 4, "word_end_exclusive": 4},
                    {"word_offset": 4, "word_count": 0, "word_end_exclusive": 4},
                    {"word_offset": 4, "word_count": 4, "word_end_exclusive": 8},
                ],
            )
            self.assertEqual(
                segments[2]["targets"][0]["local_stream_range"],
                {"word_offset": 0, "word_count": 4, "word_end_exclusive": 4},
            )
            self.assertEqual(
                segments[2]["targets"][0]["global_stream_range"],
                {"word_offset": 4, "word_count": 4, "word_end_exclusive": 8},
            )
            self.assertEqual(segments[0]["layout_contract_sha256"], linear_layout["contract_sha256"])
            self.assertEqual(segments[0]["local_stream_sha256"], linear_stream["sha256"])
            contract_payload = {
                key: value for key, value in composite.items() if key not in {"contract_sha256", "path"}
            }
            self.assertEqual(composite["contract_sha256"], sha256_json(contract_payload))

            reordered = materialize_composite_weight_stream(
                root / "reordered.memh", [descriptors[2], descriptors[1], descriptors[0]]
            )
            self.assertNotEqual(reordered["sha256"], composite["sha256"])
            self.assertNotEqual(reordered["contract_sha256"], composite["contract_sha256"])

    def test_composite_stream_rejects_count_mismatch_and_tampered_source(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            tensor_path = root / "weight.pt"
            torch.save(torch.tensor([[1.0, 2.0], [3.0, 4.0]]), tensor_path)
            row = binding("mlp.gate_proj.weight", [2, 2], tensor_path)
            layout = build_stage_weight_layout(
                stage("linear", "mlp_gate_proj", lanes=2), {}, [row], NUMERIC_POLICY
            )
            stream = materialize_stage_weight_stream(root / "local.memh", layout, [row])
            descriptor = {"stage_id": "linear", "op": "mlp_gate_proj", "layout": layout, "stream": stream}

            wrong_count = deepcopy(descriptor)
            wrong_count["stream"]["word_count"] += 1
            with self.assertRaisesRegex(ValueError, "word_count does not match"):
                materialize_composite_weight_stream(root / "wrong-count.memh", [wrong_count])

            Path(stream["path"]).write_text("00000000\n", encoding="ascii")
            with self.assertRaisesRegex(ValueError, "file/hash mismatch"):
                materialize_composite_weight_stream(root / "tampered.memh", [descriptor])
            self.assertFalse((root / "tampered.memh").exists())
