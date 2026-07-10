import ast
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from pc_cleanguard.cleanup import JunkScanner, ScanLimits


class JunkScannerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = TemporaryDirectory()
        self.root = Path(self.directory.name)

    def tearDown(self) -> None:
        self.directory.cleanup()

    def _file(self, relative: str, payload: bytes) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        return path

    def test_scans_explicit_directory_and_recognizes_core_candidates(self) -> None:
        self._file("scratch.tmp", b"12")
        self._file("events.log", b"123")
        self._file("failure.dmp", b"1234")
        self._file("cache/blob.bin", b"12345")
        self._file("setup.msi", b"123456")
        (self.root / "empty-folder").mkdir()

        result = JunkScanner().scan([self.root])
        categories = {candidate.category.value for candidate in result.candidates}

        self.assertEqual(
            {
                "temp_file",
                "log_file",
                "crash_dump",
                "cache_file",
                "installer_leftover",
                "empty_directory_candidate",
            },
            categories,
        )
        self.assertTrue(all(candidate.dry_run_only for candidate in result.candidates))
        self.assertTrue(
            all(candidate.requires_user_confirmation for candidate in result.candidates)
        )

    def test_requires_at_least_one_explicit_path(self) -> None:
        with self.assertRaises(ValueError):
            JunkScanner().scan([])

    def test_rejects_missing_or_non_directory_paths(self) -> None:
        with self.assertRaises(FileNotFoundError):
            JunkScanner().scan([self.root / "missing"])
        regular_file = self._file("single.tmp", b"x")
        with self.assertRaises(ValueError):
            JunkScanner().scan([regular_file])

    def test_rejects_explicit_directory_symbolic_link(self) -> None:
        with patch.object(Path, "is_symlink", return_value=True):
            with self.assertRaises(ValueError):
                JunkScanner().scan([self.root])

    def test_blocks_personal_and_code_directories(self) -> None:
        protected = (
            "Documents",
            "Desktop",
            "Pictures",
            "Videos",
            "Projects",
            "misc/example-repo",
        )
        for relative in protected:
            directory = self.root / relative
            directory.mkdir(parents=True)
            self._file(f"{relative}/private.tmp", b"private")
        (self.root / "misc" / "example-repo" / ".git").mkdir()

        result = JunkScanner().scan([self.root])
        blocked = {Path(item.path).name.casefold() for item in result.blocked_candidates}
        candidate_paths = {candidate.path.casefold() for candidate in result.candidates}

        self.assertTrue(
            {"documents", "desktop", "pictures", "videos", "projects"}.issubset(
                blocked
            )
        )
        self.assertIn("example-repo", blocked)
        self.assertTrue(all("private.tmp" not in path for path in candidate_paths))

    def test_file_count_limit_stops_scan_with_warning(self) -> None:
        for index in range(5):
            self._file(f"candidate-{index}.tmp", b"x")
        result = JunkScanner(ScanLimits(max_files=2, max_total_size_bytes=100)).scan(
            [self.root]
        )
        self.assertLessEqual(result.scanned_files, 2)
        self.assertTrue(any("file count limit" in item for item in result.warnings))

    def test_total_size_limit_stops_scan_with_warning(self) -> None:
        self._file("one.tmp", b"1234")
        self._file("two.tmp", b"5678")
        result = JunkScanner(ScanLimits(max_files=10, max_total_size_bytes=5)).scan(
            [self.root]
        )
        self.assertLessEqual(result.scanned_bytes, 5)
        self.assertTrue(any("size limit" in item for item in result.warnings))

    def test_scanner_source_has_no_content_or_mutation_calls(self) -> None:
        root = Path(__file__).resolve().parents[2]
        path = root / "pc_cleanguard" / "cleanup" / "junk_scanner.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        calls = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        forbidden = {
            "read_" + "text",
            "read_" + "bytes",
            "write_" + "text",
            "write_" + "bytes",
            "un" + "link",
            "rename",
            "rmdir",
        }
        self.assertTrue(forbidden.isdisjoint(calls))


if __name__ == "__main__":
    unittest.main()
