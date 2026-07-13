import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.pup import build_pup_review_pack


class PupAdversarialReviewPackTest(unittest.TestCase):
    def test_review_pack_exposes_adversarial_guard_without_commands(self):
        record = {
            "record_id": "guard-real", "software_name": "Example Guard App", "publisher": "Example Publisher",
            "aliases": [], "source_type": "public_regulatory_notice", "source_name": "Official Example Authority",
            "source_url": "https://example.invalid/official/guard", "source_title": "Official guard record",
            "source_date": "2026-07-13", "evidence_summary": "Reviewed direct-entity test evidence.",
            "behavior_categories": ["malicious_bundling"], "jurisdiction": "CN", "language": "zh-CN",
            "review_status": "approved_for_explanation", "confidence": 1.0, "false_positive_risk": "medium",
            "execution_authorized": False, "license_note": "Public metadata only.", "evidence_scope": "review",
            "mapping_type": "direct_entity", "is_synthetic": False, "entity_scope": "windows_desktop_software",
            "relation_confidence": "high",
        }
        report = {"installed_apps": [{"target_id": "app:guard", "display_name": "Example Guard App", "publisher": "Example Publisher"}]}
        with TemporaryDirectory() as directory:
            output = Path(directory) / "pack"
            summary = build_pup_review_pack(report, [record], output)
            self.assertEqual("enforced", summary["adversarial_guard_status"])
            safety = (output / "adversarial_safety_summary.md").read_text(encoding="utf-8")
            combined = "\n".join(path.read_text(encoding="utf-8") for path in output.glob("*.md"))
            self.assertIn("execution_gating_eligible_count: 0", safety)
            for left, right in (("delete this", " app"), ("uninstall this", " app"), ("disable this", " service"), ("edit", " registry")):
                self.assertNotIn(left + right, combined.casefold())


if __name__ == "__main__":
    unittest.main()
