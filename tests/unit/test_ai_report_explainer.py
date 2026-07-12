import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.ai import (
    DryRunPromptProvider,
    MockAIProvider,
    SAFETY_NOTICE,
    explain_report,
    load_report_json_file,
    write_explanation_markdown,
)
from pc_cleanguard.cli import main


ROOT = Path(__file__).resolve().parents[2]
SAMPLE_REPORT = (
    ROOT / "examples" / "reports" / "pr7_readonly_scan_pipeline_report.json"
)


class AIReportExplainerTest(unittest.TestCase):
    def test_explainer_consumes_bounded_pup_insight(self) -> None:
        report = {
            "pup_insight": {
                "summary": {"matched_targets": 2, "behavior_category_count": 1},
                "suspicious_behaviors": ["ad_popup"],
                "uncertainty_notes": ["needs review"],
                "execution_authorized": False,
            }
        }
        explanation = explain_report(report, DryRunPromptProvider())
        self.assertIn("ad_popup", explanation.prompt)
        self.assertIn("不是删除、卸载或禁用授权", explanation.prompt)

    def setUp(self) -> None:
        self.directory = TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.output = self.root / "explanation.md"

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_load_report_reads_explicit_json(self) -> None:
        report = load_report_json_file(SAMPLE_REPORT)
        self.assertEqual("scan:pr7-example", report["scan_id"])

    def test_load_report_rejects_unc_path(self) -> None:
        with self.assertRaises(ValueError):
            load_report_json_file(r"\\server\share\report.json")

    def test_explain_report_handles_pipeline_report(self) -> None:
        explanation = explain_report(
            load_report_json_file(SAMPLE_REPORT), MockAIProvider()
        )
        self.assertEqual("mock", explanation.provider)
        self.assertIn("扫描摘要", explanation.markdown)
        self.assertFalse(explanation.execution_authorized)

    def test_explanation_contains_safety_notice(self) -> None:
        explanation = explain_report({}, MockAIProvider())
        self.assertEqual(SAFETY_NOTICE, explanation.safety_notice)
        self.assertIn(SAFETY_NOTICE, explanation.markdown)

    def test_explainer_adds_notice_if_provider_omits_it(self) -> None:
        class MinimalProvider:
            name = "minimal"

            def generate(self, prompt: str, report: dict) -> str:
                return "# 解释"

        explanation = explain_report({}, MinimalProvider())
        self.assertTrue(explanation.markdown.startswith("## safety_notice"))

    def test_dry_run_explanation_returns_prompt(self) -> None:
        explanation = explain_report({}, DryRunPromptProvider())
        self.assertEqual(explanation.prompt, explanation.markdown)
        self.assertIn("不要生成命令", explanation.markdown)

    def test_writer_creates_utf8_markdown(self) -> None:
        explanation = explain_report({}, MockAIProvider())
        write_explanation_markdown(self.output, explanation)
        self.assertIn(SAFETY_NOTICE, self.output.read_text(encoding="utf-8"))

    def test_writer_does_not_overwrite_by_default(self) -> None:
        self.output.write_text("preserve", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            write_explanation_markdown(
                self.output, explain_report({}, MockAIProvider())
            )
        self.assertEqual("preserve", self.output.read_text(encoding="utf-8"))

    def test_writer_allows_explicit_overwrite(self) -> None:
        self.output.write_text("old", encoding="utf-8")
        write_explanation_markdown(
            self.output,
            explain_report({}, MockAIProvider()),
            explicit_overwrite=True,
        )
        self.assertIn(SAFETY_NOTICE, self.output.read_text(encoding="utf-8"))

    def test_cli_explain_mock_writes_markdown(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(io.StringIO()):
            code = main(
                [
                    "explain",
                    "--report",
                    str(SAMPLE_REPORT),
                    "--output",
                    str(self.output),
                    "--provider",
                    "mock",
                ]
            )
        summary = json.loads(stdout.getvalue())
        self.assertEqual(0, code)
        self.assertEqual("mock", summary["provider"])
        self.assertFalse(summary["execution_authorized"])
        self.assertIn(SAFETY_NOTICE, self.output.read_text(encoding="utf-8"))

    def test_cli_dry_run_prompt_writes_bounded_prompt(self) -> None:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            code = main(
                [
                    "explain",
                    "--report",
                    str(SAMPLE_REPORT),
                    "--output",
                    str(self.output),
                    "--dry-run-prompt",
                ]
            )
        self.assertEqual(0, code)
        self.assertIn("PR9 报告解释任务", self.output.read_text(encoding="utf-8"))

    def test_cli_explain_requires_explicit_report_and_output(self) -> None:
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as context:
            main(["explain"])
        self.assertEqual(2, context.exception.code)

    def test_cli_explain_does_not_overwrite_by_default(self) -> None:
        self.output.write_text("preserve", encoding="utf-8")
        stderr = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(stderr):
            code = main(
                [
                    "explain",
                    "--report",
                    str(SAMPLE_REPORT),
                    "--output",
                    str(self.output),
                ]
            )
        self.assertEqual(2, code)
        self.assertIn("exists", stderr.getvalue().casefold())
        self.assertEqual("preserve", self.output.read_text(encoding="utf-8"))

    def test_committed_example_matches_mock_output(self) -> None:
        expected = explain_report(
            load_report_json_file(SAMPLE_REPORT), MockAIProvider()
        ).markdown.rstrip()
        example = (
            ROOT / "examples" / "ai" / "pr9_explainer_output.md"
        ).read_text(encoding="utf-8").rstrip()
        self.assertEqual(expected, example)


if __name__ == "__main__":
    unittest.main()
