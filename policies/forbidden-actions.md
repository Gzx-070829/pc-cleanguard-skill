# Forbidden Actions

PR1 禁止一切系统修改，包括删除、卸载、移动隔离、注册表写入、服务/启动项禁用、脚本执行、外部工具调用、联网和上传。

PR1 forbids every system mutation, including deletion, uninstallation, quarantine movement, registry writes, service/startup changes, script execution, external-tool invocation, networking, and uploads.

以下对象为硬性禁止或强保护对象：

- `C:\Windows`、`C:\Windows\System32` 与 Driver Store；
- 恢复分区；
- 用户 Documents、Desktop、Pictures、Videos；
- 用户代码仓库；
- 浏览器 profile 数据；
- 密码管理器与凭据存储；
- BitLocker、TPM 与登录认证组件；
- 安全软件核心文件；
- 未知批量文件组；
- 来源不明的清理脚本。

The protected set includes Windows system paths and driver stores, recovery partitions, user documents and media, source-code repositories, browser profiles, password managers, credential stores, authentication components, security-software core files, unknown bulk groups, and untrusted cleanup scripts.

不得对 Program Files 残留、AppData 大目录或驱动做推测性删除。不得让 AI、在线声誉、社区规则或用户偏好把上述对象转为删除候选。

Never perform speculative removal of Program Files remnants, large AppData directories, or drivers. AI output, online reputation, community rules, and user preferences may not turn these protected objects into removal candidates.

社区规则不能直接触发删除。AI 判断不能直接触发删除。在线声誉不能直接触发删除。

Community rules, AI judgments, and online reputation may never directly trigger deletion.
