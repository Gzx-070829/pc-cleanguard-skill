# Persistence Chain Graph

Node/edge 契约见 `schemas/persistence_chain_*.schema.json`。`evidence_match` 和 `behavior_corroborates` 只增强人工复核；`weak_name_overlap`、`related_to_publisher` 不得提升为 direct entity。缺字段进入 `missing_metadata`，不触发扫描。

输出支持 JSON、Markdown 与 Mermaid，固定 `execution_gating_eligible_count=0`。
