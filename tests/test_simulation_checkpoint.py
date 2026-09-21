"""Regression coverage for the native VCS checkpoint compatibility layer.

The active replay lifecycle is covered in ``test_fast_replay``. This module
keeps only the compatibility contracts still consumed by the real runner;
historical cross-revision/hash-gate behavior is intentionally retired.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from accagent.framework.simulation_checkpoint import (
    FIXED_INITIAL_CHECKPOINT_CUT,
    checkpoint_contract,
    checkpoint_framework_adapter_artifacts,
    checkpoint_request_errors,
    checkpoint_reuse_decision,
    framework_checkpoint_contract,
    prepare_checkpoint_request,
    rebind_checkpoint_framework_adapter_artifacts,
)


class SimulationCheckpointTest(unittest.TestCase):
    def test_native_contract_has_no_framework_adapter(self) -> None:
        contract = framework_checkpoint_contract({})

        self.assertEqual(checkpoint_framework_adapter_artifacts(), [])
        self.assertEqual(contract["native_vcs_snapshot"]["path"], "checkpoint/native_state")
        self.assertIn("native_exact_model", contract["supported_modes"])

    def test_compatibility_rebind_is_a_noop(self) -> None:
        source = {"native_vcs_snapshot": {"path": "checkpoint/native_state"}}

        rebound, report = rebind_checkpoint_framework_adapter_artifacts(source)

        self.assertEqual(rebound, source)
        self.assertEqual(report["status"], "pass")
        self.assertFalse(report["changed"])

    def test_missing_checkpoint_selects_capture_without_blocking_request(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            manifest = run_dir / "verification" / "board_simulation" / "board_simulation_manifest.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps({"top_module": "board_tb"}), encoding="utf-8")

            request = prepare_checkpoint_request(run_dir)

        self.assertEqual(request["status"], "ready")
        self.assertEqual(request["semantic_cut"]["fixed_cut"], FIXED_INITIAL_CHECKPOINT_CUT)
        self.assertEqual(request["replay_decision"]["mode"], "cold_capture")
        self.assertEqual(checkpoint_request_errors(request), [])

    def test_exact_native_checkpoint_is_selected_only_for_matching_identity(self) -> None:
        current = {"compiled_model_sha256": "model", "workload_sha256": "workload"}
        contract = checkpoint_contract({})
        manifest = {
            "status": "pass",
            "execution_identity": current,
            "semantic_cut": {"fixed_cut": FIXED_INITIAL_CHECKPOINT_CUT},
            "state_artifacts": [{"kind": "native_vcs_snapshot", "remote_path": "checkpoint/native_state"}],
            "remote_acknowledgment_status": "pass",
            "native_simulator_snapshot": {"status": "pass"},
            "causal_cut_certificate": {"status": "pass"},
            "equivalence_certificate": {"status": "pass"},
            "checkpoint_contract": contract,
        }

        mismatched = checkpoint_reuse_decision(manifest, {**current, "workload_sha256": "other"})

        self.assertEqual(mismatched["mode"], "cold_capture")
        self.assertNotEqual(mismatched["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
