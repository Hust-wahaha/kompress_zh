# HF Model Card Draft: kompress_zh baseline v1

本文档是面向 Hugging Face 发布的第一版 model card 草稿。

当前版本仍是仓库内草稿，但写法已按对外发布口径组织。

## Model Summary

`kompress_zh` 是一个面向中文 Agent / 文档工作流的 plain-text 压缩改写模型。  
它将中文长段自然语言压缩为更短的中文文本，同时尽量保持语义保真、锚点保留与大模型可读性。

当前 baseline 配置：

- base model: `Qwen/Qwen3.5-0.8B`
- training method: `Swift + LoRA`
- mode: `language-model-only`
- dataset: `standardset_v6_1234`
- checkpoint: `reference_v1 / checkpoint-61`

## Intended Use

适合的场景：

- 中文任务说明压缩
- 中文需求与约束压缩
- 中文项目文档段落压缩
- 中文进度同步与结果说明压缩
- 混有少量路径、命令、数字、文件名的自然语言块压缩

不适合的场景：

- 代码压缩
- JSON / YAML / XML 压缩
- 日志与报错堆栈压缩
- diff / patch 压缩
- 自由摘要、主观总结、创作式改写

## Model Behavior

当前风格目标：

- 保真优先
- 轻结构化
- 轻文言压缩感
- 严格避免编造新事实
- 尽量保留 strict anchors

当前已知行为特征：

- 在 strict anchor 保留上表现较强
- 中文输出自然度较稳定
- 整体压缩倾向偏保守
- 对可明显压缩样本，常更像“稳妥改写”而非“强压缩”

## Training Data

当前第一版标准集：

- dataset tag: `standardset_v6_1234`
- total samples: `1234`
- split: `973 / 129 / 132`

数据来源原则：

- 中文 Agent / 文档工作流文本优先
- 真实项目文档、任务说明、进度同步、结果解释优先
- 保留少量真实工程锚点
- 不把 raw code / raw logs / raw configs 作为主任务数据

数据构建流程：

1. 扩原料池
2. source filtering
3. teacher labeling with `DeepSeek V4 Pro`
4. review queue routing
5. final audit sampling
6. manual review
7. official merge
8. train/val/test export

## Evaluation

测试集结果：

| Metric | Value |
| --- | --- |
| Avg prediction ratio | `0.7425` |
| Avg char F1 | `0.8039` |
| Avg anchor retention | `0.8157` |
| Avg strict anchor retention | `0.9216` |
| Avg soft anchor retention | `0.8075` |

训练结果：

| Metric | Value |
| --- | --- |
| Final checkpoint | `checkpoint-61` |
| Train loss | `0.5575` |
| Eval loss | `0.5315` |
| Eval token acc | `0.8566` |

## Limitations

当前限制包括：

- 压缩激进度偏保守
- 尚未覆盖更广泛线上真实流量分布
- 暂未提供正式 benchmark leaderboard 风格的多模型对比
- 暂未提供公开 inference demo

因此该版本更适合被描述为：

- first public baseline
- reproducible workflow checkpoint
- high-quality seed model line

而不是最终效果版。

## Safety and Reliability Notes

当前项目特别强调：

- 不把自动脚本评分直接当成质量真值
- 低分样本必须结合原文、参考压缩文、模型输出做人工复核
- soft-anchor 波动不能直接推导为模型能力显著下降

## Example Prompt Pattern

推荐输入模式：

```text
请将下面这段中文文本压缩改写为更短版本。要求：保留核心语义；尽量保留路径、命令、文件名、数字等关键锚点；允许轻结构化；不要编造新信息。

<原文>
...
```

## Release Positioning

当前版本更适合作为：

- `kompress_zh` 首版公开基线
- `headroom_zh` 的上游中文 plain-text compressor 候选
- 后续更大规模数据扩展与第二版训练的起点

## References

- [CURRENT_MAINLINE_QWEN35_COMPRESSOR.md](./CURRENT_MAINLINE_QWEN35_COMPRESSOR.md)
- [TRAINING_EVAL_STANDARDSET_V6_REFERENCE_V1_2026-06-10.md](./TRAINING_EVAL_STANDARDSET_V6_REFERENCE_V1_2026-06-10.md)
- [KOMPRESS_ZH_BASELINE_V1_DECISION_2026-06-10.md](./KOMPRESS_ZH_BASELINE_V1_DECISION_2026-06-10.md)
