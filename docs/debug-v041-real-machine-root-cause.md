# v0.4.1 真机汇流根因调查

本文记录 PR33 写生产实现之前完成的只读调查。调查只查看了既有脚本、模型、schema，以及未纳入 Git 的本机验收目录；没有执行采集结果中的命令，也没有修改系统。

## 1. Collector 与 canonical report 的字段差异

现有四个 collector 分别向 stdout 输出一个 JSON 数组：

| Collector | 原始身份字段 | 现有项目规范化字段 | 汇流缺口 |
| --- | --- | --- | --- |
| installed apps | `name`, `publisher`, `install_location`, `registry_key`, `uninstall_string` | `InstalledApp.app_id` / `target_id`, `name`, `publisher`, `install_location` | 没有 `scan_id`、平台、隐私模式、collector 状态；`uninstall_string` 只是 metadata，不能成为授权 |
| startup items | `name`, `command`, `registry_path`, `file_path` | `StartupItem.item_id` / `target_id`, `name`, `command`, `file_path` | 没有统一 report 包装、collector 状态或 unsupported fields |
| services | `service_name`, `display_name`, `path_name` | `WindowsService.service_id` / `target_id`, `display_name`, `path_name` | 没有统一 report 包装、collector 状态或 unsupported fields |
| scheduled tasks | `task_name`, `task_path`, `actions_summary` | `ScheduledTask.task_id` / `target_id`, `task_name`, `actions_summary` | 没有统一 report 包装、collector 状态或 unsupported fields |

`schemas/scan_result.schema.json` 要求顶层 `scan_id`、`timestamp`、`platform`、`privacy_mode`、`software_entries`、`startup_items`、`services`、`processes` 和 `schema_version`。现有 scan pipeline 同时接受 `installed_apps` 或 `software_entries`，而真实报告验证、PUP 复核与 persistence linker 使用 `installed_apps`。因此 v0.4.1 canonical report 应复用 `installed_apps`、`startup_items`、`services`、`scheduled_tasks`，并补齐 report 元数据与 collector 状态；不能另造无法被现有链路消费的第二套对象模型。

## 2. 为什么原输出不能直接进入 scan / trial / persistence

1. 四个文件是互不关联的裸数组，没有共同 `scan_id`、时间戳、来源类型、隐私状态或采集清单。
2. 调用方无法区分“成功但零条记录”“collector 不支持”“collector 失败”和“文件缺失”。
3. 原始记录没有稳定生成 `target_id`；scan pipeline 的现有 normalizer 能生成它，但没有目录级汇流入口。
4. trial 与 persistence 期望一个包含四个集合的 report 对象，而不是四个独立文件。
5. 旧流程没有正式 raw/redacted 边界；上次验收只能手工复制并脱敏，不能给出可验证的 redaction summary。
6. 无 manifest 时，单个 collector 失败会表现为空文件或解析错误，无法安全生成明确的 partial report。
7. persistence linker 依赖 `install_location`、`command`、`path_name`、`actions_summary` 等字段做结构关联；这些字段虽已存在于 collector，但没有 canonical 汇流、验证和脱敏保证。

## 3. Desktop demo 被阻断的原因

仓库位于 Desktop。现有 `demo quickstart` 会把调用方给出的 repo-relative demo root 解析到 Desktop 子目录；`_explicit_demo_root()` 与 `CleanupConfirmation` 都把 `desktop` / `桌面` 视为保护路径。因此 demo 在初始化前即 fail-closed。这是安全策略按设计工作，不是误报。

## 4. 为什么不能把 Desktop 加入 allowlist

Desktop 常含用户文档、照片、下载内容、代码仓库和临时工作成果。对 Desktop 做通用放行会让 synthetic demo 标记成为绕过真实文件保护的入口，也会破坏 executor 的二次路径复核。正确修复是在系统临时目录下创建 PC CleanGuard 专用、带 nonce、文件清单和 SHA-256 的 synthetic workspace；报告目录可以位于仓库，但被操作的文件不能位于 Desktop。

