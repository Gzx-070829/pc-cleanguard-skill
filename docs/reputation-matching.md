# Reputation Matching / 声誉证据匹配

PR21 将显式 report/scan JSON 中的软件、启动项、服务和计划任务名称与本地 Seed Pack 做确定性匹配。依据仅包括 normalized software name、aliases，以及名称相关时的 publisher 辅助证据。

匹配结果携带 record ID、行为类别、置信度、误报风险、review status 和 evidence。每条结果固定 `execution_authorized=false`。发布者相同不能单独构成命中，模糊名称也不会越过人工复核。

Matcher 不联网、不爬虫、不读取专有检测库，也不改变 Policy Engine 决策。
