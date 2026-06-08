# 项目进展记录

## 2026-05-15 初始工程搭建

- 建立了可复现实验目录结构：`data/raw`、`data/interim`、`data/final`、`scripts`、`runs`、`artifacts`
- 添加了最早期的试验性数据集生成与校验脚本
- 产出 `data/final/pilot.jsonl` 并完成基础 schema 校验
- 确认 `ms-swift` 支持本地 `jsonl/json/csv` 数据集
- 重构训练入口，使其直接消费 `messages` 风格的本地 JSONL 数据
- 扩展到以结构化 CoT 为核心的第一版数据集，并完成首轮正式训练
- 生成当前标准数据集 `s800`：
  - 对齐源样本 `400` 条
  - 视图扩展后 train/val/test 共 `800` 条
- 完成主线 `s800` LoRA 训练：
  - `runs/20260515_210429/checkpoints/checkpoint-40`

## 当前认可的数据方向

- 保留 `structured_think` 作为现阶段最可控的结构化思维监督目标，因为它最容易校验，也最符合当前实验目标
- 当前标准训练任务定义为两个输入视图映射到同一目标风格：
  - `modern_question -> structured_think + answer`
  - `classical_question -> structured_think + answer`
- 不把基座模型天然产生的 `<think>` 当成训练标签
- 当前大规模测试先回答一个窄问题：
  - 结构化监督加上白话/文言输入视图，是否比 baseline 更强

## 2026-05-16 评测更新

- 首次在 `data/final/test_s800.jsonl` 上做全量比较，`max_tokens=256`
- 得到 `baseline=23.75%`、`finetuned=63.75%`
- 但这轮不能作为最终结论，因为长 `<think>` 常常耗尽解码预算，导致最终答案没有稳定输出
- 通过人工检查 `weight_remaining` 样本确认了这个问题：
  - 中间计算经常是对的
  - 但最终答案串被截断
  - 从而污染规则抽取结果
- 之后用 `max_tokens=512` 重新评测：
  - `runs/20260516_150218_compare_s800_full_mt512`

### 修正后的规则评测结果

- baseline：`44/80 = 55.0%`
- finetuned：`77/80 = 96.25%`

### 修正后的微调模型分题型结果

- `give_away`：`100%`
- `box_total`：`100%`
- `equal_division`：`85.7%`
- `unit_price`：`92.9%`
- `bundle_count`：`100%`
- `weight_remaining`：`100%`

### 修正后的微调模型分视图结果

- modern：`100%`
- classical：`92.5%`

## 当前理解

- 当前 `s800` 结构化 CoT 数据集在其合成分布内已经非常强
- 当前主要残留问题不再是基础算术能力，而是输出控制
- baseline 和 finetuned 都保留了 Qwen 默认的 `<think>` 行为，这会带来：
  - 输出过长
  - 最终答案不稳定
  - 评测对解码长度敏感
- 因此下一轮必须同时优化：
  - 数据多样性
  - 目标格式纪律
  - 评测鲁棒性

## 2026-05-16 评测管线更新

- 正式评测管线升级为两阶段：
  - 第一阶段：规则抽取数值答案并做精确匹配
  - 第二阶段：使用 `DeepSeek V4 Flash` 对错例或指定样本做复核
- 这么做的原因是 baseline 已经暴露出一个明确问题：
  - 模型可能推理正确
  - 但最终答案埋在长输出里
  - 导致纯规则抽取低估真实正确率
- 新的标准评测脚本是：
  - `scripts/eval_compare_full.py`
- 当前它支持：
  - 直接生成并评测
  - 复用旧 run 的 prediction 文件
  - 对 `mismatches` 或 `all` 样本做 `DeepSeek V4 Flash` 复核
  - 分别汇报规则正确率和 LLM 复核后正确率

### 2026-05-16 全量 DeepSeek 复核结果

- 复用了 `512` token 版本的已保存 prediction
- 在 `runs/20260516_full_llm_review` 上完成 mismatch 复核
- baseline：
  - 规则评测：`55.0%`
  - LLM 复核后：`90.0%`
  - 复核错例数：`36`
  - 从错改为对：`28`
- finetuned：
  - 规则评测：`96.25%`
  - LLM 复核后：`100%`
  - 复核错例数：`3`
  - 从错改为对：`3`

