# PC CleanGuard

**Deterministic Windows governance for AI agents.**
**面向 AI Agent 的 Windows 确定性治理层。**

> Agent 可以执行，但执行必须被治理。
> Agent may be intelligent; authorization must be deterministic.

PC CleanGuard 不再试图比通用 Agent 更聪明地管理 Windows。它位于 Agent
建议与真实系统修改之间，提供确定性的 **Policy、Consent、Preconditions、
Audit 与 Rollback Contract**。

```text
Agent Request
  → Guard Decision
  → Requirements
  → Execution Contract
  → External Executor
  → Audit Receipt
  → Rollback Contract
```

Guard Core 离线、确定、stdlib-first。它不调用 LLM、不联网、不运行
PowerShell/命令行、不卸载软件，也不实现 L3/L4 executor。

## Quick start / 快速开始

评估一个结构化动作：

```powershell
python -m pc_cleanguard.cli guard evaluate `
  --request examples/guard/02-temp-clean-require-confirmation/request.json `
  --context examples/guard/02-temp-clean-require-confirmation/context.json `
  --output decision.json
```

Agent stdin 模式：

```powershell
Get-Content envelope.json | python -m pc_cleanguard.cli guard evaluate --stdin --json
```

验证 hash-chained audit：

```powershell
python -m pc_cleanguard.cli guard audit verify --input audit.jsonl --json
```

运行固定治理验收：

```powershell
python -m pc_cleanguard.cli guard benchmark --suite benchmarks/governance --output .pcg-v050-benchmark --json
```

退出码：`0` 完成，`2` 输入无效，`3` Policy BLOCK，`4` requirements
pending，`5` 内部/完整性验证失败。机器输出只写 stdout JSON；错误写 stderr。

## Python API

```python
from pc_cleanguard import ActionRequest, Guard, GuardContext

guard = Guard()
decision = guard.evaluate(request, context)

