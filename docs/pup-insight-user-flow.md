# PUP 洞察用户入口

一条命令检查显式报告中的本地 seed 线索：

```console
python -m pc_cleanguard.cli pup inspect --input report.json --seed examples/reputation/seed_records.zh-CN.json --output pup_inspection.md
```

也可以分开运行 `reputation match` 与 `reputation insight`。输出解释命中的行为类别、误报风险、不确定性和人工复核建议。

PUP insight 不是删除授权、不是卸载授权、不是禁用授权。Reputation KB 只能解释、排序和提示风险；没有命中也不构成安全证明。