### baseline 的 LLM 复核后结果

- 分题型：
  - `give_away`：`78.6%`
  - `box_total`：`100%`
  - `equal_division`：`100%`
  - `unit_price`：`64.3%`
  - `bundle_count`：`100%`
  - `weight_remaining`：`100%`
- 分视图：
  - modern：`100%`
  - classical：`80%`

### finetuned 的 LLM 复核后结果

- 分题型：全部 `100%`
- 分视图：
  - modern：`100%`
  - classical：`100%`

## 更新后的阶段性结论

- baseline 的规则评测和 LLM 复核结果差距很大，说明单纯数值抽取严重低估了它的真实能力
- finetuned 模型受这个问题影响小得多，因为它更倾向于输出明确且稳定的最终答案
- 因此后续报告必须同时展示：
  - 规则正确率
  - LLM 复核后正确率
- 在当前 `s800` 分布上，主线 LoRA 模型更适合被描述为：
  - 规则评测很强
  - LLM 复核后几乎饱和
  - 主要短板已从“不会做题”转为“输出控制”

## 2026-05-16 think 监督方向更新

- 明确确认了旧管线的关键缺口：
  - 训练目标只包含 `structured_think + answer`
  - 并没有显式监督 `<think>...</think>` 内部内容
- 同时确认了已安装的 Swift 模板行为：
  - Qwen3.5 默认开启 thinking mode
  - 会自动插入 thinking prefix
- 因而旧实验的提升应解释为：
  - 可见答案行为改善
  - 而不是 `think` 语言风格真正被对齐

### 新的显式 think 监督方案

- 新增第二套数据集变体：
  - `s800_think`
- 每条对齐源样本新增字段：
  - `structured_think`
  - `modern_think`
  - `classical_think`
- think-supervised 目标格式显式定义为：
  - `modern_question -> <think>modern_think</think> + 答案`
  - `classical_question -> <think>classical_think</think> + 答案`

### 新增支撑脚本

- `scripts/generate_dataset.py`
  - 支持 `--variant visible|think`
  - 支持 `--think-style by_view|structured`
- `scripts/validate_dataset.py`
  - 支持 `--expect-think-tags`
- `scripts/train_lora_local.py`
  - 支持 `--dataset-tag s800_think`
- `scripts/inspect_think_samples.py`
  - 用于快速抽样观察白话/文言 `think` 输出

### 当时的直接目标

- 先跑一个 `s800_think` 小规模 pilot
- 在全量训练前验证三件事：
  - `<think>` 是否由英文转为中文
  - 白话/文言输入是否真的控制思维风格
  - 答案正确率是否仍然稳定

## 2026-05-17 think 监督 pilot 正式结果

- 完成第一轮显式 think-supervised pilot：
  - run dir：`runs/20260517_002714_think_pilot`
  - checkpoint：`runs/20260517_002714_think_pilot/checkpoints/checkpoint-40`
- 最终训练状态：
  - `train_runtime = 1451s`
  - `eval_loss = 0.00076153`
  - `eval_token_acc = 1.0`

### 定性结果

- 这轮 pilot 实现了之前缺失的目标行为：
  - 白话题会触发白话中文 `<think>`
  - 文言题会触发文言中文 `<think>`
  - 抽样中不再看到默认英文 think 痕迹

### 样例证据

- 白话题：
  - 题目：`小明有12颗糖，送给小红5颗，还剩几颗？`
  - 输出 think：`原来有12颗糖，送给小红5颗，所以用减法：12-5=7。`
- 文言题：
  - 题目：`明有糖12颗，遗红5颗，尚余几何？`
  - 输出 think：`初有12颗，遗5颗，故12-5=7。`

### 在 `test_s800_think` 上的定量结果

- 对比 run：
  - `runs/20260517_113430_compare_s800_think_checkpoint40`
- 规则评测 baseline：
  - `44/80 = 55.0%`
- 规则评测 finetuned：
  - `80/80 = 100%`

### 补充说明

- 在 think 格式测试集上，微调模型的输出控制也显著改善：
  - `answer_marker_rate = 1.0`
  - `avg_chars = 50.96`
  - `avg_lines = 5.0`
