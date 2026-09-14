#!/usr/bin/env python3
import argparse
import fcntl
import json
import os
import socket
import tempfile
from pathlib import Path
from typing import Any, Dict, List


APP_STATUS_KEYS = [
    "card_id",
    "worker_ip",
    "application",
    "task",
    "performence",
    "performence_unit",
]


def detect_worker_ip() -> str:
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = info[4][0]
            if not ip.startswith("127."):
                return ip
    except OSError:
        pass
    return ""


def default_status(worker_ip: str) -> Dict[str, Any]:
    return {
        "status": [
            {
                "card_id": card_id,
                "worker_ip": worker_ip,
                "application": "idle",
                "task": "",
                "performence": None,
                "performence_unit": None,
            }
            for card_id in range(8)
        ]
    }


def load_status(path: Path, worker_ip: str) -> Dict[str, Any]:
    if path.exists() and path.stat().st_size > 0:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = default_status(worker_ip)

    if not isinstance(data, dict) or not isinstance(data.get("status"), list):
        raise ValueError(f"bad status json schema: {path}")
    return data


def find_or_create_entry(data: Dict[str, Any], card_id: int, worker_ip: str) -> Dict[str, Any]:
    entries: List[Dict[str, Any]] = data["status"]
    for entry in entries:
        if isinstance(entry, dict) and entry.get("card_id") == card_id:
            return entry

    entry = {
        "card_id": card_id,
        "worker_ip": worker_ip,
        "application": "idle",
        "task": "",
        "performence": None,
        "performence_unit": None,
    }
    entries.append(entry)
    return entry


def write_status(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp_path, 0o644)
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def read_counter(path: Path) -> int:
    if not path.exists() or path.stat().st_size == 0:
        return 0
    text = path.read_text(encoding="utf-8").strip()
    return int(text) if text else 0


def write_counter(path: Path, value: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{value}\n", encoding="utf-8")
    try:
        os.chmod(path, 0o666)
    except PermissionError:
        pass


def update_status(args: argparse.Namespace) -> str:
    json_path = Path(args.json_file)
    lock_path = Path(args.lock_file)
    counter_path = Path(args.counter_file)
    worker_ip = args.worker_ip or ""

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)

        data = load_status(json_path, worker_ip)
        entry = find_or_create_entry(data, args.card_id, worker_ip)
        if not worker_ip:
            worker_ip = str(entry.get("worker_ip") or detect_worker_ip())

        if args.mode == "start":
            counter = read_counter(counter_path) + 1
            write_counter(counter_path, counter)
            task = f"task-10-{counter}"
            application = args.application
        elif args.mode == "running":
            task = args.task
            application = args.application
        elif args.mode == "finish":
            task = ""
            application = "idle"
        else:
            raise ValueError(f"unknown mode: {args.mode}")

        # Only update values for the fixed frontend keys. Do not remove or rename keys.
        if "card_id" in entry:
            entry["card_id"] = args.card_id
        if "worker_ip" in entry:
            entry["worker_ip"] = worker_ip
        if "application" in entry:
            entry["application"] = application
        if "task" in entry:
            entry["task"] = task
        if "performence" in entry:
            entry["performence"] = None
        if "performence_unit" in entry:
            entry["performence_unit"] = None

        # If the entry was created because the card was absent, keep the exact expected keys.
        for key in APP_STATUS_KEYS:
            entry.setdefault(key, None)
        if entry["application"] is None:
            entry["application"] = application
        if entry["task"] is None:
            entry["task"] = task

        write_status(json_path, data)
        fcntl.flock(lock, fcntl.LOCK_UN)

    return task


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["start", "running", "finish"])
    parser.add_argument("--card-id", type=int, required=True)
    parser.add_argument("--task", default="")
    parser.add_argument("--application", default="应用2-4")
    parser.add_argument("--json-file", default="/home/share/app_status.json")
    parser.add_argument("--lock-file", default="/home/share/.app_status.lock")
    parser.add_argument("--counter-file", default="/home/share/.app_status_task_counter_10.txt")
    parser.add_argument("--worker-ip", default="")
    args = parser.parse_args()

    task = update_status(args)
    if args.mode == "start":
        print(task)


if __name__ == "__main__":
    main()
