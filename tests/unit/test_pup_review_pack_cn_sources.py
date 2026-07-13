import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.cli import main
from pc_cleanguard.pup import build_pup_review_pack
from pc_cleanguard.skill import READ_ONLY_EXECUTION_LEVEL, invoke_skill_action


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "tests/fixtures/reputation/pr26_realistic_windows_inventory.json"
REAL_PACK = ROOT / "data/reputation/evidence_pack.real.zh-CN.json"
CN_PACK = ROOT / "data/reputation/evidence_pack.cn.zh-CN.json"
MATRIX = ROOT / "data/reputation/cn_source_matrix.zh-CN.json"
CANDIDATES = ROOT / "data/reputation/cn_candidate_sources.zh-CN.json"


class PupReviewPackCnSourcesTest(unittest.TestCase):
    def test_review_pack_contains_cn_source_artifacts_and_counts(self):
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        with TemporaryDirectory() as directory:
            output = Path(directory) / "review"
            summary = build_pup_review_pack(
                report,
                REAL_PACK,
                output,
                cn_evidence_pack=CN_PACK,
                cn_source_matrix=MATRIX,
                cn_candidate_sources=CANDIDATES,
                include_behavior_indicators=True,
            )
            for name in ("cn_source_matrix.md", "cn_candidate_sources.md", "cn_source_policy_summary.md"):
                self.assertTrue((output / name).is_file(), name)
            machine = json.loads((output / "machine_summary.json").read_text(encoding="utf-8"))
            self.assertGreater(machine["cn_source_count"], 0)
            self.assertGreater(machine["cn_candidate_only_count"], 0)
            self.assertEqual(0, machine["execution_gating_eligible_count"])
            self.assertEqual(0, summary["execution_gating_eligible_count"])
            start = (output / "START_HERE.md").read_text(encoding="utf-8")
            self.assertIn("网友名单不能直接入库", start)
            self.assertIn("历史榜不能当现代删除名单", start)

    def test_cn_source_cli_validate_stats_candidates_and_review_pack(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            commands = [
                ["reputation", "cn-source", "validate", "--input", str(MATRIX)],
                ["reputation", "cn-source", "stats", "--input", str(MATRIX)],
                ["reputation", "cn-source", "candidates", "--input", str(CANDIDATES), "--output", str(root / "candidates.json")],
                ["pup", "review-pack", "--input", str(REPORT), "--evidence-pack", str(REAL_PACK), "--cn-evidence-pack", str(CN_PACK), "--cn-source-matrix", str(MATRIX), "--output", str(root / "review"), "--include-behavior-indicators"],
            ]
            for command in commands:
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    self.assertEqual(0, main(command), command)
            self.assertTrue((root / "candidates.json").is_file())
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(2, main(commands[2]))

    def test_cn_source_skill_actions_are_level_zero(self):
        for action in ("validate_cn_source_matrix", "summarize_cn_source_matrix"):
            response = invoke_skill_action({
                "action": action,
                "payload": {"path": str(MATRIX)},
            }).to_dict()
            self.assertEqual(READ_ONLY_EXECUTION_LEVEL, response["execution_level"])
            self.assertFalse(response["execution_authorized"])
            self.assertEqual(0, response["result"]["execution_gating_eligible_count"])


if __name__ == "__main__":
    unittest.main()
