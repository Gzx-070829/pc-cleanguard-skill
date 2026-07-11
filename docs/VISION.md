# PC CleanGuard Vision / 项目愿景

PC CleanGuard 是 AI Agent 的 Windows 系统治理安全层。它不把自然语言“看起来合理”当作操作许可，而是在 Agent 与系统修改之间提供独立、可测试、可审计的策略与权限边界。

PC CleanGuard is a Windows system-governance safety layer for AI agents. It separates explanation from authority and makes policy, evidence, permission, confirmation, and audit independently enforceable.

## 不信任自然语言理由 / Never trust natural-language rationale

Policy Engine 永远不信任 Agent 的自然语言理由。Agent 可以解释发现、证据和建议，但解释内容不参与放行或拦截；硬规则、结构化 evidence、permission level、用户确认与保护引擎才决定动作能否进入下一阶段。

如果 Agent 说“这是垃圾”“社区都建议删除”或“在线声誉很差”，系统仍必须把这些内容当作待审证据，而不是执行授权。

## Reputation KB 的位置 / Role of the Reputation KB

Reputation KB 只能用于：

- 解释已观察到的 PUP 行为类别；
- 对人工复核队列排序；
- 显示来源、日期、司法辖区、置信度与误报风险；
- 提示证据冲突和需要用户确认的原因。

Reputation KB 不能单独触发删除、卸载、隔离、启动项禁用、服务修改或计划任务修改。即使 record 已达到 `approved_for_explanation`，它仍然只有解释资格，没有执行权限。

## External Tool Adapter 的位置

External Tool Adapter 不是绕过内部策略的捷径。未来每个适配器仍必须经过显式 allowlist、发布者/签名校验、支持动作限制、风险等级、用户确认与审计治理。可信工具不等于可信参数，更不等于静默执行许可。

## 保守优先 / False positives cost more

误标比漏标更伤：错误清理开发环境、驱动组件、用户代码或正常软件会直接破坏信任。因此默认行为是保留、阻断或请求人工复核；单一来源、单一规则、AI 判断或社区报告都不能把对象自动升级为删除目标。

Developer Guard 是这一原则的第一条专用保护引擎：scanner 提前阻断开发资产，executor 在文件操作前再次复核。

## 版本路线 / Version path

- **v0.3 — Developer Guard + Reputation KB contract**：开发者路径双层防守、中文 PUP taxonomy、evidence-only reputation record。
- **v0.4 — Quarantine + Restore**：可逆隔离、恢复契约和更完整的操作历史。
- **v0.5 — PUP planner + registry backup**：PUP 治理计划与注册表备份基础；计划仍不等于执行。
- **v1.0 — External tool adapter + Agent ecosystem integration**：在 allowlist、签名、确认和审计约束下接入 Agent 生态与可信外部工具。

## 不变原则 / Invariants

不静默删除，不偷偷上传，不做黑箱声誉判断，不因单一来源自动删除。每个操作必须可解释、可记录、可分类。外部权限很大，内部刹车必须更大。

**AI 可以执行，但执行必须被治理。**
