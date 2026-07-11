import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.cleanup import (
    CleanupConfirmation,
    CleanupExecutor,
    JunkScanner,
    build_cleanup_preview,
)
from pc_cleanguard.protection import (
    DEVELOPER_PROTECTION_LEVEL,
    DeveloperGuardDecision,
    classify_developer_path,
    is_protected_developer_path,
)


class DeveloperGuardTest(unittest.TestCase):
    def test_known_developer_directories_are_protected(self) -> None:
        paths = (
            "C:/Workspace/app/.git/objects/pack.tmp",
            "C:/Workspace/app/.venv/cache.tmp",
            "C:/Workspace/app/venv/cache.tmp",
            "C:/Workspace/app/env/cache.tmp",
            "C:/Workspace/app/node_modules/pkg/cache.tmp",
            "C:/Users/Synthetic/.npm/cache/item.tmp",
            "C:/Users/Synthetic/.pnpm-store/v3/item.tmp",
            "C:/Users/Synthetic/.yarn/cache/item.tmp",
            "C:/Workspace/app/.idea/index.tmp",
            "C:/Workspace/app/.vscode/state.tmp",
            "C:/Miniconda3/envs/research/conda-meta/history.tmp",
            "C:/Users/Synthetic/AppData/Local/pip/Cache/item.tmp",
            "C:/Users/Synthetic/.cargo/registry/cache/item.tmp",
            "C:/Users/Synthetic/.gradle/caches/item.tmp",
            "C:/Users/Synthetic/.m2/repository/item.tmp",
            "C:/Users/Synthetic/AppData/Local/NVIDIA/ComputeCache/item.tmp",
            "C:/Users/Synthetic/AppData/Local/NVIDIA/DXCache/item.tmp",
            "C:/Users/Synthetic/AppData/Local/NVIDIA/GLCache/item.tmp",
        )
        for path in paths:
            with self.subTest(path=path):
                self.assertTrue(is_protected_developer_path(path))

    def test_ordinary_temp_file_is_not_developer_protected(self) -> None:
        decision = classify_developer_path("C:/Scratch/ordinary.tmp")

        self.assertIsInstance(decision, DeveloperGuardDecision)
        self.assertFalse(decision.protected)
        self.assertEqual("PROTECTION_LEVEL_NONE", decision.protection_level)

    def test_explicit_user_code_root_is_protected(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory) / "my-application"
            target = root / "build" / "trace.log"

            decision = classify_developer_path(target, user_code_roots=(root,))

        self.assertTrue(decision.protected)
        self.assertEqual(DEVELOPER_PROTECTION_LEVEL, decision.protection_level)
        self.assertEqual("user_code_root", decision.matched_rule)

    def test_protected_decision_is_explainable(self) -> None:
        decision = classify_developer_path("C:/Workspace/app/node_modules/cache.tmp")

        self.assertTrue(decision.protected)
        self.assertIn("node_modules", decision.reason)
        self.assertTrue(decision.evidence)
        self.assertTrue(
            all({"source", "fact"}.issubset(item) for item in decision.evidence)
        )

    def test_junk_scanner_blocks_developer_directory(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            developer_file = root / "node_modules" / "package" / "cache.tmp"
            developer_file.parent.mkdir(parents=True)
            developer_file.write_bytes(b"developer cache")
            ordinary = root / "scratch.tmp"
            ordinary.write_bytes(b"ordinary")

            result = JunkScanner().scan([root])

        self.assertTrue(
            any(Path(item.path).name == "node_modules" for item in result.blocked_candidates)
        )
        self.assertTrue(
            all("node_modules" not in item.path for item in result.candidates)
        )
        self.assertTrue(any(item.path == str(ordinary) for item in result.candidates))

    def test_junk_scanner_blocks_explicit_user_code_root(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            code_root = root / "application"
            code_root.mkdir()
            (code_root / "trace.log").write_bytes(b"code output")

            result = JunkScanner(user_code_roots=(code_root,)).scan([root])

        self.assertTrue(
            any(Path(item.path).name == "application" for item in result.blocked_candidates)
        )
        self.assertFalse(result.candidates)

    def test_executor_rechecks_developer_path_before_unlink(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            safe = root / "safe.tmp"
            safe.write_bytes(b"safe preview")
            preview = build_cleanup_preview(JunkScanner().scan([root])).to_dict()
            protected = root / "node_modules" / "package" / "cache.tmp"
            protected.parent.mkdir(parents=True)
            protected.write_bytes(b"must remain")
            preview["top_candidates"][0]["path"] = str(protected)

            report = CleanupExecutor().execute(
                preview,
                CleanupConfirmation(True, (root,)),
                audit_path=root / "audit.jsonl",
            ).to_dict()
            self.assertEqual("blocked", report["results"][0]["status"])
            self.assertIn("developer", report["results"][0]["reason"])
            self.assertTrue(protected.exists())

    def test_executor_blocks_explicit_user_code_root(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            code_root = root / "application"
            code_root.mkdir()
            generated_log = code_root / "generated.log"
            generated_log.write_bytes(b"belongs to user code")
            preview = build_cleanup_preview(JunkScanner().scan([root])).to_dict()

            report = CleanupExecutor(user_code_roots=(code_root,)).execute(
                preview,
                CleanupConfirmation(True, (root,)),
                audit_path=root / "code-audit.jsonl",
            ).to_dict()

            self.assertEqual("blocked", report["results"][0]["status"])
            self.assertIn("user code root", report["results"][0]["reason"])
            self.assertTrue(generated_log.exists())


if __name__ == "__main__":
    unittest.main()
