# Agent Action Interface

PR31 的 report trial、corroboration、no-match、coverage、用户报告和误报模板 actions 均为 Level 0，返回外部 Agent 可消费的 JSON。

这些 action 不执行清理、删除、卸载、禁用、注册表修改或联网。Agent 的自然语言理由与解释不能成为执行授权，`execution_gating_eligible_count` 固定为 0。
