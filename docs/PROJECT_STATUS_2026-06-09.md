# Project Status 2026-06-09

本文档记录截至 `2026-06-09` 的阶段性状态，供后续组员或 Agent 快速接手。

## 1. 当前已完成内容

### 数据

- `pilot_rewrite_v1` 已完成
- `pilot_rewrite_v2_anchor_aug` 已完成
- `Codex session` 来源接入链路已跑通
- 当前稳定基线数据规模：`185`
- 当前 clean 工作版合并数据规模：`223`
  - 即 `185` 基线 + `42` 条已接收 session 样本 - `11` 条 defer
- 大候选池 `v11 bigpool` 已构建完成
  - raw/source pool：`3174`
  - funnel filtered：`2792`
  - 排除当前 official working dataset overlap 后剩余：`2775`
- 首轮 `500` 候选批次已完成 `DeepSeek v4 pro` 全标
  - 候选文件：`data/interim/source_pool_v12_batch500_candidate_familycap24.jsonl`
  - 首轮合并标注文件：`data/raw/batch500_candidate_labeled_deepseek_v4pro_v1.jsonl`
  - 长度分布：`short=108 / medium=307 / long=85`
- 首轮 review queue 已生成
  - `P0 = 36`
  - `P1 = 78`
  - `P2 = 386`
  - 当前已切出 `P0/P1 = 114` 条进入三轮 relabel 池
  - relabel 输出目录：`data/raw/relabel_rounds/`
- `P0/P1` 三轮 relabel 已完成
  - 轮次：`conservative / balanced / aggressive`
  - 稳定晋级 `P2`：`11`
  - 继续 defer：`103`
  - 该轮实验后，当前默认策略已调整为：后续批次 `P0/P1` 不再走 relabel 主路径，直接 defer
- 当前最终待轻审 keep pool 已生成
  - `首轮原生 P2 = 386`
  - `relabel 晋级 P2 = 11`
  - 合并后 `final_keep_pool = 397`
- 当前 final audit sample 已生成
  - 抽样文件：`data/interim/batch500_candidate_final_audit_sample_v1.jsonl`
  - 抽样数：`40`
  - 其中 `promoted = 11`
  - 长度覆盖：`long=16 / medium=12 / short=12`
- 当前 final audit sample 已完成人工复核
  - `40 accept / 0 defer`
  - 未发现阻断性 semantic-loss case
- 当前批次已完成正式 merge
  - merged dataset：`data/raw/labeled_pairs_pilot_v4_batch500_p2_audited_merge.jsonl`
  - `base_count = 223`
  - `batch_keep = 397`
  - `merged_count = 620`
- 第二个 `500` 候选批次已完成
  - 首轮 review queue：`P0 = 42 / P1 = 82 / P2 = 376`
  - 按新策略，`P0/P1` 直接 defer，不再 relabel
  - `P2-only keep pool = 376`
  - final audit sample：`35`
  - 人工复核结果：`35 accept / 0 defer`
- 第二批已完成正式 merge
  - merged dataset：`data/raw/labeled_pairs_pilot_v5_batch500_v2_p2_audited_merge.jsonl`
  - `base_count = 620`
  - `batch_keep = 376`
  - `merged_count = 996`
- `targeted400` 定向补洞批次已完成
  - 候选文件：`data/interim/source_pool_v14_targeted400_post996_long_session_agent.jsonl`
  - teacher 全标：`400`
  - 首轮 review queue：`P0 = 71 / P1 = 91 / P2 = 238`
  - 按当前策略，`P0/P1` 直接 defer
  - `P2-only keep pool = 238`
  - final audit sample：`23`
  - 人工复核结果：`23 accept / 0 defer`
- `targeted400` 已完成正式 merge
  - merged dataset：`data/raw/labeled_pairs_pilot_v6_targeted400_p2_audited_merge.jsonl`
  - `base_count = 996`
  - `batch_keep = 238`
  - `merged_count = 1234`

