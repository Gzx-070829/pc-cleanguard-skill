import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.quarantine import QuarantineManager


class QuarantineManagerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = TemporaryDirectory()
        self.base = Path(self.directory.name)
        self.root = self.base / "quarantine"
        self.source = self.base / "scratch.tmp"
        self.source.write_bytes(b"recoverable content")

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_create_quarantine_creates_bounded_structure(self) -> None:
        manager = QuarantineManager.create_quarantine(self.root)

        self.assertEqual(self.root.resolve(), manager.root)
        self.assertTrue((self.root / "files").is_dir())
        self.assertTrue((self.root / "manifest.json").is_file())
        self.assertEqual([], manager.list_items())

    def test_quarantine_file_moves_regular_file_and_records_metadata(self) -> None:
        manager = QuarantineManager.create_quarantine(self.root)
        item = manager.quarantine_file(
            self.source,
            reason="confirmed L1 quarantine",
            evidence=({"source": "test", "fact": "explicit test file"},),
        )

        self.assertFalse(self.source.exists())
        self.assertTrue(Path(item.quarantine_path).is_file())
        self.assertEqual("active", item.status)
        self.assertEqual(len(b"recoverable content"), item.size_bytes)
        self.assertEqual(64, len(item.sha256))
        self.assertEqual(str(self.source.resolve()), item.original_path)
        self.assertEqual(item, manager.get_item(item.item_id))

    def test_restore_returns_file_and_marks_manifest(self) -> None:
        manager = QuarantineManager.create_quarantine(self.root)
        item = manager.quarantine_file(
            self.source,
            reason="test",
            evidence=({"source": "test", "fact": "restore"},),
        )

        result = manager.restore_item(item.item_id)

        self.assertTrue(self.source.is_file())
        self.assertEqual(b"recoverable content", self.source.read_bytes())
        self.assertEqual("restored", result.status)
        self.assertTrue(result.restored_at)
        self.assertFalse(Path(item.quarantine_path).exists())

    def test_restore_refuses_to_overwrite_original_path(self) -> None:
        manager = QuarantineManager.create_quarantine(self.root)
        item = manager.quarantine_file(
            self.source,
            reason="test",
            evidence=({"source": "test", "fact": "conflict"},),
        )
        self.source.write_text("replacement", encoding="utf-8")

        with self.assertRaises(FileExistsError):
            manager.restore_item(item.item_id)

        self.assertEqual("replacement", self.source.read_text(encoding="utf-8"))
        self.assertTrue(Path(item.quarantine_path).exists())

    def test_directory_input_is_rejected(self) -> None:
        manager = QuarantineManager.create_quarantine(self.root)
        directory = self.base / "folder"
        directory.mkdir()

        with self.assertRaises(ValueError):
            manager.quarantine_file(
                directory,
                reason="not a file",
                evidence=({"source": "test", "fact": "directory"},),
            )

        self.assertTrue(directory.is_dir())

    def test_protected_quarantine_root_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            QuarantineManager.create_quarantine(
                self.base / "Documents" / "quarantine"
            )


if __name__ == "__main__":
    unittest.main()
