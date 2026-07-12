# Roadmap

PC CleanGuard 以用户可见闭环为 Sprint PR 单位快速推进，同时保持“不静默删除、不绕过确认、不联网泄露、不把 AI/声誉建议当授权”的安全底线。

## v0.1.0 — Read-only governance loop / 只读治理闭环

已发布：Policy Engine、声明式 plan、dry-run audit、只读 Windows metadata pipeline、离线 AI explainer 与 AI-callable Skill action。

## v0.2.0 — Controlled L1 cleanup + public demo / L1 受控清理与公开 Demo

已发布：junk preview、受控 L1 temp/cache/log 文件清理、allow-root/protected-path/runtime revalidation、JSONL audit、Markdown report、synthetic demo quickstart 与 plan-only external-tool recommender。

## v0.3 — Developer Guard + Reputation KB contract

当前阶段。PR18 交付：

- 中文优先的 8 类 PUP behavior taxonomy；
- evidence-only Reputation Record schema、review status 与 synthetic examples；
- Developer Guard 纯路径分类器；
- scanner 提前阻断 + executor 删除前复核；
- `.git`、虚拟环境、依赖树、IDE metadata、开发缓存和显式 user code roots 保护。

v0.3 Reputation KB 只能解释、排序与风险提示，不能自动触发删除、卸载或禁用。

PR19 将原计划的可逆隔离基础提前接入 v0.3：普通文件 quarantine、manifest、restore、CLI、Skill actions 与 L1 cleanup integration。仍不提供 purge 或目录隔离。

PR20 把隔离设为确认清理的默认路径，增加 `clean safe` 普通用户闭环；永久删除改为显式专家模式和二次确认。首批 Reputation Seed Pack 为离线 synthetic/placeholder 证据，固定不授权执行，不采集专有检测规则。

## v0.4 — Quarantine + Restore

建设可逆隔离区、restore contract、操作历史和失败恢复。所有隔离动作仍需 Policy Engine、用户确认、目标身份复核与审计。

## v0.5 — PUP planner + registry backup

将多来源 PUP evidence 转换为声明式治理计划，并建立注册表备份/恢复基础。Planner 不直接执行；registry backup 不能成为任意写注册表入口。

## v1.0 — External tool adapter + Agent ecosystem integration

在 allowlist、发布者/签名校验、动作限制、用户确认和审计约束下接入可信外部工具与 Agent 生态。可信工具与 AI recommendation 都不是静默执行授权。

完整愿景见 [docs/VISION.md](docs/VISION.md)。PR 不创建 tag；只有正式版本创建 tag。Commit message 使用中文。
