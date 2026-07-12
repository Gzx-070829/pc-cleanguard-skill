import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.cli import main


class ReputationCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.report = self.root / "report.json"
        self.report.write_text(json.dumps({"targets": [{"target_id": "x", "object_type": "SOFTWARE", "name": "Example Synthetic App 11"}]}), encoding="utf-8")
        self.seed = Path(__file__).resolve().parents[2] / "examples/reputation/seed_records.zh-CN.json"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _run(self, args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(args)
        return code, out.getvalue(), err.getvalue()

    def test_match_insight_and_pup_inspect_generate_artifacts(self) -> None:
        matches = self.root / "matches.json"
        insight = self.root / "insight.md"
        combined = self.root / "combined.md"
        self.assertEqual(0, self._run(["reputation", "match", "--input", str(self.report), "--seed", str(self.seed), "--output", str(matches)])[0])
        self.assertEqual(0, self._run(["reputation", "insight", "--matches", str(matches), "--output", str(insight)])[0])
        self.assertEqual(0, self._run(["pup", "inspect", "--input", str(self.report), "--seed", str(self.seed), "--output", str(combined)])[0])
        self.assertTrue(matches.is_file())
        self.assertIn("不是删除授权", combined.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
