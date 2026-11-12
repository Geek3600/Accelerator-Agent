from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from accagent.framework.stage_repair_execute import regenerate_target_model_reference


class ReferenceRegenerationRefreshTest(unittest.TestCase):
    def test_incomplete_binding_still_refreshes_semantic_failure_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_state = root / "sacg_state.json"
            source_state.write_text("{}\n", encoding="utf-8")
            run_dir = root / "run"
            out_dir = run_dir / "repair_execution"
            requirements_path = (
                run_dir
                / "verification"
                / "semantic_testbench"
                / "dut_weight_binding_requirements.json"
            )
            requirements_path.parent.mkdir(parents=True)
            requirements_path.write_text(
                json.dumps(
                    {
                        "schema_version": "spatialaccagent.dut_weight_binding_requirements.v1",
                        "status": "requirements",
                    }
                ),
                encoding="utf-8",
            )
            probe_results = [
                {"status": "pass", "summary": "weight catalog ready"},
                {"status": "pass", "summary": "reference regenerated"},
                {"status": "pass", "summary": "requirements refreshed"},
                {
                    "status": "fail",
                    "summary": "fresh binding report still lacks operator harnesses",
                    "tool_report_path": str(root / "fresh_semantic_report.json"),
                },
            ]

            with (
                patch(
                    "accagent.framework.stage_repair_execute.case_adapter_for_state",
                    return_value={"case_id": "gemma_runtime"},
                ),
                patch(
                    "accagent.framework.stage_repair_execute.adapter_tool_by_name_or_role",
                    return_value=("case_semantic_testbench", {"name": "semantic"}),
                ),
                patch(
                    "accagent.framework.stage_repair_execute.run_capability_probe",
                    side_effect=probe_results,
                ) as probe,
                patch(
                    "accagent.framework.stage_repair_execute.finalize_dut_weight_binding_manifest",
                    return_value={
                        "status": "incomplete",
                        "blockers": ["operator-stage harnesses are not materialized"],
                    },
                ),
            ):
                result = regenerate_target_model_reference(
                    source_state=source_state,
                    run_dir=run_dir,
                    out_dir=out_dir,
                    step={"id": "repair_step.00"},
                    timeout_sec=30,
                )

            self.assertEqual(probe.call_count, 4)
            self.assertEqual(
                probe.call_args_list[-1].kwargs["label"],
                "reference_regeneration_semantic_testbench",
            )
            self.assertEqual(result["status"], "fail")
            self.assertEqual(result["failed_tool"], "case_semantic_testbench")
            self.assertEqual(result["capability_reports"], [result["context_package"]])
            package = json.loads(Path(result["context_package"]).read_text(encoding="utf-8"))
            self.assertEqual(
                package["tool_results"][-1]["purpose"],
                "refresh_semantic_diagnostics_after_incomplete_binding_materialization",
            )
            self.assertEqual(
                package["tool_results"][-1]["result"]["tool_report_path"],
                str(root / "fresh_semantic_report.json"),
            )


if __name__ == "__main__":
    unittest.main()
