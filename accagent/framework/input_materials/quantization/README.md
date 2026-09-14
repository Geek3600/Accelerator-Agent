# Quantization Input Materials

Place numeric precision and quantization materials for the current accelerator
design run here. Stage 0 treats this directory as the numeric input for this run.

Supported inputs:
- docs (`.md`, `.rst`, `.txt`)
- `.docx` and `.pdf` documents
- JSON/YAML policy snippets
- numeric notes or benchmark requirements

If no policy file is provided, the framework uses the fallback policy:
- weight/activation = FP16
- accumulation = FP32
- scale = FP16
- valid-output requirement and no-deadlock check.
