# v0.3.1 Release Checklist

- [x] 包版本与 CLI 版本统一为 `0.3.1`。
- [x] PR24 默认 `.pcg-quarantine` 与 Evidence Guard 保持生效。
- [x] PR25 Microsoft PUA 公开来源离线 intake/review/build 可复现。
- [x] PR26 PUP Intelligence Review Pack 本地离线生成。
- [x] PR27 Adversarial Evidence Guard、中文 evidence 与 Behavior Indicators 保持人工复核。
- [x] PR28 六类中文公开来源矩阵和候选池通过本地契约校验。
- [x] 网友名单、社区反馈、历史榜、移动 APP/SDK 类比均不能进入 Windows 执行门控。
- [x] 安全厂商文章不包含专有签名、规则、检测逻辑或样本库。
- [x] checked-in evidence 与 candidate 均保持 `execution_authorized=false`。
- [x] PUP/来源层 `execution_gating_eligible_count=0`。
- [x] 不联网 runtime、不上传、不写生产爬虫、不读取 API key。
- [x] 不新增永久删除、卸载、注册表、启动项/服务/任务禁用能力。
- [ ] 发布者在干净 main 上运行 compileall、全量 unittest、diff check 和三组安全搜索。
- [ ] 发布者确认 v0.3.1 tag 不存在后才创建 annotated tag 和 GitHub Release。

本清单不包含任何删除、卸载、禁用或注册表修改操作；它只核对发布资产与安全边界。
