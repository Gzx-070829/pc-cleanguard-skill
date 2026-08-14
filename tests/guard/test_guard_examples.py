import json
import unittest
from pathlib import Path

from pc_cleanguard.guard import (
    ActionBundle,
    ConsentGrant,
    Guard,
    GuardContext,
    evaluate_bundle,
    validate_consent,
    validate_preconditions,
    verify_audit_chain,
)


ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "examples" / "guard"


class GuardExampleTests(unittest.TestCase):
    def _json(self, path: Path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_twelve_documented_examples_have_required_contracts(self):
        directories = sorted(path for path in EXAMPLES.iterdir() if path.is_dir())
        self.assertEqual(12, len(directories))
        for directory in directories:
            with self.subTest(example=directory.name):
                for name in ("request.json", "context.json", "decision.json", "README.md"):
                    self.assertTrue((directory / name).is_file(), f"{directory.name}/{name}")

    def test_single_action_examples_match_current_deterministic_policy(self):
        for directory in sorted(EXAMPLES.iterdir()):
            if not directory.is_dir() or directory.name == "12-multi-action-bundle":
                continue
            with self.subTest(example=directory.name):
                actual = Guard().evaluate(
                    self._json(directory / "request.json"),
                    self._json(directory / "context.json"),
                ).to_dict()
                self.assertEqual(self._json(directory / "decision.json"), actual)

    def test_stale_consent_changed_target_audit_and_batch_attacks_are_reproducible(self):
        stale = EXAMPLES / "09-stale-consent"
        stale_decision = Guard().evaluate(
            self._json(stale / "request.json"), self._json(stale / "context.json")
        )
        self.assertFalse(
            validate_consent(
                stale_decision,
                ConsentGrant.from_dict(self._json(stale / "consent.json")),
                "2026-01-01T00:00:00Z",
            ).valid
        )

        changed = EXAMPLES / "10-target-changed-after-preview"
        changed_decision = Guard().evaluate(
            self._json(changed / "request.json"), self._json(changed / "context.json")
        )
        self.assertFalse(
            validate_preconditions(
                changed_decision,
                GuardContext.from_dict(self._json(changed / "current-context.json")),
            ).valid
        )

        self.assertTrue(verify_audit_chain(EXAMPLES / "11-audit-chain/audit.jsonl"))

        bundle_root = EXAMPLES / "12-multi-action-bundle"
        batch = evaluate_bundle(
            ActionBundle.from_dict(self._json(bundle_root / "action-bundle.json")),
            GuardContext.from_dict(self._json(bundle_root / "context.json")),
        )
        self.assertEqual(self._json(bundle_root / "decision.json"), batch.to_dict())
        self.assertEqual("BLOCK", batch.disposition.value)


if __name__ == "__main__":
    unittest.main()

