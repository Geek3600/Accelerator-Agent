from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from accagent.framework.live_state import (
    LIVE_STATE_SLOTS,
    activate_live_state_slot,
    board_run_binding,
    live_state_path,
    read_live_state,
    update_live_state_slot,
)


class LiveStateTest(unittest.TestCase):
    def test_fixed_path_has_only_fixed_slots_and_preserves_other_slots(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            activate_live_state_slot(
                run_dir,
                "controller",
                {"status": "running"},
                binding="controller",
            )
            activate_live_state_slot(
                run_dir,
                "agent",
                {"status": "inflight", "agent": "repair"},
                binding="agent-1",
            )
            updated = update_live_state_slot(
                run_dir,
                "controller",
                {"status": "finished"},
                binding="controller",
            )
            state = read_live_state(run_dir)

        self.assertTrue(updated["applied"])
        self.assertEqual(live_state_path(run_dir).name, "live_state.json")
        self.assertEqual(tuple(state), LIVE_STATE_SLOTS)
        self.assertEqual(state["controller"]["data"]["status"], "finished")
        self.assertEqual(state["agent"]["data"]["agent"], "repair")

    def test_old_board_status_cannot_replace_a_new_board_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            old_report = {
                "input_fingerprint_sha256": "a" * 64,
                "remote_workdir": "/remote/old",
            }
            new_report = {
                "input_fingerprint_sha256": "b" * 64,
                "remote_workdir": "/remote/new",
            }
            old_binding = board_run_binding(old_report)
            new_binding = board_run_binding(new_report)
            activate_live_state_slot(
                run_dir,
                "board_run",
                {"status": "running", "remote_workdir": "/remote/old"},
                binding=old_binding,
            )
            activate_live_state_slot(
                run_dir,
                "board_run",
                {"status": "running", "remote_workdir": "/remote/new"},
                binding=new_binding,
            )
            stale = update_live_state_slot(
                run_dir,
                "board_run",
                {"status": "fail", "remote_workdir": "/remote/old"},
                binding=old_binding,
            )
            state = read_live_state(run_dir)

        self.assertFalse(stale["applied"])
        self.assertEqual(state["board_run"]["binding"], new_binding)
        self.assertEqual(
            state["board_run"]["data"]["remote_workdir"], "/remote/new"
        )


if __name__ == "__main__":
    unittest.main()
