import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class CnWinPupReviewBacklogTest(unittest.TestCase):
    def test_candidate_files_are_nonempty_arrays(self):
        for name in ("cn_win_pup_source_candidates.zh-CN.json", "cn_win_pup_evidence_candidates.zh-CN.json"):
            data = json.loads((ROOT / "data/reputation" / name).read_text(encoding="utf-8"))
            self.assertIsInstance(data, list)
            self.assertTrue(data)

    def test_backlog_records_reviewer_decision_and_guard(self):
        data = json.loads((ROOT / "data/reputation/cn_win_pup_review_backlog.zh-CN.json").read_text(encoding="utf-8"))
        self.assertTrue(data)
        self.assertTrue(all(item.get("reviewer_decision") and item.get("guard_reason") for item in data))

    def test_community_sources_are_not_approved(self):
        data = json.loads((ROOT / "data/reputation/cn_win_pup_source_candidates.zh-CN.json").read_text(encoding="utf-8"))
        self.assertFalse(any(item.get("source_type") == "community_multi_report" and item.get("candidate_status") == "approved" for item in data))

    def test_backlog_never_authorizes_execution(self):
        data = json.loads((ROOT / "data/reputation/cn_win_pup_review_backlog.zh-CN.json").read_text(encoding="utf-8"))
        self.assertTrue(all(item.get("execution_authorized") is False for item in data))


if __name__ == "__main__":
    unittest.main()
