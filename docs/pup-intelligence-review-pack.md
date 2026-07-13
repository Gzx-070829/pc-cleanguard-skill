# PUP Intelligence Review Pack

PUP Review Pack 是一个本地、离线、带来源追溯的复核目录：

```powershell
python -m pc_cleanguard.cli pup review-pack --input report.json --evidence-pack data/reputation/evidence_pack.real.zh-CN.json --output .pcg-pup-review
```

目录包含 START HERE、用户/机器摘要、PUP insight、matches、indicators、人工 checklist、source trace、误报反馈模板和 safety notice。已有输出目录默认拒绝；只有显式 `--overwrite` 才更新这 10 个已知产物，不清空目录或删除其他文件。

Matcher 是 conservative matching，不是 AV engine。Microsoft PUA detection family 不等于本机 installed app display name；indicator overlap 只能提示人工复核。Review Pack 不联网、不上传、不执行 PowerShell，也不提供删除、卸载、禁用或注册表修改授权。PC CleanGuard 不替代 Microsoft Defender 或其他安全工具。
