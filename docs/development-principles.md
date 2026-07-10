# Development Principles / 研发原则

从 v0.2 开始，PC CleanGuard 进入加速研发模式。目标是在守住安全底线的前提下，以 Sprint PR 持续交付用户和市场能够直接感知的能力。

Starting with v0.2, PC CleanGuard uses accelerated, value-visible Sprint PRs while preserving its non-negotiable safety floor.

## Sprint PR 与市场可见价值

1. 每个 PR 都应带来用户可见能力，或让既有能力明显更易使用、理解和验证。
2. 每个 PR 可以包含多个强相关模块，不再为了形式上的“小 PR”过度拆碎完整用户链路。
3. 允许先交付 80% 可用版本，再通过 issue、真实使用和用户反馈修正小缺陷。
4. 只读、计划、预览和推荐能力应快速推进，尽快形成可运行、可展示、可反馈的闭环。
5. 真实执行能力从 Level 1 低风险操作开始推进，不因抽象风险无限拖延；每项执行能力仍须经过策略、确认和审计门禁。

## 文档与测试纪律

1. 文档只记录使用方法、架构决策、必要安全边界和维护信息，不写与当前实现不成比例的长篇安全论文。
2. 测试覆盖核心路径、失败路径和关键安全不变量，不为增加测试数量而堆砌重复用例。
3. PR 使用阶段性开发分支，但不打 tag；只有 `v0.1.0`、`v0.2.0` 等正式版本创建 tag。
4. Git commit message 使用中文，清楚说明本次交付的用户价值或工程能力。

## 不可降低的安全底线

- 不静默删除。
- 不绕过用户确认。
- 不联网上传用户数据。
- 不做黑箱判断。
- 不因单一来源自动删除。
- AI 建议不是执行授权。
- 外部工具推荐不是执行授权。
- AI 可以执行，但执行必须被治理。

研发速度可以提高，安全红线不能降低。未来 controlled executor 必须从明确范围、低风险、可确认、可解释、可记录的 Level 1 能力开始，并持续受 Policy Engine 约束。

Development speed may increase, but safety boundaries do not weaken. Any future controlled executor must begin with bounded, low-risk, explainable, confirmation-gated, and auditable Level 1 operations under the Policy Engine.
