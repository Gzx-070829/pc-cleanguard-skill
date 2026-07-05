import ast
import json
import unittest
from pathlib import Path

from pc_cleanguard.core.models import ClassificationLabel, GovernanceTarget, ObjectType
from pc_cleanguard.core.policy_engine import evaluate_target
from pc_cleanguard.windows import (
    InstalledApp,
    installed_app_to_governance_target,
    installed_app_to_scan_target_record,
    normalize_registry_app,
    normalize_registry_apps,
)


ROOT = Path(__file__).resolve().parents[2]
NOW = "2026-07-06T00:00:00Z"


class WindowsInstalledAppsTest(unittest.TestCase):
    def test_normalize_accepts_display_name(self) -> None:
        app = normalize_registry_app({"DisplayName": "Example App"})
        self.assertEqual("Example App", app.name)

    def test_normalize_accepts_collector_name(self) -> None:
        app = normalize_registry_app({"name": "Example App"})
        self.assertEqual("Example App", app.name)

    def test_missing_name_is_skipped(self) -> None:
        self.assertIsNone(normalize_registry_app({"Publisher": "Example"}))
        self.assertIsNone(normalize_registry_app({"DisplayName": "  "}))

    def test_normalize_registry_apps_skips_nameless_entries(self) -> None:
        apps = normalize_registry_apps(
            [{"DisplayName": "Example App"}, {"Publisher": "Example"}]
        )
        self.assertEqual(["Example App"], [app.name for app in apps])

    def test_identity_metadata_is_preserved(self) -> None:
        app = self._app()
        self.assertEqual("Example Publisher", app.publisher)
        self.assertEqual("1.2.3", app.version)
        self.assertEqual(r"C:\Example\App", app.install_location)
        self.assertEqual("2026-04", app.install_date)

    def test_uninstall_string_is_metadata_only(self) -> None:
        command = r"C:\Example\uninstall.exe /remove"
        app = self._app(UninstallString=command)
        self.assertEqual(command, app.uninstall_string)
        self.assertTrue(app.uninstall_available)
        self.assertNotIn(command, repr(app))

    def test_uninstall_available_requires_standard_uninstall_string(self) -> None:
        self.assertFalse(self._app(UninstallString=None).uninstall_available)
        self.assertTrue(self._app(UninstallString="example-uninstaller").uninstall_available)

    def test_quiet_string_alone_does_not_authorize_uninstall(self) -> None:
        app = self._app(UninstallString=None, QuietUninstallString="quiet-example")
        self.assertFalse(app.uninstall_available)
        self.assertEqual("quiet-example", app.quiet_uninstall_string)

    def test_registry_boolean_fields_are_normalized(self) -> None:
        app = self._app(SystemComponent=1, WindowsInstaller="true")
        self.assertTrue(app.system_component)
        self.assertTrue(app.windows_installer)

    def test_no_remove_and_no_modify_are_normalized(self) -> None:
        app = self._app(NoRemove="1", NoModify="yes")
        self.assertTrue(app.no_remove)
        self.assertTrue(app.no_modify)

    def test_estimated_size_is_normalized_to_int(self) -> None:
        self.assertEqual(12345, self._app(EstimatedSize="12,345").estimated_size_kb)

    def test_invalid_estimated_size_becomes_none(self) -> None:
        self.assertIsNone(self._app(EstimatedSize="unknown").estimated_size_kb)

    def test_app_id_is_stable(self) -> None:
        first = self._app().app_id
        second = self._app().app_id
        self.assertEqual(first, second)
        self.assertTrue(first.startswith("WINDOWS_APP:"))

    def test_app_id_does_not_contain_uninstall_string(self) -> None:
        command = "sensitive-example-command --argument"
        app = self._app(UninstallString=command)
        self.assertNotIn(command, app.app_id)
        self.assertEqual(32, len(app.app_id))

    def test_governance_target_conversion_only_constructs_target(self) -> None:
        app = self._app()
        target = installed_app_to_governance_target(app)
        self.assertIsInstance(target, GovernanceTarget)
        self.assertEqual(ObjectType.SOFTWARE, target.object_type)
        self.assertEqual(app.app_id, target.target_id)
        self.assertEqual(app.uninstall_available, target.uninstall_available)
        self.assertIsNone(target.requested_classification)

    def test_visual_cpp_runtime_remains_keep(self) -> None:
        app = normalize_registry_app(
            {
                "DisplayName": "Microsoft Visual C++ 2015-2022 Redistributable",
                "Publisher": "Microsoft Corporation",
                "UninstallString": "example-standard-entry",
            }
        )
        decision = evaluate_target(installed_app_to_governance_target(app))
        self.assertEqual(ClassificationLabel.KEEP, decision.classification)

    def test_nvidia_driver_component_remains_keep(self) -> None:
        app = normalize_registry_app(
            {
                "DisplayName": "NVIDIA Example Driver Component",
                "Publisher": "NVIDIA Corporation",
                "UninstallString": "example-standard-entry",
            }
        )
        decision = evaluate_target(installed_app_to_governance_target(app))
        self.assertEqual(ClassificationLabel.KEEP, decision.classification)

    def test_unknown_app_without_uninstaller_remains_ask_user(self) -> None:
        app = normalize_registry_app({"DisplayName": "Example Unknown Application"})
        decision = evaluate_target(installed_app_to_governance_target(app))
        self.assertEqual(ClassificationLabel.ASK_USER, decision.classification)
        self.assertNotEqual(ClassificationLabel.SAFE_REMOVE, decision.classification)

    def test_scan_target_record_matches_sqlite_insert_fields(self) -> None:
        app = self._app()
        record = installed_app_to_scan_target_record(app, "scan-1")
        self.assertEqual(
            {
                "target_id",
                "scan_id",
                "object_type",
                "name",
                "publisher",
                "version",
                "path",
                "source",
                "first_seen",
                "last_seen",
                "normalized_identity",
            },
            set(record),
        )
        self.assertEqual("scan-1", record["scan_id"])
        self.assertEqual("SOFTWARE", record["object_type"])

    def test_source_defaults_and_collector_source_are_preserved(self) -> None:
        self.assertEqual(
            "windows_registry_uninstall",
            normalize_registry_app({"DisplayName": "Example"}).source,
        )
        self.assertEqual(
            "caller_read_only_fixture",
            normalize_registry_app(
                {"DisplayName": "Example", "source": "caller_read_only_fixture"}
            ).source,
        )

    def test_raw_record_is_copied(self) -> None:
        raw = {"DisplayName": "Example App"}
        app = normalize_registry_app(raw)
        raw["DisplayName"] = "Changed"
        self.assertEqual("Example App", app.raw["DisplayName"])

    def test_normalizer_imports_no_process_or_network_modules(self) -> None:
        path = ROOT / "pc_cleanguard" / "windows" / "installed_apps.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        forbidden = {
            first + second
            for first, second in (
                ("sub", "process"),
                ("req", "uests"),
                ("url", "lib"),
                ("sock", "et"),
                ("http", ".client"),
            )
        }
        self.assertTrue(forbidden.isdisjoint(imports))

    def test_registry_sample_normalizes_all_expected_cases(self) -> None:
        raw = json.loads(
            (
                ROOT
                / "examples"
                / "scan_samples"
                / "windows_installed_apps_registry_sample.json"
            ).read_text(encoding="utf-8")
        )
        apps = normalize_registry_apps(raw)
        self.assertEqual(6, len(apps))
        self.assertTrue(any(app.publisher is None for app in apps))
        self.assertTrue(any(app.system_component for app in apps))
        self.assertTrue(any(not app.uninstall_available for app in apps))

    def test_normalized_sample_exposes_no_uninstall_command(self) -> None:
        data = json.loads(
            (
                ROOT
                / "examples"
                / "scan_samples"
                / "windows_installed_apps_normalized_sample.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(6, len(data["software_entries"]))
        for entry in data["software_entries"]:
            self.assertNotIn("uninstall_string", entry)
            self.assertIsNone(entry["winget_visible"])

    def test_scan_schema_declares_pr5_software_fields(self) -> None:
        schema = json.loads(
            (ROOT / "schemas" / "scan_result.schema.json").read_text(encoding="utf-8")
        )
        properties = schema["$defs"]["discovered_object"]["properties"]
        expected = {
            "id",
            "app_id",
            "name",
            "publisher",
            "version",
            "install_location",
            "install_date",
            "uninstall_available",
            "registry_source",
            "registry_key",
            "winget_visible",
            "source",
            "collected_at",
        }
        self.assertTrue(expected.issubset(properties))

    @staticmethod
    def _app(**overrides) -> InstalledApp:
        raw = {
            "DisplayName": "Example App",
            "Publisher": "Example Publisher",
            "DisplayVersion": "1.2.3",
            "InstallLocation": r"C:\Example\App",
            "InstallDate": "2026-04",
            "UninstallString": "example-standard-entry",
            "QuietUninstallString": None,
            "PSPath": r"HKCU:\Software\Example\App",
            "EstimatedSize": 2048,
            "SystemComponent": 0,
            "WindowsInstaller": 0,
            "NoRemove": 0,
            "NoModify": 0,
            "collected_at": NOW,
        }
        raw.update(overrides)
        return normalize_registry_app(raw)


if __name__ == "__main__":
    unittest.main()
