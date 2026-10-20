import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from accagent.framework.stage_artifacts import (
    CODEGEN_RECOVERY_CONSTRAINTS,
    CODEGEN_STAGE5_CONSTRAINTS,
    build_memory_layout,
    codegen_stage_gate_policy,
    generate_chisel_package,
    run_codegen_compile_gate,
    sbt_failure_markers,
    scala_params_expression,
    stage_worker_errors,
    update_sacg,
)
from accagent.framework.stage_params import build_parameter_bindings
from accagent.framework.stage_pipeline import build_pipeline_plan
from tests.test_stage_pipeline import ROOT, state_for


TEMPLATES = ROOT / "accagent" / "framework" / "templates" / "operator_chisel"


def prepared_state(family: str, root: Path) -> tuple[dict, dict]:
    root.mkdir(parents=True, exist_ok=True)
    state = state_for(family, root)
    model = next(item for item in state["constraints"] if item["id"] == "constraint.model.decoder")["facts"]
    model["model_type"] = {"gpt2": "gpt2", "qwen2": "qwen2", "llama": "llama"}[family]
    template = next(item for item in state["constraints"] if item["id"] == "constraint.template.library")["facts"]
    template["template_dir"] = str(TEMPLATES)
    template["source_files"] = sorted(path.name for path in TEMPLATES.glob("*.scala"))
    state["constraints"].append({"id": "constraint.deployment.board", "facts": {"board": {"fpga_part": "xcvu9p-flga2104-2L-e"}}})
    plan = build_pipeline_plan(state)
    plan_path = root / "pipeline_plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    state["artifacts"].append({"id": "artifact.stage3.pipeline_plan", "path": str(plan_path)})
    bindings = build_parameter_bindings(state)
    binding_path = root / "parameter_binding.json"
    binding_path.write_text(json.dumps(bindings), encoding="utf-8")
    state["artifacts"].append({"id": "artifact.stage4.parameter_binding", "path": str(binding_path)})
    return state, bindings


