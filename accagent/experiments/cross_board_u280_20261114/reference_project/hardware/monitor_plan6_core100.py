import json
import shlex
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


PROJECT_DIR = "/home/hyyuan/workspace/rtwsr_plan6_huginn_vu9p_shell_20261026_attn_pipeline"
SOURCE_REPORT_DIR = PROJECT_DIR + "/plan6_reports_attn_pipeline_full"
QKV_REPORT_DIR = "/home/hyyuan/workspace/rtwsr_plan6_qkv_pipeline_20261026/reports"
CORE_END_MARKER = PROJECT_DIR + "/app_shell_9p.runs/app_shell_9p_rtwsr_9p_axi_0_6_synth_1/.vivado.end.rst"
MANIFEST_SHA256 = "a186091fb9d5a2ce1a1a7454ea0fafb887cf51c8935cf52ae44e5bb52a1d878c"
LOCAL_DIR = Path(__file__).resolve().parents[1] / "results/plan6/attention_pipeline_full"
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "hyyuan@10.12.133.23"]


def record(state, **fields):
    data = {"time_utc": datetime.now(timezone.utc).isoformat(), "state": state,
            "project_dir": PROJECT_DIR, "input_manifest_sha256": MANIFEST_SHA256,
            "target_core_clock_mhz": 100, **fields}
    pending = LOCAL_DIR / "core100_progress.json.pending"
    pending.write_text(json.dumps(data, indent=2) + "\n")
    pending.replace(LOCAL_DIR / "core100_progress.json")
    print(json.dumps(data), flush=True)


def main():
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    while True:
        status_text = subprocess.check_output(
            SSH + ["cat " + shlex.quote(SOURCE_REPORT_DIR + "/huginn_vu9p_shell_status.txt")],
            text=True, timeout=45,
        )
        status = dict(line.split(" ", 1) for line in status_text.splitlines() if " " in line)
        qkv_status_text = subprocess.check_output(
            SSH + ["cat " + shlex.quote(QKV_REPORT_DIR + "/status.txt")],
            text=True, timeout=45,
        )
        qkv_status = dict(line.split(" ", 1) for line in qkv_status_text.splitlines() if " " in line)
        if status.get("INPUT_MANIFEST_SHA256") != MANIFEST_SHA256:
            raise RuntimeError("The source synthesis manifest changed")
        state = status.get("STATE", "UNKNOWN")
        if state in {"FAILED", "STOPPED_OOC_RESOURCE_LIMIT", "STOPPED_SHELL_RESOURCE_LIMIT"}:
            record("SOURCE_FLOW_STOPPED", source_status=status)
            return
        if qkv_status.get("STATE") == "FAILED":
            record("QKV_FLOW_STOPPED", qkv_status=qkv_status)
            return
        checkpoint_ready = subprocess.run(
            SSH + ["test -f " + shlex.quote(CORE_END_MARKER)],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=45,
        ).returncode == 0
        if checkpoint_ready and qkv_status.get("STATE") == "REPORTS_COMPLETE":
            break
        record("WAITING_SYNTHESIS_INPUTS", source_state=state,
               core_checkpoint_ready=checkpoint_ready, qkv_state=qkv_status.get("STATE"))
        time.sleep(60)

    record("CORE100_IMPLEMENTATION_RUNNING")
    command = ("cd " + shlex.quote(PROJECT_DIR) + " && "
               "/home/EDA/Xilinx/Vivado/2021.1/bin/vivado -mode batch "
               "-source run_plan6_core100_impl.tcl -log core100.vivado.log "
               "-journal core100.vivado.jou > core100_run.log 2>&1")
    result = subprocess.run(SSH + [command])
    subprocess.run(
        ["rsync", "-a", "--include=*.rpt", "--include=*.txt", "--include=*.sha256",
         "--include=*.xdc", "--exclude=*", "hyyuan@10.12.133.23:" + PROJECT_DIR +
         "/plan6_reports_attn_qkv_100mhz/", str(LOCAL_DIR / "core100") + "/"],
        check=True, timeout=180,
    )
    record("CORE100_FLOW_RETURNED", returncode=result.returncode)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        record("MONITOR_STOPPED", operation_result=str(error))
        raise
