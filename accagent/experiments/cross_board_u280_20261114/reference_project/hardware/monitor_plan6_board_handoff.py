import hashlib
import json
import re
import shlex
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


PROJECT_DIR = "/home/hyyuan/workspace/rtwsr_plan6_huginn_vu9p_direct_20261026"
REPORT_DIR = PROJECT_DIR + "/plan6_reports_attn_qkv_100mhz"
MANIFEST_SHA256 = "899bbb48b2393cef695f15c2b0e16265254316926e928e73a8b801872c2a8558"
RUNNER_SHA256 = "725b5ae5baf9f1f0820200b742b36f6d4e8555fef3476f03b61b6db2bc598178"
PAYLOAD_HASHES = {
    "adapter.usw512": "452e73e87166a901e64f9295145b2c5e8dcfa5fdc79bff2db1e8b1369f4c8d7c",
    "weights.usw512": "09ea390353cbc5e8d06fb4e945173a664d3660aa6b3b883cd098c5a80e142b9a",
    "adapter_gamma.fp16": "8b3a37d3404889e946a1ce02669d54ffd86fcb2c2bde48e1035876d542380407",
    "gamma.fp16": "7de91cd6a922ec7150efc87696e1f18f77939de4867be1fdbc3511cba0ed7aa1",
}
BOARD_DIR = "/root/fpga/plan6_huginn"
SOURCE_MANIFEST_PATH = PROJECT_DIR + "/source_inputs.sha256"
DIRECT_LOCAL_DIR = Path(__file__).resolve().parents[1] / "results/plan6/attention_qkv_direct100"
SSI_REPORT_DIR = PROJECT_DIR + "/plan6_reports_attn_qkv_ssi_spread_100mhz"
SSI_LOCAL_DIR = Path(__file__).resolve().parents[1] / "results/plan6/attention_qkv_ssi_spread"
BALANCE_REPORT_DIR = PROJECT_DIR + "/plan6_reports_attn_qkv_ssi_balance_slls_100mhz"
BALANCE_LOCAL_DIR = Path(__file__).resolve().parents[1] / "results/plan6/attention_qkv_ssi_balance_slls"
LOCAL_DIR = SSI_LOCAL_DIR
IMPLEMENTATIONS = [
    (PROJECT_DIR, REPORT_DIR, MANIFEST_SHA256, SOURCE_MANIFEST_PATH, DIRECT_LOCAL_DIR),
    (PROJECT_DIR, SSI_REPORT_DIR, MANIFEST_SHA256, SOURCE_MANIFEST_PATH, SSI_LOCAL_DIR),
    (PROJECT_DIR, BALANCE_REPORT_DIR, MANIFEST_SHA256, SOURCE_MANIFEST_PATH, BALANCE_LOCAL_DIR),
]
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15"]
VIVADO = "/home/EDA/Xilinx/Vivado/2021.1/bin/vivado"
REPORT_HASHES = {
    "UTILIZATION_POSTROUTE_SHA256": "utilization_postroute.rpt",
    "HIERARCHY_POSTROUTE_SHA256": "utilization_hierarchical_postroute.rpt",
    "TIMING_POSTROUTE_SHA256": "timing_postroute.rpt",
    "CLOCKS_POSTROUTE_SHA256": "clocks_postroute.rpt",
    "ROUTE_STATUS_SHA256": "route_status_postroute.rpt",
    "DRC_SHA256": "drc_postroute.rpt",
    "POWER_SHA256": "power_postroute.rpt",
}


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def report_resource_count(report_text, resource_name):
    pattern = r"^\|\s*" + re.escape(resource_name) + r"\s*\|\s*(\d+)\s*\|"
    match = re.search(pattern, report_text, re.MULTILINE)
    if not match:
        raise RuntimeError("Post-Route report is missing resource row " + resource_name)
    return int(match.group(1))


def run_eda(command):
    return subprocess.check_output(SSH + ["hyyuan@10.12.133.23", command], text=True, timeout=120)


