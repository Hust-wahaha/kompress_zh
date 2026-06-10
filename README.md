# kompress_zh

> A Chinese plain-text compression model line for agent and documentation workflows.

`kompress_zh` 是一个面向中文 Agent / 文档工作流的 **plain-text 压缩改写项目**。  
它不是通用摘要器，也不是代码压缩器；它的目标是把中文长段自然语言压得更短，同时尽量保真、保留关键锚点，并保持对大模型友好的可读性。

当前第一版 baseline 已完成：

- base model: `Qwen/Qwen3.5-0.8B`
- method: `Swift + LoRA`
- mode: `language-model-only`
- dataset: `standardset_v6_1234`
- checkpoint: `reference_v1 / checkpoint-61`

它的目标风格不是“普通摘要腔”，而是：

- **轻结构化**
- **轻文言压缩感**
- **现代中文可读**
- **对 Agent / 大模型继续可解析**

## Why This Project

在真实 Agent 场景里，很多高成本上下文并不是代码，而是：

- 任务说明
- 约束与交付要求
- 进度同步
- 项目文档段落
- 结果解释
- 含少量路径、命令、文件名、数字的自然语言块

这些内容通常：

- 比代码更长、更口语
- 比摘要任务更强调保真
- 比传统“删句子”更需要轻改写与结构重组

`kompress_zh` 的定位就是填这一层空白：  
做一个可嵌入 `headroom_zh` 或类似上下文压缩系统中的中文自然语言压缩器。

## What Makes It Distinct

这个项目的独特点，不是“我们也训练了一个压缩模型”，而是我们从一开始就按 **可嵌入 Agent 上下文压缩链路** 的标准来定义任务。

### 1. Style Is Deliberately Constrained

我们不是让 teacher 或学生模型随意“写短一点”，而是明确约束输出风格为：

- 轻结构化
- 轻文言压缩感
- 现代中文主体
- 不走纯古文
- 不走泛摘要腔
- 不走过度润色

这意味着输出既要更短，又要保留一种高信息密度、适合继续喂给强模型阅读的表达风格。

### 2. Anchors Are Not an Afterthought

很多压缩模型默认把路径、命令、文件名、URL、数字条件这类内容当成“可以顺手压掉的噪声”。  
我们反过来把它们当成真实部署里最不能乱动的部分之一。

当前 `standardset_v6_1234` 的数据分布是：

- total samples: `1234`
- anchor rows: `1223 / 1234`，约 `99.1%`
- avg anchor count: `3.96` per sample

也就是说，这不是一个“干净纯文字摘要集”，而是主动混入大量真实工程锚点的压缩数据集。

### 3. Evaluation Separates Strict vs Soft Anchors

我们没有把所有锚点混成一个粗糙分数。

当前口径明确区分：

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

这件事非常重要，因为真实可用性往往不是“少了一个编号也算严重事故”，而是“路径、命令、文件名不能丢”。

### 4. Metrics Are Treated as Routing Tools, Not Truth

我们专门避免一个常见错误：  
把自动脚本分数直接当成模型质量真值。

这里的执行原则一直是：

- 脚本负责筛查、排序、抽样
- 低分 case 必须回到原文 / 参考压缩 / 模型输出做人工复核
- `soft anchor` 波动不能被误判成模型能力显著变差

这使得我们的评测更接近“面向部署的质量判断”，而不是只做一个好看的单指标。

### 5. The Task Is Defined for Headroom-Style Use

很多人做压缩模型时，任务边界会越来越散，最后变成一个模糊的“中文摘要器”。  
我们从一开始就把边界卡住：

- 主处理对象是中文 plain-text 长段
- 允许混入少量工程锚点
- 不直接处理 raw code / raw logs / raw diffs / raw configs

这正是后面嵌入 `headroom_zh` 时可用性的来源之一：  
它不是一个泛化模糊的模型，而是一个任务边界非常清晰的组件。

## What It Is

`kompress_zh` 当前做的是：

- 中文 long-form plain-text -> 更短的中文 plain-text
- 保真优先
- 允许轻结构化
- 允许轻文言压缩感
- 尽量保留 strict anchors

