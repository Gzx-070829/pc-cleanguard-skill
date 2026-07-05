# Execution Permissions

> English summary: PR1 has no execution layer. All plans are non-executable policy artifacts.

PR1 不包含执行层，所有计划均为不可执行的策略制品。

未来执行层必须：

- 接受 Policy Engine 已签发的目标身份、分类与权限上限；
- 在执行前重新验证前置条件与确认；
- 拒绝缺少证据、审计或必需回滚方法的步骤；
- 拒绝 Level 5，并且不得把多个低风险步骤组合成高风险批量动作；
- 只记录去敏后的命令摘要，避免泄露用户路径和凭据。

Execution Layer 不能自行决定策略，不能把建议文本解释成授权。
