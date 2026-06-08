# 中文 Kompress 数据集构造方案（第一版）

## 1. 目标

第一版数据集要服务的不是“中文代码压缩”，而是：

**中文 Agent 自然语言上下文压缩**

也就是压缩下面这些文本：

- 中文任务描述
- 中文背景与约束
- 中文 issue / review / PR 讨论
- 中文文档说明
- 中文结果解释与交付文本

不作为中文压缩主样本的内容：

- 代码
- JSON / YAML / TOML
- shell 命令
- logs / stack traces
- diff / patch

这些内容继续交给 Headroom 原有结构化压缩器。

## 2. 样本单元定义

第一版不要直接拿“整段 session”做样本，而要抽取 **自然语言片段单元**。

推荐 6 类样本单元：

1. `task_brief`
   用户任务描述、需求、约束、验收标准

2. `issue_context`
   issue / bug 报告 / 复现步骤 / 环境说明

3. `review_discussion`
   PR 评论、review 建议、设计讨论

4. `doc_chunk`
   README、规范、配置说明、课程要求、实验说明

5. `result_explainer`
   对日志、报错、测试结果的中文解释与归纳

6. `delivery_text`
   最终交付文本，如 PR 摘要、变更说明、实验结论

## 3. 原料来源

## 3.1 第一层：真实 agent / software engineering 轨迹

### SWE-chat

数据卡说明它是逐 turn 存储的真实 coding-agent 会话；一行可对应 user prompt、assistant response、assistant thinking、tool call 或 metadata event，包含 `content` 与 `transcript_path` 等字段。

用途：

- 抽用户任务描述
- 抽助手解释性回复
- 抽与工具结果相邻的自然语言解释段

不直接拿来做样本的部分：

- tool input JSON
- tool result 原文
- 长代码块

### SWE-Hero OpenHands Trajectories

数据卡公开了 `trajectory_id` 等结构化字段，定位是 software engineering agent 轨迹。

用途：

- 提供更结构化的 agent 交互原料
- 方便抽取任务描述、计划说明、观察总结

## 3.2 第二层：开发者沟通与需求文本

### CodeAssistBench (CAB)

数据卡说明它包含：

- GitHub issue threads
- multi-turn Q&A conversations
- `user_satisfaction_condition`

这非常适合构造：

- issue_context
- review_discussion
- task_brief

### PromptSet

可作为程序员 prompt 模板与开发者表达方式原料。

用途：

- 学习真实开发语境里的自然语言任务表达
- 补充 task_brief 风格样本

## 3.3 第三层：我们自己项目与中文软件工程文本

这一层很重要，因为公开数据很难天然覆盖中文团队协作表达。

建议补充：

- 中文课程设计需求
- 中文项目 README / 规范 / 实验记录
- 中文 issue / PR 讨论
- 中文周报、同步记录、交付说明

注意：

- 如果涉及私有仓库或个人信息，必须脱敏
- 不要把敏感路径、密钥、账号、隐私文本直接放进训练集

## 4. 数据构造总流程

第一版建议按 6 步走。

### 第一步：抽取自然语言候选片段

从原料里抽出候选段落，过滤掉明显不该进中文压缩器的内容。

过滤规则：

- 代码行占比过高则剔除
- JSON / XML / YAML 特征明显则剔除
- 连续日志格式占比过高则剔除
- 文件路径、命令、堆栈主导则剔除

保留规则：

- 自然语言句子占比高
- 含任务、约束、背景、讨论、解释、结论

### 第二步：按样本类型归类

给每个候选片段打 `sample_type`：

- `task_brief`
- `issue_context`
- `review_discussion`
- `doc_chunk`
- `result_explainer`
- `delivery_text`

### 第三步：中文化

公开原料大概率以英文为主，所以需要做一层中文化。

第一版建议不是机械翻译，而是：

- 保留原始语义与约束
- 转成自然的中文开发者表达
- 保留必要的英文术语、函数名、库名、报错名

中文化的目标不是“纯中文化”，而是：

**生成真实中文团队会写出来的自然语言上下文。**

例如：

- 英文 issue 描述 -> 中文 bug 说明
- 英文任务要求 -> 中文开发任务描述
- 英文 review comment -> 中文 review 建议

### 第四步：生成严格抽取式压缩标签

教师模型只做一件事：