class SemanticCodeGenerationTest(TestCase):
    def test_boolean_backend_binding_uses_scala_literals(self):
        values = {"weight_bits": 4, "acc_bits": 32, "cache_tile_words": 256,
                  "cache_tile_count": 2, "cache_refill_data_width_bits": 512,
                  "cross_token_reuse_tokens": 16}
        for bindings in ({}, {"integerMode": "integer_mode"}):
            for mode, literal in [(True, "true"), (False, "false")]:
                expression = scala_params_expression(
                    {"params": {"class": "DecoderParams", "bindings": bindings}},
                    dict(values, integer_mode=mode))
                self.assertIn("integerMode = " + literal, expression)
                self.assertEqual(expression.count("integerMode ="), 1)
                self.assertIn("weightBits = 4", expression)

    def test_generated_package_contains_declared_numeric_rom_resources(self) -> None:
        from accagent.framework.semantic_simulator import semantic_memory_init_payload
        from accagent.framework.stage_artifacts import build_manifest

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            state, _ = prepared_state("gpt2", root)
            package = generate_chisel_package(root, state, build_manifest(state))
            package_root = Path(package["root"])
            references = [
                "src/main/resources/spatialaccagent/numeric/exp2_fraction_q24.mem",
                "src/main/resources/spatialaccagent/numeric/sigmoid_pwl_q18.mem",
            ]
            source = package_root / "rom_dependency.sv"
            source.write_text("\n".join(f'initial $readmemh("{name}", mem);' for name in references))
            _, dependencies, errors = semantic_memory_init_payload(root, [source])
            self.assertEqual(errors, [])
            self.assertEqual({row["remote_relative_path"] for row in dependencies}, set(references))

    def test_codegen_llm_risks_do_not_override_passing_deterministic_gates(self) -> None:
        self.assertEqual(
            stage_worker_errors({
                "status": "candidate_ready_not_promotable",
                "risks": ["Stage-6 VCS evidence has not run yet"],
            }),
            [],
        )
        self.assertEqual(
            stage_worker_errors({"status": "ready", "blocking_errors": ["parameter mismatch"]}),
            ["code_generation_agent blocking finding: parameter mismatch"],
        )

    def test_codegen_handoff_does_not_require_downstream_vcs_or_extra_audits(self) -> None:
        policy = codegen_stage_gate_policy()

        self.assertTrue(any("Stage 6, not Stage 5" in rule for rule in policy["later_stage_obligations"]))
        self.assertIn("candidate_only is the normal pre-publication state", policy["risk_classification_rule"])
        self.assertIn("Team audit proposals are not additional required reports", policy["risk_classification_rule"])

    def test_sbt_background_exception_is_a_compile_gate_failure(self) -> None:
        self.assertIn("ExceptionInInitializerError", sbt_failure_markers("ExceptionInInitializerError", ""))
        self.assertFalse(sbt_failure_markers("[info] done compiling", ""))

    def test_codegen_gate_rejects_missing_elaborated_top_outputs(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            with patch(
                "accagent.framework.stage_artifacts.subprocess.run",
                return_value=type(
                    "Completed", (), {"returncode": 0, "stdout": "", "stderr": ""}
                )(),
            ):
                result = run_codegen_compile_gate(root)

        self.assertEqual(result["status"], "fail")
        self.assertEqual(
            result["missing_generated_outputs"],
            ["GeneratedAcceleratorTop.sv", "GeneratedAxiDdrTop.sv"],
        )
        self.assertIn("required generated SystemVerilog outputs", result["summary"])

    def test_codegen_recovery_transition_does_not_require_unrelated_checkers(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.json"
            target = root / "target.json"
            source.write_text(
                json.dumps(
                    {
                        "nodes": [
                            {"id": "node.model"},
                            {"id": "node.template_library"},
                            {"id": "node.target_board"},
                        ],
                        "constraints": [
                            {"id": "constraint.memory.board"},
                            {"id": "constraint.runtime.board"},
                            {"id": "constraint.deployment.board"},
                        ],
                        "invariants": [
                            {
                                "id": "invariant.codegen_package_static",
                                "checker": "codegen_package_static_check",
                                "constraints": ["constraint.codegen.package"],
                            },
                            {
                                "id": "invariant.codegen_compile_gate",
                                "checker": "codegen_compile_gate",
                                "constraints": ["constraint.codegen.compile_gate"],
                            },
                            {
                                "id": "invariant.codegen_contract_check",
                                "checker": "codegen_contract_check",
                                "constraints": ["constraint.codegen.contract_check"],
                            },
                            {
                                "id": "invariant.board_runtime",
                                "checker": "board_runtime",
                                "constraints": ["constraint.deployment.board"],
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            manifest = {
                "generation_policy": "stage5_recovery_from_frozen_upstream_contract",
                "generated_package_root": str(root / "generated"),
                "generated_memory_layout": str(root / "generated" / "memory.json"),
                "generated_runtime_config": str(root / "generated" / "runtime.json"),
                "compile_gate": {"status": "pass", "log_path": "compile.json"},
                "contract_check": {"status": "pass", "log_path": "contract.json"},
                "package_static_check": {"status": "pass", "log_path": "static.json"},
            }

            transition_id = update_sacg(
                source,
                target,
                root / "manifest.json",
                manifest,
                [],
                transition_constraints=CODEGEN_RECOVERY_CONSTRAINTS,
            )
            state = json.loads(target.read_text(encoding="utf-8"))
            transition = next(
                item for item in state["transitions"] if item["id"] == transition_id
            )

        self.assertEqual(transition["status"], "promoted")
        self.assertEqual(
            transition["touched_constraints"], CODEGEN_RECOVERY_CONSTRAINTS
        )
        self.assertEqual(
            transition["required_checkers"],
            [
                "codegen_compile_gate",
                "codegen_contract_check",
                "codegen_package_static_check",
            ],
        )

    def test_codegen_stage5_binds_current_stage_checker_evidence(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            package_root = root / "generated"
            package_root.joinpath(
                "src/main/scala/spatialaccagent/generated"
            ).mkdir(parents=True)
            for relative in (
                "build.sbt",
                "src/main/scala/spatialaccagent/generated/GeneratedAcceleratorTop.scala",
                "src/main/scala/spatialaccagent/generated/GeneratedAxiDdrTop.scala",
                "src/main/scala/spatialaccagent/generated/GeneratedDesignParams.scala",
                "src/main/scala/spatialaccagent/generated/GeneratedContractCheck.scala",
            ):
                path = package_root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("generated\n", encoding="utf-8")
            memory_layout = package_root / "memory.json"
            runtime_config = package_root / "runtime.json"
            memory_layout.write_text("{}\n", encoding="utf-8")
            runtime_config.write_text("{}\n", encoding="utf-8")
            selection = root / "template_selection.json"
            selection.write_text(json.dumps({"missing_ops": []}), encoding="utf-8")
            board_profile = root / "board_profile.json"
            board_profile.write_text(
                json.dumps({"memory_system": {}, "runtime_interface": {}}),
                encoding="utf-8",
            )
            manifest_path = root / "manifest.json"
            candidate_manifest_path = root / "attempts" / "manifest_candidate.json"
            candidate_manifest_path.parent.mkdir(parents=True)
            manifest = {
                "generation_policy": "template_bound_codegen",
                "planned_code_outputs": ["GeneratedAcceleratorTop.sv"],
                "generated_package_root": str(package_root),
                "generated_files": [str(path.relative_to(root)) for path in package_root.rglob("*") if path.is_file()],
                "generated_memory_layout": str(memory_layout),
                "generated_runtime_config": str(runtime_config),
                "compile_gate": {"status": "pass", "log_path": "compile.json"},
                "contract_check": {"status": "pass", "log_path": "contract.json"},
                "package_static_check": {"status": "pass", "log_path": "static.json"},
                "candidate_manifest_path": str(candidate_manifest_path),
            }
            candidate_manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            manifest_path.write_text(
                json.dumps({"candidate_only": True, "status": "incomplete"}),
                encoding="utf-8",
            )
            source = root / "source.json"
            target = root / "target.json"
            source.write_text(
                json.dumps(
                    {
                        "nodes": [
                            {"id": "node.model"},
                            {"id": "node.template_library"},
                            {"id": "node.target_board"},
                        ],
                        "constraints": [
                            {"id": "constraint.memory.board"},
                            {"id": "constraint.runtime.board"},
                            {"id": "constraint.deployment.board"},
                        ],
                        "artifacts": [
                            {
                                "id": "artifact.stage2.template_selection",
                                "path": str(selection),
                            },
                            {
                                "id": "artifact.input.target_board_profile",
                                "path": str(board_profile),
                            },
                        ],
                        "invariants": [
                            {
                                "id": "invariant.codegen_package_static",
                                "checker": "codegen_package_static_check",
                                "constraints": ["constraint.codegen.package"],
                            },
                            {
                                "id": "invariant.template_coverage",
                                "checker": "template_coverage_check",
                                "constraints": ["constraint.codegen.package"],
                            },
                            {
                                "id": "invariant.codegen_manifest_static",
                                "checker": "code_generation_manifest_static_check",
                                "constraints": ["constraint.codegen.package"],
                            },
                            {
                                "id": "invariant.memory_runtime_plan",
                                "checker": "memory_runtime_plan_check",
                                "constraints": ["constraint.memory.board", "constraint.runtime.board"],
                            },
                            {
                                "id": "invariant.board_runtime",
                                "checker": "board_runtime",
                                "constraints": ["constraint.deployment.board"],
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            transition_id = update_sacg(
                source,
                target,
                manifest_path,
                manifest,
                [],
            )
            state = json.loads(target.read_text(encoding="utf-8"))
            transition = next(
                item for item in state["transitions"] if item["id"] == transition_id
            )
            evidence = [
                item
                for item in state["evidence"]
                if item["checker"]
                in {
                    "template_coverage_check",
                    "code_generation_manifest_static_check",
                    "memory_runtime_plan_check",
                }
            ]

        self.assertEqual(transition["status"], "promoted")
        self.assertEqual(transition["touched_constraints"], CODEGEN_STAGE5_CONSTRAINTS)
        self.assertNotIn("board_runtime", transition["required_checkers"])
        self.assertIn("memory_runtime_plan_check", transition["required_checkers"])
        self.assertEqual(
            {item["checker"] for item in evidence},
            {
                "template_coverage_check",
                "code_generation_manifest_static_check",
                "memory_runtime_plan_check",
            },
        )
        self.assertTrue(all(item["status"] == "pass" for item in evidence))

    def test_generated_loader_ports_follow_model_semantics(self) -> None:
        with TemporaryDirectory() as temp:
            generated = {}
            for family in ("gpt2", "qwen2", "llama"):
                state, _ = prepared_state(family, Path(temp) / family)
                generated[family] = generate_chisel_package(
                    Path(temp) / family,
                    state,
                    {"schema_version": "test", "generation_policy": "test"},
                )
            texts = {
                family: (
                    Path(package["root"])
                    / "src/main/scala/spatialaccagent/generated/GeneratedAxiDdrTop.scala"
                ).read_text(encoding="utf-8")
                for family, package in generated.items()
            }

        self.assertEqual(generated["gpt2"]["top_class"], "GPT2PreLNBlock")
        self.assertIn("val attentionOutBias", texts["gpt2"])
        self.assertEqual(generated["qwen2"]["top_class"], "Qwen2Block")
        self.assertIn("val qkvBias", texts["qwen2"])
        self.assertEqual(generated["llama"]["top_class"], "LlamaStyleBlock")
        self.assertNotIn("val qkvBias", texts["llama"])
        self.assertIn('core.io.elements.get("qkvBias").foreach', texts["llama"])
        self.assertIn("channel.valid := false.B", texts["llama"])
        self.assertIn("channel.bits := 0.U.asTypeOf(channel.bits)", texts["llama"])

    def test_codegen_uses_stage3_implementation_contract_not_model_name(self) -> None:
        with TemporaryDirectory() as temp:
            state, _ = prepared_state("qwen2", Path(temp))
            model = next(item for item in state["constraints"] if item["id"] == "constraint.model.decoder")["facts"]
            model["model_type"] = "arbitrary_future_decoder"
            package = generate_chisel_package(
                Path(temp), state, {"schema_version": "test", "generation_policy": "test"}
            )
            axi_top = (
                Path(package["root"])
                / "src/main/scala/spatialaccagent/generated/GeneratedAxiDdrTop.scala"
            ).read_text(encoding="utf-8")
            accelerator_top = (
                Path(package["root"])
                / "src/main/scala/spatialaccagent/generated/GeneratedAcceleratorTop.scala"
            ).read_text(encoding="utf-8")

        self.assertEqual(package["top_class"], "Qwen2Block")
        self.assertEqual(package["param_class"], "LlamaStyleBlockParams")
        self.assertIn("private val core = Module(new Qwen2Block(p))", accelerator_top)
        self.assertIn("val qkvBias", axi_top)

    def test_generated_contract_check_accepts_wide_linear_columns(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            state, bindings = prepared_state("gpt2", root)
            bindings["global_params"].update(
                {"lanes": 4, "compute_array_rows": 4, "compute_array_cols": 16}
            )
            binding_artifact = next(
                item for item in state["artifacts"] if item["id"] == "artifact.stage4.parameter_binding"
            )
            Path(binding_artifact["path"]).write_text(json.dumps(bindings), encoding="utf-8")
            package = generate_chisel_package(
                root, state, {"schema_version": "test", "generation_policy": "test"}
            )
            contract = (
                Path(package["root"])
                / "src/main/scala/spatialaccagent/generated/GeneratedContractCheck.scala"
            ).read_text(encoding="utf-8")

        self.assertIn("computeArrayCols > p.lanes", contract)
        self.assertIn("computeArrayCols % p.lanes == 0", contract)
        self.assertIn("combine complete input lane groups", contract)

    def test_memory_layout_uses_stage3_semantic_region_sizes(self) -> None:
        with TemporaryDirectory() as temp:
            state, bindings = prepared_state("gpt2", Path(temp))
            package = generate_chisel_package(Path(temp), state, {"schema_version": "test", "generation_policy": "test"})
            layout = build_memory_layout(state, bindings, package)
            plan = json.loads(Path(next(item["path"] for item in state["artifacts"] if item["id"] == "artifact.stage3.pipeline_plan")).read_text(encoding="utf-8"))

        expected = {
            row["name"]: row["size_bytes"]
            for row in plan["memory_schedule"]["required_regions"]
        }
        actual = {row["name"]: row["meta"].get("stage3_size_bytes") for row in layout["regions"]}
        for name in ["input_tokens", "output_tokens", "activation_ping", "activation_pong", "weight_buffer_a", "weight_buffer_b"]:
            self.assertEqual(actual[name], expected[name])
        self.assertTrue(layout["weight_storage_terms"])
