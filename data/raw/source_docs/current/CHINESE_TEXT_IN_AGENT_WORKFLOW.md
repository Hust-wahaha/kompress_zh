# 中文在 Agent / 代码助手工作流中的出现位置

## 1. 结论先说

如果场景是 `Codex / Claude Code / OpenHands / Headroom` 这类泛代码 Agent，那么：

**中文真正集中出现的，不是代码本体，也不是工具原始输出，而是“任务意图层、协作沟通层、文档说明层、结果解释层”。**

换句话说，中文压缩器的目标不该是压整个会话，而该是压那些 **自然语言组织信息** 的部分。

## 2. 先把“不会是中文主战场”的部分排掉

这些内容通常不值得交给中文 plain-text compressor：

- 源代码
- JSON / YAML / TOML / XML
- shell 命令
- 编译报错原文
- stack trace
- 日志流
- diff / patch
- API 名、库名、文件路径、函数名

这些内容即便由中文用户触发，主体仍然大概率是英文、符号化文本或结构化文本。  
它们更适合复用 Headroom 原有的 code / JSON / logs / diff 压缩器。

## 3. 中文真正会出现在哪些地方

## 3.1 任务意图层

这是最稳定、最核心的中文来源。

中文用户在用 Codex / Claude Code 时，最常直接输入的是：

- 任务要求
- 背景说明
- 约束条件
- 成功标准
- 希望的输出形式

OpenAI 对 Codex 的说明里就明确提到，用户会贴入 `spec`、`docs`，让它搭脚手架、回答代码库问题、执行修改与测试。Anthropic 对 Claude Code 的说明也明确包含：解释代码库、修 bug、执行命令、创建提交和 PR。

这说明 Agent 的输入并不只是“写代码”，而是大量带上下文的自然语言任务描述。  
对于中文团队，这一层天然很可能是中文。

### 对数据集的意义

这一类文本应作为重点样本：

- 中文任务描述
- 中文需求约束
- 中文验收标准
- 中文项目背景

## 3.2 协作沟通层

这也是中文很重要的一层。

真实软件工程协作里，自然语言往往出现在：

- issue 描述
- PR 讨论
- code review 评论
- TODO / design discussion
- bug 复现步骤
- 团队同步记录

`CodeAssistBench (CAB)` 明确包含 annotated GitHub issue dialogues 与 satisfaction conditions。  
这说明“issue 对话 + 成功条件”本身就是代码助手的重要输入形态。

对于中文团队，这些内容完全可能是中文，或中英混合。

### 对数据集的意义

这一层适合采：

- 中文 issue / 需求描述
- 中文 review 意见
- 中文修复要求
- 中文 acceptance criteria

## 3.3 文档说明层

很多团队在真实使用中，会把文档直接贴给 Agent：

- README 片段
- 产品说明
- 接口文档
- 配置说明
- 课程/项目要求
- 实验记录

OpenAI 的使用案例里明确提到会贴 `spec and docs`；Claude Code 文档也强调可以处理代码库理解、PR、文档相关工作。

对于中文用户，这些文档很可能是中文，尤其是在：

- 课程设计
- 校园项目
- 国内团队内部系统
- 面向中文用户的产品

### 对数据集的意义

这一层非常适合做压缩样本，因为它：

- 长
- 冗余多
- 信息密度不稳定
- 但又经常必须保留关键约束

## 3.4 结果解释层

很多工具原始输出本身是英文，但用户和助手之间围绕这些输出的“解释文本”常常是中文。

例如：

- 用户贴一段英文报错，问“这是什么问题，怎么修”
- 用户贴测试失败结果，要求“你先分析根因，再给修复方案”
- 助手把英文日志总结成中文结论

这里真正可压缩的，不是报错原文，而是围绕报错的那层中文解释、判断、计划与结论。

### 对数据集的意义

这一层适合构造成：

- 英文工具输出 + 中文任务说明
- 英文报错 + 中文解释文本
- 中文诊断总结 + 中文修复计划

但训练中文 compressor 时，应优先压 **中文解释层**，而不是压英文原日志本体。

## 3.5 非代码任务层

你前面说得对，这些工具早已不只做“写代码”。

现实使用里还有很多任务本质是：

- 写 README
- 写实验报告
- 写 benchmark 分析
- 写 PPT 文案
- 整理周报
- 归纳 case study
- 把技术内容转成对外文档

这些任务中，自然语言占比很高，而且中文团队更可能直接用中文输入和输出。

### 对数据集的意义

如果我们只盯“代码修改”，会漏掉很大一类真实高频中文文本。  
这部分应该纳入第一版中文压缩数据源。

## 4. 用工作流来总结：中文主要在哪一层组织信息

可以把一次 Agent 使用拆成 4 层：

1. **自然语言任务层**  
   用户在中文里说明要做什么、为什么做、有哪些限制。

2. **结构化执行层**  
   Agent 调工具、读文件、跑命令、拿到日志、修改代码。

3. **自然语言解释层**  
   用户和 Agent 用中文讨论结果、筛选重点、决定下一步。

4. **自然语言交付层**  
   输出 PR 说明、文档、报告、总结、对外解释。

其中第 `1/3/4` 层，是中文压缩器真正应该关注的主战场。  
第 `2` 层大多不该由中文压缩器负责。

## 5. 对数据集构造的直接启发

这会直接改变我们采样单位。

第一版不建议把“整段 coding session 原样扔进去压缩”，而应优先抽取这些 **中文自然语言片段单元**：

- 任务描述段
- 背景约束段
- issue / review / PR 讨论段
- 中文文档段
- 中文结果解释段
- 中文交付文本段

不建议作为中文压缩主样本的内容：

- 大片代码
- 大片日志
- 大片 diff
- 纯结构化配置

## 6. 当前最重要的判断

所以数据问题的关键不只是“有没有中文”，而是：

**中文在 Agent 工作流里主要承担“组织意图、补充上下文、解释结果、形成交付”的职责。**

这意味着我们后续构造数据集时，应重点学习如何压缩：

- 约束
- 背景
- 需求
- 讨论
- 解释
- 交付文本

而不是执着于压缩代码本体。

## 参考资料

- OpenAI Codex CLI Getting Started: https://help.openai.com/en/articles/11096431
- How OpenAI uses Codex: https://openai.com/business/guides-and-resources/how-openai-uses-codex/
- Introducing Codex: https://openai.com/index/introducing-codex/
- Claude Code Overview: https://docs.anthropic.com/en/docs/claude-code/overview
- Claude Code Common Tasks: https://docs.anthropic.com/en/docs/claude-code/common-tasks
- SWE-chat 数据卡: https://huggingface.co/datasets/SALT-NLP/SWE-chat
- CodeAssistBench 数据卡: https://huggingface.co/datasets/codingsoo/CAB
