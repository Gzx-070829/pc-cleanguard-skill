# Deterministic Policy Model

The checked-in `policies/windows-default.json` contains structured rules. The only
dispositions are `ALLOW`, `REQUIRE`, and `BLOCK`; L0-L5 express risk/execution
level while `requirements` express independent gates.

Hard L5 blocks cover protected Windows/credential/security/boot/recovery targets,
developer assets, wildcard or unbounded mutation, and policy-bypass attempts.
Consent cannot override them.

The policy pack is trusted host configuration. An integrating host must never
accept a policy path or policy object from an untrusted Agent request. Custom
policy can add restrictions, but policy selection itself is outside the Agent's
authorization surface.

Untrusted signals obey monotonic safety: they may raise risk, add requirements, or
block, but may never loosen a decision. Agent prose and intelligence confidence do
not participate in base rule matching.
