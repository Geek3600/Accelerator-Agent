#!/usr/bin/env python3
"""Generate deterministic real-model golden tensors for hardware verification."""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import re
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "spatialaccagent.target_model_reference.v1"
DEFAULT_SEED = 20260710


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tensor_sha256(tensor: Any) -> str:
    value = tensor.detach().cpu().contiguous().float().numpy()
    return hashlib.sha256(value.tobytes()).hexdigest()


def safe_id(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "tensor"


def first_tensor(value: Any) -> Any | None:
    try:
        import torch
    except ImportError:
        return None
    if isinstance(value, torch.Tensor):
        return value
    if isinstance(value, (list, tuple)):
        for item in value:
            found = first_tensor(item)
            if found is not None:
                return found
    if isinstance(value, dict):
        for item in value.values():
            found = first_tensor(item)
            if found is not None:
                return found
    return None


def nested_value(data: Any, key: str) -> Any:
    if isinstance(data, dict):
        if key in data:
            return data[key]
        for value in data.values():
            found = nested_value(value, key)
            if found is not None:
                return found
    if isinstance(data, list):
        for value in data:
            found = nested_value(value, key)
            if found is not None:
                return found
    return None


def decoder_layers(model: Any) -> Any:
    candidates = [
        getattr(getattr(model, "model", None), "layers", None),
        getattr(getattr(getattr(model, "model", None), "decoder", None), "layers", None),
        getattr(getattr(model, "transformer", None), "h", None),
        getattr(getattr(model, "gpt_neox", None), "layers", None),
    ]
    for value in candidates:
        if value is not None and len(value) > 0:
            return value
    raise ValueError(f"unsupported decoder layer container for {type(model).__name__}")


def source_weight_hash(weight_manifest: dict[str, Any], run_dir: Path) -> str:
    if weight_manifest.get("checkpoint_fingerprint_sha256"):
        return str(weight_manifest["checkpoint_fingerprint_sha256"])
    weights = weight_manifest.get("weights", {}) if isinstance(weight_manifest.get("weights"), dict) else {}
    if weights.get("checkpoint_fingerprint_sha256"):
        return str(weights["checkpoint_fingerprint_sha256"])
    if weights.get("sha256"):
        return str(weights["sha256"])
    hashes_path = run_dir / "verification" / "model_weights" / "artifact_hashes.json"
    if hashes_path.exists():
        hashes = read_json(hashes_path)
        for item in hashes.get("artifacts", []):
            if isinstance(item, dict) and item.get("role") == "hf_safetensors_weights" and item.get("sha256"):
                return str(item["sha256"])
    path = Path(str(weights.get("path") or ""))
    return sha256_file(path) if path.exists() else ""


def capture_real_model(
    run_dir: Path,
    out_dir: Path,
    seed: int,
    sequence_length: int | None,
) -> dict[str, Any]:
    import torch
    from transformers import AutoModelForCausalLM

    weight_manifest_path = run_dir / "verification" / "model_weights" / "weight_manifest.json"
    accelerator_weight_catalog_path = run_dir / "verification" / "model_weights" / "transformer_block_weight_catalog.json"
    model_config_path = run_dir / "input" / "model_config.json"
    numeric_policy_path = run_dir / "input" / "numeric_policy.json"
    pipeline_plan_path = run_dir / "pipeline_planning" / "pipeline_plan.json"
    weight_manifest = read_json(weight_manifest_path)
    accelerator_weight_catalog = read_json(accelerator_weight_catalog_path)
    model_config = read_json(model_config_path)
    numeric_policy = read_json(numeric_policy_path)
    pipeline_plan = read_json(pipeline_plan_path)
    semantic_adapter_entry = weight_manifest.get("semantic_adapter", {}) if isinstance(weight_manifest.get("semantic_adapter"), dict) else {}
    semantic_adapter = semantic_adapter_entry.get("contract", {}) if isinstance(semantic_adapter_entry.get("contract"), dict) else {}
    semantic_stages = semantic_adapter.get("semantic_stages", {}) if isinstance(semantic_adapter.get("semantic_stages"), dict) else {}
    snapshot = Path(str((weight_manifest.get("snapshot") or {}).get("snapshot_dir") or ""))
    revision = str((weight_manifest.get("snapshot") or {}).get("revision") or "")
    model_id = str(weight_manifest.get("model_id") or model_config.get("model_id") or "")
    if not snapshot.is_dir():
        raise FileNotFoundError(f"target model snapshot is missing: {snapshot}")
    if (
        accelerator_weight_catalog.get("status") != "pass"
        or accelerator_weight_catalog.get("accelerator_scope") != "transformer_blocks_only"
        or accelerator_weight_catalog.get("scope_coverage_complete") is not True
    ):
        raise ValueError("complete transformer-block weight catalog is not ready")
    if not semantic_stages:
        raise ValueError("model semantic adapter has no semantic stage mapping")
    pipeline_ops = {
        str(stage.get("op") or "")
        for stage in pipeline_plan.get("stages", [])
        if isinstance(stage, dict) and stage.get("op")
    }
    missing_semantic_ops = sorted(pipeline_ops - set(semantic_stages))
    if missing_semantic_ops:
        raise ValueError(f"model semantic adapter does not cover pipeline ops {missing_semantic_ops}")

    target_seq = sequence_length or int(
        nested_value(model_config, "target_max_seq_len")
        or nested_value(model_config, "max_seq_len")
        or 1
    )
    if target_seq <= 0:
        raise ValueError(f"invalid target sequence length: {target_seq}")

    model = AutoModelForCausalLM.from_pretrained(
        snapshot,
        local_files_only=True,
        dtype=torch.float32,
        low_cpu_mem_usage=True,
    )
    model.eval()
    layers = decoder_layers(model)
    memory_schedule = pipeline_plan.get("memory_schedule", {}) if isinstance(pipeline_plan.get("memory_schedule"), dict) else {}
    target_layer_count = int(memory_schedule.get("num_layers") or model_config.get("num_layers") or len(layers))
    if target_layer_count != len(layers):
        raise ValueError(
            f"accelerator target layer count must cover the complete target model: "
            f"accelerator={target_layer_count} model={len(layers)}"
        )
    first_layer = layers[0]
    hidden_size = int(model.config.hidden_size)
    generator = torch.Generator(device="cpu").manual_seed(seed)
    random_input = torch.randn((1, target_seq, hidden_size), generator=generator, dtype=torch.float32)
    position_ids = torch.arange(target_seq, dtype=torch.long).unsqueeze(0)

    captures: dict[str, dict[str, Any]] = {}
    semantic_runtime_inputs: dict[str, Any] = {}
    semantic_runtime_values: dict[str, Any] = {}
    hooks = []

    def register_capture(name: str, module: Any) -> None:
        def pre_hook(_module: Any, args: Any, kwargs: Any) -> None:
            value = first_tensor((args, kwargs))
            if value is not None:
                captures.setdefault(name, {})["input"] = value.detach().cpu().float().clone()
            if name == "self_attn":
                for key in ("attention_mask", "position_ids", "cache_position"):
                    tensor = kwargs.get(key)
                    if isinstance(tensor, torch.Tensor):
                        semantic_runtime_inputs[key] = tensor.detach().cpu().clone()
                    elif key in kwargs:
                        semantic_runtime_values[key] = {
                            "kind": "none" if tensor is None else type(tensor).__name__,
                            "value": None if tensor is None else str(tensor),
                        }
                position_embeddings = kwargs.get("position_embeddings")
                if isinstance(position_embeddings, (list, tuple)) and len(position_embeddings) == 2:
                    cos, sin = position_embeddings
                    if isinstance(cos, torch.Tensor) and isinstance(sin, torch.Tensor):
                        semantic_runtime_inputs["rope_cos"] = cos.detach().cpu().clone()
                        semantic_runtime_inputs["rope_sin"] = sin.detach().cpu().clone()

        def post_hook(_module: Any, _args: Any, output: Any) -> None:
            value = first_tensor(output)
            if value is not None:
                captures.setdefault(name, {})["output"] = value.detach().cpu().float().clone()

        hooks.append(module.register_forward_pre_hook(pre_hook, with_kwargs=True))
        hooks.append(module.register_forward_hook(post_hook))

    for layer_index, layer in enumerate(layers):
        register_capture(f"decoder_layer_{layer_index}", layer)
    for name, module in first_layer.named_modules():
        if not name:
            continue
        if any(True for _ in module.parameters(recurse=False)) or name.endswith(
            ("input_layernorm", "post_attention_layernorm", "self_attn", "mlp", "act_fn")
        ):
            register_capture(name, module)

    with torch.inference_mode():
        kwargs = {
            "inputs_embeds": random_input,
            "position_ids": position_ids,
            "use_cache": False,
            "output_hidden_states": True,
            "return_dict": True,
        }
        try:
            result = model(**kwargs)
        except TypeError:
            kwargs.pop("position_ids", None)
            result = model(**kwargs)
    for hook in hooks:
        hook.remove()

    hidden_states = getattr(result, "hidden_states", None)
    if not hidden_states:
        raise ValueError("target model did not return hidden states")
    native_model_output = hidden_states[-1].detach().cpu().float()
    layer_output = captures.get("decoder_layer_0", {}).get("output")
    if layer_output is None:
        raise ValueError("first decoder layer output was not captured")
    accelerator_output = captures.get(f"decoder_layer_{target_layer_count - 1}", {}).get("output")
    if accelerator_output is None:
        raise ValueError("last target decoder layer output was not captured")

    out_dir.mkdir(parents=True, exist_ok=True)
    input_path = out_dir / "random_hidden_input.pt"
    layer_output_path = out_dir / "single_layer_output.pt"
    full_output_path = out_dir / "full_model_output.pt"
    native_output_path = out_dir / "native_model_output.pt"
    torch.save(random_input.cpu(), input_path)
    torch.save(layer_output, layer_output_path)
    torch.save(accelerator_output, full_output_path)
    torch.save(native_model_output, native_output_path)

    runtime_input_records = {}
    runtime_input_dir = out_dir / "semantic_runtime_inputs"
    for name, tensor in sorted(semantic_runtime_inputs.items()):
        path = runtime_input_dir / f"{safe_id(name)}.pt"
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(tensor, path)
        runtime_input_records[name] = {
            "path": str(path),
            "file_sha256": sha256_file(path),
            "tensor_sha256": tensor_sha256(tensor),
            "shape": list(tensor.shape),
            "dtype": str(tensor.dtype),
        }

    implementation_path_text = inspect.getsourcefile(type(first_layer)) or inspect.getfile(type(first_layer))
    implementation_path = Path(implementation_path_text).resolve()
    implementation_symbols = {
        "decoder_layer": f"{type(first_layer).__module__}.{type(first_layer).__qualname__}",
    }
    for name in ("self_attn", "mlp", "input_layernorm", "post_attention_layernorm"):
        module = getattr(first_layer, name, None)
        if module is not None:
            implementation_symbols[name] = f"{type(module).__module__}.{type(module).__qualname__}"

    records = []
    layer_records = []
    for name, values in sorted(captures.items()):
        input_tensor = values.get("input")
        output_tensor = values.get("output")
        if input_tensor is None or output_tensor is None:
            continue
        tensor_path = out_dir / "operators" / f"{safe_id(name)}.pt"
        tensor_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save({"input": input_tensor, "output": output_tensor}, tensor_path)
        records.append(
            {
                "module": name,
                "tensor_path": str(tensor_path),
                "tensor_file_sha256": sha256_file(tensor_path),
                "input_shape": list(input_tensor.shape),
                "input_dtype": str(input_tensor.dtype),
                "input_sha256": tensor_sha256(input_tensor),
                "output_shape": list(output_tensor.shape),
                "output_dtype": str(output_tensor.dtype),
                "output_sha256": tensor_sha256(output_tensor),
            }
        )
        if re.fullmatch(r"decoder_layer_\d+", name):
            layer_records.append(records[-1])
    layer_records.sort(key=lambda row: int(str(row["module"]).rsplit("_", 1)[1]))
    captured_layer_indices = [int(str(row["module"]).rsplit("_", 1)[1]) for row in layer_records]
    expected_layer_indices = list(range(target_layer_count))
    if captured_layer_indices != expected_layer_indices:
        raise ValueError(
            f"decoder-layer reference coverage/order mismatch: "
            f"expected={expected_layer_indices} captured={captured_layer_indices}"
        )

    source_tensors = {
        (int(row.get("layer_index")), str(row.get("parameter_suffix"))): row
        for row in accelerator_weight_catalog.get("tensors", [])
        if isinstance(row, dict) and row.get("name") and row.get("layer_index") is not None
    }
    weight_bindings = []
    for name, parameter in first_layer.named_parameters(recurse=True):
        source_row = source_tensors.get((0, name))
        if source_row is None:
            raise ValueError(f"transformer-block catalog is missing layer-0 parameter suffix {name}")
        source_name = str(source_row["name"])
        weight_path = out_dir / "weights" / f"{safe_id(name)}.pt"
        weight_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(parameter.detach().cpu().float(), weight_path)
        weight_bindings.append(
            {
                "tensor": source_name,
                "parameter_suffix": name,
                "path": str(weight_path),
                "file_sha256": sha256_file(weight_path),
                "shape": list(parameter.shape),
                "dtype": str(parameter.dtype),
                "sha256": tensor_sha256(parameter),
                "source_dtype": source_row.get("dtype"),
                "source_data_offsets": source_row.get("data_offsets"),
                "source_slice_sha256": source_row.get("source_slice_sha256"),
            }
        )

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": "ready",
        "run_dir": str(run_dir),
        "target_model": {
            "model_id": model_id,
            "revision": revision,
            "snapshot": str(snapshot),
            "architecture": type(model).__name__,
            "num_hidden_layers": len(layers),
            "hidden_size": hidden_size,
            "accelerator_scope": "transformer_blocks_only",
            "excluded_model_regions": semantic_adapter.get("excluded_model_regions", []),
        },
        "weights": {
            "source_manifest": str(weight_manifest_path),
            "source_manifest_sha256": sha256_file(weight_manifest_path),
            "source_checkpoint_sha256": source_weight_hash(weight_manifest, run_dir),
            "accelerator_weight_catalog": str(accelerator_weight_catalog_path),
            "accelerator_weight_catalog_sha256": sha256_file(accelerator_weight_catalog_path),
            "accelerator_scope": "transformer_blocks_only",
            "accelerator_scope_tensor_count": accelerator_weight_catalog.get("tensor_count"),
            "real_target_weights": True,
            "loaded_by_reference_model": True,
            "layer_0_tensor_coverage_complete": bool(weight_bindings),
            "layer_0_tensor_bindings": weight_bindings,
        },
        "input": {
            "source": "random",
            "seed": seed,
            "distribution": "torch.randn",
            "dtype": str(random_input.dtype),
            "shape": list(random_input.shape),
            "path": str(input_path),
            "file_sha256": sha256_file(input_path),
            "tensor_sha256": tensor_sha256(random_input),
        },
        "reference": {
            "engine": f"transformers.{type(model).__name__}",
            "independent_of_rtl": True,
            "uses_same_input_and_weights": True,
            "expected_output_source": "target_model_inference",
            "oracle_kind": "high_precision_target_model",
            "execution_dtype": str(random_input.dtype),
            "numeric_policy": str(numeric_policy_path),
            "numeric_policy_sha256": sha256_file(numeric_policy_path),
            "numeric_policy_binding": {
                "reference_execution": "high_precision_target_model",
                "comparison_against_hardware_uses_explicit_tolerance": True,
                "weight_dtype": numeric_policy.get("default_rules", {}).get("weight_dtype"),
                "activation_dtype": numeric_policy.get("default_rules", {}).get("activation_dtype"),
                "acc_dtype": numeric_policy.get("default_rules", {}).get("acc_dtype"),
            },
            "single_layer_output": {
                "path": str(layer_output_path),
                "file_sha256": sha256_file(layer_output_path),
                "tensor_sha256": tensor_sha256(layer_output),
                "shape": list(layer_output.shape),
                "dtype": str(layer_output.dtype),
            },
            "full_model_output": {
                "path": str(full_output_path),
                "file_sha256": sha256_file(full_output_path),
                "tensor_sha256": tensor_sha256(accelerator_output),
                "shape": list(accelerator_output.shape),
                "dtype": str(accelerator_output.dtype),
                "scope": "all_target_decoder_layers_at_accelerator_output_boundary",
                "target_layer_count": target_layer_count,
                "source_capture": f"decoder_layer_{target_layer_count - 1}",
            },
            "native_model_output": {
                "path": str(native_output_path),
                "file_sha256": sha256_file(native_output_path),
                "tensor_sha256": tensor_sha256(native_model_output),
                "shape": list(native_model_output.shape),
                "dtype": str(native_model_output.dtype),
                "scope": "native_model_hidden_state_after_model_tail",
                "acceptance_eligible": False,
                "reason": "the current accelerator contract implements decoder layers and does not declare the model-tail operators",
            },
            "operator_records": records,
            "layer_output_records": layer_records,
            "layer_output_record_order": "numeric_decoder_layer_index_ascending",
            "all_target_layers_captured": captured_layer_indices == expected_layer_indices,
            "semantic_stage_map": semantic_stages,
            "semantic_runtime_inputs": runtime_input_records,
            "semantic_runtime_values": semantic_runtime_values,
            "semantic_execution_contract": {
                "batch_size": int(random_input.shape[0]),
                "sequence_length": target_seq,
                "position_ids": "explicit torch.arange(0, sequence_length)",
                "use_cache": False,
                "dropout": "disabled by model.eval()",
                "attention_mask": "captured actual first-layer self-attention argument; a recorded None delegates causality to the selected attention implementation",
                "attention_implementation": str(getattr(model.config, "_attn_implementation", "eager")),
                "causal_rule_without_explicit_mask": "query position i may attend key positions j <= i only",
                "position_embeddings": "captured actual first-layer RoPE cosine/sine arguments",
                "reference_execution_dtype": str(random_input.dtype),
                "hardware_boundary_casts": "defined by immutable pipeline stage numeric contracts",
            },
            "model_implementation": {
                "source_path": str(implementation_path),
                "source_sha256": sha256_file(implementation_path),
                "symbols": implementation_symbols,
                "torch_version": torch.__version__,
                "transformers_version": __import__("transformers").__version__,
            },
            "semantic_adapter": {
                "path": semantic_adapter_entry.get("path"),
                "sha256": semantic_adapter_entry.get("sha256"),
                "model_family": semantic_adapter.get("model_family"),
            },
        },
        "policy": {
            "expected_outputs_are_not_random": True,
            "expected_outputs_are_computed_from_random_input_and_real_weights": True,
            "rtl_output_is_never_read_by_reference_generation": True,
            "missing_operator_or_weight_binding_is_not_a_pass": True,
            "one_inference_run_supplies_all_hierarchical_golden_outputs": True,
            "board_expected_output_uses_declared_accelerator_boundary": True,
            "native_model_tail_output_is_audit_only_unless_pipeline_declares_tail_operators": True,
            "transformer_blocks_are_the_only_accelerator_acceptance_scope": True,
        },
    }
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate real target-model random-input golden tensors")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--sequence-length", type=int)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    run_dir = args.run_dir.resolve()
    out_dir = (args.out_dir or run_dir / "verification" / "model_reference").resolve()
    manifest_path = out_dir / "reference_manifest.json"
    try:
        manifest = capture_real_model(run_dir, out_dir, args.seed, args.sequence_length)
    except Exception as exc:
        write_json(
            manifest_path,
            {
                "schema_version": SCHEMA_VERSION,
                "status": "fail",
                "run_dir": str(run_dir),
                "error": str(exc),
            },
        )
        print(f"target_model_reference.py: {exc}", file=sys.stderr)
        print(manifest_path)
        return 1
    write_json(manifest_path, manifest)
    write_json(
        out_dir / "golden_provenance.json",
        {
            "schema_version": "spatialaccagent.target_model_golden_provenance.v1",
            "status": "pass",
            "target_model": manifest.get("target_model"),
            "source_checkpoint_sha256": manifest.get("weights", {}).get("source_checkpoint_sha256"),
            "input": manifest.get("input"),
            "single_layer_output": manifest.get("reference", {}).get("single_layer_output"),
            "full_model_output": manifest.get("reference", {}).get("full_model_output"),
            "native_model_output": manifest.get("reference", {}).get("native_model_output"),
            "all_target_layers_captured": manifest.get("reference", {}).get("all_target_layers_captured"),
            "independent_of_rtl": True,
            "expected_output_source": "target_model_inference",
            "accelerator_output_boundary": "all_target_decoder_layers_at_accelerator_output_boundary",
        },
    )
    print(manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
