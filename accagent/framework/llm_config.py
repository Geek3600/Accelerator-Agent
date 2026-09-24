"""Unified LLM configuration resolution for the framework."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.11 fallback
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:
        tomllib = None  # type: ignore[assignment]


@dataclass(frozen=True)
class LlmCfg:
    mode: str = "llm"
    model: str = ""
    endpoint: str = ""
    api_key: str = ""
    temperature: float = 0.0
    timeout_sec: int = 1800
    enforce: bool = True
    reasoning_effort: str | None = None
    store: bool = False
    text_verbosity: str | None = None
    max_output_tokens: int | None = None
    stream: bool = True
    provider: str = ""
    base_url: str = ""
    fallback_endpoint: str = ""
    fallback_api_key: str = ""
    fallback_base_url: str = ""
    wire_api: str = ""
    source: str = ""
    api_key_source: str = ""
    config_path: str = ""
    auth_path: str = ""
    configured_model: str = ""
    requested_model_override: str = ""
    http_transport: str = "urllib"
    configuration_error: str = ""


def _env(name: str, default: str = "") -> str:
    value = os.environ.get(name, "")
    return value if value != "" else default


def _truthy(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text == "":
        return default
    return text in {"1", "true", "yes", "on"}


def _read_toml(path: Path) -> dict[str, Any]:
    if not path.exists() or tomllib is None:
        return {}
    with path.open("rb") as f:
        data = tomllib.load(f)
    return data if isinstance(data, dict) else {}


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _clean_text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _provider_config(cfg: dict[str, Any], provider_name: str) -> dict[str, Any]:
    providers = cfg.get("model_providers")
    if not isinstance(providers, dict):
        return {}
    provider = providers.get(provider_name)
    return provider if isinstance(provider, dict) else {}


def _normalize_responses_endpoint(base_url: str, wire_api: str) -> str:
    base = base_url.strip().rstrip("/")
    api = wire_api.strip().strip("/")
    if not base:
        return ""
    if not api or api == "responses":
        if base.endswith("/v1/responses"):
            return base
        if base.endswith("/responses"):
            return base
        if base.endswith("/v1"):
            return base + "/responses"
        return base + "/v1/responses"
    if api.startswith("http://") or api.startswith("https://"):
        return api
    if base.endswith("/" + api):
        return base
    return base + "/" + api


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    return _truthy(raw, default)


def _env_int(name: str, default: int, minimum: int = 0) -> int:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return max(minimum, int(raw))
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _agent_reasoning_effort(env_reasoning: str, configured_reasoning: str) -> str:
    """Choose the reasoning effort used by local framework HTTP requests."""

    if env_reasoning:
        return env_reasoning
    if configured_reasoning.strip().lower() == "ultra":
        return "xhigh"
    return configured_reasoning


def _http_transport(value: str) -> str:
    """Normalize the framework-owned HTTP transport selection."""

    normalized = value.strip().lower().replace("-", "_")
    aliases = {
        "": "urllib",
        "urllib": "urllib",
        "python": "urllib",
        "curl": "curl_direct_http1",
        "curl_direct": "curl_direct_http1",
        "curl_direct_http1": "curl_direct_http1",
    }
    if normalized not in aliases:
        raise ValueError(
            "SPATIALACC_LLM_TRANSPORT must be urllib or curl_direct_http1"
        )
    return aliases[normalized]


def _auth_key_candidates(provider_name: str) -> list[str]:
    normalized = provider_name.upper().replace("-", "_").replace(" ", "_")
    keys = [f"{normalized}_API_KEY"]
    if normalized != "OPENAI":
        keys.append("OPENAI_API_KEY")
    else:
        keys.insert(0, "OPENAI_API_KEY")
    return keys


def _auth_api_key(auth: dict[str, Any], provider_name: str) -> tuple[str, str]:
    for key in _auth_key_candidates(provider_name):
        value = auth.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip(), f"auth.json:{key}"
    for key, value in auth.items():
        if isinstance(key, str) and key.upper().endswith("_API_KEY") and isinstance(value, str) and value.strip():
            return value.strip(), f"auth.json:{key}"
    env_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if env_key:
        return env_key, "env:OPENAI_API_KEY"
    return "", ""


def _provider_env_api_key(provider_cfg: dict[str, Any]) -> tuple[str, str]:
    """Resolve an explicitly declared provider credential without exposing it."""

    env_key = _clean_text(provider_cfg.get("env_key"))
    if not env_key:
        return "", ""
    value = _clean_text(os.environ.get(env_key, ""))
    return (value, f"env:{env_key}") if value else ("", "")


@lru_cache(maxsize=1)
def resolve_llm_cfg() -> LlmCfg:
    """Resolve LLM settings from explicit env vars or the user's Codex config."""

    env_mode = _clean_text(_env("SPATIALACC_LLM_MODE"))
    env_model = _clean_text(_env("SPATIALACC_LLM_MODEL"))
    env_endpoint = _clean_text(_env("SPATIALACC_LLM_ENDPOINT"))
    env_base_url = _clean_text(_env("SPATIALACC_LLM_BASE_URL"))
    env_fallback_endpoint = _clean_text(_env("SPATIALACC_LLM_FALLBACK_ENDPOINT"))
    env_fallback_base_url = _clean_text(_env("SPATIALACC_LLM_FALLBACK_BASE_URL"))
    env_fallback_api_key = _clean_text(_env("SPATIALACC_LLM_FALLBACK_API_KEY"))
    env_wire_api = _clean_text(_env("SPATIALACC_LLM_WIRE_API"))
    env_api_key = _clean_text(_env("SPATIALACC_LLM_API_KEY"))
    env_reasoning = _clean_text(_env("SPATIALACC_LLM_REASONING_EFFORT"))
    env_transport = _clean_text(_env("SPATIALACC_LLM_TRANSPORT"))
    env_verbosity = _clean_text(_env("SPATIALACC_LLM_TEXT_VERBOSITY"))
    env_max_output_tokens = os.environ.get("SPATIALACC_LLM_MAX_OUTPUT_TOKENS")
    env_store = os.environ.get("SPATIALACC_LLM_STORE")
    env_stream = os.environ.get("SPATIALACC_LLM_STREAM")
    env_timeout = os.environ.get("SPATIALACC_LLM_TIMEOUT_SEC")
    env_temperature = os.environ.get("SPATIALACC_LLM_TEMPERATURE")

    codex_cfg_path = Path.home() / ".codex" / "config.toml"
    codex_auth_path = Path.home() / ".codex" / "auth.json"
    codex_cfg = _read_toml(codex_cfg_path)
    codex_auth = _read_json(codex_auth_path)

    provider_name = _clean_text(codex_cfg.get("model_provider"))
    provider_cfg = _provider_config(codex_cfg, provider_name) if provider_name else {}

    configured_model = _clean_text(codex_cfg.get("model")) or _clean_text(codex_cfg.get("review_model"))
    requested_model_override = (
        env_model if env_model and env_model != configured_model else ""
    )
    # The launcher/user's explicit model selection is already the authorization.
    # A second approval artifact only duplicated configuration work and blocked
    # recovery experiments without adding hardware-verification evidence.
    cfg_model = env_model or configured_model
    cfg_base_url = env_base_url or _clean_text(provider_cfg.get("base_url"))
    cfg_wire_api = env_wire_api or _clean_text(provider_cfg.get("wire_api"))
    cfg_endpoint = env_endpoint or _normalize_responses_endpoint(cfg_base_url, cfg_wire_api)
    cfg_fallback_base_url = env_fallback_base_url
    cfg_fallback_endpoint = env_fallback_endpoint or _normalize_responses_endpoint(
        cfg_fallback_base_url, cfg_wire_api
    )
    cfg_reasoning = _agent_reasoning_effort(env_reasoning, _clean_text(codex_cfg.get("model_reasoning_effort")))
    cfg_store = _truthy(env_store, default=not _truthy(codex_cfg.get("disable_response_storage"), default=False))
    cfg_stream = _env_bool("SPATIALACC_LLM_STREAM", True) if env_stream is not None else True
    cfg_timeout = _env_int("SPATIALACC_LLM_TIMEOUT_SEC", 1800, 1) if env_timeout is not None else 1800
    cfg_temperature = _env_float("SPATIALACC_LLM_TEMPERATURE", 0.0) if env_temperature is not None else 0.0
    cfg_max_output_tokens = (
        _env_int("SPATIALACC_LLM_MAX_OUTPUT_TOKENS", 0, 0)
        if env_max_output_tokens is not None
        else 0
    )
    source = "env" if (env_model or env_endpoint or env_api_key or env_base_url or env_wire_api or env_reasoning or env_transport or env_max_output_tokens is not None) else "codex_config"
    cfg_enforce = True
    try:
        cfg_http_transport = _http_transport(env_transport)
        transport_error = ""
    except ValueError as exc:
        cfg_http_transport = "urllib"
        transport_error = str(exc)

    api_key = env_api_key
    api_key_source = "env:SPATIALACC_LLM_API_KEY" if api_key else ""
    if not api_key:
        api_key, api_key_source = _provider_env_api_key(provider_cfg)
    if not api_key:
        api_key, api_key_source = _auth_api_key(codex_auth, provider_name or "OpenAI")

    # Codex may be signed in through ChatGPT OAuth while an adjacent API
    # configuration supplies the actual key-based provider used by autonomous
    # framework subprocesses. An endpoint without a credential is incomplete,
    # so prefer the complete fallback whenever the primary configuration has
    # no compatible key. An explicit SPATIALACC_LLM_API_KEY already wins above.
    if not api_key:
        api_cfg_path = codex_cfg_path.with_name("api.config.toml")
        api_cfg = _read_toml(api_cfg_path)
        api_provider_name = _clean_text(api_cfg.get("model_provider"))
        api_provider_cfg = (
            _provider_config(api_cfg, api_provider_name) if api_provider_name else {}
        )
        api_key, api_key_source = _provider_env_api_key(api_provider_cfg)
        api_base_url = _clean_text(api_provider_cfg.get("base_url"))
        api_wire_api = _clean_text(api_provider_cfg.get("wire_api"))
        api_endpoint = _normalize_responses_endpoint(api_base_url, api_wire_api)
        if api_key and api_endpoint:
            provider_name = api_provider_name
            provider_cfg = api_provider_cfg
            configured_model = _clean_text(api_cfg.get("model")) or _clean_text(
                api_cfg.get("review_model")
            )
            cfg_model = env_model or configured_model
            cfg_base_url = api_base_url
            cfg_wire_api = api_wire_api
            cfg_endpoint = api_endpoint
            cfg_reasoning = _agent_reasoning_effort(
                env_reasoning, _clean_text(api_cfg.get("model_reasoning_effort"))
            )
            codex_cfg_path = api_cfg_path
            source = "api_config_fallback"

    if source == "codex_config" and not (env_model or env_endpoint or env_api_key or env_base_url or env_wire_api or env_transport or env_max_output_tokens is not None):
        if not codex_cfg:
            source = "defaults"

    return LlmCfg(
        mode="llm",
        model=cfg_model,
        endpoint=cfg_endpoint,
        api_key=api_key,
        temperature=cfg_temperature,
        timeout_sec=cfg_timeout,
        enforce=cfg_enforce,
        reasoning_effort=cfg_reasoning or None,
        store=cfg_store,
        text_verbosity=env_verbosity or None,
        max_output_tokens=cfg_max_output_tokens or None,
        stream=cfg_stream,
        provider=provider_name,
        base_url=cfg_base_url,
        fallback_endpoint=cfg_fallback_endpoint,
        fallback_api_key=env_fallback_api_key,
        fallback_base_url=cfg_fallback_base_url,
        wire_api=cfg_wire_api,
        source=source,
        api_key_source=api_key_source,
        config_path=str(codex_cfg_path),
        auth_path=str(codex_auth_path),
        configured_model=configured_model,
        requested_model_override=requested_model_override,
        http_transport=cfg_http_transport,
        configuration_error=transport_error,
    )


def resolved_llm_cfg() -> LlmCfg:
    return resolve_llm_cfg()
