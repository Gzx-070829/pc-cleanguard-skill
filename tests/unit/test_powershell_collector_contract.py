import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WINDOWS_SCRIPTS = ROOT / "scripts" / "windows"


class PowerShellCollectorContractTests(unittest.TestCase):
    def test_orchestrator_doctor_and_compat_files_exist(self):
        for name in (
            "collect-windows-metadata.ps1",
            "collector-compat.ps1",
            "collector-doctor.ps1",
        ):
            self.assertTrue((WINDOWS_SCRIPTS / name).is_file(), name)

    def test_orchestrator_reuses_all_existing_collectors_and_writes_manifest(self):
        text = (WINDOWS_SCRIPTS / "collect-windows-metadata.ps1").read_text(encoding="utf-8")
        for name in (
            "collect_installed_apps.ps1",
            "collect_startup_items.ps1",
            "collect_services.ps1",
            "collect_scheduled_tasks.ps1",
        ):
            self.assertIn(name, text)
        for output in (
            "installed_apps.json", "startup_items.json", "services.json",
            "scheduled_tasks.json", "collector_manifest.json", "collector_errors.json",
        ):
            self.assertIn(output, text)
        self.assertIn("try", text.casefold())
        self.assertIn("catch", text.casefold())

    def test_all_collector_scripts_avoid_mutation_network_and_external_tools(self):
        banned = re.compile(
            r"(?im)^\s*(?:set-itemproperty|new-itemproperty|remove-itemproperty|remove-item|"
            r"set-service|start-service|stop-service|register-scheduledtask|"
            r"unregister-scheduledtask|start-process|invoke-webrequest|invoke-restmethod|"
            r"curl\b|wget\b|reg\s+(?:add|delete)|sc\.exe|schtasks\.exe|winget\b|msiexec\b)"
        )
        for path in WINDOWS_SCRIPTS.glob("*.ps1"):
            self.assertIsNone(banned.search(path.read_text(encoding="utf-8")), path.name)

    def test_collected_commands_are_documented_as_metadata_not_execution(self):
        text = (WINDOWS_SCRIPTS / "collect-windows-metadata.ps1").read_text(encoding="utf-8")
        self.assertIn("metadata", text.casefold())
        self.assertIn("system_modified", text)
        self.assertIn("runtime_network_access", text)


if __name__ == "__main__":
    unittest.main()
