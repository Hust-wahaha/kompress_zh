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

## Still Required Before Public HF Upload

### 1. License decision

当前仓库尚未明确最终开源 license。

HF 公开发布前必须明确：

- 仓库 license
- 模型 repo license
- 数据可公开范围与说明口径

如果这一项不定，HF 页面就仍然不算正式可发状态。

### 2. Artifact packaging decision

需要明确上传的是哪一种：

- LoRA adapter only
- merged full model
- both

当前更推荐先把这个决定写清楚，再做 repo 结构整理。

### 3. Inference snippet

HF 页面至少应给出一个最小推理示例，说明：

- 输入格式
- 输出预期
- `language-model-only` 约束

### 4. Repo card metadata final pass

发布前应最终确认：

- tags
- base model name
- pipeline type
- language tags
- public wording for limitations

### 5. Weight and file naming sanity check

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

如果首发只传 adapter，就在 README 明确写：

- base model
- merge / load method
- intended inference path

## Recommended Release Order

1. 定 license
2. 定上传形态：adapter only / merged / both
3. 准备 HF repo README，优先使用 [HF_MODEL_CARD_BASELINE_V1_RELEASE.md](./HF_MODEL_CARD_BASELINE_V1_RELEASE.md)
4. 增加最小推理示例
5. 检查模型文件命名与 README 一致
6. 首次公开上传
7. 上传后回查 HF 页面显示与下载说明

## Current Recommendation

如果要追求首发稳妥而不是一步到位，当前最建议路线是：

1. 先发 `baseline v1`
2. 明确这是 first public baseline，而不是 final model
3. 强调其部署意义、风格约束、anchor-aware 设计、strict/soft 评测
4. 暂不把它包装成“终局最强版”

这会让项目显得更成熟，也更可信。
