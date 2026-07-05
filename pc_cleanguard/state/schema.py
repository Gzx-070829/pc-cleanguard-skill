"""Internal SQLite schema for PR4 state and reputation evidence."""

SCHEMA_VERSION = "0.1.0-pr4"

# SQLite stores evidence and history; it does not execute system operations.
CREATE_SCHEMA_SQL = (
    """
    CREATE TABLE IF NOT EXISTS schema_meta (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS scans (
        scan_id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        platform TEXT NOT NULL,
        privacy_mode TEXT NOT NULL,
        source TEXT NOT NULL,
        notes TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS scan_targets (
        target_id TEXT PRIMARY KEY,
        scan_id TEXT NOT NULL,
        object_type TEXT NOT NULL,
        name TEXT NOT NULL,
        publisher TEXT,
        version TEXT,
        path TEXT,
        source TEXT,
        first_seen TEXT,
        last_seen TEXT,
        normalized_identity TEXT,
        FOREIGN KEY(scan_id) REFERENCES scans(scan_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS policy_decisions (
        decision_id TEXT PRIMARY KEY,
        scan_id TEXT NOT NULL,
        target_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        classification TEXT NOT NULL,
        risk_level TEXT NOT NULL,
        permission_level TEXT NOT NULL,
        allowed INTEGER NOT NULL CHECK(allowed IN (0, 1)),
        required_confirmation INTEGER NOT NULL CHECK(required_confirmation IN (0, 1)),
        audit_required INTEGER NOT NULL CHECK(audit_required IN (0, 1)),
        blocked_by_hard_rule INTEGER NOT NULL CHECK(blocked_by_hard_rule IN (0, 1)),
        reason TEXT NOT NULL,
        evidence_json TEXT NOT NULL,
        FOREIGN KEY(scan_id) REFERENCES scans(scan_id),
        FOREIGN KEY(target_id) REFERENCES scan_targets(target_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS audit_event_index (
        event_id TEXT PRIMARY KEY,
        scan_id TEXT,
        plan_id TEXT,
        target_id TEXT,
        jsonl_path TEXT NOT NULL,
        jsonl_line INTEGER NOT NULL CHECK(jsonl_line > 0),
        timestamp TEXT NOT NULL,
        action TEXT NOT NULL,
        classification TEXT,
        result TEXT NOT NULL,
        dry_run INTEGER NOT NULL CHECK(dry_run = 1),
        FOREIGN KEY(target_id) REFERENCES scan_targets(target_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS user_preferences (
        preference_id TEXT PRIMARY KEY,
        target_key TEXT NOT NULL,
        preference_type TEXT NOT NULL CHECK(
            preference_type IN ('keep', 'remove', 'ignore', 'suspicion', 'core_tool')
        ),
        value TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        notes TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reputation_sources (
        source_id TEXT PRIMARY KEY,
        source_name TEXT NOT NULL,
        source_type TEXT NOT NULL,
        trust_tier TEXT NOT NULL,
        homepage TEXT,
        license TEXT,
        notes TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reputation_entries (
        entry_id TEXT PRIMARY KEY,
        canonical_name TEXT NOT NULL,
        publisher TEXT,
        category TEXT NOT NULL,
        suggested_classification TEXT NOT NULL CHECK(
            suggested_classification IN (
                'ASK_USER', 'STARTUP_OFF', 'SAFE_REMOVE_CANDIDATE',
                'QUARANTINE_CANDIDATE'
            )
        ),
        confidence REAL NOT NULL CHECK(confidence >= 0.0 AND confidence <= 1.0),
        severity TEXT NOT NULL,
        false_positive_risk TEXT NOT NULL,
        review_status TEXT NOT NULL,
        first_seen TEXT NOT NULL,
        last_updated TEXT NOT NULL,
        rulepack_version TEXT,
        notes TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reputation_evidence (
        evidence_id TEXT PRIMARY KEY,
        entry_id TEXT NOT NULL,
        source_id TEXT NOT NULL,
        evidence_type TEXT NOT NULL,
        summary TEXT NOT NULL,
        confidence REAL NOT NULL CHECK(confidence >= 0.0 AND confidence <= 1.0),
        observed_behavior TEXT,
        version_range TEXT,
        path_pattern TEXT,
        startup_indicator TEXT,
        service_indicator TEXT,
        network_reputation_summary TEXT,
        source_reference TEXT,
        license_note TEXT,
        captured_at TEXT NOT NULL,
        FOREIGN KEY(entry_id) REFERENCES reputation_entries(entry_id),
        FOREIGN KEY(source_id) REFERENCES reputation_sources(source_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reputation_conflicts (
        conflict_id TEXT PRIMARY KEY,
        entry_id TEXT NOT NULL,
        conflict_type TEXT NOT NULL,
        positive_summary TEXT,
        negative_summary TEXT,
        resolution_note TEXT,
        requires_user_context INTEGER NOT NULL CHECK(requires_user_context IN (0, 1)),
        created_at TEXT NOT NULL,
        FOREIGN KEY(entry_id) REFERENCES reputation_entries(entry_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS software_aliases (
        alias_id TEXT PRIMARY KEY,
        entry_id TEXT NOT NULL,
        alias TEXT NOT NULL,
        normalized_alias TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(entry_id) REFERENCES reputation_entries(entry_id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_software_aliases_normalized
        ON software_aliases(normalized_alias)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_reputation_entries_name
        ON reputation_entries(canonical_name COLLATE NOCASE)
    """,
    """
    CREATE TABLE IF NOT EXISTS publisher_aliases (
        alias_id TEXT PRIMARY KEY,
        canonical_publisher TEXT NOT NULL,
        alias TEXT NOT NULL,
        normalized_alias TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS vendor_uninstallers (
        uninstaller_id TEXT PRIMARY KEY,
        entry_id TEXT,
        vendor_name TEXT NOT NULL,
        method_type TEXT NOT NULL,
        method_summary TEXT NOT NULL,
        requires_confirmation INTEGER NOT NULL CHECK(requires_confirmation = 1),
        rollback_notes TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(entry_id) REFERENCES reputation_entries(entry_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS rulepack_versions (
        rulepack_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        version TEXT NOT NULL,
        source TEXT NOT NULL,
        loaded_at TEXT NOT NULL,
        checksum TEXT,
        notes TEXT
    )
    """,
)
