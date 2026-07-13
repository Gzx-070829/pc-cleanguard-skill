# PUP Intelligence Review Pack

PUP Review Pack 是一个本地、离线、带来源追溯的复核目录：

```powershell
python -m pc_cleanguard.cli pup review-pack --input report.json --evidence-pack data/reputation/evidence_pack.real.zh-CN.json --output .pcg-pup-review
```

目录包含 START HERE、用户/机器摘要、PUP insight、matches、indicators、人工 checklist、source trace、误报反馈模板和 safety notice。已有输出目录默认拒绝；只有显式 `--overwrite` 才更新这 10 个已知产物，不清空目录或删除其他文件。

Matcher 是 conservative matching，不是 AV engine。Microsoft PUA detection family 不等于本机 installed app display name；indicator overlap 只能提示人工复核。Review Pack 不联网、不上传、不执行 PowerShell，也不提供删除、卸载、禁用或注册表修改授权。PC CleanGuard 不替代 Microsoft Defender 或其他安全工具。

PR27 Review Pack 增加 `behavior_indicators.json/md`、`cn_evidence_summary.md` 和 `adversarial_safety_summary.md`。中文 evidence 不是黑名单，behavior indicator 也不是 PUP 定罪；两者都进入人工复核且 `execution_gating_eligible_count=0`。

PR28 在显式提供 `--cn-source-matrix` 时增加 `cn_source_matrix.md`、`cn_candidate_sources.md` 和 `cn_source_policy_summary.md`，并把来源/候选数量写入 machine summary。新增文件解释为什么网友名单、历史榜、移动端通报和厂商文章不能直接生成 Windows 动作。

PR29 可显式加入 `--cn-win-evidence-pack`、`--include-evidence-quality` 和 `--include-real-report-validation-summary`。新增中文 Windows、quality 与 matchability 产物只支持本地人工复核；installer artifact 不是软件本体结论，execution gating 仍为 0。
