# Roadmap

PC CleanGuard 以用户可见闭环为 Sprint PR 单位快速推进，同时保持“不静默删除、不绕过确认、不联网泄露、不把 AI/声誉建议当授权”的安全底线。

PR29 在 v0.3.1 基础上补齐少量中文 Windows direct/installer-artifact evidence、Evidence Quality Dashboard 与真实 report 本地验证；不进入 PR30，不扩大系统执行权限。

## v0.1.0 — Read-only governance loop / 只读治理闭环

已发布：Policy Engine、声明式 plan、dry-run audit、只读 Windows metadata pipeline、离线 AI explainer 与 AI-callable Skill action。

## v0.2.0 — Controlled L1 cleanup + public demo / L1 受控清理与公开 Demo

已发布：junk preview、受控 L1 temp/cache/log 文件清理、allow-root/protected-path/runtime revalidation、JSONL audit、Markdown report、synthetic demo quickstart 与 plan-only external-tool recommender。

## v0.3.0 — User trial + quarantine-first + PUP insight + Developer Guard

Public Preview：

- 中文优先的 8 类 PUP behavior taxonomy；
- evidence-only Reputation Record schema、review status 与 synthetic examples；
- Developer Guard 纯路径分类器；
- scanner 提前阻断 + executor 删除前复核；
- `.git`、虚拟环境、依赖树、IDE metadata、开发缓存和显式 user code roots 保护。

v0.3 Reputation KB 只能解释、排序与风险提示，不能自动触发删除、卸载或禁用。

PR19 将原计划的可逆隔离基础提前接入 v0.3：普通文件 quarantine、manifest、restore、CLI、Skill actions 与 L1 cleanup integration。仍不提供 purge 或目录隔离。

PR20 把隔离设为确认清理的默认路径，增加 `clean safe` 普通用户闭环；永久删除改为显式专家模式和二次确认。首批 Reputation Seed Pack 为离线 synthetic/placeholder 证据，固定不授权执行，不采集专有检测规则。

PR21 增加 Reputation Matcher、PUP Insight、CLI/Skill 用户入口和 AI explain 的受限洞察摘要。它让声誉证据可见，但仍不提供删除、卸载或禁用授权。

PR22 将 cleanup preview、默认隔离、审计、报告、PUP insight 和恢复说明编排为 5 分钟用户试用入口，优先验证真实用户能否理解产品价值与安全边界。

PR24 提供无需配置的 `.pcg-quarantine` 默认隔离路径，并把 Evidence Pack 的实体关系、synthetic 状态、类比依据和执行阻断规则代码化。

PR25 增加真实公开来源的人工 intake/review/build 流程和首批核验 records。构建与 PUP insight 均保持离线，所有真实 evidence 继续被阻断在执行门控之外。

PR26 将 evidence indicators、保守匹配、PUP Intelligence、来源追溯、人工 checklist 和误报反馈编排为一条命令生成的本地 Review Pack。它提升可用性，但不扩大系统执行权限。

PR27 用对抗测试焊死 Evidence Guard，加入批次级中文官方来源、report-metadata Behavior Indicators，并准备 v0.3.1 showcase/checklist。版本号、tag 和 Release 留给独立发布任务。

## v0.3.1 — Chinese source matrix + guarded candidate intake

已发布准备：PR28 把历史公开材料、安全厂商公开文章、官方/监管来源、可信媒体、社区多源反馈和网友屏蔽名单分层。只有满足契约的本地公开来源才可进入 candidate/review；历史榜、网友名单和移动端通报不得成为现代 Windows 删除名单。PUP 层执行门控仍为 0。

## v0.4 — Reputation adapters + PUP planner + registry backup planning

在明确来源许可和人工审核下接入真实公开 Reputation adapter；构建 PUP 声明式 planner 与注册表备份规划。声誉证据仍不授权执行，registry backup planning 不提供任意写入口。

## v0.5 — Controlled uninstall + stronger external-tool governance

在 allowlist、签名/发布者核验、用户确认、回滚和审计下推进更强的受控卸载与外部工具治理。

## v1.0 — External tool adapter + Agent ecosystem integration

在 allowlist、发布者/签名校验、动作限制、用户确认和审计约束下接入可信外部工具与 Agent 生态。可信工具与 AI recommendation 都不是静默执行授权。

完整愿景见 [docs/VISION.md](docs/VISION.md)。PR 不创建 tag；只有正式版本创建 tag。Commit message 使用中文。
