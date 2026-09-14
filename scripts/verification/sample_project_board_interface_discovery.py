#!/usr/bin/env python3
"""Discover the exact board wrapper from the current user sample project."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.verification.sample_project_board_interface_impl import (
    IDENTITY_SCHEMA_VERSION,
    build_report,
    resume_existing_board_domain_repair,
    write_validated_identity,
)
from accagent.framework.active_board_job import pending_exact_board_job


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument(
        "--remote-timeout-sec",
        type=int,
        default=0,
        help="Outer transport/tool timeout; 0 waits indefinitely during development",
    )
    parser.add_argument(
        "--resume-domain-repair-only",
        action="store_true",
        help="Resume checker-driven domain repair from the current hash-validated discovery artifacts",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    run_dir = args.run_dir.resolve()
    out_dir = run_dir / "verification" / "board_interface"
    out = (args.out or out_dir / "board_source_identity.json").resolve()
    if not args.resume_domain_repair_only and pending_exact_board_job(run_dir):
        # The VCS contract has already sealed the exact board inputs.  Discovery
        # must not rewrite them while the real simulation still needs collection.
        print(out)
        return 0
    try:
        if args.resume_domain_repair_only:
            report = resume_existing_board_domain_repair(
                run_dir, out_dir, args.remote_timeout_sec
            )
        else:
            report = build_report(run_dir, out_dir, args.remote_timeout_sec)
    except Exception as exc:
        report = {
            "schema_version": IDENTITY_SCHEMA_VERSION,
            "status": "fail",
            "run_dir": str(run_dir),
            "blockers": [str(exc)],
            "policy": {
                "vivado_or_llm_unavailable_fails_closed": True,
                "no_regex_or_filename_guess_fallback": True,
            },
        }
    report = write_validated_identity(out, report)
    print(out)
    return 0 if report.get("status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
