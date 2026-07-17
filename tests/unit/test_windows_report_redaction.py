import copy
import os
import unittest
from unittest.mock import patch

from pc_cleanguard.windows.report_redaction import redact_windows_report


class WindowsReportRedactionTests(unittest.TestCase):
    def test_redacts_identity_values_but_preserves_product_structure(self):
        report = {
            "source_kind": "windows_collector_raw",
            "privacy_mode": "offline",
            "device_name": "WORKSTATION-42",
            "installed_apps": [{
                "target_id": "app:1",
                "name": "Example Product",
                "publisher": "Example Publisher",
                "install_location": r"C:\Users\alice\AppData\Local\Example Product\bin",
                "support_email": "alice@example.com",
                "api_token": "abcdefghijklmnopqrstuvwxyz0123456789",
            }],
            "startup_items": [{"target_id": "start:1", "name": "Example", "command": r"\\WORKSTATION-42\Users\alice\Example Product\app.exe"}],
            "services": [],
            "scheduled_tasks": [],
            "redaction_summary": {},
        }
        original = copy.deepcopy(report)
        with patch.dict(os.environ, {"COMPUTERNAME": "WORKSTATION-42", "USERNAME": "alice"}, clear=False):
            redacted, summary = redact_windows_report(report)

        self.assertEqual(original, report)
        encoded = str(redacted)
        self.assertNotIn("alice", encoded.casefold())
        self.assertNotIn("WORKSTATION-42", encoded)
        self.assertNotIn("alice@example.com", encoded)
        self.assertNotIn("abcdefghijklmnopqrstuvwxyz0123456789", encoded)
        self.assertEqual(
            r"C:\Users\<USER>\AppData\Local\Example Product\bin",
            redacted["installed_apps"][0]["install_location"],
        )
        self.assertEqual("Example Product", redacted["installed_apps"][0]["name"])
        self.assertEqual("Example Publisher", redacted["installed_apps"][0]["publisher"])
        self.assertEqual("windows_collector_redacted", redacted["source_kind"])
        self.assertGreaterEqual(summary["redacted_value_count"], 5)
        self.assertFalse(summary["reversible_mapping_created"])

    def test_summary_contains_counts_only_not_original_values(self):
        report = {
            "source_kind": "windows_collector_raw",
            "privacy_mode": "offline",
            "installed_apps": [{"target_id": "app:1", "name": "Product", "path": r"C:\Users\secret-user\Product"}],
            "startup_items": [], "services": [], "scheduled_tasks": [], "redaction_summary": {},
        }
        _, summary = redact_windows_report(report)
        self.assertNotIn("secret-user", str(summary))
        self.assertIn("redaction_counts", summary)


if __name__ == "__main__":
    unittest.main()
