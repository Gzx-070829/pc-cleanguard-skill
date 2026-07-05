# Safety Model

> English summary: Hard rules win, uncertainty is preserved, and every non-`KEEP` decision requires evidence and audit preparation.

## 决策优先级

1. Level 5 与敏感路径硬规则。
2. 用户显式核心工具保护。
3. 已知系统组件、运行时、驱动和关键开发工具保护。
4. 来源可信度与证据充分性检查。
5. 普通候选分类。

冲突取更保守结果。`SAFE_REMOVE`、`STARTUP_OFF` 和 `QUARANTINE` 只是候选状态，必须有证据、确认和审计；`QUARANTINE` 还要求可逆。AI、社区规则、在线声誉或偏好都不能独立提高权限。

所有非 `KEEP` 结果必须包含非空 evidence chain 且 `audit_required=true`。`BLOCK` 必须使用 Level 5。
