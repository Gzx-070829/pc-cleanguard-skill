import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from pc_cleanguard.cli import main
from pc_cleanguard.evaluation import run_windows_local_evaluation
from pc_cleanguard.windows import build_windows_canonical_report, redact_windows_report


ROOT = Path(__file__).resolve().parents[2]


def _report():
    source = {
        "installed_apps": [{"name": "Example Neutral Utility", "publisher": "Example Publisher", "install_location": r"C:\Users\tester\AppData\Local\Example"}],
        "startup_items": [{"name": "Example Updater", "command": r"C:\Users\tester\AppData\Local\Example\update.exe"}],
        "services": [{"service_name": "UnrelatedService"}],
        "scheduled_tasks": [{"task_name": "Unrelated Task"}],
    }
    raw = build_windows_canonical_report(source)
    return redact_windows_report(raw)[0]


class WindowsLocalEvaluationTests(unittest.TestCase):
    def test_evaluation_consumes_redacted_report_and_writes_required_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "evaluation"
            result = run_windows_local_evaluation(
                _report(), output, [], cn_win_evidence_pack=[],
                include_persistence_chain=True,
                include_pup_review=True,
                include_evidence_quality=True,
                include_user_friendly_report=True,
            )
            for name in (
                "START_HERE.md", "environment_summary.json", "report_validation.json",
                "report_stats.json", "matchability_summary.md", "pup_review_pack",
                "persistence_chain.json", "persistence_chain.md",
                "persistence_governance_plan.json", "persistence_governance_plan.md",
                "link_diagnostics.json", "user_friendly_summary.md", "FINAL_EVALUATION.md",
            ):
                self.assertTrue((output / name).exists(), name)
            self.assertFalse(result.runtime_network_access)
            self.assertFalse(result.collector_execution_performed)
            self.assertEqual(0, result.execution_gating_eligible_count)
            final = (output / "FINAL_EVALUATION.md").read_text(encoding="utf-8")
            self.assertIn("No-match", final)
            self.assertIn("系统修改", final)

    def test_raw_report_is_rejected(self):
        raw = build_windows_canonical_report({"installed_apps": [], "startup_items": [], "services": [], "scheduled_tasks": []})
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                run_windows_local_evaluation(raw, Path(directory) / "evaluation", [])

    def test_cli_evaluation_uses_explicit_report_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = root / "report.json"
            report.write_text(json.dumps(_report()), encoding="utf-8")
            output = root / "evaluation"
            arguments = [
                "evaluation", "windows", "--report", str(report), "--output", str(output),
                "--evidence-pack", str(ROOT / "data/reputation/evidence_pack.real.zh-CN.json"),
                "--cn-win-evidence-pack", str(ROOT / "data/reputation/evidence_pack.cn_win.zh-CN.json"),
                "--include-persistence-chain", "--include-pup-review",
                "--include-evidence-quality", "--include-user-friendly-report",
            ]
            with contextlib.redirect_stdout(io.StringIO()):
                code = main(arguments)
            self.assertEqual(0, code)
            summary = json.loads((output / "environment_summary.json").read_text(encoding="utf-8"))
            self.assertFalse(summary["collector_execution_performed"])
            self.assertFalse(summary["runtime_network_access"])


if __name__ == "__main__":
    unittest.main()
