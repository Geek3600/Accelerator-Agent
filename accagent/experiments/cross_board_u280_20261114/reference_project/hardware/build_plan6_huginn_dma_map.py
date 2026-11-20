"""Build the fixed Huginn payload map consumed by the Plan 6 DMA controller."""
import hashlib
import json
from pathlib import Path

from hardware.export_plan6_huginn_core import build_huginn_linear_operator_map


ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_DIR = ROOT / "results/plan6/huginn_recurrent_core"
MANIFEST = PAYLOAD_DIR / "manifest.json"
OUTPUT = PAYLOAD_DIR / "dma_operator_map.json"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    manifest = json.loads(MANIFEST.read_text())
    operators = build_huginn_linear_operator_map(manifest)
    if len(operators) != 21:
        raise ValueError(f"expected 21 Huginn linear operators, found {len(operators)}")
    result = {
        "format": "Plan6-Huginn-DMA-Operator-Map-v1",
        "payload_manifest_sha256": sha256(MANIFEST),
        "weight_files_sha256": {
            name: sha256(PAYLOAD_DIR / name)
            for name in ("weights.usw512", "adapter.usw512")
        },
        "gamma_files_sha256": {
            name: sha256(PAYLOAD_DIR / name)
            for name in ("gamma.fp16", "adapter_gamma.fp16")
        },
        "operators": operators,
    }
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    return result


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, ensure_ascii=False))