### session 增量的当前口径

本轮 `session` 子集已经完成一轮 strict 清账：

- 已接收：`42`
- 已明确 defer：`11`
- 待补判：`0`
- 孤儿决策 ID：`0`

因此当前应把：

- `labeled_pairs_pilot_v2_anchor_aug.jsonl`
  视为稳定基线
- `labeled_pairs_pilot_v3_session_aug_clean.jsonl`
  视为当前已清账的 session 增量工作版数据集

其中需要特别记录的一点是：

- 第一版 `decision_v1` 曾混入旧样本集 ID，导致 `pending` 与 `orphan` 问题暴露
- 现已改为与当前 `53` 条 cleaned-intersection 样本严格对齐的 `decision_v2`
- strict merge 已通过，说明当前 `v3_session_aug_clean` 至少在流程一致性上已闭环

### 训练

- `Qwen/Qwen3.5-0.8B + Swift + LoRA` 训练链路已跑通
- `language-model-only` 已强制落实到训练和评测脚本
- 语言模型输出中多余 `<think>` 空壳问题已处理
- 基于 `standardset_v6_1234` 的第一版正式训练已完成
  - dataset tag：`standardset_v6_1234`
  - split：`train=973 / val=129 / test=132`
  - run：`20260610_152155_train_standardset_v6_1234_qwen3.5-0.8b_reference_v1`
  - final checkpoint：`checkpoint-61`
  - final train loss：`0.5575`
  - final eval loss：`0.5315`
  - final eval token acc：`0.8566`

### 评测

- 已完成 `V1` 与 `V2` 在同一测试集上的可比评测
- 已对原有 `anchor retention` 规则做人工审计与重构
- 已完成 `standardset_v6_1234 -> checkpoint-61` 的测试集正式评测
  - eval run：`20260610_160737_eval_standardset_v6_1234_qwen3.5-0.8b_reference_v1_test_eval`
  - `avg_prediction_ratio = 0.7425`
  - `avg_char_f1 = 0.8039`
  - `avg_anchor_retention_rate = 0.8157`
  - `avg_strict_anchor_retention_rate = 0.9216`
  - `avg_soft_anchor_retention_rate = 0.8075`

## 2. 当前最重要的评测结论

旧版 `anchor retention` 规则过严，主要问题包括：

- 把反引号差异当作锚点丢失
- 把 URL 子串重复计数
- 把章节号、编号、纯数字与关键锚点混在一起

因此旧结论：

- `V1 anchor = 0.443`
- `V2 anchor = 0.321`

不能直接用于判断模型能力。

重构后，当前更可信的可比结果为：

- `V1`
  - `avg_prediction_ratio = 0.631`
  - `avg_char_f1 = 0.804`
  - `avg_strict_anchor_retention_rate = 0.667`
  - `avg_soft_anchor_retention_rate = 0.724`
- `V2`
  - `avg_prediction_ratio = 0.637`
  - `avg_char_f1 = 0.802`
  - `avg_strict_anchor_retention_rate = 0.667`
  - `avg_soft_anchor_retention_rate = 0.547`

当前可下的结论是：

1. `V2` 没有证明带来整体能力提升
2. `V2` 也没有把硬锚点能力训坏
3. `V1` 与 `V2` 在 `strict anchor` 上持平
4. 差异主要落在 `soft anchor`
5. 因此此前“V2 明显更差”的强结论不成立

## 3. 当前数据量判断

当前稳定基线 `185` 条、clean 工作版增量 `223` 条：

- 足够跑通 MVP
- 足够发现主要失败模式
- 不足以判断能力是否稳定
- 不足以支撑部署级能力结论

当前最新工作版数据集规模：

- `1234`

当前判断：

