"""Measured-trace anchored memory bandwidth sensitivity for Plan 6."""

from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "results/plan6/memory_bandwidth_sensitivity_20261028.json"
TRACE_PATH = "results/plan6/address_slice_20261028/huginn_shell_cycle_mt.log"

OBSERVED = {
    "model": "Huginn-3.5B",
    "scope": "4 recurrent blocks x 32 recurrences, context 512",
    "core_clock_hz": 100_000_000,
    "shell_cycles": 225_187_127,
    "read_bytes": 13_311_334_400,
    "read_beats": 207_989_600,
    "exclusive_ddr_dma_cycles": 184_316_821,
    "linear_compute_cycles": 8_653_568,
    "attention_cycles": 14_699_520,
    "norm_cycles": 5_795_328,
    "activation_cycles": 8_448_896,
    "linear_pipeline_drain_cycles": 593_824,
    "rope_cycles": 7_040,
    "uram_ring_stall_cycles": 2_663_584,
    "control_wait_cycles": 8_546,
}

CORE_CLOCK_HZ = 225_000_000
HBM_CHANNEL_WIDTH_BITS = 256
HBM_CHANNEL_CLOCK_HZ = 450_000_000
HBM_CHANNEL_COUNT = 32
U280_EFFECTIVE_BANDWIDTH_BYTES_PER_SECOND = 390_000_000_000
GPU_REFERENCE_LATENCY_MS = 132.32
BEAT_BYTES = 64
UNIQUE_WEIGHT_BYTES = 400_834_560 + 14_192_640
PRIMARY_POOL_BYTES = 672 * 4096 * 72 // 8
SHADOW_RING_BYTES = 128 * 4096 * 72 // 8
RECURRENCES = 32


def ceil_div(value: int, divisor: int) -> int:
    return (value + divisor - 1) // divisor


def nonmemory_cycles() -> int:
    return OBSERVED["shell_cycles"] - OBSERVED["exclusive_ddr_dma_cycles"]


def requested_optimization_nonmemory_cycles() -> dict[str, int]:
    measured_nonmemory = nonmemory_cycles()
    attention_saved = OBSERVED["attention_cycles"] - 2_200_000
    norm_activation_saved = OBSERVED["norm_cycles"] + OBSERVED["activation_cycles"]
    linear_saved = OBSERVED["linear_compute_cycles"] // 2
    remaining = measured_nonmemory - attention_saved - norm_activation_saved - linear_saved
    return {
        "measured_nonmemory_cycles": measured_nonmemory,
        "attention_target_cycles": 2_200_000,
        "assumed_norm_activation_hidden_cycles": norm_activation_saved,
        "assumed_192_channel_linear_cycles": OBSERVED["linear_compute_cycles"] - linear_saved,
        "ideal_optimized_nonmemory_cycles": remaining,
    }


def scenario(name: str, bandwidth_bytes_per_second: float, clock_hz: int, label: str) -> dict[str, int | float | str]:
    memory_cycles = math.ceil(OBSERVED["read_bytes"] * clock_hz / bandwidth_bytes_per_second)
    current_work_cycles = nonmemory_cycles()
    optimized_work_cycles = requested_optimization_nonmemory_cycles()[
        "ideal_optimized_nonmemory_cycles"
    ]
    current_lower_bound_cycles = max(memory_cycles, current_work_cycles)
    optimized_lower_bound_cycles = max(memory_cycles, optimized_work_cycles)
    optimized_latency_ms = optimized_lower_bound_cycles * 1000.0 / clock_hz
    return {
        "name": name,
        "classification": label,
        "assumed_core_clock_hz": clock_hz,
        "assumed_bandwidth_bytes_per_second": bandwidth_bytes_per_second,
        "equivalent_64B_beats_per_core_cycle": bandwidth_bytes_per_second / (BEAT_BYTES * clock_hz),
        "read_transfer_lower_bound_cycles": memory_cycles,
        "read_transfer_lower_bound_ms": OBSERVED["read_bytes"] * 1000.0 / bandwidth_bytes_per_second,
        "unchanged_work_total_lower_bound_cycles": current_lower_bound_cycles,
        "unchanged_work_total_lower_bound_ms": current_lower_bound_cycles * 1000.0 / clock_hz,
        "all_requested_optimizations_total_lower_bound_cycles": optimized_lower_bound_cycles,
        "all_requested_optimizations_total_lower_bound_ms": optimized_latency_ms,
        "lower_bound_speedup_vs_4090_reference": GPU_REFERENCE_LATENCY_MS / optimized_latency_ms,
    }


