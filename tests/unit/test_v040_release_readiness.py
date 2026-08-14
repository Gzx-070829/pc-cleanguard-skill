import unittest
from pathlib import Path
import pc_cleanguard


ROOT = Path(__file__).parents[2]


class V040ReleaseReadinessTest(unittest.TestCase):
    def test_current_version_is_042_while_v040_release_docs_remain(self):
        self.assertEqual("0.4.2", pc_cleanguard.__version__)
        for name in ("docs/release-v0.4.0-checklist.md", "docs/v0.4.0-public-preview.md", "docs/v0.4.0-release-notes.md", "docs/v0.4.0-safety-boundaries.md", "docs/v0.4.0-agent-integration-preview.md"):
            self.assertTrue((ROOT / name).is_file(), name)

    def test_positioning_is_present(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("持久化链路治理", text)
        self.assertIn("Persistence Chain Governance", text)