- 已超过原先 `800 ~ 1200` 的阶段目标
- 已足够作为第一版 `1k+` 标准集启动正式训练/评测
- 后续若继续扩源，更适合作为并行副线，而非阻塞当前 mainline
- 第一版正式训练与测试集评测均已完成，当前已从“可开训”进入“baseline 可收口”的阶段

## 4. 当前执行策略

当前不应：

- 继续只靠 `100~200` 条规模反复下结论
- 继续让人工对全量样本逐条重度复核
- 把 review queue 或决策脚本结果直接当成最终真值
- 把不同版本样本池上的 decision file 混用

当前应：

1. 将 `v6 standard-set` 与 `reference_v1 checkpoint-61` 固化为当前第一版 baseline
2. 用脚本做风险筛查、分层路由、抽样，不把脚本结果当真值
3. 后续扩源批次的 `P0/P1` 默认直接 defer，不再走 relabel 主路径
4. 人工主要守最终候选入库集，重点看原生 `P2` 中的长文本、强锚点与边界样本
5. 当前主任务切到 baseline 固化、对外叙事整理、HF 发布准备与 `headroom_zh` 接入准备
6. 已完成 case review 后，不再盲目重复同配方重训，也不再围绕这版做高频局部调优
7. 每次人工决策都与具体输入样本集版本绑定
8. 优先把 semantic drift 或 case 串位样本 defer，而不是为了凑量硬收

## 5. 当前新增工具

### `scripts/build_review_queue.py`

作用：

- 对 teacher 标注结果自动分级
- 生成 `P0/P1/P2` 复核队列
- 自动抽取一批人工审计样本

高风险信号包括：

- 长文本
- 压缩过猛
- 严格锚点疑似缺失
- 关键 cue 组疑似掉点

### `scripts/apply_manual_review_decisions.py`

作用：

- 将人工 accept / defer 决策落到正式数据链路
- 可单独产出 `accepted / deferred / pending / orphan_decision_ids`
- 支持严格模式，发现 `undecided` 或孤儿决策时阻断正式 merge

这一步的意义不是“自动决定样本质量”，而是确保：

- 人工判断真正进入数据集
- 决策文件与样本集版本不再静默错位

### `docs/DATASET_800_EXPANSION_SOP.md`

作用：

- 定义从 `185` 条扩到 `800 ~ 1200` 的批次化生产方案
- 明确长度分布、类型分布、人工复核策略和训练节奏

### `scripts/select_review_tier_subset.py`

作用：

- 从 review queue 中快速切出 `P0/P1/P2` 子集
- 便于直接构造 relabel 池或人工抽检池

### `scripts/select_promotable_relabeled_samples.py`

作用：

- 聚合多轮 relabel 结果
- 只接收稳定达到 `P2` 条件的样本
- 将反复不稳定的样本直接 defer

当前状态：

- 该工具保留，作为已验证过的旁路工具
- 但不再作为后续批次默认主路径

### `scripts/split_jsonl_shards.py`

作用：

- 将大批次 JSONL 均分为多个 shard
- 便于 teacher 并发标注与断点续跑

### `scripts/build_final_audit_sample.py`

作用：

- 从最终 keep pool 中抽取轻量人工审样本
- 优先覆盖 `relabel` 晋级样本、长文本和随机 `P2`
- 避免人工再回到全量逐条重审

## 6. 当前一句话总结

项目已完成从 MVP 验证到大漏斗扩量生产、`1k+` 标准集收束，再到第一版正式训练/测试集评测的过渡：主线、评测口径、source pool 扩展、session 来源接入、分层复核与人工决策落库链路均已建立；两组 `500` 主批次与一组 `targeted400` 定向补洞批次已完成正式 merge，当前 `1234` 条 `v6 standard-set` 已完成首轮 AutoDL 训练与测试集评测。当前模型已可视为第一版可用 `kompress_zh` baseline，虽然压缩力度仍偏保守，但不再作为当前阶段持续细抠对象；主线已切到 baseline 固化、开源叙事与后续接入准备。
