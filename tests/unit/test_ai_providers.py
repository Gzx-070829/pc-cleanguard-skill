import ast
import unittest
from pathlib import Path

from pc_cleanguard.ai import DryRunPromptProvider, MockAIProvider, SAFETY_NOTICE


ROOT = Path(__file__).resolve().parents[2]


def _report() -> dict:
    return {
        "normalized_counts": {"total_targets": 3},
        "decisions": [
            {
                "classification": "KEEP",
                "risk_level": "LOW",
                "permission_level": "LEVEL_0_READ_ONLY",
                "required_confirmation": False,
            },
            {
                "classification": "ASK_USER",
                "risk_level": "MEDIUM",
                "permission_level": "LEVEL_0_READ_ONLY",
                "required_confirmation": True,
            },
            {
                "classification": "BLOCK",
                "risk_level": "CRITICAL",
                "permission_level": "LEVEL_5_FORBIDDEN",
                "blocked_by_hard_rule": True,
            },
        ],
    }


class AIProvidersTest(unittest.TestCase):
    def test_mock_provider_generates_chinese_markdown(self) -> None:
        output = MockAIProvider().generate("safe prompt", _report())
        self.assertIn("# PC CleanGuard AI 报告解释", output)
        self.assertIn(SAFETY_NOTICE, output)
        self.assertIn("需要用户确认", output)

    def test_mock_provider_summarizes_without_echoing_free_text(self) -> None:
        report = _report()
        report["decisions"][0]["reason"] = "UNTRUSTED_FREE_TEXT"
        output = MockAIProvider().generate("safe prompt", report)
        self.assertNotIn("UNTRUSTED_FREE_TEXT", output)
        self.assertIn("`KEEP`：1", output)

    def test_dry_run_provider_returns_prompt_verbatim(self) -> None:
        prompt = "# bounded local prompt"
        self.assertEqual(prompt, DryRunPromptProvider().generate(prompt, _report()))

    def test_dry_run_provider_rejects_empty_prompt(self) -> None:
        with self.assertRaises(ValueError):
            DryRunPromptProvider().generate("", _report())

    def test_providers_do_not_mutate_report(self) -> None:
        report = _report()
        original = repr(report)
        MockAIProvider().generate("safe", report)
        DryRunPromptProvider().generate("safe", report)
        self.assertEqual(original, repr(report))

    def test_ai_and_cli_modules_have_no_transport_process_or_environment_access(self) -> None:
        imports = set()
        calls = set()
        attributes = set()
        paths = list((ROOT / "pc_cleanguard" / "ai").glob("*.py"))
        paths.append(ROOT / "pc_cleanguard" / "cli.py")
        for path in paths:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module.split(".")[0])
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        calls.add(node.func.id)
                    elif isinstance(node.func, ast.Attribute):
                        calls.add(node.func.attr)
                elif isinstance(node, ast.Attribute):
                    attributes.add(node.attr)
        forbidden_imports = {
            first + second
            for first, second in (
                ("sub", "process"),
                ("req", "uests"),
                ("url", "lib"),
                ("sock", "et"),
            )
        }
        self.assertTrue(forbidden_imports.isdisjoint(imports))
        self.assertTrue({"system", "popen", "Popen", "run"}.isdisjoint(calls))
        self.assertTrue({"getenv", "environ"}.isdisjoint(attributes | calls))


if __name__ == "__main__":
    unittest.main()
