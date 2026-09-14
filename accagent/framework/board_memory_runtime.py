"""Evidence-bound board memory/runtime plans for exact board integration.

The LLM owns semantic planning.  This module only validates that the returned
plan is completely bound to current-run artifacts and preserves the mandatory
double-buffered spatial-accelerator runtime mechanisms.
"""

from __future__ import annotations

import ast
import copy
import re
from collections import Counter
from typing import Any

from accagent.framework.board_validation_scope import (
    BoardValidationScopeError,
    validation_scope_from_plan,
)

from accagent.framework.board_acceptance_contract import canonical_contract_sha256
from accagent.framework.board_runtime_image import (
    IMAGE_FORMAT as BOARD_RUNTIME_IMAGE_FORMAT,
    MANIFEST_SCHEMA_VERSION as BOARD_RUNTIME_IMAGE_MANIFEST_VERSION,
)
from accagent.framework.board_weight_image import (
    IMAGE_FORMAT as BOARD_WEIGHT_IMAGE_FORMAT,
    PLAN_SCHEMA_VERSION as BOARD_WORKLOAD_IMAGE_PLAN_VERSION,
)


PLAN_SCHEMA_VERSION = "spatialaccagent.board_memory_runtime_plan.v1"
PLAN_AGENT_ID = "exact_board_memory_runtime_contract_agent"
RUNTIME_IDENTITY_PROJECTION_SCHEMA_VERSION = (
    "spatialaccagent.board_runtime_identity_projection.v1"
)
CURRENT_ARTIFACT_NAMES = {
    "identity",
    "model",
    "catalog",
    "requirements",
    "stage_memory_layout",
    "workload_image",
}
REQUIRED_TRACE_ROLES = {
    "weight_prefetch_start",
    "weight_prefetch_complete",
    "weight_bank_switch",
    "activation_bank_switch",
    "final_writeback_start",
    "final_writeback_complete",
    "runtime_load_start",
    "runtime_load_complete",
}
RUNTIME_TRACE_ROLES = {"runtime_load_start", "runtime_load_complete"}


_ARTIFACT_REF_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "kind": {"type": "string", "enum": ["artifact_ref"]},
        "artifact": {"type": "string", "enum": sorted(CURRENT_ARTIFACT_NAMES)},
        "path": {"type": "string"},
    },
    "required": ["kind", "artifact", "path"],
}

_EXPRESSION_REF_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "symbol": {"type": "string"},
        "artifact": {"type": "string", "enum": sorted(CURRENT_ARTIFACT_NAMES)},
        "path": {"type": "string"},
    },
    "required": ["symbol", "artifact", "path"],
}

_DERIVED_EXPRESSION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "kind": {"type": "string", "enum": ["derived_expression"]},
        "expression": {"type": "string"},
        "refs": {
            "type": "array",
            "minItems": 1,
            "items": _EXPRESSION_REF_SCHEMA,
        },
    },
    "required": ["kind", "expression", "refs"],
}

_BOUND_INTEGER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "resolved_value": {"type": "integer"},
        "source": {
            "oneOf": [_ARTIFACT_REF_SCHEMA, _DERIVED_EXPRESSION_SCHEMA],
        },
    },
    "required": ["resolved_value", "source"],
}

_LAYER_SEGMENT_SCHEMA = {
    "type": "object",
    "additionalProperties": True,
    "properties": {
        "layer_index": {"type": "integer"},
        "byte_offset": {"type": "integer"},
        "byte_count": {"type": "integer"},
        "byte_end_exclusive": {"type": "integer"},
        "tensor_hashes": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "layer_index",
        "byte_offset",
        "byte_count",
        "byte_end_exclusive",
        "tensor_hashes",
    ],
}

_BOARD_WORKLOAD_IMAGE_PLAN_SCHEMA = {
    "type": "object",
    "additionalProperties": True,
    "properties": {
        "schema_version": {
            "type": "string",
            "enum": [BOARD_WORKLOAD_IMAGE_PLAN_VERSION],
        },
        "status": {"type": "string", "enum": ["pass"]},
        "target_layer_count": {"type": "integer"},
        "input_identity": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "transformer_block_weight_catalog_sha256": {"type": "string"},
                "source_checkpoint_sha256": {"type": "string"},
                "connected_weight_stream_contract_sha256": {"type": "string"},
                "stage_weight_layout_contract_sha256s": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "canonical_weight_layout_set_sha256": {"type": "string"},
            },
            "required": [
                "transformer_block_weight_catalog_sha256",
                "source_checkpoint_sha256",
                "connected_weight_stream_contract_sha256",
                "stage_weight_layout_contract_sha256s",
                "canonical_weight_layout_set_sha256",
            ],
        },
        "image": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "format": {"type": "string", "enum": [BOARD_WEIGHT_IMAGE_FORMAT]},
                "word_bits": {"type": "integer", "enum": [32]},
                "byte_order": {"type": "string", "enum": ["little"]},
                "layer_order": {"type": "array", "items": {"type": "integer"}},
                "layer_alignment_bytes": {"type": "integer"},
            },
            "required": [
                "format",
                "word_bits",
                "byte_order",
                "layer_order",
                "layer_alignment_bytes",
            ],
        },
        "memory": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "weight_bank_count": {"type": "integer", "enum": [2]},
                "weight_bank_capacity_bytes": {"type": "integer"},
            },
            "required": ["weight_bank_count", "weight_bank_capacity_bytes"],
        },
        "additional_runtime_fields": {"type": "object", "additionalProperties": True},
    },
    "required": [
        "schema_version",
        "status",
        "target_layer_count",
        "input_identity",
        "image",
        "memory",
    ],
}

_MEMORY_REGION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "region_id": {"type": "string"},
        "purpose": {"type": "string"},
        "axi_interface_ref": {"type": "string"},
        "address_width_bits": {"type": "integer"},
        "data_width_bits": {"type": "integer"},
        "base_address": _BOUND_INTEGER_SCHEMA,
        "size_bytes": _BOUND_INTEGER_SCHEMA,
        "alignment_bytes": _BOUND_INTEGER_SCHEMA,
    },
    "required": [
        "region_id",
        "purpose",
        "axi_interface_ref",
        "address_width_bits",
        "data_width_bits",
        "base_address",
        "size_bytes",
        "alignment_bytes",
    ],
}

_BANK_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "bank_id": {"type": "string"},
        "region_id": {"type": "string"},
        "capacity_bytes": _BOUND_INTEGER_SCHEMA,
    },
    "required": ["bank_id", "region_id", "capacity_bytes"],
}

_RUNTIME_LOADER_ABI_SCHEMA = {
    "type": ["object", "null"],
    "additionalProperties": False,
    "properties": {
        "valid_port": {"type": "string"},
        "ready_port": {"type": "string"},
        "data_port": {"type": "string"},
        "data_width_bits": {"type": "integer"},
        "addr_port": {"type": "string"},
        "addr_width_bits": {"type": "integer"},
        "last_port": {"type": "string"},
    },
    "required": [
        "valid_port",
        "ready_port",
        "data_port",
        "data_width_bits",
        "addr_port",
        "addr_width_bits",
        "last_port",
    ],
}

_RUNTIME_LOADER_PROTOCOL_SCHEMA = {
    "type": ["object", "null"],
    "additionalProperties": False,
    "properties": {
        "ready_valid_acceptance": {"type": "boolean"},
        "address_start": {"type": "integer"},
        "address_increment": {"type": "integer"},
        "data_word_bits": {"type": "integer"},
        "last_on_final_accepted_word": {"type": "boolean"},
        "complete_before_kernel_start": {"type": "boolean"},
    },
    "required": [
        "ready_valid_acceptance",
        "address_start",
        "address_increment",
        "data_word_bits",
        "last_on_final_accepted_word",
        "complete_before_kernel_start",
    ],
}

_RUNTIME_LOAD_SCHEDULE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "layer_index": {"type": "integer"},
        "segment_id": {"type": "string"},
        "byte_offset": {"type": "integer"},
        "byte_count": {"type": "integer"},
        "word_offset": {"type": "integer"},
        "word_count": {"type": "integer"},
        "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "loader_address_start": {"type": "integer"},
        "loader_address_count": {"type": "integer"},
        "last_word_address": {"type": "integer"},
        "complete_before_kernel_start": {"type": "boolean"},
    },
    "required": [
        "layer_index",
        "segment_id",
        "byte_offset",
        "byte_count",
        "word_offset",
        "word_count",
        "sha256",
        "loader_address_start",
        "loader_address_count",
        "last_word_address",
        "complete_before_kernel_start",
    ],
}

_RUNTIME_CONSTANTS_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "enabled": {"type": "boolean"},
        "region_id": {"type": ["string", "null"]},
        "connected_runtime_stream_contract_sha256": {
            "type": ["string", "null"],
            "pattern": "^[0-9a-f]{64}$",
        },
        "loader_abi": _RUNTIME_LOADER_ABI_SCHEMA,
        "loader_protocol": _RUNTIME_LOADER_PROTOCOL_SCHEMA,
        "load_schedule": {
            "type": "array",
            "items": _RUNTIME_LOAD_SCHEDULE_SCHEMA,
        },
        "trace_point_ids": {"type": "array", "items": {"type": "string"}},
        "full_runtime_image_manifest": {
            "type": "object",
            "additionalProperties": True,
        },
        "materialized_projection": {
            "type": "object",
            "additionalProperties": True,
        },
    },
    "required": [
        "enabled",
        "region_id",
        "connected_runtime_stream_contract_sha256",
        "loader_abi",
        "loader_protocol",
        "load_schedule",
        "trace_point_ids",
    ],
}


