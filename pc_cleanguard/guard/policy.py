"""Deterministic Windows policy evaluation with monotonic risk merging."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from ..protection import classify_developer_path
from .errors import GuardInputError
from .models import (
    ActionRequest,
    Disposition,
    GuardContext,
    GuardDecision,
    GuardRiskLevel,
    Requirement,
    RiskSignal,
    decision_fingerprint_for,
)
from .normalize import canonical_value, require_local_path


DEFAULT_POLICY_PATH = Path(__file__).resolve().parents[2] / "policies" / "windows-default.json"

_LEVEL_REQUIREMENTS = {
    GuardRiskLevel.L0: (),
    GuardRiskLevel.L1: (
        Requirement.USER_CONFIRMATION,
        Requirement.TARGET_REVALIDATION,
        Requirement.AUDIT,
    ),
    GuardRiskLevel.L2: (
        Requirement.USER_CONFIRMATION,
        Requirement.ROLLBACK_CONTRACT,
        Requirement.TARGET_REVALIDATION,
        Requirement.AUDIT,
        Requirement.POSTCONDITION_VERIFY,
    ),
    GuardRiskLevel.L3: (
        Requirement.USER_CONFIRMATION,
        Requirement.ROLLBACK_PLAN,
        Requirement.TARGET_REVALIDATION,
        Requirement.AUDIT,
        Requirement.POSTCONDITION_VERIFY,
    ),
    GuardRiskLevel.L4: (
        Requirement.EXPLICIT_HIGH_RISK_CONFIRMATION,
        Requirement.ADMIN_ACKNOWLEDGEMENT,
        Requirement.BACKUP,
        Requirement.ROLLBACK_CONTRACT,
        Requirement.TARGET_REVALIDATION,
        Requirement.AUDIT,
        Requirement.POSTCONDITION_VERIFY,
    ),
    GuardRiskLevel.L5: (),
}

_READ_PREFIXES = ("read", "get", "list", "inspect", "scan", "preview", "report", "explain", "verify")

_HARD_BLOCK_PARTS = {
    "system32",
    "syswow64",
    "winsxs",
    "boot",
    "recovery",
    "system volume information",
    "$recycle.bin",
    "credentials",
    "credential manager",
    "password manager",
    "passwords",
    "microsoft\\protect",
    "windows defender",
    "securityhealth",
    "desktop",
    "documents",
    "pictures",
    "photos",
    "videos",
    "桌面",
    "文档",
    "图片",
    "照片",
    "视频",
}

_BROWSER_PROFILE_PATTERNS = (
    "\\google\\chrome\\user data\\",
    "\\microsoft\\edge\\user data\\",
    "\\mozilla\\firefox\\profiles\\",
    "\\bravesoftware\\brave-browser\\user data\\",
    "\\opera software\\opera stable\\",
)


def load_policy_pack(path: str | Path | None = None) -> dict:
    source = DEFAULT_POLICY_PATH if path is None else Path(path)
    require_local_path(source, name="policy path")
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise GuardInputError(f"unable to load deterministic policy pack: {source}") from error
    if not isinstance(data, dict) or set(data) != {"policy_id", "version", "platform", "rules"}:
        raise GuardInputError("policy pack must contain policy_id/version/platform/rules")
    if data["platform"] != "windows" or not isinstance(data["rules"], list) or not data["rules"]:
        raise GuardInputError("policy pack must define non-empty Windows rules")
    seen = set()
    for rule in data["rules"]:
        required = {
            "rule_id", "action_types", "conditions", "risk_level", "disposition",
            "requirements", "reason",
        }
        if not isinstance(rule, dict) or set(rule) != required:
            raise GuardInputError("every policy rule must use the stable rule contract")
        if rule["rule_id"] in seen:
            raise GuardInputError("policy rule IDs must be unique")
        seen.add(rule["rule_id"])
        try:
            GuardRiskLevel(rule["risk_level"])
            Disposition(rule["disposition"])
            tuple(Requirement(item) for item in rule["requirements"])
        except (TypeError, ValueError) as error:
            raise GuardInputError(f"invalid policy rule: {rule['rule_id']}") from error
    return canonical_value(data)


def _truthy_status(status: Mapping[str, Any], identifier: str) -> bool:
    values = []
    if identifier in status:
        values.append(status[identifier])
    for key in ("protected", "blocked", "is_protected"):
        if key in status:
            values.append(status[key])
    for value in values:
        if value is True:
            return True
        if isinstance(value, Mapping) and any(
            value.get(key) is True for key in ("protected", "blocked", "is_protected")
        ):
            return True
    return False


def _path_block_reason(path: str | None) -> str | None:
    if path is None:
        return None
    folded = path.replace("/", "\\").casefold()
    if folded.startswith("\\\\"):
        return "UNC/network mutation targets are outside the local Windows guard scope"
    parts = tuple(part for part in folded.split("\\") if part)
    if "*" in folded or "?" in folded:
        return "wildcard or unbounded target paths are forbidden"
    for protected in sorted(_HARD_BLOCK_PARTS):
        if "\\" in protected:
            if protected in folded:
                return f"target is inside protected Windows data: {protected}"
        elif protected in parts:
            return f"target contains protected path component: {protected}"
    if any(pattern in folded for pattern in _BROWSER_PROFILE_PATTERNS):
        return "target is inside a protected browser profile"
    developer = classify_developer_path(path)
    if developer.protected:
        return developer.reason
    return None


def _hard_block_reasons(request: ActionRequest, context: GuardContext) -> tuple[str, ...]:
    reasons = []
    action = request.action_type.casefold()
    effect = request.requested_effect.casefold()
    if action in {
        "policy_bypass", "bypass_policy", "wildcard_delete", "bulk_delete_unbounded",
        "delete_credential", "delete_security_software", "boot_mutation", "recovery_mutation",
    }:
        reasons.append("action type is forbidden by the L5 policy boundary")
    if any(token in action for token in ("bypass_policy", "force_allow")):
        reasons.append("attempts to bypass deterministic policy are forbidden")
    if ("*" in effect or "wildcard" in effect) and any(
        token in action for token in ("delete", "remove", "mutat", "clean")
    ):
        reasons.append("unbounded wildcard mutation is forbidden")
    if request.parameters.get("bypass_policy") is True or request.parameters.get("force_allow") is True:
        reasons.append("structured policy-bypass parameters are forbidden")
    if request.parameters.get("authorization_source") in {
        "agent", "ai", "reputation", "pup", "community", "evidence",
    }:
        reasons.append("untrusted intelligence cannot be an authorization source")
    for target in request.targets:
        reason = _path_block_reason(target.path)
        if reason:
            reasons.append(f"{target.identifier}: {reason}")
        code_roots = context.user_policy.get("user_code_roots", [])
        if not isinstance(code_roots, list) or any(
            not isinstance(root, str) or not root.strip() for root in code_roots
        ):
            reasons.append("user policy contains invalid user_code_roots")
        elif target.path is not None and code_roots:
            developer = classify_developer_path(
                target.path,
                user_code_roots=code_roots,
            )
            if developer.protected:
                reasons.append(f"{target.identifier}: {developer.reason}")
        if _truthy_status(context.protected_status, target.identifier):
            reasons.append(f"{target.identifier}: context marks target protected")
        if _truthy_status(context.developer_status, target.identifier):
            reasons.append(f"{target.identifier}: context marks target developer-protected")
        facts = context.target_facts.get(target.identifier, {})
        if isinstance(facts, Mapping) and facts.get("protected") is True:
            reasons.append(f"{target.identifier}: current target facts mark target protected")
        protected_targets = context.user_policy.get("protected_targets", [])
        if isinstance(protected_targets, list) and (
            target.identifier in protected_targets
            or (target.path is not None and target.path in protected_targets)
        ):
            reasons.append(f"{target.identifier}: user policy marks target protected")
        protected_paths = context.user_policy.get("protected_paths", [])
        if isinstance(protected_paths, list) and target.path is not None:
            folded_path = target.path.casefold().replace("/", "\\")
            if any(
                isinstance(root, str)
                and folded_path.startswith(root.casefold().replace("/", "\\").rstrip("\\") + "\\")
                for root in protected_paths
            ):
                reasons.append(f"{target.identifier}: target is under a user-policy protected path")
    denied_actions = context.user_policy.get("deny_action_types", [])
    if isinstance(denied_actions, list) and request.action_type in denied_actions:
        reasons.append("user policy explicitly denies this action type")
    if context.system_status.get("policy_bypass_requested") is True:
        reasons.append("system context reports a policy-bypass request")
    return tuple(dict.fromkeys(reasons))


def _match_action_rule(action_type: str, policy: dict) -> dict | None:
    folded = action_type.casefold()
    for rule in policy["rules"]:
        types = tuple(item.casefold() for item in rule["action_types"])
        if "*" not in types and folded in types:
            return rule
    return None


def _snapshot(request: ActionRequest, context: GuardContext) -> dict:
    targets = {}
    for target in request.targets:
        facts = dict(target.observed_state)
        current = context.target_facts.get(target.identifier)
        if isinstance(current, Mapping):
            facts.update(canonical_value(dict(current)))
        if target.path is not None:
            facts.setdefault("path", target.path)
        facts.setdefault("target_type", target.target_type)
        targets[target.identifier] = {
            "target_fingerprint": target.target_fingerprint,
            "facts": facts,
        }
    return {
        "targets": targets,
        "scope": canonical_value(context.scope),
        "context_preconditions": canonical_value(context.preconditions),
    }


def _build_decision(
    *,
    request: ActionRequest,
    context: GuardContext,
    policy: dict,
    disposition: Disposition,
    risk_level: GuardRiskLevel,
    requirements: Iterable[Requirement],
    matched_rules: Iterable[str],
    blocked_reasons: Iterable[str],
    explanation: str,
) -> GuardDecision:
    requirement_values = tuple(sorted(set(requirements), key=lambda item: item.value))
    matched = tuple(dict.fromkeys(matched_rules))
    blocked = tuple(dict.fromkeys(blocked_reasons))
    snapshot = _snapshot(request, context)
    policy_version = f"{policy['policy_id']}/{policy['version']}"
    target_fingerprints = tuple(item.target_fingerprint for item in request.targets)
    decision_fingerprint = decision_fingerprint_for(
        request_id=request.request_id,
        action_fingerprint=request.action_fingerprint,
        target_fingerprints=target_fingerprints,
        requested_effect=request.requested_effect,
        scope_snapshot=context.scope,
        preconditions_snapshot=snapshot,
        policy_version=policy_version,
        disposition=disposition,
        risk_level=risk_level,
        requirements=requirement_values,
        matched_rules=matched,
        blocked_reasons=blocked,
        generated_at=request.requested_at,
    )
    return GuardDecision(
        decision_id=f"decision:{decision_fingerprint[:24]}",
        request_id=request.request_id,
        disposition=disposition,
        risk_level=risk_level,
        requirements=requirement_values,
        matched_rules=matched,
        blocked_reasons=blocked,
        explanation=explanation,
        decision_fingerprint=decision_fingerprint,
        execution_authorized=False,
        generated_at=request.requested_at,
        action_fingerprint=request.action_fingerprint,
        target_fingerprints=target_fingerprints,
        requested_effect=request.requested_effect,
        scope_snapshot=context.scope,
        preconditions_snapshot=snapshot,
        policy_version=policy_version,
    )


def evaluate(
    request: ActionRequest | Mapping[str, Any],
    context: GuardContext | Mapping[str, Any],
    policy: dict | str | Path | None = None,
) -> GuardDecision:
    """Evaluate structured inputs only; no I/O other than loading a local policy pack."""

    if not isinstance(request, ActionRequest):
        request = ActionRequest.from_dict(request)
    if not isinstance(context, GuardContext):
        context = GuardContext.from_dict(context)
    if policy is None or isinstance(policy, (str, Path)):
        policy_pack = load_policy_pack(policy)
    elif isinstance(policy, dict):
        policy_pack = canonical_value(policy)
        # Reuse the same validation without accepting an implicit mutable pack.
        required = {"policy_id", "version", "platform", "rules"}
        if set(policy_pack) != required or policy_pack.get("platform") != "windows":
            raise GuardInputError("invalid in-memory policy pack")
    else:
        raise GuardInputError("policy must be a path, object, or None")

    hard_blocks = _hard_block_reasons(request, context)
    if hard_blocks:
        decision = _build_decision(
            request=request,
            context=context,
            policy=policy_pack,
            disposition=Disposition.BLOCK,
            risk_level=GuardRiskLevel.L5,
            requirements=(),
            matched_rules=("windows.hard-block",),
            blocked_reasons=hard_blocks,
            explanation="L5 policy blocked a forbidden or protected Windows action.",
        )
        return merge_risk_signals(decision, context.risk_signals)

    rule = _match_action_rule(request.action_type, policy_pack)
    if rule is None:
        if request.action_type.casefold().startswith(_READ_PREFIXES):
            risk = GuardRiskLevel.L0
            disposition = Disposition.ALLOW
            requirements = ()
            matched_rules = ("windows.read-only-fallback",)
            reason = "Structured action is read-only and has no mutation effect."
        else:
            risk = GuardRiskLevel.L5
            disposition = Disposition.BLOCK
            requirements = ()
            matched_rules = ("windows.unknown-mutation-fail-closed",)
            reason = "Unknown mutation action is blocked until a deterministic rule exists."
            hard_blocks = (reason,)
    else:
        risk = GuardRiskLevel(rule["risk_level"])
        disposition = Disposition(rule["disposition"])
        requirements = tuple(Requirement(item) for item in rule["requirements"])
        expected = _LEVEL_REQUIREMENTS[risk]
        if not set(expected).issubset(requirements):
            raise GuardInputError(f"policy rule {rule['rule_id']} weakens L{risk.rank} requirements")
        matched_rules = (rule["rule_id"],)
        reason = rule["reason"]

    decision = _build_decision(
        request=request,
        context=context,
        policy=policy_pack,
        disposition=disposition,
        risk_level=risk,
        requirements=requirements,
        matched_rules=matched_rules,
        blocked_reasons=hard_blocks,
        explanation=reason,
    )
    return merge_risk_signals(decision, context.risk_signals)


def merge_risk_signals(
    decision: GuardDecision,
    signals: Iterable[RiskSignal | Mapping[str, Any]],
) -> GuardDecision:
    """Merge restriction-only intelligence without creating authorization."""

    if not isinstance(decision, GuardDecision):
        raise GuardInputError("decision must be a GuardDecision")
    normalized = tuple(
        signal if isinstance(signal, RiskSignal) else RiskSignal.from_dict(signal)
        for signal in signals
    )
    if not normalized:
        return decision

    risk = decision.risk_level
    disposition = decision.disposition
    requirements = set(decision.requirements)
    matched = list(decision.matched_rules)
    blocked = list(decision.blocked_reasons)
    for signal in normalized:
        if signal.severity.rank > risk.rank:
            risk = signal.severity
        requirements.update(signal.requirements)
        matched.append(f"risk-signal:{signal.source}:{signal.signal_type}")
        if signal.block or signal.severity is GuardRiskLevel.L5:
            disposition = Disposition.BLOCK
            blocked.append(f"untrusted signal raised a block: {signal.reason}")
        elif disposition is Disposition.ALLOW and signal.severity.rank > 0:
            disposition = Disposition.REQUIRE
            requirements.add(Requirement.ADMIN_ACKNOWLEDGEMENT)

    # A raised level carries every deterministic baseline gate for that level.
    # Signals may therefore add restrictions, but can never create a high-risk
    # label backed by a lower-risk authorization contract.
    requirements.update(_LEVEL_REQUIREMENTS[risk])

    if decision.disposition is Disposition.BLOCK:
        disposition = Disposition.BLOCK
    if disposition is Disposition.BLOCK and not blocked:
        blocked.append("risk signal raised the decision to a hard block")
    final_matched = tuple(dict.fromkeys(matched))
    final_blocked = tuple(dict.fromkeys(blocked))
    merged_fingerprint = decision_fingerprint_for(
        request_id=decision.request_id,
        action_fingerprint=decision.action_fingerprint,
        target_fingerprints=decision.target_fingerprints,
        requested_effect=decision.requested_effect,
        scope_snapshot=decision.scope_snapshot,
        preconditions_snapshot=decision.preconditions_snapshot,
        policy_version=decision.policy_version,
        disposition=disposition,
        risk_level=risk,
        requirements=tuple(requirements),
        matched_rules=final_matched,
        blocked_reasons=final_blocked,
        generated_at=decision.generated_at,
    )
    return GuardDecision(
        decision_id=f"decision:{merged_fingerprint[:24]}",
        request_id=decision.request_id,
        disposition=disposition,
        risk_level=risk,
        requirements=tuple(requirements),
        matched_rules=final_matched,
        blocked_reasons=final_blocked,
        explanation=(
            decision.explanation
            + " Untrusted intelligence was applied as restriction-only input."
        ),
        decision_fingerprint=merged_fingerprint,
        execution_authorized=False,
        generated_at=decision.generated_at,
        action_fingerprint=decision.action_fingerprint,
        target_fingerprints=decision.target_fingerprints,
        requested_effect=decision.requested_effect,
        scope_snapshot=decision.scope_snapshot,
        preconditions_snapshot=decision.preconditions_snapshot,
        policy_version=decision.policy_version,
    )
