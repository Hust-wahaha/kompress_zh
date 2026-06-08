# 仓库规则与使用规范

本文档不是计划，也不是草案，而是当前仓库已经采用的工作规范。后续组员直接按本文档执行即可，不需要再对照“计划完成了多少”。

## 一、目录职责

### `data/`

- `data/raw`
  - 外部原始来源数据
  - 公开数据集原文件
  - 未清洗、未统一字段的原始材料
- `data/interim`
  - 对齐后的中间数据
  - 已做风格转换、字段补全，但还不是最终训练版本的数据
- `data/final`
  - 可直接进入训练或评测的数据版本
  - 默认要求 schema 稳定

### `src/`

- 放可复用公共逻辑
- 当前已落地：
  - `src/common/paths.py`
  - `src/common/naming.py`
  - `src/common/schema.py`
- 不把一次性实验入口写在这里

### `scripts/`

- 只放命令行入口脚本
- 当前主入口包括：
  - `generate_dataset.py`
  - `validate_dataset.py`
  - `train_lora_local.py`
  - `eval_compare_full.py`
  - `inspect_think_samples.py`

### `runs/`

- 放训练、评测、抽样、案例分析的运行产物
- 所有实验输出默认写入这里
- 不把 `runs/` 内文件手工移动到其他地方，以免破坏追溯关系

### `docs/`

- 放正式文档
- 默认入口：
  - `README.md`
  - `PROJECT_PROGRESS.md`
  - `DATA_SCHEMA.md`
  - `TEAM_SYNC_LOG.md`

## 二、命名规则

### 数据集标签 `dataset_tag`

统一格式：

```text
{source}_{task}_{size}_{version}
```

示例：

- `synth_think_800_v1`
- `math23k_structuredthink_2000_v1`
- `math23k_think_2000_v2`

字段含义：

- `source`
  - 数据来源或来源组合
- `task`
  - 监督任务类型，例如 `think`、`structuredthink`、`shortthink`
- `size`
  - 最终训练样本规模，写绝对数值
- `version`
  - 同方向数据迭代版本，从 `v1` 开始递增

说明：

- 当前历史数据集 `s800`、`s800_think` 保留兼容，不强制重命名
- 从现在开始新增数据集，统一按新规则命名
- 对于历史数据集，数据文件名继续保留旧标签；但新生成的 `run` 目录名会自动映射为更清晰的规范标签：
  - `s800` -> `synth_structuredthink_800_v1`
  - `s800_think` -> `synth_think_800_v1`

### run 目录命名

训练：

```text
{timestamp}_train_{dataset_tag}_{model_tag}_{exp_tag}
```

评测：

```text
{timestamp}_eval_{dataset_tag}_{model_tag}_{eval_tag}
```

抽样：

```text
{timestamp}_inspect_{dataset_tag}_{model_tag}_{inspect_tag}
```

示例：

- `20260517_195355_train_s800_think_qwen3.5-0.8b_smoke_ref`
- `20260517_203504_train_s800_think_qwen3.5-0.8b_reference_v1`

### 模型标签 `model_tag`

统一要求：

- 优先从 `model_id` 自动推导
- 必要时允许手工通过 `--model-tag` 覆盖
- 新模型不要在脚本里再次写死新的字符串

当前已内置常用映射示例：

- `Qwen/Qwen3.5-0.8B` -> `qwen3.5-0.8b`
- `Qwen/Qwen3.5-2B` -> `qwen3.5-2b`
- `Qwen/Qwen3.5-4B` -> `qwen3.5-4b`

后续新增模型时，应优先补到 `src/common/naming.py`，保持训练、评测、抽样三类 run 的命名口径一致。

## 三、数据字段命名规则

- 所有显式思维监督字段统一命名为 `xxx_think`
- 不再新增 `xxx_cot`
- `structured_cot` 只作为历史兼容字段保留
- 新增方法时直接扩展为：
  - `short_think`
  - `compressed_think`
  - `symbolic_think`
  - 其他符合规则的新字段

数据字段详情、必填/可选说明，统一看：

- [DATA_SCHEMA.md](DATA_SCHEMA.md)

## 四、脚本使用规范

### 数据生成

