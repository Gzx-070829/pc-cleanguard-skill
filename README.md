# PC CleanGuard Skill

开源、可审计、隐私优先的 AI 系统治理 Skill。

Open-source, auditable, privacy-first AI System Governance Skill.

> **PC CleanGuard 不是传统清理软件。**
> **It is not a traditional cleaner.**
>
> 它面向 AI Agent 建立受治理的系统安全边界；当前 PR7 只读分析，不执行任何真实清理。
> It establishes governed safety boundaries for AI agents; PR7 analyzes data read-only and performs no cleanup.

PC CleanGuard 面向 Codex、WorkBuddy、本地 AI Agent 和未来系统级 AI 助手。它的目标不是“一键清理电脑”，而是让 AI Agent 在严格策略、权限分级、证据链、用户确认、隐私保护和审计留痕约束下，安全地分析、分类和规划未来的系统治理操作。

PC CleanGuard is designed for Codex, WorkBuddy, local AI agents, and future system-level assistants. It replaces one-click cleanup with governed analysis, classification, and planning under policy, permission, evidence, consent, privacy, and audit controls.

核心原则 / Core principle:

**AI 可以执行，但执行必须被治理。**

**AI may execute, but execution must be governed.**

**外部权限很大，内部刹车必须更大。**

**External permission is large; internal brakes must be larger.**

## 项目定位

PC CleanGuard 在 AI 建议与系统操作之间建立可审计的安全门。它先回答“能否做、为何做、需要谁确认”，而不是直接动手。

PC CleanGuard is an auditable safety gate between AI recommendations and system operations. It answers whether an action is permitted, why, and whose confirmation is required before execution is considered.

## 它是什么

- Windows 对象的保守治理策略模型。
- 以证据链、风险标签和权限等级约束 Agent 的 Skill。
- 为未来受控执行层提供独立、不可绕过的 Policy Engine。

## 它不是什么

它不是磁盘清理器、卸载器、杀毒软件、系统优化器或后台监控器。PR1 没有删除、卸载、移动、注册表写入、服务/启动项修改、联网或上传能力。

## v0.1 PR7 当前范围

PR7 打通可用的只读治理链路：显式 JSON 输入 → normalizer → `GovernanceTarget` → Policy Engine → Report Builder → dry-run Audit。调用方还可显式指定安全本地路径，写出 report JSON 和 audit JSONL；默认不覆盖已有文件。

PR7 completes a useful read-only governance chain from explicit JSON input to normalized targets, policy decisions, reports, and dry-run audit events. Optional artifact writing requires explicit safe local paths and does not overwrite by default.

## 安全原则

1. 不静默删除。
2. 不偷偷上传。
3. 不做黑箱声誉判断。
4. 不因单一来源自动删除。
5. 社区规则不能直接触发删除。
6. AI 判断不能直接触发删除。
7. 在线声誉不能直接触发删除。
8. 用户文档、代码、照片不参与云端声誉查询。
9. 每个操作必须可解释、可记录、可分类。
10. 硬规则先于普通分类，敏感目标直接 `BLOCK`。
11. 不确定时 `KEEP` 或 `ASK_USER`。
12. 用户偏好不能绕过 `BLOCK` 或 Level 5。

In short: no silent deletion, hidden upload, black-box reputation verdict, or automatic removal from a single source. Every proposed action must be explainable, classifiable, consent-aware, and auditable.

**先造刹车，再造发动机。 / Build the brakes before the engine.**

## 系统架构

```text
Normalized Target + Evidence
             |
        Policy Engine
             |
 Classification + Risk + Permission + Confirmation + Audit
             |
      Non-executable PR2 report
```

未来 Execution Layer 必须消费 Policy Engine 的结果，不能自行制定或弱化策略。

The future Execution Layer may consume policy decisions, but it may never create or weaken them.

## 风险分类标签

`KEEP`、`ASK_USER`、`SAFE_REMOVE`、`STARTUP_OFF`、`QUARANTINE`、`BLOCK`。候选标签不是执行授权。

## 执行权限等级

Level 0 只读扫描；Level 1 低风险清理；Level 2 可逆操作；Level 3 标准卸载；Level 4 高风险系统修改；Level 5 禁止区。PR1 只运行 Level 0。

## 隐私承诺

PR7 仍仅实现 Offline Mode：不联网、不上传，不对用户文档、代码或照片做云端声誉检查。

PR7 is offline-only: no networking, uploads, or cloud reputation checks for documents, source code, or photos.

## 开发状态

当前里程碑：**v0.1 PR7 — Read-only Scan Pipeline**。PR7 处理调用方显式提供的 JSON，产生归一化计数、目标、策略决策、报告和 dry-run 审计事件。Python 仍不自动执行 PowerShell collector。

Current milestone: **v0.1 PR7 — Read-only Scan Pipeline**. PR7 processes caller-supplied JSON into normalized counts, targets, policy decisions, a report, and dry-run audit events. Python still never invokes PowerShell collectors.

详细用法见 [只读扫描流水线](docs/readonly-scan-pipeline.md)。

**JSONL 管审计，SQLite 管历史。PR3 只记录 dry-run，不代表执行。**

**声誉记录不是执行授权；最终仍由 Policy Engine 把关。**

**卸载字符串只是元数据，不是执行授权。PR5 不清理、不删除、不卸载、不联网、不上传。**

**启动命令、服务路径和任务动作只是元数据。PR6 不采集进程，也不修改系统。**
