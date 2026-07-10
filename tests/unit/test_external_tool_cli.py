import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.cli import main
from pc_cleanguard.external_tools import ExternalToolType

from .test_external_tool_catalog import make_record
from .test_external_tool_recommender import cleanup_plan


class ExternalToolCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.input_path = self.root / "recommendation-input.json"
        self.output_path = self.root / "recommendations.json"
        record = make_record(
            ExternalToolType.OFFICIAL_UNINSTALLER,
            tool_id="example-official-tool",
        )
        self.input_path.write_text(
            json.dumps(
                {
                    "cleanup_plan": cleanup_plan(),
                    "catalog": {"records": [record.to_dict()]},
                    "allowlisted_tool_ids": [record.tool_id],
                    "installed_apps": [],
                    "governance_decisions": [],
                    "evidence": [],
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.directory.cleanup()

    def _run(self, *extra: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        arguments = [
            "tools",
            "recommend",
            "--input",
            str(self.input_path),
            "--output",
            str(self.output_path),
            *extra,
        ]
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(arguments)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_tools_recommend_writes_json(self) -> None:
        code, stdout, stderr = self._run()
        self.assertEqual(0, code)
        self.assertEqual("", stderr)
        output = json.loads(self.output_path.read_text(encoding="utf-8"))
        self.assertEqual(1, len(output["recommendations"]))
        self.assertTrue(output["recommendations"][0]["plan_only"])
        self.assertFalse(output["execution_authorized"])
        self.assertEqual(1, json.loads(stdout)["recommendations"])

    def test_tools_recommend_does_not_overwrite_by_default(self) -> None:
        self.output_path.write_text("preserve", encoding="utf-8")
        code, _, stderr = self._run()
        self.assertEqual(2, code)
        self.assertIn("exists", stderr.casefold())
        self.assertEqual("preserve", self.output_path.read_text(encoding="utf-8"))

    def test_tools_recommend_can_explicitly_overwrite(self) -> None:
        self.output_path.write_text("old", encoding="utf-8")
        code, _, _ = self._run("--overwrite")
        self.assertEqual(0, code)
        self.assertIn(
            "recommendations",
            json.loads(self.output_path.read_text(encoding="utf-8")),
        )

    def test_tools_recommend_requires_explicit_paths(self) -> None:
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as context:
            main(["tools", "recommend"])
        self.assertEqual(2, context.exception.code)


if __name__ == "__main__":
    unittest.main()
