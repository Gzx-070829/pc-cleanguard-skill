import unittest
import io
from contextlib import redirect_stderr, redirect_stdout
from tempfile import TemporaryDirectory
from pathlib import Path

from pc_cleanguard.reputation import build_evidence_quality_summary, load_evidence_pack, render_evidence_quality_markdown, score_evidence_record_quality
from pc_cleanguard.cli import main


ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "data/reputation/evidence_pack.cn_win.zh-CN.json"


class EvidenceQualityDashboardTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = load_evidence_pack(PACK)

    def test_record_score_has_required_dimensions(self):
        score = score_evidence_record_quality(self.records[0])
        self.assertTrue({"source_completeness", "entity_clarity", "mapping_precision", "time_scope_clarity", "execution_safety", "quality_score"}.issubset(score))

    def test_summary_counts_mapping_types(self):
        summary = build_evidence_quality_summary([self.records])
        self.assertEqual(len(self.records), summary["total_records"])
        self.assertGreaterEqual(summary["installer_artifact_records"], 1)

    def test_summary_execution_gating_is_zero(self):
        self.assertEqual(0, build_evidence_quality_summary([self.records])["execution_gating_eligible_count"])

    def test_markdown_is_explanation_only(self):
        text = render_evidence_quality_markdown(build_evidence_quality_summary([self.records]))
        self.assertIn("数据质量", text)
        self.assertIn("execution_gating_eligible_count: `0`", text)

    def test_cli_writes_quality_markdown_without_overwrite(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "quality.md"
            command = ["reputation", "evidence", "quality", "--inputs", str(PACK), "--output", str(output)]
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(0, main(command))
                self.assertEqual(2, main(command))


if __name__ == "__main__":
    unittest.main()
