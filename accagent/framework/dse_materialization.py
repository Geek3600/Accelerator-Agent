"""Checks that DSE candidates reach the generated FPGA implementation inputs."""

from __future__ import annotations

import json
import hashlib
import re
from typing import Any
from pathlib import Path


PHYSICAL_DSE_KEYS = (
    "lanes",
    "compute_array_rows",
    "compute_array_cols",
    "fifo_depth",
    "activation_banks",
    "weight_banks_by_role",
)

GENERATED_FIELD_NAMES = {
    "lanes": "GeneratedDesignParams.lanes",
    "compute_array_rows": "GeneratedDesignParams.computeArrayRows",
    "compute_array_cols": "GeneratedDesignParams.computeArrayCols",
    "fifo_depth": "GeneratedDesignParams.fifoDepth",
    "activation_banks": "GeneratedDesignParams.activationBanks",
    "weight_banks_by_role": "GeneratedDesignParams.weightBanksByRole",
    "cross_token_reuse_tokens": "GeneratedDesignParams.crossTokenReuseTokens",
    "attention_output_cross_token_reuse_tokens": "GeneratedDesignParams.attentionOutputCrossTokenReuseTokens",
}

# Template-level prior rules. They intentionally do not inspect candidate hashes.
# These are conservative predictions, not an independently validated oracle.
PARAMETER_MODULE_FAMILIES = {
    "compute_array_rows": ["Linear", "QKVProjection", "DenseFFN", "PhysicalLinear", "WeightTileCache"],
    "compute_array_cols": ["Linear", "QKVProjection", "DenseFFN", "PhysicalLinear", "WeightTileCache"],
    "fifo_depth": ["PhysicalStreamFifo", "PhysicalSimpleDualPortMemory"],
    "activation_banks": ["PhysicalSimpleDualPortMemory"],
    "cross_token_reuse_tokens": ["Linear", "WeightTileCache", "PhysicalLinear"],
    "attention_output_cross_token_reuse_tokens": ["Attention", "Linear", "PhysicalLinear"],
}


def parameter_module_dependencies(parameter: str, filenames: list[str]) -> dict[str, Any]:
    """Declare parameter-to-module-family edges before observing output diffs."""
    prefixes = PARAMETER_MODULE_FAMILIES.get(parameter)
    if prefixes is None:
        raise ValueError(f"no declared module-family rule for {parameter}")
    affected = sorted(name for name in filenames if Path(name).stem.startswith(tuple(prefixes)))
    return {
        "parameter": parameter,
        "module_families": prefixes,
        "predicted_affected": affected,
        "predicted_unrelated": sorted(set(filenames) - set(affected)),
        "edges": [{"src": f"parameter.{parameter}", "dst": f"module.{name}",
                   "kind": "declared_materialization_dependency"} for name in affected],
        "basis": "template_family_prior_without_candidate_hashes",
    }


def _stable(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sv_port_signature(source: str) -> list[dict[str, Any]]:
    """Extract ANSI headers from emitted flat SV; retain raw width expressions.

    This is an interface fingerprint, not a general Verilog type checker.
    VCS remains responsible for resolving module connections and widths.
    """
    text = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)
    modules = []
    for match in re.finditer(r"\bmodule\s+(\w+)\s*\((.*?)\);", text, re.S):
        direction, width, ports = None, "", []
        for chunk in match.group(2).split(","):
            declared = re.match(r"\s*(input|output|inout)\b(.*)", chunk, re.S)
            if declared:
                direction, chunk = declared.groups()
                dimensions = re.findall(r"\[[^\]]+\]", chunk)
                width = "".join(re.sub(r"\s+", "", d) for d in dimensions)
            names = re.findall(r"\b[A-Za-z_]\w*\b", re.sub(r"\[[^\]]+\]", "", chunk))
            if names and direction:
                ports.append({"name": names[-1], "direction": direction, "packed_range": width or "scalar"})
        modules.append({"module": match.group(1), "ports": ports})
    return modules


def build_stage5_sv_manifest(generated_root: Path, parameters: dict[str, Any]) -> dict[str, Any]:
    """Bind a generated SystemVerilog file set to its Stage-4 parameter signature.

    The manifest detects later partial replacement or deletion. It does not
    establish that the recorded files implement the parameter semantics.
    """

    root = Path(generated_root)
    signature = candidate_physical_signature(parameters)
    files = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.glob("*.sv"))
        if path.is_file()
    }
    if not files:
        raise ValueError(f"no generated SystemVerilog files in {root}")
    return {
        "schema_version": "spatialaccagent.stage5_sv_manifest.v1",
        "parameter_signature": signature,
        "parameter_signature_sha256": hashlib.sha256(_stable(signature).encode()).hexdigest(),
        "generated_sv": files,
        "generated_sv_count": len(files),
        "port_signatures": {path.name: sv_port_signature(path.read_text())
                            for path in sorted(root.glob("*.sv")) if path.is_file()},
        "parameter_scala": {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
                            for path in sorted(root.rglob("GeneratedDesignParams.scala"))},
    }


