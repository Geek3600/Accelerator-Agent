import json
import tempfile
import unittest
from pathlib import Path

from scripts.synthesis.compute_slot_adapter_generator import (
    _module_port_names,
    generate,
)


RUN_DIR = Path(__file__).resolve().parents[1] / "accagent" / "runs" / "spatialacc_qwen_agent_fast_run"
LEGACY_ADAPTER = RUN_DIR / "generated" / "board_integration" / "app_shell_9p_cnn_core_0_1.v"
GENERATED_TOP = RUN_DIR / "generated" / "chisel" / "GeneratedAxiDdrTop.sv"


def adapter_contract(legacy_source: str) -> dict:
    ports = sorted(_module_port_names(legacy_source))
    route_specs = [
        ("rms1Weight", 0, 896),
        ("qkvWeight", 896, 516096),
        ("qkvBias", 516992, 1152),
        ("attentionOutWeight", 518144, 401408),
        ("rms2Weight", 919552, 896),
        ("mlpGateWeight", 920448, 2179072),
        ("mlpUpWeight", 3099520, 2179072),
        ("mlpDownWeight", 5278592, 2179072),
    ]
    return {
        "integration_target": {
            "replacement_module_identity": "app_shell_9p_cnn_core_0_1",
        },
        "compute_slot_abi": {
            "required_ports": [{"name": port} for port in ports],
        },
        "dut_loader_route_contract": {
            "weight_routes": [
                {
                    "dut_port": f"core.io.{port}",
                    "global_stream_range": {
                        "word_offset": start,
                        "word_count": count,
                    },
                    "local_stream_range": {"word_offset": 0},
                }
                for port, start, count in route_specs
            ],
            "runtime_routes": [
                {"dut_port": "core.io.ropeRuntime"},
            ],
        },
        "generated_core": {"params": {"max_seq_len": 16}},
    }


