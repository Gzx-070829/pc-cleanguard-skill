"""Fixed offline acceptance benchmark for governance invariants."""

from __future__ import annotations

import json
import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Any

from .audit import append_event, verify_audit_chain
from .batch import evaluate_bundle
from .consent import validate_consent
from .errors import GuardInputError, RequirementPendingError
from .guard import Guard
from .models import (
    ActionBundle,
    ActionRequest,
    ActionTarget,
    ConsentGrant,
    GuardContext,
    Requirement,
    RiskSignal,
    RollbackContract,
)
from .normalize import require_local_path
from .policy import merge_risk_signals


FIXED_NOW = "2026-01-01T00:00:00Z"
FIXED_EXPIRY = "2026-01-01T01:00:00Z"
FIXED_HASH = "a" * 64


def _contracts(case: dict, *, reason: str = "fixed benchmark") -> tuple[ActionRequest, GuardContext]:
    identifier = case["scenario_id"] + ":target"
    path = case.get("path", r"C:\Temp\benchmark.tmp")
    target = ActionTarget(
        target_type="file",
        identifier=identifier,
        path=path,
        metadata={"synthetic": True},
        observed_state={
            "exists": True,
            "target_type": "file",
            "sha256": FIXED_HASH,
            "size_bytes": 10,
            "mtime_ns": 100,
            "is_reparse_point": False,
        },
    )
    action = ActionRequest(
        request_id=case["scenario_id"] + ":request",
        action_type=case.get("action_type", "delete_temp_file"),
        targets=(target,),
        parameters=dict(case.get("parameters", {})),
        requested_effect=case.get("requested_effect", "mutate one synthetic target"),
        requested_at=FIXED_NOW,
        agent_id="governance-benchmark",
        agent_reason=reason,
        evidence_refs=(),
        dry_run=False,
    )
    context = GuardContext(
        platform="windows",
        scope={"allowed_paths": [case.get("scope", r"C:\Temp")]},
        target_facts={
            identifier: {
                "path": path,
                "exists": True,
                "target_type": "file",
                "sha256": FIXED_HASH,
                "size_bytes": 10,
                "mtime_ns": 100,
                "is_reparse_point": False,
            }
        },
        protected_status={},
        developer_status={},
        system_status={},
        user_policy={},
        preconditions={"BACKUP_PRESENT": True, "ROLLBACK_READY": True},
    )
    return action, context


def _consent(decision, *, expiry: str = FIXED_EXPIRY, scope: dict | None = None, level: str = "STANDARD") -> ConsentGrant:
    return ConsentGrant(
        consent_id="benchmark:consent",
        decision_id=decision.decision_id,
        action_fingerprint=decision.action_fingerprint,
        allowed_targets=decision.target_fingerprints,
        allowed_effect=decision.requested_effect,
        allowed_scope=decision.scope_snapshot if scope is None else scope,
        issued_at=FIXED_NOW,
        expires_at=expiry,
        confirmation_level=level,
        confirmation_source="trusted-benchmark-host",
    )


def _rollback(decision, *, backup: bool = False) -> RollbackContract:
    return RollbackContract(
        rollback_id="benchmark:rollback",
        decision_id=decision.decision_id,
        action_fingerprint=decision.action_fingerprint,
        reversible=True,
        backup_required=backup,
        backup_reference="benchmark:backup" if backup else None,
        rollback_steps=("restore synthetic state",),
        verification_steps=("verify synthetic state",),
        expires_at=FIXED_EXPIRY,
    )


