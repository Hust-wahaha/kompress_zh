# 代码助手场景数据集调研结论

## 1. 结论先说

你的怀疑基本是对的：

**在“代码助手 / Agent 上下文压缩”这个具体场景下，直接可用的中文开源数据集几乎没有。**

更准确地说：

- 有不少开源的代码助手轨迹数据
- 有一些与提示词、PR、issue、代码变更相关的数据
- 但**没有发现一个成熟的、专门面向中文代码助手上下文压缩的小模型训练集**

所以我们大概率不能指望“找到现成中文数据集直接开训”，而是要：

**用开源英文/多语种 agent 数据作原料，自己蒸馏出中文压缩监督数据。**

## 2. 为什么说“几乎没有”

## 2.1 真正像样的代码助手轨迹集，主流仍然是英文

目前最有代表性的真实 coding-agent 轨迹数据之一是 `SWE-chat`：

- 含完整会话转录、tool calls、thinking traces、代码改动
- 来自真实开发者使用 Claude Code、Codex、Gemini CLI 等的会话

但它的定位是 **real-world coding agent sessions**，不是中文压缩数据集。  
即使数据卡里出现多语言标签，也不能等价理解为“有一套高质量中文代码助手压缩语料”。

## 2.2 公开的 agent / software engineering 轨迹集，大多不是中文优先

例如：

- `nvidia/SWE-Hero-openhands-trajectories`
- `OpenHands` 相关 trajectories / feedback
- `cx-cmu/agent_trajectories`

这些数据对我们很有参考价值，但核心用途更接近：

- agent 行为训练
- tool-use 研究
- software engineering benchmark

而不是“中文 plain-text compression”。

## 2.3 代码语境中“中文部分”本来就不是主体

即使面对中文开发者，真实上下文里 token 大头通常还是：

- code
- diff
- logs
- stack traces
- issue/PR 模板化英文文本

所以开源社区天然更容易积累：

- 代码轨迹数据
- 英文 agent 数据

而不是“专门的中文自然语言上下文压缩语料”。

## 3. 目前可利用的数据原料有哪些

虽然没有现成目标数据集，但有几类数据值得拿来做“中文压缩蒸馏原料”。

## 3.1 真实代码助手轨迹

### SWE-chat

价值：

- 最接近真实 coding-agent 交互
- 有完整 transcript、tool calls、thinking、code changes

局限：

- 不是为压缩任务构造的
- 中文比例未知且不一定高
- 数据访问有条件限制

### OpenHands / SWE-Hero trajectories

价值：

- 结构化程度高
- 有较完整轨迹
- 能拿来抽取“用户意图 + 助手规划 + 工具观察”片段

局限：

- 更多是 agent 训练数据
- 中文覆盖仍然不是主轴

## 3.2 开发者提示词数据

### PromptSet

这是一个程序员 prompt 数据集，收集了开源 Python 项目中的提示词。

价值：

- 能提供真实开发场景 prompt 模板
- 可帮助我们理解“哪些文本值得压缩”

局限：

- 不是会话轨迹
- 不是中文优先
- 没有压缩标签

## 3.3 GitHub issue / PR 对话数据

### CodeAssistBench (CAB)

它包含 annotated GitHub issue dialogues 与 satisfaction conditions。

价值：

- 很适合拿来构造“需求描述 / 问题上下文 / 成功条件”这类文本
- 这些文本恰好是我们最想压缩的自然语言部分

局限：

- 仍不是中文优先
- 不是直接的压缩标签数据

## 4. 对我们最现实的判断

如果我们的目标是做：

- 中文
- 代码助手 / Agent 场景
- plain-text compressor

那么最现实的路线不是“找一个现成中文开源数据集”，而是下面这条：

1. 从开放的 coding-agent / issue / prompt 数据中抽取自然语言上下文
2. 过滤掉 code / JSON / logs / diff 等本就该交给 Headroom 原压缩器的内容
3. 只保留需要中文压缩器处理的 **自然语言片段**
4. 用大模型把这些内容改写/翻译/扩展成中文开发语境文本
5. 再生成严格抽取式压缩标签

也就是说，我们真正要造的不是“原始数据”，而是：

**中文代码助手自然语言压缩蒸馏集。**

## 5. 数据路线建议

建议分三层数据源：

### 第一层：真实英文/多语种代码助手原料

- `SWE-chat`
- `SWE-Hero-openhands-trajectories`
- `OpenHands` trajectories / feedback
- `cx-cmu/agent_trajectories`

作用：

- 提供真实 agent 语境

### 第二层：开发者自然语言文本原料

- `PromptSet`
- `CodeAssistBench`
- GitHub issue / PR 文本数据

作用：

- 提供更集中的自然语言开发场景表达

### 第三层：我们自己构造的中文蒸馏数据

作用：

- 补足“中文 + 压缩标签 + 代码助手语境”这个公开数据缺口

## 6. 当前结论对项目的直接影响

这轮调研说明了一件很关键的事：

**我们后续数据工作的重点，不该是“找现成中文数据集”，而该是“设计一套高质量的数据构造流程”。**

这反而和我们现在项目的定位一致：

- 不是拿一个公开中文数据集直接训
- 而是利用开放 agent 数据与开发者语料，蒸馏出一个中文代码助手压缩数据集

## 参考链接

- SWE-chat: https://huggingface.co/datasets/SALT-NLP/SWE-chat
- SWE-chat 站点: https://www.swe-chat.com/
- SWE-Hero OpenHands trajectories: https://huggingface.co/datasets/nvidia/SWE-Hero-openhands-trajectories
- OpenHands datasets: https://huggingface.co/OpenHands/datasets
- agent_trajectories: https://huggingface.co/datasets/cx-cmu/agent_trajectories
- PromptSet: https://huggingface.co/datasets/pisterlabs/promptset
- CodeAssistBench: https://huggingface.co/datasets/codingsoo/CAB
