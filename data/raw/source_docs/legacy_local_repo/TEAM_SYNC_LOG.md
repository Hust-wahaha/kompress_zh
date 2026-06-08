# 团队协作进度日志

本文件是全组统一的接龙式进度文档。所有组员都只在文末追加，不覆盖、不删除他人内容。

## 目的

- 降低组员之间的沟通成本
- 保证任何人都能快速接手上一位同学的工作
- 避免“知道做了什么，但不知道为什么、改了哪里、结果如何”

## 强制更新规则

- 每完成一段可汇报工作，就追加一条记录
- 时间必须写绝对时间，统一格式：`YYYY-MM-DD HH:MM`
- 必须写清楚文件路径、实验目录、结果结论
- 结论和问题都要写，不能只写“已完成”
- 发现前文有误时，新增一条“勘误/修正”，不要直接改写旧记录
- 新条目统一追加到文末，按时间自然接龙

## 记录模板

将下面模板复制到文末直接填写：

```md
## [姓名] | [YYYY-MM-DD HH:MM]

### 本次工作
- 

### 为什么这样做
- 

### 修改/涉及文件
- 

### 实验或运行信息
- 机器：
- 命令：
- 输出目录：

### 结果与结论
- 

### 风险 / 遗留问题
- 

### 建议下一步
- 
```

## 填写标准

- “本次工作”写动作，不写空话
- “为什么这样做”写动机，不写“老师要求”
- “修改/涉及文件”必须写仓库内相对路径
- “结果与结论”必须包含可复用信息，例如准确率、失败模式、异常现象
- “建议下一步”要写到下一个同学可以直接开做

## 示例

## Zhuoya Wang_with_codex | 2026-05-17 18:00

### 本次工作
- 跑通 `s800_think` 的显式 `think` 监督
- 补齐仓库中文文档与协作规范

### 为什么这样做
- 需要先验证“监督 `<think>` 内容本身”这条主线是否成立
- 后续会有同学分工造数据和做评测，仓库必须先变成可协作状态

### 修改/涉及文件
- `scripts/generate_dataset.py`
- `scripts/train_lora_local.py`
- `scripts/inspect_think_samples.py`
- `docs/PROJECT_PROGRESS.md`

### 实验或运行信息
- 机器：AutoDL RTX 4090 24GB
- 命令：`python scripts/train_lora_local.py --dataset-tag s800_think --run-tag think_pilot`
- 输出目录：`runs/20260517_002714_think_pilot`

### 结果与结论
- 微调后白话题输出白话 `think`
- 微调后文言题输出文言 `think`
- `test_s800_think` 规则评测从 `55.0%` 提升到 `100%`

### 风险 / 遗留问题
- 当前数据规模仍小，暂时不能代表跨分布泛化
- 更细的 `think` 质量评测脚本仍待补齐

### 建议下一步
- 继续扩充数据集版本，同时保持命名与 schema 稳定
- 让评测同学基于统一目录和字段规范补深度指标

## Zhuoya Wang_with_codex | 2026-05-17 20:35

### 本次工作
- 在 AutoDL 上补跑一条全链路 smoke 训练参考
- 启动一条正式训练参考 run，供后续组员直接复用
- 验证远端仓库新架构、虚拟环境、数据生成与校验链路可用

### 为什么这样做
- 仅有“脚本能启动”还不够，组员更需要看到完整训练产物长什么样
- smoke run 用来证明仓库现在能从数据到 checkpoint 全链路闭环
- formal reference run 用来提供标准参数模板，避免后续同学直接照搬不合理的 smoke 评测频率

### 修改/涉及文件
- `docs/PROJECT_PROGRESS.md`
- `docs/TEAM_SYNC_LOG.md`
- 远端实验目录：`runs/20260517_195355_train_s800_think_qwen3.5-0.8b_smoke_ref`