这里的 strict anchors 主要指：

- 文件名
- 路径
- URL
- 命令与关键参数
- repo / model id
- 关键数字条件

它 **不** 直接处理：

- raw code blocks
- raw JSON / YAML / XML
- logs / stack traces
- diffs / patches
- search result dumps

这些内容更适合由外部路由层或结构化压缩链路处理。

## Current Status

当前仓库不是概念草案，而是已经跑通了完整闭环的工作版项目：

- 原料扩池 -> teacher 标注 -> 分层复核 -> 人工 audit -> 正式 merge
- 本地数据生产 -> AutoDL 训练 -> 测试集评测 -> case review
- baseline 文档、训练记录、评测结果和主线边界均已沉淀

第一版 baseline 的核心结果：

| Item | Value |
| --- | --- |
| Dataset | `standardset_v6_1234` |
| Train / Val / Test | `973 / 129 / 132` |
| Final checkpoint | `checkpoint-61` |
| Train loss | `0.5575` |
| Eval loss | `0.5315` |
| Eval token acc | `0.8566` |
| Avg prediction ratio | `0.7425` |
| Avg char F1 | `0.8039` |
| Avg strict anchor retention | `0.9216` |
| Avg soft anchor retention | `0.8075` |

当前结论很明确：

- 这版模型已经是一个**成立的 MVP / baseline**
- 它在保真和 strict anchor 保留上已经可用
- 它仍然偏保守，不是最终效果版
- 当前阶段更适合把它作为正式 baseline 固化，而不是继续围绕这版做高频小修补

如果只看“平均压缩率”，你会漏掉这个项目真正重要的点。  
当前这版 baseline 更值得看的其实是：

- 风格已经稳定落在“轻结构化 + 轻文言压缩感”这一带
- `strict anchor` 保留已经到 `0.9216`
- 数据和评测都明确围绕真实 Agent 文本而不是普通摘要文本设计
- 这使它更像一个可嵌入系统组件，而不是一个随便训出来的压缩 demo

## Project Principles

这个项目目前遵守几条很明确的工程原则：

1. 不把脚本指标当真值，脚本只做筛查、排序、抽样。
2. 真实结论必须结合 case review 和人工判断。
3. 训练与数据问题分层处理，本地负责数据，AutoDL 负责训练与评测。
4. 当前模型只做 plain-text，自觉避免把任务边界扩成“万能压缩器”。
5. 先做出可靠 baseline，再讨论更大的模型故事。

## Why This Matters for Headroom

`headroom_zh` 或类似系统真正需要的，不是一个“能把话写短”的模型，而是一个：

- 能压缩中文长段
- 仍保留关键执行锚点
- 输出继续适合强模型往下读
- 不把工程上下文压坏的组件

`kompress_zh` 当前的这些设计选择，正是在为这个目标服务：

- 轻结构化让信息更快被后续模型解析
- 轻文言压缩感提高单位长度信息密度
- anchor-heavy 数据分布让模型习惯在压缩时保护关键字面内容
- strict / soft 分层评测让我们真正知道“有没有把关键东西压坏”

## Repository Map

```text
data/
  raw/         source docs, labeled pairs, review decisions
  interim/     review queues, source pools, audit packs
  final/       train/val/test exports for official runs

scripts/
  build_dataset.py
  validate_dataset.py
  label_with_deepseek.py
  train_lora.py
  eval.py

src/
  zh_plaintext_compressor/common/

experiments/
  remote_sync/
  logs/

docs/
  mainline, status, training notes, release-facing docs
```

## Read This First

如果你是第一次进入这个仓库，建议按这个顺序读：

1. [docs/CURRENT_MAINLINE_QWEN35_COMPRESSOR.md](./docs/CURRENT_MAINLINE_QWEN35_COMPRESSOR.md)
2. [docs/KOMPRESS_ZH_BASELINE_V1_DECISION_2026-06-10.md](./docs/KOMPRESS_ZH_BASELINE_V1_DECISION_2026-06-10.md)
3. [docs/TRAINING_EVAL_STANDARDSET_V6_REFERENCE_V1_2026-06-10.md](./docs/TRAINING_EVAL_STANDARDSET_V6_REFERENCE_V1_2026-06-10.md)
4. [docs/HF_MODEL_CARD_DRAFT_BASELINE_V1.md](./docs/HF_MODEL_CARD_DRAFT_BASELINE_V1.md)
5. [docs/README.md](./docs/README.md)

