import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from scripts.synthesis.app_shell_target_hint_synthesis import apply_decision, validated_stage6_selection


class AppShellTargetHintSynthesisTest(unittest.TestCase):
    def test_only_reuses_the_unchanged_hash_verified_stage6_slot(self) -> None:
        target = {
            "selected_cell_id": "cell-7", "replacement_module_identity": "SlotAdapter",
            "bd_cell": "/slot_7",
        }
        identity = {
            "compute_slot_abi": {
                "selected_cell_id": "cell-7", "replacement_module_identity": "SlotAdapter",
                "replacement_instance_boundary": "/slot_7",
            },
        }
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            path = run_dir / "verification" / "board_interface" / "board_source_identity.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(identity), encoding="utf-8")
            with patch(
                "scripts.synthesis.app_shell_target_hint_synthesis.validate_exact_board_identity",
                return_value={"status": "pass"},
            ):
                accepted = validated_stage6_selection(run_dir, {"integration_target": target})
                changed = validated_stage6_selection(run_dir, {
                    "integration_target": {**target, "bd_cell": "/other_slot"},
                })
            with patch(
                "scripts.synthesis.app_shell_target_hint_synthesis.validate_exact_board_identity",
                return_value={"status": "fail"},
            ):
                stale = validated_stage6_selection(run_dir, {"integration_target": target})

        self.assertEqual(accepted["status"], "pass")
        self.assertFalse(accepted["human_approval_claimed"])
        self.assertEqual(changed["status"], "target_mismatch")
        self.assertEqual(stale["status"], "unavailable")

    def test_applies_scalar_target_fields_without_list_hash_error(self) -> None:
        contract = {"integration_target": {"replacement_module_identity": "old"}}
        decision = {
            "decision": "approved_target",
            "citations": [],
            "proposed_contract_update": {
                "integration_target": {
                    "ip_name": "new_ip",
                    "bd_cell": "/slot",
                    "bd_path": "shell",
                    "adapter_contract": "compute_slot_abi",
                }
            },
        }

        updated = apply_decision(contract, decision)

        self.assertEqual(updated["integration_target"]["ip_name"], "new_ip")
        self.assertEqual(updated["integration_target"]["bd_cell"], "/slot")


if __name__ == "__main__":
    unittest.main()
