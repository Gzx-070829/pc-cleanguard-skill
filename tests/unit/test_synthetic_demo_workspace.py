import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pc_cleanguard.demo.workspace import (
    SYNTHETIC_MANIFEST_NAME,
    create_synthetic_workspace,
    dedicated_synthetic_temp_root,
    verify_synthetic_workspace,
)


class SyntheticDemoWorkspaceTests(unittest.TestCase):
    def test_workspace_is_randomized_under_dedicated_temp_root_and_verifies(self):
        workspace = create_synthetic_workspace()
        root = Path(workspace["workspace_root"])
        self.assertTrue(root.is_relative_to(dedicated_synthetic_temp_root()))
        self.assertTrue((root / SYNTHETIC_MANIFEST_NAME).is_file())
        verified = verify_synthetic_workspace(root, workspace["nonce"])
        self.assertTrue(verified["synthetic_only"])
        self.assertEqual(set(workspace["expected_files"]), set(verified["expected_files"]))

    def test_nonce_and_hash_mismatch_fail_closed(self):
        workspace = create_synthetic_workspace()
        root = Path(workspace["workspace_root"])
        with self.assertRaises(ValueError):
            verify_synthetic_workspace(root, "wrong-nonce")
        first = root / workspace["expected_files"][0]
        first.write_bytes(first.read_bytes() + b"tampered")
        with self.assertRaises(ValueError):
            verify_synthetic_workspace(root, workspace["nonce"])

    def test_unknown_file_is_rejected(self):
        workspace = create_synthetic_workspace()
        root = Path(workspace["workspace_root"])
        (root / "unknown.tmp").write_text("not registered", encoding="utf-8")
        with self.assertRaises(ValueError):
            verify_synthetic_workspace(root, workspace["nonce"])

    def test_manifest_outside_dedicated_temp_root_cannot_grant_access(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / SYNTHETIC_MANIFEST_NAME).write_text(json.dumps({
                "workspace_id": root.name, "nonce": "forged", "created_by": "pc_cleanguard",
                "created_at": "2026-07-17T00:00:00Z", "synthetic_only": True,
                "expected_files": [], "file_hashes": {},
                "allowed_operations": ["preview", "quarantine", "restore"],
                "workspace_root": str(root),
            }), encoding="utf-8")
            with self.assertRaises(ValueError):
                verify_synthetic_workspace(root, "forged")

    def test_symlink_or_reparse_entry_is_rejected(self):
        workspace = create_synthetic_workspace()
        root = Path(workspace["workspace_root"])
        target = root / workspace["expected_files"][0]
        link = root / "linked.tmp"
        try:
            link.symlink_to(target)
        except OSError:
            self.skipTest("symlink creation is unavailable on this Windows host")
        with self.assertRaises(ValueError):
            verify_synthetic_workspace(root, workspace["nonce"])

    def test_reparse_parent_in_dedicated_namespace_is_rejected(self):
        from pc_cleanguard.demo import workspace as workspace_module
        original = workspace_module._is_reparse
        with patch(
            "pc_cleanguard.demo.workspace._is_reparse",
            side_effect=lambda path: Path(path).name == "PC-CleanGuard" or original(path),
        ):
            with self.assertRaises(ValueError):
                create_synthetic_workspace()


if __name__ == "__main__":
    unittest.main()
