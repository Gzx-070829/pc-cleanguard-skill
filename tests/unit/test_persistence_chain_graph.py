import json, unittest
from pathlib import Path

from pc_cleanguard.persistence.graph import build_persistence_chain_graph


class PersistenceGraphTest(unittest.TestCase):
    def test_no_match_still_reports_missing_metadata(self):
        graph = build_persistence_chain_graph({"report_id": "r0", "installed_apps": [{"display_name": "Example"}]})
        self.assertGreater(graph["risk_summary"]["missing_metadata_count"], 0)
        self.assertEqual(0, graph["execution_gating_eligible_count"])

    def test_evidence_and_behavior_edges_never_authorize(self):
        report = {"installed_apps": [{"target_id": "app:a", "display_name": "Alpha"}]}
        matches = [{"target_id": "app:a", "matched_record_id": "ev1", "mapping_type": "direct_entity", "source_title": "Public source"}]
        behaviors = [{"target_id": "app:a", "behavior_type": "startup_persistence"}]
        graph = build_persistence_chain_graph(report, matches, behaviors)
        self.assertTrue({"evidence_match", "behavior_corroborates"} <= {e["edge_type"] for e in graph["edges"]})
        self.assertFalse(any(e["execution_authorized"] for e in graph["edges"]))

    def test_three_fixtures_have_expected_review_strength(self):
        base = Path(__file__).parents[1] / "fixtures/reports"
        graphs = {}
        for kind in ("no_match", "weak_chain", "strong_chain"):
            report = json.loads((base / f"v040_persistence_{kind}_report.json").read_text(encoding="utf-8"))
            graphs[kind] = build_persistence_chain_graph(report)
            self.assertFalse(graphs[kind]["execution_authorized"])
        self.assertNotEqual("strong_review_signal", graphs["weak_chain"]["risk_summary"]["review_signal"])
        self.assertIn("weak_name_overlap", {edge["edge_type"] for edge in graphs["weak_chain"]["edges"]})
        self.assertEqual("strong_review_signal", graphs["strong_chain"]["risk_summary"]["review_signal"])
        self.assertGreater(graphs["no_match"]["risk_summary"]["missing_metadata_count"], 0)
