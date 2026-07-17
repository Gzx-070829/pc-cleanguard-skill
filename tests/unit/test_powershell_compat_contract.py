import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WINDOWS_SCRIPTS = ROOT / "scripts" / "windows"


class PowerShellCompatibilityContractTests(unittest.TestCase):
    def test_new_scripts_do_not_use_powershell_7_only_constructs(self):
        for name in (
            "collect-windows-metadata.ps1",
            "collector-compat.ps1",
            "collector-doctor.ps1",
        ):
            text = (WINDOWS_SCRIPTS / name).read_text(encoding="utf-8")
            compact = text.replace(" ", "").casefold()
            self.assertNotIn("??", text, name)
            self.assertNotIn("foreach-object-parallel", compact, name)
            self.assertNotIn("convertfrom-json-ashtable", compact, name)
            self.assertNotIn("?\n", text, name)

    def test_output_encoding_is_explicit_utf8_without_bom(self):
        compat = (WINDOWS_SCRIPTS / "collector-compat.ps1").read_text(encoding="utf-8")
        self.assertIn("UTF8Encoding", compat)
        self.assertIn("WriteAllText", compat)
        self.assertIn("$false", compat)
        for name in ("collect-windows-metadata.ps1", "collector-doctor.ps1"):
            text = (WINDOWS_SCRIPTS / name).read_text(encoding="utf-8")
            self.assertIn("Write-PcgUtf8Json", text, name)

    def test_scheduled_task_unavailability_is_structured_unsupported(self):
        text = (WINDOWS_SCRIPTS / "collect-windows-metadata.ps1").read_text(encoding="utf-8")
        self.assertIn("Get-ScheduledTask", text)
        self.assertIn('"unsupported"', text)
        self.assertIn("cmdlet_unavailable", text)

    def test_legacy_collectors_run_without_inherited_strict_mode(self):
        text = (WINDOWS_SCRIPTS / "collect-windows-metadata.ps1").read_text(encoding="utf-8")
        self.assertIn("Set-StrictMode -Off", text)
        self.assertIn("& $collectorScript", text)

    def test_doctor_reports_process_policy_without_changing_it(self):
        text = (WINDOWS_SCRIPTS / "collector-doctor.ps1").read_text(encoding="utf-8")
        self.assertIn("Get-ExecutionPolicy", text)
        self.assertIn("process_only", text)
        self.assertNotIn("Set-ExecutionPolicy", text)


if __name__ == "__main__":
    unittest.main()