- baseline 仍然保留原先问题：
  - 输出很长
  - 最终答案不稳定
  - classical view 明显更弱

## 当前下一步重点

- think 监督这条路线已经被验证为技术上可行
- 当前下一优先级转为仓库规范化，目标是让：
  - 负责造数据的同学能扩展数据而不破坏训练主线
  - 负责深度评测的同学能加指标而不污染核心训练逻辑
  - 所有实验产物都能稳定追溯、方便横向比较

## 2026-05-17 仓库规范化第一阶段推进

- 新增并统一了仓库公共模块：
  - `src/common/paths.py`
  - `src/common/naming.py`
  - `src/common/schema.py`
- 把数据、训练、评测、抽样脚本接入统一命名规则，后续新 run 自动按阶段生成目录名
- 新增中文文档入口：
  - `docs/README.md`
  - `docs/TEAM_SYNC_LOG.md`
- 明确并固化当前命名口径：
  - 所有显式思维监督字段统一用 `xxx_think`
  - `structured_cot` 仅作为历史兼容字段保留
- 当前仓库仍保持旧实验结果不变，规范化只影响后续新增数据和新增 run

## 2026-05-30 第二阶段主线收敛

- 当前项目阶段正式从“显式 `think` 监督是否可行”切换到“如何形成可扩展、可比较、可汇报的实验体系”
- 第二阶段的三条主轴明确为：
  - `Data Set`
  - `Model`
  - `Benchmark`
- 当前代码现状下，这三条主轴分别对应：
  - `Data Set`：扩展 `s800 / s800_think` 之外的数据来源与难度层次，同时保持 `xxx_think` schema 稳定
  - `Model`：在 `0.8B` 主线基础上扩展到 `2B / 4B`，并系统比较 `modern_think / classical_think / structured_think`
  - `Benchmark`：以现有 `eval_compare_full.py` 为稳定基线，冻结答案抽取、复核与对照组口径，再逐步扩指标
- 当前阶段不再以“单次训练跑通”为目标，而以“多数据版本、多模型规模、多监督形式之间的横向可比性”为目标
- 第二阶段已经新增统一执行文档：
  - `docs/STAGE2_EXECUTION_GUIDE.md`
- 新文档的定位不是 brainstorm，而是当前协作正式入口，用于统一：
  - 每位组员的任务边界
  - 不可破坏的主线限制条件
  - 文档、脚本、实验目录之间的协作规则

## 2026-05-30 README 展示化与 run 命名规范化

- 根 `README.md` 已从“阶段记录型说明”升级为“研究问题 + 方法概览 + 实验矩阵 + 协作入口”的展示型首页
- 当前首页已明确：
  - 项目研究问题
  - 三条第二阶段主轴
  - 方法流程
  - 实验矩阵
  - 文档阅读顺序
- 同时对 `run` 命名逻辑做了兼容式规范化：
  - 历史数据文件仍保留 `s800 / s800_think`
  - 但新生成的 `run` 目录名不再直接暴露这些旧标签，而会自动映射为更清晰的规范名
  - 当前映射规则：
    - `s800` -> `synth_structuredthink_800_v1`
    - `s800_think` -> `synth_think_800_v1`
- 这样做的目的是：
  - 不破坏现有数据文件路径与旧实验结果
  - 同时让后续新增训练、评测、抽样 run 的目录名更适合横向比较与长期追溯

## 2026-05-30 model_tag 规范化

- 为了给后续 `2B / 4B` 模型轴扩展铺路，当前主线已不再把 `model_tag` 只当成写死的 `qwen3.5-0.8b`
- 训练、评测、抽样三类脚本现在统一支持：
  - `--model-id`
  - `--model-tag`
- 当前规范是：
  - 默认优先根据 `model_id` 自动推导 `model_tag`
  - 仅在需要特殊展示名时才手工覆盖 `--model-tag`
- 命名逻辑已经集中到：
  - `src/common/naming.py`
- 当前内置的常用映射包括：
  - `Qwen/Qwen3.5-0.8B` -> `qwen3.5-0.8b`
  - `Qwen/Qwen3.5-2B` -> `qwen3.5-2b`
  - `Qwen/Qwen3.5-4B` -> `qwen3.5-4b`
