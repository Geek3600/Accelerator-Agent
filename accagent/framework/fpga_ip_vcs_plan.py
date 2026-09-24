#!/usr/bin/env python3
"""Materialize a VCS-MX compilation plan from Vivado export_simulation data."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shlex
from pathlib import Path
from typing import Any


LIBRARY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
MODULE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
LANGUAGES = {"vhdl", "verilog", "systemverilog"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_relative_workdir(value: str) -> Path:
    path = Path(value)
    if not value or path.is_absolute() or any(part in {".", ".."} for part in path.parts):
        if value != ".":
            raise ValueError(f"compiler workdir is not a safe relative path: {value}")
    return Path(".") if value == "." else path


def resolved_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def modules_from_manifest(path: Path) -> list[str]:
    if not path.is_file():
        raise ValueError(f"FPGA IP module manifest is missing: {path}")
    modules = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not modules or len(modules) != len(set(modules)):
        raise ValueError("FPGA IP module manifest is empty or contains duplicates")
    invalid = [module for module in modules if not MODULE_RE.fullmatch(module)]
    if invalid:
        raise ValueError(f"FPGA IP module manifest contains unsafe names: {invalid}")
    return modules


def parse_file_info(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8", newline="") as stream:
        for line_number, fields in enumerate(csv.reader(stream), start=1):
            if not fields:
                continue
            if len(fields) == 5 and not fields[-1]:
                fields = fields[:-1]
            if len(fields) != 4:
                raise ValueError(f"{path}:{line_number} is not a four-column Vivado file_info row")
            filename, language, library, source = (value.strip() for value in fields)
            normalized_language = language.lower()
            if (
                not filename
                or normalized_language not in LANGUAGES
                or not LIBRARY_RE.fullmatch(library)
                or not source
            ):
                raise ValueError(f"{path}:{line_number} contains an invalid Vivado file_info row")
            source_path = Path(source)
            if not source_path.is_absolute() or source_path.name != filename or not source_path.is_file():
                raise ValueError(f"{path}:{line_number} references an unavailable simulation source: {source}")
            rows.append(
                {
                    "filename": filename,
                    "language": normalized_language,
                    "library": library,
                    "source": str(source_path.resolve()),
                }
            )
    if not rows:
        raise ValueError(f"Vivado file_info is empty: {path}")
    return rows


def default_library_for_module(module: str, rows: list[dict[str, str]], ip_root: Path) -> str:
    expected = (ip_root / module / "sim" / f"{module}.v").resolve()
    matches = [row["library"] for row in rows if Path(row["source"]).resolve() == expected]
    if len(matches) != 1:
        raise ValueError(f"Vivado file_info does not identify exactly one simulation wrapper for {module}")
    return matches[0]


def setup_lines(
    stage_root: Path,
    workdir: Path,
    libraries: list[str],
    library_root: Path,
) -> list[str]:
    return [
        f"{library}:{os.path.relpath(stage_root / library_root / library, start=stage_root / workdir).replace(os.sep, '/')}"
        for library in libraries
    ]


def merge_setup(path: Path, dynamic_lines: list[str], stage_root: Path, workdir: Path) -> None:
    existing = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    dynamic_by_library = {
        line.split(":", 1)[0]: line.split(":", 1)[1]
        for line in dynamic_lines
    }
    retained: list[str] = []
    present: set[str] = set()
    for line in existing:
        if ":" not in line or line.startswith("OTHERS="):
            retained.append(line)
            continue
        library, location = line.split(":", 1)
        expected = dynamic_by_library.get(library)
        if expected is None:
            retained.append(line)
            continue
        current_path = (path.parent / location).resolve()
        expected_path = (path.parent / expected).resolve()
        if current_path != expected_path:
            raise ValueError(
                f"existing synopsys_sim.setup maps {library} to a conflicting directory: {path}"
            )
        retained.append(line)
        present.add(library)
    missing = [line for line in dynamic_lines if line.split(":", 1)[0] not in present]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([*missing, *retained]) + "\n", encoding="utf-8")


def build(args: argparse.Namespace) -> dict[str, Any]:
    stage_root = Path.cwd().resolve()
    module_manifest = Path(args.module_manifest).resolve()
    ip_root = Path(args.ip_root).resolve()
    export_root = Path(args.export_root).resolve()
    library_root = Path(args.library_root)
    if library_root.is_absolute() or ".." in library_root.parts:
        raise ValueError("library root must be a safe relative path")
    modules = modules_from_manifest(module_manifest)
    records: list[dict[str, str]] = []
    defaults: list[str] = []
    seen: dict[tuple[str, str], dict[str, str]] = {}
    libraries: list[str] = []
    for module in modules:
        info = export_root / module / "vcs" / "file_info.txt"
        rows = parse_file_info(info)
        defaults.append(default_library_for_module(module, rows, ip_root))
        for row in rows:
            source = Path(row["source"])
            if not (resolved_under(source, ip_root) or resolved_under(source, export_root)):
                raise ValueError(f"Vivado file_info source is outside the generated/exported IP closure: {source}")
            key = (row["library"], row["filename"])
            digest = sha256_file(source)
            previous = seen.get(key)
            if previous is not None:
                if previous["sha256"] != digest or previous["language"] != row["language"]:
                    raise ValueError(
                        "Vivado file_info has conflicting content for logical library/basename: "
                        + f"{row['library']}/{row['filename']}"
                    )
                continue
            record = {**row, "sha256": digest, "module": module}
            seen[key] = record
            records.append(record)
            if row["library"] not in libraries:
                libraries.append(row["library"])
    if len(set(defaults)) != 1:
        raise ValueError("Vivado IP wrappers do not agree on one default simulation library")
    default_library = defaults[0]
    glbl_rows = [
        row
        for row in records
        if row["library"] == default_library and row["filename"] == "glbl.v"
    ]
    if len(glbl_rows) != 1:
        raise ValueError("Vivado IP export does not provide exactly one default-library glbl.v")

    for library in libraries:
        (stage_root / library_root / library).mkdir(parents=True, exist_ok=True)
    workdirs = [safe_relative_workdir(value) for value in args.compiler_workdir]
    if not workdirs:
        workdirs = [Path(".")]
    if len({path.as_posix() for path in workdirs}) != len(workdirs):
        raise ValueError("compiler workdirs contain duplicates")
    for workdir in workdirs:
        merge_setup(
            stage_root / workdir / "synopsys_sim.setup",
            setup_lines(stage_root, workdir, libraries, library_root),
            stage_root,
            workdir,
        )

    if args.expected_default_library and args.expected_default_library != default_library:
        raise ValueError(
            "generated DUT work library differs from Vivado IP default library: "
            + f"expected {args.expected_default_library}, got {default_library}"
        )
    compile_script = stage_root / "fpga_ip" / "compile_ip_models.sh"
    compile_lines = ["#!/usr/bin/env bash", "set -euo pipefail"]
    for row in records:
        if row["language"] == "vhdl":
            command = ["vhdlan", "-full64", "-work", row["library"], row["source"]]
        elif row["language"] == "verilog":
            command = ["vlogan", "-full64", "-work", row["library"], "+v2k", row["source"]]
        else:
            command = ["vlogan", "-full64", "-sverilog", "-work", row["library"], row["source"]]
        compile_lines.append(shlex.join(command))
    compile_script.write_text("\n".join(compile_lines) + "\n", encoding="utf-8")
    compile_script.chmod(0o755)

    runtime_env = stage_root / "fpga_ip" / "vcs_runtime.env"
    runtime_env.write_text(
        "\n".join(
            [
                f"FPGA_IP_DEFAULT_LIBRARY={shlex.quote(default_library)}",
                f"FPGA_IP_GLBL_UNIT={shlex.quote(default_library + '.glbl')}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    elab_args = stage_root / "fpga_ip" / "vcs_elab_args.txt"
    elab_args.write_text(
        "\n".join(value for library in libraries for value in ("-L", library)) + "\n",
        encoding="utf-8",
    )
    plan = {
        "schema_version": "spatialaccagent.vivado_vcs_library_plan.v1",
        "modules": modules,
        "default_library": default_library,
        "glbl_unit": default_library + ".glbl",
        "libraries": libraries,
        "compiler_workdirs": [path.as_posix() for path in workdirs],
        "records": records,
    }
    (stage_root / "fpga_ip" / "vcs_library_plan.json").write_text(
        json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return plan


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module-manifest", required=True)
    parser.add_argument("--ip-root", required=True)
    parser.add_argument("--export-root", required=True)
    parser.add_argument("--library-root", required=True)
    parser.add_argument("--compiler-workdir", action="append", default=[])
    parser.add_argument("--expected-default-library", default="")
    args = parser.parse_args()
    try:
        plan = build(args)
    except (OSError, ValueError, csv.Error) as exc:
        print(f"SPATIALACC_VIVADO_VCS_LIBRARY_PLAN_FAIL {exc}")
        return 1
    print(
        "SPATIALACC_VIVADO_VCS_LIBRARY_PLAN_PASS "
        + f"libraries={len(plan['libraries'])} sources={len(plan['records'])} "
        + f"default_library={plan['default_library']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
