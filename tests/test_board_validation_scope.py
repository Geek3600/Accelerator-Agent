import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from accagent.framework.board_validation_scope import (
    FULL_MODEL_MODE,
    PREFIX_MODEL_MODE,
    SINGLE_LAYER_MODE,
    BoardValidationScopeError,
    resolve_board_validation_scope,
    validation_scope_record_errors,
    validation_scope_from_plan,
)
from scripts.verification.qwen_hierarchical_check import check_multilayer_pipeline


class BoardValidationScopeTest(TestCase):
    def test_configurable_count_derives_prefix_and_lifecycle_policy(self) -> None:
        scope = resolve_board_validation_scope(
            {
                "acceptance_policy": {
                    "board_validation_mode": PREFIX_MODEL_MODE,
                    "board_validation_layer_count": 7,
                }
            },
            {"num_layers": 24},
        )

        self.assertEqual(scope.layer_indices, tuple(range(7)))
        self.assertEqual(scope.reference_output_layer_index, 6)
        self.assertTrue(scope.requires_next_layer_prefetch)
        self.assertFalse(scope.covers_full_model)

    def test_count_one_keeps_terminal_schedule_without_layer_constants(self) -> None:
        scope = resolve_board_validation_scope(
            {
                "acceptance_policy": {
                    "board_validation_mode": PREFIX_MODEL_MODE,
                    "board_validation_layer_count": 1,
                }
            },
            {"num_layers": 24},
        )

        self.assertEqual(scope.layer_indices, (0,))
        self.assertFalse(scope.requires_next_layer_prefetch)

    def test_full_and_legacy_single_modes_remain_supported(self) -> None:
        full = resolve_board_validation_scope(
            {"acceptance_policy": {"board_validation_mode": FULL_MODEL_MODE}},
            {"num_layers": 3},
        )
        single = resolve_board_validation_scope(
            {"acceptance_policy": {"board_validation_mode": SINGLE_LAYER_MODE}},
            {"num_layers": 3},
        )

        self.assertEqual(full.layer_indices, (0, 1, 2))
        self.assertEqual(single.layer_indices, (0,))

    def test_plan_scope_uses_configurable_prefix_for_partial_layer_order(self) -> None:
        scope = validation_scope_from_plan(
            {"image": {"layer_order": [0, 1, 2]}},
            model_layer_count=24,
        )

        self.assertEqual(scope.mode, PREFIX_MODEL_MODE)
        self.assertEqual(scope.layer_indices, (0, 1, 2))

    def test_count_and_indices_must_agree(self) -> None:
        with self.assertRaisesRegex(BoardValidationScopeError, "conflicts"):
            resolve_board_validation_scope(
                {
                    "acceptance_policy": {
                        "board_validation_mode": PREFIX_MODEL_MODE,
                        "board_validation_layer_count": 2,
                        "board_validation_layer_indices": [0, 1, 2],
                    }
                },
                {"num_layers": 24},
            )

    def test_record_requires_every_configured_layer_not_the_whole_model(self) -> None:
        scope = resolve_board_validation_scope(
            {
                "acceptance_policy": {
                    "board_validation_mode": PREFIX_MODEL_MODE,
                    "board_validation_layer_count": 1,
                }
            },
            {"num_layers": 24},
        )
        record = {
            "status": "pass",
            "accelerator_scope": "transformer_blocks_only",
            "model_layer_count": 24,
            "validation_layer_indices": [0],
            "bound_layer_count": 1,
            "all_target_layers": False,
        }

        self.assertEqual(
            validation_scope_record_errors(
                scope,
                record,
                allowed_statuses={"pass"},
                require_accelerator_scope=True,
            ),
            [],
        )
        record["all_target_layers"] = True
        self.assertIn(
            "record all_target_layers does not match whether the current workload covers the full model",
            validation_scope_record_errors(scope, record),
        )

    def test_board_pipeline_gate_accepts_a_complete_configured_prefix(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            source = run_dir / "generated" / "board_integration" / "adapter.sv"
            source.parent.mkdir(parents=True)
            source.write_text("module adapter; endmodule\n", encoding="utf-8")
            import hashlib

            source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
            (run_dir / "input").mkdir(parents=True)
            (run_dir / "input" / "model_config.json").write_text(
                json.dumps({"num_layers": 24}), encoding="utf-8"
            )
            (run_dir / "input" / "task_card.json").write_text(
                json.dumps(
                    {
                        "acceptance_policy": {
                            "board_validation_mode": PREFIX_MODEL_MODE,
                            "board_validation_layer_count": 1,
                        }
                    }
                ),
                encoding="utf-8",
            )
            catalog = run_dir / "verification" / "model_weights" / "transformer_block_weight_catalog.json"
            catalog.parent.mkdir(parents=True)
            catalog.write_text(
                json.dumps(
                    {
                        "scope_coverage_complete": True,
                        "tensors": [
                            {"layer_index": 0, "source_slice_sha256": "a" * 64},
                            {"layer_index": 1, "source_slice_sha256": "b" * 64},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            binding = run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
            binding.parent.mkdir(parents=True)
            binding.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "accelerator_scope": "transformer_blocks_only",
                        "scope_coverage_complete": True,
                        "model_layer_count": 24,
                        "validation_layer_indices": [0],
                        "bound_layer_count": 1,
                        "all_target_layers": False,
                        "board_consumed_tensor_hashes": ["a" * 64],
                        "multilayer_harness": {
                            "source_files": [{"path": str(source), "sha256": source_hash}]
                        },
                    }
                ),
                encoding="utf-8",
            )

            report = check_multilayer_pipeline(run_dir)

        self.assertEqual(report["status"], "pass")
