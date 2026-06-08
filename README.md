# Qwen3.5 中文 Plain-Text 压缩器

这是当前正式主线项目。

项目目标已经从早期“数学题 `think` 监督”切换为：

**基于 `Qwen/Qwen3.5-0.8B`、使用 `Swift + LoRA`、面向 Headroom 中文 plain-text 场景的压缩改写模型。**

## 从哪里开始读

请优先阅读：

- [docs/CURRENT_MAINLINE_QWEN35_COMPRESSOR.md](./docs/CURRENT_MAINLINE_QWEN35_COMPRESSOR.md)

然后再看：

- [docs/README.md](./docs/README.md)
- [docs/DEEPSEEK_V4_PRO_TEACHER_PROMPT.md](./docs/DEEPSEEK_V4_PRO_TEACHER_PROMPT.md)
- [docs/DATASET_V1_CONSTRUCTION_PLAN.md](./docs/DATASET_V1_CONSTRUCTION_PLAN.md)

## 当前共识

1. 当前模型不再主做 `<think>` 监督。
2. 当前模型输出的是 assistant 的可见压缩文本。
3. 当前模型只处理中文 plain-text 长段，不处理 raw code/log/json/diff。
4. 当前训练与推理必须显式使用 `language-model-only` 思路，避免把 vision encoder 带进文本压缩任务。

## 目录职责

- `docs/`
  - 当前压缩器项目的主线说明、调研文档和执行规范。

- `data/`
  - 新压缩器任务的数据源、切块结果、训练集和评测集。

- `scripts/`
  - 新压缩器专用的数据构造、校验、训练和评测脚本。

- `src/`
  - 新压缩器专用的可复用模块。

- `experiments/`
  - 新压缩器的训练记录、评测结果、速度测试和对比产物。

## 当前脚手架

- `scripts/build_dataset.py`
  - `source-pool`：从 `data/raw/` 下的 `.md` / `.txt` 文档切块，生成待标注 source pool。
  - `training`：把已标注的 `original_text -> compressed_text` JSONL 规范化并展开为 train/val/test 数据集。

- `scripts/validate_dataset.py`
  - 校验 source pool 或 training dataset 的字段、压缩率和锚点保留情况。

- `scripts/train_lora.py`
  - 独立于 legacy 项目的新训练入口。
  - 默认按 `language-model-only` 约束加载 `Qwen/Qwen3.5-0.8B`。

- `scripts/eval.py`
  - 独立于 legacy 项目的新评测入口。
  - 记录压缩率、锚点保留率和参考文本字符级 F1。

## 最小启动命令

```bash
python scripts/build_dataset.py training --input-file data/raw/labeled_pairs_demo_v1.jsonl --dataset-tag demo_rewrite_v1
python scripts/validate_dataset.py data/final/train_demo_rewrite_v1.jsonl --mode training --require-shorter
```

## 与旧项目的关系

- 旧数学 `think` 项目只作为历史资产和骨架参考保留。
- 如果要复用旧 Swift + LoRA 训练链路，请先复制或迁移需要的部分，再按当前压缩任务语义重写，不要直接沿用旧默认值。
- 旧项目入口见 [../legacy_math_think/README.md](../legacy_math_think/README.md)。
