# 中文 Windows PUP Direct Evidence

v0.3.2 保留 5 条经人工核验、时间与组件范围受限的公开 evidence。direct_entity 也必须核对本机签名、版本、渠道和用户意图，不能形成删除授权。

PR29 引入一小组人工核验、可追溯的中文 Windows 公开 evidence。它用于本地解释、排序和人工复核，不是黑名单，也不是删除、卸载、禁用或注册表修改授权。

`direct_entity` 必须由来源明确指向 Windows 桌面实体，并保留版本/时间范围、受影响组件、观察行为和关系置信度。本机同名软件仍需核对发布者、签名、版本、渠道与用户意图。`execution_authorized=false`，PUP 层执行门控计数恒为 0。

当前 pack 只保存公开页面元数据与克制摘要，不采集安全厂商专有签名、规则、检测逻辑或样本。
