"""Calibrated structural cost estimates, never substitutes for tool results."""

from __future__ import annotations

import hashlib
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


MODEL = "calibrated_bounded_ddr_pipeline_ratio_v20_attention_output_reuse"
RESOURCE_KEYS = ("lut", "ff", "dsp", "bram36", "bram18", "uram")
# Estimated and structural candidates should retain implementation headroom;
# fitting just below a discovered capacity is not a good final design point.
RESOURCE_HEADROOM_FRACTION = 0.85


def linear_schedule_id(source: str | None = None) -> str:
    if source is None:
        source = (Path(__file__).parent / "templates/operator_chisel/Linear.scala").read_text(encoding="utf-8")
    match = re.search(r'val\s+scheduleId\s*:\s*String\s*=\s*"([^"]+)"', source)
    return match.group(1) if match else "legacy_blocking_fp"


def _integer_norm_service(
    hidden: int, lanes: int, source: str | None = None,
) -> tuple[int, dict[str, int]]:
    """Count one no-stall IntegerVectorNorm token from its bound FSM source."""
    if source is None:
        source = (Path(__file__).parent / "templates/operator_chisel/Norm.scala").read_text(encoding="utf-8")
    beats = math.ceil(hidden / lanes)
    sqrt_iterations = 32  # PhysicalIntegerSqrt(64): one bit-pair per cycle.
    stats_capture_cycles = 2 if "statsAccumulatePending" in source else 1
    finalize_stages = re.findall(r"finalizeStage\s*===\s*(\d+)\.U", source)
    finalize_cycles = max(map(int, finalize_stages)) + 1 if finalize_stages else 1
    reciprocal_match = re.search(
        r"when\(state === sReciprocal\)\s*\{.*?divIterationReg === (\d+)\.U",
        source,
        re.S,
    )
    reciprocal_cycles = int(reciprocal_match.group(1)) + 1 if reciprocal_match else 1
    emit_stages = re.findall(r"emitStage\s*===\s*(\d+)\.U", source)
    emit_capture_cycles = max(map(int, emit_stages)) + 1 if emit_stages else 1
    components = {
        "input_collect": beats,
        "statistics_read_capture": (1 + stats_capture_cycles) * beats,
        "statistics_finalize": finalize_cycles,
        "sqrt_issue": 1,
        "sqrt_iterations": sqrt_iterations,
        "sqrt_result_accept": 1,
        "reciprocal": reciprocal_cycles,
        "output_read_capture_and_handshake": (1 + emit_capture_cycles + 1) * beats,
    }
    return sum(components.values()), components


def _integer_linear_service_profile(
    *, input_dim: int, output_dim: int, input_lanes: int, output_lanes: int,
    rows: int, cols: int, token_tile_size: int, tokens: int,
    source: str | None = None,
) -> tuple[list[int], dict[str, int]]:
    """Count Linear's no-stall integer FSM work and ping-pong service interval."""
    if min(input_dim, output_dim, input_lanes, output_lanes, rows, cols, token_tile_size, tokens) <= 0:
        raise ValueError("integer Linear cycle dimensions must be positive")
    if input_dim % cols or output_dim % rows or input_dim % input_lanes or output_dim % output_lanes:
        raise ValueError("integer Linear cycle dimensions must tile the materialized array and stream widths")
    if cols & (cols - 1):
        raise ValueError("integer Linear reduction columns must be a power of two")

    mac_terms = input_dim // cols
    output_tiles = output_dim // rows
    input_beats = input_dim // input_lanes
    output_beats = output_dim // output_lanes
    output_pipe_indices = re.findall(r"writePipeValid(\d+)", source or "")
    output_requant_pipeline_tail_cycles = (
        max(map(int, output_pipe_indices)) + 1
        if output_pipe_indices and "outputWritePendingForDrain" in str(source)
        else 0
    )
    # Cache-word reads are synchronous. Each accepted MAC then traverses the
    # registered multiplier, log2(cols) registered reduction levels, and the
    # registered partial-sum accumulator.
    pipeline_tail_cycles = 1 + 1 + int(math.log2(cols)) + 1
    profiles: list[int] = []
    max_internal_chunk_cycles = 0
    max_chunk_compute_ii = 0
    for chunk_start in range(0, tokens, token_tile_size):
        chunk_tokens = min(token_tile_size, tokens - chunk_start)
        # sIdle selects the full input bank. Every output tile then executes
        # sInit, streamed MAC issue and pipeline drain, sCapture, and sWrite
        # once per token while the internal output ping-pong bank fills.
        chunk_components = {
            "sInit": 1,
            "mac_issue": chunk_tokens * mac_terms,
            "mac_pipeline_drain": pipeline_tail_cycles,
            "sCapture": 1,
            "sWrite": chunk_tokens,
        }
        chunk_compute_cycles = 1 + output_tiles * sum(chunk_components.values())
        chunk_compute_ii = math.ceil(chunk_compute_cycles / chunk_tokens)
        # Linear's two input/output banks overlap collection, compute, and
        # output drain. The slowest of those services bounds token admission;
        # output drain is counted separately from the internal sWrite cycles.
        service_ii = max(
            input_beats,
            output_beats + output_requant_pipeline_tail_cycles,
            chunk_compute_ii,
        )
        profiles.extend([service_ii] * chunk_tokens)
        max_internal_chunk_cycles = max(max_internal_chunk_cycles, chunk_compute_cycles)
        max_chunk_compute_ii = max(max_chunk_compute_ii, chunk_compute_ii)

    components = {
        "mac_terms_per_output_tile": mac_terms,
        "output_tiles": output_tiles,
        "input_beats_per_token": input_beats,
        "output_beats_per_token": output_beats,
        "synchronous_cache_read_cycles_per_mac": 1,
        "integer_multiplier_cycles": 1,
        "reduction_register_levels": int(math.log2(cols)),
        "accumulator_register_cycles": 1,
        "pipeline_tail_cycles_per_output_tile": pipeline_tail_cycles,
        "output_requant_pipeline_tail_cycles": output_requant_pipeline_tail_cycles,
        "maximum_internal_chunk_compute_cycles": max_internal_chunk_cycles,
        "maximum_chunk_compute_ii_cycles_per_token": max_chunk_compute_ii,
        "maximum_chunk_fsm_cycles": {
            "sIdle": 1,
            "sInit_per_output_tile": 1,
            "mac_issue_per_output_tile": max(
                min(token_tile_size, tokens - start) * mac_terms
                for start in range(0, tokens, token_tile_size)
            ),
            "mac_pipeline_drain_per_output_tile": pipeline_tail_cycles,
            "sCapture_per_output_tile": 1,
            "sWrite_per_output_tile": max(
                min(token_tile_size, tokens - start)
                for start in range(0, tokens, token_tile_size)
            ),
        },
        "attention_projection_completion_after_final_input_cycles": (
            max_internal_chunk_cycles + output_requant_pipeline_tail_cycles + output_beats + 1
        ),
    }
    return profiles, components


def _integer_attention_row_services(
    sequence: int,
    heads: int,
    *,
    output_projection_cycles: int = 0,
    softmax_cycles_per_head: int = 1,
) -> list[int]:
    """Count shared-template causal-row states and the serialized output projection."""
    return [
        1 + heads * (6 * (row + 1) + softmax_cycles_per_head + 4) + output_projection_cycles
        for row in range(sequence)
    ]


