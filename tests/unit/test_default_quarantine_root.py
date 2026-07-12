import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.cleanup import get_default_quarantine_root


class DefaultQuarantineRootTest(unittest.TestCase):
    def test_default_is_dot_pcg_quarantine_under_base(self) -> None:
        with TemporaryDirectory() as directory:
            self.assertEqual(Path(directory).resolve() / ".pcg-quarantine", get_default_quarantine_root(directory))


if __name__ == "__main__":
    unittest.main()
