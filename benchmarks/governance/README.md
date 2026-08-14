# Governance Acceptance Benchmark

This fixed, synthetic, offline suite tests policy determinism, forbidden-action
blocking, consent binding, target revalidation, rollback completeness, audit
integrity, batch maximum restriction, Agent-reason invariance, and monotonic
safety. It measures governance correctness—not Agent intelligence.

Release gate: `failed`, `authorization_failures`, `monotonicity_failures`, and
`audit_failures` must all be zero.