def validate_stage5_sv_manifest(
    generated_root: Path,
    parameters: dict[str, Any],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    """Check exact Stage-5 source membership and hashes against its binding."""

    errors: list[str] = []
    try:
        expected_signature = candidate_physical_signature(parameters)
    except ValueError as exc:
        expected_signature = {}
        errors.append(str(exc))
    observed_signature = manifest.get("parameter_signature")
    signature_sha = hashlib.sha256(_stable(observed_signature).encode()).hexdigest()
    if observed_signature != expected_signature or manifest.get("parameter_signature_sha256") != signature_sha:
        errors.append("Stage-5 manifest parameter signature does not match selected parameters")
    observed_files = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(Path(generated_root).glob("*.sv"))
        if path.is_file()
    }
    expected_files = manifest.get("generated_sv")
    if not isinstance(expected_files, dict):
        expected_files = {}
        errors.append("Stage-5 manifest generated_sv must be an object")
    missing = sorted(set(expected_files) - set(observed_files))
    added = sorted(set(observed_files) - set(expected_files))
    changed = sorted(name for name in set(observed_files) & set(expected_files)
                     if observed_files[name] != expected_files[name])
    if missing or added or changed:
        errors.append(f"Stage-5 SV manifest mismatch: missing={missing}, added={added}, changed={changed}")
    if manifest.get("generated_sv_count") != len(expected_files):
        errors.append("Stage-5 manifest generated_sv_count does not match its file map")
    for relative, expected in manifest.get("parameter_scala", {}).items():
        path = Path(generated_root) / relative
        if not path.resolve().is_relative_to(Path(generated_root).resolve()) or not path.is_file():
            errors.append(f"Stage-5 manifest parameter source missing or outside root: {relative}")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            errors.append(f"Stage-5 manifest parameter source changed: {relative}")
    port_changes = sorted(name for name in set(expected_files) & set(observed_files)
                          if sv_port_signature((Path(generated_root) / name).read_text())
                          != manifest.get("port_signatures", {}).get(name))
    if port_changes:
        errors.append(f"Stage-5 SV interface signature changed: {port_changes}")
    return {
        "schema_version": "spatialaccagent.stage5_sv_manifest_check.v1",
        "status": "pass" if not errors else "fail",
        "expected_file_count": len(expected_files),
        "observed_file_count": len(observed_files),
        "missing_files": missing,
        "added_files": added,
        "changed_files": changed,
        "port_signature_changes": port_changes,
        "errors": errors,
    }


def candidate_physical_signature(parameters: dict[str, Any]) -> dict[str, Any]:
    """Return exactly the fields that Stage 5 must materialize in generated RTL."""

    if not isinstance(parameters, dict):
        raise ValueError("DSE candidate parameters must be an object")
    missing = [key for key in PHYSICAL_DSE_KEYS if key not in parameters]
    if missing:
        raise ValueError(f"DSE candidate is missing physical parameters: {missing}")
    signature = {key: parameters[key] for key in PHYSICAL_DSE_KEYS}
    # Older candidate fixtures predate the reuse binding. Keep them valid, but
    # validate reuse whenever a Stage-4 record supplies it.
    if "cross_token_reuse_tokens" in parameters:
        signature["cross_token_reuse_tokens"] = parameters["cross_token_reuse_tokens"]
    if "attention_output_cross_token_reuse_tokens" in parameters:
        signature["attention_output_cross_token_reuse_tokens"] = parameters[
            "attention_output_cross_token_reuse_tokens"
        ]
    return signature


