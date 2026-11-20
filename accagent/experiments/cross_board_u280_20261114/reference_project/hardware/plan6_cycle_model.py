"""Cycle model for the Plan 6 recurrent-core workload.

The model is deliberately independent of the RTL sequencers.  It consumes the
model geometry in :mod:`plan6_models` and applies the equations in
``docs/plan6.md`` to every recurrent block and context length.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

try:
    from .plan6_models import PLAN6_MODELS
except ImportError:  # pragma: no cover - supports direct script execution
    from plan6_models import PLAN6_MODELS


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "results/plan6"
JSON_PATH = OUTPUT_DIR / "recurrent_core_cycle_model.json"
CSV_PATH = OUTPUT_DIR / "recurrent_core_cycle_model.csv"

# Plan 6 hardware-model constants.
TOTAL_CHANNELS = 96
WINDOW_SIZE = 256
CYCLES_PER_WINDOW = 4
PIPELINE_CYCLES = 5
SCALE_BUS_BITS = 256
ATTENTION_LANES = 128
NORM_LANES = 16
NORM_QUANTIZE_CYCLES = 22
NORM_FIXED_SETUP_CYCLES = 1 + 64 + 32 + 28 + 1
ELEMENTWISE_LANES = 32
BF16_BYTES = 2
KV_CACHE_BRAM_BLOCKS = 256
RAMB36_BITS = 36 * 1024
KV_CACHE_BRAM_BYTES = KV_CACHE_BRAM_BLOCKS * RAMB36_BITS // 8
USW512_BYTES_PER_WINDOW = 64
CORE_CLOCK_HZ = 200_000_000
VU9P_PREFETCH_BW_BYTES_PER_SECOND = 38.4e9
U280_PREFETCH_BW_BYTES_PER_SECOND = 390e9
PLATFORMS = {
    "vu9p_ddr4": {
        "fpga_device": "VU9P",
        "external_memory_system": "DDR4",
        "bandwidth_bytes_per_second": VU9P_PREFETCH_BW_BYTES_PER_SECOND,
    },
    "u280_hbm2": {
        "fpga_device": "U280",
        "external_memory_system": "HBM2",
        "bandwidth_bytes_per_second": U280_PREFETCH_BW_BYTES_PER_SECOND,
    },
}
PRIMARY_OPERATOR_POOL_BYTES = 672 * 4096 * 72 // 8
KV_CACHE_OFFCHIP_DEFAULT = True
MODELLED_COMPONENTS = [
    "all recurrent-core linear projections, including Huginn fused QKV and separate Gate/Up",
    "RoPE, QK/PV work, online softmax, and configured KV-cache traffic",
    "RTL-FSM-counted attention-output INT8 quantization and RMSNorm, plus modeled justnorm, SwiGLU, learned-vector scaling, residual, and slerp passes",
    "configured next-operator transfer stalls using the supplied memory bandwidth",
]
UNMODELLED_COMPONENTS = [
    "quantized payload contents and bit-exact weight/activation/KV data-path execution",
    "full recurrent-core RTL numerical execution and closed-loop activation feedback",
    "physical KV-cache banking, arbitration, and measured on-chip/off-chip placement",
    "measured DMA transactions, backpressure, and effective DDR/HBM bandwidth",
    "contention between KV-cache traffic and next-operator prefetch on shared memory ports",
    "post-route core clock, power, bitstream execution, and board measurements",
    "cross-SLR transfer stalls and operator command/setup cycles",
    "Q/K bias addition and nonlinear lookup implementation latency",
]


def ceil_div(value: int, divisor: int) -> int:
    if value < 0 or divisor <= 0:
        raise ValueError("ceil_div requires a non-negative value and positive divisor")
    return (value + divisor - 1) // divisor


def linear_cycles(output_channels: int, input_columns: int) -> int:
    """Plan 6 ``C_op`` for one USW-512 linear operator."""
    if output_channels <= 0 or input_columns <= 0:
        raise ValueError("linear dimensions must be positive")
    return (
        ceil_div(output_channels, TOTAL_CHANNELS)
        * (CYCLES_PER_WINDOW * ceil_div(input_columns, WINDOW_SIZE))
        + PIPELINE_CYCLES
        + ceil_div(output_channels * 16, SCALE_BUS_BITS)
    )


def vector_cycles(length: int, lanes: int = NORM_LANES) -> int:
    """One streaming vector pass, including one pipeline cycle."""
    if length <= 0 or lanes <= 0:
        raise ValueError("vector length and lanes must be positive")
    return ceil_div(length, lanes) + 1


def norm_cycles(length: int, lanes: int = NORM_LANES) -> int:
    """Conservative cycle count for the implemented RMSNorm/INT8 FSM."""
    chunks = ceil_div(length, lanes)
    # Collect, two read/multiply/multiply/clamp/consume passes, quantize, emit.
    return (12 + NORM_QUANTIZE_CYCLES) * chunks + NORM_FIXED_SETUP_CYCLES


def elementwise_cycles(length: int, lanes: int = ELEMENTWISE_LANES) -> int:
    """One streaming elementwise pass, including one pipeline cycle."""
    if length <= 0 or lanes <= 0:
        raise ValueError("elementwise length and lanes must be positive")
    return ceil_div(length, lanes) + 1


def usw512_bytes(output_channels: int, input_columns: int) -> int:
    """Payload bytes for a matrix stored as complete 256-element USW windows."""
    if output_channels <= 0 or input_columns <= 0:
        raise ValueError("linear dimensions must be positive")
    return output_channels * ceil_div(input_columns, WINDOW_SIZE) * USW512_BYTES_PER_WINDOW


def is_full_attention(model: dict[str, Any], block_index: int) -> bool:
    return bool((int(model["full_attention_mask"]) >> block_index) & 1)


def active_context(model: dict[str, Any], block_index: int, context_tokens: int) -> int:
    if context_tokens not in model["context_lengths"]:
        raise ValueError(
            f"unsupported context {context_tokens}; expected {model['context_lengths']}"
        )
    if is_full_attention(model, block_index) or not model["sliding_window"]:
        return context_tokens
    return min(context_tokens, int(model["sliding_window"]))


def recurrent_kv_cache_bytes(model: dict[str, Any], context_tokens: int) -> int:
    """Bytes for the key/value cache of every recurrent block and pass."""
    per_pass = sum(
        active_context(model, block, context_tokens)
        * int(model["kv_size"])
        * 2
        * BF16_BYTES
        for block in range(int(model["core_blocks"]))
    )
    return per_pass * int(model["recurrences"])


def attention_kv_cycles(
    model: dict[str, Any],
    block_index: int,
    context_tokens: int,
    *,
    clock_hz: int = CORE_CLOCK_HZ,
    kv_cache_offchip: bool = KV_CACHE_OFFCHIP_DEFAULT,
    memory_bandwidth_bytes_per_second: float = VU9P_PREFETCH_BW_BYTES_PER_SECOND,
) -> dict[str, int]:
    """Return the four terms of the Plan 6 attention/KV equation."""
    if clock_hz <= 0 or memory_bandwidth_bytes_per_second <= 0:
        raise ValueError("clock and memory bandwidth must be positive")
    active = active_context(model, block_index, context_tokens)
    rope = ceil_div(int(model["query_size"]) + int(model["kv_size"]), 32)
    qk_pv = ceil_div(2 * active * int(model["query_size"]), ATTENTION_LANES)
    softmax = active + 24
    kv_bytes = active * int(model["kv_size"]) * 2 * BF16_BYTES
    if kv_cache_offchip:
        bytes_per_cycle = memory_bandwidth_bytes_per_second / clock_hz
        kv_memory_stall = math.ceil(kv_bytes / bytes_per_cycle)
    else:
        kv_memory_stall = 0
    return {
        "rope_cycles": rope,
        "qk_pv_cycles": qk_pv,
        "softmax_cycles": softmax,
        "kv_memory_stall_cycles": kv_memory_stall,
        "active_context_tokens": active,
        "kv_cache_bytes_read": kv_bytes,
    }


def attention_quantizer_cycles(query_size: int) -> int:
    """Count scan, seven-step rounded division, and per-window writeback."""
    if query_size <= 0:
        raise ValueError("query_size must be positive")
    return 1 + 11 * query_size + 2 * ceil_div(query_size, WINDOW_SIZE)


def _attention_linear_ops(model: dict[str, Any]) -> list[tuple[str, int, int]]:
    hidden = int(model["hidden_size"])
    query = int(model["query_size"])
    kv = int(model["kv_size"])
    if model["model_name"].startswith("Huginn"):
        ops = [("qkv_proj", query + 2 * kv, hidden)]
    else:
        ops = [("q_proj", query, hidden), ("k_proj", kv, hidden), ("v_proj", kv, hidden)]
    gate_rows = int(model.get("attention_gate_rows", 0))
    if gate_rows:
        ops.append(("g_proj", gate_rows, hidden))
    ops.append(("o_proj", hidden, query))
    return ops


def _ffn_linear_ops(model: dict[str, Any]) -> list[tuple[str, int, int]]:
    hidden = int(model["hidden_size"])
    intermediate = int(model["intermediate_size"])
    if model["model_name"].startswith("Huginn"):
        return [
            ("gate_proj", intermediate, hidden),
            ("up_proj", intermediate, hidden),
            ("down_proj", hidden, intermediate),
        ]
    return [
        ("gate_proj", intermediate, hidden),
        ("up_proj", intermediate, hidden),
        ("down_proj", hidden, intermediate),
    ]


def _dory_attention_nonlinear_cycles(model: dict[str, Any]) -> int:
    query = int(model["query_size"])
    kv = int(model["kv_size"])
    # q/k justnorm, output gate/justnorm, and three-normalization slerp.
    return (
        norm_cycles(query)
        + norm_cycles(kv)
        + elementwise_cycles(query)
        + norm_cycles(query)
        + 3 * norm_cycles(int(model["hidden_size"]))
        + elementwise_cycles(int(model["hidden_size"]))
    )


def _dory_mlp_nonlinear_cycles(model: dict[str, Any]) -> int:
    intermediate = int(model["intermediate_size"])
    hidden = int(model["hidden_size"])
    # Learned gate/up scaling, SiLU product, justnorm, and slerp residual.
    return (
        3 * elementwise_cycles(intermediate)
        + norm_cycles(intermediate)
        + 3 * norm_cycles(hidden)
        + elementwise_cycles(hidden)
    )


def block_nonlinear_cycles(model: dict[str, Any]) -> int:
    """Non-linear and residual work for one physical block/pair."""
    hidden = int(model["hidden_size"])
    intermediate = int(model["intermediate_size"])
    if model["normalization"] == "ngpt_justnorm_slerp":
        return _dory_attention_nonlinear_cycles(model) + _dory_mlp_nonlinear_cycles(model)
    # Four Sandwich RMSNorms, SwiGLU, and two fused residual-add passes.
    return (
        4 * norm_cycles(hidden)
        + elementwise_cycles(intermediate)
        + 2 * elementwise_cycles(hidden)
    )


def _recurrent_boundary_cycles(model: dict[str, Any]) -> tuple[int, int, str, str]:
    """Return pre, post cycles and their operation labels."""
    hidden = int(model["hidden_size"])
    if model["model_name"].startswith("Huginn"):
        pre = linear_cycles(int(model["pre_rows"]), int(model["pre_columns"]))
        return pre, 0, "adapter", "none"
    if model["model_name"].startswith("Dory"):
        return (
            elementwise_cycles(hidden) + norm_cycles(hidden),
            norm_cycles(hidden),
            "recurrent_input_add_justnorm",
            "justnorm_loop_tail",
        )
    return 0, norm_cycles(hidden), "identity", "model_norm_loop_tail"


def _prefetch_operator_sequence(
    model: dict[str, Any],
    context_tokens: int,
    *,
    clock_hz: int,
    bandwidth_bytes_per_second: float,
    kv_cache_offchip: bool,
) -> list[dict[str, int | str]]:
    """Return matrix transfers and the compute window available for each next transfer."""
    hidden = int(model["hidden_size"])
    intermediate = int(model["intermediate_size"])
    dory = model["normalization"] == "ngpt_justnorm_slerp"
    huginn = model["model_name"].startswith("Huginn")
    records: list[dict[str, int | str]] = []
    dory_slerp = 3 * norm_cycles(hidden) + elementwise_cycles(hidden)
    residual_norm = elementwise_cycles(hidden) + norm_cycles(hidden)
    attention_prelude = {
        block: attention_kv_cycles(
            model,
            block,
            context_tokens,
            clock_hz=clock_hz,
            kv_cache_offchip=kv_cache_offchip,
            memory_bandwidth_bytes_per_second=bandwidth_bytes_per_second,
        )
        for block in range(int(model["core_blocks"]))
    }

    def append_operator(name: str, rows: int, columns: int, prelude: int = 0) -> None:
        records.append({
            "name": name,
            "bytes": usw512_bytes(rows, columns),
            "cycles": linear_cycles(rows, columns),
            "prelude_cycles": prelude,
        })

    for recurrence in range(int(model["recurrences"])):
        if huginn:
            append_operator(
                "adapter",
                int(model["pre_rows"]),
                int(model["pre_columns"]),
                residual_norm if recurrence else 0,
            )
        for block in range(int(model["core_blocks"])):
            if dory:
                start_prelude = int(model.get("pre_vector_length", hidden))
                if block == 0:
                    start_prelude = elementwise_cycles(hidden) + norm_cycles(hidden)
                    if recurrence:
                        start_prelude += dory_slerp + norm_cycles(hidden)
                else:
                    start_prelude = dory_slerp
                for name, rows, columns in _attention_linear_ops(model):
                    prelude = 0
                    terms = attention_prelude[block]
                    if name == "q_proj":
                        prelude = start_prelude
                    elif name == "g_proj":
                        prelude = (
                            terms["rope_cycles"]
                            + norm_cycles(int(model["query_size"]))
                            + norm_cycles(int(model["kv_size"]))
                        )
                    elif name == "o_proj":
                        prelude = (
                            terms["qk_pv_cycles"]
                            + terms["softmax_cycles"]
                            + attention_quantizer_cycles(int(model["query_size"]))
                            + terms["kv_memory_stall_cycles"]
                            + elementwise_cycles(int(model["query_size"]))
                            + norm_cycles(int(model["query_size"]))
                        )
                    append_operator(name, rows, columns, prelude)

                for name, rows, columns in _ffn_linear_ops(model):
                    prelude = dory_slerp if name == "gate_proj" else 0
                    if name == "down_proj":
                        prelude = (
                            3 * elementwise_cycles(intermediate)
                            + norm_cycles(intermediate)
                        )
                    append_operator(name, rows, columns, prelude)
            else:
                attn_ops = _attention_linear_ops(model)
                for index, (name, rows, columns) in enumerate(attn_ops):
                    prelude = norm_cycles(hidden) if index == 0 and model.get("has_pre_attention_norm", True) else 0
                    if index == 0 and block > 0:
                        prelude += residual_norm + norm_cycles(hidden)
                    elif index == 0 and block == 0 and recurrence and not huginn:
                        prelude += residual_norm + norm_cycles(hidden)
                    if name == "o_proj":
                        terms = attention_prelude[block]
                        prelude = sum(
                            terms[key]
                            for key in (
                                "rope_cycles", "qk_pv_cycles", "softmax_cycles",
                                "kv_memory_stall_cycles",
                            )
                        )
                        prelude += attention_quantizer_cycles(int(model["query_size"]))
                    append_operator(name, rows, columns, prelude)

                for index, (name, rows, columns) in enumerate(_ffn_linear_ops(model)):
                    prelude = 0
                    if index == 0:
                        prelude = residual_norm + norm_cycles(hidden)
                    if name == "down_proj":
                        prelude = elementwise_cycles(intermediate)
                    append_operator(name, rows, columns, prelude)

    return records


def prefetch_stall_cycles(
    model: dict[str, Any],
    context_tokens: int,
    *,
    clock_hz: int = CORE_CLOCK_HZ,
    bandwidth_bytes_per_second: float = VU9P_PREFETCH_BW_BYTES_PER_SECOND,
    retained_next_operator_bytes: int = 0,
    kv_cache_offchip: bool = KV_CACHE_OFFCHIP_DEFAULT,
) -> dict[str, int]:
    """Estimate unhidden next-operator prefetch cycles.

    ``retained_next_operator_bytes`` is an explicit reuse assumption. It does
    not infer that the active operator pool can also retain the next operator.
    """
    if clock_hz <= 0 or bandwidth_bytes_per_second <= 0 or retained_next_operator_bytes < 0:
        raise ValueError("clock, bandwidth and residency values are invalid")
    records = _prefetch_operator_sequence(
        model,
        context_tokens,
        clock_hz=clock_hz,
        bandwidth_bytes_per_second=bandwidth_bytes_per_second,
        kv_cache_offchip=kv_cache_offchip,
    )
    bytes_per_cycle = bandwidth_bytes_per_second / clock_hz
    transitions = max(0, len(records) - 1)
    stall = 0
    prefetched = 0
    for index, current in enumerate(records[:-1]):
        next_record = records[index + 1]
        offchip = max(0, int(next_record["bytes"]) - retained_next_operator_bytes)
        prefetched += offchip
        prefetch_cycles = math.ceil(offchip / bytes_per_cycle)
        overlap_cycles = int(current["cycles"]) + int(next_record["prelude_cycles"])
        stall += max(0, prefetch_cycles - overlap_cycles)
    return {
        "prefetch_stall_cycles": stall,
        "prefetched_bytes": prefetched,
        "prefetch_transitions": transitions,
        "token_matrix_bytes": sum(int(record["bytes"]) for record in records),
        "initial_matrix_bytes": int(records[0]["bytes"]) if records else 0,
    }


def estimate_case(
    model_name: str,
    context_tokens: int,
    *,
    platform: str = "vu9p_ddr4",
    clock_hz: int = CORE_CLOCK_HZ,
    prefetch_bandwidth_bytes_per_second: float | None = None,
    retained_next_operator_bytes: int = 0,
    kv_cache_offchip: bool = KV_CACHE_OFFCHIP_DEFAULT,
) -> dict[str, Any]:
    if model_name not in PLAN6_MODELS:
        raise KeyError(f"unknown Plan 6 model {model_name}")
    if platform not in PLATFORMS:
        raise KeyError(f"unknown Plan 6 platform {platform}")
    if clock_hz <= 0:
        raise ValueError("clock_hz must be positive")
    if prefetch_bandwidth_bytes_per_second is None:
        prefetch_bandwidth_bytes_per_second = PLATFORMS[platform][
            "bandwidth_bytes_per_second"
        ]
    model = PLAN6_MODELS[model_name]
    blocks = int(model["core_blocks"])
    recurrences = int(model["recurrences"])
    attn_ops = _attention_linear_ops(model)
    ffn_ops = _ffn_linear_ops(model)
    attn_linear = sum(linear_cycles(rows, columns) for _, rows, columns in attn_ops)
    ffn_linear = sum(linear_cycles(rows, columns) for _, rows, columns in ffn_ops)
    attn_kv_terms = [
        attention_kv_cycles(
            model,
            block,
            context_tokens,
            clock_hz=clock_hz,
            kv_cache_offchip=kv_cache_offchip,
            memory_bandwidth_bytes_per_second=prefetch_bandwidth_bytes_per_second,
        )
        for block in range(blocks)
    ]
    attn_kv = sum(
        row["rope_cycles"] + row["qk_pv_cycles"] + row["softmax_cycles"]
        + row["kv_memory_stall_cycles"]
        for row in attn_kv_terms
    )
    nonlinear_block = block_nonlinear_cycles(model) + attention_quantizer_cycles(
        int(model["query_size"])
    )
    pre_cycles, post_cycles, pre_label, post_label = _recurrent_boundary_cycles(model)
    prefetch = prefetch_stall_cycles(
        model,
        context_tokens,
        clock_hz=clock_hz,
        bandwidth_bytes_per_second=prefetch_bandwidth_bytes_per_second,
        retained_next_operator_bytes=retained_next_operator_bytes,
        kv_cache_offchip=kv_cache_offchip,
    )
    attention_linear_total = recurrences * blocks * attn_linear
    ffn_linear_total = recurrences * blocks * ffn_linear
    attention_kv_total = recurrences * attn_kv
    nonlinear_total = recurrences * (blocks * nonlinear_block + pre_cycles + post_cycles)
    total_cycles = (
        attention_linear_total
        + ffn_linear_total
        + attention_kv_total
        + nonlinear_total
        + prefetch["prefetch_stall_cycles"]
    )
    categories = {
        "attention_linear_cycles": attention_linear_total,
        "attention_kv_cycles": attention_kv_total,
        "ffn_linear_cycles": ffn_linear_total,
        "nonlinear_reinjection_cycles": nonlinear_total,
        "prefetch_stall_cycles": prefetch["prefetch_stall_cycles"],
    }
    if sum(categories.values()) != total_cycles:
        raise AssertionError("cycle categories do not sum to total")
    category_latency_ms = {
        name.removesuffix("_cycles"): cycles / clock_hz * 1000.0
        for name, cycles in categories.items()
    }
    category_percent = {
        name.removesuffix("_cycles"): cycles / total_cycles * 100.0
        for name, cycles in categories.items()
    }
    active_contexts = sorted({row["active_context_tokens"] for row in attn_kv_terms})
    kv_cache_window_bytes = [row["kv_cache_bytes_read"] for row in attn_kv_terms]
    kv_cache_core_bytes = recurrent_kv_cache_bytes(model, context_tokens)
    return {
        "result_kind": "equation_estimate_not_measurement",
        "evaluation_mode": "analytical_equation_model_with_RTL_FSM_cycles",
        "platform": platform,
        "fpga_device": PLATFORMS[platform]["fpga_device"],
        "external_memory_system": PLATFORMS[platform]["external_memory_system"],
        "model": model_name,
        "model_name": model["model_name"],
        "scope": "complete recurrent core, including all configured blocks and recurrences",
        "context_tokens": context_tokens,
        "assumed_core_clock_hz": clock_hz,
        "assumed_prefetch_bandwidth_bytes_per_second": prefetch_bandwidth_bytes_per_second,
        "assumed_retained_next_operator_bytes": retained_next_operator_bytes,
        "kv_cache_offchip": kv_cache_offchip,
        "kv_cache_placement_assumption": (
            "external_memory_streamed_through_on_chip_window"
            if kv_cache_offchip else "on_chip_assumed"
        ),
        "kv_cache_mode": model.get("recurrent_kv_cache_mode", model.get("kv_cache_mode")),
        "kv_cache_copies": blocks * recurrences,
        "kv_cache_onchip_window_capacity_bytes": KV_CACHE_BRAM_BYTES,
        "kv_cache_window_bytes_per_block": kv_cache_window_bytes,
        "kv_cache_window_max_bytes_per_block": max(kv_cache_window_bytes, default=0),
        "kv_cache_window_fits_onchip": max(kv_cache_window_bytes, default=0) <= KV_CACHE_BRAM_BYTES,
        "kv_cache_bytes_per_recurrent_core": kv_cache_core_bytes,
        "kv_cache_read_bytes_per_token": kv_cache_core_bytes,
        "core_blocks": blocks,
        "recurrences": recurrences,
        "active_context_tokens": active_contexts,
        "full_attention_blocks": [i for i in range(blocks) if is_full_attention(model, i)],
        "attention_linear_ops": [{"name": n, "rows": r, "columns": c, "cycles": linear_cycles(r, c)} for n, r, c in attn_ops],
        "ffn_linear_ops": [{"name": n, "rows": r, "columns": c, "cycles": linear_cycles(r, c)} for n, r, c in ffn_ops],
        "boundary": {
            "pre_label": pre_label,
            "pre_cycles_per_recurrence": pre_cycles,
            "post_label": post_label,
            "post_cycles_per_recurrence": post_cycles,
        },
        "category_cycles": categories,
        "category_latency_ms_per_token": category_latency_ms,
        "category_percent_per_token": category_percent,
        "estimated_cycles_per_token": total_cycles,
        "estimated_latency_ms_per_token": total_cycles / clock_hz * 1000.0,
        "estimated_tokens_per_second": clock_hz / total_cycles,
        "prefetched_bytes": prefetch["prefetched_bytes"],
        "prefetch_transitions": prefetch["prefetch_transitions"],
        "token_matrix_bytes": prefetch["token_matrix_bytes"],
        "initial_matrix_bytes": prefetch["initial_matrix_bytes"],
        "kv_cache_bytes_read_per_block": kv_cache_window_bytes,
    }


def all_cases(**kwargs: Any) -> list[dict[str, Any]]:
    return [
        estimate_case(model_name, context, platform=platform, **kwargs)
        for model_name in PLAN6_MODELS
        for context in PLAN6_MODELS[model_name]["context_lengths"]
        for platform in PLATFORMS
    ]


def write_outputs(
    json_path: Path = JSON_PATH,
    csv_path: Path = CSV_PATH,
    **kwargs: Any,
) -> tuple[Path, Path]:
    cases = all_cases(**kwargs)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "format": "Plan6-Recurrent-Core-Cycle-Model-v4",
        "result_kind": "equation_estimate_not_measurement",
        "evaluation_mode": "analytical_equation_model_with_RTL_FSM_cycles",
        "scope": "complete recurrent core, including all configured blocks and recurrences",
        "modelled_components": MODELLED_COMPONENTS,
        "unmodelled_components": UNMODELLED_COMPONENTS,
        "assumptions": {
            "total_channels": TOTAL_CHANNELS,
            "window_size": WINDOW_SIZE,
            "cycles_per_window": CYCLES_PER_WINDOW,
            "pipeline_cycles": PIPELINE_CYCLES,
            "scale_bus_bits": SCALE_BUS_BITS,
            "attention_lanes": ATTENTION_LANES,
            "norm_lanes": NORM_LANES,
            "elementwise_lanes": ELEMENTWISE_LANES,
            "usw512_bytes_per_window": USW512_BYTES_PER_WINDOW,
            "primary_operator_pool_bytes": PRIMARY_OPERATOR_POOL_BYTES,
            "kv_cache_bram_blocks": KV_CACHE_BRAM_BLOCKS,
            "ramb36_bits": RAMB36_BITS,
            "kv_cache_onchip_window_capacity_bytes": KV_CACHE_BRAM_BYTES,
            "default_core_clock_hz": CORE_CLOCK_HZ,
            "default_vu9p_prefetch_bandwidth_bytes_per_second": VU9P_PREFETCH_BW_BYTES_PER_SECOND,
            "default_u280_prefetch_bandwidth_bytes_per_second": U280_PREFETCH_BW_BYTES_PER_SECOND,
            "platforms": PLATFORMS,
            "prefetch_reuse_rule": "max(0, next_operator_bytes - assumed_retained_next_operator_bytes)",
            "initial_operator_load": "excluded; first matrix is assumed ready before the measured token",
            "prefetch_transition_rule": "only adjacent matrices within the token; no transfer after its final matrix",
            "kv_cache_stall_rule": "external KV bytes divided by configured bandwidth when kv_cache_offchip=true",
            "normalization_cycles": "conservative 28*ceil(vector_length/16)+61; includes the 28-cycle divide path",
            "attention_output_quantization_cycles": "1+2*query_size+2*ceil(query_size/256); included in nonlinear cycles and pre-O-projection overlap",
            "prefetch_overlap_rule": "current matrix cycles plus the non-matrix stages before the next matrix",
            "synchronization_and_setup": "cross-SLR and command/setup cycles are not modeled",
        },
        "cases": cases,
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")

    fields = [
        "result_kind", "platform", "fpga_device", "external_memory_system",
        "model", "model_name", "scope", "context_tokens", "evaluation_mode",
        "unmodelled_components",
        "assumed_core_clock_hz", "assumed_prefetch_bandwidth_bytes_per_second",
        "assumed_retained_next_operator_bytes", "kv_cache_offchip", "kv_cache_placement_assumption", "kv_cache_mode",
        "kv_cache_copies", "kv_cache_onchip_window_capacity_bytes",
        "kv_cache_window_max_bytes_per_block", "kv_cache_window_fits_onchip",
        "kv_cache_bytes_per_recurrent_core", "kv_cache_read_bytes_per_token",
        "core_blocks", "recurrences", "active_context_tokens",
        "estimated_cycles_per_token", "estimated_latency_ms_per_token", "estimated_tokens_per_second",
        "attention_linear_cycles", "attention_kv_cycles", "ffn_linear_cycles",
        "nonlinear_reinjection_cycles", "prefetch_stall_cycles", "prefetched_bytes",
        "prefetch_transitions", "token_matrix_bytes", "initial_matrix_bytes",
        "attention_linear_ms_per_token", "attention_linear_percent",
        "attention_kv_ms_per_token", "attention_kv_percent",
        "ffn_linear_ms_per_token", "ffn_linear_percent",
        "nonlinear_reinjection_ms_per_token", "nonlinear_reinjection_percent",
        "prefetch_stall_ms_per_token", "prefetch_stall_percent",
    ]
    with csv_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for case in cases:
            row = {key: case[key] for key in fields if key in case}
            row.update(case["category_cycles"])
            for category, latency in case["category_latency_ms_per_token"].items():
                row[f"{category}_ms_per_token"] = latency
            for category, percentage in case["category_percent_per_token"].items():
                row[f"{category}_percent"] = percentage
            row["unmodelled_components"] = "; ".join(UNMODELLED_COMPONENTS)
            row["active_context_tokens"] = ";".join(map(str, case["active_context_tokens"]))
            writer.writerow(row)
    return json_path, csv_path


if __name__ == "__main__":
    paths = write_outputs()
    print("\n".join(str(path) for path in paths))
