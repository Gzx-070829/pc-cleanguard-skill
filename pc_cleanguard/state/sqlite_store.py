"""Explicit-path SQLite state store with parameterized queries only."""

from __future__ import annotations

import json
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .schema import CREATE_SCHEMA_SQL, SCHEMA_VERSION


_WINDOWS_SYSTEM_PATH = re.compile(
    r"^[a-z]:\\(?:windows|program files(?: \(x86\))?|programdata|recovery|"
    r"system volume information|\$recycle\.bin)(?:\\|$)",
    re.IGNORECASE,
)
_POSIX_SYSTEM_PREFIXES = (
    "/bin",
    "/boot",
    "/dev",
    "/etc",
    "/proc",
    "/root",
    "/sbin",
    "/sys",
    "/usr",
    "/var",
)
_PREFERENCE_TYPES = {"keep", "remove", "ignore", "suspicion", "core_tool"}


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {key: row[key] for key in row.keys()}


class SQLiteStateStore:
    """Queryable local memory; never an execution or cleanup component."""

    def __init__(self, db_path: str | Path):
        if not isinstance(db_path, (str, Path)) or not str(db_path).strip():
            raise ValueError("db_path must be an explicit non-empty path")
        self.db_path = Path(db_path)
        if self.db_path.suffix.casefold() not in {".sqlite", ".db"}:
            raise ValueError("db_path must use the .sqlite or .db extension")
        self._validate_database_path()

    def _validate_database_path(self) -> None:
        raw_path = str(self.db_path).replace("/", "\\")
        resolved = self.db_path.resolve(strict=False)
        resolved_windows = str(resolved).replace("/", "\\")
        if raw_path.startswith("\\\\") or resolved_windows.startswith("\\\\"):
            raise ValueError("network and device database paths are not allowed")
        if _WINDOWS_SYSTEM_PATH.match(raw_path) or _WINDOWS_SYSTEM_PATH.match(
            resolved_windows
        ):
            raise ValueError("system directory database paths are not allowed")
        resolved_posix = resolved.as_posix()
        if any(
            resolved_posix == prefix or resolved_posix.startswith(prefix + "/")
            for prefix in _POSIX_SYSTEM_PREFIXES
        ):
            raise ValueError("system directory database paths are not allowed")

    @contextmanager
    def _connection(self, require_existing: bool = True):
        self._validate_database_path()
        if require_existing and not self.db_path.is_file():
            raise RuntimeError("database is not initialized")
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def initialize(self) -> None:
        self._validate_database_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection(require_existing=False) as connection:
            for statement in CREATE_SCHEMA_SQL:
                connection.execute(statement)
            connection.execute(
                """
                INSERT INTO schema_meta(key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
                """,
                ("schema_version", SCHEMA_VERSION, _utc_timestamp()),
            )

    def get_schema_version(self) -> str:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT value FROM schema_meta WHERE key = ?",
                ("schema_version",),
            ).fetchone()
        if row is None:
            raise RuntimeError("schema version is missing")
        return str(row["value"])

    def insert_scan(
        self,
        scan_id: str,
        created_at: str,
        platform: str,
        privacy_mode: str,
        source: str,
        notes: Optional[str] = None,
    ) -> None:
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO scans(scan_id, created_at, platform, privacy_mode, source, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (scan_id, created_at, platform, privacy_mode, source, notes),
            )

    def insert_scan_target(
        self,
        target_id: str,
        scan_id: str,
        object_type: str,
        name: str,
        publisher: Optional[str] = None,
        version: Optional[str] = None,
        path: Optional[str] = None,
        source: Optional[str] = None,
        first_seen: Optional[str] = None,
        last_seen: Optional[str] = None,
        normalized_identity: Optional[str] = None,
    ) -> None:
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO scan_targets(
                    target_id, scan_id, object_type, name, publisher, version, path,
                    source, first_seen, last_seen, normalized_identity
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    target_id,
                    scan_id,
                    object_type,
                    name,
                    publisher,
                    version,
                    path,
                    source,
                    first_seen,
                    last_seen,
                    normalized_identity,
                ),
            )

    def insert_policy_decision(
        self,
        decision_id: str,
        scan_id: str,
        target_id: str,
        created_at: str,
        classification: str,
        risk_level: str,
        permission_level: str,
        allowed: bool,
        required_confirmation: bool,
        audit_required: bool,
        blocked_by_hard_rule: bool,
        reason: str,
        evidence: object,
    ) -> None:
        evidence_json = json.dumps(evidence, ensure_ascii=False, separators=(",", ":"))
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO policy_decisions(
                    decision_id, scan_id, target_id, created_at, classification,
                    risk_level, permission_level, allowed, required_confirmation,
                    audit_required, blocked_by_hard_rule, reason, evidence_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    decision_id,
                    scan_id,
                    target_id,
                    created_at,
                    classification,
                    risk_level,
                    permission_level,
                    int(bool(allowed)),
                    int(bool(required_confirmation)),
                    int(bool(audit_required)),
                    int(bool(blocked_by_hard_rule)),
                    reason,
                    evidence_json,
                ),
            )

    def insert_audit_event_index(
        self,
        event_id: str,
        jsonl_path: str,
        jsonl_line: int,
        timestamp: str,
        action: str,
        result: str,
        dry_run: bool,
        scan_id: Optional[str] = None,
        plan_id: Optional[str] = None,
        target_id: Optional[str] = None,
        classification: Optional[str] = None,
    ) -> None:
        if dry_run is not True:
            raise ValueError("PR4 indexes dry-run audit events only")
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO audit_event_index(
                    event_id, scan_id, plan_id, target_id, jsonl_path, jsonl_line,
                    timestamp, action, classification, result, dry_run
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    scan_id,
                    plan_id,
                    target_id,
                    jsonl_path,
                    jsonl_line,
                    timestamp,
                    action,
                    classification,
                    result,
                    1,
                ),
            )

    def upsert_user_preference(
        self,
        preference_id: str,
        target_key: str,
        preference_type: str,
        value: str,
        created_at: str,
        updated_at: str,
        notes: Optional[str] = None,
    ) -> None:
        if preference_type not in _PREFERENCE_TYPES:
            raise ValueError("unsupported preference_type")
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO user_preferences(
                    preference_id, target_key, preference_type, value,
                    created_at, updated_at, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(preference_id) DO UPDATE SET
                    target_key = excluded.target_key,
                    preference_type = excluded.preference_type,
                    value = excluded.value,
                    updated_at = excluded.updated_at,
                    notes = excluded.notes
                """,
                (
                    preference_id,
                    target_key,
                    preference_type,
                    value,
                    created_at,
                    updated_at,
                    notes,
                ),
            )

    def get_scan_targets(self, scan_id: str) -> list[dict]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM scan_targets WHERE scan_id = ? ORDER BY target_id",
                (scan_id,),
            ).fetchall()
        return [_row_to_dict(row) for row in rows]

    def get_policy_decisions_for_target(self, target_id: str) -> list[dict]:
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM policy_decisions
                WHERE target_id = ? ORDER BY created_at, decision_id
                """,
                (target_id,),
            ).fetchall()
        decisions = []
        for row in rows:
            decision = _row_to_dict(row)
            decision["allowed"] = bool(decision["allowed"])
            decision["required_confirmation"] = bool(
                decision["required_confirmation"]
            )
            decision["audit_required"] = bool(decision["audit_required"])
            decision["blocked_by_hard_rule"] = bool(
                decision["blocked_by_hard_rule"]
            )
            decision["evidence"] = json.loads(decision.pop("evidence_json"))
            decisions.append(decision)
        return decisions

    def get_user_preferences(self, target_key: str) -> list[dict]:
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM user_preferences
                WHERE target_key = ? ORDER BY preference_id
                """,
                (target_key,),
            ).fetchall()
        return [_row_to_dict(row) for row in rows]