## Quick Start

### 1. Build a dataset export

```bash
python scripts/build_dataset.py training --input-file data/raw/labeled_pairs_demo_v1.jsonl --dataset-tag demo_rewrite_v1
```

### 2. Validate the export

```bash
python scripts/validate_dataset.py data/final/train_demo_rewrite_v1.jsonl --mode training --require-shorter
```

### 3. Train with LoRA

```bash
python scripts/train_lora.py --dataset-tag standardset_v6_1234 --run-tag reference_v1 --language-model-only
```

### 4. Run offline eval

```bash
python scripts/eval.py --dataset-tag standardset_v6_1234 --checkpoint <checkpoint_dir> --run-tag test_eval --language-model-only
```

## Data Philosophy

当前数据不是“随便抓一些中文段落压缩一下”，而是有明确风格边界的：

- 真实 Agent / 文档工作流来源优先
- 中文自然语言长段落优先
- 允许少量工程锚点混入
- 主动覆盖 anchor-heavy 场景，而不是回避它
- 不追求华丽摘要感，追求高信息密度与模型可解析性
- 人工复核主要守 semantic drift、关键锚点丢失、过度文言化、假精炼

当前标准集规模为 `1234`，它更像：

- 一个高标准 baseline set
- 一个可继续扩到 `3k ~ 4k` 的样板
- 一个后续协作扩数时可复用的风格参考

## Limitations

当前 baseline 也有明确限制：

- 压缩激进度仍偏保守
- 对本可大幅压缩的样本，经常只做到“稳妥改写”
- 尚未完成大规模真实线上接入验证
- 尚未发布正式 Hugging Face 模型卡与推理样例仓

但这不影响它已经具备一个很强的阶段性价值：

- 它证明了“中文 Agent plain-text 压缩器”这条路线是可做的
- 它证明了轻结构化 + 轻文言 + anchor-aware 的任务定义可以训成稳定 baseline
- 它已经足够支撑后续 `headroom_zh` 的第一轮真实集成验证

因此当前更准确的说法是：

> `kompress_zh` 已经有一版可信 baseline，但仍处在“从工程闭环走向成熟开源项目”的过渡阶段。

## Roadmap

短期主线：

- 固化 baseline 文档与公开叙事
- 准备 Hugging Face 首版发布材料
- 为 `headroom_zh` 接入准备最小验证链路

中期主线：

- 以当前 `1k+` 标准集为样板，扩到更完整的数据规模
- 训练第二版更强模型
- 做更系统的 case benchmark 和接入评测

## Acknowledgement of Scope

这个仓库和早期数学 `think` 监督路线不是同一个项目方向。  
旧链路只作为工程资产和训练骨架参考保留，当前正式主线已经完全切到中文 plain-text 压缩改写。

## Documentation

完整文档索引见：

- [docs/README.md](./docs/README.md)

其中最关键的几份：

- [docs/CURRENT_MAINLINE_QWEN35_COMPRESSOR.md](./docs/CURRENT_MAINLINE_QWEN35_COMPRESSOR.md)
- [docs/PROJECT_STATUS_2026-06-09.md](./docs/PROJECT_STATUS_2026-06-09.md)
- [docs/TRAINING_EVAL_STANDARDSET_V6_REFERENCE_V1_2026-06-10.md](./docs/TRAINING_EVAL_STANDARDSET_V6_REFERENCE_V1_2026-06-10.md)
- [docs/KOMPRESS_ZH_BASELINE_V1_DECISION_2026-06-10.md](./docs/KOMPRESS_ZH_BASELINE_V1_DECISION_2026-06-10.md)

## Status Line

`kompress_zh` 当前已经完成第一版 baseline 收口。  
下一阶段重点不是继续死抠这版，而是把它做成一个看起来成熟、叙事完整、可被复用和推广的社区项目起点。
