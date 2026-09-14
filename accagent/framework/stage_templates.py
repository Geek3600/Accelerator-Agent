"""Select hardware templates for model operators."""

from __future__ import annotations

import argparse
import hashlib
import copy
import re
from pathlib import Path
from typing import Any

from accagent.framework.sacg_store import SACGStore
from accagent.framework.sacg_utils import read_json, write_json
from accagent.framework.stage_entry import run_sacg_stage
from accagent.framework.stage_llm import run_stage_agent
from accagent.framework.stage_team import run_design_team, team_failure_errors, team_summary


class TemplateSelectionError(ValueError):
    pass


TOUCHED_NODES = ["node.model", "node.template_library"]
TOUCHED_CONSTRAINTS = [
    "constraint.model.decoder",
    "constraint.shape.model",
    "constraint.numeric.policy",
    "constraint.template.library",
    "constraint.arch.design_space",
    "constraint.deployment.board",
    "constraint.memory.board",
    "constraint.runtime.board",
    "constraint.cross_layer.input_consistency",
]


REQUIRED_CROSS_LAYER_CONSTRAINTS = [
    "constraint.numeric.policy",
    "constraint.memory.board",
    "constraint.runtime.board",
    "constraint.deployment.board",
    "constraint.cross_layer.input_consistency",
]


PARAM_ALIASES = {
    "hidden_size": ["hiddenSize", "inDim", "outDim"],
    "intermediate_size": ["intermediateSize"],
    "num_q_heads": ["qHeads", "numHeads"],
    "num_kv_heads": ["kvHeads"],
    "head_dim": ["headDim"],
    "seq_len": ["seqLen", "maxSeqLen"],
    "lanes": ["lanes", "inLanes", "outLanes"],
    "tile_m": ["tileM"],
    "tile_n": ["tileN"],
    "tile_k": ["tileK"],
    "eps": ["eps"],
    "elem_bits": ["elemBits", "inputBits", "outputBits"],
    "input_bits": ["inputBits"],
    "output_bits": ["outputBits"],
    "frac_bits": ["fracBits"],
    "rope_theta": ["ropeTheta", "theta"],
    "causal": ["causal"],
}


TEMPLATE_CASE_CLASS = {
    "attention": "AttentionParams",
    "decoder_block": "LlamaStyleBlockParams",
    "elementwise": "ElementwiseMulParams",
    "ffn": "GatedMLPParams",
    "kv_cache": "KVCacheParams",
    "linear": "LinearParams",
    "mask": "AttentionMaskParams",
    "norm": "RMSNormParams",
    "qkv_projection": "QKVProjectionParams",
    "residual": "ResidualParams",
    "rope": "RoPEParams",
    "softmax": "SoftmaxParams",
}


def get_constraint(state: dict[str, Any], constraint_id: str) -> dict[str, Any]:
    for constraint in state.get("constraints", []):
        if constraint.get("id") == constraint_id:
            return constraint
    raise TemplateSelectionError(f"SACG missing constraint: {constraint_id}")


def optional_constraint_facts(state: dict[str, Any], constraint_id: str) -> dict[str, Any]:
    for constraint in state.get("constraints", []):
        if constraint.get("id") == constraint_id:
            facts = constraint.get("facts", {})
            return facts if isinstance(facts, dict) else {}
    return {}


def artifact_record(state: dict[str, Any], artifact_id: str) -> dict[str, Any] | None:
    for artifact in state.get("artifacts", []):
        if artifact.get("id") == artifact_id:
            return artifact
    return None


def read_artifact_json(state: dict[str, Any], artifact_id: str) -> dict[str, Any]:
    artifact = artifact_record(state, artifact_id)
    if not artifact:
        return {}
    path = artifact.get("path")
    if not path:
        return {}
    try:
        data = read_json(Path(path))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dtype_bits(dtype: Any) -> int | None:
    text = str(dtype or "").strip().upper().replace("_", "")
    if text in {"FP16", "FLOAT16", "BF16", "BFloat16".upper()}:
        return 16
    if text in {"FP32", "FLOAT32"}:
        return 32
    if text in {"FP64", "FLOAT64"}:
        return 64
    match = re.search(r"(?:INT|UINT|I|U)(\d+)", text)
    if match:
        return int(match.group(1))
    return None


def numeric_elem_bits(numeric: dict[str, Any]) -> dict[str, Any]:
    rules = numeric.get("default_rules", {})
    dtype = rules.get("activation_dtype") or numeric.get("activation_dtype") or rules.get("weight_dtype")
    bits = dtype_bits(dtype)
    return {
        "value": bits,
        "source": "constraint.numeric.policy.default_rules.activation_dtype",
        "dtype": dtype,
        "status": "bound" if bits is not None else "missing",
    }


def numeric_bits(numeric: dict[str, Any], field: str, fallback_field: str = "activation_dtype") -> dict[str, Any]:
    rules = numeric.get("default_rules", {})
    dtype = rules.get(field) or numeric.get(field) or rules.get(fallback_field) or numeric.get(fallback_field)
    bits = dtype_bits(dtype)
    return {
        "value": bits,
        "source": f"constraint.numeric.policy.default_rules.{field}",
        "dtype": dtype,
        "status": "bound" if bits is not None else "missing",
    }


def flatten_candidate_values(value: Any, key_names: set[str]) -> list[int]:
    found: list[int] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key) in key_names and isinstance(child, list):
                for item in child:
                    if isinstance(item, int) and item > 0 and item not in found:
                        found.append(item)
            found.extend(flatten_candidate_values(child, key_names))
    elif isinstance(value, list):
        for child in value:
            found.extend(flatten_candidate_values(child, key_names))
    return found