def run_timing_not_met_bitgen(project_dir, report_dir, manifest_sha256):
    tcl_name = "plan6_bitgen_after_timing_not_met_generic.tcl"
    tcl_path = report_dir + "/" + tcl_name
    log_path = report_dir + "/bitgen_after_timing_not_met.vivado.log"
    journal_path = report_dir + "/bitgen_after_timing_not_met.vivado.jou"
    subprocess.run(
        ["scp", "-q", str(Path(__file__).with_name(tcl_name)),
         "hyyuan@10.12.133.23:" + tcl_path], check=True, timeout=60,
    )
    command = (
        "cd " + shlex.quote(report_dir) + " && " + shlex.quote(VIVADO) +
        " -mode batch -source " + shlex.quote(tcl_path) +
        " -log " + shlex.quote(log_path) + " -journal " + shlex.quote(journal_path) +
        " -tclargs " + shlex.quote(project_dir) + " " + shlex.quote(report_dir) +
        " " + shlex.quote(manifest_sha256)
    )
    result = subprocess.run(SSH + ["hyyuan@10.12.133.23", command], timeout=3600)
    if result.returncode != 0:
        raise RuntimeError("Post-Route bitstream generation failed with exit code " +
                           str(result.returncode))
    status_path = shlex.quote(report_dir + "/huginn_vu9p_shell_status.txt")
    status_text = run_eda("cat " + status_path)
    if "STATE CORE_TIMING_NOT_MET_BITSTREAM_READY" not in status_text:
        raise RuntimeError("Bitstream generation completed without a ready status")


def board_command(command):
    nested_ssh = ("ssh -o BatchMode=yes -o ConnectTimeout=15 "
                  "-o StrictHostKeyChecking=yes -o UserKnownHostsFile=/tmp/plan6_known_hosts "
                  "root@10.12.131.149 ")
    return SSH + ["root@10.12.131.150", nested_ssh + shlex.quote(command)]


def record(state, **fields):
    data = {
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "state": state,
        "project_dir": PROJECT_DIR,
        "input_manifest_sha256": MANIFEST_SHA256,
        **fields,
    }
    pending = LOCAL_DIR / "handoff.json.pending"
    pending.write_text(json.dumps(data, indent=2) + "\n")
    pending.replace(LOCAL_DIR / "handoff.json")
    print(json.dumps(data), flush=True)


