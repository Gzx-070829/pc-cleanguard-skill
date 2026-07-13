# 中文 Windows PUP 人工复核策略

v0.3.3 将 approved evidence 扩至 10 条，同时保留 candidate/backlog。公开安全文章只提取可核验的行为描述，不复制厂商专有签名、规则、检测逻辑或样本库。

- direct_entity 不是删除、卸载或禁用授权。
- installer_artifact 不是软件本体定罪。
- related_publisher 不映射到具体软件处置。
- name_collision_candidate 必须降级为弱线索。
- 社区、论坛和用户 blocklist 只能进入 candidate/backlog。
- feedback 只进入 review queue，不会自动修改 evidence pack。
- PUP 层的 `execution_gating_eligible_count` 固定为 0。

论坛名单、网友屏蔽列表、模糊吐槽、无法区分产品/安装器/组件/发布者的材料只能进入 candidate/backlog。中文 evidence 不是黑名单。

来源进入 source candidate，不等于形成 evidence；candidate 被接受，也只允许用于 explanation/review。社区反馈必须有长期多源证据并默认需要第二来源；历史材料只能标记 historical context。

人工复核至少检查：实体名称、发布者、数字签名、版本、安装来源、分发渠道、用户意图、时间范围和独立安全工具提示。名称碰撞必须降级，发布者关系只能形成 publisher-level warning。所有线索允许的后续动作只有保留、询问用户、核验来源、收集更多证据和提交误报反馈。