## 5. Windows PowerShell 5.1 与 PowerShell 7 差异

只读探针使用 `-NoProfile -ExecutionPolicy Bypass -File` 分别运行了四个既有脚本。当前机器上 Windows PowerShell 与 pwsh 均成功得到相同条数（218 / 10 / 310 / 202），说明现有脚本没有已复现的 PS7-only 语法错误。

已确认的差异与兼容风险是：

1. 上次 Windows PowerShell 失败日志是 `running scripts is disabled`。这是宿主进程的 ExecutionPolicy 环境限制；pwsh 当时可运行。当前进程级 `-ExecutionPolicy Bypass` 可运行，且不会修改用户或机器策略。
2. 旧脚本只写 stdout，输出编码依赖宿主和重定向方式。Windows PowerShell 5.1 常见文件输出默认 UTF-16LE，而 PowerShell 7 默认 UTF-8；这会让同一 JSON 在 Python UTF-8 读取路径中表现不一致。
3. `Get-ScheduledTask` 的模块可用性可能因 Windows 版本、PowerShell edition 或模块加载环境不同。旧脚本用 `-ErrorAction SilentlyContinue`，无法区分 unsupported 与空结果。
4. `Get-CimInstance` / ScheduledTasks 模块失败时，旧脚本没有 collector 级 try/catch 和 manifest 状态，错误可能成为空输出或非结构化 stderr。
5. 新入口必须避开 `??`、`?:`、`ForEach-Object -Parallel`、`ConvertFrom-Json -AsHashtable` 和其他 PS7-only 参数，并使用显式 UTF-8 no BOM 文件写入。

## 6. 代码问题与环境限制

代码问题：

- 缺少 collector manifest、目录 ingest、canonical report、schema 验证和 partial 状态。
- 缺少正式 redaction 与不可逆的计数摘要。
- 缺少 PS5.1/PS7 共用的显式编码、独立 try/catch、structured unsupported 输出。
- 缺少安全 synthetic workspace、验收编排、本地 evaluation 和 link diagnostics。
- publisher-only 目前会生成弱边；v0.4.1 要将其记为被拒绝的诊断线索，而不是实体边。

环境限制：

- 上次 Windows PowerShell 的脚本执行策略阻断。
- `Get-ScheduledTask` 等 cmdlet 可能在某些环境不可用。
- Desktop 是受保护用户目录；仓库位置导致 repo-relative demo root 合法地被拒绝。
- PUP 零命中、persistence 零边均可能是合法数据结果，不能通过降低阈值“修复”。

## 7. 修复对应的先失败测试

| 修复 | 先确认 RED 的测试 |
| --- | --- |
| collector 目录读取、manifest 与 partial 状态 | `test_windows_collector_ingest.py` |
| 复用四类 normalizer 构建 canonical report | `test_windows_canonical_report.py` |
| 用户名、设备、邮箱、token 与路径脱敏 | `test_windows_report_redaction.py` |
| `windows report build/validate/stats` 安全参数与默认不覆盖 | `test_windows_report_cli.py` |
| PowerShell 只读、独立错误状态、UTF-8 输出契约 | `test_powershell_collector_contract.py` |
| 禁止 PS7-only 语法并保留 PS5.1 兼容 | `test_powershell_compat_contract.py` |
| temp 专用 synthetic manifest、nonce、hash、未知文件、symlink fail-closed | `test_synthetic_demo_workspace.py` |
| synthetic quarantine / restore / SHA-256 / 无永久删除 | `test_demo_acceptance.py` |
| canonical redacted report 的离线 evaluation 产物 | `test_windows_local_evaluation.py` |
| 零边解释、publisher-only 拒绝、strong fixture 保持强边 | `test_persistence_link_diagnostics.py` |
| 版本、文档、evidence 非授权与发布清单 | `test_v041_release_readiness.py` |

所有实现均按上述测试组执行 RED → GREEN → REFACTOR；Python 不会启动 PowerShell，collector 输出中的 command/path/action 永远只作 metadata。
