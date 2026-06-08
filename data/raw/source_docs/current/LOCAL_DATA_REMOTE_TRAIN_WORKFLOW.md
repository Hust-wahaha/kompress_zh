# 本地造数据 / AutoDL 训练工作流规范

## 1. 总体原则

项目后续按两段式流水线推进：

- **本地机器**：负责数据原料收集、清洗、中文化、教师标注、质检、导出数据集
- **AutoDL**：负责模型训练、评测、结果汇总、模型产物管理

这样划分最合理，因为：

- 造数据阶段更依赖外部 API 与人工抽检
- 训练阶段更依赖 GPU、稳定环境和可追溯运行目录

## 2. 本地阶段负责什么

本地阶段负责：

1. 构建候选原料池
2. 抽取 Markdown / 自然语言片段
3. 对英文或混合文本做中文化
4. 用教师模型生成严格抽取式压缩标签
5. 生成人工抽检样本
6. 导出训练集 / 验证集 / 审核集

本地阶段**不负责**：

- 正式模型训练
- 大规模 LoRA / 全参微调
- 正式 benchmark 评测

## 3. AutoDL 阶段负责什么

AutoDL 负责：

1. 拉取已定版数据集
2. 执行训练脚本
3. 执行离线评测与案例导出
4. 保存运行产物与日志
5. 将结果同步回仓库

AutoDL 阶段**不负责**：

- 临时修改数据标签
- 现场手工编辑训练数据
- 将未定版数据直接混入正式实验

## 4. 教师模型配置

当前教师模型固定为：

- `deepseek-v4-pro`

本地运行时通过环境变量提供：

```bash
export DEEPSEEK_API_KEY='***'
export DEEPSEEK_MODEL='deepseek-v4-pro'
```

约束：

- 不要把 key 写进代码
- 不要把 key 写进文档示例中的真实值
- 不要把 key 提交到 GitHub

## 5. 本地目录建议

建议后续本地数据生产按下面结构组织：

```text
data/
  sources/
    markdown_pool/
    agent_docs_pool/
  interim/
    extracted_blocks/
    zh_rewritten/
    teacher_labeled/
  processed/
    zh_kompress_v0_1_seed1k/
      train.jsonl
      val.jsonl
      audit_sample.jsonl
      manifest.json
```

含义：

- `sources/`：原始候选原料
- `interim/`：中间产物，不可直接训练
- `processed/`：已定版、可训练数据

## 6. 数据版本原则

只有满足下面条件，数据才允许进入 `processed/`：

1. 字段 schema 固定
2. 教师模型版本已记录
3. 中文化策略已记录
4. 至少完成一轮人工抽检
5. 有 `manifest.json` 记录来源与过滤规则

## 7. 教师标注脚本配置原则

后续脚本应默认从环境变量读取配置，例如：

- `DEEPSEEK_API_KEY`
- `DEEPSEEK_MODEL`
- `DEEPSEEK_BASE_URL`（若后续需要兼容代理/中转）
- `LABELING_BATCH_SIZE`
- `LABELING_MAX_RETRIES`

不要把这些参数写死在脚本里。

## 8. 本地造数据的推荐顺序

建议顺序如下：

1. 扩原料池
2. 选 `P0/P1` 文档
3. 切 Markdown 逻辑块
4. 过滤代码块 / 日志块 / 配置块
5. 做中文化
6. 用 `deepseek-v4-pro` 打抽取式压缩标签
7. 做字符级对齐
8. 抽样人工复核
9. 导出 `train/val/audit`

## 9. AutoDL 训练的输入边界

AutoDL 训练端只接受：

- 已定版 `processed/` 数据
- 已记录版本号的数据集目录

训练时禁止：

- 直接读取 `sources/`
- 直接读取 `interim/`
- 手工修改 JSONL 后不记版本就训练

## 10. 结果追溯要求

每次训练运行都必须能反查到：

- 使用了哪个数据版本
- 使用了哪个教师模型版本
- 使用了哪个过滤规则版本
- 使用了哪个训练配置

所以建议在每个训练 run 里记录：

- `dataset_version`
- `teacher_model`
- `labeling_prompt_version`
- `train_config_version`

## 11. 当前最推荐的启动方式

下一步如果要真正开工，建议：

1. 先在本地完成 `Markdown` 子集 `300~500` 条
2. 用 `deepseek-v4-pro` 打标签
3. 抽检后导出 `zh_kompress_v0_1_md_seed`
4. 再把这个版本推到仓库
5. 最后再去 AutoDL 跑第一版训练

## 12. 当前最重要的判断

把“造数据”和“训练”分开，不只是为了方便，而是为了：

**保证数据质量问题和训练问题不会混在一起。**

这对我们这种要反复迭代的数据驱动项目尤其重要。
