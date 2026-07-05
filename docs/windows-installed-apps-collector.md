# Windows Installed Apps Collector / Windows 已安装软件采集器

## Scope / 范围

PR5 introduces a read-only Windows installed apps collector. It lets PC CleanGuard observe installed-app metadata without modifying the computer.

PR5 引入只读 Windows 已安装软件采集器，让 PC CleanGuard 在不修改电脑的前提下观察软件元数据。

The collector reads only the three approved HKLM/HKCU uninstall-registry paths and outputs JSON to stdout. It has no output-file option and needs no administrator permission.

采集器只读取三个获准的 HKLM/HKCU 卸载注册表路径，并且只向 stdout 输出 JSON。它没有文件输出选项，也不需要管理员权限。

## Safety boundary / 安全边界

No uninstall, deletion, registry write, service change, startup change, network call, or upload is performed.

不卸载、不删除、不写注册表、不改服务、不改启动项、不联网、不上传。

Uninstall strings are metadata only. Their presence means only that a standard entry was observed; it is not execution authorization or automatic-uninstall permission.

卸载字符串只是元数据。它的存在只表示观察到标准入口，不是执行授权，也不是自动卸载许可。

The Python normalizer never executes the collector, PowerShell, an uninstall string, or any external tool. It accepts caller-supplied dictionaries, normalizes fields, constructs a `GovernanceTarget`, and leaves every classification to the Policy Engine.

Python normalizer 不自动执行 collector、PowerShell、卸载字符串或任何外部工具。它只接收调用方提供的字典、归一化字段、构造 `GovernanceTarget`，并把所有分类交给 Policy Engine。

## Data handling / 数据处理

Missing registry values become `null` or conservative defaults. `app_id` is a short stable hash of normalized identity fields and never contains the uninstall command. Install dates remain unparsed strings because Windows entries use inconsistent formats.

缺失注册表字段转换为 `null` 或保守默认值。`app_id` 是身份字段的稳定短哈希，不包含卸载命令。由于 Windows 条目日期格式并不一致，安装日期保留原始字符串。

PR5 does not call winget; `winget_visible` is schema space reserved for a future read-only collector.

PR5 不调用 winget；`winget_visible` 只是为未来只读采集器预留的 schema 字段。
