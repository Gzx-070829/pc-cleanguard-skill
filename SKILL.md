---
name: pc-cleanguard-skill
description: Deterministically govern structured Windows system actions proposed by an AI Agent. Use to evaluate policy, surface consent/precondition/rollback requirements, issue a narrowly bound execution contract, record receipts, or verify a local audit chain. Legacy cleanup/PUP/persistence actions remain compatibility-only.
---

# PC CleanGuard Agent Governance Contract

Current public version: `0.5.0 Governance Re-foundation`.

PC CleanGuard 是 AI Agent 与 Windows 系统操作之间的确定性治理层。它不是
Cleaner、杀毒软件、Agent Runtime、sandbox 或通用 shell executor。

## Constitutional rule / 宪法原则

> Agent can propose an action, but it cannot authorize itself.

> Agent 可以很聪明，但授权必须是确定性的。

Natural-language reasoning is never an authorization source. `agent_reason`, AI
confidence, Reputation, PUP, Behavior, Evidence, community input, and Persistence
intelligence may explain or increase restrictions; they may never produce
`ALLOW`, Consent, or an ExecutionContract.

AI explanation ≠ execution authorization.
Reputation / Evidence / PUP / Persistence / Behavior ≠ execution authorization.

## Required Agent sequence

1. Normalize intent into an `ActionRequest`; never hide mutations in prose.
2. Call `evaluate_action` / `Guard.evaluate` with a structured `GuardContext`.
3. Surface `ALLOW`, `REQUIRE`, or `BLOCK`, risk level, matched rules, blocked
   reasons, and every requirement.
4. Never self-assert consent. A trusted host/UI must authenticate and bind a
   `ConsentGrant` to the exact decision, fingerprint, targets, effect, scope, and
   expiry.
5. Re-observe the target immediately before execution. Any path/type/hash/size/
   mtime/reparse/protection change invalidates the old decision.
6. Require a valid rollback contract or rollback plan for L2/L3/L4.
7. Call `prepare_execution`; only a returned `ExecutionContract` is an execution
   authorization for an external executor.
8. Send only the exact contract to an external executor; do not expand targets,
   effects, parameters, or scope.
9. Call `record_execution_result`, record postconditions, and verify the audit
   chain. On partial batch failure, use reverse rollback order.

## Primary core actions (exactly five)

```text
evaluate_action
prepare_execution
evaluate_action_bundle
record_execution_result
verify_audit
```

All five actions are deterministic, offline, machine-readable, and contain no
network/LLM/subprocess/executor behavior. `prepare_execution` may return an
authorized contract after all gates; invoking the Skill action itself performs no
Windows mutation.

Python callers use `invoke_guard_action`. The legacy `invoke_skill_action` entry
also dispatches these five names for migration compatibility.

## Policy levels

- L0: read-only; normally `ALLOW`.
- L1: narrow low-risk mutation; confirmation + revalidation + audit.
- L2: reversible filesystem mutation; L1 + rollback contract + postcondition.
- L3: official uninstall contract; confirmation + rollback plan + revalidation +
  audit + postcondition. Guard does not invoke the uninstaller.
- L4: registry/service/startup/task/browser system mutation; explicit high-risk
  confirmation + admin acknowledgement + backup + rollback + revalidation +
  audit + postcondition. Guard does not execute it.
- L5: protected system/credential/boot/security/wildcard/bypass action; always
  `BLOCK`.

Consent can satisfy requirements; it can never change `BLOCK` to `ALLOW`.

## Monotonic safety

Untrusted information may increase risk, add requirements, or block. It must
never lower risk, remove a requirement, or make a disposition less restrictive.
Two requests with identical structured action facts but different
`agent_reason` values must have identical authorization fields.

## Executor boundary

The Guard defines `ExecutorProtocol` but ships no general executor. Never invoke
PowerShell, cmd, shell, subprocess, uninstall strings, registry/service/task
tools, network clients, or LLM providers from Guard Core. The external executor
must reject expired contracts and any target/effect mismatch.

## Consent trust boundary

`"user_confirmed": true` inside an Agent payload is not consent. Reject expired,
wrong-decision, wrong-fingerprint, target-substituted, effect-changed,
scope-broadened, or under-strength grants. Consent authenticity belongs to the
integrating host/trusted UI; PC CleanGuard is not an OS identity boundary.

## Protected targets

Hard protection includes Windows/System32, boot/recovery, credentials/password
stores, security cores, broad wildcard mutations, Desktop/Documents/media,
browser profiles, code repositories, `.git`, virtualenvs, `node_modules`, IDE
metadata, developer caches, and explicit user code roots. Agent confidence cannot
override protection.

## Legacy actions

v0.1-v0.4 scan, explain, cleanup plan, quarantine, reputation, PUP, evidence,
persistence, Windows collection/reporting and trial actions remain Legacy /
Compatibility interfaces. They exist for research and historical reproduction,
not as v0.5 authorization sources. The old Cleaner/PUP/Persistence route remains
`FEATURE_FROZEN` after a final A/B delta of only +2.2.

## Chinese safety commitments / 中文安全承诺

不静默删除。不偷偷上传。不做黑箱声誉判断。不因单一来源自动删除。社区规则、AI
判断和在线声誉不能直接触发删除。用户文档、代码、照片和凭据默认保护。每个操作
必须可解释、可记录、可分类。外部权限很大，内部刹车必须更大。AI 可以执行，但
执行必须被治理。先造刹车，再造发动机。
