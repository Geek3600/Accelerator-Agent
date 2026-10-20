from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.synthesis.app_shell_runtime_vivado import build_kernel_synthesis_tcl, build_tcl, create_source_closure_archive, main, requires_generated_ip


class AppShellRuntimeVivadoTest(unittest.TestCase):
    def test_only_explicit_integer_closure_can_omit_generated_ip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            generated = root / "vivado"
            generated.mkdir()
            closure = root / "simulation/fpga_ip_simulation_closure.json"
            closure.parent.mkdir()
            self.assertTrue(requires_generated_ip(generated))
            for backend, modules, expected in [
                ("integer_dsp", [], False),
                ("integer_dsp", ["needed_ip"], True),
                ("floating_point", [], True),
            ]:
                closure.write_text(json.dumps({"status": "ready", "compute_backend": backend,
                                               "required_ip_modules": modules}))
                self.assertEqual(requires_generated_ip(generated), expected)
            closure.write_text(json.dumps({"status": "ready", "compute_backend": "integer_dsp",
                                           "required_ip_modules": []}))
            archive = root / "closure.tar.gz"
            create_source_closure_archive(archive, generated, None, None)
            import tarfile
            with tarfile.open(archive) as bundle:
                names = bundle.getnames()
            self.assertIn("analysis_context/fpga_ip_simulation_closure.json", names)
            self.assertNotIn("gen_xilinx_fp_ips_23.tcl", names)

    def test_collected_kernel_synthesis_does_not_depend_on_board_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            generated = root / "vivado"
            generated.mkdir()
            (generated / "GeneratedAxiDdrTop.sv").write_text("module AnotherTop(\n input clock,\n output result\n); endmodule\n", encoding="utf-8")
            modules = root / "modules.txt"
            modules.write_text("fp_mul\n", encoding="utf-8")
            ip_tcl = root / "ip.tcl"
            ip_tcl.write_text("puts ip\n", encoding="utf-8")
            reports = root / "app_shell_runtime_bitstream"
            reports.mkdir()
            for metric in ("utilization", "timing"):
                (reports / f"app_shell_synth_{metric}.rpt").write_text("test report\n", encoding="utf-8")
            (reports / "app_shell_runtime_inspection.txt").write_text(
                "kernel_synthesis_completed=1\nkernel_top=AnotherTop\nintegration_ready=1\n", encoding="utf-8"
            )
            report = root / "report.json"
            result = main([
                "--run-dir", str(root), "--contract", str(root / "unused.json"),
                "--wrapper-rtl", str(root / "unused_adapter.sv"), "--generated-vivado-dir", str(generated),
                "--ip-module-manifest", str(modules), "--ip-generation-tcl", str(ip_tcl),
                "--fpga-part", "test_part", "--clock-target-mhz", "250", "--collect-only", "--out", str(report),
            ])
            output = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(result, 0)
        self.assertEqual(output["synthesis_top"], "AnotherTop")
        self.assertEqual(output["timing_clock"], "spatialacc_kernel_clock")
        self.assertEqual(output["measurement_scope"], "generated_kernel_synthesis")

    def test_kernel_synthesis_exposes_real_top_ports_without_board_tieoffs(self) -> None:
        text = build_kernel_synthesis_tcl("CustomKernel", "compute_clk", "target_part", 200.0, 16)

        self.assertIn("synth_design -top {CustomKernel} -part {target_part} -mode out_of_context", text)
        self.assertIn("-period 5.000000 [get_ports {compute_clk}]", text)
        self.assertIn("read_verilog -sv $source", text)
        self.assertIn("read_ip $source", text)
        self.assertIn("generate_synth_checkpoint false", text)
        self.assertIn("IS_BLACKBOX == 1", text)
        self.assertIn("measurement_scope=generated_kernel_synthesis", text)
        for forbidden in ("adapter_path", "source_project_xpr", "DONT_TOUCH", "set_case_analysis", "read_checkpoint"):
            self.assertNotIn(forbidden, text)

    def test_real_app_shell_tcl_keeps_slot_ooc_and_top_implementation_in_one_flow(self) -> None:
        text = build_tcl(
            "app_shell_9p_cnn_core_0_1",
            "app_shell_9p_cnn_core_0_1_synth_1",
            16,
            "/cnn_core_0",
            "c0_ddr4_s_axi_clk",
            250.0,
        )

        self.assertIn("save_project_as -force -dir $clone_root", text)
        self.assertIn("write_ooc_pre_hook", text)
        self.assertIn("set target_bd_cell {/cnn_core_0}", text)
        self.assertIn("get_bd_cells -quiet $target_bd_cell", text)
        self.assertIn('execution_mode eq "preflight"', text)
        self.assertIn("ooc_pre_hook_bound", text)
        self.assertIn("ooc_pre_hook_in_script", text)
        self.assertIn("spatialacc_clock_port", text)
        self.assertIn("spatialacc_clock_period_ns", text)
        self.assertIn("spatialacc_dut_clock.xdc", text)
        self.assertIn("read_xdc -mode out_of_context", text)
        self.assertIn("create_clock -name spatialacc_dut_clock", text)
        self.assertIn("4.000000", text)
        self.assertIn("ooc_adapter_copied", text)
        self.assertIn("STEPS.SYNTH_DESIGN.TCL.PRE", text)
        self.assertIn("set generated_root [file normalize $generated_root]", text)
        self.assertIn("set fp_ip_root [file normalize $fp_ip_root]", text)
        self.assertIn("read_verilog -sv $f", text)
        self.assertIn("proc spatialacc_collect_xci_files", text)
        self.assertIn("[spatialacc_collect_xci_files $fp_ip_root]", text)
        self.assertIn("read_ip $f", text)
        self.assertIn("set fp_ips [get_ips -quiet fp_*]", text)
        self.assertIn("generated_root", text)
        self.assertIn("generate_synth_checkpoint false", text)
        self.assertIn("rename read_ip spatialacc_original_read_ip", text)
        self.assertIn("SPATIALACC_COMPUTE_SLOT_ADAPTER_ACTIVE", text)
        self.assertIn("rename set_property spatialacc_original_set_property", text)
        self.assertIn("SPATIALACC_REPLACED_SLOT_XDC_OMITTED", text)
        self.assertIn("[llength [lindex $args 2]] == 0", text)
        self.assertIn("ooc_activation_marker", text)
        self.assertIn("ooc_adapter_active", text)
        self.assertIn('execution_mode eq "ooc"', text)
        self.assertIn("ooc_synthesis_completed", text)
        self.assertIn("ooc_slot_wrapper", text)
        self.assertIn("file copy -force $adapter_path $slot_wrapper", text)
        self.assertIn("file_contains", text)
        self.assertIn("same_file_contents", text)
        self.assertIn("wait_on_run $ooc_run", text)
        self.assertIn('if {$execution_mode eq "preflight"} {\n  reset_run $ooc_run\n  launch_runs $ooc_run -scripts_only', text)
        self.assertIn('}\nreset_run $ooc_run\nset ooc_resource_source [file join $work_dir src]', text)
        self.assertIn('file copy -force $ooc_resource_source $ooc_dir', text)
        self.assertIn('launch_runs $ooc_run -jobs $jobs', text)
        self.assertNotIn("./runme.sh > ooc_run.log", text)
        self.assertIn("launch_runs $top_synth -jobs $jobs", text)
        self.assertIn("launch_runs $top_impl -to_step write_bitstream -jobs $jobs", text)
        self.assertIn("report_utilization", text)
        self.assertIn("report_timing_summary", text)
        self.assertIn("report_power", text)
        self.assertIn("write_checkpoint -force", text)

    def test_source_closure_archive_contains_rtl_and_ip_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            vivado = root / "vivado"
            vivado.mkdir()
            (vivado / "GeneratedAxiDdrTop.sv").write_text("module GeneratedAxiDdrTop; endmodule\n", encoding="utf-8")
            resources = root / "src" / "main" / "resources" / "spatialaccagent" / "numeric"
            resources.mkdir(parents=True)
            (resources / "exp2_fraction_q24.mem").write_text("00000000\n", encoding="utf-8")
            modules = root / "fpga_ip_modules.txt"
            modules.write_text("fp_add_sp_12\n", encoding="utf-8")
            generator = root / "gen_xilinx_fp_ips_23.tcl"
            generator.write_text("puts fp_ip\n", encoding="utf-8")
            scala = root / "src" / "main" / "scala" / "Design.scala"
            scala.parent.mkdir(parents=True)
            scala.write_text("object Design\n", encoding="utf-8")
            runtime = root / "runtime" / "runtime_config.json"
            runtime.parent.mkdir(parents=True)
            runtime.write_text("{}\n", encoding="utf-8")
            archive = root / "closure.tar.gz"

            create_source_closure_archive(archive, vivado, modules, generator)

            import tarfile

            with tarfile.open(archive, "r:gz") as bundle:
                names = set(bundle.getnames())
        self.assertIn("generated_vivado/GeneratedAxiDdrTop.sv", names)
        self.assertIn("src/main/resources/spatialaccagent/numeric/exp2_fraction_q24.mem", names)
        self.assertIn("fpga_ip_modules.txt", names)
        self.assertIn("gen_xilinx_fp_ips_23.tcl", names)
        self.assertIn("analysis_context/src/main/scala/Design.scala", names)
        self.assertIn("analysis_context/runtime/runtime_config.json", names)


if __name__ == "__main__":
    unittest.main()