**从中文原文中抽取必须保留的片段，顺序不变，不得改写。**

标签原则：

- 只能输出原文中已有字符或片段
- 不允许同义改写
- 不允许总结式重写
- 不允许增补原文没有的信息

### 第五步：字符级对齐

由于中文没有天然 word boundary，第一版建议：

- 用字符级位置对齐
- 生成每个字符的 `keep/drop` 标签
- 额外保留连续 span 边界

### 第六步：人工抽检与质量过滤

每一批数据至少检查：

- 中文化是否自然
- 压缩标签是否严格抽取式
- 是否丢失关键约束
- 是否保留了必要数字、文件名、变量名、版本信息

## 5. 数据 schema

建议用 JSONL，一行一个样本。  
字段分成必填和选填。

## 5.1 必填字段

- `sample_id`
  全局唯一 ID

- `dataset_version`
  数据集版本，如 `zh_kompress_v0_1`

- `sample_type`
  样本类型，取值见上文 6 类

- `source_family`
  原料来源大类，如 `swe_chat`、`cab`、`promptset`、`local_project`

- `source_ref`
  原始样本引用，如 transcript 路径、issue id、文件名、记录 id

- `language`
  第一版固定写 `zh`

- `text_original`
  中文原文

- `text_compressed_extractive`
  教师输出的抽取式压缩结果

- `char_labels`
  与 `text_original` 对齐的 0/1 标签序列

- `quality_status`
  例如 `auto_pass`、`manual_pass`、`rejected`

## 5.2 选填字段

- `text_source_raw`
  中文化前原文

- `text_source_lang`
  原始语言，如 `en`

- `compression_ratio_char`
  字符级压缩率

- `contains_code_token`
  是否混有代码符号

- `contains_path_or_cmd`
  是否含路径或命令

- `critical_spans`
  必须保留的关键信息片段，如版本号、文件名、数值条件

- `teacher_model`
  生成压缩标签所用教师模型

- `translator_model`
  中文化所用模型

- `notes`
  备注

## 6. 数据质量红线

出现下面任一情况，应直接过滤或退回重做：

- 压缩结果包含原文没有的字词
- 丢失任务约束或验收条件
- 丢失关键数字、版本号、文件路径、函数名
- 中文化后表达不自然，像机翻
- 样本主体其实是代码 / 日志 / JSON

## 7. 第一版规模建议

第一版不要贪大，建议：

- `1k`：打通全流程
- `5k`：训练第一版 MVP
- `20k+`：再做正式版本

样本分布建议尽量均衡：

- `task_brief`
- `issue_context`
- `review_discussion`
- `doc_chunk`
- `result_explainer`
- `delivery_text`

不要让某一类样本过多主导风格。

## 8. 训练前最小验证集

在 full dataset 前，先固定一份 `200~300` 条人工高质量验证集，要求：

- 六类样本都有
- 每条都有人工复核
- 用于检查：
  - 压缩率
  - 关键信息保留
  - 下游大模型任务质量变化

## 9. 版本管理建议

数据版本命名建议：

- `zh_kompress_v0_1_seed1k`
- `zh_kompress_v0_2_mixed5k`
- `zh_kompress_v0_3_agent20k`

并额外记录：

- 原料来源比例
- 中文化模型版本
- 教师标注模型版本
- 过滤规则版本

## 10. 当前最推荐的执行顺序

建议按下面顺序开工：

1. 先从 `SWE-chat + CAB + 本地中文项目文档` 抽样
2. 只做 `task_brief / issue_context / doc_chunk / result_explainer` 四类
3. 先做 `1k` 条
4. 先把中文化与抽取式标注流程跑通
5. 验证可用后，再扩到 `review_discussion / delivery_text`

这样最稳，且最容易定位问题。

## 参考链接

- SWE-chat 数据卡: https://huggingface.co/datasets/SALT-NLP/SWE-chat
- SWE-Hero OpenHands Trajectories: https://huggingface.co/datasets/nvidia/SWE-Hero-openhands-trajectories
- CodeAssistBench: https://huggingface.co/datasets/codingsoo/CAB
- PromptSet: https://huggingface.co/datasets/pisterlabs/promptset
- OpenAI Codex CLI Getting Started: https://help.openai.com/en/articles/11096431
- Claude Code Overview: https://docs.anthropic.com/en/docs/claude-code/overview
