from __future__ import annotations

import unittest

from scripts.synthesis.app_shell_target_discovery import build_tcl


class AppShellTargetDiscoveryTest(unittest.TestCase):
    def test_discovery_opens_bd_in_private_project_copy(self) -> None:
        text = build_tcl("/board/sample.xpr", ["compute_slot"])

        self.assertIn("open_project $project_xpr", text)
        self.assertIn("save_project_as -force -dir $clone_root $project_name", text)
        self.assertIn('set project_xpr [file join $clone_root "${project_name}.xpr"]', text)
        self.assertLess(text.index("save_project_as -force"), text.index("open_bd_design $bd"))
        self.assertIn("project_clone_status", text)


if __name__ == "__main__":
    unittest.main()
