# Reputation Evidence Quality Dashboard

v0.3.2 增加中文 Windows approved/candidate/backlog、mapping、行为覆盖、时间范围、第二来源、误报风险和 `quality_gate_passed`。任一执行授权、正向 execution gating、来源缺失或越界语气都会使质量门失败。

```powershell
python -m pc_cleanguard.cli reputation evidence quality --inputs data/reputation/evidence_pack.real.zh-CN.json data/reputation/evidence_pack.cn_win.zh-CN.json --output evidence_quality.md
```

Dashboard 评估来源完整性、实体清晰度、映射精度、时间范围、误报风险、复核状态、行为覆盖和执行安全。它是数据质量报告，不是执行授权；`execution_gating_eligible_count` 固定为 0。已有输出默认不覆盖，只有显式 `--overwrite` 才更新。
