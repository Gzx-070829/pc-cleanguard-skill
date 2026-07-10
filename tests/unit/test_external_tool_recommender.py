import unittest

from pc_cleanguard.core.models import RiskLevel
from pc_cleanguard.external_tools import (
    ExternalToolCatalog,
    ExternalToolRecord,
    ExternalToolType,
    ToolRecommender,
    ToolTrustPolicy,
)


def tool_record(
    tool_id: str,
    tool_type: ExternalToolType,
    *actions: str,
) -> ExternalToolRecord:
    return ExternalToolRecord(
        tool_id=tool_id,
        name=f"Example {tool_type.value}",
        tool_type=tool_type,
        official_website=f"https://tools.example.invalid/{tool_id}",
        license="Example License",
        supported_actions=actions or ("standard_uninstall",),
        risk_level=RiskLevel.HIGH,
        required_user_confirmation=True,
    )


def cleanup_plan() -> dict:
    return {
        "plan_id": "cleanup-plan:pr13-test",
        "mode": "plan_only",
        "execution_level": "LEVEL_0_READ_ONLY",
        "execution_authorized": False,
        "steps": [
            {
                "step_id": "review-0001",
                "target_id": "SOFTWARE:example-notes",
                "classification": "SAFE_REMOVE",
                "review_action": "REVIEW_REMOVAL_CANDIDATE",
                "blocked": False,
                "evidence": [
                    {"source": "policy_decision", "fact": "synthetic candidate"}
                ],
            },
            {
                "step_id": "review-0002",
                "target_id": "SOFTWARE:protected-example",
                "classification": "BLOCK",
                "review_action": "BLOCKED_BY_POLICY",
                "blocked": True,
                "evidence": [
                    {"source": "policy_decision", "fact": "protected target"}
                ],
            },
        ],
    }


class ExternalToolRecommenderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.official = tool_record(
            "example-official", ExternalToolType.OFFICIAL_UNINSTALLER
        )
        self.winget = tool_record(
            "example-winget", ExternalToolType.WINGET, "package_uninstall"
        )
        self.vendor = tool_record(
            "example-vendor-cleanup",
            ExternalToolType.VENDOR_CLEANUP_TOOL,
            "vendor_cleanup",
        )
        self.third_party = tool_record(
            "example-third-party",
            ExternalToolType.TRUSTED_THIRD_PARTY_UNINSTALLER,
            "review_uninstall",
        )
        self.catalog = ExternalToolCatalog(
            (self.official, self.winget, self.vendor, self.third_party)
        )
        self.installed_apps = [
            {
                "target_id": "SOFTWARE:example-notes",
                "package_id": "Example.Notes",
                "vendor_cleanup_tool_id": "example-vendor-cleanup",
            }
        ]

    def _recommender(self, *trusted: str) -> ToolRecommender:
        return ToolRecommender(self.catalog, ToolTrustPolicy(tuple(trusted)))

    def test_allowlisted_tools_are_recommended_for_matching_candidate(self) -> None:
        recommendations = self._recommender(
            "example-official",
            "example-winget",
            "example-vendor-cleanup",
            "example-third-party",
        ).recommend(cleanup_plan(), installed_apps=self.installed_apps)
        self.assertEqual(4, len(recommendations))
        self.assertTrue(all(item.trusted for item in recommendations))
        self.assertTrue(all(not item.blocked for item in recommendations))

    def test_untrusted_tool_is_returned_as_blocked_recommendation(self) -> None:
        recommendation = self._recommender().recommend(cleanup_plan())[0]
        self.assertFalse(recommendation.trusted)
        self.assertTrue(recommendation.blocked)
        self.assertTrue(recommendation.blocked_if_untrusted)

    def test_winget_requires_package_id_metadata(self) -> None:
        recommendations = self._recommender("example-winget").recommend(cleanup_plan())
        self.assertNotIn("example-winget", {item.tool_id for item in recommendations})

    def test_vendor_tool_requires_explicit_metadata_association(self) -> None:
        recommendations = self._recommender("example-vendor-cleanup").recommend(
            cleanup_plan(),
            installed_apps=[{"target_id": "SOFTWARE:example-notes"}],
        )
        self.assertNotIn(
            "example-vendor-cleanup", {item.tool_id for item in recommendations}
        )

    def test_blocked_cleanup_steps_never_match(self) -> None:
        recommendations = self._recommender("example-official").recommend(cleanup_plan())
        self.assertTrue(
            all("SOFTWARE:protected-example" not in item.matched_target_ids for item in recommendations)
        )

    def test_every_recommendation_is_confirmation_only_level_zero(self) -> None:
        recommendation = self._recommender("example-official").recommend(
            cleanup_plan()
        )[0].to_dict()
        self.assertTrue(recommendation["plan_only"])
        self.assertTrue(recommendation["requires_user_confirmation"])
        self.assertEqual("LEVEL_0_READ_ONLY", recommendation["execution_level"])
        self.assertFalse(recommendation["execution_authorized"])
        self.assertIn("matched_reason", recommendation)
        self.assertIn("notes_for_ai", recommendation)
        self.assertGreater(recommendation["confidence"], 0)

    def test_serialized_recommendation_contains_no_invocation_material(self) -> None:
        data = self._recommender("example-official").recommend(cleanup_plan())[0].to_dict()
        forbidden_keys = {"command", "arguments", "executable", "uninstall_string"}
        self.assertTrue(forbidden_keys.isdisjoint(data))

    def test_recommender_rejects_non_plan_cleanup_input(self) -> None:
        unsafe_plan = cleanup_plan()
        unsafe_plan["mode"] = "execute"
        unsafe_plan["execution_authorized"] = True
        with self.assertRaises(ValueError):
            self._recommender("example-official").recommend(unsafe_plan)


if __name__ == "__main__":
    unittest.main()
