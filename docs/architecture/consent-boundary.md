# Consent Boundary

A `ConsentGrant` is an expiring capability-like statement bound to one decision,
action fingerprint, exact ordered targets, effect, scope, confirmation level, and
confirmation source. Validation rejects expiry, future issuance, mismatched
decision/fingerprint/target/effect/scope, weak confirmation, and explicitly
self-asserted Agent sources.

`"user_confirmed": true` in an Agent request is ordinary untrusted input. It is
never a grant. The integrating host or trusted UI must authenticate the human and
construct the grant. PC CleanGuard validates binding; it does not claim to be an
OS identity or signature boundary.

