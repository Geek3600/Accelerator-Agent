from __future__ import annotations

import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase

import torch
from torch import nn

from accagent.framework.board_runtime_capture import (
    BoardRuntimeCaptureError,
    capture_board_runtime_contract,
)
from accagent.framework.board_runtime_image import (
    CAPTURE_SCHEMA_VERSION,
    materialize_board_runtime_image,
    sha256_file,
)
from accagent.framework.semantic_runtime import (
    materialize_composite_runtime_stream,
    materialize_semantic_runtime_constants,
    tensor_sha256,
)


class OpaqueRuntimeNode(nn.Module):
    def forward(
        self,
        hidden: torch.Tensor,
        opaque_carrier: tuple[str, torch.Tensor],
        *,
        envelope: dict,
    ) -> torch.Tensor:
        del opaque_carrier, envelope
        return hidden


class SyntheticDecoderLayer(nn.Module):
    def __init__(
        self,
        layer_index: int,
        integer_runtime: torch.Tensor,
        table_runtime: torch.Tensor,
        *,
        duplicate_integer_path: bool = False,
    ) -> None:
        super().__init__()
        self.runtime_node = OpaqueRuntimeNode()
        self.register_buffer("integer_runtime", integer_runtime)
        self.register_buffer("table_runtime", table_runtime)
        self.layer_index = layer_index
        self.duplicate_integer_path = duplicate_integer_path

    def forward(self, hidden: torch.Tensor) -> torch.Tensor:
        envelope = {"buried": [{"table_slot": self.table_runtime}]}
        if self.duplicate_integer_path:
            envelope["duplicate_slot"] = self.integer_runtime
        value = self.runtime_node(
            hidden,
            ("opaque", self.integer_runtime),
            envelope=envelope,
        )
        return value + float(self.layer_index + 1)


class SyntheticCausalLM(nn.Module):
    def __init__(self, *, duplicate_integer_path: bool = False) -> None:
        super().__init__()
        runtime_values = [
            (
                torch.tensor([index, index + 1], dtype=torch.int64),
                torch.tensor(
                    [[[[index + 0.25, index + 0.5], [index + 0.75, index + 1.0]]]],
                    dtype=torch.float32,
                ).reshape(1, 2, 2),
            )
            for index in range(3)
        ]
        self.blocks = nn.ModuleList(
            [
                SyntheticDecoderLayer(
                    index,
                    integer_runtime,
                    table_runtime,
                    duplicate_integer_path=duplicate_integer_path and index == 0,
                )
                for index, (integer_runtime, table_runtime) in enumerate(runtime_values)
            ]
        )
        self.inference_calls = 0

    def forward(self, inputs_embeds: torch.Tensor, **_kwargs) -> SimpleNamespace:
        self.inference_calls += 1
        hidden = inputs_embeds
        hidden_states = [hidden]
        for block in self.blocks:
            hidden = block(hidden)
            hidden_states.append(hidden)
        return SimpleNamespace(hidden_states=tuple(hidden_states))


