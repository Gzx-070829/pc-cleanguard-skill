import tempfile
import unittest
from pathlib import Path

from pc_cleanguard.pipeline import run_readonly_scan_pipeline
from pc_cleanguard.windows.report_builder import build_windows_canonical_report
from pc_cleanguard.windows.report_validation import validate_windows_canonical_report


class WindowsCanonicalReportTests(unittest.TestCase):
    def _collections(self):
        return {
            "collections": {
                "installed_apps": [{"name": "Example App", "publisher": "Example Publisher", "install_location": r"C:\Program Files\Example"}],
                "startup_items": [{"name": "Example Startup", "command": r"C:\Program Files\Example\app.exe"}],
                "services": [{"service_name": "ExampleService", "display_name": "Example Service", "path_name": r"C:\Program Files\Example\svc.exe"}],
                "scheduled_tasks": [{"task_name": "Example Task", "actions_summary": r"C:\Program Files\Example\app.exe"}],
            },
            "collector_status": {
                name: {"status": "success", "record_count": 1}
                for name in ("installed_apps", "startup_items", "services", "scheduled_tasks")
            },
            "collection_errors": [],
            "manifest": {"generated_at": "2026-07-17T00:00:00Z"},
        }

    def test_builds_report_consumable_by_existing_scan_pipeline(self):
        report = build_windows_canonical_report(self._collections())
        self.assertEqual([], validate_windows_canonical_report(report))
        self.assertEqual("Windows", report["platform"])
        self.assertEqual(1, len(report["installed_apps"]))
        self.assertTrue(report["installed_apps"][0]["target_id"].startswith("WINDOWS_APP:"))
        result = run_readonly_scan_pipeline(report, scan_id="canonical:test")
        self.assertEqual(4, result.normalized_counts["total_targets"])

    def test_partial_report_keeps_successful_records_and_failure_status(self):
        source = self._collections()
        source["collector_status"]["scheduled_tasks"] = {
            "status": "unsupported", "record_count": 0, "error_code": "cmdlet_unavailable"
        }
        source["collections"]["scheduled_tasks"] = []
        report = build_windows_canonical_report(source)
        self.assertEqual("partial", report["collection_state"])
        self.assertIn("scheduled_tasks", report["unsupported_collectors"])
        self.assertEqual(1, len(report["installed_apps"]))

    def test_collected_commands_remain_metadata_and_are_never_executed(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "must-not-exist.txt"
            source = self._collections()
            source["collections"]["startup_items"][0]["command"] = f"write {marker}"
            report = build_windows_canonical_report(source)
            self.assertIn(str(marker), report["startup_items"][0]["command"])
            self.assertFalse(marker.exists())

    def test_unknown_fields_are_named_not_silently_discarded(self):
        source = self._collections()
        source["collections"]["installed_apps"][0]["future_field"] = "future-value"
        report = build_windows_canonical_report(source)
        self.assertTrue(any(item["field"] == "future_field" for item in report["unsupported_fields"]))

    def test_nameless_record_is_reported_at_its_original_index(self):
        source = self._collections()
        source["collections"]["installed_apps"] = [
            {"publisher": "Missing Identity"},
            {"name": "Valid App"},
        ]
        source["collector_status"]["installed_apps"]["record_count"] = 2
        report = build_windows_canonical_report(source)
        self.assertEqual(1, len(report["installed_apps"]))
        self.assertTrue(any(
            issue["collector"] == "installed_apps" and issue["record_index"] == 0
            for issue in report["unsupported_records"]
        ))


if __name__ == "__main__":
    unittest.main()
