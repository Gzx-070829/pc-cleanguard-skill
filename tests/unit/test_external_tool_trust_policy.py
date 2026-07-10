import unittest

from pc_cleanguard.external_tools.catalog import ExternalToolType
from pc_cleanguard.external_tools.trust_policy import ToolTrustPolicy

from .test_external_tool_catalog import make_record


class ExternalToolTrustPolicyTest(unittest.TestCase):
    def test_exact_allowlist_marks_record_trusted_for_planning_only(self) -> None:
        record = make_record()
        decision = ToolTrustPolicy((record.tool_id,)).evaluate(record)
        self.assertTrue(decision.trusted)
        self.assertIn("allowlisted", decision.reason)
        self.assertFalse(decision.to_dict()["execution_authorized"])

    def test_unlisted_record_is_not_trusted(self) -> None:
        decision = ToolTrustPolicy().evaluate(make_record())
        self.assertFalse(decision.trusted)
        self.assertIn("allowlist", decision.reason)

    def test_disallowed_type_is_not_trusted_even_when_id_is_listed(self) -> None:
        record = make_record(ExternalToolType.WINGET, tool_id="example-winget")
        policy = ToolTrustPolicy(
            allowlisted_tool_ids=(record.tool_id,),
            allowed_tool_types=(ExternalToolType.OFFICIAL_UNINSTALLER,),
        )
        decision = policy.evaluate(record)
        self.assertFalse(decision.trusted)
        self.assertIn("type", decision.reason)

    def test_policy_rejects_duplicate_allowlist_ids(self) -> None:
        with self.assertRaises(ValueError):
            ToolTrustPolicy(("example-tool", "example-tool"))

    def test_policy_requires_at_least_one_allowed_type(self) -> None:
        with self.assertRaises(ValueError):
            ToolTrustPolicy(allowed_tool_types=())


if __name__ == "__main__":
    unittest.main()
