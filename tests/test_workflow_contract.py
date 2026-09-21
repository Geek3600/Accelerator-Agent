import unittest

from accagent.framework.workflow_contract import public_stage, public_workflow_manifest


class WorkflowContractTest(unittest.TestCase):
    def test_public_workflow_is_consecutive_stage_zero_to_seven(self) -> None:
        workflow = public_workflow_manifest()
        self.assertEqual([stage["id"] for stage in workflow], list(range(8)))
        self.assertEqual(workflow[5]["internal_steps"], ["code_generation", "verification_artifacts"])
        self.assertEqual(workflow[6]["internal_steps"], ["debug_loop"])
        self.assertEqual(workflow[7]["internal_steps"], ["backend_board"])

    def test_internal_steps_map_to_their_public_stage(self) -> None:
        self.assertEqual(public_stage("verification_artifacts")["id"], 5)
        self.assertEqual(public_stage("debug_loop")["id"], 6)
        self.assertEqual(public_stage("backend_board")["id"], 7)
