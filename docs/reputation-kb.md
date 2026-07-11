# Reputation KB Contract / 声誉知识库契约

PR18 建立 Reputation KB 的数据契约与信任边界，不联网、不爬取网站，也不把现有 SQLite knowledge store 接入自动执行。

## 用途

Reputation record 只服务于解释、排序、风险提示和人工复核。每条记录必须说明软件身份、行为类别、来源、日期、证据摘要、置信度、司法辖区、语言、误报风险、review status 与许可说明。

Schema：[`schemas/reputation_record.schema.json`](../schemas/reputation_record.schema.json)

Synthetic examples：[`examples/reputation/pr18_reputation_records.json`](../examples/reputation/pr18_reputation_records.json)

## 中文 PUP behavior taxonomy

- `forced_installation`：强制安装
- `difficult_uninstall`：难以卸载
- `browser_hijacking`：浏览器劫持
- `ad_popup`：广告弹窗
- `malicious_collection`：恶意收集
- `malicious_uninstall`：恶意卸载
- `malicious_bundling`：恶意捆绑
- `other_user_rights_violation`：其他侵害用户权益行为

这些标签描述有证据支持的行为类别，不等于“恶意软件定罪”，也不携带卸载或删除许可。

## Review status

- `draft`：未完成，不能对外解释为结论。
- `needs_human_review`：证据或身份仍需人工复核。
- `approved_for_explanation`：可用于解释和风险提示，仍不能授权执行。
- `deprecated`：已过时，仅保留历史语境。
- `rejected`：记录被拒绝，不应参与推荐。

## Source boundary

允许记录 official vendor、security vendor、curated research、community report、user report 与 synthetic test 等来源类型。来源名称与 URL 只是出处 metadata：

- community report 不是 verdict；
- security vendor signal 不是本地身份确认；
- online reputation 不是删除授权；
- AI summary 不能提高 record 的执行权限；
- 单一来源不能自动触发删除、卸载或禁用。

所有 PR18 record 固定 `execution_authorized=false`。`confidence` 只表达当前证据质量，不是动作概率或授权分数。

## Privacy and licensing

不上传原始用户路径、文件、代码、照片、浏览器资料或凭据。公开 record 必须记录来源日期与 `license_note`，不能复制无许可内容。PR18 示例全部使用 `example.invalid`、虚构软件和自有 synthetic evidence。

## Update governance

新增或修改 record 必须经过 schema、taxonomy、误报风险与人工 review 检查。争议记录降级到 `needs_human_review` 或 `rejected`，不能用紧急标签绕过 Policy Engine、Developer Guard、BLOCK 或 Level 5。
