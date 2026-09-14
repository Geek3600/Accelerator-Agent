from __future__ import annotations

import copy
import json
import struct
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

import torch

from accagent.framework.board_runtime_image import (
    BoardRuntimeImageError,
    CAPTURE_SCHEMA_VERSION,
    IMAGE_FORMAT,
    LAYER_RUNTIME_CAPTURE_CONTRACT_SCHEMA,
    materialize_board_runtime_image,
    sha256_file,
    sha256_json,
    validate_layer_runtime_capture_contract,
)
from accagent.framework.semantic_runtime import (
    materialize_composite_runtime_stream,
    materialize_semantic_runtime_constants,
    tensor_sha256,
)


class BoardRuntimeImageTest(TestCase):
    def setUp(self) -> None:
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.adapter = {
            "schema_version": "spatialaccagent.model_semantic_adapter.v1",
            "accelerator_scope": "transformer_blocks_only",
            "semantic_runtime_streams": {
                "custom_runtime_op": {
                    "source_order": ["source_x", "source_y"],
                    "targets": {
                        "source_x": {
                            "target_id": "runtime.target_x",
                            "semantic_role": "user_runtime_integer",
                            "storage_dtype": "uint32",
                            "source_axis_order": ["batch", "token"],
                            "drop_singleton_axes": [0],
                            "address_formula": "token",
                            "sharing": "one value for each invocation token",
                        },
                        "source_y": {
                            "target_id": "runtime.target_y",
                            "semantic_role": "user_runtime_table",
                            "storage_dtype": "fp16",
                            "source_axis_order": ["batch", "token", "feature"],
                            "drop_singleton_axes": [0],
                            "address_formula": "token * feature_count + feature",
                            "sharing": "captured independently for each layer invocation",
                        },
                    },
                }
            },
        }
        self.adapter_path = self.root / "semantic_adapter.json"
        self.adapter_path.write_text(
            json.dumps(self.adapter, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        layer_values = [
            (
                torch.tensor([[0, 1]], dtype=torch.int64),
                torch.tensor([[[1.0, 2.0], [3.0, 4.0]]], dtype=torch.float32),
            ),
            (
                torch.tensor([[0, 1]], dtype=torch.int64),
                torch.tensor([[[1.0, 2.0], [3.0, 4.0]]], dtype=torch.float32),
            ),
            (
                torch.tensor([[2, 3]], dtype=torch.int64),
                torch.tensor([[[1.0, 2.0], [3.0, 4.0]]], dtype=torch.float32),
            ),
        ]
        self.layer_sources: list[dict[str, dict]] = []
        for layer_index, (source_x, source_y) in enumerate(layer_values):
            layer_dir = self.root / "captures" / f"layer_{layer_index}"
            layer_dir.mkdir(parents=True)
            rows = {}
            for key, tensor in (("source_x", source_x), ("source_y", source_y)):
                path = layer_dir / f"{key}.pt"
                torch.save(tensor, path)
                rows[key] = {
                    "source_key": key,
                    "path": str(path),
                    "file_sha256": sha256_file(path),
                    "tensor_sha256": tensor_sha256(tensor),
                    "dtype": str(tensor.dtype),
                    "shape": list(tensor.shape),
                }
            self.layer_sources.append(rows)

        reference = {
            "reference": {
                "semantic_runtime_inputs": copy.deepcopy(self.layer_sources[0])
            }
        }
        self.semantic_runtime = materialize_semantic_runtime_constants(
            reference,
            self.adapter,
            self.root / "semantic_runtime",
            semantic_adapter_sha256=sha256_file(self.adapter_path),
        )
        self.assertEqual(self.semantic_runtime["status"], "pass")
        runtime_stream = self.semantic_runtime["streams"][0]
        self.connected = materialize_composite_runtime_stream(
            self.root / "connected_runtime.memh",
            [
                {"stage_id": "stage_empty_before", "op": "empty_before", "runtime_contract": None},
                {
                    "stage_id": "stage_runtime_custom",
                    "op": "custom_runtime_op",
                    "runtime_contract": runtime_stream,
                },
                {"stage_id": "stage_empty_after", "op": "empty_after", "runtime_contract": None},
            ],
        )
        self.capture = self.make_capture()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def make_capture(self) -> dict:
        capture = {
            "schema_version": CAPTURE_SCHEMA_VERSION,
            "status": "pass",
            "accelerator_scope": "transformer_blocks_only",
            "target_layer_count": len(self.layer_sources),
            "source_reference_manifest_sha256": "1" * 64,
            "semantic_adapter_sha256": sha256_file(self.adapter_path),
            "semantic_runtime_contract_sha256": self.semantic_runtime["contract_sha256"],
            "connected_runtime_stream_contract_sha256": self.connected["contract_sha256"],
            "layers": [
                {
                    "layer_index": layer_index,
                    "stage_invocations": [
                        {
                            "stage_id": "stage_runtime_custom",
                            "consumer_op": "custom_runtime_op",
                            "sources": [
                                copy.deepcopy(sources["source_x"]),
                                copy.deepcopy(sources["source_y"]),
                            ],
                        }
                    ],
                }
                for layer_index, sources in enumerate(self.layer_sources)
            ],
        }
        capture["contract_sha256"] = sha256_json(capture)
        return capture

    def runtime_contract_input(self) -> Path:
        return Path(str(self.semantic_runtime["path"]))

    def assert_no_output(self, image: Path, manifest: Path) -> None:
        self.assertFalse(image.exists())
        self.assertFalse(manifest.exists())
        self.assertEqual(list(image.parent.glob(f".{image.name}.*.tmp")), [])
        self.assertEqual(list(manifest.parent.glob(f".{manifest.name}.*.tmp")), [])

    def test_schema_requires_explicit_full_layer_invocations(self) -> None:
        self.assertEqual(
            LAYER_RUNTIME_CAPTURE_CONTRACT_SCHEMA["properties"]["schema_version"]["enum"],
            [CAPTURE_SCHEMA_VERSION],
        )
        self.assertIn("layers", LAYER_RUNTIME_CAPTURE_CONTRACT_SCHEMA["required"])
        layer_schema = LAYER_RUNTIME_CAPTURE_CONTRACT_SCHEMA["properties"]["layers"]["items"]
        self.assertIn("stage_invocations", layer_schema["required"])

        capture = copy.deepcopy(self.capture)
        capture["unbound_llm_note"] = "must not become authority"
        capture["contract_sha256"] = sha256_json(
            {key: value for key, value in capture.items() if key != "contract_sha256"}
        )
        report, errors = validate_layer_runtime_capture_contract(
            capture,
            self.adapter_path,
            self.runtime_contract_input(),
            self.connected,
        )
        self.assertEqual(report, {"status": "fail"})
        self.assertRegex(errors[0], "not an allowed field")

    def test_exact_equal_layers_deduplicate_and_different_layer_stays_distinct(self) -> None:
        image = self.root / "out" / "runtime.u32le.bin"
        manifest_path = self.root / "out" / "board_runtime_image_manifest.json"

        manifest = materialize_board_runtime_image(
            self.capture,
            self.adapter_path,
            self.runtime_contract_input(),
            self.connected,
            image,
            manifest_path,
        )

        self.assertEqual(manifest["status"], "pass")
        self.assertEqual(manifest["image_format"], IMAGE_FORMAT)
        self.assertEqual(manifest["target_layer_count"], 3)
        self.assertEqual(manifest["canonical_layer_word_count"], 4)
        self.assertEqual(manifest["unique_stream_count"], 2)
        bindings = manifest["layer_bindings"]
        self.assertEqual(bindings[0]["segment_id"], bindings[1]["segment_id"])
        self.assertNotEqual(bindings[1]["segment_id"], bindings[2]["segment_id"])
        self.assertEqual(manifest["total_bytes"], 32)
        self.assertEqual(sha256_file(image), manifest["image_sha256"])
        contract_payload = {
            key: value for key, value in manifest.items() if key != "manifest_contract_sha256"
        }
        self.assertEqual(
            sha256_json(contract_payload), manifest["manifest_contract_sha256"]
        )
        self.assertTrue(
            manifest["deduplication_policy"]["cross_layer_sharing_is_never_assumed"]
        )

        semantic_words = [
            int(line, 16)
            for line in Path(
                self.semantic_runtime["streams"][0]["stream"]["path"]
            ).read_text(encoding="ascii").splitlines()
        ]
        expected_first = b"".join(struct.pack("<I", word) for word in semantic_words)
        self.assertEqual(image.read_bytes()[: len(expected_first)], expected_first)

    def test_validator_reports_layer_byte_identities_without_writing(self) -> None:
        report, errors = validate_layer_runtime_capture_contract(
            self.capture,
            self.adapter_path,
            self.runtime_contract_input(),
            self.connected,
        )

        self.assertEqual(errors, [])
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["layers"][0]["sha256"], report["layers"][1]["sha256"])
        self.assertNotEqual(report["layers"][1]["sha256"], report["layers"][2]["sha256"])

    def test_missing_layer_or_source_fails_without_partial_output(self) -> None:
        for mutation in ("missing_layer", "missing_source"):
            with self.subTest(mutation=mutation):
                capture = copy.deepcopy(self.capture)
                if mutation == "missing_layer":
                    capture["layers"].pop()
                else:
                    capture["layers"][1]["stage_invocations"][0]["sources"].pop()
                capture["contract_sha256"] = sha256_json(
                    {key: value for key, value in capture.items() if key != "contract_sha256"}
                )
                image = self.root / mutation / "runtime.bin"
                manifest = self.root / mutation / "manifest.json"

                with self.assertRaises(BoardRuntimeImageError):
                    materialize_board_runtime_image(
                        capture,
                        self.adapter_path,
                        self.runtime_contract_input(),
                        self.connected,
                        image,
                        manifest,
                    )
                self.assert_no_output(image, manifest)

    def test_capture_file_and_tensor_hashes_are_not_advisory(self) -> None:
        capture = copy.deepcopy(self.capture)
        capture["layers"][0]["stage_invocations"][0]["sources"][0][
            "tensor_sha256"
        ] = "2" * 64
        capture["contract_sha256"] = sha256_json(
            {key: value for key, value in capture.items() if key != "contract_sha256"}
        )
        image = self.root / "tamper" / "runtime.bin"
        manifest = self.root / "tamper" / "manifest.json"

        with self.assertRaisesRegex(BoardRuntimeImageError, "tensor value hash mismatch"):
            materialize_board_runtime_image(
                capture,
                self.adapter_path,
                self.runtime_contract_input(),
                self.connected,
                image,
                manifest,
            )
        self.assert_no_output(image, manifest)

    def test_capture_dtype_must_match_semantic_runtime_authority(self) -> None:
        capture = copy.deepcopy(self.capture)
        row = capture["layers"][0]["stage_invocations"][0]["sources"][1]
        source_path = Path(row["path"])
        tensor = torch.load(source_path, map_location="cpu", weights_only=True).to(
            torch.float16
        )
        replacement = source_path.with_name("source_y_fp16.pt")
        torch.save(tensor, replacement)
        row.update(
            {
                "path": str(replacement),
                "file_sha256": sha256_file(replacement),
                "tensor_sha256": tensor_sha256(tensor),
                "dtype": str(tensor.dtype),
                "shape": list(tensor.shape),
            }
        )
        capture["contract_sha256"] = sha256_json(
            {key: value for key, value in capture.items() if key != "contract_sha256"}
        )
        image = self.root / "dtype_tamper" / "runtime.bin"
        manifest = self.root / "dtype_tamper" / "manifest.json"

        with self.assertRaisesRegex(BoardRuntimeImageError, "source_dtype differs"):
            materialize_board_runtime_image(
                capture,
                self.adapter_path,
                self.runtime_contract_input(),
                self.connected,
                image,
                manifest,
            )
        self.assert_no_output(image, manifest)

    def test_connected_target_layout_mismatch_fails_closed(self) -> None:
        connected = copy.deepcopy(self.connected)
        target = connected["stage_segments"][1]["targets"][0]
        target["semantic_role"] = "different_runtime_role"
        connected["contract_sha256"] = sha256_json(
            {
                key: value
                for key, value in connected.items()
                if key not in {"contract_sha256", "path"}
            }
        )
        capture = copy.deepcopy(self.capture)
        capture["connected_runtime_stream_contract_sha256"] = connected["contract_sha256"]
        capture["contract_sha256"] = sha256_json(
            {key: value for key, value in capture.items() if key != "contract_sha256"}
        )
        image = self.root / "layout_tamper" / "runtime.bin"
        manifest = self.root / "layout_tamper" / "manifest.json"

        with self.assertRaisesRegex(BoardRuntimeImageError, "connected target differs"):
            materialize_board_runtime_image(
                capture,
                self.adapter_path,
                self.runtime_contract_input(),
                connected,
                image,
                manifest,
            )
        self.assert_no_output(image, manifest)
