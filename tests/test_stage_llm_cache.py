import hashlib
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from accagent.framework import stage_llm
from accagent.framework.llm_config import LlmCfg
from accagent.framework.stage_llm import stage_worker_output_cacheable


class StageLlmCacheTests(unittest.TestCase):
    def test_llm_inflight_slot_serves_persisted_waiters_fifo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            limiter_dir = Path(tmp) / "limiter"
            first_acquired = threading.Event()
            second_acquired = threading.Event()
            release_first = threading.Event()
            release_second = threading.Event()
            acquired_order: list[str] = []

            def wait_for(predicate) -> None:
                deadline = time.monotonic() + 3.0
                while time.monotonic() < deadline:
                    if predicate():
                        return
                    time.sleep(0.01)
                self.fail("timed out waiting for limiter state")

            def worker(
                schema_name: str,
                acquired_event: threading.Event,
                release_event: threading.Event,
            ) -> None:
                with stage_llm.llm_inflight_slot(schema_name):
                    acquired_order.append(schema_name)
                    acquired_event.set()
                    release_event.wait(timeout=3.0)

            with patch.dict(
                "os.environ",
                {
                    "SPATIALACC_LLM_LIMITER_DIR": str(limiter_dir),
                    "SPATIALACC_LLM_MAX_INFLIGHT": "1",
                    "SPATIALACC_LLM_SLOT_WAIT_SEC": "0.01",
                },
                clear=False,
            ):
                with stage_llm.llm_inflight_slot("holder"):
                    first = threading.Thread(
                        target=worker,
                        args=("first", first_acquired, release_first),
                    )
                    first.start()
                    state_path = limiter_dir / "inflight.json"
                    wait_for(
                        lambda: [
                            waiter.get("schema_name")
                            for waiter in stage_llm.read_limiter_state(state_path)["waiters"]
                        ]
                        == ["first"]
                    )

                    second = threading.Thread(
                        target=worker,
                        args=("second", second_acquired, release_second),
                    )
                    second.start()
                    wait_for(
                        lambda: [
                            waiter.get("schema_name")
                            for waiter in stage_llm.read_limiter_state(state_path)["waiters"]
                        ]
                        == ["first", "second"]
                    )

                wait_for(first_acquired.is_set)
                self.assertEqual(acquired_order, ["first"])
                self.assertFalse(second_acquired.is_set())
                release_first.set()
                wait_for(second_acquired.is_set)
                release_second.set()
                first.join(timeout=3.0)
                second.join(timeout=3.0)

            self.assertFalse(first.is_alive())
            self.assertFalse(second.is_alive())
            self.assertEqual(acquired_order, ["first", "second"])
            state = stage_llm.read_limiter_state(state_path)
            self.assertEqual(state["leases"], {})
            self.assertEqual(state["waiters"], [])

    def test_only_promoting_business_decisions_are_cacheable(self) -> None:
        for status in ("ready", "pass", "proceed", "accepted", "complete", "completed"):
            with self.subTest(status=status):
                self.assertTrue(stage_worker_output_cacheable({"status": status}))

        for status in (
            "conditional_ready_downstream_blocked",
            "needs_refinement",
            "blocked_specific_nodes_for_repair",
            "retry_required",
            "failed_real_tool_gate",
        ):
            with self.subTest(status=status):
                self.assertFalse(stage_worker_output_cacheable({"status": status}))

    def test_transport_fallback_outputs_are_not_cacheable(self) -> None:
        for status in ("", "llm_error", "llm_error_provider", "fallback", "fallback_diagnostic"):
            with self.subTest(status=status):
                self.assertFalse(stage_worker_output_cacheable({"status": status}))

    def test_replaced_llm_artifacts_are_immutably_archived(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            llm_dir = Path(tmp) / "llm"
            llm_dir.mkdir()
            result_path = llm_dir / "board_agent_result.json"
            prompt_path = llm_dir / "board_agent_prompt.md"
            retry_prompt_path = llm_dir / "board_agent_compact_retry_prompt.md"
            repair_path = llm_dir / "board_agent_schema_repair_01.txt"
            prior = {
                "prompt_hash": "old-prompt-hash",
                "request_path": str(prompt_path),
                "compact_retry_request_path": str(retry_prompt_path),
                "schema_repair_attempts": [{"output_path": str(repair_path)}],
                "output": {"status": "blocked"},
            }
            result_path.write_text(json.dumps(prior), encoding="utf-8")
            prompt_path.write_text("old full prompt", encoding="utf-8")
            retry_prompt_path.write_text("old compact prompt", encoding="utf-8")
            repair_path.write_text("old invalid json", encoding="utf-8")

            snapshot = stage_llm.archive_replaced_stage_worker_artifacts(
                result_path,
                prompt_path,
                retry_prompt_path,
                "new-prompt-hash",
            )

            self.assertIsNotNone(snapshot)
            assert snapshot is not None
            manifest_path = Path(snapshot["manifest_path"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(
                manifest["schema_version"],
                stage_llm.ARTIFACT_HISTORY_SCHEMA,
            )
            self.assertEqual(manifest["replaced_prompt_hash"], "old-prompt-hash")
            self.assertEqual(manifest["replacement_prompt_hash"], "new-prompt-hash")
            self.assertEqual(
                manifest["replaced_result_sha256"],
                hashlib.sha256(result_path.read_bytes()).hexdigest(),
            )
            archived = {
                Path(item["source_path"]).name: Path(item["snapshot_path"])
                for item in manifest["archived_files"]
            }
            self.assertEqual(
                json.loads(archived[result_path.name].read_text(encoding="utf-8")),
                prior,
            )
            self.assertEqual(archived[prompt_path.name].read_text(encoding="utf-8"), "old full prompt")
            self.assertEqual(
                archived[retry_prompt_path.name].read_text(encoding="utf-8"),
                "old compact prompt",
            )
            self.assertEqual(archived[repair_path.name].read_text(encoding="utf-8"), "old invalid json")

    def test_no_snapshot_is_created_without_a_prior_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            llm_dir = Path(tmp) / "llm"
            llm_dir.mkdir()
            self.assertIsNone(
                stage_llm.archive_replaced_stage_worker_artifacts(
                    llm_dir / "agent_result.json",
                    llm_dir / "agent_prompt.md",
                    llm_dir / "agent_compact_retry_prompt.md",
                    "new-prompt-hash",
                )
            )

    def test_changed_prompt_content_uses_a_distinct_history_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            llm_dir = Path(tmp) / "llm"
            llm_dir.mkdir()
            result_path = llm_dir / "board_agent_result.json"
            prompt_path = llm_dir / "board_agent_prompt.md"
            retry_prompt_path = llm_dir / "board_agent_compact_retry_prompt.md"
            result_path.write_text(
                json.dumps(
                    {
                        "prompt_hash": "completed-prompt-hash",
                        "request_path": str(prompt_path),
                        "output": {"status": "ready_to_apply"},
                    }
                ),
                encoding="utf-8",
            )
            prompt_path.write_text("completed prompt", encoding="utf-8")
            first = stage_llm.archive_replaced_stage_worker_artifacts(
                result_path,
                prompt_path,
                retry_prompt_path,
                "next-prompt-hash",
            )
            prompt_path.write_text("interrupted next prompt", encoding="utf-8")
            second = stage_llm.archive_replaced_stage_worker_artifacts(
                result_path,
                prompt_path,
                retry_prompt_path,
                "next-prompt-hash",
            )

            assert first is not None and second is not None
            self.assertNotEqual(first["manifest_path"], second["manifest_path"])
            second_manifest = json.loads(
                Path(second["manifest_path"]).read_text(encoding="utf-8")
            )
            archived_prompt = next(
                Path(row["snapshot_path"])
                for row in second_manifest["archived_files"]
                if row["source_path"] == str(prompt_path)
            )
            self.assertEqual(
                archived_prompt.read_text(encoding="utf-8"),
                "interrupted next prompt",
            )

    def test_live_transaction_blocks_a_second_controller_while_owner_lives(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            llm_dir = Path(tmp) / "llm"
            llm_dir.mkdir()
            path = stage_llm.live_llm_transaction_path(llm_dir, "board_agent")
            stage_llm.begin_live_llm_transaction(
                path,
                agent="board_agent",
                stage="verification.targeted_specialist",
                prompt_hash_value="a" * 64,
                prompt_path=llm_dir / "board_agent_prompt.md",
                prompt_bytes=42,
                result_path=llm_dir / "board_agent_result.json",
                model="test-model",
                reasoning_effort="xhigh",
                stream=True,
                context_binding={},
            )

            with self.assertRaisesRegex(
                stage_llm.StageLLMError,
                "refusing duplicate LLM transaction",
            ):
                stage_llm.begin_live_llm_transaction(
                    path,
                    agent="board_agent",
                    stage="verification.targeted_specialist",
                    prompt_hash_value="b" * 64,
                    prompt_path=llm_dir / "board_agent_prompt.md",
                    prompt_bytes=43,
                    result_path=llm_dir / "board_agent_result.json",
                    model="test-model",
                    reasoning_effort="xhigh",
                    stream=True,
                    context_binding={},
                )

    def test_duplicate_stage_worker_cannot_overwrite_live_prompt_evidence(self) -> None:
        schema = {
            "type": "object",
            "properties": {"status": {"type": "string"}},
            "required": ["status"],
        }
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            llm_dir = out_dir / "llm"
            llm_dir.mkdir()
            prompt_path = llm_dir / "board_agent_prompt.md"
            prompt_path.write_text("immutable in-flight prompt", encoding="utf-8")
            live_path = stage_llm.live_llm_transaction_path(llm_dir, "board_agent")
            stage_llm.begin_live_llm_transaction(
                live_path,
                agent="board_agent",
                stage="verification.targeted_specialist",
                prompt_hash_value="a" * 64,
                prompt_path=prompt_path,
                prompt_bytes=len("immutable in-flight prompt"),
                result_path=llm_dir / "board_agent_result.json",
                model="test-model",
                reasoning_effort="xhigh",
                stream=True,
                context_binding={},
            )

            with (
                patch.object(
                    stage_llm,
                    "resolved_llm_cfg",
                    return_value=LlmCfg(
                        model="test-model",
                        endpoint="https://example.invalid",
                        api_key="key",
                        stream=True,
                    ),
                ),
                patch.object(
                    stage_llm,
                    "cached_stage_worker_record",
                    return_value={"output": {"status": "ready"}},
                ) as cache,
            ):
                with self.assertRaisesRegex(
                    stage_llm.StageLLMError,
                    "refusing duplicate LLM transaction",
                ):
                    stage_llm.run_stage_agent(
                        agent="board_agent",
                        stage="verification.targeted_specialist",
                        task="review current board evidence",
                        inputs={},
                        out_dir=out_dir,
                        fallback_summary="fallback",
                        output_schema=schema,
                    )
            cache.assert_not_called()

            self.assertEqual(
                prompt_path.read_text(encoding="utf-8"),
                "immutable in-flight prompt",
            )

    def test_stale_live_transaction_is_archived_before_a_safe_relaunch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            llm_dir = Path(tmp) / "llm"
            llm_dir.mkdir()
            path = stage_llm.live_llm_transaction_path(llm_dir, "board_agent")
            first = stage_llm.begin_live_llm_transaction(
                path,
                agent="board_agent",
                stage="verification.targeted_specialist",
                prompt_hash_value="a" * 64,
                prompt_path=llm_dir / "board_agent_prompt.md",
                prompt_bytes=42,
                result_path=llm_dir / "board_agent_result.json",
                model="test-model",
                reasoning_effort="xhigh",
                stream=True,
                context_binding={},
            )
            first["owner_pid"] = 0
            stage_llm._write_live_llm_transaction(path, first)

            replacement = stage_llm.begin_live_llm_transaction(
                path,
                agent="board_agent",
                stage="verification.targeted_specialist",
                prompt_hash_value="b" * 64,
                prompt_path=llm_dir / "board_agent_prompt.md",
                prompt_bytes=43,
                result_path=llm_dir / "board_agent_result.json",
                model="test-model",
                reasoning_effort="xhigh",
                stream=True,
                context_binding={},
            )

            archives = list((llm_dir / "history").glob("*live.json"))
            self.assertEqual(len(archives), 1)
            archive = json.loads(archives[0].read_text(encoding="utf-8"))
            self.assertEqual(archive["archive_reason"], "stale_inflight")
            self.assertEqual(archive["transaction"]["transaction_id"], first["transaction_id"])
            self.assertNotEqual(replacement["transaction_id"], first["transaction_id"])

    def test_stage_worker_records_credential_free_completed_transaction(self) -> None:
        schema = {
            "type": "object",
            "properties": {"status": {"type": "string"}},
            "required": ["status"],
        }
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            with (
                patch.object(
                    stage_llm,
                    "resolved_llm_cfg",
                    return_value=LlmCfg(
                        model="test-model",
                        endpoint="https://example.invalid",
                        api_key="secret-must-not-persist",
                        stream=True,
                    ),
                ),
                patch.object(
                    stage_llm,
                    "call_llm_with_retry",
                    return_value=(json.dumps({"status": "ready"}), []),
                ),
            ):
                record = stage_llm.run_stage_agent(
                    agent="board_agent",
                    stage="verification.targeted_specialist",
                    task="review current board evidence",
                    inputs={},
                    out_dir=out_dir,
                    fallback_summary="fallback",
                    output_schema=schema,
                )

            transaction_path = Path(record["live_transaction_path"])
            transaction = json.loads(transaction_path.read_text(encoding="utf-8"))
            serialized = json.dumps(transaction, sort_keys=True)
            self.assertEqual(transaction["status"], "completed")
            self.assertEqual(transaction["output_status"], "ready")
            self.assertEqual(transaction["result_sha256"], hashlib.sha256(
                Path(record["result_path"]).read_bytes()
            ).hexdigest())
            self.assertEqual(transaction["context_binding"]["validated_lower_layer_certificate_count"], 0)
            self.assertNotIn("secret-must-not-persist", serialized)
            self.assertNotIn("api_key", serialized)

if __name__ == "__main__":
    unittest.main()