def _integer_attention_softmax_cycles(source: str | None = None) -> tuple[int, dict[str, int]]:
    """Count the current integer Attention Softmax control states from source."""
    if source is None:
        source = (Path(__file__).parent / "templates/operator_chisel/Attention.scala").read_text(encoding="utf-8")
    if all(state in source for state in ("sSoftmaxMax", "sSoftmaxExp", "sSoftmaxDivide", "sSoftmaxProb")):
        match = re.search(
            r"when\(state === sSoftmaxDivide\)\s*\{.*?divIterationReg === (\d+)\.U",
            source,
            re.S,
        )
        if not match:
            raise ValueError("iterative integer Attention Softmax has no statically bounded divider counter")
        iterations = int(match.group(1)) + 1
        components = {
            "maximum_state": 1,
            "exponential_sum_state": 1,
            "restoring_divider_iterations": iterations,
            "probability_state": 1,
        }
        return sum(components.values()), components
    if re.search(r"state === sSoftmax\b", source):
        return 1, {"combinational_softmax_state": 1}
    raise ValueError("integer Attention source has no recognized finite Softmax schedule")


def _pipeline_cycles(stage_profiles: list[tuple[str, list[int], bool]], tokens: int) -> int:
    """Schedule nominal token services, optionally waiting for a whole-sequence barrier."""
    finishes = [0] * tokens
    for _, profile, waits_for_all_inputs in stage_profiles:
        stage_finishes = [0] * tokens
        previous_output = 0
        barrier_cycle = max(finishes, default=0) if waits_for_all_inputs else 0
        for token in range(tokens):
            service = profile[token % len(profile)]
            previous_output = max(finishes[token], previous_output, barrier_cycle) + service
            stage_finishes[token] = previous_output
        finishes = stage_finishes
    return finishes[-1] if finishes else 0


def _attention_projection_chunk_deadlock(
    *, integer_mac: bool, token_tile_size: int, sequence: int, matrix_roles: set[str],
    attention_source: str | None = None, linear_source: str | None = None,
) -> dict[str, Any] | None:
    """Recognize the template's row-to-chunk cyclic wait from both source sides."""
    has_attention_output = any(
        ("attn" in role.lower() or "attention" in role.lower())
        and ("out" in role.lower() or "proj" in role.lower())
        for role in matrix_roles
    )
    if not integer_mac or not has_attention_output or sequence <= 1 or token_tile_size <= 1:
        return None
    root = Path(__file__).parent / "templates/operator_chisel"
    try:
        attention = attention_source or (root / "Attention.scala").read_text(encoding="utf-8")
        linear = linear_source or (root / "Linear.scala").read_text(encoding="utf-8")
    except OSError:
        return None
    attention_waits_for_projection = (
        "private val outputProjection = Module(new Linear(p.outLinear))" in attention
        and "state === sProjectDrain" in attention
        and "when(io.out.fire && io.out.bits.last" in attention
    )
    linear_waits_for_chunk = (
        "when(loadToken === loadChunkTokens - 1.U)" in linear
        and "inputFull(loadBank) := true.B" in linear
        and "state === sIdle && inputFull(computeBank)" in linear
    )
    if not (attention_waits_for_projection and linear_waits_for_chunk):
        return None
    return {
        "kind": "cyclic_stream_wait",
        "reason": (
            "IntegerAttention waits for its output-projection result before advancing to the next row, "
            "while the output Linear starts only after collecting token_tile_size input tokens; "
            f"the selected chunk is {token_tile_size} tokens."
        ),
        "token_tile_size": token_tile_size,
        "sequence_length": sequence,
        "attention_source": "templates/operator_chisel/Attention.scala",
        "linear_source": "templates/operator_chisel/Linear.scala",
    }


