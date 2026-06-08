# Headroom 原版 Kompress 调研与中文迁移结论

## 1. 它到底是什么

Headroom 不是单一“压缩模型”，而是一整层 **上下文压缩基础设施**。它先判断输入内容类型，再路由到不同压缩器：

- `SmartCrusher`：压 JSON / 结构化对象
- `CodeCompressor`：压代码
- `Kompress`：压自然语言文本
- 另外还有日志、搜索结果、diff 等专门处理链路

所以 `Kompress` 在 Headroom 里只负责 **plain text / prose**，不是拿一个模型硬压所有内容。这一点非常关键，也是我们最值得继承的设计。

## 2. 原版 Kompress 是怎么做的

原版 `kompress-base` 本质是一个 **extractive token compressor**：

- 基座模型：`answerdotai/ModernBERT-base`
- 任务形式：对每个 token 做二分类，判断“保留 / 丢弃”
- 输出形式：不是改写，不是总结，而是从原文中**抽取原词**并保持原顺序

它还有一个双头结构：

- `token head`：逐 token 判断保留与否
- `span head`：用 1D CNN 学局部片段的重要性，避免只看单 token

这意味着它的目标不是“写得更好”，而是“尽量少删错关键信息”。

## 3. 它是怎么训练的

根据 `kompress-base / kompress-small` 模型卡，训练核心不是生成式 SFT，而是 **抽取式标注 + token classification**。

- 数据规模：约 `215K~263K` 条样本
- 数据来源：8 个英文数据集，覆盖聊天、新闻、长文档、会议、对话等
- 代表数据：`lmsys-chat-1m`、`cnn_dailymail`、`xsum`、`govreport`、`arxiv`、`meetingbank`、`samsum`
- 标注方式：用 `Claude Sonnet 4.6` 生成压缩标签

最关键的一点是：**标签必须严格抽取式**。

也就是只允许输出：

- 原文中的词
- 顺序不能变
- 不能自由改写

他们明确提到，早期如果让大模型“自由压缩 / 自由改写”，就会导致对齐失败，训练标签质量很差；后来改成“像荧光笔一样标出该保留的词”，标签质量才稳定下来。

## 4. 它做了哪些工程设计

原版方案不只是模型本身，工程上也做得很成熟：

- **按内容类型路由**，而不是 one-model-for-all
- **分块压缩**：按词切块，再做局部推理
- **双后端**：优先 ONNX，回退 PyTorch
- **CPU 优先可部署**：`kompress-small` 主打本地快速推理
- **可逆压缩 CCR**：压缩后原文仍保留，本体需要时可取回
- **与代理/CLI/Proxy/MCP 打通**：不是实验脚本，而是直接可接入 Claude Code / Codex 的运行链路

## 5. 它做了哪些调整

目前已确认的关键调整有两类：

### 5.1 模型层

- `kompress-base`：150M，主模型
- `kompress-small`：70M，从 `base` 蒸馏得到

`small` 保留了教师模型的压缩能力，同时显著提升速度，适合本地落地。

### 5.2 训练层

- `small` 不是重新做人标，而是直接复用同一批抽取式标签
- 用知识蒸馏训练 student
- 损失函数包含 hard label 的交叉熵，也包含 teacher 分布的 KL 项

这说明他们非常重视“压缩决策边界”的继承，而不只是追求更小参数量。

## 6. 对我们中文版最直接的启发

我们**不应该重做整个 Headroom**，而应该只替换其中的中文自然语言压缩器。

建议直接继承的部分：

- Headroom 整体框架
- 内容路由机制
- JSON / code / logs / diff 的原有压缩器
- extractive 标注思想
- token head + span head 的建模思路
- ONNX + PyTorch 双推理后端

必须改的部分：

- 英文基座模型要换成中文或中英双语 encoder
- 训练语料要换成中文 agent 场景文本
- 中文抽取标签要重新制作
- 路由器里要新增“中文 plain text”分支

## 7. 对我们产品定位的结论

我们后续最合理的产品形态不是“另起炉灶做一个新系统”，而是：

`Fork Headroom + 保留原结构化压缩链路 + 新增中文 Kompress`

建议的路由策略：

- 代码 / JSON / logs / diff：继续使用 Headroom 原方案
- 英文自然语言：继续使用原版英文 `Kompress`
- 中文自然语言：使用我们训练的中文 `Kompress`
- 中英混合文本：先做启发式切分，后续再优化

## 8. 当前最重要的研究判断

这个项目最值得借鉴的，不是某个 prompt，也不是某个 tricks，而是下面这条主线：

**把“文本压缩”建模成抽取式 token 选择问题，而不是生成式改写问题。**

这对我们做中文版非常重要，因为它意味着：

- 更容易做高质量监督
- 更容易评测信息保留
- 更容易控制长度
- 更容易部署成稳定的本地小模型

## 参考资料

- Headroom README: https://github.com/chopratejas/headroom
- Headroom Docs: https://headroom-docs.vercel.app/docs
- Kompress Base 模型卡: https://huggingface.co/chopratejas/kompress-base
- Kompress Small 模型卡: https://huggingface.co/chopratejas/kompress-small
