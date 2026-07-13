# PUP Risk User Flow

推荐流程：

```text
explicit report JSON
  → local reviewed Evidence Pack
  → conservative direct/indicator matching
  → uncertainty + source trace + checklist
  → local Review Pack
  → user review / keep / ask / collect more evidence
```

用户应优先查看 `source_url`、`match_basis`、`false_positive_risk` 和 checklist。名称重叠、publisher hint 或 behavior context 都不能证明本机目标属于某个 detection family；没有命中也不证明安全。

PUP insight 不直接删除、不卸载、不禁用，也不修改注册表。若安全工具有独立提示，应在其受信任界面中核验，而不是把 Review Pack 当作执行命令。
