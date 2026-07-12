"""Strict validation for local source manifests; no fetching occurs here."""

from __future__ import annotations

from .source_pack import ALLOWED_SEED_SOURCE_TYPES


def _valid_public_url(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    lowered = value.strip().casefold()
    return lowered.startswith(("https://", "http://")) and len(value.split("/", 3)) >= 3


def validate_source_manifest(manifest: dict) -> dict:
    if not isinstance(manifest, dict):
        raise TypeError("source manifest must be an object")
    required = {"pack_id", "language", "purpose", "execution_authorized", "sources"}
    if set(manifest) != required:
        raise ValueError("source manifest fields do not match the PR20 contract")
    if manifest["execution_authorized"] is not False:
        raise ValueError("source manifest cannot authorize execution")
    if (
        manifest["language"] != "zh-CN"
        or not isinstance(manifest["pack_id"], str)
        or not manifest["pack_id"].strip()
    ):
        raise ValueError("source manifest identity is invalid")
    if not isinstance(manifest["purpose"], str) or not manifest["purpose"].strip():
        raise ValueError("source manifest purpose is required")
    sources = manifest["sources"]
    if not isinstance(sources, list) or not sources:
        raise ValueError("source manifest requires sources")
    source_fields = {"source_id", "source_type", "source_name", "source_url", "license_note"}
    seen = set()
    for source in sources:
        if not isinstance(source, dict) or set(source) != source_fields:
            raise ValueError("invalid source manifest entry")
        if source["source_type"] not in ALLOWED_SEED_SOURCE_TYPES:
            raise ValueError("unsupported seed source type")
        if not _valid_public_url(source["source_url"]):
            raise ValueError("source_url must be an explicit HTTP(S) URL")
        for field in ("source_id", "source_name", "license_note"):
            if not isinstance(source[field], str) or not source[field].strip():
                raise ValueError(f"{field} must be non-empty")
        if source["source_id"] in seen:
            raise ValueError("source IDs must be unique")
        seen.add(source["source_id"])
    return manifest
