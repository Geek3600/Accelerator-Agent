from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from accagent.framework.repair_experience import (
    build_project_knowledge_query,
    build_repair_experience_query,
    load_repair_experiences,
    record_repair_iteration_experience,
    retrieve_project_knowledge,
    retrieve_repair_experience,
)
from accagent.framework.stage_llm import compact_verification_capability_repair_package


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RepairExperienceTest(unittest.TestCase):
    def make_iteration(
        self,
        root: Path,
        *,
        iteration: int,
        result_status: str,
        stage_passed: bool,
        capability_status: str | None,
        after_sha256: str,
        include_context_snapshot: bool = True,
        include_project_knowledge_update: bool = False,
    ) -> tuple[Path, Path]:
        run_dir = root / "runs" / "source_run"
        iteration_dir = (
            run_dir
            / "repair_execution"
            / "loop"
            / f"iteration_{iteration:04d}"
        )
        snapshot_dir = iteration_dir / "snapshots"
        source_prefix = root / "mutable_sources" / str(iteration)

        context = {
            "verification_scope": "single_layer_closure",
            "debug_layer": "single_transformer_layer_kernel",
            "repair_scope": "verification_capability_repair",
            "repair_kind": "localized_semantic_dut_repair",
            "repair_gate": "case_single_layer_functional",
            "violated_contract": "whole_sequence_barrier_forbidden",
            "stage_id": "stage_01_self_attention",
            "target_modules": ["Attention"],
            "current_single_layer_real_tool_failure": {
                "failure_class": "intra_layer_spatial_pipeline_violation",
                "proof_mode": "single_layer_pipeline_contract",
                "input_fingerprint_sha256": "1" * 64,
                "pipeline_trace_sha256": "2" * 64,
                "summary": "token zero output followed final token input",
            },
        }
        llm_record = {
            "agent": "localized_semantic_dut_repair_agent",
            "model": "test-model",
            "prompt_hash": "3" * 64,
            "output": {
                "summary": "decouple collection from causal token computation",
                "root_cause": "collection and compute shared a whole-sequence state",
            },
        }
        patch_report = {
            "status": "pass",
            "files": [
                {
                    "path": str(root / "templates" / "Attention.scala"),
                    "operation": "replace",
                    "before_sha256": "4" * 64,
                    "after_sha256": after_sha256,
                    "bytes": 1024,
                }
            ],
            "repair_checkpoint": {
                "repair_kind": "localized_semantic_dut_repair",
                "stage_id": "stage_01_self_attention",
                "module": "Attention",
                "violated_contract": "whole_sequence_barrier_forbidden",
            },
        }
        validation = {"status": "pass", "commands": []}
        capability = (
            {
                "schema_version": "spatialaccagent.single_layer_functional_report.v1",
                "status": capability_status,
                "input_fingerprint_sha256": "5" * 64,
                "failure_class": (
                    "downstream_pipeline_failure"
                    if capability_status == "fail"
                    else None
                ),
            }
            if capability_status is not None
            else None
        )

        context_source = source_prefix / "context.json"
        if include_project_knowledge_update:
            llm_record["output"]["project_knowledge_updates"] = [
                {
                    "knowledge_kind": "ready_valid_protocol",
                    "subject_ids": [
                        "stage_01_self_attention",
                        "Attention",
                    ],
                    "claim": (
                        "The packet boundary is a token boundary; full-sequence "
                        "retirement requires an independent token count."
                    ),
                    "timing_observations": [
                        "token 1 may enter while token 0 remains downstream"
                    ],
                    "validity_scope": "current_source_fingerprint",
                    "validity_conditions": [
                        "StreamBeat.last retains token-boundary semantics"
                    ],
                    "evidence_refs": [str(context_source) + "#/current_single_layer_real_tool_failure"],
                    "confidence": "high",
                    "reuse_guidance": "Do not infer sequence completion from StreamBeat.last.",
                    "supersedes_knowledge_ids": [],
                    "contradicts_knowledge_ids": [],
                }
            ]
        artifacts = {
            "llm_record": (source_prefix / "llm.json", llm_record),
            "agent_patch_application": (source_prefix / "patch.json", patch_report),
            "agent_requested_validation": (source_prefix / "validation.json", validation),
        }
        if include_context_snapshot:
            artifacts["context_package"] = (context_source, context)
        if capability is not None:
            artifacts["capability_report"] = (
                source_prefix / "capability.json",
                capability,
            )

        snapshots = []
        source_paths = {}
        for index, (role, (source_path, value)) in enumerate(artifacts.items()):
            snapshot_path = snapshot_dir / f"{index:02d}_{role}.json"
            write_json(snapshot_path, value)
            source_paths[role] = str(source_path)
            snapshots.append(
                {
                    "role": role,
                    "source_path": str(source_path),
                    "source_sha256": sha256_file(snapshot_path),
                    "snapshot_path": str(snapshot_path),
                }
            )

        result = {
            "status": result_status,
            "summary": f"post-patch status={result_status}",
            "stage_passed": stage_passed,
            "target_modules": ["Attention"],
            "context_package": str(context_source),
            "llm_record": source_paths["llm_record"],
            "agent_patch_application": source_paths["agent_patch_application"],
            "agent_requested_validation": source_paths["agent_requested_validation"],
            "capability_reports": (
                [
                    {
                        "path": source_paths["capability_report"],
                        "schema_version": capability["schema_version"],
                        "status": capability_status,
                    }
                ]
                if capability is not None
                else []
            ),
        }
        record = {
            "schema_version": "spatialaccagent.stage8_repair_loop_iteration.v1",
            "iteration": iteration,
            "repair_execution_report": {
                "step_results": [
                    {
                        "step_id": "repair_step.00",
                        "scope": "verification_capability_repair",
                        "result": result,
                    }
                ]
            },
            "disposition": {"status": "complete" if stage_passed else "continue"},
            "evidence_snapshots": snapshots,
        }
        record_path = iteration_dir / "iteration_record.json"
        write_json(record_path, record)
        return run_dir, record_path

    def test_validated_experience_is_content_addressed_and_cross_run_retrievable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "shared" / "repair_experience.jsonl"
            run_dir, record_path = self.make_iteration(
                root,
                iteration=1,
                result_status="pass",
                stage_passed=True,
                capability_status="pass",
                after_sha256="a" * 64,
            )
            with patch.dict(os.environ, {"SPATIALACC_REPAIR_EXPERIENCE_DB": str(db_path)}):
                first = record_repair_iteration_experience(record_path, run_dir=run_dir)
                second = record_repair_iteration_experience(record_path, run_dir=run_dir)
                query = build_repair_experience_query(
                    {
                        "verification_scope": "single_layer_closure",
                        "debug_layer": "single_transformer_layer_kernel",
                        "repair_scope": "verification_capability_repair",
                        "repair_kind": "localized_semantic_dut_repair",
                        "repair_gate": "case_single_layer_functional",
                        "violated_contract": "whole_sequence_barrier_forbidden",
                        "stage_id": "stage_01_self_attention",
                        "target_modules": ["Attention"],
                        "capability_probe": {
                            "failure_class": "intra_layer_spatial_pipeline_violation",
                            "proof_mode": "single_layer_pipeline_contract",
                        },
                    }
                )
                context = retrieve_repair_experience(
                    root / "runs" / "different_model_run",
                    query,
                )

            self.assertEqual(first["recorded"], 1)
            self.assertEqual(second["recorded"], 0)
            self.assertEqual(second["duplicates"], 1)
            self.assertEqual(len(load_repair_experiences(db_path)), 1)
            self.assertEqual(context["selected_count"], 1)
            self.assertEqual(
                context["episodes"][0]["outcome"]["status"],
                "validated_success",
            )
            self.assertIn("violated_contract", context["episodes"][0]["similarity"]["exact_match_fields"])

    def test_falsified_is_retrieved_but_inconclusive_is_not_promoted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "shared" / "repair_experience.jsonl"
            success_run, success_path = self.make_iteration(
                root,
                iteration=1,
                result_status="pass",
                stage_passed=True,
                capability_status="pass",
                after_sha256="a" * 64,
            )
            _, failed_path = self.make_iteration(
                root,
                iteration=2,
                result_status="fail",
                stage_passed=False,
                capability_status="fail",
                after_sha256="b" * 64,
            )
            _, inconclusive_path = self.make_iteration(
                root,
                iteration=3,
                result_status="fail",
                stage_passed=False,
                capability_status=None,
                after_sha256="c" * 64,
            )
            with patch.dict(os.environ, {"SPATIALACC_REPAIR_EXPERIENCE_DB": str(db_path)}):
                for path in (success_path, failed_path, inconclusive_path):
                    record_repair_iteration_experience(path, run_dir=success_run)
                query = {
                    "violated_contract": "whole_sequence_barrier_forbidden",
                    "stage_role": "self_attention",
                }
                context = retrieve_repair_experience(success_run, query, limit=8)

            stored_statuses = {
                row["outcome"]["status"] for row in load_repair_experiences(db_path)
            }
            selected_statuses = {
                row["outcome"]["status"] for row in context["episodes"]
            }
            self.assertEqual(
                stored_statuses,
                {"validated_success", "falsified", "inconclusive"},
            )
            self.assertEqual(selected_statuses, {"validated_success", "falsified"})

    def test_legacy_iteration_without_context_snapshot_uses_repair_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "shared" / "repair_experience.jsonl"
            run_dir, record_path = self.make_iteration(
                root,
                iteration=1,
                result_status="pass",
                stage_passed=True,
                capability_status="pass",
                after_sha256="e" * 64,
                include_context_snapshot=False,
            )
            with patch.dict(os.environ, {"SPATIALACC_REPAIR_EXPERIENCE_DB": str(db_path)}):
                result = record_repair_iteration_experience(record_path, run_dir=run_dir)
                context = retrieve_repair_experience(
                    run_dir,
                    {
                        "violated_contract": "whole_sequence_barrier_forbidden",
                        "stage_role": "self_attention",
                    },
                )

            self.assertEqual(result["recorded"], 1)
            self.assertEqual(context["selected_count"], 1)
            self.assertEqual(
                context["episodes"][0]["outcome"]["status"],
                "validated_success",
            )

    def test_compact_retry_preserves_bounded_experience_context(self) -> None:
        experience = {
            "schema_version": "spatialaccagent.repair_experience_context.v1",
            "status": "ready",
            "selected_count": 1,
            "episodes": [{"experience_id": "repair_experience." + "d" * 64}],
        }
        compact = compact_verification_capability_repair_package(
            {
                "schema_version": "spatialaccagent.verification_capability_repair_package.v0",
                "stage": "repair_execution",
                "relevant_repair_experience": experience,
            }
        )
        self.assertEqual(compact["relevant_repair_experience"], experience)

    def test_validated_project_knowledge_is_source_bound_and_cross_layer_rebinds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "shared" / "repair_experience.jsonl"
            run_dir, record_path = self.make_iteration(
                root,
                iteration=1,
                result_status="pass",
                stage_passed=True,
                capability_status="pass",
                after_sha256="a" * 64,
                include_project_knowledge_update=True,
            )
            with patch.dict(os.environ, {"SPATIALACC_REPAIR_EXPERIENCE_DB": str(db_path)}):
                record_repair_iteration_experience(record_path, run_dir=run_dir)
                exact = retrieve_project_knowledge(
                    run_dir,
                    {
                        "project_id": run_dir.name,
                        "subject_ids": ["stage_01_self_attention"],
                        "current_input_fingerprint_sha256s": ["5" * 64],
                    },
                )
                board_query = build_project_knowledge_query(
                    {
                        "run_dir": str(run_dir),
                        "verification_scope": "board_axi_ddr_closure",
                        "debug_layer": "board_axi_ddr_wrapped_system",
                        "target_modules": ["board_scheduler"],
                        "current_board_vcs_feedback": {
                            "input_fingerprint_sha256": "6" * 64,
                        },
                    }
                )
                rebound = retrieve_project_knowledge(run_dir, board_query)

            self.assertEqual(exact["selected_count"], 1)
            self.assertEqual(
                exact["knowledge"][0]["epistemic_status"],
                "validated_for_recorded_source",
            )
            self.assertEqual(
                exact["knowledge"][0]["applicability"],
                "exact_current_source",
            )
            self.assertEqual(rebound["selected_count"], 1)
            self.assertEqual(
                rebound["knowledge"][0]["applicability"],
                "same_project_source_rebind_required",
            )

    def test_falsified_project_knowledge_is_negative_evidence_and_can_be_deduplicated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "shared" / "repair_experience.jsonl"
            run_dir, record_path = self.make_iteration(
                root,
                iteration=1,
                result_status="fail",
                stage_passed=False,
                capability_status="fail",
                after_sha256="b" * 64,
                include_project_knowledge_update=True,
            )
            with patch.dict(os.environ, {"SPATIALACC_REPAIR_EXPERIENCE_DB": str(db_path)}):
                ingest = record_repair_iteration_experience(record_path, run_dir=run_dir)
                query = {
                    "project_id": run_dir.name,
                    "subject_ids": ["Attention"],
                }
                selected = retrieve_project_knowledge(run_dir, query)
                excluded = retrieve_project_knowledge(
                    run_dir,
                    query,
                    exclude_experience_ids=set(ingest["experience_ids"]),
                )

            self.assertEqual(
                selected["knowledge"][0]["epistemic_status"],
                "falsified_or_causally_insufficient",
            )
            self.assertEqual(excluded["selected_count"], 0)

    def test_deferred_real_tool_pass_is_attributed_to_original_agent_intervention(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "shared" / "repair_experience.jsonl"
            run_dir, failed_path = self.make_iteration(
                root,
                iteration=1,
                result_status="fail",
                stage_passed=False,
                capability_status="fail",
                after_sha256="a" * 64,
                include_project_knowledge_update=True,
            )
            _, passed_path = self.make_iteration(
                root,
                iteration=2,
                result_status="pass",
                stage_passed=True,
                capability_status="pass",
                after_sha256="a" * 64,
            )
            passed = json.loads(passed_path.read_text(encoding="utf-8"))
            passed["evidence_snapshots"] = [
                row
                for row in passed["evidence_snapshots"]
                if row.get("role") != "llm_record"
            ]
            passed["repair_execution_report"]["step_results"][0]["result"][
                "llm_record"
            ] = None
            write_json(passed_path, passed)

            with patch.dict(os.environ, {"SPATIALACC_REPAIR_EXPERIENCE_DB": str(db_path)}):
                first = record_repair_iteration_experience(failed_path, run_dir=run_dir)
                second = record_repair_iteration_experience(passed_path, run_dir=run_dir)
                relevant = retrieve_repair_experience(
                    run_dir,
                    {
                        "violated_contract": "whole_sequence_barrier_forbidden",
                        "stage_role": "self_attention",
                    },
                )
                knowledge = retrieve_project_knowledge(
                    run_dir,
                    {
                        "project_id": run_dir.name,
                        "subject_ids": ["stage_01_self_attention"],
                        "current_input_fingerprint_sha256s": ["5" * 64],
                    },
                )

            self.assertEqual(first["recorded"], 1)
            self.assertEqual(second["recorded"], 1)
            self.assertEqual(len(load_repair_experiences(db_path)), 2)
            self.assertEqual(relevant["selected_count"], 1)
            self.assertEqual(
                relevant["episodes"][0]["outcome"]["status"],
                "validated_success",
            )
            attribution = relevant["episodes"][0]["outcome"][
                "deferred_real_tool_attribution"
            ]
            self.assertEqual(
                attribution["source_intervention_experience_id"],
                first["experience_ids"][0],
            )
            self.assertEqual(
                knowledge["knowledge"][0]["epistemic_status"],
                "validated_for_recorded_source",
            )

    def test_unarchived_live_llm_result_is_recovered_only_by_exact_patch_projection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "shared" / "repair_experience.jsonl"
            replacement = "object RecoveredRepair { val depth = 113 }\n"
            after_sha256 = hashlib.sha256(replacement.encode("utf-8")).hexdigest()
            run_dir, record_path = self.make_iteration(
                root,
                iteration=1,
                result_status="pass",
                stage_passed=True,
                capability_status="pass",
                after_sha256=after_sha256,
            )
            record = json.loads(record_path.read_text(encoding="utf-8"))
            for snapshot_row in record["evidence_snapshots"]:
                if snapshot_row.get("role") != "agent_patch_application":
                    continue
                snapshot_path = Path(snapshot_row["snapshot_path"])
                patch_report = json.loads(snapshot_path.read_text(encoding="utf-8"))
                patch_report["files"][0]["bytes"] = len(replacement.encode("utf-8"))
                write_json(snapshot_path, patch_report)
                snapshot_row["source_sha256"] = sha256_file(snapshot_path)
            record["evidence_snapshots"] = [
                row
                for row in record["evidence_snapshots"]
                if row.get("role") != "llm_record"
            ]
            result = record["repair_execution_report"]["step_results"][0]["result"]
            result["llm_record"] = None
            write_json(record_path, record)

            live_result = {
                "agent": "localized_semantic_dut_repair_agent",
                "model": "test-model",
                "prompt_hash": "3" * 64,
                "output": {
                    "summary": "bound residual elasticity to one token plus one beat",
                    "root_cause": "sequence-depth queues removed downstream token credit",
                    "file_edits": [
                        {
                            "path": str(root / "templates" / "Attention.scala"),
                            "operation": "replace",
                            "expected_sha256": "4" * 64,
                            "content": replacement,
                        }
                    ],
                },
            }
            live_path = run_dir / "repair_execution" / "llm" / "localized_result.json"
            write_json(live_path, live_result)

            with patch.dict(os.environ, {"SPATIALACC_REPAIR_EXPERIENCE_DB": str(db_path)}):
                ingest = record_repair_iteration_experience(record_path, run_dir=run_dir)
                episodes = load_repair_experiences(db_path)

            self.assertEqual(ingest["recorded"], 1)
            self.assertEqual(episodes[0]["outcome"]["status"], "validated_success")
            self.assertEqual(
                episodes[0]["provenance"]["llm_record_recovery"]["method"],
                "exact_complete_file_edit_projection_match",
            )

    def test_legacy_v1_episode_remains_loadable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "repair_experience.jsonl"
            projection = {
                "schema_version": "spatialaccagent.repair_experience_episode.v1",
                "key": {"violated_contract": "legacy_contract"},
                "intervention": {
                    "agent": "legacy_agent",
                    "prompt_hash": "1" * 64,
                    "file_changes": [],
                },
                "outcome": {
                    "status": "falsified",
                    "evidence_grade": "same_layer_real_tool_fail",
                    "post_input_fingerprint_sha256": "2" * 64,
                    "post_failure_class": "legacy_failure",
                },
            }
            identity = hashlib.sha256(
                json.dumps(
                    projection,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=True,
                ).encode("utf-8")
            ).hexdigest()
            legacy = {
                **projection,
                "experience_id": "repair_experience." + identity,
                "recorded_at": "2026-01-01T00:00:00+00:00",
                "observation": {},
                "provenance": {},
                "evidence_bindings": [],
                "transfer_policy": {},
            }
            path.write_text(json.dumps(legacy) + "\n", encoding="utf-8")
            self.assertEqual(len(load_repair_experiences(path)), 1)

    def test_compact_retry_preserves_project_knowledge_without_recompression(self) -> None:
        knowledge = {
            "schema_version": "spatialaccagent.project_knowledge_context.v1",
            "status": "ready",
            "selected_count": 1,
            "knowledge": [{"knowledge_id": "project_knowledge." + "e" * 64}],
        }
        compact = compact_verification_capability_repair_package(
            {
                "schema_version": "spatialaccagent.verification_capability_repair_package.v0",
                "stage": "repair_execution",
                "relevant_project_knowledge": knowledge,
            }
        )
        self.assertEqual(compact["relevant_project_knowledge"], knowledge)


if __name__ == "__main__":
    unittest.main()