- 这样后续模型规模扩展时：
  - 不需要再改一轮 run 命名规则
  - 训练、评测、抽样目录名会天然保持一致

## 2026-05-17 AutoDL 全链路参考 run

- 为了让后续组员有可以直接参考的训练样板，新增了两类参考 run：
  - `smoke` 参考：验证全链路是否完整可用
  - `reference` 参考：作为正式训练参数模板

### smoke 参考 run

- run 目录：
  - `runs/20260517_195355_train_s800_think_qwen3.5-0.8b_smoke_ref`
- 目标：
  - 验证 `run_config.json`
  - 验证 checkpoint 正常产出
  - 验证 `last_checkpoint.txt`
  - 验证训练入口、数据入口、LoRA、CUDA、Swift 模板全链路可跑
- 结果：
  - 已完整跑通
  - 最终日志显示：
    - `train_runtime = 445.4s`
    - `train_loss = 1.652`
    - `eval_loss = 1.083`
    - `eval_token_acc = 0.7705`

### smoke 配置的经验教训

- 该 run 使用了非常高的评测频率：
  - `save_steps=1`
  - `eval_steps=1`
- 这虽然适合作为“教学型样板”，方便观察每一步如何产生产物，但并不适合作为正式训练默认配置
- 原因是：
  - 即使训练步数很少，只要每一步都跑完整验证集，总耗时依然会明显膨胀

### formal reference run

- 已完成一条正式参考 run，供后续组员直接对照标准配置：
  - `run_tag=reference_v1`
  - run 目录：`runs/20260517_203504_train_s800_think_qwen3.5-0.8b_reference_v1`
- 参数口径：
  - `dataset_tag=s800_think`
  - `max_length=1024`
  - `learning_rate=1e-4`
  - `gradient_accumulation_steps=16`
  - `num_train_epochs=1.0`
  - `save_steps=25`
  - `eval_steps=25`
  - `logging_steps=5`
- 这条 run 的用途是：
  - 给后续正式实验提供标准训练模板
  - 避免队友误用 smoke 参数

### formal reference run 最终结果

- 最终 checkpoint：
  - `checkpoint-40`
- 最终训练结果：
  - `train_runtime = 1322.5324s`
  - `train_loss = 0.27809329`
  - `epoch = 1.0`
- 最终验证结果：
  - `eval_loss = 0.00075078`
  - `eval_token_acc = 1.0`

### 参考意义

- `smoke_ref` 解决的是“整条链路能不能通”
- `reference_v1` 解决的是“正式训练默认应该怎么配”
- 因此后续组员若要新开正式实验，应优先参考：
  - `runs/20260517_203504_train_s800_think_qwen3.5-0.8b_reference_v1`

## 2026-05-19 reference_v1 复核结果

- 在 GPU 恢复可见后，重新补跑了 `reference_v1` 的 `think` 抽样与正式评测

### `think` 抽样对比结论

- 基座模型 `think`：
  - 仍是英文长推理，典型格式是 `Thinking Process:`
  - 现代汉语题和文言题都没有被监督到中文 `think`
- `reference_v1` 微调后 `think`：
  - 已稳定转为中文
  - 白话题对应白话 `think`
  - 文言题对应文言 `think`
  - 典型样式是：
    - 白话：`原来有12颗糖，送给小红5颗，所以用减法：12-5=7。`
    - 文言：`初有12颗，遗5颗，故12-5=7。`

### 正式评测结果

- 评测 run：
  - `runs/20260518_232002_eval_s800_think_qwen3.5-0.8b_reference_v1_rule_gpu_fixed`
- 规则评测 baseline：
  - `55.0%`
- 规则评测 finetuned：
  - `100%`
- mismatch 复核后 baseline：
  - `100%`
- mismatch 复核后 finetuned：
  - `100%`

### 结论

- `reference_v1` 不只是提升了最终答案稳定性，也把 `<think>` 内部内容从英文长推理改成了受监督的中文思维输出
- 这说明当前数据与训练方式确实实现了“显式监督 think 内容”的目标
- 同时也说明 baseline 的 `55%` 只是规则抽取口径偏低，经过 LLM 复核后其真实正确率同样可以回到 `100%`
