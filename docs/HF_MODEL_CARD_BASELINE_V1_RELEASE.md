---
base_model: Qwen/Qwen3.5-0.8B
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

# kompress_zh baseline v1

> First public baseline for Chinese agent-grade plain-text compression.

`kompress_zh` is a Chinese plain-text compression model line for agent and document workflows. It is not designed as a generic summarizer. Its purpose is to compress long Chinese working text into shorter, denser, still-usable text blocks while preserving meaning, execution anchors, and downstream readability for stronger models.

If summarized in one sentence:

> `kompress_zh` baseline v1 is a deployment-oriented Chinese plain-text compressor with light structure, light wenyan compression style, anchor-aware data construction, and case-level fidelity review.

## Release Snapshot

- base model: `Qwen/Qwen3.5-0.8B`
- training method: `Swift + LoRA`
- inference mode: `language-model-only`
- dataset: `standardset_v6_1234`
- checkpoint: `reference_v1 / checkpoint-61`
- evaluation date: `2026-06-10`

Headline numbers for baseline v1:

- `25.7%` average reduction on the evaluated test split
- `92.2%` strict anchor retention
- `99.1%` anchor-bearing data in the baseline dataset
- evaluated on `132` test samples

This release should be understood as:

- a first public baseline
- a reproducible workflow checkpoint
- a candidate upstream component for `headroom_zh`-style systems

It should not be described as a final production model or as the strongest possible compression variant.

## What Makes This Model Different

### 1. It is not a generic Chinese summarizer

The target is not "write a shorter summary." The target is "compress Chinese agent context without breaking what downstream models still need."

### 2. The style is constrained on purpose

The target output style is:

- light structured
- light wenyan compression feel
- modern Chinese as the main body
- high information density
- still readable by downstream LLMs

This avoids two common failure modes:

- generic summary tone
- over-classical wording that hurts controllability

### 3. The data is intentionally anchor-heavy

The dataset is not a clean natural-language-only summarization corpus. It intentionally includes many samples with anchors such as:

- paths
- filenames
- commands
- URLs
- parameters
- model ids
- numeric constraints

Baseline dataset summary:

- total samples: `1234`
- split: `973 / 129 / 132`
- anchor rows: `1223 / 1234`
- average anchor count: `3.96`

### 4. Evaluation separates strict and soft anchors

The evaluation does not collapse all anchors into one coarse score.

`strict anchors` include:

- URLs
- paths
- filenames
- commands and parameters
- repo or model ids

`soft anchors` include:

- numbering
- field names
- identifiers
- light formatting tokens

This matters because deployment failures are usually caused by broken paths, commands, or filenames, not by a minor numbering change.

### 5. Automatic scripts are not treated as ground truth

Scoring scripts are used for filtering, ranking, and sampling. Final judgment for suspicious low-score cases is still based on case-level manual review over:

- source text
- reference compression
- model output

## Intended Use

This model is best suited for:

- Chinese task instructions
- Chinese constraints and execution rules
- Chinese project docs with long natural-language blocks
- Chinese sync notes and result explanations
- natural-language-heavy text containing some paths, commands, URLs, filenames, and numbers

This model is not meant for:

- raw code
- raw JSON / YAML / XML
- logs or stack traces
- diffs or patches
- free-form summarization
- subjective commentary
- creative rewriting

The most natural system position is:

1. route Chinese plain-text long blocks into `kompress_zh`
2. keep structured or code-heavy content on specialized compression paths
3. let stronger downstream models consume the compressed context

## Input and Output Profile

The input side is typically:

- long Chinese working text
- process specs
- coordination notes
- delivery rules
- test instructions
- doc paragraphs with execution anchors

The output target is:

- shorter
- denser
- semantically faithful
- anchor-preserving whenever possible
- still useful as working text

In other words, the output is not a summary artifact. It is compressed working text.

## Evaluation Context

Baseline v1 metrics refer to the `2026-06-10` offline evaluation snapshot:

- test split size: `132`
- train / val / test: `973 / 129 / 132`
- inference mode: `language-model-only`
- base family: `Qwen3.5-0.8B`

Test-set metrics:

| Metric | Value |
| --- | --- |
| Avg prediction ratio | `0.7425` |
| Avg reduction | `25.7%` |
| Avg char F1 | `0.8039` |
| Avg anchor retention | `0.8157` |
| Avg strict anchor retention | `0.9216` |
| Avg soft anchor retention | `0.8075` |

Training snapshot:

| Metric | Value |
| --- | --- |
| Final checkpoint | `checkpoint-61` |
| Train loss | `0.5575` |
| Eval loss | `0.5315` |
| Eval token acc | `0.8566` |

These numbers should be interpreted as a strong baseline snapshot for anchor-heavy Chinese agent text, not as a universal final benchmark claim.

## Known Strengths

- stable light-structured compression style
- strong strict-anchor retention for a small baseline model
- useful on execution-heavy Chinese text rather than only on clean summarization data
- already plausible as a first upstream component for `headroom_zh`

## Current Limitations

- compression is still conservative on many samples
- link-heavy material is often not compressed aggressively enough
- a minority of cases may compress away "next step", "risk", or "delivery" hints
- large-scale real online integration has not been completed yet

## Prompt Pattern

Recommended input pattern:

```text
请将下面这段中文文本压缩改写为更短版本。要求：保留核心语义；尽量保留路径、命令、文件名、数字等关键锚点；允许轻结构化；允许轻文言压缩感；不要编造新信息。

<原文>
...
```

## Release Positioning

This release is best treated as:

- the first public `kompress_zh` baseline
- a release-facing checkpoint for the current training and evaluation workflow
- a foundation for stronger future versions with larger curated data

## References

- [README.md](../README.md)
- [CURRENT_MAINLINE_QWEN35_COMPRESSOR.md](./CURRENT_MAINLINE_QWEN35_COMPRESSOR.md)
- [TRAINING_EVAL_STANDARDSET_V6_REFERENCE_V1_2026-06-10.md](./TRAINING_EVAL_STANDARDSET_V6_REFERENCE_V1_2026-06-10.md)
- [KOMPRESS_ZH_BASELINE_V1_DECISION_2026-06-10.md](./KOMPRESS_ZH_BASELINE_V1_DECISION_2026-06-10.md)
