---
base_model: Qwen/Qwen3.5-0.8B
license: apache-2.0
language:
  - zh
tags:
  - chinese
  - text-compression
  - prompt-compression
  - agent
  - qwen
pipeline_tag: text-generation
---

# kompress_zh-baseline-v1-lora

> LoRA adapter release for `kompress_zh` baseline v1.

`kompress_zh-baseline-v1-lora` is the first public LoRA adapter release for the `kompress_zh` project, a Chinese plain-text compression model line designed for agent-grade context rather than generic summarization.

This release is intended for Chinese working text such as:

- task instructions
- execution rules
- project docs
- sync notes
- result explanations
- long natural-language-heavy text containing paths, filenames, commands, URLs, and numbers

It is not intended for:

- raw code
- raw JSON / YAML / XML
- logs or stack traces
- diffs or patches
- free-form summarization

## Release Snapshot

- base model: `Qwen/Qwen3.5-0.8B`
- release type: `LoRA adapter only`
- training method: `Swift + LoRA`
- inference mode: `language-model-only`
- dataset: `standardset_v6_1234`
- checkpoint source: `reference_v1 / checkpoint-61`
- evaluation date: `2026-06-10`

Headline metrics:

- `25.7%` average reduction on the evaluated test split
- `92.2%` strict anchor retention
- `99.1%` anchor-bearing data in the baseline dataset
- evaluated on `132` test samples

## Design Intent

This model line is built around four decisions:

1. It compresses Chinese plain text, not raw code or structured blobs.
2. It aims for light structure plus light wenyan compression feel.
3. It treats anchors such as paths, commands, and filenames as high-value content.
4. It uses case-level review rather than trusting automatic scores as ground truth.

The output target is compressed working text, not a generic summary artifact.

## How To Use

This release assumes:

- base model: `Qwen/Qwen3.5-0.8B`
- adapter loading via `peft`
- text-only usage

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

base_model = "Qwen/Qwen3.5-0.8B"
adapter_path = "Hust-wahaha/kompress_zh-baseline-v1-lora"

tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    base_model,
    trust_remote_code=True,
    device_map="auto",
    torch_dtype="auto",
)
model = PeftModel.from_pretrained(model, adapter_path)
model.eval()

source_text = """当前统一基线评测入口是 `scripts/eval_compare_full.py`。
未经统一确认，不要私自修改以下核心口径：
- `max_tokens`
- baseline / finetuned 对照方式
- `DeepSeek` 复核模式"""

prompt = f"""请将下面这段中文文本压缩改写为更短版本。要求：保留核心语义；尽量保留路径、命令、文件名、数字等关键锚点；允许轻结构化；允许轻文言压缩感；不要编造新信息。

<原文>
{source_text}
"""

inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=192)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

Notes:

- This baseline is `language-model-only`.
- Do not use vision inputs.
- The model is designed for compression, not free-form creative rewriting.

## Evaluation Context

The current public numbers refer to the baseline-v1 offline snapshot:

- train / val / test: `973 / 129 / 132`
- test split size: `132`
- avg prediction ratio: `0.7425`
- avg reduction: `25.7%`
- avg char F1: `0.8039`
- avg strict anchor retention: `0.9216`
- avg soft anchor retention: `0.8075`

These numbers should be treated as a first public baseline checkpoint rather than a final universal benchmark.

## Data and Release Scope

- this adapter is intended to be public
- the full training dataset is **not promised as fully open**
- public release focuses on task definition, evaluation framing, examples, and usable adapter weights

This conservative data stance exists because the source pool mixes multiple real-world workflow-style inputs, and not every upstream source should be treated as fully redistributable.

## Files Expected In This HF Repo

At release time, this repo should contain at least:

- `README.md`
- `adapter_config.json`
- `adapter_model.safetensors`
- `LICENSE`

Optional extra files may be added if the export stack produces them.

## Current Limitations

- compression is still conservative on many samples
- link-heavy material is still harder than desired
- some cases may under-compress where a stronger model could go further
- this is a baseline release, not the final strongest version
