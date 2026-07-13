import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from pc_cleanguard.cli import main
from pc_cleanguard.reputation import (
    build_evidence_pack,
    evidence_pack_stats,
    load_evidence_candidates,
    load_evidence_pack,
    load_evidence_review_queue,
)


ROOT = Path(__file__).resolve().parents[2]
CANDIDATES = ROOT / "data/reputation/cn_evidence_candidates.zh-CN.json"
REVIEWS = ROOT / "data/reputation/cn_evidence_review_queue.zh-CN.json"
PACK = ROOT / "data/reputation/evidence_pack.cn.zh-CN.json"


class ReputationCnEvidencePackTest(unittest.TestCase):
    def test_cn_pack_is_reproducible_and_strictly_non_authorizing(self):
        candidates = load_evidence_candidates(CANDIDATES)
        reviews = load_evidence_review_queue(REVIEWS)
        records = load_evidence_pack(PACK)
        self.assertEqual(records, build_evidence_pack(candidates, reviews))
        self.assertGreaterEqual(len(records), 5)
        self.assertTrue(all(record["is_synthetic"] is False for record in records))
        self.assertTrue(all(record["execution_authorized"] is False for record in records))
        self.assertTrue(all(record["language"] == "zh-CN" for record in records))
        self.assertTrue(all(record["mapping_type"] == "analogical_behavior" for record in records))
        self.assertTrue(all(record["entity_scope"] in {"mobile_app", "mobile_sdk"} for record in records))
        self.assertTrue(all(record["source_url"] and record["source_title"] and record["evidence_summary"] for record in records))
        self.assertEqual(0, evidence_pack_stats(records)["execution_gating_eligible_count"])

    def test_cn_validate_and_stats_cli_are_offline(self):
        for command in ("cn-validate", "cn-stats"):
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(0, main(["reputation", "evidence", command, "--input", str(PACK)]))


if __name__ == "__main__":
    unittest.main()
