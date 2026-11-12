import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from scripts.verification.case_hierarchical_check import check_multilayer_pipeline


class MultilayerCompileOnlyPolicyTest(TestCase):
    def _make_run(self, root: Path, policy: str) -> None:
        (root / "input").mkdir(parents=True)
        (root / "generated" / "memory").mkdir(parents=True)
        (root / "verification_artifacts").mkdir(parents=True)
        (root / "verification" / "model_weights").mkdir(parents=True)
        (root / "input" / "model_config.json").write_text(
            json.dumps({"num_layers": 24}), encoding="utf-8"
        )
        (root / "input" / "task_card.json").write_text(
            json.dumps({"acceptance_policy": {"policy": policy}}), encoding="utf-8"
        )
        (root / "generated" / "memory" / "dut_weight_binding_manifest.json").write_text(
            "{}\n", encoding="utf-8"
        )
        (root / "verification_artifacts" / "verification_plan.json").write_text(
            json.dumps(
                {"verification_execution_policy": {"validation_policy": policy}}
            ),
            encoding="utf-8",
        )

    def test_compile_only_does_not_require_a_multilayer_runtime_harness(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            self._make_run(run_dir, "vcs_compile_only")

            report = check_multilayer_pipeline(run_dir)

        checks = {check["name"]: check for check in report["checks"]}
        self.assertEqual(report["status"], "pass", report["blockers"])
        self.assertEqual(checks["multilayer_compile_scope"]["status"], "not_applicable")
        self.assertEqual(checks["multilayer_harness_sources"]["status"], "not_applicable")

    def test_full_semantic_policy_still_requires_a_multilayer_harness(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            self._make_run(run_dir, "full_semantic_simulation")

            report = check_multilayer_pipeline(run_dir)

        checks = {check["name"]: check for check in report["checks"]}
        self.assertEqual(report["status"], "fail")
        self.assertEqual(checks["multilayer_compile_scope"]["status"], "fail")
        self.assertEqual(checks["multilayer_harness_sources"]["status"], "fail")