def u280_optimization_waterfall() -> list[dict[str, int | float | str]]:
    norm_activation_cycles = OBSERVED["norm_cycles"] + OBSERVED["activation_cycles"]
    attention_cycles_saved = OBSERVED["attention_cycles"] - 2_200_000
    linear_cycles_saved = OBSERVED["linear_compute_cycles"] // 2
    resident_bytes = min(PRIMARY_POOL_BYTES + SHADOW_RING_BYTES, UNIQUE_WEIGHT_BYTES)
    recurrence_reuse_bytes = resident_bytes * (RECURRENCES - 1)
    variants = [
        (
            "u280_hbm_only",
            OBSERVED["read_bytes"],
            nonmemory_cycles(),
            "390 GB/s effective HBM assumption; measured non-memory cycle counts retained",
        ),
        (
            "plus_norm_activation_stream_fusion",
            OBSERVED["read_bytes"],
            nonmemory_cycles() - norm_activation_cycles,
            "all measured Norm and activation cycles assumed hidden",
        ),
        (
            "plus_attention_pipeline",
            OBSERVED["read_bytes"],
            nonmemory_cycles() - norm_activation_cycles - attention_cycles_saved,
            "Attention assumed reduced from measured 14,699,520 to 2,200,000 cycles",
        ),
        (
            "plus_192_channel_linear",
            OBSERVED["read_bytes"],
            nonmemory_cycles() - norm_activation_cycles - attention_cycles_saved - linear_cycles_saved,
            "linear compute assumed halved; no 192-channel RTL result",
        ),
        (
            "plus_primary_and_shadow_weight_residency",
            OBSERVED["read_bytes"] - recurrence_reuse_bytes,
            nonmemory_cycles() - norm_activation_cycles - attention_cycles_saved - linear_cycles_saved,
            "primary and shadow capacities assumed to retain one identical region across 32 recurrences",
        ),
    ]
    rows = []
    for name, read_bytes, work_cycles, assumption in variants:
        transfer_cycles = math.ceil(read_bytes * CORE_CLOCK_HZ / U280_EFFECTIVE_BANDWIDTH_BYTES_PER_SECOND)
        total_cycles = max(transfer_cycles, work_cycles)
        latency_ms = total_cycles * 1000.0 / CORE_CLOCK_HZ
        rows.append({
            "name": name,
            "classification": "idealized U280 HBM scenario; not RTL, implementation, or board measurement",
            "assumption": assumption,
            "read_bytes": read_bytes,
            "read_transfer_lower_bound_cycles": transfer_cycles,
            "remaining_nonmemory_cycles": work_cycles,
            "total_cycles_lower_bound_with_perfect_overlap": total_cycles,
            "latency_ms_lower_bound_at_assumed_225mhz": latency_ms,
            "speedup_vs_4090_reference_lower_bound": GPU_REFERENCE_LATENCY_MS / latency_ms,
        })
    return rows


