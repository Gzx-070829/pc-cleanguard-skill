import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.cli import main

ROOT = Path(__file__).resolve().parents[2]


class Pr26RealisticFixtureFlowTest(unittest.TestCase):
    def test_fixture_is_declared_synthetic_and_cli_indicators_work(self) -> None:
        fixture = json.loads((ROOT / "tests/fixtures/reputation/pr26_realistic_windows_inventory.json").read_text(encoding="utf-8"))
        self.assertTrue(fixture["synthetic_but_realistic"])
        evidence = ROOT / "data/reputation/evidence_pack.real.zh-CN.json"
        with TemporaryDirectory() as directory:
            output = Path(directory) / "indicators.json"
            commands = [
                ["reputation", "evidence", "indicators", "--input", str(evidence), "--output", str(output)],
                ["reputation", "evidence", "indicators-stats", "--input", str(evidence)],
            ]
            for command in commands:
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    self.assertEqual(0, main(command), command)
            self.assertTrue(json.loads(output.read_text(encoding="utf-8")))

    def test_pr26_runtime_has_no_network_or_process_imports(self) -> None:
        forbidden = (
            "import " + "subprocess", "from " + "subprocess", "import " + "requests",
            "import " + "urllib", "from " + "urllib", "import " + "socket",
            "import " + "http.client",
        )
        paths = [
            ROOT / "pc_cleanguard/reputation/indicators.py",
            ROOT / "pc_cleanguard/reputation/review_checklist.py",
            ROOT / "pc_cleanguard/pup/intelligence.py",
            ROOT / "pc_cleanguard/pup/review_pack.py",
            ROOT / "pc_cleanguard/pup/source_trace.py",
            ROOT / "pc_cleanguard/pup/feedback_template.py",
        ]
        for path in paths:
            source = path.read_text(encoding="utf-8")
            self.assertFalse(any(token in source for token in forbidden), path.name)


if __name__ == "__main__":
    unittest.main()
