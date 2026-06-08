# 中文版 Kompress 相关项目调研结论

## 1. 结论先说

**没有发现一个已经成熟开源、且与我们目标高度等价的“中文版 Headroom/Kompress”。**

更准确地说：

- 已有很多“提示词压缩 / 上下文压缩”工作
- 也有部分项目支持多语种，甚至标了中文
- 但**没有看到一个已经成型的、面向 Agent 场景、可本地部署、专做中文自然语言抽取式压缩、并且能像 Headroom 一样直接接入代理链路的现成轮子**

所以我们不是在“从零发明 prompt compression”，但也**不是简单重复一个现成中文版产品**。

## 2. 最值得关注的现有轮子

## 2.1 Headroom + Kompress

这是我们当前最该复用的底座。

- Headroom 已经把代理层、路由层、结构化压缩、CCR、CLI/Proxy/MCP 都做好了
- 原版 `kompress-small` 模型卡明确写了 `English only`
- 原版 `kompress-base` 也是英文路线

结论：

- **产品基础设施直接复用**
- **中文 plain-text compressor 仍然要自己补**

## 2.2 LLMLingua / LLMLingua-2

这是最接近“现成方法学轮子”的项目。

它不是 Headroom 那种完整代理产品，但它在“如何训练一个 prompt compressor”这件事上很有参考价值：

- 有公开代码仓库
- 有公开论文
- 有公开数据集
- 有公开 token classification 模型

尤其关键的是，微软公开了一个 **多语种 token classification 模型**：

- `microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank`

模型卡显示：

- 基座是 `bert-base-multilingual-cased`
- 任务是 `token classification`
- 目标是 `task agnostic prompt compression`

但它的问题也很明显：

- 训练数据来自 `MeetingBank-LLMCompressed`
- 该数据集卡明确标注语言为 **English**
- 也就是“多语种底座 + 英文压缩数据”，并不是面向中文场景专门做的压缩器

结论：

- **这不是我们最终想要的中文版 Kompress**
- 但它是一个非常强的 baseline / 方法学参考

## 2.3 Caveman Compression

这个项目有一定启发，但不属于我们要做的主线。

它提供三类方案：

- LLM-based
- MLM-based
- NLP-based

其中 README 明确写到 NLP 方案支持 `zh`。  
但它的中文支持更像 **规则/模板层面的多语种适配**，不是一个中文压缩模型产品。

结论：

- 可借鉴“轻量规则压缩”思路
- 不是我们要找的中文 Kompress 轮子

## 3. 有研究价值，但不等价于我们目标的项目

## 3.1 Sentinel

`Sentinel` 模型卡标了 `English` 和 `Chinese`，但它做的是：

- 从小代理模型抽 attention 特征
- 再用逻辑回归做 sentence-level relevance 选择

它更偏 **轻量上下文筛选框架**，不是 Headroom 这种产品化文本压缩器。

## 3.2 Semi-Dynamic Soft Context Compression

`qwen3-semi-dynamic-soft-context-compress` 也标了 `English` / `Chinese`，但它压缩的是：

- 长文档到 latent tokens
- 再注入 decoder

这是 **soft context compression / latent compression** 路线，不是抽取式文本压缩。

它和我们现在的目标不一样：

- 更重
- 更偏研究模型
- 不适合直接替换 Headroom 里的 plain-text compressor

## 3.3 RCC / Glyph

这些都属于“长上下文压缩”的更广义研究：

- `RCC`：递归压缩上下文状态
- `Glyph`：把文本渲染成图像再交给 VLM

都很有意思，但都不是我们这个课设当前最该走的工程路线。

## 4. 我们到底算不算重复造轮子

要分两层看。

### 4.1 在“研究方向”层面

算部分重复。

因为：

- Prompt compression 这个方向早就有人做
- Token classification / extractive compression 也不是我们首创
- LLMLingua-2 已经把“蒸馏式压缩监督 + token 分类”做得很清楚

### 4.2 在“中文版 Headroom 可用产品”层面

**不算明显重复。**

因为目前没有看到一个现成开源项目同时满足下面这几条：

- 中文自然语言压缩
- 本地轻量模型
- Agent 场景
- 可插入 Headroom / Claude Code / Codex 类链路
- 以中文信息保真为目标

所以我们更准确的定位应该是：

**复用 Headroom 的系统壳子，复用 LLMLingua-2 / Kompress 的方法学，但补一个目前市场上还缺的“中文 plain-text compressor”。**

## 5. 对我们最有价值的直接启发

建议直接借这三样：

1. **Headroom**
   直接复用基础设施和路由框架。

2. **Kompress**
   借它的产品落地方式与抽取式模型形态。

3. **LLMLingua-2**
   借它的数据蒸馏、二值标签、token classification 训练路线。

## 6. 当前最稳的项目判断

如果我们现在去做：

- `fork Headroom`
- 保留原有 code / JSON / logs 压缩器
- 保留英文 `Kompress`
- 只新增一个中文 plain-text compressor

那么这件事是有明确价值的，不是低水平重复。

但也要实事求是：

- 我们不是第一个做“prompt/context compression”的
- 我们真正的创新点，应该表述为  
  **“把 Headroom 风格的本地上下文压缩能力扩展到中文自然语言场景，并验证其在 Agent 输入压缩中的效果与成本收益。”**

## 参考链接

- Headroom: https://github.com/chopratejas/headroom
- Kompress Small: https://huggingface.co/chopratejas/kompress-small
- LLMLingua: https://github.com/microsoft/LLMLingua
- LLMLingua-2 多语种模型: https://huggingface.co/microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank
- MeetingBank-LLMCompressed: https://huggingface.co/datasets/microsoft/MeetingBank-LLMCompressed
- Caveman Compression: https://github.com/wilpel/caveman-compression
- Sentinel: https://huggingface.co/ReRaWo/Sentinel
- Semi-Dynamic Context Compress: https://huggingface.co/yuyijiong/qwen3-semi-dynamic-soft-context-compress
- RCC: https://huggingface.co/papers/2406.06110
- Glyph: https://github.com/thu-coai/Glyph