contract = guard.prepare_execution(
    decision=decision,
    consent=consent,
    rollback=rollback,
    current_context=current_context,
)
```

主操作只有四个：`evaluate`、`prepare_execution`、
`record_execution_result`、`verify_audit`。Agent 主 Skill actions 只有五个：
`evaluate_action`、`prepare_execution`、`evaluate_action_bundle`、
`record_execution_result`、`verify_audit`。

## What the Guard decides

| Level | Boundary | Result |
| --- | --- | --- |
| L0 | read/report/preview/explain | normally `ALLOW` |
| L1 | narrow low-risk file mutation | confirmation + revalidation + audit |
| L2 | reversible filesystem mutation | L1 + rollback contract + postcondition |
| L3 | official uninstall contract | confirmation + rollback plan; external executor only |
| L4 | registry/service/startup/task/browser system mutation | explicit high-risk consent + backup + rollback + revalidation + audit |
| L5 | protected/credential/boot/wildcard/bypass action | always `BLOCK` |

`ALLOW`、`REQUIRE`、`BLOCK` 是仅有的 disposition。`agent_reason`、AI
confidence、PUP、Reputation、Behavior、Evidence 和 Persistence signal 都不是授权
来源。Untrusted information 只能提高限制，不能降低限制。

Consent 必须由 integrating host / trusted UI 验证真实性，并绑定 decision、action
fingerprint、targets、effect、scope 与 expiry。Agent 写
`"user_confirmed": true` 不是 ConsentGrant。目标在 preview 后发生 hash/size/mtime/
path/type 变化时，旧授权失效，必须重新评估。

## Why v0.5 exists

旧 PC CleanGuard 在最终 A/B 中仅领先 Bare Codex **+2.2** 分，没有达到继续
大型 Skill 开发的门槛：

```text
Bare Codex                 87.3
Codex + PC CleanGuard      89.5
Delta                      +2.2
```

因此 v0.4.x 的大型 Cleaner/PUP/Persistence 产品路线保持
`FEATURE_FROZEN`。v0.5 不是把旧系统继续做大，而是删除没有证明必要性的产品
假设，只保留实验中最稳定的治理价值。Bare Codex 获胜的任务、rubric 和历史结论
均未改写。详见[最终 A/B 验收](docs/PC-CleanGuard-Final-AB-Evaluation.md)与
[重构决策](docs/refoundation/v0.5.0-refoundation-decision.md)。

## Security boundary / 安全边界

- Agent natural-language reasoning is never an authorization source.
- AI explanation ≠ execution authorization.
- Reputation / Evidence / PUP / Persistence / Behavior ≠ execution authorization.
- Consent cannot override L5 or hard `BLOCK`.
- L2/L3/L4 缺少 rollback contract/plan 时不能生成 ExecutionContract。
- Guard Core 不 import Cleaner、PUP、Reputation、Persistence、Windows collector
  execution 或 AI provider。
- Audit 使用 canonical JSON + SHA-256 前向哈希链；历史事件被修改可检测。
- 不静默删除，不偷偷上传，不做黑箱声誉判断，不因单一来源自动删除。

PC CleanGuard **不是 OS sandbox、kernel enforcement 或 EDR**。如果 Agent 可以绕过
集成直接调用 Windows API，它也可以绕过 Guard。有效治理要求 Agent host 将相关
动作强制路由到 Guard，并由可信 UI/host 认证 Consent。

详见 [SECURITY.md](SECURITY.md) 与 [Guard Core architecture](docs/architecture/guard-core.md)。

## Legacy / Compatibility (v0.1–v0.4)

旧功能仍保留，用于研究、兼容与历史复现，但不再是产品核心。CLI `clean`、`trial`、
`pup`、`reputation`、`persistence`、`windows` 等属于 Legacy / Compatibility。
旧 `invoke_skill_action` 仍可用；新 Agent 集成应优先使用 `invoke_guard_action`。

历史只读/演示入口仍可复现：

```powershell
python -m pc_cleanguard.cli scan --input input.json --report report.json --audit audit.jsonl
python -m pc_cleanguard.cli explain --report report.json --output explanation.md --provider mock
python -m pc_cleanguard.cli trial run --root .pcg-demo --output .pcg-trial
python -m pc_cleanguard.cli quarantine restore --root .pcg-quarantine --item-id <id>
```

v0.1.0 Public Preview、v0.2 demo 和 v0.4 showcase 继续保留：

- [v0.2 quick try](docs/v0.2-quick-try.md)
- [v0.2 release checklist](docs/release-v0.2.0-checklist.md)
- [public demo](examples/public_demo/README.md)
- [v0.2 Agent flow](examples/skill_actions/v0.2_cleanup_agent_flow.json)
- [legacy migration status](docs/legacy/README.md)

Windows 真机历史流程也未删除。采集由用户显式启动；**Python 不自动启动 PowerShell**：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\collect-windows-metadata.ps1 -OutputDirectory .pcg-collectors
python -m pc_cleanguard.cli windows report build --collector-dir .pcg-collectors --output windows-report.redacted.json --validation-output windows-report-validation.json
python -m pc_cleanguard.cli evaluation windows --report windows-report.redacted.json --output .pcg-evaluation --evidence-pack data/reputation/evidence_pack.real.zh-CN.json
```

`ExecutionPolicy Bypass` 只属于该用户启动的进程；推荐分享 redacted report。
`0 PUP match` 和 `persistence 0 edge` 都是允许的保守结果。Synthetic compatibility
测试仍不得放宽 Desktop/Documents/代码仓库保护。旧“持久化链路治理
(Persistence Chain Governance)”现为 optional intelligence，不再授权执行。

## Project documents

- [v0.5 design](docs/refoundation/v0.5.0-design.md)
- [migration map](docs/refoundation/v0.5.0-migration-map.md)
- [v0.5 release notes](docs/releases/v0.5.0.md)
- [roadmap](ROADMAP.md)
- [Agent Governance Contract](SKILL.md)

License and contribution rules remain in [CONTRIBUTING.md](CONTRIBUTING.md).
