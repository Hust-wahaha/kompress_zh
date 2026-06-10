# HF Model Card Draft: kompress_zh baseline v1

> First public baseline for Chinese agent-grade plain-text compression.

`kompress_zh` 是一个面向中文 Agent / 文档工作流的 plain-text 压缩改写模型。  
它的目标不是生成“更像摘要”的文本，而是将中文长段压缩为更短、更密、更适合继续供强模型处理的工作文本，同时尽量保持语义、锚点和执行可用性。

如果只用一句话概括这版 baseline：

> 这是一个面向 `headroom_zh` 一类系统的中文 plain-text compressor baseline，核心特征是轻结构化、轻文言压缩感、anchor-aware 数据设计，以及 case-level 的严格保真审核。

## Release Snapshot

- base model: `Qwen/Qwen3.5-0.8B`
- training method: `Swift + LoRA`
- mode: `language-model-only`
- dataset: `standardset_v6_1234`
- checkpoint: `reference_v1 / checkpoint-61`

核心数字：

- `25.7%` average reduction on the evaluated test set
- `92.2%` strict anchor retention
- `99.1%` anchor-bearing data in the baseline dataset
- evaluated on the `2026-06-10` baseline-v1 test split (`132` samples)

这一版更适合被描述为：

- first public baseline
- deployment-oriented compression component
- reproducible workflow checkpoint

而不是最终效果版。

## Evaluation Context

为避免把离线数字说得过满，这里明确当前口径：

- evaluation date: `2026-06-10`
- test split size: `132`
- train / val / test: `973 / 129 / 132`
- inference mode: `language-model-only`
- base family: `Qwen3.5-0.8B`

因此，本页数字应理解为：

- 一个已成立的首版 baseline 快照
- 面向 anchor-heavy 中文 Agent 文本的离线结果
- 后续公开版本继续迭代时的参照点

## What Makes This Project Distinct

很多中文压缩项目默认沿着“摘要化”方向演化，`kompress_zh` 则刻意把任务定义收紧在更偏部署的一侧。

它当前最有辨识度的点主要有四个：

1. 输出风格不是普通摘要，而是 `light structured + light wenyan`
   - 目标是提高单位长度信息密度，同时保持强模型可继续解析。

2. 数据分布不是纯净自然语言摘要集，而是主动引入大量锚点密集样本
   - 路径、文件名、命令、URL、参数、数字条件不是噪声，而是要尽量保护的执行锚点。

3. 评测不把所有 anchor 混成一个总分
   - `strict anchors` 与 `soft anchors` 被分开追踪，以避免误判真实部署风险。

4. 自动脚本不是最终裁判
   - 低分样本需要回到原文、参考压缩文和模型输出做人工 case review。

## What This Model Is For

`kompress_zh` 适合处理：

- 中文任务说明
- 中文需求与约束
- 中文项目文档长段
- 中文进度同步
- 中文结果解释
- 混有路径、命令、文件名、URL、数字条件的自然语言块

它不适合直接处理：

- raw code
- raw JSON / YAML / XML
- logs / stack traces
- diff / patch
- 自由摘要
- 主观总结
- 创作式改写

最合理的系统位置是：

1. 上游路由识别“中文 plain-text 长段”
2. 交给 `kompress_zh`
3. 其余结构化内容继续走专门压缩链路

## Inputs and Outputs

输入侧更接近：

- 中文长段说明文本
- 中文规约、同步、交付、执行指南
- 混有路径、命令、URL、文件名、数字条件的自然语言块

输出侧目标是：

- 更短
- 更密
- 仍保留核心语义
- 仍尽量保留 strict anchors
- 仍适合强模型继续消费

也就是说，它输出的不是“摘要结果”，而是**压缩后的工作文本**。

## Core Design Philosophy

### 1. Not a Generic Summarizer

本项目从一开始就不是中文摘要器路线。

核心目标是：

- 更短
- 仍保真
- 仍保留关键锚点
- 仍适合后续模型继续读

也就是说，压缩后的输出要继续承担工作文本角色，而不是只提供一个“人类可读总结”。

### 2. Style-Constrained Compression

目标风格不是普通摘要腔，而是：

- 轻结构化
- 轻文言压缩感
- 现代中文主体
- 高信息密度
- 大模型继续可解析

我们刻意避免：

- 纯古文
- 过度润色
- 泛摘要口吻
- 为了“高级感”牺牲执行可读性

### 3. Anchor-Aware Data Construction

