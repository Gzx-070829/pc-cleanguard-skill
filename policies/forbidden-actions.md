# Forbidden Actions

PR1 禁止一切系统修改，包括删除、卸载、移动隔离、注册表写入、服务/启动项禁用、脚本执行、外部工具调用、联网和上传。

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

不得对 Program Files 残留、AppData 大目录或驱动做推测性删除。不得让 AI、在线声誉、社区规则或用户偏好把上述对象转为删除候选。
