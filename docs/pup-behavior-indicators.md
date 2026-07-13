# PUP Behavior Indicators / 行为线索

PR27 从用户显式提供的 report 元数据生成行为线索，例如启动项、服务、计划任务、bundle/installer 名称、未知发布者或可疑安装位置。它不读取真实浏览器配置、不扫描注册表、不访问文件内容，也不执行系统命令。

Behavior indicator 不是 PUP 定罪。每条线索固定 `requires_human_review=true`、`execution_gating_eligible=false`，高误伤风险进入 uncertainty notes 和人工 checklist。

```powershell
python -m pc_cleanguard.cli pup behavior --input report.json --output behavior_indicators.json
```

输出只用于解释和复核；PC CleanGuard 不是杀毒软件，也不替代 Microsoft Defender。