### 实验或运行信息
- 机器：AutoDL RTX 4090 24GB
- smoke 命令：`.venv/bin/python scripts/train_lora_local.py --dataset-tag s800_think --run-tag smoke_ref --max-length 512 --num-train-epochs 0.05 --gradient-accumulation-steps 8 --save-steps 1 --eval-steps 1 --logging-steps 1`
- smoke 输出目录：`runs/20260517_195355_train_s800_think_qwen3.5-0.8b_smoke_ref`
- formal 命令：`.venv/bin/python scripts/train_lora_local.py --dataset-tag s800_think --run-tag reference_v1 --max-length 1024 --learning-rate 1e-4 --train-batch-size 1 --eval-batch-size 1 --gradient-accumulation-steps 16 --num-train-epochs 1.0 --save-steps 25 --eval-steps 25 --logging-steps 5`
- formal 输出目录：`runs/20260517_203504_train_s800_think_qwen3.5-0.8b_reference_v1`

### 结果与结论
- smoke 训练已完整跑通
- smoke run 证明以下链路都正常：
  - 数据读取
  - Swift 模板编码
  - LoRA 挂载
  - CUDA 训练
  - checkpoint 保存
  - run_config / last_checkpoint 追溯文件生成
- smoke 最终结果：
  - `train_runtime = 445.4s`
  - `train_loss = 1.652`
  - `eval_loss = 1.083`
  - `eval_token_acc = 0.7705`
- smoke 同时暴露出一个重要经验：
  - `eval_steps=1` 虽然适合教学观察，但会显著拖慢总时长，不能作为正式默认配置

### 风险 / 遗留问题
- 远端命令应统一显式使用 `.venv/bin/python`，不要依赖交互 shell 的 PATH
- 当前文档与仓库结构已适合组员接手，但更深入的评测维度仍待后续组员扩展

### 建议下一步
- 后续组员新增训练实验时，优先参考 formal run，不要直接照抄 smoke 参数
- 若新增数据方向，先保证 `dataset_tag`、`xxx_think` 命名和 schema 规则不被破坏

## Zhuoya Wang_with_codex | 2026-05-17 22:21

### 本次工作
- 补记 `reference_v1` 正式参考 run 的最终结果
- 将仓库规范文档改名为更直接的规则文档 `REPOSITORY_RULES.md`

### 为什么这样做
- 队友需要直接可执行的现行规则，而不是继续看带有 `plan` 语义的文档名
- 正式参考 run 已完成，需要把它补进文档，作为后续训练模板

### 修改/涉及文件
- `README.md`
- `docs/README.md`
- `docs/PROJECT_PROGRESS.md`
- `docs/TEAM_SYNC_LOG.md`
- `docs/PHASE1_EXECUTION_CHECKLIST.md`
- `docs/REPOSITORY_RULES.md`

### 实验或运行信息
- 机器：AutoDL RTX 4090 24GB
- formal 输出目录：`runs/20260517_203504_train_s800_think_qwen3.5-0.8b_reference_v1`

### 结果与结论
- `reference_v1` 已正常完成
- 最终 checkpoint：
  - `checkpoint-40`
- 最终训练结果：
  - `train_runtime = 1322.5324s`
  - `train_loss = 0.27809329`
- 最终验证结果：
  - `eval_loss = 0.00075078`
  - `eval_token_acc = 1.0`
- 后续正式训练应优先参考这条 run，而不是 `smoke_ref`

### 风险 / 遗留问题
- 当前文档与仓库结构已经适合组员接手，但更深入的评测维度仍待后续组员扩展

### 建议下一步
- 后续若新增数据方向，先保证 `dataset_tag`、`xxx_think` 命名和 schema 规则不被破坏
- 新实验默认沿用 `reference_v1` 参数，再按实验目标做局部改动

## Zhuoya Wang_with_codex | 2026-05-19 10:20

### 本次工作
- 在 GPU 恢复后，补跑 `reference_v1` 的 `think` 抽样与正式评测
- 把最新结果补进项目进度文档和协作日志

### 为什么这样做
- 需要确认 `reference_v1` 不仅在答案上有效，也在 `<think>` 内容上真的发生了变化
- 既然模型与评测都已经跑完，就应该把最终结论写入正式文档，方便后续组员直接查看

### 修改/涉及文件
- `docs/PROJECT_PROGRESS.md`
- `docs/TEAM_SYNC_LOG.md`