def build_report() -> dict[str, object]:
    observed_latency_ms = OBSERVED["shell_cycles"] * 1000.0 / OBSERVED["core_clock_hz"]
    repeated_capacity_bytes = min(PRIMARY_POOL_BYTES, UNIQUE_WEIGHT_BYTES)
    total_pool_bytes = PRIMARY_POOL_BYTES + SHADOW_RING_BYTES
    optimized_work_ms = (
        requested_optimization_nonmemory_cycles()["ideal_optimized_nonmemory_cycles"]
        * 1000.0
        / CORE_CLOCK_HZ
    )
    target_speedups = []
    for target_speedup in (2.0, 2.5, 3.0, 3.7):
        target_latency_ms = GPU_REFERENCE_LATENCY_MS / target_speedup
        required_bandwidth = OBSERVED["read_bytes"] / (target_latency_ms / 1000.0)
        target_speedups.append({
            "target_speedup_vs_4090": target_speedup,
            "target_latency_ms": target_latency_ms,
            "minimum_read_bandwidth_bytes_per_second": required_bandwidth,
            "equivalent_64B_beats_per_225mhz_core_cycle": required_bandwidth / (BEAT_BYTES * CORE_CLOCK_HZ),
            "attainable_under_idealized_nonmemory_floor": target_latency_ms >= optimized_work_ms,
        })
    return {
        "format": "Plan6-Memory-Bandwidth-Sensitivity-v1",
        "result_kind": "measured_trace_and_idealized_scenario_bounds",
        "trace_path": TRACE_PATH,
        "measured_run": {
            **OBSERVED,
            "latency_ms_at_configured_clock": observed_latency_ms,
            "effective_read_bandwidth_bytes_per_second": OBSERVED["read_bytes"] * OBSERVED["core_clock_hz"] / OBSERVED["shell_cycles"],
            "read_beats_per_shell_cycle": OBSERVED["read_beats"] / OBSERVED["shell_cycles"],
            "exclusive_nonmemory_cycles": nonmemory_cycles(),
        },
        "interface_audit": {
            "accelerator_read_masters": 1,
            "accelerator_read_data_width_bits": 512,
            "accelerator_core_side_max_beats_per_cycle": 1,
            "maximum_outstanding_read_bursts": 1,
            "shell_ddr4_controllers": 2,
            "current_accelerator_connection": "rtwsr_9p_axi_0/M_AXI -> rtwsr_dma_cc -> axi_interconnect_1 -> ddr4_0",
            "other_ddr4_controller_connection": "axi_interconnect_2 -> ddr4_1; no RTWSR M_AXI master is connected",
            "core_to_ddr_clock_converter": True,
            "source": "VU9P Plan 6 Block Design, rtwsr_9p_axi.sv, and rtwsr_weight_dma.sv",
        },
        "u280_hbm_platform_assumptions": {
            "platform_status": "user reports no available U280 board or reference project; projection only",
            "effective_bandwidth_bytes_per_second": U280_EFFECTIVE_BANDWIDTH_BYTES_PER_SECOND,
            "hbm_channels": HBM_CHANNEL_COUNT,
            "assumed_channel_width_bits": HBM_CHANNEL_WIDTH_BITS,
            "assumed_channel_clock_hz": HBM_CHANNEL_CLOCK_HZ,
            "aggregate_channel_peak_bytes_per_second": HBM_CHANNEL_COUNT * HBM_CHANNEL_WIDTH_BITS // 8 * HBM_CHANNEL_CLOCK_HZ,
            "channels_needed_for_effective_bandwidth": math.ceil(
                U280_EFFECTIVE_BANDWIDTH_BYTES_PER_SECOND
                / (HBM_CHANNEL_WIDTH_BITS / 8 * HBM_CHANNEL_CLOCK_HZ)
            ),
            "equivalent_512bit_beats_per_225mhz_core_cycle": U280_EFFECTIVE_BANDWIDTH_BYTES_PER_SECOND / (BEAT_BYTES * CORE_CLOCK_HZ),
            "required_interface_change": "stripe concurrent DMA reads over HBM channels and merge responses; current RTL has one serialized 512-bit M_AXI read path",
        },
        "onchip_residency": {
            "unique_weight_payload_bytes": UNIQUE_WEIGHT_BYTES,
            "primary_pool_bytes": PRIMARY_POOL_BYTES,
            "streaming_shadow_ring_bytes": SHADOW_RING_BYTES,
            "maximum_unique_weight_fraction_in_primary_pool": PRIMARY_POOL_BYTES / UNIQUE_WEIGHT_BYTES,
            "maximum_unique_weight_fraction_in_primary_plus_shadow": total_pool_bytes / UNIQUE_WEIGHT_BYTES,
            "maximum_32_recurrence_traffic_saving_if_primary_pool_pins_one_region": repeated_capacity_bytes * (RECURRENCES - 1),
            "maximum_traffic_fraction_saved_under_that_assumption": repeated_capacity_bytes * (RECURRENCES - 1) / OBSERVED["read_bytes"],
            "assumption": "the pinned region is preserved across all 32 recurrences without displacing streamed operators",
            "primary_plus_shadow_capacity_bytes": total_pool_bytes,
            "maximum_32_recurrence_traffic_saving_if_both_pools_pin_one_region": min(total_pool_bytes, UNIQUE_WEIGHT_BYTES) * (RECURRENCES - 1),
            "maximum_traffic_fraction_saved_if_both_pools_are_available_for_pinning": min(total_pool_bytes, UNIQUE_WEIGHT_BYTES) * (RECURRENCES - 1) / OBSERVED["read_bytes"],
        },
        "optimization_assumptions": {
            **requested_optimization_nonmemory_cycles(),
            "core_clock_hz": CORE_CLOCK_HZ,
            "norm_activation_fusion_assumption": "all measured Norm and activation cycles are hidden by GEMV; not an RTL result",
            "attention_assumption": "14,699,520 cycles reduced to 2,200,000 as proposed in docs/new_hardware_plan.md",
            "linear_assumption": "192 channels halve measured linear compute cycles; not an RTL result",
            "overlap_assumption": "memory transfer is perfectly overlapped with remaining work",
            "omitted_cycles": "shell setup, transfer startup, backpressure changes, control changes, and routing effects",
            "idealized_nonmemory_latency_floor_ms_at_assumed_clock": optimized_work_ms,
        },
        "u280_optimization_waterfall": u280_optimization_waterfall(),
        "target_bandwidth_requirements": target_speedups,
        "scenarios": [
            scenario("vu9p_single_m_axi_100mhz", 1 * BEAT_BYTES * 100_000_000, 100_000_000, "current-interface throughput ceiling; measured RTL uses one core-side beat/cycle"),
            scenario("vu9p_single_m_axi_225mhz", 1 * BEAT_BYTES * CORE_CLOCK_HZ, CORE_CLOCK_HZ, "frequency-scaled current-interface ceiling; 225 MHz full-core timing is unverified"),
            scenario("vu9p_dual_m_axi_225mhz", 2 * BEAT_BYTES * CORE_CLOCK_HZ, CORE_CLOCK_HZ, "hypothetical two independent 512-bit accelerator read paths"),
            scenario("six_beats_per_core_cycle_225mhz", 6 * BEAT_BYTES * CORE_CLOCK_HZ, CORE_CLOCK_HZ, "hypothetical multi-channel architecture"),
            scenario("eight_beats_per_core_cycle_225mhz", 8 * BEAT_BYTES * CORE_CLOCK_HZ, CORE_CLOCK_HZ, "hypothetical multi-channel architecture"),
            scenario("u280_hbm2_390GBps_225mhz", 390_000_000_000, CORE_CLOCK_HZ, "HBM platform reference; not a VU9P measurement"),
            scenario("hbm2e_650GBps_225mhz", 650_000_000_000, CORE_CLOCK_HZ, "HBM platform reference; not a VU9P measurement"),
        ],
        "batch_weight_reuse": [
            {
                "batch_tokens": batch,
                "assumption": "every operator payload is loaded once and reused across all tokens; requires a batched compute path not present in current RTL",
                "external_read_bytes_per_token": OBSERVED["read_bytes"] / batch,
                "transfer_lower_bound_ms_per_token_at_38_4gbps": OBSERVED["read_bytes"] * 1000.0 / (batch * 38_400_000_000),
                "transfer_lower_bound_ms_per_token_at_current_single_m_axi_225mhz": OBSERVED["read_bytes"] * 1000.0 / (batch * BEAT_BYTES * CORE_CLOCK_HZ),
            }
            for batch in (8, 16)
        ],
        "gpu_reference": {
            "latency_ms": GPU_REFERENCE_LATENCY_MS,
            "source": "docs/hardware_architecture_and_performance.md",
            "scope_match_verified_by_this_script": False,
        },
    }


if __name__ == "__main__":
    report = build_report()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(OUTPUT_PATH)
