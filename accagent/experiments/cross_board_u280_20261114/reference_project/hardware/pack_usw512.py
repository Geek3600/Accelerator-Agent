"""Bit-exact USW-512 packing for ternary and bounded sparse weights."""

import math

import numpy as np


WINDOW_SIZE = 256
DENSE_BYTES = 52
SLOT_COUNT = 4
SLOT_BYTES = 3
WORD_BYTES = 64
Q4_12_SCALE = 1 << 12


def _array(value, name):
    if hasattr(value, "detach"):
        value = value.detach()
    if hasattr(value, "cpu"):
        value = value.cpu()
    if str(getattr(value, "dtype", "")) == "torch.bfloat16":
        value = value.float()
    result = np.asarray(value)
    if result.dtype.kind not in "iuf":
        raise TypeError(f"{name} must contain real numeric values")
    result = result.astype(np.float64, copy=False)
    if not np.isfinite(result).all():
        raise ValueError(f"{name} must contain only finite values")
    return result


def _positive_dimension(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return int(value)


def window_slot_mask(indices, values, columns):
    """Select up to four largest-magnitude outliers per 256-value window."""
    indices = np.asarray(indices, dtype=np.int64)
    values = np.asarray(values, dtype=np.float64)
    columns = _positive_dimension(columns, "columns")
    if indices.shape != values.shape:
        raise ValueError("indices and values must have the same shape")
    if indices.size == 0:
        return np.zeros(indices.shape, dtype=bool)

    chunks = (columns + WINDOW_SIZE - 1) // WINDOW_SIZE
    window_keys = (indices // columns) * chunks + (indices % columns) // WINDOW_SIZE
    order = np.lexsort((indices, -np.abs(values), window_keys))
    ordered_keys = window_keys[order]
    starts = np.r_[0, np.flatnonzero(ordered_keys[1:] != ordered_keys[:-1]) + 1]
    ranks = np.arange(order.size) - np.repeat(starts, np.diff(np.r_[starts, order.size]))
    keep = np.zeros(indices.shape, dtype=bool)
    keep[order[ranks < SLOT_COUNT]] = True
    return keep


def _q4_12_code(normalized):
    scaled = normalized * Q4_12_SCALE
    if not math.isfinite(normalized) or not math.isfinite(scaled):
        raise OverflowError("normalized W_sp value is outside signed Q4.12 range")
    return min(32767, max(-32768, int(round(scaled))))


def _encode_dense(trits):
    encoded = bytearray(DENSE_BYTES)
    for byte_index in range(51):
        code = 0
        for digit_index in range(5):
            trit = int(trits[byte_index * 5 + digit_index])
            code += (trit + 1) * (3 ** digit_index)
        encoded[byte_index] = code
    encoded[51] = int(trits[255]) + 1
    return encoded


def _decode_dense(encoded):
    trits = np.empty(WINDOW_SIZE, dtype=np.int8)
    position = 0
    for byte_index in range(51):
        code = encoded[byte_index]
        if code > 242:
            raise ValueError("dense radix-3 byte is outside the valid range 0..242")
        for _ in range(5):
            trits[position] = code % 3 - 1
            code //= 3
            position += 1
    final_code = encoded[51]
    if final_code > 2:
        raise ValueError("the final dense byte must encode exactly one trit")
    trits[255] = final_code - 1
    return trits


def pack_matrix_to_usw512(W_tern, W_sp, alpha, beta_steps):
    """Return packed bytes, Gamma[r, c], effective trits, and sparse Q4.12 codes.

    Sparse values are normalized by alpha, rounded to Q4.12, and saturated to
    signed int16. Outliers beyond four per window are projected onto the
    ternary grid.
    Each 64-byte record stores four 24-bit slots in bits [95:0], followed by
    the 52-byte radix-3 payload in bits [511:96].
    """
    ternary = _array(W_tern, "W_tern").copy()
    sparse = _array(W_sp, "W_sp").copy()
    scales = _array(alpha, "alpha")
    step_scales = _array(beta_steps, "beta_steps")

    if ternary.ndim != 2 or ternary.shape[0] == 0 or ternary.shape[1] == 0:
        raise ValueError("W_tern must have shape [C_out, K] with positive dimensions")
    if sparse.shape != ternary.shape:
        raise ValueError("W_sp must have the same [C_out, K] shape as W_tern")
    if not np.isin(ternary, (-1.0, 0.0, 1.0)).all():
        raise ValueError("W_tern values must be exactly -1, 0, or +1")

    channels, columns = ternary.shape
    if scales.shape != (channels,):
        raise ValueError("alpha must have shape [C_out]")
    if step_scales.ndim != 2 or step_scales.shape[0] == 0 or step_scales.shape[1] != channels:
        raise ValueError("beta_steps must have shape [R, C_out] with positive R")
    if (scales < 0).any():
        raise ValueError("alpha values must be non-negative")
    if ((step_scales < 0.80) | (step_scales > 2.00)).any():
        raise ValueError("beta_steps values must be within the Plan 5 range [0.80, 2.00]")

    gamma_full = step_scales * scales[np.newaxis, :]
    if not np.isfinite(gamma_full).all() or (np.abs(gamma_full) > np.finfo(np.float16).max).any():
        raise OverflowError("Gamma values cannot be represented as finite FP16")
    gamma = gamma_full.astype("<f2")
    if not np.isfinite(gamma).all():
        raise OverflowError("Gamma values cannot be represented as finite FP16")

    ternary = ternary.astype(np.int8, copy=False)
    flat_ternary = ternary.reshape(-1)
    flat_sparse = sparse.reshape(-1)
    sparse_indices = np.flatnonzero(flat_sparse)
    if (flat_ternary[sparse_indices] != 0).any():
        raise ValueError("W_tern must be zero at every nonzero W_sp coordinate")
    sparse_rows = sparse_indices // columns
    sparse_scales = scales[sparse_rows]
    if (sparse_scales == 0).any():
        raise ValueError("nonzero W_sp requires a positive alpha for its output channel")

    keep_slots = window_slot_mask(sparse_indices, flat_sparse[sparse_indices], columns)
    folded_indices = sparse_indices[~keep_slots]
    if folded_indices.size:
        folded_rows = folded_indices // columns
        folded_values = flat_sparse[folded_indices]
        folded_scales = scales[folded_rows]
        folded_trits = np.clip(np.rint(folded_values / folded_scales), -1, 1).astype(np.int8)
        flat_ternary[folded_indices] = folded_trits
        flat_sparse[folded_indices] = 0.0

    chunks = (columns + WINDOW_SIZE - 1) // WINDOW_SIZE

    for row in range(channels):
        row_alpha = float(scales[row])
        for chunk_index in range(chunks):
            start = chunk_index * WINDOW_SIZE
            stop = min(start + WINDOW_SIZE, columns)
            sparse_values = sparse[row, start:stop]
            sparse_positions = np.flatnonzero(sparse_values)
            if sparse_positions.size and (ternary[row, start:stop][sparse_positions] != 0).any():
                raise ValueError("W_tern must be zero at every nonzero W_sp coordinate")
            if sparse_positions.size > SLOT_COUNT:
                raise ValueError(
                    f"window ({row}, {chunk_index}) contains {sparse_positions.size} "
                    f"outliers; USW-512 supports at most {SLOT_COUNT}"
                )
            if sparse_positions.size and row_alpha == 0.0:
                raise ValueError("nonzero W_sp requires a positive alpha for its output channel")
            for local_index in sparse_positions:
                normalized = float(sparse_values[local_index]) / row_alpha
                _q4_12_code(normalized)

    packed = bytearray()
    sparse_q4_12 = np.zeros((channels, columns), dtype=np.int16)

    for row in range(channels):
        row_alpha = float(scales[row])
        for chunk_index in range(chunks):
            start = chunk_index * WINDOW_SIZE
            stop = min(start + WINDOW_SIZE, columns)
            valid_width = stop - start
            dense_trits = np.zeros(WINDOW_SIZE, dtype=np.int8)
            dense_trits[:valid_width] = ternary[row, start:stop]
            sparse_values = sparse[row, start:stop]
            sparse_positions = np.flatnonzero(sparse_values)

            slots = []
            for local_index in sparse_positions:
                sparse_weight = float(sparse_values[local_index])
                normalized = sparse_weight / row_alpha
                fixed_value = _q4_12_code(normalized)
                sparse_q4_12[row, start + local_index] = fixed_value
                if fixed_value != 0:
                    slots.append((local_index, abs(sparse_weight), fixed_value))
            slots.sort(key=lambda slot: slot[1], reverse=True)

            record = bytearray(WORD_BYTES)
            for slot_index in range(SLOT_COUNT):
                if slot_index < len(slots):
                    local_index, _, fixed_value = slots[slot_index]
                    local_index = int(local_index)
                    raw_value = fixed_value & 0xFFFF
                else:
                    local_index = 0
                    raw_value = 0
                slot_word = (local_index << 16) | raw_value
                slot_start = slot_index * SLOT_BYTES
                record[slot_start:slot_start + SLOT_BYTES] = slot_word.to_bytes(SLOT_BYTES, "little")
            record[12:] = _encode_dense(dense_trits)
            packed.extend(record)

    return bytes(packed), gamma, ternary.copy(), sparse_q4_12


def unpack_matrix_from_usw512(packed, rows, columns):
    """Decode USW-512 records into ternary weights and signed Q4.12 codes."""
    rows = _positive_dimension(rows, "rows")
    columns = _positive_dimension(columns, "columns")
    if not isinstance(packed, (bytes, bytearray, memoryview)):
        raise TypeError("packed must be bytes-like")
    packed = memoryview(packed).cast("B")
    chunks = (columns + WINDOW_SIZE - 1) // WINDOW_SIZE
    expected_length = rows * chunks * WORD_BYTES
    if len(packed) != expected_length:
        raise ValueError(f"packed length must be exactly {expected_length} bytes")

    ternary = np.zeros((rows, columns), dtype=np.int8)
    sparse_q4_12 = np.zeros((rows, columns), dtype=np.int16)
    record_index = 0

    for row in range(rows):
        for chunk_index in range(chunks):
            record_start = record_index * WORD_BYTES
            record = packed[record_start:record_start + WORD_BYTES]
            dense_trits = _decode_dense(record[12:64])
            start = chunk_index * WINDOW_SIZE
            valid_width = min(WINDOW_SIZE, columns - start)
            if (dense_trits[valid_width:] != 0).any():
                raise ValueError("trit padding beyond K must decode to zero")
            ternary[row, start:start + valid_width] = dense_trits[:valid_width]

            used_positions = set()
            for slot_index in range(SLOT_COUNT):
                slot_start = slot_index * SLOT_BYTES
                raw_value = int(record[slot_start]) | (int(record[slot_start + 1]) << 8)
                fixed_value = raw_value if raw_value < 0x8000 else raw_value - 0x10000
                local_index = int(record[slot_start + 2])
                if fixed_value == 0:
                    if local_index != 0:
                        raise ValueError("empty outlier slots must have local_idx zero")
                    continue
                if local_index >= valid_width:
                    raise ValueError("outlier local_idx points into padded columns beyond K")
                if local_index in used_positions:
                    raise ValueError("nonzero outlier slots must have distinct local_idx values")
                if dense_trits[local_index] != 0:
                    raise ValueError("dense ternary value must be zero at every nonzero outlier slot")
                used_positions.add(local_index)
                sparse_q4_12[row, start + local_index] = fixed_value
            record_index += 1

    return ternary, sparse_q4_12
