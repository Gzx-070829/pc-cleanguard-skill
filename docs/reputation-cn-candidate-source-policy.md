# 中文候选来源策略

候选池是人工调查队列，不是 approved evidence。真实实体候选必须有 `source_url`、`source_title`、日期/时间范围和克制的 `evidence_summary`；没有可靠来源时不得编造软件指控。

敏感厂商、驱动工具、输入法、下载站、浏览器工具条等实体必须先进入 candidate/review backlog。厂商级争议不得扩展到全部产品；名称碰撞不得当 direct entity；移动端来源只能 analogical behavior。

```powershell
python -m pc_cleanguard.cli reputation cn-source candidates --input data/reputation/cn_candidate_sources.zh-CN.json --output cn_candidate_summary.json
```

输出默认不覆盖。全部候选固定 `execution_authorized=false`，不能授权删除、卸载、禁用或注册表修改。
