import json
import unittest
from pathlib import Path

from pc_cleanguard.cleanup import build_cleanup_summary, validate_cleanup_preview


ROOT = Path(__file__).resolve().parents[2]
PUBLIC_DEMO = ROOT / "examples" / "public_demo"


class V02PublicDemoReleaseTest(unittest.TestCase):
    def test_public_demo_package_contains_readable_artifacts(self) -> None:
        expected = {
            "preview.json",
            "dry_run_result.json",
            "confirmed_result.json",
            "audit.jsonl",
            "cleanup_report.md",
            "README.md",
        }
        self.assertTrue(PUBLIC_DEMO.is_dir())
        self.assertTrue(expected.issubset({path.name for path in PUBLIC_DEMO.iterdir()}))
        preview = json.loads(
            (PUBLIC_DEMO / "preview.json").read_text(encoding="utf-8")
        )
        dry_run = json.loads(
            (PUBLIC_DEMO / "dry_run_result.json").read_text(encoding="utf-8")
        )
        confirmed = json.loads(
            (PUBLIC_DEMO / "confirmed_result.json").read_text(encoding="utf-8")
        )
        audit = [
            json.loads(line)
            for line in (PUBLIC_DEMO / "audit.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]

        validate_cleanup_preview(preview)
        dry_summary = build_cleanup_summary(preview, dry_run)
        confirmed_summary = build_cleanup_summary(preview, confirmed)
        self.assertGreater(preview["total_candidates"], 0)
        self.assertEqual("dry_run", dry_run["mode"])
        self.assertFalse(dry_run["confirmed"])
        self.assertEqual("confirmed_l1", confirmed["mode"])
        self.assertTrue(confirmed["confirmed"])
        self.assertTrue(audit)
        self.assertTrue(all(event["dry_run"] for event in audit))
        self.assertEqual(1, dry_summary["would_clean_count"])
        self.assertEqual(1, confirmed_summary["cleaned_count"])

    def test_cleanup_agent_flow_covers_public_v02_chain(self) -> None:
        path = ROOT / "examples" / "skill_actions" / "v0.2_cleanup_agent_flow.json"
        flow = json.loads(path.read_text(encoding="utf-8"))
        step_ids = {step["id"] for step in flow["steps"]}

        self.assertEqual("0.2", flow["schema_version"])
        self.assertTrue(flow["requires_user_confirmation"])
        self.assertFalse(flow["execution_authorized"])
        self.assertTrue(
            {
                "clean_preview",
                "clean_execute_dry_run",
                "clean_report",
                "explain",
                "skill_action_chain",
            }.issubset(step_ids)
        )

    def test_quick_try_and_release_documents_contain_release_gates(self) -> None:
        quick_try = (ROOT / "docs" / "v0.2-quick-try.md").read_text(
            encoding="utf-8"
        )
        checklist = (ROOT / "docs" / "release-v0.2.0-checklist.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("demo init-cleanup", quick_try)
        self.assertIn("demo run-cleanup", quick_try)
        self.assertIn("demo quickstart", quick_try)
        self.assertIn("clean report", quick_try)
        self.assertIn("--confirm", quick_try)
        self.assertIn("compileall", checklist)
        self.assertIn("unittest discover", checklist)
        self.assertIn("危险", checklist)
        self.assertIn("tag", checklist.casefold())

    def test_readme_points_to_public_demo_and_quick_try(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        required_links = {
            "docs/v0.2-quick-try.md",
            "docs/release-v0.2.0-checklist.md",
            "examples/public_demo/README.md",
            "examples/skill_actions/v0.2_cleanup_agent_flow.json",
        }
        for relative in required_links:
            self.assertIn(relative, readme)
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_issue_templates_exist_with_required_safety_context(self) -> None:
        issue_root = ROOT / ".github" / "ISSUE_TEMPLATE"
        expected = {
            "bug_report.yml",
            "software_rule_feedback.yml",
            "cleanup_false_positive.yml",
        }
        self.assertTrue(expected.issubset({path.name for path in issue_root.iterdir()}))
        combined = "\n".join(
            (issue_root / name).read_text(encoding="utf-8") for name in expected
        )
        self.assertIn("name:", combined)
        self.assertIn("description:", combined)
        self.assertIn("validations:", combined)
        self.assertIn("privacy", combined.casefold())
        self.assertIn("confirmation", combined.casefold())


if __name__ == "__main__":
    unittest.main()
