# Rollback Contract

L2, L3, and L4 cannot receive an `ExecutionContract` without a bound,
non-expired rollback contract/plan. It identifies the decision and action
fingerprint, reversibility, backup need/reference, rollback steps, verification
steps, and expiry.

L2/L4 require reversible contracts; L4 also requires a referenced backup. L3
requires a documented rollback plan even where an uninstall is not perfectly
reversible. The Guard validates the contract but never performs rollback. Batch
results expose reverse dependency order for a host/executor to use after partial
failure.

