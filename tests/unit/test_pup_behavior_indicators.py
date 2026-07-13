import unittest

from pc_cleanguard.pup import (
    build_behavior_indicators_from_report,
    render_behavior_indicator_section,
    summarize_behavior_indicators,
    validate_behavior_indicator,
)
from pc_cleanguard.reputation import build_human_review_checklist


REPORT = {
    "installed_apps": [
        {"target_id": "app:bundle", "display_name": "Example Bundle Installer", "publisher": "Unknown"},
    ],
    "startup_items": [{"target_id": "startup:1", "name": "ExampleUpdater"}],
    "services": [{"target_id": "service:1", "display_name": "Example Helper Service"}],
    "scheduled_tasks": [{"target_id": "task:1", "task_name": "Example Updater Task"}],
}


class PupBehaviorIndicatorsTest(unittest.TestCase):
    def test_builds_review_only_indicators_from_report_metadata(self):
        indicators = build_behavior_indicators_from_report(REPORT)
        kinds = {item["behavior_type"] for item in indicators}
        self.assertTrue({"bundled_installer_trace", "startup_persistence", "service_persistence", "scheduled_task_persistence"}.issubset(kinds))
        self.assertTrue(all(item["requires_human_review"] is True for item in indicators))
        self.assertTrue(all(item["execution_gating_eligible"] is False for item in indicators))
        summary = summarize_behavior_indicators(indicators)
        self.assertEqual(0, summary["execution_gating_eligible_count"])
        self.assertEqual(len(indicators), summary["behavior_indicator_count"])
        self.assertIn("人工复核", render_behavior_indicator_section(indicators))

    def test_behavior_indicators_enter_checklist_not_verdict(self):
        indicators = build_behavior_indicators_from_report(REPORT)
        checklist = build_human_review_checklist([], behavior_indicators=indicators)
        self.assertEqual(len(indicators), len(checklist["behavior_items"]))
        self.assertEqual(0, checklist["execution_gating_eligible_count"])

    def test_validator_rejects_execution_eligible_indicator(self):
        indicator = build_behavior_indicators_from_report(REPORT)[0]
        indicator["execution_gating_eligible"] = True
        with self.assertRaises(ValueError):
            validate_behavior_indicator(indicator)


if __name__ == "__main__":
    unittest.main()
