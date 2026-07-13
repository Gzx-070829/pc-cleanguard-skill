import unittest

from pc_cleanguard.persistence.levels import GOVERNANCE_LEVELS, classify_governance_level


class PersistenceLevelsTest(unittest.TestCase):
    def test_levels_are_stable(self):
        self.assertEqual(tuple(f"L{i}" for i in range(6)), tuple(GOVERNANCE_LEVELS))

    def test_mutations_are_l4_or_l5_and_never_executable(self):
        self.assertEqual("L5", classify_governance_level("silent_delete")["level"])
        self.assertEqual("L4", classify_governance_level("registry_change_proposal")["level"])
        self.assertFalse(classify_governance_level("registry_change_proposal")["execution_authorized"])

    def test_official_uninstaller_identification_is_l3_proposal_only(self):
        result = classify_governance_level("identify_official_uninstaller_proposal")
        self.assertEqual("L3", result["level"])
        self.assertTrue(result["proposal_only"])
        self.assertFalse(result["execution_authorized"])
