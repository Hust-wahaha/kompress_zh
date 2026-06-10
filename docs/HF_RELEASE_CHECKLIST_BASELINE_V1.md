# HF Release Checklist: kompress_zh baseline v1

这份清单用于把当前仓库材料推进到真正可发的 Hugging Face 首版。

## Already Ready

- baseline 版本口径已固定
  - `Qwen/Qwen3.5-0.8B`
  - `Swift + LoRA`
  - `language-model-only`
  - `standardset_v6_1234`
  - `reference_v1 / checkpoint-61`

- 对外首页叙事已成型
  - 根目录 [README.md](../README.md)

- HF release-facing model card 已整理
  - [HF_MODEL_CARD_BASELINE_V1_RELEASE.md](./HF_MODEL_CARD_BASELINE_V1_RELEASE.md)

- 训练与评测结果已有固定文档
  - [TRAINING_EVAL_STANDARDSET_V6_REFERENCE_V1_2026-06-10.md](./TRAINING_EVAL_STANDARDSET_V6_REFERENCE_V1_2026-06-10.md)

## Decisions Already Made

### 1. License

- repository license: `Apache-2.0`
- recommended HF model repo license: `Apache-2.0`

### 2. Release format

- baseline-v1 public release format: `LoRA adapter only`

这样做的原因很直接：

- 首发更稳妥
- 文件体积更小
- 便于说明与复现实验链路
- 不必把首发包装成“完整终局模型”

### 3. Data stance

- 数据**不承诺全开放**
- 可以公开任务定义、数据原则、统计口径、样例风格
- 不默认承诺公开完整训练原始数据或完整清洗集

### 4. Weight stance

- baseline-v1 的 `LoRA adapter` 权重按当前决策应公开

这是合理的，因为如果权重不公开，HF 首发本身就失去实际使用价值。

### 5. Inference style

- HF 页面应提供最小 `base model + LoRA adapter` 推理示例
- 明确 `language-model-only`
- 明确本模型处理的是 Chinese plain-text compression，而不是 generic summarization

## Still Required Before Public HF Upload

### 1. Adapter artifact packaging

需要实际准备并检查：

- adapter 文件
- config 文件
- tokenizer 相关文件
- README 与真实 artifact 名称一致

### 2. Repo card metadata final pass

发布前应最终确认：

- tags
- base model name
- pipeline type
- language tags
- public wording for limitations

### 3. Weight and file naming sanity check

上传前应统一：

- checkpoint naming
- adapter file naming
- tokenizer / config completeness
- README references to actual downloadable artifact names

## Recommended HF Repo Layout

最小建议结构：

```text
README.md
adapter_config.json / model files
generation_config.json
special_tokens_map.json
tokenizer_config.json
LICENSE
```

baseline-v1 当前建议就是只传 adapter，因此 README 应明确写：

- base model
- merge / load method
- intended inference path

## Recommended Release Order

1. 准备 `LoRA adapter` 上传文件
2. 用 [HF_MODEL_CARD_BASELINE_V1_RELEASE.md](./HF_MODEL_CARD_BASELINE_V1_RELEASE.md) 作为 HF repo README 基底
3. 保留最小推理示例
4. 检查模型文件命名与 README 一致
5. 首次公开上传
6. 上传后回查 HF 页面显示与下载说明

## Current Recommendation

当前最稳妥且成熟的首发路线已经明确：

1. 先发 `baseline v1`
2. 公开 `LoRA adapter` 权重
3. 使用 `Apache-2.0`
4. 不承诺完整数据集开源
5. 强调其部署意义、风格约束、anchor-aware 设计、strict/soft 评测
6. 暂不把它包装成“终局最强版”

这会让项目显得更成熟，也更可信。
