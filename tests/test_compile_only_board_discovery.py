import copy
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from accagent.framework import board_acceptance_contract as contract
from accagent.framework.stage_repair_execute import (
    BOARD_INTEGRATION_REPAIR_SCHEMA, board_integration_repair_context, board_integration_prompt_rules,
    expand_agent_text_repeats, apply_agent_file_edits, exact_board_agent_task,
)
from accagent.framework.stage_llm import (
    _compact_exact_board_generation_kernel_inputs,
    _compact_verilog_module_interface,
    compact_verification_capability_repair_package,
    compact_board_post_vcs_repair_package,
    compact_retry_prompt,
)
from scripts.verification import sample_project_board_interface_impl as impl
from tests import test_sample_project_board_interface_discovery as fixtures
from tests.test_board_acceptance_contract import _case


class CompileOnlyBoardDiscoveryTests(unittest.TestCase):
    def test_compile_only_compact_request_omits_runtime_observation_rules(self):
        with patch("accagent.framework.stage_llm.exact_board_compact_request_errors", return_value=[]):
            prompt = compact_retry_prompt(
                "exact_board_integration_generation_agent", "repair_execution",
                exact_board_agent_task("repair"),
                {"verification_capability_repair_package": {
                    "verification_scope": "board_axi_ddr_closure",
                    "current_board_vcs_feedback": {"status": "ready"},
                }}, BOARD_INTEGRATION_REPAIR_SCHEMA,
                prompt_rules=board_integration_prompt_rules("repair"),
            )
        self.assertIn("entire certified family", prompt)
        self.assertIn("repeat_expansions", prompt)
        self.assertNotIn("Layer-3 observation must be unconditional", prompt)
        self.assertNotIn("current_signal_epoch is the only dynamic hardware evidence", prompt)

    def test_agent_numbered_source_expansion_keeps_literal_sv_braces(self):
        edit = {"path": "adapter.sv", "operation": "replace_text", "content": "",
                "text_replacements": [{"old_text": "// ports", "new_text": "@@PORTS@@"}],
                "repeat_expansions": [{"marker": "@@PORTS@@", "first_index": 2,
                    "last_index": 4, "template": "wire [7:0] p_{index} = {a[{index_plus_10}], b};\n"}]}
        expanded = expand_agent_text_repeats(edit)
        self.assertEqual(expanded["text_replacements"][0]["new_text"],
                         "".join(f"wire [7:0] p_{i} = {{a[{i + 10}], b}};\n" for i in range(2, 5)))
        self.assertNotIn("repeat_expansions", expanded)
        self.assertEqual(edit["text_replacements"][0]["new_text"], "@@PORTS@@")
        for bad in [dict(edit, path="manifest.json"),
                    dict(edit, content="@@PORTS@@"),
                    dict(edit, repeat_expansions=[dict(edit["repeat_expansions"][0], last_index=100_000)])]:
            with self.assertRaises(ValueError):
                expand_agent_text_repeats(bad)

    def test_agent_numbered_source_expansion_uses_normal_patch_executor(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp).resolve()
            target = run / "generated/board_integration/adapter.sv"
            target.parent.mkdir(parents=True)
            target.write_text("module Adapter;\n// ports\nendmodule\n")
            prior_hash = hashlib.sha256(target.read_bytes()).hexdigest()
            result = apply_agent_file_edits({"status": "ready_to_apply", "file_edits": [{
                "path": str(target), "operation": "replace_text", "content": "",
                "expected_sha256": prior_hash,
                "text_replacements": [{"old_text": "// ports", "new_text": "@@PORTS@@"}],
                "repeat_expansions": [{"marker": "@@PORTS@@", "first_index": 0,
                    "last_index": 36026, "template": "wire [31:0] scale_{index}; // loadable channel metadata configuration storage connection\n"}],
            }]}, run, run / "repair_execution", allowed_exact_files={target},
                allow_board_integration=True, require_exact_source_hash=True)
            self.assertEqual(result["status"], "pass", result)
            source = target.read_text()
            self.assertIn("wire [31:0] scale_36026;", source)
            self.assertEqual(source.count("wire [31:0] scale_"), 36027)
            self.assertGreater(len(source.encode()), 2_000_000)
            self.assertNotIn("@@PORTS@@", source)

            # An ordinary oversized edit still uses the existing bound.
            rejected = apply_agent_file_edits({"status": "ready_to_apply", "file_edits": [{
                "path": str(target), "operation": "replace", "content": source + "// changed\n",
                "expected_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            }]}, run, run / "repair_execution", allowed_exact_files={target},
                allow_board_integration=True, require_exact_source_hash=True)
            self.assertIn("implementation patch exceeds the 2 MB bounded-repair limit", rejected["blockers"])
            self.assertEqual(target.read_text(), source)

            # A small anchored edit to an already large board adapter is not
            # a multi-megabyte LLM payload and must remain executable.
            edited = apply_agent_file_edits({"status": "ready_to_apply", "file_edits": [{
                "path": str(target), "operation": "replace_text", "content": "",
                "expected_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                "text_replacements": [{"old_text": "wire [31:0] scale_36026;",
                                       "new_text": "wire [31:0] scale_36026 = cfg;"}],
            }]}, run, run / "repair_execution", allowed_exact_files={target},
                allow_board_integration=True, require_exact_source_hash=True)
            self.assertEqual(edited["status"], "pass", edited)
            self.assertIn("scale_36026 = cfg", target.read_text())

    def test_compile_repair_keeps_kernel_interface_and_scale_design_inputs(self):
        adaptive = {
            "kernel_binding_design_inputs": {
                "certified_top_sources": [{"interface_contract": {
                    "ordered_port_groups": [{"name": "io_scale", "width": 32}],
                }}],
                "current_generator_sources": [{"content": "scale source semantics"}],
            },
            "target_board_profile": {"value": {"memory_system": {"address_map": {"ddr_base": "0x2800000000"}}}},
            "shared_board_source_index": {"rows": [{"source_id": "board-source"}]},
            "exact_board_source_identity": {"value": {"status": "pass"}},
            "model_derived_memory_layout": {"value": {"weight_storage_terms": ["scales"]}},
            "full_weight_image_manifest": {"value": {"scale_consumer_binding": "qkv"}},
        }
        result = compact_board_post_vcs_repair_package({
            "current_board_vcs_feedback": {"runner_report": {"value": {
                "compile": {"status": "fail"},
            }}},
            "exact_board_integration_repair_context": {"adaptive_design_inputs": copy.deepcopy(adaptive)},
        })
        self.assertEqual(result["exact_board_integration_repair_context"]["adaptive_design_inputs"], adaptive)

    def test_deterministic_preflight_repair_can_create_its_missing_manifest(self):
        manifest_authority_path = (
            "accagent/runs/test_run/generated/memory/dut_weight_binding_manifest.json"
        )
        manifest_path = str((Path.cwd() / manifest_authority_path).resolve())
        source_path = "/run/generated/board_integration/accelerator.sv"
        source_text = "module generated_accelerator; endmodule\n"
        source_sha256 = hashlib.sha256(source_text.encode()).hexdigest()
        inputs = {
            "verification_capability_repair_package": {
                "generation_phase_contract": {
                    "status": "repair_deterministic_preflight",
                    "current_preflight_feedback_ready": True,
                },
                "current_board_preflight_feedback": {
                    "status": "ready",
                    "blockers": ["the binding manifest is missing"],
                },
                "exact_board_integration_repair_context": {
                    "status": "ready",
                    "required_binding_manifest": manifest_path,
                    "required_generated_root": "/run/generated/board_integration",
                },
                "repair_source_bundle": {
                    "documents": [
                        {
                            "path": source_path,
                            "sha256": source_sha256,
                            "content": source_text,
                        }
                    ],
                    "editable_contract": {
                        "allowed_exact_files": [manifest_authority_path],
                        "current_board_source_files": [
                            {
                                "path": source_path,
                                "sha256": source_sha256,
                            }
                        ],
                        "board_manifest_rewrite_authority": {
                            "target_file": {"path": manifest_authority_path}
                        },
                    },
                },
            }
        }
        certified_top = (
            "module CertifiedTop(\n"
            "  input clock,\n"
            "  input [31:0] data,\n"
            "  output [31:0] result\n"
            ");\n"
            + ("wire unused;\n" * 80_000)
            + "endmodule\n"
        )
        inputs["verification_capability_repair_package"][
            "exact_board_integration_repair_context"
        ]["adaptive_design_inputs"] = {
            "kernel_binding_design_inputs": {
                "certified_top_sources": [
                    {
                        "path": "/run/generated/KernelTop.sv",
                        "sha256": hashlib.sha256(certified_top.encode()).hexdigest(),
                        "size_bytes": len(certified_top.encode()),
                        "content": certified_top,
                    }
                ],
                "current_generator_sources": [],
            }
        }
        inputs["verification_capability_repair_package"][
            "repair_source_bundle"
        ]["editable_contract"]["board_manifest_rewrite_authority"] = {
            "target_file": {"path": manifest_authority_path},
            "stage2_vcs_compile_authority": {
                "module_declaration": certified_top,
            }
        }
        prompt = compact_retry_prompt(
            "exact_board_integration_generation_agent",
            "repair_execution",
            "Create the missing binding manifest from current exact-board evidence",
            inputs,
            BOARD_INTEGRATION_REPAIR_SCHEMA,
        )
        self.assertIn(manifest_path, prompt)
        self.assertIn("repair_deterministic_preflight", prompt)
        self.assertLess(len(prompt.encode()), 100_000)
        self.assertIn('"port_count":3', prompt)
        self.assertIn('"numeric_port_ranges_expand_losslessly":true', prompt)
        self.assertNotIn("wire unused;", prompt)

    def test_large_certified_top_is_projected_to_complete_ordered_port_ranges(self):
        ports = ["  input clock,"]
        ports.extend(f"  input [7:0] io_weight_{index}," for index in range(2048))
        ports.extend(f"  output [31:0] io_result_{index}," for index in range(64))
        source_text = "module KernelTop(\n" + "\n".join(ports) + "\n);\nendmodule\n"
        interface = _compact_verilog_module_interface(source_text)
        self.assertEqual(interface["module"], "KernelTop")
        self.assertEqual(interface["port_count"], 2113)
        self.assertTrue(interface["policy"]["port_order_preserved"])
        self.assertEqual(
            interface["ordered_port_groups"][1],
            {
                "direction": "input",
                "packed_width": "[7:0]",
                "name_pattern": "io_weight_{index}",
                "first_index": 0,
                "last_index": 2047,
                "count": 2048,
                "order_start": 1,
            },
        )

        import hashlib

        source = {
            "path": "/run/generated/KernelTop.sv",
            "sha256": hashlib.sha256(source_text.encode()).hexdigest(),
            "size_bytes": len(source_text.encode()),
            "content": source_text,
        }
        inputs = {
            "verification_capability_repair_package": {
                "generation_phase_contract": {
                    "status": "generation_required_before_probe"
                },
                "exact_board_integration_repair_context": {
                    "status": "ready",
                    "required_binding_manifest": "/run/generated/manifest.json",
                    "adaptive_design_inputs": {
                        "kernel_binding_design_inputs": {
                            "status": "design_required",
                            "certified_top_sources": [source],
                            "current_generator_sources": [],
                        }
                    },
                },
                "repair_source_bundle": {
                    "editable_contract": {
                        "board_manifest_rewrite_authority": {
                            "stage2_vcs_compile_authority": {
                                "module_declaration": (
                                    source_text + ("// compile-plan detail\n" * 1000)
                                ),
                            }
                        }
                    }
                },
            }
        }
        compacted = _compact_exact_board_generation_kernel_inputs(inputs)
        projected = compacted["verification_capability_repair_package"][
            "exact_board_integration_repair_context"
        ]["adaptive_design_inputs"]["kernel_binding_design_inputs"][
            "certified_top_sources"
        ][0]
        self.assertNotIn("content", projected)
        self.assertEqual(projected["sha256"], source["sha256"])
        self.assertEqual(projected["interface_contract"]["port_count"], 2113)
        prompt = compact_retry_prompt(
            "exact_board_integration_generation_agent",
            "repair_execution",
            "Create the exact-board adapter",
            inputs,
            BOARD_INTEGRATION_REPAIR_SCHEMA,
        )
        self.assertLess(len(prompt.encode()), 100_000)
        self.assertNotIn("io_weight_2047", prompt)
        self.assertIn('"last_index":2047', prompt)
        self.assertIn('"source_bytes":', prompt)
        self.assertIn('"numeric_port_ranges_expand_losslessly":true', prompt)

    def test_repeated_compaction_preserves_selected_board_source_bodies(self):
        sources = [
            {'path': '/sources/top.v', 'sha256': 'a' * 64, 'closure_role': 'exact_sample_top'},
            {'path': '/sources/slot.v', 'sha256': 'b' * 64, 'closure_role': 'compute_slot_implementation'},
        ]
        documents = [dict(row, content=f'module selected_{index}; endmodule\n', truncated=False)
                     for index, row in enumerate(sources)]
        package = {
            'verification_scope': 'board_axi_ddr_closure',
            'generation_phase_contract': {'status': 'generation_required_before_probe'},
            'exact_board_integration_repair_context': {
                'status': 'ready',
                'required_binding_manifest': '/generated/memory/dut_weight_binding_manifest.json',
                'adaptive_design_inputs': {
                    'kernel_binding_design_inputs': {
                        'status': 'design_required',
                        'current_generator_sources': [{'path': '/generated/Block.scala',
                                                      'content': 'operator.io.tile <> io.tile(0)'}],
                    },
                    'exact_board_source_identity': {'value': {
                        'selected_simulation_source_closure': {'source_files': sources},
                    }},
                },
            },
            'repair_source_bundle': {'documents': documents, 'editable_contract': {}},
        }
        result = compact_verification_capability_repair_package(package)
        for _ in range(2):
            result = compact_verification_capability_repair_package(result)
            contents = {row['path']: row.get('content')
                        for row in result['repair_source_bundle']['documents']}
            for row in documents:
                self.assertEqual(row['content'], contents.get(row['path']))
        prompt = compact_retry_prompt(
            'exact_board_integration_generation_agent', 'repair_execution', 'Create the connected design',
            {'verification_capability_repair_package': result}, BOARD_INTEGRATION_REPAIR_SCHEMA,
        )
        self.assertIn('module selected_0', prompt)
        self.assertIn('module selected_1', prompt)
        self.assertIn('operator.io.tile <> io.tile(0)', prompt)

    def test_generation_context_defers_runtime_without_hiding_physical_blockers(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch('accagent.framework.stage_repair_execute.exact_board_memory_runtime_authority',
                   side_effect=AssertionError('runtime images are not compile prerequisites')):
            result = board_integration_repair_context({}, Path(directory))
        self.assertTrue(result['runtime_materialization_deferred'])
        self.assertIn('exact board-source identity has not passed', result['blockers'])
        self.assertNotIn('complete Transformer-block weight catalog is unavailable', result['blockers'])
        prompt = '\n'.join(board_integration_prompt_rules())
        self.assertIn('connected synthesizable accelerator integration', prompt)
        self.assertIn('required_binding_manifest', prompt)
        self.assertIn('Do not invent separate verification/case_hierarchy manifests', prompt)
        self.assertIn("scale/shift loading path and configuration address map are design outputs", prompt)
        self.assertIn("Never substitute guessed numeric constants", prompt)

    def test_identity_preflight_keeps_source_and_physical_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            identity_path, _, identity, _ = _case(Path(directory))
            identity.update(validation_policy='vcs_compile_only', functional_semantics_claimed=False,
                            deferred_runtime_evidence=['runtime behavior is unverified'])
            abi = identity['compute_slot_abi']
            abi['control_abi'] = {'port_classifications': [
                dict(port, fact_port_id=port['port_id']) for port in abi['required_ports']
            ]}
            identity['compute_slot_abi_sha256'] = contract.canonical_contract_sha256(abi)
            timing = identity['timing_contract']
            for key in ('timescale', 'timeprecision', 'startup_sequence', 'memory_timing_model'):
                timing.pop(key, None)
            for row in timing['resets']:
                row.pop('minimum_assert_cycles', None)
            for interface in identity['axi_interfaces']:
                interface.pop('supports_unaligned_access', None)
                interface['parameter_evidence_refs'].pop('supports_unaligned_access', None)
            identity['axi_interfaces_sha256'] = contract.canonical_contract_sha256(identity['axi_interfaces'])
            identity['timing_contract_sha256'] = contract.canonical_contract_sha256(timing)
            identity_path.write_text(json.dumps(identity))
            result = contract.validate_exact_board_identity(identity_path)
            self.assertEqual('pass', result['status'], result['blockers'])
            abi['port_bindings'][0]['width_bits'] = 999
            identity['compute_slot_abi_sha256'] = contract.canonical_contract_sha256(abi)
            identity_path.write_text(json.dumps(identity))
            self.assertEqual('fail', contract.validate_exact_board_identity(identity_path)['status'])

    def test_contract_defers_runtime_but_keeps_physical_binding(self):
        full = impl.board_interface_domain_output_contract()
        bounded = impl.board_interface_domain_output_contract(compile_only=True)
        self.assertIn('control_sequence', full['control_abi']['required_fields'])
        self.assertNotIn('control_sequence', bounded['control_abi']['required_fields'])
        self.assertIn('port_bindings', bounded['compute_slot_abi'])
        self.assertIn('signal_fact_map', bounded['axi_interfaces'])
        self.assertFalse(bounded['top_level']['passing_values']['functional_semantics_claimed'])

    def test_missing_runtime_semantics_needs_explicit_compile_policy(self):
        fixture = fixtures.ControlAbiTests()
        facts, cell = fixture.facts()
        control = {'port_classifications': fixture.control('source')['port_classifications']}
        self.assertEqual([], impl._validate_control(control, cell, facts, {}, [], compile_only=True))
        self.assertTrue(impl._validate_control(control, cell, facts, {}, []))
        wrong = copy.deepcopy(control)
        wrong['port_classifications'][0]['width_bits'] = 97
        self.assertTrue(impl._validate_control(wrong, cell, facts, {}, [], compile_only=True))
        wrong = copy.deepcopy(control)
        wrong['port_classifications'].pop()
        self.assertTrue(impl._validate_control(wrong, cell, facts, {}, [], compile_only=True))

    def test_compile_timing_rejects_wrong_frequency_and_polarity(self):
        cell = {'object_id': 'cell', 'kind': 'cell', 'path': '/slot', 'bd_path': '/design'}
        objects = [cell]
        for name, props in [('clk', {'TYPE': 'clk', 'CONFIG.FREQ_HZ': '100000000'}),
                            ('rst', {'TYPE': 'rst', 'CONFIG.POLARITY': 'ACTIVE_LOW'}),
                            ('cal', {'TYPE': 'undef'})]:
            objects.append({'object_id': name, 'kind': 'pin', 'path': '/slot/' + name,
                            'owner_path': '/slot', 'bd_path': '/design', 'properties': props,
                            'connected_nets': [{'kind': 'net', 'path': '/' + name}]})
        facts = {'objects': objects}
        timing = {'clock_domains': [{'fact_port_id': 'clk', 'name': 'clk',
                                    'frequency_hz': 100000000, 'period_ps': 10000, 'evidence_refs': ['clk']}],
                  'resets': [{'fact_port_id': 'rst', 'name': 'rst', 'active_level': 0, 'evidence_refs': ['rst']}],
                  'calibration': [{'fact_port_id': 'cal', 'name': 'cal', 'evidence_refs': ['cal']}]}
        self.assertEqual([], impl._validate_compile_timing(timing, cell, facts))
        timing['resets'][0]['active_level'] = 1
        self.assertTrue(impl._validate_compile_timing(timing, cell, facts))
        timing['resets'][0]['active_level'] = 0
        timing['clock_domains'][0]['period_ps'] = 4000
        self.assertTrue(impl._validate_compile_timing(timing, cell, facts))
        timing['clock_domains'][0]['period_ps'] = 10000
        timing['calibration'][0]['evidence_refs'].append('invented:pin')
        self.assertTrue(impl._validate_compile_timing(timing, cell, facts))

    def test_compile_identity_cannot_certify_runtime(self):
        identity = {'validation_policy': 'vcs_compile_only', 'functional_semantics_claimed': False}
        self.assertTrue(contract.compile_only_board_contract(identity))
        self.assertFalse(contract.compile_only_board_contract({'validation_policy': 'vcs_compile_only'}))
        with patch.object(contract, '_validate_exact_board_contract', return_value={'status': 'pass'}), \
             patch.object(contract, '_load_json_object', return_value=(identity, [])):
            result = contract.validate_exact_board_acceptance(Path('identity'), Path('simulation'))
        self.assertEqual('fail', result['status'])
        self.assertIn('runtime semantics', result['blockers'][0])