def int_candidates(value: Any) -> list[int]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, int) and item > 0]


def first_legal(candidates: list[int], predicate: Any) -> tuple[int | None, list[int]]:
    legal = [value for value in candidates if predicate(value)]
    return (legal[0] if legal else None), legal


def ordered_candidates(candidates: list[int], preferred: Any = None) -> list[int]:
    values: list[int] = []
    if isinstance(preferred, int) and preferred > 0:
        values.append(preferred)
    for value in candidates:
        if isinstance(value, int) and value > 0 and value not in values:
            values.append(value)
    return values


def linear_profile(search_params: dict[str, Any], op: str) -> dict[str, Any]:
    linear_tiles = search_params.get("linear_tiles", {})
    if not isinstance(linear_tiles, dict):
        return {}
    for profile in linear_tiles.values():
        if not isinstance(profile, dict):
            continue
        applies_to = [str(item) for item in profile.get("applies_to", [])]
        if op in applies_to:
            return profile
    return {}


def select_lanes(shape: dict[str, Any], numeric: dict[str, Any], memory: dict[str, Any], search_params: dict[str, Any]) -> dict[str, Any]:
    elem_bits = numeric_elem_bits(numeric).get("value")
    memory_system = memory.get("memory_system", {})
    axi_bits = memory_system.get("axi_data_width_bits")
    candidates: list[int] = []
    lane_groups = search_params.get("lanes", {})
    if isinstance(lane_groups, dict):
        for group in lane_groups.values():
            if isinstance(group, dict):
                for value in int_candidates(group.get("candidates")):
                    if value not in candidates:
                        candidates.append(value)
    for value in flatten_candidate_values(
        search_params,
        {"lanes_candidates", "vector_lanes_candidates", "head_dim_lanes_candidates", "rope_lanes_candidates"},
    ):
        if value not in candidates:
            candidates.append(value)
    if not candidates:
        candidates = [1, 2, 4, 8, 16, 32]
    hidden = shape.get("hidden_size")
    intermediate = shape.get("intermediate_size")
    head_dim = shape.get("head_dim")

    def legal(value: int) -> bool:
        dims = [dim for dim in [hidden, intermediate, head_dim] if isinstance(dim, int) and dim > 0]
        if any(dim % value != 0 for dim in dims):
            return False
        if isinstance(elem_bits, int) and isinstance(axi_bits, int):
            beat_bits = value * elem_bits
            return beat_bits <= axi_bits and axi_bits % beat_bits == 0
        return True

    selected, legal_values = first_legal(candidates, legal)
    return {
        "value": selected,
        "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
        "candidate_values": candidates,
        "legal_values": legal_values,
        "status": "bound" if selected is not None else "missing",
    }


def projection_dims(op: str, shape: dict[str, Any]) -> tuple[int | None, int | None]:
    hidden = shape.get("hidden_size")
    intermediate = shape.get("intermediate_size")
    head_dim = shape.get("head_dim")
    num_q = shape.get("num_q_heads")
    num_kv = shape.get("num_kv_heads")
    if op in {"mlp_gate_proj", "mlp_up_proj"}:
        return hidden, intermediate
    if op == "mlp_down_proj":
        return intermediate, hidden
    if op == "q_proj":
        return hidden, (num_q * head_dim if isinstance(num_q, int) and isinstance(head_dim, int) else None)
    if op in {"k_proj", "v_proj"}:
        return hidden, (num_kv * head_dim if isinstance(num_kv, int) and isinstance(head_dim, int) else None)
    return hidden, hidden


def tile_size_profile(tile_sizes: dict[str, Any], op: str) -> tuple[str, dict[str, Any]]:
    if op in {"mlp_gate_proj", "mlp_up_proj"}:
        profile = tile_sizes.get("ffn_gate_up", {})
        return "ffn_gate_up", profile if isinstance(profile, dict) else {}
    if op == "mlp_down_proj":
        profile = tile_sizes.get("ffn_down", {})
        return "ffn_down", profile if isinstance(profile, dict) else {}
    if op in {"q_proj", "k_proj", "v_proj", "fused_qkv"}:
        profile = tile_sizes.get("qkv_projection", {})
        return "qkv_projection", profile if isinstance(profile, dict) else {}
    if op in {"out_proj", "output_projection"}:
        profile = tile_sizes.get("out_projection", {})
        return "out_projection", profile if isinstance(profile, dict) else {}
    return "", {}


def profile_tile_candidates(profile: dict[str, Any], param: str) -> list[int]:
    preferred = profile.get("preferred_initial")
    preferred_value = preferred.get(param) if isinstance(preferred, dict) else None
    return ordered_candidates(int_candidates(profile.get(f"{param}_candidates")), preferred_value)


