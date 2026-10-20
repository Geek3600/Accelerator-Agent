"""Calibrated structural cost estimates, never substitutes for tool results."""

from __future__ import annotations

import hashlib
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


MODEL = "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi"
RESOURCE_KEYS = ("lut", "ff", "dsp", "bram36", "bram18", "uram")
# Estimated and structural candidates should retain implementation headroom;
# fitting just below a discovered capacity is not a good final design point.
RESOURCE_HEADROOM_FRACTION = 0.85


def linear_schedule_id(source: str | None = None) -> str:
    if source is None:
        source = (Path(__file__).parent / "templates/operator_chisel/Linear.scala").read_text(encoding="utf-8")
    match = re.search(r'val\s+scheduleId\s*:\s*String\s*=\s*"([^"]+)"', source)
    return match.group(1) if match else "legacy_blocking_fp"


def integer_operator_source_identity() -> dict[str, str]:
    """Fingerprint integer operator implementations for calibration isolation."""
    root = Path(__file__).parent / "templates/operator_chisel"
    result: dict[str, str] = {}
    for name in ("Common.scala", "PhysicalResources.scala", "Linear.scala", "WeightTileCache.scala", "QKVProjection.scala", "DecoderBlock.scala", "Norm.scala", "Softmax.scala", "Attention.scala", "Activation.scala", "RoPE.scala", "Residual.scala", "Elementwise.scala", "FFN.scala", "KVCache.scala"):
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


