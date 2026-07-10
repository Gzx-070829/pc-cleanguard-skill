# External Tool Recommender / 外部工具推荐器

PR13 把 cleanup plan、治理判断、证据和已安装软件元数据连接到 PR12 的显式工具目录与信任策略。输出只是给用户和 AI 阅读的结构化建议，不是执行授权。

PR13 connects cleanup plans, governance decisions, evidence, and installed-app metadata to the explicit PR12 catalog and trust policy. Its output is a structured suggestion for review, never execution authority.

## 数据流 / Data flow

```text
cleanup plan + decisions + evidence + installed-app metadata
                         |
                    ToolMatcher
                         |
     explicit catalog + ToolTrustPolicy allowlist
                         |
                  ToolRecommender
                         |
 ExternalToolRecommendation (Level 0, plan only, confirmation required)
```

只有未被策略阻断的 `REVIEW_REMOVAL_CANDIDATE` 才参与匹配。`BLOCK`、Level 5 和 hard-rule 阻断不会产生工具匹配。

Only unblocked `REVIEW_REMOVAL_CANDIDATE` steps are matched. `BLOCK`, Level 5, and hard-rule blocks never become tool matches.

## 匹配规则 / Matching rules

- `official_uninstaller`：适合普通软件卸载候选，作为优先复核路径。
- `winget`：仅当对应 installed-app metadata 明确包含 `package_id` 时匹配。
- `vendor_cleanup_tool`：仅当 metadata 的 `vendor_cleanup_tool_id` 精确匹配 catalog record 时匹配。
- `trusted_third_party_uninstaller`：只作为次级复核建议，不作为默认路径。

匹配成功不等于受信。每条 catalog record 仍必须经过 `ToolTrustPolicy`：allowlisted 工具可以作为可信计划建议；未受信工具会保留为 `blocked=true` 的解释性建议。

A metadata match is not trust. Every catalog record still passes through `ToolTrustPolicy`: allowlisted records may appear as trusted planning suggestions, while untrusted records remain visible only as blocked explanations.

## 固定安全属性 / Fixed safety properties

每条 recommendation 都固定包含：

- `execution_level=LEVEL_0_READ_ONLY`
- `requires_user_confirmation=true`
- `plan_only=true`
- `blocked_if_untrusted=true`
- `execution_authorized=false`

Recommendation 不包含真实命令、参数或可执行文件路径。外部工具推荐不是下载、运行、卸载或系统修改授权。AI 只能把建议和证据展示给用户；真正执行必须等待未来的 controlled executor，并再次通过 Policy Engine 和用户确认。

Recommendations contain no real command, arguments, or executable path. AI may present the suggestion and evidence, but actual use must wait for a future controlled executor with fresh policy and user-confirmation gates.

不得自动下载未知 EXE/MSI，不得静默运行卸载器，不得运行 package manager 或 uninstall metadata，不得联网或上传。

## Skill action

`recommend_external_tools` 接受以下显式 JSON payload：

- `cleanup_plan` 或 `report_summary`，二选一；
- `catalog.records`；
- `allowlisted_tool_ids`；
- 可选的 `governance_decisions`、`evidence` 和 `installed_apps`。

示例见 `examples/skill_actions/recommend_external_tools_request.json`。响应的所有 recommendations 都是 Level 0 计划。

## CLI

```powershell
python -m pc_cleanguard.cli tools recommend --input examples/skill_actions/recommend_external_tools_request.json --output output/recommendations.json
```

CLI 只读取显式 `.json` 输入并写入显式 `.json` 输出。输出文件存在时默认拒绝覆盖；只有调用方显式添加 `--overwrite` 才会替换治理产物。该子命令不发现工具、不下载、不联网、不启动任何进程。

## Schemas and examples

- `schemas/external_tool_recommendation.schema.json`
- `schemas/skill_action_request.schema.json`
- `schemas/skill_action_response.schema.json`
- `examples/external_tools/pr13_tool_recommendations.json`
- `examples/skill_actions/recommend_external_tools_response.json`