class ComputeSlotAdapterGeneratorTest(unittest.TestCase):
    def test_replaces_scheduler_with_generated_top_and_preserves_exact_abi(self) -> None:
        legacy_source = LEGACY_ADAPTER.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            contract = root / "contract.json"
            legacy = root / "legacy.v"
            top = root / "GeneratedAxiDdrTop.sv"
            output = root / "adapter.v"
            manifest = root / "adapter_manifest.json"
            contract.write_text(json.dumps(adapter_contract(legacy_source)), encoding="utf-8")
            legacy.write_text(legacy_source, encoding="utf-8")
            top.write_text(GENERATED_TOP.read_text(encoding="utf-8"), encoding="utf-8")

            result = generate(contract, legacy, top, output, manifest)
            generated = output.read_text(encoding="utf-8")

        self.assertEqual(result["module"], "app_shell_9p_cnn_core_0_1")
        self.assertEqual(result["weight_route_count"], 8)
        self.assertEqual(result["required_port_count"], len(_module_port_names(legacy_source)))
        self.assertNotIn("SingleLayerSemanticHarness", generated)
        self.assertIn("GeneratedAxiDdrTop spatialacc_generated_top", generated)
        self.assertIn("WEIGHT_ROUTE_MLP_DOWN = 4'd8", generated)
        self.assertIn("reg [8:0] weight_words_per_tx_d", generated)
        self.assertIn("reg kernel_input_start_q;", generated)
        self.assertIn("reg kernel_input_last_q;", generated)
        self.assertIn("WEIGHT_QKV_START = 23'd896", generated)
        self.assertIn("WEIGHT_QKV_END = 23'd516992", generated)
        self.assertIn("case (weight_route_d)", generated)
        self.assertIn("wire gen_qkv_valid; wire gen_qkv_ready;", generated)
        self.assertIn("wire gen_mlp_down_valid; wire gen_mlp_down_ready;", generated)
        self.assertNotIn("gen_qkv_valid <=", generated)
        self.assertNotIn("gen_mlp_down_valid <=", generated)

    def test_uses_contract_route_count_and_unfamiliar_port_name(self) -> None:
        legacy_source = LEGACY_ADAPTER.read_text(encoding="utf-8")
        top_source = """module GenericBoardTop(
  input clock, reset, io_start,
  input [4:0] io_cfgSeqlen,
  input io_cfgPrefill, io_cfgSingleQuery,
  input [3:0] io_position,
  output io_projectionWeights_ready,
  input io_projectionWeights_valid,
  input [511:0] io_projectionWeights_bits_data,
  input [9:0] io_projectionWeights_bits_addr,
  input io_axiReadValid,
  output io_axiReadReady,
  input [255:0] io_axiReadData,
  input [10:0] io_axiReadAddr,
  input io_axiReadStart, io_axiReadLast,
  output io_axiWriteValid,
  input io_axiWriteReady,
  output [255:0] io_axiWriteData,
  output [10:0] io_axiWriteAddr,
  output io_axiWriteStart, io_axiWriteLast,
  output io_busy, io_done,
  output [63:0] io_performanceCycles,
  output io_performanceValid
); endmodule
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            contract = root / "contract.json"
            legacy = root / "legacy.v"
            top = root / "GenericBoardTop.sv"
            output = root / "adapter.v"
            manifest = root / "adapter_manifest.json"
            data = adapter_contract(legacy_source)
            data["dut_loader_route_contract"]["weight_routes"] = [{
                "dut_port": "core.io.projectionWeights",
                "dut_port_role": "projection_weight",
                "global_stream_range": {"word_offset": 0, "word_count": 128},
                "local_stream_range": {"word_offset": 0},
            }]
            data["dut_loader_route_contract"].pop("runtime_routes", None)
            contract.write_text(json.dumps(data), encoding="utf-8")
            legacy.write_text(legacy_source, encoding="utf-8")
            top.write_text(top_source, encoding="utf-8")

            result = generate(contract, legacy, top, output, manifest)
            generated = output.read_text(encoding="utf-8")

        self.assertEqual(result["weight_route_count"], 1)
        self.assertEqual(result["generated_top_module"], "GenericBoardTop")
        self.assertIn("WEIGHT_ROUTE_ROUTE_0", generated)
        self.assertIn("reg [511:0] gen_projection_data;", generated)
        self.assertIn(".io_projectionWeights_valid(gen_projection_valid)", generated)
        self.assertIn(".io_projectionWeights_bits_addr(weight_pack_addr_q)", generated)
        self.assertNotIn("gen_qkv", generated)

    def test_emits_explicit_axi_width_adapters_for_non_256_top(self) -> None:
        legacy_source = LEGACY_ADAPTER.read_text(encoding="utf-8")
        top_source = """module WidthVariantTop(
  input clock, reset, io_start,
  input [4:0] io_cfgSeqlen,
  input io_cfgPrefill, io_cfgSingleQuery,
  input [3:0] io_position,
  output io_projectionWeights_ready,
  input io_projectionWeights_valid,
  input [127:0] io_projectionWeights_bits_data,
  input [9:0] io_projectionWeights_bits_addr,
  input io_axiReadValid,
  output io_axiReadReady,
  input [127:0] io_axiReadData,
  input [10:0] io_axiReadAddr,
  input io_axiReadStart, io_axiReadLast,
  output io_axiWriteValid,
  input io_axiWriteReady,
  output [511:0] io_axiWriteData,
  output [10:0] io_axiWriteAddr,
  output io_axiWriteStart, io_axiWriteLast,
  output io_busy, io_done,
  output [63:0] io_performanceCycles,
  output io_performanceValid
); endmodule
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            contract = root / "contract.json"
            legacy = root / "legacy.v"
            top = root / "WidthVariantTop.sv"
            output = root / "adapter.v"
            manifest = root / "adapter_manifest.json"
            data = adapter_contract(legacy_source)
            data["dut_loader_route_contract"]["weight_routes"] = [{
                "dut_port": "core.io.projectionWeights",
                "dut_port_role": "projection_weight",
                "global_stream_range": {"word_offset": 0, "word_count": 128},
                "local_stream_range": {"word_offset": 0},
            }]
            data["dut_loader_route_contract"].pop("runtime_routes", None)
            contract.write_text(json.dumps(data), encoding="utf-8")
            legacy.write_text(legacy_source, encoding="utf-8")
            top.write_text(top_source, encoding="utf-8")

            result = generate(contract, legacy, top, output, manifest)
            generated = output.read_text(encoding="utf-8")
            adapter_manifest = json.loads(manifest.read_text(encoding="utf-8"))

        self.assertEqual(result["axi_data_widths"]["generated_read_bits"], 128)
        self.assertEqual(result["axi_data_widths"]["generated_write_bits"], 512)
        self.assertIn("wire [127:0] generated_axi_read_data = kernel_input_data_q[127:0];", generated)
        self.assertIn("wire [255:0] kernel_output_data_q = gen_axi_write_data[255:0];", generated)
        self.assertIn("axi_data_widths", adapter_manifest)


if __name__ == "__main__":
    unittest.main()
