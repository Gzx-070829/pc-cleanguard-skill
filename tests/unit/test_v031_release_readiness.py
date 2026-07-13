import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import pc_cleanguard
from pc_cleanguard.cli import main


ROOT = Path(__file__).resolve().parents[2]


class V031ReleaseReadinessTest(unittest.TestCase):
    def test_version_and_cli_are_031(self):
        self.assertEqual("0.3.1", pc_cleanguard.__version__)
        output = io.StringIO()
        with redirect_stdout(output), self.assertRaises(SystemExit) as context:
            main(["--version"])
        self.assertEqual(0, context.exception.code)
        self.assertEqual("PC CleanGuard Skill 0.3.1", output.getvalue().strip())

    def test_release_documents_and_showcase_exist(self):
        required = [
            "docs/release-v0.3.1-checklist.md",
            "docs/v0.3.1-public-preview.md",
            "docs/v0.3.1-release-notes.md",
            "examples/showcase/v0.3.1/README.md",
            "examples/showcase/v0.3.1/START_HERE.md",
            "examples/showcase/v0.3.1/user_summary.md",
            "examples/showcase/v0.3.1/machine_summary.json",
            "examples/showcase/v0.3.1/pup_insight.md",
            "examples/showcase/v0.3.1/behavior_indicators.md",
            "examples/showcase/v0.3.1/cn_evidence_summary.md",
            "examples/showcase/v0.3.1/cn_source_matrix.md",
            "examples/showcase/v0.3.1/cn_candidate_sources.md",
            "examples/showcase/v0.3.1/adversarial_safety_summary.md",
        ]
        for relative in required:
            self.assertTrue((ROOT / relative).is_file(), relative)
        machine = json.loads((ROOT / "examples/showcase/v0.3.1/machine_summary.json").read_text(encoding="utf-8"))
        self.assertEqual(0, machine["execution_gating_eligible_count"])
        self.assertFalse(machine["execution_authorized"])

    def test_checked_in_reputation_json_never_authorizes_execution(self):
        for path in (ROOT / "data/reputation").glob("*.json"):
            payload = json.loads(path.read_text(encoding="utf-8"))
            text = json.dumps(payload, ensure_ascii=False).lower()
            self.assertNotIn('"execution_authorized": true', text, path.name)


if __name__ == "__main__":
    unittest.main()
