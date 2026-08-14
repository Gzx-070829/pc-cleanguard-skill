import ast
import json
import unittest
from pathlib import Path

import pc_cleanguard


ROOT = Path(__file__).resolve().parents[2]


class V041ReleaseReadinessTests(unittest.TestCase):
    def test_current_version_is_050_while_v041_assets_remain(self):
        self.assertEqual("0.5.0", pc_cleanguard.__version__)
        pyproject = ROOT / "pyproject.toml"
        if pyproject.is_file():
            self.assertIn('version = "0.5.0"', pyproject.read_text(encoding="utf-8"))

    def test_release_documents_exist(self):
        for name in (
            "windows-real-machine-quickstart.md",
            "windows-collector-compatibility.md",
            "windows-report-ingestion.md",
            "synthetic-demo-workspace.md",
            "release-v0.4.1-checklist.md",
            "v0.4.1-release-notes.md",
            "v0.4.1-public-preview.md",
        ):
            self.assertTrue((ROOT / "docs" / name).is_file(), name)

    def test_readme_documents_real_two_step_flow_and_boundaries(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for phrase in (
            "collect-windows-metadata.ps1", "windows report build", "evaluation windows",
            "Python 不自动启动 PowerShell", "ExecutionPolicy Bypass", "redacted report",
            "0 PUP match", "persistence 0 edge", "Desktop",
        ):
            self.assertIn(phrase, text)

    def test_local_evaluation_directories_are_ignored(self):
        text = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".pcg-local-evaluation/", text)
        self.assertIn(".pcg-local-evaluation-v041/", text)

    def test_new_python_modules_do_not_import_execution_or_network_stacks(self):
        forbidden = {"subprocess", "requests", "urllib", "socket", "http", "http.client"}
        paths = [
            *(ROOT / "pc_cleanguard/windows").glob("*.py"),
            *(ROOT / "pc_cleanguard/evaluation").glob("*.py"),
            ROOT / "pc_cleanguard/demo/workspace.py",
            ROOT / "pc_cleanguard/demo/acceptance.py",
            ROOT / "pc_cleanguard/persistence/diagnostics.py",
        ]
        for path in paths:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            imported = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module)
            self.assertFalse(imported.intersection(forbidden), path.name)

    def test_checked_in_evidence_never_authorizes_execution(self):
        for path in (ROOT / "data" / "reputation").glob("*.json"):
            value = json.loads(path.read_text(encoding="utf-8"))
            stack = [value]
            while stack:
                current = stack.pop()
                if isinstance(current, dict):
                    if "execution_authorized" in current:
                        self.assertIs(False, current["execution_authorized"], str(path))
                    if "execution_gating_eligible_count" in current:
                        self.assertEqual(0, current["execution_gating_eligible_count"], str(path))
                    stack.extend(current.values())
                elif isinstance(current, list):
                    stack.extend(current)


if __name__ == "__main__":
    unittest.main()
