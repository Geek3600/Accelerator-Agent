from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.verification import external_simulation_fixture as fixture


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


def object_row(
    object_id: str,
    kind: str,
    path: str,
    *,
    owner_path: str = "",
    properties: dict[str, object] | None = None,
    connected_nets: list[dict[str, str]] | None = None,
    members: list[dict[str, str]] | None = None,
) -> dict[str, object]:
    return {
        "object_id": object_id,
        "kind": kind,
        "bd_path": "/project/design.bd",
        "path": path,
        "owner_path": owner_path,
        "properties": properties or {},
        "connected_nets": connected_nets or [],
        "members": members or [],
    }


class ExternalFixtureCase:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.run_dir = root / "run"
        self.board_dir = self.run_dir / "verification" / "board_interface"
        self.project = root / "opaque_project.xpr"
        self.xci_a = root / "configured_a.xci"
        self.xci_b = root / "configured_b.xci"
        self.project.write_text("project-authority\n", encoding="utf-8")
        self.xci_a.write_text("configured-a\n", encoding="utf-8")
        self.xci_b.write_text("configured-b\n", encoding="utf-8")
        self.tool_root = root / "opaque_tool_installation"
        executable = self.tool_root / "bin" / "vivado"
        executable.parent.mkdir(parents=True)
        executable.write_text("tool\n", encoding="utf-8")
        self.executable = str(executable)
        self.installation_sv = self.tool_root / "data" / "hdl" / "installation_model.sv"
        self.installation_vhd = self.tool_root / "data" / "hdl" / "installation_component.vhd"
        self.installation_sv.parent.mkdir(parents=True)
        self.installation_sv.write_text(
            "package installation_model; endpackage\n", encoding="utf-8"
        )
        self.installation_vhd.write_text(
            "entity installation_component is end entity;\n"
            "architecture rtl of installation_component is begin end architecture;\n",
            encoding="utf-8",
        )
        self.library_dirs = {
            "vendor_lib": self.tool_root / "compiled_libraries" / "vendor_lib",
            "installation_lib": self.tool_root / "compiled_libraries" / "installation_lib",
        }
        for directory in self.library_dirs.values():
            directory.mkdir(parents=True)
        self.setup = root / "external_simulation_lib" / "synopsys_sim.setup"
        self.setup.parent.mkdir(parents=True)
        self.setup.write_text(
            "VCS_BUILTIN : $SYNOPSYS_SIM/$ARCH\n"
            + "\n".join(
                f"{library} : {directory}" for library, directory in self.library_dirs.items()
            )
            + "\n",
            encoding="utf-8",
        )
        self.part = "vendor-part-from-project"
        self.version = "tool-version-from-project"
        self.facts = self._facts()
        self.identity = self._identity()
        self._write_inputs()

    def _provider_objects(
        self,
        suffix: str,
        component: str,
        net: str,
        external_path: str,
    ) -> list[dict[str, object]]:
        cell_path = f"/provider_{suffix}"
        config = {
            "VLNV": "vendor.example:ip:opaque_controller:7.3",
            "CONFIG.Component_Name": component,
            "CONFIG.BusWidth": "73",
            "CONFIG.RankCount": "3",
            "CONFIG.TimingProfile": "profile-from-xci",
        }
        return [
            object_row(
                f"cell:{suffix}",
                "cell",
                cell_path,
                properties=config,
            ),
            object_row(
                f"port:{suffix}",
                "interface_port",
                external_path,
                properties={"VLNV": "vendor.example:interface:opaque_physical:4.1", "MODE": "Master"},
                connected_nets=[{"kind": "interface_net", "path": net}],
            ),
            object_row(
                f"net:{suffix}",
                "interface_net",
                net,
                members=[{"kind": "interface_pin", "path": f"{cell_path}/PHYSICAL"}],
            ),
            object_row(
                f"interface-pin:{suffix}",
                "interface_pin",
                f"{cell_path}/PHYSICAL",
                owner_path=cell_path,
                properties={"VLNV": "vendor.example:interface:opaque_physical:4.1", "MODE": "Master"},
                connected_nets=[{"kind": "interface_net", "path": net}],
                members=[
                    {"kind": "pin", "path": f"{cell_path}/payload"},
                    {"kind": "pin", "path": f"{cell_path}/strobe"},
                ],
            ),
            object_row(
                f"pin:{suffix}:payload",
                "pin",
                f"{cell_path}/payload",
                owner_path=cell_path,
                properties={"DIR": "IO", "LEFT": "72", "RIGHT": "0"},
            ),
            object_row(
                f"pin:{suffix}:strobe",
                "pin",
                f"{cell_path}/strobe",
                owner_path=cell_path,
                properties={"DIR": "O", "LEFT": "2", "RIGHT": "0"},
            ),
        ]

    def _facts(self) -> dict[str, object]:
        objects = [
            *self._provider_objects("a", "configured_a", "/external_net_a", "/external_a"),
            *self._provider_objects("b", "configured_b", "/external_net_b", "/external_b"),
            object_row(
                "pin:a:calibration",
                "pin",
                "/provider_a/calibration",
                owner_path="/provider_a",
                properties={"DIR": "O"},
            ),
        ]
        return {
            "schema_version": "test.vivado.facts.v1",
            "status": "pass",
            "project": {
                "path": str(self.project),
                "part": self.part,
                "vivado_version": self.version,
                "simulation_fileset": "opaque_simset",
                "top_module": "opaque_wrapper",
            },
            "simulation": {
                "source_files": [
                    {
                        "source_id": "source:selected-timing",
                        "remote_path": str(self.root / "timing.sv"),
                        "parent_composite_file": str(self.xci_a),
                        "owner_cell_ids": ["cell:a"],
                    },
                    {
                        "source_id": "source:equivalent-provider",
                        "remote_path": str(self.root / "other_timing.sv"),
                        "parent_composite_file": str(self.xci_b),
                        "owner_cell_ids": ["cell:b"],
                    },
                ]
            },
            "objects": objects,
            "blockers": [],
        }

    def _identity(self) -> dict[str, object]:
        return {
            "schema_version": "test.identity.v1",
            "status": "pass",
            "sample_project": str(self.project),
            "sample_project_sha256": fixture.sha256_file(self.project),
            "vivado_facts_path": str(self.board_dir / "vivado_board_facts.json"),
            "vivado_facts_sha256": "pending",
            "vivado_tool": {
                "host": "",
                "port": 22,
                "executable": self.executable,
            },
            "timing_contract": {
                "memory_timing_model": {"source_ids": ["source:selected-timing"]},
                "calibration": [{"driver_object_id": "pin:a:calibration"}],
            },
        }

    def _write_inputs(self) -> None:
        write_json(
            self.run_dir / "input" / "tool_profile.json",
            {
                "tools": [
                    {
                        "role": "synthesis_implementation_bitstream_generation",
                        "name": "vivado",
                        "host": "",
                        "port": 22,
                        "executable": self.executable,
                    }
                ]
            },
        )
        write_json(
            self.run_dir / "input" / "target_board_profile.json",
            {
                "board": {"fpga_part": self.part},
                "board_pass_criteria": {"required_fpga_part": self.part},
            },
        )
        self.rewrite_facts_and_identity()

    def rewrite_facts_and_identity(self) -> None:
        facts_path = self.board_dir / "vivado_board_facts.json"
        write_json(facts_path, self.facts)
        self.identity["vivado_facts_sha256"] = fixture.sha256_file(facts_path)
        write_json(self.board_dir / "board_source_identity.json", self.identity)

    def fake_exporter(self, call_counter: list[int] | None = None):
        vendor_source = self.root / "vendor component model.sv"
        export_script = self.root / "compile_fixture.sh"
        glbl = self.root / "glbl.v"
        firmware = self.root / "controller_firmware.elf"
        runtime_script = self.root / "simulate_fixture.do"
        runtime_data = self.root / "runtime_data" / "state.bin"
        export_notes = self.root / "export_notes.txt"
        include_dir = self.root / "model_includes"
        header = include_dir / "model_types.svh"
        include_dir.mkdir(parents=True)
        header.write_text("typedef logic [7:0] model_byte_t;\n", encoding="utf-8")
        runtime_data.parent.mkdir(parents=True)
        runtime_data.write_bytes(b"runtime-state\n")
        export_notes.write_text("unreferenced export metadata\n", encoding="utf-8")
        vendor_source.write_text(
            'module vendor_fixture_top; initial $readmemh("runtime_data/state.bin", memory); endmodule\n',
            encoding="utf-8",
        )
        glbl.write_text("module glbl; endmodule\n", encoding="utf-8")
        firmware.write_bytes(b"\x7fELF-not-hdl\n")
        runtime_script.write_text("run\n", encoding="utf-8")
        export_script.write_text(
            "\n".join(
                [
                    'vlogan_opts="-full64"',
                    'vhdlan_opts="-full64"',
                    "compile()",
                    "{",
                    f'  vlogan -work vendor_lib $vlogan_opts -sverilog +incdir+"{include_dir}" ' + "\\",
                    f'    "{vendor_source}" ' + "\\",
                    f'    "{self.installation_sv}" ' + "\\",
                    "    2>&1 | tee -a vlogan.log",
                    "  vhdlan -work installation_lib $vhdlan_opts " + "\\",
                    f'    "{self.installation_vhd}" ' + "\\",
                    "    2>&1 | tee -a vhdlan.log",
                    f'  vlogan -work vendor_lib $vlogan_opts "{glbl}"',
                    "}",
                    "simulate()",
                    "{",
                    "  ./fixture_simv -do simulate_fixture.do",
                    "}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        def run(authority: dict[str, object], _output_dir: Path, _timeout: int):
            if call_counter is not None:
                call_counter.append(1)
            group = authority["provider_groups"][0]
            group_id = group["configuration_sha256"]
            component = group["representative"]["component_name"]
            missing = "\n".join(
                [
                    "Missing instances for simulation:",
                    "Index  Instance Path  File Path  Line",
                    "-----  -------------  ---------  ----",
                    "< empty >",
                ]
            )
            raw_export = {
                "schema_version": fixture.EXPORT_SCHEMA_VERSION,
                "metadata": {"vivado_version": self.version, "export_status": "pass"},
                "providers": [
                    {
                        "group_id": group_id,
                        "component_name": component,
                        "status": "pass",
                        "source_part": self.part,
                        "ip_properties": {"VLNV": group["configuration"]["vlnv"]},
                        "ip_file": group["representative"]["configured_ip"]["remote_path"],
                        "example": {
                            "status": "pass",
                            "project": str(self.root / "example_project"),
                            "part": self.part,
                            "diagnostic": "",
                        },
                        "fileset_count": 1,
                        "filesets": [
                            {
                                "index": 0,
                                "name": "vendor_simulation_fileset",
                                "status": "pass",
                                "top": "vendor_fixture_top",
                                "top_lib": "vendor_lib",
                                "source_set": "vendor_sources",
                                "diagnostic": "",
                                "sources": [
                                    {
                                        "compile_order": 0,
                                        "remote_path": str(vendor_source),
                                        "properties": {
                                            "LIBRARY": "vendor_lib",
                                            "FILE_TYPE": "SystemVerilog",
                                            "USED_IN": "simulation",
                                        },
                                    },
                                    {
                                        "compile_order": 1,
                                        "remote_path": str(firmware),
                                        "properties": {
                                            "LIBRARY": "vendor_lib",
                                            "FILE_TYPE": "ELF",
                                            "USED_IN": "simulation",
                                        },
                                    },
                                    {
                                        "compile_order": 2,
                                        "remote_path": str(header),
                                        "properties": {
                                            "LIBRARY": "vendor_lib",
                                            "FILE_TYPE": "SystemVerilog Header",
                                            "USED_IN": "simulation",
                                            "IS_GLOBAL_INCLUDE": "true",
                                        },
                                    },
                                ],
                                "missing_status": "pass",
                                "missing_diagnostic": "",
                                "missing_report": missing,
                                "export_status": "pass",
                                "export_diagnostic": "",
                                "export_files": [
                                    {"remote_path": str(export_script), "size_bytes": export_script.stat().st_size},
                                    {"remote_path": str(glbl), "size_bytes": glbl.stat().st_size},
                                    {"remote_path": str(runtime_script), "size_bytes": runtime_script.stat().st_size},
                                    {"remote_path": str(runtime_data), "size_bytes": runtime_data.stat().st_size},
                                    {"remote_path": str(export_notes), "size_bytes": export_notes.stat().st_size},
                                ],
                            }
                        ],
                    }
                ],
            }
            paths = {
                str(vendor_source),
                str(export_script),
                str(glbl),
                str(firmware),
                str(runtime_script),
                str(runtime_data),
                str(export_notes),
                str(header),
                *(
                    str(instance["configured_ip"]["remote_path"])
                    for provider_group in authority["provider_groups"]
                    for instance in provider_group["instances"]
                ),
            }
            payloads = {path: Path(path).read_bytes() for path in paths}
            return raw_export, payloads, {"test_export": True}

        return run


class ExternalSimulationFixtureTests(unittest.TestCase):
    def test_structural_authority_finds_equivalent_external_providers_without_names(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            case = ExternalFixtureCase(Path(temp))
            authority, blockers = fixture.derive_external_fixture_authority(case.run_dir)
            self.assertEqual(blockers, [])
            self.assertEqual(len(authority["provider_groups"]), 1)
            instances = authority["provider_groups"][0]["instances"]
            self.assertEqual({row["cell_id"] for row in instances}, {"cell:a", "cell:b"})
            self.assertEqual(
                {row["selected_by_runtime_timing_authority"] for row in instances},
                {False, True},
            )
            self.assertEqual(
                {len(row["external_interfaces"][0]["provider_member_pins"]) for row in instances},
                {2},
            )
            self.assertTrue(authority["policy"]["provider_names_or_model_names_not_used_for_selection"])

    def test_materialization_hashes_every_payload_and_reuses_exact_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            case = ExternalFixtureCase(Path(temp))
            calls: list[int] = []
            exporter = case.fake_exporter(calls)
            first = fixture.materialize_external_simulation_fixture(
                case.run_dir, exporter=exporter
            )
            self.assertEqual(first["status"], "pass", first.get("blockers"))
            self.assertEqual(len(calls), 1)
            self.assertGreaterEqual(len(first["materialized_files"]), 13)
            compile_authority = first["compile_authority"]
            self.assertEqual(compile_authority["status"], "pass")
            for row in first["materialized_files"]:
                path = Path(row["path"])
                self.assertEqual(row["sha256"], fixture.sha256_file(path))
                self.assertEqual(row["size_bytes"], path.stat().st_size)
                self.assertTrue(row["source_id"].startswith("external-fixture-source:"))
                self.assertTrue(row["artifact_id"].startswith("external-fixture-artifact:"))
                self.assertEqual(Path(row["staged_path"]).name, Path(row["remote_path"]).name)
                self.assertEqual(path.name, Path(row["remote_path"]).name)

            compiler_input_names = {
                Path(row["remote_path"]).name
                for row in compile_authority["compiler_inputs"]
            }
            self.assertEqual(
                compiler_input_names,
                {
                    "vendor component model.sv",
                    case.installation_sv.name,
                    case.installation_vhd.name,
                },
            )
            self.assertEqual(
                {Path(row["remote_path"]).name for row in compile_authority["hdl_export_artifacts"]},
                {"glbl.v"},
            )
            runtime_names = {
                Path(row["remote_path"]).name
                for row in compile_authority["runtime_auxiliary_files"]
            }
            self.assertEqual(runtime_names, {"simulate_fixture.do", "state.bin"})
            self.assertEqual(
                {
                    Path(row["remote_path"]).name: row["runtime_staged_path"]
                    for row in compile_authority["runtime_auxiliary_files"]
                },
                {
                    "simulate_fixture.do": "simulate_fixture.do",
                    "state.bin": "runtime_data/state.bin",
                },
            )
            self.assertTrue(
                {
                    "controller_firmware.elf",
                    "compile_fixture.sh",
                    "configured_a.xci",
                    "configured_b.xci",
                    "synopsys_sim.setup",
                    "model_types.svh",
                    "export_notes.txt",
                }.isdisjoint(runtime_names)
            )
            self.assertNotIn(
                "controller_firmware.elf",
                {Path(row["remote_path"]).name for row in compile_authority["compile_sources"]},
            )
            self.assertEqual(
                [row["driver"] for row in compile_authority["compile_invocations"]],
                ["vlogan", "vhdlan", "vlogan"],
            )
            include_rows = compile_authority["include_directories"]
            self.assertEqual(len(include_rows), 1)
            include_row = include_rows[0]
            self.assertEqual(Path(include_row["remote_path"]).name, "model_includes")
            header_row = next(
                row
                for row in first["materialized_files"]
                if Path(row["remote_path"]).name == "model_types.svh"
            )
            self.assertEqual(include_row["member_source_ids"], [header_row["source_id"]])
            self.assertEqual(
                include_row["staged_path"],
                str(Path(header_row["staged_path"]).parent),
            )
            self.assertEqual(
                compile_authority["compile_invocations"][0]["include_directory_ids"],
                [include_row["include_dir_id"]],
            )
            self.assertEqual(
                compile_authority["compile_invocations"][1]["include_directory_ids"], []
            )
            self.assertEqual(
                {row["library"] for row in compile_authority["synopsys_sim_setup"]["required_library_directories"]},
                set(case.library_dirs),
            )
            self.assertEqual(
                compile_authority["synopsys_sim_setup"]["coverage_strength"],
                {"covered_library_count": 2, "compile_work_library_count": 2},
            )
            self.assertTrue(
                all(
                    row["exists"]
                    for row in compile_authority["synopsys_sim_setup"]["required_library_directories"]
                )
            )
            installation_authority = compile_authority[
                "vivado_installation_hdl_authority"
            ]
            self.assertEqual(installation_authority["status"], "pass")
            self.assertEqual(
                installation_authority["selected_root"], str(case.tool_root.resolve())
            )
            self.assertEqual(
                {
                    Path(row["remote_path"]).name
                    for row in installation_authority["files"]
                },
                {case.installation_sv.name, case.installation_vhd.name},
            )
            self.assertTrue(
                all(row.get("sha256") for row in installation_authority["files"])
            )
            declared = {
                (unit["kind"], unit["name"])
                for row in compile_authority["compile_sources"]
                for unit in row["declared_design_units"]
            }
            self.assertIn(("module", "vendor_fixture_top"), declared)
            self.assertIn(("package", "installation_model"), declared)
            self.assertIn(("entity", "installation_component"), declared)
            second = fixture.materialize_external_simulation_fixture(
                case.run_dir, exporter=exporter
            )
            self.assertEqual(second["status"], "pass")
            self.assertTrue(second["cache_reused"])
            self.assertEqual(len(calls), 1)

    def test_local_projection_schema_change_reuses_hash_valid_vivado_export(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            case = ExternalFixtureCase(Path(temp))
            calls: list[int] = []
            exporter = case.fake_exporter(calls)
            first = fixture.materialize_external_simulation_fixture(case.run_dir, exporter=exporter)
            self.assertEqual(first["status"], "pass", first.get("blockers"))
            report_path = case.board_dir / "external_simulation_fixture.json"
            cached = json.loads(report_path.read_text(encoding="utf-8"))
            cached["schema_version"] = "spatialaccagent.external_simulation_fixture.v1"
            cached["authority"]["implementation"]["sha256"] = "previous-local-projection"
            cached["authority"]["authority_sha256"] = fixture.canonical_sha256(
                {
                    key: value
                    for key, value in cached["authority"].items()
                    if key != "authority_sha256"
                }
            )
            cached["authority_sha256"] = cached["authority"]["authority_sha256"]
            supplement_paths = {
                str(case.installation_sv.resolve()),
                str(case.installation_vhd.resolve()),
                str(case.setup.resolve()),
            }
            retained = []
            for row in cached["materialized_files"]:
                if row["remote_path"] in supplement_paths:
                    Path(row["path"]).unlink()
                else:
                    retained.append(row)
            cached["materialized_files"] = retained
            cached["contract_sha256"] = fixture._contract_sha256(cached)
            write_json(report_path, cached)

            projected = fixture.materialize_external_simulation_fixture(
                case.run_dir, exporter=exporter
            )
            self.assertEqual(projected["status"], "pass", projected.get("blockers"))
            self.assertEqual(len(calls), 1)
            self.assertTrue(projected["transport"]["vivado_export_cache_reused"])
            self.assertTrue(projected["transport"]["local_projection_recomputed"])
            self.assertEqual(projected["schema_version"], fixture.SCHEMA_VERSION)
            self.assertTrue(
                supplement_paths.issubset(
                    {row["remote_path"] for row in projected["materialized_files"]}
                )
            )

    def test_matching_but_damaged_export_cache_fails_without_rerunning_export(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            case = ExternalFixtureCase(Path(temp))
            calls: list[int] = []
            exporter = case.fake_exporter(calls)
            first = fixture.materialize_external_simulation_fixture(case.run_dir, exporter=exporter)
            self.assertEqual(first["status"], "pass")
            Path(first["materialized_files"][0]["path"]).unlink()

            report = fixture.materialize_external_simulation_fixture(case.run_dir, exporter=exporter)
            self.assertEqual(report["status"], "fail")
            self.assertEqual(len(calls), 1)
            self.assertTrue(
                any("missing or hash-invalid" in value for value in report["blockers"]),
                report["blockers"],
            )

    def test_same_directory_basename_content_conflict_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            case = ExternalFixtureCase(Path(temp))
            complete = case.fake_exporter()

            def conflicting(authority: dict[str, object], output_dir: Path, timeout: int):
                raw, payloads, transport = complete(authority, output_dir, timeout)
                canonical = str(case.root / "conflict.do")
                alias = str(case.root / "alias" / ".." / "conflict.do")
                export_files = raw["providers"][0]["filesets"][0]["export_files"]
                export_files.extend(
                    [
                        {"remote_path": canonical, "size_bytes": 1},
                        {"remote_path": alias, "size_bytes": 1},
                    ]
                )
                payloads[canonical] = b"a"
                payloads[alias] = b"b"
                return raw, payloads, transport

            report = fixture.materialize_external_simulation_fixture(
                case.run_dir, exporter=conflicting
            )
            self.assertEqual(report["status"], "fail")
            self.assertTrue(
                any("basename/content conflict" in value for value in report["blockers"]),
                report["blockers"],
            )

    def test_multiple_usable_synopsys_setups_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            case = ExternalFixtureCase(Path(temp))
            second = case.tool_root / "alternative" / "synopsys_sim.setup"
            second.parent.mkdir(parents=True)
            second.write_text(case.setup.read_text(encoding="utf-8"), encoding="utf-8")
            report = fixture.materialize_external_simulation_fixture(
                case.run_dir, exporter=case.fake_exporter()
            )
            self.assertEqual(report["status"], "fail")
            self.assertTrue(
                any("equal strongest compile-library coverage" in value for value in report["blockers"]),
                report["blockers"],
            )

    def test_synopsys_setup_with_zero_compile_library_coverage_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            case = ExternalFixtureCase(Path(temp))
            setup, _, blockers = fixture._discover_synopsys_setup(
                case.identity,
                [{"work_library": "unmapped_work_library"}],
                0,
            )
            self.assertEqual(setup, {})
            self.assertTrue(
                any("covers any VCS compile work library" in value for value in blockers),
                blockers,
            )

    def test_unique_strongest_synopsys_setup_coverage_is_selected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            case = ExternalFixtureCase(Path(temp))
            partial = case.tool_root / "partial" / "synopsys_sim.setup"
            partial.parent.mkdir(parents=True)
            partial.write_text(
                f"vendor_lib : {case.library_dirs['vendor_lib']}\n",
                encoding="utf-8",
            )
            report = fixture.materialize_external_simulation_fixture(
                case.run_dir, exporter=case.fake_exporter()
            )
            self.assertEqual(report["status"], "pass", report.get("blockers"))
            selected = report["compile_authority"]["synopsys_sim_setup"]
            self.assertEqual(selected["remote_path"], str(case.setup.resolve()))
            self.assertEqual(
                selected["coverage_strength"],
                {"covered_library_count": 2, "compile_work_library_count": 2},
            )

    def test_configured_ip_hash_change_invalidates_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            case = ExternalFixtureCase(Path(temp))
            calls: list[int] = []
            exporter = case.fake_exporter(calls)
            first = fixture.materialize_external_simulation_fixture(case.run_dir, exporter=exporter)
            self.assertEqual(first["status"], "pass")
            case.xci_b.write_text("changed-configured-b\n", encoding="utf-8")
            second = fixture.materialize_external_simulation_fixture(case.run_dir, exporter=exporter)
            self.assertEqual(second["status"], "pass")
            self.assertNotEqual(first["authority_sha256"], second["authority_sha256"])
            self.assertEqual(len(calls), 2)

    def test_provider_must_be_connected_to_an_external_interface(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            case = ExternalFixtureCase(Path(temp))
            for row in case.facts["objects"]:
                if row.get("object_id") == "port:a":
                    row["connected_nets"] = []
            case.rewrite_facts_and_identity()
            _, blockers = fixture.derive_external_fixture_authority(case.run_dir)
            self.assertTrue(
                any("do not structurally resolve" in blocker for blocker in blockers),
                blockers,
            )

    def test_legacy_fixture_path_is_rejected_before_read(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            case = ExternalFixtureCase(Path(temp))
            legacy = fixture.FORBIDDEN_LEGACY_ROOT / "configured_a.xci"
            case.facts["simulation"]["source_files"][0]["parent_composite_file"] = str(legacy)
            case.rewrite_facts_and_identity()
            observed_reads: list[str] = []
            original_source_bytes = fixture.source_bytes

            def guarded_read(host: str, path: str, timeout: int, port: int = 22) -> bytes:
                observed_reads.append(path)
                if fixture._is_forbidden_legacy_path(path):
                    raise AssertionError("legacy path was read")
                return original_source_bytes(host, path, timeout, port)

            with mock.patch.object(fixture, "source_bytes", side_effect=guarded_read):
                _, blockers = fixture.derive_external_fixture_authority(case.run_dir)
            self.assertTrue(any("forbidden legacy fixture" in value for value in blockers), blockers)
            self.assertFalse(any(fixture._is_forbidden_legacy_path(path) for path in observed_reads))

    def test_incomplete_export_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            case = ExternalFixtureCase(Path(temp))
            complete_exporter = case.fake_exporter()

            def incomplete(authority: dict[str, object], output_dir: Path, timeout: int):
                raw, payloads, transport = complete_exporter(authority, output_dir, timeout)
                raw["providers"][0]["filesets"][0]["export_files"] = []
                return raw, payloads, transport

            report = fixture.materialize_external_simulation_fixture(
                case.run_dir, exporter=incomplete
            )
            self.assertEqual(report["status"], "fail")
            self.assertTrue(any("no successful VCS export_simulation" in value for value in report["blockers"]))


if __name__ == "__main__":
    unittest.main()
