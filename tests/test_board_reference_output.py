from unittest import TestCase

from accagent.framework.board_reference_output import select_board_reference_output
from accagent.framework.board_validation_scope import resolve_board_validation_scope


class BoardReferenceOutputTest(TestCase):
    def setUp(self) -> None:
        self.reference = {
            "reference": {
                "full_model_output": {
                    "path": "/reference/full.pt",
                    "file_sha256": "f" * 64,
                    "tensor_sha256": "e" * 64,
                    "shape": [1, 2, 3],
                    "dtype": "torch.float32",
                    "source_capture": "decoder_layer_4",
                },
                "layer_output_records": [
                    {
                        "module": f"decoder_layer_{index}",
                        "tensor_path": f"/reference/layer_{index}.pt",
                        "tensor_file_sha256": f"{index}" * 64,
                        "output_sha256": f"{index + 1}" * 64,
                        "output_shape": [1, 2, 3],
                        "output_dtype": "torch.float32",
                    }
                    for index in range(5)
                ],
            }
        }

    def test_partial_prefix_selects_its_terminal_layer_capture(self) -> None:
        scope = resolve_board_validation_scope(
            {
                "acceptance_policy": {
                    "board_validation_mode": "configurable_prefix_pipeline_liveness",
                    "board_validation_layer_count": 3,
                }
            },
            {"num_layers": 5},
        )

        selected = select_board_reference_output(self.reference, scope)

        self.assertEqual(selected["reference_kind"], "layer_output_record")
        self.assertEqual(selected["source_capture"], "decoder_layer_2")
        self.assertEqual(selected["path"], "/reference/layer_2.pt")
        self.assertEqual(selected["payload_key"], "output")

    def test_full_prefix_retains_the_model_final_output_capture(self) -> None:
        scope = resolve_board_validation_scope(
            {"acceptance_policy": {"board_validation_mode": "full_model_pipeline_liveness"}},
            {"num_layers": 5},
        )

        selected = select_board_reference_output(self.reference, scope)

        self.assertEqual(selected["reference_kind"], "full_model_output")
        self.assertEqual(selected["path"], "/reference/full.pt")
        self.assertIsNone(selected["payload_key"])
