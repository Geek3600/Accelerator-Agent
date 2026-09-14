from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

import torch

from accagent.framework.semantic_runtime import (
    materialize_composite_runtime_stream,
    materialize_semantic_runtime_constants,
    sha256_file,
    tensor_sha256,
)
from scripts.verification.semantic_testbench_generator import (
    semantic_harness_tb,
    stream_metadata_contract,
    validate_harness_weight_hashes,
)


class SemanticRuntimeContractTest(TestCase):
    def runtime_record(self, path: Path, tensor: torch.Tensor) -> dict:
        torch.save(tensor, path)
        return {
            "path": str(path),
            "file_sha256": sha256_file(path),
            "tensor_sha256": tensor_sha256(tensor),
            "dtype": str(tensor.dtype),
            "shape": list(tensor.shape),
        }

    def test_adapter_declared_runtime_tensors_are_packed_in_explicit_order(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            position = torch.tensor([[0, 1]], dtype=torch.int64)
            cosine = torch.tensor([[[1.0, 2.0], [3.0, 4.0]]], dtype=torch.float32)
            reference = {
                "reference": {
                    "semantic_runtime_inputs": {
                        "position_ids": self.runtime_record(root / "position.pt", position),
                        "rope_cos": self.runtime_record(root / "cos.pt", cosine),
                    }
                }
            }
            adapter = {
                "semantic_runtime_streams": {
                    "self_attention": {
                        "source_order": ["position_ids", "rope_cos"],
                        "targets": {
                            "position_ids": {
                                "target_id": "attention.position_ids",
                                "semantic_role": "position_ids",
                                "storage_dtype": "uint32",
                                "source_axis_order": ["batch", "token"],
                                "drop_singleton_axes": [0],
                                "address_formula": "token",
                                "sharing": "one position per token",
                            },
                            "rope_cos": {
                                "target_id": "attention.rope.cos",
                                "semantic_role": "rotary_cosine",
                                "storage_dtype": "fp16",
                                "source_axis_order": ["batch", "token", "head_dimension"],
                                "drop_singleton_axes": [0],
                                "address_formula": "token * head_dimension_count + head_dimension",
                                "sharing": "shared across attention heads",
                            },
                        },
                    }
                }
            }

            contract = materialize_semantic_runtime_constants(
                reference,
                adapter,
                root / "out",
                semantic_adapter_sha256="a" * 64,
            )

            self.assertEqual(contract["status"], "pass")
            stream = contract["streams"][0]
            self.assertEqual([row["source_key"] for row in stream["targets"]], ["position_ids", "rope_cos"])
            self.assertEqual(stream["targets"][0]["logical_axis_order"], ["token"])
            self.assertEqual(stream["targets"][1]["logical_shape"], [2, 2])
            words = Path(stream["stream"]["path"]).read_text(encoding="ascii").splitlines()
            self.assertEqual(words[:2], ["00000000", "00000001"])
            self.assertEqual(words[2], "40003c00")
            self.assertEqual(words[3], "44004200")

    def test_source_order_must_cover_exactly_the_declared_targets(self) -> None:
        with TemporaryDirectory() as temp_dir:
            contract = materialize_semantic_runtime_constants(
                {"reference": {"semantic_runtime_inputs": {}}},
                {
                    "semantic_runtime_streams": {
                        "self_attention": {
                            "source_order": ["rope_cos"],
                            "targets": {"rope_cos": {}, "rope_sin": {}},
                        }
                    }
                },
                Path(temp_dir),
                semantic_adapter_sha256="b" * 64,
            )

            self.assertEqual(contract["status"], "fail")
            self.assertIn("source_order/targets disagree", " ".join(contract["blockers"]))

    def test_composite_runtime_stream_preserves_stage_order_and_zero_segments(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            position = torch.tensor([[3, 4]], dtype=torch.int64)
            reference = {
                "reference": {
                    "semantic_runtime_inputs": {
                        "position_ids": self.runtime_record(root / "position.pt", position),
                    }
                }
            }
            adapter = {
                "semantic_runtime_streams": {
                    "self_attention": {
                        "source_order": ["position_ids"],
                        "targets": {
                            "position_ids": {
                                "target_id": "attention.position_ids",
                                "semantic_role": "position_ids",
                                "storage_dtype": "uint32",
                                "source_axis_order": ["batch", "token"],
                                "drop_singleton_axes": [0],
                            }
                        },
                    }
                }
            }
            runtime = materialize_semantic_runtime_constants(
                reference,
                adapter,
                root / "runtime",
                semantic_adapter_sha256="a" * 64,
            )["streams"][0]

            composite = materialize_composite_runtime_stream(
                root / "composite.memh",
                [
                    {"stage_id": "stage_00", "op": "rms_norm", "runtime_contract": None},
                    {"stage_id": "stage_01", "op": "self_attention", "runtime_contract": runtime},
                ],
            )

            self.assertEqual(composite["stage_order"], ["stage_00", "stage_01"])
            self.assertEqual(composite["stage_segments"][0]["global_stream_range"]["word_count"], 0)
            self.assertEqual(composite["stage_segments"][1]["global_stream_range"]["word_offset"], 0)
            self.assertEqual((root / "composite.memh").read_text(encoding="ascii").splitlines(), ["00000003", "00000004"])

    def test_runtime_constant_stage_requires_matching_contract_and_loader(self) -> None:
        runtime_contract = {"contract_sha256": "c" * 64}
        harness = {
            "runtime_constant_contract_sha256": "c" * 64,
            "interface": {
                "runtime_loader": {
                    "valid_port": "runtime_valid",
                    "ready_port": "runtime_ready",
                    "data_port": "runtime_data",
                    "data_width_bits": 32,
                    "addr_port": "runtime_addr",
                    "addr_width_bits": 16,
                    "last_port": "runtime_last",
                }
            },
        }

        self.assertEqual(
            validate_harness_weight_hashes(harness, [], runtime_constant_stream=runtime_contract),
            [],
        )
        harness["runtime_constant_contract_sha256"] = "wrong"
        self.assertIn(
            "runtime-constant contract hash",
            " ".join(validate_harness_weight_hashes(harness, [], runtime_constant_stream=runtime_contract)),
        )

    def test_semantic_testbench_loads_runtime_constants_before_stimulus(self) -> None:
        harness = {
            "top_module": "RuntimeHarness",
            "interface": {
                "clock_port": "clock",
                "reset_port": "reset",
                "inputs": [
                    {
                        "valid_port": "in_valid",
                        "ready_port": "in_ready",
                        "data_port": "in_data",
                        "data_width_bits": 32,
                    }
                ],
                "output": {
                    "valid_port": "out_valid",
                    "ready_port": "out_ready",
                    "data_port": "out_data",
                    "data_width_bits": 32,
                },
                "runtime_loader": {
                    "valid_port": "runtime_valid",
                    "ready_port": "runtime_ready",
                    "data_port": "runtime_data",
                    "data_width_bits": 32,
                    "addr_port": "runtime_addr",
                    "addr_width_bits": 8,
                    "last_port": "runtime_last",
                },
                "weight_loader": {
                    "valid_port": "weight_valid",
                    "ready_port": "weight_ready",
                    "data_port": "weight_data",
                    "data_width_bits": 32,
                    "addr_port": "weight_addr",
                    "addr_width_bits": 8,
                    "last_port": "weight_last",
                },
            },
        }
        testbench = semantic_harness_tb(
            tb_module="runtime_tb",
            harness=harness,
            input_vectors=[{"path": "/tmp/input.memh", "bits": 32, "lanes": 1, "beats": 1}],
            expected_output={"bits": 32, "lanes": 1, "beats": 1},
            output_path=Path("/tmp/output.memh"),
            weight_stream={"path": "/tmp/weights.memh", "word_count": 3},
            runtime_stream={"path": "/tmp/runtime.memh", "word_count": 2},
        )

        self.assertIn('$value$plusargs("INPUT_0_MEMH=%s", input_path_0)', testbench)
        self.assertIn('$value$plusargs("WEIGHT_MEMH=%s", weight_path)', testbench)
        self.assertIn('$value$plusargs("RUNTIME_MEMH=%s", runtime_path)', testbench)
        self.assertIn("while (weight_accepted < 3) begin", testbench)
        self.assertIn("weight_last = weight_accepted == 2;", testbench)
        self.assertIn("weight_valid = 0;", testbench)
        self.assertIn("real-weight loader made no progress", testbench)
        self.assertIn("while (runtime_accepted < 2) begin", testbench)
        self.assertIn("$readmemh(runtime_path, runtime_mem);", testbench)
        self.assertIn('$value$plusargs("OUTPUT_MEMH=%s", output_path)', testbench)
        self.assertIn("runtime_last = runtime_accepted == 1;", testbench)
        self.assertIn("runtime_valid = 0;", testbench)
        self.assertIn("runtime-constant loader made no progress", testbench)
        self.assertLess(
            testbench.index("real-weight load did not complete"),
            testbench.index("while (runtime_accepted < 2) begin"),
        )
        self.assertLess(
            testbench.index("runtime-constant load did not complete"),
            testbench.index("while (cycles < 10000000"),
        )
        terminal_flush_wait = testbench.rindex("    @(negedge clock);")
        self.assertLess(testbench.index("semantic harness timeout or output-shape mismatch"), terminal_flush_wait)
        self.assertLess(terminal_flush_wait, testbench.index("    $fclose(output_fd);"))
        self.assertLess(testbench.index("    $fclose(output_fd);"), testbench.index("PASS semantic harness"))
        self.assertLess(testbench.index("PASS semantic harness"), testbench.index("    $finish;"))

    def test_stream_metadata_contract_is_shape_driven_and_model_independent(self) -> None:
        contract = stream_metadata_contract()

        self.assertEqual(
            contract["derived_values"]["beats_per_logical_vector"],
            "tensor_shape[-1] / lanes",
        )
        self.assertEqual(
            contract["internal_streambeat_fields"]["addr"],
            "accepted_beat_index in row-major global-beat order",
        )
        self.assertIn("valid && ready", contract["transaction_order"][-1])
        self.assertNotIn("qwen", str(contract).lower())
        self.assertNotIn("opt", str(contract).lower())
