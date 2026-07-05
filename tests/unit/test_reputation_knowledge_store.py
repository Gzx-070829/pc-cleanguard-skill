import ast
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.core.models import GovernanceTarget, ObjectType
from pc_cleanguard.core.policy_engine import evaluate_target
from pc_cleanguard.core.report_builder import build_report
from pc_cleanguard.reputation import (
    EvidenceType,
    ReputationCategory,
    ReputationConflict,
    ReputationEntry,
    ReputationEvidence,
    ReputationKnowledgeStore,
    ReputationSource,
    ReviewStatus,
    SourceType,
    SuggestedClassification,
)
from pc_cleanguard.state import SQLiteStateStore


NOW = "2026-07-06T00:00:00Z"


class ReputationKnowledgeStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        state = SQLiteStateStore(Path(self.temporary_directory.name) / "state.db")
        state.initialize()
        self.state = state
        self.store = ReputationKnowledgeStore(state)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_insert_reputation_source_succeeds(self) -> None:
        self.store.insert_source(self._source())
        row = self._table_row("reputation_sources", "source_id", "source-1")
        self.assertEqual("COMMUNITY_REPORT", row["source_type"])

    def test_insert_reputation_entry_succeeds(self) -> None:
        self.store.insert_entry(self._entry())
        self.assertEqual(1, len(self.store.find_entries_by_name("Example Utility")))

    def test_insert_reputation_evidence_succeeds(self) -> None:
        self._insert_entry_with_source()
        self.store.insert_evidence(self._evidence())
        rows = self.store.get_evidence_for_entry("entry-1")
        self.assertEqual("COMMUNITY_REPORT", rows[0]["evidence_type"])

    def test_insert_reputation_conflict_succeeds(self) -> None:
        self.store.insert_entry(self._entry())
        self.store.insert_conflict(self._conflict())
        self.assertTrue(
            self.store.get_conflicts_for_entry("entry-1")[0][
                "requires_user_context"
            ]
        )

    def test_insert_software_alias_succeeds(self) -> None:
        self.store.insert_entry(self._entry())
        self.store.insert_software_alias("alias-1", "entry-1", "Example Alias", NOW)
        row = self._table_row("software_aliases", "alias_id", "alias-1")
        self.assertEqual("example alias", row["normalized_alias"])

    def test_insert_publisher_alias_succeeds(self) -> None:
        self.store.insert_publisher_alias(
            "publisher-alias-1", "Example Publisher", "Example Pub", NOW
        )
        row = self._table_row(
            "publisher_aliases", "alias_id", "publisher-alias-1"
        )
        self.assertEqual("example pub", row["normalized_alias"])

    def test_insert_vendor_uninstaller_requires_confirmation(self) -> None:
        self.store.insert_entry(self._entry())
        self.store.insert_vendor_uninstaller(
            "uninstaller-1",
            "Example Publisher",
            "documented_standard_method",
            "Synthetic metadata only.",
            NOW,
            entry_id="entry-1",
        )
        row = self._table_row(
            "vendor_uninstallers", "uninstaller_id", "uninstaller-1"
        )
        self.assertEqual(1, row["requires_confirmation"])

    def test_insert_rulepack_version_succeeds(self) -> None:
        self.store.insert_rulepack_version(
            "rulepack-1", "Synthetic Rules", "0.1", "local_fixture", NOW
        )
        row = self._table_row("rulepack_versions", "rulepack_id", "rulepack-1")
        self.assertEqual("0.1", row["version"])

    def test_find_entries_by_canonical_name(self) -> None:
        self.store.insert_entry(self._entry())
        rows = self.store.find_entries_by_name("example utility")
        self.assertEqual("entry-1", rows[0]["entry_id"])

    def test_find_entries_by_alias(self) -> None:
        self.store.insert_entry(self._entry())
        self.store.insert_software_alias("alias-1", "entry-1", "Example Alias", NOW)
        rows = self.store.find_entries_by_name("  EXAMPLE   ALIAS ")
        self.assertEqual("entry-1", rows[0]["entry_id"])

    def test_find_entries_by_name_is_parameterized(self) -> None:
        self.store.insert_entry(self._entry())
        self.assertEqual([], self.store.find_entries_by_name("' OR 1=1 --"))

    def test_get_evidence_for_entry_includes_source_metadata(self) -> None:
        self._insert_entry_with_source()
        self.store.insert_evidence(self._evidence())
        row = self.store.get_evidence_for_entry("entry-1")[0]
        self.assertEqual("Synthetic Community", row["source_name"])
        self.assertEqual("unverified", row["trust_tier"])

    def test_get_conflicts_for_entry_succeeds(self) -> None:
        self.store.insert_entry(self._entry())
        self.store.insert_conflict(self._conflict())
        row = self.store.get_conflicts_for_entry("entry-1")[0]
        self.assertEqual("needs_user_context", row["conflict_type"])

    def test_delete_is_not_a_suggested_classification(self) -> None:
        with self.assertRaises(ValueError):
            SuggestedClassification("DELETE")

    def test_auto_uninstall_is_not_a_suggested_classification(self) -> None:
        with self.assertRaises(ValueError):
            SuggestedClassification("AUTO_UNINSTALL")

    def test_force_and_silent_remove_are_not_suggestions(self) -> None:
        for value in ("FORCE_REMOVE", "AUTO_DELETE", "SILENT_REMOVE"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    SuggestedClassification(value)

    def test_entry_results_contain_no_execution_authorization(self) -> None:
        self.store.insert_entry(self._entry())
        row = self.store.find_entries_by_name("Example Utility")[0]
        self.assertTrue(
            {
                "execution_authorization",
                "command",
                "auto_execute",
                "uninstall_permission",
            }.isdisjoint(row)
        )

    def test_community_source_remains_evidence_not_verdict(self) -> None:
        self._insert_entry_with_source()
        self.store.insert_evidence(self._evidence())
        row = self.store.get_evidence_for_entry("entry-1")[0]
        self.assertEqual("COMMUNITY_REPORT", row["source_type"])
        self.assertNotIn("verdict", row)

    def test_synthetic_examples_are_parseable_and_complete(self) -> None:
        data = self._synthetic_data()
        self.assertIs(True, data["synthetic"])
        categories = {entry["category"].casefold() for entry in data["entries"]}
        self.assertTrue(
            {"possible_pup", "adware", "bundled_software", "fake_optimizer"}
            .issubset(categories)
        )
        evidence_types = {
            evidence["evidence_type"].casefold() for evidence in data["evidence"]
        }
        self.assertTrue(
            {
                "false_positive_note",
                "community_report",
                "security_vendor_signal",
                "known_uninstaller",
            }.issubset(evidence_types)
        )
        self.assertTrue(data["conflicts"][0]["requires_user_context"])

    def test_synthetic_examples_make_no_real_brand_allegations(self) -> None:
        data = self._synthetic_data()
        self.assertTrue(
            all(
                entry["canonical_name"].startswith("Example ")
                for entry in data["entries"]
            )
        )
        self.assertIn("不是现实软件指控", data["disclaimer_zh"])
        self.assertIn("cannot authorize removal", data["disclaimer_en"])

    def test_stores_do_not_import_process_or_network_modules(self) -> None:
        forbidden = {
            first + second
            for first, second in (
                ("sub", "process"),
                ("req", "uests"),
                ("url", "lib"),
                ("sock", "et"),
            )
        }
        for tree in self._store_trees():
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module.split(".")[0])
            self.assertTrue(forbidden.isdisjoint(imports))

    def test_dangerous_database_entrypoints_are_absent(self) -> None:
        for store_type in (SQLiteStateStore, ReputationKnowledgeStore):
            names = vars(store_type)
            for first, second in (
                ("raw_", "query"),
                ("clear_", "database"),
                ("delete_", "database"),
                ("execute", "script"),
            ):
                self.assertNotIn(first + second, names)

    def test_execute_calls_do_not_use_formatted_or_concatenated_sql(self) -> None:
        for tree in self._store_trees():
            for node in ast.walk(tree):
                if not (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "execute"
                    and node.args
                ):
                    continue
                sql_argument = node.args[0]
                self.assertNotIsInstance(sql_argument, ast.JoinedStr)
                self.assertNotIsInstance(sql_argument, ast.BinOp)
                self.assertFalse(
                    isinstance(sql_argument, ast.Call)
                    and isinstance(sql_argument.func, ast.Attribute)
                    and sql_argument.func.attr == "format"
                )

    def test_pr4_does_not_change_policy_or_report_authorization(self) -> None:
        target = GovernanceTarget(
            target_id="SOFTWARE:User Core",
            object_type=ObjectType.SOFTWARE,
            name="User Core",
            user_declared_core=True,
            online_reputation="PUP",
        )
        decision = evaluate_target(target)
        self.assertEqual("KEEP", decision.classification.value)
        report = build_report("scan", "Windows", "offline", [decision])
        self.assertIs(False, report["summary"]["destructive_actions_executed"])
        self.assertIs(False, report["managed_mode_compatibility"]["automatic_execution_allowed"])

    def _source(self) -> ReputationSource:
        return ReputationSource(
            source_id="source-1",
            source_name="Synthetic Community",
            source_type=SourceType.COMMUNITY_REPORT,
            trust_tier="unverified",
            created_at=NOW,
            updated_at=NOW,
        )

    def _entry(self) -> ReputationEntry:
        return ReputationEntry(
            entry_id="entry-1",
            canonical_name="Example Utility",
            publisher="Example Publisher",
            category=ReputationCategory.POSSIBLE_PUP,
            suggested_classification=SuggestedClassification.ASK_USER,
            confidence=0.5,
            severity="medium",
            false_positive_risk="high",
            review_status=ReviewStatus.NEEDS_REVIEW,
            first_seen=NOW,
            last_updated=NOW,
        )

    def _evidence(self) -> ReputationEvidence:
        return ReputationEvidence(
            evidence_id="evidence-1",
            entry_id="entry-1",
            source_id="source-1",
            evidence_type=EvidenceType.COMMUNITY_REPORT,
            summary="Synthetic evidence requiring review.",
            confidence=0.4,
            captured_at=NOW,
        )

    def _conflict(self) -> ReputationConflict:
        return ReputationConflict(
            conflict_id="conflict-1",
            entry_id="entry-1",
            conflict_type="needs_user_context",
            requires_user_context=True,
            created_at=NOW,
        )

    def _insert_entry_with_source(self) -> None:
        self.store.insert_source(self._source())
        self.store.insert_entry(self._entry())

    def _table_row(self, table: str, key: str, value: str):
        queries = {
            ("reputation_sources", "source_id"): (
                "SELECT * FROM reputation_sources WHERE source_id = ?"
            ),
            ("software_aliases", "alias_id"): (
                "SELECT * FROM software_aliases WHERE alias_id = ?"
            ),
            ("publisher_aliases", "alias_id"): (
                "SELECT * FROM publisher_aliases WHERE alias_id = ?"
            ),
            ("vendor_uninstallers", "uninstaller_id"): (
                "SELECT * FROM vendor_uninstallers WHERE uninstaller_id = ?"
            ),
            ("rulepack_versions", "rulepack_id"): (
                "SELECT * FROM rulepack_versions WHERE rulepack_id = ?"
            ),
        }
        query = queries.get((table, key))
        if query is None:
            raise ValueError("test helper table/key is not allowlisted")
        with self.state._connection() as connection:
            row = connection.execute(query, (value,)).fetchone()
        return row

    @staticmethod
    def _synthetic_data() -> dict:
        path = (
            Path(__file__).resolve().parents[2]
            / "examples"
            / "reputation"
            / "synthetic_reputation_entries.json"
        )
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _store_trees() -> list[ast.AST]:
        root = Path(__file__).resolve().parents[2] / "pc_cleanguard"
        return [
            ast.parse((root / relative).read_text(encoding="utf-8"))
            for relative in (
                Path("state/sqlite_store.py"),
                Path("reputation/knowledge_store.py"),
            )
        ]


if __name__ == "__main__":
    unittest.main()
