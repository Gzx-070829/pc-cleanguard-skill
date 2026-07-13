# Real Report Trial Flow

```powershell
python -m pc_cleanguard.cli trial report --input report.json --output .pcg-report-trial --evidence-pack data/reputation/evidence_pack.real.zh-CN.json --cn-win-evidence-pack data/reputation/evidence_pack.cn_win.zh-CN.json --include-behavior-indicators --include-evidence-quality
```

流程只读取显式 report/evidence，离线生成形状检查、脱敏清单、matchability、Review Pack、质量报告和 match/no-match 说明。默认不覆盖，不上传、不修改系统。