def select_tile_param(param: str, op: str, shape: dict[str, Any], search_params: dict[str, Any]) -> dict[str, Any]:
    seq_len = shape.get("target_max_seq_len")
    in_dim, out_dim = projection_dims(op, shape)
    profile = linear_profile(search_params, op)
    source = f"constraint.arch.design_space.search_params"
    fallback = search_params.get("global_datapath", {}) if isinstance(search_params.get("global_datapath"), dict) else {}
    candidates = profile.get(f"{param}_candidates") or fallback.get(f"{param}_candidates") or []
    tiles = search_params.get("tiles", {})
    if isinstance(tiles, dict):
        if param == "tile_m":
            token_tiles = tiles.get("tile_m_tokens", {})
            if isinstance(token_tiles, dict):
                candidates = int_candidates(token_tiles.get("candidates")) or candidates
                source = "constraint.arch.design_space.search_params.tiles.tile_m_tokens"
        elif op in {"mlp_gate_proj", "mlp_up_proj"}:
            gate_up = tiles.get("mlp_gate_up_projection", {})
            common = tiles.get("safe_common_ffn_tile_candidates", {})
            if isinstance(gate_up, dict):
                key = "tile_k_hidden_candidates" if param == "tile_k" else "tile_n_intermediate_candidates"
                candidates = int_candidates(gate_up.get(key)) or candidates
                source = f"constraint.arch.design_space.search_params.tiles.mlp_gate_up_projection.{key}"
            if not candidates and isinstance(common, dict):
                candidates = int_candidates(common.get(param)) or candidates
                source = f"constraint.arch.design_space.search_params.tiles.safe_common_ffn_tile_candidates.{param}"
        elif op == "mlp_down_proj":
            down = tiles.get("mlp_down_projection", {})
            common = tiles.get("safe_common_ffn_tile_candidates", {})
            if isinstance(down, dict):
                key = "tile_k_intermediate_candidates" if param == "tile_k" else "tile_n_hidden_candidates"
                candidates = int_candidates(down.get(key)) or candidates
                source = f"constraint.arch.design_space.search_params.tiles.mlp_down_projection.{key}"
            if not candidates and isinstance(common, dict):
                candidates = int_candidates(common.get(param)) or candidates
                source = f"constraint.arch.design_space.search_params.tiles.safe_common_ffn_tile_candidates.{param}"
    tile_sizes = search_params.get("tile_sizes", {})
    if isinstance(tile_sizes, dict):
        profile_name, nested_profile = tile_size_profile(tile_sizes, op)
        nested_candidates = profile_tile_candidates(nested_profile, param) if nested_profile else []
        if nested_candidates:
            candidates = nested_candidates
            source = f"constraint.arch.design_space.search_params.tile_sizes.{profile_name}.{param}_candidates"
        elif param == "tile_m":
            seq_tile = tile_sizes.get("seq_tile_m", {})
            if isinstance(seq_tile, dict):
                candidates = ordered_candidates(int_candidates(seq_tile.get("candidates")), seq_tile.get("preferred_initial")) or candidates
                if candidates:
                    source = "constraint.arch.design_space.search_params.tile_sizes.seq_tile_m.candidates"
            else:
                candidates = (
                    int_candidates(tile_sizes.get("seq_tile_m_candidates"))
                    or int_candidates(tile_sizes.get("linear_tile_m_candidates"))
                    or candidates
                )
                if candidates:
                    source = "constraint.arch.design_space.search_params.tile_sizes.seq_tile_m_candidates"
        elif param == "tile_n":
            if op in {"mlp_gate_proj", "mlp_up_proj"}:
                candidates = int_candidates(tile_sizes.get("ffn_gate_up_tile_n_candidates")) or candidates
                if candidates:
                    source = "constraint.arch.design_space.search_params.tile_sizes.ffn_gate_up_tile_n_candidates"
            elif op == "mlp_down_proj":
                candidates = int_candidates(tile_sizes.get("ffn_down_tile_n_candidates")) or candidates
                if candidates:
                    source = "constraint.arch.design_space.search_params.tile_sizes.ffn_down_tile_n_candidates"
            candidates = int_candidates(tile_sizes.get("common_matmul_tile_n_candidates")) or candidates
            if candidates and source == "constraint.arch.design_space.search_params":
                source = "constraint.arch.design_space.search_params.tile_sizes.common_matmul_tile_n_candidates"
        elif param == "tile_k":
            candidates = int_candidates(tile_sizes.get("common_matmul_tile_k_candidates")) or candidates
            if candidates:
                source = "constraint.arch.design_space.search_params.tile_sizes.common_matmul_tile_k_candidates"
    candidates = [value for value in candidates if isinstance(value, int) and value > 0]
    if param == "tile_m":
        divisor = seq_len
    elif param == "tile_n":
        divisor = out_dim
    else:
        divisor = in_dim
    selected, legal_values = first_legal(candidates, lambda value: isinstance(divisor, int) and divisor > 0 and divisor % value == 0)
    return {
        "value": selected,
        "source": source,
        "candidate_values": candidates,
        "legal_values": legal_values,
        "divides": divisor,
        "status": "bound" if selected is not None else "missing",
    }


def parse_case_class_params(source_text: str) -> dict[str, list[dict[str, Any]]]:
    classes: dict[str, list[dict[str, Any]]] = {}
    pattern = re.compile(r"final\s+case\s+class\s+(\w+)\s*\((.*?)\)\s*(?:\{|extends)", re.DOTALL)
    for match in pattern.finditer(source_text):
        class_name = match.group(1)
        body = match.group(2)
        params: list[dict[str, Any]] = []
        for raw in body.split(","):
            text = raw.strip()
            if not text or ":" not in text:
                continue
            name = text.split(":", 1)[0].strip()
            if not re.match(r"^[A-Za-z_]\w*$", name):
                continue
            params.append({"name": name, "has_default": "=" in text})
        classes[class_name] = params
    return classes


def source_param_names(params: list[dict[str, Any]]) -> set[str]:
    return {str(item["name"]) for item in params}


def constructor_param_matches(param: str, names: set[str]) -> bool:
    aliases = PARAM_ALIASES.get(param, [param])
    return any(alias in names for alias in aliases)


def canonical_ops(op: str) -> list[str]:
    candidates = [op]
    stripped = re.sub(r"_\d+$", "", op)
    if stripped not in candidates:
        candidates.append(stripped)
    aliases = {
        "layer_norm": ["layer_norm"],
        "rms_norm": ["rms_norm"],
        "residual_add": ["residual_add"],
    }
    for prefix, values in aliases.items():
        if op.startswith(prefix):
            for value in values:
                if value not in candidates:
                    candidates.append(value)
    return candidates


