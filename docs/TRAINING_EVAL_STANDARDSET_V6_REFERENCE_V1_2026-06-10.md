# Training / Eval Note: standardset_v6_1234 reference_v1

本文档记录第一版 `1k+` 标准集 `standardset_v6_1234` 在 AutoDL 上的正式训练与测试集评测结果。

## 1. 数据版本

- dataset tag: `standardset_v6_1234`
- source file: `data/raw/labeled_pairs_pilot_v6_targeted400_p2_audited_merge.jsonl`
- total: `1234`
- split:
  - `train = 973`
  - `val = 129`
  - `test = 132`
- avg original chars: `430.67`
- avg compressed chars: `278.50`
- teacher-reference avg compression ratio: `0.6563`
- anchor rows: `1223 / 1234`

## 2. 训练配置

- base model: `Qwen/Qwen3.5-0.8B`
- method: `Swift + LoRA`
- mode: `language-model-only`
- run tag: `reference_v1`
- remote run dir:
  - `/root/projects/qwen35_zh_plaintext_compressor/experiments/20260610_152155_train_standardset_v6_1234_qwen3.5-0.8b_reference_v1`
- key hyperparameters:
  - `max_length = 1536`
  - `learning_rate = 1e-4`
  - `train_batch_size = 1`
  - `eval_batch_size = 1`
  - `gradient_accumulation_steps = 16`
  - `num_train_epochs = 1.0`

## 3. 训练结果

- final checkpoint: `checkpoint-61`
- train runtime: `2572s` (`42m 52s`)
- final train loss: `0.5575`
- final eval loss: `0.5315`
- final eval token acc: `0.8566`

中途关键节点：

- `step 40`
  - `eval_loss = 0.5355`
  - `eval_token_acc = 0.8560`
- `step 60`
  - `eval_loss = 0.5314`
  - `eval_token_acc = 0.8568`

判断：

- 训练过程稳定，无中断、无发散
- 后半程指标整体平稳略升
- 该 checkpoint 可作为当前第一版 mainline 压缩模型

## 4. 测试集评测

- eval run dir:
  - `/root/projects/qwen35_zh_plaintext_compressor/experiments/20260610_160737_eval_standardset_v6_1234_qwen3.5-0.8b_reference_v1_test_eval`
- evaluated model:
  - `checkpoint-61`
- test file:
  - `data/final/test_standardset_v6_1234.jsonl`

测试集结果：

- `avg_prediction_ratio = 0.7425`
- `avg_char_f1 = 0.8039`
- `avg_anchor_retention_rate = 0.8157`
- `avg_strict_anchor_retention_rate = 0.9216`
- `avg_soft_anchor_retention_rate = 0.8075`

## 5. 当前结论

这版模型已经证明：

- 小模型可在 `1234` 条高标准中文压缩数据上稳定收敛
- `strict anchor` 已达到较强水平
- 输出总体能较好贴近 teacher 风格

但当前也有明确短板：

- `prediction_ratio = 0.7425` 偏保守
- 模型更像“稳妥保真压缩器”，而不是“更强压缩但仍可靠”的版本

因此，这一版应被视为：

- 第一版可用 mainline checkpoint
- 不是最终效果版

## 6. 下一步最优先问题

下一步不宜盲目重复同配方重训，优先应处理：

1. 抽查测试集真实输出，确认“偏保守”主要出现在哪些文本类型。
2. 清理训练模板中的遗留 `response_prefix: '<think>\\n'` 问题，避免其继续拉高输出长度。
3. 在确认模板问题后，再决定第二版是：
   - 清模板后同数据重训
   - 还是补少量更强压缩风格数据再训