def main():
    global PROJECT_DIR, MANIFEST_SHA256, REPORT_DIR, SOURCE_MANIFEST_PATH, LOCAL_DIR
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    while True:
        states = []
        selected = None
        for implementation in IMPLEMENTATIONS:
            project_dir, report_dir, manifest_sha256, _, local_dir = implementation
            status_path = shlex.quote(report_dir + "/huginn_vu9p_shell_status.txt")
            status_text = run_eda("if [ -f " + status_path + " ]; then cat " + status_path + "; fi")
            status = dict(line.split(" ", 1) for line in status_text.splitlines() if " " in line)
            if status:
                assert status["PROJECT_DIR"] == project_dir
                assert status["INPUT_MANIFEST_SHA256"] == manifest_sha256
            states.append({"project_dir": project_dir, "report_dir": report_dir,
                           "state": status.get("STATE", "UNKNOWN")})
            if status.get("STATE") == "CORE_TIMING_NOT_MET":
                record("BITGEN_AFTER_TIMING_NOT_MET", project_dir=project_dir,
                       report_dir=report_dir,
                       input_manifest_sha256=manifest_sha256)
                run_timing_not_met_bitgen(project_dir, report_dir, manifest_sha256)
                status_text = run_eda("cat " + status_path)
                status = dict(line.split(" ", 1) for line in status_text.splitlines()
                              if " " in line)
                states[-1]["state"] = status.get("STATE", "UNKNOWN")
            if status.get("STATE") in {
                "CORE_100MHZ_ROUTED", "CORE_TIMING_NOT_MET_BITSTREAM_READY"
            }:
                selected = implementation
                break
        if selected:
            PROJECT_DIR, REPORT_DIR, MANIFEST_SHA256, SOURCE_MANIFEST_PATH, LOCAL_DIR = selected
            LOCAL_DIR.mkdir(parents=True, exist_ok=True)
            record("IMPLEMENTATION_SELECTED", selected_project_dir=PROJECT_DIR,
                   selected_report_dir=REPORT_DIR)
            break
        if all(item["state"] == "FAILED" for item in states):
            record("IMPLEMENTATION_FAILED", implementations=states)
            return
        record("WAITING_IMPLEMENTATION", implementations=states)
        time.sleep(60)

    assert status["PROJECT_DIR"] == PROJECT_DIR
    assert status["INPUT_MANIFEST_SHA256"] == MANIFEST_SHA256
    assert status["CNN_CORE_COUNT"] == "0"
    assert status["CORE_CLOCK_CONFIG_MHZ"] == "100"
    assert status["QKV_IMPLEMENTATION"] == "PIPELINED_BRAM"
    expected_placement = {
        SSI_REPORT_DIR: "SSI_SpreadSLLs",
        BALANCE_REPORT_DIR: "SSI_BalanceSLLs",
    }.get(REPORT_DIR)
    if expected_placement:
        assert status["PLACEMENT_DIRECTIVE"] == expected_placement
    setup_wns = float(status["CORE_SETUP_WNS_NS"])
    hold_whs = float(status["CORE_HOLD_WHS_NS"])
    if status["STATE"] == "CORE_100MHZ_ROUTED":
        assert setup_wns >= 0 and hold_whs >= 0
    else:
        assert status["STATE"] == "CORE_TIMING_NOT_MET_BITSTREAM_READY"
        assert setup_wns < 0 or hold_whs < 0
    run_eda("sha256sum -c --status " + shlex.quote(SOURCE_MANIFEST_PATH))
    run_eda("sha256sum -c --status " + shlex.quote(REPORT_DIR + "/implementation_inputs.sha256"))
    subprocess.run(
        ["rsync", "-a", "--include=*.rpt", "--include=*.txt", "--include=*.sha256", "--include=*.xdc",
         "--exclude=*", "hyyuan@10.12.133.23:" + REPORT_DIR + "/", str(LOCAL_DIR) + "/"],
        check=True, timeout=180,
    )
    implementation_sha256 = sha256_file(LOCAL_DIR / "implementation_inputs.sha256")
    assert implementation_sha256 == status["IMPLEMENTATION_INPUTS_SHA256"]
    for field, filename in REPORT_HASHES.items():
        assert sha256_file(LOCAL_DIR / filename) == status[field], filename

    utilization_text = (LOCAL_DIR / "utilization_postroute.rpt").read_text()
    uram_used = report_resource_count(utilization_text, "URAM")
    ramb36_used = report_resource_count(utilization_text, "RAMB36E2 only")
    assert uram_used <= 832
    assert ramb36_used <= 648

    route_text = (LOCAL_DIR / "route_status_postroute.rpt").read_text()
    routable = re.search(r"# of routable nets\.+\s*:\s*(\d+)", route_text)
    routed = re.search(r"# of fully routed nets\.+\s*:\s*(\d+)", route_text)
    errors = re.search(r"# of nets with routing errors\.+\s*:\s*(\d+)", route_text)
    assert routable and routed and errors
    assert int(routable[1]) > 0 and routable[1] == routed[1] and int(errors[1]) == 0
    drc_text = (LOCAL_DIR / "drc_postroute.rpt").read_text()
    assert "Design State : Fully Routed" in drc_text
    assert not re.search(r"\|\s*Error\s*\|", drc_text)
    drc_critical_warning_count = len(re.findall(r"\|\s*Critical Warning\s*\|", drc_text))
    timing_text = (LOCAL_DIR / "timing_postroute.rpt").read_text()
    shell_timing_met = "All user specified timing constraints are met." in timing_text
    core_timing_met = setup_wns >= 0 and hold_whs >= 0
    assert core_timing_met == (status["STATE"] == "CORE_100MHZ_ROUTED")
    if "SHELL_TIMING_CONSTRAINTS_MET" in status:
        assert shell_timing_met == (status["SHELL_TIMING_CONSTRAINTS_MET"] == "1")

    bitstream = LOCAL_DIR / "app_shell_9p_wrapper.bit"
    expected_bitstream = REPORT_DIR + "/app_shell_9p_wrapper.bit"
    assert status["BITSTREAM_PATH"] == expected_bitstream
    subprocess.run(["scp", "-q", "hyyuan@10.12.133.23:" + expected_bitstream, str(bitstream)],
                   check=True, timeout=300)
    bitstream_sha256 = sha256_file(bitstream)
    assert bitstream_sha256 == status["BITSTREAM_SHA256"]
    provenance = {
        "bitstream_sha256": bitstream_sha256,
        "runner_sha256": RUNNER_SHA256,
        "card": 1,
        "context_tokens": 512,
        "core_clock_config_mhz": 100,
        "core_setup_wns_ns": float(status["CORE_SETUP_WNS_NS"]),
        "core_hold_whs_ns": float(status["CORE_HOLD_WHS_NS"]),
        "implementation_state": status["STATE"],
        "implementation_report_dir": REPORT_DIR,
        "placement_directive": status.get("PLACEMENT_DIRECTIVE", ""),
        "postroute_drc_critical_warning_count": drc_critical_warning_count,
        "postroute_resources": {"uram288": uram_used, "ramb36e2": ramb36_used},
        "implementation_inputs_sha256": implementation_sha256,
        "core_timing_met": core_timing_met,
        "shell_timing_constraints_met": shell_timing_met,
        "payload_sha256": PAYLOAD_HASHES,
    }
    board_bitstream = BOARD_DIR + "/app_shell_9p_wrapper.bit"
    existing_bitstream = subprocess.check_output(
        board_command("if [ -f " + shlex.quote(board_bitstream) + " ]; then sha256sum " +
                      shlex.quote(board_bitstream) + "; fi"),
        text=True, timeout=60,
    ).strip()
    previous_bitstream_sha256 = existing_bitstream.split()[0] if existing_bitstream else None
    if previous_bitstream_sha256:
        provenance["previous_board_bitstream_sha256"] = previous_bitstream_sha256
    record("BOARD_TRANSFER", **provenance)
    board_pending = BOARD_DIR + "/app_shell_9p_wrapper.bit.pending"
    with bitstream.open("rb") as source:
        subprocess.run(board_command("cat > " + shlex.quote(board_pending)), stdin=source,
                       check=True, timeout=300)
    board_hashes = subprocess.check_output(
        board_command("sha256sum " + shlex.quote(board_pending) + " " +
                      shlex.quote(BOARD_DIR + "/plan6_vu9p_board_run_card1") + " " +
                      " ".join(shlex.quote(BOARD_DIR + "/payload/" + name) for name in PAYLOAD_HASHES)),
        text=True, timeout=60,
    )
    expected_hashes = [bitstream_sha256, RUNNER_SHA256, *PAYLOAD_HASHES.values()]
    assert [line.split()[0] for line in board_hashes.splitlines()] == expected_hashes
    archive = None
    if previous_bitstream_sha256 and previous_bitstream_sha256 != bitstream_sha256:
        archive = BOARD_DIR + "/app_shell_9p_wrapper.previous_" + previous_bitstream_sha256[:16] + ".bit"
        archived = subprocess.check_output(
            board_command("if [ -f " + shlex.quote(archive) + " ]; then sha256sum " +
                          shlex.quote(archive) + "; fi"),
            text=True, timeout=60,
        ).strip()
        if archived and archived.split()[0] != previous_bitstream_sha256:
            raise RuntimeError("The previous board bitstream archive path contains different data")
        if not archived:
            subprocess.run(board_command("mv " + shlex.quote(board_bitstream) + " " +
                                         shlex.quote(archive)), check=True, timeout=60)
        provenance["previous_board_bitstream_archive"] = archive
    try:
        subprocess.run(board_command("mv " + shlex.quote(board_pending) + " " +
                                     shlex.quote(board_bitstream)), check=True, timeout=60)
    except Exception:
        if archive:
            subprocess.run(board_command("mv " + shlex.quote(archive) + " " +
                                         shlex.quote(board_bitstream)), check=False, timeout=60)
        raise
    record("BOARD_RUNNING", **provenance)
    with (LOCAL_DIR / "board_run.log").open("w") as output:
        result = subprocess.run(
            board_command("cd " + shlex.quote(BOARD_DIR) +
                          " && timeout -k 10s 4500s ./plan6_vu9p_board_run_card1"),
            stdout=output, stderr=subprocess.STDOUT, timeout=4560,
        )
    board_text = (LOCAL_DIR / "board_run.log").read_text()
    result_line = next((line for line in board_text.splitlines()
                        if line.startswith("PLAN6_VU9P_RESULT ")), None)
    state = "BOARD_MEASURED" if result.returncode == 0 and result_line else "BOARD_RUN_INCOMPLETE"
    record(state, returncode=result.returncode, board_result=result_line, **provenance)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        record("HANDOFF_INCOMPLETE", operation_result=str(error))
        raise
