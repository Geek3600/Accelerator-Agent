import json
import tempfile
import unittest
from pathlib import Path

from accagent.framework import stage_llm
from accagent.framework.llm_config import LlmCfg
from scripts.verification import sample_project_board_interface_impl as impl
from unittest.mock import patch


class BoardSelectorCheckpointReuseTests(unittest.TestCase):
    @staticmethod
    def _llm_contract(stream: bool, transport: str) -> dict[str, object]:
        return {
            "model": "test-model",
            "reasoning_effort": "xhigh",
            "mode": "llm",
            "stream": stream,
            "transport": transport,
            "prompt_protocol": "spatialaccagent.llm_io.v0",
            "system_sha256": "1" * 64,
            "action_grounding_registry_sha256": "2" * 64,
            "action_contract_examples_sha256": "3" * 64,
            "llm_policy_sha256": "4" * 64,
        }

    def test_semantic_contract_ignores_wire_transport(self) -> None:
        streaming = self._llm_contract(True, "responses_sse_stream")
        json_direct = self._llm_contract(False, "responses_json")
        json_direct["http_transport"] = "curl_direct_http1"

        self.assertEqual(
            impl._selector_map_semantic_llm_contract(streaming),
            impl._selector_map_semantic_llm_contract(json_direct),
        )

    def test_record_validation_ignores_stream_and_http_transport(self) -> None:
        agent = "exact_board_interface_selector_map_000_agent"
        request = {
            "agent": agent,
            "stage": "verification.layer3.board_interface_selection.map",
        }
        record = {
            "schema_version": "spatialaccagent.stage_worker_record.v0",
            "agent": agent,
            "stage": request["stage"],
            "model": "test-model",
            "reasoning_effort": "xhigh",
            "mode": "llm",
            "stream": True,
            "transport": "responses_sse_stream",
            "http_transport": "urllib",
            "prompt_protocol": "spatialaccagent.llm_io.v0",
            "used_fallback": False,
            "error": None,
            "output": {
                "schema_version": impl.SELECTION_MAP_SCHEMA_VERSION,
                "status": "pass",
            },
        }

        self.assertEqual(
            impl._selector_map_record_errors(
                record,
                request,
                self._llm_contract(False, "responses_json"),
            ),
            [],
        )

    def test_history_artifacts_recover_a_hash_bound_checkpoint(self) -> None:
        agent = "exact_board_interface_selector_map_000_agent"
        stage = "verification.layer3.board_interface_selection.map"
        contract = self._llm_contract(False, "responses_json")
        output = {
            "schema_version": impl.SELECTION_MAP_SCHEMA_VERSION,
            "status": "pass",
            "blockers": [],
            "reviewed_object_ids": [],
            "reviewed_source_ids": [],
            "candidate_cells": [],
            "candidate_wrapper_sources": [],
            "candidate_relevant_sources": [],
            "candidate_replacement_sources": [],
            "findings": [],
        }
        old_policy = {
            "schema_version": "spatialaccagent.llm_policy.v0",
            "mode": "llm",
            "enforce": True,
            "model": "test-model",
            "locked_model": "test-model",
            "model_override_approval_path": "",
            "requested_model_override": "",
            "configuration_error": "",
            "endpoint_configured": True,
            "api_key_configured": True,
            "reasoning_effort": "xhigh",
            "policy": "mandatory",
        }
        current_policy = {
            "schema_version": "spatialaccagent.llm_policy.v0",
            "mode": "llm",
            "enforce": True,
            "model": "test-model",
            "configured_model": "test-model",
            "model_selection_policy": "explicit model selection is authoritative",
            "requested_model_override": "",
            "configuration_error": "",
            "endpoint_configured": True,
            "api_key_configured": True,
            "reasoning_effort": "xhigh",
            "policy": "mandatory",
        }
        with tempfile.TemporaryDirectory() as temp:
            out_dir = Path(temp) / "board_interface"
            llm_dir = out_dir / "llm"
            history = llm_dir / "history"
            history.mkdir(parents=True)
            prompt_path = history / f"{agent}_prompt.archived.md"
            prompt_path.write_text(
                "<llm_policy>\n"
                + json.dumps(old_policy, sort_keys=True)
                + "\n</llm_policy>\n",
                encoding="utf-8",
            )
            record_path = history / f"{agent}_result.archived.json"
            record = {
                "schema_version": "spatialaccagent.stage_worker_record.v0",
                "agent": agent,
                "stage": stage,
                "model": "test-model",
                "reasoning_effort": "xhigh",
                "mode": "llm",
                "stream": True,
                "transport": "responses_sse_stream",
                "prompt_protocol": "spatialaccagent.llm_io.v0",
                "prompt_hash": impl.sha256_file(prompt_path),
                "used_fallback": False,
                "error": None,
                "result_path": str(llm_dir / f"{agent}_result.json"),
                "request_path": str(llm_dir / f"{agent}_prompt.md"),
                "output": output,
            }
            impl.write_json(record_path, record)
            descriptor = {
                "fingerprint": "b" * 64,
                "payload": {
                    "task": "same-task",
                    "prompt_rules": ["same-rule"],
                    "output_schema": {"type": "object"},
                    "stable_inputs": {
                        "global_vivado_context": {"same": "facts"},
                        "target_board_profile": {"same": "profile"},
                        "chunk": {
                            "evidence_units": [],
                            "assigned_coverage": {},
                        },
                        "global_coverage_commitment": {},
                    },
                },
            }
            components = impl._selector_map_fingerprint_components(
                descriptor, contract
            )
            components["llm_contract_sha256"] = "legacy-policy-hash"
            manifest = {
                "schema_version": impl.SELECTOR_MAP_CHECKPOINT_SCHEMA_VERSION,
                "status": "pass",
                "chunk_count": 1,
                "llm_contract": contract,
                "chunks": [
                    {
                        "chunk_index": 0,
                        "chunk_count": 1,
                        "agent": agent,
                        "semantic_fingerprint": "a" * 64,
                        "fingerprint_components": components,
                        "record_file": f"{agent}_result.json",
                        "record_sha256": impl.sha256_file(record_path),
                        "output_sha256": impl.canonical_sha256(output),
                        "prompt_file": f"{agent}_prompt.md",
                        "origin_prompt_sha256": impl.sha256_file(prompt_path),
                        "origin_exact_prompt_validated": True,
                    }
                ],
            }
            impl.write_json(
                llm_dir / impl.SELECTOR_MAP_CHECKPOINT_NAME,
                manifest,
            )
            request = {
                "agent": agent,
                "stage": stage,
                "inputs": {"chunk": {"chunk_index": 0, "chunk_count": 1}},
            }
            with patch.object(
                stage_llm, "llm_policy_summary", return_value=current_policy
            ):
                reused, reason = impl._reuse_selector_map_checkpoint(
                    out_dir,
                    request,
                    descriptor,
                    {"object_ids": [], "source_ids": []},
                    set(),
                    set(),
                    set(),
                    contract,
                )

        self.assertEqual(reason, "semantic_checkpoint_reuse")
        self.assertIsNotNone(reused)
        self.assertIn("history", str(reused["result_path"]))
        self.assertIn("history", str(reused["request_path"]))

    def test_progressive_coverage_accepts_history_checkpoint_record_path(self) -> None:
        agent = "exact_board_interface_selector_map_000_agent"
        with tempfile.TemporaryDirectory() as temp:
            out_dir = Path(temp) / "board_interface"
            llm_dir = out_dir / "llm"
            history = llm_dir / "history"
            history.mkdir(parents=True)
            record_path = history / f"{agent}_result.archived.json"
            impl.write_json(
                record_path,
                {
                    "agent": agent,
                    "output": {
                        "reviewed_object_ids": [],
                        "reviewed_source_ids": [],
                    },
                },
            )
            checkpoint_path = llm_dir / impl.SELECTOR_MAP_CHECKPOINT_NAME
            impl.write_json(
                checkpoint_path,
                {
                    "chunks": [
                        {
                            "agent": agent,
                            "record_file": f"{agent}_result.json",
                            "record_artifact_path": str(
                                record_path.relative_to(llm_dir)
                            ),
                            "record_sha256": impl.sha256_file(record_path),
                            "semantic_fingerprint": "a" * 64,
                        }
                    ]
                },
            )

            ledger, errors = impl._write_progressive_coverage_ledger(
                out_dir,
                {"raw_fact_sha256": "b" * 64},
                {"object_ids": [], "source_ids": []},
                [
                    {
                        "agent": agent,
                        "result_path": str(record_path),
                        "output": {
                            "reviewed_object_ids": [],
                            "reviewed_source_ids": [],
                        },
                    }
                ],
                [],
                {
                    "path": str(checkpoint_path),
                    "sha256": impl.sha256_file(checkpoint_path),
                },
                1,
                1,
            )
            coverage = json.loads(Path(ledger["path"]).read_text(encoding="utf-8"))

        self.assertEqual(errors, [])
        self.assertEqual(
            coverage["worker_records"][0]["path"], str(record_path.resolve())
        )

    def test_llm_prompt_policy_excludes_transport_provenance(self) -> None:
        with patch.object(
            stage_llm,
            "resolved_llm_cfg",
            return_value=LlmCfg(
                model="test-model",
                http_transport="curl_direct_http1",
                max_output_tokens=32768,
            ),
        ):
            policy = stage_llm.llm_policy_summary()

        self.assertNotIn("http_transport", policy)
        self.assertNotIn("max_output_tokens", policy)

if __name__ == "__main__":
    unittest.main()
