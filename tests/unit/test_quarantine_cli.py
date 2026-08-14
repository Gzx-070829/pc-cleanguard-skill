import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.cli import main


class QuarantineCliTest(unittest.TestCase):
    @staticmethod
    def _run(arguments: list[str]) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(arguments)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_add_list_restore_round_trip(self) -> None:
        with TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "quarantine"
            source = base / "sample.tmp"
            source.write_bytes(b"restore me")

            add_code, add_stdout, add_stderr = self._run([
                "quarantine", "add", "--root", str(root), "--path", str(source),
                "--reason", "explicit CLI test",
            ])
            item_id = json.loads(add_stdout)["item_id"]
            list_code, list_stdout, list_stderr = self._run([
                "quarantine", "list", "--root", str(root),
            ])
            restore_code, restore_stdout, restore_stderr = self._run([
                "quarantine", "restore", "--root", str(root), "--item-id", item_id,
            ])

            self.assertEqual((0, 0, 0), (add_code, list_code, restore_code))
            self.assertEqual(
                3,
                (add_stderr + list_stderr + restore_stderr).count(
                    "Legacy compatibility interface"
                ),
            )
            self.assertEqual(1, len(json.loads(list_stdout)["items"]))
            self.assertEqual("restored", json.loads(restore_stdout)["status"])
            self.assertEqual(b"restore me", source.read_bytes())


if __name__ == "__main__":
    unittest.main()
