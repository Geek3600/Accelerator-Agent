import json
import struct
from argparse import Namespace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from scripts.verification.target_model_weight_catalog import (
    CatalogError,
    bind_transformer_scope,
    generate,
    validate_layer_coverage,
)
from scripts.verification.semantic_testbench_generator import required_weights, stage_tensors


def tensor(name: str) -> dict[str, object]:
    return {"name": name, "dtype": "F16", "shape": [2, 2], "data_offsets": [0, 8]}


def write_safetensors(path: Path, tensors: list[str]) -> None:
    header = {}
    payload = bytearray()
    for index, name in enumerate(tensors):
        start = len(payload)
        payload.extend(bytes([index + 1]) * 8)
        header[name] = {"dtype": "F16", "shape": [2, 2], "data_offsets": [start, len(payload)]}
    encoded = json.dumps(header, separators=(",", ":")).encode("utf-8")
    path.write_bytes(struct.pack("<Q", len(encoded)) + encoded + payload)


class TransformerBlockWeightScopeTest(TestCase):
    def test_complete_scope_excludes_non_block_model_regions(self) -> None:
        tensors = [
            tensor("model.embed_tokens.weight"),
            tensor("model.layers.0.attn.weight"),
            tensor("model.layers.0.mlp.weight"),
            tensor("model.layers.1.attn.weight"),
            tensor("model.layers.1.mlp.weight"),
            tensor("model.norm.weight"),
        ]

        selected, excluded, pattern = bind_transformer_scope(
            tensors,
            [r"^model\.layers\.(?P<layer>\d+)\.(?P<suffix>.+)$"],
            num_layers=2,
        )
        layer_ids, suffixes = validate_layer_coverage(selected, num_layers=2)

        self.assertEqual(pattern, r"^model\.layers\.(?P<layer>\d+)\.(?P<suffix>.+)$")
        self.assertEqual(layer_ids, [0, 1])
        self.assertEqual(suffixes, ["attn.weight", "mlp.weight"])
        self.assertEqual(len(selected), 4)
        self.assertEqual(excluded, ["model.embed_tokens.weight", "model.norm.weight"])

    def test_missing_layer_or_weight_suffix_is_incomplete(self) -> None:
        tensors = [
            tensor("model.layers.0.attn.weight"),
            tensor("model.layers.0.mlp.weight"),
            tensor("model.layers.1.attn.weight"),
        ]

        selected, _, _ = bind_transformer_scope(
            tensors,
            [r"^model\.layers\.(?P<layer>\d+)\.(?P<suffix>.+)$"],
            num_layers=2,
        )

        with self.assertRaises(CatalogError):
            validate_layer_coverage(selected, num_layers=2)

    def test_adapter_regex_supports_non_qwen_decoder_prefix(self) -> None:
        tensors = [
            tensor("model.decoder.embed_tokens.weight"),
            tensor("model.decoder.layers.0.self_attn.q_proj.weight"),
            tensor("model.decoder.layers.1.self_attn.q_proj.weight"),
            tensor("model.decoder.final_layer_norm.weight"),
        ]

        selected, excluded, _ = bind_transformer_scope(
            tensors,
            [r"^model\.decoder\.layers\.(?P<layer>\d+)\.(?P<suffix>.+)$"],
            num_layers=2,
        )
        layer_ids, suffixes = validate_layer_coverage(selected, num_layers=2)

        self.assertEqual(layer_ids, [0, 1])
        self.assertEqual(suffixes, ["self_attn.q_proj.weight"])
        self.assertEqual(
            excluded,
            ["model.decoder.embed_tokens.weight", "model.decoder.final_layer_norm.weight"],
        )

    def test_generic_catalog_supports_sharded_safetensors(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            snapshot = root / "snapshot"
            run_dir = root / "run"
            snapshot.mkdir()
            (run_dir / "input").mkdir(parents=True)
            (snapshot / "config.json").write_text(
                json.dumps({"model_type": "synthetic", "num_hidden_layers": 2, "hidden_size": 4}),
                encoding="utf-8",
            )
            write_safetensors(
                snapshot / "model-00001-of-00002.safetensors",
                ["model.decoder.embed_tokens.weight", "model.decoder.layers.0.attn.weight"],
            )
            write_safetensors(
                snapshot / "model-00002-of-00002.safetensors",
                ["model.decoder.layers.1.attn.weight", "model.decoder.final_layer_norm.weight"],
            )
            (snapshot / "model.safetensors.index.json").write_text(
                json.dumps(
                    {
                        "weight_map": {
                            "model.decoder.embed_tokens.weight": "model-00001-of-00002.safetensors",
                            "model.decoder.layers.0.attn.weight": "model-00001-of-00002.safetensors",
                            "model.decoder.layers.1.attn.weight": "model-00002-of-00002.safetensors",
                            "model.decoder.final_layer_norm.weight": "model-00002-of-00002.safetensors",
                        }
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "input" / "model_config.json").write_text(
                json.dumps({"model_type": "synthetic", "num_layers": 2}),
                encoding="utf-8",
            )
            adapter_path = root / "semantic_adapter.json"
            adapter_path.write_text(
                json.dumps(
                    {
                        "accelerator_scope": "transformer_blocks_only",
                        "decoder_layer_tensor_patterns": [
                            r"^model\.decoder\.layers\.(?P<layer>\d+)\.(?P<suffix>.+)$"
                        ],
                        "semantic_stages": {"synthetic_op": {}},
                    }
                ),
                encoding="utf-8",
            )

            outputs = generate(
                Namespace(
                    run_dir=run_dir,
                    out_dir=None,
                    model_id="synthetic/model",
                    model_dir=snapshot,
                    semantic_adapter=adapter_path,
                )
            )
            catalog = json.loads(Path(outputs["accelerator_catalog"]).read_text(encoding="utf-8"))

            self.assertEqual(catalog["tensor_count"], 2)
            self.assertEqual(catalog["layer_ids"], [0, 1])
            self.assertTrue(catalog["scope_coverage_complete"])
            self.assertTrue(all(row["source_slice_sha256"] for row in catalog["tensors"]))
            self.assertEqual(len(json.loads(Path(outputs["manifest"]).read_text())["checkpoint_files"]), 2)

    def test_semantic_tensor_selection_is_adapter_driven(self) -> None:
        stage_map = {
            "synthetic_norm": {
                "inputs": [{"source": "accelerator_input"}],
                "expected": {"record": "decoder.norm", "value": "output"},
                "required_weight_suffixes": ["decoder.norm.weight"],
            },
            "synthetic_add": {
                "inputs": [
                    {"record": "decoder.norm", "value": "output"},
                    {"record": "decoder.branch", "value": "output"},
                ],
                "expected": {"record": "decoder.add", "value": "output"},
                "required_weight_suffixes": [],
            },
        }
        records = {
            "decoder.norm": {"output": "norm-output"},
            "decoder.branch": {"output": "branch-output"},
            "decoder.add": {"output": "add-output"},
        }

        inputs, expected = stage_tensors("synthetic_add", "block-input", records, stage_map)

        self.assertEqual(inputs, ["norm-output", "branch-output"])
        self.assertEqual(expected, "add-output")
        self.assertEqual(required_weights("synthetic_norm", stage_map), ["decoder.norm.weight"])
