import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = {
    "startup": ROOT / "scripts" / "windows" / "collect_startup_items.ps1",
    "services": ROOT / "scripts" / "windows" / "collect_services.ps1",
    "tasks": ROOT / "scripts" / "windows" / "collect_scheduled_tasks.ps1",
}


class WindowsCollectorsPr6ScriptSafetyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = {name: path.read_text(encoding="utf-8") for name, path in SCRIPTS.items()}
        cls.lower = {name: text.casefold() for name, text in cls.text.items()}

    def test_all_three_scripts_exist(self) -> None:
        self.assertTrue(all(path.is_file() for path in SCRIPTS.values()))

    def test_all_scripts_declare_read_only_collector(self) -> None:
        for name, text in self.lower.items():
            with self.subTest(name=name):
                self.assertIn("read-only collector", text)

    def test_startup_collector_has_only_approved_registry_roots(self) -> None:
        expected = {
            r"hkcu:\software\microsoft\windows\currentversion\run",
            r"hkcu:\software\microsoft\windows\currentversion\runonce",
            r"hklm:\software\microsoft\windows\currentversion\run",
            r"hklm:\software\microsoft\windows\currentversion\runonce",
            r"hklm:\software\wow6432node\microsoft\windows\currentversion\run",
            r"hklm:\software\wow6432node\microsoft\windows\currentversion\runonce",
        }
        paths = set(
            re.findall(r'"((?:hkcu|hklm):\\[^"\r\n]+)"', self.lower["startup"])
        )
        self.assertEqual(expected, paths)

    def test_startup_collector_observes_startup_folders(self) -> None:
        text = self.lower["startup"]
        self.assertIn("$env:appdata", text)
        self.assertIn("$env:programdata", text)
        self.assertIn("get-childitem", text)

    def test_services_collector_uses_win32_service(self) -> None:
        self.assertIn("get-ciminstance -classname win32_service", self.lower["services"])

    def test_tasks_collector_uses_read_only_task_command(self) -> None:
        self.assertIn("get-scheduledtask", self.lower["tasks"])

    def test_all_scripts_convert_to_json_and_write_stdout(self) -> None:
        for name, text in self.lower.items():
            with self.subTest(name=name):
                self.assertIn("convertto-json", text)
                self.assertIn("write-output", text)

    def test_all_scripts_have_no_output_redirection(self) -> None:
        for name, text in self.text.items():
            with self.subTest(name=name):
                self.assertNotIn(">", text)

    def test_startup_collector_has_no_registry_or_file_mutation(self) -> None:
        self._assert_absent(
            "startup",
            "Set-ItemProperty",
            "New-ItemProperty",
            "Remove-ItemProperty",
            "Remove-Item",
            "Move-Item",
            "Rename-Item",
        )

    def test_service_collector_has_no_service_mutation(self) -> None:
        self._assert_absent(
            "services",
            "Stop-Service",
            "Start-Service",
            "Restart-Service",
            "Set-Service",
            "sc.exe",
            "net.exe",
        )

    def test_task_collector_has_no_task_mutation(self) -> None:
        self._assert_absent(
            "tasks",
            "Disable-ScheduledTask",
            "Enable-ScheduledTask",
            "Unregister-ScheduledTask",
            "Register-ScheduledTask",
            "Set-ScheduledTask",
            "Start-ScheduledTask",
            "Stop-ScheduledTask",
        )

    def test_all_scripts_have_no_process_execution(self) -> None:
        self._assert_absent_all("Start-Process", "Invoke-Expression", "Invoke-Command")

    def test_all_scripts_have_no_network_commands(self) -> None:
        self._assert_absent_all("Invoke-WebRequest", "Invoke-RestMethod", "curl")

    def test_all_scripts_have_no_file_write_commands(self) -> None:
        self._assert_absent_all("Out-File", "Set-Content", "Add-Content")

    def test_all_scripts_have_no_child_shell_commands(self) -> None:
        self._assert_absent_all("cmd.exe", "powershell.exe", "pwsh.exe")

    def test_all_scripts_have_no_output_path_parameter(self) -> None:
        self._assert_absent_all("param(", "outputpath")

    def test_pr6_does_not_collect_processes(self) -> None:
        self._assert_absent_all("Get-Process", "Win32_Process")

    def test_metadata_fields_are_present(self) -> None:
        self.assertIn("command", self.lower["startup"])
        self.assertIn("path_name", self.lower["services"])
        self.assertIn("actions_summary", self.lower["tasks"])

    def _assert_absent_all(self, *values: str) -> None:
        for name in SCRIPTS:
            self._assert_absent(name, *values)

    def _assert_absent(self, name: str, *values: str) -> None:
        for value in values:
            with self.subTest(script=name, value=value):
                self.assertNotIn(value.casefold(), self.lower[name])


if __name__ == "__main__":
    unittest.main()
