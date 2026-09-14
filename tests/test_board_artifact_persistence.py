import hashlib
import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from accagent.framework.board_artifact_persistence import (
    board_remote_stage_root,
    persist_board_remote_artifacts,
)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n", encoding="utf-8")


class BoardArtifactPersistenceTests(unittest.TestCase):
    def test_default_board_root_is_persistent_and_overridable(self) -> None:
        with TemporaryDirectory() as temp_dir, patch.dict(os.environ, {}, clear=True):
            root = board_remote_stage_root(
                {}, Path(temp_dir) / "model run", "builder@fpga.example"
            )
            self.assertEqual(
                root,
                "/home/builder/workspace/spatialaccagent_artifacts/board_vcs/model_run",
            )
            self.assertNotIn("/tmp", root)
        with TemporaryDirectory() as temp_dir, patch.dict(
            os.environ,
            {"SPATIALACC_REMOTE_BOARD_VCS_ROOT": "/data/board-vcs"},
            clear=True,
        ):
            self.assertEqual(
                board_remote_stage_root({}, Path(temp_dir), "builder"),
                "/data/board-vcs",
            )

    def test_board_receipt_archives_exact_staged_sources_and_evidence(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            board_dir = run_dir / "verification" / "board_simulation"
            source = run_dir / "generated" / "board_integration" / "BoardTop.sv"
            staged_source = board_dir / "vcs_stage" / "sources" / source.name
            compile_log = board_dir / "reports" / "compile.log"
            sim_log = board_dir / "reports" / "sim.log"
            progress_log = board_dir / "reports" / "progress.jsonl"
            executed = board_dir / "board_simulation_executed_manifest.json"
            manifest = board_dir / "board_simulation_manifest.json"
            identity = run_dir / "verification" / "board_interface" / "identity.json"
            for path, content in (
                (source, "new mutable source\n"),
                (staged_source, "exact simulated source\n"),
                (compile_log, "compile evidence\n"),
                (sim_log, "simulation evidence\n"),
                (progress_log, "{\"event\":\"progress\"}\n"),
            ):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            write_json(identity, {"status": "pass"})
            write_json(
                manifest,
                {
                    "source_files": [
                        {
                            "path": str(source),
                            "role": "compute_slot_adapter",
                        }
                    ]
                },
            )
            write_json(
                executed,
                {
                    "dynamic_evidence_records": [
                        {
                            "path": str(progress_log),
                            "sha256": hashlib.sha256(
                                progress_log.read_bytes()
                            ).hexdigest(),
                        }
                    ]
                },
            )
            fingerprint = "b" * 64
            remote_root = "/home/builder/workspace/spatialaccagent_artifacts/board_vcs/run"
            remote_dir = f"{remote_root}/{fingerprint[:12]}_1"
            contract = board_dir / "vcs_stage" / ".spatialacc_semantic_job.json"
            write_json(
                contract,
                {
                    "input_fingerprint_sha256": fingerprint,
                    "remote_stage_root": remote_root,
                    "remote_workdir": remote_dir,
                },
            )
            report = {
                "manifest": str(manifest),
                "source_identity": str(identity),
                "executed_manifest": str(executed),
                "compile_log": str(compile_log),
                "sim_log": str(sim_log),
                "run": {"status": "fail"},
                "input_fingerprint_sha256": fingerprint,
                "remote_workdir": remote_dir,
                "remote_job_recovery_contract": {"job_contract": str(contract)},
            }
            with patch(
                "accagent.framework.semantic_simulator.command_result",
                return_value={"status": "pass", "returncode": 0},
            ):
                result = persist_board_remote_artifacts(
                    run_dir=run_dir,
                    report=report,
                    host="builder@fpga.example",
                    port=22,
                    timeout_sec=0,
                )
            self.assertEqual(result["status"], "pass")
            receipt = json.loads(Path(result["receipt"]).read_text(encoding="utf-8"))
            evidence_names = {Path(row["path"]).name for row in receipt["evidence_files"]}
            self.assertTrue(any(name.endswith("compile.log") for name in evidence_names))
            self.assertTrue(any(name.endswith("sim.log") for name in evidence_names))
            self.assertTrue(any(name.endswith("progress.jsonl") for name in evidence_names))
            snapshot = Path(receipt["source_snapshots"][0]["snapshot_path"])
            self.assertEqual(snapshot.read_text(encoding="utf-8"), "exact simulated source\n")

            progress_log.write_text("changed after execution\n", encoding="utf-8")
            with patch(
                "accagent.framework.semantic_simulator.command_result"
            ) as upload:
                failed = persist_board_remote_artifacts(
                    run_dir=run_dir,
                    report=report,
                    host="builder@fpga.example",
                    port=22,
                    timeout_sec=0,
                )
            self.assertEqual(failed["status"], "fail")
            self.assertIn("changed before archival", failed["blockers"][0])
            upload.assert_not_called()


if __name__ == "__main__":
    unittest.main()
