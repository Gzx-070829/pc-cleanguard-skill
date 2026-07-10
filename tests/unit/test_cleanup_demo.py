import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.demo.cleanup_demo import init_cleanup_demo, run_cleanup_demo


class CleanupDemoTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = TemporaryDirectory()
        self.base = Path(self.directory.name)
        self.root = self.base / ".pcg-demo"
        self.output = self.base / ".pcg-demo-output"

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_init_creates_only_bounded_demo_content(self) -> None:
        result = init_cleanup_demo(self.root)

        self.assertEqual(self.root.resolve(), Path(result["root"]))
        self.assertTrue((self.root / "temp" / "example.tmp").is_file())
        self.assertTrue((self.root / "cache" / "example.cache").is_file())
        self.assertTrue((self.root / "logs" / "example.log").is_file())
        self.assertTrue((self.root / "dumps" / "example.dmp").is_file())
        self.assertTrue((self.root / "installers" / "example.old").is_file())
        self.assertTrue((self.root / "empty").is_dir())
        self.assertTrue((self.root / "README.txt").is_file())
        self.assertTrue((self.root / ".pc-cleanguard-demo.json").is_file())

    def test_init_does_not_overwrite_existing_root_by_default(self) -> None:
        self.root.mkdir()
        preserved = self.root / "keep.txt"
        preserved.write_text("keep", encoding="utf-8")

        with self.assertRaises(FileExistsError):
            init_cleanup_demo(self.root)

        self.assertEqual("keep", preserved.read_text(encoding="utf-8"))

    def test_force_only_refreshes_a_marked_demo_root(self) -> None:
        init_cleanup_demo(self.root)
        candidate = self.root / "temp" / "example.tmp"
        candidate.write_text("changed", encoding="utf-8")

        init_cleanup_demo(self.root, force=True)

        self.assertNotEqual("changed", candidate.read_text(encoding="utf-8"))

    def test_init_rejects_protected_root(self) -> None:
        with self.assertRaises(ValueError):
            init_cleanup_demo(self.base / "Documents" / ".pcg-demo")

    def test_run_default_generates_complete_dry_run_artifacts(self) -> None:
        init_cleanup_demo(self.root)
        result = run_cleanup_demo(self.root, self.output)

        self.assertFalse(result["confirmed"])
        for name in (
            "preview.json",
            "dry_run_result.json",
            "audit.jsonl",
            "cleanup_report.md",
        ):
            self.assertTrue((self.output / name).is_file(), name)
        execution = json.loads(
            (self.output / "dry_run_result.json").read_text(encoding="utf-8")
        )
        self.assertGreater(execution["summary"]["would_clean"], 0)
        self.assertTrue((self.root / "temp" / "example.tmp").exists())
        self.assertTrue((self.root / "cache" / "example.cache").exists())
        self.assertTrue((self.root / "logs" / "example.log").exists())

    def test_confirm_deletes_only_demo_l1_files(self) -> None:
        init_cleanup_demo(self.root)
        result = run_cleanup_demo(self.root, self.output, confirm=True)

        self.assertTrue(result["confirmed"])
        self.assertFalse((self.root / "temp" / "example.tmp").exists())
        self.assertFalse((self.root / "cache" / "example.cache").exists())
        self.assertFalse((self.root / "logs" / "example.log").exists())
        self.assertTrue((self.root / "dumps" / "example.dmp").exists())
        self.assertTrue((self.root / "installers" / "example.old").exists())
        self.assertTrue((self.root / "empty").is_dir())
        execution = json.loads(
            (self.output / "dry_run_result.json").read_text(encoding="utf-8")
        )
        skipped = {
            item["category"]
            for item in execution["results"]
            if item["status"] == "skipped"
        }
        self.assertIn("crash_dump", skipped)
        self.assertIn("installer_leftover", skipped)
        self.assertIn("empty_directory_candidate", skipped)

    def test_run_requires_marker_created_by_demo_init(self) -> None:
        self.root.mkdir()
        (self.root / "untrusted.tmp").write_text("do not touch", encoding="utf-8")

        with self.assertRaises(ValueError):
            run_cleanup_demo(self.root, self.output, confirm=True)

        self.assertTrue((self.root / "untrusted.tmp").exists())

    def test_confirm_does_not_delete_user_added_file_inside_demo_root(self) -> None:
        init_cleanup_demo(self.root)
        added = self.root / "user-added.tmp"
        added.write_text("user data", encoding="utf-8")

        run_cleanup_demo(self.root, self.output, confirm=True)

        self.assertTrue(added.exists())
        execution = json.loads(
            (self.output / "dry_run_result.json").read_text(encoding="utf-8")
        )
        self.assertTrue(
            any(
                item["path"] == str(added.resolve())
                for item in json.loads(
                    (self.output / "preview.json").read_text(encoding="utf-8")
                )["blocked_candidates"]
            )
        )
        self.assertFalse(
            any(item["path"] == str(added.resolve()) for item in execution["results"])
        )

    def test_confirm_blocks_modified_manifest_file(self) -> None:
        init_cleanup_demo(self.root)
        modified = self.root / "temp" / "example.tmp"
        modified.write_text("not synthetic demo content", encoding="utf-8")

        run_cleanup_demo(self.root, self.output, confirm=True)

        self.assertTrue(modified.exists())

    def test_run_rejects_output_inside_demo_root(self) -> None:
        init_cleanup_demo(self.root)

        with self.assertRaises(ValueError):
            run_cleanup_demo(self.root, self.root / "output")


if __name__ == "__main__":
    unittest.main()
