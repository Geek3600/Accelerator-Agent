"""Single-source FPGA IP contract shared by Stage 2 and Stage 5."""

from __future__ import annotations

import re
import json
from pathlib import Path
from typing import Any, Iterable


FORBIDDEN_SOURCE_PATTERNS = {
    "hardfloat_backend": re.compile(
        r"\b(?:hardfloat|RecFN|AddRecFN|MulRecFN|CompareRecFN|DivSqrtRecFN|INToRecFN|RecFNToIN)\b"
    ),
    "sync_read_mem_backend": re.compile(r"\bSyncReadMem\s*\("),
    "generic_queue_backend": re.compile(r"\bnew\s+Queue\s*\("),
    "inferred_mem_backend": re.compile(r"\bMem\s*\("),
    "legacy_combinational_fp_helper": re.compile(r"\bIeeeMath\.(?:add|sub|mul|lessThan|sum|to|from)Fp32\s*\("),
    "unhandshaked_physical_fp_helper": re.compile(
        r"\bPhysicalMath\.(?:addFp32|subFp32|mulFp32|divFp32|lessThanFp32|sumFp32|fp32ToSigned|signedToFp32|unsignedToFp32)\s*\("
    ),
}

REQUIRED_PHYSICAL_MARKERS = (
    "configureFpgaIp",
    '"fp_add_sp_12"',
    '"fp_sub_sp_12"',
    '"fp_mul_sp_9"',
    '"fp_div_sp_29"',
    '"fp_sqrt_sp_29"',
    '"xpm_memory_sdpram"',
    '"xpm_memory_sprom"',
    "PhysicalStreamFifo",
)

DSP_MULTIPLIER_IP_MARKER = "CONFIG.C_Mult_Usage {Full_Usage}"

FP_MODULE_NAME = re.compile(
    r"^(?:"
    r"fp_(?:add|sub|mul|div|sqrt)_sp_[0-9]+|"
    r"fp_cmp_(?:lt|eq|gt)_sp_[0-9]+|"
    r"fp_i2f_[su][0-9]+_sp_[0-9]+|"
    r"fp_f2i_[su][0-9]+_sp_[0-9]+"
    r")$"
)
FP_MODULE_INSTANTIATION = re.compile(
    r"(?m)^\s*(fp_[a-z0-9_]+)\s+[A-Za-z_$][A-Za-z0-9_$]*\s*\("
)


def simulation_source_contract() -> dict[str, Any]:
    return {
        "compute_models": "generated Vivado floating_point IP simulation models",
        "memory_models": "Xilinx XPM simulation library",
        "required_libraries": ["unisims_ver", "xpm"],
        "required_sources": ["glbl.v", "generated_ip_simulation_sources"],
        "same_module_names_as_implementation": True,
        "same_interface_and_cycle_latency_as_implementation": True,
        "behavioral_fallback_allowed": False,
    }


def discover_fp_modules(generated_root: Path) -> list[str]:
    """Return the Vivado floating-point blackboxes used by elaborated RTL."""

    paths = [*generated_root.glob("*.sv"), *generated_root.glob("*.v")]
    vivado_dir = generated_root / "vivado"
    if vivado_dir.is_dir():
        paths.extend(vivado_dir.rglob("*.sv"))
        paths.extend(vivado_dir.rglob("*.v"))
    modules: set[str] = set()
    for path in sorted(set(paths)):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for name in FP_MODULE_INSTANTIATION.findall(text):
            if FP_MODULE_NAME.fullmatch(name):
                modules.add(name)
    return sorted(modules)


def write_fp_module_manifest(generated_root: Path, manifest_path: Path) -> list[str]:
    modules = discover_fp_modules(generated_root)
    if not modules:
        raise ValueError(f"no Vivado floating-point modules found below {generated_root}")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text("\n".join(modules) + "\n", encoding="utf-8")
    return modules


def refresh_fpga_ip_simulation_closure(generated_root: Path, closure_path: Path) -> list[str]:
    """Bind the Stage 5 IP closure to the blackboxes emitted this elaboration."""

    payload = json.loads(closure_path.read_text(encoding="utf-8"))
    manifest_value = payload.get("ip_module_manifest")
    if not isinstance(manifest_value, str) or not manifest_value:
        raise ValueError("FPGA IP simulation closure is missing ip_module_manifest")
    manifest_path = Path(manifest_value)
    if not manifest_path.is_absolute():
        manifest_path = closure_path.parent / manifest_path
    modules = write_fp_module_manifest(generated_root, manifest_path)
    payload["status"] = "ready"
    payload["required_ip_modules"] = modules
    closure_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return modules