```bash
python scripts/generate_dataset.py --variant think --think-style by_view --dataset-tag s800_think
```

作用：

- 生成 `data/interim/aligned_*.jsonl`
- 生成 `data/final/train/val/test_*.jsonl`
- 生成数据摘要 json

### 数据校验

```bash
python scripts/validate_dataset.py data/final/train_s800_think.jsonl --expect-think-tags
```

作用：

- 检查字段是否缺失
- 检查 `messages` 格式是否正确
- 检查 `<think>` 包裹格式是否符合当前训练目标

### 训练

```bash
python scripts/train_lora_local.py --dataset-tag s800_think --run-tag reference_v1
```

作用：

- 自动创建标准命名的训练 run 目录
- 保存 `run_config.json`
- 保存 checkpoint
- 保存 `last_checkpoint.txt`

### 评测

```bash
python scripts/eval_compare_full.py --dataset-tag s800_think --checkpoint <checkpoint_path> --run-tag rule
```

作用：

- 生成 baseline / finetuned prediction
- 生成 `compare_summary.json`
- 可选接 `DeepSeek V4 Flash` 复核

### 抽样检查

```bash
python scripts/inspect_think_samples.py --checkpoint <checkpoint_path> --dataset-tag s800_think --tag think-samples
```

作用：

- 抽样检查白话 / 文言输入下的 `think` 输出是否符合预期

## 五、参考 Run 怎么用

### `smoke_ref`

- 目录：
  - `runs/20260517_195355_train_s800_think_qwen3.5-0.8b_smoke_ref`
- 用途：
  - 给新同学看完整训练产物长什么样
  - 用来验证链路是否通
- 注意：
  - 这条 run 的 `eval_steps=1`
  - 适合教学观察
  - 不适合作为正式长实验默认参数

### `reference_v1`

- 目录：
  - `runs/20260517_203504_train_s800_think_qwen3.5-0.8b_reference_v1`
- 用途：
  - 作为正式训练参数模板
  - 后续组员开新实验时优先参考它

## 六、文档更新规则

- 高层实验结论：
  - 写进 `PROJECT_PROGRESS.md`
- 数据字段规范：
  - 写进 `DATA_SCHEMA.md`
- 协作进展、交接说明、个人推进：
  - 统一追加到 `TEAM_SYNC_LOG.md`

禁止的做法：

- 不把重要结论只留在微信或口头交流里

## 七、依赖与环境

- 仓库当前采用 `uv + pyproject.toml` 作为主环境入口
- 新成员优先执行：

```bash
uv sync
```

- 兜底安装方式：

```bash
uv pip install -r requirements.txt
```

- 代码里实际会用到的核心外部依赖包括：
  - `ms-swift`
  - `torch`
  - `transformers`
  - `peft`
  - `datasets`
  - `accelerate`
- `ms-swift` 是外部包，不是仓库内目录；代码中的 `import swift` 就来自它
- AutoDL 当前实测环境版本：
  - `Python 3.12.3`
  - `torch 2.11.0+cu130`
  - `ms_swift 4.1.3`
  - `transformers 5.6.2`
- AutoDL 上训练和评测优先用 Linux 环境，统一通过 `uv run` 或 `.venv/bin/python` 启动
- 不覆盖他人日志条目
- 不只写“已完成”，必须写清楚做了什么、为什么、改了哪些文件、结果是什么

## 七、当前注意事项

- AutoDL 上运行时，统一优先使用：

```bash
.venv/bin/python
```

- 不要依赖交互 shell 的 `python3` 路径
- 不要把 `runs/`、`artifacts/`、`__pycache__/`、`.ipynb_checkpoints/` 提交到仓库
- 不要把临时响应文件、个人草稿、无关 notebook 缓存混进正式提交

## 八、当前组员最小上手路径

新同学接手时，按下面顺序操作即可：

1. 读 [README.md](../README.md)
2. 读 [DATA_SCHEMA.md](DATA_SCHEMA.md)
3. 读本文件
4. 看 `scripts/` 入口
5. 看 `runs/20260517_195355_train_s800_think_qwen3.5-0.8b_smoke_ref`
6. 在 `TEAM_SYNC_LOG.md` 追加自己的工作记录
