import importlib.util
import sys
import unittest
from pathlib import Path

RUNNER_DIR = Path(__file__).resolve().parents[1] / "accagent/experiments/gpt2_medium_seq32_20261027/core_method_validation_20261031"
sys.path.insert(0, str(RUNNER_DIR))
spec = importlib.util.spec_from_file_location("tracebench_v6_rtl", RUNNER_DIR / "run_tracebench_v6_rtl.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class TracebenchRtlTest(unittest.TestCase):
    def test_injection_preserves_child_named_ports(self):
        source = "module A(input io_x, output io_y);\nB b(.io_x(io_x), .io_y(io_y));\nendmodule\n"
        mutated = runner.inject_port_mismatch(source, "io_x", "io_x_fault")
        self.assertIn("input io_x_fault", mutated)
        self.assertIn(".io_x(io_x_fault)", mutated)
        consumer = "module Top; A a(.io_x(x), .io_y(y)); endmodule"
        candidate, repaired = runner.infer_port_repair(mutated, "io_x", consumer, "A", "a")
        self.assertEqual(candidate, "io_x_fault")
        self.assertEqual(repaired, source)

    def test_does_not_guess_with_ambiguous_or_incomplete_evidence(self):
        source = "module A(input bad_x, input bad_z, output io_y); endmodule"
        consumer = "module Top; A a(.io_x(x), .io_y(y)); endmodule"
        self.assertIsNone(runner.infer_port_repair(source, "io_x", consumer, "A", "a"))
        self.assertIsNone(runner.infer_port_repair(source, "io_x", "", "A", "a"))

    def test_parser_accepts_vcs_wrapped_diagnostic(self):
        match = runner.parse_undefined_port('Port "io_x" is not defined in module \'A\' defined \n  in "A.sv", 2')
        self.assertEqual(match.groups(), ("io_x", "A", "A.sv"))


if __name__ == "__main__":
    unittest.main()