def cost_features(parameters: dict, workload: dict, terms: list[dict], family: str, part: str, *, linear_source: str | None = None) -> dict:
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
    services = []
    # The materialized Linear schedule uses cross_token_reuse_tokens as its
    # bounded activation/cache context. Keep the legacy token_tile_size key as
    # a compatibility fallback, but never let the estimator silently revert to
    # the old fixed 16-token traversal.
    if parameters.get("cross_token_reuse_tokens") is None:
        raise ValueError("estimator requires materialized cross_token_reuse_tokens")
    token_tile_size = int(parameters["cross_token_reuse_tokens"])
    architecture_regime = {
        "refill_data_width_bits": cache_refill_data_width_bits,
        "refill_payload_units": "full_board_axi_payload_bits",
        "cross_token_reuse_tokens": token_tile_size,
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
                "contract_id": "w4a8_bounded_integer_operator_schedule_v1",
                "source_sha256": integer_operator_source_identity(),
                "normalization": "two streamed vector passes plus fixed restoring statistics/reciprocal stages and a 32-cycle iterative 64-bit square root",
                "attention": "causal and explicitly masked QK/PV rows with signed A8xA8 products, independent Q/K/V Q31 projection scales, and row Softmax",
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
    batch_context = int(parameters.get("batch_size", workload.get("batch_size", sequence)) or sequence)
    max_seq_len = int(parameters.get("max_seq_len", workload.get("sequence_length", sequence)) or sequence)
    token_tile_size = max(1, min(batch_context, sequence, token_tile_size))
    if max_seq_len > 1:
        token_tile_size = min(token_tile_size, max(1, max_seq_len // 2))
    # Record the effective bounded context after the same legality clamp used
    # by LinearParams. The estimator must not describe one reuse value while
    # charging traffic and cycles for a different materialized schedule.
    architecture_regime["cross_token_reuse_tokens"] = token_tile_size
    # This is the materialized Linear schedule context, not a legacy fixed
    # token tile. All traffic and cycle estimates below must follow the selected
    # cross-token reuse candidate.
    token_chunks = math.ceil(tokens / token_tile_size)
    token_slot_factor = token_chunks * token_tile_size / tokens
    for role, elements in matrices.items():
        input_dim = input_dimensions[role]
        if linear_schedule in {"token_interleaved_fp_pipeline_v2", "token_interleaved_policy_mac_v3"}:
            output_dim = math.ceil(elements / input_dim)
            mac_terms = math.ceil(input_dim / cols)
            output_tiles = math.ceil(output_dim / rows)
            # Integer MAC/reduction stages are one-cycle elastic DSP logic;
            # FP estimates retain their separately calibrated Vivado-IP fill.
            pipe_fill = (1 + int(math.log2(cols)) + 1) if integer_mac else (9 + 12 * int(math.log2(cols)) + 12)
            compute = output_tiles * (mac_terms * token_slot_factor + pipe_fill * token_chunks / tokens)
            services.append(max(input_dim / lanes, compute + math.ceil(output_dim / lanes)))
            linear_activation_bits += 2 * token_tile_size * (input_dim + output_dim) * int(parameters.get("elem_bits", 16))
        else:
            mac_service = 2 + 9 + 12 + 12 * math.log2(cols)
            services.append(input_dim / lanes + elements * mac_service / (rows * cols))
    if integer_mac:
        q_heads = int(workload.get("num_q_heads", 0) or 0)
        head_dim = int(workload.get("head_dim", 0) or 0)
        intermediate = int(workload.get("intermediate_size", hidden) or hidden)
        vector_beats = math.ceil(hidden / lanes)
        intermediate_beats = math.ceil(intermediate / lanes)
        # Structural cycles follow the current integer operator topology:
        # two streamed norm passes, causal QK/PV key visits, per-head rotate
        # beats, gated activation/multiply, and two residual streams. These are
        # bounded source-derived estimates, not measured latency or QoR.
        # Two normalization operators each perform a bounded 32-iteration
        # restoring square root after their streamed statistics pass. Charge
        # that source-bound latency rather than treating sqrt as combinational.
        norm_sqrt_iterations = 32
        norm_cycles = 2 * sequence * vector_beats * 2 + 2 * sequence * norm_sqrt_iterations
        attention_cycles = q_heads * sequence * (sequence + 1) + q_heads * sequence
        rope_cycles = q_heads * sequence * math.ceil(max(1, head_dim) / lanes)
        ffn_pointwise_cycles = sequence * intermediate_beats * 2
        residual_cycles = 2 * sequence * vector_beats
        services.extend([
            norm_cycles,
            attention_cycles,
            rope_cycles,
            ffn_pointwise_cycles,
            residual_cycles,
        ])
    else:
        services.extend([hidden * 24, sequence * hidden * 24])
    compute_cycles_per_layer = sum(services) + (tokens - 1) * max(services)
    axi_bits = int(workload.get("axi_data_width_bits", 0) or 0)
    if axi_bits <= 0 or axi_bits % 8:
        raise ValueError("estimator requires a declared byte-aligned board AXI data width")
    weight_image_bytes_per_layer = sum(
        math.ceil(int(term["elements"]) * int(term["element_bits"]) / 8.0)
        for term in terms
    )

    # Model the actual bounded-cache traversal, including repeated DDR tile
    # refills for matrices larger than the cache. A matrix that fits in the
    # cache is loaded once for the layer; otherwise each token chunk revisits
    # the tile sequence and therefore re-reads it from external DDR. Bias and
    # vector terms remain part of the complete model-semantic image.
    refill_words_per_layer = 0
    cache_tile_entry_bits = 0
    for role, elements in role_elements.items():
        bits = role_bits[role]
        if role in matrices:
            width_elements = rows * cols if cols > lanes else lanes * lanes
            matrix_entries = math.ceil((elements * bits) / max(1, width_elements * bits))
            tile_count = math.ceil(matrix_entries / cache_tile_words)
            traversals = 1 if tile_count <= cache_tile_count else token_chunks
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
    ddr_refill_beats_per_layer = math.ceil(weight_image_bytes_per_layer / (axi_bits / 8))
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
    axi_words_per_burst = max(1, min(256, 4096 // (axi_bits // 8))) * axi_words_per_beat
    for role, elements in matrices.items():
        input_dim = input_dimensions[role]
        output_dim = math.ceil(elements / input_dim)
        width_elements = rows * cols if cols > lanes else lanes * lanes
        entries = math.ceil(output_dim * input_dim / width_elements)
        tile_count = math.ceil(entries / cache_tile_words)
        traversals = 1 if tile_count <= cache_tile_count else token_chunks
        tile_requests_per_layer += tile_count * traversals
        image_words_per_cache_word = width_elements * role_bits[role] // 32
        for tile_index in range(tile_count):
            tile_entries = min(cache_tile_words, entries - tile_index * cache_tile_words)
            tile_words = tile_entries * image_words_per_cache_word
            tile_beats = math.ceil(tile_words / axi_words_per_beat)
            tile_axi_bursts_per_layer += math.ceil(tile_beats / max(1, axi_words_per_burst // axi_words_per_beat)) * traversals
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
    initial_refill_cycles = refill_service_cycles_per_layer
    overlapped_refill_stall_cycles = max(0, refill_service_cycles_per_layer - compute_cycles_per_layer)
    pipeline_cycles = (
        initial_refill_cycles
        + layers * compute_cycles_per_layer
        + max(0, layers - 1) * overlapped_refill_stall_cycles
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
            "cycles": pipeline_cycles,
            "compute_cycles_per_layer": compute_cycles_per_layer,
            "ddr_refill_beats_per_layer": ddr_refill_beats_per_layer,
            "ddr_refill_words_per_layer": refill_words_per_layer,
            "ddr_refill_bytes_per_layer": refill_bytes_per_layer,
            "cache_refill_data_width_bits": cache_refill_data_width_bits,
            "effective_cross_token_reuse_tokens": token_tile_size,
            "response_words_per_cycle": response_words_per_cycle,
            "axi_words_per_beat": axi_words_per_beat,
            "tile_requests_per_layer": tile_requests_per_layer,
            "axi_bursts_per_layer": axi_bursts_per_layer,
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


def estimate(features: dict, samples: list[dict]) -> dict[str, Any]:
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
    for key in (*RESOURCE_KEYS, "cycles", "clock_frequency_mhz"):
        proxy = features["proxies"][key]
        corrected = [_value(sample, key) * proxy / sample["cost_features"]["proxies"][key] for sample in anchors]
        estimates[key] = sum(weight * value for weight, value in zip(weights, corrected)) / sum(weights)
        if estimates[key] > 0:
            spreads.append(max(abs(value / estimates[key] - 1) for value in corrected))
    cycles = max(1, round(estimates["cycles"]))
    for key, minimum in features.get("resource_lower_bounds", {}).items():
        estimates[key] = max(estimates[key], minimum)
    clock = estimates["clock_frequency_mhz"]
    tps = features["workload"]["processed_tokens"] * clock * 1_000_000 / cycles
    factor = max(1.25, 1 + min(distances), 1 + max(spreads, default=0))
    cross_model = any(sample["cost_features"].get("family") != features["family"] for sample in anchors)
    if cross_model:
        factor = max(2.0, factor)
    return {
        "status": "estimated", "model": MODEL,
        "resources": {key: max(0, round(estimates[key])) for key in RESOURCE_KEYS},
        "clock_frequency_mhz": clock, "latency_cycles": cycles,
        "performance_tokens_per_second": tps,
        "anchor_source_fingerprints": [sample["source_fingerprint"] for sample in anchors],
        "calibration_sample_count": len(anchors),
        "cross_model_extrapolation": not bool(same_family),
        "cross_model_calibration": cross_model,
        "extrapolation_distance": min(distances),
        "sensitivity_bounds": {
            "performance_tokens_per_second": [tps / factor, tps * factor],
            "resources": {key: [value / factor, value * factor] for key, value in ((key, estimates[key]) for key in RESOURCE_KEYS)},
        },
        "uncertainty": "Sensitivity bounds, not statistical confidence intervals. Confirm with the next synthesis/source-cycle result.",
        "assumptions": "Source-bound ratios calibrate structural pipeline fill/bottleneck, PE and memory-packing proxies. Clock is inherited from compatible synthesis anchors; bank counts do not imply compute speedup. Architectural changes require new anchors.",
    }


def validation_report(samples: list[dict]) -> dict:
    errors: dict[str, list[float]] = defaultdict(list)
    zero_errors: dict[str, list[float]] = defaultdict(list)
    count = 0
    for held_out in samples:
        if not held_out.get("cost_features"):
            continue
        training = [sample for sample in samples if sample["source_fingerprint"] != held_out["source_fingerprint"]]
        prediction = estimate(held_out["cost_features"], training)
        if prediction["status"] != "estimated":
            continue
        count += 1
        for key in (*RESOURCE_KEYS, "clock_frequency_mhz", "performance_tokens_per_second"):
            actual = _value(held_out, key)
            predicted = prediction["resources"][key] if key in RESOURCE_KEYS else prediction[key]
            if actual > 0:
                errors[key].append(abs(predicted - actual) / actual)
            else:
                zero_errors[key].append(abs(predicted))
    return {
        "method": "leave_one_source_fingerprint_out",
        "sample_count": len(samples),
        "held_out_prediction_count": count,
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
