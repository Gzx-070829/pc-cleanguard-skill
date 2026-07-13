# Reputation Evidence Intake

PR25 把公开来源候选、人工复核决定和最终 Evidence Pack 分成三个离线文件：

```text
evidence_candidates.zh-CN.json
  → human review
  → evidence_review_queue.zh-CN.json
  → offline build
  → evidence_pack.real.zh-CN.json
```

候选记录只描述“某个公开页面声称了什么”，不能直接进入 Reputation Matcher。只有 `reviewer_decision=accept_as_evidence`、source URL/title 非空、映射和实体范围合法的候选才能构建。构建出的记录会再次通过 PR24 Evidence Guard，强制 `is_synthetic=false`、`execution_authorized=false`。

```powershell
python -m pc_cleanguard.cli reputation evidence intake validate --input data/reputation/evidence_candidates.zh-CN.json
python -m pc_cleanguard.cli reputation evidence review validate --input data/reputation/evidence_review_queue.zh-CN.json
python -m pc_cleanguard.cli reputation evidence build --candidates data/reputation/evidence_candidates.zh-CN.json --reviews data/reputation/evidence_review_queue.zh-CN.json --output output/evidence_pack.real.zh-CN.json
```

这些命令只读显式本地 JSON，并写调用方指定的 JSON；不联网、不下载、不执行系统动作。输出已存在时默认拒绝覆盖。

不确定就使用 `needs_more_evidence`、`reject` 或降低关系置信度，不得为了数量把候选硬塞进 real evidence。MIIT APP/SDK 通报必须保持移动端 `entity_scope`，只能使用 analogical/publisher 映射，不能成为 Windows 删除名单。
