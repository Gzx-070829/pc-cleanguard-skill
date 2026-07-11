"""Validated JSON contracts for reversible quarantine items."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple


def validated_evidence(evidence: Iterable[dict]) -> Tuple[dict, ...]:
    items = tuple(evidence)
    if not items or any(
        not isinstance(item, dict)
        or not isinstance(item.get("source"), str)
        or not item["source"].strip()
        or not isinstance(item.get("fact"), str)
        or not item["fact"].strip()
        for item in items
    ):
        raise ValueError("evidence must contain source/fact objects")
    return tuple(
        {"source": item["source"].strip(), "fact": item["fact"].strip()}
        for item in items
    )


@dataclass(frozen=True, slots=True)
class QuarantineItem:
    item_id: str
    original_path: str
    quarantine_path: str
    sha256: str
    size_bytes: int
    original_mtime: float
    reason: str
    evidence: Tuple[dict, ...]
    created_at: str
    restored_at: str | None = None
    status: str = "active"

    def __post_init__(self) -> None:
        for name in (
            "item_id", "original_path", "quarantine_path", "sha256",
            "reason", "created_at",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if len(self.sha256) != 64 or any(c not in "0123456789abcdef" for c in self.sha256):
            raise ValueError("sha256 must be a lowercase SHA-256 digest")
        if not isinstance(self.size_bytes, int) or isinstance(self.size_bytes, bool) or self.size_bytes < 0:
            raise ValueError("size_bytes must be a non-negative integer")
        if not isinstance(self.original_mtime, (int, float)) or isinstance(self.original_mtime, bool):
            raise ValueError("original_mtime must be numeric")
        if self.status not in {"active", "restored"}:
            raise ValueError("unsupported quarantine item status")
        if self.status == "active" and self.restored_at is not None:
            raise ValueError("active items cannot have restored_at")
        if self.status == "restored" and not self.restored_at:
            raise ValueError("restored items require restored_at")
        object.__setattr__(self, "evidence", validated_evidence(self.evidence))

    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "original_path": self.original_path,
            "quarantine_path": self.quarantine_path,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "original_mtime": self.original_mtime,
            "reason": self.reason,
            "evidence": [dict(item) for item in self.evidence],
            "created_at": self.created_at,
            "restored_at": self.restored_at,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "QuarantineItem":
        if not isinstance(data, dict):
            raise TypeError("quarantine item must be an object")
        return cls(**{**data, "evidence": tuple(data.get("evidence", ()))})


@dataclass(frozen=True, slots=True)
class QuarantineManifest:
    root: str
    items: Tuple[QuarantineItem, ...]
    updated_at: str
    schema_version: str = "0.3"

    def __post_init__(self) -> None:
        if self.schema_version != "0.3":
            raise ValueError("unsupported quarantine manifest version")
        if not isinstance(self.root, str) or not self.root.strip():
            raise ValueError("root must be a non-empty string")
        if not isinstance(self.updated_at, str) or not self.updated_at.strip():
            raise ValueError("updated_at must be a non-empty string")
        if not all(isinstance(item, QuarantineItem) for item in self.items):
            raise TypeError("items must contain QuarantineItem objects")
        ids = [item.item_id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("quarantine item IDs must be unique")

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "root": self.root,
            "updated_at": self.updated_at,
            "items": [item.to_dict() for item in self.items],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "QuarantineManifest":
        if not isinstance(data, dict):
            raise TypeError("manifest must be an object")
        if set(data) != {"schema_version", "root", "updated_at", "items"}:
            raise ValueError("unexpected quarantine manifest fields")
        return cls(
            schema_version=data["schema_version"],
            root=data["root"],
            updated_at=data["updated_at"],
            items=tuple(QuarantineItem.from_dict(item) for item in data["items"]),
        )
