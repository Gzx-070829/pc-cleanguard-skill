import inspect
import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pc_cleanguard.state import SCHEMA_VERSION, SQLiteStateStore


NOW = "2026-07-06T00:00:00Z"


class SQLiteStateStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.db_path = Path(self.temporary_directory.name) / "state.sqlite"
        self.store = SQLiteStateStore(self.db_path)
        self.store.initialize()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_initialize_creates_all_required_tables(self) -> None:
        expected = {
            "schema_meta",
            "scans",
            "scan_targets",
            "policy_decisions",
            "audit_event_index",
            "user_preferences",
            "reputation_sources",
            "reputation_entries",
            "reputation_evidence",
            "reputation_conflicts",
            "software_aliases",
            "publisher_aliases",
            "vendor_uninstallers",
            "rulepack_versions",
        }
        with self.store._connection() as connection:
            rows = connection.execute(
                "SELECT name FROM sqlite_master WHERE type = ?",
                ("table",),
            ).fetchall()
        self.assertTrue(expected.issubset({row["name"] for row in rows}))

    def test_schema_meta_contains_version(self) -> None:
        self.assertEqual(SCHEMA_VERSION, self.store.get_schema_version())

    def test_db_path_is_required_and_has_no_default(self) -> None:
        parameter = inspect.signature(SQLiteStateStore).parameters["db_path"]
        self.assertIs(inspect.Parameter.empty, parameter.default)
        with self.assertRaises(TypeError):
            SQLiteStateStore()

    def test_only_sqlite_and_db_extensions_are_allowed(self) -> None:
        SQLiteStateStore(Path(self.temporary_directory.name) / "allowed.sqlite")
        SQLiteStateStore(Path(self.temporary_directory.name) / "allowed.db")
        with self.assertRaises(ValueError):
            SQLiteStateStore(Path(self.temporary_directory.name) / "rejected.txt")

    def test_unc_paths_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            SQLiteStateStore(r"\\server\share\state.sqlite")

    def test_system_paths_are_rejected(self) -> None:
        for path in (
            r"C:\Windows\state.sqlite",
            r"C:\Windows\System32\state.db",
            r"C:\Program Files\state.sqlite",
            r"C:\Program Files (x86)\state.db",
        ):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    SQLiteStateStore(path)

    def test_non_initialize_methods_do_not_implicitly_create_database(self) -> None:
        path = Path(self.temporary_directory.name) / "missing.sqlite"
        store = SQLiteStateStore(path)
        with self.assertRaises(RuntimeError):
            store.get_schema_version()
        self.assertFalse(path.exists())

    def test_insert_scan_succeeds(self) -> None:
        self._insert_scan()
        with self.store._connection() as connection:
            row = connection.execute(
                "SELECT * FROM scans WHERE scan_id = ?", ("scan-1",)
            ).fetchone()
        self.assertEqual("Windows", row["platform"])

    def test_insert_scan_target_succeeds(self) -> None:
        self._insert_scan_and_target()
        self.assertEqual("Synthetic App", self.store.get_scan_targets("scan-1")[0]["name"])

    def test_insert_policy_decision_succeeds(self) -> None:
        self._insert_decision()
        decisions = self.store.get_policy_decisions_for_target("SOFTWARE:Synthetic")
        self.assertEqual("ASK_USER", decisions[0]["classification"])
        self.assertTrue(decisions[0]["required_confirmation"])

    def test_insert_audit_event_index_succeeds(self) -> None:
        self._insert_scan_and_target()
        self.store.insert_audit_event_index(
            "event-1",
            "explicit/audit.jsonl",
            1,
            NOW,
            "REPORT_ONLY",
            "planned",
            True,
            scan_id="scan-1",
            target_id="SOFTWARE:Synthetic",
            classification="KEEP",
        )
        with self.store._connection() as connection:
            row = connection.execute(
                "SELECT * FROM audit_event_index WHERE event_id = ?", ("event-1",)
            ).fetchone()
        self.assertEqual(1, row["dry_run"])

    def test_audit_event_index_rejects_non_dry_run(self) -> None:
        with self.assertRaises(ValueError):
            self.store.insert_audit_event_index(
                "event-1", "audit.jsonl", 1, NOW, "REPORT_ONLY", "planned", False
            )

    def test_upsert_user_preference_succeeds(self) -> None:
        self.store.upsert_user_preference(
            "pref-1", "SOFTWARE:Synthetic", "keep", "true", NOW, NOW
        )
        self.store.upsert_user_preference(
            "pref-1", "SOFTWARE:Synthetic", "keep", "still-true", NOW, NOW
        )
        preferences = self.store.get_user_preferences("SOFTWARE:Synthetic")
        self.assertEqual(1, len(preferences))
        self.assertEqual("still-true", preferences[0]["value"])

    def test_preference_type_is_restricted(self) -> None:
        with self.assertRaises(ValueError):
            self.store.upsert_user_preference(
                "pref-1", "target", "override_block", "true", NOW, NOW
            )

    def test_get_scan_targets_uses_parameterized_identity(self) -> None:
        self._insert_scan_and_target()
        self.assertEqual([], self.store.get_scan_targets("scan-1' OR 1=1 --"))

    def test_get_policy_decisions_for_target_succeeds(self) -> None:
        self._insert_decision()
        rows = self.store.get_policy_decisions_for_target("SOFTWARE:Synthetic")
        self.assertEqual("decision-1", rows[0]["decision_id"])
        self.assertIs(False, rows[0]["allowed"])

    def test_get_user_preferences_succeeds(self) -> None:
        self.store.upsert_user_preference(
            "pref-1", "SOFTWARE:Synthetic", "core_tool", "true", NOW, NOW
        )
        self.assertEqual(
            "core_tool",
            self.store.get_user_preferences("SOFTWARE:Synthetic")[0][
                "preference_type"
            ],
        )

    def test_evidence_json_round_trips(self) -> None:
        evidence = {"facts": ["quoted ' evidence", "中文证据"], "confidence": 0.5}
        self._insert_decision(evidence=evidence)
        row = self.store.get_policy_decisions_for_target("SOFTWARE:Synthetic")[0]
        self.assertEqual(evidence, row["evidence"])
        self.assertNotIn("evidence_json", row)

    def test_dangerous_database_methods_are_absent(self) -> None:
        names = vars(SQLiteStateStore)
        for first, second in (
            ("raw_", "query"),
            ("clear_", "database"),
            ("delete_", "database"),
        ):
            self.assertNotIn(first + second, names)

    def _insert_scan(self) -> None:
        self.store.insert_scan("scan-1", NOW, "Windows", "offline", "synthetic")

    def _insert_scan_and_target(self) -> None:
        self._insert_scan()
        self.store.insert_scan_target(
            "SOFTWARE:Synthetic",
            "scan-1",
            "SOFTWARE",
            "Synthetic App",
            source="unit_test",
            first_seen=NOW,
            last_seen=NOW,
            normalized_identity="synthetic app",
        )

    def _insert_decision(self, evidence=None) -> None:
        self._insert_scan_and_target()
        self.store.insert_policy_decision(
            "decision-1",
            "scan-1",
            "SOFTWARE:Synthetic",
            NOW,
            "ASK_USER",
            "MEDIUM",
            "LEVEL_0_READ_ONLY",
            False,
            True,
            True,
            False,
            "Needs user context.",
            evidence if evidence is not None else {"facts": ["synthetic"]},
        )


if __name__ == "__main__":
    unittest.main()
