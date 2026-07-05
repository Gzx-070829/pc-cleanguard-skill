# Roadmap

本路线图以中文说明项目阶段，并保留英文组件名称，方便中英文社区共同审计。

This roadmap keeps stage descriptions in Chinese while retaining English component names for international collaboration.

- **v0.1**：安全扫描 + 报告 + 规则分类基础。
  - **v0.1 PR1**：仓库骨架、安全契约、schemas、最小 Policy Engine、测试。
  - **当前 PR — v0.1 PR2**：非破坏性 Report Builder、Execution Plan Builder、示例报告和测试。
- **v0.2**：SQLite 历史 + 用户偏好 + 审计日志实现。
- **v0.3**：只开放低风险清理的受控执行。
- **v0.4**：Reputation Engine + 更新管理器。
- **v0.5**：Quarantine + Restore Manager。
- **v1.0**：Governed Managed Mode。

后续版本仍须遵守 Policy Engine 前置、最小权限、明确确认、可逆优先和审计完整性原则。

Every future milestone remains subject to Policy Engine gating, least privilege, explicit confirmation, reversibility, and audit integrity.
