# Windows Startup, Services, and Scheduled Tasks Collectors / Windows 启动项、服务与计划任务采集器

## Scope / 范围

PR6 introduces read-only collectors for startup items, Windows services, and scheduled tasks. PR6 does not collect running processes.

PR6 引入启动项、Windows 服务和计划任务的只读采集器。PR6 不采集运行进程。

Startup collection is limited to the approved HKCU/HKLM `Run` and `RunOnce` keys plus the user and common Startup folders. Service collection reads `Win32_Service`. Scheduled-task collection reads task metadata and summaries only.

启动项采集仅限获准的 HKCU/HKLM `Run`、`RunOnce` 项以及用户和公共 Startup 文件夹。服务采集读取 `Win32_Service`。计划任务只读取任务元数据和摘要。

## Safety boundary / 安全边界

Collectors observe metadata only and output JSON to stdout. They expose no output-file parameter and perform no registry write, startup disabling, service start/stop/change, task execution/change, deletion, network call, or upload.

采集器只观察元数据并向 stdout 输出 JSON。它们没有输出文件参数，不写注册表、不禁用启动项、不启动/停止/修改服务、不执行/修改计划任务、不删除、不联网、不上传。

Startup commands, service path names, and scheduled-task action summaries are metadata only. They are not commands for PC CleanGuard and never grant execution authorization.

启动命令、服务路径和计划任务动作摘要只是元数据。它们不是 PC CleanGuard 的执行命令，也不授予执行权限。

Python normalizers accept caller-supplied dictionaries and never execute PowerShell collectors, startup commands, service binaries, or task actions. They only construct `GovernanceTarget` objects; classification remains exclusively in the Policy Engine.

Python normalizer 只接收调用方提供的字典，不自动执行 PowerShell collector、启动命令、服务程序或任务动作。它们只构造 `GovernanceTarget`；分类仍完全由 Policy Engine 负责。

## Sample privacy / 示例隐私

PR6 examples use synthetic `Example` names or clearly marked Microsoft/NVIDIA examples. User paths use `%USERPROFILE%`; samples contain no real account, token, host name, or machine-specific path.

PR6 示例使用虚构的 `Example` 名称或明确标注的 Microsoft/NVIDIA 示例。用户路径统一使用 `%USERPROFILE%`，不包含真实账号、token、主机名或机器路径。
