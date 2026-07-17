import json
import tempfile
import unittest
from pathlib import Path

from pc_cleanguard.windows.collector_ingest import load_collector_directory
from pc_cleanguard.windows.collector_manifest import validate_collector_manifest


def _write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


class WindowsCollectorIngestTests(unittest.TestCase):
    def test_loads_four_collections_and_manifest_without_mutating_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = {
                "schema_version": "0.4.1",
                "source_kind": "windows_powershell_collector",
                "generated_at": "2026-07-17T00:00:00Z",
                "collectors": {
                    name: {"status": "success", "file": f"{name}.json", "record_count": 1}
                    for name in ("installed_apps", "startup_items", "services", "scheduled_tasks")
                },
            }
            _write_json(root / "collector_manifest.json", manifest)
            _write_json(root / "collector_errors.json", [])
            _write_json(root / "installed_apps.json", [{"name": "Example App"}])
            _write_json(root / "startup_items.json", [{"name": "Example Start"}])
            _write_json(root / "services.json", [{"service_name": "ExampleSvc"}])
            _write_json(root / "scheduled_tasks.json", [{"task_name": "ExampleTask"}])
            before = (root / "installed_apps.json").read_bytes()

            loaded = load_collector_directory(root)

            self.assertEqual([], validate_collector_manifest(loaded["manifest"]))
            self.assertEqual(1, len(loaded["collections"]["installed_apps"]))
            self.assertEqual(before, (root / "installed_apps.json").read_bytes())

    def test_failed_and_unsupported_collectors_are_structured_not_fatal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = {
                "schema_version": "0.4.1",
                "source_kind": "windows_powershell_collector",
                "generated_at": "2026-07-17T00:00:00Z",
                "collectors": {
                    "installed_apps": {"status": "success", "file": "installed_apps.json", "record_count": 0},
                    "startup_items": {"status": "failed", "file": "startup_items.json", "record_count": 0, "error_code": "collector_failed"},
                    "services": {"status": "success", "file": "services.json", "record_count": 0},
                    "scheduled_tasks": {"status": "unsupported", "file": "scheduled_tasks.json", "record_count": 0, "error_code": "cmdlet_unavailable"},
                },
            }
            _write_json(root / "collector_manifest.json", manifest)
            _write_json(root / "collector_errors.json", [{"collector": "startup_items", "error_code": "collector_failed"}])
            for name in ("installed_apps", "startup_items", "services", "scheduled_tasks"):
                _write_json(root / f"{name}.json", [])

            loaded = load_collector_directory(root)

            self.assertEqual("failed", loaded["collector_status"]["startup_items"]["status"])
            self.assertEqual("unsupported", loaded["collector_status"]["scheduled_tasks"]["status"])
            self.assertEqual(1, len(loaded["collection_errors"]))

    def test_manifest_validation_reports_missing_collectors(self):
        errors = validate_collector_manifest(
            {"schema_version": "0.4.1", "source_kind": "windows_powershell_collector", "generated_at": "now", "collectors": {}}
        )
        self.assertTrue(any("installed_apps" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
