#!/usr/bin/env python3
import argparse
from pathlib import Path


MAX_PASSWORD_LEN = 20


def password_to_exact_mask(password: str, line_no: int) -> str:
    if not password:
        raise ValueError(f"line {line_no}: empty password")
    try:
        password.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(f"line {line_no}: non-ASCII password {password!r}") from exc
    if len(password) > MAX_PASSWORD_LEN:
        raise ValueError(
            f"line {line_no}: password length {len(password)} exceeds Office2010 mask limit {MAX_PASSWORD_LEN}"
        )
    if any(ch in "\r\n\0" for ch in password):
        raise ValueError(f"line {line_no}: unsupported control character in password")
    return "".join(f"#{ch}" for ch in password)


def extract_password(line: str, line_no: int) -> str:
    line = line.rstrip("\n")
    if line.endswith("\r"):
        line = line[:-1]
    if not line:
        return ""
    if "\t" in line:
        return line.rsplit("\t", 1)[1]
    return line


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert PYJM pattern<TAB>password output into Office2010 exact hcmask lines."
    )
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()

    input_path = Path(args.input_file)
    output_path = Path(args.output_file)

    masks: list[str] = []
    skipped = 0

    with input_path.open("r", encoding="utf-8") as src:
        for line_no, line in enumerate(src, 1):
            password = extract_password(line, line_no)
            if not password:
                skipped += 1
                continue
            mask = password_to_exact_mask(password, line_no)
            masks.append(mask)

    if not masks:
        raise RuntimeError(f"no valid passwords converted from {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(masks) + "\n", encoding="utf-8")

    print(f"[Done] input_file = {input_path}")
    print(f"[Done] output_file = {output_path}")
    print(f"[Done] masks_written = {len(masks)}")
    print(f"[Stats] skipped = {skipped}")


if __name__ == "__main__":
    main()
