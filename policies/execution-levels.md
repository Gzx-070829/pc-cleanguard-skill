# Execution Levels

- **Level 0 — 只读扫描**：读取最小元数据并生成报告。PR1 唯一实现等级。
  **Read-only scan:** read minimal metadata and produce a report. This is the only level implemented by PR1.
- **Level 1 — 低风险清理**：PR15 仅开放 cleanup preview 中的 temp/cache/log 普通文件；必须显式确认、位于 allow-root、通过保护路径与当前元数据复核，并逐项审计。其他对象不属于 Level 1 执行范围。
  **Low-risk cleanup:** PR15 permits only previewed temp/cache/log regular files after explicit confirmation, allow-root containment, protected-path and current-metadata checks, with per-item audit records.
- **Level 2 — 可逆操作**：未来启动项关闭或隔离；必须确认、回滚和审计。
  **Reversible operation:** reserved for future startup changes or quarantine; confirmation, rollback, and audit are mandatory.
- **Level 3 — 标准卸载**：未来仅使用已验证标准卸载器；必须确认和审计。
  **Standard uninstall:** reserved for future verified standard uninstallers; confirmation and audit are mandatory.
- **Level 4 — 高风险系统修改**：默认拒绝，未来需专家策略和强化确认。
  **High-risk system modification:** denied by default and requires a future expert policy plus strengthened confirmation.
- **Level 5 — 禁止区**：无执行许可，不能被偏好、AI、社区或声誉绕过。
  **Forbidden zone:** no execution permission; preferences, AI, community input, and reputation cannot bypass it.

权限等级是上限。Execution Layer 不得提升 Policy Engine 返回的等级。

Permission levels are hard ceilings. The Execution Layer must never elevate the level returned by the Policy Engine.