BOARD_MEMORY_RUNTIME_PLAN_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "schema_version": {"type": "string", "enum": [PLAN_SCHEMA_VERSION]},
        "agent": {"type": "string", "enum": [PLAN_AGENT_ID]},
        "status": {"type": "string", "enum": ["ready", "blocked"]},
        "summary": {"type": "string"},
        "blocked_reasons": {"type": "array", "items": {"type": "string"}},
        "input_bindings": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                name: {"type": "string", "pattern": "^[0-9a-f]{64}$"}
                for name in (
                    "exact_board_identity_sha256",
                    "target_model_sha256",
                    "transformer_block_catalog_sha256",
                    "dut_weight_requirements_sha256",
                    "stage_memory_layout_sha256",
                    "compute_slot_abi_sha256",
                    "control_abi_sha256",
                    "timing_contract_sha256",
                    "axi_interfaces_sha256",
                )
            },
            "required": [
                "exact_board_identity_sha256",
                "target_model_sha256",
                "transformer_block_catalog_sha256",
                "dut_weight_requirements_sha256",
                "stage_memory_layout_sha256",
                "compute_slot_abi_sha256",
                "control_abi_sha256",
                "timing_contract_sha256",
                "axi_interfaces_sha256",
            ],
        },
        "workload_image": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "image_plan": _BOARD_WORKLOAD_IMAGE_PLAN_SCHEMA,
                "region_id": {"type": "string"},
                "semantic_refs": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "layer_alignment_bytes": _BOUND_INTEGER_SCHEMA,
                        "weight_bank_capacity_bytes": _BOUND_INTEGER_SCHEMA,
                    },
                    "required": [
                        "layer_alignment_bytes",
                        "weight_bank_capacity_bytes",
                    ],
                },
                "full_weight_image_manifest": {
                    "type": "object",
                    "additionalProperties": True,
                },
                "materialized_projection": {
                    "type": "object",
                    "additionalProperties": True,
                },
            },
            "required": ["image_plan", "region_id", "semantic_refs"],
        },
        "memory_regions": {"type": "array", "items": _MEMORY_REGION_SCHEMA},
        "physical_cfg_bindings": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "binding_id": {"type": "string"},
                    "runtime_role": {"type": "string"},
                    "binding_mode": {"type": "string", "enum": ["program", "observe"]},
                    "field_id": {"type": "string"},
                    "fact_port_id": {"type": "string"},
                    "register": {"type": "string"},
                    "bit_offset": {"type": "integer"},
                    "width_bits": {"type": "integer"},
                    "access": {"type": "string"},
                    "reset_value": {"type": "integer"},
                    "value": _BOUND_INTEGER_SCHEMA,
                },
                "required": [
                    "binding_id",
                    "runtime_role",
                    "binding_mode",
                    "field_id",
                    "fact_port_id",
                    "register",
                    "bit_offset",
                    "width_bits",
                    "access",
                    "reset_value",
                    "value",
                ],
            },
        },
        "programming_sequence": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "clock_domain": {"type": "string"},
                "enforcement": {"type": "string"},
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "order": {"type": "integer"},
                            "event": {"type": "string"},
                            "fact_port_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["order", "event", "fact_port_ids"],
                    },
                },
            },
            "required": ["clock_domain", "enforcement", "steps"],
        },
        "runtime_constants": _RUNTIME_CONSTANTS_SCHEMA,
        "weight_double_buffer": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "bank_count": {"type": "integer", "enum": [2]},
                "initial_layer_index": {"type": "integer"},
                "initial_bank_id": {"type": "string"},
                "banks": {"type": "array", "items": _BANK_SCHEMA},
                "ownership_protocol": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "single_compute_owner": {"type": "boolean"},
                        "inactive_bank_prefetch_only": {"type": "boolean"},
                        "prefetch_completion_before_switch": {"type": "boolean"},
                        "atomic_switch": {"type": "boolean"},
                    },
                    "required": [
                        "single_compute_owner",
                        "inactive_bank_prefetch_only",
                        "prefetch_completion_before_switch",
                        "atomic_switch",
                    ],
                },
                "layer_schedule": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "layer_index": {"type": "integer"},
                            "compute_bank_id": {"type": "string"},
                            "prefetch_layer_index": {"type": ["integer", "null"]},
                            "prefetch_bank_id": {"type": ["string", "null"]},
                            "prefetch_overlaps_compute": {"type": "boolean"},
                            "switch_is_atomic": {"type": "boolean"},
                        },
                        "required": [
                            "layer_index",
                            "compute_bank_id",
                            "prefetch_layer_index",
                            "prefetch_bank_id",
                            "prefetch_overlaps_compute",
                            "switch_is_atomic",
                        ],
                    },
                },
                "trace_point_ids": {"type": "array", "items": {"type": "string"}},
            },
            "required": [
                "bank_count",
                "initial_layer_index",
                "initial_bank_id",
                "banks",
                "ownership_protocol",
                "layer_schedule",
                "trace_point_ids",
            ],
        },
        "activation_ping_pong": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "bank_count": {"type": "integer", "enum": [2]},
                "required_activation_bytes": _BOUND_INTEGER_SCHEMA,
                "banks": {"type": "array", "items": _BANK_SCHEMA},
                "input_load": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "source_region_id": {"type": "string"},
                        "destination_bank_id": {"type": "string"},
                        "complete_before_start": {"type": "boolean"},
                    },
                    "required": [
                        "source_region_id",
                        "destination_bank_id",
                        "complete_before_start",
                    ],
                },
                "layer_schedule": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "layer_index": {"type": "integer"},
                            "read_bank_id": {"type": "string"},
                            "write_bank_id": {"type": "string"},
                            "external_writeback": {"type": "boolean"},
                        },
                        "required": [
                            "layer_index",
                            "read_bank_id",
                            "write_bank_id",
                            "external_writeback",
                        ],
                    },
                },
                "trace_point_ids": {"type": "array", "items": {"type": "string"}},
            },
            "required": [
                "bank_count",
                "required_activation_bytes",
                "banks",
                "input_load",
                "layer_schedule",
                "trace_point_ids",
            ],
        },
        "final_writeback": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "enabled": {"type": "boolean"},
                "only_final_layer": {"type": "boolean"},
                "layer_index": {"type": "integer"},
                "source_activation_bank_id": {"type": "string"},
                "destination_region_id": {"type": "string"},
                "starts_after_final_layer_completion": {"type": "boolean"},
                "trace_point_ids": {"type": "array", "items": {"type": "string"}},
            },
            "required": [
                "enabled",
                "only_final_layer",
                "layer_index",
                "source_activation_bank_id",
                "destination_region_id",
                "starts_after_final_layer_completion",
                "trace_point_ids",
            ],
        },
        "trace_points": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "trace_id": {"type": "string"},
                    "role": {"type": "string", "enum": sorted(REQUIRED_TRACE_ROLES)},
                    "clock_domain": {"type": "string"},
                    "condition": {"type": "string"},
                    "observed_fields": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["trace_id", "role", "clock_domain", "condition", "observed_fields"],
            },
        },
    },
    "required": [
        "schema_version",
        "agent",
        "status",
        "summary",
        "blocked_reasons",
        "input_bindings",
        "workload_image",
        "memory_regions",
        "physical_cfg_bindings",
        "programming_sequence",
        "runtime_constants",
        "weight_double_buffer",
        "activation_ping_pong",
        "final_writeback",
        "trace_points",
    ],
}


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _parse_int(value: Any) -> int:
    if _is_int(value):
        return value
    if isinstance(value, str):
        return int(value, 0)
    raise ValueError(f"not an integer: {value!r}")


def _rows(value: Any) -> list[dict[str, Any]]:
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []


def _values(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _hash(value: Any) -> str:
    return canonical_contract_sha256(value)


def board_runtime_identity_projection(identity: dict[str, Any]) -> dict[str, Any]:
    """Return the exact board facts that can change a memory/runtime plan.

    Discovery records, prompt paths, evidence packaging, and other audit-only
    fields remain part of the full board identity used by generation and
    preflight, but do not invalidate an otherwise identical runtime plan.
    """

    identity = identity if isinstance(identity, dict) else {}
    abi = (
        identity.get("compute_slot_abi", {})
        if isinstance(identity.get("compute_slot_abi"), dict)
        else {}
    )
    control = (
        abi.get("control_abi", {})
        if isinstance(abi.get("control_abi"), dict)
        else {}
    )
    timing = (
        identity.get("timing_contract", {})
        if isinstance(identity.get("timing_contract"), dict)
        else {}
    )
    axi = (
        identity.get("axi_interfaces", [])
        if isinstance(identity.get("axi_interfaces"), list)
        else []
    )
    return {
        "schema_version": RUNTIME_IDENTITY_PROJECTION_SCHEMA_VERSION,
        "source_identity_schema_version": identity.get("schema_version"),
        "status": identity.get("status"),
        "exact_user_sample_wrapper": identity.get("exact_user_sample_wrapper"),
        "top_module": identity.get("top_module"),
        "wrapper_top_module": identity.get("wrapper_top_module"),
        "simulation_fileset_top_module": identity.get(
            "simulation_fileset_top_module"
        ),
        "selected_simulation_source_closure_sha256": identity.get(
            "selected_simulation_source_closure_sha256"
        ),
        "compute_slot_abi_sha256": _hash(abi),
        "control_abi_sha256": _hash(control),
        "timing_contract_sha256": _hash(timing),
        "axi_interfaces_sha256": _hash(axi),
        "compute_slot_abi": copy.deepcopy(abi),
        "timing_contract": copy.deepcopy(timing),
        "axi_interfaces": copy.deepcopy(axi),
    }


def _schema_type_matches(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": _is_int(value),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }.get(expected, True)


def _validate_schema_shape(
    value: Any,
    schema: dict[str, Any],
    label: str,
    errors: list[str],
) -> None:
    alternatives = schema.get("oneOf")
    if isinstance(alternatives, list):
        matched = 0
        for alternative in alternatives:
            candidate_errors: list[str] = []
            if isinstance(alternative, dict):
                _validate_schema_shape(value, alternative, label, candidate_errors)
            if not candidate_errors:
                matched += 1
        if matched != 1:
            errors.append(f"{label} must match exactly one allowed schema alternative")
        return
    expected_type = schema.get("type")
    expected_types = expected_type if isinstance(expected_type, list) else [expected_type]
    expected_types = [item for item in expected_types if isinstance(item, str)]
    if expected_types and not any(_schema_type_matches(value, item) for item in expected_types):
        errors.append(f"{label} has the wrong JSON type")
        return
    if "enum" in schema and value not in schema.get("enum", []):
        errors.append(f"{label} is not an allowed value")
    pattern = schema.get("pattern")
    if isinstance(pattern, str) and isinstance(value, str) and re.fullmatch(pattern, value) is None:
        errors.append(f"{label} does not match the required pattern")
    if isinstance(value, dict):
        properties = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{label}.{key} is required")
        if schema.get("additionalProperties") is False:
            for key in sorted(set(value) - set(properties)):
                errors.append(f"{label}.{key} is not an allowed field")
        for key, child in properties.items():
            if key in value and isinstance(child, dict):
                _validate_schema_shape(value[key], child, f"{label}.{key}", errors)
    elif isinstance(value, list):
        minimum = schema.get("minItems")
        if _is_int(minimum) and len(value) < minimum:
            errors.append(f"{label} has fewer than {minimum} items")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                _validate_schema_shape(item, item_schema, f"{label}[{index}]", errors)


def _json_pointer(value: Any, pointer: str) -> Any:
    if pointer == "":
        return value
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise ValueError("JSON pointer must be empty or start with '/'")
    current = value
    for raw_token in pointer[1:].split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            if token not in current:
                raise KeyError(token)
            current = current[token]
        elif isinstance(current, list):
            if not token.isdigit() or int(token) >= len(current):
                raise KeyError(token)
            current = current[int(token)]
        else:
            raise KeyError(token)
    return current


_BINARY_OPS = {
    ast.Add: lambda left, right: left + right,
    ast.Sub: lambda left, right: left - right,
    ast.Mult: lambda left, right: left * right,
    ast.FloorDiv: lambda left, right: left // right,
    ast.Mod: lambda left, right: left % right,
    ast.LShift: lambda left, right: left << right,
    ast.RShift: lambda left, right: left >> right,
    ast.BitAnd: lambda left, right: left & right,
    ast.BitOr: lambda left, right: left | right,
}
_UNARY_OPS = {ast.UAdd: lambda value: value, ast.USub: lambda value: -value}


def _eval_integer_expression(expression: str, symbols: dict[str, int]) -> int:
    if not expression or len(expression) > 512:
        raise ValueError("derived expression is empty or too long")
    tree = ast.parse(expression, mode="eval")

    def visit(node: ast.AST, depth: int = 0) -> int:
        if depth > 32:
            raise ValueError("derived expression is too deep")
        if isinstance(node, ast.Expression):
            return visit(node.body, depth + 1)
        if isinstance(node, ast.Constant) and _is_int(node.value):
            return int(node.value)
        if isinstance(node, ast.Name):
            if node.id not in symbols:
                raise ValueError(f"unknown derived-expression symbol: {node.id}")
            return symbols[node.id]
        if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPS:
            left = visit(node.left, depth + 1)
            right = visit(node.right, depth + 1)
            if isinstance(node.op, (ast.FloorDiv, ast.Mod)) and right == 0:
                raise ValueError("division by zero")
            if isinstance(node.op, (ast.LShift, ast.RShift)) and not 0 <= right <= 256:
                raise ValueError("derived-expression shift is out of range")
            return _BINARY_OPS[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
            return _UNARY_OPS[type(node.op)](visit(node.operand, depth + 1))
        raise ValueError(f"unsupported derived-expression syntax: {type(node).__name__}")

    return visit(tree)


def _resolve_bound_integer(
    value: Any,
    label: str,
    roots: dict[str, Any],
    errors: list[str],
    *,
    allowed_artifacts: set[str] | None = None,
) -> int | None:
    if not isinstance(value, dict):
        errors.append(f"{label} must be an evidence-bound integer object")
        return None
    resolved = value.get("resolved_value")
    if not _is_int(resolved):
        errors.append(f"{label}.resolved_value must be an integer")
        return None
    source = value.get("source")
    if not isinstance(source, dict):
        errors.append(f"{label}.source is missing")
        return None
    kind = str(source.get("kind") or "")
    try:
        if kind == "artifact_ref":
            artifact = str(source.get("artifact") or "")
            if artifact not in roots:
                raise ValueError(f"unknown current artifact {artifact!r}")
            if allowed_artifacts is not None and artifact not in allowed_artifacts:
                raise ValueError(f"artifact {artifact!r} is not authoritative for this value")
            expected = _parse_int(_json_pointer(roots[artifact], str(source.get("path") or "")))
        elif kind == "derived_expression":
            refs = _rows(source.get("refs"))
            if not refs:
                raise ValueError("derived_expression.refs is empty")
            symbols: dict[str, int] = {}
            for index, row in enumerate(refs):
                symbol = str(row.get("symbol") or "")
                if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", symbol):
                    raise ValueError(f"refs[{index}].symbol is invalid")
                if symbol in symbols:
                    raise ValueError(f"duplicate symbol {symbol}")
                artifact = str(row.get("artifact") or "")
                if artifact not in roots:
                    raise ValueError(f"unknown current artifact {artifact!r}")
                if allowed_artifacts is not None and artifact not in allowed_artifacts:
                    raise ValueError(f"artifact {artifact!r} is not authoritative for this value")
                symbols[symbol] = _parse_int(
                    _json_pointer(roots[artifact], str(row.get("path") or ""))
                )
            expected = _eval_integer_expression(str(source.get("expression") or ""), symbols)
        else:
            raise ValueError("source.kind must be artifact_ref or derived_expression")
    except (KeyError, TypeError, ValueError, SyntaxError) as exc:
        errors.append(f"{label} cannot be resolved from current artifacts: {exc}")
        return None
    if expected != resolved:
        errors.append(f"{label}.resolved_value {resolved} does not match derived value {expected}")
        return None
    return resolved


def _tensor_hash(row: dict[str, Any]) -> str:
    for key in ("source_slice_sha256", "sha256", "tensor_sha256"):
        value = str(row.get(key) or "").lower()
        if re.fullmatch(r"[0-9a-f]{64}", value):
            return value
    return ""


def _layer_count(model: dict[str, Any], catalog: dict[str, Any]) -> int:
    for value in (
        model.get("num_layers"),
        model.get("num_hidden_layers"),
        model.get("model_shape", {}).get("num_hidden_layers")
        if isinstance(model.get("model_shape"), dict)
        else None,
        catalog.get("target_layer_count"),
    ):
        if _is_int(value) and value > 0:
            return int(value)
    return 0


def _requirement_validation_layer_indices(
    requirements: dict[str, Any],
    model_layer_count: int,
    errors: list[str],
) -> list[int]:
    """Resolve the current board workload declared by semantic requirements.

    Legacy requirements predate explicit board scopes and therefore retain the
    full-model interpretation. New requirements must bind a contiguous prefix
    consistently so a partial board run cannot be validated against all model
    tensors by accident.
    """

    declared = requirements.get("board_validation_scope")
    if declared is None:
        return list(range(max(model_layer_count, 0)))
    if not isinstance(declared, dict):
        errors.append("weight requirements board_validation_scope is not an object")
        return []
    indices = declared.get("validation_layer_indices")
    try:
        scope = validation_scope_from_plan(
            {"image": {"layer_order": indices}},
            model_layer_count=model_layer_count,
        )
    except BoardValidationScopeError as exc:
        errors.append(f"weight requirements board_validation_scope is invalid: {exc}")
        return []
    expected_indices = list(scope.layer_indices)
    if declared.get("model_layer_count") != model_layer_count:
        errors.append(
            "weight requirements board_validation_scope model_layer_count differs from the target model"
        )
    if declared.get("validation_layer_count") != len(expected_indices):
        errors.append(
            "weight requirements board_validation_scope validation_layer_count is inconsistent"
        )
    if declared.get("reference_output_layer_index") != expected_indices[-1]:
        errors.append(
            "weight requirements board_validation_scope reference_output_layer_index is inconsistent"
        )
    if declared.get("covers_full_model") is not scope.covers_full_model:
        errors.append(
            "weight requirements board_validation_scope covers_full_model is inconsistent"
        )
    if (
        declared.get("requires_next_layer_prefetch")
        is not scope.requires_next_layer_prefetch
    ):
        errors.append(
            "weight requirements board_validation_scope requires_next_layer_prefetch is inconsistent"
        )
    return expected_indices


def _full_image_authority(
    workload: dict[str, Any], requirements: dict[str, Any]
) -> dict[str, Any]:
    candidates = [
        workload.get("full_weight_image_manifest"),
        requirements.get("full_weight_image_manifest"),
        requirements.get("board_workload_image"),
        requirements.get("workload_image"),
    ]
    board_inputs = requirements.get("board_memory_runtime_inputs")
    if isinstance(board_inputs, dict):
        candidates.append(board_inputs.get("full_weight_image_manifest"))
    if (
        requirements.get("scope_coverage_complete") is True
        and isinstance(requirements.get("layer_segments"), list)
    ):
        candidates.append(requirements)
    return next((value for value in candidates if isinstance(value, dict)), {})


def _image_value(image: dict[str, Any], key: str) -> Any:
    if key in image:
        return image.get(key)
    nested = image.get("image") if isinstance(image.get("image"), dict) else {}
    aliases = {
        "image_sha256": ("sha256",),
        "total_bytes": ("size_bytes", "byte_count"),
        "image_format": ("format",),
        "word_bits": ("word_bits",),
    }
    for alias in aliases.get(key, (key,)):
        if alias in nested:
            return nested.get(alias)
    return None


def _materialized_projection(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": manifest.get("status"),
        "schema_version": manifest.get("schema_version"),
        "accelerator_scope": manifest.get("accelerator_scope"),
        "scope_coverage_complete": manifest.get("scope_coverage_complete"),
        "source_checkpoint_sha256": manifest.get("source_checkpoint_sha256"),
        "accelerator_weight_catalog_sha256": manifest.get(
            "accelerator_weight_catalog_sha256"
        ),
        "canonical_weight_layout_set_sha256": manifest.get(
            "canonical_weight_layout_set_sha256"
        ),
        "connected_weight_stream_contract_sha256": manifest.get(
            "connected_weight_stream_contract_sha256"
        ),
        "stage_weight_layout_contract_sha256s": manifest.get(
            "stage_weight_layout_contract_sha256s"
        ),
        "target_layer_count": manifest.get("target_layer_count"),
        "tensor_count": manifest.get("packed_tensor_count"),
        "word_bits": manifest.get("word_bits"),
        "byte_order": manifest.get("byte_order"),
        "image_format": manifest.get("image_format"),
        "image_sha256": manifest.get("image_sha256", manifest.get("sha256")),
        "image_path": manifest.get("path"),
        "manifest_path": manifest.get("manifest_path"),
        "manifest_contract_sha256": manifest.get("manifest_contract_sha256"),
        "total_bytes": manifest.get("total_bytes", manifest.get("byte_count")),
        "canonical_layer_bytes": manifest.get("canonical_layer_byte_count"),
        "layer_alignment_bytes": manifest.get("layer_alignment_bytes"),
        "weight_bank_capacity_bytes": manifest.get("weight_bank_capacity_bytes"),
        "layer_order": manifest.get("layer_order"),
        "packed_tensor_hashes": manifest.get("packed_tensor_hashes"),
        "layer_segments": manifest.get("layer_segments"),
    }


def bind_materialized_workload(
    plan: dict[str, Any], manifest: dict[str, Any]
) -> dict[str, Any]:
    """Inject a packer-owned manifest without mutating or reinterpreting it."""

    if not isinstance(plan, dict) or not isinstance(manifest, dict):
        raise TypeError("plan and manifest must be JSON objects")
    bound = copy.deepcopy(plan)
    workload = bound.get("workload_image")
    if not isinstance(workload, dict):
        raise ValueError("plan.workload_image is missing")
    workload["full_weight_image_manifest"] = copy.deepcopy(manifest)
    workload["materialized_projection"] = _materialized_projection(manifest)
    return bound


def _runtime_materialized_projection(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": manifest.get("status"),
        "schema_version": manifest.get("schema_version"),
        "accelerator_scope": manifest.get("accelerator_scope"),
        "scope_coverage_complete": manifest.get("scope_coverage_complete"),
        "capture_contract_sha256": manifest.get("capture_contract_sha256"),
        "source_reference_manifest_sha256": manifest.get(
            "source_reference_manifest_sha256"
        ),
        "semantic_adapter_sha256": manifest.get("semantic_adapter_sha256"),
        "semantic_runtime_contract_sha256": manifest.get(
            "semantic_runtime_contract_sha256"
        ),
        "connected_runtime_stream_contract_sha256": manifest.get(
            "connected_runtime_stream_contract_sha256"
        ),
        "target_layer_count": manifest.get("target_layer_count"),
        "canonical_layer_word_count": manifest.get("canonical_layer_word_count"),
        "word_bits": manifest.get("word_bits"),
        "byte_order": manifest.get("byte_order"),
        "image_format": manifest.get("image_format"),
        "image_path": manifest.get("path"),
        "image_sha256": manifest.get("image_sha256", manifest.get("sha256")),
        "total_bytes": manifest.get("total_bytes", manifest.get("byte_count")),
        "word_count": manifest.get("word_count"),
        "unique_stream_count": manifest.get("unique_stream_count"),
        "unique_segments": manifest.get("unique_segments"),
        "layer_bindings": manifest.get("layer_bindings"),
        "deduplication_policy": manifest.get("deduplication_policy"),
        "manifest_path": manifest.get("manifest_path"),
        "manifest_contract_sha256": manifest.get("manifest_contract_sha256"),
    }


def bind_materialized_runtime_constants(
    plan: dict[str, Any], manifest: dict[str, Any]
) -> dict[str, Any]:
    """Inject a framework-owned full runtime image manifest into an LLM plan."""

    if not isinstance(plan, dict) or not isinstance(manifest, dict):
        raise TypeError("plan and manifest must be JSON objects")
    bound = copy.deepcopy(plan)
    runtime = bound.get("runtime_constants")
    if not isinstance(runtime, dict):
        raise ValueError("plan.runtime_constants is missing")
    runtime["full_runtime_image_manifest"] = copy.deepcopy(manifest)
    runtime["materialized_projection"] = _runtime_materialized_projection(manifest)
    return bound


def _runtime_manifest_authority(
    runtime: dict[str, Any], authority: dict[str, Any] | None, errors: list[str]
) -> dict[str, Any]:
    embedded = runtime.get("full_runtime_image_manifest")
    embedded = embedded if isinstance(embedded, dict) else {}
    authority = authority if isinstance(authority, dict) else {}
    candidates = [
        authority
        if authority.get("schema_version") == BOARD_RUNTIME_IMAGE_MANIFEST_VERSION
        else None,
        authority.get("full_runtime_image_manifest"),
        authority.get("board_runtime_image_manifest"),
    ]
    supplied = next((row for row in candidates if isinstance(row, dict)), {})
    if supplied and embedded and supplied != embedded:
        errors.append(
            "runtime_constants full manifest differs from the framework runtime authority"
        )
    return copy.deepcopy(supplied or embedded)


def _certified_single_layer_binding(
    authority: dict[str, Any] | None, requirements: dict[str, Any]
) -> dict[str, Any]:
    authority = authority if isinstance(authority, dict) else {}
    candidates = [
        authority.get("certified_single_layer_binding"),
        authority.get("single_layer_harness"),
        requirements.get("certified_single_layer_binding"),
        requirements.get("single_layer_harness"),
    ]
    if "interface" in authority:
        candidates.insert(0, authority)
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        nested = candidate.get("single_layer_harness")
        if isinstance(nested, dict):
            candidate = nested
        if isinstance(candidate.get("interface"), dict):
            return candidate
    return {}


def _connected_runtime_contract(
    requirements: dict[str, Any], errors: list[str]
) -> tuple[dict[str, Any], str, int]:
    value = requirements.get("connected_runtime_stream_contract")
    if value in (None, {}):
        return {}, "", 0
    if not isinstance(value, dict):
        errors.append("connected_runtime_stream_contract is not an object")
        return {}, "", 0
    declared_hash = str(value.get("contract_sha256") or "").lower()
    payload = {
        key: child
        for key, child in value.items()
        if key not in {"contract_sha256", "path"}
    }
    if (
        not re.fullmatch(r"[0-9a-f]{64}", declared_hash)
        or _hash(payload) != declared_hash
    ):
        errors.append("certified connected runtime stream contract hash is invalid")
    if value.get("status") != "pass":
        errors.append("certified connected runtime stream contract is not pass")
    if value.get("word_bits") != 32:
        errors.append("certified connected runtime stream must use 32-bit words")
    word_count = value.get("word_count")
    if not _is_int(word_count) or word_count < 0:
        errors.append("certified connected runtime stream word_count is invalid")
        word_count = 0
    stage_rows = _rows(value.get("stage_segments"))
    if word_count > 0 and not stage_rows:
        errors.append("connected runtime stream has no stage segment coverage")
    expected_offset = 0
    seen_stage_ids: set[str] = set()
    for index, row in enumerate(stage_rows):
        stage_id = str(row.get("stage_id") or "")
        stream_range = (
            row.get("global_stream_range")
            if isinstance(row.get("global_stream_range"), dict)
            else {}
        )
        count = stream_range.get("word_count")
        end = stream_range.get("word_end_exclusive")
        if not stage_id or stage_id in seen_stage_ids:
            errors.append(
                f"connected runtime stream stage_segments[{index}] has no unique stage_id"
            )
        seen_stage_ids.add(stage_id)
        if (
            not _is_int(count)
            or count < 0
            or stream_range.get("word_offset") != expected_offset
            or end != expected_offset + int(count or 0)
        ):
            errors.append(
                f"connected runtime stream stage_segments[{index}] range is not contiguous"
            )
            continue
        expected_offset = int(end)
    if stage_rows and expected_offset != word_count:
        errors.append("connected runtime stream stage ranges do not cover word_count")
    return copy.deepcopy(value), declared_hash, int(word_count)


def _validate_certified_runtime_loader(
    binding: dict[str, Any],
    connected: dict[str, Any],
    connected_hash: str,
    connected_word_count: int,
    errors: list[str],
) -> dict[str, Any]:
    if not binding:
        errors.append("certified connected-kernel runtime loader authority is missing")
        return {}
    if binding.get("connected_runtime_stream_contract_sha256") != connected_hash:
        errors.append(
            "certified connected-kernel binding does not bind the runtime stream contract"
        )
    interface = binding.get("interface") if isinstance(binding.get("interface"), dict) else {}
    loader = (
        interface.get("runtime_loader")
        if isinstance(interface.get("runtime_loader"), dict)
        else {}
    )
    required_ports = (
        "valid_port",
        "ready_port",
        "data_port",
        "addr_port",
        "last_port",
    )
    if any(not str(loader.get(name) or "") for name in required_ports):
        errors.append("certified runtime loader is missing a ready/valid/data/address/last port")
    if loader.get("data_width_bits") != 32:
        errors.append("certified runtime loader data width is not 32 bits")
    addr_width = loader.get("addr_width_bits")
    if (
        not _is_int(addr_width)
        or addr_width <= 0
        or connected_word_count > (1 << int(addr_width or 0))
    ):
        errors.append("certified runtime loader address width cannot cover the stream")

    route_contract = (
        binding.get("loader_route_contract")
        if isinstance(binding.get("loader_route_contract"), dict)
        else {}
    )
    routes = _rows(route_contract.get("runtime_routes"))
    expected = {
        str(row.get("stage_id") or ""): copy.deepcopy(row.get("global_stream_range"))
        for row in _rows(connected.get("stage_segments"))
        if isinstance(row.get("global_stream_range"), dict)
        and int(row.get("global_stream_range", {}).get("word_count") or 0) > 0
    }
    actual: dict[str, Any] = {}
    for index, route in enumerate(routes):
        stage_id = str(route.get("stage_id") or "")
        if not stage_id or stage_id in actual:
            errors.append(
                f"certified runtime loader route[{index}] has no unique stage_id"
            )
            continue
        actual[stage_id] = copy.deepcopy(route.get("global_stream_range"))
    if actual != expected:
        errors.append(
            "certified runtime loader routes do not exactly cover the connected runtime stream"
        )
    return copy.deepcopy(loader)


def _normalize_layer_segment(
    row: dict[str, Any], word_bits: int, label: str, errors: list[str]
) -> dict[str, Any] | None:
    layer_index = row.get("layer_index")
    if not _is_int(layer_index):
        errors.append(f"{label}.layer_index must be an integer")
        return None
    bytes_per_word = word_bits // 8 if word_bits > 0 and word_bits % 8 == 0 else 0
    try:
        if all(_is_int(row.get(key)) for key in ("byte_offset", "byte_count")):
            byte_offset = int(row["byte_offset"])
            byte_count = int(row["byte_count"])
        elif bytes_per_word and all(
            _is_int(row.get(key)) for key in ("word_offset", "word_count")
        ):
            byte_offset = int(row["word_offset"]) * bytes_per_word
            byte_count = int(row["word_count"]) * bytes_per_word
        else:
            raise ValueError("byte_offset/byte_count or word_offset/word_count is required")
    except ValueError as exc:
        errors.append(f"{label}: {exc}")
        return None
    byte_end = row.get("byte_end_exclusive", byte_offset + byte_count)
    if not _is_int(byte_end) or byte_end != byte_offset + byte_count:
        errors.append(f"{label}.byte_end_exclusive does not match offset + count")
        return None
    tensor_hashes = [
        str(value).lower() for value in _values(row.get("tensor_hashes")) if str(value)
    ]
    if any(not re.fullmatch(r"[0-9a-f]{64}", value) for value in tensor_hashes):
        errors.append(f"{label}.tensor_hashes contains an invalid SHA-256")
    return {
        **copy.deepcopy(row),
        "layer_index": int(layer_index),
        "byte_offset": byte_offset,
        "byte_count": byte_count,
        "byte_end_exclusive": int(byte_end),
        "tensor_hashes": tensor_hashes,
    }


def _validate_input_bindings(
    plan: dict[str, Any],
    identity: dict[str, Any],
    model: dict[str, Any],
    catalog: dict[str, Any],
    requirements: dict[str, Any],
    stage_memory_layout: dict[str, Any],
    errors: list[str],
) -> dict[str, str]:
    abi = identity.get("compute_slot_abi") if isinstance(identity.get("compute_slot_abi"), dict) else {}
    control = abi.get("control_abi") if isinstance(abi.get("control_abi"), dict) else {}
    timing = identity.get("timing_contract") if isinstance(identity.get("timing_contract"), dict) else {}
    axi = identity.get("axi_interfaces") if isinstance(identity.get("axi_interfaces"), list) else []
    expected = {
        "exact_board_identity_sha256": _hash(
            board_runtime_identity_projection(identity)
        ),
        "target_model_sha256": _hash(model),
        "transformer_block_catalog_sha256": _hash(catalog),
        "dut_weight_requirements_sha256": _hash(requirements),
        "stage_memory_layout_sha256": _hash(stage_memory_layout),
        "compute_slot_abi_sha256": _hash(abi),
        "control_abi_sha256": _hash(control),
        "timing_contract_sha256": _hash(timing),
        "axi_interfaces_sha256": _hash(axi),
    }
    declared_internal = {
        "compute_slot_abi_sha256": identity.get("compute_slot_abi_sha256"),
        "control_abi_sha256": identity.get("control_abi_sha256"),
        "timing_contract_sha256": identity.get("timing_contract_sha256"),
        "axi_interfaces_sha256": identity.get("axi_interfaces_sha256"),
    }
    for name, declared in declared_internal.items():
        if str(declared or "").lower() != expected[name]:
            errors.append(f"identity.{name} does not match its current contract")
    bindings = plan.get("input_bindings") if isinstance(plan.get("input_bindings"), dict) else {}
    for name, value in expected.items():
        if str(bindings.get(name) or "").lower() != value:
            errors.append(f"input_bindings.{name} does not bind the current artifact")
    return expected


def _validate_catalog_and_image(
    workload: dict[str, Any],
    model: dict[str, Any],
    catalog: dict[str, Any],
    requirements: dict[str, Any],
    roots: dict[str, Any],
    errors: list[str],
) -> tuple[dict[str, Any], int, int]:
    model_layer_count = _layer_count(model, catalog)
    if model_layer_count <= 0:
        errors.append("target model layer count is unavailable")
    model_count = next(
        (
            int(value)
            for value in (model.get("num_layers"), model.get("num_hidden_layers"))
            if _is_int(value) and value > 0
        ),
        model_layer_count,
    )
    catalog_count = catalog.get("target_layer_count")
    if not _is_int(catalog_count) or catalog_count != model_layer_count or model_count != model_layer_count:
        errors.append("target model and Transformer-block catalog layer counts differ")
    catalog_rows = _rows(catalog.get("tensors"))
    if (
        catalog.get("status") != "pass"
        or catalog.get("accelerator_scope") != "transformer_blocks_only"
        or catalog.get("scope_coverage_complete") is not True
        or catalog.get("tensor_count") != len(catalog_rows)
    ):
        errors.append("Transformer-block catalog is not complete and pass")
    catalog_by_layer: dict[int, list[str]] = {index: [] for index in range(max(model_layer_count, 0))}
    for index, row in enumerate(catalog_rows):
        layer_index = row.get("layer_index")
        tensor_hash = _tensor_hash(row)
        if not _is_int(layer_index) or layer_index not in catalog_by_layer:
            errors.append(f"catalog.tensors[{index}].layer_index is outside the target model")
            continue
        if not tensor_hash:
            errors.append(f"catalog.tensors[{index}] lacks a valid tensor SHA-256")
            continue
        catalog_by_layer[int(layer_index)].append(tensor_hash)
    if model_layer_count and any(not values for values in catalog_by_layer.values()):
        errors.append("Transformer-block catalog has an empty target layer")
    image_plan = (
        workload.get("image_plan") if isinstance(workload.get("image_plan"), dict) else {}
    )
    plan_identity = (
        image_plan.get("input_identity")
        if isinstance(image_plan.get("input_identity"), dict)
        else {}
    )
    plan_image = image_plan.get("image") if isinstance(image_plan.get("image"), dict) else {}
    plan_memory = (
        image_plan.get("memory") if isinstance(image_plan.get("memory"), dict) else {}
    )
    if (
        image_plan.get("schema_version") != BOARD_WORKLOAD_IMAGE_PLAN_VERSION
        or image_plan.get("status") != "pass"
    ):
        errors.append("workload_image.image_plan is not a pass board workload image plan")
    try:
        validation_scope = validation_scope_from_plan(
            image_plan,
            model_layer_count=model_layer_count,
        )
    except BoardValidationScopeError as exc:
        errors.append(str(exc))
        validation_layer_indices: list[int] = []
        layer_count = 0
    else:
        validation_layer_indices = list(validation_scope.layer_indices)
        layer_count = validation_scope.validation_layer_count
    requirement_layer_indices = _requirement_validation_layer_indices(
        requirements,
        model_layer_count,
        errors,
    )
    if requirement_layer_indices != validation_layer_indices:
        errors.append(
            "weight requirements board validation scope differs from the workload image plan"
        )
    required_rows = _rows(requirements.get("board_required_tensors"))
    required_catalog_hashes = [
        value
        for layer_index in requirement_layer_indices
        for value in catalog_by_layer.get(layer_index, [])
    ]
    if requirements.get("board_required_layer_count") != len(
        requirement_layer_indices
    ):
        errors.append(
            "weight requirements layer count does not match the board validation scope"
        )
    if requirements.get("board_required_tensor_count") != len(
        required_catalog_hashes
    ):
        errors.append(
            "weight requirements tensor count does not match the board validation scope"
        )
    if Counter(_tensor_hash(row) for row in required_rows) != Counter(
        required_catalog_hashes
    ):
        errors.append(
            "weight requirements do not exactly cover the board validation scope catalog hashes"
        )
    if image_plan.get("target_layer_count") != layer_count:
        errors.append("workload image plan target_layer_count differs from the validation scope")
    contract = requirements.get("connected_weight_stream_contract")
    if not isinstance(contract, dict):
        errors.append("certified connected_weight_stream_contract is missing")
        contract = {}
    connected_hash = str(contract.get("contract_sha256") or "").lower()
    connected_payload = {
        key: value for key, value in contract.items() if key not in {"contract_sha256", "path"}
    }
    if not re.fullmatch(r"[0-9a-f]{64}", connected_hash) or _hash(connected_payload) != connected_hash:
        errors.append("certified connected weight stream contract hash is invalid")
    stage_requirements = _rows(requirements.get("stage_requirements"))
    layout_hashes = [
        str(row.get("weight_layout_contract_sha256") or "").lower()
        for row in stage_requirements
    ]
    if not layout_hashes or any(
        not re.fullmatch(r"[0-9a-f]{64}", value) for value in layout_hashes
    ):
        errors.append("weight requirements lack the canonical stage layout hashes")
    layout_set_hash = _hash(
        {"stage_weight_layout_contract_sha256s": layout_hashes}
    )
    expected_plan_identity = {
        "transformer_block_weight_catalog_sha256": requirements.get(
            "accelerator_weight_catalog_sha256"
        ),
        "source_checkpoint_sha256": catalog.get("source_checkpoint_sha256"),
        "connected_weight_stream_contract_sha256": connected_hash,
        "stage_weight_layout_contract_sha256s": layout_hashes,
        "canonical_weight_layout_set_sha256": layout_set_hash,
    }
    for field, expected in expected_plan_identity.items():
        if plan_identity.get(field) != expected:
            errors.append(f"workload image plan input_identity.{field} differs from current evidence")
    if (
        plan_image.get("format") != BOARD_WEIGHT_IMAGE_FORMAT
        or plan_image.get("word_bits") != 32
        or plan_image.get("byte_order") != "little"
        or plan_image.get("layer_order") != validation_layer_indices
    ):
        errors.append("workload image plan format/word order/layer order is not canonical")
    if plan_memory.get("weight_bank_count") != 2:
        errors.append("workload image plan does not declare exactly two weight banks")
    semantic_refs = (
        workload.get("semantic_refs")
        if isinstance(workload.get("semantic_refs"), dict)
        else {}
    )
    alignment = _resolve_bound_integer(
        semantic_refs.get("layer_alignment_bytes"),
        "workload_image.semantic_refs.layer_alignment_bytes",
        roots,
        errors,
        allowed_artifacts={
            "identity",
            "model",
            "catalog",
            "requirements",
            "stage_memory_layout",
        },
    )
    bank_capacity = _resolve_bound_integer(
        semantic_refs.get("weight_bank_capacity_bytes"),
        "workload_image.semantic_refs.weight_bank_capacity_bytes",
        roots,
        errors,
        allowed_artifacts={
            "identity",
            "model",
            "catalog",
            "requirements",
            "stage_memory_layout",
        },
    )
    if alignment != plan_image.get("layer_alignment_bytes"):
        errors.append("image plan layer alignment differs from its current-artifact derivation")
    if bank_capacity != plan_memory.get("weight_bank_capacity_bytes"):
        errors.append("image plan bank capacity differs from its current-artifact derivation")

    authority = _full_image_authority(workload, requirements)
    if not authority:
        errors.append("workload_image.full_weight_image_manifest is missing after materialization")
    declared_manifest_hash = str(authority.get("manifest_contract_sha256") or "").lower()
    manifest_payload = {
        key: value for key, value in authority.items() if key != "manifest_contract_sha256"
    }
    if (
        not re.fullmatch(r"[0-9a-f]{64}", declared_manifest_hash)
        or _hash(manifest_payload) != declared_manifest_hash
    ):
        errors.append("full weight image manifest contract hash is invalid")
    image = _materialized_projection(authority)
    for field in (
        "status",
        "accelerator_scope",
        "scope_coverage_complete",
        "source_checkpoint_sha256",
        "accelerator_weight_catalog_sha256",
        "canonical_weight_layout_set_sha256",
        "target_layer_count",
        "tensor_count",
        "word_bits",
        "byte_order",
        "image_format",
        "image_sha256",
        "total_bytes",
        "canonical_layer_bytes",
        "layer_alignment_bytes",
        "weight_bank_capacity_bytes",
        "layer_order",
        "packed_tensor_hashes",
        "layer_segments",
    ):
        if image.get(field) is None:
            errors.append(f"full weight image manifest is missing {field}")
    supplied_projection = workload.get("materialized_projection")
    if isinstance(supplied_projection, dict) and supplied_projection != image:
        errors.append("workload image materialized projection differs from the injected manifest")
    if authority.get("board_workload_image_plan_sha256") != _hash(image_plan):
        errors.append("full weight image manifest does not bind the exact LLM image plan")
    if authority.get("dut_weight_binding_requirements_sha256") != _hash(requirements):
        errors.append("full weight image manifest does not bind the current requirements")
    if image.get("status") != "pass":
        errors.append("workload_image.status is not pass/ready")
    if (
        image.get("accelerator_scope") != "transformer_blocks_only"
        or image.get("scope_coverage_complete") is not True
    ):
        errors.append("workload image is not complete for Transformer blocks only")
    if image.get("source_checkpoint_sha256") != catalog.get("source_checkpoint_sha256"):
        errors.append("workload image does not bind the catalog checkpoint")
    if image.get("accelerator_weight_catalog_sha256") != requirements.get(
        "accelerator_weight_catalog_sha256"
    ):
        errors.append("workload image does not bind the accelerator catalog artifact")
    selected_catalog_hashes = [
        value for layer in validation_layer_indices for value in catalog_by_layer.get(layer, [])
    ]
    if image.get("target_layer_count") != layer_count or image.get("tensor_count") != len(selected_catalog_hashes):
        errors.append("workload image layer/tensor counts do not match the validation scope")
    if image.get("layer_order") != validation_layer_indices:
        errors.append("workload image layer_order is not the validation scope")
    packed_values = image.get("packed_tensor_hashes")
    packed_hashes = [
        str(value).lower() for value in packed_values
    ] if isinstance(packed_values, list) else []
    if Counter(packed_hashes) != Counter(selected_catalog_hashes):
        errors.append("workload image tensor hashes do not exactly cover the validation scope")

    for field, expected in (
        ("canonical_weight_layout_set_sha256", layout_set_hash),
        ("connected_weight_stream_contract_sha256", connected_hash),
        ("stage_weight_layout_contract_sha256s", layout_hashes),
        ("layer_alignment_bytes", alignment),
        ("weight_bank_capacity_bytes", bank_capacity),
        ("image_format", plan_image.get("format")),
        ("word_bits", plan_image.get("word_bits")),
        ("byte_order", plan_image.get("byte_order")),
        ("layer_order", plan_image.get("layer_order")),
    ):
        if image.get(field) != expected:
            errors.append(f"materialized workload image {field} differs from its plan/authority")
    if not re.fullmatch(r"[0-9a-f]{64}", str(image.get("image_sha256") or "").lower()):
        errors.append("materialized workload image SHA-256 is invalid")

    word_bits = image.get("word_bits")
    if not _is_int(word_bits) or word_bits <= 0 or word_bits % 8:
        errors.append("workload_image.word_bits must be a positive byte multiple")
        word_bits = 0
    contract_word_bits = contract.get("word_bits")
    contract_word_count = contract.get("word_count")
    canonical_layer_bytes = 0
    if (
        not _is_int(contract_word_bits)
        or contract_word_bits <= 0
        or contract_word_bits % 8
        or not _is_int(contract_word_count)
        or contract_word_count <= 0
    ):
        errors.append("certified connected weight stream has invalid word geometry")
    else:
        canonical_layer_bytes = contract_word_bits // 8 * contract_word_count
    if image.get("canonical_layer_bytes") != canonical_layer_bytes:
        errors.append("workload image canonical_layer_bytes differs from the certified kernel stream")
    if not _is_int(alignment) or alignment <= 0 or alignment & (alignment - 1):
        errors.append("workload image layer alignment must be a positive power of two")
        alignment = 1
    total_bytes = image.get("total_bytes")
    if not _is_int(total_bytes) or total_bytes <= 0:
        errors.append("workload_image.total_bytes must be positive")
        total_bytes = 0
    segments = []
    for index, row in enumerate(_rows(image.get("layer_segments"))):
        normalized = _normalize_layer_segment(
            row, int(word_bits), f"workload_image.layer_segments[{index}]", errors
        )
        if normalized is not None:
            segments.append(normalized)
    if len(segments) != layer_count:
        errors.append("workload image does not have exactly one segment per target layer")
    padded_layer_bytes = (
        (canonical_layer_bytes + alignment - 1) // alignment * alignment
        if canonical_layer_bytes > 0 and alignment > 0
        else 0
    )
    expected_offset = 0
    for segment_index, segment in enumerate(segments):
        layer_index = validation_layer_indices[segment_index] if segment_index < len(validation_layer_indices) else -1
        if segment["layer_index"] != layer_index:
            errors.append(f"workload image segment {layer_index} has the wrong layer_index")
        if segment["byte_offset"] != expected_offset:
            errors.append(f"workload image layer {layer_index} offset is not canonical/aligned")
        if segment.get("payload_byte_count") != canonical_layer_bytes:
            errors.append(f"workload image layer {layer_index} payload differs from the certified stream")
        if segment["byte_count"] != padded_layer_bytes:
            errors.append(f"workload image layer {layer_index} padded segment size is not canonical")
        if segment.get("padding_byte_count") != padded_layer_bytes - canonical_layer_bytes:
            errors.append(f"workload image layer {layer_index} padding count is inconsistent")
        if Counter(segment["tensor_hashes"]) != Counter(catalog_by_layer.get(layer_index, [])):
            errors.append(f"workload image layer {layer_index} tensor hashes are incomplete")
        expected_offset = segment["byte_end_exclusive"]
    if segments and total_bytes != segments[-1]["byte_end_exclusive"]:
        errors.append("workload image total_bytes differs from the final layer end")
    materialized_bank_capacity = image.get("weight_bank_capacity_bytes")
    if not _is_int(materialized_bank_capacity) or materialized_bank_capacity < padded_layer_bytes:
        errors.append("workload image weight bank capacity is smaller than one canonical layer")
    image["layer_segments"] = segments
    normalized_workload = copy.deepcopy(workload)
    normalized_workload["board_validation_scope"] = {
        "model_layer_count": model_layer_count,
        "validation_layer_indices": validation_layer_indices,
        "validation_layer_count": layer_count,
    }
    normalized_workload["full_weight_image_manifest"] = copy.deepcopy(authority)
    normalized_workload["materialized_projection"] = image
    return normalized_workload, layer_count, canonical_layer_bytes


def _axi_interfaces(identity: dict[str, Any], errors: list[str]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(_rows(identity.get("axi_interfaces"))):
        keys = {
            str(row.get(field) or "")
            for field in ("interface_id", "fact_interface_id", "name")
            if str(row.get(field) or "")
        }
        if not keys:
            errors.append(f"identity.axi_interfaces[{index}] has no stable identifier")
        for key in keys:
            if key in result and result[key] is not row:
                errors.append(f"AXI interface identifier {key!r} is ambiguous")
            result[key] = row
    if not result:
        errors.append("exact board identity has no AXI interface")
    return result


def _validate_memory_regions(
    plan: dict[str, Any],
    roots: dict[str, Any],
    identity: dict[str, Any],
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    interfaces = _axi_interfaces(identity, errors)
    regions: dict[str, dict[str, Any]] = {}
    intervals: dict[str, list[tuple[int, int, str]]] = {}
    for index, row in enumerate(_rows(plan.get("memory_regions"))):
        label = f"memory_regions[{index}]"
        region_id = str(row.get("region_id") or "")
        if not region_id or region_id in regions:
            errors.append(f"{label}.region_id is missing or duplicated")
            continue
        interface_ref = str(row.get("axi_interface_ref") or "")
        interface = interfaces.get(interface_ref)
        if interface is None:
            errors.append(f"{label}.axi_interface_ref is not an exact discovered interface")
            continue
        address_width = interface.get("address_width_bits")
        data_width = interface.get("data_width_bits")
        if row.get("address_width_bits") != address_width:
            errors.append(f"{label}.address_width_bits differs from the exact AXI interface")
        if row.get("data_width_bits") != data_width:
            errors.append(f"{label}.data_width_bits differs from the exact AXI interface")
        base = _resolve_bound_integer(row.get("base_address"), f"{label}.base_address", roots, errors)
        size = _resolve_bound_integer(row.get("size_bytes"), f"{label}.size_bytes", roots, errors)
        alignment = _resolve_bound_integer(
            row.get("alignment_bytes"), f"{label}.alignment_bytes", roots, errors
        )
        if base is None or size is None or alignment is None:
            continue
        if not _is_int(address_width) or address_width <= 0:
            errors.append(f"{label} exact AXI address width is invalid")
            continue
        if not _is_int(data_width) or data_width <= 0 or data_width % 8:
            errors.append(f"{label} exact AXI data width is invalid")
            continue
        beat_bytes = data_width // 8
        if size <= 0 or base < 0:
            errors.append(f"{label} base/size is invalid")
        if alignment <= 0 or alignment & (alignment - 1) or alignment < beat_bytes:
            errors.append(f"{label} alignment must be a power of two at least one AXI beat")
        elif base % alignment or size % alignment:
            errors.append(f"{label} base and size are not aligned")
        if base + size > 1 << address_width:
            errors.append(f"{label} exceeds the exact AXI address width")
        normalized = {
            **copy.deepcopy(row),
            "resolved_base_address": base,
            "resolved_size_bytes": size,
            "resolved_alignment_bytes": alignment,
        }
        regions[region_id] = normalized
        intervals.setdefault(interface_ref, []).append((base, base + size, region_id))
    for interface_ref, rows in intervals.items():
        ordered = sorted(rows)
        for previous, current in zip(ordered, ordered[1:]):
            if current[0] < previous[1]:
                errors.append(
                    f"memory regions {previous[2]!r} and {current[2]!r} overlap on {interface_ref!r}"
                )
    return regions


def _validate_cfg_bindings(
    plan: dict[str, Any],
    roots: dict[str, Any],
    identity: dict[str, Any],
    errors: list[str],
) -> list[dict[str, Any]]:
    abi = identity.get("compute_slot_abi") if isinstance(identity.get("compute_slot_abi"), dict) else {}
    control = abi.get("control_abi") if isinstance(abi.get("control_abi"), dict) else {}
    fields = _rows(control.get("configuration_fields"))
    field_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    for index, row in enumerate(fields):
        key = (
            str(row.get("field_id") or ""),
            str(row.get("fact_port_id") or ""),
            str(row.get("register") or ""),
        )
        if not all(key) or key in field_by_key:
            errors.append(f"identity configuration field {index} has no unique physical identity")
        field_by_key[key] = row
    seen: set[tuple[str, str, str]] = set()
    seen_binding_ids: set[str] = set()
    normalized = []
    for index, row in enumerate(_rows(plan.get("physical_cfg_bindings"))):
        label = f"physical_cfg_bindings[{index}]"
        binding_id = str(row.get("binding_id") or "")
        if not binding_id or binding_id in seen_binding_ids:
            errors.append(f"{label}.binding_id is missing or duplicated")
        seen_binding_ids.add(binding_id)
        if not str(row.get("runtime_role") or ""):
            errors.append(f"{label}.runtime_role is missing")
        key = (
            str(row.get("field_id") or ""),
            str(row.get("fact_port_id") or ""),
            str(row.get("register") or ""),
        )
        field = field_by_key.get(key)
        if field is None:
            errors.append(f"{label} does not reference an exact discovered physical cfg field")
            continue
        if key in seen:
            errors.append(f"{label} duplicates a physical cfg field")
        seen.add(key)
        for name in ("bit_offset", "width_bits", "access", "reset_value"):
            actual = str(row.get(name)).lower() if name == "access" else row.get(name)
            expected = str(field.get(name)).lower() if name == "access" else field.get(name)
            if actual != expected:
                errors.append(f"{label}.{name} differs from the exact physical cfg field")
        mode = str(row.get("binding_mode") or "")
        access = str(field.get("access") or "").lower()
        if mode == "program" and access not in {"rw", "wo"}:
            errors.append(f"{label} programs a non-writable physical cfg field")
        if mode == "observe" and access not in {"ro", "rw"}:
            errors.append(f"{label} observes a non-readable physical cfg field")
        value = _resolve_bound_integer(row.get("value"), f"{label}.value", roots, errors)
        width = field.get("width_bits")
        if not _is_int(width) or width <= 0:
            errors.append(f"{label} exact physical cfg field width is invalid")
        elif value is not None and (value < 0 or value >= 1 << width):
            errors.append(f"{label}.value does not fit the physical cfg field width")
        normalized.append({**copy.deepcopy(row), "resolved_value": value})
    if seen != set(field_by_key):
        errors.append("physical_cfg_bindings do not exactly cover every discovered configuration field")
    return normalized


def _validate_programming_sequence(
    plan: dict[str, Any], identity: dict[str, Any], errors: list[str]
) -> dict[str, Any]:
    abi = identity.get("compute_slot_abi") if isinstance(identity.get("compute_slot_abi"), dict) else {}
    control = abi.get("control_abi") if isinstance(abi.get("control_abi"), dict) else {}
    sequence = plan.get("programming_sequence")
    if not isinstance(sequence, dict):
        errors.append("programming_sequence is missing")
        return {}
    if sequence.get("clock_domain") != control.get("clock_domain"):
        errors.append("programming_sequence.clock_domain differs from discovered control ABI")
    if sequence.get("enforcement") != control.get("control_sequence_enforcement"):
        errors.append("programming_sequence.enforcement differs from discovered control ABI")
    expected_steps = _rows(control.get("control_sequence"))
    actual_steps = _rows(sequence.get("steps"))

    def projection(row: dict[str, Any]) -> tuple[Any, str, tuple[str, ...]]:
        return (
            row.get("order"),
            str(row.get("event") or ""),
            tuple(sorted(str(value) for value in _values(row.get("fact_port_ids")))),
        )

    if [projection(row) for row in actual_steps] != [projection(row) for row in expected_steps]:
        errors.append("programming_sequence does not exactly match the discovered control ABI order/events/ports")
    if not expected_steps:
        errors.append("discovered control ABI has no programming sequence")
    return copy.deepcopy(sequence)


def _validate_bank_rows(
    rows: Any,
    label: str,
    roots: dict[str, Any],
    regions: dict[str, dict[str, Any]],
    minimum_capacity: int,
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(_rows(rows)):
        row_label = f"{label}[{index}]"
        bank_id = str(row.get("bank_id") or "")
        region_id = str(row.get("region_id") or "")
        if not bank_id or bank_id in result:
            errors.append(f"{row_label}.bank_id is missing or duplicated")
            continue
        region = regions.get(region_id)
        if region is None:
            errors.append(f"{row_label}.region_id does not reference a validated memory region")
            continue
        capacity = _resolve_bound_integer(
            row.get("capacity_bytes"), f"{row_label}.capacity_bytes", roots, errors
        )
        if capacity is None:
            continue
        if capacity < minimum_capacity:
            errors.append(f"{row_label} capacity is smaller than the required payload")
        if capacity > region["resolved_size_bytes"]:
            errors.append(f"{row_label} capacity exceeds its memory region")
        result[bank_id] = {**copy.deepcopy(row), "resolved_capacity_bytes": capacity}
    if len(result) != 2:
        errors.append(f"{label} must define exactly two distinct banks")
    if len({str(row.get("region_id")) for row in result.values()}) != len(result):
        errors.append(f"{label} banks must use distinct memory regions")
    return result


def _validate_weight_double_buffer(
    plan: dict[str, Any],
    roots: dict[str, Any],
    regions: dict[str, dict[str, Any]],
    layer_count: int,
    canonical_layer_bytes: int,
    trace_roles: dict[str, str],
    errors: list[str],
) -> dict[str, Any]:
    value = plan.get("weight_double_buffer")
    if not isinstance(value, dict):
        errors.append("weight_double_buffer is missing")
        return {}
    if value.get("bank_count") != 2:
        errors.append("weight_double_buffer.bank_count must be exactly two")
    banks = _validate_bank_rows(
        value.get("banks"),
        "weight_double_buffer.banks",
        roots,
        regions,
        canonical_layer_bytes,
        errors,
    )
    protocol = value.get("ownership_protocol")
    if not isinstance(protocol, dict):
        errors.append("weight double-buffer ownership protocol is missing")
    elif layer_count > 1:
        required_flags = {
            "single_compute_owner",
            "inactive_bank_prefetch_only",
            "prefetch_completion_before_switch",
            "atomic_switch",
        }
        if any(protocol.get(name) is not True for name in required_flags):
            errors.append("weight double-buffer ownership/atomic-switch protocol is incomplete")
    elif (
        protocol.get("single_compute_owner") is not True
        or protocol.get("inactive_bank_prefetch_only") is not True
        or protocol.get("prefetch_completion_before_switch") is not False
        or protocol.get("atomic_switch") is not False
    ):
        errors.append(
            "single-layer terminal schedule must retain two physical banks without a prefetch/switch"
        )
    initial_bank = str(value.get("initial_bank_id") or "")
    if value.get("initial_layer_index") != 0 or initial_bank not in banks:
        errors.append("weight double buffer does not start with layer zero in a real bank")
    schedule = _rows(value.get("layer_schedule"))
    if len(schedule) != layer_count:
        errors.append("weight double-buffer schedule does not cover every target layer")
    previous_prefetch_bank: str | None = None
    for layer_index, row in enumerate(schedule):
        label = f"weight_double_buffer.layer_schedule[{layer_index}]"
        compute_bank = str(row.get("compute_bank_id") or "")
        if row.get("layer_index") != layer_index or compute_bank not in banks:
            errors.append(f"{label} has an invalid layer or compute bank")
        if layer_index == 0 and compute_bank != initial_bank:
            errors.append(f"{label} does not use the initially loaded bank")
        if previous_prefetch_bank is not None and compute_bank != previous_prefetch_bank:
            errors.append(f"{label} does not atomically acquire the previously prefetched bank")
        if layer_index + 1 < layer_count:
            prefetch_bank = str(row.get("prefetch_bank_id") or "")
            if row.get("prefetch_layer_index") != layer_index + 1:
                errors.append(f"{label} does not prefetch exactly the next layer")
            if prefetch_bank not in banks or prefetch_bank == compute_bank:
                errors.append(f"{label} does not prefetch into the inactive bank")
            if row.get("prefetch_overlaps_compute") is not True:
                errors.append(f"{label} does not overlap next-layer prefetch with compute")
            if row.get("switch_is_atomic") is not True:
                errors.append(f"{label} does not request an atomic bank switch")
            previous_prefetch_bank = prefetch_bank
        else:
            if row.get("prefetch_layer_index") is not None or row.get("prefetch_bank_id") is not None:
                errors.append(f"{label} prefetches beyond the final layer")
            if row.get("prefetch_overlaps_compute") is not False or row.get("switch_is_atomic") is not False:
                errors.append(f"{label} final-layer prefetch/switch flags must be false")
    trace_ids = {str(item) for item in _values(value.get("trace_point_ids"))}
    required_roles = (
        {"weight_prefetch_start", "weight_prefetch_complete", "weight_bank_switch"}
        if layer_count > 1
        else set()
    )
    if {trace_roles.get(trace_id) for trace_id in trace_ids} != required_roles:
        errors.append(
            "weight double buffer does not bind the required prefetch/switch trace roles"
        )
    return {**copy.deepcopy(value), "banks": list(banks.values())}


def _validate_activation_ping_pong(
    plan: dict[str, Any],
    roots: dict[str, Any],
    regions: dict[str, dict[str, Any]],
    layer_count: int,
    trace_roles: dict[str, str],
    errors: list[str],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    value = plan.get("activation_ping_pong")
    if not isinstance(value, dict):
        errors.append("activation_ping_pong is missing")
        return {}, []
    if value.get("bank_count") != 2:
        errors.append("activation_ping_pong.bank_count must be exactly two")
    required_bytes = _resolve_bound_integer(
        value.get("required_activation_bytes"),
        "activation_ping_pong.required_activation_bytes",
        roots,
        errors,
    )
    banks = _validate_bank_rows(
        value.get("banks"),
        "activation_ping_pong.banks",
        roots,
        regions,
        required_bytes or 1,
        errors,
    )
    input_load = value.get("input_load") if isinstance(value.get("input_load"), dict) else {}
    if str(input_load.get("source_region_id") or "") not in regions:
        errors.append("activation input_load source is not a validated memory region")
    initial_bank = str(input_load.get("destination_bank_id") or "")
    if initial_bank not in banks or input_load.get("complete_before_start") is not True:
        errors.append("activation input is not fully loaded into a ping-pong bank before start")
    schedule = _rows(value.get("layer_schedule"))
    if len(schedule) != layer_count:
        errors.append("activation ping-pong schedule does not cover every target layer")
    previous_write: str | None = None
    previous_read: str | None = None
    for layer_index, row in enumerate(schedule):
        label = f"activation_ping_pong.layer_schedule[{layer_index}]"
        read_bank = str(row.get("read_bank_id") or "")
        write_bank = str(row.get("write_bank_id") or "")
        if row.get("layer_index") != layer_index or read_bank not in banks or write_bank not in banks:
            errors.append(f"{label} has an invalid layer/bank")
        if read_bank == write_bank:
            errors.append(f"{label} reads and writes the same activation bank")
        if layer_index == 0 and read_bank != initial_bank:
            errors.append(f"{label} does not read the initial input bank")
        if previous_write is not None and (read_bank != previous_write or write_bank != previous_read):
            errors.append(f"{label} does not alternate activation ping-pong ownership")
        should_write_back = layer_index == layer_count - 1
        if row.get("external_writeback") is not should_write_back:
            errors.append(f"{label} violates final-layer-only external writeback")
        previous_read, previous_write = read_bank, write_bank
    trace_ids = {str(item) for item in _values(value.get("trace_point_ids"))}
    if {trace_roles.get(trace_id) for trace_id in trace_ids} != {"activation_bank_switch"}:
        errors.append("activation ping-pong does not bind its bank-switch trace role")
    return (
        {
            **copy.deepcopy(value),
            "required_activation_bytes_resolved": required_bytes,
            "banks": list(banks.values()),
        },
        schedule,
    )


def _validate_final_writeback(
    plan: dict[str, Any],
    regions: dict[str, dict[str, Any]],
    activation_schedule: list[dict[str, Any]],
    layer_count: int,
    trace_roles: dict[str, str],
    errors: list[str],
) -> dict[str, Any]:
    value = plan.get("final_writeback")
    if not isinstance(value, dict):
        errors.append("final_writeback is missing")
        return {}
    if (
        value.get("enabled") is not True
        or value.get("only_final_layer") is not True
        or value.get("starts_after_final_layer_completion") is not True
    ):
        errors.append("final writeback is not enabled only after final-layer completion")
    if value.get("layer_index") != layer_count - 1:
        errors.append("final writeback layer_index is not the final target layer")
    if str(value.get("destination_region_id") or "") not in regions:
        errors.append("final writeback destination is not a validated memory region")
    if activation_schedule and value.get("source_activation_bank_id") != activation_schedule[-1].get(
        "write_bank_id"
    ):
        errors.append("final writeback does not source the final activation ping-pong output bank")
    trace_ids = {str(item) for item in _values(value.get("trace_point_ids"))}
    required_roles = {"final_writeback_start", "final_writeback_complete"}
    if {trace_roles.get(trace_id) for trace_id in trace_ids} != required_roles:
        errors.append("final writeback does not bind both start/complete trace roles")
    return copy.deepcopy(value)


def _validate_runtime_manifest(
    manifest: dict[str, Any],
    connected: dict[str, Any],
    connected_hash: str,
    connected_word_count: int,
    layer_count: int,
    errors: list[str],
) -> dict[str, Any]:
    if not manifest:
        errors.append(
            "runtime_constants.full_runtime_image_manifest is missing after materialization"
        )
        return {}
    declared_hash = str(manifest.get("manifest_contract_sha256") or "").lower()
    payload = {
        key: value
        for key, value in manifest.items()
        if key != "manifest_contract_sha256"
    }
    if (
        not re.fullmatch(r"[0-9a-f]{64}", declared_hash)
        or _hash(payload) != declared_hash
    ):
        errors.append("full runtime image manifest contract hash is invalid")
    if manifest.get("schema_version") != BOARD_RUNTIME_IMAGE_MANIFEST_VERSION:
        errors.append("full runtime image manifest schema is unsupported")
    if (
        manifest.get("status") != "pass"
        or manifest.get("accelerator_scope") != "transformer_blocks_only"
        or manifest.get("scope_coverage_complete") is not True
    ):
        errors.append("full runtime image manifest is not complete for Transformer blocks")
    if manifest.get("target_layer_count") != layer_count:
        errors.append("full runtime image manifest does not cover every target layer")
    if (
        manifest.get("connected_runtime_stream_contract_sha256")
        != connected_hash
    ):
        errors.append("full runtime image manifest does not bind the connected runtime contract")
    if manifest.get("canonical_layer_word_count") != connected_word_count:
        errors.append("runtime manifest layer word count differs from the connected contract")
    for field in (
        "capture_contract_sha256",
        "source_reference_manifest_sha256",
        "semantic_adapter_sha256",
        "semantic_runtime_contract_sha256",
        "connected_runtime_stream_contract_sha256",
        "image_sha256",
    ):
        if not re.fullmatch(r"[0-9a-f]{64}", str(manifest.get(field) or "").lower()):
            errors.append(f"full runtime image manifest {field} is invalid")
    if (
        manifest.get("word_bits") != 32
        or manifest.get("byte_order") != "little"
        or manifest.get("image_format") != BOARD_RUNTIME_IMAGE_FORMAT
    ):
        errors.append("full runtime image format/word order is not canonical")
    total_bytes = manifest.get("total_bytes", manifest.get("byte_count"))
    total_words = manifest.get("word_count")
    if (
        not _is_int(total_bytes)
        or total_bytes < 0
        or not _is_int(total_words)
        or total_words < 0
        or total_bytes != total_words * 4
    ):
        errors.append("full runtime image byte/word geometry is invalid")
        total_bytes = 0
        total_words = 0
    nested_image = manifest.get("image") if isinstance(manifest.get("image"), dict) else {}
    if (
        not str(manifest.get("path") or "")
        or manifest.get("sha256") != manifest.get("image_sha256")
        or manifest.get("byte_count") != total_bytes
    ):
        errors.append("full runtime image top-level file identity is inconsistent")
    expected_image = {
        "path": manifest.get("path"),
        "sha256": manifest.get("image_sha256", manifest.get("sha256")),
        "format": manifest.get("image_format"),
        "word_bits": manifest.get("word_bits"),
        "byte_order": manifest.get("byte_order"),
        "byte_count": total_bytes,
        "word_count": total_words,
    }
    if any(nested_image.get(key) != value for key, value in expected_image.items()):
        errors.append("full runtime image nested image identity is inconsistent")

    segments: dict[str, dict[str, Any]] = {}
    intervals: list[tuple[int, int, str]] = []
    for index, row in enumerate(_rows(manifest.get("unique_segments"))):
        label = f"full runtime image unique_segments[{index}]"
        segment_id = str(row.get("segment_id") or "")
        byte_offset = row.get("byte_offset")
        byte_count = row.get("byte_count")
        byte_end = row.get("byte_end_exclusive")
        word_offset = row.get("word_offset")
        word_count = row.get("word_count")
        word_end = row.get("word_end_exclusive")
        segment_hash = str(row.get("sha256") or "").lower()
        layer_indices = _values(row.get("layer_indices"))
        if not segment_id or segment_id in segments:
            errors.append(f"{label}.segment_id is missing or duplicated")
            continue
        if (
            not all(
                _is_int(value)
                for value in (
                    byte_offset,
                    byte_count,
                    byte_end,
                    word_offset,
                    word_count,
                    word_end,
                )
            )
            or byte_offset < 0
            or byte_count <= 0
            or byte_end != byte_offset + byte_count
            or byte_offset != word_offset * 4
            or byte_count != word_count * 4
            or word_end != word_offset + word_count
        ):
            errors.append(f"{label} has invalid byte/word geometry")
            continue
        if word_count != connected_word_count:
            errors.append(f"{label} word count differs from the connected runtime stream")
        if not re.fullmatch(r"[0-9a-f]{64}", segment_hash):
            errors.append(f"{label}.sha256 is invalid")
        if (
            not layer_indices
            or any(
                not _is_int(layer) or layer < 0 or layer >= layer_count
                for layer in layer_indices
            )
            or len(set(layer_indices)) != len(layer_indices)
        ):
            errors.append(f"{label}.layer_indices is invalid")
        normalized = {
            **copy.deepcopy(row),
            "sha256": segment_hash,
            "layer_indices": [int(layer) for layer in layer_indices if _is_int(layer)],
        }
        segments[segment_id] = normalized
        intervals.append((int(byte_offset), int(byte_end), segment_id))
    if manifest.get("unique_stream_count") != len(segments):
        errors.append("full runtime image unique_stream_count is inconsistent")
    expected_offset = 0
    for byte_offset, byte_end, segment_id in sorted(intervals):
        if byte_offset != expected_offset:
            errors.append(
                f"full runtime image segment {segment_id!r} overlaps or leaves an image gap"
            )
        expected_offset = max(expected_offset, byte_end)
    if expected_offset != total_bytes:
        errors.append("full runtime image segments do not exactly cover the image")

    bindings: list[dict[str, Any]] = []
    segment_layers: dict[str, list[int]] = {segment_id: [] for segment_id in segments}
    expected_stage_bindings = [
        {
            "stage_id": str(row.get("stage_id") or ""),
            "consumer_op": str(row.get("op") or ""),
            "runtime_contract_sha256": row.get("runtime_contract_sha256"),
            "word_offset": row.get("global_stream_range", {}).get("word_offset"),
            "word_count": row.get("global_stream_range", {}).get("word_count"),
        }
        for row in _rows(connected.get("stage_segments"))
        if isinstance(row.get("global_stream_range"), dict)
        and int(row.get("global_stream_range", {}).get("word_count") or 0) > 0
    ]
    for index, row in enumerate(_rows(manifest.get("layer_bindings"))):
        label = f"full runtime image layer_bindings[{index}]"
        layer_index = row.get("layer_index")
        segment_id = str(row.get("segment_id") or "")
        segment = segments.get(segment_id)
        if layer_index != index or index >= layer_count:
            errors.append(f"{label}.layer_index does not cover target layers in order")
        if segment is None:
            errors.append(f"{label}.segment_id does not reference a runtime segment")
            continue
        for field in (
            "byte_offset",
            "byte_count",
            "word_offset",
            "word_count",
            "sha256",
        ):
            actual = str(row.get(field)).lower() if field == "sha256" else row.get(field)
            expected = segment.get(field)
            if actual != expected:
                errors.append(f"{label}.{field} differs from its runtime segment")
        if not isinstance(row.get("stage_bindings"), list):
            errors.append(f"{label}.stage_bindings is not an array")
        else:
            actual_stage_bindings = [
                {
                    "stage_id": str(stage.get("stage_id") or ""),
                    "consumer_op": str(stage.get("consumer_op") or ""),
                    "runtime_contract_sha256": stage.get(
                        "runtime_contract_sha256"
                    ),
                    "word_offset": stage.get("word_offset"),
                    "word_count": stage.get("word_count"),
                }
                for stage in _rows(row.get("stage_bindings"))
            ]
            if actual_stage_bindings != expected_stage_bindings:
                errors.append(
                    f"{label}.stage_bindings differ from the connected runtime contract"
                )
        if _is_int(layer_index) and 0 <= layer_index < layer_count:
            segment_layers[segment_id].append(int(layer_index))
        bindings.append(copy.deepcopy(row))
    if len(bindings) != layer_count:
        errors.append("full runtime image does not bind every target layer exactly once")
    for segment_id, segment in segments.items():
        if sorted(segment_layers[segment_id]) != sorted(segment.get("layer_indices", [])):
            errors.append(
                f"full runtime image segment {segment_id!r} layer reuse declaration is inconsistent"
            )
    policy = (
        manifest.get("deduplication_policy")
        if isinstance(manifest.get("deduplication_policy"), dict)
        else {}
    )
    if (
        policy.get("cross_layer_sharing_is_never_assumed") is not True
        or policy.get("shared_segment_requires_equal_recomputed_bytes") is not True
        or policy.get("different_streams_remain_distinct") is not True
    ):
        errors.append("runtime image deduplication policy is not exact-byte-only")
    projection = _runtime_materialized_projection(manifest)
    projection["unique_segments"] = list(segments.values())
    projection["layer_bindings"] = bindings
    return projection


def _validate_runtime_constants(
    plan: dict[str, Any],
    requirements: dict[str, Any],
    regions: dict[str, dict[str, Any]],
    workload_region_id: str,
    layer_count: int,
    trace_roles: dict[str, str],
    authority: dict[str, Any] | None,
    errors: list[str],
) -> dict[str, Any]:
    value = plan.get("runtime_constants")
    if not isinstance(value, dict):
        errors.append("runtime_constants is missing")
        return {}
    connected, connected_hash, connected_word_count = _connected_runtime_contract(
        requirements, errors
    )
    enabled = value.get("enabled") is True
    if not enabled:
        if value.get("enabled") is not False:
            errors.append("runtime_constants.enabled must be explicit")
        if connected_word_count != 0:
            errors.append("runtime constants cannot be disabled when the connected stream is non-empty")
        if any(
            (
                value.get("region_id") not in (None, ""),
                value.get("connected_runtime_stream_contract_sha256") not in (None, ""),
                value.get("loader_abi") not in (None, {}),
                value.get("loader_protocol") not in (None, {}),
                bool(_values(value.get("load_schedule"))),
                bool(_values(value.get("trace_point_ids"))),
                isinstance(value.get("full_runtime_image_manifest"), dict),
                isinstance(value.get("materialized_projection"), dict),
            )
        ):
            errors.append("disabled runtime_constants must not claim runtime resources or loading")
        return {
            "enabled": False,
            "region_id": None,
            "connected_runtime_stream_contract_sha256": None,
            "loader_abi": None,
            "loader_protocol": None,
            "load_schedule": [],
            "trace_point_ids": [],
        }

    if connected_word_count <= 0 or not connected_hash:
        errors.append("runtime_constants are enabled without a non-empty certified stream")
    if value.get("connected_runtime_stream_contract_sha256") != connected_hash:
        errors.append("runtime_constants do not bind the connected runtime stream contract")
    binding = _certified_single_layer_binding(authority, requirements)
    certified_loader = _validate_certified_runtime_loader(
        binding,
        connected,
        connected_hash,
        connected_word_count,
        errors,
    )
    if value.get("loader_abi") != certified_loader:
        errors.append("runtime_constants.loader_abi differs from the certified kernel loader")
    protocol = value.get("loader_protocol")
    required_protocol = {
        "ready_valid_acceptance": True,
        "address_start": 0,
        "address_increment": 1,
        "data_word_bits": 32,
        "last_on_final_accepted_word": True,
        "complete_before_kernel_start": True,
    }
    if protocol != required_protocol:
        errors.append(
            "runtime loader protocol must accept addressed data/last fully before kernel start"
        )

    manifest = _runtime_manifest_authority(value, authority, errors)
    projection = _validate_runtime_manifest(
        manifest,
        connected,
        connected_hash,
        connected_word_count,
        layer_count,
        errors,
    )
    supplied_projection = value.get("materialized_projection")
    if isinstance(supplied_projection, dict) and supplied_projection != projection:
        errors.append("runtime constants materialized projection differs from its manifest")
    region_id = str(value.get("region_id") or "")
    region = regions.get(region_id)
    if region is None:
        errors.append("runtime_constants.region_id does not reference a validated memory region")
    else:
        if region_id == workload_region_id:
            errors.append("runtime constants and weight workload image must use non-overlapping regions")
        if region["resolved_size_bytes"] < int(projection.get("total_bytes") or 0):
            errors.append("runtime constants image does not fit its physical memory region")

    expected_bindings = _rows(projection.get("layer_bindings"))
    schedule = _rows(value.get("load_schedule"))
    if len(schedule) != layer_count:
        errors.append("runtime load schedule does not cover every target layer")
    manifest_fields = (
        "layer_index",
        "segment_id",
        "byte_offset",
        "byte_count",
        "word_offset",
        "word_count",
        "sha256",
    )
    for layer_index, row in enumerate(schedule):
        label = f"runtime_constants.load_schedule[{layer_index}]"
        expected = expected_bindings[layer_index] if layer_index < len(expected_bindings) else {}
        for field in manifest_fields:
            actual = str(row.get(field)).lower() if field == "sha256" else row.get(field)
            reference = (
                str(expected.get(field)).lower()
                if field == "sha256"
                else expected.get(field)
            )
            if actual != reference:
                errors.append(f"{label}.{field} differs from the runtime manifest")
        word_count = row.get("word_count")
        if (
            row.get("loader_address_start") != 0
            or row.get("loader_address_count") != word_count
            or not _is_int(word_count)
            or row.get("last_word_address") != int(word_count or 0) - 1
            or row.get("complete_before_kernel_start") is not True
        ):
            errors.append(
                f"{label} does not complete the certified address/data/last load before kernel start"
            )
    trace_ids = {str(item) for item in _values(value.get("trace_point_ids"))}
    if {trace_roles.get(trace_id) for trace_id in trace_ids} != RUNTIME_TRACE_ROLES:
        errors.append("runtime constants do not bind both runtime load trace roles")
    return {
        **copy.deepcopy(value),
        "full_runtime_image_manifest": copy.deepcopy(manifest),
        "materialized_projection": projection,
        "load_schedule": copy.deepcopy(schedule),
    }


def _validate_trace_points(
    plan: dict[str, Any],
    identity: dict[str, Any],
    runtime_enabled: bool,
    requires_next_layer_prefetch: bool,
    errors: list[str],
) -> dict[str, str]:
    abi = identity.get("compute_slot_abi") if isinstance(identity.get("compute_slot_abi"), dict) else {}
    control = abi.get("control_abi") if isinstance(abi.get("control_abi"), dict) else {}
    clock_domain = str(control.get("clock_domain") or "")
    trace_roles: dict[str, str] = {}
    role_counts: Counter[str] = Counter()
    for index, row in enumerate(_rows(plan.get("trace_points"))):
        label = f"trace_points[{index}]"
        trace_id = str(row.get("trace_id") or "")
        role = str(row.get("role") or "")
        if not trace_id or trace_id in trace_roles:
            errors.append(f"{label}.trace_id is missing or duplicated")
            continue
        if role not in REQUIRED_TRACE_ROLES:
            errors.append(f"{label}.role is not a required board-runtime event")
        if row.get("clock_domain") != clock_domain:
            errors.append(f"{label}.clock_domain differs from the discovered control ABI")
        if not str(row.get("condition") or "") or not [
            value for value in _values(row.get("observed_fields")) if str(value)
        ]:
            errors.append(f"{label} lacks an observable event condition/field set")
        trace_roles[trace_id] = role
        role_counts[role] += 1
    expected_roles = (
        set(REQUIRED_TRACE_ROLES)
        if runtime_enabled
        else REQUIRED_TRACE_ROLES - RUNTIME_TRACE_ROLES
    )
    if not requires_next_layer_prefetch:
        expected_roles -= {
            "weight_prefetch_start",
            "weight_prefetch_complete",
            "weight_bank_switch",
        }
    if set(role_counts) != expected_roles or any(count != 1 for count in role_counts.values()):
        errors.append("trace_points must contain exactly one point for every required runtime role")
    return trace_roles


def validate_and_normalize_plan(
    plan: dict[str, Any],
    identity: dict[str, Any],
    model: dict[str, Any],
    catalog: dict[str, Any],
    requirements: dict[str, Any],
    stage_memory_layout: dict[str, Any],
    runtime_constant_authority: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], list[str]]:
    """Validate one LLM board-memory/runtime plan against current-run evidence.

    ``runtime_constant_authority`` may bind a framework-materialized
    ``full_runtime_image_manifest`` and the certified ``single_layer_harness``.
    It remains optional so plans with no connected runtime stream can use the
    original six-argument API and explicitly disable runtime constants.

    The function is intentionally pure: it does not invoke an LLM, materialize
    weights, edit RTL, or run a repair loop.
    """

    errors: list[str] = []
    if not all(
        isinstance(value, dict)
        for value in (plan, identity, model, catalog, requirements, stage_memory_layout)
    ):
        return {}, ["plan and every authority input must be a JSON object"]
    normalized = copy.deepcopy(plan)
    _validate_schema_shape(plan, BOARD_MEMORY_RUNTIME_PLAN_SCHEMA, "plan", errors)
    if plan.get("schema_version") != PLAN_SCHEMA_VERSION:
        errors.append(f"schema_version must be {PLAN_SCHEMA_VERSION}")
    if plan.get("agent") != PLAN_AGENT_ID:
        errors.append(f"agent must be the single planner {PLAN_AGENT_ID}")
    if plan.get("status") != "ready":
        errors.append("plan status is not ready")
    if plan.get("status") == "ready" and _values(plan.get("blocked_reasons")):
        errors.append("ready plan has blocked_reasons")
    if identity.get("status") != "pass":
        errors.append("exact board identity status is not pass")
    if not str(plan.get("summary") or ""):
        errors.append("plan summary is missing")

    input_hashes = _validate_input_bindings(
        plan, identity, model, catalog, requirements, stage_memory_layout, errors
    )
    workload = (
        plan.get("workload_image") if isinstance(plan.get("workload_image"), dict) else {}
    )
    roots = {
        "identity": identity,
        "model": model,
        "catalog": catalog,
        "requirements": requirements,
        "stage_memory_layout": stage_memory_layout,
        "workload_image": workload,
    }
    normalized_workload, layer_count, canonical_layer_bytes = _validate_catalog_and_image(
        workload, model, catalog, requirements, roots, errors
    )
    normalized["workload_image"] = normalized_workload
    image_projection = (
        normalized_workload.get("materialized_projection")
        if isinstance(normalized_workload.get("materialized_projection"), dict)
        else {}
    )
    roots["workload_image"] = image_projection
    regions = _validate_memory_regions(plan, roots, identity, errors)
    normalized["memory_regions"] = list(regions.values())
    image_region = regions.get(str(normalized_workload.get("region_id") or ""))
    if image_region is None:
        errors.append("workload_image.region_id does not reference a validated memory region")
    elif image_region["resolved_size_bytes"] < int(image_projection.get("total_bytes") or 0):
        errors.append("workload image does not fit its physical memory region")
    normalized["physical_cfg_bindings"] = _validate_cfg_bindings(
        plan, roots, identity, errors
    )
    normalized["programming_sequence"] = _validate_programming_sequence(plan, identity, errors)
    runtime_value = (
        plan.get("runtime_constants")
        if isinstance(plan.get("runtime_constants"), dict)
        else {}
    )
    runtime_enabled = runtime_value.get("enabled") is True
    trace_roles = _validate_trace_points(
        plan,
        identity,
        runtime_enabled,
        layer_count > 1,
        errors,
    )
    normalized["runtime_constants"] = _validate_runtime_constants(
        plan,
        requirements,
        regions,
        str(normalized_workload.get("region_id") or ""),
        layer_count,
        trace_roles,
        runtime_constant_authority,
        errors,
    )
    normalized["weight_double_buffer"] = _validate_weight_double_buffer(
        plan,
        roots,
        regions,
        layer_count,
        canonical_layer_bytes,
        trace_roles,
        errors,
    )
    normalized_activation, activation_schedule = _validate_activation_ping_pong(
        plan, roots, regions, layer_count, trace_roles, errors
    )
    normalized["activation_ping_pong"] = normalized_activation
    normalized["final_writeback"] = _validate_final_writeback(
        plan, regions, activation_schedule, layer_count, trace_roles, errors
    )
    normalized["trace_points"] = copy.deepcopy(_rows(plan.get("trace_points")))

    normalized["validation"] = {
        "status": "pass" if not errors else "fail",
        "errors": list(errors),
        "input_hashes": input_hashes,
        "target_layer_count": layer_count,
        "canonical_layer_bytes": canonical_layer_bytes,
        "no_opaque_numeric_literals": True,
        "physical_cfg_matching_policy": "exact_field_and_fact_identity_only",
    }
    if not errors:
        contract_payload = {
            key: value
            for key, value in normalized.items()
            if key not in {"contract_sha256", "validation"}
        }
        normalized["contract_sha256"] = _hash(contract_payload)
    return normalized, errors
