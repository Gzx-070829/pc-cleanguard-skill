"""Execution-time target revalidation and TOCTOU protection."""

from __future__ import annotations

from pathlib import PureWindowsPath
from typing import Any, Mapping

from ..protection import classify_developer_path
from .models import (
    GuardContext,
    GuardDecision,
    PreconditionName,
    PreconditionValidation,
    Requirement,
)
from .normalize import canonical_value


def _inside_scope(path: str, roots: list[str]) -> bool:
    try:
        candidate = PureWindowsPath(path)
        return any(
            candidate == PureWindowsPath(root)
            or candidate.is_relative_to(PureWindowsPath(root))
            for root in roots
        )
    except (TypeError, ValueError):
        return False


def _current_fact(context: GuardContext, identifier: str) -> dict:
    value = context.target_facts.get(identifier, {})
    return dict(value) if isinstance(value, Mapping) else {}


def _status_protects(status: Mapping[str, Any], identifier: str) -> bool:
    values = [status.get(identifier)]
    values.extend(status.get(key) for key in ("protected", "blocked", "is_protected"))
    return any(
        value is True
        or (
            isinstance(value, Mapping)
            and any(value.get(key) is True for key in ("protected", "blocked", "is_protected"))
        )
        for value in values
    )


def _protected_by_user_policy(
    context: GuardContext,
    identifier: str,
    path: str | None,
) -> bool:
    targets = context.user_policy.get("protected_targets", [])
    if not isinstance(targets, list):
        return True
    if identifier in targets or (path is not None and path in targets):
        return True

    protected_paths = context.user_policy.get("protected_paths", [])
    if not isinstance(protected_paths, list) or any(
        not isinstance(root, str) or not root.strip() for root in protected_paths
    ):
        return True
    if path is not None and protected_paths and _inside_scope(path, protected_paths):
        return True

    code_roots = context.user_policy.get("user_code_roots", [])
    if not isinstance(code_roots, list) or any(
        not isinstance(root, str) or not root.strip() for root in code_roots
    ):
        return True
    return bool(
        path is not None
        and code_roots
        and classify_developer_path(path, user_code_roots=code_roots).protected
    )


def validate_preconditions(
    decision: GuardDecision,
    current_context: GuardContext,
) -> PreconditionValidation:
    """Compare current structured facts with the policy-time snapshot."""

    if not isinstance(decision, GuardDecision) or not isinstance(current_context, GuardContext):
        return PreconditionValidation(
            False,
            (),
            (Requirement.TARGET_REVALIDATION.value,),
            ("decision and current_context must be Guard contracts",),
            {},
        )

    needs_revalidation = Requirement.TARGET_REVALIDATION in decision.requirements
    if not needs_revalidation:
        return PreconditionValidation(True, (), (), (), {"targets": {}})

    checked: list[str] = []
    failed: list[str] = []
    errors: list[str] = []
    observed: dict[str, Any] = {"targets": {}, "scope": canonical_value(current_context.scope)}
    expected_targets = decision.preconditions_snapshot.get("targets", {})
    roots = decision.scope_snapshot.get("allowed_paths", [])
    if not isinstance(roots, list):
        roots = []

    def check(name: PreconditionName, condition: bool, message: str) -> None:
        checked.append(name.value)
        if not condition:
            failed.append(name.value)
            errors.append(message)

    for identifier, expected_entry in expected_targets.items():
        expected = dict(expected_entry.get("facts", {}))
        current = _current_fact(current_context, identifier)
        observed["targets"][identifier] = canonical_value(current)

        check(
            PreconditionName.TARGET_EXISTS,
            current.get("exists") is True,
            f"{identifier}: target no longer exists",
        )
        check(
            PreconditionName.TARGET_TYPE_MATCH,
            current.get("target_type") == expected.get("target_type"),
            f"{identifier}: target type changed",
        )
        if "sha256" in expected:
            check(
                PreconditionName.HASH_MATCH,
                current.get("sha256") == expected.get("sha256"),
                f"{identifier}: target hash changed after evaluation",
            )
        if "size_bytes" in expected:
            check(
                PreconditionName.SIZE_MATCH,
                current.get("size_bytes") == expected.get("size_bytes"),
                f"{identifier}: target size changed after evaluation",
            )
        if "mtime_ns" in expected:
            check(
                PreconditionName.MTIME_MATCH,
                current.get("mtime_ns") == expected.get("mtime_ns"),
                f"{identifier}: target modification time changed after evaluation",
            )
        elif "mtime" in expected:
            check(
                PreconditionName.MTIME_MATCH,
                current.get("mtime") == expected.get("mtime"),
                f"{identifier}: target modification time changed after evaluation",
            )

        expected_path = expected.get("path")
        current_path = current.get("path")
        path_matches = isinstance(expected_path, str) and current_path == expected_path
        scope_matches = path_matches and bool(roots) and _inside_scope(current_path, roots)
        check(
            PreconditionName.PATH_SCOPE_MATCH,
            scope_matches,
            f"{identifier}: target path changed or is outside the evaluated scope",
        )
        check(
            PreconditionName.NOT_REPARSE_POINT,
            current.get("is_reparse_point") is False,
            f"{identifier}: target is or became a reparse point",
        )
        protected = current.get("protected") is True
        if isinstance(current_path, str):
            protected = protected or classify_developer_path(current_path).protected
        protected = protected or _status_protects(
            current_context.protected_status,
            identifier,
        )
        protected = protected or _status_protects(
            current_context.developer_status,
            identifier,
        )
        protected = protected or _protected_by_user_policy(
            current_context,
            identifier,
            current_path if isinstance(current_path, str) else None,
        )
        check(
            PreconditionName.NOT_PROTECTED,
            not protected,
            f"{identifier}: target is protected at execution time",
        )

    if Requirement.BACKUP in decision.requirements:
        check(
            PreconditionName.BACKUP_PRESENT,
            current_context.preconditions.get(PreconditionName.BACKUP_PRESENT.value) is True,
            "required backup is not present",
        )
    if Requirement.ROLLBACK_CONTRACT in decision.requirements or Requirement.ROLLBACK_PLAN in decision.requirements:
        check(
            PreconditionName.ROLLBACK_READY,
            current_context.preconditions.get(PreconditionName.ROLLBACK_READY.value) is True,
            "rollback is not ready",
        )

    return PreconditionValidation(
        not failed,
        tuple(dict.fromkeys(checked)),
        tuple(dict.fromkeys(failed)),
        tuple(errors),
        canonical_value(observed),
    )
