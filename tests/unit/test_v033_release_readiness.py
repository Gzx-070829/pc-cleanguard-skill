import io, json, unittest
from contextlib import redirect_stdout
from pathlib import Path

import pc_cleanguard
from pc_cleanguard.cli import main

ROOT = Path(__file__).resolve().parents[2]


class V033ReleaseReadinessTest(unittest.TestCase):
    def test_current_version_and_cli_are_042_while_v033_assets_remain(self):
        self.assertEqual("0.4.2", pc_cleanguard.__version__)
        output=io.StringIO()
        with redirect_stdout(output), self.assertRaises(SystemExit): main(["--version"])
        self.assertEqual("PC CleanGuard Skill 0.4.2", output.getvalue().strip())

    def test_release_docs_exist(self):
        for name in ("docs/release-v0.3.3-checklist.md", "docs/v0.3.3-public-preview.md", "docs/v0.3.3-release-notes.md", "docs/v0.3.3-preview-notes.md"):
            self.assertTrue((ROOT/name).is_file(),name)

    def test_showcase_exists_and_is_safe(self):
        base=ROOT/"examples/showcase/v0.3.3"
        names=("README.md","START_HERE.md","user_friendly_summary.md","machine_summary.json","evidence_coverage.md","corroboration_summary.md","no_match_report.md","match_report.md","false_positive_feedback_template.md","safety_notice.md")
        for name in names: self.assertTrue((base/name).is_file(),name)
        machine=json.loads((base/"machine_summary.json").read_text(encoding="utf-8")); self.assertEqual(0,machine["execution_gating_eligible_count"])

    def test_cn_win_evidence_reaches_target_and_is_safe(self):
        records=json.loads((ROOT/"data/reputation/evidence_pack.cn_win.zh-CN.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(records),10)
        self.assertTrue(all(item["execution_authorized"] is False for item in records))
        required=("source_url","source_title","source_date","evidence_summary","version_or_time_scope","affected_component","guard_reason","uncertainty_notes","why_not_execution_authorization","recommended_human_checks")
        self.assertTrue(all(all(item.get(field) for field in required) for item in records))
        self.assertFalse(any(item["source_type"]=="user_blocklist_or_forum_list" for item in records))


if __name__ == "__main__": unittest.main()
