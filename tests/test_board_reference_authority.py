import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from accagent.framework.board_reference_authority import (
    semantic_board_reference_artifacts,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class BoardReferenceAuthorityTest(TestCase):
    def make_run(self, root: Path) -> Path:
        run_dir = root / "run"
        semantic_dir = run_dir / "verification" / "semantic_testbench"
        reference_dir = run_dir / "verification" / "model_reference"
        real_tools_dir = run_dir / "verification" / "real_tools"
        catalog_dir = run_dir / "verification" / "model_weights"
        input_dir = run_dir / "input"
        for path in (semantic_dir, reference_dir, real_tools_dir, catalog_dir, input_dir):
            path.mkdir(parents=True, exist_ok=True)

        files = {
            "board_input": semantic_dir / "board_input.memh",
            "board_expected": semantic_dir / "board_expected.memh",
            "tensor_input": reference_dir / "input.pt",
            "tensor_expected": reference_dir / "expected.pt",
            "numeric": input_dir / "numeric_policy.json",
        }
        for name, path in files.items():
            path.write_bytes(f"{name}\n".encode("ascii"))
        shape = [1, 3, 5]
        checkpoint = "a" * 64
        tensor_input = {
            "path": str(files["tensor_input"]),
            "file_sha256": sha256(files["tensor_input"]),
            "tensor_sha256": "b" * 64,
            "shape": shape,
            "dtype": "torch.float32",
        }
        tensor_expected = {
            "path": str(files["tensor_expected"]),
            "file_sha256": sha256(files["tensor_expected"]),
            "tensor_sha256": "c" * 64,
            "shape": shape,
            "dtype": "torch.float32",
            "scope": "all_target_decoder_layers_at_accelerator_output_boundary",
            "target_layer_count": 7,
        }
        reference_path = reference_dir / "reference_manifest.json"
        reference_path.write_text(
            json.dumps(
                {
                    "input": tensor_input,
                    "reference": {
                        "all_target_layers_captured": True,
                        "independent_of_rtl": True,
                        "expected_output_source": "target_model_inference",
                        "full_model_output": tensor_expected,
                        "numeric_policy_sha256": sha256(files["numeric"]),
                        "real_weight_source": {
                            "source_checkpoint_sha256": checkpoint
                        },
                    },
                }
            ),
            encoding="utf-8",
        )
        semantic_path = semantic_dir / "semantic_testbench_manifest.json"
        semantic_path.write_text(
            json.dumps(
                {
                    "status": "ready",
                    "blockers": [],
                    "accelerator_scope": "transformer_blocks_only",
                    "board": {
                        "all_target_layer_reference_captured": True,
                        "expected_target_layers": 7,
                        "input_vector": {
                            "path": str(files["board_input"]),
                            "sha256": sha256(files["board_input"]),
                            "tensor_shape": shape,
                            "encoding": "packed",
                        },
                        "expected_output": {
                            "path": str(files["board_expected"]),
                            "sha256": sha256(files["board_expected"]),
                            "tensor_shape": shape,
                            "encoding": "packed",
                        },
                    },
                    "random_input": tensor_input,
                    "real_weight_source": {
                        "source_checkpoint_sha256": checkpoint
                    },
                    "numeric_policy": str(files["numeric"]),
                    "numeric_policy_sha256": sha256(files["numeric"]),
                    "numeric_comparison_policy": {"atol": 0.25},
                }
            ),
            encoding="utf-8",
        )
        (catalog_dir / "transformer_block_weight_catalog.json").write_text(
            json.dumps(
                {
                    "target_layer_count": 7,
                    "source_checkpoint_sha256": checkpoint,
                }
            ),
            encoding="utf-8",
        )
        (real_tools_dir / "case_target_model_reference.json").write_text(
            json.dumps(
                {
                    "status": "pass",
                    "produced_reports": [
                        {"path": str(reference_path), "status": "ready"}
                    ],
                }
            ),
            encoding="utf-8",
        )
        return run_dir

    def test_binds_board_files_to_independent_model_tensors(self) -> None:
        with TemporaryDirectory() as temp_dir:
            authority, blockers = semantic_board_reference_artifacts(
                self.make_run(Path(temp_dir))
            )

        self.assertEqual(blockers, [])
        self.assertEqual(authority["status"], "ready")
        self.assertEqual(
            authority["board_input_artifact"]["source_tensor"]["tensor_sha256"],
            "b" * 64,
        )
        self.assertEqual(
            authority["board_expected_output_artifact"]["source_tensor"][
                "tensor_sha256"
            ],
            "c" * 64,
        )
        self.assertTrue(authority["policy"]["expected_output_is_independent_of_rtl"])

    def test_hash_mismatch_fails_closed(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = self.make_run(Path(temp_dir))
            semantic_path = (
                run_dir
                / "verification"
                / "semantic_testbench"
                / "semantic_testbench_manifest.json"
            )
            semantic = json.loads(semantic_path.read_text(encoding="utf-8"))
            semantic["board"]["expected_output"]["sha256"] = "0" * 64
            semantic_path.write_text(json.dumps(semantic), encoding="utf-8")

            authority, blockers = semantic_board_reference_artifacts(run_dir)

        self.assertEqual(authority["status"], "incomplete")
        self.assertTrue(any("expected-output" in blocker for blocker in blockers))

    def test_partial_prefix_binds_its_terminal_layer_capture(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = self.make_run(Path(temp_dir))
            reference_path = run_dir / "verification" / "model_reference" / "reference_manifest.json"
            semantic_path = (
                run_dir
                / "verification"
                / "semantic_testbench"
                / "semantic_testbench_manifest.json"
            )
            reference_dir = reference_path.parent
            terminal_capture = reference_dir / "decoder_layer_2.pt"
            terminal_capture.write_bytes(b"decoder-layer-2\n")
            reference = json.loads(reference_path.read_text(encoding="utf-8"))
            reference["reference"]["layer_output_records"] = [
                {
                    "module": f"decoder_layer_{index}",
                    "tensor_path": str(terminal_capture if index == 2 else reference_dir / f"decoder_layer_{index}.pt"),
                    "tensor_file_sha256": sha256(terminal_capture) if index == 2 else "0" * 64,
                    "output_sha256": "d" * 64 if index == 2 else "0" * 64,
                    "output_shape": [1, 3, 5],
                    "output_dtype": "torch.float32",
                }
                for index in range(3)
            ]
            reference_path.write_text(json.dumps(reference), encoding="utf-8")

            task_card = run_dir / "input" / "task_card.json"
            model_config = run_dir / "input" / "model_config.json"
            task_card.write_text(
                json.dumps(
                    {
                        "acceptance_policy": {
                            "board_validation_mode": "configurable_prefix_pipeline_liveness",
                            "board_validation_layer_count": 3,
                        }
                    }
                ),
                encoding="utf-8",
            )
            model_config.write_text(json.dumps({"num_layers": 7}), encoding="utf-8")
            semantic = json.loads(semantic_path.read_text(encoding="utf-8"))
            semantic["board"].update(
                {
                    "expected_target_layers": 3,
                    "validation_layer_indices": [0, 1, 2],
                    "reference_output_layer_index": 2,
                    "scoped_layer_reference_captured": True,
                    "board_validation_scope": {
                        "schema_version": "spatialaccagent.board_validation_scope.v1",
                        "mode": "configurable_prefix_pipeline_liveness",
                        "model_layer_count": 7,
                        "validation_layer_indices": [0, 1, 2],
                        "validation_layer_count": 3,
                        "reference_output_layer_index": 2,
                        "covers_full_model": False,
                        "requires_next_layer_prefetch": True,
                        "contract_sha256": "placeholder",
                    },
                }
            )
            semantic["board"]["expected_output"].update(
                {
                    "source_capture": "decoder_layer_2",
                    "source_tensor_path": str(terminal_capture),
                    "source_tensor_file_sha256": sha256(terminal_capture),
                    "source_tensor_sha256": "d" * 64,
                    "reference_kind": "layer_output_record",
                }
            )
            semantic_path.write_text(json.dumps(semantic), encoding="utf-8")

            authority, blockers = semantic_board_reference_artifacts(run_dir)

        self.assertEqual(blockers, [])
        self.assertEqual(authority["reference_output_layer_index"], 2)
        self.assertEqual(
            authority["board_expected_output_artifact"]["source_tensor"]["path"],
            str(terminal_capture),
        )
