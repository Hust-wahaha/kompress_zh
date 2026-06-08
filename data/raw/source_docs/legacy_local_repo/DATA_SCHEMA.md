# 数据 Schema 说明

本文档用于明确三件事：

1. 哪些字段是所有数据都必须提供的
2. 哪些字段是特定任务下才需要提供的可选字段
3. `*_think` 字段应该如何统一命名，保证后续可以持续扩展

目标是降低数据构造门槛，避免做数据的同学把精力耗在一次性构造一个“大而全”的字段全集上。

## 一、Schema 分层原则

当前数据字段分成三层：

### 第一层：核心必填字段

这部分字段无论做什么数据集方向，都必须具备。

### 第二层：任务相关可选字段

这部分字段只在某类监督任务下需要提供。
例如：

- 做结构化思维监督时，需要 `structured_think`
- 做显式 think 监督时，需要某些 `*_think` 字段

### 第三层：训练展开字段

这部分字段不是原始对齐样本必须具备的，而是训练样本展开、视图扩展、格式渲染后新增的字段。

## 二、当前推荐的核心必填字段

下面这些字段建议作为所有“可进入主仓库的数据样本”的最低要求。

### `id` 必填

- 含义：样本主键
- 作用：唯一标识一条基础题目
- 示例：`give-000`

### `source` 必填

- 含义：样本来源标识
- 作用：标记数据来自哪个公开数据集、生成器或混合来源
- 示例：`synthetic-template-s800`

### `family` 必填

- 含义：题型类别
- 作用：用于分题型评测、采样均衡、错误分析
- 示例：`give_away`、`equal_division`

### `split` 必填

- 含义：数据划分
- 作用：标记 train / val / test
- 示例：`train`

### `answer` 必填

- 含义：标准最终答案
- 作用：训练目标中的最终答案字段，也是评测 gold answer
- 示例：`46`

### `modern_question` 必填

- 含义：白话题面
- 作用：白话输入视图
- 示例：`小明有52颗糖，送给小红6颗，还剩几颗？`

### `classical_question` 建议保留，主线任务中视作必备

- 含义：文言题面
- 作用：文言输入视图
- 示例：`明有糖52颗，遗红6颗，尚余几何？`

说明：

- 如果只是做单视图试验，可以先不提供 `classical_question`
- 但当前课设主线已经明确包含白话 / 文言对照，所以主仓库里的正式数据建议把它视作必备字段

### `question_fields` 最低要求

题面字段至少需要有一个稳定输入视图。当前主线建议直接同时保留：

- `modern_question`
- `classical_question`

## 三、当前推荐的任务相关可选字段

### 1. 结构化思维监督字段

#### `structured_think` 可选

- 含义：结构化风格的 think 文本
- 作用：用于结构化思维监督任务，强调紧凑、可校验、格式稳定
- 示例：`初有52颗，送出6颗，故52-6=46。`

说明：

- 当数据集要支持 `structuredthink` 监督任务时，这个字段必须存在
- 当数据集只服务于其他实验方向时，可以不提供

### 2. think 监督字段

#### 当前已有字段

- `modern_think`
- `classical_think`

它们的含义分别是：

##### `modern_think` 可选

- 含义：白话风格 think 文本
- 作用：显式监督白话输入下的思维过程
- 示例：`原来有52颗糖，送给小红6颗，所以用减法：52-6=46。`

##### `classical_think` 可选

- 含义：文言风格 think 文本
- 作用：显式监督文言输入下的思维过程
- 示例：`初有52颗，遗6颗，故52-6=46。`

说明：

- 当数据集要支持当前主线 think 监督时，这两个字段建议同时提供
- 如果某数据集只做单风格 think 实验，也可以只提供其中一个，但必须在元信息中说明

## 四、可扩展字段命名规范

这是最重要的部分。后续不应该把字段设计绑死在 `modern_think` / `classical_think` / `structured_think` 这三种上，而是做成可拓展字段族。

