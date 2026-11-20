import json
from pathlib import Path
import unittest

from hardware.plan6_models import PLAN6_MODELS


ROOT = Path(__file__).resolve().parents[2]
HF_CACHE = Path("/home/remote/.cache/huggingface/hub")
OURO_CONFIG = HF_CACHE / (
    "models--ByteDance--Ouro-1.4B/snapshots/"
    "574fa66cb8bf5abdc979642d01cf2b79b16bfab1/config.json"
)
DORY_CONFIG = HF_CACHE / (
    "models--nvidia--NVIDIA-Nemotron-Labs-Dory1.0-4B-BF16/snapshots/"
    "b366b87f762ea334ba3eb55912031baba1515810/config.json"
)


def read_json(path):
    if not path.is_file():
        raise FileNotFoundError(f"pinned model config is missing: {path}")
    return json.loads(path.read_text())


class Plan6ModelConfigTests(unittest.TestCase):
    def test_huginn_manifest_matches_plan6_dimensions(self):
        manifest_path = ROOT / "results/plan6/huginn_recurrent_core/manifest.json"
        manifest = read_json(manifest_path)["model"]
        expected = PLAN6_MODELS["huginn"]

        self.assertEqual(manifest["hidden_size"], expected["hidden_size"])
        self.assertEqual(manifest["intermediate_size"], expected["intermediate_size"])
        self.assertEqual(manifest["core_blocks"], expected["core_blocks"])
        self.assertEqual(manifest["recurrences"], expected["recurrences"])
        self.assertEqual(manifest["head_dim"], expected["head_dim"])

    def test_ouro_pinned_config_matches_plan6_dimensions(self):
        config = read_json(OURO_CONFIG)
        expected = PLAN6_MODELS["ouro14"]

        self.assertEqual(config["hidden_size"], expected["hidden_size"])
        self.assertEqual(config["intermediate_size"], expected["intermediate_size"])
        self.assertEqual(config["num_hidden_layers"], expected["core_blocks"])
        self.assertEqual(config["total_ut_steps"], expected["recurrences"])
        self.assertEqual(expected["runtime_overrides"]["total_ut_steps"], expected["recurrences"])
        self.assertEqual(config["num_attention_heads"] * config["head_dim"], expected["query_size"])
        self.assertEqual(config["num_key_value_heads"] * config["head_dim"], expected["kv_size"])

    def test_dory_pinned_config_matches_plan6_dimensions_and_mask(self):
        config = read_json(DORY_CONFIG)
        expected = PLAN6_MODELS["dory4b"]
        recurrent_start = config["n_input_layers"]
        recurrent_stop = recurrent_start + config["n_recurrent_layers"]
        recurrent_types = config["layer_types"][recurrent_start:recurrent_stop]

        self.assertEqual(config["hidden_size"], expected["hidden_size"])
        self.assertEqual(config["intermediate_size"], expected["intermediate_size"])
        self.assertEqual(config["n_input_layers"], expected["input_sublayers"])
        self.assertEqual(config["n_recurrent_layers"], expected["recurrent_sublayers"])
        self.assertEqual(config["n_output_layers"], expected["output_sublayers"])
        self.assertEqual(config["n_recurrent_layers"] // 2, expected["core_blocks"])
        self.assertEqual(config["n_recurrent_loops"], 2)
        self.assertEqual(expected["runtime_overrides"]["n_recurrent_loops"], expected["recurrences"])
        self.assertEqual(expected["runtime_overrides"]["recurrent_kv_cache_mode"], "per_loop")
        self.assertFalse(expected["has_pre_attention_norm"])
        self.assertFalse(expected["has_pre_ffn_norm"])
        self.assertEqual(config["num_attention_heads"] * config["head_dim"], expected["query_size"])
        self.assertEqual(config["num_key_value_heads"] * config["head_dim"], expected["kv_size"])
        self.assertEqual(len(recurrent_types), expected["recurrent_sublayers"])
        self.assertTrue(all(recurrent_types[index] == "mlp" for index in range(1, len(recurrent_types), 2)))

        full_attention_mask = 0
        for block in range(expected["core_blocks"]):
            if recurrent_types[block * 2] == "full_attention":
                full_attention_mask |= 1 << block
        self.assertEqual(full_attention_mask, expected["full_attention_mask"])
        self.assertEqual(config["sliding_window"], expected["sliding_window"])
        self.assertEqual(
            config["rope_parameters"]["full_attention"]["rope_theta"],
            expected["full_attention_rope_theta"],
        )
        self.assertEqual(
            config["rope_parameters"]["sliding_attention"]["rope_theta"],
            expected["sliding_attention_rope_theta"],
        )

    def test_all_model_core_weights_use_fixed_twsr_configuration(self):
        for expected in PLAN6_MODELS.values():
            quantization = expected["quantization"]
            self.assertEqual(
                quantization["method"],
                "pre_sparse_ridge_twn_sparse005_tf_norm_step_scale",
            )
            self.assertEqual(quantization["group_size"], -1)
            self.assertEqual(quantization["damping"], 1.0)
            self.assertEqual(quantization["beta"], "tf_norm")
            self.assertEqual(quantization["sparse_fraction"], 0.005)


if __name__ == "__main__":
    unittest.main()
