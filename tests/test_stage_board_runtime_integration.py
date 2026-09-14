import hashlib
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from accagent.framework.board_acceptance_contract import canonical_contract_sha256
from accagent.framework.board_runtime_capture import CAPTURE_CONTRACT_FILENAME
from accagent.framework.board_runtime_image import (
    CAPTURE_SCHEMA_VERSION,
    MANIFEST_SCHEMA_VERSION,
)
from accagent.framework.stage_repair_execute import (
    exact_board_memory_runtime_paths,
    prepare_board_runtime_artifacts,
    reference_gate_python_execution,
    reusable_board_runtime_capture,
    reusable_board_runtime_image,
    run_runtime_artifact_api,
    sha256_file,
)


class StageBoardRuntimeIntegrationTest(TestCase):
    def write_json(self, path: Path, value: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    def fixture(self, root: Path) -> tuple[dict, dict, dict[str, Path]]:
        run_dir = root / "run"
        paths = exact_board_memory_runtime_paths(run_dir, run_dir / "repair_execution")
        reference_path = run_dir / "verification" / "model_reference" / "reference.json"
        adapter_path = run_dir / "adapter.json"
        semantic_runtime_path = run_dir / "semantic_runtime.json"
        reference = {"schema_version": "reference.test", "status": "ready"}
        adapter = {
            "semantic_runtime_streams": {
                "opaque_consumer": {"source_order": ["opaque_source"]}
            }
        }
        semantic_runtime = {"schema_version": "semantic.test", "status": "pass"}
        semantic_runtime["contract_sha256"] = canonical_contract_sha256(
            semantic_runtime
        )
        connected = {
            "schema_version": "connected.test",
            "status": "pass",
            "path": str(run_dir / "runtime.memh"),
            "sha256": "1" * 64,
            "word_bits": 32,
            "word_count": 1,
            "stage_order": ["stage_0"],
            "stage_segments": [
                {
                    "stage_id": "stage_0",
                    "op": "opaque_consumer",
                    "global_stream_range": {
                        "word_offset": 0,
                        "word_count": 1,
                        "word_end_exclusive": 1,
                    },
                }
            ],
        }
        connected["contract_sha256"] = canonical_contract_sha256(
            {key: value for key, value in connected.items() if key != "path"}
        )
        self.write_json(reference_path, reference)
        self.write_json(adapter_path, adapter)
        self.write_json(semantic_runtime_path, semantic_runtime)

        source_rows = []
        for layer_index in range(2):
            source_path = (
                paths["runtime_capture_dir"]
                / "layers"
                / f"layer_{layer_index}"
                / "opaque.pt"
            )
            source_path.parent.mkdir(parents=True, exist_ok=True)
            source_path.write_bytes(f"tensor-{layer_index}".encode("ascii"))
            source_rows.append(
                {
                    "source_key": "opaque_source",
                    "path": str(source_path),
                    "file_sha256": sha256_file(source_path),
                    "tensor_sha256": hashlib.sha256(
                        f"value-{layer_index}".encode("ascii")
                    ).hexdigest(),
                    "dtype": "torch.float32",
                    "shape": [1],
                }
            )
        capture = {
            "schema_version": CAPTURE_SCHEMA_VERSION,
            "status": "pass",
            "accelerator_scope": "transformer_blocks_only",
            "target_layer_count": 2,
            "source_reference_manifest_sha256": sha256_file(reference_path),
            "semantic_adapter_sha256": sha256_file(adapter_path),
            "semantic_runtime_contract_sha256": semantic_runtime[
                "contract_sha256"
            ],
            "connected_runtime_stream_contract_sha256": connected[
                "contract_sha256"
            ],
            "layers": [
                {
                    "layer_index": layer_index,
                    "stage_invocations": [
                        {
                            "stage_id": "stage_0",
                            "consumer_op": "opaque_consumer",
                            "sources": [source_rows[layer_index]],
                        }
                    ],
                }
                for layer_index in range(2)
            ],
            "capture_provenance": {
                "inference_count": 1,
                "reference_output_verified": True,
                "expected_final_decoder_output_sha256": "2" * 64,
                "observed_final_decoder_output_sha256": "2" * 64,
            },
        }
        capture["contract_sha256"] = canonical_contract_sha256(capture)
        self.write_json(paths["runtime_capture"], capture)

        payload = bytes.fromhex("01020304")
        paths["runtime_image"].parent.mkdir(parents=True, exist_ok=True)
        paths["runtime_image"].write_bytes(payload)
        payload_hash = hashlib.sha256(payload).hexdigest()
        manifest = {
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "status": "pass",
            "accelerator_scope": "transformer_blocks_only",
            "scope_coverage_complete": True,
            "target_layer_count": 2,
            "capture_contract_identity_sha256": sha256_file(
                paths["runtime_capture"]
            ),
            "capture_contract_sha256": capture["contract_sha256"],
            "source_reference_manifest_sha256": sha256_file(reference_path),
            "semantic_adapter_sha256": sha256_file(adapter_path),
            "semantic_runtime_contract_identity_sha256": sha256_file(
                semantic_runtime_path
            ),
            "semantic_runtime_contract_sha256": semantic_runtime[
                "contract_sha256"
            ],
            "connected_runtime_stream_contract_identity_sha256": canonical_contract_sha256(
                connected
            ),
            "connected_runtime_stream_contract_sha256": connected[
                "contract_sha256"
            ],
            "path": str(paths["runtime_image"]),
            "image_sha256": payload_hash,
            "total_bytes": len(payload),
            "unique_segments": [
                {
                    "segment_id": "segment_0",
                    "byte_offset": 0,
                    "byte_count": len(payload),
                    "sha256": payload_hash,
                }
            ],
            "layer_bindings": [
                {"layer_index": layer_index, "segment_id": "segment_0"}
                for layer_index in range(2)
            ],
            "manifest_path": str(paths["runtime_image_manifest"]),
        }
        manifest["manifest_contract_sha256"] = canonical_contract_sha256(manifest)
        self.write_json(paths["runtime_image_manifest"], manifest)
        authority = {
            "model": {"num_hidden_layers": 2},
            "semantic_adapter": adapter,
            "semantic_adapter_path": adapter_path,
            "semantic_runtime_contract": semantic_runtime,
            "connected_runtime_stream_contract": connected,
            "paths": {
                "source_reference": reference_path,
                "semantic_runtime_contract": semantic_runtime_path,
            },
        }
        return authority, capture, paths

    def test_reuses_hash_valid_runtime_artifacts_without_subprocess(self) -> None:
        with TemporaryDirectory() as temp_dir:
            authority, _capture, paths = self.fixture(Path(temp_dir))
            with patch(
                "accagent.framework.stage_repair_execute.run_runtime_artifact_api"
            ) as runner:
                capture, manifest, blockers, executions = (
                    prepare_board_runtime_artifacts(paths, authority)
                )

        self.assertEqual(capture["status"], "pass")
        self.assertEqual(manifest["status"], "pass")
        self.assertEqual(blockers, [])
        self.assertEqual(executions, [])
        runner.assert_not_called()

    def test_capture_and_image_reuse_fail_closed_on_changed_bytes(self) -> None:
        with TemporaryDirectory() as temp_dir:
            authority, _capture, paths = self.fixture(Path(temp_dir))
            self.assertTrue(
                reusable_board_runtime_capture(
                    paths["runtime_capture"],
                    paths["runtime_capture_dir"],
                    authority,
                )
            )
            self.assertTrue(
                reusable_board_runtime_image(
                    paths["runtime_image_manifest"],
                    paths["runtime_image"],
                    paths["runtime_capture"],
                    authority,
                )
            )
            paths["runtime_image"].write_bytes(b"changed")
            self.assertFalse(
                reusable_board_runtime_image(
                    paths["runtime_image_manifest"],
                    paths["runtime_image"],
                    paths["runtime_capture"],
                    authority,
                )
            )
            source = next(paths["runtime_capture_dir"].glob("layers/**/*.pt"))
            source.write_bytes(b"changed")
            self.assertFalse(
                reusable_board_runtime_capture(
                    paths["runtime_capture"],
                    paths["runtime_capture_dir"],
                    authority,
                )
            )

    def test_runtime_image_materialization_passes_scope_explicitly(self) -> None:
        with TemporaryDirectory() as temp_dir:
            authority, _capture, paths = self.fixture(Path(temp_dir))
            with patch(
                "accagent.framework.stage_repair_execute.subprocess.run"
            ) as runner:
                runner.return_value.returncode = 0
                runner.return_value.stdout = ""
                runner.return_value.stderr = ""
                execution = run_runtime_artifact_api(
                    "image",
                    [
                        paths["runtime_capture"],
                        authority["semantic_adapter_path"],
                        authority["paths"]["semantic_runtime_contract"],
                        authority["paths"]["source_reference"],
                        paths["runtime_image"],
                        paths["runtime_image_manifest"],
                    ],
                    {"executable": sys.executable},
                    validation_layer_indices=[0],
                )

        self.assertEqual(execution["returncode"], 0)
        command = runner.call_args.args[0]
        self.assertEqual(json.loads(command[-1]), [0])
        self.assertIn("sys.argv[7]", command[2])

    def test_reference_capture_python_is_bound_to_passed_gate_execution(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            reference_path = root / "reference.json"
            gate_path = root / "reference_gate.json"
            reference_path.write_text('{"status":"ready"}\n', encoding="utf-8")
            gate_path.write_text('{"status":"pass"}\n', encoding="utf-8")
            environment_hash = "a" * 64
            gate = {
                "status": "pass",
                "execution": {"argv": [sys.executable, "reference.py"]},
                "execution_fingerprint": {
                    "payload": {
                        "python_environment_fingerprint_sha256": environment_hash
                    }
                },
                "output_fingerprints": {
                    "artifacts": [
                        {
                            "path": str(reference_path),
                            "sha256": sha256_file(reference_path),
                        }
                    ]
                },
                "python_environment": {
                    "status": "pass",
                    "selected_executable": sys.executable,
                    "selected_identity": {
                        "python": {"executable": sys.executable}
                    },
                    "environment_fingerprint_sha256": environment_hash,
                    "required_modules": ["torch", "transformers"],
                    "effective_environment": {},
                },
            }
            authority = {
                "reference_gate": gate,
                "paths": {
                    "source_reference": reference_path,
                    "reference_gate": gate_path,
                },
            }
            resolved, errors = reference_gate_python_execution(authority)
            self.assertEqual(errors, [])
            self.assertEqual(Path(resolved["executable"]).resolve(), Path(sys.executable).resolve())

            gate["execution"]["argv"][0] = str(root / "other-python")
            _resolved, errors = reference_gate_python_execution(authority)
            self.assertIn("identities disagree", " ".join(errors))
