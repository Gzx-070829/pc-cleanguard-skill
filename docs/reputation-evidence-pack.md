# Reputation Evidence Pack

Evidence Pack 是解释、排序、人工复核和风险提示的数据层，不是黑名单。`mapping_type` 表示证据与目标实体的关系；`is_synthetic` 独立表示数据真伪，两条轴不得混用。

允许的关系为 direct entity、related publisher、name collision candidate 和 analogical behavior。类比证据必须提供 `analogy_basis`。移动 APP/SDK 监管证据只能保持移动实体范围并作为类比或发布者级线索，不能映射为 Windows 桌面软件执行授权。

所有记录固定 `execution_authorized=false`。即使是 Windows direct entity 且关系置信度高，也只能进入 review，不能单独授权删除、卸载、禁用或注册表修改。
