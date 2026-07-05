# Execution Levels

- **Level 0 — 只读扫描**：读取最小元数据并生成报告。PR1 唯一实现等级。
  **Read-only scan:** read minimal metadata and produce a report. This is the only level implemented by PR1.
- **Level 1 — 低风险清理**：未来可处理严格白名单、可再生成数据；仍需策略与审计。
  **Low-risk cleanup:** reserved for future strictly allowlisted, reproducible data; policy and audit remain mandatory.
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
