import json
import tempfile
import unittest
from pathlib import Path

from accagent.framework.fpga_ip_contract import simulation_source_contract
from accagent.framework.fpga_ip_runtime import (
    stage_fpga_ip_runtime,
)


class FpgaIpRuntimeTest(unittest.TestCase):
    def test_stages_one_vivado_ip_closure_for_vcs_workdir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / "run"
            simulation_dir = run_dir / "generated" / "chisel" / "simulation"
            scripts_dir = simulation_dir / "scripts"
            scripts_dir.mkdir(parents=True)
            generator = scripts_dir / "gen_xilinx_fp_ips_23.tcl"
            generator.write_text("puts ip-generation\n", encoding="utf-8")
            module_manifest = simulation_dir / "fpga_ip_modules.txt"
            module_manifest.write_text(
                "fp_add_sp_12\nfp_f2i_s16_sp_7\nfp_i2f_s36_sp_7\n",
                encoding="utf-8",
            )
            closure = {
                "status": "ready",
                "policy": simulation_source_contract(),
                "ip_generation_tcl": str(generator),
                "ip_output_dir": str(simulation_dir / "vivado_ip"),
                "ip_project_dir": str(simulation_dir / "vivado_ip_project"),
                "ip_module_manifest": str(module_manifest),
                "fpga_part": "xcvu9p_CIV-flgb2104-2-i",
                "required_ip_modules": [
                    "fp_add_sp_12", "fp_f2i_s16_sp_7", "fp_i2f_s36_sp_7",
                ],
                "vcs_compile_requirements": {
                    "generated_ip_simulation_sources": "generated IP sources",
                    "xpm_library": "xpm",
                    "unisims_library": "unisims_ver",
                    "global_module": "glbl.v",
                },
            }
            (simulation_dir / "fpga_ip_simulation_closure.json").write_text(
                json.dumps(closure), encoding="utf-8"
            )
            staged = stage_fpga_ip_runtime(
                run_dir,
                root / "stage",
                {"tools": [{"name": "vivado", "executable": "/opt/Xilinx/Vivado/2021.1/bin/vivado"}]},
            )

            self.assertEqual(staged["status"], "ready")
            self.assertTrue(Path(staged["staged_tcl"]).is_file())
            self.assertTrue(Path(staged["staged_module_manifest"]).is_file())
            self.assertTrue((root / "stage" / "fpga_ip" / "fpga_ip_simulation_closure.json").is_file())
            command = staged["provision_command"]
            self.assertIn('"$VIVADO_BIN" -mode batch', command)
            self.assertIn("xcvu9p_CIV-flgb2104-2-i", command)
            self.assertIn("fpga_ip/fpga_ip_modules.txt", command)
            self.assertIn("export_vcs_file_info.tcl", command)
            self.assertIn("build_vcs_library_plan.py", command)
            self.assertIn("--compiler-workdir .", command)
            self.assertIn("--compiler-workdir vcs_work", command)
            self.assertTrue((root / "stage" / "fpga_ip" / "export_vcs_file_info.tcl").is_file())
            self.assertTrue((root / "stage" / "fpga_ip" / "build_vcs_library_plan.py").is_file())
            self.assertEqual(staged["remote_vcs_compile_script"], "fpga_ip/compile_ip_models.sh")
            self.assertEqual(staged["remote_vcs_runtime_env"], "fpga_ip/vcs_runtime.env")
            self.assertEqual(staged["remote_vcs_elab_args"], "fpga_ip/vcs_elab_args.txt")
            self.assertEqual(staged["compiler_workdirs"], [".", "vcs_work"])

            root_compile = stage_fpga_ip_runtime(
                run_dir,
                root / "stage_root_compile",
                {"tools": [{"name": "vivado", "executable": "/opt/Xilinx/Vivado/2021.1/bin/vivado"}]},
                compiler_workdir=".",
            )
            self.assertEqual(root_compile["compiler_workdirs"], ["."])

    def test_relative_closure_artifacts_resolve_from_closure_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / "run"
            simulation_dir = run_dir / "generated" / "chisel" / "simulation"
            scripts_dir = simulation_dir / "scripts"
            scripts_dir.mkdir(parents=True)
            (scripts_dir / "gen.tcl").write_text("puts generation\n", encoding="utf-8")
            (simulation_dir / "modules.txt").write_text("fp_add_sp_12\n", encoding="utf-8")
            closure = {
                "status": "ready",
                "policy": simulation_source_contract(),
                "ip_generation_tcl": "scripts/gen.tcl",
                "ip_output_dir": "vivado_ip",
                "ip_project_dir": "vivado_ip_project",
                "ip_module_manifest": "modules.txt",
                "fpga_part": "xcvu9p-flgb2104-2-i",
                "required_ip_modules": ["fp_add_sp_12"],
                "vcs_compile_requirements": {
                    "generated_ip_simulation_sources": "generated IP sources",
                    "xpm_library": "xpm",
                    "unisims_library": "unisims_ver",
                    "global_module": "glbl.v",
                },
            }
            (simulation_dir / "fpga_ip_simulation_closure.json").write_text(
                json.dumps(closure), encoding="utf-8"
            )

            staged = stage_fpga_ip_runtime(
                run_dir,
                root / "stage",
                {"tools": [{"name": "vivado", "executable": "/opt/vivado"}]},
            )

            self.assertEqual(Path(staged["staged_tcl"]).read_text(), "puts generation\n")
            self.assertEqual(Path(staged["staged_module_manifest"]).read_text(), "fp_add_sp_12\n")

    def test_formal_vivado_runner_uses_generated_manifest_and_board_part(self) -> None:
        root = Path(__file__).resolve().parents[1]
        runner = (root / "scripts" / "synthesis" / "run_qwen_generated_bitstream_23.sh").read_text(
            encoding="utf-8"
        )
        synthesis_tcl = (root / "scripts" / "synthesis" / "qwen_generated_bitstream_23.tcl").read_text(
            encoding="utf-8"
        )

        self.assertIn('LOCAL_IP_TCL="$LOCAL_SV_DIR/scripts/gen_xilinx_fp_ips_23.tcl"', runner)
        self.assertIn('LOCAL_IP_MODULES="$LOCAL_SV_DIR/simulation/fpga_ip_modules.txt"', runner)
        self.assertNotIn("simulation/scripts/gen_xilinx_fp_ips_23.tcl", runner)
        self.assertIn("'$FPGA_PART' fpga_ip_modules.txt", runner)
        self.assertIn("'$CLOCK_PERIOD_NS' '$FPGA_PART'", runner)
        self.assertIn(
            'set part_name [get_arg_or_default 2 "xcvu9p_CIV-flgb2104-2-i"]',
            synthesis_tcl,
        )
        self.assertIn("set_property generate_synth_checkpoint false $ip_file", synthesis_tcl)
