import hashlib
import json
import struct
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

import torch

from accagent.framework.board_weight_image import (
    BoardWeightImageError,
    PLAN_SCHEMA_VERSION,
    materialize_board_weight_image,
)
from accagent.framework.weight_layout import (
    build_stage_weight_layout,
    materialize_composite_weight_stream,
    materialize_stage_weight_stream,
    sha256_file,
    sha256_json,
)
from scripts.verification.target_model_weight_catalog import (
    bind_transformer_scope,
    hash_tensor_slices,
    parse_safetensors,
    validate_layer_coverage,
)


NUMERIC_POLICY = {
    "policy_id": "synthetic-mixed-checkpoint",
    "default_rules": {
        "weight_dtype": "fp16",
        "acc_dtype": "fp32",
        "rounding": "nearest_even",
        "saturation": False,
    },
}


def stage(stage_id: str, op: str) -> dict[str, object]:
    return {
        "stage_id": stage_id,
        "op": op,
        "template_id": "synthetic",
        "bound_params": {
            "lanes": {"value": 2},
            "input_bits": {"value": 32},
            "head_dim": {"value": 2},
        },
        "numeric_contract": {},
    }


def tensor_raw(value: torch.Tensor, dtype: str) -> bytes:
    if dtype == "BF16":
        return value.to(torch.bfloat16).contiguous().view(torch.int16).numpy().astype("<i2", copy=False).tobytes()
    if dtype == "F16":
        return value.to(torch.float16).contiguous().view(torch.int16).numpy().astype("<i2", copy=False).tobytes()
    if dtype == "F32":
        return value.to(torch.float32).contiguous().view(torch.int32).numpy().astype("<i4", copy=False).tobytes()
    raise ValueError(dtype)


def write_safetensors(path: Path, tensors: list[tuple[str, str, torch.Tensor]]) -> None:
    header = {}
    payload = bytearray()
    for name, dtype, value in tensors:
        raw = tensor_raw(value, dtype)
        start = len(payload)
        payload.extend(raw)
        header[name] = {
            "dtype": dtype,
            "shape": list(value.shape),
            "data_offsets": [start, len(payload)],
        }
    encoded = json.dumps(header, sort_keys=True, separators=(",", ":")).encode("utf-8")
    path.write_bytes(struct.pack("<Q", len(encoded)) + encoded + payload)


def binding(row: dict[str, object], path: Path) -> dict[str, object]:
    value = torch.load(path, map_location="cpu", weights_only=True).detach().cpu().float().contiguous()
    return {
        "tensor": row["name"],
        "parameter_suffix": row["parameter_suffix"],
        "sha256": hashlib.sha256(value.numpy().tobytes()).hexdigest(),
        "file_sha256": sha256_file(path),
        "path": str(path),
        "shape": row["shape"],
        "source_dtype": row["dtype"],
    }


def memh_binary(path: Path) -> bytes:
    return b"".join(struct.pack("<I", int(line, 16)) for line in path.read_text().splitlines())


