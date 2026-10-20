from unittest import TestCase

from accagent.framework.repair_loop import (
    DEBUG_LAYERS,
    current_layer,
    layer_reports,
)


class RepairLoopLayerTest(TestCase):
    def test_reused_lower_layer_passes_are_not_reopened_by_pending_gates(self) -> None:
        required_gates = []
        for layer in DEBUG_LAYERS:
            for gate in layer["required_gates"]:
                status = "pending_later_stage"
                if gate == "case_leaf_functional":
                    status = "pass"
                if gate == "case_board_interface_discovery":
                    status = "fail"
                required_gates.append({"name": gate, "status": status})

        layers = layer_reports(
            {"required_gates": required_gates},
            {"results": []},
        )

        self.assertEqual(layers[0]["status"], "pass")
        self.assertEqual(layers[1]["status"], "pending_later_stage")
        self.assertEqual(layers[2]["status"], "needs_repair")
        self.assertEqual(current_layer(layers)["id"], "board_axi_ddr_wrapped_system")
