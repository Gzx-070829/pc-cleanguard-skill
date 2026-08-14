# External Executor Boundary

Guard Core defines only `ExecutorProtocol`. It contains no `subprocess`, shell,
PowerShell, cmd, uninstall, registry, service, startup, task, network, or external
tool runner.

An external executor may act only on a valid, unexpired `ExecutionContract`, using
the exact authorized targets and effect. It must re-check contract binding, report
results and postconditions, and implement rollback separately. Legacy L1 cleanup
and quarantine implementations remain compatibility executors and are not Guard
dependencies.

