import io, json, tempfile, unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

from pc_cleanguard.persistence.graph import build_persistence_chain_graph
from pc_cleanguard.persistence.render import render_persistence_chain_markdown, render_persistence_chain_mermaid
from pc_cleanguard.cli import main


class PersistenceRenderTest(unittest.TestCase):
    def test_markdown_and_mermaid_are_review_only(self):
        graph = build_persistence_chain_graph({"installed_apps": [{"target_id": "a", "display_name": "Example"}]})
        self.assertIn("持久化链路", render_persistence_chain_markdown(graph))
        mermaid = render_persistence_chain_mermaid(graph)
        self.assertIn("flowchart", mermaid)
        self.assertIn("review-only", mermaid)

    def test_cli_graph_and_plan_write_explicit_outputs(self):
        fixture = Path(__file__).parents[1] / "fixtures/reports/v040_persistence_strong_chain_report.json"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); graph_json = root / "graph.json"
            with redirect_stdout(io.StringIO()):
                self.assertEqual(0, main(["persistence", "graph", "--input", str(fixture), "--output", str(root / "graph.md"), "--json-output", str(graph_json)]))
                self.assertEqual(0, main(["persistence", "plan", "--graph", str(graph_json), "--output", str(root / "plan.md"), "--json-output", str(root / "plan.json")]))
            self.assertTrue((root / "plan.json").is_file())

    def test_cli_agent_preview_and_guard(self):
        fixture = Path(__file__).parents[1] / "fixtures/reports/v040_persistence_no_match_report.json"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); request = root / "request.json"
            request.write_text(json.dumps({"action":"disable service"}), encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(0, main(["agent", "governance-preview", "--input", str(fixture), "--output", str(root / "preview.json")]))
                self.assertEqual(0, main(["agent", "validate-request", "--input", str(request), "--output", str(root / "validation.json")]))
            result = json.loads((root / "validation.json").read_text(encoding="utf-8"))
            self.assertEqual("blocked", result["status"])

    def test_cli_does_not_overwrite_by_default(self):
        fixture = Path(__file__).parents[1] / "fixtures/reports/v040_persistence_no_match_report.json"
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); md=root/"graph.md"; js=root/"graph.json"
            with redirect_stdout(io.StringIO()): self.assertEqual(0,main(["persistence","graph","--input",str(fixture),"--output",str(md),"--json-output",str(js)]))
            with redirect_stderr(io.StringIO()): self.assertEqual(2,main(["persistence","graph","--input",str(fixture),"--output",str(md),"--json-output",str(js)]))
