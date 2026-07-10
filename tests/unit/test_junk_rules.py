import unittest
from pathlib import Path

from pc_cleanguard.cleanup import (
    JUNK_CATEGORIES,
    JunkCategory,
    default_junk_rules,
    match_junk_rule,
)


class JunkRulesTest(unittest.TestCase):
    def test_supported_categories_are_exactly_pr14_scope(self) -> None:
        self.assertEqual(
            {
                "temp_file",
                "cache_file",
                "log_file",
                "crash_dump",
                "installer_leftover",
                "empty_directory_candidate",
            },
            set(JUNK_CATEGORIES),
        )

    def test_file_extensions_match_expected_categories(self) -> None:
        cases = {
            "example.tmp": JunkCategory.TEMP_FILE,
            "example.log": JunkCategory.LOG_FILE,
            "example.dmp": JunkCategory.CRASH_DUMP,
            "example.cache": JunkCategory.CACHE_FILE,
            "example.msi": JunkCategory.INSTALLER_LEFTOVER,
        }
        for name, expected in cases.items():
            with self.subTest(name=name):
                rule = match_junk_rule(Path("scratch") / name)
                self.assertIsNotNone(rule)
                self.assertEqual(expected, rule.category)

    def test_cache_directory_metadata_matches_cache_rule(self) -> None:
        rule = match_junk_rule(Path("scratch") / "cache" / "blob.bin")
        self.assertIsNotNone(rule)
        self.assertEqual(JunkCategory.CACHE_FILE, rule.category)

    def test_empty_directory_requires_explicit_empty_flag(self) -> None:
        path = Path("scratch") / "empty"
        self.assertIsNone(match_junk_rule(path))
        rule = match_junk_rule(path, is_empty_directory=True)
        self.assertIsNotNone(rule)
        self.assertEqual(JunkCategory.EMPTY_DIRECTORY_CANDIDATE, rule.category)

    def test_rules_have_bounded_confidence_and_explanation(self) -> None:
        for rule in default_junk_rules():
            with self.subTest(category=rule.category.value):
                self.assertGreater(rule.confidence, 0)
                self.assertLessEqual(rule.confidence, 1)
                self.assertTrue(rule.reason)


if __name__ == "__main__":
    unittest.main()
