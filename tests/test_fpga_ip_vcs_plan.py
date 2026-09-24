import argparse
import json
import os
import tempfile
import unittest
from pathlib import Path

from accagent.framework.fpga_ip_vcs_plan import build


class FpgaIpVcsPlanTest(unittest.TestCase):
    def make_closure(self, root: Path, *, conflict: bool = False) -> argparse.Namespace:
        ip_root = root / "fpga_ip" / "vivado_ip"
        export_root = root / "fpga_ip" / "vivado_export"
        modules = ["fp_add_sp_12", "fp_mul_sp_9"]
        (root / "fpga_ip").mkdir(parents=True)
        (root / "fpga_ip" / "modules.txt").write_text(
            "\n".join(modules) + "\n", encoding="utf-8"
        )
        for index, module in enumerate(modules):
            hdl = ip_root / module / "hdl"
            sim = ip_root / module / "sim"
            vcs = export_root / module / "vcs"
            hdl.mkdir(parents=True)
            sim.mkdir(parents=True)
            vcs.mkdir(parents=True)
            shared = hdl / "floating_point_v7_1_rfs.vhd"
            shared.write_text(
                "library ieee;" + (" -- conflict" if conflict and index else "") + "\n",
                encoding="utf-8",
            )
            rtl = hdl / "floating_point_v7_1_rfs.v"
            rtl.write_text("module floating_point_v7_1; endmodule\n", encoding="utf-8")
            wrapper = sim / f"{module}.v"
            wrapper.write_text(f"module {module}; endmodule\n", encoding="utf-8")
            glbl = vcs / "glbl.v"
            glbl.write_text("module glbl; endmodule\n", encoding="utf-8")
            rows = [
                f"{shared.name},vhdl,floating_point_v7_1_12,{shared.resolve()},",
                f"{rtl.name},verilog,floating_point_v7_1_12,{rtl.resolve()},",
                f"{wrapper.name},verilog,xil_defaultlib,{wrapper.resolve()},",
                f"glbl.v,Verilog,xil_defaultlib,{glbl.resolve()},",
            ]
            (vcs / "file_info.txt").write_text("\n".join(rows) + "\n", encoding="utf-8")
        return argparse.Namespace(
            module_manifest="fpga_ip/modules.txt",
            ip_root="fpga_ip/vivado_ip",
            export_root="fpga_ip/vivado_export",
            library_root="custom_lib",
            compiler_workdir=[".", "compile", "elab"],
            expected_default_library="xil_defaultlib",
        )

    def build_in(self, root: Path, args: argparse.Namespace) -> dict:
        prior = Path.cwd()
        try:
            os.chdir(root)
            return build(args)
        finally:
            os.chdir(prior)

    def test_preserves_official_language_library_order_and_deduplicates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = self.build_in(root, self.make_closure(root))

            self.assertEqual(plan["default_library"], "xil_defaultlib")
            self.assertEqual(
                [
                    (row["language"], row["library"], row["filename"])
                    for row in plan["records"]
                ],
                [
                    ("vhdl", "floating_point_v7_1_12", "floating_point_v7_1_rfs.vhd"),
                    ("verilog", "floating_point_v7_1_12", "floating_point_v7_1_rfs.v"),
                    ("verilog", "xil_defaultlib", "fp_add_sp_12.v"),
                    ("verilog", "xil_defaultlib", "glbl.v"),
                    ("verilog", "xil_defaultlib", "fp_mul_sp_9.v"),
                ],
            )
            script = (root / "fpga_ip" / "compile_ip_models.sh").read_text(
                encoding="utf-8"
            )
            self.assertLess(script.index("vhdlan"), script.index("vlogan"))
            self.assertIn("-work floating_point_v7_1_12", script)
            self.assertIn("-work xil_defaultlib", script)
            setup = (root / "compile" / "synopsys_sim.setup").read_text()
            self.assertIn(
                "floating_point_v7_1_12:../custom_lib/floating_point_v7_1_12",
                setup,
            )
            self.assertEqual(
                (root / "fpga_ip" / "vcs_elab_args.txt").read_text().splitlines(),
                ["-L", "floating_point_v7_1_12", "-L", "xil_defaultlib"],
            )
            runtime = (root / "fpga_ip" / "vcs_runtime.env").read_text()
            self.assertIn("FPGA_IP_DEFAULT_LIBRARY=xil_defaultlib", runtime)
            self.assertIn("FPGA_IP_GLBL_UNIT=xil_defaultlib.glbl", runtime)
            persisted = json.loads(
                (root / "fpga_ip" / "vcs_library_plan.json").read_text()
            )
            self.assertEqual(persisted["records"], plan["records"])

    def test_conflicting_same_library_basename_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with self.assertRaisesRegex(ValueError, "conflicting content"):
                self.build_in(root, self.make_closure(root, conflict=True))

    def test_missing_wrapper_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            args = self.make_closure(root)
            wrapper = (
                root
                / "fpga_ip"
                / "vivado_ip"
                / "fp_mul_sp_9"
                / "sim"
                / "fp_mul_sp_9.v"
            )
            wrapper.unlink()
            with self.assertRaisesRegex(ValueError, "unavailable simulation source"):
                self.build_in(root, args)


if __name__ == "__main__":
    unittest.main()
