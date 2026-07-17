# Windows 真机快速开始

v0.4.1 把采集和分析拆成两个显式步骤。Python 不自动启动 PowerShell，collector 也不会执行采集到的 command、service path、task action 或 uninstall string。

## 1. 只读采集

先检查当前宿主：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\collector-doctor.ps1 -OutputPath .pcg-collectors-doctor.json
```

再采集四类 metadata：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\collect-windows-metadata.ps1 -OutputDirectory .pcg-collectors
```

`-ExecutionPolicy Bypass` 仅影响这个新进程，不修改用户或机器 ExecutionPolicy，不写注册表。若安装了 PowerShell 7，可把 `powershell.exe` 换成 `pwsh`。缺少 `Get-ScheduledTask` 时，该 collector 会标记为 structured `unsupported`，其他采集继续。

输出包括四个 JSON 数组、`collector_manifest.json` 和 `collector_errors.json`。它们可能含用户名、设备名和完整路径，请视为本地敏感数据。

## 2. 构建脱敏报告并离线评估

```powershell
python -m pc_cleanguard.cli windows report build --collector-dir .pcg-collectors --output windows-report.redacted.json --validation-output windows-report-validation.json
python -m pc_cleanguard.cli windows report stats --input windows-report.redacted.json --output windows-report-stats.json
```

默认 `--output` 是脱敏 report。只有同时提供 `--raw-output` 和 `--i-understand-local-sensitive-data` 才写 raw canonical report。

```powershell
python -m pc_cleanguard.cli evaluation windows --report windows-report.redacted.json --output .pcg-evaluation --evidence-pack data/reputation/evidence_pack.real.zh-CN.json --cn-win-evidence-pack data/reputation/evidence_pack.cn_win.zh-CN.json --include-persistence-chain --include-pup-review --include-evidence-quality --include-user-friendly-report
```

从 `.pcg-evaluation/START_HERE.md` 开始阅读。0 PUP match 不等于绝对安全；0 persistence edge 也可能是缺少强结构 metadata 的合法结果。
