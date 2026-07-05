"""SQLite reputation knowledge store: evidence, not execution authority."""

from __future__ import annotations

from typing import Optional

from ..state.sqlite_store import SQLiteStateStore, _row_to_dict
from .reputation_models import (
    ReputationConflict,
    ReputationEntry,
    ReputationEvidence,
    ReputationSource,
)


def _normalize_identity(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("identity must be a non-empty string")
    return " ".join(value.casefold().split())


class ReputationKnowledgeStore:
    """Store reputation evidence and metadata without producing actions."""

    def __init__(self, state_store: SQLiteStateStore):
        if not isinstance(state_store, SQLiteStateStore):
            raise TypeError("state_store must be a SQLiteStateStore")
        state_store.get_schema_version()
        self.state_store = state_store

    def insert_source(self, source: ReputationSource) -> None:
        if not isinstance(source, ReputationSource):
            raise TypeError("source must be a ReputationSource")
        with self.state_store._connection() as connection:
            connection.execute(
                """
                INSERT INTO reputation_sources(
                    source_id, source_name, source_type, trust_tier, homepage,
                    license, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source.source_id,
                    source.source_name,
                    source.source_type.value,
                    source.trust_tier,
                    source.homepage,
                    source.license,
                    source.notes,
                    source.created_at,
                    source.updated_at,
                ),
            )

    def insert_entry(self, entry: ReputationEntry) -> None:
        if not isinstance(entry, ReputationEntry):
            raise TypeError("entry must be a ReputationEntry")
        with self.state_store._connection() as connection:
            connection.execute(
                """
                INSERT INTO reputation_entries(
                    entry_id, canonical_name, publisher, category,
                    suggested_classification, confidence, severity,
                    false_positive_risk, review_status, first_seen,
                    last_updated, rulepack_version, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.entry_id,
                    entry.canonical_name,
                    entry.publisher,
                    entry.category.value,
                    entry.suggested_classification.value,
                    float(entry.confidence),
                    entry.severity,
                    entry.false_positive_risk,
                    entry.review_status.value,
                    entry.first_seen,
                    entry.last_updated,
                    entry.rulepack_version,
                    entry.notes,
                ),
            )

    def insert_evidence(self, evidence: ReputationEvidence) -> None:
        if not isinstance(evidence, ReputationEvidence):
            raise TypeError("evidence must be a ReputationEvidence")
        with self.state_store._connection() as connection:
            connection.execute(
                """
                INSERT INTO reputation_evidence(
                    evidence_id, entry_id, source_id, evidence_type, summary,
                    confidence, observed_behavior, version_range, path_pattern,
                    startup_indicator, service_indicator,
                    network_reputation_summary, source_reference, license_note,
                    captured_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    evidence.evidence_id,
                    evidence.entry_id,
                    evidence.source_id,
                    evidence.evidence_type.value,
                    evidence.summary,
                    float(evidence.confidence),
                    evidence.observed_behavior,
                    evidence.version_range,
                    evidence.path_pattern,
                    evidence.startup_indicator,
                    evidence.service_indicator,
                    evidence.network_reputation_summary,
                    evidence.source_reference,
                    evidence.license_note,
                    evidence.captured_at,
                ),
            )

    def insert_conflict(self, conflict: ReputationConflict) -> None:
        if not isinstance(conflict, ReputationConflict):
            raise TypeError("conflict must be a ReputationConflict")
        with self.state_store._connection() as connection:
            connection.execute(
                """
                INSERT INTO reputation_conflicts(
                    conflict_id, entry_id, conflict_type, positive_summary,
                    negative_summary, resolution_note, requires_user_context,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    conflict.conflict_id,
                    conflict.entry_id,
                    conflict.conflict_type,
                    conflict.positive_summary,
                    conflict.negative_summary,
                    conflict.resolution_note,
                    int(conflict.requires_user_context),
                    conflict.created_at,
                ),
            )

    def insert_software_alias(
        self,
        alias_id: str,
        entry_id: str,
        alias: str,
        created_at: str,
    ) -> None:
        normalized_alias = _normalize_identity(alias)
        with self.state_store._connection() as connection:
            connection.execute(
                """
                INSERT INTO software_aliases(
                    alias_id, entry_id, alias, normalized_alias, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (alias_id, entry_id, alias, normalized_alias, created_at),
            )

    def insert_publisher_alias(
        self,
        alias_id: str,
        canonical_publisher: str,
        alias: str,
        created_at: str,
    ) -> None:
        normalized_alias = _normalize_identity(alias)
        with self.state_store._connection() as connection:
            connection.execute(
                """
                INSERT INTO publisher_aliases(
                    alias_id, canonical_publisher, alias, normalized_alias,
                    created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    alias_id,
                    canonical_publisher,
                    alias,
                    normalized_alias,
                    created_at,
                ),
            )

    def insert_vendor_uninstaller(
        self,
        uninstaller_id: str,
        vendor_name: str,
        method_type: str,
        method_summary: str,
        created_at: str,
        entry_id: Optional[str] = None,
        rollback_notes: Optional[str] = None,
    ) -> None:
        with self.state_store._connection() as connection:
            connection.execute(
                """
                INSERT INTO vendor_uninstallers(
                    uninstaller_id, entry_id, vendor_name, method_type,
                    method_summary, requires_confirmation, rollback_notes,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    uninstaller_id,
                    entry_id,
                    vendor_name,
                    method_type,
                    method_summary,
                    1,
                    rollback_notes,
                    created_at,
                ),
            )

    def insert_rulepack_version(
        self,
        rulepack_id: str,
        name: str,
        version: str,
        source: str,
        loaded_at: str,
        checksum: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> None:
        with self.state_store._connection() as connection:
            connection.execute(
                """
                INSERT INTO rulepack_versions(
                    rulepack_id, name, version, source, loaded_at, checksum, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (rulepack_id, name, version, source, loaded_at, checksum, notes),
            )

    def find_entries_by_name(self, name: str) -> list[dict]:
        normalized_name = _normalize_identity(name)
        with self.state_store._connection() as connection:
            rows = connection.execute(
                """
                SELECT DISTINCT entry.*
                FROM reputation_entries AS entry
                LEFT JOIN software_aliases AS alias
                    ON alias.entry_id = entry.entry_id
                WHERE entry.canonical_name = ? COLLATE NOCASE
                    OR alias.normalized_alias = ?
                ORDER BY entry.entry_id
                """,
                (name.strip(), normalized_name),
            ).fetchall()
        return [_row_to_dict(row) for row in rows]

    def get_evidence_for_entry(self, entry_id: str) -> list[dict]:
        with self.state_store._connection() as connection:
            rows = connection.execute(
                """
                SELECT evidence.*, source.source_name, source.source_type,
                    source.trust_tier
                FROM reputation_evidence AS evidence
                JOIN reputation_sources AS source
                    ON source.source_id = evidence.source_id
                WHERE evidence.entry_id = ?
                ORDER BY evidence.captured_at, evidence.evidence_id
                """,
                (entry_id,),
            ).fetchall()
        return [_row_to_dict(row) for row in rows]

    def get_conflicts_for_entry(self, entry_id: str) -> list[dict]:
        with self.state_store._connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM reputation_conflicts
                WHERE entry_id = ? ORDER BY created_at, conflict_id
                """,
                (entry_id,),
            ).fetchall()
        conflicts = []
        for row in rows:
            conflict = _row_to_dict(row)
            conflict["requires_user_context"] = bool(
                conflict["requires_user_context"]
            )
            conflicts.append(conflict)
        return conflicts
