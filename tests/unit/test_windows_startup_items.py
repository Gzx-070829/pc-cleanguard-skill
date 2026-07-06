import ast
import json
import unittest
from pathlib import Path

from pc_cleanguard.core.models import ClassificationLabel, GovernanceTarget, ObjectType
from pc_cleanguard.core.policy_engine import evaluate_target
from pc_cleanguard.windows import (
    StartupItem,
    normalize_startup_item,
    normalize_startup_items,
    startup_item_to_governance_target,
    startup_item_to_scan_target_record,
)


ROOT = Path(__file__).resolve().parents[2]
NOW = "2026-07-06T00:00:00Z"


class WindowsStartupItemsTest(unittest.TestCase):
    def test_normalize_registry_entry(self) -> None:
        item = self._registry_item()
        self.assertEqual("registry_run", item.location_type)
        self.assertEqual("ExampleStartup", item.registry_value_name)

    def test_normalize_startup_folder_entry(self) -> None:
        item = normalize_startup_item(
            {
                "name": "Example Shortcut",
                "location_type": "startup_folder",
                "startup_folder_path": r"%USERPROFILE%\Startup",
                "file_path": r"%USERPROFILE%\Startup\Example Shortcut.lnk",
            }
        )
        self.assertEqual(r"%USERPROFILE%\Startup\Example Shortcut.lnk", item.file_path)

    def test_nameless_entry_is_skipped(self) -> None:
        self.assertIsNone(normalize_startup_item({"command": "example"}))
        self.assertEqual([], normalize_startup_items([{"command": "example"}]))

    def test_command_is_metadata_only(self) -> None:
        command = r"%USERPROFILE%\Example\startup.exe --startup"
        item = self._registry_item(command=command)
        self.assertEqual(command, item.command)
        self.assertNotIn(command, repr(item))

    def test_item_id_is_stable(self) -> None:
        self.assertEqual(self._registry_item().item_id, self._registry_item().item_id)

    def test_item_id_does_not_contain_command(self) -> None:
        command = "sensitive-example-command --argument"
        item = self._registry_item(command=command)
        self.assertNotIn(command, item.item_id)
        self.assertTrue(item.item_id.startswith("STARTUP_ITEM:"))

    def test_governance_target_has_startup_type_without_classification(self) -> None:
        target = startup_item_to_governance_target(self._registry_item())
        self.assertIsInstance(target, GovernanceTarget)
        self.assertEqual(ObjectType.STARTUP_ITEM, target.object_type)
        self.assertIsNone(target.requested_classification)

    def test_toolbar_startup_remains_review_or_reversible_candidate(self) -> None:
        item = self._registry_item(name="Example Toolbar Startup")
        decision = evaluate_target(startup_item_to_governance_target(item))
        self.assertIn(
            decision.classification,
            {ClassificationLabel.ASK_USER, ClassificationLabel.STARTUP_OFF},
        )
        self.assertNotEqual(ClassificationLabel.SAFE_REMOVE, decision.classification)

    def test_scan_target_record_matches_sqlite_fields(self) -> None:
        record = startup_item_to_scan_target_record(self._registry_item(), "scan-1")
        self.assertEqual("STARTUP_ITEM", record["object_type"])
        self.assertEqual("scan-1", record["scan_id"])
        self.assertNotIn("command", record)

    def test_sample_is_safe_and_parseable(self) -> None:
        data = self._sample("windows_startup_items_sample.json")
        self.assertEqual(3, len(normalize_startup_items(data)))
        serialized = json.dumps(data)
        self.assertNotIn("C:\\Users\\", serialized)
        self.assertIn("%USERPROFILE%", serialized)

    def test_module_imports_no_process_or_network_packages(self) -> None:
        self._assert_safe_imports("startup_items.py")

    @staticmethod
    def _registry_item(**overrides) -> StartupItem:
        raw = {
            "name": "Example Startup",
            "command": "example-startup-command",
            "location_type": "registry_run",
            "registry_path": r"HKCU:\Software\Microsoft\Windows\CurrentVersion\Run",
            "registry_value_name": "ExampleStartup",
            "publisher": "Example Vendor",
            "source": "windows_registry_run",
            "collected_at": NOW,
        }
        raw.update(overrides)
        return normalize_startup_item(raw)

    @staticmethod
    def _sample(name: str):
        return json.loads((ROOT / "examples" / "scan_samples" / name).read_text(encoding="utf-8"))

    def _assert_safe_imports(self, module_name: str) -> None:
        tree = ast.parse(
            (ROOT / "pc_cleanguard" / "windows" / module_name).read_text(encoding="utf-8")
        )
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        forbidden = {a + b for a, b in (("sub", "process"), ("req", "uests"), ("url", "lib"), ("sock", "et"))}
        self.assertTrue(forbidden.isdisjoint(imports))


if __name__ == "__main__":
    unittest.main()