def effective_linear_token_tile_size(parameters: dict[str, Any], tokens: int, sequence: int) -> int:
    """Return the exact bounded input chunk used by the materialized Linear."""
    if parameters.get("cross_token_reuse_tokens") is None:
        raise ValueError("estimator requires materialized cross_token_reuse_tokens")
    tile_size = int(parameters["cross_token_reuse_tokens"])
    batch_context = int(parameters.get("linear_batch_size", tokens) or tokens)
    max_seq_len = int(parameters.get("max_seq_len", sequence) or sequence)
    tile_size = max(1, min(batch_context, sequence, tile_size))
    if max_seq_len > 1:
        tile_size = min(tile_size, max(1, max_seq_len // 2))
    return tile_size


def effective_attention_output_token_tile_size(
    parameters: dict[str, Any], tokens: int, sequence: int,
) -> int:
    """Return the separately bound token chunk used by Attention's output Linear."""
    output_tokens = parameters.get("attention_output_cross_token_reuse_tokens", 1)
    return effective_linear_token_tile_size(
        {**parameters, "cross_token_reuse_tokens": output_tokens}, tokens, sequence,
    )


def source_schedule_blockers(
    parameters: dict[str, Any],
    workload: dict[str, Any],
    terms: list[dict[str, Any]],
    *,
    linear_source: str | None = None,
    attention_source: str | None = None,
) -> list[dict[str, Any]]:
    """Check source-level stream liveness independently of QoR estimation."""
    if str(parameters.get("compute_backend") or "vivado_fp_ip") != "integer_dsp":
        return []
    sequence = int(workload.get("sequence_length", 0) or 0)
    tokens = int(workload.get("processed_tokens", 0) or 0)
    if sequence <= 0 or tokens <= 0 or parameters.get("cross_token_reuse_tokens") is None:
        return []
    matrix_roles = {
        str(term.get("physical_role") or "")
        for term in terms
        if isinstance(term.get("factors"), list)
        and len(term["factors"]) >= 2
        and not str(term.get("physical_role") or "").endswith("_bias")
    }
    blocker = _attention_projection_chunk_deadlock(
        integer_mac=True,
        token_tile_size=effective_attention_output_token_tile_size(parameters, tokens, sequence),
        sequence=sequence,
        matrix_roles=matrix_roles,
        attention_source=attention_source,
        linear_source=linear_source,
    )
    return [blocker] if blocker else []


def integer_operator_source_identity(source_overrides: dict[str, str] | None = None) -> dict[str, str]:
    """Fingerprint integer operator implementations for calibration isolation."""
    root = Path(__file__).parent / "templates/operator_chisel"
    result: dict[str, str] = {}
    source_overrides = source_overrides or {}
    for name in ("Common.scala", "PhysicalResources.scala", "Linear.scala", "WeightTileCache.scala", "QKVProjection.scala", "DecoderBlock.scala", "Norm.scala", "Softmax.scala", "Attention.scala", "Activation.scala", "RoPE.scala", "Residual.scala", "Elementwise.scala", "FFN.scala", "KVCache.scala"):
        if name in source_overrides:
            result[name] = hashlib.sha256(source_overrides[name].encode("utf-8")).hexdigest()
            continue
        path = root / name
        if not path.is_file():
            raise ValueError(f"integer DSE source identity is missing {path}")
        result[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    # Integer calibration is specific to the actual deployed image format and
    # exact-board service generator as well as the operator hierarchy. Do not
    # reuse FP or older integer samples after either boundary changes.
    framework_root = Path(__file__).parent
    repository_root = framework_root.parent.parent
    external_sources = {
        "board_weight_image.py": framework_root / "board_weight_image.py",
        "weight_layout.py": framework_root / "weight_layout.py",
        "fpga_ip_contract.py": framework_root / "fpga_ip_contract.py",
        "fpga_ip_runtime.py": framework_root / "fpga_ip_runtime.py",
        "fpga_ip_vcs_plan.py": framework_root / "fpga_ip_vcs_plan.py",
        "board_memory_runtime.py": framework_root / "board_memory_runtime.py",
        "numeric_policy.py": framework_root / "numeric_policy.py",
        "stage_input.py": framework_root / "stage_input.py",
        "stage_templates.py": framework_root / "stage_templates.py",
        "stage_pipeline.py": framework_root / "stage_pipeline.py",
        "stage_params.py": framework_root / "stage_params.py",
        "stage_artifacts.py": framework_root / "stage_artifacts.py",
        "fixture_generator.scala": repository_root / "tests/fixtures/linear_pipeline/src/main/scala/GenerateLinearPipeline.scala",
        "fixture_prepare.py": repository_root / "tests/fixtures/linear_pipeline/prepare.py",
        "fixture_run_vcs.sh": repository_root / "tests/fixtures/linear_pipeline/run_vcs.sh",
        "compute_slot_adapter_generator.py": repository_root / "scripts/synthesis/compute_slot_adapter_generator.py",
        "board_shell_wrapper_generator.py": repository_root / "scripts/synthesis/board_shell_wrapper_generator.py",
        "ddr_tile_service_contract.json": framework_root.parent / "diagnostics/ddr_alignment_20261017/ddr_tile_service_contract.json",
        # Estimator and exact-board image/service-generator changes alter the
        # source-bound latency, refill, and physical-resource regime. They must
        # not inherit calibration samples collected under an older ABI.
        "dse_estimator.py": framework_root / "dse_estimator.py",
    }
    for name, path in external_sources.items():
        if not path.is_file():
            raise ValueError(f"integer DSE source identity is missing {path}")
        result[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def cost_features(parameters: dict, workload: dict, terms: list[dict], family: str, part: str, *, linear_source: str | None = None, attention_source: str | None = None, norm_source: str | None = None, allow_cycle_break_fallback: bool = False) -> dict:
    if not family or not part:
        raise ValueError("estimator requires a model family and target part")
    lanes = int(parameters["lanes"])
    rows = int(parameters["compute_array_rows"])
    cols = int(parameters["compute_array_cols"])
    hidden = int(workload["hidden_size"])
    tokens = int(workload["processed_tokens"])
    layers = int(workload["model_layers"])
    sequence = int(workload["sequence_length"])
    if min(lanes, rows, cols, hidden, tokens, layers, sequence) <= 0:
        raise ValueError("estimator dimensions must be positive")
    matrices: dict[str, int] = defaultdict(int)
    input_dimensions: dict[str, int] = {}
    matrix_instances: dict[str, set[str]] = defaultdict(set)
    memory_blocks = 0
    linear_activation_bits = 0
    role_elements: dict[str, int] = defaultdict(int)
    role_bits: dict[str, int] = {}
    for term in terms:
        role = str(term["physical_role"])
        elements = int(term["elements"])
        role_elements[role] += elements
        role_bits[role] = int(term["element_bits"])
        # Head count and head dimension can factor a rank-one bias. They
        # do not create another Linear instance or a matrix-width XPM word.
        if len(term.get("factors", [])) >= 2 and not role.endswith("_bias"):
            matrices[role] += elements
            input_dimensions[role] = int(workload.get(str(term["factors"][0]), hidden))
            matrix_instances[role].add(str(term.get("stage") or role))
    if not matrices:
        raise ValueError("estimator requires model-semantic matrix storage terms")
    role_banks = parameters.get("weight_banks_by_role", {})
    cache_tile_words = int(parameters.get("cache_tile_words", 256))
    cache_tile_count = int(parameters.get("cache_tile_count", 2))
    if cache_tile_words <= 0 or cache_tile_count <= 0:
        raise ValueError("bounded weight-cache dimensions must be positive")
    matrix_cache_bits = 0
    matrix_cache_entries = 0
    matrix_cache_primitive_blocks = 0
    raw_refill_width = parameters.get("cache_refill_data_width_bits")
    if raw_refill_width is None:
        raise ValueError("estimator requires a materialized discovered-board refill payload width")
    cache_refill_data_width_bits = int(raw_refill_width)
    if (
        cache_refill_data_width_bits < 64
        or cache_refill_data_width_bits % 32
        or (cache_refill_data_width_bits & (cache_refill_data_width_bits - 1)) != 0
    ):
        raise ValueError("materialized cache refill width must be a supported full-beat payload")
    board_axi_bits = int(workload.get("axi_data_width_bits", 0) or 0)
    if board_axi_bits <= 0 or board_axi_bits % 8:
        raise ValueError("estimator requires a declared byte-aligned board AXI data width")
    if cache_refill_data_width_bits != board_axi_bits:
        raise ValueError(
            "materialized cache refill width must equal the discovered board AXI payload: "
            f"selected={cache_refill_data_width_bits} board={board_axi_bits}"
        )
    for role, instances in matrix_instances.items():
        banks = int(role_banks.get(role, parameters.get("weight_banks", 1)))
        if banks <= 0:
            raise ValueError("weight banks must be positive")
        # Match WeightTileCache exactly. A response beat needs one physical
        # write lane per cache word it can touch, not one lane per 32-bit image
        # word. Each lane is then banked by the declared XPM role bank count.
        width_elements = rows * cols if cols > lanes else lanes * lanes
        cache_word_bits = width_elements * role_bits[role]
        image_words_per_cache_word = max(1, cache_word_bits // 32)
        image_words_per_response = cache_refill_data_width_bits // 32
        phase_period = image_words_per_cache_word // math.gcd(image_words_per_cache_word, image_words_per_response)
        response_write_lanes = max(
            1,
            max(
                (
                    ((beat * image_words_per_response) % image_words_per_cache_word)
                    + image_words_per_response
                    + image_words_per_cache_word
                    - 1
                ) // image_words_per_cache_word
                for beat in range(phase_period)
            ),
        )
        cache_lane_depth = math.ceil((cache_tile_words * cache_tile_count) / response_write_lanes)
        # WeightTileCache packs the logical active and shadow banks into two
        # address regions of each lane's one SDPRAM XPM. Physical bank
        # interleaving and minimum-depth behavior then match
        # PhysicalSimpleDualPortMemory over the combined depth.
        physical_bank_depth = max(2, math.ceil((2 * cache_lane_depth) / banks))
        physical_entries = response_write_lanes * banks * physical_bank_depth
        matrix_cache_entries += len(instances) * physical_entries
        matrix_cache_bits += len(instances) * physical_entries * cache_word_bits
        # Each write lane and role bank instantiates the actual cache-word
        # width rounded to 72-bit URAM columns and the combined bank-region
        # depth rounded to full 4096-word URAM columns.
        matrix_cache_primitive_blocks += (
            len(instances)
            * response_write_lanes
            * banks
            * math.ceil(cache_word_bits / 72)
            * math.ceil(physical_bank_depth / 4096)
        )
    memory_blocks += matrix_cache_primitive_blocks
    for role, elements in role_elements.items():
        if role in matrices:
            continue
        banks = int(role_banks.get(role, parameters.get("weight_banks", 1)))
        if banks <= 0:
            raise ValueError("weight banks must be positive")
        depth = math.ceil(elements / lanes / banks)
        memory_blocks += banks * math.ceil(lanes * role_bits[role] / 72) * math.ceil(depth / 4096)
    linear_schedule = linear_schedule_id(linear_source)
    compute_backend = str(parameters.get("compute_backend") or "vivado_fp_ip")
    integer_mac = compute_backend == "integer_dsp"
    matrix_weight_bits = max((role_bits[role] for role in matrices), default=int(parameters.get("weight_bits", 0) or 0))
    activation_bits = int(parameters.get("activation_bits", parameters.get("elem_bits", 16)))
    accumulator_bits = int(parameters.get("acc_bits", 32))
    scale_bits = int(parameters.get("scale_bits", 32))
    scale_shift = int(parameters.get("scale_shift", 31))
    rounding = str(parameters.get("rounding") or "")
    saturation = parameters.get("saturation") is True
    if integer_mac and (matrix_weight_bits, activation_bits, accumulator_bits) != (4, 8, 32):
        raise ValueError(
            "integer_dsp cost features require signed INT4 matrix weights, INT8 activations, and INT32 accumulators"
        )
    if integer_mac and (scale_bits, scale_shift, rounding, saturation) != (32, 31, "nearest_even", True):
        raise ValueError("integer_dsp cost features require the explicit INT32 Q31 nearest-even saturating scale contract")
    services: list[tuple[str, int]] = []
    # The materialized Linear schedule uses cross_token_reuse_tokens as its
    # bounded activation/cache context. Keep the legacy token_tile_size key as
    # a compatibility fallback, but never let the estimator silently revert to
    # the old fixed 16-token traversal.
    token_tile_size = effective_linear_token_tile_size(parameters, tokens, sequence)
    attention_output_token_tile_size = effective_attention_output_token_tile_size(
        parameters, tokens, sequence,
    )
    architecture_regime = {
        "refill_data_width_bits": cache_refill_data_width_bits,
        "refill_payload_units": "full_board_axi_payload_bits",
        "cross_token_reuse_tokens": token_tile_size,
        "attention_output_cross_token_reuse_tokens": attention_output_token_tile_size,
        "cache_tile_words": cache_tile_words,
        "cache_tile_count": cache_tile_count,
        "linear_schedule": linear_schedule,
        "compute_backend": compute_backend,
        "activation_bits": activation_bits,
        "weight_bits": matrix_weight_bits,
        "accumulator_bits": accumulator_bits,
        "scale_bits": scale_bits,
        "scale_fractional_bits": scale_shift,
        "scale_exponent_contract": (
            "signed_per_channel_binary_exponent_consumed_after_unsigned_q31_multiply"
            if integer_mac else "not_applicable_fp_policy"
        ),
        "rounding": rounding,
        "saturation": saturation,
        "integer_operator_latency_contract": (
            {
                "contract_id": "w4a8_bounded_integer_operator_schedule_v2",
                "source_sha256": integer_operator_source_identity({
                    **({"Linear.scala": linear_source} if linear_source is not None else {}),
                    **({"Attention.scala": attention_source} if attention_source is not None else {}),
                    **({"Norm.scala": norm_source} if norm_source is not None else {}),
                }),
                "normalization": "streamed input/statistics/output passes, source-counted finalize and reciprocal FSM states, and a 32-cycle iterative 64-bit square root",
                "attention": "causal and explicitly masked QK/PV rows dispatched on tokenReady, signed A8xA8 products, source-counted Softmax/divider states, and serialized output projection",
                "linear": "synchronous cache read, registered INT4xINT8 multiplier, registered reduction tree and accumulator, sInit/sCapture/sWrite control, output requant pipeline, and two-bank drain",
                "rope": "fixed-point rotate-half with runtime Q15 tables",
                "requantization": "signed accumulator times unsigned Q31 multiplier, composed channel/activation/output exponents up to 10 signed bits, nearest-even rounding and signed saturation in the output stage",
                "activation_residual": "one elastic integer stage per accepted beat",
            }
            if integer_mac else "not_applicable_fp_policy"
        ),
    }
    # Match LinearParams exactly: the bounded context is limited by both the
    # generated batch context and maxSeqLen/2, so reuse candidates alter real
    # chunking, refill traversals, and activation storage rather than merely
    # changing metadata.
    # LinearParams.batchSize is a token capacity, not the model's batch count.
    # A batch of one with a 32-token sequence still needs a 32-token context.
    # Record the effective bounded context after the same legality clamp used
    # by LinearParams. The estimator must not describe one reuse value while
    # charging traffic and cycles for a different materialized schedule.
    architecture_regime["cross_token_reuse_tokens"] = token_tile_size
    attention_output_roles = [
        role for role in matrices
        if ("attn" in role.lower() or "attention" in role.lower())
        and ("out" in role.lower() or "proj" in role.lower())
    ]
    q_heads = int(workload.get("num_q_heads", 0) or 0)
    head_dim = int(workload.get("head_dim", 0) or 0)
    if q_heads > 0 and head_dim > 0:
        # Attention emits the concatenated query-head vector, which need not
        # equal hidden_size (for example, Gemma 3 1B uses 4 x 256 -> 1152).
        for role in attention_output_roles:
            input_dimensions[role] = q_heads * head_dim
    source_blockers = source_schedule_blockers(
        parameters,
        workload,
        terms,
        attention_source=attention_source,
        linear_source=linear_source,
    )
    cycle_blockers = source_blockers[0] if source_blockers else None
    fallback_roles = (
        set(attention_output_roles)
        if cycle_blockers and allow_cycle_break_fallback else set()
    )
    role_reuse_tokens = {
        role: (
            1 if role in fallback_roles
            else attention_output_token_tile_size if role in attention_output_roles
            else token_tile_size
        )
        for role in matrices
    }
    role_token_chunks = {
        role: math.ceil(tokens / reuse_tokens)
        for role, reuse_tokens in role_reuse_tokens.items()
    }
    architecture_regime["effective_cross_token_reuse_tokens_by_role"] = role_reuse_tokens
    # This is the materialized Linear schedule context, not a legacy fixed
    # token tile. All traffic and cycle estimates below must follow the selected
    # cross-token reuse candidate.
    linear_services: dict[str, int] = {}
    linear_service_profiles: dict[str, list[int]] = {}
    linear_cycle_components: dict[str, dict[str, int]] = {}
    for role, elements in matrices.items():
        input_dim = input_dimensions[role]
        role_token_tile_size = role_reuse_tokens[role]
        if linear_schedule in {"token_interleaved_fp_pipeline_v2", "token_interleaved_policy_mac_v3"}:
            if role in attention_output_roles and elements % input_dim:
                raise ValueError(
                    f"attention output projection has {elements} weight elements, "
                    f"not divisible by its {input_dim}-wide input"
                )
            output_dim = math.ceil(elements / input_dim)
            is_attention_output = role in attention_output_roles
            input_lanes = head_dim if integer_mac and is_attention_output and head_dim > 0 else lanes
            if integer_mac:
                profile, components = _integer_linear_service_profile(
                    input_dim=input_dim,
                    output_dim=output_dim,
                    input_lanes=input_lanes,
                    output_lanes=lanes,
                    rows=rows,
                    cols=cols,
                    token_tile_size=role_token_tile_size,
                    tokens=tokens,
                    source=linear_source,
                )
                service = max(profile)
                linear_cycle_components[role] = components
            else:
                mac_terms = math.ceil(input_dim / cols)
                output_tiles = math.ceil(output_dim / rows)
                pipe_fill = 9 + 12 * int(math.log2(cols)) + 12
                role_chunks = role_token_chunks[role]
                compute = output_tiles * (mac_terms + pipe_fill * role_chunks / tokens)
                service = max(
                    math.ceil(input_dim / input_lanes),
                    math.ceil(compute) + math.ceil(output_dim / lanes),
                )
                profile = [service] * tokens
            linear_service_profiles[role] = profile
            linear_services[role] = service
            if not integer_mac:
                services.append((f"linear:{role}", service))
            linear_activation_bits += 2 * role_token_tile_size * (input_dim + output_dim) * int(parameters.get("elem_bits", 16))
        else:
            mac_service = 2 + 9 + 12 + 12 * math.log2(cols)
            service = math.ceil(input_dim / lanes + elements * mac_service / (rows * cols))
            services.append((f"linear:{role}", service))
    attention_softmax_cycles, attention_softmax_components = (
        _integer_attention_softmax_cycles(attention_source) if integer_mac else (0, {})
    )
    cycle_model_fallback = None
    if integer_mac:
        intermediate = int(workload.get("intermediate_size", hidden) or hidden)
        vector_beats = math.ceil(hidden / lanes)
        intermediate_beats = math.ceil(intermediate / lanes)
        norm_service, norm_components = _integer_norm_service(hidden, lanes, norm_source)
        qkv_roles = [role for role in linear_services if "qkv" in role.lower()]
        gate_roles = [role for role in linear_services if "gate" in role.lower()]
        up_roles = [role for role in linear_services if "up" in role.lower()]
        down_roles = [role for role in linear_services if "down" in role.lower()]
        classified_roles = set(qkv_roles + attention_output_roles + gate_roles + up_roles + down_roles)
        unknown_roles = [role for role in linear_services if role not in classified_roles]
        attention_projection_cycles = max(
            (
                linear_cycle_components[role]["attention_projection_completion_after_final_input_cycles"]
                for role in attention_output_roles
            ),
            default=0,
        )
        if cycle_blockers and attention_output_roles and allow_cycle_break_fallback:
            # This explicit scenario changes the projection role's token
            # context. Its Linear schedule, activation storage, and repeated
            # DDR tile traversal are all recomputed with that same context.
            # It does not describe the currently bound RTL.
            cycle_model_fallback = {
                "kind": "counterfactual_single_token_projection_delivery",
                "reason": "break the detected Attention/Linear chunk wait at the producer-consumer boundary",
                "original_token_tile_size": token_tile_size,
                "fallback_projection_token_tile_size": 1,
                "bound_attention_output_token_tile_size": attention_output_token_tile_size,
                "projection_completion_cycles": attention_projection_cycles,
                "affected_roles": sorted(fallback_roles),
                "effective_cross_token_reuse_tokens_by_role": role_reuse_tokens,
                "token_chunks_by_role": role_token_chunks,
                "selected_array_dimensions_unchanged": True,
                "ddr_traffic_recomputed_for_role_reuse": True,
            }

        # These stage profiles follow the bound integer template FSMs. The
        # attention FSM starts row r when tokenReady(r) is set; causal row
        # dependencies do not impose a whole-sequence input barrier. Linear
        # chunking is represented by its configured token context and checked
        # for cyclic producer/consumer waits above.
        stage_profiles: list[tuple[str, list[int], bool]] = [
            ("norm1", [norm_service] * sequence, False),
        ]
        consumed_roles: set[str] = set()
        for role in qkv_roles:
            stage_profiles.append((f"linear:{role}", linear_service_profiles[role], False))
            consumed_roles.add(role)
        for role in unknown_roles:
            stage_profiles.append((f"linear:{role}", linear_service_profiles[role], False))
            consumed_roles.add(role)

        has_rope = any(term.get("stage") and "rope" in str(term["stage"]).lower() for term in terms)
        if has_rope:
            rope_service = q_heads * math.ceil(max(1, head_dim) / lanes)
            stage_profiles.append(("rope", [rope_service] * sequence, False))
        elif any(name in family.lower() for name in ("llama", "qwen", "mistral")):
            rope_service = q_heads * math.ceil(max(1, head_dim) / lanes)
            stage_profiles.append(("rope", [rope_service] * sequence, False))

        attention_profile = _integer_attention_row_services(
            sequence,
            q_heads,
            output_projection_cycles=attention_projection_cycles,
            softmax_cycles_per_head=attention_softmax_cycles,
        )
        stage_profiles.append(("attention", attention_profile, False))
        consumed_roles.update(attention_output_roles)
        stage_profiles.extend([
            ("residual1", [vector_beats] * sequence, False),
            ("norm2", [norm_service] * sequence, False),
        ])

        expand_roles = gate_roles + up_roles
        if expand_roles:
            stage_profiles.append((
                "mlp_expand",
                [
                    max(linear_service_profiles[role][token] for role in expand_roles)
                    for token in range(tokens)
                ],
                False,
            ))
            consumed_roles.update(expand_roles)
        ffn_pointwise_service = intermediate_beats * (2 if gate_roles else 1)
        stage_profiles.append(("ffn_pointwise", [ffn_pointwise_service] * sequence, False))
        for role in down_roles:
            stage_profiles.append((f"linear:{role}", linear_service_profiles[role], False))
            consumed_roles.add(role)
        stage_profiles.append(("residual2", [vector_beats] * sequence, False))
        for role in linear_services:
            if role not in consumed_roles:
                stage_profiles.append((f"linear:{role}", linear_service_profiles[role], False))

        services = [(name, max(profile)) for name, profile, _ in stage_profiles]
        stage_profiles_by_name = {name: profile for name, profile, _ in stage_profiles}
    else:
        services.extend([("norm", hidden * 24), ("attention", sequence * hidden * 24)])
        stage_profiles = [(name, [cycles] * tokens, False) for name, cycles in services]
        stage_profiles_by_name = {name: profile for name, profile, _ in stage_profiles}
        cycle_blockers = None
    stage_services = {name: max(profile) for name, profile in stage_profiles_by_name.items()}
    bottleneck_cycles_per_token = max(stage_services.values())
    nominal_compute_cycles = _pipeline_cycles(stage_profiles, tokens)
    compute_cycles_per_layer = None if (cycle_blockers and cycle_model_fallback is None) else nominal_compute_cycles
    axi_bits = int(workload.get("axi_data_width_bits", 0) or 0)
    if axi_bits <= 0 or axi_bits % 8:
        raise ValueError("estimator requires a declared byte-aligned board AXI data width")
    weight_image_bytes_per_layer = sum(
        (int(term["elements"]) * int(term["element_bits"]) + 7) // 8
        for term in terms
    )

    # Model the actual bounded-cache traversal, including repeated DDR tile
    # refills for matrices larger than the cache. A matrix that fits in the
    # cache is loaded once for the layer; otherwise each token chunk revisits
    # the tile sequence and therefore re-reads it from external DDR. Bias and
    # vector terms remain part of the complete model-semantic image.
    refill_words_per_layer = 0
    cache_tile_entry_bits = 0
    refill_traversals_by_role: dict[str, int] = {}
    for role, elements in role_elements.items():
        bits = role_bits[role]
        if role in matrices:
            width_elements = rows * cols if cols > lanes else lanes * lanes
            matrix_entries = math.ceil((elements * bits) / max(1, width_elements * bits))
            tile_count = math.ceil(matrix_entries / cache_tile_words)
            traversals = 1 if tile_count <= cache_tile_count else role_token_chunks[role]
            refill_traversals_by_role[role] = traversals
            # Only the logical entries in the final tile transfer from DDR;
            # XPM slot padding is storage overhead, not image traffic.
            refill_words_per_layer += (
                matrix_entries * width_elements * bits // 32
            ) * traversals
            cache_tile_entry_bits = max(cache_tile_entry_bits, width_elements * bits)
        else:
            refill_words_per_layer += math.ceil(elements * bits / 32)
    refill_bytes_per_layer = max(
        weight_image_bytes_per_layer,
        refill_words_per_layer * 4.0,
    )
    semantic_image_beats_per_layer = math.ceil(weight_image_bytes_per_layer / (axi_bits // 8))
    # The cache response contract consumes a selected wide payload containing
    # complete 32-bit image words. Credit the selected physical payload rate;
    # AXI transfer cycles remain separate from cache-service cycles so board
    # arbitration and payload packing are not conflated.
    raw_refill_width = parameters.get("cache_refill_data_width_bits")
    if raw_refill_width is None:
        raise ValueError("production estimator features require the materialized discovered-board refill payload width")
    cache_refill_data_width_bits = int(raw_refill_width)
    if (
        cache_refill_data_width_bits < 64
        or cache_refill_data_width_bits % 32
        or cache_refill_data_width_bits != axi_bits
    ):
        raise ValueError(
            "production materialized cache refill width must equal the discovered full board AXI payload"
        )
    response_words_per_cycle = cache_refill_data_width_bits // 32
    axi_words_per_beat = axi_bits // 32
    refill_response_cycles = math.ceil(refill_words_per_layer / response_words_per_cycle)
    axi_transfer_cycles = math.ceil(refill_words_per_layer / axi_words_per_beat)
    # Include request/last-beat handling per bounded tile and both the AXI
    # transfer and cache-service paths. These are structural estimates, not
    # measured bandwidth or a claim that arbitration never stalls.
    tile_requests_per_layer = 0
    tile_axi_bursts_per_layer = 0
    tile_requests_by_role: dict[str, int] = {}
    tile_axi_bursts_by_role: dict[str, int] = {}
    axi_words_per_burst = max(1, min(256, 4096 // (axi_bits // 8))) * axi_words_per_beat
    for role, elements in matrices.items():
        input_dim = input_dimensions[role]
        output_dim = math.ceil(elements / input_dim)
        width_elements = rows * cols if cols > lanes else lanes * lanes
        entries = math.ceil(output_dim * input_dim / width_elements)
        tile_count = math.ceil(entries / cache_tile_words)
        traversals = 1 if tile_count <= cache_tile_count else role_token_chunks[role]
        role_tile_requests = tile_count * traversals
        role_axi_bursts = 0
        tile_requests_per_layer += role_tile_requests
        image_words_per_cache_word = width_elements * role_bits[role] // 32
        for tile_index in range(tile_count):
            tile_entries = min(cache_tile_words, entries - tile_index * cache_tile_words)
            tile_words = tile_entries * image_words_per_cache_word
            tile_beats = math.ceil(tile_words / axi_words_per_beat)
            role_axi_bursts += math.ceil(tile_beats / max(1, axi_words_per_burst // axi_words_per_beat)) * traversals
        tile_requests_by_role[role] = role_tile_requests
        tile_axi_bursts_by_role[role] = role_axi_bursts
        tile_axi_bursts_per_layer += role_axi_bursts
    # Account for AXI's maximum 256-beat and 4-KiB burst boundaries as well
    # as per-tile ownership/request setup. Wide AXI beats and wide cache
    # responses share their steady-state beat rate; the service setup costs
    # are additive and do not assume a scalar serializer or unstalled DDR.
    minimum_axi_bursts = math.ceil(axi_transfer_cycles / max(1, axi_words_per_burst // axi_words_per_beat))
    axi_bursts_per_layer = max(tile_axi_bursts_per_layer, minimum_axi_bursts)
    refill_service_cycles_per_layer = (
        max(refill_response_cycles, axi_transfer_cycles)
        + 2 * tile_requests_per_layer
        + 2 * axi_bursts_per_layer
    )
    ddr_refill_beats_per_layer = math.ceil(refill_bytes_per_layer / (axi_bits // 8))
    initial_refill_cycles = refill_service_cycles_per_layer
    if cycle_blockers and cycle_model_fallback is None:
        overlapped_refill_stall_cycles = None
        compute_cycles_all_layers = None
        exposed_refill_stall_cycles = None
        pipeline_cycles = None
    else:
        overlapped_refill_stall_cycles = max(0, refill_service_cycles_per_layer - compute_cycles_per_layer)
        compute_cycles_all_layers = layers * compute_cycles_per_layer
        exposed_refill_stall_cycles = max(0, layers - 1) * overlapped_refill_stall_cycles
        pipeline_cycles = (
            initial_refill_cycles
            + compute_cycles_all_layers
            + exposed_refill_stall_cycles
        )
    input_transfer_bytes = math.ceil(tokens * hidden * int(parameters.get("input_bits", activation_bits)) / 8)
    output_transfer_bytes = math.ceil(tokens * hidden * int(parameters.get("output_bits", activation_bits)) / 8)
    activation_transfer_beats_per_layer = math.ceil(
        (input_transfer_bytes + output_transfer_bytes) / (axi_bits // 8)
    )
    operators = len({str(term.get("stage")) for term in terms})
    processing_elements = len(matrices) * rows * cols
    # The integer attention hierarchy materializes signed A8xA8 QK and PV
    # multipliers in addition to the W4A8 Linear PE array. Include those
    # physical products in the DSP proxy instead of reusing the FP-era PE-only
    # count. All dimensions are supplied by the current generic workload.
    attention_dsp = 0
    if integer_mac:
        q_heads = int(workload.get("num_q_heads", 0) or 0)
        head_dim = int(workload.get("head_dim", 0) or 0)
        if q_heads > 0 and head_dim > 0:
            attention_dsp = 2 * q_heads * head_dim
    integer_operator_dsp = operators * lanes if integer_mac else 0
    dsp_products = processing_elements + attention_dsp + integer_operator_dsp
    logic_units = processing_elements + operators * lanes + len(matrices) * lanes * lanes
    activation_banks = int(parameters.get("activation_banks", 1))
    fifo_depth = int(parameters.get("fifo_depth", 1))
    if min(activation_banks, fifo_depth) <= 0:
        raise ValueError("activation banks and FIFO depth must be positive")
    # Match the integer policy's actual stream width instead of charging
    # every activation/FIFO as a 32-bit FP element. Accumulator/bias memory
    # remains charged separately from semantic weight-storage terms.
    stream_bits = int(parameters.get("output_bits", activation_bits))
    activation_blocks = operators * activation_banks * math.ceil(lanes * activation_bits / 36) * math.ceil(sequence * hidden / lanes / activation_banks / 1024)
    activation_blocks += math.ceil(linear_activation_bits / (36 * 1024))
    fifo_blocks = operators * math.ceil(lanes * stream_bits / 36) * math.ceil(fifo_depth / 1024)
    cache_blocks = math.ceil(sequence * hidden * activation_bits / (4096 * 72))
    weight_uram_blocks = memory_blocks if parameters.get("weight_memory") == "xpm_uram" else 0
    weight_bram_blocks = memory_blocks if parameters.get("weight_memory") == "xpm_bram" else 0
    cache_uram_blocks = cache_blocks if parameters.get("large_cache_memory") == "xpm_uram" else 0
    cache_bram_blocks = cache_blocks if parameters.get("large_cache_memory") == "xpm_bram" else 0
    return {
        "estimator_model": MODEL,
        "family": family, "part": part,
        "linear_schedule": linear_schedule,
        "architecture_regime": architecture_regime,
        "precision_bits": matrix_weight_bits,
        "activation_bits": activation_bits,
        "weight_bits": matrix_weight_bits,
        "accumulator_bits": accumulator_bits,
        "scale_bits": scale_bits,
        "scale_shift": scale_shift,
        "rounding": rounding,
        "saturation": saturation,
        "compute_backend": compute_backend,
        "memory_implementation": [parameters.get(key) for key in ("weight_memory", "activation_memory", "large_cache_memory")],
        "parameters": parameters, "workload": workload,
        # This template family keeps the complete block's weights resident.
        # Banking changes packing, but cannot reduce the stored bit count.
        "resource_lower_bounds": {
            "uram": math.ceil(
                (matrix_cache_bits + sum(
                    role_elements[role] * role_bits[role]
                    for role in role_elements if role not in matrices
                )) / (4096 * 72)
            ) if parameters.get("weight_memory") == "xpm_uram" else 0,
        },
        "proxies": {
            "cycles": int(pipeline_cycles) if pipeline_cycles is not None else None,
            "cycle_model_status": (
                "counterfactual_cycle_break"
                if cycle_model_fallback else ("blocked" if cycle_blockers else "estimated")
            ),
            "cycle_model_blockers": [cycle_blockers] if cycle_blockers else [],
            "cycle_model_fallback": cycle_model_fallback,
            "compute_cycles_per_layer": compute_cycles_per_layer,
            "operator_stage_service_cycles_per_token": stage_services,
            "operator_stage_service_profile_cycles_per_token": stage_profiles_by_name,
            "operator_stage_sequence_barriers": [
                name for name, _, waits_for_all_inputs in stage_profiles if waits_for_all_inputs
            ],
            "integer_norm_service_cycle_components": norm_components if integer_mac else {},
            "integer_attention_softmax_cycles_per_head": attention_softmax_cycles if integer_mac else None,
            "integer_attention_softmax_cycle_components": attention_softmax_components if integer_mac else {},
            "integer_linear_fsm_cycle_components": linear_cycle_components if integer_mac else {},
            "pipeline_steady_state_ii_cycles": bottleneck_cycles_per_token,
            "compute_cycles_all_layers": compute_cycles_all_layers,
            "pipeline_cycle_terms": {
                "initial_weight_refill": initial_refill_cycles,
                "compute_all_layers": compute_cycles_all_layers,
                "exposed_inter_layer_refill_stall": exposed_refill_stall_cycles,
                "total": int(pipeline_cycles) if pipeline_cycles is not None else None,
            },
            "cycle_model_precision": "source_fsm_state_count_with_causal_ready_token_schedule_no_external_stalls",
            "cycle_model_is_rtl_exact": False,
            "cycle_model_unmodeled_effects": [
                "DDR/MIG read and write response latency variation",
                "AXI backpressure, arbitration, and read/write turnaround",
                "top-level input/output transfer overlap with weight refill",
                "finite inter-stage FIFO occupancy and ready/valid backpressure outside the detected chunk barrier",
                "runtime modifications to generated RTL that differ from the shared Chisel templates",
            ],
            "ddr_refill_beats_per_layer": ddr_refill_beats_per_layer,
            "semantic_weight_image_beats_per_layer": semantic_image_beats_per_layer,
            "semantic_weight_image_bytes_per_layer": weight_image_bytes_per_layer,
            "ddr_refill_words_per_layer": refill_words_per_layer,
            "ddr_refill_bytes_per_layer": refill_bytes_per_layer,
            "activation_input_bytes_per_layer": input_transfer_bytes,
            "activation_output_bytes_per_layer": output_transfer_bytes,
            "activation_transfer_beats_per_layer": activation_transfer_beats_per_layer,
            "cache_refill_data_width_bits": cache_refill_data_width_bits,
            "effective_cross_token_reuse_tokens": token_tile_size,
            "effective_cross_token_reuse_tokens_by_role": role_reuse_tokens,
            "ddr_refill_traversals_by_role": refill_traversals_by_role,
            "response_words_per_cycle": response_words_per_cycle,
            "axi_words_per_beat": axi_words_per_beat,
            "tile_requests_per_layer": tile_requests_per_layer,
            "tile_requests_by_role": tile_requests_by_role,
            "axi_bursts_per_layer": axi_bursts_per_layer,
            "tile_axi_bursts_by_role": tile_axi_bursts_by_role,
            "axi_transfer_cycles_per_layer": axi_transfer_cycles,
            "cache_response_cycles_per_layer": refill_response_cycles,
            "materialized_refill_rate_bits_per_cycle": cache_refill_data_width_bits,
            "materialized_refill_rate_source": "exact_board_ddr_tile_service.aggregate_response_data_width_bits",
            "refill_payload_units": "full_board_axi_payload_bits; addresses/counts remain 32-bit image-word units",
            "scalar_refill_fallback_allowed": False,
            "cache_refill_service_cycles_per_layer": refill_service_cycles_per_layer,
            "initial_refill_cycles": initial_refill_cycles,
            "overlapped_refill_stall_cycles_per_layer": overlapped_refill_stall_cycles,
            "weight_cache_bits": matrix_cache_bits,
            "weight_cache_entries": matrix_cache_entries,
            "weight_cache_tile_entry_bits": cache_tile_entry_bits,
            "weight_cache_tile_words": cache_tile_words,
            "weight_cache_tile_count": cache_tile_count,
            "axi_data_width_bits": axi_bits,
            "clock_frequency_mhz": 1.0,
            "lut": max(1, logic_units),
            "ff": max(1, 32 * logic_units + fifo_depth * lanes * operators),
            "dsp": max(1, dsp_products),
            "bram36": max(1, activation_blocks + fifo_blocks + weight_bram_blocks + cache_bram_blocks),
            "bram18": max(1, activation_blocks + fifo_blocks),
            "uram": max(1, weight_uram_blocks + cache_uram_blocks),
        },
    }


def _value(sample: dict, key: str) -> float:
    if key in RESOURCE_KEYS:
        return float(sample["resources"][key])
    if key == "cycles":
        return float(sample["performance_estimation"]["latency_cycles"])
    return float(sample[key])


def _has_measured_cycle_counter(sample: dict) -> bool:
    evidence = sample.get("cycle_evidence")
    performance = sample.get("performance_estimation")
    return (
        isinstance(evidence, dict)
        and evidence.get("kind") == "rtl_counter"
        and evidence.get("status") == "pass"
        and sample.get("performance_model") == "synthesizable_dut_counter"
        and isinstance(performance, dict)
        and performance.get("rtl_cycles_measured") is True
        and performance.get("measurement_complete") is True
        and performance.get("count_is_latency") is True
    )


def estimate(features: dict, samples: list[dict]) -> dict[str, Any]:
    if features.get("proxies", {}).get("cycle_model_status") == "counterfactual_cycle_break":
        proxies = features["proxies"]
        return {
            "status": "counterfactual_schedule",
            "model": MODEL,
            "reason": "cycle count assumes an explicit single-token boundary change that is not present in the bound RTL",
            "latency_cycles": proxies.get("cycles"),
            "performance_tokens_per_second": None,
            "cycle_model_blockers": proxies.get("cycle_model_blockers", []),
            "cycle_model_fallback": proxies.get("cycle_model_fallback"),
        }
    if features.get("proxies", {}).get("cycle_model_status") == "blocked":
        blockers = features["proxies"].get("cycle_model_blockers", [])
        return {
            "status": "blocked_schedule",
            "model": MODEL,
            "reason": blockers[0]["reason"] if blockers else "source schedule has no finite completion",
            "cycle_model_blockers": blockers,
            "latency_cycles": None,
            "performance_tokens_per_second": None,
        }
    compatible = [
        sample for sample in samples
        if isinstance(sample.get("cost_features"), dict)
        and sample["cost_features"].get("estimator_model") == features.get("estimator_model")
        and sample["cost_features"].get("part") == features["part"]
        and sample["cost_features"].get("precision_bits") == features["precision_bits"]
        and sample["cost_features"].get("memory_implementation") == features["memory_implementation"]
        and sample["cost_features"].get("linear_schedule", "legacy_blocking_fp") == features.get("linear_schedule", "legacy_blocking_fp")
        and sample["cost_features"].get("architecture_regime") == features.get("architecture_regime")
    ]
    if not compatible:
        return {"status": "insufficient_evidence", "model": MODEL, "reason": "no compatible source-bound calibration sample"}
    same_family = [sample for sample in compatible if sample["cost_features"].get("family") == features["family"]]
    anchors = compatible
    if len(anchors) < 2:
        return {
            "status": "insufficient_evidence", "model": MODEL,
            "reason": "at least two compatible source-bound synthesis samples are required",
        }
    distances = [
        sum(abs(math.log(features["proxies"][key] / sample["cost_features"]["proxies"][key])) for key in ("cycles", "lut", "ff", "dsp", "uram")) / 5
        for sample in anchors
    ]
    weights = [
        (4.0 if sample["cost_features"].get("family") == features["family"] else 1.0)
        / (0.05 + distance) ** 2
        for sample, distance in zip(anchors, distances)
    ]
    estimates = {}
    spreads = []
    for key in (*RESOURCE_KEYS, "clock_frequency_mhz"):
        proxy = features["proxies"][key]
        corrected = [_value(sample, key) * proxy / sample["cost_features"]["proxies"][key] for sample in anchors]
        estimates[key] = sum(weight * value for weight, value in zip(weights, corrected)) / sum(weights)
        if estimates[key] > 0:
            spreads.append(max(abs(value / estimates[key] - 1) for value in corrected))
    cycle_anchors = [sample for sample in anchors if _has_measured_cycle_counter(sample)]
    if cycle_anchors:
        cycle_weights = [
            weight for sample, weight in zip(anchors, weights)
            if _has_measured_cycle_counter(sample)
        ]
        corrected_cycles = [
            _value(sample, "cycles") * features["proxies"]["cycles"]
            / sample["cost_features"]["proxies"]["cycles"]
            for sample in cycle_anchors
        ]
        estimates["cycles"] = sum(
            weight * value for weight, value in zip(cycle_weights, corrected_cycles)
        ) / sum(cycle_weights)
        if estimates["cycles"] > 0:
            spreads.append(max(abs(value / estimates["cycles"] - 1) for value in corrected_cycles))
        cycle_estimate_source = "source_bound_rtl_counter_calibration"
    else:
        estimates["cycles"] = float(features["proxies"]["cycles"])
        cycle_estimate_source = "uncalibrated_integer_structural_proxy"
    cycles = max(1, round(estimates["cycles"]))
    for key, minimum in features.get("resource_lower_bounds", {}).items():
        estimates[key] = max(estimates[key], minimum)
    clock = estimates["clock_frequency_mhz"]
    tps = features["workload"]["processed_tokens"] * clock * 1_000_000 / cycles
    factor = max(1.25, 1 + min(distances), 1 + max(spreads, default=0))
    if not cycle_anchors:
        factor = max(2.0, factor)
    cross_model = any(sample["cost_features"].get("family") != features["family"] for sample in anchors)
    if cross_model:
        factor = max(2.0, factor)
    return {
        "status": "estimated", "model": MODEL,
        "resources": {key: max(0, round(estimates[key])) for key in RESOURCE_KEYS},
        "clock_frequency_mhz": clock, "latency_cycles": cycles,
        "performance_tokens_per_second": tps,
        "cycle_estimate_source": cycle_estimate_source,
        "cycle_calibration_sample_count": len(cycle_anchors),
        "cycle_calibration_source_fingerprints": [sample["source_fingerprint"] for sample in cycle_anchors],
        "cycle_estimate_is_rtl_exact": False,
        "anchor_source_fingerprints": [sample["source_fingerprint"] for sample in anchors],
        "calibration_sample_count": len(anchors),
        "cross_model_extrapolation": not bool(same_family),
        "cross_model_calibration": cross_model,
        "extrapolation_distance": min(distances),
        "sensitivity_bounds": {
            "performance_tokens_per_second": [tps / factor, tps * factor],
            "resources": {key: [value / factor, value * factor] for key, value in ((key, estimates[key]) for key in RESOURCE_KEYS)},
        },
        "uncertainty": "Sensitivity bounds, not statistical confidence intervals. Cycle predictions without a matching RTL counter anchor are uncalibrated structural estimates.",
        "assumptions": "Only source-bound RTL counter reports calibrate cycle counts. Analytical source-schedule/DSE cycles are not cycle calibration labels. Clock and resources use compatible synthesis anchors; bank counts do not imply compute speedup. Architectural changes require new anchors.",
    }


def validation_report(samples: list[dict]) -> dict:
    errors: dict[str, list[float]] = defaultdict(list)
    zero_errors: dict[str, list[float]] = defaultdict(list)
    count = 0
    cycle_validation_count = 0
    for held_out in samples:
        if not held_out.get("cost_features"):
            continue
        training = [sample for sample in samples if sample["source_fingerprint"] != held_out["source_fingerprint"]]
        prediction = estimate(held_out["cost_features"], training)
        if prediction["status"] != "estimated":
            continue
        count += 1
        validation_keys = (*RESOURCE_KEYS, "clock_frequency_mhz")
        if _has_measured_cycle_counter(held_out):
            validation_keys = (*validation_keys, "cycles", "performance_tokens_per_second")
            cycle_validation_count += 1
        for key in validation_keys:
            actual = _value(held_out, key)
            predicted = (
                prediction["resources"][key] if key in RESOURCE_KEYS
                else prediction["latency_cycles"] if key == "cycles"
                else prediction[key]
            )
            if actual > 0:
                errors[key].append(abs(predicted - actual) / actual)
            else:
                zero_errors[key].append(abs(predicted))
    return {
        "method": "leave_one_source_fingerprint_out",
        "sample_count": len(samples),
        "held_out_prediction_count": count,
        "cycle_validation_sample_count": cycle_validation_count,
        "mean_relative_absolute_error": {key: sum(values) / len(values) for key, values in errors.items()},
        "mean_absolute_error_for_zero_actual": {key: sum(values) / len(values) for key, values in zero_errors.items()},
        "status": "evaluated" if errors else "insufficient_independent_samples",
    }


def rank_candidates(records: list[dict], targets: dict, budget: dict) -> list[str]:
    def score(record: dict) -> tuple:
        prediction = record.get("qor_estimate") or {}
        if prediction.get("status") != "estimated":
            proxy = record.get("structural_cost_proxy") or {}
            cycles = float(proxy.get("cycles") or 0)
            if cycles <= 0:
                return (2, 0, 0, 0, 0, str(record["candidate_id"]))
            usage = [
                float(proxy[key]) / float(budget[key])
                for key in RESOURCE_KEYS
                if budget.get(key) and proxy.get(key) is not None
            ]
            overage = sum(
                max(0.0, ratio / RESOURCE_HEADROOM_FRACTION - 1.0)
                for ratio in usage
            )
            return (1, int(overage > 0), overage, cycles, max(usage, default=0.0), str(record["candidate_id"]))
        resource_miss = sum(
            max(0, value / (budget[key] * RESOURCE_HEADROOM_FRACTION) - 1)
            for key, value in prediction["resources"].items() if budget.get(key)
        )
        throughput = prediction["performance_tokens_per_second"]
        clock = prediction["clock_frequency_mhz"]
        throughput_miss = max(0, targets.get("performance_tokens_per_second", 0) / throughput - 1)
        clock_miss = max(0, targets.get("clock_frequency_mhz", 0) / clock - 1)
        # Resources constrain the search; spare capacity is not the objective.
        # Once targets are met, prefer throughput over calibration proximity.
        return (
            0, int(resource_miss > 0), resource_miss,
            int(throughput_miss > 0 or clock_miss > 0),
            throughput_miss, clock_miss, -throughput,
            prediction["extrapolation_distance"], str(record["candidate_id"]),
        )

    return [str(record["candidate_id"]) for record in sorted(records, key=score) if record.get("feasible") and not record.get("measurement")]