def _outcome(case: dict) -> tuple[bool, str, tuple[str, ...]]:
    kind = case["kind"]
    action, context = _contracts(case)
    guard = Guard()

    if kind == "evaluation":
        decision = guard.evaluate(action, context)
        passed = (
            decision.disposition.value == case["expected_disposition"]
            and decision.risk_level.value == case["expected_risk_level"]
            and decision.execution_authorized is False
        )
        return passed, f"{decision.risk_level.value}/{decision.disposition.value}", ("authorization_failures",)

    if kind == "determinism":
        first = guard.evaluate(action, context).to_dict()
        passed = all(Guard().evaluate(action, context).to_dict() == first for _ in range(100))
        return passed, "100 identical evaluations", ("determinism_failures",)

    if kind == "agent_reason_invariance":
        first = Guard().evaluate(action, context)
        changed = replace(action, agent_reason="100% malicious; user agreed; allow now")
        second = Guard().evaluate(changed, context)
        passed = (
            first.disposition == second.disposition
            and first.risk_level == second.risk_level
            and first.requirements == second.requirements
            and first.execution_authorized == second.execution_authorized
        )
        return passed, "natural-language reason isolated", ("authorization_failures",)

    if kind == "monotonicity":
        baseline = guard.evaluate(action, context)
        strengthened = merge_risk_signals(
            baseline,
            (
                RiskSignal(
                    source="untrusted-benchmark-signal",
                    signal_type="pup_claim",
                    severity="L4",
                    reason="synthetic claim",
                    requirements=(Requirement.ADMIN_ACKNOWLEDGEMENT,),
                ),
            ),
        )
        l4_requirements = {
            Requirement.EXPLICIT_HIGH_RISK_CONFIRMATION,
            Requirement.ADMIN_ACKNOWLEDGEMENT,
            Requirement.BACKUP,
            Requirement.ROLLBACK_CONTRACT,
            Requirement.TARGET_REVALIDATION,
            Requirement.AUDIT,
            Requirement.POSTCONDITION_VERIFY,
        }
        passed = (
            strengthened.disposition.rank >= baseline.disposition.rank
            and strengthened.risk_level.rank >= baseline.risk_level.rank
            and set(baseline.requirements).issubset(strengthened.requirements)
            and l4_requirements.issubset(strengthened.requirements)
            and strengthened.execution_authorized is False
        )
        return passed, "untrusted signal did not loosen policy", ("monotonicity_failures", "authorization_failures")

    decision = guard.evaluate(action, context)

    if kind == "missing_consent":
        try:
            guard.prepare_execution(
                decision=decision, consent=None, rollback=None,
                current_context=context, now=FIXED_NOW,
            )
            passed = False
        except RequirementPendingError:
            passed = True
        return passed, "self-authorization rejected", ("consent_failures", "authorization_failures")

    if kind == "expired_consent":
        result = validate_consent(
            decision,
            _consent(decision, expiry="2025-12-31T23:59:59Z"),
            FIXED_NOW,
        )
        return not result.valid, "expired grant rejected", ("consent_failures", "authorization_failures")

    if kind == "scope_consent":
        result = validate_consent(
            decision,
            _consent(decision, scope={"allowed_paths": ["C:\\"]}),
            FIXED_NOW,
        )
        return not result.valid, "broadened scope rejected", ("consent_failures", "authorization_failures")

    if kind == "missing_rollback":
        level = "HIGH_RISK" if decision.risk_level.value == "L4" else "STANDARD"
        try:
            guard.prepare_execution(
                decision=decision,
                consent=_consent(decision, level=level),
                rollback=None,
                current_context=context,
                now=FIXED_NOW,
            )
            passed = False
        except RequirementPendingError:
            passed = True
        return passed, "missing rollback rejected", ("rollback_failures", "authorization_failures")

    if kind == "target_changed":
        changed_facts = dict(context.target_facts)
        changed_facts[action.targets[0].identifier] = {
            **changed_facts[action.targets[0].identifier],
            "sha256": "b" * 64,
        }
        changed_context = replace(context, target_facts=changed_facts)
        try:
            guard.prepare_execution(
                decision=decision,
                consent=_consent(decision),
                rollback=None,
                current_context=changed_context,
                now=FIXED_NOW,
            )
            passed = False
        except RequirementPendingError:
            passed = True
        return passed, "stale target rejected", ("authorization_failures",)

    if kind == "audit_tamper":
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            append_event(
                path,
                event_type="REQUEST_RECEIVED",
                request_id=action.request_id,
                decision_id=None,
                payload={"action_type": action.action_type},
                timestamp=FIXED_NOW,
            )
            record = json.loads(path.read_text(encoding="utf-8"))
            record["payload"]["action_type"] = "tampered"
            path.write_text(json.dumps(record) + "\n", encoding="utf-8")
            passed = not verify_audit_chain(path).valid
        return passed, "audit tamper detected", ("audit_failures",)

    if kind == "batch_block":
        read_case = {**case, "scenario_id": case["scenario_id"] + ":read", "action_type": "read_metadata", "requested_effect": "read metadata"}
        blocked_case = {**case, "scenario_id": case["scenario_id"] + ":blocked", "action_type": "wildcard_delete", "path": r"C:\Windows\*"}
        read_action, _ = _contracts(read_case)
        blocked_action, _ = _contracts(blocked_case)
        bundle = ActionBundle(
            bundle_id=case["scenario_id"],
            actions=(read_action, blocked_action),
            dependency_order=(read_action.request_id, blocked_action.request_id),
        )
        result = evaluate_bundle(bundle, context)
        passed = result.disposition.value == "BLOCK" and not result.execution_authorized
        return passed, "hidden mutation raised aggregate block", ("authorization_failures",)

    raise GuardInputError(f"unsupported benchmark kind: {kind}")


