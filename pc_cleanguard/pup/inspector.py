"""Combine local seed loading, matching, and insight generation."""

from __future__ import annotations

from pathlib import Path

from ..reputation.insight import build_pup_insight
from ..reputation.matcher import ReputationMatcher
from ..reputation.reporting import render_pup_insight_markdown
from ..reputation.seed_loader import load_seed_records
from ..reputation.evidence_pack_loader import load_evidence_pack


def inspect_pup_risk(report: dict, seed_path: str | Path, *, evidence_pack: bool = False) -> dict:
    records = load_evidence_pack(seed_path) if evidence_pack else load_seed_records(seed_path)
    matches = ReputationMatcher(records).match(report)
    insight = build_pup_insight(matches)
    return {
        "matches": matches,
        "match_count": len(matches),
        "insight": insight,
        "markdown": render_pup_insight_markdown(insight),
        "execution_authorized": False,
    }