def template_priority(op: str, template_id: str) -> tuple[int, str]:
    preferred = {
        "q_proj": "qkv_projection",
        "k_proj": "qkv_projection",
        "v_proj": "qkv_projection",
        "fused_qkv": "qkv_projection",
        "mlp_fc1": "ffn",
        "mlp_fc2": "ffn",
        "mlp_gate_proj": "ffn",
        "mlp_up_proj": "ffn",
        "mlp_down_proj": "ffn",
    }
    return (0 if preferred.get(op) == template_id else 1, template_id)


def match_template(op: str, templates: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, str | None, list[str]]:
    support_map: dict[str, list[dict[str, Any]]] = {}
    for template in templates:
        for supported_op in template.get("supported_ops", []):
            support_map.setdefault(str(supported_op), []).append(template)

    for candidate_op in canonical_ops(op):
        matches = support_map.get(candidate_op, [])
        if matches:
            matches = sorted(matches, key=lambda item: template_priority(candidate_op, str(item.get("template_id"))))
            return matches[0], candidate_op, [str(item.get("template_id")) for item in matches]
    return None, None, []


def wrapper_ops(model_facts: dict[str, Any]) -> list[str]:
    model_type = model_facts.get("model_type")
    block_type = model_facts.get("block_type")
    candidates: list[str] = []
    if model_type:
        candidates.append(f"{model_type}_block")
    if block_type:
        candidates.append(f"{block_type}_block")
    candidates.append("decoder_block")
    return list(dict.fromkeys(candidates))


def is_decoder_block_op(op: str) -> bool:
    return op in {
        "decoder_block",
        "opt_block",
        "gpt2_block",
        "llama_block",
        "qwen2_block",
        "gemma3_text_block",
    } or op.endswith("_block")


def add_attention_subtemplates(
    selected: list[dict[str, Any]],
    missing_ops: list[str],
    templates: list[dict[str, Any]],
) -> None:
    if not any(item.get("op") == "self_attention" for item in selected):
        return
    for op in ["softmax", "causal_mask"]:
        if any(item.get("op") == op for item in selected):
            continue
        template, matched_op, candidates = match_template(op, templates)
        if template is None:
            missing_ops.append(op)
            continue
        selected.append(make_selection("attention_submodule", op, matched_op, template, candidates))


def bind_param(
    param: str,
    op: str,
    shape: dict[str, Any],
    model_facts: dict[str, Any],
    model_config: dict[str, Any],
    numeric: dict[str, Any],
    memory: dict[str, Any],
    search_params: dict[str, Any],
    lane_binding: dict[str, Any],
) -> dict[str, Any]:
    shape_sources = {
        "hidden_size": "constraint.shape.model.hidden_size",
        "intermediate_size": "constraint.shape.model.intermediate_size",
        "num_q_heads": "constraint.shape.model.num_q_heads",
        "num_kv_heads": "constraint.shape.model.num_kv_heads",
        "head_dim": "constraint.shape.model.head_dim",
        "seq_len": "constraint.shape.model.target_max_seq_len",
    }
    shape_keys = {
        "hidden_size": "hidden_size",
        "intermediate_size": "intermediate_size",
        "num_q_heads": "num_q_heads",
        "num_kv_heads": "num_kv_heads",
        "head_dim": "head_dim",
        "seq_len": "target_max_seq_len",
    }
    if param in shape_keys:
        if param == "hidden_size" and op == "activation_mul":
            value = shape.get("intermediate_size")
            return {
                "value": value,
                "source": "constraint.shape.model.intermediate_size",
                "status": "bound" if value is not None else "missing",
            }
        value = shape.get(shape_keys[param])
        return {"value": value, "source": shape_sources[param], "status": "bound" if value is not None else "missing"}
    if param == "lanes":
        return lane_binding
    if param in {"tile_m", "tile_n", "tile_k"}:
        return select_tile_param(param, op, shape, search_params)
    if param == "eps":
        value = (model_config.get("norm") or {}).get("eps")
        return {
            "value": value,
            "source": "artifact.input.model_config.norm.eps",
            "status": "bound" if value is not None else "missing",
        }
    if param == "elem_bits":
        return numeric_elem_bits(numeric)
    if param == "input_bits":
        return numeric_bits(numeric, "acc_dtype")
    if param == "output_bits":
        if is_decoder_block_op(op):
            return {
                **numeric_bits(numeric, "acc_dtype"),
                "source": "constraint.numeric.policy.default_rules.acc_dtype (decoder block residual stream)",
            }
        return numeric_bits(numeric, "activation_dtype")
    if param == "frac_bits":
        value = (numeric.get("default_rules") or {}).get("frac_bits") or numeric.get("frac_bits")
        return {
            "value": value,
            "source": "constraint.numeric.policy.frac_bits",
            "status": "bound" if value is not None else "missing",
        }
    if param == "rope_theta":
        pos = model_facts.get("position_encoding") if isinstance(model_facts.get("position_encoding"), dict) else {}
        cfg_pos = ((model_config.get("attention") or {}).get("position_encoding") or {})
        value = pos.get("rope_theta") or cfg_pos.get("rope_theta")
        return {
            "value": value,
            "source": "constraint.model.decoder.position_encoding.rope_theta",
            "status": "bound" if value is not None else "missing",
        }
    if param == "causal":
        value = ((model_config.get("attention") or {}).get("causal"))
        if value is None:
            value = True
        return {
            "value": bool(value),
            "source": "artifact.input.model_config.attention.causal",
            "status": "bound",
        }
    return {"value": None, "source": "unhandled", "status": "missing"}


