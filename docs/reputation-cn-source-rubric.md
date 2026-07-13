# 中文来源 Review Rubric

Rubric 位于 `data/reputation/cn_source_rubric.zh-CN.json`，由离线 validator 校验。

- `source_reliability`：official、vendor_public_article、reputable_media、security_vendor_public_article、community_multi_report、weak_source。
- `entity_clarity`：exact_windows_desktop_entity、installer_or_bundle_artifact、publisher_level_only、name_collision_possible、mobile_only、unclear。
- `risk_category`：强制安装、难卸载、浏览器劫持、广告弹窗、捆绑安装、误导扫描、隐私越界、启动/任务持久化或 unknown 的稳定枚举。
- `allowed_use`：只能 explanation/review/publisher warning/name-collision warning。
- `forbidden_use`：固定包含删除、卸载、禁用、注册表修改授权四项。

实体不清、跨平台或仅发布者级来源必须降级。中文俗称不能作为 direct entity，社区多报告也不能自动升级为 approved evidence。
