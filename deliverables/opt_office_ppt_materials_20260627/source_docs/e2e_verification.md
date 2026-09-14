# E2E Functional Verification Framework

## Goal  

This flow is for **real-data end-to-end verification** of the current accelerator:

- real OPT-125M weights
- real inputs
- full-chain output comparison

At the moment the repository only contains two **example tensor dump files**, not a complete end-to-end dataset:

- `weight/QKVProj/q_125mopt.json`
- `weight/layernorm/125mopt_layernorm.json`

So the current implementation provides a **framework scaffold** that:

1. inspects torch text dumps
2. extracts named tensors
3. normalizes them into reusable metadata + binary files
4. records which real artifacts are still missing for full end-to-end checking

## Script

Main script:

- `scripts/verification/opt125m_e2e.py`

Sample manifest:

- `scripts/verification/sample_opt125_manifest.json`

## Commands

Inspect one example file:

```bash
python scripts/verification/opt125m_e2e.py inspect weight/QKVProj/q_125mopt.json
python scripts/verification/opt125m_e2e.py inspect weight/layernorm/125mopt_layernorm.json
```

Prepare a normalized sample case:

```bash
python scripts/verification/opt125m_e2e.py prepare-case \
  scripts/verification/sample_opt125_manifest.json \
  --out-dir verification/cases/opt125m_sample
```

## Output Layout

The prepared case directory contains:

- `resolved_manifest.json`
- `artifacts/*.meta.json`
- `artifacts/*.f32.bin`

Each tensor entry is exported as:

- one metadata JSON
- one raw little-endian FP32 binary file

## Important Notes

1. The current sample files are **PyTorch text dumps**, not standard JSON.
2. The `layernorm` example contains duplicate `weight` labels; the sample manifest resolves them by `occurrence`.
3. This is **not yet a full Top-level golden check**, because the repository still lacks complete real artifacts for:
   - all layer weights/biases
   - quantization parameters
   - full input case
   - full final golden output

## Next Step

When the real verification files are ready, extend the manifest with:

- Top input tensor
- all layer weights / bias / scale / zero-point
- golden final output

Then the next script stage can drive the actual simulator and compare full-chain outputs automatically.
