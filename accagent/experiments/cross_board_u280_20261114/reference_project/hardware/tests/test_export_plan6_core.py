import json
import unittest
from pathlib import Path

import numpy as np
import torch

from hardware.export_plan6_huginn_core import (
    build_huginn_linear_operator_map,
    make_linear_operator_views,
    make_rope_table,
    pack_twsr_matrix,
)
from hardware.pack_usw512 import unpack_matrix_from_usw512


class Plan6HuginnCoreExportTests(unittest.TestCase):
    def test_full_huginn_payload_dma_map_covers_every_linear_matrix(self):
        payload_dir = Path(__file__).resolve().parents[2] / "results/plan6/huginn_recurrent_core"
        manifest = json.loads((payload_dir / "manifest.json").read_text())
        views = build_huginn_linear_operator_map(manifest)
        self.assertEqual(len(views), 21)

        weight_sizes = {
            "weights.usw512": (payload_dir / "weights.usw512").stat().st_size,
            "adapter.usw512": (payload_dir / "adapter.usw512").stat().st_size,
        }
        gamma_sizes = {
            "gamma.fp16": (payload_dir / "gamma.fp16").stat().st_size,
            "adapter_gamma.fp16": (payload_dir / "adapter_gamma.fp16").stat().st_size,
        }
        per_block = {
            (view["command_id"], tuple(view["shape"]))
            for view in views if view["block_index"] == 0
        }
        self.assertEqual(per_block, {
            (3, (15840, 5280)),
            (9, (5280, 5280)),
            (21, (17920, 5280)),
            (22, (17920, 5280)),
            (15, (5280, 17920)),
        })

        for view in views:
            rows, columns = view["shape"]
            self.assertEqual(view["weight_bytes"], rows * ((columns + 255) // 256) * 64)
            self.assertLessEqual(
                view["weight_offset_bytes"] + view["weight_bytes"],
                weight_sizes[view["weight_file"]],
            )
            gamma_end = (
                view["gamma_offset_bytes"]
                + (view["rounds"] - 1) * view["gamma_recurrence_stride_bytes"]
                + view["gamma_row_offset"] * 2
                + view["gamma_bytes_per_recurrence"]
            )
            self.assertLessEqual(gamma_end, gamma_sizes[view["gamma_file"]])

    def test_adapter_twsr_payload_roundtrip_and_step_gamma(self):
        weight = torch.tensor([[0.5, -1.0, 0.75] + [2.0] * 253,
                               [-0.5, 0.0, 0.0] + [-3.0] * 253], dtype=torch.bfloat16)
        quantized = weight.clone()
        quantized[:, :3] = 0
        quantized[:, 3:] = torch.sign(quantized[:, 3:]) * torch.tensor(
            [[2.0], [3.0]], dtype=torch.bfloat16
        )
        sparse_indices = torch.tensor([0, 1, 256], dtype=torch.int32)
        quantized.view(-1)[sparse_indices] = weight.view(-1)[sparse_indices]
        beta = torch.stack((torch.full((2,), 1.25), torch.full((2,), 0.80))).repeat(16, 1)

        packed, gamma, ternary, alpha, encoded_sparse_slots = pack_twsr_matrix(
            weight, quantized, sparse_indices, beta
        )
        decoded_ternary, decoded_sparse = unpack_matrix_from_usw512(packed, 2, 256)

        np.testing.assert_array_equal(decoded_ternary, ternary)
        self.assertEqual(encoded_sparse_slots, 3)
        self.assertEqual(np.count_nonzero(decoded_sparse), 3)
        self.assertEqual(gamma.shape, (32, 2))
        np.testing.assert_allclose(gamma[0], [2.5, 3.75], rtol=0, atol=0)
        np.testing.assert_allclose(gamma[-1], [1.6, 2.4], rtol=0, atol=1e-3)
        np.testing.assert_allclose(alpha, [2.0, 3.0])

    def test_rope_table_matches_position_pair_layout(self):
        table = make_rope_table(head_dim=4, context=2)

        self.assertEqual(table.shape, (2, 2, 2))
        np.testing.assert_array_equal(table[0, :, 0], [1.0, 1.0])
        np.testing.assert_array_equal(table[0, :, 1], [0.0, 0.0])
        self.assertGreater(float(table[1, 0, 1]), 0.0)

    def test_huginn_fused_gate_up_payload_has_two_zero_copy_views(self):
        fused = {
            "name": "transformer.core_block.0.mlp.fc",
            "shape": [35840, 5280],
            "windows_per_row": 21,
            "rounds": 32,
            "usw512_offset_bytes": 1000,
            "gamma_fp16_offset_bytes": 2000,
            "weight_file": "weights.usw512",
            "gamma_file": "gamma.fp16",
        }
        gate, up = make_linear_operator_views(fused)
        self.assertEqual([gate["name"], up["name"]], [
            "transformer.core_block.0.mlp.fc.gate_proj",
            "transformer.core_block.0.mlp.fc.up_proj",
        ])
        self.assertEqual(gate["shape"], [17920, 5280])
        self.assertEqual(gate["weight_offset_bytes"], 1000)
        self.assertEqual(up["weight_offset_bytes"], 1000 + 17920 * 21 * 64)
        self.assertEqual(gate["gamma_offset_bytes"], up["gamma_offset_bytes"])
        self.assertEqual((gate["gamma_row_offset"], up["gamma_row_offset"]), (0, 17920))
        self.assertEqual(gate["gamma_row_stride_elements"], 35840)
        self.assertEqual((gate["command_id"], up["command_id"]), (21, 22))
        self.assertEqual(gate["gamma_recurrence_stride_bytes"], 35840 * 2)


if __name__ == "__main__":
    unittest.main()
