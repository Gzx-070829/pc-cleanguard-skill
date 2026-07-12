"""Offline source-pack contract for evidence-only reputation records."""

ALLOWED_SEED_SOURCE_TYPES = frozenset({
    "public_regulatory_notice",
    "public_vendor_behavior_article",
    "community_report",
    "synthetic_example",
})

ALLOWED_SEED_REVIEW_STATUSES = frozenset({
    "needs_human_review",
    "approved_for_explanation",
})

