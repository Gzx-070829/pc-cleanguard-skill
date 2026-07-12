import unittest

from pc_cleanguard.experience import build_user_summary, render_user_summary_markdown


class UserSummaryTest(unittest.TestCase):
    def test_summary_contains_cleanup_pup_safety_and_restore_guidance(self) -> None:
        cleanup = {
            "total_candidates": 6, "total_reclaimable_bytes": 1234,
            "quarantined_count": 2, "skipped_count": 3, "blocked_count": 1,
            "top_items": [{"status": "skipped", "reason": "outside L1"}],
        }
        pup = {"match_count": 1}
        summary = build_user_summary(cleanup, pup, confirmed=True, quarantine_root="Q")
        self.assertEqual(1234, summary["reclaimable_bytes"])
        self.assertEqual(1, summary["pup_clue_count"])
        self.assertIn("不静默删除", summary["safety_boundaries"])
        self.assertIn("quarantine restore", summary["how_to_restore"])
        markdown = render_user_summary_markdown(summary)
        self.assertIn("可释放空间", markdown)
        self.assertIn("PUP 线索", markdown)
        self.assertIn("如何恢复", markdown)
        self.assertIn("outside L1", markdown)


if __name__ == "__main__":
    unittest.main()
