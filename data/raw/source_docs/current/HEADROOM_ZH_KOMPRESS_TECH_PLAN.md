# 中文版 Kompress 技术方案（第一版）

## 1. 目标定义

我们要做的不是中文摘要模型，也不是中文改写模型，而是一个面向 Agent 场景的 **中文自然语言抽取式压缩器**：

- 输入：中文 plain text 上下文
- 输出：原文中的一部分内容
- 约束：尽量保留关键信息，尽量减少 token，占用更短上下文
- 形式：**只能抽取原文字符/片段，不自由改写**

这与 Headroom 原版 Kompress 的核心思想保持一致。

## 2. 任务建模

### 2.1 不做生成式改写

第一版不建议直接做生成式压缩，原因很简单：

- 标签难控
- 信息保真难评测
- 部署成本更高
- 很容易“压缩是压了，但意思变了”

所以第一版应继续采用 **token / span 选择** 的建模方式。

### 2.2 中文不建议沿用“按英文单词抽取”

英文版是按 word 级抽取，因为英文天然有空格。  
中文没有这个优势，所以第一版不建议依赖中文分词器做人为切词后再监督。

更稳妥的方案是：

- **监督单位：字符级**
- **输出约束：连续片段级**

也就是：

- 标注时让教师模型从原文中直接抽取“原句片段”
- 对齐时映射回原文字符位置
- 训练时做字符级保留/丢弃分类
- 推理后再把连续保留字符拼成片段输出

这样做的好处是：

- 不依赖中文分词质量
- 更容易对齐标签
- 更适合中文、标点、数字、英文混合文本

## 3. 数据与标签方案

## 3.1 我们需要什么数据

目标数据不是“数学题推理数据”，而是 **中文 Agent/上下文压缩数据**。  
第一版建议覆盖下面几类：

- 助手回答、计划、说明文字
- 用户需求描述
- 工具输出解释性文本
- 报错分析与排查步骤
- 文档段落、README、issue、PR 讨论

如果后续要接入 Codex / Claude Code，这些场景比单纯数学题更贴近产品落地。

## 3.2 标签如何做

标签生成建议严格模仿原版 Headroom 的做法：

- 用大模型做教师标注
- 但提示词必须要求 **只保留原文中的字符或片段**
- 不允许改写
- 不允许同义替换
- 不允许重排顺序

可执行的一句话原则：

“请像荧光笔一样，从原文中只选出必须保留的片段，输出顺序保持不变，不得改写。”

后处理时做两步：

1. 将教师输出和原文做严格对齐
2. 转成字符级 `keep/drop` 标签

## 3.3 样本规模建议

第一版可按三阶段推进：

- `5k`：验证训练与推理链路
- `20k~50k`：做第一版可用模型
- `100k+`：再考虑蒸馏、小模型化、正式集成

## 4. 基座模型建议

## 4.1 第一版推荐路线

第一版建议优先选 **稳定、轻量、容易微调** 的中文 encoder，而不是一上来追求最强。

推荐优先级：

1. `hfl/chinese-roberta-wwm-ext`
2. `google-bert/bert-base-chinese`
3. `BAAI/bge-m3` 作为后续长上下文升级路线

## 4.2 为什么这样选

`hfl/chinese-roberta-wwm-ext` 与 `bert-base-chinese` 的优点：

- 中文基础能力稳定
- 生态成熟
- token classification 改造成本低
- 本地推理与导出 ONNX 都更现实

`BAAI/bge-m3` 的优点：

- 官方模型卡显示支持 `8192` 上下文
- 多语种能力更强
- 对未来处理中英混合文本更有潜力

但它更重，第一版不适合直接拿来赌工程速度。

## 4.3 结论

建议：

- **MVP / v0.1**：`hfl/chinese-roberta-wwm-ext`
- **v0.2 升级**：尝试 `bge-m3`

这个顺序更稳。

## 5. 模型结构建议

建议继续沿用原版 Kompress 的思路：

- encoder
- token classification head
- span importance head

中文版无需一开始就大改结构。  
最小可行做法就是：

- 保留原双头思路
- 只是把“word 聚合”改成“char / span 聚合”

如果第一版效果不够，再考虑：

- span head 增强
- CRF / chunk-level decoding
- 蒸馏小模型

## 6. 训练流程建议

第一版训练流程：

1. 收集中文上下文原文
2. 用教师大模型生成严格抽取式压缩结果
3. 做字符位置对齐，生成 `keep/drop` 标签
4. 微调 encoder + token/span heads
5. 导出 PyTorch 与 ONNX
6. 接入 Headroom 路由器做真实压缩测试

损失函数建议：

- 主损失：token classification CE
- 辅助损失：span importance BCE / regression

如果后续做小模型蒸馏，再加：

- teacher-student KL

## 7. 评测指标建议

不能只看压缩率，至少看四类指标：

- 压缩率：保留了多少字符 / token
- 信息保真：教师或评审模型判断关键信息是否丢失
- 下游可用性：压缩后送入大模型，任务结果是否下降
- 延迟与部署：本地 CPU / ONNX 推理速度

第一版最重要的是第三项。  
如果压缩率很好，但压完之后下游任务质量明显下降，这个模型就不能用。

## 8. 与 Headroom 的集成方式

我们不改 Headroom 的主路线，只新增中文自然语言压缩分支。

建议路由：

- `code/json/log/diff`：继续走原压缩器
- `English plain text`：继续走原版 Kompress
- `Chinese plain text`：走我们新模型
- `mixed text`：第一版先用启发式规则决定走哪边

第一版启发式足够：

- 中文字符占比高：走中文 Kompress
- 代码符号 / JSON 特征明显：走原结构化压缩器
- 英文占比高：走原版英文 Kompress

## 9. 首轮最小可行版本

如果要尽快跑通，建议直接按下面执行：

1. 基座定为 `hfl/chinese-roberta-wwm-ext`
2. 只做中文 plain text 压缩
3. 标签采用严格抽取式，不允许改写
4. 监督单位采用字符级对齐
5. 先做 `5k` 样本验证链路
6. 先导出 PyTorch，链路通了再补 ONNX

这条路线的优点是：

- 训练快
- 风险低
- 容易判断问题出在数据、模型还是集成

## 10. 当前不建议做的事

第一版不建议：

- 一开始就做生成式压缩
- 一开始就追求中英混合统一模型
- 一开始就追求插件化完整产品
- 一开始就上超大中文 encoder
- 一开始就做复杂 reranker / RL 优化

这些都应该在第一版能用之后再说。

## 参考资料

- Headroom README: https://github.com/chopratejas/headroom
- Kompress Base: https://huggingface.co/chopratejas/kompress-base
- Kompress Small: https://huggingface.co/chopratejas/kompress-small
- `hfl/chinese-roberta-wwm-ext`: https://huggingface.co/hfl/chinese-roberta-wwm-ext
- `google-bert/bert-base-chinese`: https://huggingface.co/google-bert/bert-base-chinese
- `BAAI/bge-m3`: https://huggingface.co/BAAI/bge-m3
