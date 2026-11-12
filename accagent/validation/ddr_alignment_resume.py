"""Resume the three existing model controllers after shared architecture validation."""

import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "accagent/diagnostics/ddr_alignment_20261017"
STATUS = OUT / "implementation/implementation_status.json"


def main():
    print("Waiting for actual shared-architecture leaf VCS pass", flush=True)
    while True:
        if STATUS.is_file():
            status = json.loads(STATUS.read_text())
            if status.get("status") in {"leaf_regression_pass", "leaf_compile_pass"}:
                break
        time.sleep(10)
    old = json.loads((ROOT / "accagent/diagnostics/dse_calibration_20261017/controllers.json").read_text())
    env = os.environ.copy()
    env["JDK_JAVA_OPTIONS"] = "-Xmx1800m -XX:ActiveProcessorCount=2"
    controllers = []
    for item in old["controllers"]:
        run = Path(item["run_dir"])
        command = item["command"][:]
        command[command.index("--start-stage") + 1] = "template_selection"
        state = run / "constraint_extraction/initial_design_graph.json"
        command[command.index("--sacg-state") + 1] = str(state)
        log = run / "controller_resume_20261017_ddr_architecture.log"
        with log.open("a") as output:
            process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=output,
                                       stderr=subprocess.STDOUT, start_new_session=True)
        controllers.append({"run_dir": str(run), "pid": process.pid,
                            "source_state": str(state), "start_stage": "template_selection",
                            "log": str(log), "command": command})
        print(run.name, process.pid, flush=True)
    (OUT / "regenerated_controllers.json").write_text(json.dumps({
        "timestamp": datetime.now().astimezone().isoformat(),
        "controllers": controllers,
        "acceptance": "Shared architecture implemented and VCS compile/elaboration/link passed; regenerated models still require their VCS gates and real Vivado synthesis with resource and retained-hardware checks.",
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
