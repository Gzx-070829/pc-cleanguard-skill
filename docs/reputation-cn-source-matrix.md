# 中文公开 PUP 来源矩阵

`data/reputation/cn_source_matrix.zh-CN.json` 把公开来源分为六类：历史公开材料、安全厂商公开文章、官方/监管通报、可信媒体、社区多源反馈、网友屏蔽/论坛名单。它是来源准入表，不是黑名单。

每条来源记录必须有 URL、标题、日期或 `unknown`、平台范围、许可说明、允许用途和四项固定禁止用途。`unknown` 日期不能配高可靠性；社区与网友列表必须要求第二来源；历史材料只能解释历史背景；移动 APP/SDK 通报不能映射 Windows direct entity。

```powershell
python -m pc_cleanguard.cli reputation cn-source validate --input data/reputation/cn_source_matrix.zh-CN.json
python -m pc_cleanguard.cli reputation cn-source stats --input data/reputation/cn_source_matrix.zh-CN.json
```

运行时只读取显式本地 JSON，不访问 URL。Matrix、Evidence 和 Behavior Indicator 都不等于删除授权，所有 PUP 线索需要人工复核。