### 实验或运行信息
- 机器：AutoDL RTX 4090 24GB
- `think` 抽样 run：
  - `runs/20260518_230355_inspect_s800_think_qwen3.5-0.8b_reference_v1_base_gpu`
  - `runs/20260518_230359_inspect_s800_think_qwen3.5-0.8b_reference_v1_ft_gpu`
- 正式评测 run：
  - `runs/20260518_232002_eval_s800_think_qwen3.5-0.8b_reference_v1_rule_gpu_fixed`

### 结果与结论
- 基座模型的 `think` 仍是英文长推理
- `reference_v1` 的 `think` 已稳定变为中文，并能跟随白话/文言题面切换
- 正式规则评测结果：
  - baseline `55.0%`
  - finetuned `100%`
- mismatch 复核后：
  - baseline `100%`
  - finetuned `100%`

### 风险 / 遗留问题
- 后续如果新增更复杂的题型或更强压缩目标，还需要再做新的评测与 case study
- baseline 的 `55%` 只是规则抽取口径偏低，不是最终真实正确率

### 建议下一步
- 如果继续扩数据，优先保持当前 `xxx_think` 命名和 `reference_v1` 的训练/评测口径一致

## Zhuoya Wang_with_codex | 2026-05-17 22:35

### 本次工作
- 统一团队协作日志中的历史、当前与未来署名规范
- 补全中间日志条目中已经过时的“待补记”状态

### 为什么这样做
- 协作日志是组内长期接龙文档，署名必须统一，否则后续追溯容易混乱
- 已经完成的事项不应该继续保留“待补记”状态，否则会误导队友判断当前进度

### 修改/涉及文件
- `docs/TEAM_SYNC_LOG.md`

### 实验或运行信息
- 机器：本地文档整理
- 命令：无
- 输出目录：无

### 结果与结论
- 所有历史与当前 `Codex` 署名均已统一为 `Zhuoya Wang_with_codex`
- 示例、历史条目、后续接龙口径现在一致
- `formal` 参考 run 的输出目录与状态在日志中已补齐，不再存在“待补记”残留

### 风险 / 遗留问题
- 无新增风险

### 建议下一步
- 以后所有由你与我协同完成的日志条目，统一继续使用 `Zhuoya Wang_with_codex`

## Zhuoya Wang_with_codex | 2026-05-30 20:50

### 本次工作
- 新增第二阶段统一执行文档
- 重写仓库根 `README.md`
- 更新文档导航，明确新同学的阅读顺序

### 为什么这样做
- 当前项目已经从“think 监督是否可行”进入“多数据、多模型、多评测轴并行推进”的第二阶段
- 如果不把任务边界、限制条件和协作口径提前冻结，后续很容易出现各做各的、结果无法整合的问题
- 原有 `README` 更偏第一阶段记录，不足以作为后续对外展示和新成员接手入口

### 修改/涉及文件
- `README.md`
- `docs/README.md`
- `docs/STAGE2_EXECUTION_GUIDE.md`
- `docs/PROJECT_PROGRESS.md`
- `docs/TEAM_SYNC_LOG.md`

### 实验或运行信息
- 机器：本地文档整理
- 命令：无
- 输出目录：无

### 结果与结论
- 现在仓库已经有一份明确的第二阶段协作入口文档，组员可以只看自己负责的部分开展工作
- 根 `README` 已改为更接近论文式项目首页的结构，明确了研究问题、当前阶段、三条主轴和协作入口
- 文档导航已更新，新的默认阅读顺序为：
  - `README.md`
  - `docs/STAGE2_EXECUTION_GUIDE.md`
  - `docs/PROJECT_PROGRESS.md`
  - `docs/DATA_SCHEMA.md`

### 风险 / 遗留问题
- 当前本地文档主线仍主要围绕 `s800 / s800_think`，后续若公开数据集扩展脚本正式进入主仓，README 还需补一次脚本入口说明
- 第二阶段 Benchmark 协议虽然已确定由谁负责，但具体评测字段与命令模板仍需后续落正式文档

### 建议下一步
- 由各负责同学按 `STAGE2_EXECUTION_GUIDE.md` 开始推进自己的任务
- 后续任何影响全组可比性的改动，先更新文档，再改脚本

## Zhuoya Wang_with_codex | 2026-05-30 21:10

