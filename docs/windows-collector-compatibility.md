# Windows Collector 兼容性

## 支持范围

| Host | 状态 | 说明 |
| --- | --- | --- |
| Windows PowerShell 5.1 | 支持 | 使用兼容语法与显式 UTF-8 no BOM 文件写入 |
| PowerShell 7 on Windows | 支持 | 可选；可用 cmdlet 与结果写入 manifest |
| 非 Windows | 不支持 collector | Python report/evaluation 仍可消费调用方提供的 canonical JSON |

入口不会使用 `??`、`?:`、parallel pipeline 或 `ConvertFrom-Json -AsHashtable`。每个 collector 独立 try/catch；可选 cmdlet 不存在时生成 `unsupported`，不调用外部命令 fallback。

旧的四个 collector 继续负责实际读取。编排器只调用它们、解析 JSON、写固定文件与 manifest，不复制采集逻辑。旧脚本在隔离作用域中关闭继承的 StrictMode，以兼容注册表对象上可能缺失的可选属性。

## 编码

Windows PowerShell 5.1 与 PowerShell 7 的宿主默认文件编码不同。v0.4.1 使用 `System.Text.UTF8Encoding(false)` 和 `WriteAllText` 明确写 UTF-8 no BOM，不依赖 stdout 重定向的宿主默认值。

## ExecutionPolicy

文档命令中的 `-ExecutionPolicy Bypass` 只设置新启动进程的策略。脚本不会调用策略写入、注册表写入或系统配置命令。若组织策略仍阻断，请保留 doctor 输出并由管理员按组织规则处理，不要修改 PC CleanGuard 的保护逻辑。
