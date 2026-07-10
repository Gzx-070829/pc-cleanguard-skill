import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.cleanup import CleanupConfirmation


class CleanupConfirmationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = TemporaryDirectory()
        self.root = Path(self.directory.name)

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_explicit_allow_root_accepts_contained_file(self) -> None:
        candidate = self.root / "scratch.tmp"
        candidate.write_bytes(b"x")
        decision = CleanupConfirmation(False, (self.root,)).evaluate(candidate)
        self.assertTrue(decision.allowed)
        self.assertIn("allow-root", decision.reason)

    def test_path_outside_allow_root_is_blocked(self) -> None:
        allowed = self.root / "allowed"
        outside = self.root / "outside"
        allowed.mkdir()
        outside.mkdir()
        candidate = outside / "scratch.tmp"
        candidate.write_bytes(b"x")
        decision = CleanupConfirmation(True, (allowed,)).evaluate(candidate)
        self.assertFalse(decision.allowed)
        self.assertIn("outside", decision.reason)

    def test_personal_directory_is_blocked_inside_allow_root(self) -> None:
        documents = self.root / "Documents"
        documents.mkdir()
        candidate = documents / "private.tmp"
        candidate.write_bytes(b"private")
        decision = CleanupConfirmation(True, (self.root,)).evaluate(candidate)
        self.assertFalse(decision.allowed)
        self.assertIn("protected", decision.reason)

    def test_code_repository_is_blocked_inside_allow_root(self) -> None:
        repository = self.root / "worktree"
        repository.mkdir()
        (repository / ".git").mkdir()
        candidate = repository / "build.log"
        candidate.write_bytes(b"log")
        decision = CleanupConfirmation(True, (self.root,)).evaluate(candidate)
        self.assertFalse(decision.allowed)
        self.assertIn("code repository", decision.reason)

    def test_browser_profile_is_blocked_inside_allow_root(self) -> None:
        profile = self.root / "Chrome" / "User Data" / "Default"
        profile.mkdir(parents=True)
        candidate = profile / "browser.cache"
        candidate.write_bytes(b"cache")
        decision = CleanupConfirmation(True, (self.root,)).evaluate(candidate)
        self.assertFalse(decision.allowed)
        self.assertIn("browser profile", decision.reason)

    def test_confirmation_requires_existing_explicit_roots(self) -> None:
        with self.assertRaises(ValueError):
            CleanupConfirmation(False, ())
        with self.assertRaises(FileNotFoundError):
            CleanupConfirmation(False, (self.root / "missing",))


if __name__ == "__main__":
    unittest.main()
