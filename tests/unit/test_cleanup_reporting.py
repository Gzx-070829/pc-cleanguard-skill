import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.cleanup import JunkScanner, build_cleanup_preview
from pc_cleanguard.cleanup.reporting import (
    build_cleanup_summary,
    render_cleanup_report_markdown,
    write_cleanup_report_markdown,
)


class CleanupReportingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = TemporaryDirectory()
        self.root = Path(self.directory.name)
        (self.root / "one.tmp").write_bytes(b"123")
        (self.root / "two.log").write_bytes(b"12345")
        (self.root / "dump.dmp").write_bytes(b"12")
        self.preview = build_cleanup_preview(JunkScanner().scan([self.root])).to_dict()

    def tearDown(self) -> None:
        self.directory.cleanup()

    def _execution_result(self) -> dict:
        return {
            "schema_version": "0.2",
            "mode": "dry_run",
            "confirmed": False,
            "execution_level": "LEVEL_1_LOW_RISK_CLEANUP",
            "allow_roots": [str(self.root)],
            "audit_path": str(self.root / "audit.jsonl"),
            "summary": {
                "total_results": 2,
                "would_clean": 1,
                "cleaned": 0,
                "blocked": 0,
                "skipped": 1,
                "failed": 0,
                "bytes_reclaimed": 0,
                "execution_performed": False,
            },
            "results": [
                {
                    "path": str(self.root / "one.tmp"),
                    "category": "temp_file",
                    "action": "delete_file",
                    "status": "would_clean",
                    "reason": "explicit confirmation is absent",
                    "bytes_reclaimed": 0,
                    "evidence": [{"source": "test", "fact": "preview candidate"}],
                    "audit_event": {},
                },
                {
                    "path": str(self.root / "dump.dmp"),
                    "category": "crash_dump",
                    "action": "skip",
                    "status": "skipped",
                    "reason": "outside L1 allowlist",
                    "bytes_reclaimed": 0,
                    "evidence": [{"source": "test", "fact": "not L1"}],
                    "audit_event": {},
                },
            ],
        }

    def test_summary_combines_preview_and_execution_result(self) -> None:
        summary = build_cleanup_summary(self.preview, self._execution_result())

        self.assertEqual(3, summary["total_candidates"])
        self.assertEqual(10, summary["total_reclaimable_bytes"])
        self.assertEqual(0, summary["cleaned_count"])
        self.assertEqual(0, summary["cleaned_bytes"])
        self.assertEqual(1, summary["would_clean_count"])
        self.assertEqual(1, summary["skipped_count"])
        self.assertEqual(0, summary["blocked_count"])
        self.assertEqual(1, summary["by_status"]["would_clean"])
        self.assertEqual(1, summary["by_category"]["temp_file"]["count"])
        self.assertTrue(summary["top_items"])
        self.assertGreater(summary["top_items"][0]["size_bytes"], 0)
        self.assertTrue(summary["safety_notes"])

    def test_summary_can_be_built_from_preview_without_result(self) -> None:
        summary = build_cleanup_summary(self.preview)

        self.assertEqual(3, summary["total_candidates"])
        self.assertEqual({}, summary["by_status"])
        self.assertEqual(0, summary["cleaned_count"])
        self.assertEqual(3, len(summary["top_items"]))

    def test_summary_rejects_result_from_another_preview(self) -> None:
        result = self._execution_result()
        result["results"][0]["path"] = str(self.root / "unrelated.tmp")

        with self.assertRaises(ValueError):
            build_cleanup_summary(self.preview, result)

    def test_markdown_contains_cleanup_outcomes(self) -> None:
        markdown = render_cleanup_report_markdown(
            build_cleanup_summary(self.preview, self._execution_result())
        )

        self.assertIn("Reclaimable", markdown)
        self.assertIn("Cleaned", markdown)
        self.assertIn("Skipped", markdown)
        self.assertIn("Blocked", markdown)
        self.assertIn("安全说明", markdown)

    def test_markdown_writer_does_not_overwrite_by_default(self) -> None:
        output = self.root / "report.md"
        output.write_text("preserve", encoding="utf-8")

        with self.assertRaises(FileExistsError):
            write_cleanup_report_markdown(output, "replacement")

        self.assertEqual("preserve", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
