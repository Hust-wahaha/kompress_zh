# 中文 Kompress 两条实现路线对比

## 1. 问题定义

我们现在有两条主路线：

### 路线 A：从 Headroom / Kompress 改中文

- `fork Headroom`
- 保留原有代理层、路由层、结构化压缩器
- 新增一个中文 plain-text compressor
- 最终目标是做成“中文版 Headroom 文本压缩能力”

### 路线 B：从 LLMLingua-2 改造成可接 Headroom

- 直接复用 LLMLingua-2 的训练范式与代码
- 先做一个中文 prompt compressor
- 再想办法把它接入 Headroom 或自建轻量接入层

## 2. 两条路线的本质区别

路线 A 的核心是：

**先站在产品/系统壳子上，再补中文模型。**

路线 B 的核心是：

**先站在压缩模型训练框架上，再补系统接入。**

也就是说：

- A 更偏“产品化落地”
- B 更偏“训练与算法复用”

## 3. 路线 A 的优缺点

### 优点

1. 最符合我们现在的最终目标  
   我们已经明确不重造轮子，而是复用 Headroom 做一个中文版补丁。

2. 产品叙事最顺  
   很容易讲清楚：
   “我们在成熟上下文压缩框架上补齐中文自然语言压缩能力。”

3. 系统壳子现成  
   Headroom 已有：
   - CLI / wrap / proxy / MCP
   - 内容路由
   - code / JSON / logs / diff 压缩链路
   - 真实 Agent 使用场景

4. 最接近最终展示形态  
   如果课程设计最后要做“可用产品”，这条路线明显更像成品。

### 缺点

1. 训练脚手架没有 LLMLingua-2 那么直接  
   Headroom 原版公开出来的重点是产品与推理侧，不是完整中文训练脚本模板。

2. 中文模型训练部分需要自己补得更多  
   包括：
   - 数据 schema
   - 标注流程
   - 训练脚本适配
   - 推理接口

## 4. 路线 B 的优缺点

### 优点

1. 训练路线更清楚  
   LLMLingua README 和代码已经公开了：
   - 数据收集
   - GPT-4 压缩标注
   - `label_word.py`
   - `filter.py`
   - token classification 训练脚本

2. 更适合快速复现一个 baseline  
   如果目标只是“先训出一个中文压缩器”，LLMLingua-2 的训练路径更顺手。

3. 方法学更标准  
   论文、模型、数据集、训练说明都更完整，适合做学术叙述。

### 缺点

1. 离最终产品形态更远  
   LLMLingua 不是 Headroom 那种完整上下文压缩产品壳。

2. 后续仍然要做系统接入  
   即便模型训出来，也还要解决：
   - 怎么接 Agent
   - 怎么与结构化压缩器共存
   - 怎么做按内容路由

3. 它公开的现成多语种模型并不等于中文可用产品  
   `microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank`
   虽然是 multilingual base，但公开数据集 `MeetingBank-LLMCompressed` 的语言标签是 `English`。

## 5. 哪条更适合我们当前项目

如果只问“哪条更容易先训出一个压缩模型”，答案偏向 **路线 B**。  

如果问“哪条更适合我们整个项目当前阶段和最终交付”，答案明显是 **路线 A**。

原因很直接：

我们现在要的不是一篇单纯的压缩模型实验，而是：

- 有研究依据
- 有中文特色
- 能接到真实 Agent 场景
- 最后还能拿出一个产品化展示

这四条叠加后，路线 A 更合适。

## 6. 最稳的实际执行方式

最优解其实不是二选一，而是：

**产品走 A，训练方法借 B。**

也就是：

1. 系统与产品形态上：以 Headroom 为主线
2. 中文压缩模型训练上：借鉴 LLMLingua-2 的数据蒸馏与 token classification 流程
3. 训练出的中文模型最后接回 Headroom

这条路线的好处是：

- 不重造产品壳子
- 不重造训练方法
- 每一部分都站在现成轮子上

## 7. 推荐决策

当前建议明确如下：

- **主路线**：`Fork Headroom + 新增中文 plain-text compressor`
- **训练参考**：最大程度借鉴 LLMLingua-2 的数据构造和训练链路
- **不建议**：先独立重做一套 LLMLingua 风格产品，再考虑以后接 Headroom

## 8. 下一步怎么落地

按这个决策，下一步应拆成三件事：

1. 定中文数据 schema  
   明确原文、压缩结果、字符级标签、样本来源字段。

2. 定教师标注管线  
   用大模型生成“严格抽取式压缩”标签。

3. 定 Headroom 接入接口  
   先让中文 compressor 以最小接口替换原 plain-text 分支。

## 参考链接

- Headroom: https://github.com/chopratejas/headroom
- LLMLingua: https://github.com/microsoft/LLMLingua
- LLMLingua-2 多语种模型: https://huggingface.co/microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank
- MeetingBank-LLMCompressed: https://huggingface.co/datasets/microsoft/MeetingBank-LLMCompressed