def check_fpga_ip_simulation_closure(path: Path) -> dict[str, Any]:
    """Validate only the small, executable IP/VCS handoff manifest.

    This deliberately validates stable structural facts instead of adding a
    second hash/identity system.  The actual VCS invocation remains
    responsible for resolving the target Vivado installation and generated IP
    simulation files at execution time.
    """

    errors: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {"status": "fail", "errors": [f"cannot read FPGA IP simulation closure: {exc}"]}

    if not isinstance(payload, dict):
        return {"status": "fail", "errors": ["FPGA IP simulation closure must be a JSON object"]}
    if payload.get("status") != "ready":
        errors.append("FPGA IP simulation closure is not ready")
    if payload.get("policy") != simulation_source_contract():
        errors.append("FPGA IP simulation closure policy does not match the required Vivado/XPM timing model")
    for key in ("ip_generation_tcl", "ip_output_dir", "ip_project_dir", "ip_module_manifest", "fpga_part"):
        if not isinstance(payload.get(key), str) or not payload[key]:
            errors.append(f"FPGA IP simulation closure is missing {key}")
    manifest_path = Path(str(payload.get("ip_module_manifest") or ""))
    if manifest_path and not manifest_path.is_absolute():
        manifest_path = path.parent / manifest_path
    manifest_modules: list[str] = []
    if not manifest_path.is_file():
        errors.append(f"FPGA IP module manifest is missing: {manifest_path}")
    else:
        manifest_modules = [
            line.strip()
            for line in manifest_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        invalid = [name for name in manifest_modules if not FP_MODULE_NAME.fullmatch(name)]
        if invalid:
            errors.append(f"FPGA IP module manifest contains unsupported names: {invalid}")
        if len(manifest_modules) != len(set(manifest_modules)):
            errors.append("FPGA IP module manifest contains duplicate names")
    required_modules = payload.get("required_ip_modules")
    if not isinstance(required_modules, list) or not required_modules:
        errors.append("FPGA IP simulation closure has no required floating-point modules")
    elif sorted(str(name) for name in required_modules) != sorted(manifest_modules):
        errors.append("FPGA IP simulation closure module list does not match the elaborated RTL manifest")
    vcs = payload.get("vcs_compile_requirements")
    if not isinstance(vcs, dict) or not all(
        isinstance(vcs.get(key), str) and vcs[key]
        for key in ("generated_ip_simulation_sources", "xpm_library", "unisims_library", "global_module")
    ):
        errors.append("FPGA IP simulation closure lacks a complete VCS source requirement")
    return {"status": "pass" if not errors else "fail", "errors": errors, "closure": payload}


def check_fpga_ip_generation_contract(path: Path) -> dict[str, Any]:
    """Require every generated PE multiplier IP to be explicitly DSP-backed."""

    errors: list[str] = []
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        return {"status": "fail", "errors": [f"cannot read FPGA IP generator: {exc}"]}
    if "CONFIG.Operation_Type {Multiply}" not in source:
        errors.append("FPGA IP generator does not define a floating-point multiplier")
    if DSP_MULTIPLIER_IP_MARKER not in source:
        errors.append(
            "FPGA IP generator does not require Full_Usage DSP mapping for fp_mul_sp_* PE multipliers"
        )
    return {
        "schema_version": "spatialaccagent.fpga_ip_generation_contract.v1",
        "status": "pass" if not errors else "fail",
        "required_multiplier_config": DSP_MULTIPLIER_IP_MARKER,
        "errors": errors,
    }


def _source_paths(template_dir: Path, sources: Iterable[str] | None) -> list[Path]:
    # All templates live in one Scala package and block wrappers instantiate
    # sibling operators. Checking a caller-provided subset would allow a stale
    # HardFloat/Queue implementation to escape Stage 2 simply because it was
    # not named in one metadata record.
    del sources
    return sorted(template_dir.glob("*.scala"))


def check_fpga_ip_template_contract(
    template_dir: Path,
    sources: Iterable[str] | None = None,
) -> dict[str, Any]:
    paths = _source_paths(template_dir, sources)
    errors: list[str] = []
    violations: list[dict[str, Any]] = []
    physical = template_dir / "PhysicalResources.scala"

    if not paths:
        errors.append(f"no Scala template sources found in {template_dir}")
    if not physical.is_file():
        errors.append("PhysicalResources.scala is missing")
        physical_text = ""
    else:
        physical_text = physical.read_text(encoding="utf-8", errors="ignore")

    missing_markers = [marker for marker in REQUIRED_PHYSICAL_MARKERS if marker not in physical_text]
    if missing_markers:
        errors.append(f"physical FPGA IP abstraction is missing markers: {missing_markers}")

    for path in paths:
        if not path.is_file():
            errors.append(f"template source is missing: {path.name}")
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for kind, pattern in FORBIDDEN_SOURCE_PATTERNS.items():
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                violations.append(
                    {"kind": kind, "source": path.name, "line": line, "token": match.group(0)}
                )

    if violations:
        errors.append(
            f"template closure contains {len(violations)} non-FPGA arithmetic/memory implementation(s)"
        )

    return {
        "schema_version": "spatialaccagent.fpga_ip_contract.v1",
        "status": "pass" if not errors else "fail",
        "checked_sources": [path.name for path in paths],
        "physical_resource_source": str(physical),
        "required_bindings": {
            "arithmetic": "Vivado floating_point/DSP IP",
            "weights": "XPM URAM",
            "activations": "XPM BRAM",
            "fifo": "XPM BRAM",
            "large_cache": "XPM URAM",
        },
        "simulation": simulation_source_contract(),
        "violations": violations,
        "errors": errors,
    }
