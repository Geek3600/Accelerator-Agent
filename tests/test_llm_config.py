import unittest
from unittest.mock import patch
import os

from accagent.framework import llm_config
from accagent.framework.llm_config import LlmCfg, _agent_reasoning_effort


class LlmConfigTests(unittest.TestCase):
    def test_streaming_is_the_default_transport(self) -> None:
        self.assertTrue(LlmCfg().stream)

    def test_inherited_ultra_uses_highest_supported_route(self) -> None:
        self.assertEqual(_agent_reasoning_effort("", "ultra"), "xhigh")
        self.assertEqual(_agent_reasoning_effort("", "ULTRA"), "xhigh")

    def test_explicit_reasoning_effort_is_preserved(self) -> None:
        self.assertEqual(_agent_reasoning_effort("medium", "ultra"), "medium")
        self.assertEqual(_agent_reasoning_effort("xhigh", "ultra"), "xhigh")

    def test_explicit_model_selection_does_not_require_approval_artifact(self) -> None:
        with (
            patch.dict(os.environ, {"SPATIALACC_LLM_MODEL": "gpt-5.5"}, clear=True),
            patch.object(
                llm_config,
                "_read_toml",
                return_value={
                    "model": "gpt-5.6-sol",
                    "model_provider": "OpenAI",
                    "model_providers": {
                        "OpenAI": {
                            "base_url": "https://example.invalid/v1",
                            "wire_api": "responses",
                        }
                    },
                },
            ),
            patch.object(
                llm_config,
                "_read_json",
                return_value={"OPENAI_API_KEY": "test-key"},
            ),
        ):
            llm_config.resolve_llm_cfg.cache_clear()
            cfg = llm_config.resolve_llm_cfg()

        llm_config.resolve_llm_cfg.cache_clear()
        self.assertEqual(cfg.model, "gpt-5.5")
        self.assertEqual(cfg.configured_model, "gpt-5.6-sol")
        self.assertEqual(cfg.requested_model_override, "gpt-5.5")
        self.assertEqual(cfg.configuration_error, "")

    def test_explicit_curl_transport_is_normalized(self) -> None:
        with (
            patch.dict(
                os.environ,
                {"SPATIALACC_LLM_TRANSPORT": "curl-direct-http1"},
                clear=True,
            ),
            patch.object(
                llm_config,
                "_read_toml",
                return_value={
                    "model": "test-model",
                    "model_provider": "OpenAI",
                    "model_providers": {
                        "OpenAI": {
                            "base_url": "https://example.invalid/v1",
                            "wire_api": "responses",
                        }
                    },
                },
            ),
            patch.object(
                llm_config,
                "_read_json",
                return_value={"OPENAI_API_KEY": "test-key"},
            ),
        ):
            llm_config.resolve_llm_cfg.cache_clear()
            cfg = llm_config.resolve_llm_cfg()

        llm_config.resolve_llm_cfg.cache_clear()
        self.assertEqual(cfg.http_transport, "curl_direct_http1")
        self.assertEqual(cfg.configuration_error, "")

    def test_optional_output_budget_is_resolved_from_environment(self) -> None:
        with (
            patch.dict(
                os.environ,
                {"SPATIALACC_LLM_MAX_OUTPUT_TOKENS": "32768"},
                clear=True,
            ),
            patch.object(llm_config, "_read_toml", return_value={}),
            patch.object(llm_config, "_read_json", return_value={}),
        ):
            llm_config.resolve_llm_cfg.cache_clear()
            cfg = llm_config.resolve_llm_cfg()

        llm_config.resolve_llm_cfg.cache_clear()
        self.assertEqual(cfg.max_output_tokens, 32768)

    def test_keyed_api_config_fallback_recovers_from_chatgpt_oauth(self) -> None:
        primary_cfg = {
            "model": "gpt-5.6-sol",
            "model_provider": "OpenAI",
            "model_providers": {
                "OpenAI": {
                    "base_url": "https://chatgpt.invalid/v1",
                    "wire_api": "responses",
                }
            },
        }
        api_cfg = {
            "model": "gpt-5.6-sol",
            "model_provider": "OpenAI",
            "model_providers": {
                "OpenAI": {
                    "base_url": "https://api.invalid/v1",
                    "wire_api": "responses",
                    "env_key": "TEST_AGENT_API_KEY",
                }
            },
        }
        with (
            patch.dict(os.environ, {"TEST_AGENT_API_KEY": "test-key"}, clear=True),
            patch.object(llm_config, "_read_toml", side_effect=[primary_cfg, api_cfg]),
            patch.object(llm_config, "_read_json", return_value={"tokens": {}}),
        ):
            llm_config.resolve_llm_cfg.cache_clear()
            cfg = llm_config.resolve_llm_cfg()

        llm_config.resolve_llm_cfg.cache_clear()
        self.assertEqual(cfg.source, "api_config_fallback")
        self.assertEqual(cfg.endpoint, "https://api.invalid/v1/responses")
        self.assertEqual(cfg.api_key_source, "env:TEST_AGENT_API_KEY")
        self.assertTrue(cfg.config_path.endswith("api.config.toml"))



if __name__ == "__main__":
    unittest.main()
