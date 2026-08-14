# Security Policy

本安全策略以中文保留关键威胁和不可绕过的安全边界，并提供英文摘要，便于国际协作。

This policy preserves the authoritative safety boundaries in Chinese and provides English summaries for international review.

## 报告安全漏洞

请不要公开可能导致误删、策略绕过或隐私泄露的细节。通过仓库维护者指定的私密安全渠道提交：受影响版本、复现步骤、最小样例、影响评估和建议缓解方式。不要附带真实用户文件、凭据或完整路径。

## 重点风险

- **误分类风险**：软件、文件或系统组件可能因身份不完整、别名或证据冲突而被错误分类；不确定时降级为 `ASK_USER` 或 `KEEP`。
- **误删除风险**：候选分类不是执行授权；任何真实操作仍须通过权限、确认、适用的可逆性要求和审计安全门。
- **L1 受控清理风险**：PR15 只允许 cleanup preview 中的 temp/cache/log 普通文件；缺少 `--confirm`、allow-root、当前文件复核、保护路径检查或审计输出时不得删除。
- **隐私泄露**：PR1 离线运行，不联网、不上传；日志和样例应去标识化。
- **规则库投毒**：规则贡献必须提供来源和反例分析，经过代码审查与危险案例测试后才能合并。
- **外部工具调用**：PR1 禁止调用任何卸载、杀毒、清理、启动项或系统修改工具。
- **AI 生成绕过策略风险**：AI 输出是不可信建议，不能改写硬规则、权限上限或直接触发操作。
- **社区规则恶意标记正常软件的风险**：社区输入只能增加证据或提高怀疑程度；恶意或低质量标记必须被降级、拒绝或送交人工复核。
- **紧急警告规则**：只允许提高风险、产生告警或降级为 `ASK_USER`/`BLOCK`；不得触发删除。规则需注明时效、来源、影响范围并接受快速复核和撤回。

Threat summary: misclassification, accidental deletion, privacy leakage, rule poisoning, unsafe external-tool invocation, AI policy bypass, and malicious community labeling are all treated as first-class security risks.

以下约束不可协商：

```text
社区规则不能直接触发删除。
在线声誉不能直接触发删除。
AI 判断不能直接触发删除。
用户偏好不能绕过 BLOCK。
用户偏好不能绕过 Level 5 禁区。
用户偏好不能绕过 BLOCK 或 Level 5。
```

## 负责任披露流程

维护者应确认收件、复现和分级，在修复可用前限制细节传播；完成修复、回归测试和规则签核后协调发布。若漏洞已被利用，应优先发布紧急警告规则以阻断风险，但该规则仍不得执行删除。报告人和维护者共同商定公开时间与致谢方式。

PR1 尚未声明长期支持版本；安全修复以当前默认分支和受影响的已发布标签为准。

## Governance bypass threat model

v0.5 treats the Agent and all natural-language/evidence intelligence as untrusted
with respect to authorization.

- **Agent bypasses Guard / Agent 绕过 Guard**：如果集成允许 Agent 直接调用
  Windows API、PowerShell 或其他 executor，Guard 无法拦截。Host 必须强制相关动作
  经过 Guard。
- **Fabricated consent / 伪造确认**：Agent payload 中的 `user_confirmed` 不可信。
  Consent 必须由 trusted host/UI 认证，并绑定 decision、fingerprint、targets、effect、
  scope、confirmation level 与 expiry。
- **TOCTOU target change / 目标变化**：preview 与执行之间的 path/type/hash/size/
  mtime/reparse/protection 变化必须使旧授权失效并触发重新评估。
- **Audit tampering / 审计篡改**：canonical SHA-256 前向哈希链检测历史 payload
  或链接修改；它不提供签名、加密或访问控制。
- **Scope expansion / 范围扩大**：Consent 或 executor 试图从单目标扩大到 wildcard、
  新目录或新 effect 时必须拒绝。
- **Rollback mismatch / 回滚错配**：L2/L3/L4 rollback contract/plan 必须绑定同一
  decision 与 action fingerprint，未过期且满足 backup/reversibility/verification 要求。
- **Untrusted evidence escalation / 不可信证据越权**：PUP、Reputation、Behavior、
  Evidence、community input 和 Agent confidence 只能增加限制，不能产生授权或降低
  requirements。

PC CleanGuard is not kernel enforcement, a sandbox, EDR, antivirus, or an OS
identity boundary. Its protection is only effective when the integrating host
routes actions through it and protects the trusted consent/audit surfaces.
