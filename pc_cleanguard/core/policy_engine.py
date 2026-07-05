"""Pure, conservative policy evaluation for PC CleanGuard PR1.

The module performs no I/O, process invocation, networking, deletion,
uninstallation, registry access, or filesystem mutation.
"""

from __future__ import annotations

from typing import Iterable

from .models import (
    ClassificationLabel,
    EvidenceChain,
    GovernanceTarget,
    ObjectType,
    PermissionLevel,
    PolicyDecision,
    RiskLevel,
)


_WINDOWS_PROTECTED_PREFIXES = (
    "c:\\windows",
    "c:\\programdata\\microsoft\\crypto",
    "c:\\programdata\\microsoft\\protect",
)

_PROTECTED_PATH_PARTS = (
    "\\documents\\",
    "\\desktop\\",
    "\\pictures\\",
    "\\videos\\",
    "\\microsoft\\credentials\\",
    "\\system32\\driverstore\\",
    "\\google\\chrome\\user data\\",
    "\\mozilla\\firefox\\profiles\\",
    "\\microsoft\\edge\\user data\\",
    "\\password vault\\",
    "\\recovery\\",
)

_CODE_REPOSITORY_PARTS = (
    "\\.git\\",
    "\\source\\repos\\",
    "\\code\\repositories\\",
)

_DRIVER_VENDORS = ("nvidia", "amd", "advanced micro devices", "intel")
_DRIVER_TERMS = ("driver", "display", "graphics", "chipset", "control panel")

_DEVELOPER_TOOL_TERMS = (
    "python",
    "node.js",
    "nodejs",
    "conda",
    "anaconda",
    "miniconda",
    "git",
    "docker",
    "cuda",
    "visual studio build tools",
)

_ORGANIZATIONAL_OR_SECURITY_TERMS = (
    "vpn",
    "school",
    "campus",
    "enterprise",
    "endpoint protection",
    "antivirus",
    "security agent",
    "edr",
)


def _normalize_path(path: str | None) -> str:
    if not path:
        return ""
    return path.replace("/", "\\").strip().rstrip("\\").casefold()


def _contains_any(value: str, terms: Iterable[str]) -> bool:
    return any(term in value for term in terms)


def _is_sensitive_path(target: GovernanceTarget) -> bool:
    path = _normalize_path(target.path)
    protected_sources = {
        "authentication_component",
        "bitlocker_component",
        "browser_profile",
        "code_repository",
        "credential_store",
        "password_manager",
        "recovery_partition",
        "security_software_core",
        "tpm_component",
        "unknown_bulk_file_group",
        "unknown_cleanup_script",
    }
    if not path:
        return target.source.casefold() in protected_sources

    if any(
        path == prefix or path.startswith(prefix + "\\")
        for prefix in _WINDOWS_PROTECTED_PREFIXES
    ):
        return True

    padded = path + "\\"
    if _contains_any(padded, _PROTECTED_PATH_PARTS):
        return True
    if _contains_any(padded, _CODE_REPOSITORY_PARTS):
        return True
    if path.endswith("\\.git"):
        return True
    return target.source.casefold() in protected_sources


def _is_user_temp(path: str | None) -> bool:
    normalized = _normalize_path(path)
    return "\\appdata\\local\\temp\\" in normalized + "\\"


def _evidence(target: GovernanceTarget, reason: str) -> EvidenceChain:
    current = target.evidence_chain
    sources = current.sources or (target.source or "policy_engine",)
    facts = current.facts + (reason,)
    return EvidenceChain(
        sources=sources,
        facts=facts,
        references=current.references,
        confidence=max(current.confidence, 0.5),
    )


def _decision(
    target: GovernanceTarget,
    classification: ClassificationLabel,
    risk_level: RiskLevel,
    permission_level: PermissionLevel,
    reason: str,
    *,
    allowed: bool = False,
    required_confirmation: bool = False,
    rollback_required: bool = False,
    blocked_by_hard_rule: bool = False,
) -> PolicyDecision:
    audit_required = classification is not ClassificationLabel.KEEP
    evidence = _evidence(target, reason)
    return PolicyDecision(
        target_id=target.target_id,
        classification=classification,
        risk_level=risk_level,
        permission_level=permission_level,
        allowed=allowed,
        reason=reason,
        evidence_chain=evidence,
        required_confirmation=required_confirmation,
        rollback_required=rollback_required,
        audit_required=audit_required,
        blocked_by_hard_rule=blocked_by_hard_rule,
    )


def _keep(target: GovernanceTarget, reason: str) -> PolicyDecision:
    return _decision(
        target,
        ClassificationLabel.KEEP,
        RiskLevel.LOW,
        PermissionLevel.LEVEL_0_READ_ONLY,
        reason,
    )


