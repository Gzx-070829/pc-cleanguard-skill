# v0.4.1 Release Checklist

只有以下项目全部通过，才允许 merge、tag 和 GitHub Release：

- [ ] 根因文档先于生产实现完成。
- [ ] 新功能按测试组完成 RED → GREEN → REFACTOR。
- [ ] compileall、全部 unittest 与 diff-check 通过。
- [ ] Windows PowerShell 5.1 doctor 和 collector 通过；四类结果或 structured unsupported 均有 manifest。
- [ ] 若安装 pwsh，doctor/collector 无未捕获异常。
- [ ] canonical report build/validate/stats 通过。
- [ ] 默认 report 已脱敏，未发现用户名、设备名、邮箱或 token-like 原值。
- [ ] synthetic workspace 位于专用 temp root；隔离、恢复和 SHA-256 通过。
- [ ] Desktop、Documents、代码仓库与 Developer Guard 没有放宽。
- [ ] Windows local evaluation、persistence graph、link diagnostics 与 governance plan 通过。
- [ ] PUP 0 match 被允许；任何 match 仍不授权执行。
- [ ] `execution_gating_eligible_count=0`。
- [ ] 未联网、上传、写注册表、禁用服务/启动项/任务、卸载或永久删除真实文件。
- [ ] `.pcg-local-evaluation-v041/` 被 Git 忽略，raw report 未被追踪。
- [ ] CLI version 为 0.4.1。
- [ ] commit、merge、tag 与 Release 名称符合 PR33 约定。
