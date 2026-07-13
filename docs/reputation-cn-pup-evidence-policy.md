# 中文 PUP Evidence Policy

中文 PUP evidence 不是黑名单。PR27 只收录能够人工核验 URL、标题、日期和摘要的公开来源，并继续经过 PR25 的 candidate → review queue → pack 流程。

首批 5 条记录来自工信部公开 APP/SDK 用户权益通报。为避免把移动应用名单误用为 Windows 软件结论，记录只保存批次级行为摘要，不复制附件中的具体应用名称；全部限定为 `analogical_behavior`、`mobile_app/mobile_sdk`、`execution_authorized=false`。

官方来源提高的是来源可靠性，不是执行置信度。真实来源也不能单独触发删除、卸载、禁用或注册表修改。大量社区反馈最多进入 `needs_human_review`；论坛截图、情绪化投诉、无来源博客和专有签名/规则/样本库不得进入 pack。

PC CleanGuard 不联网抓取这些页面，不上传本地报告，也不替代 Microsoft Defender 或其他安全工具。
