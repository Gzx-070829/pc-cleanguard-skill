import json
import ast
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.experience import run_user_trial


class TrialRunnerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = TemporaryDirectory()
        self.base = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_default_trial_is_dry_run_and_generates_product_artifacts(self) -> None:
        root, output = self.base / ".pcg-demo", self.base / ".pcg-trial"
        result = run_user_trial(root, output)
        self.assertFalse(result["confirmed"])
        self.assertFalse(result["execution_performed"])
        for name in ("START_HERE.md", "user_summary.md", "machine_summary.json", "cleanup_report.md", "pup_insight.md"):
            self.assertTrue((output / name).is_file(), name)
        machine = json.loads((output / "machine_summary.json").read_text(encoding="utf-8"))
        self.assertGreater(machine["cleanup_candidates"], 0)
        self.assertEqual(1, machine["pup_clue_count"])

    def test_confirmed_trial_quarantines_l1_and_writes_manifest(self) -> None:
        root, output, quarantine = self.base / "demo", self.base / "trial", self.base / "quarantine"
        result = run_user_trial(root, output, confirm=True, quarantine_root=quarantine)
        self.assertTrue(result["confirmed"])
        self.assertGreater(result["machine_summary"]["quarantined_count"], 0)
        self.assertTrue((quarantine / "manifest.json").is_file())
        self.assertFalse((root / "temp/example.tmp").exists())
        self.assertIn("quarantine restore", (output / "user_summary.md").read_text(encoding="utf-8"))

    def test_confirm_requires_explicit_quarantine_root(self) -> None:
        with self.assertRaises(ValueError):
            run_user_trial(self.base / "demo", self.base / "trial", confirm=True)

    def test_experience_modules_have_no_process_or_network_imports(self) -> None:
        package = Path(__file__).resolve().parents[2] / "pc_cleanguard" / "experience"
        imports = set()
        for path in package.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module.split(".")[0])
        forbidden = {"sub" + "process", "req" + "uests", "url" + "lib", "sock" + "et"}
        self.assertTrue(forbidden.isdisjoint(imports))


if __name__ == "__main__":
    unittest.main()
