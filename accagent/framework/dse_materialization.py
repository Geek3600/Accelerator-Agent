"""Checks that DSE candidates reach the generated FPGA implementation inputs."""

from __future__ import annotations

import json
from typing import Any


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
}


def _stable(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def candidate_physical_signature(parameters: dict[str, Any]) -> dict[str, Any]:
    """Return exactly the fields that Stage 5 must materialize in generated RTL."""

    if not isinstance(parameters, dict):
        raise ValueError("DSE candidate parameters must be an object")
    missing = [key for key in PHYSICAL_DSE_KEYS if key not in parameters]
    if missing:
        raise ValueError(f"DSE candidate is missing physical parameters: {missing}")
    return {key: parameters[key] for key in PHYSICAL_DSE_KEYS}


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
