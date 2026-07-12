import unittest

from pc_cleanguard.reputation import ReputationMatcher


RECORD = {
    "record_id": "r1", "software_name": "Example Synthetic App",
    "publisher": "Example Publisher", "aliases": ["Example Helper"],
    "behavior_categories": ["ad_popup"], "confidence": 0.7,
    "false_positive_risk": "high", "review_status": "needs_human_review",
    "execution_authorized": False,
}


class ReputationMatcherTest(unittest.TestCase):
    def test_alias_matches_installed_app_and_preserves_risk(self) -> None:
        report = {"installed_apps": [{"target_id": "app:1", "DisplayName": "Example Helper", "Publisher": "Example Publisher"}]}
        match = ReputationMatcher([RECORD]).match(report)[0]
        self.assertEqual("app:1", match["target_id"])
        self.assertEqual("high", match["false_positive_risk"])
        self.assertFalse(match["execution_authorized"])

    def test_publisher_assists_normalized_name_match(self) -> None:
        report = {"installed_apps": [{"name": "Example Synthetic App Agent", "publisher": "Example Publisher"}]}
        self.assertEqual(1, len(ReputationMatcher([RECORD]).match(report)))

    def test_startup_service_and_task_aliases_match(self) -> None:
        record = {**RECORD, "aliases": ["Helper Startup", "Helper Service", "Helper Task"]}
        report = {
            "startup_items": [{"name": "Helper Startup"}],
            "services": [{"display_name": "Helper Service"}],
            "scheduled_tasks": [{"task_name": "Helper Task"}],
        }
        matches = ReputationMatcher([record]).match(report)
        self.assertEqual(
            {"STARTUP_ITEM", "SERVICE", "SCHEDULED_TASK"},
            {match["target_type"] for match in matches},
        )


if __name__ == "__main__":
    unittest.main()
