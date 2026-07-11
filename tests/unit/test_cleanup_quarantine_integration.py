import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.cleanup import (
    CleanupConfirmation,
    CleanupExecutor,
    JunkScanner,
    build_cleanup_preview,
    build_cleanup_summary,
)
from pc_cleanguard.quarantine import QuarantineManager


class CleanupQuarantineIntegrationTest(unittest.TestCase):
    def test_confirmed_l1_file_is_quarantined_instead_of_deleted(self) -> None:
        with TemporaryDirectory() as directory:
            base = Path(directory)
            allowed = base / "allowed"
            allowed.mkdir()
            candidate = allowed / "scratch.tmp"
            candidate.write_bytes(b"recover me")
            preview = build_cleanup_preview(JunkScanner().scan([allowed])).to_dict()
            quarantine_root = base / "quarantine"

            report = CleanupExecutor(quarantine_root=quarantine_root).execute(
                preview,
                CleanupConfirmation(True, (allowed,)),
                audit_path=base / "audit.jsonl",
            ).to_dict()

            self.assertFalse(candidate.exists())
            self.assertEqual("confirmed_l1_quarantine", report["mode"])
            self.assertEqual("quarantined", report["results"][0]["status"])
            self.assertEqual("quarantine_file", report["results"][0]["action"])
            self.assertEqual(
                "pathlib_replace",
                report["results"][0]["audit_event"]["execution_method"],
            )
            self.assertEqual(1, report["summary"]["quarantined"])
            summary = build_cleanup_summary(preview, report)
            self.assertEqual(1, summary["by_status"]["quarantined"])
            item = QuarantineManager(quarantine_root).list_items()[0]
            self.assertEqual(str(candidate.resolve()), item.original_path)

    def test_quarantine_mode_without_confirmation_is_still_dry_run(self) -> None:
        with TemporaryDirectory() as directory:
            base = Path(directory)
            candidate = base / "scratch.tmp"
            candidate.write_bytes(b"stay")
            preview = build_cleanup_preview(JunkScanner().scan([base])).to_dict()
            quarantine_root = base / "quarantine"

            report = CleanupExecutor(quarantine_root=quarantine_root).execute(
                preview,
                CleanupConfirmation(False, (base,)),
                audit_path=base / "audit.jsonl",
            ).to_dict()

            self.assertTrue(candidate.exists())
            self.assertFalse(quarantine_root.exists())
            self.assertEqual("would_clean", report["results"][0]["status"])
            self.assertEqual("dry_run", report["mode"])

    def test_developer_guard_blocks_quarantine_execution(self) -> None:
        with TemporaryDirectory() as directory:
            base = Path(directory)
            safe = base / "safe.tmp"
            safe.write_bytes(b"preview")
            preview = build_cleanup_preview(JunkScanner().scan([base])).to_dict()
            protected = base / "node_modules" / "pkg" / "cache.tmp"
            protected.parent.mkdir(parents=True)
            protected.write_bytes(b"developer")
            preview["top_candidates"][0]["path"] = str(protected)

            report = CleanupExecutor(quarantine_root=base / "quarantine").execute(
                preview,
                CleanupConfirmation(True, (base,)),
                audit_path=base / "audit.jsonl",
            ).to_dict()

            self.assertEqual("blocked", report["results"][0]["status"])
            self.assertTrue(protected.exists())


if __name__ == "__main__":
    unittest.main()
