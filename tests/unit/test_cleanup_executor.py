import ast
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.cleanup import (
    CleanupConfirmation,
    CleanupExecutor,
    JunkScanner,
    build_cleanup_preview,
)


class CleanupExecutorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.temp_file = self.root / "scratch.tmp"
        self.log_file = self.root / "events.log"
        self.cache_file = self.root / "cache" / "blob.bin"
        self.crash_file = self.root / "failure.dmp"
        self.installer_file = self.root / "old.msi"
        self.empty_directory = self.root / "empty-folder"
        self.cache_file.parent.mkdir()
        self.empty_directory.mkdir()
        self.temp_file.write_bytes(b"123")
        self.log_file.write_bytes(b"12345")
        self.cache_file.write_bytes(b"1234")
        self.crash_file.write_bytes(b"123456")
        self.installer_file.write_bytes(b"1234567")
        self.preview = build_cleanup_preview(JunkScanner().scan([self.root])).to_dict()
        self.audit = self.root / "execution-audit.jsonl"

    def tearDown(self) -> None:
        self.directory.cleanup()

    def _execute(self, confirmed: bool, *, root: Path | None = None):
        return CleanupExecutor(
            permanent=confirmed,
            permanent_delete_acknowledged=confirmed,
        ).execute(
            self.preview,
            CleanupConfirmation(confirmed, (root or self.root,)),
            audit_path=self.audit,
        )

    def test_default_mode_only_reports_would_clean(self) -> None:
        report = self._execute(False).to_dict()
        eligible = [item for item in report["results"] if item["status"] == "would_clean"]
        self.assertEqual(3, len(eligible))
        self.assertTrue(self.temp_file.exists())
        self.assertTrue(self.log_file.exists())
        self.assertTrue(self.cache_file.exists())
        self.assertEqual(0, report["summary"]["bytes_reclaimed"])
        self.assertTrue(all(item["audit_event"]["dry_run"] for item in eligible))

    def test_confirmed_mode_deletes_only_l1_files(self) -> None:
        report = self._execute(True).to_dict()
        self.assertFalse(self.temp_file.exists())
        self.assertFalse(self.log_file.exists())
        self.assertFalse(self.cache_file.exists())
        self.assertTrue(self.crash_file.exists())
        self.assertTrue(self.installer_file.exists())
        self.assertTrue(self.empty_directory.is_dir())
        self.assertEqual(12, report["summary"]["bytes_reclaimed"])
        self.assertEqual(3, report["summary"]["cleaned"])

    def test_non_l1_and_directory_candidates_are_skipped(self) -> None:
        report = self._execute(True).to_dict()
        skipped = [item for item in report["results"] if item["status"] == "skipped"]
        self.assertEqual(3, len(skipped))
        self.assertEqual(
            {"crash_dump", "installer_leftover", "empty_directory_candidate"},
            {item["category"] for item in skipped},
        )
        self.assertTrue(all(item["bytes_reclaimed"] == 0 for item in skipped))

    def test_candidate_outside_allow_root_is_blocked(self) -> None:
        allowed = self.root / "allowed"
        allowed.mkdir()
        report = self._execute(True, root=allowed).to_dict()
        blocked = [item for item in report["results"] if item["status"] == "blocked"]
        self.assertEqual(3, len(blocked))
        self.assertTrue(self.temp_file.exists())

    def test_protected_candidate_is_blocked_even_if_preview_claims_l1(self) -> None:
        documents = self.root / "Documents"
        documents.mkdir()
        protected = documents / "private.tmp"
        protected.write_bytes(b"private")
        temp_candidate = next(
            item
            for item in self.preview["top_candidates"]
            if item["category"] == "temp_file"
        )
        temp_candidate["path"] = str(protected)
        report = self._execute(True).to_dict()
        result = next(item for item in report["results"] if item["path"] == str(protected))
        self.assertEqual("blocked", result["status"])
        self.assertTrue(protected.exists())

    def test_preview_candidate_must_preserve_dry_run_confirmation_flags(self) -> None:
        self.preview["top_candidates"][0]["dry_run_only"] = False
        with self.assertRaises(ValueError):
            self._execute(True)
        self.assertTrue(self.temp_file.exists())

    def test_each_result_has_required_fields_and_audit_jsonl(self) -> None:
        report = self._execute(False).to_dict()
        lines = [
            json.loads(line) for line in self.audit.read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(len(report["results"]), len(lines))
        required = {
            "path",
            "action",
            "status",
            "reason",
            "bytes_reclaimed",
            "evidence",
            "audit_event",
        }
        self.assertTrue(all(required.issubset(item) for item in report["results"]))

    def test_cleanup_modules_have_no_process_or_network_imports(self) -> None:
        root = Path(__file__).resolve().parents[2] / "pc_cleanguard" / "cleanup"
        imports = set()
        for path in root.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module.split(".")[0])
        forbidden = {
            first + second
            for first, second in (
                ("sub", "process"),
                ("req", "uests"),
                ("url", "lib"),
                ("sock", "et"),
            )
        }
        self.assertTrue(forbidden.isdisjoint(imports))

    def test_execution_result_schema_is_l1_and_command_free(self) -> None:
        schema_path = (
            Path(__file__).resolve().parents[2]
            / "schemas"
            / "cleanup_execution_result.schema.json"
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertEqual(
            "LEVEL_1_LOW_RISK_CLEANUP",
            schema["properties"]["execution_level"]["const"],
        )
        item = schema["$defs"]["execution_item"]
        self.assertTrue(
            {
                "path",
                "action",
                "status",
                "reason",
                "bytes_reclaimed",
                "evidence",
                "audit_event",
            }.issubset(item["required"])
        )
        self.assertNotIn('"command"', json.dumps(schema).casefold())


if __name__ == "__main__":
    unittest.main()
