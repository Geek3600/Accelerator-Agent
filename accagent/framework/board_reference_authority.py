"""Hash-bound semantic artifacts required by exact board simulation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from accagent.framework.board_validation_scope import (
    BoardValidationScope,
    BoardValidationScopeError,
    resolve_board_validation_scope,
)
from accagent.framework.board_reference_output import (
    BoardReferenceOutputError,
    select_board_reference_output,
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _resolve_file(raw_path: Any, base_dir: Path) -> Path:
    path = Path(str(raw_path or "")).expanduser()
    return (path if path.is_absolute() else base_dir / path).resolve()


def _verified_artifact(
    row: Any,
    *,
    label: str,
    hash_field: str,
    base_dir: Path,
    blockers: list[str],
) -> dict[str, Any]:
    if not isinstance(row, dict):
        blockers.append(f"{label} is missing")
        return {}
    path = _resolve_file(row.get("path"), base_dir)
    expected_hash = str(row.get(hash_field) or "").lower()
    if not path.is_file():
        blockers.append(f"{label} file is missing: {path}")
        return {}
    actual_hash = _sha256_file(path)
    if expected_hash != actual_hash:
        blockers.append(f"{label} file hash does not match its manifest")
    result = {
        key: row.get(key)
        for key in (
            "path",
            "sha256",
            "file_sha256",
            "tensor_sha256",
            "shape",
            "tensor_shape",
            "dtype",
            "encoding",
            "bits",
            "lanes",
            "beats",
            "scope",
            "target_layer_count",
            "source_capture",
            "source_tensor_path",
            "source_tensor_file_sha256",
            "source_tensor_sha256",
            "reference_kind",
        )
        if key in row
    }
    result["path"] = str(path)
    result[hash_field] = actual_hash
    return result


def semantic_board_reference_artifacts(run_dir: Path) -> tuple[dict[str, Any], list[str]]:
    """Bind existing board vectors to their independently executed model tensors."""

    run_dir = run_dir.resolve()
    semantic_path = (
        run_dir / "verification" / "semantic_testbench" / "semantic_testbench_manifest.json"
    )
    reference_path = (
        run_dir / "verification" / "model_reference" / "reference_manifest.json"
    )
    reference_report_path = (
        run_dir / "verification" / "real_tools" / "case_target_model_reference.json"
    )
    catalog_path = (
        run_dir
        / "verification"
        / "model_weights"
        / "transformer_block_weight_catalog.json"
    )
    task_card_path = run_dir / "input" / "task_card.json"
    model_path = run_dir / "input" / "model_config.json"
    semantic = _read_json(semantic_path)
    reference = _read_json(reference_path)
    reference_report = _read_json(reference_report_path)
    catalog = _read_json(catalog_path)
    board = semantic.get("board") if isinstance(semantic.get("board"), dict) else {}
    blockers: list[str] = []
    resolved_scope: BoardValidationScope | None = None
    try:
        resolved_scope = resolve_board_validation_scope(
            _read_json(task_card_path), _read_json(model_path)
        )
        scope = resolved_scope.as_dict()
    except BoardValidationScopeError:
        # Keep isolated artifact tests and historical full-model evidence readable.
        declared_layers = int(board.get("expected_target_layers") or catalog.get("target_layer_count") or 0)
        scope = {
            "model_layer_count": int(catalog.get("target_layer_count") or declared_layers),
            "validation_layer_count": declared_layers,
            "validation_layer_indices": list(range(declared_layers)),
            "reference_output_layer_index": max(0, declared_layers - 1),
        }

    if semantic.get("status") != "ready" or semantic.get("blockers") not in ([], None):
        blockers.append("semantic testbench manifest is not ready")
    produced_reference = [
        row
        for row in reference_report.get("produced_reports", [])
        if isinstance(row, dict)
        and Path(str(row.get("path") or "")).resolve() == reference_path
        and row.get("status") == "ready"
    ]
    if reference_report.get("status") != "pass" or len(produced_reference) != 1:
        blockers.append("target-model reference real-tool execution has not passed")

    reference_value = (
        reference.get("reference")
        if isinstance(reference.get("reference"), dict)
        else {}
    )
    board_input = _verified_artifact(
        board.get("input_vector"),
        label="board input artifact",
        hash_field="sha256",
        base_dir=semantic_path.parent,
        blockers=blockers,
    )
    board_expected = _verified_artifact(
        board.get("expected_output"),
        label="board expected-output artifact",
        hash_field="sha256",
        base_dir=semantic_path.parent,
        blockers=blockers,
    )
    tensor_input = _verified_artifact(
        reference.get("input"),
        label="target-model input tensor",
        hash_field="file_sha256",
        base_dir=reference_path.parent,
        blockers=blockers,
    )
    try:
        expected_reference = (
            select_board_reference_output(reference, resolved_scope)
            if resolved_scope is not None
            else (
                reference_value.get("full_model_output")
                if scope["validation_layer_count"] == scope["model_layer_count"]
                else reference_value.get("single_layer_output")
            )
        )
    except BoardReferenceOutputError as exc:
        blockers.append(str(exc))
        expected_reference = {}
    tensor_expected = _verified_artifact(
        expected_reference,
        label="target-model expected-output tensor",
        hash_field="file_sha256",
        base_dir=reference_path.parent,
        blockers=blockers,
    )

    semantic_input = semantic.get("random_input")
    if not isinstance(semantic_input, dict) or any(
        semantic_input.get(key) != reference.get("input", {}).get(key)
        for key in ("path", "file_sha256", "tensor_sha256", "shape", "dtype")
    ):
        blockers.append("semantic testbench input does not bind the target-model reference input")
    if board_input.get("tensor_shape") != tensor_input.get("shape"):
        blockers.append("board input shape does not match the target-model input tensor")
    if board_expected.get("tensor_shape") != tensor_expected.get("shape"):
        blockers.append("board expected-output shape does not match the target-model output tensor")
    if resolved_scope is not None and (
        board_expected.get("source_capture") != expected_reference.get("source_capture")
        or board_expected.get("source_tensor_path") != expected_reference.get("path")
        or board_expected.get("source_tensor_file_sha256")
        != expected_reference.get("file_sha256")
        or board_expected.get("source_tensor_sha256")
        != expected_reference.get("tensor_sha256")
    ):
        blockers.append("board expected-output provenance does not match the validation-scope reference capture")
    if reference_value.get("independent_of_rtl") is not True:
        blockers.append("target-model expected output is not declared independent of RTL")
    if reference_value.get("expected_output_source") != "target_model_inference":
        blockers.append("target-model expected output was not produced by model inference")

    semantic_weights = (
        semantic.get("real_weight_source")
        if isinstance(semantic.get("real_weight_source"), dict)
        else {}
    )
    reference_weights = (
        reference_value.get("real_weight_source")
        if isinstance(reference_value.get("real_weight_source"), dict)
        else {}
    )
    checkpoint_hashes = {
        str(value)
        for value in (
            catalog.get("source_checkpoint_sha256"),
            semantic_weights.get("source_checkpoint_sha256"),
            reference_weights.get("source_checkpoint_sha256"),
        )
        if value
    }
    if len(checkpoint_hashes) != 1:
        blockers.append("checkpoint identity is missing or inconsistent across board reference artifacts")
    checkpoint_sha256 = next(iter(checkpoint_hashes), "")

    target_layers = int(board.get("expected_target_layers") or 0)
    if (
        target_layers != scope["validation_layer_count"]
        or board.get("validation_layer_indices", scope["validation_layer_indices"])
        != scope["validation_layer_indices"]
        or (scope["validation_layer_count"] == scope["model_layer_count"]
            and board.get("all_target_layer_reference_captured") is not True)
        or (scope["validation_layer_count"] != scope["model_layer_count"]
            and board.get("scoped_layer_reference_captured") is not True)
        or int(catalog.get("target_layer_count") or 0) != scope["model_layer_count"]
    ):
        blockers.append("board reference artifacts do not match the validation scope and complete model catalog")

    numeric_path = _resolve_file(semantic.get("numeric_policy"), run_dir)
    numeric_sha256 = str(semantic.get("numeric_policy_sha256") or "").lower()
    if (
        not numeric_path.is_file()
        or _sha256_file(numeric_path) != numeric_sha256
        or reference_value.get("numeric_policy_sha256") != numeric_sha256
    ):
        blockers.append("numeric policy identity is missing or inconsistent")

    authority = {
        "schema_version": "spatialaccagent.semantic_board_reference_artifacts.v1",
        "status": "ready" if not blockers else "incomplete",
        "blockers": blockers,
        "accelerator_scope": semantic.get("accelerator_scope"),
        "model_layer_count": scope["model_layer_count"],
        "target_layer_count": target_layers,
        "validation_layer_indices": scope["validation_layer_indices"],
        "reference_output_layer_index": scope["reference_output_layer_index"],
        "source_checkpoint_sha256": checkpoint_sha256,
        "semantic_testbench_manifest": {
            "path": str(semantic_path),
            "sha256": _sha256_file(semantic_path) if semantic_path.is_file() else None,
        },
        "target_model_reference_manifest": {
            "path": str(reference_path),
            "sha256": _sha256_file(reference_path) if reference_path.is_file() else None,
        },
        "target_model_reference_execution": {
            "path": str(reference_report_path),
            "sha256": (
                _sha256_file(reference_report_path)
                if reference_report_path.is_file()
                else None
            ),
            "status": reference_report.get("status"),
        },
        "numeric_policy": {
            "path": str(numeric_path),
            "sha256": numeric_sha256,
            "comparison": semantic.get("numeric_comparison_policy"),
        },
        "board_input_artifact": {
            **board_input,
            "source_tensor": tensor_input,
        },
        "board_expected_output_artifact": {
            **board_expected,
            "source_tensor": tensor_expected,
        },
        "policy": {
            "board_memh_artifacts_are_the_vcs_runtime_files": True,
            "source_tensors_are_read_only_semantic_provenance": True,
            "expected_output_is_target_model_inference": True,
            "expected_output_is_independent_of_rtl": True,
            "rtl_output_must_never_replace_expected_output": True,
        },
    }
    authority["contract_sha256"] = _canonical_sha256(authority)
    return authority, blockers
