from pathlib import Path

import numpy as np


PAYLOAD_DIR = Path(__file__).resolve().parents[1] / "results/plan6/huginn_recurrent_core"
INPUT_PATH = PAYLOAD_DIR / "rmsnorm.bf16"
OUTPUT_PATH = PAYLOAD_DIR / "rmsnorm.q4_12"
EXPECTED_VALUES = 4 * 4 * 5280


def main():
    bf16 = np.fromfile(INPUT_PATH, dtype="<u2")
    if bf16.size != EXPECTED_VALUES:
        raise ValueError(f"expected {EXPECTED_VALUES} BF16 values, got {bf16.size}")
    values = (bf16.astype(np.uint32) << 16).view(np.float32)
    if not np.isfinite(values).all():
        raise ValueError("Norm gamma contains a non-finite value")
    scaled = np.rint(values.astype(np.float64) * 4096)
    if np.any(scaled < -32768) or np.any(scaled > 32767):
        raise ValueError("Norm gamma does not fit Q4.12")
    quantized = scaled.astype("<i2")
    quantized.tofile(OUTPUT_PATH)
    print(f"values={quantized.size} bytes={OUTPUT_PATH.stat().st_size} output={OUTPUT_PATH}")


if __name__ == "__main__":
    main()
