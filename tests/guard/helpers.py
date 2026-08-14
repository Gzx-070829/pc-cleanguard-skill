"""Fixed, synthetic Guard fixtures."""

from __future__ import annotations

from pc_cleanguard.guard import (
    ActionRequest,
    ActionTarget,
    ConsentGrant,
    GuardContext,
    RollbackContract,
)


NOW = "2026-01-01T00:00:00Z"
LATER = "2026-01-01T01:00:00Z"
HASH_A = "a" * 64


def target(path: str = r"C:\Temp\fixture.tmp", *, identifier: str = "target-1") -> ActionTarget:
    return ActionTarget(
        target_type="file",
        identifier=identifier,
        path=path,
        metadata={"category": "temp_file"},
        observed_state={
            "exists": True,
            "target_type": "file",
            "sha256": HASH_A,
            "size_bytes": 7,
            "mtime_ns": 100,
            "is_reparse_point": False,
        },
    )


def request(
    action_type: str = "delete_temp_file",
    *,
    request_id: str = "request-1",
    path: str = r"C:\Temp\fixture.tmp",
    reason: str = "synthetic request",
    parameters: dict | None = None,
    requested_effect: str = "remove one synthetic temp file",
) -> ActionRequest:
    return ActionRequest(
        request_id=request_id,
        action_type=action_type,
        targets=(target(path),),
        parameters=parameters or {},
        requested_effect=requested_effect,
        requested_at=NOW,
        agent_id="test-agent",
        agent_reason=reason,
        evidence_refs=(),
        dry_run=False,
    )


def context(
    *,
    path: str = r"C:\Temp\fixture.tmp",
    sha256: str = HASH_A,
    extra_preconditions: dict | None = None,
) -> GuardContext:
    preconditions = {
        "BACKUP_PRESENT": True,
        "ROLLBACK_READY": True,
    }
    preconditions.update(extra_preconditions or {})
    return GuardContext(
        platform="windows",
        scope={"allowed_paths": [r"C:\Temp"]},
        target_facts={
            "target-1": {
                "path": path,
                "exists": True,
                "target_type": "file",
                "sha256": sha256,
                "size_bytes": 7,
                "mtime_ns": 100,
                "is_reparse_point": False,
            }
        },
        protected_status={},
        developer_status={},
        system_status={},
        user_policy={},
        preconditions=preconditions,
    )


def consent_for(decision, *, expires_at: str = LATER, level: str = "STANDARD") -> ConsentGrant:
    return ConsentGrant(
        consent_id="consent-1",
        decision_id=decision.decision_id,
        action_fingerprint=decision.action_fingerprint,
        allowed_targets=decision.target_fingerprints,
        allowed_effect=decision.requested_effect,
        allowed_scope=decision.scope_snapshot,
        issued_at=NOW,
        expires_at=expires_at,
        confirmation_level=level,
        confirmation_source="trusted-test-host",
    )


def rollback_for(decision, *, backup_required: bool = False) -> RollbackContract:
    return RollbackContract(
        rollback_id="rollback-1",
        decision_id=decision.decision_id,
        action_fingerprint=decision.action_fingerprint,
        reversible=True,
        backup_required=backup_required,
        backup_reference="backup:test" if backup_required else None,
        rollback_steps=("restore synthetic target",),
        verification_steps=("verify synthetic target state",),
        expires_at=LATER,
    )
