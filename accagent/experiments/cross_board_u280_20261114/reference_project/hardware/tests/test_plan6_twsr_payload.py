import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import torch

from hardware.export_plan6_twsr_payload import (
    export_recurrent_core_payload,
    pack_twsr_matrix,
)
from hardware.plan6_models import PLAN6_MODELS


class Plan6TWSRPayloadTests(unittest.TestCase):
    def make_source(self):
        source = torch.empty((2, 512), dtype=torch.bfloat16)
        source[0] = torch.where(torch.arange(512) % 2 == 0, 0.5, -0.5)
        source[1] = torch.where(torch.arange(512) % 2 == 0, 0.25, -0.25)
        indices = torch.tensor([0, 1, 2, 512, 513, 514])
        source.view(-1)[indices] = torch.tensor(
            [0.25, -0.25, 0.5, 0.125, -0.125, 0.25], dtype=torch.bfloat16
        )
        return source, indices

    def test_packs_sparse_ternary_weights_and_round_gamma(self):
        source, indices = self.make_source()
        beta = torch.ones((4, 2), dtype=torch.bfloat16)

        packed, gamma, record = pack_twsr_matrix(
            source, source, indices, beta, PLAN6_MODELS["ouro14"]["quantization"]
        )

        self.assertEqual(len(packed), 2 * 2 * 64)
        self.assertEqual(gamma.shape, (4, 2))
        np.testing.assert_array_equal(gamma, np.tile(np.array([0.5, 0.25], dtype=np.float16), (4, 1)))
        self.assertEqual(record["candidate_sparse_coordinates"], 6)
        self.assertEqual(record["encoded_sparse_slots"], 6)

    def test_rejects_sparse_coordinates_outside_fixed_fraction(self):
        source = torch.ones((2, 512), dtype=torch.bfloat16)
        with self.assertRaisesRegex(ValueError, "candidate fraction"):
            pack_twsr_matrix(
                source,
                source,
                torch.tensor([0]),
                torch.ones((4, 2)),
                PLAN6_MODELS["ouro14"]["quantization"],
            )

    def test_exports_weights_gamma_and_core_auxiliary_parameters(self):
        source, indices = self.make_source()
        model = torch.nn.Module()
        model.model = torch.nn.Module()
        model.model.layers = torch.nn.ModuleList([torch.nn.Module()])
        model.model.layers[0].attn = torch.nn.Module()
        model.model.layers[0].attn.q_proj = torch.nn.Linear(
            512, 2, bias=True, dtype=torch.bfloat16
        )
        model.model.layers[0].norm = torch.nn.LayerNorm(2, dtype=torch.bfloat16)
        model.model.norm = torch.nn.LayerNorm(2, dtype=torch.bfloat16)
        with torch.no_grad():
            model.model.layers[0].attn.q_proj.weight.copy_(source)
        name = "model.layers.0.attn.q_proj"
        beta = torch.ones((4, 2), dtype=torch.bfloat16)

        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "ouro14_recurrent_core_twsr"
            result = export_recurrent_core_payload(
                "ouro14",
                model,
                {name: model.model.layers[0].attn.q_proj},
                {name: source},
                {name: (source.clone(), None)},
                {name: indices},
                {name: beta},
                {"samples": 128, "sequence_length": 512},
                output_dir,
            )
            manifest = json.loads((result / "manifest.json").read_text())

            self.assertEqual(result, output_dir)
            self.assertEqual((result / "weights.usw512").stat().st_size, 256)
            self.assertEqual((result / "gamma.fp16").stat().st_size, 16)
            self.assertGreater((result / "auxiliary.bf16").stat().st_size, 0)
            self.assertEqual(manifest["layers"][0]["name"], name)
            auxiliary_names = {row["name"] for row in manifest["auxiliary_parameters"]}
            self.assertIn(f"{name}.bias", auxiliary_names)
            self.assertIn("model.layers.0.norm.weight", auxiliary_names)
            self.assertIn("model.norm.weight", auxiliary_names)
            self.assertNotIn(f"{name}.weight", auxiliary_names)


if __name__ == "__main__":
    unittest.main()
