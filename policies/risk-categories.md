# Risk Categories

| 分类 | 适用对象 | 允许动作 | 禁止动作 | 用户确认 | 审计 |
|---|---|---|---|---|---|
| `KEEP` | 系统组件、核心工具、证据不足但应保护的对象 | 保留、只读报告 | 修改、删除、卸载 | 否 | 可选 |
| `ASK_USER` | 身份/用途不明或证据冲突对象 | 询问、补充证据 | 自动修改 | 必须 | 必须 |
| `SAFE_REMOVE` | 已知非必要软件且有标准卸载器 | 提议未来标准卸载 | 静默删除、残留扫除 | 必须 | 必须 |
| `STARTUP_OFF` | 非关键启动项 | 提议未来可逆禁用 | 删除程序、禁用关键项 | 必须 | 必须 |
| `QUARANTINE` | 临时目录中的高疑似文件 | 提议未来可逆隔离 | PR1 移动、直接删除 | 必须 | 必须 |
| `BLOCK` | Level 5、敏感路径、用户数据与保护对象 | 拒绝并解释 | 任何修改 | 不适用 | 必须 |

分类描述的是策略结果，不是执行指令。

The classifications below are policy outcomes, not execution instructions.

| Label | Applies to | Permitted response | Forbidden response | User confirmation | Audit |
|---|---|---|---|---|---|
| `KEEP` | System components, core tools, or protected uncertain objects | Preserve and report read-only | Modify, delete, or uninstall | No | Optional |
| `ASK_USER` | Unknown identity/use or conflicting evidence | Ask and collect evidence | Automatic modification | Required | Required |
| `SAFE_REMOVE` | Known non-essential software with a standard uninstaller | Propose a future standard uninstall | Silent deletion or remnant sweeping | Required | Required |
| `STARTUP_OFF` | Non-critical startup items | Propose a future reversible disable | Delete the program or disable critical items | Required | Required |
| `QUARANTINE` | Highly suspicious files in temporary locations | Propose future reversible isolation | Move in PR1 or delete directly | Required | Required |
| `BLOCK` | Level 5, sensitive paths, user data, and protected objects | Refuse and explain | Any modification | Not applicable | Required |

Candidate labels never constitute execution authorization.