def validate_candidate_universe(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate the complete candidate set before any QoR measurement.

    This is intentionally a structural gate.  It does not estimate QoR.  It
    proves that every candidate carries all physical dimensions and that a
    declared change cannot silently disappear before Stage 5 code generation.
    """

    errors: list[str] = []
    signatures: dict[str, dict[str, Any]] = {}
    for record in records:
        candidate = str(record.get("candidate_id") or "")
        try:
            signature = candidate_physical_signature(record.get("parameters", {}))
        except ValueError as exc:
            errors.append(f"{candidate or '<missing candidate>'}: {exc}")
            continue
        if not candidate:
            errors.append("candidate is missing candidate_id")
            continue
        signatures[candidate] = signature

    for key in PHYSICAL_DSE_KEYS:
        values = {_stable(signature[key]) for signature in signatures.values()}
        if len(values) > 1:
            missing_binding = [
                candidate
                for candidate, signature in signatures.items()
                if key not in signature
            ]
            if missing_binding:
                errors.append(f"{key} varies but is not bound for {missing_binding}")
    attention_output_values = {
        _stable(signature.get("attention_output_cross_token_reuse_tokens"))
        for signature in signatures.values()
    }
    if len(attention_output_values) > 1 or any(
        isinstance(record.get("parameters"), dict)
        and "attention_output_cross_token_reuse_tokens" in record["parameters"]
        for record in records
    ):
        missing_attention_output_binding = [
            candidate
            for candidate, signature in signatures.items()
            if "attention_output_cross_token_reuse_tokens" not in signature
        ]
        if missing_attention_output_binding:
            errors.append(
                "attention_output_cross_token_reuse_tokens varies or is declared but is not bound for "
                f"{missing_attention_output_binding}"
            )

    return {
        "schema_version": "spatialaccagent.dse_candidate_materialization.v1",
        "status": "pass" if not errors else "fail",
        "candidate_count": len(records),
        "physical_dimensions": list(PHYSICAL_DSE_KEYS),
        "generated_fields": dict(GENERATED_FIELD_NAMES),
        "candidate_signatures": signatures,
        "errors": errors,
        "policy": (
            "Every admitted DSE dimension must be materialized in GeneratedDesignParams and passed into "
            "the FPGA-IP/XPM configuration before exact app-shell QoR measurement."
        ),
    }


def validate_generated_params_source(
    source_text: str,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    """Check the actual generated Scala binding for one selected candidate."""

    signature = candidate_physical_signature(parameters)
    errors: list[str] = []
    expected_lines = {
        "lanes": f"val lanes: Int = {int(signature['lanes'])}",
        "compute_array_rows": f"val computeArrayRows: Int = {int(signature['compute_array_rows'])}",
        "compute_array_cols": f"val computeArrayCols: Int = {int(signature['compute_array_cols'])}",
        "fifo_depth": f"val fifoDepth: Int = {int(signature['fifo_depth'])}",
        "activation_banks": f"val activationBanks: Int = {int(signature['activation_banks'])}",
    }
    if "cross_token_reuse_tokens" in signature:
        expected_lines["cross_token_reuse_tokens"] = (
            f"val crossTokenReuseTokens: Int = {int(signature['cross_token_reuse_tokens'])}"
        )
    if "attention_output_cross_token_reuse_tokens" in signature:
        expected_lines["attention_output_cross_token_reuse_tokens"] = (
            "val attentionOutputCrossTokenReuseTokens: Int = "
            f"{int(signature['attention_output_cross_token_reuse_tokens'])}"
        )
    for key, line in expected_lines.items():
        if line not in source_text:
            errors.append(f"GeneratedDesignParams does not materialize {key}: {line}")

    for key, field in (("weight_banks_by_role", "weightBanksByRole"),):
        if f"val {field}: Map[String, Int] =" not in source_text:
            errors.append(f"GeneratedDesignParams does not declare {field}")

    required_forwarding = (
        "GeneratedDesignParams.fifoDepth",
        "GeneratedDesignParams.activationBanks",
        "GeneratedDesignParams.weightBanksByRole",
    )
    for marker in required_forwarding:
        if marker not in source_text:
            errors.append(f"Generated FPGA-IP configuration does not forward {marker}")
    if "attention_output_cross_token_reuse_tokens" in signature and (
        "PhysicalImplementation.configureAttentionOutputCrossTokenReuse(" not in source_text
    ):
        errors.append(
            "Generated FPGA-IP configuration does not forward "
            "GeneratedDesignParams.attentionOutputCrossTokenReuseTokens"
        )
    for field, value in (
        ("computeArrayRows", signature["compute_array_rows"]),
        ("computeArrayCols", signature["compute_array_cols"]),
    ):
        if (
            f"val {field}: Int = {int(value)}" not in source_text
            and f"{field} = {int(value)}" not in source_text
            and f"{field} = GeneratedDesignParams.{field}" not in source_text
        ):
            errors.append(f"Generated accelerator parameters do not materialize {field}={int(value)}")

    return {
        "schema_version": "spatialaccagent.generated_dse_binding.v1",
        "status": "pass" if not errors else "fail",
        "parameters": signature,
        "generated_fields": dict(GENERATED_FIELD_NAMES),
        "errors": errors,
    }
