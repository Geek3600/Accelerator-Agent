import json
import tempfile
import unittest
from pathlib import Path

from accagent.framework.sacg_store import SACGStore


class RepairAuthorizationTest(unittest.TestCase):
    def test_only_related_exact_files_are_authorized(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "plan.json"
            target.write_text("{}", encoding="utf-8")
            state = {
                "nodes": [{"id": "n"}], "edges": [{"id": "e"}],
                "constraints": [{"id": "c"}],
                "artifacts": [
                    {"id": "a", "path": str(target), "edges": ["e"]},
                    {"id": "unrelated", "path": str(target)},
                    {"id": "directory", "path": str(root), "edges": ["e"]},
                ],
            }
            state_path = root / "state.json"
            state_path.write_text(json.dumps(state), encoding="utf-8")
            store = SACGStore(state_path)
            transition = store.declare_transition("repair", ["n"], ["e"], ["c"], repair_scopes=["signal_connection"])
            self.assertEqual(store.authorize_repair_artifacts(transition["id"], ["a"]), [str(target.resolve())])
            with self.assertRaises(ValueError):
                store.authorize_repair_artifacts(transition["id"], ["unrelated"])
            with self.assertRaises(ValueError):
                store.authorize_repair_artifacts(transition["id"], ["directory"])
            self.assertEqual(store.authorize_repair_artifacts(transition["id"], ["directory"], requested_paths={"directory": [str(target)]}), [str(target.resolve())])
            with self.assertRaises(ValueError):
                store.authorize_repair_artifacts(transition["id"], ["directory"], requested_paths={"directory": ["/etc/passwd"]})
            forbidden = store.declare_transition("repair", ["n"], ["e"], ["c"], repair_scopes=["bypass_checker"])
            with self.assertRaises(ValueError):
                store.authorize_repair_artifacts(forbidden["id"], ["a"])


if __name__ == "__main__":
    unittest.main()
