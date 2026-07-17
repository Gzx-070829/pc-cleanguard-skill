# Windows Collector → Canonical Report

`windows report build` 读取一个用户显式指定的 collector 目录，验证 manifest，并复用现有 InstalledApp、StartupItem、WindowsService 与 ScheduledTask normalizer。

Canonical report 使用现有分析链需要的集合名：

- `installed_apps`
- `startup_items`
- `services`
- `scheduled_tasks`

同时包含 `scan_id`、时间、平台、隐私模式、collector 状态、错误、unsupported collector/field、redaction summary 与非授权标记。单个 collector 失败时结果为 `partial`；成功记录不会因另一个 collector 失败而丢失。无法转换的字段只记录字段名，不静默忽略，也不在 summary 复制原值。

## Raw 与 redacted

raw report 保留本地 metadata，可能含完整路径、用户名、设备名、邮箱、token-like 字符串和任务/服务命令。默认输出会把身份片段替换为 `<USER>`、`<DEVICE>`、`<EMAIL>` 或 `<TOKEN>`，同时保留产品名、发布者、服务名、任务名和软件目录层级。

Redaction summary 只含类型和数量，不生成可逆映射。推荐后续 scan、PUP review 和 persistence evaluation 使用 redacted report。

## 安全边界

构建、验证和 stats 都是离线文件转换。Python 不运行 collector，不执行 metadata，不联网、不上传，也不产生删除、卸载、禁用或注册表修改授权。
