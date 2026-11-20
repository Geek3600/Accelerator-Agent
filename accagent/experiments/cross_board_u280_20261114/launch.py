"""Start or resume the isolated cross-board experiment with the normal agent."""

from __future__ import annotations

import datetime
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT = Path(__file__).resolve().parent
DESIGN = "gpt2_medium_seq32_u280_gpt61_20261114"
RUN = ROOT / "accagent/runs" / DESIGN
MODEL_DIR = Path(
    "/home/remote/.cache/huggingface/hub/models--openai-community--gpt2-medium/"
    "snapshots/6dcaa7a952f72f9298047fd5137cd6e4f05f41da"
)


def main() -> None:
    sys.path.insert(0, str(ROOT))
    from accagent.framework.llm_config import resolve_llm_cfg

    cfg = resolve_llm_cfg()
    baseline = json.loads(
        (ROOT / "accagent/runs/gpt2_medium_seq32_gpt61_20261027/agent/agent_run_report.json")
        .read_text()
    )["llm"]
    if cfg.model != "gpt-6.1-sol" or cfg.endpoint != baseline["endpoint"]:
        raise SystemExit("Upstream must match the frozen GPT-6.1-Sol baseline route.")
    if not cfg.api_key or cfg.configuration_error:
        raise SystemExit("The existing upstream credentials/configuration are unavailable.")
    if not (MODEL_DIR / "config.json").is_file():
        raise SystemExit("The shared GPT-2 Medium checkpoint is unavailable.")

    manifest_path = EXPERIMENT / "launch.json"
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text())
        cmdline = Path(f"/proc/{previous.get('pid')}/cmdline")
        if cmdline.exists() and DESIGN.encode() in cmdline.read_bytes():
            print(json.dumps({"status": "already_running", "pid": previous["pid"]}))
            return

    RUN.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.update({
        "SPATIALACC_LLM_MODEL": "gpt-6.1-sol",
        "SPATIALACC_LLM_ENDPOINT": cfg.endpoint,
        "SPATIALACC_LLM_BASE_URL": cfg.base_url,
        "SPATIALACC_LLM_API_KEY": cfg.api_key,
        "SPATIALACC_LLM_WIRE_API": "responses",
        "SPATIALACC_LLM_FALLBACK_ENDPOINT": "",
        "SPATIALACC_LLM_FALLBACK_BASE_URL": "",
        "SPATIALACC_LLM_FALLBACK_API_KEY": "",
        "SPATIALACC_LLM_TRANSIENT_RETRY_UNBOUNDED": "1",
        "SPATIALACC_ACCORD_PROFILE": "ACCORD",
        "SPATIALACC_VERIFICATION_POLICY": "vcs_compile_only",
        "SPATIALACC_CLOCK_TARGET_MHZ": "150",
        "SPATIALACC_APP_SHELL_MODE": "synth",
        "SPATIALACC_RUN_BOARD_TOOLS": "0",
        "SPATIALACC_DEBUG_LOOP_SLOTS": "1",
        "SPATIALACC_DEBUG_LOOP_MAX_RSS_MB": "6144",
        "SPATIALACC_DEBUG_LOOP_MAX_VMSIZE_MB": "6144",
        "SPATIALACC_SBT_HEAP_MB": "2048",
    })
    request = RUN / "backend_board/optimization_request.json"
    if not request.exists():
        request.parent.mkdir(parents=True, exist_ok=True)
        request.write_text(json.dumps({
            "scope": "existing_design_timing",
            "clock_frequency_mhz": 150.0,
            "stop_at_clock_target": True,
            "source": "user_cross_board_experiment",
        }, indent=2) + "\n")

    command = [
        sys.executable, "-u", "-m", "accagent.framework.agent",
        "--run-dir", str(RUN), "--design", DESIGN,
        "--task-spec", str(EXPERIMENT / "task_spec.md"),
        "--model-source", str(EXPERIMENT / "model_config.json"),
        "--model-dir", str(MODEL_DIR),
        "--board-materials-dir", str(EXPERIMENT / "board_materials"),
        "--quantization-materials-dir", str(ROOT / "accagent/framework/input_materials/quantization"),
        "--tool-materials-dir", str(ROOT / "accagent/framework/input_materials/tools"),
        "--tool-timeout-sec", "7200",
    ]
    log_path = RUN / "agent_u280.log"
    with log_path.open("ab", buffering=0) as log:
        process = subprocess.Popen(
            command, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
        )
    manifest = {
        "started_at": datetime.datetime.now().astimezone().isoformat(),
        "pid": process.pid,
        "status": "started",
        "run_dir": str(RUN), "log": str(log_path), "command": command,
        "upstream": {"model": cfg.model, "endpoint": cfg.endpoint, "wire_api": "responses"},
        "verification_policy": "vcs_compile_only", "timing_target_mhz": 150,
        "memory_guard_rss_mb": 6144, "memory_guard_vmsize_mb": 6144,
        "shared_model_dir": str(MODEL_DIR),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
