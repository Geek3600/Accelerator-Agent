from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.synthesis.app_shell_runtime_vivado import build_tcl, create_source_closure_archive


class AppShellRuntimeVivadoTest(unittest.TestCase):
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
            archive = root / "closure.tar.gz"

            create_source_closure_archive(archive, vivado, modules, generator)

            import tarfile

            with tarfile.open(archive, "r:gz") as bundle:
                names = set(bundle.getnames())
        self.assertIn("generated_vivado/GeneratedAxiDdrTop.sv", names)
        self.assertIn("src/main/resources/spatialaccagent/numeric/exp2_fraction_q24.mem", names)
        self.assertIn("fpga_ip_modules.txt", names)
        self.assertIn("gen_xilinx_fp_ips_23.tcl", names)


if __name__ == "__main__":
    unittest.main()