### 本次工作
- 继续强化根 `README.md` 的对外展示结构
- 规范化新 run 的数据集标签呈现方式

### 为什么这样做
- 当前 README 已经不只是给组内自用，还承担新成员接手和对外展示的入口作用
- 现有脚本虽然已有统一 `make_run_dir()`，但上游默认 `dataset_tag` 仍沿用 `s800 / s800_think`，导致新 run 名在第二阶段显得混乱

### 修改/涉及文件
- `README.md`
- `src/common/naming.py`
- `scripts/train_lora_local.py`
- `scripts/eval_compare_full.py`
- `docs/REPOSITORY_RULES.md`
- `docs/PROJECT_PROGRESS.md`
- `docs/TEAM_SYNC_LOG.md`

### 实验或运行信息
- 机器：本地文档与脚本整理
- 命令：未实际发起训练，仅修改命名逻辑与默认参数来源
- 输出目录：无

### 结果与结论
- README 现在新增了：
  - 项目亮点
  - 方法概览
  - 第二阶段实验矩阵
- `run` 命名现在对历史数据集采用兼容映射：
  - `s800` -> `synth_structuredthink_800_v1`
  - `s800_think` -> `synth_think_800_v1`
- 数据文件路径保持不变，因此不会破坏旧数据与旧脚本
- `train_lora_local.py` 与 `eval_compare_full.py` 的默认 `dataset_tag` 现在都统一从 `src/common/naming.py` 取值，不再各自手写字符串

### 风险 / 遗留问题
- 当前本地仓库尚未把公开数据扩展脚本正式并入主线，所以 README 仍主要围绕现有 `local_repo` 主线脚本展开
- 后续若 `2B / 4B` 模型轴正式接入，`model_tag` 也需要做同样层级的规范化

### 建议下一步
- 下一步可继续把 `model_tag` 从写死 `qwen3.5-0.8b` 改成统一可配置
- 待你确认后，再把这一轮文档与命名修改整体推送到 GitHub

## Zhuoya Wang_with_codex | 2026-05-30 21:25

### 本次工作
- 将 `model_tag` 从单一硬编码改为统一可配置
- 把训练、评测、抽样三类脚本全部接入同一套模型命名逻辑

### 为什么这样做
- 前一轮已经把 `dataset_tag` 的 run 命名做了兼容规范化，但如果 `model_tag` 仍写死，后续 `2B / 4B` 实验还是会再次出现命名混乱
- 第二阶段已经明确要扩模型轴，因此必须先把 `model_id -> model_tag -> run 名` 这条链路收干净

### 修改/涉及文件
- `src/common/naming.py`
- `scripts/train_lora_local.py`
- `scripts/eval_compare_full.py`
- `scripts/inspect_think_samples.py`
- `README.md`
- `docs/REPOSITORY_RULES.md`
- `docs/PROJECT_PROGRESS.md`
- `docs/TEAM_SYNC_LOG.md`

### 实验或运行信息
- 机器：本地脚本整理
- 命令：`python3 -m py_compile src/common/naming.py scripts/train_lora_local.py scripts/eval_compare_full.py scripts/inspect_think_samples.py`
- 输出目录：无

### 结果与结论
- 三类主线脚本现在都支持：
  - `--model-id`
  - `--model-tag`
- 默认会根据 `model_id` 自动得到规范 `model_tag`
- 当前已内置常用映射：
  - `Qwen/Qwen3.5-0.8B` -> `qwen3.5-0.8b`
  - `Qwen/Qwen3.5-2B` -> `qwen3.5-2b`
  - `Qwen/Qwen3.5-4B` -> `qwen3.5-4b`
- 这样后续如果白泽鑫扩 2B / 4B，不需要再自己处理 run 命名问题

### 风险 / 遗留问题
- 当前内置映射只覆盖常见 Qwen 型号；后续如果接其他模型家族，应继续补到 `src/common/naming.py`
- 现有历史文档中的旧 run 名不会自动改写，属于正常历史记录

### 建议下一步
- 下一步可以把这轮文档与命名更新推到 GitHub
- 后续模型轴扩展时，优先复用现有 `--model-id` / `--model-tag` 入口，不要再在脚本里手写新字符串
