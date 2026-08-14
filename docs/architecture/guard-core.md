# Guard Core

PC CleanGuard v0.5 is a deterministic Windows contract authority between an AI
Agent and an external executor. Its responsibilities are limited to Policy,
Consent, Preconditions, Audit, and Rollback.

```text
ActionRequest -> Policy -> Consent/Preconditions/Rollback
              -> ExecutionContract -> external executor -> Audit receipt
```

The public facade is `Guard` with four principal operations: `evaluate`,
`prepare_execution`, `record_execution_result`, and `verify_audit`. Core code uses
the standard library and the existing Developer Guard path classifier. It does
not import Cleaner, PUP, Reputation, Persistence, collectors, AI providers, or
executors.

The Guard is not a sandbox or kernel boundary. The integrating host must route
relevant actions through it.

