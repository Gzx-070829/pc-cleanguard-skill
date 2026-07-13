# Source Trace / 来源追溯

Microsoft Security Intelligence 的 PUA detection family 是公开安全情报来源，但 detection family 不等于本机 installed app display name，也不是 PC CleanGuard 的删除授权。

## ev-real-ms-installcore

- source_title: PUA:Win32/InstallCore threat description - Microsoft Security Intelligence
- source_url: https://www.microsoft.com/en-us/wdsi/threats/malware-encyclopedia-description?Name=PUA%3AWin32%2FInstallCore
- source_date: 2015-03-11
- source_type: public_vendor_behavior_article
- mapping_type: direct_entity
- entity_scope: windows_desktop_software
- relation_confidence: high
- evidence_summary: Microsoft 页面描述该 Windows PUA 家族可能捆绑非预期软件、修改浏览器设置与快捷方式，并安装浏览器扩展；本记录仅复述页面中的行为范围。
- matched_targets: app:installcore
- guard_reason: evidence is explanation/review/sorting/risk-hint only; execution gating is always blocked; Family-name overlap is a high-false-positive review hint and requires local identity checks.; indicator matching cannot authorize execution
- why_not_execution_authorization: Evidence 和 indicator match 只是复核线索，不能确认用户意图，也不能授权任何系统动作。

## ev-real-ms-slimware

- source_title: PUA:Win32/Slimware threat description - Microsoft Security Intelligence
- source_url: https://www.microsoft.com/en-us/wdsi/threats/malware-encyclopedia-description?Name=PUA%3AWin32%2FSlimware
- source_date: 2017-02-08
- source_type: public_vendor_behavior_article
- mapping_type: direct_entity
- entity_scope: windows_desktop_software
- relation_confidence: high
- evidence_summary: Microsoft 页面描述该 Windows PUA 家族展示可疑问题并要求付费修复、在应用外显示广告，并可能捆绑安装其他应用。
- matched_targets: app:slimware
- guard_reason: evidence is explanation/review/sorting/risk-hint only; execution gating is always blocked; Family-name overlap is a high-false-positive review hint and requires local identity checks.; indicator matching cannot authorize execution
- why_not_execution_authorization: Evidence 和 indicator match 只是复核线索，不能确认用户意图，也不能授权任何系统动作。

## ev-real-ms-mediaarena

- source_title: PUA:Win32/MediaArena threat description - Microsoft Security Intelligence
- source_url: https://www.microsoft.com/en-us/wdsi/threats/malware-encyclopedia-description?Name=PUA%3AWin32%2FMediaArena&threatId=359463
- source_date: 2023-03-20
- source_type: public_vendor_behavior_article
- mapping_type: direct_entity
- entity_scope: windows_desktop_software
- relation_confidence: high
- evidence_summary: Microsoft 页面描述该 Windows PUA 家族可能修改浏览器设置、重定向搜索并收集搜索查询；记录不声称同名普通文件必然属于该家族。
- matched_targets: app:mediaarena
- guard_reason: evidence is explanation/review/sorting/risk-hint only; execution gating is always blocked; Family-name overlap is a high-false-positive review hint and requires local identity checks.; indicator matching cannot authorize execution
- why_not_execution_authorization: Evidence 和 indicator match 只是复核线索，不能确认用户意图，也不能授权任何系统动作。

## ev-real-ms-fusioncore

- source_title: PUA:Win32/FusionCore threat description - Microsoft Security Intelligence
- source_url: https://www.microsoft.com/en-us/wdsi/threats/malware-encyclopedia-description?Name=PUA%3AWin32%2FFusionCore
- source_date: 2016-06-28
- source_type: public_vendor_behavior_article
- mapping_type: direct_entity
- entity_scope: windows_desktop_software
- relation_confidence: high
- evidence_summary: Microsoft 页面将该 Windows PUA 家族描述为 bundling software，并说明其可能安装其他潜在不需要的应用；本记录不推断具体安装实例。
- matched_targets: app:fusioncore
- guard_reason: evidence is explanation/review/sorting/risk-hint only; execution gating is always blocked; Family-name overlap is a high-false-positive review hint and requires local identity checks.; indicator matching cannot authorize execution
- why_not_execution_authorization: Evidence 和 indicator match 只是复核线索，不能确认用户意图，也不能授权任何系统动作。

## ev-real-ms-piriformbundler

- source_title: PUA:Win32/PiriformBundler threat description - Microsoft Security Intelligence
- source_url: https://www.microsoft.com/en-us/wdsi/threats/malware-encyclopedia-description?Name=PUA%3AWin32%2FPiriformBundler
- source_date: 2020-07-27
- source_type: public_vendor_behavior_article
- mapping_type: direct_entity
- entity_scope: windows_desktop_software
- relation_confidence: medium
- evidence_summary: Microsoft 页面仅针对被识别为该 PUA detection family 的特定安装器，描述其捆绑其他提供方软件的行为；不把 Piriform 产品整体标记为 PUA。
- matched_targets: app:piriform
- guard_reason: evidence is explanation/review/sorting/risk-hint only; execution gating is always blocked; relation confidence is not high; Family-name overlap is a high-false-positive review hint and requires local identity checks.; indicator matching cannot authorize execution
- why_not_execution_authorization: Evidence 和 indicator match 只是复核线索，不能确认用户意图，也不能授权任何系统动作。
