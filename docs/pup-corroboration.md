# PUP 行为佐证

Evidence 命中会与同一 target 的浏览器、启动项、计划任务、服务和安装链 metadata 关联，形成 strong、moderate、weak、publisher-only 或 no-corroboration 人工复核信号。

direct_entity 也不是删除授权；installer_artifact 不是软件本体结论；name/publisher overlap 必须降级。行为佐证增强人工复核，不形成 PUP verdict，`execution_gating_eligible_count` 始终为 0。

PR31 将佐证结果接入用户报告：strong/moderate/weak/no-match 都会说明来源、行为 metadata 和人工检查步骤，但不会形成自动处置。
