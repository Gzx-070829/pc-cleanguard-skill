import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "windows" / "collect_installed_apps.ps1"


class WindowsCollectorScriptSafetyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = SCRIPT_PATH.read_text(encoding="utf-8")
        cls.lower_script = cls.script.casefold()

    def test_collector_script_exists(self) -> None:
        self.assertTrue(SCRIPT_PATH.is_file())

    def test_script_declares_read_only_collector(self) -> None:
        self.assertIn("read-only collector", self.lower_script)
        self.assertIn("does not uninstall", self.lower_script)

    def test_script_reads_all_and_only_approved_registry_roots(self) -> None:
        expected = {
            r"hklm:\software\microsoft\windows\currentversion\uninstall\*",
            r"hklm:\software\wow6432node\microsoft\windows\currentversion\uninstall\*",
            r"hkcu:\software\microsoft\windows\currentversion\uninstall\*",
        }
        paths = set(re.findall(r'"((?:hklm|hkcu):\\[^"\r\n]+)"', self.lower_script))
        self.assertEqual(expected, paths)

    def test_script_uses_get_item_property(self) -> None:
        self.assertIn("get-itemproperty", self.lower_script)

    def test_script_uses_convert_to_json(self) -> None:
        self.assertIn("convertto-json", self.lower_script)

    def test_script_outputs_json_to_stdout(self) -> None:
        self.assertIn("write-output", self.lower_script)
        self.assertNotIn(">", self.script)

    def test_script_has_no_set_item_property(self) -> None:
        self._assert_absent("Set-ItemProperty")

    def test_script_has_no_new_item_property(self) -> None:
        self._assert_absent("New-ItemProperty")

    def test_script_has_no_remove_item_or_property(self) -> None:
        self._assert_absent("Remove-ItemProperty")
        self._assert_absent("Remove-Item")

    def test_script_has_no_process_start_or_expression_execution(self) -> None:
        self._assert_absent("Start-Process")
        self._assert_absent("Invoke-Expression")

    def test_script_has_no_remote_command_execution(self) -> None:
        self._assert_absent("Invoke-Command")

    def test_script_has_no_web_commands(self) -> None:
        self._assert_absent("Invoke-WebRequest")
        self._assert_absent("Invoke-RestMethod")
        self._assert_absent("curl")

    def test_script_has_no_winget_uninstall(self) -> None:
        self._assert_absent("winget uninstall")

    def test_script_has_no_service_commands(self) -> None:
        self._assert_absent("Stop-Service")
        self._assert_absent("Set-Service")

    def test_script_has_no_scheduled_task_commands(self) -> None:
        self._assert_absent("Disable-ScheduledTask")
        self._assert_absent("Unregister-ScheduledTask")

    def test_script_has_no_file_writing_commands(self) -> None:
        self._assert_absent("Out-File")
        self._assert_absent("Set-Content")
        self._assert_absent("Add-Content")

    def test_script_has_no_child_shell_commands(self) -> None:
        self._assert_absent("cmd.exe")
        self._assert_absent("powershell.exe")

    def test_script_has_no_external_tool_commands(self) -> None:
        self._assert_absent("winget")
        self._assert_absent("defender")

    def test_script_has_no_output_path_parameter(self) -> None:
        self._assert_absent("param(")
        self._assert_absent("outputpath")

    def test_script_command_surface_is_allowlisted(self) -> None:
        expected = {
            "Get-Date",
            "Get-ItemProperty",
            "Where-Object",
            "ForEach-Object",
            "ConvertTo-Json",
            "Write-Output",
        }
        command_pattern = re.compile(
            r"\b(?:Get-Date|Get-ItemProperty|Where-Object|ForEach-Object|"
            r"ConvertTo-Json|Write-Output)\b",
            re.IGNORECASE,
        )
        self.assertEqual(expected, {match.group(0) for match in command_pattern.finditer(self.script)})

    def _assert_absent(self, text: str) -> None:
        self.assertNotIn(text.casefold(), self.lower_script)


if __name__ == "__main__":
    unittest.main()
