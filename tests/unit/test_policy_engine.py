import unittest

from pc_cleanguard.core.models import (
    ClassificationLabel,
    EvidenceChain,
    GovernanceTarget,
    ObjectType,
    PermissionLevel,
)
from pc_cleanguard.core.policy_engine import evaluate_target
from tests.fixtures.policy_cases import software_target


class PolicyEngineTest(unittest.TestCase):
    def test_visual_cpp_redistributable_is_kept(self) -> None:
        decision = evaluate_target(
            software_target(
                "Microsoft Visual C++ 2015-2022 Redistributable (x64)",
                publisher="Microsoft Corporation",
                uninstall_available=True,
            )
        )
        self.assertEqual(ClassificationLabel.KEEP, decision.classification)
        self.assertFalse(decision.allowed)

    def test_driver_components_are_kept(self) -> None:
        cases = (
            ("NVIDIA Graphics Driver", "NVIDIA Corporation"),
            ("AMD Display Driver", "Advanced Micro Devices, Inc."),
            ("Intel Chipset Driver", "Intel Corporation"),
            ("NVIDIA Display Driver Component", None),
        )
        for name, publisher in cases:
            with self.subTest(name=name):
                decision = evaluate_target(
                    software_target(name, publisher=publisher, uninstall_available=True)
                )
                self.assertEqual(ClassificationLabel.KEEP, decision.classification)

    def test_unknown_toolbar_startup_entry_is_reversible_candidate(self) -> None:
        target = GovernanceTarget(
            target_id="startup:unknown-toolbar",
            object_type=ObjectType.STARTUP_ITEM,
            name="Unknown Search Toolbar",
            path=r"C:\Users\Alice\AppData\Local\Toolbar\toolbar.exe",
        )
        decision = evaluate_target(target)
        self.assertEqual(ClassificationLabel.STARTUP_OFF, decision.classification)
        self.assertTrue(decision.required_confirmation)
        self.assertTrue(decision.rollback_required)

    def test_known_bloatware_with_uninstaller_is_candidate_only(self) -> None:
        decision = evaluate_target(
            software_target(
                "Coupon Companion",
                publisher="Example Vendor",
                known_bloatware=True,
                uninstall_available=True,
            )
        )
        self.assertEqual(ClassificationLabel.SAFE_REMOVE, decision.classification)
        self.assertTrue(decision.required_confirmation)
        self.assertTrue(decision.audit_required)

    def test_user_declared_core_software_is_kept(self) -> None:
        decision = evaluate_target(
            software_target(
                "Special Research Tool",
                user_declared_core=True,
                uninstall_available=True,
            )
        )
        self.assertEqual(ClassificationLabel.KEEP, decision.classification)

    def test_dotnet_and_directx_runtimes_are_kept(self) -> None:
        for name in ("Microsoft .NET Runtime 8.0", "DirectX Runtime"):
            with self.subTest(name=name):
                decision = evaluate_target(software_target(name))
                self.assertEqual(ClassificationLabel.KEEP, decision.classification)

    def test_suspicious_user_temp_file_is_quarantine_candidate(self) -> None:
        target = GovernanceTarget(
            target_id="file:suspicious-temp",
            object_type=ObjectType.FILE,
            name="unknown-payload.bin",
            path=r"C:\Users\Alice\AppData\Local\Temp\unknown-payload.bin",
            suspicious=True,
            evidence_chain=EvidenceChain(
                sources=("local_metadata",),
                facts=("Unexpected binary in user temp",),
                confidence=0.7,
            ),
        )
        decision = evaluate_target(target)
        self.assertEqual(ClassificationLabel.QUARANTINE, decision.classification)
        self.assertTrue(decision.required_confirmation)
        self.assertTrue(decision.rollback_required)

    def test_system32_delete_request_is_blocked(self) -> None:
        target = GovernanceTarget(
            target_id="directory:system32",
            object_type=ObjectType.DIRECTORY,
            name="System32",
            path=r"C:\Windows\System32",
            requested_classification=ClassificationLabel.SAFE_REMOVE,
        )
        decision = evaluate_target(target)
        self.assertEqual(ClassificationLabel.BLOCK, decision.classification)
        self.assertTrue(decision.blocked_by_hard_rule)

    def test_code_repository_delete_request_is_blocked(self) -> None:
        target = GovernanceTarget(
            target_id="directory:source-repo",
            object_type=ObjectType.DIRECTORY,
            name="customer-project",
            path=r"C:\Users\Alice\source\repos\customer-project",
            requested_classification=ClassificationLabel.SAFE_REMOVE,
        )
        decision = evaluate_target(target)
        self.assertEqual(ClassificationLabel.BLOCK, decision.classification)

    def test_unknown_app_without_uninstaller_asks_user(self) -> None:
        decision = evaluate_target(software_target("Unrecognized Utility"))
        self.assertEqual(ClassificationLabel.ASK_USER, decision.classification)
        self.assertNotEqual(ClassificationLabel.SAFE_REMOVE, decision.classification)
        self.assertFalse(decision.allowed)

    def test_community_delete_rule_is_downgraded(self) -> None:
        decision = evaluate_target(
            software_target(
                "Normal Notes App",
                source="community_rule",
                uninstall_available=True,
                community_recommendation=ClassificationLabel.SAFE_REMOVE,
            )
        )
        self.assertEqual(ClassificationLabel.ASK_USER, decision.classification)
        self.assertFalse(decision.allowed)

        field_only_decision = evaluate_target(
            software_target(
                "Another Normal App",
                uninstall_available=True,
                community_recommendation=ClassificationLabel.SAFE_REMOVE,
            )
        )
        self.assertEqual(
            ClassificationLabel.ASK_USER, field_only_decision.classification
        )
        self.assertFalse(field_only_decision.allowed)

    def test_ai_bad_verdict_without_evidence_only_asks_user(self) -> None:
        decision = evaluate_target(
            software_target(
                "Ordinary App",
                source="ai_judgment",
                uninstall_available=True,
                requested_classification=ClassificationLabel.BLOCK,
            )
        )
        self.assertEqual(ClassificationLabel.ASK_USER, decision.classification)
        self.assertFalse(decision.allowed)

    def test_online_pup_reputation_cannot_override_user_core(self) -> None:
        decision = evaluate_target(
            software_target(
                "User Essential Legacy App",
                user_declared_core=True,
                online_reputation="PUP",
                uninstall_available=True,
            )
        )
        self.assertIn(
            decision.classification,
            {ClassificationLabel.KEEP, ClassificationLabel.ASK_USER},
        )
        self.assertFalse(decision.allowed)

    def test_protected_developer_tools_are_never_safe_remove(self) -> None:
        for name in (
            "Python 3.13",
            "Node.js",
            "Miniconda",
            "Git",
            "Docker Desktop",
            "CUDA Toolkit",
            "Visual Studio Build Tools",
        ):
            with self.subTest(name=name):
                decision = evaluate_target(
                    software_target(name, uninstall_available=True)
                )
                self.assertIn(
                    decision.classification,
                    {ClassificationLabel.KEEP, ClassificationLabel.ASK_USER},
                )
                self.assertNotEqual(
                    ClassificationLabel.SAFE_REMOVE, decision.classification
                )

    def test_all_non_keep_decisions_have_evidence_and_audit(self) -> None:
        targets = (
            software_target("Unknown No Uninstaller"),
            software_target(
                "Known Optional App",
                known_bloatware=True,
                uninstall_available=True,
            ),
            GovernanceTarget(
                target_id="startup:suspicious",
                object_type=ObjectType.STARTUP_ITEM,
                name="Mystery Toolbar",
            ),
            GovernanceTarget(
                target_id="file:temp",
                object_type=ObjectType.FILE,
                name="payload.tmp",
                path=r"C:\Users\Alice\AppData\Local\Temp\payload.tmp",
                suspicious=True,
            ),
            GovernanceTarget(
                target_id="directory:windows",
                object_type=ObjectType.DIRECTORY,
                name="Windows",
                path=r"C:\Windows",
            ),
        )
        for target in targets:
            with self.subTest(target=target.target_id):
                decision = evaluate_target(target)
                self.assertNotEqual(ClassificationLabel.KEEP, decision.classification)
                self.assertFalse(decision.evidence_chain.is_empty)
                self.assertTrue(decision.audit_required)

    def test_block_always_uses_level_5(self) -> None:
        decision = evaluate_target(
            GovernanceTarget(
                target_id="directory:windows",
                object_type=ObjectType.DIRECTORY,
                name="Windows",
                path=r"C:\Windows",
                user_declared_core=True,
            )
        )
        self.assertEqual(ClassificationLabel.BLOCK, decision.classification)
        self.assertEqual(
            PermissionLevel.LEVEL_5_FORBIDDEN, decision.permission_level
        )
        self.assertTrue(decision.blocked_by_hard_rule)


if __name__ == "__main__":
    unittest.main()
