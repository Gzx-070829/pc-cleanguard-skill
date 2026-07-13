import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.cli import main
from pc_cleanguard.reputation import (
    build_evidence_pack,
    evidence_pack_stats,
    load_evidence_candidates,
    load_evidence_pack,
    load_evidence_review_queue,
)


ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "data/reputation/evidence_pack.real.zh-CN.json"


class ReputationRealEvidencePackTest(unittest.TestCase):
    def test_checked_in_real_pack_is_reviewed_and_non_authorizing(self) -> None:
        records = load_evidence_pack(PACK)
        self.assertGreaterEqual(len(records), 5)
        self.assertTrue(all(not item["is_synthetic"] for item in records))
        self.assertTrue(all(item["execution_authorized"] is False for item in records))
        self.assertTrue(
            all(
                item["source_url"].strip()
                and item["source_title"].strip()
                and item["evidence_summary"].strip()
                for item in records
            )
        )
        stats = evidence_pack_stats(records)
        self.assertEqual(len(records), stats["real_source_count"])
        self.assertEqual(0, stats["synthetic_count"])
        self.assertEqual(0, stats["execution_gating_eligible_count"])

    def test_checked_in_pack_is_reproducible_from_reviewed_inputs(self) -> None:
        candidates = load_evidence_candidates(
            ROOT / "data/reputation/evidence_candidates.zh-CN.json"
        )
        reviews = load_evidence_review_queue(
            ROOT / "data/reputation/evidence_review_queue.zh-CN.json"
        )
        self.assertEqual(load_evidence_pack(PACK), build_evidence_pack(candidates, reviews))

    def test_pr25_runtime_has_no_network_or_process_imports(self) -> None:
        forbidden = (
            "import " + "subprocess",
            "from " + "subprocess",
            "import " + "requests",
            "import " + "urllib",
            "from " + "urllib",
            "import " + "socket",
            "import " + "http.client",
        )
        for name in ("evidence_intake.py", "evidence_review.py"):
            source = (ROOT / "pc_cleanguard/reputation" / name).read_text(encoding="utf-8")
            self.assertFalse(any(token in source for token in forbidden), name)

    def test_cli_intake_review_build_and_stats_are_offline(self) -> None:
        candidates = ROOT / "data/reputation/evidence_candidates.zh-CN.json"
        reviews = ROOT / "data/reputation/evidence_review_queue.zh-CN.json"
        with TemporaryDirectory() as directory:
            output = Path(directory) / "built.json"
            commands = [
                ["reputation", "evidence", "intake", "validate", "--input", str(candidates)],
                ["reputation", "evidence", "review", "validate", "--input", str(reviews)],
                ["reputation", "evidence", "build", "--candidates", str(candidates), "--reviews", str(reviews), "--output", str(output)],
                ["reputation", "evidence", "stats", "--input", str(PACK)],
            ]
            for command in commands:
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    self.assertEqual(0, main(command), command)
            built = load_evidence_pack(output)
            self.assertEqual(len(load_evidence_pack(PACK)), len(built))
            self.assertTrue(all(item["execution_authorized"] is False for item in built))


if __name__ == "__main__":
    unittest.main()
