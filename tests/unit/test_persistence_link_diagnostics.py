import json
import unittest
from pathlib import Path

from pc_cleanguard.persistence import (
    build_persistence_chain_graph,
    build_persistence_link_diagnostics,
)


ROOT = Path(__file__).resolve().parents[2]


class PersistenceLinkDiagnosticsTests(unittest.TestCase):
    def test_zero_edge_is_valid_and_explained(self):
        report = {
            "report_id": "zero-edge",
            "installed_apps": [{"target_id": "app:a", "name": "Example App"}],
            "startup_items": [{"target_id": "start:x", "name": "Different Startup"}],
            "services": [], "scheduled_tasks": [],
        }
        graph = build_persistence_chain_graph(report)
        diagnostics = build_persistence_link_diagnostics(report, graph=graph)
        self.assertEqual(0, diagnostics["linked_pair_count"])
        self.assertTrue(diagnostics["zero_edge_explanation"])
        self.assertTrue(diagnostics["unlinked_nodes"])
        self.assertIn("executable_path", diagnostics["recommended_metadata"])

    def test_publisher_only_is_rejected_as_strong_entity_link(self):
        report = {
            "installed_apps": [
                {"target_id": "app:a", "name": "Alpha", "publisher": "Shared Publisher"},
                {"target_id": "app:b", "name": "Beta", "publisher": "Shared Publisher"},
            ],
            "startup_items": [], "services": [], "scheduled_tasks": [],
        }
        graph = build_persistence_chain_graph(report)
        self.assertFalse(any(edge["confidence"] == "strong" for edge in graph["edges"]))
        diagnostics = build_persistence_link_diagnostics(report, graph=graph)
        self.assertGreaterEqual(diagnostics["rejected_publisher_only"], 1)
        self.assertEqual(0, diagnostics["linked_by_publisher"])

    def test_strong_fixture_keeps_structural_edges(self):
        report = json.loads(
            (ROOT / "examples/reports/v040_persistence_strong_chain_report.json").read_text(encoding="utf-8")
        )
        graph = build_persistence_chain_graph(report)
        diagnostics = build_persistence_link_diagnostics(report, graph=graph)
        self.assertGreaterEqual(diagnostics["linked_pair_count"], 4)
        self.assertGreaterEqual(
            diagnostics["linked_by_executable_root"] + diagnostics["linked_by_command_path"] + diagnostics["linked_by_exact_path"],
            4,
        )
        self.assertEqual(0, diagnostics["execution_gating_eligible_count"])


if __name__ == "__main__":
    unittest.main()
