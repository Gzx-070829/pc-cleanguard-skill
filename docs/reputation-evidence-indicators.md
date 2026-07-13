# Reputation Evidence Indicators

Evidence Indicator 把已核验 record 中的 detection family、installer family、publisher 和 behavior metadata 转换为结构化人工复核线索。它不是 AV signature，也不是本机实体判定。

硬边界：

- `detection_family` 只作为 report-level informational context，不能直接等同 installed app display name。
- `installer_family` 的名称重叠最多是 medium-strength、高误报风险线索。
- `publisher_hint` 只能辅助解释，不能单独形成目标命中。
- `behavior_hint` 只进入解释和 uncertainty notes。
- weak/informational 指标必须人工复核。
- 所有 indicator 固定 `requires_human_review=true`、`execution_gating_eligible=false`。

```powershell
python -m pc_cleanguard.cli reputation evidence indicators --input data/reputation/evidence_pack.real.zh-CN.json --output indicators.json
python -m pc_cleanguard.cli reputation evidence indicators-stats --input data/reputation/evidence_pack.real.zh-CN.json
```

这些命令完全离线，只读取显式本地 Evidence Pack 并写显式 JSON 输出。
