"""Validate actual CIRCT ANSI grouping without weakening the DDR contract."""
import tempfile
import unittest
from pathlib import Path
from accagent.framework.stage_artifacts import check_generated_ddr_tile_service_abi

HEADER = """
  input clock, reset, {p}ddrTileRequest_ready,
  output {p}ddrTileRequest_valid,
  output [15:0] {p}ddrTileRequest_bits_routeId,
                  {p}ddrTileRequest_bits_layerIndex,
                  {p}ddrTileRequest_bits_tileIndex,
  output {p}ddrTileRequest_bits_shadowBank,
  output [31:0] {p}ddrTileRequest_bits_tileWordCount,
  output [63:0] {p}ddrTileRequest_bits_ddrWordAddress,
  output {p}ddrTileResponse_ready,
  input {p}ddrTileResponse_valid,
  input [15:0] {p}ddrTileResponse_bits_routeId,
                 {p}ddrTileResponse_bits_layerIndex,
                 {p}ddrTileResponse_bits_tileIndex,
  input {p}ddrTileResponse_bits_shadowBank,
  input [31:0] {p}ddrTileResponse_bits_wordIndex,
  input [4:0] {p}ddrTileResponse_bits_validWords,
  input [511:0] {p}ddrTileResponse_bits_data,
  input {p}ddrTileResponse_bits_last
"""

class DdrServiceAbiTests(unittest.TestCase):
    def write_tops(self, root):
        for name, prefix in [("GeneratedAcceleratorTop", ""), ("GeneratedAxiDdrTop", "io_")]:
            (root / (name + ".sv")).write_text("module " + name + "(" + HEADER.format(p=prefix) + "); endmodule")

    def test_accepts_grouped_declarations_and_chisel_outer_ports(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_tops(root)
            self.assertEqual(check_generated_ddr_tile_service_abi(root, 512), [])

    def test_rejects_payload_narrowing_and_direction_reversal(self):
        for old, new, expected in [("[511:0]", "[31:0]", "width=32"), ("input io_ddrTileResponse_valid", "output io_ddrTileResponse_valid", "direction=output")]:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.write_tops(root)
                target = root / "GeneratedAxiDdrTop.sv"
                target.write_text(target.read_text().replace(old, new))
                self.assertTrue(any(expected in error for error in check_generated_ddr_tile_service_abi(root, 512)))

    def test_rejects_missing_grouped_metadata_port(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_tops(root)
            target = root / "GeneratedAcceleratorTop.sv"
            target.write_text(target.read_text().replace("ddrTileRequest_bits_tileIndex", "removedPort"))
            self.assertTrue(any("missing connected DDR service port io_ddrTileRequest_bits_tileIndex" in error for error in check_generated_ddr_tile_service_abi(root, 512)))
