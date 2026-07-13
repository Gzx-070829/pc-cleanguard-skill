import unittest

from pc_cleanguard.reputation import (
    EvidenceUse,
    ReputationMatcher,
    build_pup_insight,
    classify_evidence_use,
    evidence_guard_status,
    is_execution_gating_eligible,
    validate_evidence_record,
)


def _record(**changes):
    record = {
        "record_id": "adversarial-direct",
        "software_name": "Example Same Name App",
        "publisher": "Example Publisher",
        "aliases": [],
        "source_type": "public_regulatory_notice",
        "source_name": "Official Example Authority",
        "source_url": "https://example.invalid/official/adversarial",
        "source_title": "Official reviewed example",
        "source_date": "2026-07-13",
        "evidence_summary": "A deliberately strong evidence record for guard testing.",
        "behavior_categories": ["malicious_bundling"],
        "jurisdiction": "CN",
        "language": "zh-CN",
        "review_status": "approved_for_explanation",
        "confidence": 0.99,
        "false_positive_risk": "medium",
        "execution_authorized": False,
        "license_note": "Public metadata and short paraphrase only.",
        "evidence_scope": "review",
        "mapping_type": "direct_entity",
        "is_synthetic": False,
        "entity_scope": "windows_desktop_software",
        "relation_confidence": "high",
    }
    record.update(changes)
    return validate_evidence_record(record)


class ReputationAdversarialGuardTest(unittest.TestCase):
    def test_strong_real_direct_match_still_cannot_enter_execution_gate(self):
        record = _record()
        matches = ReputationMatcher([record]).match({
            "installed_apps": [{"target_id": "app:1", "display_name": record["software_name"], "publisher": record["publisher"]}]
        })
        self.assertEqual(EvidenceUse.REVIEW_HINT, classify_evidence_use(record))
        self.assertFalse(is_execution_gating_eligible(record))
        self.assertFalse(matches[0]["execution_authorized"])
        self.assertFalse(matches[0]["execution_gating_eligible"])
        guard = evidence_guard_status([record])
        self.assertEqual("enforced", guard["status"])
        self.assertEqual(0, guard["execution_gating_eligible_count"])
        self.assertEqual(
            {"no_delete_authorization", "no_uninstall_authorization", "no_disable_authorization", "no_registry_edit_authorization"},
            set(guard["blocked_actions"]),
        )

    def test_indirect_mapping_types_remain_non_authorizing(self):
        publisher = _record(mapping_type="related_publisher", entity_scope="publisher_level")
        self.assertEqual(EvidenceUse.PUBLISHER_LEVEL_WARNING, classify_evidence_use(publisher))

        collision = _record(mapping_type="name_collision_candidate", false_positive_risk="high")
        matches = ReputationMatcher([collision]).match({"installed_apps": [{"display_name": collision["software_name"]}]})
        self.assertLessEqual(matches[0]["confidence"], 0.3)
        self.assertTrue(any("name collision" in note for note in build_pup_insight(matches)["uncertainty_notes"]))

        mobile = _record(
            mapping_type="analogical_behavior",
            entity_scope="mobile_app",
            analogy_basis="移动端行为只用于 Windows 风险类比。",
        )
        self.assertEqual(EvidenceUse.EXPLAIN_ONLY, classify_evidence_use(mobile))
        self.assertNotEqual("windows_desktop_software", mobile["entity_scope"])

    def test_behavior_hint_alone_does_not_identify_software(self):
        record = _record(
            software_name="Unrelated Evidence Family",
            behavior_categories=["browser_hijacking"],
        )
        matches = ReputationMatcher([record], include_indicators=True).match({
            "installed_apps": [{"display_name": "browser_hijacking"}]
        })
        self.assertEqual([], matches)


if __name__ == "__main__":
    unittest.main()
