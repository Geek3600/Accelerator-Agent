"""Prepare independent Stage 0 inputs with LLM-facing sub-agents."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import shlex
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable

from accagent.framework.agent_common import compact_json
from accagent.framework.case_adapter import adapter_tool, build_case_adapter
from accagent.framework.dse_candidates import physical_candidate_tuples
from accagent.framework.llm_config import resolved_llm_cfg
from accagent.framework.llm_io import (
    PROMPT_PROTOCOL,
    build_prompt,
    parse_json_object,
    read_response_text,
    repair_prompt,
    response_payload,
    validate_schema,
)
from accagent.framework.model_config_extractor import ConfigError, normalize
from accagent.framework.numeric_policy import resolve_numeric_policy
from accagent.framework.stage_input_common import (
    DEFAULT_TEMPLATE_DIR,
    DEFAULT_BOARD_MATERIALS_DIR,
    DEFAULT_QUANTIZATION_MATERIALS_DIR,
    DEFAULT_TOOL_MATERIALS_DIR,
    InputPreparationError,
    read_json,
    rel,
    write_json,
)
from accagent.framework.stage_team import run_design_team, team_failure_errors, team_summary
from accagent.framework.stage_llm import (
    llm_transient_attempts,
    llm_transient_retry_unbounded,
    retry_sleep_seconds,
    stream_transport_fallback_error,
    transient_llm_error,
)


TEXT_SUFFIXES = {
    ".md",
    ".rst",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".tcl",
    ".xdc",
    ".sdc",
    ".sv",
    ".v",
    ".vhd",
    ".vh",
    ".xpr",
    ".xci",
    ".xml",
    ".sh",
    ".py",
    ".mk",
    ".make",
    ".cfg",
    ".ini",
    ".log",
    ".rpt",
}


SENSITIVE_FIELD_MARKERS = (
    "password",
    "passphrase",
    "secret",
    "credential",
    "private_key",
    "private-key",
    "api_key",
    "api-key",
    "access_key",
    "access-key",
    "authorization",
)
SENSITIVE_TEXT_PATTERNS = (
    re.compile(
        r"(?im)^(?=[^\n]*(?:password(?!less\b)|passphrase|secret|credential|private[ _-]?key|api[ _-]?key|access[ _-]?key|authorization))[^\n]*$"
    ),
    re.compile(r"(?im)^.*(?:密码|口令|密钥|令牌).*$"),
)


def is_sensitive_field(name: object) -> bool:
    value = str(name or "").strip().lower().replace("passwordless", "")
    return any(marker in value for marker in SENSITIVE_FIELD_MARKERS)


def redact_sensitive_text(text: str) -> str:
    """Keep Stage-0 prompts and records free of credentials from user materials."""

    redacted = text
    for pattern in SENSITIVE_TEXT_PATTERNS:
        redacted = pattern.sub("[REDACTED SENSITIVE MATERIAL]", redacted)
    return redacted


def sanitize_llm_payload(value: Any) -> Any:
    """Drop credential-shaped fields before persisting or reusing LLM artifacts."""

    if isinstance(value, list):
        return [item for item in (sanitize_llm_payload(item) for item in value) if item is not None]
    if not isinstance(value, dict):
        return value
    if is_sensitive_field(value.get("field")):
        return None
    return {
        str(key): sanitized
        for key, item in value.items()
        if not is_sensitive_field(key)
        if (sanitized := sanitize_llm_payload(item)) is not None
    }


STAGE0_SYSTEM = """You are a SpatialAccAgent input-preparation specialist.

You are part of a chip-design team building spatial FPGA accelerators for
decoder-only LLM inference. Your Stage 0 responsibility is to convert the
current-run human input materials into precise hardware-facing JSON objects
that downstream architecture, code generation, verification, and backend teams
can trust.

Team context:
- model/shape specialists need exact decoder block, attention, MLP, norm, head,
  sequence, and operator-order facts;
- numeric specialists need precision, quantization, tolerance, rounding, and
  missing-policy risks;
- board/platform specialists need FPGA part, DDR/AXI width, shell/runtime,
  remote execution, and board pass criteria;
- toolchain specialists need VCS or Verilator for functional verification and
  Vivado for synthesis, implementation, and bitstream generation;
- later teams must preserve cross-layer consistency and cannot silently change
  model semantics, numeric policy, memory layout, AXI/DDR access, or template
  architecture.

Rules:
- Use only facts visible in the supplied materials or deterministic candidate.
- Treat deterministic regex/parser outputs as candidate evidence only; semantic extraction from non-structured user materials must be performed by the LLM with cited source evidence.
- Do not reduce prompt completeness or omit design/debug intent to make a request shorter. If a request must be split for transport stability, split it by complete semantic domain or complete material chunk, preserve source/provenance/conflicts, and make each sub-agent's responsibility explicit.
- Production runs must use real LLM calls and real tools. Fallback, dry-run, smoke-only, or checker-skipped evidence cannot promote a design.
- Hardware debug and repair must follow the three-layer loop: operator/leaf modules first, connected single-transformer-layer kernel second, and board-accurate AXI/DDR wrapped system third. A failed layer must use real tool output, CCTG/contract-guided localization, bounded repair, and rerun until correct before promotion.
- Do not accept or reject input facts because they match a fixed project/model/board keyword list.
- Do not invent hidden model, board, tool, or quantization facts.
- If materials are incomplete or conflicting, keep unknown fields null and
  record the issue in notes.
