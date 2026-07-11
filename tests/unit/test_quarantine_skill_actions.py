import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.skill import invoke_skill_action


class QuarantineSkillActionsTest(unittest.TestCase):
    def test_quarantine_list_restore_actions_run_with_explicit_confirmation(self) -> None:
        with TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "quarantine"
            source = base / "agent.tmp"
            source.write_bytes(b"agent reversible")
            added = invoke_skill_action({
                "action": "quarantine_file",
                "payload": {
                    "root": str(root), "path": str(source), "reason": "agent review",
                    "evidence": [{"source": "user", "fact": "explicit confirmation"}],
                    "confirmed": True,
                },
            })
            listed = invoke_skill_action({
                "action": "list_quarantine_items", "payload": {"root": str(root)},
            })
            restored = invoke_skill_action({
                "action": "restore_quarantine_item",
                "payload": {"root": str(root), "item_id": added.result["item_id"], "confirmed": True},
            })

            self.assertEqual("quarantined", added.result["status"])
            self.assertEqual(1, len(listed.result["items"]))
            self.assertEqual("restored", restored.result["status"])
            self.assertTrue(source.is_file())
            self.assertEqual("LEVEL_2_REVERSIBLE", added.execution_level)
            self.assertTrue(added.requires_user_confirmation)
            self.assertFalse(added.execution_authorized)

    def test_mutating_action_rejects_missing_confirmation(self) -> None:
        with TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "agent.tmp"
            source.write_bytes(b"stay")
            with self.assertRaises(ValueError):
                invoke_skill_action({
                    "action": "quarantine_file",
                    "payload": {
                        "root": str(base / "q"), "path": str(source),
                        "reason": "no consent", "confirmed": False,
                    },
                })
            self.assertTrue(source.exists())


if __name__ == "__main__":
    unittest.main()
