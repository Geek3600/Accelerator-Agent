#!/usr/bin/env python3
"""Build a contract-guided failure-localization artifact from boundary traces."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from accagent.framework.debug_closure import (
    build_boundary_contracts,
    load_trace_records,
    localize_failure,
)
from accagent.framework.sacg_utils import read_json, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Contract-guided failure localization")
    parser.add_argument("--sacg-state", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--verification-result", type=Path)
    parser.add_argument("--trace", action="append", default=[], type=Path)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    state = read_json(args.sacg_state)
    verification = read_json(args.verification_result) if args.verification_result and args.verification_result.exists() else {}
    contracts = build_boundary_contracts(state, args.run_dir)
    records = load_trace_records(args.trace)
    result = localize_failure(contracts, verification, records)
    result["boundary_contract_count"] = len(contracts.get("boundaries", []))
    result["trace_record_count"] = len(records)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.out, result)
    print(f"{result['status']}: root={result.get('root_candidate_module')} contract={result.get('violated_contract')}")
    return 0 if result["status"] in {"localized", "no_failure"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
