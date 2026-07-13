import json
import unittest
import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.validation.real_report_validation import validate_real_report_shape, write_real_report_validation_pack
from pc_cleanguard.cli import main


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "tests/fixtures/reputation/pr29_cn_win_pup_inventory.json"


class RealReportValidationPackTest(unittest.TestCase):
    def setUp(self):
        self.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_shape_summary_covers_windows_groups(self):
        summary = validate_real_report_shape(self.report)
        self.assertTrue(all(summary["groups_present"].values()))

    def test_matchability_score_is_bounded(self):
        score = validate_real_report_shape(self.report)["matchability_score"]
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 100)

    def test_pii_hints_are_reported_without_reading_other_files(self):
        summary = validate_real_report_shape({"installed_apps": [{"path": "C:/Users/Alice/AppData/X"}]})
        self.assertGreater(summary["pii_hint_count"], 0)
        self.assertFalse(summary["runtime_network_access"])

    def test_pack_writes_six_local_artifacts(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "validation"
            result = write_real_report_validation_pack(self.report, output)
            self.assertEqual(6, result["artifact_count"])
            self.assertEqual({"START_HERE.md", "report_shape_summary.json", "pii_redaction_checklist.md", "matchability_summary.md", "unsupported_fields.md", "next_steps.md"}, {item.name for item in output.iterdir()})

    def test_validate_report_cli_is_local_and_non_overwriting(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "validation"
            command = ["validate", "report", "--input", str(REPORT), "--output", str(output)]
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(0, main(command))
                self.assertEqual(2, main(command))


if __name__ == "__main__":
    unittest.main()
