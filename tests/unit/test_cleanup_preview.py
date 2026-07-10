import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.cleanup import JunkScanner, build_cleanup_preview


class CleanupPreviewTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = TemporaryDirectory()
        self.root = Path(self.directory.name)

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_preview_counts_candidates_and_reclaimable_bytes(self) -> None:
        (self.root / "one.tmp").write_bytes(b"123")
        (self.root / "two.log").write_bytes(b"12345")
        result = JunkScanner().scan([self.root])
        preview = build_cleanup_preview(result).to_dict()

        self.assertEqual(2, preview["total_candidates"])
        self.assertEqual(8, preview["total_reclaimable_bytes"])
        self.assertEqual(1, preview["by_category"]["temp_file"]["count"])
        self.assertEqual(3, preview["by_category"]["temp_file"]["size_bytes"])
        self.assertTrue(preview["requires_confirmation"])

    def test_preview_includes_blocked_paths_and_warnings(self) -> None:
        documents = self.root / "Documents"
        documents.mkdir()
        (documents / "private.tmp").write_bytes(b"private")
        preview = build_cleanup_preview(JunkScanner().scan([self.root])).to_dict()
        self.assertEqual(1, len(preview["blocked_candidates"]))
        self.assertTrue(preview["warnings"])

    def test_top_candidates_are_sorted_by_size(self) -> None:
        (self.root / "small.tmp").write_bytes(b"1")
        (self.root / "large.log").write_bytes(b"12345")
        preview = build_cleanup_preview(
            JunkScanner().scan([self.root]), top_limit=1
        ).to_dict()
        self.assertEqual(1, len(preview["top_candidates"]))
        self.assertTrue(preview["top_candidates"][0]["path"].endswith("large.log"))
        self.assertTrue(any("top candidate limit" in item for item in preview["warnings"]))

    def test_preview_contains_no_execution_authority(self) -> None:
        (self.root / "candidate.tmp").write_bytes(b"x")
        preview = build_cleanup_preview(JunkScanner().scan([self.root])).to_dict()
        self.assertTrue(preview["dry_run_only"])
        self.assertFalse(preview["execution_authorized"])
        for candidate in preview["top_candidates"]:
            self.assertTrue(candidate["dry_run_only"])
            self.assertTrue(candidate["requires_user_confirmation"])
            self.assertNotIn("command", candidate)

    def test_cleanup_schemas_are_dry_run_and_command_free(self) -> None:
        schema_root = Path(__file__).resolve().parents[2] / "schemas"
        candidate = json.loads(
            (schema_root / "junk_candidate.schema.json").read_text(encoding="utf-8")
        )
        preview = json.loads(
            (schema_root / "cleanup_preview.schema.json").read_text(encoding="utf-8")
        )
        self.assertTrue(candidate["properties"]["dry_run_only"]["const"])
        self.assertTrue(
            candidate["properties"]["requires_user_confirmation"]["const"]
        )
        self.assertFalse(candidate["properties"]["execution_authorized"]["const"])
        self.assertTrue(preview["properties"]["dry_run_only"]["const"])
        serialized = json.dumps((candidate, preview)).casefold()
        self.assertNotIn('"command"', serialized)


if __name__ == "__main__":
    unittest.main()