很多压缩模型会天然把路径、命令、URL、文件名、数字条件视为冗余噪声。  
`kompress_zh` 反过来把它们视为部署场景里最需要保护的部分之一。

当前标准集：

- total samples: `1234`
- split: `973 / 129 / 132`
- anchor rows: `1223 / 1234`
- avg anchor count: `3.96`

这意味着数据分布不是“纯净自然语言摘要集”，而是主动覆盖 anchor-heavy 的真实工作文本。

### 4. Deployment-Oriented Evaluation

本项目没有把所有锚点混成一个粗糙总分，而是明确区分：

- `strict anchors`
  - URL
  - 路径
  - 文件名
  - 命令 / 参数
  - repo / model id
- `soft anchors`
  - 编号
  - 字段名
  - identifier
  - 轻格式 token

这是一个很重要的设计，因为真实部署里最严重的错误通常不是“编号轻微变化”，而是“路径、命令、文件名被压坏”。

### 5. Designed for Integration, Not Just Offline Scores

`kompress_zh` 的目标一直不是单纯做一个离线压缩 benchmark。

它更接近一个待嵌入模块：

- 上游负责识别中文 plain-text 长段
- `kompress_zh` 负责高保真压缩
- 下游强模型继续消费压缩后的上下文

因此，这个 baseline 更应该被理解为系统组件起点，而不是一次性模型展示。

## Behavior Profile

当前已知行为特征：

- strict anchor 保留较强
- 中文输出自然度稳定
- 风格能稳定落在“轻结构化 + 轻文言压缩感”
- 整体压缩倾向偏保守
- 对本可明显再压的样本，常更像“稳妥改写”而非“强压缩”

更准确地说：

> 这是一个已经可用的 baseline compressor，但还不是压缩激进度最优版。

## Evaluation Summary

测试集结果：

| Metric | Value |
| --- | --- |
| Avg prediction ratio | `0.7425` |
| Avg reduction | `25.7%` |
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

## Why These Metrics Matter

如果只看压缩率，会误解这个模型。

`kompress_zh` 真正更有意义的点是：

- 在 anchor-heavy 数据上仍能稳定压缩
- strict anchors 保留已达到较强水平
- 数据、风格、评测都围绕真实 Agent 工作文本设计
- 输出继续适合进入 `headroom_zh` 一类系统的下游推理链路

## Failure Modes We Track Explicitly

我们关心的不是抽象的“效果不好”，而是部署里真的会出问题的 failure modes：

1. 该压得更狠时仍偏保守
   - 常见于 link-heavy 文本和说明性段落。

2. soft anchors 波动引发误判
   - 若不区分 strict / soft，很容易把次要变化误判成严重退化。

3. 少数样本压掉“下一步 / 风险 / 交付”类提示
   - 这类问题不能只靠均值发现。

4. 极高密度 checklist / 规范文本本来就难压
   - 若误判成模型太差，会直接把训练方向带偏。

## Safety and Reliability Notes

本项目特别强调：

- 不把自动脚本评分直接当成真值
- 低分样本必须结合原文、参考压缩文、模型输出做人工复核
- `soft anchor` 波动不能直接推导为模型能力显著下降

这也是它与很多“先训一个压缩模型看看”路线的主要差别：

- 更重视 strict anchor 保真
- 更重视 case-level audit
- 更重视系统集成可用性

## Example Prompt Pattern

推荐输入模式：

```text
请将下面这段中文文本压缩改写为更短版本。要求：保留核心语义；尽量保留路径、命令、文件名、数字等关键锚点；允许轻结构化；允许轻文言压缩感；不要编造新信息。

<原文>
...
```

## Release Positioning

当前版本更适合作为：

- `kompress_zh` 首版公开基线
- `headroom_zh` 的上游中文 plain-text compressor 候选
- 后续更大规模数据扩展与第二版训练的起点

它当前还不适合被描述为：

- final production model
- strongest compression variant
- universal Chinese compressor

## References

- [README.md](../README.md)
- [CURRENT_MAINLINE_QWEN35_COMPRESSOR.md](./CURRENT_MAINLINE_QWEN35_COMPRESSOR.md)
- [TRAINING_EVAL_STANDARDSET_V6_REFERENCE_V1_2026-06-10.md](./TRAINING_EVAL_STANDARDSET_V6_REFERENCE_V1_2026-06-10.md)
- [KOMPRESS_ZH_BASELINE_V1_DECISION_2026-06-10.md](./KOMPRESS_ZH_BASELINE_V1_DECISION_2026-06-10.md)
