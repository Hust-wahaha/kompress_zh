# 第一阶段执行清单

## 目标

在不改变当前主实验结论的前提下，把仓库整理到“目录职责清楚、命名规则落地、脚本入口统一、结果可追溯”的最低可协作状态。

## 本阶段不做的事

- 不重写训练框架
- 不改动已经完成的实验结论
- 不引入新的模型或新的数据来源
- 不做大规模算法重构

## 任务 1：目录职责落地

- 建立并固定以下目录：
  - `data/raw`
  - `data/interim`
  - `data/final`
  - `src`
  - `scripts`
  - `runs`
  - `docs`
- 在 `docs/README.md` 或主 README 中明确每个目录的责任边界

## 任务 2：命名规则落地

- 固定 `dataset_tag` 格式：
  - `{source}_{task}_{size}_{version}`
- 固定 run 目录格式：
  - 训练：`{timestamp}_train_{dataset_tag}_{model_tag}_{exp_tag}`
  - 评测：`{timestamp}_eval_{dataset_tag}_{model_tag}_{eval_tag}`
  - 抽样：`{timestamp}_inspect_{dataset_tag}_{model_tag}_{inspect_tag}`
- 统一 think 字段命名：
  - 所有显式思维监督字段统一为 `xxx_think`
- 保留旧字段兼容层，但文档中标注为“历史兼容”

## 任务 3：Schema 固化

- 固定主仓库核心必填字段：
  - `id`
  - `source`
  - `family`
  - `split`
  - `modern_question`
  - `classical_question`
  - `answer`
- 固定可选任务字段：
  - `structured_think`
  - `modern_think`
  - `classical_think`
- 固定训练展开字段说明：
  - `base_id`
  - `view`
  - `dataset_variant`
  - `think_style`
  - `messages`

## 任务 4：脚本入口统一

- 所有主要入口统一参数风格：
  - `--dataset-tag`
  - `--run-tag`
  - `--output-dir` 或默认输出规则
- 当前涉及脚本：
  - `generate_dataset.py`
  - `train_lora_local.py`
  - `validate_dataset.py`
  - `eval_compare_full.py`
  - `inspect_think_samples.py`

## 任务 5：追溯信息补齐

- 每次训练 run 必须保存：
  - `run_config.json`
  - `last_checkpoint.txt`
- 每次评测 run 必须保存：
  - `compare_summary.json`
  - predictions 文件
- 每次抽样 run 必须保存：
  - `summary.json`
  - `think_samples.json`

## 任务 6：协作文档补齐

- 补齐以下文档并保证全中文：
  - `PROJECT_PROGRESS.md`
  - `TEAM_SYNC_LOG.md`
  - `DATA_SCHEMA.md`
  - `REPOSITORY_RULES.md`
  - `PHASE1_EXECUTION_CHECKLIST.md`

## 本阶段完成标准

满足下面条件即可视为第一阶段完成：

1. 新同学能看文档知道每个目录放什么
2. 新同学能按命名规则新增数据集和实验
3. 新同学能看 schema 知道哪些字段必须填
4. 新同学能从 run 目录反推出数据、模型、实验意图
5. 现有 `s800` / `s800_think` 结果不被破坏
