# Contributing

欢迎贡献。项目从 v0.2 起采用 Sprint PR 加速交付用户可见价值，同时保持安全底线不变。提交前请运行编译、单元测试、Schema 解析和 `git diff --check`。

Contributions are welcome, but safety boundaries take priority over delivery speed. Code, rules, tests, and documentation must preserve conservative policy behavior.

## Sprint PR 贡献方式

- 每个 PR 应提供用户可见能力，可包含多个组成同一用户链路的强相关模块。
- 允许先提交 80% 可用版本，并用 issue 与用户反馈跟踪不阻断核心路径的小缺陷。
- 文档保持必要、准确、可维护，不为每个只读模块重复撰写长篇安全论证。
- 测试覆盖核心路径、失败路径和安全不变量，不以测试数量作为目标。
- 只读、计划、预览和推荐能力应快速推进；真实执行从受治理的 Level 1 低风险能力开始。
- PR 不打 tag，只有正式版本创建 tag；commit message 使用中文。

详细原则见 [`docs/development-principles.md`](docs/development-principles.md)。

## 贡献类型

- 代码贡献：保持 Policy Engine 纯判断、标准库优先，并补充测试。
- 规则库贡献：按下述证据模板提交，规则不能授权执行。
- 文档贡献：确保安全承诺与实现一致。
- 安全报告：按 `SECURITY.md` 私密披露。
- 测试用例贡献：覆盖正例、反例、边界条件和不变量。
- 危险案例贡献：使用合成、去标识化数据，说明预期保护结果。

## 规则库证据模板

```text
软件名称：
发布者：
版本范围：
安装路径特征：
行为证据：
启动项/服务证据：
网络声誉证据：
建议分类：
为什么不是 KEEP：
为什么不是 BLOCK：
误伤风险：
建议安全操作：
卸载方式：
回滚/恢复说明：
来源：
```

社区规则可以提高怀疑程度，可以建议 `ASK_USER`、`STARTUP_OFF` 或 `SAFE_REMOVE candidate`。社区规则不能直接触发删除，也不能绕过 Policy Engine。网络声誉只能作为证据之一，不能替代本地身份核验和用户确认。

不能提交“XX 是垃圾软件，建议删除”这种无证据规则。规则贡献只能增加证据或提高怀疑程度，不能直接触发删除。

Do not submit unsupported claims such as “this is junk software; delete it.” Rule contributions may add evidence or increase suspicion, but they may never directly trigger deletion or bypass the Policy Engine.

## Pull request 要求

保持变更目标内聚、解释安全影响、列出测试结果。一个 Sprint PR 可以包含多个强相关模块，但不得混入无关重构。新增分类规则必须说明误伤风险和降级行为；涉及 Level 4/5、安全路径或隐私的变更至少需要安全审查。不得提交真实用户路径、样本文件、访问令牌或遥测数据。

Keep each Sprint PR cohesive, explain its safety impact, and include verification results. Closely related modules may ship together; unrelated changes should not. Changes involving Level 4/5, sensitive paths, or privacy require explicit security review.

安全底线始终包括：不静默删除、不绕过用户确认、不联网上传用户数据、不做黑箱判断、不因单一来源自动删除。AI 建议和外部工具推荐都不是执行授权；AI 可以执行，但执行必须被治理。
