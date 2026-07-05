# Report Format / 报告格式

## Purpose / 用途

PR2 把多个 `PolicyDecision` 组织成结构化、可审计的报告。报告不是清理结果，执行计划不是执行命令，PR2 不会修改系统。

PR2 organizes multiple `PolicyDecision` objects into a structured, audit-ready report. A report is not a cleanup result, an execution plan is not an execution command, and PR2 does not modify the system.

## Top-level sections / 顶层结构

- `summary`：扫描标识、分类计数和风险汇总；`destructive_actions_executed` 永远为 `false`。
- `findings`：每个目标的身份、分类、风险、权限、证据摘要和潜在影响。
- `recommendations`：带 evidence chain、确认和回滚信息的保守建议。
- `execution_plan`：仅用于审查的声明式 `PLAN_*` 步骤和 `blocked_steps`。
- `managed_mode_compatibility`：未来兼容性标记，不是自动执行授权。
- `risk_notes`：PR2 的非执行安全限制。
- `audit_notes`：未来执行需要写入的审计要求。

The seven sections separate observations, policy recommendations, non-executable plans, future compatibility flags, risk constraints, and audit requirements.

## Evidence and target display / 证据与目标显示

每个 recommendation 必须有 `evidence_chain`。PR2 不扫描系统，也不补造 publisher；缺失 publisher 时输出 `null`。由于 Builder 只接收 `PolicyDecision`，显示用 `object_type` 和 `name` 从规范化 `target_id` 的 `TYPE:Display Name` 形式提取，不能识别时使用 `UNKNOWN` 并保留原始 ID。

Every recommendation must include an `evidence_chain`. PR2 performs no system discovery and never invents a publisher. Display metadata is conservatively derived from normalized `TYPE:Display Name` target identifiers, with `UNKNOWN` as the fallback.

## Safety boundary / 安全边界

`SAFE_REMOVE` 只是候选标签。`BLOCK` 和 Level 5 步骤只能进入 `blocked_steps`。Managed Mode compatibility 只是未来兼容性标记，不是自动执行授权。任何未来执行仍必须重新经过 Policy Engine、用户确认、回滚检查和审计事件生成。

`SAFE_REMOVE` is only a candidate label. `BLOCK` and Level 5 steps belong only in `blocked_steps`. Managed Mode compatibility is a future-facing marker, never automatic execution authorization.