class BoardRuntimeCaptureTest(TestCase):
    def setUp(self) -> None:
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.snapshot = self.root / "checkpoint_snapshot"
        self.snapshot.mkdir()
        self.weight_manifest_path = self.root / "weight_manifest.json"
        self._write_json(self.weight_manifest_path, {"status": "ready"})

        self.adapter = {
            "schema_version": "spatialaccagent.model_semantic_adapter.v1",
            "model_family": "synthetic_family",
            "accelerator_scope": "transformer_blocks_only",
            "semantic_runtime_streams": {
                "opaque_runtime_consumer": {
                    "source_order": ["integer_source", "table_source"],
                    "targets": {
                        "integer_source": {
                            "target_id": "runtime.integer_target",
                            "semantic_role": "synthetic_integer_role",
                            "storage_dtype": "uint32",
                            "source_axis_order": ["token"],
                            "drop_singleton_axes": [],
                            "address_formula": "token",
                            "sharing": "captured at every decoder layer invocation",
                        },
                        "table_source": {
                            "target_id": "runtime.table_target",
                            "semantic_role": "synthetic_table_role",
                            "storage_dtype": "fp16",
                            "source_axis_order": ["batch", "token", "feature"],
                            "drop_singleton_axes": [0],
                            "address_formula": "token * feature_count + feature",
                            "sharing": "captured at every decoder layer invocation",
                        },
                    },
                }
            },
            "semantic_stages": {
                "opaque_runtime_consumer": {
                    "inputs": [{"source": "opaque_input"}],
                    "expected": {"record": "runtime_node", "value": "output"},
                    "required_weight_suffixes": [],
                }
            },
        }
        self.adapter_path = self.root / "semantic_adapter.json"
        self._write_json(self.adapter_path, self.adapter)

        self.model = SyntheticCausalLM()
        self.input_tensor = torch.arange(8, dtype=torch.float32).reshape(1, 2, 4)
        self.expected_output = self.input_tensor + 6.0
        self.input_path = self.root / "reference_input.pt"
        self.final_output_path = self.root / "reference_final_output.pt"
        torch.save(self.input_tensor, self.input_path)
        torch.save(self.expected_output, self.final_output_path)

        runtime_dir = self.root / "reference_runtime"
        runtime_dir.mkdir()
        first_layer = self.model.blocks[0]
        self.runtime_records = {
            "integer_source": self._tensor_record(
                runtime_dir / "source_without_argument_name_a.pt",
                first_layer.integer_runtime,
            ),
            "table_source": self._tensor_record(
                runtime_dir / "source_without_argument_name_b.pt",
                first_layer.table_runtime,
            ),
        }
        self.reference = self._make_reference()
        self.reference_path = self.root / "reference_manifest.json"
        self._write_json(self.reference_path, self.reference)
        self.semantic_runtime, self.connected = self._make_runtime_contracts(
            self.adapter, self.adapter_path, self.reference
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def _write_json(path: Path, value: dict) -> None:
        path.write_text(
            json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    @staticmethod
    def _qualified_type(value: object) -> str:
        return f"{type(value).__module__}.{type(value).__qualname__}"

    def _tensor_record(self, path: Path, tensor: torch.Tensor) -> dict:
        torch.save(tensor, path)
        return {
            "path": str(path),
            "file_sha256": sha256_file(path),
            "tensor_sha256": tensor_sha256(tensor),
            "shape": list(tensor.shape),
            "dtype": str(tensor.dtype),
        }

    def _make_reference(self) -> dict:
        return {
            "schema_version": "spatialaccagent.target_model_reference.v1",
            "status": "ready",
            "run_dir": str(self.root),
            "target_model": {
                "model_id": "synthetic/model",
                "revision": "synthetic-revision",
                "snapshot": str(self.snapshot),
                "architecture": type(self.model).__name__,
                "num_hidden_layers": len(self.model.blocks),
                "hidden_size": self.input_tensor.shape[-1],
                "accelerator_scope": "transformer_blocks_only",
                "excluded_model_regions": [],
            },
            "weights": {
                "source_manifest": str(self.weight_manifest_path),
                "source_manifest_sha256": sha256_file(self.weight_manifest_path),
                "source_checkpoint_sha256": "a" * 64,
                "accelerator_scope": "transformer_blocks_only",
                "real_target_weights": True,
                "loaded_by_reference_model": True,
            },
            "input": self._existing_tensor_record(self.input_path, self.input_tensor),
            "reference": {
                "engine": f"synthetic.{type(self.model).__name__}",
                "independent_of_rtl": True,
                "uses_same_input_and_weights": True,
                "expected_output_source": "target_model_inference",
                "full_model_output": {
                    **self._existing_tensor_record(
                        self.final_output_path, self.expected_output
                    ),
                    "scope": "all_target_decoder_layers_at_accelerator_output_boundary",
                    "target_layer_count": len(self.model.blocks),
                    "source_capture": "arbitrary_last_layer_record",
                },
                "semantic_runtime_inputs": copy.deepcopy(self.runtime_records),
                "semantic_adapter": {
                    "path": str(self.adapter_path),
                    "sha256": sha256_file(self.adapter_path),
                    "model_family": "synthetic_family",
                },
                "layer_output_records": [
                    {"module": f"arbitrary_layer_marker_{index}"}
                    for index in range(len(self.model.blocks))
                ],
                "all_target_layers_captured": True,
                "model_implementation": {
                    "symbols": {
                        "decoder_layer": self._qualified_type(self.model.blocks[0])
                    }
                },
            },
        }

    @staticmethod
    def _existing_tensor_record(path: Path, tensor: torch.Tensor) -> dict:
        return {
            "path": str(path),
            "file_sha256": sha256_file(path),
            "tensor_sha256": tensor_sha256(tensor),
            "shape": list(tensor.shape),
            "dtype": str(tensor.dtype),
        }

    def _make_runtime_contracts(
        self, adapter: dict, adapter_path: Path, reference: dict
    ) -> tuple[dict, dict]:
        semantic_runtime = materialize_semantic_runtime_constants(
            reference,
            adapter,
            self.root / f"runtime_{sha256_file(adapter_path)[:8]}",
            semantic_adapter_sha256=sha256_file(adapter_path),
        )
        self.assertEqual(semantic_runtime["status"], "pass")
        connected = materialize_composite_runtime_stream(
            self.root / f"connected_{sha256_file(adapter_path)[:8]}.memh",
            [
                {
                    "stage_id": "arbitrary_stage_before",
                    "op": "unrelated_before",
                    "runtime_contract": None,
                },
                {
                    "stage_id": "arbitrary_runtime_stage_7",
                    "op": "opaque_runtime_consumer",
                    "runtime_contract": semantic_runtime["streams"][0],
                },
                {
                    "stage_id": "arbitrary_stage_after",
                    "op": "unrelated_after",
                    "runtime_contract": None,
                },
            ],
        )
        return semantic_runtime, connected

    def _capture(self, output_dir: Path, *, model: nn.Module | None = None) -> dict:
        return capture_board_runtime_contract(
            self.reference_path,
            self.adapter_path,
            self.semantic_runtime,
            self.connected,
            output_dir,
            model=model or self.model,
        )

    def test_one_inference_learns_paths_and_captures_every_layer(self) -> None:
        output_dir = self.root / "captured_runtime"
        capture = self._capture(output_dir)

        self.assertEqual(self.model.inference_calls, 1)
        self.assertEqual(capture["schema_version"], CAPTURE_SCHEMA_VERSION)
        self.assertEqual(capture["target_layer_count"], 3)
        self.assertTrue(capture["capture_provenance"]["reference_output_verified"])
        self.assertFalse(capture["capture_provenance"]["keyword_matching_used"])
        self.assertEqual(
            capture["capture_provenance"]["capture_match_fields"],
            ["tensor_sha256", "shape", "dtype"],
        )
        for layer_index, layer in enumerate(capture["layers"]):
            self.assertEqual(layer["layer_index"], layer_index)
            self.assertEqual(
                [row["stage_id"] for row in layer["stage_invocations"]],
                ["arbitrary_runtime_stage_7"],
            )
            sources = layer["stage_invocations"][0]["sources"]
            self.assertEqual(
                [row["source_key"] for row in sources],
                ["integer_source", "table_source"],
            )
            self.assertTrue(all(Path(row["path"]).is_file() for row in sources))
            self.assertNotIn("integer_source", " ".join(sources[0]["capture_path"]))
            self.assertNotIn("table_source", " ".join(sources[1]["capture_path"]))
        self.assertNotEqual(
            capture["layers"][0]["stage_invocations"][0]["sources"][0][
                "tensor_sha256"
            ],
            capture["layers"][2]["stage_invocations"][0]["sources"][0][
                "tensor_sha256"
            ],
        )

        image = self.root / "runtime_image" / "runtime.bin"
        manifest = materialize_board_runtime_image(
            capture["path"],
            self.adapter_path,
            self.semantic_runtime,
            self.connected,
            image,
        )
        self.assertEqual(manifest["status"], "pass")
        self.assertEqual(manifest["target_layer_count"], 3)

    def test_ambiguous_first_layer_identity_fails_without_artifacts(self) -> None:
        model = SyntheticCausalLM(duplicate_integer_path=True)
        output_dir = self.root / "ambiguous_capture"

        with self.assertRaisesRegex(BoardRuntimeCaptureError, "matched 2.*paths"):
            self._capture(output_dir, model=model)

        self.assertEqual(model.inference_calls, 1)
        self.assertFalse(output_dir.exists())
        self.assertTrue(all(not block._forward_hooks for block in model.blocks))
        self.assertTrue(
            all(not block.runtime_node._forward_pre_hooks for block in model.blocks)
        )

    def test_final_decoder_output_must_match_existing_reference(self) -> None:
        wrong_output = self.expected_output + 1.0
        wrong_path = self.root / "wrong_reference_final.pt"
        torch.save(wrong_output, wrong_path)
        reference = copy.deepcopy(self.reference)
        reference["reference"]["full_model_output"].update(
            self._existing_tensor_record(wrong_path, wrong_output)
        )
        self._write_json(self.reference_path, reference)
        output_dir = self.root / "wrong_output_capture"

        with self.assertRaisesRegex(
            BoardRuntimeCaptureError, "observed final decoder-layer output differs"
        ):
            self._capture(output_dir)

        self.assertEqual(self.model.inference_calls, 1)
        self.assertFalse(output_dir.exists())

    def test_missing_adapter_expected_record_fails_before_inference(self) -> None:
        adapter = copy.deepcopy(self.adapter)
        adapter["semantic_stages"]["opaque_runtime_consumer"]["expected"] = {
            "value": "output"
        }
        adapter_path = self.root / "adapter_without_record.json"
        self._write_json(adapter_path, adapter)
        reference = copy.deepcopy(self.reference)
        reference["reference"]["semantic_adapter"].update(
            {"path": str(adapter_path), "sha256": sha256_file(adapter_path)}
        )
        reference_path = self.root / "reference_without_record.json"
        self._write_json(reference_path, reference)
        runtime, connected = self._make_runtime_contracts(
            adapter, adapter_path, reference
        )
        output_dir = self.root / "missing_record_capture"

        with self.assertRaisesRegex(BoardRuntimeCaptureError, "expected.record"):
            capture_board_runtime_contract(
                reference_path,
                adapter_path,
                runtime,
                connected,
                output_dir,
                model=self.model,
            )

        self.assertEqual(self.model.inference_calls, 0)
        self.assertFalse(output_dir.exists())
