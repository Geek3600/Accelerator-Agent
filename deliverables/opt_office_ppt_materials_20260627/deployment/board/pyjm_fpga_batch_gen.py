#!/usr/bin/env python3
import argparse
import os
import random
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import List, Tuple


DEFAULT_PATTERNS = "/home/hyyuan/pyjm12_demo/patterns.txt"
DEFAULT_OUTPUT = "/home/hyyuan/pyjm12_demo/10^4_fpga.txt"
DEFAULT_TOOL = "/tmp/pyjm_fpga_demo"
DEFAULT_DDR_IMAGE = "/home/hyyuan/pyjm12_demo/ddr_image.u32.bin"


@dataclass
class PatternRow:
    pattern: str
    ratio: float
    pw_num: int = 0


def read_patterns_and_allocate(path: str, total: int) -> List[PatternRow]:
    rows: List[PatternRow] = []
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.rstrip("\n")
            if not line.strip():
                continue
            fields = line.split("\t")
            if len(fields) < 2:
                raise ValueError(f"bad patterns line {line_no}: {line!r}")
            ratio = float(fields[1])
            if ratio > 0:
                rows.append(PatternRow(fields[0].strip(), ratio))

    for row in rows:
        row.pw_num = int(row.ratio * total)

    diff = total - sum(row.pw_num for row in rows)
    if diff > 0:
        for i in sorted(range(len(rows)), key=lambda i: rows[i].ratio, reverse=True)[:diff]:
            rows[i].pw_num += 1
    elif diff < 0:
        for i in sorted(range(len(rows)), key=lambda i: rows[i].pw_num, reverse=True)[:abs(diff)]:
            rows[i].pw_num -= 1

    if sum(row.pw_num for row in rows) != total:
        raise RuntimeError("allocated password count does not match total_generate")
    return rows


def parse_simple_pattern(pattern: str) -> List[Tuple[str, int]]:
    return [(kind, int(count)) for kind, count in re.findall(r"([A-Za-z])(\d+)", pattern)]


def match_simple_pattern(password: str, pattern: str) -> bool:
    parts = parse_simple_pattern(pattern)
    if not parts:
        return True
    if len(password) != sum(count for _, count in parts):
        return False

    pos = 0
    for kind, count in parts:
        seg = password[pos:pos + count]
        pos += count
        if kind == "L" and not all(ch.isalpha() for ch in seg):
            return False
        if kind == "N" and not all(ch.isdigit() for ch in seg):
            return False
        if kind == "S" and not all((not ch.isalnum()) and (not ch.isspace()) for ch in seg):
            return False
        if kind == "U" and not all(ch.isupper() for ch in seg):
            return False
        if kind == "l" and not all(ch.islower() for ch in seg):
            return False
    return True


def pattern_len(pattern: str) -> int:
    parts = parse_simple_pattern(pattern)
    return sum(count for _, count in parts) if parts else 0


def parse_password(stdout: str) -> str:
    for line in stdout.splitlines():
        if line.startswith("password_value="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("missing password_value in FPGA tool output")


def fpga_generate(args: argparse.Namespace, pattern: str, nonce: int) -> str:
    cmd = [
        args.fpga_tool,
        "--runs", "1",
        "--poll-timeout-ms", str(args.poll_timeout_ms),
        "--write-ddr-mode", "0",
        "--pattern", pattern,
        "--password-len", str(pattern_len(pattern)),
        "--raw-output-bytes", "1024",
        "--nonce", str(nonce),
        "--no-password-record",
    ]

    env = os.environ.copy()
    env["XDMA_ID"] = args.xdma_id
    env["DDR_IMAGE"] = args.ddr_image
    env["PATTERN"] = pattern

    input_text = None
    if os.geteuid() != 0:
        sudo_cmd = ["sudo"]
        sudo_password = os.environ.get("PYJM_SUDO_PASSWORD")
        if sudo_password is not None:
            sudo_cmd += ["-S", "-p", ""]
            input_text = sudo_password + "\n"
        cmd = sudo_cmd + ["env", f"XDMA_ID={args.xdma_id}", f"DDR_IMAGE={args.ddr_image}", f"PATTERN={pattern}"] + cmd

    proc = subprocess.run(cmd, env=env, input=input_text, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        raise RuntimeError(f"FPGA tool failed with exit code {proc.returncode}")
    return parse_password(proc.stdout)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--patterns-file", default=DEFAULT_PATTERNS)
    parser.add_argument("--output-file", default=DEFAULT_OUTPUT)
    parser.add_argument("--total-generate", type=int, default=10000)
    parser.add_argument("--max-retry-factor", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--validate-simple-pattern", action="store_true")
    parser.add_argument("--fpga-tool", default=DEFAULT_TOOL)
    parser.add_argument("--xdma-id", default="7")
    parser.add_argument("--ddr-image", default=DEFAULT_DDR_IMAGE)
    parser.add_argument("--poll-timeout-ms", type=int, default=5000)
    args = parser.parse_args()

    random.seed(args.seed)
    rows = read_patterns_and_allocate(args.patterns_file, args.total_generate)
    os.makedirs(os.path.dirname(args.output_file), exist_ok=True)

    total_written = 0
    empty_count = 0
    mismatch_count = 0
    incomplete_patterns = 0

    with open(args.output_file, "w", encoding="utf-8") as out:
        for row in rows:
            if row.pw_num <= 0:
                continue

            written = 0
            attempts = 0
            max_attempts = max(row.pw_num * args.max_retry_factor, 20)
            while written < row.pw_num and attempts < max_attempts:
                attempts += 1
                pwd = fpga_generate(args, row.pattern, random.getrandbits(32))

                if pwd == "":
                    empty_count += 1
                    continue
                if args.validate_simple_pattern and not match_simple_pattern(pwd, row.pattern):
                    mismatch_count += 1
                    continue

                out.write(f"{row.pattern}\t{pwd}\n")
                total_written += 1
                written += 1

            if written < row.pw_num:
                incomplete_patterns += 1
                print(f"[Warn] pattern={row.pattern} target={row.pw_num} written={written} attempts={attempts}")

    print(f"[Done] output_file = {args.output_file}")
    print(f"[Done] total_written = {total_written}")
    print(f"[Stats] empty_count = {empty_count}")
    print(f"[Stats] mismatch_count = {mismatch_count}")
    print(f"[Stats] incomplete_patterns = {incomplete_patterns}")


if __name__ == "__main__":
    main()