- Return only the requested top-level JSON object.
"""


MODEL_CONFIG_SCHEMA = {
    "type": "object",
    "additionalProperties": True,
    "properties": {
        "model_type": {"type": "string"},
        "model_dir": {"type": "string"},
        "num_layers": {"type": "integer"},
        "hidden_size": {"type": "integer"},
        "target_max_seq_len": {"type": "integer"},
        "block": {"type": "object", "additionalProperties": True, "required": ["operator_sequence"]},
        "attention": {"type": "object", "additionalProperties": True},
        "norm": {"type": "object", "additionalProperties": True},
        "mlp": {"type": "object", "additionalProperties": True},
    },
    "required": ["model_type", "num_layers", "hidden_size", "target_max_seq_len", "block", "attention", "norm", "mlp"],
}


TASK_CARD_SCHEMA = {
    "type": "object",
    "additionalProperties": True,
    "properties": {
        "schema_version": {"type": "string"},
        "target_model": {"type": "string"},
        "target_layers": {"type": "integer"},
        "target_seq_len": {"type": "integer"},
        "design_goal": {"type": "string"},
        "human_inputs": {"type": "array", "items": {"type": "string"}},
        "required_outputs": {"type": "array", "items": {"type": "string"}},
        "acceptance_policy": {"type": "object", "additionalProperties": True},
        "notes": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["schema_version", "target_model", "target_layers", "target_seq_len", "design_goal", "human_inputs", "notes"],
}


NUMERIC_POLICY_SCHEMA = {
    "type": "object",
    "additionalProperties": True,
    "properties": {
        "schema_version": {"type": "string"},
        "policy_id": {"type": "string"},
        "default_rules": {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "weight_dtype": {"type": "string"},
                "activation_dtype": {"type": "string"},
                "acc_dtype": {"type": "string"},
                "scale_dtype": {"type": "string"},
                "rounding": {"type": "string"},
                "saturation": {"type": "boolean"},
            },
            "required": ["weight_dtype", "activation_dtype", "acc_dtype", "scale_dtype", "rounding", "saturation"],
        },
        "tolerance": {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "stage": {"type": "string"},
                "system": {"type": "string"},
                "comparison": {
                    "type": "object",
                    "additionalProperties": True,
                    "properties": {
                        "atol": {"type": "number", "minimum": 0},
                        "rtol": {"type": "number", "minimum": 0},
                        "max_mismatch_fraction": {"type": "number", "minimum": 0, "maximum": 1},
                    },
                },
            },
            "required": ["stage", "system"],
        },
        "notes": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["schema_version", "policy_id", "default_rules", "tolerance", "notes"],
}


BOARD_PROFILE_SCHEMA = {
    "type": "object",
    "additionalProperties": True,
    "properties": {
        "schema_version": {"type": "string"},
        "board": {"type": "object", "additionalProperties": True},
        "shell": {"type": "object", "additionalProperties": True},
        "memory_system": {"type": "object", "additionalProperties": True},
        "runtime_interface": {"type": "object", "additionalProperties": True},
        "board_pass_criteria": {"type": "object", "additionalProperties": True},
        "notes": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["schema_version", "board", "shell", "memory_system", "runtime_interface", "board_pass_criteria", "notes"],
}


TOOL_PROFILE_SCHEMA = {
    "type": "object",
    "additionalProperties": True,
    "properties": {
        "schema_version": {"type": "string"},
        "tools": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": True,
                "properties": {
                    "name": {"type": "string"},
                    "role": {"type": "string"},
                    "scope": {"type": ["string", "null"]},
                    "host": {"type": ["string", "null"]},
                    "port": {"type": ["integer", "null"]},
                    "executable": {"type": ["string", "null"]},
                    "env": {"type": "object", "additionalProperties": True},
                    "workdir": {"type": ["string", "null"]},
                    "constraints": {"type": "array", "items": {"type": "string"}},
                    "source": {"type": ["string", "null"]},
                },
                "required": ["name", "role", "scope", "host", "port", "executable", "env", "workdir", "constraints", "source"],
            },
        },
        "notes": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["schema_version", "tools", "notes"],
}


FIELD_EVIDENCE_SCHEMA = {
    "type": "object",
    "additionalProperties": True,
    "properties": {
        "schema_version": {"type": "string"},
        "policy": {"type": "object", "additionalProperties": True},
        "evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": True,
                "properties": {
                    "field": {"type": "string"},
                    "value": {},
                    "source": {"type": ["string", "null"]},
                    "chunk_id": {"type": ["string", "null"]},
                    "excerpt": {"type": "string"},
                    "confidence": {"type": ["string", "number", "null"]},
                    "reason": {"type": ["string", "null"]},
                },
                "required": ["field", "value", "source", "chunk_id", "excerpt"],
            },
        },
    },
    "required": ["schema_version", "policy", "evidence"],
}


DESIGN_SPACE_SCHEMA = {
    "type": "object",
    "additionalProperties": True,
    "properties": {
        "schema_version": {"type": "string"},
        "status": {"type": "string"},
        "sources": {"type": "object", "additionalProperties": True},
        "search_params": {"type": "object", "additionalProperties": True},
        "objectives": {"type": "array", "items": {"type": "string"}},
        "hard_constraints": {"type": "array", "items": {"type": "string"}},
        "notes": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["schema_version", "status", "sources", "search_params", "objectives", "hard_constraints", "notes"],
}


def framework_physical_candidate_domain_seed() -> dict[str, Any]:
    """Return the read-only default topology domain available to Stage-0 agents.

    This declares framework-supported generated-hardware topology, not a
    case-specific architecture choice.  The LLM must still return the complete
    current design-space domain, and Stage 4 remains the sole selector.
    """

    return {
        "candidate_universe": {
            "candidate_dimensions": {
                "lanes": {"legal_values": [8, 16]},
                "compute_array": {
                    "legal_row_col_pairs": [
                        {"rows": 4, "cols": 4},
                        {"rows": 4, "cols": 8},
                        {"rows": 4, "cols": 16},
                        {"rows": 8, "cols": 4},
                        {"rows": 8, "cols": 8},
                        {"rows": 8, "cols": 16},
                        {"rows": 16, "cols": 4},
                        {"rows": 16, "cols": 8},
                        {"rows": 16, "cols": 16},
                    ]
                },
                "physical_fifo_depth": {"legal_values": [32, 64, 128]},
                "activation_bank_count": {"legal_values": [2, 4]},
            }
        }
    }


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def read_docx_text(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as zf:
            xml = zf.read("word/document.xml").decode("utf-8", errors="replace")
    except Exception as exc:
        return f"[unable to extract docx text: {exc}]"
    text = re.sub(r"<[^>]+>", " ", xml)
    text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    return re.sub(r"\s+", " ", text).strip()


def ensure_pdftotext() -> tuple[bool, str]:
    probe = subprocess.run(["bash", "-lc", "command -v pdftotext"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if probe.returncode == 0 and probe.stdout.strip():
        return True, probe.stdout.strip()

    installers = [
        ["bash", "-lc", "command -v apt-get >/dev/null && sudo -n apt-get update && sudo -n apt-get install -y poppler-utils"],
        ["bash", "-lc", "command -v dnf >/dev/null && sudo -n dnf install -y poppler-utils"],
        ["bash", "-lc", "command -v yum >/dev/null && sudo -n yum install -y poppler-utils"],
    ]
    errors = []
    for cmd in installers:
        proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300, check=False)
        if proc.returncode == 0:
            retry = subprocess.run(["bash", "-lc", "command -v pdftotext"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            if retry.returncode == 0 and retry.stdout.strip():
                return True, retry.stdout.strip()
        errors.append((proc.stderr or proc.stdout).strip())
    return False, "; ".join(error for error in errors if error)


def read_pdf_text(path: Path) -> str:
    available, detail = ensure_pdftotext()
    if not available:
        return f"[unable to extract pdf text: pdftotext is not installed and automatic install failed: {detail}]"
    try:
        proc = subprocess.run(
            ["pdftotext", str(path), "-"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
            check=False,
        )
    except Exception as exc:
        return f"[unable to extract pdf text: {exc}]"
    if proc.returncode != 0:
        return f"[unable to extract pdf text: {proc.stderr.strip()}]"
    return proc.stdout


def env_int(name: str, default: int, minimum: int = 0) -> int:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return max(minimum, int(raw))
    except ValueError:
        return default


def read_material_file(path: Path) -> tuple[str, str | None]:
    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES or not suffix:
        return read_text(path), None
    if suffix == ".docx":
        return read_docx_text(path), None
    if suffix == ".pdf":
        return read_pdf_text(path), None
    return "", "unsupported suffix"


def split_material_chunks(text: str, chars_per_chunk: int) -> list[tuple[int, int, str]]:
    if not text:
        return []
    if chars_per_chunk <= 0:
        return [(0, len(text), text)]
    chunks = []
    for start in range(0, len(text), chars_per_chunk):
        end = min(start + chars_per_chunk, len(text))
        chunks.append((start, end, text[start:end]))
    return chunks


def read_text_bundle_indexed(path: Path, input_dir: Path, label: str) -> tuple[str, dict[str, Any]]:
    """Read current-run materials, split them into citeable chunks, and write an index."""

    chars_per_chunk = env_int("SPATIALACC_MATERIAL_CHUNK_CHARS", 12000, 1000)
    prompt_max_chars = env_int("SPATIALACC_MATERIAL_PROMPT_MAX_CHARS", 0, 0)
    index: dict[str, Any] = {
        "schema_version": "spatialaccagent.material_index.v0",
        "label": label,
        "root": str(path.resolve()) if path.exists() else str(path),
        "chunk_chars": chars_per_chunk,
        "prompt_max_chars": prompt_max_chars or None,
        "files": [],
        "chunks": [],
        "skipped": [],
        "prompt_omitted_chunks": [],
    }
    if not path.exists():
        write_json(input_dir / f"material_index_{label}.json", index)
        return "", index

    files = [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file())
    prompt_parts: list[str] = []
    prompt_chars = 0
    chunk_no = 0
    for f in files:
        if f.name.startswith("."):
            continue
        text, skipped_reason = read_material_file(f)
        if skipped_reason:
            index["skipped"].append({"path": str(f), "reason": skipped_reason})
            continue
        if not text:
            continue
        file_record = {
            "path": str(f),
            "suffix": f.suffix.lower(),
            "chars": len(text),
            "sha256": hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest(),
        }
        index["files"].append(file_record)
        for start, end, chunk_text in split_material_chunks(text, chars_per_chunk):
            chunk_no += 1
            chunk_id = f"{label}:{chunk_no:06d}"
            chunk_record = {
                "id": chunk_id,
                "source": str(f),
                "offset_start": start,
                "offset_end": end,
                "chars": len(chunk_text),
            }
            index["chunks"].append(chunk_record)
            block = (
                f"### chunk:{chunk_id} source:{f} offset:{start}-{end}\n"
                "```text\n"
                f"{chunk_text}\n"
                "```"
            )
            if prompt_max_chars and prompt_chars + len(block) > prompt_max_chars:
                index["prompt_omitted_chunks"].append(chunk_id)
                continue
            prompt_parts.append(block)
            prompt_chars += len(block)
    write_json(input_dir / f"material_index_{label}.json", index)
    return "\n\n".join(prompt_parts), index


def read_text_bundle(path: Path) -> str:
    """Read all user-provided documents and sample-project text into one prompt block."""

    if not path.exists():
        return ""
    if path.is_file():
        return read_text(path)

    chunks: list[str] = []
    skipped: list[str] = []
    for f in sorted(p for p in path.rglob("*") if p.is_file()):
        if f.name.startswith("."):
            continue
        text, skipped_reason = read_material_file(f)
        if skipped_reason:
            skipped.append(str(f))
            continue
        if not text:
            continue
        chunks.append(f"### {f}\n```text\n{text}\n```")
    if skipped:
        chunks.append(
            "### Non-text files discovered in user materials\n```text\n"
            + "\n".join(skipped[:500])
            + "\n```"
        )
    return "\n\n".join(chunks)


def llm_mode() -> str:
    return resolved_llm_cfg().mode


def llm_enforce() -> bool:
    return resolved_llm_cfg().enforce


def llm_required() -> bool:
    return True


def env_first(*names: str, default: str = "") -> str:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return default


def llm_timeout_sec() -> int:
    return resolved_llm_cfg().timeout_sec


def require_llm_configuration(input_dir: Path) -> None:
    """Fail before Stage 0 starts if a real LLM endpoint is not configured."""

    llm = resolved_llm_cfg()
    mode = llm.mode
    endpoint = llm.endpoint
    model = llm.model
    key_present = bool(llm.api_key)
    errors: list[str] = []
    if mode.strip().lower() in {"", "off", "none", "disabled"}:
        errors.append(f"LLM mode is disabled: {mode}")
    if not endpoint:
        errors.append("missing LLM endpoint")
    if not model:
        errors.append("missing LLM model")
    if not key_present:
        errors.append("missing LLM api key")

    write_json(
        input_dir / "llm_preflight.json",
        {
            "schema_version": "spatialaccagent.llm_preflight.v0",
            "mode": mode,
            "provider": llm.provider,
            "base_url": llm.base_url,
            "wire_api": llm.wire_api,
            "config_path": llm.config_path,
            "auth_path": llm.auth_path,
            "api_key_source": llm.api_key_source,
            "endpoint_configured": bool(endpoint),
            "model_configured": bool(model),
            "api_key_configured": key_present,
            "ready": not errors,
            "errors": errors,
        },
    )
    if errors:
        raise InputPreparationError("LLM configuration incomplete: " + "; ".join(errors))


def prompt_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def cached_llm_output(out_path: Path, expected_prompt_hash: str) -> dict[str, Any] | None:
    if not out_path.exists():
        return None
    try:
        record = read_json(out_path)
    except Exception:
        return None
    if record.get("error") or record.get("used_fallback"):
        return None
    existing_hash = record.get("prompt_hash")
    if existing_hash and existing_hash != expected_prompt_hash:
        return None
    output = record.get("output")
    return output if isinstance(output, dict) else None


class LlmTransientFailure(InputPreparationError):
    def __init__(self, message: str, retry_errors: list[str]):
        super().__init__(message)
        self.retry_errors = retry_errors


def compact_for_llm_retry(value: Any, *, depth: int = 0) -> Any:
    max_depth = env_int("SPATIALACC_STAGE0_COMPACT_RETRY_DEPTH", 5, 1)
    max_items = env_int("SPATIALACC_STAGE0_COMPACT_RETRY_ITEMS", 40, 8)
    max_text = env_int("SPATIALACC_STAGE0_COMPACT_RETRY_TEXT", 180, 80)
    if depth >= max_depth:
        if isinstance(value, (dict, list)):
            return {"_omitted": type(value).__name__}
        return value
    if isinstance(value, str):
        if len(value) <= max_text:
            return value
        return value[:max_text] + f"\n... truncated {len(value) - max_text} chars ..."
    if isinstance(value, list):
        result = [compact_for_llm_retry(item, depth=depth + 1) for item in value[:max_items]]
        if len(value) > max_items:
            result.append({"_omitted_items": len(value) - max_items})
        return result
    if isinstance(value, dict):
        return {str(key): compact_for_llm_retry(item, depth=depth + 1) for key, item in value.items()}
    return value


def build_compact_retry_prompt(name: str, schema: dict[str, Any], candidate: dict[str, Any], error: str) -> str:
    return build_prompt(
        agent=f"{name}_compact_retry",
        task=(
            "The full Stage 0 LLM request failed during provider transport. Produce the same schema-bound "
            "JSON using this compacted current-run candidate evidence. This is still a mandatory LLM "
            "semantic review; do not copy values blindly if the compact evidence is insufficient."
        ),
        inputs={
            "full_prompt_transport_error": error,
            "compacted_candidate_evidence": compact_for_llm_retry(candidate),
            "candidate_policy": (
                "Deterministic candidates are hints and source excerpts, not accepted evidence. "
                "Return only fields supported by the compacted evidence, and preserve uncertainty or conflicts."
            ),
        },
        output_schema=schema,
        rules=[
            "Return exactly one valid JSON object matching the output schema.",
            "Keep used_fallback false by producing a real LLM decision; do not claim tool or checker pass.",
            "If compact evidence is insufficient for a field, omit that field or record the conflict instead of inventing it.",
            "Every evidence item that remains must cite its source and excerpt from the compacted candidate evidence.",
        ],
    )


def allow_lossy_compact_retry() -> bool:
    return os.environ.get("SPATIALACC_STAGE0_ALLOW_LOSSY_COMPACT_RETRY", "").strip().lower() in {"1", "true", "yes", "on"}


def stage0_llm_request(
    endpoint: str,
    key: str,
    model: str,
    prompt: str,
    schema_name: str,
    schema: dict[str, Any],
    *,
    store: bool,
    reasoning_effort: str | None,
    text_verbosity: str | None,
    max_output_tokens: int | None,
    stream: bool,
) -> urllib.request.Request:
    """Build a Stage-0 request for one concrete Responses transport."""

    payload = response_payload(
        model,
        STAGE0_SYSTEM,
        prompt,
        schema_name,
        schema,
        strict=False,
        store=store,
        reasoning_effort=reasoning_effort,
        text_verbosity=text_verbosity,
        max_output_tokens=max_output_tokens,
        stream=stream,
    )
    return urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream" if stream else "application/json",
            "Connection": "close",
        },
        method="POST",
    )


def post_llm_json(
    request_or_factory: urllib.request.Request | Callable[[bool], urllib.request.Request],
    timeout_sec: int,
    label: str,
    stream: bool,
) -> tuple[str, list[str]]:
    """Retry one Stage-0 request and switch SSE/JSON after a transport fault."""

    errors: list[str] = []
    max_attempts = None if llm_transient_retry_unbounded() else llm_transient_attempts()
    attempt = 1
    current_stream = stream

    def request_for_transport(use_stream: bool) -> urllib.request.Request:
        if callable(request_or_factory):
            return request_or_factory(use_stream)
        return request_or_factory

    while True:
        try:
            return read_response_text(
                request_for_transport(current_stream), timeout_sec, current_stream
            ), errors
        except Exception as exc:
            errors.append(f"attempt {attempt}: {exc}")
            if not transient_llm_error(exc):
                raise LlmTransientFailure(str(exc), errors) from exc
            if max_attempts is not None and attempt >= max_attempts:
                raise LlmTransientFailure(str(exc), errors) from exc
            delay = retry_sleep_seconds(exc, attempt)
            retry_mode = "unbounded" if max_attempts is None else f"{attempt}/{max_attempts}"
            print(
                f"[stage0:llm] retry {label} after transient error "
                f"({retry_mode}): {exc}; sleep {delay:.1f}s",
                file=sys.stderr,
                flush=True,
            )
            if stream_transport_fallback_error(exc):
                current_stream = not current_stream
                transport = "responses_sse_stream" if current_stream else "responses_json"
                print(
                    f"[stage0:llm] switching {label} retry transport to {transport}",
                    file=sys.stderr,
                    flush=True,
                )
            time.sleep(delay)
            attempt += 1


def llm_json(name: str, prompt: str, schema: dict[str, Any], candidate: dict[str, Any], log_dir: Path) -> dict[str, Any]:
    """Ask the configured LLM for JSON. Stage 0 does not run without LLM."""

    log_dir.mkdir(parents=True, exist_ok=True)
    prompt = redact_sensitive_text(prompt)
    candidate = sanitize_llm_payload(candidate)
    req_path = log_dir / f"{name}_request.md"
    out_path = log_dir / f"{name}_result.json"
    req_path.write_text(prompt, encoding="utf-8")
    current_prompt_hash = prompt_hash(STAGE0_SYSTEM + "\n" + prompt)

    mode = llm_mode()
    cached = cached_llm_output(out_path, current_prompt_hash)
    if cached is not None:
        print(f"[stage0:llm] reuse cached {name}: {out_path}", file=sys.stderr, flush=True)
        return sanitize_llm_payload(cached) | {"_llm_provenance": {"sub_agent": name, "mode": mode, "used_fallback": False}}

    record: dict[str, Any] = {
        "schema_version": "spatialaccagent.stage0_llm_record.v1",
        "prompt_protocol": PROMPT_PROTOCOL,
        "sub_agent": name,
        "mode": mode,
        "request_path": str(req_path),
        "prompt_hash": current_prompt_hash,
        "used_fallback": False,
        "error": None,
        "deterministic_candidate": candidate,
        "output": None,
    }
    if mode.strip().lower() in {"", "off", "none", "disabled"}:
        if not llm_required():
            record["used_fallback"] = True
            record["output"] = candidate
            write_json(out_path, record)
            return candidate | {"_llm_provenance": {"sub_agent": name, "mode": mode, "used_fallback": True}}
        record["error"] = f"LLM mode is disabled: {mode}"
        write_json(out_path, record)
        raise InputPreparationError(record["error"])

    llm = resolved_llm_cfg()
    record["stream"] = llm.stream
    record["transport"] = "responses_sse_stream" if llm.stream else "responses_json"
    record["http_transport"] = llm.http_transport
    record["reasoning_effort"] = llm.reasoning_effort
    key = llm.api_key
    endpoint = llm.endpoint
    model = llm.model
    if not key or not endpoint:
        if not llm_required():
            record["used_fallback"] = True
            record["output"] = candidate
            write_json(out_path, record)
            return candidate | {"_llm_provenance": {"sub_agent": name, "mode": mode, "used_fallback": True}}
        record["error"] = "missing LLM endpoint or API key"
        write_json(out_path, record)
        raise InputPreparationError(record["error"])
    if not model:
        if not llm_required():
            record["used_fallback"] = True
            record["output"] = candidate
            write_json(out_path, record)
            return candidate | {"_llm_provenance": {"sub_agent": name, "mode": mode, "used_fallback": True}}
        record["error"] = "missing LLM model"
        write_json(out_path, record)
        raise InputPreparationError(record["error"])

    started = time.monotonic()
    print(f"[stage0:llm] start {name}", file=sys.stderr, flush=True)
    print(f"[stage0:llm] prompt {req_path}", file=sys.stderr, flush=True)
    def request_for(prompt_text: str, request_schema_name: str) -> Callable[[bool], urllib.request.Request]:
        return lambda use_stream: stage0_llm_request(
            endpoint,
            key,
            model,
            prompt_text,
            request_schema_name,
            schema,
            store=llm.store,
            reasoning_effort=llm.reasoning_effort,
            text_verbosity=llm.text_verbosity,
            max_output_tokens=llm.max_output_tokens,
            stream=use_stream,
        )

    try:
        try:
            raw_text, retry_errors = post_llm_json(
                request_for(prompt, f"{name}_json"),
                llm_timeout_sec(),
                f"{name}_json",
                llm.stream,
            )
        except Exception as first_exc:
            if not transient_llm_error(first_exc) or not allow_lossy_compact_retry():
                raise
            compact_prompt = build_compact_retry_prompt(name, schema, candidate, str(first_exc))
            compact_prompt_path = log_dir / f"{name}_compact_retry_request.md"
            compact_prompt_path.write_text(compact_prompt, encoding="utf-8")
            record["compact_retry_request_path"] = str(compact_prompt_path)
            record["compact_retry_after_error"] = str(first_exc)
            record["compact_retry_prompt_bytes"] = len(compact_prompt.encode("utf-8"))
            raw_text, compact_retry_errors = post_llm_json(
                request_for(compact_prompt, f"{name}_compact_retry_json"),
                llm_timeout_sec(),
                f"{name}_compact_retry_json",
                llm.stream,
            )
            retry_errors = [f"full prompt failed: {first_exc}", *compact_retry_errors]
        if retry_errors:
            record["retry_errors"] = retry_errors
        record["raw_text"] = redact_sensitive_text(raw_text)
        try:
            output = parse_json_object(raw_text)
            validate_schema(output, schema, name)
        except Exception as parse_exc:
            record["parse_error"] = str(parse_exc)
            fix_prompt = repair_prompt(name, prompt, raw_text, str(parse_exc), schema)
            repair_text, repair_retry_errors = post_llm_json(
                request_for(fix_prompt, f"{name}_repair_json"),
                llm_timeout_sec(),
                f"{name}_repair_json",
                llm.stream,
            )
            if repair_retry_errors:
                record["repair_retry_errors"] = repair_retry_errors
            record["repair_raw_text"] = redact_sensitive_text(repair_text)
            output = parse_json_object(repair_text)
            validate_schema(output, schema, name)
        output = sanitize_llm_payload(output)
        record["used_fallback"] = False
        record["duration_sec"] = time.monotonic() - started
        record["output"] = output
        write_json(out_path, record)
        print(f"[stage0:llm] done {name} ({record['duration_sec']:.1f}s)", file=sys.stderr, flush=True)
        print(f"[stage0:llm] output {name}: {compact_json(output, 900)}", file=sys.stderr, flush=True)
        print(f"[stage0:llm] log {out_path}", file=sys.stderr, flush=True)
        return output | {"_llm_provenance": {"sub_agent": name, "mode": mode, "used_fallback": False}}
    except Exception as exc:
        record["error"] = str(exc)
        if isinstance(exc, LlmTransientFailure):
            record["retry_errors"] = exc.retry_errors
        record["duration_sec"] = time.monotonic() - started
        write_json(out_path, record)
        print(f"[stage0:llm] failed {name}: {exc}", file=sys.stderr, flush=True)
        print(f"[stage0:llm] log {out_path}", file=sys.stderr, flush=True)
        raise InputPreparationError(str(exc)) from exc


def target_seq_from_task(task_text: str) -> int:
    return 16


def task_qor_targets(task_text: str) -> dict[str, Any]:
    """Extract explicit QoR gates from the current task specification.

    These values are user constraints, not LLM-generated architecture advice.
    The Stage-0 DSE agent receives them for context, but cannot erase or weaken
    them in the design-space artifact consumed by later stages.
    """

    text = " ".join(str(task_text or "").split())

    def target_number(patterns: list[str], *, unit_scale: float = 1.0) -> float | None:
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1)) * unit_scale
        return None

    clock_mhz = target_number(
        [r"(?:achieved\s+)?clock(?:\s+frequency)?[^.;:]{0,80}?(?:at\s+least|>=|no\s+less\s+than)\s*(\d+(?:\.\d+)?)\s*mhz"]
    )
    if clock_mhz is None:
        clock_mhz = target_number(
            [r"(?:achieved\s+)?clock(?:\s+frequency)?[^.;:]{0,80}?(?:at\s+least|>=|no\s+less\s+than)\s*(\d+(?:\.\d+)?)\s*ghz"],
            unit_scale=1000.0,
        )

    performance = target_number(
        [
            r"(?:measured\s+)?(?:performance|throughput)[^.;:]{0,100}?(?:strictly\s+greater\s+than|greater\s+than|>)\s*(\d+(?:\.\d+)?)\s*(?:tokens?\s*/\s*s|tokens?\s+per\s+second)",
            r"(?:measured\s+)?(?:performance|throughput)[^.;:]{0,100}?(?:at\s+least|>=|no\s+less\s+than)\s*(\d+(?:\.\d+)?)\s*(?:tokens?\s*/\s*s|tokens?\s+per\s+second)",
        ]
    )
    strict_performance = bool(
        re.search(
            r"(?:performance|throughput)[^.;:]{0,100}?(?:strictly\s+greater\s+than|>)",
            text,
            re.IGNORECASE,
        )
    )
    resources_within_board = bool(
        re.search(
            r"(?:lut|ff|bram|uram|dsp)[^.;:]{0,160}?(?:within|not\s+exceed|must\s+not\s+exceed)[^.;:]{0,120}?(?:board\s+)?resource\s+budget",
            text,
            re.IGNORECASE,
        )
    )
    power_measured = bool(re.search(r"(?:measure|report)[^.;:]{0,80}\bpower\b|\bpower\b[^.;:]{0,80}(?:measure|report)", text, re.IGNORECASE))
    power_unconstrained = bool(
        re.search(
            r"(?:no|without)\s+(?:a\s+)?power\s+limit|do\s+not\s+impose\s+(?:a\s+)?power\s+limit|power\s+(?:is\s+)?unconstrained",
            text,
            re.IGNORECASE,
        )
    )

    targets: dict[str, Any] = {
        "resource_budget": "discovered_target_board" if resources_within_board else None,
        "resource_comparison": "<=" if resources_within_board else None,
        "power_w": None,
        "power_report_required": power_measured,
        "power_limit_applies": not power_unconstrained if power_measured else None,
        "source": "task_spec",
    }
    if clock_mhz is not None:
        targets["clock_frequency_mhz"] = clock_mhz
        targets["clock_frequency_comparison"] = ">="
    if performance is not None:
        targets["performance_tokens_per_second"] = performance
        targets["performance_comparison"] = ">" if strict_performance else ">="
    return {key: value for key, value in targets.items() if value is not None}


def task_qor_hard_constraints(targets: dict[str, Any]) -> list[str]:
    constraints: list[str] = []
    clock = targets.get("clock_frequency_mhz")
    if isinstance(clock, (int, float)):
        constraints.append(f"clock_frequency_mhz {targets.get('clock_frequency_comparison', '>=')} {clock:g}")
    performance = targets.get("performance_tokens_per_second")
    if isinstance(performance, (int, float)):
        constraints.append(
            f"performance_tokens_per_second {targets.get('performance_comparison', '>=')} {performance:g}"
        )
    if targets.get("resource_budget") == "discovered_target_board":
        constraints.append("lut_ff_bram_uram_dsp <= discovered_target_board_resource_budget")
    if targets.get("power_report_required"):
        constraints.append("power_w measured" if not targets.get("power_limit_applies") else "power_w within_task_limit")
    return constraints


def bind_task_qor_targets(design_space: dict[str, Any], targets: dict[str, Any]) -> dict[str, Any]:
    """Make explicit task QoR gates immutable in the Stage-0 handoff."""

    result = copy.deepcopy(design_space)
    result["qor_targets"] = copy.deepcopy(targets)
    result["hard_constraints"] = task_qor_hard_constraints(targets)
    sources = result.setdefault("sources", {})
    if isinstance(sources, dict):
        sources["task_qor_targets"] = {
            "source": "task_spec",
            "values": copy.deepcopy(targets),
            "binding": "deterministic_user_constraint",
        }
    notes = result.setdefault("notes", [])
    if isinstance(notes, list):
        notes.append("Explicit task QoR targets are deterministically bound and cannot be weakened by DSE planning.")
    return result


def _positive_candidate_values(value: Any) -> list[int]:
    """Read integer candidates from the finite Stage-0 declaration forms."""

    if isinstance(value, dict):
        values: Any = None
        for key in ("candidate_values", "values_in_complete_universe", "entries_candidates", "candidates", "values"):
            if key in value:
                values = value[key]
                break
        if values is None and value.get("fixed") is not None:
            values = [value["fixed"]]
    else:
        values = value
    if not isinstance(values, list):
        values = [values] if values is not None else []
    result: list[int] = []
    for item in values:
        try:
            parsed = int(item)
        except (TypeError, ValueError):
            continue
        if parsed > 0 and parsed not in result:
            result.append(parsed)
    return result


def _declared_lane_candidates(search_params: dict[str, Any]) -> list[int]:
    """Collect only lanes explicitly declared by the Stage-0 schema."""

    result: list[int] = []

    def visit(value: Any, key: str = "") -> None:
        if key in {"lanes", "global_lanes"}:
            for lane in _positive_candidate_values(value):
                if lane not in result:
                    result.append(lane)
        if isinstance(value, dict):
            for child_key, child in value.items():
                visit(child, str(child_key))
        elif isinstance(value, list):
            for child in value:
                visit(child, key)

    visit(search_params)
    return result


def semantic_stream_contract(
    case_adapter: dict[str, Any] | None,
    numeric_policy: dict[str, Any],
    board: dict[str, Any],
) -> dict[str, Any]:
    """Resolve the stream widths that every physical lane candidate must pack."""

    adapter = case_adapter or {}
    dataflow = adapter.get("pipeline_dataflow")
    if not isinstance(dataflow, dict):
        semantic = adapter.get("model_semantic_adapter", {})
        path_value = semantic.get("path") if isinstance(semantic, dict) else None
        path = Path(str(path_value)) if path_value else None
        if path is not None and not path.is_file():
            path = Path.cwd() / path
        if path is not None and path.is_file():
            try:
                dataflow = read_json(path).get("pipeline_dataflow")
            except (OSError, ValueError, json.JSONDecodeError):
                dataflow = None
    if not isinstance(dataflow, dict):
        return {"status": "unavailable", "required_stream_bits": [], "axi_data_width_bits": None}

    rules = numeric_policy.get("default_rules", {}) if isinstance(numeric_policy.get("default_rules"), dict) else {}
    dtype_bits = {
        "FP32": 32,
        "FLOAT32": 32,
        "F32": 32,
        "FP16": 16,
        "FLOAT16": 16,
        "F16": 16,
        "BF16": 16,
        "BFP16": 16,
        "INT8": 8,
        "UINT8": 8,
        "I8": 8,
        "U8": 8,
    }

    def bits_for_role(role: Any) -> int | None:
        role_name = str(role or "")
        field = {"activation": "activation_dtype", "accumulator": "acc_dtype"}.get(role_name)
        if field is None:
            return None
        dtype = str(rules.get(field) or "").strip().upper().replace("_", "")
        return dtype_bits.get(dtype)

    roles: list[str] = []
    boundary = dataflow.get("boundary_numeric", {})
    if isinstance(boundary, dict):
        roles.extend(str(boundary.get(key)) for key in ("input", "output") if boundary.get(key))
    metadata = dataflow.get("stage_metadata", {})
    if isinstance(metadata, dict):
        for item in metadata.values():
            numeric = item.get("numeric", {}) if isinstance(item, dict) else {}
            if isinstance(numeric, dict):
                roles.extend(str(numeric.get(key)) for key in ("input", "output") if numeric.get(key))
    stream_bits = sorted({bits for role in roles if (bits := bits_for_role(role)) is not None})
    memory = board.get("memory_system", {}) if isinstance(board.get("memory_system"), dict) else {}
    axi_bits = maybe_int(memory.get("axi_data_width_bits"))
    if axi_bits is None:
        axi_bits = maybe_int(memory.get("ddr_word_width_bits"))
    return {
        "status": "ready" if stream_bits and axi_bits else "incomplete",
        "required_numeric_roles": sorted(set(roles)),
        "required_stream_bits": stream_bits,
        "axi_data_width_bits": axi_bits,
        "packing_rule": "lanes * stream_element_bits must be <= AXI width and divide it exactly",
    }


def design_space_stream_packing_errors(
    design_space: dict[str, Any], stream_contract: dict[str, Any]
) -> list[str]:
    """Reject an LLM lane domain that cannot represent a declared stream width."""

    if stream_contract.get("status") != "ready":
        return []
    search_params = design_space.get("search_params", {})
    if not isinstance(search_params, dict):
        return ["design_space.search_params must be an object"]
    lanes = _declared_lane_candidates(search_params)
    if not lanes:
        return ["design_space does not declare any physical lanes candidates"]
    axi_bits = maybe_int(stream_contract.get("axi_data_width_bits"))
    stream_bits = [maybe_int(value) for value in stream_contract.get("required_stream_bits", [])]
    stream_bits = [value for value in stream_bits if value and value > 0]
    errors = []
    for bits in stream_bits:
        valid = [lane for lane in lanes if lane * bits <= axi_bits and axi_bits % (lane * bits) == 0]
        if not valid:
            errors.append(
                f"no declared lane candidate can pack stream element width {bits} into "
                f"axi_data_width_bits={axi_bits}; at least one lane must satisfy lanes*bits <= AXI "
                "and divide AXI exactly"
            )
    return errors


def design_space_physical_candidate_errors(design_space: dict[str, Any]) -> list[str]:
    """Require Stage 0 to hand off a complete physical DSE domain.

    Stage 4 may select a concrete point, but it cannot validate a domain that
    contains only candidate counts or descriptive axes.  Keep this check
    deterministic and reuse the same normalizer that Stage 4 uses so the two
    stages cannot disagree about whether the domain exists.
    """

    search_params = design_space.get("search_params", {})
    if not isinstance(search_params, dict):
        return ["design_space.search_params must be an object"]
    try:
        candidates = physical_candidate_tuples(search_params)
    except ValueError as exc:
        return [f"design_space physical candidate domain is incomplete: {exc}"]
    if not candidates:
        return ["design_space physical candidate domain is empty"]
    return []


def mark_llm_semantic_failure(log_dir: Path, name: str, error: str) -> None:
    """Keep invalid LLM evidence for audit while forcing a fresh retry."""

    path = log_dir / f"{name}_result.json"
    if not path.exists():
        return
    try:
        record = read_json(path)
    except Exception:
        return
    record["semantic_validation_error"] = error
    record["error"] = error
    write_json(path, record)


def load_model_source(path: Path, target_seq: int) -> dict[str, Any]:
    source = read_json(path)
    if {"model_type", "block", "attention", "mlp"} <= set(source):
        model = source
        model["target_max_seq_len"] = int(model.get("target_max_seq_len") or target_seq)
        return model
    return normalize(source, target_seq, "auto")


def prepare_model_config(task_text: str, source_path: Path, fallback: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    source_text = read_text(source_path)
    if len(source_text) > 24000:
        source_text = source_text[:24000] + "\n... truncated ..."
    prompt = build_prompt(
        agent="model_config_agent",
        task="Act as the model and shape intake engineer. Extract the hardware-facing model_config JSON for accelerator design.",
        inputs={
            "human_task_spec": task_text,
            "model_source_path": str(source_path),
            "model_source_content": source_text,
            "deterministic_extractor_candidate": fallback,
        },
        output_schema=MODEL_CONFIG_SCHEMA,
        rules=[
            "You are responsible for preventing wrong-model, wrong-layer-count, wrong-head-count, and wrong-operator-order errors from entering the hardware flow.",
            "Keep only fields needed by hardware architecture, template selection, shape constraints, and pipeline sizing.",
            "Do not invent hidden model semantics.",
            "Use the deterministic extractor candidate when it is consistent with the model source.",
            "If the human task and model source disagree, preserve the model source facts and record the conflict in notes or equivalent schema-supported fields.",
            "Expose attention kind, q/kv head counts, head_dim, position encoding, norm type, MLP type, intermediate size, bias policy, and weight layout when available.",
        ],
    )
    return llm_json("model_config_agent", prompt, MODEL_CONFIG_SCHEMA, fallback, out_dir)


def prepare_task_card(task_text: str, model_config: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    fallback = {
        "schema_version": "spatialaccagent.task_card.v0",
        "target_model": model_config.get("model_type"),
        "target_layers": model_config.get("num_layers"),
        "target_seq_len": model_config.get("target_max_seq_len"),
        "design_goal": "generate a complete board-runnable spatial accelerator",
        "human_inputs": ["task_spec", "model_source", "model_dir", "board_materials_dir", "quantization_materials_dir", "tool_materials_dir"],
        "notes": ["deterministic candidate generated from structured model facts"],
    }
    prompt = build_prompt(
        agent="task_card_agent",
        task="Act as the design-run coordinator. Create the task_card JSON for a complete board-runnable spatial accelerator design run.",
        inputs={
            "human_task_spec": task_text,
            "hardware_model_facts": model_config,
        },
        output_schema=TASK_CARD_SCHEMA,
        rules=[
            "The task card is the handoff from the human request to the chip-design team.",
            "The top-level object is the task card itself.",
            "Do not wrap the task card in a task_card, result, or output field.",
            "The run target is a complete accelerator through board execution, not a partial simulation-only run.",
            "Required outputs should include generated accelerator code, tool evidence, bitstream evidence, and board-valid output evidence when applicable.",
            "Acceptance policy should reflect no-deadlock and valid-output requirements unless the task explicitly asks for bit-exact numeric matching.",
        ],
    )
    return llm_json("task_card_agent", prompt, TASK_CARD_SCHEMA, fallback, out_dir)


def infer_numeric_fallback(policy_text: str) -> dict[str, str]:
    return {"weight_dtype": "unknown", "activation_dtype": "unknown", "acc_dtype": "unknown", "scale_dtype": "unknown"}


def infer_board_fallback(board_text: str) -> dict[str, Any]:
    fpga_match = re.search(r"\bxc[a-z0-9]+(?:_[a-z0-9]+)?-[a-z0-9]+-[0-9]+-[a-z]\b", board_text, re.IGNORECASE)
    remote_match = re.search(r"\b[\w.-]+@(?:\d{1,3}\.){3}\d{1,3}\b", board_text)
    vivado_match = re.search(r"(/[^\s:]+/Vivado/[^\s:]+/bin/vivado)", board_text)
    vcs_match = re.search(r"(/[^\s:]+/vcs)", board_text)
    return {
        "board_id": "unspecified_board",
        "fpga_part": fpga_match.group(0).lower() if fpga_match else None,
        "remote_host": remote_match.group(0) if remote_match else None,
        "vivado_path": vivado_match.group(1) if vivado_match else None,
        "vcs_path": vcs_match.group(1) if vcs_match else None,
    }


def tool_materials_summary(tool_text: str) -> dict[str, Any]:
    lower = tool_text.lower()
    remote_match = re.search(r"[A-Za-z0-9_.-]+@(?:\d{1,3}\.){3}\d{1,3}", tool_text)
    return {
        "materials_present": bool(tool_text.strip()),
        "vcs": {
            "scope": "remote" if "vcs" in lower and remote_match else None,
            "remote_host": remote_match.group(0) if "vcs" in lower and remote_match else None,
            "role": "functional_verification" if "vcs" in lower else None,
        },
        "verilator": {
            "scope": "local" if "verilator" in lower and ("本地" in tool_text or "local" in lower) else None,
            "role": "functional_verification" if "verilator" in lower else None,
        },
        "vivado": {
            "scope": "remote" if "vivado" in lower and remote_match else None,
            "remote_host": remote_match.group(0) if "vivado" in lower and remote_match else None,
            "role": "synthesis_place_route_bitstream" if "vivado" in lower else None,
        },
    }


def find_tool_block(text: str, tool_name: str) -> str:
    pattern = re.compile(rf"^### [^\n]*{re.escape(tool_name)}[^\n]*\n.*?(?=^### |\Z)", re.IGNORECASE | re.DOTALL | re.MULTILINE)
    match = pattern.search(text)
    return match.group(0) if match else text


def tool_block_body(block: str) -> str:
    lines = []
    for line in block.splitlines():
        stripped = line.strip()
        if stripped.startswith("### "):
            continue
        if stripped.startswith("```"):
            continue
        lines.append(line)
    return "\n".join(lines)


def first_remote_host(text: str) -> str | None:
    match = re.search(r"[A-Za-z0-9_.-]+@(?:\d{1,3}\.){3}\d{1,3}", text)
    return match.group(0) if match else None


def remote_hosts(text: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r"[A-Za-z0-9_.-]+@(?:\d{1,3}\.){3}\d{1,3}", text)))


def clean_remote_path(path: str) -> str:
    return path.strip().rstrip("`'\".,;:，。；：)")


def extract_remote_sample_refs(materials_text: str) -> list[dict[str, Any]]:
    hosts = remote_hosts(materials_text)
    if not hosts:
        return []
    path_matches = re.findall(r"(/home/[A-Za-z0-9_./+=@-]+)", materials_text)
    refs: list[dict[str, Any]] = []
    for raw_path in path_matches:
        path = clean_remote_path(raw_path)
        if not path.startswith("/home/"):
            continue
        lower = path.lower()
        root = path
        if lower.endswith((".xpr", ".tcl", ".xdc", ".sv", ".v", ".vhd", ".xml", ".xci")):
            root = str(Path(path).parent)
        refs.append({"host": hosts[0], "port": 22, "root": root, "source_path": path})
    broad_roots = [ref for ref in refs if str(ref["root"]).rstrip("/") != "/home/share" and ref["root"] == ref["source_path"]]
    unique = []
    seen = set()
    for ref in sorted(refs, key=lambda item: len(str(item["root"]))):
        if str(ref["root"]).rstrip("/") == "/home/share":
            continue
        parent = next(
            (
                kept
                for kept in broad_roots
                if kept["host"] == ref["host"]
                and str(ref["source_path"]).startswith(str(kept["root"]).rstrip("/") + "/")
            ),
            None,
        )
        if parent and ref["root"] != parent["root"]:
            parent["source_path"] = ref["source_path"]
            continue
        key = (ref["host"], ref["port"], ref["root"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(ref)
    return unique


def first_path(text: str, basename: str) -> str | None:
    escaped = re.escape(basename)
    for match in re.finditer(rf"(/[^\s`'\"，。；;:]+/{escaped})(?:\b|$)", text):
        path = match.group(1)
        if "/framework/input_materials/tools/" not in path:
            return path
    return None


def clean_executable_path(value: Any) -> str | None:
    if not value:
        return None
    return str(value).strip().rstrip(".,;:，。；：")


def infer_tool_profile_fallback(tool_text: str, board: dict[str, Any]) -> dict[str, Any]:
    runtime = board.get("runtime_interface", {})
    shell = board.get("shell", {})
    known_remote = runtime.get("remote_host")
    tools: list[dict[str, Any]] = []
    specs = [
        ("verilator", "functional_verification", "verilator"),
        ("vcs", "functional_verification", "vcs"),
        ("vivado", "synthesis_place_route_bitstream", "vivado"),
    ]
    for name, role, executable_name in specs:
        block = find_tool_block(tool_text, name)
        body = tool_block_body(block)
        lower = body.lower()
        if name not in lower:
            continue
        local_words = ("本地" in body) or ("local" in lower)
        remote_words = ("远程" in body) or ("服务器" in body) or ("remote" in lower)
        remote_host = first_remote_host(body)
        if not remote_host and remote_words and not local_words:
            remote_host = known_remote
        scope = "local" if local_words else ("remote" if remote_host or remote_words else None)
        executable = first_path(body, executable_name)
        if not executable and name == "vivado":
            executable = shell.get("vivado_path")
        if not executable and name == "vcs":
            vcs_path = runtime.get("vcs_path")
            if vcs_path:
                executable = str(vcs_path)
        executable = clean_executable_path(executable)
        tools.append(
            {
                "name": name,
                "role": role,
                "scope": scope,
                "host": remote_host if scope == "remote" else None,
                "port": None,
                "executable": executable,
                "env": {},
                "workdir": None,
                "constraints": [],
                "source": "tool input materials deterministic parser",
            }
        )
    return {
        "schema_version": "spatialaccagent.tool_profile.v0",
        "tools": tools,
        "notes": [
            "Fallback parser only records facts visible in user-provided tool and board materials.",
            "Missing host/path fields must remain null until the user documents them or the tool profile agent extracts them.",
        ],
    }


def prepare_tool_profile(tool_summary: dict[str, Any], board: dict[str, Any], field_evidence_summary: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    fallback = infer_tool_profile_fallback(json.dumps(tool_summary, ensure_ascii=False), board)
    tool_field_evidence = filter_field_evidence_summary(field_evidence_summary, ("tool.",))
    prompt = build_prompt(
        agent="tool_profile_agent",
        task="Act as the EDA toolchain engineer. Extract the external EDA tool profile from current-run tool materials.",
        inputs={
            "tool_materials_summary": tool_summary,
            "target_board_profile": board,
            "field_evidence_summary": tool_field_evidence,
        },
        output_schema=TOOL_PROFILE_SCHEMA,
        rules=[
            "Treat the tool materials directory as the complete current-run tool input.",
            "Field evidence summary is the source-of-truth audit trail. Critical host, executable, environment, and script fields must match evidence when evidence exists.",
            "The formal framework needs VCS or Verilator for functional verification and Vivado for synthesis, implementation, and bitstream generation.",
            "Do not assume a fixed host, path, license server, version, or command unless it appears in the provided documents or target_board_profile.",
            "Use common tool names such as vcs, verilator, and vivado when present.",
            "Use scope=local for tools on the current machine, scope=remote for tools accessed through ssh, and null when unknown.",
            "Put missing host/path/port/env/workdir fields as null or empty objects rather than inventing defaults.",
            "Record limitations, license requirements, sandbox restrictions, or version constraints in constraints.",
            "For remote tools, record host and any required environment variables. For Vivado, executable must identify the Vivado binary when provided.",
        ],
    )
    profile = llm_json("tool_profile_agent", prompt, TOOL_PROFILE_SCHEMA, fallback, out_dir)
    return merge_tool_profile_bindings(profile, board, field_evidence_summary)


def merge_tool_profile_bindings(
    profile: dict[str, Any],
    board: dict[str, Any],
    field_evidence_summary: dict[str, Any],
) -> dict[str, Any]:
    """Complete blank tool endpoint fields from current-run, source-bound inputs.

    The tool-profile LLM owns semantic extraction, but an otherwise valid response
    may omit an operational field that is already present in the current-run
    evidence.  Fill only blank fields; never overwrite an explicit LLM value or
    invent a tool path/host.  The board runtime endpoint is the shared remote EDA
    endpoint when the tool-specific host was omitted.
    """

    result = copy.deepcopy(profile)
    tools = result.get("tools")
    if not isinstance(tools, list):
        return result

    runtime = board.get("runtime_interface", {})
    if not isinstance(runtime, dict):
        runtime = {}
    shared_remote_host = summary_field_value(field_evidence_summary, "runtime_interface.remote_host")
    if blank_profile_value(shared_remote_host):
        shared_remote_host = runtime.get("remote_host")
    shared_remote_port = runtime.get("remote_port")

    bound_fields: list[str] = []
    for tool in tools:
        if not isinstance(tool, dict):
            continue
        name = str(tool.get("name") or "").lower()
        if name not in {"vcs", "vivado"}:
            continue

        host_field = f"tool.{name}.host"
        executable_field = f"tool.{name}.executable"
        host = summary_field_value(field_evidence_summary, host_field)
        executable = summary_field_value(field_evidence_summary, executable_field)
        if blank_profile_value(host):
            host = shared_remote_host
        if blank_profile_value(executable):
            executable = None

        before = (tool.get("host"), tool.get("executable"), tool.get("scope"), tool.get("port"))
        fill_if_blank(tool, "host", host)
        fill_if_blank(tool, "executable", executable)
        if blank_profile_value(tool.get("scope")) and evidence_value_present(tool.get("host")):
            tool["scope"] = "remote"
        if blank_profile_value(tool.get("port")) and evidence_value_present(tool.get("host")):
            fill_if_blank(tool, "port", shared_remote_port or 22)
        after = (tool.get("host"), tool.get("executable"), tool.get("scope"), tool.get("port"))
        if before != after:
            bound_fields.append(name)

    if bound_fields:
        notes = result.setdefault("notes", [])
        if isinstance(notes, list):
            notes.append(
                "Blank VCS/Vivado endpoint fields were completed from current-run source-bound board/tool evidence; explicit LLM values were preserved."
            )
    return result


def prepare_numeric_policy(materials_text: str, out_dir: Path) -> dict[str, Any]:
    policy_text = "\n".join(line.strip() for line in materials_text.splitlines() if line.strip())
    inferred = infer_numeric_fallback(policy_text)
    fallback = {
        "schema_version": "spatialaccagent.numeric_policy.v0",
        "policy_id": "llm_semantic_extraction_required" if policy_text else "numeric_policy_missing",
        "default_rules": {
            "weight_dtype": inferred["weight_dtype"],
            "activation_dtype": inferred["activation_dtype"],
            "acc_dtype": inferred["acc_dtype"],
            "scale_dtype": inferred["scale_dtype"],
            "rounding": "unknown",
            "saturation": False,
        },
        "tolerance": {
            "stage": "functional_or_shape",
            "system": "valid_output_required",
        },
        "notes": ["neutral candidate; numeric_policy_agent must extract semantic precision facts from current-run materials"],
    }
    if not policy_text:
        fallback["notes"].append("No quantization policy materials found; downstream gates must treat numeric precision as unresolved.")
    prompt = build_prompt(
        agent="numeric_policy_agent",
        task="Act as the numeric precision engineer. Convert the current-run quantization materials into numeric_policy JSON.",
        inputs={"quantization_materials": policy_text},
        output_schema=NUMERIC_POLICY_SCHEMA,
        rules=[
            "Treat the quantization materials directory as the complete current-run numeric input.",
            "If no explicit quantization policy is provided, mark dtype and rounding fields unknown and record a blocking note; do not invent a default precision.",
            "Use exactly the field names in the schema.",
            "Do not rename default_rules to rules or default_numeric_rules.",
            "Copy atol, rtol, and max_mismatch_fraction into tolerance.comparison only when the materials provide them. Do not guess missing quantitative values; the framework deterministically applies its loose defaults after extraction.",
            "Do not loosen a provided tolerance or change numeric policy beyond the provided materials.",
            "Record unclear, conflicting, or missing quantization decisions in notes so later verification does not silently assume them.",
        ],
    )
    return resolve_numeric_policy(
        llm_json("numeric_policy_agent", prompt, NUMERIC_POLICY_SCHEMA, fallback, out_dir)
    )


def summary_field_value(field_evidence_summary: dict[str, Any], field: str) -> Any:
    for item in field_evidence_summary.get("selected_fields", []):
        if item.get("field") != field:
            continue
        evidence = item.get("evidence", [])
        if isinstance(evidence, list) and evidence:
            return evidence[0].get("value")
    return None


def filter_field_evidence_summary(field_evidence_summary: dict[str, Any], prefixes: tuple[str, ...]) -> dict[str, Any]:
    return {
        "schema_version": field_evidence_summary.get("schema_version", "spatialaccagent.field_evidence_summary.v0"),
        "policy": field_evidence_summary.get("policy", {}),
        "selected_fields": [
            item
            for item in field_evidence_summary.get("selected_fields", [])
            if isinstance(item, dict) and any(str(item.get("field") or "").startswith(prefix) for prefix in prefixes)
        ],
    }


def blank_profile_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"", "none", "null"}
    if isinstance(value, (list, dict, tuple, set)):
        return not bool(value)
    return value == 0


def evidence_value_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return bool(value)
    return True


def fill_if_blank(target: dict[str, Any], key: str, value: Any) -> None:
    if evidence_value_present(value) and blank_profile_value(target.get(key)):
        target[key] = value


def merge_board_profile_field_evidence(profile: dict[str, Any], field_evidence_summary: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(profile)
    memory = result.setdefault("memory_system", {})
    runtime = result.setdefault("runtime_interface", {})
    shell = result.setdefault("shell", {})
    address_map = memory.setdefault("address_map", {}) if isinstance(memory, dict) else {}

    memory_fields = {
        "memory_system.ddr_channels": "ddr_channels",
        "memory_system.ddr_word_width_bits": "ddr_word_width_bits",
        "memory_system.axi_data_width_bits": "axi_data_width_bits",
        "memory_system.axi_data_bytes": "axi_data_bytes",
        "memory_system.axi_addr_width_bits": "axi_addr_width_bits",
        "memory_system.axi_id_width_bits": "axi_id_width_bits",
        "memory_system.axi_wstrb_width_bits": "axi_wstrb_width_bits",
        "memory_system.core_side_interface_name": "core_side_interface_name",
        "memory_system.axi_clock": "axi_clock",
        "memory_system.axi_reset": "axi_reset",
        "memory_system.calibration_done_signal": "calibration_done_signal",
        "memory_system.real_board_reference_rtl": "real_board_reference_rtl",
    }
    for field, key in memory_fields.items():
        fill_if_blank(memory, key, summary_field_value(field_evidence_summary, field))

    runtime_fields = {
        "runtime_interface.control_protocol": "control_protocol",
        "runtime_interface.board_run_command": "board_run_command",
        "runtime_interface.remote_host": "remote_host",
        "runtime_interface.mimic_dir": "mimic_dir",
        "runtime_interface.xdma_id_default": "xdma_id_default",
        "runtime_interface.ctrl_base": "ctrl_base",
        "runtime_interface.ddr_base": "ddr_base",
        "runtime_interface.output_abs": "output_abs",
        "runtime_interface.ddr_image_default": "ddr_image_default",
    }
    for field, key in runtime_fields.items():
        fill_if_blank(runtime, key, summary_field_value(field_evidence_summary, field))

    fill_if_blank(shell, "core_ddr_axi_interface", memory.get("core_side_interface_name"))
    fill_if_blank(shell, "init_calibration_done_signal", memory.get("calibration_done_signal"))
    fill_if_blank(shell, "real_board_axi_reference_rtl", memory.get("real_board_reference_rtl"))
    fill_if_blank(address_map, "control_registers", runtime.get("ctrl_base"))
    fill_if_blank(address_map, "ddr_base", runtime.get("ddr_base"))
    fill_if_blank(address_map, "output_abs", runtime.get("output_abs"))
    return result


def prepare_board_profile(board_summary: dict[str, Any], field_evidence_summary: dict[str, Any], sample_project_summary_data: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    board_inputs = board_summary
    inferred = infer_board_fallback(json.dumps(board_summary, ensure_ascii=False))
    board_field_evidence = filter_field_evidence_summary(field_evidence_summary, ("board.", "memory_system.", "runtime_interface."))
    fallback = {
        "schema_version": "spatialaccagent.target_board_profile.v0",
        "board": {
            "board_id": inferred["board_id"],
            "fpga_part": inferred["fpga_part"],
            "resource_budget": {"lut": None, "ff": None, "bram": None, "uram": None, "dsp": None},
            "clock_options_mhz": [],
        },
        "shell": {"vivado_version": None, "shell_type": None, "ip_repos": [], "vivado_path": inferred["vivado_path"]},
        "memory_system": {
            "ddr_channels": None,
            "ddr_word_width_bits": None,
            "axi_data_width_bits": None,
            "axi_data_bytes": None,
            "axi_addr_width_bits": None,
            "axi_id_width_bits": None,
            "axi_wstrb_width_bits": None,
            "core_side_interface_name": None,
            "axi_clock": None,
            "axi_reset": None,
            "calibration_done_signal": None,
            "real_board_reference_rtl": None,
        },
        "runtime_interface": {
            "control_protocol": None,
            "board_run_command": None,
            "remote_host": inferred["remote_host"],
            "vcs_path": inferred["vcs_path"],
            "mimic_dir": None,
            "xdma_id_default": None,
            "ctrl_base": None,
            "ddr_base": None,
            "output_abs": None,
            "ddr_image_default": None,
        },
        "board_pass_criteria": {
            "bitstream_generated": True,
            "board_runtime_completes": True,
            "valid_output_bytes_required": True,
        },
        "notes": ["fallback board profile; board agent should refine from board docs/sample shell"],
    }
    if not board_summary.get("file_count"):
        fallback["notes"].append("No board materials provided; fallback board profile retained and marked for later manual refinement.")

    prompt = build_prompt(
        agent="board_profile_agent",
        task="Act as the FPGA board/platform engineer. Extract the target_board_profile JSON from current-run board/platform materials.",
        inputs={
            "board_materials_summary": board_summary,
            "sample_project_summary": sample_project_summary_data,
            "field_evidence_summary": board_field_evidence,
        },
        output_schema=BOARD_PROFILE_SCHEMA,
        rules=[
            "Treat the board materials directory as the complete current-run board input.",
            "Field evidence summary is the source-of-truth audit trail. Critical FPGA part, DDR/AXI, runtime command, and control protocol fields must match evidence when evidence exists.",
            "The downstream accelerator must keep DDR/AXI-compatible board flow, so DDR channels, AXI width, control protocol, runtime command, remote host, and FPGA part are critical.",
            "Put all FPGA board, shell, memory, runtime, and pass/fail fields inside the schema sections.",
            "Use null for unknown board facts and record uncertainty in notes.",
            "Do not invent resource numbers that are not present in the source information.",
            "If sample projects or scripts imply board flow, use only the summarized evidence and do not repeat long file listings.",
            "Extract runtime ABI fields such as control base, DDR base, output address, device id, runtime directory, image path, board AXI prefix, clock/reset, and calibration signal only when they appear in source evidence.",
        ],
    )
    return merge_board_profile_field_evidence(llm_json("board_profile_agent", prompt, BOARD_PROFILE_SCHEMA, fallback, out_dir), field_evidence_summary)


def prepare_template_library(template_dir: Path, input_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    template_dir = template_dir.resolve()
    metadata_src = template_dir / "template_metadata.json"
    if not template_dir.exists():
        raise InputPreparationError(f"template directory not found: {template_dir}")
    if not metadata_src.exists():
        raise InputPreparationError(f"template metadata not found: {metadata_src}")

    metadata = read_json(metadata_src)
    write_json(input_dir / "template_metadata.json", metadata)
    source_files = sorted(str(path.relative_to(template_dir)) for path in template_dir.glob("*.scala"))
    library = {
        "schema_version": "spatialaccagent.template_library.v0",
        "template_dir": str(template_dir),
        "metadata": "template_metadata.json",
        "source_files": source_files,
        "policy": {
            "free_form_rtl_generation": False,
            "template_internal_rewrite_requires_approval": True,
            "parameter_binding_allowed": True,
            "top_connection_allowed": True,
        },
    }
    write_json(input_dir / "template_library.json", library)
    return library, metadata


def prepare_design_space(
    model: dict[str, Any],
    templates: dict[str, Any],
    board: dict[str, Any],
    numeric_policy: dict[str, Any],
    qor_targets: dict[str, Any],
    out_dir: Path,
    case_adapter: dict[str, Any] | None = None,
) -> dict[str, Any]:
    physical_domain_seed = framework_physical_candidate_domain_seed()
    fallback = {
        "schema_version": "spatialaccagent.design_space.v0",
        "status": "generated_by_stage0_agent",
        "sources": {
            "model_type": model.get("model_type"),
            "template_library_id": templates.get("library_id"),
            "board_id": board.get("board", {}).get("board_id"),
        },
        "search_params": copy.deepcopy(physical_domain_seed),
        "objectives": [
            "minimize_resources",
            "minimize_power_w",
            "maximize_clock_frequency_mhz",
            "maximize_performance_tokens_per_second",
        ],
        "qor_targets": qor_targets,
        "hard_constraints": task_qor_hard_constraints(qor_targets),
        "notes": [
            "fallback formal DSE universe contains only parameters that change generated FPGA RTL/XPM topology",
            "framework physical-domain seed is a read-only topology boundary, not a selected architecture or QoR claim",
        ],
    }
    prompt = build_prompt(
        agent="design_space_agent",
        task="Act as the design-space exploration engineer. Create the initial hardware design_space JSON for this model/template/board triplet.",
        inputs={
            "model_config": model,
            "template_metadata_summary": {"library_id": templates.get("library_id"), "templates": templates.get("templates", [])},
            "target_board_profile": board,
            "numeric_policy": numeric_policy,
            "semantic_stream_contract": semantic_stream_contract(case_adapter, numeric_policy, board),
            "explicit_task_qor_targets": qor_targets,
            "framework_physical_domain_seed": physical_domain_seed,
        },
        output_schema=DESIGN_SPACE_SCHEMA,
        rules=[
            "The design space must be compatible with the extracted model facts, template library, numeric policy, and target board profile.",
            "Search parameters must be hardware parameters, not model semantics.",
            "Declare a finite, complete candidate universe containing only parameters that genuinely change generated RTL, Vivado FP IP, XPM BRAM/URAM topology, or board behavior. Exclude metadata-only tile, burst, pipeline-depth, and clock-target fields until they are wired into generated hardware.",
            "Include lanes, compute_array.rows, compute_array.cols, physical FIFO depth, activation-bank count, and optional physical_weight_layout_candidates. The two compute_array values are the physical MAC PE array dimensions; every PE must instantiate one fixed Vivado multiplier/DSP IP, so they must be real generated-hardware parameters rather than metadata. Keep compute_array.cols power-of-two for the trusted reduction tree and require both dimensions to tile the selected vector lanes. When supplied, each layout must bind every model-semantic weight-storage term declared by the current semantic adapter to a positive XPM URAM bank count. Do not use another model family's role names. If no explicit layouts are supplied, Stage 4 derives the complete all-URAM baseline from the same semantic contract.",
            "For every numeric stream element width declared by the semantic_stream_contract, declare at least one lane candidate whose lane payload is no wider than the board AXI beat and divides that AXI width exactly. The contract may contain both activation and accumulator/residual streams; checking only the activation dtype is invalid. Candidates that cannot pack a declared stream width are ineligible and must not be described as legal, and the framework will reject a domain with no valid lane for any required width.",
            "The supplied explicit_task_qor_targets are immutable user constraints. Repeat them accurately, but do not add, delete, weaken, or replace them.",
            "The design must bind Vivado floating-point/DSP IP and XPM physical memories from the first implementation candidate; do not select a software arithmetic or ideal-memory backend.",
            "Do not choose parameters that require changing model semantics or bypassing DDR/AXI/runtime constraints.",
            "framework_physical_domain_seed is read-only framework topology evidence. It is not a selected architecture, QoR estimate, or automatic fallback promotion. Return a complete current design-space universe; when current model/board/template evidence has no more specific PE geometry, state explicit legal tuples or correlated pairs from this seed rather than only a candidate count.",
            "Do not provide resource, power, frequency, or performance estimates. Stage 4 will use only real target-board app-shell Vivado and hardware-counter measurements for those four metrics.",
        ],
    )
    result = llm_json("design_space_agent", prompt, DESIGN_SPACE_SCHEMA, fallback, out_dir)
    stream_contract = semantic_stream_contract(case_adapter, numeric_policy, board)
    packing_errors = design_space_stream_packing_errors(result, stream_contract)
    if packing_errors:
        raise InputPreparationError("design_space stream packing validation failed: " + "; ".join(packing_errors))
    candidate_errors = design_space_physical_candidate_errors(result)
    if candidate_errors:
        repair_prompt = build_prompt(
            agent="design_space_candidate_domain_repair_agent",
            task=(
                "Repair the current Stage-0 design-space JSON because its physical DSE domain is not "
                "complete. Return the same design-space schema with a finite, explicit, legal candidate "
                "domain that downstream Stage 4 can normalize without inventing any candidate."
            ),
            inputs={
                "current_design_space": result,
                "validation_errors": candidate_errors,
                "model_config": model,
                "template_metadata_summary": {
                    "library_id": templates.get("library_id"),
                    "templates": templates.get("templates", []),
                },
                "target_board_profile": board,
                "numeric_policy": numeric_policy,
                "semantic_stream_contract": semantic_stream_contract(case_adapter, numeric_policy, board),
                "explicit_task_qor_targets": qor_targets,
                "framework_physical_domain_seed": physical_domain_seed,
            },
            output_schema=DESIGN_SPACE_SCHEMA,
            rules=[
                "Preserve model semantics, numeric policy, board facts, and explicit task QoR constraints.",
                "Do not select one architecture point; Stage 4 owns concrete selection.",
                "Declare the complete physical candidate universe, including lanes, compute_array rows and cols, physical FIFO depth, and activation-bank count.",
                "Use one of the accepted complete forms: hardware_parameter_tuples, candidate_universe legal tuples/pairs/shapes plus all physical axes, candidate_dimensions, or legacy axes with valid candidate pairs.",
                "Candidate counts, composition descriptions, and unpaired descriptive axes are not a candidate universe and must not be returned alone.",
                "Do not invent a candidate from a constructor default or from another model family; every value must be supported by the current model, board, and template evidence.",
                "framework_physical_domain_seed is read-only framework topology evidence, not a concrete architecture selection or QoR result. When the failed result lacks literal PE tuples/pairs, return a complete correlated physical domain from this seed instead of deriving geometry from a candidate count. Stage 4 remains the only concrete selection authority.",
                "Return exactly one valid JSON object matching the design-space schema.",
            ],
        )
        result = llm_json(
            "design_space_candidate_domain_repair_agent",
            repair_prompt,
            DESIGN_SPACE_SCHEMA,
            result,
            out_dir,
        )
        candidate_errors = design_space_physical_candidate_errors(result)
        if candidate_errors:
            detail = "; ".join(candidate_errors)
            mark_llm_semantic_failure(out_dir, "design_space_candidate_domain_repair_agent", detail)
            raise InputPreparationError(detail)
    result = bind_task_qor_targets(result, qor_targets)
    sources = result.setdefault("sources", {})
    if isinstance(sources, dict) and stream_contract.get("status") == "ready":
        sources["stream_packing_contract"] = {
            "required_numeric_roles": stream_contract.get("required_numeric_roles", []),
            "required_stream_bits": stream_contract.get("required_stream_bits", []),
            "axi_data_width_bits": stream_contract.get("axi_data_width_bits"),
            "binding": "deterministic_semantic_stream_contract",
        }
    return result


def tool_by_name(tool_profile: dict[str, Any], name: str) -> dict[str, Any] | None:
    for item in tool_profile.get("tools", []):
        if str(item.get("name", "")).lower() == name.lower():
            return item
    return None


def env_prefix(env: dict[str, Any]) -> str:
    parts = []
    for key, value in sorted(env.items()):
        if value is None or value == "":
            continue
        parts.append(f"{key}={shlex.quote(str(value))}")
    return " ".join(parts)


def profile_env(tool_profile: dict[str, Any], tool_name: str) -> dict[str, str]:
    tool = tool_by_name(tool_profile, tool_name) or {}
    env = {str(k): str(v) for k, v in dict(tool.get("env") or {}).items() if v is not None and v != ""}
    host = tool.get("host")
    port = tool.get("port")
    executable = tool.get("executable")
    workdir = tool.get("workdir")
    if host:
        env["REMOTE_HOST"] = str(host)
    if port:
        env["REMOTE_PORT"] = str(port)
    if workdir:
        env["REMOTE_WORKDIR"] = str(workdir)
    if tool_name == "vivado" and executable:
        env["VIVADO_BIN"] = str(clean_executable_path(executable))
    if tool_name == "vcs" and executable:
        path = Path(str(clean_executable_path(executable)))
        env["REMOTE_VCS_HOME"] = str(path.parent.parent if path.name == "vcs" else path)
    if tool_name == "verilator" and executable:
        env["VERILATOR_BIN"] = str(clean_executable_path(executable))
    return env


def command_with_env(command: str, env: dict[str, str]) -> str:
    prefix = env_prefix(env)
    return f"{prefix} {command}" if prefix else command


def structured_command(
    *,
    name: str,
    kind: str,
    scope: str,
    argv: list[str],
    cwd: Path | str,
    env: dict[str, str] | None = None,
    required: bool = False,
    required_group: str | None = None,
    timeout_sec: int | None = None,
    consumes: list[str] | None = None,
    produces: list[str] | None = None,
    script_expected_after_codegen: bool = False,
) -> dict[str, Any]:
    env = env or {}
    command = command_with_env(" ".join(shlex.quote(str(part)) for part in argv), env) if argv else ""
    item: dict[str, Any] = {
        "name": name,
        "kind": kind,
        "scope": scope,
        "execution": {
            "argv": [str(part) for part in argv],
            "cwd": str(cwd),
            "env": env,
            "timeout_sec": timeout_sec,
        },
        "command": command,
        "required": required,
        "script_expected_after_codegen": script_expected_after_codegen,
        "consumes": consumes or [],
        "produces": produces or [],
    }
    if required_group:
        item["required_group"] = required_group
    return item


def tool_configured(tool_profile: dict[str, Any], tool_name: str, *, require_host: bool = False, require_executable: bool = False) -> bool:
    tool = tool_by_name(tool_profile, tool_name)
    if not tool:
        return False
    if require_host and not tool.get("host"):
        return False
    if require_executable and not tool.get("executable"):
        return False
    return bool(tool.get("scope"))


def run_probe_command(argv: list[str], timeout_sec: int, max_output_chars: int = 4000) -> dict[str, Any]:
    started = time.monotonic()
    max_output_chars = max(1000, max_output_chars)
    try:
        proc = subprocess.run(
            argv,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_sec,
            check=False,
        )
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip()[-max_output_chars:],
            "stderr": proc.stderr.strip()[-max_output_chars:],
            "duration_sec": round(time.monotonic() - started, 3),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "returncode": None,
            "stdout": (exc.stdout or "").strip()[-max_output_chars:] if isinstance(exc.stdout, str) else "",
            "stderr": (exc.stderr or "").strip()[-max_output_chars:] if isinstance(exc.stderr, str) else "",
            "duration_sec": round(time.monotonic() - started, 3),
            "error": f"timeout after {timeout_sec}s",
        }
    except Exception as exc:
        return {
            "ok": False,
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "duration_sec": round(time.monotonic() - started, 3),
            "error": str(exc),
        }


def ssh_command_argv(host: str, port: int, remote_command: str) -> list[str]:
    known_hosts = os.environ.get("SPATIALACC_TOOL_PROBE_KNOWN_HOSTS", "/tmp/spatialacc_stage0_ssh_known_hosts")
    return [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=10",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        f"UserKnownHostsFile={known_hosts}",
        "-p",
        str(port),
        str(host),
        remote_command,
    ]


def run_ssh_command(host: str, port: int, remote_command: str, timeout_sec: int, max_output_chars: int = 4000) -> dict[str, Any]:
    return run_probe_command(ssh_command_argv(host, port, remote_command), timeout_sec, max_output_chars=max_output_chars)


def sample_project_grep_command(root: str, max_matches: int) -> str:
    root_q = shlex.quote(root)
    pattern = (
        "Option Name=\"Part\"|C_DATA_WIDTH|DATA_WIDTH|AXI|DDR|"
        "AWADDR|ARADDR|WSTRB|clock|reset|addr|data|strobe|VLNV"
    )
    includes = " ".join(
        shlex.quote(arg)
        for arg in [
            "--include=*.xpr",
            "--include=*.tcl",
            "--include=*.xdc",
            "--include=*.sv",
            "--include=*.v",
            "--include=*.vhd",
            "--include=*.xml",
            "--include=*.xci",
        ]
    )
    return (
        f"if test -e {root_q}; then "
        f"grep -RInE {shlex.quote(pattern)} {includes} {root_q} 2>/dev/null | head -n {max_matches}; "
        "else exit 4; fi"
    )


def sample_project_part_command(root: str, source_path: str | None, max_matches: int) -> str:
    root_q = shlex.quote(root)
    source = clean_remote_path(str(source_path or ""))
    source_q = shlex.quote(source) if source else ""
    pattern_q = shlex.quote('Option Name="Part"|xc[a-zA-Z0-9_+-]+-[a-zA-Z0-9]+-[0-9]+-[a-zA-Z]')
    if source and source.lower().endswith(".xpr"):
        return (
            f"if test -f {source_q}; then grep -HnE {pattern_q} {source_q} 2>/dev/null | head -n {max_matches}; "
            f"else find {root_q} -maxdepth 4 -type f -name '*.xpr' -exec grep -HnE {pattern_q} {{}} + 2>/dev/null | head -n {max_matches}; fi"
        )
    return f"find {root_q} -maxdepth 4 -type f -name '*.xpr' -exec grep -HnE {pattern_q} {{}} + 2>/dev/null | head -n {max_matches}"


def sample_project_find_command(root: str, max_files: int) -> str:
    root_q = shlex.quote(root)
    return (
        f"if test -d {root_q}; then "
        f"find {root_q} -maxdepth 6 -type f 2>/dev/null | head -n {max_files}; "
        f"elif test -f {root_q}; then printf '%s\\n' {root_q}; "
        "else exit 4; fi"
    )


def sample_project_report_text(index: dict[str, Any]) -> str:
    parts = []
    for i, sample in enumerate(index.get("samples", []), 1):
        parts.append(f"### chunk:sample_project:{i:04d} source:{sample.get('host')}:{sample.get('root')}")
        parts.append("```text")
        parts.append(f"status: {sample.get('status')}")
        if sample.get("error"):
            parts.append(f"error: {sample.get('error')}")
        parts.append("part_evidence:")
        parts.append(str(sample.get("part_evidence", ""))[:4000])
        parts.append("file_list_excerpt:")
        parts.extend(str(path) for path in sample.get("file_list_excerpt", [])[:20])
        parts.append("grep_evidence:")
        parts.append(str(sample.get("grep_evidence", ""))[:6000])
        parts.append("```")
    return "\n".join(parts)


def sample_project_summary(index: dict[str, Any]) -> dict[str, Any]:
    summary = {
        "schema_version": "spatialaccagent.sample_project_summary.v0",
        "refs": index.get("refs", []),
        "policy": index.get("policy", {}),
        "samples": [],
    }
    for sample in index.get("samples", []):
        summary["samples"].append(
            {
                "host": sample.get("host"),
                "port": sample.get("port"),
                "root": sample.get("root"),
                "source_path": sample.get("source_path"),
                "status": sample.get("status"),
                "error": sample.get("error"),
                "file_count": len(sample.get("file_list_excerpt", [])),
                "file_list_excerpt": [str(path) for path in sample.get("file_list_excerpt", [])[:5]],
                "part_evidence_excerpt": str(sample.get("part_evidence", ""))[:600],
                "grep_evidence_excerpt": str(sample.get("grep_evidence", ""))[:900],
            }
        )
    return summary


def material_index_summary(index: dict[str, Any], label: str) -> dict[str, Any]:
    return {
        "schema_version": "spatialaccagent.material_index_summary.v0",
        "label": label,
        "root": index.get("root"),
        "file_count": len(index.get("files", [])),
        "chunk_count": len(index.get("chunks", [])),
        "skipped_count": len(index.get("skipped", [])),
        "files": [
            {
                "path": item.get("path"),
                "suffix": item.get("suffix"),
                "chars": item.get("chars"),
            }
            for item in index.get("files", [])[:6]
        ],
        "skipped": [item.get("path") for item in index.get("skipped", [])[:3]],
    }


def prepare_sample_project_index(board_materials_text: str, input_dir: Path) -> tuple[str, dict[str, Any]]:
    refs = extract_remote_sample_refs(board_materials_text)
    timeout_sec = env_int("SPATIALACC_SAMPLE_PROJECT_TIMEOUT_SEC", 60, 10)
    max_files = env_int("SPATIALACC_SAMPLE_PROJECT_MAX_FILES", 3000, 100)
    max_matches = env_int("SPATIALACC_SAMPLE_PROJECT_MAX_GREP_MATCHES", 500, 50)
    index: dict[str, Any] = {
        "schema_version": "spatialaccagent.sample_project_index.v0",
        "refs": refs,
        "policy": {
            "read_only_remote_inputs": True,
            "max_files": max_files,
            "max_grep_matches": max_matches,
            "timeout_sec": timeout_sec,
        },
        "samples": [],
    }
    for ref in refs:
        host = str(ref["host"])
        port = int(ref.get("port") or 22)
        root = str(ref["root"])
        find_probe = run_ssh_command(host, port, sample_project_find_command(root, max_files), timeout_sec, max_output_chars=200000)
        part_probe = run_ssh_command(host, port, sample_project_part_command(root, ref.get("source_path"), max_matches), timeout_sec, max_output_chars=60000)
        grep_probe = run_ssh_command(host, port, sample_project_grep_command(root, max_matches), timeout_sec, max_output_chars=300000)
        sample = {
            "host": host,
            "port": port,
            "root": root,
            "source_path": ref.get("source_path"),
            "status": "ok" if find_probe.get("ok") and part_probe.get("ok") and grep_probe.get("ok") else "error",
            "file_list_probe": find_probe,
            "part_probe": part_probe,
            "grep_probe": grep_probe,
            "file_list_excerpt": [line for line in str(find_probe.get("stdout") or "").splitlines() if line.strip()],
            "part_evidence": part_probe.get("stdout") or "",
            "grep_evidence": grep_probe.get("stdout") or "",
        }
        if sample["status"] != "ok":
            sample["error"] = "; ".join(
                str(value)
                for value in [
                    find_probe.get("error") or find_probe.get("stderr"),
                    part_probe.get("error") or part_probe.get("stderr"),
                    grep_probe.get("error") or grep_probe.get("stderr"),
                ]
                if value
            )
        index["samples"].append(sample)
    write_json(input_dir / "sample_project_index.json", index)
    write_json(input_dir / "sample_project_summary.json", sample_project_summary(index))
    return sample_project_report_text(index), index


def chunk_context(text: str, pos: int) -> tuple[str | None, str | None]:
    prefix = text[:pos]
    header_pos = prefix.rfind("### chunk:")
    if header_pos < 0:
        return None, None
    header_end = text.find("\n", header_pos)
    if header_end < 0:
        header_end = len(text)
    header = text[header_pos:header_end]
    match = re.search(r"chunk:([^\s]+)\s+source:(.*?)(?:\s+offset:|$)", header)
    if not match:
        return None, header
    return match.group(1), match.group(2).strip()


def evidence_excerpt(text: str, start: int, end: int, limit: int = 260) -> str:
    left = max(0, start - limit // 2)
    right = min(len(text), end + limit // 2)
    return re.sub(r"\s+", " ", text[left:right]).strip()


def add_regex_evidence(
    evidence: list[dict[str, Any]],
    text: str,
    field: str,
    pattern: str,
    *,
    flags: int = re.IGNORECASE,
    value_group: int | str = 1,
    transform: Any | None = None,
) -> None:
    seen = {(item.get("field"), str(item.get("value")), item.get("source"), item.get("excerpt")) for item in evidence}
    for match in re.finditer(pattern, text, flags):
        value: Any = match.group(value_group)
        value = value.strip() if isinstance(value, str) else value
        if transform:
            value = transform(value)
        chunk_id, source = chunk_context(text, match.start())
        item = {
            "field": field,
            "value": value,
            "source": source,
            "chunk_id": chunk_id,
            "excerpt": evidence_excerpt(text, match.start(), match.end()),
        }
        key = (item["field"], str(item["value"]), item["source"], item["excerpt"])
        if key not in seen:
            evidence.append(item)
            seen.add(key)


def extract_field_evidence_candidates(
    board_materials_text: str,
    tool_materials_text: str,
    quantization_materials_text: str,
    input_dir: Path,
) -> dict[str, Any]:
    evidence: list[dict[str, Any]] = []
    board_text = board_materials_text
    tool_text = tool_materials_text
    quant_text = quantization_materials_text

    add_regex_evidence(evidence, board_text, "board.fpga_part", r"\b(xc[a-z0-9]+(?:_[a-z0-9]+)?-[a-z0-9]+-[0-9]+-[a-z])\b")
    add_regex_evidence(evidence, board_text, "memory_system.ddr_word_width_bits", r"\bC_DATA_WIDTH\s*=\s*(\d+)\b", transform=int)
    add_regex_evidence(evidence, board_text, "memory_system.ddr_word_width_bits", r"\bAXI\s*(?:数据)?(?:data)?\s*(?:width|宽度)[^0-9]{0,40}(\d+)\s*bit", transform=int)
    add_regex_evidence(evidence, board_text, "memory_system.ddr_word_width_bits", r"\bddr_word_width_bits[^0-9]{0,40}(\d+)\b", transform=int)
    add_regex_evidence(evidence, board_text, "memory_system.axi_data_width_bits", r"\baxi_data_width_bits[^0-9]{0,40}(\d+)\b", transform=int)
    add_regex_evidence(evidence, board_text, "memory_system.axi_data_width_bits", r"\bAXI\s*(?:数据)?(?:data)?\s*(?:width|宽度)[^0-9]{0,40}(\d+)\s*bit", transform=int)
    add_regex_evidence(evidence, board_text, "memory_system.axi_data_bytes", r"\bAXI\s*beat\s*(?:字节数|bytes?)[^0-9]{0,40}(\d+)\s*(?:bytes?)?", transform=int)
    add_regex_evidence(evidence, board_text, "memory_system.axi_data_bytes", r"\bAXI_BEAT_BYTES\s*=\s*(\d+)\b", transform=int)
    add_regex_evidence(evidence, board_text, "memory_system.axi_data_bytes", r"\baxi_data_bytes[^0-9]{0,40}(\d+)\b", transform=int)
    add_regex_evidence(evidence, board_text, "memory_system.ddr_channels", r"\bddr_channels[^0-9]{0,40}(\d+)\b", transform=int)
    add_regex_evidence(evidence, board_text, "memory_system.axi_addr_width_bits", r"\bAXI\s*(?:地址|address)\s*(?:width|宽度)[^0-9]{0,40}(\d+)\s*bit", transform=int)
    add_regex_evidence(evidence, board_text, "memory_system.axi_id_width_bits", r"\bAXI\s*ID\s*(?:width|宽度)[^0-9]{0,40}(\d+)\s*bit", transform=int)
    add_regex_evidence(evidence, board_text, "memory_system.axi_wstrb_width_bits", r"\b(?:AXI\s*)?(?:写\s*)?strobe\s*(?:width|宽度)[^0-9]{0,40}(\d+)\s*bit", transform=int)
    add_regex_evidence(evidence, board_text, "memory_system.core_side_interface_name", r"\bcore_side_interface_name[^A-Za-z0-9_]{0,40}([A-Za-z0-9_]+(?:_\*)?)(?=[`\s，。；;,.]|$)")
    add_regex_evidence(evidence, board_text, "memory_system.core_side_interface_name", r"(?:接口名|interface(?:\s+name)?)\s*(?:是|:|=)?\s*`?([A-Za-z0-9_]+(?:_\*)?)(?=[`\s，。；;,.]|$)")
    add_regex_evidence(evidence, board_text, "memory_system.axi_clock", r"\baxi_clock[^A-Za-z0-9_]{0,40}([A-Za-z0-9_]+)\b")
    add_regex_evidence(evidence, board_text, "memory_system.axi_clock", r"(?:DDR UI / AXI clock|AXI clock|DDR clock)[^A-Za-z0-9_]{0,40}`?([A-Za-z0-9_]+)`?")
    add_regex_evidence(evidence, board_text, "memory_system.axi_reset", r"\baxi_reset[^A-Za-z0-9_]{0,40}([A-Za-z0-9_]+)\b")
    add_regex_evidence(evidence, board_text, "memory_system.axi_reset", r"(?:DDR reset|AXI reset)[^A-Za-z0-9_]{0,40}`?([A-Za-z0-9_]+)`?")
    add_regex_evidence(evidence, board_text, "memory_system.calibration_done_signal", r"\bcalibration_done_signal[^A-Za-z0-9_]{0,40}([A-Za-z0-9_]+)\b")
    add_regex_evidence(evidence, board_text, "memory_system.calibration_done_signal", r"(?:calibration done|calib(?:ration)? done|校准完成)[^A-Za-z0-9_]{0,40}`?([A-Za-z0-9_]+)`?")
    add_regex_evidence(evidence, board_text, "memory_system.real_board_reference_rtl", r"(?:参考\s*RTL|reference\s*RTL)[^A-Za-z0-9_./-]{0,40}`?([A-Za-z0-9_./-]+\.s?v)`?")
    add_regex_evidence(evidence, board_text, "runtime_interface.board_run_command", r"\b(scripts/board/[A-Za-z0-9_./-]+\.sh)\b")
    add_regex_evidence(evidence, board_text, "runtime_interface.control_protocol", r"\bcontrol_protocol[^A-Za-z0-9_]{0,40}([A-Za-z0-9_]+)\b")
    add_regex_evidence(evidence, board_text, "runtime_interface.remote_host", r"\b([A-Za-z0-9_.-]+@(?:\d{1,3}\.){3}\d{1,3})\b")
    add_regex_evidence(evidence, board_text, "runtime_interface.mimic_dir", r"\bMIMIC_DIR\s*=\s*(/[^\s`'\"，。；;]+)")
    add_regex_evidence(evidence, board_text, "runtime_interface.mimic_dir", r"\bmimic_dir[^/\n]{0,80}(/[^\s`'\"，。；;]+)")
    add_regex_evidence(evidence, board_text, "runtime_interface.xdma_id_default", r"\bXDMA_ID\s*=\s*(\d+)\b", transform=int)
    add_regex_evidence(evidence, board_text, "runtime_interface.xdma_id_default", r"\bxdma_id_default[^0-9]{0,40}(\d+)\b", transform=int)
    add_regex_evidence(evidence, board_text, "runtime_interface.ctrl_base", r"\bCTRL_BASE\s*=\s*(0x[0-9a-fA-F]+)\b")
    add_regex_evidence(evidence, board_text, "runtime_interface.ctrl_base", r"\bctrl_base[^0-9a-fA-Fx]{0,40}(0x[0-9a-fA-F]+)\b")
    add_regex_evidence(evidence, board_text, "runtime_interface.ddr_base", r"\bDDR_BASE\s*=\s*(0x[0-9a-fA-F]+)\b")
    add_regex_evidence(evidence, board_text, "runtime_interface.ddr_base", r"\bddr_base[^0-9a-fA-Fx]{0,40}(0x[0-9a-fA-F]+)\b")
    add_regex_evidence(evidence, board_text, "runtime_interface.output_abs", r"\bOUTPUT_ABS\s*=\s*(0x[0-9a-fA-F]+)\b")
    add_regex_evidence(evidence, board_text, "runtime_interface.output_abs", r"\boutput_abs[^0-9a-fA-Fx]{0,40}(0x[0-9a-fA-F]+)\b")
    add_regex_evidence(evidence, board_text, "runtime_interface.ddr_image_default", r"\bddr_image(?:_default)?[^/\n]{0,120}(/[^\s`'\"，。；;]+)")

    add_regex_evidence(evidence, tool_text, "tool.vcs.host", r"\b([A-Za-z0-9_.-]+@(?:\d{1,3}\.){3}\d{1,3})\b")
    add_regex_evidence(evidence, tool_text, "tool.vcs.executable", r"(/[^\s`'\"，。；;]+/bin/vcs)\b")
    add_regex_evidence(evidence, tool_text, "tool.vivado.host", r"\b([A-Za-z0-9_.-]+@(?:\d{1,3}\.){3}\d{1,3})\b")
    add_regex_evidence(evidence, tool_text, "tool.vivado.executable", r"(/[^\s`'\"，。；;]+/Vivado/[^\s`'\"，。；;]+/bin/vivado)\b")
    add_regex_evidence(evidence, quant_text, "numeric_policy.default_precision", r"\b(fp16|bf16|int8|int4)\b", flags=re.IGNORECASE, transform=lambda value: str(value).lower())

    result = {
        "schema_version": "spatialaccagent.field_evidence_candidates.v0",
        "policy": {
            "candidate_only": True,
            "regex_is_not_semantic_ground_truth": True,
            "llm_semantic_confirmation_required": True,
            "critical_fields_must_match_evidence_when_present": True,
            "llm_output_is_not_accepted_as_evidence_without_source": True,
        },
        "evidence": evidence,
    }
    write_json(input_dir / "field_evidence_candidates.json", result)
    return result


def extract_field_evidence(
    board_materials_text: str,
    tool_materials_text: str,
    quantization_materials_text: str,
    input_dir: Path,
) -> dict[str, Any]:
    """Compatibility wrapper returning deterministic candidates, not final semantic evidence."""

    return extract_field_evidence_candidates(board_materials_text, tool_materials_text, quantization_materials_text, input_dir)


def prepare_field_evidence(
    board_materials_text: str,
    tool_materials_text: str,
    quantization_materials_text: str,
    regex_candidates: dict[str, Any],
    input_dir: Path,
    out_dir: Path,
) -> dict[str, Any]:
    split_agents = os.environ.get("SPATIALACC_FIELD_EVIDENCE_SPLIT_AGENTS", "1").strip().lower() not in {"0", "false", "no", "off"}
    if split_agents:
        result = prepare_field_evidence_split_agents(
            board_materials_text,
            tool_materials_text,
            quantization_materials_text,
            regex_candidates,
            input_dir,
            out_dir,
        )
        write_json(input_dir / "field_evidence.json", result)
        return result

    prompt = build_prompt(
        agent="field_evidence_agent",
        task=(
            "Act as the source-evidence engineer. Convert current-run board, tool, and quantization "
            "materials into field_evidence JSON for the chip-design team."
        ),
        inputs={
            "material_corpus_summary": {
                "board_material_chars": len(board_materials_text),
                "tool_material_chars": len(tool_materials_text),
                "quantization_material_chars": len(quantization_materials_text),
                "source_excerpts_are_embedded_in": "deterministic_regex_candidate_summary.selected_fields[].evidence[].excerpt",
            },
            "deterministic_regex_candidate_summary": prompt_field_evidence_summary(regex_candidates),
        },
        output_schema=FIELD_EVIDENCE_SCHEMA,
        rules=[
            "You are the adaptive semantic extractor; deterministic regex candidates are hints only, not ground truth.",
            "Do not use a fixed keyword list as the reason for accepting a value. Accept a field only when the cited excerpt semantically supports it.",
            "Each evidence item must cite source, chunk_id when available, and a short excerpt from the supplied materials.",
            "Reject false positives from regex candidates, especially generic paths, sample/scaffold interfaces, stale board names, or values that are contradicted by nearby text.",
            "If several values conflict, include the competing evidence items and explain the conflict in policy or reason fields; do not silently choose one.",
            "For board/app-shell target fields, produce candidate evidence only; do not select an integration target unless the materials explicitly name it.",
            "Unknown fields should be omitted from evidence rather than invented.",
        ],
    )
    result = llm_json("field_evidence_agent", prompt, FIELD_EVIDENCE_SCHEMA, regex_candidates, out_dir)
    result.setdefault("schema_version", "spatialaccagent.field_evidence.v0")
    policy = result.setdefault("policy", {})
    if isinstance(policy, dict):
        policy["llm_semantic_confirmation_required"] = True
        policy["regex_candidates_are_not_ground_truth"] = True
        policy["llm_output_is_not_accepted_as_evidence_without_source"] = True
    result["_regex_candidate_count"] = len(regex_candidates.get("evidence", [])) if isinstance(regex_candidates.get("evidence"), list) else 0
    write_json(input_dir / "field_evidence.json", result)
    return result


def field_evidence_subset(field_evidence: dict[str, Any], prefixes: tuple[str, ...]) -> dict[str, Any]:
    evidence = [
        item
        for item in field_evidence.get("evidence", [])
        if isinstance(item, dict) and any(str(item.get("field") or "").startswith(prefix) for prefix in prefixes)
    ]
    return {
        "schema_version": field_evidence.get("schema_version", "spatialaccagent.field_evidence_candidates.v0"),
        "policy": copy.deepcopy(field_evidence.get("policy", {})),
        "evidence": evidence,
    }


def prepare_field_evidence_domain(
    *,
    domain: str,
    domain_materials_text: str,
    source_prefixes: tuple[str, ...],
    regex_candidates: dict[str, Any],
    out_dir: Path,
) -> dict[str, Any]:
    candidate_subset = field_evidence_subset(regex_candidates, source_prefixes)
    prompt = build_prompt(
        agent=f"field_evidence_{domain}_agent",
        task=(
            f"Act as the source-evidence engineer for the {domain} input domain. "
            "Review compact current-run candidate excerpts and return only evidence supported by those excerpts."
        ),
        inputs={
            "material_corpus_summary": {
                "domain": domain,
                "material_chars": len(domain_materials_text),
                "complete_domain_material_is_supplied": True,
            },
            "domain_materials_text": domain_materials_text,
            "deterministic_regex_candidate_summary": prompt_field_evidence_summary(candidate_subset),
        },
        output_schema=FIELD_EVIDENCE_SCHEMA,
        rules=[
            "Deterministic regex candidates are hints only, not ground truth.",
            "Accept a field only when the cited excerpt semantically supports it.",
            "Each evidence item must cite source, chunk_id when available, and a short excerpt from the supplied candidate summary.",
            "Reject false positives, stale sample/scaffold interfaces, generic paths, or contradicted values.",
            "If compact evidence is insufficient for a field, omit it rather than inventing it.",
        ],
    )
    result = llm_json(f"field_evidence_{domain}_agent", prompt, FIELD_EVIDENCE_SCHEMA, candidate_subset, out_dir)
    result.setdefault("schema_version", f"spatialaccagent.field_evidence.{domain}.v0")
    return result


def prepare_field_evidence_split_agents(
    board_materials_text: str,
    tool_materials_text: str,
    quantization_materials_text: str,
    regex_candidates: dict[str, Any],
    input_dir: Path,
    out_dir: Path,
) -> dict[str, Any]:
    domains = [
        ("board", board_materials_text, ("board.", "memory_system.", "runtime_interface.")),
        ("tool", tool_materials_text, ("tool.",)),
        ("quantization", quantization_materials_text, ("numeric_policy.",)),
    ]
    outputs = [
        prepare_field_evidence_domain(
            domain=domain,
            domain_materials_text=domain_materials_text,
            source_prefixes=prefixes,
            regex_candidates=regex_candidates,
            out_dir=out_dir,
        )
        for domain, domain_materials_text, prefixes in domains
    ]
    evidence: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for output in outputs:
        for item in output.get("evidence", []):
            if not isinstance(item, dict):
                continue
            key = (
                str(item.get("field") or ""),
                str(item.get("value") or ""),
                str(item.get("source") or ""),
                str(item.get("excerpt") or ""),
            )
            if key in seen:
                continue
            seen.add(key)
            evidence.append(item)
    result = {
        "schema_version": "spatialaccagent.field_evidence.v0",
        "policy": {
            "llm_semantic_confirmation_required": True,
            "regex_candidates_are_not_ground_truth": True,
            "llm_output_is_not_accepted_as_evidence_without_source": True,
            "split_domain_agents": [domain for domain, _, _ in domains],
            "source": "merged_from_domain_llm_agents",
        },
        "evidence": evidence,
        "_regex_candidate_count": len(regex_candidates.get("evidence", [])) if isinstance(regex_candidates.get("evidence"), list) else 0,
        "_domain_result_paths": [
            str(out_dir / f"field_evidence_{domain}_agent_result.json")
            for domain, _, _ in domains
        ],
    }
    write_json(input_dir / "field_evidence_domain_merge.json", result)
    return result


def prompt_field_evidence_summary(field_evidence: dict[str, Any]) -> dict[str, Any]:
    selected_fields = [
        "board.fpga_part",
        "memory_system.ddr_channels",
        "memory_system.ddr_word_width_bits",
        "memory_system.axi_data_width_bits",
        "memory_system.axi_data_bytes",
        "memory_system.axi_addr_width_bits",
        "memory_system.axi_id_width_bits",
        "memory_system.axi_wstrb_width_bits",
        "memory_system.core_side_interface_name",
        "memory_system.axi_clock",
        "memory_system.axi_reset",
        "memory_system.calibration_done_signal",
        "memory_system.real_board_reference_rtl",
        "runtime_interface.control_protocol",
        "runtime_interface.board_run_command",
        "runtime_interface.remote_host",
        "runtime_interface.mimic_dir",
        "runtime_interface.xdma_id_default",
        "runtime_interface.ctrl_base",
        "runtime_interface.ddr_base",
        "runtime_interface.output_abs",
        "runtime_interface.ddr_image_default",
        "tool.vcs.host",
        "tool.vcs.executable",
        "tool.vivado.host",
        "tool.vivado.executable",
        "numeric_policy.default_precision",
    ]
    evidence_items = field_evidence.get("evidence", [])
    summary = {
        "schema_version": "spatialaccagent.field_evidence_summary.v0",
        "policy": field_evidence.get("policy", {}),
        "selected_fields": [],
    }
    for field in selected_fields:
        matches = [
            item
            for item in evidence_items
            if isinstance(item, dict) and item.get("field") == field and evidence_value_present(item.get("value"))
        ]
        if not matches:
            continue
        compact_items = []
        seen_values: set[str] = set()
        for item in matches[:2]:
            value = str(item.get("value"))
            if value in seen_values:
                continue
            seen_values.add(value)
            compact_items.append(
                {
                    "value": item.get("value"),
                    "source": item.get("source"),
                    "chunk_id": item.get("chunk_id"),
                    "excerpt": str(item.get("excerpt", ""))[:220],
                }
            )
        summary["selected_fields"].append({"field": field, "count": len(matches), "evidence": compact_items})
    return summary


def evidence_values(field_evidence: dict[str, Any], field: str) -> list[Any]:
    values = []
    for item in field_evidence.get("evidence", []):
        if isinstance(item, dict) and item.get("field") == field and evidence_value_present(item.get("value")):
            values.append(item.get("value"))
    return values


def evidence_int_values(field_evidence: dict[str, Any], field: str) -> set[int]:
    result = set()
    for value in evidence_values(field_evidence, field):
        try:
            result.add(int(value))
        except (TypeError, ValueError):
            continue
    return result


def normalize_text_value(value: Any) -> str:
    return str(value or "").strip().lower()


def maybe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def build_material_index(
    quantization_index: dict[str, Any],
    board_index: dict[str, Any],
    tool_index: dict[str, Any],
    sample_project_index: dict[str, Any],
    input_dir: Path,
) -> dict[str, Any]:
    index = {
        "schema_version": "spatialaccagent.material_index_bundle.v0",
        "inputs": {
            "quantization": "material_index_quantization.json",
            "board": "material_index_board.json",
            "tools": "material_index_tools.json",
            "sample_project": "sample_project_index.json",
        },
        "counts": {
            "quantization_chunks": len(quantization_index.get("chunks", [])),
            "board_chunks": len(board_index.get("chunks", [])),
            "tool_chunks": len(tool_index.get("chunks", [])),
            "sample_project_refs": len(sample_project_index.get("refs", [])),
            "sample_project_samples": len(sample_project_index.get("samples", [])),
        },
    }
    write_json(input_dir / "material_index.json", index)
    return index


def quote_remote_env(env: dict[str, Any]) -> str:
    pairs = []
    for key, value in sorted(env.items()):
        if value is None or value == "":
            continue
        pairs.append(f"{shlex.quote(str(key))}={shlex.quote(str(value))}")
    return " ".join(pairs)


def probe_local_tool(tool: dict[str, Any], timeout_sec: int) -> dict[str, Any]:
    name = str(tool.get("name") or "").lower()
    executable = clean_executable_path(tool.get("executable")) or name
    resolved = shutil.which(executable) if executable and not Path(executable).is_absolute() else executable
    if not resolved or (Path(resolved).is_absolute() and not Path(resolved).exists()):
        return {
            "name": name,
            "scope": "local",
            "host": None,
            "executable": executable,
            "resolved_executable": resolved,
            "available": False,
            "version_probe": {"ok": False, "error": "local executable not found"},
            "flow_probe": {"ok": False, "error": "local executable not found"},
        }
    version_args = [resolved, "--version"] if name == "verilator" else [resolved, "-version"]
    version_probe = run_probe_command(version_args, timeout_sec)
    flow_probe = {"ok": bool(version_probe.get("ok")), "note": "minimal flow probe not required for this local tool"}
    if name == "verilator":
        workdir = Path(os.environ.get("SPATIALACC_LOCAL_PROBE_WORKDIR", "/tmp/spatialacc_stage0_tool_probe/verilator"))
        workdir.mkdir(parents=True, exist_ok=True)
        tb = workdir / "stage0_verilator_probe.sv"
        tb.write_text("module stage0_verilator_probe(input logic a, output logic y); assign y = a; endmodule\n", encoding="utf-8")
        flow_probe = run_probe_command([resolved, "--lint-only", str(tb)], timeout_sec)
    return {
        "name": name,
        "scope": "local",
        "host": None,
        "executable": executable,
        "resolved_executable": resolved,
        "available": bool(version_probe.get("ok")) and bool(flow_probe.get("ok")),
        "version_probe": version_probe,
        "flow_probe": flow_probe,
    }


def remote_probe_workdir_expr(
    tool: dict[str, Any],
    name: str,
    run_namespace: str = "",
) -> str:
    safe_namespace = re.sub(r"[^A-Za-z0-9_.-]", "_", run_namespace).strip("._-")
    namespace_suffix = f"/{safe_namespace}" if safe_namespace else ""
    configured = tool.get("workdir") or os.environ.get("SPATIALACC_REMOTE_PROBE_WORKDIR")
    if configured:
        return shlex.quote(
            str(configured).rstrip("/")
            + f"/stage0_{name}_probe"
            + namespace_suffix
        )
    safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", name)
    return (
        f"$HOME/workspace/spatialacc_stage0_tool_probe/{safe_name}"
        + namespace_suffix
    )


def probe_remote_vcs_flow(
    tool: dict[str, Any],
    executable: str,
    timeout_sec: int,
    run_namespace: str = "",
) -> dict[str, Any]:
    host = str(tool.get("host"))
    port = int(tool.get("port") or 22)
    env_dict = dict(tool.get("env") or {})
    env_dict.setdefault("VCS_TARGET_ARCH", "linux64")
    env = quote_remote_env(env_dict)
    exe = shlex.quote(executable)
    workdir = remote_probe_workdir_expr(tool, "vcs", run_namespace)
    tb = 'module stage0_vcs_probe_tb; initial begin $display("STAGE0_VCS_PROBE_PASS"); $finish; end endmodule'
    run_vcs = f"{env} {exe} -full64 -sverilog -o simv stage0_vcs_probe_tb.sv > vcs_compile.log 2>&1" if env else f"{exe} -full64 -sverilog -o simv stage0_vcs_probe_tb.sv > vcs_compile.log 2>&1"
    remote_body = " && ".join(
        [
            f"mkdir -p {workdir} && cd {workdir}",
            "rm -f simv stage0_vcs_probe_tb.sv vcs_compile.log sim.log",
            f"printf '%s\\n' {shlex.quote(tb)} > stage0_vcs_probe_tb.sv",
            run_vcs,
            "./simv > sim.log 2>&1",
            "grep -q STAGE0_VCS_PROBE_PASS sim.log",
            "printf 'STAGE0_VCS_FLOW_PASS\\n'",
        ]
    )
    return run_ssh_command(host, port, remote_body, timeout_sec)


def parse_vivado_resource_budget(report_text: str) -> dict[str, int] | None:
    """Parse resource capacities from a real Vivado utilization report."""

    labels = {
        "CLB LUTs": "lut",
        "CLB Registers": "ff",
        "RAMB36/FIFO": "bram36",
        "RAMB18": "bram18",
        "URAM": "uram",
        "DSPs": "dsp",
    }
    budget: dict[str, int] = {}
    for line in str(report_text or "").splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip().replace("*", "") for cell in line.strip().strip("|").split("|")]
        if len(cells) < 5:
            continue
        key = labels.get(cells[0])
        if not key:
            continue
        try:
            budget[key] = int(cells[4].replace(",", ""))
        except ValueError:
            continue
    if set(labels.values()) <= set(budget):
        budget["bram"] = budget["bram36"]
        return budget
    return None


def probe_remote_vivado_flow(
    tool: dict[str, Any],
    executable: str,
    board_part: str | None,
    timeout_sec: int,
    run_namespace: str = "",
) -> dict[str, Any]:
    if not board_part:
        return {"ok": False, "error": "board fpga_part missing; Vivado synthesis probe cannot choose part"}
    host = str(tool.get("host"))
    port = int(tool.get("port") or 22)
    exe = shlex.quote(executable)
    workdir = remote_probe_workdir_expr(tool, "vivado", run_namespace)
    verilog = "module stage0_vivado_probe(input clk, input a, output y); assign y = a; endmodule"
    tcl_lines = [
        "read_verilog stage0_vivado_probe.v",
        f"synth_design -top stage0_vivado_probe -part {board_part}",
        "report_utilization -file util.rpt",
        'puts "STAGE0_VIVADO_PROBE_PASS"',
        "exit",
    ]
    write_tcl = " ".join(shlex.quote(line) for line in tcl_lines)
    remote_body = " && ".join(
        [
            f"mkdir -p {workdir} && cd {workdir}",
            "rm -f stage0_vivado_probe.v probe.tcl vivado.log vivado_stdout.log util.rpt",
            f"printf '%s\\n' {shlex.quote(verilog)} > stage0_vivado_probe.v",
            f"printf '%s\\n' {write_tcl} > probe.tcl",
            f"{exe} -mode batch -source probe.tcl -nojournal -log vivado.log > vivado_stdout.log 2>&1",
            "(grep -q STAGE0_VIVADO_PROBE_PASS vivado.log || grep -q STAGE0_VIVADO_PROBE_PASS vivado_stdout.log)",
            "printf 'STAGE0_VIVADO_FLOW_PASS\\n'",
            r"grep -E '^\|[[:space:]]*(CLB LUTs\*|CLB Registers|RAMB36/FIFO\*|RAMB18|URAM|DSPs)' util.rpt",
        ]
    )
    probe = run_ssh_command(host, port, remote_body, timeout_sec)
    budget = parse_vivado_resource_budget(str(probe.get("stdout") or ""))
    if budget is None:
        probe["resource_budget_error"] = "Vivado flow probe did not expose a complete FPGA resource budget"
    else:
        probe["resource_budget"] = budget
    return probe


def probe_remote_tool(
    tool: dict[str, Any],
    timeout_sec: int,
    board_part: str | None = None,
    run_namespace: str = "",
) -> dict[str, Any]:
    name = str(tool.get("name") or "").lower()
    host = tool.get("host")
    port = int(tool.get("port") or 22)
    executable = clean_executable_path(tool.get("executable"))
    if not host:
        return {
            "name": name,
            "scope": "remote",
            "host": host,
            "port": port,
            "executable": executable,
            "available": False,
            "version_probe": {"ok": False, "error": "remote host missing"},
            "flow_probe": {"ok": False, "error": "remote host missing"},
        }
    if not executable:
        return {
            "name": name,
            "scope": "remote",
            "host": host,
            "port": port,
            "executable": executable,
            "available": False,
            "version_probe": {"ok": False, "error": "remote executable missing"},
            "flow_probe": {"ok": False, "error": "remote executable missing"},
        }

    env_dict = dict(tool.get("env") or {})
    if name == "vcs":
        env_dict.setdefault("VCS_TARGET_ARCH", "linux64")
    env = quote_remote_env(env_dict)
    executable_q = shlex.quote(executable)
    if name == "vivado":
        remote_body = f"test -x {executable_q} && {executable_q} -version"
    elif name == "vcs":
        remote_body = f"test -x {executable_q} && {env} {executable_q} -ID" if env else f"test -x {executable_q} && {executable_q} -ID"
    else:
        remote_body = f"test -x {executable_q}"
    version_probe = run_ssh_command(str(host), port, remote_body, timeout_sec)
    flow_probe = {"ok": bool(version_probe.get("ok")), "note": "minimal flow probe not required for this remote tool"}
    if name == "vcs":
        flow_probe = probe_remote_vcs_flow(
            tool, executable, timeout_sec, run_namespace
        )
    elif name == "vivado":
        flow_probe = probe_remote_vivado_flow(
            tool, executable, board_part, timeout_sec, run_namespace
        )
    return {
        "name": name,
        "scope": "remote",
        "host": str(host),
        "port": port,
        "executable": executable,
        "available": bool(version_probe.get("ok")) and bool(flow_probe.get("ok")),
        "version_probe": version_probe,
        "flow_probe": flow_probe,
    }


def prepare_tool_availability(tool_profile: dict[str, Any], input_dir: Path, board_profile: dict[str, Any] | None = None) -> dict[str, Any]:
    timeout_sec = int(os.environ.get("SPATIALACC_TOOL_PROBE_TIMEOUT_SEC", "120") or "120")
    timeout_sec = max(5, timeout_sec)
    board_part = (board_profile or {}).get("board", {}).get("fpga_part")
    run_namespace = input_dir.parent.name
    tools = []
    for tool in tool_profile.get("tools", []):
        scope = str(tool.get("scope") or "").lower()
        name = str(tool.get("name") or "").lower()
        if name not in {"vcs", "verilator", "vivado"}:
            continue
        if scope == "remote":
            tools.append(
                probe_remote_tool(
                    tool,
                    timeout_sec,
                    board_part,
                    run_namespace,
                )
            )
        elif scope == "local":
            tools.append(probe_local_tool(tool, timeout_sec))
        else:
            tools.append(
                {
                    "name": name,
                    "scope": scope or None,
                    "host": tool.get("host"),
                    "executable": clean_executable_path(tool.get("executable")),
                    "available": False,
                    "version_probe": {"ok": False, "error": "tool scope missing or unsupported"},
                    "flow_probe": {"ok": False, "error": "tool scope missing or unsupported"},
                }
            )
    availability = {
        "schema_version": "spatialaccagent.tool_availability.v0",
        "policy": {
            "vivado_required": True,
            "functional_verification_requires_any_one_of": ["vcs", "verilator"],
            "minimal_flow_probe_required": True,
            "probe_timeout_sec": timeout_sec,
        },
        "tools": tools,
    }
    vivado = availability_by_name(availability, "vivado")
    budget = (vivado or {}).get("flow_probe", {}).get("resource_budget")
    if isinstance(budget, dict):
        availability["discovered_target_board_resource_budget"] = budget
    write_json(input_dir / "tool_availability.json", availability)
    return availability


def bind_discovered_board_resource_budget(
    board_profile: dict[str, Any],
    tool_availability: dict[str, Any],
) -> dict[str, Any]:
    """Attach only real Vivado-discovered device capacity to the board profile."""

    result = copy.deepcopy(board_profile)
    budget = tool_availability.get("discovered_target_board_resource_budget")
    if not isinstance(budget, dict):
        return result
    required = {"lut", "ff", "bram", "bram36", "bram18", "uram", "dsp"}
    if not required <= set(budget):
        return result
    board = result.setdefault("board", {})
    if isinstance(board, dict):
        board["resource_budget"] = {key: int(budget[key]) for key in sorted(required)}
        board["resource_budget_source"] = "real_vivado_target_part_probe"
    return result


def availability_by_name(tool_availability: dict[str, Any], name: str) -> dict[str, Any] | None:
    for item in tool_availability.get("tools", []):
        if str(item.get("name", "")).lower() == name.lower():
            return item
    return None


def tool_probe_ok(tool_availability: dict[str, Any], name: str) -> bool:
    tool = availability_by_name(tool_availability, name)
    if not tool:
        return False
    return bool(tool.get("available")) and bool(tool.get("version_probe", {}).get("ok")) and bool(tool.get("flow_probe", {}).get("ok"))


def local_path_exists(value: str, cwd: Path) -> bool:
    path = Path(value)
    if path.is_absolute():
        return path.exists()
    return (Path.cwd() / value).exists() or (cwd / value).exists()


def shell_command_referenced_paths(command: str) -> list[str]:
    candidates = re.findall(r"(?<![A-Za-z0-9_./-])(\./scripts/[A-Za-z0-9_./-]+|scripts/[A-Za-z0-9_./-]+|[A-Za-z0-9_./-]+\.sh)(?![A-Za-z0-9_./-])", command)
    return list(dict.fromkeys(candidate[2:] if candidate.startswith("./") else candidate for candidate in candidates))


def path_exists_for_protocol(item: dict[str, Any]) -> bool:
    argv = item.get("execution", {}).get("argv") or []
    if not argv:
        return False
    first = str(argv[0])
    cwd = Path(str(item.get("execution", {}).get("cwd") or Path.cwd()))
    if first in {"bash", "sh"} and len(argv) >= 3 and str(argv[1]) == "-lc":
        referenced = shell_command_referenced_paths(str(argv[2]))
        return all(local_path_exists(path, cwd) for path in referenced) if referenced else True
    if first in {"python", "python3", sys.executable}:
        if len(argv) >= 2 and str(argv[1]).endswith(".py"):
            return local_path_exists(str(argv[1]), cwd)
        return bool(shutil.which(first) or first == sys.executable)
    if first in {"bash", "sh", "python", "python3", sys.executable}:
        return bool(shutil.which(first) or first == sys.executable)
    first_path = Path(first)
    if first_path.is_absolute():
        return first_path.exists()
    repo_path = Path.cwd() / first
    if repo_path.exists():
        return True
    return cwd.exists() and (cwd / first).exists()


def prepare_tool_protocols(
    board: dict[str, Any],
    tool_profile: dict[str, Any],
    tool_materials_text: str,
    tool_materials_dir: Path,
    input_dir: Path,
    case_adapter: dict[str, Any],
) -> dict[str, Any]:
    run_dir = input_dir.parent.resolve()
    chisel_dir = run_dir / "generated" / "chisel"
    top_sv = chisel_dir / "GeneratedAcceleratorTop.sv"
    fpga_top_sv = chisel_dir / "GeneratedAxiDdrTop.sv"
    sv_glob = chisel_dir / "*.sv"
    vcs_env = profile_env(tool_profile, "vcs")
    verilator_env = profile_env(tool_profile, "verilator")
    vivado_env = profile_env(tool_profile, "vivado")
    has_verilator = tool_configured(tool_profile, "verilator")
    has_vcs = tool_configured(tool_profile, "vcs", require_host=True)
    has_vivado = tool_configured(tool_profile, "vivado", require_host=True, require_executable=True)
    verilator_tool = tool_by_name(tool_profile, "verilator") or {}
    verilator_bin = clean_executable_path(verilator_tool.get("executable")) or "verilator"

    def case_tool(
        role: str,
        *,
        env: dict[str, str] | None = None,
        required: bool | None = None,
    ) -> dict[str, Any]:
        spec = adapter_tool(case_adapter, role) or {
            "name": f"case_{role}",
            "kind": f"case_{role}",
            "scope": "local",
            "argv": [],
            "required": False,
            "consumes": [],
            "produces": [],
        }
        argv = list(spec.get("argv") or [])
        requires_external = str(spec.get("requires_external_tool") or "")
        if requires_external == "vcs" and not has_vcs:
            argv = []
        elif requires_external == "verilator" and not has_verilator:
            argv = []
        elif requires_external == "vivado" and not has_vivado:
            argv = []
        item = structured_command(
            name=str(spec.get("name") or f"case_{role}"),
            kind=str(spec.get("kind") or f"case_{role}"),
            scope=str(spec.get("scope") or "local"),
            argv=argv,
            cwd=Path.cwd(),
            env=env or {},
            required=bool(spec.get("required", False)) if required is None else required,
            required_group=spec.get("required_group"),
            consumes=list(spec.get("consumes") or []),
            produces=list(spec.get("produces") or []),
        )
        item["adapter_role"] = role
        if spec.get("legacy_name"):
            item["legacy_name"] = spec.get("legacy_name")
        return item

    tools = [
        structured_command(
            name="chisel_generate",
            kind="chisel_generation",
            scope="local",
            argv=[
                "bash",
                "-lc",
                f"./scripts/elaborate.sh && test -f {shlex.quote(str(top_sv))} && test -f {shlex.quote(str(fpga_top_sv))}",
            ],
            cwd=chisel_dir,
            required=True,
            script_expected_after_codegen=True,
            consumes=[str(chisel_dir / "src/main/scala")],
            produces=[str(top_sv), str(fpga_top_sv)],
        ),
        structured_command(
            name="chisel_compile",
            kind="chisel_compile",
            scope="local",
            argv=[
                "bash",
                "-lc",
                f"test -f {shlex.quote(str(top_sv))} && test -f {shlex.quote(str(fpga_top_sv))}",
            ],
            cwd=run_dir,
            required=True,
            consumes=[str(top_sv), str(fpga_top_sv)],
        ),
        case_tool("weight_manifest_generate"),
        case_tool("board_interface_discovery"),
        case_tool("tb_scaffold_generate"),
        case_tool("stage_leaf_static"),
        case_tool("real_weight_artifacts"),
        case_tool("multilayer_pipeline"),
        case_tool("axi_ddr_interface"),
        structured_command(name="stage_verilator_lint", kind="stage_verilator_lint", scope="local", argv=["bash", "-lc", f"{shlex.quote(verilator_bin)} --lint-only -Wno-fatal --timing {shlex.quote(str(chisel_dir))}/*.sv"] if has_verilator else [], cwd=Path.cwd(), required=False, consumes=[str(chisel_dir)]),
        case_tool("verilator_liveness", env=verilator_env, required=False),
        case_tool("vcs_liveness", env=vcs_env, required=False),
        case_tool("vcs_functional_sim", env=vcs_env),
        case_tool("vcs_evidence_analyzer"),
        case_tool("vivado_synthesis", env=vivado_env),
        case_tool("vivado_implementation", env=vivado_env),
        case_tool("runtime_bitstream"),
        structured_command(name="board_runtime", kind="board_runtime", scope="board", argv=shlex.split(board.get("runtime_interface", {}).get("board_run_command") or ""), cwd=Path.cwd(), required=True),
    ]
    protocols = {
        "schema_version": "spatialaccagent.tool_protocols.v0",
        "input_materials": {
            "tool_materials_dir": str(tool_materials_dir.resolve()),
            "summary": tool_materials_summary(tool_materials_text),
            "extracted_tool_profile": "tool_profile.json",
            "text_excerpt": tool_materials_text[:4000],
        },
        "case_adapter": {
            "case_id": case_adapter.get("case_id"),
            "status": case_adapter.get("status"),
            "model_family": case_adapter.get("model_family"),
            "source": case_adapter.get("source"),
            "artifact": "case_adapter.json",
            "errors": case_adapter.get("errors", []),
        },
        "tools": [
            item | {"script_exists": path_exists_for_protocol(item)}
            for item in tools
        ],
        "policy": {
            "real_tool_evidence_required_for_final_design_pass": True,
            "unconfigured_tool_is_pending_evidence": True,
            "functional_sim_accepts_any_one_of": case_adapter.get("acceptance", {}).get("functional_sim_accepts_any_one_of", []),
            "legacy_liveness_tools_not_acceptance": case_adapter.get("acceptance", {}).get("legacy_liveness_tools_not_acceptance", []),
        },
    }
    write_json(input_dir / "tool_protocols.json", protocols)
    return protocols


def prepare_human_boundary(input_dir: Path) -> dict[str, Any]:
    boundary = {
        "schema_version": "spatialaccagent.human_agent_boundary.v0",
        "auto_allowed": ["parameter_sync", "signal_connection", "script_path", "trace_parser", "wrapper_runtime_sync", "valid_delay", "address_offset", "ddr_image_regen", "small_fifo_depth", "regression_rerun"],
        "approval_required": ["pipeline_stage_change", "tile_size_change", "parallelism_change", "memory_layout_change", "data_packing_change", "numeric_policy_change", "major_template_rewrite", "timing_pipeline_stage", "axi_ddr_access_change", "major_buffer_structure"],
        "forbidden": ["delete_failing_test", "modify_golden_to_pass", "loosen_tolerance_without_approval", "change_model_semantics", "treat_gqa_as_mha", "bypass_checker", "mark_failed_regression_pass", "claim_root_cause_without_evidence"],
    }
    write_json(input_dir / "human_agent_boundary.json", boundary)
    return boundary


def validate_inputs(items: dict[str, dict[str, Any]]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    task = items["task_card"]
    model = items["model_config"]
    numeric = items["numeric_policy"]
    board = items["target_board_profile"]
    tool_profile = items.get("tool_profile", {})
    tool_availability = items.get("tool_availability", {})
    tool_protocols = items.get("tool_protocols", {})
    case_adapter = items.get("case_adapter", {})
    field_evidence = items.get("field_evidence", {})
    sample_project_index = items.get("sample_project_index", {})
    field_policy = field_evidence.get("policy", {}) if isinstance(field_evidence.get("policy"), dict) else {}
    if not field_policy.get("llm_semantic_confirmation_required"):
        errors.append("field_evidence missing llm_semantic_confirmation_required policy")
    if field_policy.get("candidate_only"):
        errors.append("field_evidence is regex candidate-only; LLM semantic extraction did not produce final evidence")
    for index, item in enumerate(field_evidence.get("evidence", []) if isinstance(field_evidence.get("evidence"), list) else []):
        if not item.get("source") or not item.get("excerpt"):
            errors.append(f"field_evidence[{index}] missing source/excerpt for semantic traceability")
            break
    if not task.get("target_model"):
        errors.append("task_card missing target_model")
    if not task.get("design_goal"):
        errors.append("task_card missing design_goal")
    if not model.get("block", {}).get("operator_sequence"):
        errors.append("model_config missing block.operator_sequence")
    numeric_rules = numeric.get("default_rules", {})
    numeric_required = ["weight_dtype", "activation_dtype", "acc_dtype", "scale_dtype", "rounding", "saturation"]
    numeric_missing = [name for name in numeric_required if name not in numeric_rules]
    if numeric_missing:
        errors.append(f"numeric_policy.default_rules missing exact fields: {numeric_missing}")
    if not numeric.get("tolerance", {}).get("stage"):
        errors.append("numeric_policy missing tolerance.stage")
    if not numeric.get("tolerance", {}).get("system"):
        errors.append("numeric_policy missing tolerance.system")
    comparison = numeric.get("tolerance", {}).get("comparison", {})
    comparison_missing = [
        name
        for name in ("atol", "rtol", "max_mismatch_fraction")
        if not isinstance(comparison, dict) or comparison.get(name) is None
    ]
    if comparison_missing:
        errors.append(f"numeric_policy missing resolved tolerance.comparison fields: {comparison_missing}")
    if not numeric_rules:
        errors.append("numeric_policy missing default_rules")
    if not items["template_metadata"].get("templates"):
        errors.append("template_metadata missing templates")
    if not items["design_space"].get("search_params"):
        errors.append("design_space missing search_params")
    qor_targets = items["design_space"].get("qor_targets", {})
    if qor_targets.get("resource_budget") == "discovered_target_board":
        budget = board.get("board", {}).get("resource_budget", {}) if isinstance(board.get("board"), dict) else {}
        required_budget_fields = {"lut", "ff", "bram36", "bram18", "uram", "dsp"}
        if not required_budget_fields <= set(budget):
            errors.append("target_board_profile missing real Vivado-discovered resource budget")
    if case_adapter.get("status") not in {"ready", "pass"}:
        adapter_errors = case_adapter.get("errors", [])
        errors.append(f"case_adapter is not ready for this run: status={case_adapter.get('status')} errors={adapter_errors}")
    if not board.get("board"):
        errors.append("target_board_profile missing board section")
    if "memory_system" not in board:
        errors.append("target_board_profile missing memory_system section")
    if "runtime_interface" not in board:
        errors.append("target_board_profile missing runtime_interface section")
    if not board.get("board", {}).get("fpga_part"):
        errors.append("target_board_profile missing board.fpga_part")

    memory = board.get("memory_system", {})
    for field in ["ddr_channels", "ddr_word_width_bits", "axi_data_bytes"]:
        if memory.get(field) in {None, "", 0}:
            errors.append(f"target_board_profile.memory_system missing {field}")

    runtime = board.get("runtime_interface", {})
    if not runtime.get("board_run_command"):
        errors.append("target_board_profile.runtime_interface missing board_run_command")
    if not runtime.get("control_protocol"):
        errors.append("target_board_profile.runtime_interface missing control_protocol")

    sample_refs = sample_project_index.get("refs", [])
    sample_errors = [sample for sample in sample_project_index.get("samples", []) if sample.get("status") != "ok"]
    if sample_refs and sample_errors:
        warnings.append("sample_project_index failed to read one or more declared sample projects; later real-tool/remote probes must confirm these references")

    ddr_width_values = evidence_int_values(field_evidence, "memory_system.ddr_word_width_bits")
    selected_ddr_width = maybe_int(memory.get("ddr_word_width_bits"))
    if ddr_width_values and selected_ddr_width not in ddr_width_values:
        errors.append(
            f"target_board_profile.memory_system.ddr_word_width_bits={memory.get('ddr_word_width_bits')} "
            f"does not match field evidence {sorted(ddr_width_values)}"
        )
    if len(ddr_width_values) > 1:
        warnings.append(
            "field evidence contains multiple DDR/AXI width values; downstream board-runtime gates must use "
            "target_board_profile source labels and real board reference RTL rather than assuming a fixed width"
        )

    axi_byte_values = evidence_int_values(field_evidence, "memory_system.axi_data_bytes")
    selected_axi_bytes = maybe_int(memory.get("axi_data_bytes"))
    if axi_byte_values and selected_axi_bytes not in axi_byte_values:
        errors.append(
            f"target_board_profile.memory_system.axi_data_bytes={memory.get('axi_data_bytes')} "
            f"does not match field evidence {sorted(axi_byte_values)}"
        )
    if len(axi_byte_values) > 1:
        warnings.append(
            "field evidence contains multiple AXI beat byte values; downstream board-runtime gates must use "
            "target_board_profile source labels and real board reference RTL rather than assuming a fixed beat size"
        )

    part_values = {normalize_text_value(value) for value in evidence_values(field_evidence, "board.fpga_part")}
    selected_part = normalize_text_value(board.get("board", {}).get("fpga_part"))
    if part_values and selected_part and selected_part not in part_values:
        errors.append(f"target_board_profile.board.fpga_part={selected_part} does not match field evidence {sorted(part_values)}")

    run_command_values = {normalize_text_value(value) for value in evidence_values(field_evidence, "runtime_interface.board_run_command")}
    selected_run_command = normalize_text_value(runtime.get("board_run_command"))
    if run_command_values and selected_run_command and selected_run_command not in run_command_values:
        errors.append(
            f"target_board_profile.runtime_interface.board_run_command={selected_run_command} "
            f"does not match field evidence {sorted(run_command_values)}"
        )

    tools_by_name = {str(tool.get("name", "")).lower(): tool for tool in tool_profile.get("tools", [])}
    if "vcs" not in tools_by_name and "verilator" not in tools_by_name:
        errors.append("tool_profile must include at least one functional verification tool: vcs or verilator")
    if "vivado" not in tools_by_name:
        errors.append("tool_profile missing required vivado tool")

    vcs = tools_by_name.get("vcs")
    if vcs is not None and str(vcs.get("scope")) == "remote" and not vcs.get("host"):
        errors.append("tool_profile.vcs remote tool missing host")
    vivado = tools_by_name.get("vivado")
    if vivado is not None:
        if not vivado.get("host"):
            errors.append("tool_profile.vivado missing host")
        if not vivado.get("executable"):
            errors.append("tool_profile.vivado missing executable")

    if not tool_availability.get("tools"):
        errors.append("tool_availability missing probe results")
    if not tool_probe_ok(tool_availability, "vivado"):
        errors.append("tool_availability.vivado did not pass version and minimal synthesis flow probes")
    if not tool_probe_ok(tool_availability, "vcs") and not tool_probe_ok(tool_availability, "verilator"):
        errors.append("tool_availability must confirm at least one functional verification tool with version and minimal flow probe: vcs or verilator")

    vcs_exec_values = {normalize_text_value(value) for value in evidence_values(field_evidence, "tool.vcs.executable")}
    if vcs is not None and vcs_exec_values and normalize_text_value(vcs.get("executable")) not in vcs_exec_values:
        errors.append("tool_profile.vcs.executable does not match field evidence")
    vivado_exec_values = {normalize_text_value(value) for value in evidence_values(field_evidence, "tool.vivado.executable")}
    if vivado is not None and vivado_exec_values and normalize_text_value(vivado.get("executable")) not in vivado_exec_values:
        errors.append("tool_profile.vivado.executable does not match field evidence")

    protocol_tools = tool_protocols.get("tools", [])
    required_protocols = [tool for tool in protocol_tools if tool.get("required")]
    for tool in required_protocols:
        if not tool.get("execution", {}).get("argv"):
            errors.append(f"tool_protocols.{tool.get('name')} missing execution.argv")
        if not tool.get("script_exists") and not tool.get("script_expected_after_codegen"):
            errors.append(f"tool_protocols.{tool.get('name')} first executable/script does not exist")

    functional_group = [tool for tool in protocol_tools if tool.get("required_group") == "functional_sim"]
    if functional_group and not any(tool.get("execution", {}).get("argv") and tool.get("script_exists") for tool in functional_group):
        errors.append("tool_protocols functional_sim group has no configured executable tool")
    return errors, warnings


PREPARED_INPUT_ARTIFACTS = (
    "material_index",
    "sample_project_index",
    "field_evidence_candidates",
    "field_evidence",
    "task_card",
    "model_config",
    "numeric_policy",
    "target_board_profile",
    "tool_profile",
    "tool_availability",
    "case_adapter",
    "template_library",
    "template_metadata",
    "design_space",
    "tool_protocols",
    "human_agent_boundary",
)


def revalidate_prepared_inputs(manifest_path: Path) -> list[str]:
    """Re-run the Stage-0 deterministic gate for a passed input artifact.

    This permits a framework-only Stage-0 implementation change to retain a
    valid current-run intake without replaying its LLM team.  It is deliberately
    fail-closed: all referenced artifacts, physical candidates, stream packing,
    real-tool probes, and protocol evidence must still satisfy current checks.
    """

    errors: list[str] = []
    try:
        manifest = read_json(manifest_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"prepared_inputs cannot be read for semantic revalidation: {exc}"]
    if manifest.get("status") != "ready" or manifest.get("errors"):
        return [
            "prepared_inputs is not a reusable passed intake: "
            f"status={manifest.get('status')} errors={manifest.get('errors', [])}"
        ]

    run_dir = Path(str(manifest.get("run_dir") or manifest_path.parents[1])).resolve()
    if run_dir != manifest_path.parents[1].resolve():
        errors.append("prepared_inputs run_dir does not match its artifact location")
    refs = manifest.get("inputs")
    if not isinstance(refs, dict):
        return [*errors, "prepared_inputs missing inputs object"]

    items: dict[str, dict[str, Any]] = {}
    for name in PREPARED_INPUT_ARTIFACTS:
        ref = refs.get(name)
        if not ref:
            errors.append(f"prepared_inputs missing artifact reference: {name}")
            continue
        path = Path(str(ref))
        if not path.is_absolute():
            path = run_dir / path
        if not path.is_file():
            errors.append(f"prepared_inputs artifact is missing: {name} -> {path}")
            continue
        try:
            data = read_json(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"prepared_inputs artifact is unreadable: {name} -> {exc}")
            continue
        if not isinstance(data, dict):
            errors.append(f"prepared_inputs artifact is not an object: {name}")
            continue
        items[name] = data

    required_for_gate = set(PREPARED_INPUT_ARTIFACTS) - {"field_evidence_candidates"}
    if required_for_gate <= set(items):
        input_errors, _warnings = validate_inputs(items)
        errors.extend(input_errors)
        design_space = items["design_space"]
        stream_contract = semantic_stream_contract(
            items["case_adapter"], items["numeric_policy"], items["target_board_profile"]
        )
        errors.extend(design_space_stream_packing_errors(design_space, stream_contract))
        errors.extend(design_space_physical_candidate_errors(design_space))

    design_team = manifest.get("design_team")
    if not isinstance(design_team, dict):
        errors.append("prepared_inputs missing design_team acceptance record")
    else:
        errors.extend(team_failure_errors(design_team))
    return errors


def prepare_inputs(args: argparse.Namespace) -> tuple[Path, dict[str, Any]]:
    run_dir = args.run_dir.resolve()
    input_dir = run_dir / "input"
    llm_dir = input_dir / "llm"
    input_dir.mkdir(parents=True, exist_ok=True)
    require_llm_configuration(input_dir)

    task_text = read_text(args.task_spec)
    qor_targets = task_qor_targets(task_text)
    quantization_materials_text, quantization_index = read_text_bundle_indexed(args.quantization_materials_dir, input_dir, "quantization")
    board_materials_text, board_index = read_text_bundle_indexed(args.board_materials_dir, input_dir, "board")
    tool_materials_text, tool_index = read_text_bundle_indexed(args.tool_materials_dir, input_dir, "tools")
    _sample_project_text, sample_project_index = prepare_sample_project_index(board_materials_text, input_dir)
    sample_project_summary_data = sample_project_summary(sample_project_index)
    board_summary = material_index_summary(board_index, "board")
    tool_summary = material_index_summary(tool_index, "tools")
    material_index = build_material_index(quantization_index, board_index, tool_index, sample_project_index, input_dir)
    field_evidence_candidates = extract_field_evidence_candidates(board_materials_text, tool_materials_text, quantization_materials_text, input_dir)
    field_evidence = prepare_field_evidence(
        board_materials_text,
        tool_materials_text,
        quantization_materials_text,
        field_evidence_candidates,
        input_dir,
        llm_dir,
    )
    field_evidence_summary = prompt_field_evidence_summary(field_evidence)
    target_seq = target_seq_from_task(task_text)

    model_source = args.model_source.resolve()
    model_dir = args.model_dir.resolve()
    if not model_dir.is_dir():
        raise InputPreparationError(f"model_dir is not a directory: {model_dir}")
    model_fallback = load_model_source(model_source, target_seq)

    llm_workers = env_int("SPATIALACC_STAGE0_LLM_WORKERS", 1, 1)
    template_library, template_metadata = prepare_template_library(args.template_dir, input_dir)

    if llm_workers == 1:
        model_config = prepare_model_config(task_text, model_source, model_fallback, llm_dir)
        model_config = {**model_config, "model_dir": str(model_dir)}
        numeric_policy = prepare_numeric_policy(quantization_materials_text, llm_dir)
        target_board_profile = prepare_board_profile(board_summary, field_evidence_summary, sample_project_summary_data, llm_dir)
        task_card = prepare_task_card(task_text, model_config, llm_dir)
        case_adapter = build_case_adapter(model_config, run_dir, args.tool_materials_dir)
        tool_profile = prepare_tool_profile(tool_summary, target_board_profile, field_evidence_summary, llm_dir)
        design_space = prepare_design_space(
            model_config,
            template_metadata,
            target_board_profile,
            numeric_policy,
            qor_targets,
            llm_dir,
            case_adapter,
        )
    else:
        first_wave: dict[str, Any] = {}
        with ThreadPoolExecutor(max_workers=llm_workers) as pool:
            futures = {
                pool.submit(prepare_model_config, task_text, model_source, model_fallback, llm_dir): "model_config",
                pool.submit(prepare_numeric_policy, quantization_materials_text, llm_dir): "numeric_policy",
                pool.submit(prepare_board_profile, board_summary, field_evidence_summary, sample_project_summary_data, llm_dir): "target_board_profile",
            }
            for future in as_completed(futures):
                first_wave[futures[future]] = future.result()

        model_config = first_wave["model_config"]
        model_config = {**model_config, "model_dir": str(model_dir)}
        numeric_policy = first_wave["numeric_policy"]
        target_board_profile = first_wave["target_board_profile"]
        case_adapter = build_case_adapter(model_config, run_dir, args.tool_materials_dir)

        second_wave: dict[str, Any] = {}
        with ThreadPoolExecutor(max_workers=llm_workers) as pool:
            futures = {
                pool.submit(prepare_task_card, task_text, model_config, llm_dir): "task_card",
                pool.submit(prepare_tool_profile, tool_summary, target_board_profile, field_evidence_summary, llm_dir): "tool_profile",
                pool.submit(
                    prepare_design_space,
                    model_config,
                    template_metadata,
                    target_board_profile,
                    numeric_policy,
                    qor_targets,
                    llm_dir,
                    case_adapter,
                ): "design_space",
            }
            for future in as_completed(futures):
                second_wave[futures[future]] = future.result()

        task_card = second_wave["task_card"]
        tool_profile = second_wave["tool_profile"]
        design_space = second_wave["design_space"]
    # The checkpoint is an explicit run input.  Do not let a shared environment
    # variable select another parallel run's model material.
    tool_availability = prepare_tool_availability(tool_profile, input_dir, target_board_profile)
    target_board_profile = bind_discovered_board_resource_budget(target_board_profile, tool_availability)
    write_json(input_dir / "case_adapter.json", case_adapter)
    tool_protocols = prepare_tool_protocols(
        target_board_profile,
        tool_profile,
        tool_materials_text,
        args.tool_materials_dir,
        input_dir,
        case_adapter,
    )
    human_boundary = prepare_human_boundary(input_dir)

    outputs = {
        "material_index": material_index,
        "sample_project_index": sample_project_index,
        "field_evidence_candidates": field_evidence_candidates,
        "field_evidence": field_evidence,
        "task_card": task_card,
        "model_config": model_config,
        "numeric_policy": numeric_policy,
        "target_board_profile": target_board_profile,
        "tool_profile": tool_profile,
        "tool_availability": tool_availability,
        "case_adapter": case_adapter,
        "template_library": template_library,
        "template_metadata": template_metadata,
        "design_space": design_space,
        "tool_protocols": tool_protocols,
        "human_agent_boundary": human_boundary,
    }
    for name, data in outputs.items():
        if name not in {"template_library", "template_metadata", "tool_protocols", "human_agent_boundary", "case_adapter"}:
            write_json(input_dir / f"{name}.json", data)

    refs = {name: rel(input_dir / f"{name}.json", run_dir) for name in outputs}
    errors, warnings = validate_inputs(outputs)
    manifest = {
        "schema_version": "spatialaccagent.prepared_inputs.v0",
        "stage": "input_preparation",
        "status": "ready" if not errors else "incomplete",
        "run_dir": str(run_dir),
        "mode": "independent_from_scratch_design",
        "inputs": refs,
        "source_specs": {
            "task_spec": str(args.task_spec.resolve()),
            "model_source": str(model_source),
            "model_dir": str(model_dir),
            "board_materials_dir": str(args.board_materials_dir.resolve()),
            "quantization_materials_dir": str(args.quantization_materials_dir.resolve()),
            "tool_materials_dir": str(args.tool_materials_dir.resolve()),
            "template_dir": str(args.template_dir.resolve()),
        },
        "source_roles": {
            "task_spec": "run-specific objective and acceptance boundary",
            "model_source": "run-specific model architecture source",
            "model_dir": "run-specific target checkpoint directory",
            "quantization_materials_dir": "current-run numeric and quantization design materials",
            "board_materials_dir": "current-run target FPGA board, DDR/AXI, runtime, and sample-project materials",
            "tool_materials_dir": "current-run EDA tool location, usage, and limitation materials",
            "template_dir": "trusted local hardware template library",
        },
        "summary": {
            "model_type": model_config.get("model_type"),
            "operator_count": len(model_config.get("block", {}).get("operator_sequence", [])),
            "template_count": len(template_metadata.get("templates", [])),
            "tool_protocols": len(tool_protocols.get("tools", [])),
            "llm_mode": llm_mode(),
            "llm_provider": resolved_llm_cfg().provider,
        },
        "errors": errors,
        "warnings": warnings,
    }
    pseudo_state = {
        "design_id": "stage0_input_preparation",
        "constraints": [
            {"id": "constraint.task.goal", "type": "task"},
            {"id": "constraint.model.decoder", "type": "model"},
            {"id": "constraint.shape.model", "type": "shape"},
            {"id": "constraint.numeric.policy", "type": "numeric"},
            {"id": "constraint.template.library", "type": "template"},
            {"id": "constraint.arch.design_space", "type": "architecture"},
            {"id": "constraint.deployment.board", "type": "deployment"},
            {"id": "constraint.memory.board", "type": "memory"},
            {"id": "constraint.runtime.board", "type": "runtime"},
            {"id": "constraint.tool.protocols", "type": "tool"},
            {"id": "constraint.human.boundary", "type": "human_boundary"},
        ],
        "artifacts": [{"id": f"artifact.input.{name}", "type": "input"} for name in outputs],
        "nodes": [],
        "edges": [],
        "invariants": [],
    }
    team = run_design_team(
        stage="input_preparation",
        objective="Prepare and audit model, numeric, template, board, tool, and human-boundary inputs for SACG extraction.",
        state=pseudo_state,
        candidate_artifact={"prepared_inputs": manifest, "outputs": outputs},
        out_dir=input_dir,
    )
    manifest["design_team"] = team_summary(team)
    errors.extend(team_failure_errors(manifest["design_team"]))
    manifest["errors"] = errors
    manifest["status"] = "ready" if not errors else "incomplete"
    manifest_path = input_dir / "prepared_inputs.json"
    write_json(manifest_path, manifest)
    return manifest_path, manifest


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Independent input preparation stage")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--task-spec", type=Path, required=True)
    parser.add_argument("--model-source", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--template-dir", type=Path, default=DEFAULT_TEMPLATE_DIR)
    parser.add_argument("--board-materials-dir", type=Path, default=DEFAULT_BOARD_MATERIALS_DIR)
    parser.add_argument("--quantization-materials-dir", type=Path, default=DEFAULT_QUANTIZATION_MATERIALS_DIR)
    parser.add_argument("--tool-materials-dir", type=Path, default=DEFAULT_TOOL_MATERIALS_DIR)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        manifest_path, manifest = prepare_inputs(args)
        if manifest["errors"]:
            for error in manifest["errors"]:
                print(f"error: {error}", file=sys.stderr)
            print(manifest_path)
            return 1
        print(manifest_path)
        return 0
    except (OSError, InputPreparationError, ConfigError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
