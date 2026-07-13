import unittest

from pc_cleanguard.reputation import build_human_review_checklist, render_human_review_checklist
from pc_cleanguard.pup import build_false_positive_feedback_template, build_source_trace


class ReputationReviewChecklistTest(unittest.TestCase):
    def test_checklist_contains_source_and_safe_review_actions(self) -> None:
        matches = [{
            "target_id": "app:1", "matched_record_id": "record:1",
            "matched_name": "Example", "match_basis": "evidence_indicator",
            "matched_indicator_type": "installer_family", "source_url": "https://example.invalid/source",
            "source_title": "Example source", "source_date": "2026-01-01",
            "false_positive_risk": "high", "why_not_execution_authorization": "review evidence only",
            "human_review_checklist": ["核对安装来源"],
        }]
        checklist = build_human_review_checklist(matches)
        markdown = render_human_review_checklist(checklist)
        self.assertIn("source_url", markdown)
        self.assertIn("report_false_positive", markdown)
        forbidden = ["delete" + " this app", "uninstall" + " this app", "修改" + "注册表"]
        self.assertFalse(any(item in markdown for item in forbidden))

    def test_source_trace_and_feedback_are_local_review_artifacts(self) -> None:
        match = {
            "target_id": "app:1", "matched_record_id": "record:1",
            "target_observed_value": "Example", "source_url": "https://example.invalid/source",
            "source_title": "Example source", "source_date": "2026-01-01",
            "mapping_type": "direct_entity", "entity_scope": "windows_desktop_software",
            "guard_reason": ["execution gating is blocked"],
            "why_not_execution_authorization": "review only",
        }
        record = {
            "record_id": "record:1", "source_title": "Example source",
            "source_url": "https://example.invalid/source", "source_date": "2026-01-01",
            "source_type": "public_vendor_behavior_article", "mapping_type": "direct_entity",
            "entity_scope": "windows_desktop_software", "relation_confidence": "medium",
            "evidence_summary": "Example summary",
        }
        trace = build_source_trace([match], [record])
        feedback = build_false_positive_feedback_template([match])
        self.assertIn("detection family 不等于", trace)
        self.assertIn("不会自动上传", feedback)


if __name__ == "__main__":
    unittest.main()