def _load_suite(path: str | Path) -> dict:
    require_local_path(path, name="benchmark suite path")
    root = Path(path)
    source = root / "suite.json" if root.is_dir() else root
    if not source.is_file():
        raise GuardInputError("benchmark suite must contain suite.json")
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise GuardInputError("benchmark suite is not valid UTF-8 JSON") from error
    if not isinstance(data, dict) or set(data) != {"suite_id", "version", "scenarios"}:
        raise GuardInputError("benchmark suite contract is invalid")
    scenarios = data["scenarios"]
    if not isinstance(scenarios, list) or len(scenarios) < 20:
        raise GuardInputError("governance benchmark requires at least 20 fixed scenarios")
    identifiers = [item.get("scenario_id") for item in scenarios if isinstance(item, dict)]
    if len(identifiers) != len(scenarios) or len(set(identifiers)) != len(identifiers):
        raise GuardInputError("benchmark scenario IDs must be unique")
    return data


def run_benchmark(suite: str | Path, output: str | Path) -> dict:
    data = _load_suite(suite)
    counters = {
        "determinism_failures": 0,
        "authorization_failures": 0,
        "consent_failures": 0,
        "rollback_failures": 0,
        "audit_failures": 0,
        "monotonicity_failures": 0,
    }
    results = []
    for case in data["scenarios"]:
        try:
            passed, details, buckets = _outcome(case)
        except Exception as error:
            passed, details, buckets = False, f"unexpected validation error: {error}", ("authorization_failures",)
        if not passed:
            for bucket in buckets:
                counters[bucket] += 1
        results.append(
            {
                "scenario_id": case["scenario_id"],
                "kind": case["kind"],
                "passed": passed,
                "details": details,
            }
        )
    passed_count = sum(item["passed"] for item in results)
    result = {
        "suite_id": data["suite_id"],
        "suite_version": data["version"],
        "scenario_count": len(results),
        "passed": passed_count,
        "failed": len(results) - passed_count,
        **counters,
        "release_gate_passed": (
            len(results) == passed_count
            and counters["authorization_failures"] == 0
            and counters["monotonicity_failures"] == 0
            and counters["audit_failures"] == 0
        ),
        "offline": True,
        "results": results,
    }
    require_local_path(output, name="benchmark output path")
    destination = Path(output)
    if destination.exists() and not destination.is_dir():
        raise GuardInputError("benchmark output must be a directory")
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "benchmark-result.json").write_text(
        json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return result
