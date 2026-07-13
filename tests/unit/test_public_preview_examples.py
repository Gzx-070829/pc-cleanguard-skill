import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pc_cleanguard
from pc_cleanguard.skill import ACTION_NAMES, invoke_skill_action


ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "examples" / "skill_actions"


class PublicPreviewExamplesTest(unittest.TestCase):
    def _request(self, name: str) -> dict:
        return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))

    def test_public_preview_version_is_v032(self) -> None:
        self.assertEqual("0.3.2", pc_cleanguard.__version__)

    def test_examples_cover_every_public_action(self) -> None:
        request_paths = list(EXAMPLES.glob("*.request.json")) + list(
            EXAMPLES.glob("*_request.json")
        )
        actions = {self._request(path.name)["action"] for path in request_paths}
        self.assertEqual(set(ACTION_NAMES), actions)

    def test_scan_example_runs(self) -> None:
        response = invoke_skill_action(self._request("scan_from_json.request.json"))
        scan = response.result["scan_result"]
        self.assertEqual(1, scan["normalized_counts"]["total_targets"])
        self.assertFalse(response.execution_authorized)

    def test_explain_example_runs_offline_mock(self) -> None:
        response = invoke_skill_action(self._request("explain_report.request.json"))
        self.assertEqual("mock", response.result["provider"])
        self.assertIn("safety_notice", response.result["markdown"])
        self.assertFalse(response.execution_authorized)

    def test_cleanup_plan_example_is_confirmation_only(self) -> None:
        response = invoke_skill_action(
            self._request("build_cleanup_plan.request.json")
        )
        plan = response.result["cleanup_plan"]
        self.assertTrue(plan["requires_user_confirmation"])
        self.assertFalse(plan["execution_authorized"])
        self.assertTrue(
            all(step["requires_user_confirmation"] for step in plan["steps"])
        )
        self.assertTrue(
            all(step["execution_authorized"] is False for step in plan["steps"])
        )

    def test_write_examples_use_explicit_temp_paths(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            report_request = self._request("write_report.request.json")
            report_request["payload"]["path"] = str(root / "report.json")
            audit_request = self._request("write_audit.request.json")
            audit_request["payload"]["path"] = str(root / "audit.jsonl")

            report_response = invoke_skill_action(report_request)
            audit_response = invoke_skill_action(audit_request)

            self.assertTrue((root / "report.json").is_file())
            self.assertTrue((root / "audit.jsonl").is_file())
            self.assertFalse(report_response.execution_authorized)
            self.assertFalse(audit_response.execution_authorized)

    def test_readme_documents_all_three_entry_points(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("pc_cleanguard.cli scan", readme)
        self.assertIn("pc_cleanguard.cli explain", readme)
        self.assertIn("invoke_skill_action", readme)
        self.assertIn("v0.1.0 Public Preview", readme)


if __name__ == "__main__":
    unittest.main()
