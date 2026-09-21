import json
import tempfile
import unittest
from pathlib import Path

from accagent.framework.fpga_ip_contract import (
    check_fpga_ip_generation_contract,
    check_fpga_ip_simulation_closure,
    check_fpga_ip_template_contract,
    discover_fp_modules,
    refresh_fpga_ip_simulation_closure,
    simulation_source_contract,
)


def _closure(path: Path) -> None:
    module_manifest = path.parent / "fpga_ip_modules.txt"
    module_manifest.write_text(
        "fp_add_sp_12\nfp_f2i_s16_sp_7\nfp_i2f_s36_sp_7\n",
        encoding="utf-8",
    )
    path.write_text(
        json.dumps(
            {
                "status": "ready",
                "policy": simulation_source_contract(),
                "ip_generation_tcl": "/work/gen_ip.tcl",
                "ip_output_dir": "/work/vivado_ip",
                "ip_project_dir": "/work/vivado_project",
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
        ),
        encoding="utf-8",
    )


class FpgaIpContractTest(unittest.TestCase):
    def test_template_maps_large_cache_to_explicit_xpm_uram(self) -> None:
        source = Path(
            "accagent/framework/templates/operator_chisel/PhysicalResources.scala"
        ).read_text(encoding="utf-8")
        self.assertIn('case "cache" => if (largeCacheMemoryBackend == "xpm_uram") "ultra" else "block"', source)
        self.assertNotIn('case "cache" => if (largeCacheMemoryBackend == "xpm_uram") "auto" else "block"', source)

    def test_ip_generator_requires_dsp_backed_pe_multipliers(self) -> None:
        generator = Path("scripts/synthesis/gen_xilinx_fp_ips_23.tcl")
        report = check_fpga_ip_generation_contract(generator)
        self.assertEqual(report["status"], "pass", report["errors"])

        with tempfile.TemporaryDirectory() as temp_dir:
            broken = Path(temp_dir) / "gen_ip.tcl"
            broken.write_text("CONFIG.Operation_Type {Multiply}\n", encoding="utf-8")
            self.assertEqual(check_fpga_ip_generation_contract(broken)["status"], "fail")

    def test_discovers_actual_fp_modules_and_refreshes_closure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "Top.sv").write_text(
                "fp_add_sp_12 add_ip (.*);\nfp_i2f_s36_sp_7 convert_ip (.*);\n",
                encoding="utf-8",
            )
            (root / "vivado").mkdir()
            (root / "vivado" / "Top.sv").write_text(
                "fp_f2i_s16_sp_7 output_ip (.*);\n",
                encoding="utf-8",
            )
            closure = root / "closure.json"
            _closure(closure)
            modules = refresh_fpga_ip_simulation_closure(root, closure)

            self.assertEqual(
                modules,
                ["fp_add_sp_12", "fp_f2i_s16_sp_7", "fp_i2f_s36_sp_7"],
            )
            self.assertEqual(discover_fp_modules(root), modules)
            self.assertEqual(check_fpga_ip_simulation_closure(closure)["status"], "pass")

    def test_ip_simulation_closure_requires_real_vcs_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            closure = Path(temp_dir) / "closure.json"
            _closure(closure)
            self.assertEqual(check_fpga_ip_simulation_closure(closure)["status"], "pass")

            payload = json.loads(closure.read_text(encoding="utf-8"))
            del payload["vcs_compile_requirements"]["global_module"]
            closure.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(check_fpga_ip_simulation_closure(closure)["status"], "fail")

    def test_template_contract_rejects_nonphysical_implementations(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            (tmp_path / "PhysicalResources.scala").write_text(
                '\n'.join([
                    'configureFpgaIp', '"fp_add_sp_12"', '"fp_sub_sp_12"',
                    '"fp_mul_sp_9"', '"fp_div_sp_29"', '"fp_sqrt_sp_29"',
                    '"xpm_memory_sdpram"', 'PhysicalStreamFifo',
                ]),
                encoding="utf-8",
            )
            (tmp_path / "Bad.scala").write_text(
                'val q = new Queue(UInt(8.W), 2)\n'
                'val m = SyncReadMem(4, UInt(8.W))\n'
                'val x = PhysicalMath.mulFp32(a, b)\n',
                encoding="utf-8",
            )
            report = check_fpga_ip_template_contract(tmp_path)
        self.assertEqual(report["status"], "fail")
        self.assertGreaterEqual(
            {row["kind"] for row in report["violations"]},
            {"generic_queue_backend", "sync_read_mem_backend", "unhandshaked_physical_fp_helper"},
        )
