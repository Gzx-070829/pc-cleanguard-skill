# Real-source Evidence Review / 真实来源人工核验

PR25 首批加入 5 条人工核验记录，均来自 Microsoft Security Intelligence 的公开 Windows PUA description 页面。核验于 2026-07-13 完成，记录了页面标题、页面展示的发布日期和克制的中文行为摘要：

- [PUA:Win32/InstallCore](https://www.microsoft.com/en-us/wdsi/threats/malware-encyclopedia-description?Name=PUA%3AWin32%2FInstallCore) — 页面发布日期 2015-03-11；只记录捆绑、浏览器修改和非预期安装行为。
- [PUA:Win32/FusionCore](https://www.microsoft.com/en-us/wdsi/threats/malware-encyclopedia-description?Name=PUA%3AWin32%2FFusionCore) — 页面发布日期 2016-06-28；只记录 bundling 描述。
- [PUA:Win32/Slimware](https://www.microsoft.com/en-us/wdsi/threats/malware-encyclopedia-description?Name=PUA%3AWin32%2FSlimware) — 页面发布日期 2017-02-08；只记录页面展示的广告、可疑问题提示和捆绑行为。
- [PUA:Win32/PiriformBundler](https://www.microsoft.com/en-us/wdsi/threats/malware-encyclopedia-description?Name=PUA%3AWin32%2FPiriformBundler) — 页面发布日期 2020-07-27；仅指页面定义的特定 bundling installers，不把 Piriform 产品整体标记为 PUA。
- [PUA:Win32/MediaArena](https://www.microsoft.com/en-us/wdsi/threats/malware-encyclopedia-description?Name=PUA%3AWin32%2FMediaArena&threatId=359463) — 页面发布日期 2023-03-20；只记录浏览器设置修改、搜索重定向和搜索查询收集描述。

这些 detection-family 记录采用 `direct_entity + windows_desktop_software`，但 direct entity 只表示来源页面与检测族名称直接对应。它不证明本机同名文件属于该家族，更不授权删除、卸载或禁用。`relation_confidence` 描述关系质量，不是执行置信度；`false_positive_risk` 继续要求本地身份与用户意图复核。

真实 evidence 不是黑名单。真实来源 evidence 仅用于解释、排序和人工复核，不是删除、卸载、禁用授权。运行时完全离线，也不会自动访问上述 URL。

PR26 未扩充这 5 条记录：现有官方来源足以验证 indicator/review-pack 闭环，继续为数量加入实体会增加核验和误伤风险。本轮优先把来源追溯、保守匹配和反馈闭环做完整；新增真实记录仍必须走 PR25 intake/review 流程。

PR27 另建中文 pack，加入 5 条人工核验的工信部公开批次页面。它们不复制具体 APP 名单，只作为移动端行为类比；不能映射为 Windows direct entity、发布者黑名单或 PUP 执行建议。
