import json
import unittest
from pathlib import Path

from pc_cleanguard.guard import Guard

from tests.guard.helpers import context, request


ROOT = Path(__file__).resolve().parents[2]


class GuardSchemaTests(unittest.TestCase):
    def test_exactly_eight_agent_boundary_schemas_exist(self):
        schema_root = ROOT / "schemas" / "guard"
        expected = {
            "action_request.schema.json",
            "guard_context.schema.json",
            "guard_decision.schema.json",
            "consent_grant.schema.json",
            "rollback_contract.schema.json",
            "execution_contract.schema.json",
            "action_bundle.schema.json",
            "audit_event.schema.json",
        }
        self.assertEqual(expected, {path.name for path in schema_root.glob("*.json")})
        for name in expected:
            schema = json.loads((schema_root / name).read_text(encoding="utf-8"))
            self.assertEqual("https://json-schema.org/draft/2020-12/schema", schema["$schema"])
            self.assertFalse(schema.get("additionalProperties", True))

    def test_decision_schema_fixes_authorization_false(self):
        schema = json.loads(
            (ROOT / "schemas/guard/guard_decision.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(False, schema["properties"]["execution_authorized"]["const"])
        self.assertEqual(["ALLOW", "REQUIRE", "BLOCK"], schema["properties"]["disposition"]["enum"])

    def test_execution_contract_is_the_only_schema_with_true_authorization(self):
        schema_root = ROOT / "schemas" / "guard"
        true_files = []
        for path in schema_root.glob("*.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            text = json.dumps(data, sort_keys=True)
            if '"execution_authorized": {"const": true}' in text:
                true_files.append(path.name)
        self.assertEqual(["execution_contract.schema.json"], true_files)

    def test_policy_pack_is_structured_and_loadable(self):
        decision = Guard().evaluate(request(), context())
        self.assertEqual("windows-default/0.5", decision.policy_version)


if __name__ == "__main__":
    unittest.main()