class BoardWeightImageTest(TestCase):
    def setUp(self) -> None:
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name)
        layer_values = {
            0: {
                "input_norm.weight": ("BF16", torch.tensor([0.25, 0.5, 0.75, 1.0])),
                "proj.weight": ("F16", torch.arange(1, 17, dtype=torch.float32).reshape(4, 4)),
                "output_norm.weight": ("F32", torch.tensor([1.125, 1.25, 1.5, 1.75])),
            },
            1: {
                "input_norm.weight": ("BF16", torch.tensor([2.0, 2.5, 3.0, 3.5])),
                "proj.weight": ("F16", torch.arange(21, 37, dtype=torch.float32).reshape(4, 4)),
                "output_norm.weight": ("F32", torch.tensor([4.125, 4.25, 4.5, 4.75])),
            },
        }
        self.values = layer_values
        self.shards = []
        all_rows = []
        for layer_index in [0, 1]:
            shard = self.root / f"model-{layer_index + 1:05d}-of-00002.safetensors"
            write_safetensors(
                shard,
                [
                    (
                        f"blocks.{layer_index}.{suffix}",
                        dtype,
                        value,
                    )
                    for suffix, (dtype, value) in layer_values[layer_index].items()
                ],
            )
            self.shards.append(shard)
            file_hash = sha256_file(shard)
            _, rows = parse_safetensors(shard, file_hash)
            all_rows.extend(rows)
        selected, _, _ = bind_transformer_scope(
            all_rows,
            [r"^blocks\.(?P<layer>\d+)\.(?P<suffix>.+)$"],
            num_layers=2,
        )
        selected = hash_tensor_slices(selected)
        layer_ids, suffixes = validate_layer_coverage(selected, 2)
        checkpoint_hash = sha256_json(
            [
                {"path": path.name, "size_bytes": path.stat().st_size, "sha256": sha256_file(path)}
                for path in self.shards
            ]
        )
        self.catalog = {
            "schema_version": "spatialaccagent.transformer_block_weight_catalog.v1",
            "status": "pass",
            "accelerator_scope": "transformer_blocks_only",
            "scope_coverage_complete": True,
            "source_checkpoint_sha256": checkpoint_hash,
            "target_layer_count": 2,
            "layer_ids": layer_ids,
            "tensor_count": len(selected),
            "per_layer_tensor_count": len(suffixes),
            "tensor_suffixes": suffixes,
            "tensors": selected,
        }
        layer_zero = {row["parameter_suffix"]: row for row in selected if row["layer_index"] == 0}
        binding_dir = self.root / "layer0"
        binding_dir.mkdir()
        self.bindings = {}
        for suffix, row in layer_zero.items():
            tensor_path = binding_dir / f"{suffix.replace('.', '_')}.pt"
            torch.save(layer_values[0][suffix][1].to({"BF16": torch.bfloat16, "F16": torch.float16, "F32": torch.float32}[row["dtype"]]), tensor_path)
            self.bindings[suffix] = binding(row, tensor_path)

        layouts = [
            build_stage_weight_layout(
                stage("stage_norm_in", "rms_norm_1"),
                {},
                [self.bindings["input_norm.weight"]],
                NUMERIC_POLICY,
            ),
            build_stage_weight_layout(
                stage("stage_projection", "mlp_gate_proj"),
                {},
                [self.bindings["proj.weight"]],
                NUMERIC_POLICY,
            ),
            build_stage_weight_layout(
                stage("stage_norm_out", "rms_norm_2"),
                {},
                [self.bindings["output_norm.weight"]],
                NUMERIC_POLICY,
            ),
        ]
        stage_streams = []
        for layout in layouts:
            suffix_list = [
                source["parameter_suffix"]
                for target in layout["storage_targets"]
                for source in target["source_tensors"]
            ]
            stream = materialize_stage_weight_stream(
                self.root / "canonical" / layout["stage_id"] / "weight.memh",
                layout,
                [self.bindings[suffix] for suffix in suffix_list],
            )
            stage_streams.append(
                {
                    "stage_id": layout["stage_id"],
                    "op": layout["op"],
                    "layout": layout,
                    "stream": stream,
                }
            )
        self.connected = materialize_composite_weight_stream(
            self.root / "canonical" / "layer0.memh",
            stage_streams,
        )
        self.layouts = layouts
        self.requirements = self.make_requirements(self.catalog)
        self.plan = self.make_plan(self.catalog, self.requirements)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def make_requirements(self, catalog: dict[str, object]) -> dict[str, object]:
        return {
            "schema_version": "spatialaccagent.dut_weight_binding_requirements.v1",
            "status": "requirements",
            "accelerator_scope": "transformer_blocks_only",
            "accelerator_weight_catalog_sha256": sha256_json(catalog),
            "source_checkpoint_sha256": catalog["source_checkpoint_sha256"],
            "connected_weight_stream_contract": self.connected,
            "stage_requirements": [
                {
                    "stage_id": layout["stage_id"],
                    "op": layout["op"],
                    "required_tensors": [
                        self.bindings[source["parameter_suffix"]]
                        for target in layout["storage_targets"]
                        for source in target["source_tensors"]
                    ],
                    "weight_layout": layout,
                    "weight_layout_contract_sha256": layout["contract_sha256"],
                }
                for layout in self.layouts
            ],
        }

    def make_plan(
        self,
        catalog: dict[str, object],
        requirements: dict[str, object],
        *,
        bank_capacity: int | None = None,
    ) -> dict[str, object]:
        layout_hashes = [layout["contract_sha256"] for layout in self.layouts]
        layer_bytes = int(self.connected["word_count"]) * 4
        aligned_bytes = ((layer_bytes + 63) // 64) * 64
        return {
            "schema_version": PLAN_SCHEMA_VERSION,
            "status": "pass",
            "target_layer_count": 2,
            "input_identity": {
                "transformer_block_weight_catalog_sha256": sha256_json(catalog),
                "source_checkpoint_sha256": catalog["source_checkpoint_sha256"],
                "connected_weight_stream_contract_sha256": self.connected["contract_sha256"],
                "stage_weight_layout_contract_sha256s": layout_hashes,
                "canonical_weight_layout_set_sha256": sha256_json(
                    {"stage_weight_layout_contract_sha256s": layout_hashes}
                ),
            },
            "image": {
                "format": "u32le_binary",
                "word_bits": 32,
                "byte_order": "little",
                "layer_order": [0, 1],
                "layer_alignment_bytes": 64,
            },
            "memory": {
                "weight_bank_count": 2,
                "weight_bank_capacity_bytes": bank_capacity if bank_capacity is not None else aligned_bytes,
            },
            "additional_runtime_fields": {"agent_owned": True},
        }

    def assert_no_partial_output(self, image: Path, manifest: Path) -> None:
        self.assertFalse(image.exists())
        self.assertFalse(manifest.exists())
        self.assertEqual(list(image.parent.glob(f".{image.name}.*.tmp")), [])
        self.assertEqual(list(manifest.parent.glob(f".{manifest.name}.*.tmp")), [])

    def test_two_layer_mixed_dtype_image_matches_canonical_layer_and_is_order_stable(self) -> None:
        image = self.root / "out" / "weights.u32le.bin"
        manifest_path = self.root / "out" / "full_weight_image_manifest.json"
        manifest = materialize_board_weight_image(
            self.catalog,
            self.requirements,
            self.plan,
            image,
            manifest_path,
        )

        payload = image.read_bytes()
        expected_layer_zero = memh_binary(Path(self.connected["path"]))
        first = manifest["layer_segments"][0]
        second = manifest["layer_segments"][1]
        self.assertEqual(payload[first["byte_offset"] : first["byte_offset"] + first["payload_byte_count"]], expected_layer_zero)
        self.assertNotEqual(
            payload[first["byte_offset"] : first["byte_offset"] + first["payload_byte_count"]],
            payload[second["byte_offset"] : second["byte_offset"] + second["payload_byte_count"]],
        )
        self.assertEqual(first["byte_offset"] % 64, 0)
        self.assertEqual(second["byte_offset"] % 64, 0)
        self.assertEqual(manifest["packed_tensor_count"], 6)
        self.assertEqual(set(manifest["packed_tensor_hashes"]), {row["source_slice_sha256"] for row in self.catalog["tensors"]})
        self.assertTrue(manifest["scope_coverage_complete"])
        self.assertEqual(manifest["sha256"], sha256_file(image))
        contract_hash = manifest["manifest_contract_sha256"]
        self.assertEqual(
            contract_hash,
            sha256_json({key: value for key, value in manifest.items() if key != "manifest_contract_sha256"}),
        )
        self.assertEqual(json.loads(manifest_path.read_text()), manifest)

        shuffled_catalog = deepcopy(self.catalog)
        shuffled_catalog["tensors"] = list(reversed(shuffled_catalog["tensors"]))
        shuffled_requirements = self.make_requirements(shuffled_catalog)
        shuffled_plan = self.make_plan(shuffled_catalog, shuffled_requirements)
        shuffled_image = self.root / "shuffled" / "weights.u32le.bin"
        materialize_board_weight_image(
            shuffled_catalog,
            shuffled_requirements,
            shuffled_plan,
            shuffled_image,
        )
        self.assertEqual(shuffled_image.read_bytes(), payload)

    def test_missing_layer_suffix_fails_without_output(self) -> None:
        catalog = deepcopy(self.catalog)
        catalog["tensors"] = [
            row
            for row in catalog["tensors"]
            if not (row["layer_index"] == 1 and row["parameter_suffix"] == "output_norm.weight")
        ]
        catalog["tensor_count"] = len(catalog["tensors"])
        requirements = self.make_requirements(catalog)
        plan = self.make_plan(catalog, requirements)
        image = self.root / "missing" / "weights.bin"
        manifest = self.root / "missing" / "full_weight_image_manifest.json"

        with self.assertRaisesRegex(BoardWeightImageError, "suffix coverage is inconsistent"):
            materialize_board_weight_image(catalog, requirements, plan, image, manifest)
        self.assert_no_partial_output(image, manifest)

    def test_shard_and_slice_tamper_fail_without_partial_output(self) -> None:
        shard = self.shards[1]
        raw = bytearray(shard.read_bytes())
        raw[-1] ^= 0x01
        shard.write_bytes(raw)
        shard_image = self.root / "shard-tamper" / "weights.bin"
        shard_manifest = self.root / "shard-tamper" / "full_weight_image_manifest.json"

        with self.assertRaisesRegex(BoardWeightImageError, "source shard hash mismatch"):
            materialize_board_weight_image(
                self.catalog,
                self.requirements,
                self.plan,
                shard_image,
                shard_manifest,
            )
        self.assert_no_partial_output(shard_image, shard_manifest)

        new_shard_hash = sha256_file(shard)
        catalog = deepcopy(self.catalog)
        for row in catalog["tensors"]:
            if Path(row["source_file"]) == shard:
                row["source_file_sha256"] = new_shard_hash
        requirements = self.make_requirements(catalog)
        plan = self.make_plan(catalog, requirements)
        image = self.root / "tamper" / "weights.bin"
        manifest = self.root / "tamper" / "full_weight_image_manifest.json"

        with self.assertRaisesRegex(BoardWeightImageError, "source tensor slice hash mismatch"):
            materialize_board_weight_image(catalog, requirements, plan, image, manifest)
        self.assert_no_partial_output(image, manifest)

    def test_bank_shortfall_fails_before_writing_output(self) -> None:
        required = int(self.connected["word_count"]) * 4
        plan = self.make_plan(self.catalog, self.requirements, bank_capacity=required - 4)
        image = self.root / "small-bank" / "weights.bin"
        manifest = self.root / "small-bank" / "full_weight_image_manifest.json"

        with self.assertRaisesRegex(BoardWeightImageError, r"shortfall=4 bytes"):
            materialize_board_weight_image(self.catalog, self.requirements, plan, image, manifest)
        self.assert_no_partial_output(image, manifest)
