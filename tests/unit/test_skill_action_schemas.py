import json
import unittest
from pathlib import Path

from pc_cleanguard.skill import ACTION_NAMES, scan_from_json


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = ROOT / "schemas"


class SkillActionSchemasTest(unittest.TestCase):
    def _schema(self, name: str) -> dict:
        return json.loads((SCHEMA_ROOT / name).read_text(encoding="utf-8"))

    def test_pr10_schemas_are_valid_json_objects(self) -> None:
        for name in (
            "skill_action_request.schema.json",
            "skill_action_response.schema.json",
            "cleanup_plan.schema.json",
            "external_tool_recommendation.schema.json",
        ):
            with self.subTest(name=name):
                schema = self._schema(name)
                self.assertEqual("object", schema["type"])
                self.assertEqual(
                    "https://json-schema.org/draft/2020-12/schema",
                    schema["$schema"],
                )

    def test_request_schema_lists_exact_action_names(self) -> None:
        schema = self._schema("skill_action_request.schema.json")
        self.assertEqual(set(ACTION_NAMES), set(schema["properties"]["action"]["enum"]))

    def test_request_schema_requires_action_and_payload(self) -> None:
        schema = self._schema("skill_action_request.schema.json")
        self.assertEqual({"action", "payload"}, set(schema["required"]))
        self.assertFalse(schema["additionalProperties"])

    def test_response_schema_requires_governance_fields(self) -> None:
        schema = self._schema("skill_action_response.schema.json")
        required = set(schema["required"])
        self.assertTrue(
            {
                "requires_user_confirmation",
                "execution_level",
                "evidence",
                "execution_authorized",
            }.issubset(required)
        )
        self.assertEqual(
            "LEVEL_0_READ_ONLY",
            schema["properties"]["execution_level"]["const"],
        )
        self.assertFalse(schema["properties"]["execution_authorized"]["const"])

    def test_cleanup_plan_schema_is_plan_only(self) -> None:
        schema = self._schema("cleanup_plan.schema.json")
        self.assertEqual("plan_only", schema["properties"]["mode"]["const"])
        self.assertFalse(schema["properties"]["execution_authorized"]["const"])
        step = schema["$defs"]["review_step"]
        self.assertFalse(step["additionalProperties"])

    def test_cleanup_plan_schema_contains_no_command_property(self) -> None:
        serialized = json.dumps(self._schema("cleanup_plan.schema.json")).casefold()
        self.assertNotIn('"command"', serialized)
        self.assertNotIn('"executable"', serialized)

    def test_runtime_response_matches_response_required_fields(self) -> None:
        response = scan_from_json({}).to_dict()
        schema = self._schema("skill_action_response.schema.json")
        self.assertTrue(set(schema["required"]).issubset(response))
        self.assertFalse(response["execution_authorized"])

    def test_external_tool_recommendation_schema_is_non_executing(self) -> None:
        schema = self._schema("external_tool_recommendation.schema.json")
        properties = schema["properties"]
        self.assertTrue(properties["plan_only"]["const"])
        self.assertTrue(properties["requires_user_confirmation"]["const"])
        self.assertTrue(properties["blocked_if_untrusted"]["const"])
        self.assertFalse(properties["execution_authorized"]["const"])
        self.assertEqual("LEVEL_0_READ_ONLY", properties["execution_level"]["const"])
        serialized = json.dumps(schema).casefold()
        self.assertNotIn('"command"', serialized)
        self.assertNotIn('"arguments"', serialized)


if __name__ == "__main__":
    unittest.main()
