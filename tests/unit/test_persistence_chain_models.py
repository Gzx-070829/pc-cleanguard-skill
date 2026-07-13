import json, unittest
from pathlib import Path

from pc_cleanguard.persistence.models import NODE_TYPES, EDGE_TYPES, validate_edge, validate_node


class PersistenceModelsTest(unittest.TestCase):
    def test_checked_in_schemas_enforce_safe_constants(self):
        root = Path(__file__).parents[2] / "schemas"
        node_schema = json.loads((root / "persistence_chain_node.schema.json").read_text(encoding="utf-8"))
        edge_schema = json.loads((root / "persistence_chain_edge.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(False, node_schema["properties"]["execution_authorized"]["const"])
        self.assertIn("weak_name_overlap", edge_schema["properties"]["edge_type"]["enum"])

    def test_required_node_types_are_stable(self):
        self.assertTrue({"software", "startup_item", "service", "scheduled_task", "browser_homepage", "registry_run_key", "updater", "promo_component", "leftover_file"} <= NODE_TYPES)

    def test_node_and_edge_validate_as_review_only(self):
        node = validate_node({"node_id": "software:a", "node_type": "software", "label": "Example", "metadata": {}, "risk_level": "review", "requires_human_review": True, "execution_authorized": False})
        edge = validate_edge({"edge_id": "e1", "source": node["node_id"], "target": "startup:s", "edge_type": "persists_via", "confidence": "strong", "reason": "explicit path", "requires_human_review": True, "execution_authorized": False})
        self.assertFalse(edge["execution_authorized"])

    def test_execution_authorization_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_node({"node_id": "x", "node_type": "software", "label": "x", "execution_authorized": True})

    def test_action_contract_schemas_exist(self):
        base = Path(__file__).parents[2] / "schemas/skill_actions"
        for stem in ("build_persistence_chain_graph", "build_persistence_governance_plan", "build_agent_governance_preview", "validate_agent_execution_request"):
            for suffix in ("input", "output"):
                self.assertTrue((base / f"{stem}.{suffix}.schema.json").is_file())
