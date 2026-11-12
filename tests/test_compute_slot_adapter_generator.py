import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.synthesis import compute_slot_adapter_generator as adapter_generator

from scripts.synthesis.compute_slot_adapter_generator import (
    _module_name,
    _module_port_names,
    _route_rows,
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
    def test_compact_ansi_ports_keep_individual_widths_and_directions(self) -> None:
        source = "module Slot(input wire [511:0] data,input wire valid,output wire [3:0] id); endmodule"
        self.assertEqual(_module_port_names(source), {"data", "valid", "id"})
        self.assertEqual(adapter_generator._module_port_widths(source),
                         {"data": 512, "valid": 1, "id": 4})
        self.assertEqual(adapter_generator._module_port_directions(source),
                         {"data": "input", "valid": "input", "id": "output"})

    def test_board_abi_selects_contracted_module_after_helper_modules(self) -> None:
        source = (
            "module scale_config_store(input wire cfg_done); endmodule\n"
            "module cnn_core(input wire [511:0] c0_ddr4_s_axi_rdata, "
            "output wire c0_ddr4_s_axi_rready); endmodule\n"
        )
        self.assertEqual(
            _module_port_names(source, "cnn_core"),
            {"c0_ddr4_s_axi_rdata", "c0_ddr4_s_axi_rready"},
        )
        self.assertEqual(
            adapter_generator._module_port_widths(source, "cnn_core"),
            {"c0_ddr4_s_axi_rdata": 512, "c0_ddr4_s_axi_rready": 1},
        )
        self.assertEqual(
            adapter_generator._module_port_directions(source, "cnn_core"),
            {"c0_ddr4_s_axi_rdata": "input", "c0_ddr4_s_axi_rready": "output"},
        )

    def test_direct_ddr_adapter_bypasses_legacy_harness_and_rejects_tieoff(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            contract, source, top, out, manifest = [root / x for x in
                ("contract.json", "slot.sv", "top.sv", "out.sv", "manifest.json")]
            contract.write_text(json.dumps({"integration_target": {
                "replacement_module_identity": "Slot"}, "generated_core": {
                "params": {"cache_refill_data_width_bits": 512}}}))
            top.write_text("module Core(\ninput io_ddrTileRequest_ready,\n"
                           "output io_ddrTileRequest_valid,\ninput io_ddrTileResponse_valid,\n"
                           "output io_ddrTileResponse_ready\n); endmodule")
            good = ("module Slot(input clock);\nwire request_ready, response_valid;\n"
                    "Core kernel(.io_ddrTileRequest_ready(request_ready),"
                    ".io_ddrTileResponse_valid(response_valid));\nendmodule")
            source.write_text(good)
            with patch.object(adapter_generator, "_current_board_scheduler_source", return_value=source), \
                patch.object(adapter_generator, "_validate_current_board_scheduler_abi", return_value={
                    "axi_data_bits": 512,
                }):
                result = generate(contract, source, top, out, manifest)
                self.assertEqual(result["adapter_mode"], "direct_contract_adapter")
                self.assertEqual(out.read_text(), good)
                wildcard = ("module Slot(input clock);\n"
                            "wire io_ddrTileRequest_ready, io_ddrTileResponse_valid;\n"
                            "assign io_ddrTileRequest_ready = can_accept;\n"
                            "assign io_ddrTileResponse_valid = buffer_valid;\n"
                            "Core kernel(.*);\nendmodule")
                source.write_text(wildcard)
                self.assertEqual(generate(contract, source, top, out, manifest)["status"], "ready")
                source.write_text(good.replace("(request_ready)", "(1'b0)"))
                with self.assertRaisesRegex(ValueError, "disconnected or tied low"):
                    generate(contract, source, top, out, manifest)

    def test_generated_top_handshake_must_be_connected_on_that_instance(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            contract, source, top, out, manifest = [root / x for x in
                ("contract.json", "slot.sv", "top.sv", "out.sv", "manifest.json")]
            contract.write_text(json.dumps({"integration_target": {
                "replacement_module_identity": "Slot"}, "generated_core": {
                "params": {"cache_refill_data_width_bits": 512}}}))
            top.write_text(
                "module GeneratedAxiDdrTop(input clock, input reset, "
                "input io_ddrTileRequest_ready, output io_ddrTileRequest_valid, "
                "input io_ddrTileResponse_valid, output io_ddrTileResponse_ready); "
                "endmodule\n"
            )
            source.write_text(
                "module Slot(input clock, input reset);\n"
                "wire request_ready, response_valid;\n"
                "GeneratedAcceleratorTop u_kernel("
                ".io_ddrTileRequest_ready(request_ready),"
                ".io_ddrTileResponse_valid(response_valid));\n"
                "GeneratedAxiDdrTop u_generated(\n"
                "  .clock(clock), .reset(reset)\n"
                ");\n"
                "endmodule\n"
            )
            with patch.object(adapter_generator, "_current_board_scheduler_source", return_value=source), \
                patch.object(adapter_generator, "_validate_current_board_scheduler_abi", return_value={
                    "axi_data_bits": 512,
                }):
                with self.assertRaisesRegex(ValueError, "disconnected or tied low"):
                    generate(contract, source, top, out, manifest)

    def test_module_name_accepts_parameterized_board_scheduler(self) -> None:
        for declaration in (
            "module board_slot(input wire clk); endmodule",
            "module board_slot #(parameter integer WIDTH = 512)(input wire clk); endmodule",
            "module automatic board_slot # (parameter WIDTH=512) (input clk); endmodule",
        ):
            with self.subTest(declaration=declaration):
                self.assertEqual(_module_name(declaration), "board_slot")
        with self.assertRaises(ValueError):
            _module_name("wire clk;")

    def test_derives_unique_weight_routes_from_target_segments(self) -> None:
        top = """module GeneratedTop(
  output io_norm1Weight_ready, input io_norm1Weight_valid,
  input [127:0] io_norm1Weight_bits,
  output io_qkvWeight_ready, input io_qkvWeight_valid,
  input [255:0] io_qkvWeight_bits_data,
  input [9:0] io_qkvWeight_bits_addr
); endmodule
"""
        contract = {
            "loader_route_contract": {
                "weight": {
                    "stage_segments": [
                        {
                            "stage_id": "stage_00_layer_norm_1",
                            "op": "layer_norm_1",
                            "targets": [{
                                "target_id": "norm.scale",
                                "dut_port_role": "weight",
                                "global_stream_range": {"word_offset": 0, "word_count": 8},
                                "local_stream_range": {"word_offset": 0},
                            }],
                        },
                        {
                            "stage_id": "stage_01_self_attention",
                            "op": "self_attention",
                            "targets": [{
                                "target_id": "attention.qkv.weight",
                                "dut_port_role": "qkv_weight",
                                "global_stream_range": {"word_offset": 8, "word_count": 32},
                                "local_stream_range": {"word_offset": 0},
                            }],
                        },
                    ],
                },
            },
        }

        routes = _route_rows(contract, port_names=_module_port_names(top))

        self.assertEqual([row["port"] for row in routes], ["norm1Weight", "qkvWeight"])
        self.assertEqual([row["start"] for row in routes], [0, 8])

    def test_merges_adjacent_targets_that_share_one_generated_port(self) -> None:
        top = """module GeneratedTop(
  output io_norm1Weight_ready, input io_norm1Weight_valid,
  input [127:0] io_norm1Weight_bits
); endmodule
"""
        contract = {
            "loader_route_contract": {
                "weight": {
                    "stage_segments": [{
                        "stage_id": "stage_00_layer_norm_1",
                        "op": "layer_norm_1",
                        "targets": [
                            {
                                "target_id": "norm.bias",
                                "dut_port_role": "weight",
                                "global_stream_range": {"word_offset": 0, "word_count": 8},
                                "local_stream_range": {"word_offset": 0},
                            },
                            {
                                "target_id": "norm.scale",
                                "dut_port_role": "weight",
                                "global_stream_range": {"word_offset": 8, "word_count": 8},
                                "local_stream_range": {"word_offset": 0},
                            },
                        ],
                    }],
                },
            },
        }

        routes = _route_rows(contract, port_names=_module_port_names(top))

        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0]["port"], "norm1Weight")
        self.assertEqual(routes[0]["count"], 16)

    def test_rejects_wrong_direction_and_width_before_writing_adapter(self) -> None:
        source = "module SlotAdapter(\n  output wire [7:0] control\n);\nassign control = 0;\nendmodule\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            contract = root / "contract.json"
            legacy = root / "source.sv"
            generated_top = root / "GeneratedTop.sv"
            output = root / "adapter.v"
            manifest = root / "manifest.json"
            legacy.write_text(source, encoding="utf-8")
            generated_top.write_text("module GeneratedTop; endmodule\n", encoding="utf-8")
            for direction, width, error in [
                ("input", 8, "direction mismatch for control"),
                ("output", 4, "width mismatch for control"),
            ]:
                with self.subTest(direction=direction, width=width):
                    contract.write_text(json.dumps({
                        "integration_target": {"replacement_module_identity": "SlotAdapter"},
                        "compute_slot_abi": {"required_ports": [{
                            "name": "control", "direction": direction, "width_bits": width,
                        }]},
                    }), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, error):
                        generate(contract, legacy, generated_top, output, manifest)
                    self.assertFalse(output.exists())
                    self.assertFalse(manifest.exists())

    def test_accepts_current_contract_bound_systemverilog_adapter_artifact(self) -> None:
        source = """module SlotAdapter(\n  input clock,\n  input reset,\n  output ready\n);\nassign ready = !reset;\nendmodule\n"""
        top = "module GeneratedTop(input clock); endmodule\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            contract = root / "contract.json"
            legacy = root / "agent_board_wrapper.sv"
            generated_top = root / "GeneratedAxiDdrTop.sv"
            output = root / "adapter.v"
            manifest = root / "adapter_manifest.json"
            contract.write_text(
                json.dumps(
                    {
                        "integration_target": {"replacement_module_identity": "SlotAdapter"},
                        "compute_slot_abi": {
                            "required_ports": [{"name": "clock"}, {"name": "reset"}, {"name": "ready"}]
                        },
                    }
                ),
                encoding="utf-8",
            )
            legacy.write_text(source, encoding="utf-8")
            generated_top.write_text(top, encoding="utf-8")

            result = generate(contract, legacy, generated_top, output, manifest)

            self.assertEqual(result["adapter_mode"], "direct_contract_adapter")
            self.assertFalse(result["uses_generated_top"])
            self.assertEqual(output.read_text(encoding="utf-8"), source)

    def test_direct_adapter_does_not_require_runtime_weight_mapping(self) -> None:
        source = """module SlotAdapter(\n  input clock,\n  input reset,\n  output ready\n);\nassign ready = !reset;\nendmodule\n"""
        top = """module GeneratedTop(
  input io_qkvWeight_valid
); endmodule
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            contract = root / "contract.json"
            legacy = root / "legacy.sv"
            generated_top = root / "GeneratedTop.sv"
            output = root / "adapter.sv"
            manifest = root / "adapter_manifest.json"
            contract.write_text(json.dumps({
                "integration_target": {"replacement_module_identity": "SlotAdapter"},
                "compute_slot_abi": {"required_ports": [{"name": "clock"}, {"name": "reset"}, {"name": "ready"}]},
                "loader_route_contract": {"weight": {"word_count": 64}},
            }), encoding="utf-8")
            legacy.write_text(source, encoding="utf-8")
            generated_top.write_text(top, encoding="utf-8")

            result = generate(contract, legacy, generated_top, output, manifest)
            self.assertEqual(output.read_text(encoding="utf-8"), source)
            self.assertEqual(result["weight_route_count"], 0)
            self.assertFalse(result["uses_generated_top"])

    def test_direct_adapter_is_not_rewritten_to_prove_runtime_routes(self) -> None:
        source = """module SlotAdapter(
  input clock,
  input reset,
  output ready
);
assign ready = !reset;
endmodule
"""
        top = """module GeneratedTop(
  output io_qkvWeight_ready,
  input io_qkvWeight_valid,
  input [127:0] io_qkvWeight_bits_data,
  input [7:0] io_qkvWeight_bits_addr
); endmodule
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            contract = root / "contract.json"
            legacy = root / "legacy.sv"
            generated_top = root / "GeneratedTop.sv"
            output = root / "adapter.sv"
            manifest = root / "adapter_manifest.json"
            contract.write_text(json.dumps({
                "integration_target": {"replacement_module_identity": "SlotAdapter"},
                "compute_slot_abi": {"required_ports": [{"name": "clock"}, {"name": "reset"}, {"name": "ready"}]},
                "loader_route_contract": {
                    "weight": {
                        "word_count": 4,
                        "stage_segments": [{"targets": [{
                            "target_id": "attention.qkv.weight",
                            "dut_port_role": "qkv_weight",
                            "global_stream_range": {"word_offset": 0, "word_count": 4},
                            "local_stream_range": {"word_offset": 0},
                        }]}],
                    },
                },
            }), encoding="utf-8")
            legacy.write_text(source, encoding="utf-8")
            generated_top.write_text(top, encoding="utf-8")

            result = generate(contract, legacy, generated_top, output, manifest)
            self.assertEqual(output.read_text(encoding="utf-8"), source)
            self.assertFalse(result["uses_generated_top"])

    def test_direct_adapter_defers_constant_bindings_to_real_compilation(self) -> None:
        source = """module SlotAdapter(
  input clock,
  input reset,
  output ready
);
  GeneratedTop generated_top(
    .io_qkvWeight_ready(),
    .io_qkvWeight_valid(1'b0),
    .io_qkvWeight_bits_data(128'b0),
    .io_qkvWeight_bits_addr(8'b0)
  );
assign ready = !reset;
endmodule
"""
        top = """module GeneratedTop(
  output io_qkvWeight_ready,
  input io_qkvWeight_valid,
  input [127:0] io_qkvWeight_bits_data,
  input [7:0] io_qkvWeight_bits_addr
); endmodule
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            contract = root / "contract.json"
            legacy = root / "legacy.sv"
            generated_top = root / "GeneratedTop.sv"
            output = root / "adapter.sv"
            manifest = root / "adapter_manifest.json"
            contract.write_text(json.dumps({
                "integration_target": {"replacement_module_identity": "SlotAdapter"},
                "compute_slot_abi": {"required_ports": [{"name": "clock"}, {"name": "reset"}, {"name": "ready"}]},
                "loader_route_contract": {"weight_routes": [{
                    "dut_port": "core.io.qkvWeight",
                    "global_stream_range": {"word_offset": 0, "word_count": 4},
                    "local_stream_range": {"word_offset": 0},
                }]},
            }), encoding="utf-8")
            legacy.write_text(source, encoding="utf-8")
            generated_top.write_text(top, encoding="utf-8")

            result = generate(contract, legacy, generated_top, output, manifest)
            self.assertEqual(output.read_text(encoding="utf-8"), source)
            self.assertTrue(result["uses_generated_top"])

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
