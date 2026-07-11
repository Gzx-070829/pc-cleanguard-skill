"""Pure path classifier for developer assets that cleanup must preserve."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Tuple


DEVELOPER_PROTECTION_LEVEL = "PROTECTION_LEVEL_BLOCK_DEVELOPER_ASSET"
_NO_PROTECTION_LEVEL = "PROTECTION_LEVEL_NONE"

_COMPONENT_RULES = {
    ".git": "git_metadata",
    ".venv": "python_virtual_environment",
    "venv": "python_virtual_environment",
    "env": "python_virtual_environment",
    "node_modules": "node_dependency_tree",
    ".npm": "npm_cache",
    ".pnpm-store": "pnpm_store",
    ".yarn": "yarn_data",
    ".idea": "ide_metadata",
    ".vscode": "ide_metadata",
}


def _path_parts(path: str | Path) -> Tuple[str, ...]:
    if not isinstance(path, (str, Path)) or not str(path).strip():
        raise ValueError("path must be a non-empty local path")
    normalized = str(path).replace("\\", "/")
    return tuple(part.casefold() for part in normalized.split("/") if part)


def _contains_sequence(parts: Tuple[str, ...], sequence: Tuple[str, ...]) -> bool:
    width = len(sequence)
    return any(parts[index : index + width] == sequence for index in range(len(parts)))


def _matched_rule(parts: Tuple[str, ...]) -> str | None:
    for part in parts:
        if part in _COMPONENT_RULES:
            return _COMPONENT_RULES[part]
    if "envs" in parts and any("conda" in part for part in parts):
        return "conda_environment"
    if _contains_sequence(parts, ("pip", "cache")) or _contains_sequence(
        parts, (".cache", "pip")
    ):
        return "pip_cache"
    if ".cargo" in parts and ({"registry", "cache"}.intersection(parts)):
        return "cargo_registry_cache"
    if (
        ".gradle" in parts and {"cache", "caches"}.intersection(parts)
    ) or _contains_sequence(parts, ("gradle", "cache")):
        return "gradle_cache"
    if _contains_sequence(parts, (".m2", "repository")):
        return "maven_repository"
    if ".nv" in parts or "nv_cache" in parts:
        return "cuda_nvidia_cache"
    gpu_cache_names = {"computecache", "dxcache", "glcache", "cache"}
    if "nvidia" in parts and gpu_cache_names.intersection(parts):
        return "cuda_nvidia_cache"
    if "cuda" in parts and gpu_cache_names.intersection(parts):
        return "cuda_nvidia_cache"
    return None


@dataclass(frozen=True, slots=True)
class DeveloperGuardDecision:
    path: str
    protected: bool
    reason: str
    evidence: Tuple[dict, ...]
    protection_level: str
    matched_rule: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.path, str) or not self.path.strip():
            raise ValueError("path must be a non-empty string")
        if not isinstance(self.protected, bool):
            raise TypeError("protected must be a bool")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("reason must be a non-empty string")
        if not self.evidence or any(
            not isinstance(item, dict)
            or not isinstance(item.get("source"), str)
            or not item["source"].strip()
            or not isinstance(item.get("fact"), str)
            or not item["fact"].strip()
            for item in self.evidence
        ):
            raise ValueError("evidence must contain source/fact objects")
        expected = DEVELOPER_PROTECTION_LEVEL if self.protected else _NO_PROTECTION_LEVEL
        if self.protection_level != expected:
            raise ValueError("protection_level does not match protected state")
        if self.protected != (self.matched_rule is not None):
            raise ValueError("matched_rule does not match protected state")

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "protected": self.protected,
            "reason": self.reason,
            "evidence": [dict(item) for item in self.evidence],
            "protection_level": self.protection_level,
            "matched_rule": self.matched_rule,
            "execution_authorized": False,
        }


def _explicit_code_roots(user_code_roots: Iterable[str | Path]) -> Tuple[Path, ...]:
    if isinstance(user_code_roots, (str, Path)):
        raise TypeError("user_code_roots must be an iterable of explicit roots")
    roots = []
    for raw_root in user_code_roots:
        if not isinstance(raw_root, (str, Path)) or not str(raw_root).strip():
            raise ValueError("user code roots must be non-empty local paths")
        roots.append(Path(raw_root).resolve(strict=False))
    return tuple(roots)


def classify_developer_path(
    path: str | Path,
    *,
    user_code_roots: Iterable[str | Path] = (),
) -> DeveloperGuardDecision:
    """Classify one path without reading content or authorizing any action."""

    parts = _path_parts(path)
    candidate = Path(path).resolve(strict=False)
    for root in _explicit_code_roots(user_code_roots):
        if candidate == root or candidate.is_relative_to(root):
            reason = f"path is inside an explicit user code root: {root}"
            return DeveloperGuardDecision(
                path=str(path),
                protected=True,
                reason=reason,
                evidence=(
                    {"source": "developer_guard", "fact": reason},
                    {"source": "user_code_root", "fact": str(root)},
                ),
                protection_level=DEVELOPER_PROTECTION_LEVEL,
                matched_rule="user_code_root",
            )
    rule = _matched_rule(parts)
    if rule is not None:
        matched_component = next(
            (part for part in parts if _COMPONENT_RULES.get(part) == rule),
            rule,
        )
        reason = f"developer-protected path matched {rule}: {matched_component}"
        return DeveloperGuardDecision(
            path=str(path),
            protected=True,
            reason=reason,
            evidence=(
                {"source": "developer_guard", "fact": reason},
                {"source": "path_metadata", "fact": "classification used path components only"},
            ),
            protection_level=DEVELOPER_PROTECTION_LEVEL,
            matched_rule=rule,
        )
    return DeveloperGuardDecision(
        path=str(path),
        protected=False,
        reason="no developer-protected path rule matched",
        evidence=(
            {
                "source": "developer_guard",
                "fact": "no protected developer path component or explicit code root matched",
            },
        ),
        protection_level=_NO_PROTECTION_LEVEL,
        matched_rule=None,
    )


def is_protected_developer_path(
    path: str | Path,
    *,
    user_code_roots: Iterable[str | Path] = (),
) -> bool:
    return classify_developer_path(
        path,
        user_code_roots=user_code_roots,
    ).protected
