import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.quarantine import QuarantineManager, QuarantineManifest


class QuarantineManifestTest(unittest.TestCase):
    def test_manifest_round_trip_preserves_item_fields(self) -> None:
        with TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "sample.log"
            source.write_bytes(b"log")
            manager = QuarantineManager.create_quarantine(base / "quarantine")
            item = manager.quarantine_file(
                source,
                reason="reviewed log",
                evidence=({"source": "preview", "fact": "L1 log"},),
            )
            data = json.loads((manager.root / "manifest.json").read_text("utf-8"))
            manifest = QuarantineManifest.from_dict(data)

        self.assertEqual(item.item_id, manifest.items[0].item_id)
        self.assertEqual("reviewed log", manifest.items[0].reason)
        self.assertIsNone(manifest.items[0].restored_at)

    def test_unknown_item_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            manager = QuarantineManager.create_quarantine(Path(directory) / "q")
            with self.assertRaises(KeyError):
                manager.get_item("missing")


if __name__ == "__main__":
    unittest.main()
