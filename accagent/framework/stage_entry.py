"""Shared entrypoint helper for SACG-stage tools."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Callable


StageFn = Callable[[argparse.Namespace], tuple[Path, dict]]


def run_sacg_stage(description: str, stage_fn: StageFn, argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--sacg-state", type=Path, required=True)
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    try:
        report_path, report = stage_fn(args)
        if report["errors"]:
            for error in report["errors"]:
                print(f"error: {error}", file=sys.stderr)
            print(report_path)
            return 1
        print(report_path)
        return 0
    except (OSError, ValueError, json.JSONDecodeError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