### 1. `*_think` 字段族

所有思维过程字段统一采用：

```text
{style}_think
```

其中 `style` 表示思维风格或方法标签。

当前例子：

- `modern_think`
- `classical_think`

未来可以自然扩展为：

- `compressed_think`
- `short_think`
- `keyword_think`
- `symbolic_think`
- `wenyan_think`
- `hybrid_think`

规则：

- 只要字段本质是在监督 `<think>` 内部内容，就统一命名为 `xxx_think`
- 不要再额外发明一套不一致命名
- `xxx` 必须表达“风格、压缩策略、表达策略或方法标签”

说明：

- 不再单独维护 `*_cot` 命名族
- 只要字段本质是在显式监督思维内容，无论它是否结构化、压缩化、文言化，都统一命名为 `xxx_think`

## 五、当前训练展开字段

这部分字段不是所有原始对齐样本都必须有，但训练展开后通常会出现。

### `base_id` 展开字段（可选但建议保留）

- 含义：对应的基础题目 id
- 作用：把多个视图记录关联回同一道题
- 示例：`give-000`

### `view` 展开字段（建议保留）

- 含义：当前训练记录使用的输入视图
- 作用：区分白话视图和文言视图
- 当前可选值：
  - `modern`
  - `classical`

### `dataset_variant` 展开字段（建议保留）

- 含义：当前样本属于哪种监督任务变体
- 作用：记录这是 visible-output 监督、think 监督还是其他训练变体
- 当前可选值：
  - `visible`
  - `think`

说明：

- 后续如果新增其他训练变体，可以继续扩展
- 例如：
  - `shortthink`
  - `compressedthink`
  - `structured`

### `think_style` 展开字段（可选但建议保留）

- 含义：记录 `<think>` 内实际采用哪种风格策略
- 当前可选值：
  - `by_view`
  - `structured`

说明：

- 这是训练样本层追溯字段，不是最低必填字段
- 但如果一个数据集有多种 think 生成策略，建议保留

### `messages` 展开字段

- 含义：直接送入训练模板的对话格式数据
- 作用：训练入口直接读取
- 当前固定三轮：
  - `system`
  - `user`
  - `assistant`

## 六、`messages` 内部字段

### `role`

- 含义：消息角色
- 当前固定使用：
  - `system`
  - `user`
  - `assistant`

### `content`

- 含义：对应角色文本
- `assistant` 当前存在两种主格式

结构化思维监督格式：

```text
{structured_think} 答案：{answer}。
```

显式 think 监督格式：

```text
<think>
{某个 xxx_think 字段对应的文本}
</think>

答案：{answer}。
```

## 七、当前推荐的最低交付标准

为了降低做数据的同学的负担，我建议把“最小可交付数据”定义成下面两种。

### 1. 最小结构化思维监督样本

必须提供：

- `id`
- `source`
- `family`
- `split`
- `modern_question`
- `answer`
- `structured_think`

建议提供：

- `classical_question`

### 2. 最小 think 监督样本

必须提供：

- `id`
- `source`
- `family`
- `split`
- `modern_question`
- `answer`
- 至少一个 `*_think` 字段

当前主线建议提供：

- `modern_think`
- `classical_think`
- `classical_question`

## 八、当前我的建议

基于你们现在的课设目标，我建议最终固定为：

### 主仓库核心必填

- `id`
- `source`
- `family`
- `split`
- `modern_question`
- `classical_question`
- `answer`

### 结构化思维方向可选必填

- 做 structuredthink 任务时：
  - `structured_think`

### think 方向可选必填

- 做当前主线 think 任务时：
  - `modern_think`
  - `classical_think`

### 可扩展字段规则

- 所有新的思维方法字段统一命名为：
  - `xxx_think`

这样后续即使提出新方法，也不需要推翻 schema，只需要新增一个符合规则的字段即可。
