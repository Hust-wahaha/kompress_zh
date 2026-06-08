# 为什么一直没有成熟的中文版 Kompress

## 1. 结论先说

我现在的判断是：

**这个缺口长期存在，不是因为“中文压缩没价值”，而是因为它同时卡在了数据、建模、评测、产品激励四个地方。**

更直白一点：

- 不是没人知道 prompt compression 有用
- 而是“做一个中文可用的小压缩模型”这件事，短期商业回报没有那么直接
- 同时工程和评测又比英文更麻烦

所以这个方向就一直没有被卷到“成熟开源产品”那一步。

## 2. 英文先起量，是因为训练资源和公开数据先在那里

目前最有代表性的两条公开路线，本质上都明显偏英文：

- `Kompress` 模型卡明确写了 `English only`
- `LLMLingua-2` 公开的小模型虽然用了 multilingual base，但其公开训练数据 `MeetingBank-LLMCompressed` 的数据卡明确写了 `Languages: English`

这说明至少在公开开源层面，主流 prompt compression 训练资源首先是围绕英文建立起来的。

这会带来连锁反应：

- 数据蒸馏流程先在英文上成熟
- 标签对齐工具先按英文 token / word 设计
- benchmark 也先围绕英文任务建设

于是后来的团队自然继续沿着英文做，而不是额外为中文重打一套地基。

## 3. 中文比英文更难做“抽取式压缩”

`Kompress` 的关键成功点是：**严格抽取式压缩**。  
但中文在这里天生更难。

原因不是中文不能压，而是中文没有英文那种天然空格边界：

- 英文可以比较自然地按 word 做抽取与恢复
- 中文如果按字做，标签更细碎
- 如果按词做，又依赖分词器，容易引入对齐误差

再加上 tokenizer 对不同语言并不公平。  
相关研究指出，不同语言在 tokenization 成本上存在系统性差异，这种不均衡会影响训练与推理成本分布。

这意味着中文压缩模型要处理的不只是“删什么”，还包括：

- 用什么粒度监督
- 怎么做稳定对齐
- 怎么避免压缩后语义断裂

这些都比英文 word-level extractive compression 更麻烦。

## 4. 现有替代方案削弱了做专门中文压缩器的紧迫性

过去一年，很多平台直接给了另外两条降本路线：

- **更长上下文**
- **Prompt Caching**

例如 OpenAI 官方文档已经把 Prompt Caching 做成平台能力，并明确说明它可以自动降低延迟和输入成本。

这会改变很多团队的优先级：

- 如果我能直接用更长上下文模型
- 或者通过 cache 折扣先省一大截

那我未必会优先投入资源去训练一个专门的中文压缩器。

换句话说，中文压缩器不是“没必要”，而是它常常排不到最前面的工程优先级。

## 5. 真正强需求的场景，很多原始内容本来就不是中文

我们现在受到 Headroom 启发，很自然会想到 Agent / 编码场景。  
但这类场景里大量上下文本来就是：

- code
- JSON
- logs
- diff
- search results
- 英文报错

这类内容 Headroom 已经可以通过结构化压缩器或英文 `Kompress` 处理很大一部分。  
也就是说，很多团队即使服务中文用户，真正占 token 大头的内容也不一定是中文自然语言。

所以“专门为中文 plain text 再训一个模型”的商业吸引力，没有想象中那么立刻。

## 6. 缺少公认的中文评测基准，导致很难证明价值

一个压缩模型要成立，至少要证明三件事：

- 压缩率
- 信息保真
- 下游任务质量不明显下降

英文 prompt compression 之所以更容易推进，是因为：

- 已有英文数据蒸馏集
- 已有英文 benchmark
- 已有英文工具链

而中文这边目前缺的恰恰是“统一评测口径”。  
没有统一 benchmark，就很难回答：

- 压缩后到底保留了多少关键信息？
- 对问答、RAG、Agent、代码助手分别影响多大？
- 是真的省钱，还是只是把问题藏起来？

这让很多团队宁愿继续用通用大模型和缓存机制，而不是押一个中文小压缩器。

## 7. 这不代表这个方向没价值，恰恰说明它有切入口

正因为现在没有成熟中文产品，反而说明这个切口是成立的。  
但前提是我们要把定位说准：

不是“发明 prompt compression”

而是：

**把已经在英文世界被验证有效的上下文压缩方法，迁移并产品化到中文自然语言 Agent 场景。**

## 8. 我们最应该吸取的判断

这个缺口存在的核心原因，不是单点技术不行，而是下面四点叠加：

1. 英文数据和开源训练资源先成熟
2. 中文抽取式压缩的标签对齐更难
3. 长上下文和缓存先吃掉了一部分需求
4. 中文缺少公认 benchmark，导致价值不容易被证明

## 参考资料

- Kompress Small 模型卡: https://huggingface.co/chopratejas/kompress-small
- Kompress Base 模型卡: https://huggingface.co/chopratejas/kompress-base
- LLMLingua README: https://github.com/microsoft/LLMLingua
- LLMLingua-2 多语种模型卡: https://huggingface.co/microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank
- MeetingBank-LLMCompressed 数据卡: https://huggingface.co/datasets/microsoft/MeetingBank-LLMCompressed
- Prompt Compression Survey: https://aclanthology.org/2025.naacl-long.368.pdf
- OpenAI Prompt Caching 文档: https://platform.openai.com/docs/guides/prompt-caching
- Language Model Tokenizers Introduce Unfairness Between Languages: https://openreview.net/pdf?id=Pj4YYuxTq9
