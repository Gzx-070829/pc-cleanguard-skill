# Audit Chain

Guard audit is an append-only local JSONL sequence. Each event contains its own
canonical SHA-256 hash and the previous event hash. Verification recomputes every
hash and link; changing any historical payload invalidates the chain.

Events cover request, decision, consent, precondition, contract issuance,
execution report, postcondition, and rollback lifecycle points. This provides
tamper evidence, not confidentiality, signatures, distributed consensus, or a
blockchain. Hosts must still protect file access and retention.

