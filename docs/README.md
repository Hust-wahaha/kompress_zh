# 文档索引

本文档用于告诉后续组员和 Agent：

- 当前哪份文档是**现行主线**
- 哪些文档是**历史调研参考**
- 接手执行时应按什么顺序阅读

## 1. 先读哪份

当前项目的**首要文档**是：

- [CURRENT_MAINLINE_QWEN35_COMPRESSOR.md](./CURRENT_MAINLINE_QWEN35_COMPRESSOR.md)

这份文档描述了当前唯一有效的执行主线，包括：

- 为什么项目方向已经改变
- 为什么当前仍复用 `Qwen3.5-0.8B + Swift + LoRA`
- 为什么训练目标从 `think` 监督转为“非 think 压缩改写”
- `--language-model-only` 为什么是硬约束
- 当前数据、训练、评测、Headroom 接入边界分别是什么

如果只读一份文档，就读这份。

## 2. 推荐阅读顺序

### 第一层：执行必读

1. [CURRENT_MAINLINE_QWEN35_COMPRESSOR.md](./CURRENT_MAINLINE_QWEN35_COMPRESSOR.md)

### 第二层：配套背景

2. [CHINESE_TEXT_IN_AGENT_WORKFLOW.md](./CHINESE_TEXT_IN_AGENT_WORKFLOW.md)
3. [HEADROOM_ZH_STRATEGY.md](./HEADROOM_ZH_STRATEGY.md)
4. [HEADROOM_KOMPRESS_ANALYSIS.md](./HEADROOM_KOMPRESS_ANALYSIS.md)

### 第三层：数据与风险参考

5. [CHINESE_KOMPRESS_DATA_CONSTRUCTION_PLAN.md](./CHINESE_KOMPRESS_DATA_CONSTRUCTION_PLAN.md)
6. [CHINESE_KOMPRESS_RISK_MAP.md](./CHINESE_KOMPRESS_RISK_MAP.md)
7. [AGENT_DOC_SOURCE_POOL_SPEC.md](./AGENT_DOC_SOURCE_POOL_SPEC.md)

## 3. 哪些文档是历史调研参考，不是现行方案

以下文档仍有参考价值，但**不要直接把它们当成当前执行规范**：

- [HEADROOM_ZH_KOMPRESS_TECH_PLAN.md](./HEADROOM_ZH_KOMPRESS_TECH_PLAN.md)
  - 这是旧版“抽取式 encoder 压缩”路线，和当前生成式压缩改写主线不一致。

- [CHINESE_KOMPRESS_MARKDOWN_DATASET_SPEC.md](./CHINESE_KOMPRESS_MARKDOWN_DATASET_SPEC.md)
- [CHINESE_KOMPRESS_MARKDOWN_LABELING_PROMPT.md](./CHINESE_KOMPRESS_MARKDOWN_LABELING_PROMPT.md)
- [CHINESE_KOMPRESS_MARKDOWN_PRIORITY.md](./CHINESE_KOMPRESS_MARKDOWN_PRIORITY.md)
  - 这些主要围绕 earlier markdown/doc 数据收集与旧标签思路，可作素材参考，但不是现行训练任务定义。

- [CHINESE_KOMPRESS_ROUTE_COMPARISON.md](./CHINESE_KOMPRESS_ROUTE_COMPARISON.md)
  - 这是路线比较文档，不是最终执行稿。

- [WHY_NO_CHINESE_KOMPRESS_YET.md](./WHY_NO_CHINESE_KOMPRESS_YET.md)
- [CHINESE_KOMPRESS_LANDSCAPE_SURVEY.md](./CHINESE_KOMPRESS_LANDSCAPE_SURVEY.md)
- [CODING_AGENT_DATASET_SURVEY.md](./CODING_AGENT_DATASET_SURVEY.md)
  - 这些是背景调研材料。

## 4. 当前最重要的执行共识

后续推进时请默认遵守以下共识：

1. 当前任务不是数学 `think` 监督，而是中文长文本压缩改写。
2. 当前输出不是 `<think>`，而是 assistant 的可见压缩文本。
3. 当前主基座仍是 `Qwen/Qwen3.5-0.8B`。
4. 当前训练方式仍是 `Swift + LoRA`。
5. 当前必须使用 `language-model-only`，避免把 vision encoder 带进来。
6. 当前模型只处理 Headroom 路由出来的中文 plain-text 长段。

## 5. 后续建议

如果要继续执行项目，建议新的 Agent 或组员优先做下面几件事：

1. 按当前主线重写数据 schema。
2. 设计新的 teacher prompt，用于生成压缩改写目标。
3. 改造现有 Swift 训练脚本，使其不再依赖旧 `think` 数据格式。
4. 先做小批量样本和最小训练，再讨论大规模扩展。