def _ask_user(target: GovernanceTarget, reason: str) -> PolicyDecision:
    return _decision(
        target,
        ClassificationLabel.ASK_USER,
        RiskLevel.MEDIUM,
        PermissionLevel.LEVEL_0_READ_ONLY,
        reason,
        required_confirmation=True,
    )


def evaluate_target(target: GovernanceTarget) -> PolicyDecision:
    """Return a policy decision without performing any action."""

    name = target.name.casefold()
    publisher = (target.publisher or "").casefold()
    combined_identity = f"{name} {publisher}"

    # Hard rules always run first and cannot be bypassed by user preferences.
    if _is_sensitive_path(target):
        return _decision(
            target,
            ClassificationLabel.BLOCK,
            RiskLevel.CRITICAL,
            PermissionLevel.LEVEL_5_FORBIDDEN,
            "The target is inside a protected system, user-data, credential, browser, recovery, or code-repository location.",
            blocked_by_hard_rule=True,
        )

    # Explicit user core declarations protect the object, including reputation conflicts.
    if target.user_declared_core:
        return _keep(
            target,
            "The user declared this object a core tool; reputation or preference signals cannot authorize removal.",
        )

    if "visual c++" in name and ("redistributable" in name or "redist" in name):
        return _keep(target, "Microsoft Visual C++ Redistributable is a shared runtime dependency.")

    if (
        ".net runtime" in name
        or "dotnet runtime" in name
        or "windows desktop runtime" in name
    ):
        return _keep(target, ".NET runtime components are shared application dependencies.")

    if "directx" in name and ("runtime" in name or "redistributable" in name):
        return _keep(target, "DirectX runtime components are shared graphics dependencies.")

    if _contains_any(combined_identity, _DRIVER_VENDORS) and _contains_any(
        name, _DRIVER_TERMS
    ):
        return _keep(target, "NVIDIA, AMD, or Intel driver components are protected by default.")

    if _contains_any(combined_identity, _DEVELOPER_TOOL_TERMS):
        return _keep(
            target,
            "Developer runtimes and toolchains are preserved by default because project dependencies may be implicit.",
        )

    if _contains_any(combined_identity, _ORGANIZATIONAL_OR_SECURITY_TERMS):
        return _keep(
            target,
            "VPN, school, enterprise, and security software are protected by default.",
        )

    # Untrusted recommendations may only lower confidence or request review.
    destructive_labels = {
        ClassificationLabel.SAFE_REMOVE,
        ClassificationLabel.QUARANTINE,
        ClassificationLabel.BLOCK,
    }
    if target.community_recommendation in destructive_labels or (
        target.source.casefold() == "community_rule"
        and target.requested_classification in destructive_labels
    ):
        return _ask_user(
            target,
            "A community rule requested a destructive classification; community input cannot authorize deletion and was downgraded.",
        )

    if (
        target.source.casefold() in {"ai", "ai_judgment"}
        and not target.evidence_chain.has_substantive_evidence
    ):
        return _ask_user(
            target,
            "An AI judgment labeled the target as harmful without substantive evidence; only user review is permitted.",
        )

    if target.online_reputation and target.online_reputation.casefold() in {
        "pup",
        "malicious",
        "suspicious",
    }:
        return _ask_user(
            target,
            "Online reputation is an advisory signal only and cannot directly authorize removal.",
        )

    if (
        target.object_type is ObjectType.STARTUP_ITEM
        and ("toolbar" in name or target.suspicious)
    ):
        return _decision(
            target,
            ClassificationLabel.STARTUP_OFF,
            RiskLevel.MEDIUM,
            PermissionLevel.LEVEL_2_REVERSIBLE,
            "The startup item appears non-essential or suspicious; only a future reversible disable candidate is appropriate.",
            allowed=True,
            required_confirmation=True,
            rollback_required=True,
        )

    if target.known_bloatware and target.uninstall_available:
        return _decision(
            target,
            ClassificationLabel.SAFE_REMOVE,
            RiskLevel.MEDIUM,
            PermissionLevel.LEVEL_3_STANDARD_UNINSTALL,
            "The software matches a known bloatware rule and exposes a standard uninstaller; it is a candidate only.",
            allowed=True,
            required_confirmation=True,
        )

    if (
        target.object_type is ObjectType.FILE
        and target.suspicious
        and _is_user_temp(target.path)
    ):
        return _decision(
            target,
            ClassificationLabel.QUARANTINE,
            RiskLevel.HIGH,
            PermissionLevel.LEVEL_2_REVERSIBLE,
            "A suspicious file is located in the user's temporary directory; only a future reversible quarantine candidate is appropriate.",
            allowed=True,
            required_confirmation=True,
            rollback_required=True,
        )

    if target.object_type is ObjectType.SOFTWARE and not target.uninstall_available:
        return _ask_user(
            target,
            "The software is unknown and has no standard uninstaller; removal is not authorized.",
        )

    return _ask_user(
        target,
        "No conservative allow rule applies; collect more evidence and ask the user before any proposed change.",
    )
