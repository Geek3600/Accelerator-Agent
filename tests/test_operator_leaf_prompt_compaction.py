from __future__ import annotations

import json
import unittest

from accagent.framework.stage_llm import (
    _canonical_json_sha256,
    _compact_operator_leaf_repair_bundle,
    _operator_leaf_stage_ids,
    compact_verification_capability_repair_package,
)


class OperatorLeafPromptCompactionTest(unittest.TestCase):
    def test_capability_prompt_keeps_only_authorized_run_source_bodies(self) -> None:
        public_template = "templates/Norm.scala"
        run_norm = "run/generated/chisel/src/main/scala/spatialaccagent/templates/Norm.scala"
        run_attention = "run/generated/chisel/src/main/scala/spatialaccagent/templates/Attention.scala"
        harness_root = "run/generated/chisel/src/main/scala/spatialaccagent/semantic_harness"
        harness_source = f"{harness_root}/NormHarness.scala"
        source = "class Norm {\n" + ("  // current source line\n" * 4000) + "}\n"
        package = {
            "verification_scope": "operator_leaf_closure",
            "repair_kind": "semantic_loader_harness_binding",
            "repair_source_bundle": {
                "documents": [
                    {
                        "path": public_template,
                        "sha256": "a" * 64,
                        "content": source,
                        "content_preservation": "full source required by the previous broad package",
                    },
                    {
                        "path": run_norm,
                        "sha256": "b" * 64,
                        "content": source,
                        "content_preservation": "authorized current source",
                    },
                    {
                        "path": run_attention,
                        "sha256": "c" * 64,
                        "content": source,
                        "content_preservation": "unrelated full source",
                    },
                    {
                        "path": harness_source,
                        "sha256": "d" * 64,
                        "content": source,
                        "content_preservation": "editable semantic harness",
                    },
                ],
                "editable_contract": {
                    "read_only_template_sources": [
                        public_template,
                        run_norm,
                        run_attention,
                    ],
                    "approved_bounded_template_repair_exact_files": [run_norm],
                    "allowed_create_or_replace_roots": [harness_root],
                    "allowed_exact_files": [],
                    "localized_allowed_exact_files": [],
                },
                "generated_module_inventory": [],
            },
        }

        compacted = compact_verification_capability_repair_package(package)
        documents = compacted["repair_source_bundle"]["documents"]
        by_path = {row["path"]: row for row in documents}

        self.assertEqual(by_path[run_norm]["content"], source)
        self.assertEqual(by_path[harness_source]["content"], source)
        self.assertNotIn("content", by_path[public_template])
        self.assertNotIn("content", by_path[run_attention])
        self.assertEqual(by_path[public_template]["sha256"], "a" * 64)
        self.assertEqual(by_path[run_attention]["sha256"], "c" * 64)
        self.assertLess(
            len(json.dumps(compacted, separators=(",", ":"))),
            len(json.dumps(package, separators=(",", ":"))) * 3 // 5,
        )

    def test_large_q31_channels_survive_repeated_compaction(self) -> None:
        channels = [
            {
                "binary_shift": index % 31,
                "multiplier_unsigned_q31": 100000 + index,
            }
            for index in range(96)
        ]
        bundle = {
            "documents": [
                {
                    "path": "verification/semantic_testbench/dut_weight_binding_requirements.json",
                    "sha256": "a" * 64,
                    "json_content": {
                        "schema_version": "spatialaccagent.dut_weight_binding_requirements.v1",
                        "status": "requirements",
                        "connected_weight_stream_contract": {
                            "schema_version": "spatialaccagent.connected_weight_stream_contract.v1",
                            "status": "ready",
                            "stage_segments": [
                                {
                                    "stage_id": "stage_05_mlp_gate_proj",
                                    "stage_index": 5,
                                    "op": "mlp_gate_proj",
                                    "targets": [
                                        {
                                            "target_id": "linear.weight",
                                            "target_kind": "weight",
                                            "port": "weight",
                                            "source_tensor_hashes": ["b" * 64],
                                            "scale_metadata": {
                                                "representation": "q31",
                                                "payload": channels,
                                            },
                                            "materialized_target": {
                                                "quantization": {
                                                    "scale_fixed_point": {
                                                        "representation": "q31",
                                                        "fractional_bits": 31,
                                                        "channels": channels,
                                            },
                                                }
                                            },
                                        }
                                    ],
                                }
                            ],
                        },
                    },
                },
                {
                    "path": "accagent/framework/stage_repair_execute.py",
                    "content": "framework source without a pipeline stage id",
                },
            ]
        }

        for _ in range(2):
            _compact_operator_leaf_repair_bundle(
                bundle,
                stage_ids=_operator_leaf_stage_ids(bundle["documents"]),
                read_only_template_paths=set(),
            )

        document = bundle["documents"][0]["json_content"]
        payloads = document["required_scale_payloads"]
        self.assertEqual(bundle["operator_leaf_prompt_projection"]["current_stage_ids"], [])
        self.assertEqual(
            _operator_leaf_stage_ids(
                [{"path": "verification/stages/stage_05_mlp_gate_proj/harness.sv"}]
            ),
            {"stage_05_mlp_gate_proj"},
        )
        self.assertEqual(len(payloads), 1)
        self.assertEqual(payloads[0]["channel_encoding"], "ordered_field_value_rows_v1")
        self.assertEqual(
            payloads[0]["channel_fields"],
            ["binary_shift", "multiplier_unsigned_q31"],
        )
        self.assertEqual(
            payloads[0]["scale_fixed_point"]["channels"],
            [[row["binary_shift"], row["multiplier_unsigned_q31"]] for row in channels],
        )
        self.assertEqual(payloads[0]["channel_count"], len(channels))
        self.assertEqual(payloads[0]["scale_fixed_point"]["fractional_bits"], 31)
        self.assertEqual(payloads[0]["channels_sha256"], _canonical_json_sha256(channels))
        compact_metadata = payloads[0]["scale_metadata"]["payload"]
        self.assertEqual(compact_metadata["item_count"], len(channels))
        self.assertEqual(
            compact_metadata["projection"], "hash_bound_array_summary"
        )
        self.assertTrue(compact_metadata["full_payload_remains_on_disk"])
        self.assertLess(
            len(json.dumps(payloads[0], separators=(",", ":"))),
            len(json.dumps(channels, separators=(",", ":"))),
        )


if __name__ == "__main__":
    unittest.main()