def validate_binding(op: str, bound: dict[str, dict[str, Any]], shape: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for name, record in bound.items():
        if record.get("status") != "bound":
            errors.append(f"{op}: parameter {name} is not bound from SACG/input artifacts")
    hidden = value_of(bound, "hidden_size", shape.get("hidden_size"))
    intermediate = value_of(bound, "intermediate_size", shape.get("intermediate_size"))
    q_heads = value_of(bound, "num_q_heads", shape.get("num_q_heads"))
    kv_heads = value_of(bound, "num_kv_heads", shape.get("num_kv_heads"))
    head_dim = value_of(bound, "head_dim", shape.get("head_dim"))
    lanes = value_of(bound, "lanes", None)
    has_attention_shape = "num_q_heads" in bound and "head_dim" in bound
    if has_attention_shape and all(isinstance(value, int) for value in [hidden, q_heads, head_dim]) and hidden != q_heads * head_dim:
        errors.append(f"{op}: hidden_size={hidden} does not equal num_q_heads*head_dim={q_heads * head_dim}")
    if "num_q_heads" in bound and "num_kv_heads" in bound and isinstance(q_heads, int) and isinstance(kv_heads, int) and kv_heads and q_heads % kv_heads != 0:
        errors.append(f"{op}: num_q_heads={q_heads} is not divisible by num_kv_heads={kv_heads}")
    if isinstance(lanes, int):
        dims = [dim for dim in [hidden, intermediate, head_dim] if isinstance(dim, int)]
        for dim in dims:
            if dim % lanes != 0:
                errors.append(f"{op}: dimension {dim} is not divisible by lanes={lanes}")
    return errors


def value_of(bound: dict[str, dict[str, Any]], name: str, default: Any = None) -> Any:
    record = bound.get(name)
    if isinstance(record, dict) and record.get("status") == "bound":
        return record.get("value")
    return default


def build_parameter_bindings(
    selected: list[dict[str, Any]],
    state: dict[str, Any],
    model_facts: dict[str, Any],
    shape: dict[str, Any],
    numeric: dict[str, Any],
    memory: dict[str, Any],
    design_space: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    model_config = read_artifact_json(state, "artifact.input.model_config")
    search_params = design_space.get("search_params", {}) if isinstance(design_space.get("search_params"), dict) else {}
    lane_binding = select_lanes(shape, numeric, memory, search_params)
    bindings: list[dict[str, Any]] = []
    errors: list[str] = []
    for item in selected:
        required_params = [str(param) for param in item.get("required_params", [])]
        bound = {
            param: bind_param(param, str(item["op"]), shape, model_facts, model_config, numeric, memory, search_params, lane_binding)
            for param in required_params
        }
        binding_errors = validate_binding(str(item["op"]), bound, shape)
        missing_params = [name for name, record in bound.items() if record.get("status") != "bound"]
        errors.extend(binding_errors)
        bindings.append(
            {
                "role": item.get("role"),
                "op": item.get("op"),
                "matched_op": item.get("matched_op"),
                "template_id": item.get("template_id"),
                "source": item.get("source"),
                "required_params": required_params,
                "bound_params": bound,
                "missing_params": missing_params,
                "legality_errors": binding_errors,
                "status": "ready" if not missing_params and not binding_errors else "incomplete",
            }
        )
    return bindings, errors


def source_name_covered_by_metadata(source_name: str, metadata_params: list[str]) -> bool:
    for param in metadata_params:
        if source_name in PARAM_ALIASES.get(param, [param]):
            return True
    return False


def template_source_checks(selected: list[dict[str, Any]], template_facts: dict[str, Any], numeric: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    template_dir = Path(str(template_facts.get("template_dir") or ""))
    elem_bits = numeric_elem_bits(numeric).get("value")
    checks: list[dict[str, Any]] = []
    errors: list[str] = []
    for item in selected:
        template_id = str(item.get("template_id"))
        source = str(item.get("source") or "")
        path = template_dir / source if source else Path("")
        check: dict[str, Any] = {
            "op": item.get("op"),
            "template_id": template_id,
            "source": source,
            "path": str(path) if source else None,
            "exists": bool(source and path.exists()),
            "sha256": sha256_file(path) if source else None,
            "case_class": TEMPLATE_CASE_CLASS.get(template_id),
            "metadata_required_params": item.get("required_params", []),
            "errors": [],
            "warnings": [],
        }
        if not source or not path.exists():
            check["errors"].append("template source file is missing")
        else:
            text = path.read_text(encoding="utf-8")
            case_classes = parse_case_class_params(text)
            case_class = check["case_class"]
            params = case_classes.get(str(case_class), [])
            names = source_param_names(params)
            if not params:
                check["errors"].append(f"expected case class {case_class} was not found in source")
            else:
                required_params = [str(param) for param in item.get("required_params", [])]
                missing_in_constructor = [
                    param for param in required_params if not constructor_param_matches(param, names)
                ]
                source_required_missing = [
                    param["name"]
                    for param in params
                    if not param.get("has_default") and not source_name_covered_by_metadata(str(param["name"]), required_params)
                ]
                numeric_params = [name for name in ["elemBits", "inputBits", "outputBits"] if name in names]
                unbound_numeric_params = []
                if isinstance(elem_bits, int) and numeric_params:
                    for name in numeric_params:
                        if not source_name_covered_by_metadata(name, required_params):
                            unbound_numeric_params.append(name)
                check.update(
                    {
                        "constructor_params": params,
                        "missing_required_params_in_constructor": missing_in_constructor,
                        "source_required_params_missing_from_metadata": source_required_missing,
                        "numeric_constructor_params_not_bound_by_metadata": unbound_numeric_params,
                    }
                )
                if missing_in_constructor:
                    check["errors"].append(
                        f"metadata required params not present in {case_class}: {missing_in_constructor}"
                    )
                if source_required_missing:
                    check["errors"].append(
                        f"{case_class} required constructor params missing from metadata: {source_required_missing}"
                    )
                if unbound_numeric_params:
                    check["errors"].append(
                        f"numeric constructor params are not bound despite numeric elem_bits={elem_bits}: {unbound_numeric_params}"
                    )
        errors.extend(f"{item.get('op')}/{template_id}: {error}" for error in check["errors"])
        check["status"] = "pass" if not check["errors"] else "fail"
        checks.append(check)
    return checks, errors


def source_contains(template_facts: dict[str, Any], source: str, pattern: str) -> bool:
    template_dir = Path(str(template_facts.get("template_dir") or ""))
    path = template_dir / source
    if not path.exists():
        return False
    return pattern in path.read_text(encoding="utf-8")


def attention_semantics(
    selected: list[dict[str, Any]],
    model_facts: dict[str, Any],
    model_config: dict[str, Any],
    template_facts: dict[str, Any],
) -> tuple[dict[str, Any], list[str], list[dict[str, Any]]]:
    if not any(item.get("op") == "self_attention" for item in selected):
        return {"required": False, "components": []}, [], []

    selected_ops = {str(item.get("op")) for item in selected}
    selected_template_ids = {str(item.get("template_id")) for item in selected}
    attention_cfg = model_config.get("attention") or {}
    position = attention_cfg.get("position_encoding") or model_facts.get("position_encoding") or {}
    causal = bool(attention_cfg.get("causal", True))
    q_heads = model_facts.get("num_q_heads")
    kv_heads = model_facts.get("num_kv_heads")
    required_components = [
        ("qkv_projection", "DecoderBlock.scala", "Module(new QKVProjection", True),
        ("rope", "DecoderBlock.scala", "Module(new RoPE", (position.get("type") == "rope")),
        ("gqa_head_mapping", "QKVProjection.scala", "kvGroupSize", isinstance(q_heads, int) and isinstance(kv_heads, int) and q_heads != kv_heads),
        ("softmax", "DecoderBlock.scala", "Module(new Softmax", True),
        ("output_projection", "DecoderBlock.scala", "Module(new Linear(p.outLinear)", True),
        ("kv_cache", "DecoderBlock.scala", "Module(new KVCache", bool(attention_cfg.get("uses_kv_cache"))),
        ("causal_mask", "DecoderBlock.scala", "Module(new Mask", causal),
    ]
    components: list[dict[str, Any]] = []
    errors: list[str] = []
    adapters: list[dict[str, Any]] = []
    for name, source, pattern, required in required_components:
        covered = source_contains(template_facts, source, pattern)
        if name == "softmax" and ("softmax" in selected_ops or "softmax" in selected_template_ids):
            covered = True
            source = "Softmax.scala"
            pattern = "template_id=softmax"
        if name == "causal_mask" and ("causal_mask" in selected_ops or "mask" in selected_template_ids):
            covered = True
            source = "Mask.scala"
            pattern = "template_id=mask"
        if name == "causal_mask" and source_contains(template_facts, "DecoderBlock.scala", "attn.io.mask := 0.U"):
            covered = covered and ("causal_mask" in selected_ops or "mask" in selected_template_ids)
        if name == "softmax":
            covered = covered or source_contains(template_facts, "Attention.scala", "Module(new Softmax")
        status = "covered" if covered else ("not_required" if not required else "unsupported")
        component = {
            "component": name,
            "required": required,
            "status": status,
            "source": source,
            "evidence_pattern": pattern,
        }
        if name == "gqa_head_mapping":
            component["params"] = {"num_q_heads": q_heads, "num_kv_heads": kv_heads}
            if isinstance(q_heads, int) and isinstance(kv_heads, int):
                component["gqa_group_size"] = q_heads // kv_heads if kv_heads else None
                if kv_heads == 0 or q_heads % kv_heads != 0:
                    status = "unsupported"
                    component["status"] = status
        if required and status != "covered":
            message = f"self_attention semantic component {name} is required but not covered by selected templates"
            errors.append(message)
            adapters.append(
                {
                    "component": name,
                    "required_action": "bind an existing trusted template/submodule or request approval before changing template internals",
                    "reason": message,
                }
            )
        components.append(component)
    return {"required": True, "components": components}, errors, adapters


def cross_layer_trace(state: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    constraints = []
    errors: list[str] = []
    for constraint_id in REQUIRED_CROSS_LAYER_CONSTRAINTS:
        facts = optional_constraint_facts(state, constraint_id)
        present = bool(facts)
        if not present:
            errors.append(f"missing required cross-layer constraint: {constraint_id}")
        constraints.append(
            {
                "constraint": constraint_id,
                "present": present,
                "fact_keys": sorted(str(key) for key in facts.keys())[:20],
            }
        )
    return {"constraints": constraints, "status": "pass" if not errors else "fail"}, errors


def checker_result(name: str, errors: list[str], warnings: list[str] | None = None, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "checker": name,
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "warnings": warnings or [],
        "evidence": evidence or {},
    }


def llm_blocking_errors(output: dict[str, Any]) -> list[str]:
    if not output:
        return []
    errors: list[str] = []
    status = str(output.get("status") or "").strip().lower()
    if status and status not in {"ready", "pass", "approved"}:
        errors.append(f"template_selection_agent status is {output.get('status')}")
    risks = output.get("risks", [])
    if isinstance(risks, list) and risks:
        errors.append(f"template_selection_agent reported {len(risks)} unresolved risk(s)")
    return errors


def stage2_gate_policy() -> dict[str, Any]:
    return {
        "schema_version": "spatialaccagent.stage2_gate_policy.v0",
        "current_stage_blocks": [
            "any decoder operator has no trusted selected template or explicit required adapter",
            "any selected template required parameter is unbound, illegal, or only supplied by an implicit constructor default when model/numeric/board input has a value",
            "any selected template source file is missing or its metadata required parameters do not match the Chisel case-class constructor",
            "self_attention lacks selected or embedded coverage for Q/K/V projection, RoPE when required, GQA/MQA head mapping, softmax, output projection, required KV-cache behavior, or causal mask",
            "numeric policy, board memory, board runtime, board deployment, or cross-layer input-consistency constraints are absent from the template-selection trace",
            "LLM sub-agent output reports a concrete contradiction in the candidate selection for this stage",
        ],
        "not_current_stage_blocks": [
            "VCS/Verilator simulation has not been run yet",
            "Vivado synthesis, implementation, timing closure, or bitstream generation has not been run yet",
            "final generated accelerator code has not been emitted yet",
            "runtime driver, board wrapper, or full DDR/AXI top-level integration has not been generated yet",
            "later-stage numeric accuracy or board bring-up evidence is not present yet",
        ],
        "classification_rule": (
            "Put only unresolved current_stage_blocks in risks. Put not_current_stage_blocks in proposed_actions "
            "or approval_required_for. If all deterministic checker_results pass and no current_stage_blocks remain, "
            "return status='ready' and risks=[]."
        ),
    }


def build_selection(state: dict[str, Any]) -> dict[str, Any]:
    model_facts = get_constraint(state, "constraint.model.decoder").get("facts", {})
    shape_facts = get_constraint(state, "constraint.shape.model").get("facts", {})
    numeric_facts = get_constraint(state, "constraint.numeric.policy").get("facts", {})
    template_facts = get_constraint(state, "constraint.template.library").get("facts", {})
    design_space = optional_constraint_facts(state, "constraint.arch.design_space")
    memory_facts = optional_constraint_facts(state, "constraint.memory.board")
    templates = template_facts.get("templates", [])
    if not isinstance(templates, list) or not templates:
        raise TemplateSelectionError("template library constraint has no templates")

    selected: list[dict[str, Any]] = []
    missing_ops: list[str] = []

    for op in wrapper_ops(model_facts):
        template, matched_op, candidates = match_template(op, templates)
        if template:
            selected.append(make_selection("block_wrapper", op, matched_op, template, candidates))
            break
    else:
        missing_ops.append("decoder_block")

    operator_sequence = model_facts.get("operator_sequence", [])
    if not isinstance(operator_sequence, list):
        raise TemplateSelectionError("constraint.model.decoder operator_sequence must be a list")

    for op in operator_sequence:
        op_name = str(op)
        template, matched_op, candidates = match_template(op_name, templates)
        if template is None:
            missing_ops.append(op_name)
            continue
        selected.append(make_selection("operator", op_name, matched_op, template, candidates))

    add_attention_subtemplates(selected, missing_ops, templates)

    model_config = read_artifact_json(state, "artifact.input.model_config")
    parameter_bindings, binding_errors = build_parameter_bindings(
        selected,
        state,
        model_facts,
        shape_facts,
        numeric_facts,
        memory_facts,
        design_space,
    )
    source_checks, source_errors = template_source_checks(selected, template_facts, numeric_facts)
    attention, attention_errors, adapters = attention_semantics(selected, model_facts, model_config, template_facts)
    trace, trace_errors = cross_layer_trace(state)
    coverage_errors = [f"missing template for op: {op}" for op in missing_ops]
    errors = coverage_errors + binding_errors + source_errors + attention_errors + trace_errors
    checker_results = [
        checker_result(
            "operator_coverage_check",
            coverage_errors,
            evidence={"required_ops": len(operator_sequence), "missing_ops": missing_ops},
        ),
        checker_result(
            "template_parameter_binding_check",
            binding_errors,
            evidence={"binding_count": len(parameter_bindings)},
        ),
        checker_result(
            "template_source_and_interface_check",
            source_errors,
            evidence={"checked_templates": len(source_checks)},
        ),
        checker_result("attention_semantic_expansion_check", attention_errors, evidence=attention),
        checker_result("cross_layer_trace_check", trace_errors, evidence=trace),
    ]
    unsupported_bindings = [
        {
            "kind": "parameter_binding",
            "op": item["op"],
            "template_id": item["template_id"],
            "missing_params": item["missing_params"],
            "legality_errors": item["legality_errors"],
        }
        for item in parameter_bindings
        if item["status"] != "ready"
    ]
    unsupported_bindings.extend(
        {
            "kind": "template_interface",
            "op": item.get("op"),
            "template_id": item.get("template_id"),
            "errors": item.get("errors", []),
        }
        for item in source_checks
        if item.get("status") != "pass"
    )
    unsupported_bindings.extend(
        {
            "kind": "attention_semantics",
            "component": item["component"],
            "status": item["status"],
        }
        for item in attention.get("components", [])
        if item.get("required") and item.get("status") != "covered"
    )
    supported_bindings = [
        {
            "op": item["op"],
            "template_id": item["template_id"],
            "bound_params": item["bound_params"],
        }
        for item in parameter_bindings
        if item["status"] == "ready"
    ]
    unique_template_ids = sorted({item["template_id"] for item in selected})
    return {
        "schema_version": "spatialaccagent.template_selection.v0",
        "stage": "template_selection",
        "status": "ready" if not errors else "incomplete",
        "library_id": template_facts.get("library_id"),
        "model_type": model_facts.get("model_type"),
        "operator_sequence": operator_sequence,
        "selected_templates": selected,
        "selected_template_ids": unique_template_ids,
        "missing_ops": missing_ops,
        "parameter_bindings": parameter_bindings,
        "supported_bindings": supported_bindings,
        "unsupported_bindings": unsupported_bindings,
        "required_adapters": adapters,
        "template_source_checks": source_checks,
        "attention_semantics": attention,
        "cross_layer_trace": trace,
        "checker_results": checker_results,
        "stage_gate_policy": stage2_gate_policy(),
        "forbidden_edits": [
            "Do not close missing template coverage with free-form RTL.",
            "Do not rely on Chisel default constructor values when a model, numeric, or board value is available.",
            "Do not change template internals, data order, memory layout, numeric policy, or board/runtime assumptions without approval.",
        ],
        "coverage": {
            "required_ops": len(operator_sequence),
            "covered_ops": len(operator_sequence) - len([op for op in missing_ops if op != "decoder_block"]),
            "has_block_wrapper": selected[0]["role"] == "block_wrapper" if selected else False,
        },
        "constraints_touched": TOUCHED_CONSTRAINTS,
        "errors": errors,
        "warnings": [],
    }


def make_selection(
    role: str,
    op: str,
    matched_op: str | None,
    template: dict[str, Any],
    candidates: list[str],
) -> dict[str, Any]:
    return {
        "role": role,
        "op": op,
        "matched_op": matched_op,
        "template_id": template.get("template_id"),
        "source": template.get("source"),
        "required_params": template.get("required_params", []),
        "constraints_emitted": template.get("constraints_emitted", []),
        "candidate_template_ids": candidates,
    }


def update_sacg_state(
    source_state: Path,
    target_state: Path,
    selection_path: Path,
    selection: dict[str, Any],
    errors: list[str],
) -> str:
    write_json(target_state, copy.deepcopy(read_json(source_state)))
    store = SACGStore(target_state)
    transition = store.declare_transition(
        action_type="template_selection",
        touched_nodes=TOUCHED_NODES,
        touched_edges=[],
        touched_constraints=TOUCHED_CONSTRAINTS,
        note="Selected Chisel templates for model operators.",
    )
    store.bind_artifact(
        artifact_id="artifact.stage2.template_selection",
        path=str(selection_path),
        artifact_type="stage.template_selection",
        nodes=TOUCHED_NODES,
        edges=[],
        constraints=TOUCHED_CONSTRAINTS,
        producer_transition=transition["id"],
    )
    if errors:
        store.reject(transition["id"], f"strict template binding failed: {errors[:8]}")
    else:
        store.promote(transition["id"])
    store.save()
    return transition["id"]


def select_templates(args: argparse.Namespace) -> tuple[Path, dict[str, Any]]:
    source_state = args.sacg_state.resolve()
    run_dir = source_state.parents[1]
    out_dir = run_dir / "template_selection"
    out_dir.mkdir(parents=True, exist_ok=True)

    selection_path = out_dir / "template_selection.json"
    state_path = out_dir / "sacg_state.json"
    report_path = out_dir / "template_selection_report.json"

    source_data = read_json(source_state)
    selection = build_selection(source_data)
    write_json(selection_path, selection)
    team = run_design_team(
        stage="template_selection",
        objective="Strictly bind trusted templates to every model operator, source file, parameter, attention semantic, and cross-layer board/numeric constraint without drifting into free-form RTL generation.",
        state=source_data,
        candidate_artifact=selection,
        out_dir=out_dir,
    )
    design_team = team_summary(team)
    errors = list(selection.get("errors", []))
    errors.extend(team_failure_errors(design_team))
    if errors:
        llm = {"result_path": None, "output": {}}
    else:
        llm = run_stage_agent(
            agent="template_selection_agent",
            stage="template_selection",
            task=(
                "Review strict template bindings, source/interface checks, attention semantics, team decomposition, "
                "and cross-layer gate risks. Apply candidate_template_selection.stage_gate_policy exactly: report "
                "only unresolved current Stage 2 blockers in risks, move later simulation/synthesis/code-generation/"
                "board bring-up obligations to proposed_actions or approval_required_for, and return status='ready' "
                "with risks=[] only when all current Stage 2 blocks are closed."
            ),
            inputs={
                "candidate_template_selection": selection,
                "design_team": design_team,
                "source_sacg_state": str(source_state),
                "stage_gate_policy": selection.get("stage_gate_policy", {}),
            },
            out_dir=out_dir,
            fallback_summary="Strict template binding produced by deterministic template matcher and checkers.",
        )
        errors.extend(llm_blocking_errors(llm["output"]))
    if errors:
        selection["status"] = "incomplete"
        selection["errors"] = errors
        write_json(selection_path, selection)

    transition_id = update_sacg_state(source_state, state_path, selection_path, selection, errors)

    report = {
        "schema_version": "spatialaccagent.template_selection_report.v0",
        "stage": "template_selection",
        "status": "ready" if not errors else "incomplete",
        "source_sacg_state": str(source_state),
        "outputs": {
            "template_selection": str(selection_path),
            "sacg_state": str(state_path),
            "llm_agent": llm["result_path"],
            "team_subtask_plan": team["subtask_plan_path"],
            "team_aggregate": team["aggregate_path"],
        },
        "llm_agent": llm["output"],
        "design_team": design_team,
        "selected_template_ids": selection["selected_template_ids"],
        "missing_ops": selection["missing_ops"],
        "checker_results": selection.get("checker_results", []),
        "unsupported_bindings": selection.get("unsupported_bindings", []),
        "required_adapters": selection.get("required_adapters", []),
        "sacg_transition_id": transition_id,
        "errors": errors,
    }
    write_json(report_path, report)
    return report_path, report


def main(argv: list[str] | None = None) -> int:
    return run_sacg_stage("Template selection stage", select_templates, argv)


if __name__ == "__main__":
    raise SystemExit(main())
