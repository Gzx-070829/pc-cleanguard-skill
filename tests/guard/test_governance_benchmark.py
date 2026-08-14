import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from pc_cleanguard.cli import main
from pc_cleanguard.guard.benchmark import run_benchmark


ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / "benchmarks" / "governance"


class GovernanceBenchmarkTests(unittest.TestCase):
    def test_fixed_suite_has_about_twenty_scenarios_and_zero_gate_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run_benchmark(SUITE, Path(directory) / "result")
            self.assertGreaterEqual(result["scenario_count"], 20)
            self.assertEqual(0, result["failed"])
            self.assertEqual(0, result["authorization_failures"])
            self.assertEqual(0, result["monotonicity_failures"])
            self.assertEqual(0, result["audit_failures"])
            self.assertTrue((Path(directory) / "result" / "benchmark-result.json").is_file())

    def test_cli_benchmark_emits_machine_json(self):
        with tempfile.TemporaryDirectory() as directory:
            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                code = main(
                    [
                        "guard", "benchmark", "--suite", str(SUITE),
                        "--output", str(Path(directory) / "out"), "--json",
                    ]
                )
            self.assertEqual(0, code, stderr.getvalue())
            self.assertEqual(0, json.loads(stdout.getvalue())["failed"])
            self.assertEqual("", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()

