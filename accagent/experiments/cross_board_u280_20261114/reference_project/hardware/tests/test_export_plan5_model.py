import json
import hashlib
import tempfile
import unittest
from pathlib import Path

import numpy as np
import torch

from hardware.export_plan5_model import annotate_payload_manifest, preflight_model, run_export
from hardware.pack_usw512 import unpack_matrix_from_usw512


BF16 = torch.bfloat16


def checkpoint_inputs(columns, dense, sparse):
    weight = torch.zeros((1, columns), dtype=BF16)
    for index, value in dense.items():
        weight[0, index] = value
    indices = torch.tensor(list(sparse), dtype=torch.int32)
    values = torch.tensor(list(sparse.values()), dtype=BF16)
    for index, value in sparse.items():
        weight[0, index] = value
    return weight, {"indices": indices, "values": values}


class Plan5ModelExportTests(unittest.TestCase):
    def test_compatible_layer_roundtrips_to_atomic_payload(self):
        weight, retained = checkpoint_inputs(256, {0: 1.0, 2: -1.0}, {6: 3.0, 255: -4.0})
        bank = {"core.layer": (weight, None)}
        masks = {"core.layer": retained}
        beta = {"core.layer": torch.tensor([[1.0], [2.0]], dtype=BF16)}
        report, alpha = preflight_model(bank, masks, beta, expected_layers=1)
        self.assertTrue(report["compatible"])
        self.assertEqual(report["totals"]["reconstruction_mismatch_rows"], 0)
        self.assertEqual(report["totals"]["q4_12_exact_slots"], 2)

        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "package"
            plan3_path = Path(directory) / "plan3.pt"
            beta_path = Path(directory) / "beta.pt"
            probe_path = Path(directory) / "probe.pt"
            report_path = Path(directory) / "preflight.json"
            torch.save({"bank": bank}, plan3_path)
            torch.save({"tf_norm_step_scale": beta}, beta_path)
            torch.save({"retained": {("gptq", -1): masks}}, probe_path)
            result = run_export(plan3_path, beta_path, probe_path, report_path,
                                output_dir, expected_layers=1)
            self.assertTrue(result["compatible"])
            manifest = annotate_payload_manifest(output_dir / "manifest.json", report_path)
            self.assertEqual((output_dir / "weights.usw512").stat().st_size, 64)
            self.assertEqual((output_dir / "gamma.fp16").stat().st_size, 4)
            self.assertEqual(manifest["layers"][0]["shape"], [1, 256])
            self.assertEqual(manifest["layers"][0]["quantization"]["encoded_sparse_slots"], 2)
            self.assertEqual(
                manifest["quantization"]["method"],
                "pre_sparse_ridge_twn_sparse005_tf_norm_step_scale",
            )
            self.assertEqual(manifest["quantization"]["group_size"], -1)
            self.assertEqual(
                manifest["quantization"]["source_checkpoints"]["plan3_checkpoint"]["sha256"],
                hashlib.sha256(plan3_path.read_bytes()).hexdigest(),
            )
            self.assertTrue(report_path.exists())

    def test_overfull_window_folds_excess_and_writes_payload(self):
        sparse = {index: 0.5 for index in (4, 20, 40, 60, 80, 100)}
        weight, retained = checkpoint_inputs(1024, {0: 1.0}, sparse)
        bank = {"core.layer": (weight, None)}
        masks = {"core.layer": retained}
        beta = {"core.layer": torch.ones((2, 1), dtype=BF16)}

        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "package"
            report_path = Path(directory) / "preflight.json"
            plan3_path = Path(directory) / "plan3.pt"
            beta_path = Path(directory) / "beta.pt"
            probe_path = Path(directory) / "probe.pt"
            torch.save({"bank": bank}, plan3_path)
            torch.save({"tf_norm_step_scale": beta}, beta_path)
            torch.save({"retained": {("gptq", -1): masks}}, probe_path)
            result = run_export(plan3_path, beta_path, probe_path, report_path,
                                output_dir, expected_layers=1)

            self.assertTrue(result["compatible"])
            self.assertEqual(result["totals"]["windows_over_capacity"], 1)
            self.assertEqual(result["totals"]["coordinates_over_capacity"], 2)
            self.assertEqual(result["totals"]["coordinates_folded_to_ternary"], 2)
            self.assertEqual(result["totals"]["folded_ternary_zero"], 2)
            self.assertEqual(result["totals"]["q4_12_checked_slots"], 4)
            packed = (output_dir / "weights.usw512").read_bytes()
            decoded_ternary, decoded_sparse = unpack_matrix_from_usw512(packed, 1, 1024)
            self.assertTrue(decoded_ternary[0, 0])
            self.assertEqual(np.count_nonzero(decoded_sparse), 4)
            np.testing.assert_array_equal(np.flatnonzero(decoded_sparse[0]), [4, 20, 40, 60])
            self.assertTrue(report_path.exists())

    def test_nonexact_q4_12_values_are_rounded_and_exportable(self):
        weight, retained = checkpoint_inputs(256, {0: 3.0, 2: -3.0}, {6: 1.0, 255: -1.0})
        report, _ = preflight_model(
            {"core.layer": (weight, None)}, {"core.layer": retained},
            {"core.layer": torch.ones((2, 1), dtype=BF16)}, expected_layers=1
        )
        self.assertTrue(report["compatible"])
        self.assertEqual(report["totals"]["q4_12_inexact_slots"], 2)
        self.assertEqual(report["totals"]["q4_12_saturated_slots"], 0)


if __name__ == "__main__":
    unittest.main()
