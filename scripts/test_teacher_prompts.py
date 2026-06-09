from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from statistics import mean

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from zh_plaintext_compressor.common.schema import (
    anchor_retention_breakdown,
    char_compression_ratio,
    char_f1,
    extract_anchor_tokens,
    has_anchor_content,
)

API_ENDPOINT = "https://api.deepseek.com/chat/completions"
DEFAULT_MODEL = "deepseek-v4-pro"
OUTPUT_DIR = ROOT_DIR / "experiments" / "prompt_tests"

BASE_SYSTEM_RULES = """你是一个严格的中文压缩改写标注助手。

你的唯一任务是：
对输入的中文自然语言长段落做“保真压缩改写”，产出一个更短、仍可直接使用的中文版本。

这不是摘要任务，不是自由润色任务，也不是古文改写任务。

你必须遵守：
1. 忠实保留原意，不得编造原文没有的新事实、结论、要求、限制、步骤或判断。
2. 明显缩短文本，但不能为了压缩率牺牲关键信息。
3. 优先删除冗余表达、重复解释、客套话、口水话、过度展开的背景句。
4. 允许适度重组句子结构，使表达更紧凑。
5. 遇到文件名、路径、命令、参数、URL、API 名、模型名、版本号、数值、时间、约束条件、验收条件、下一步行动项时，应尽量保留。
6. 若原文中存在明确的任务目标、限制条件、交付物、结论、TODO、风险、决策、下一步，优先保留这些信息。
7. 只输出一个 JSON 对象，不得输出任何额外说明、Markdown 标记或注释。

JSON 字段固定为：
{
  "compressed_text": "...",
  "style_tag": "lite_wenyan_structured",
  "contains_anchor": true,
  "quality_notes": "..."
}
"""

PROMPT_VARIANTS = {
    "conservative": {
        "system": BASE_SYSTEM_RULES
        + """
额外要求：
- 优先保证保真，压缩率可以保守。
- 尽量保留原文中的限制条件、步骤顺序和行动项。
- 允许轻结构化，但尽量不要改动原文逻辑顺序。
- 轻文言化要非常克制，宁可偏现代中文，也不要显得“假精炼”。
""",
        "user": """任务：请对下面这段中文文本做保真压缩改写。

重点：
- 优先保留任务目标、约束、结论、TODO、下一步、风险、交付要求
- 尽量保留文件名、路径、命令、参数、URL、模型名、版本号、数值
- 可以缩短，但不要为追求压缩率而牺牲信息

原文：
{original_text}
""",
    },
    "balanced": {
        "system": BASE_SYSTEM_RULES
        + """
额外要求：
- 输出风格应为现代中文为主、轻结构化、轻文言压缩感。
- 可使用“因、故、若、下一步”等轻量压缩表达，但必须保持现代中文可读。
- 需要在保真和压缩率之间取得平衡。
""",
        "user": """任务：请对下面这段中文文本做“保真压缩改写”。

压缩目标：
- 尽量缩短
- 保留任务目标、约束、结论、TODO、下一步、风险、交付要求
- 尽量保留文件名、路径、命令、参数、URL、模型名、版本号、数值等关键锚点
- 允许轻结构化、轻文言化
- 不得编造原文没有的信息

原文：
{original_text}
""",
    },
    "aggressive": {
        "system": BASE_SYSTEM_RULES
        + """
额外要求：
- 在不丢失关键信息的前提下尽量压短。
- 优先把长句改成短句、并列句或紧凑分点。
- 允许更明显的轻文言压缩表达，但仍必须可读，且不能变成纯古文。
- 对背景铺垫、解释性修饰、重复说明应更激进地压缩。
""",
        "user": """任务：请把下面这段中文文本压缩到尽可能短，但必须保留可执行信息。

必须优先保留：
- 任务目标
- 限制条件
- 下一步 / TODO / 验收要求
- 文件名、路径、命令、参数、URL、模型名、版本号、数值

允许：
- 重组句式
- 轻结构化
- 轻文言化压缩

禁止：
- 编造
- 纯摘要化
- 纯古文化

原文：
{original_text}
""",
    },
}

SAMPLES = [
    {
        "sample_id": "sample_project_split",
        "source": "demo",
        "original_text": "当前需要先把中文压缩器项目和旧数学 think 项目分开管理。新主线所有脚本都应只放在 projects/qwen35_zh_plaintext_compressor/ 下，旧项目只保留作 legacy 参考。下一步先补 build_dataset.py、validate_dataset.py、train_lora.py、eval.py 四个入口。",
        "reference_text": "先分离新旧项目：新主线脚本只放 `projects/qwen35_zh_plaintext_compressor/`，旧数学 think 线仅作 legacy 参考。下一步补齐 `build_dataset.py`、`validate_dataset.py`、`train_lora.py`、`eval.py` 四个入口。",
    },
    {
        "sample_id": "sample_training_constraints",
        "source": "demo",
        "original_text": "训练阶段必须显式启用 language-model-only 思路，避免把 vision encoder 带进文本压缩任务。输出目标不是 think，而是 assistant 可见的压缩改写文本；允许轻结构化和轻文言化，但不能牺牲可读性，也不能丢掉文件名、命令、数字这些关键锚点。",
        "reference_text": "训练需显式走 `language-model-only`，禁止把 vision encoder 带入文本压缩。目标输出是 assistant 可见压缩文本，可轻结构化、轻文言化，但须保留文件名、命令、数字等关键锚点，并保持可读。",
    },
    {
        "sample_id": "sample_eval_focus",
        "source": "demo",
        "original_text": "第一版评测不要再围绕答案正确率，而要围绕压缩器本身：至少记录压缩率、长度下降幅度、信息保真、关键锚点保留率和本地推理速度。评测样本优先选择中文需求说明、文档块、结果解释，以及夹杂少量路径和命令的自然语言段落。",
        "reference_text": "首版评测聚焦压缩器本身：记录压缩率、长度下降、信息保真、锚点保留率与本地推理速度。样本优先选中文需求说明、文档块、结果解释，以及夹少量路径和命令的自然语言段。",
    },
    {
        "sample_id": "sample_doc_chunk",
        "source": "mainline_doc",
        "original_text": "当前模型只处理 Headroom 已路由出来的中文 plain text 长段落，重点包括中文任务描述、中文需求与约束、中文文档说明、中文结果解释、中文进度总结、中文交付文本、中文 session 中的长自然语言块。原始代码块、原始 JSON / YAML / XML、原始日志流、原始报错堆栈、原始 diff / patch、原始搜索结果，不作为本模型主任务。",
        "reference_text": "模型仅处理 Headroom 路由出的中文 plain-text 长段，如任务描述、需求约束、文档说明、结果解释、进度总结、交付文本和 session 自然语言块；原始代码、JSON/YAML/XML、日志、报错堆栈、diff/patch、搜索结果不属主任务。",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--api-key-env", type=str, default="DEEPSEEK_API_KEY")
    parser.add_argument("--max-workers", type=int, default=6)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--run-tag", type=str, default="teacher_prompt_ab")
    return parser.parse_args()


def call_api(model: str, system_prompt: str, user_prompt: str, timeout: int, api_key: str) -> dict:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.0,
        "max_tokens": 1024,
        "response_format": {"type": "json_object"},
        "thinking": {"type": "disabled"},
    }
    request = urllib.request.Request(
        API_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8"))
    content = body["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    parsed["_raw_response"] = content
    parsed["_usage"] = body.get("usage", {})
    return parsed


def score_output(original_text: str, reference_text: str, result: dict) -> dict:
    compressed_text = str(result.get("compressed_text", "")).strip()
    ratio = char_compression_ratio(original_text, compressed_text)
    anchor_breakdown = anchor_retention_breakdown(original_text, compressed_text)
    combined = anchor_breakdown["combined"]
    strict = anchor_breakdown["strict"]
    soft = anchor_breakdown["soft"]
    kept, total = int(combined["kept"]), int(combined["total"])
    anchor_rate = kept / total if total else 1.0
    reference_f1 = char_f1(reference_text, compressed_text)
    anchor_count = len(extract_anchor_tokens(original_text))
    return {
        "compressed_text": compressed_text,
        "style_tag": result.get("style_tag"),
        "contains_anchor": result.get("contains_anchor"),
        "quality_notes": result.get("quality_notes"),
        "compression_ratio": ratio,
        "anchor_kept": kept,
        "anchor_total": total,
        "anchor_retention_rate": anchor_rate,
        "strict_anchor_kept": strict["kept"],
        "strict_anchor_total": strict["total"],
        "strict_anchor_retention_rate": strict["rate"],
        "soft_anchor_kept": soft["kept"],
        "soft_anchor_total": soft["total"],
        "soft_anchor_retention_rate": soft["rate"],
        "reference_char_f1": reference_f1,
        "predicted_contains_anchor": has_anchor_content(compressed_text),
        "source_anchor_count": anchor_count,
    }


def run_single_case(
    *,
    variant_name: str,
    sample: dict,
    model: str,
    timeout: int,
    api_key: str,
) -> dict:
    prompts = PROMPT_VARIANTS[variant_name]
    result = call_api(
        model=model,
        system_prompt=prompts["system"],
        user_prompt=prompts["user"].format(original_text=sample["original_text"]),
        timeout=timeout,
        api_key=api_key,
    )
    scored = score_output(sample["original_text"], sample["reference_text"], result)
    return {
        "variant": variant_name,
        "sample_id": sample["sample_id"],
        "source": sample["source"],
        "original_text": sample["original_text"],
        "reference_text": sample["reference_text"],
        **scored,
        "usage": result.get("_usage", {}),
        "raw_response": result.get("_raw_response", ""),
    }


def summarize_variant(rows: list[dict]) -> dict:
    return {
        "count": len(rows),
        "avg_compression_ratio": mean(row["compression_ratio"] for row in rows),
        "avg_anchor_retention_rate": mean(row["anchor_retention_rate"] for row in rows),
        "avg_strict_anchor_retention_rate": mean(
            row["strict_anchor_retention_rate"] for row in rows if row["strict_anchor_retention_rate"] is not None
        ),
        "avg_soft_anchor_retention_rate": mean(
            row["soft_anchor_retention_rate"] for row in rows if row["soft_anchor_retention_rate"] is not None
        ),
        "avg_reference_char_f1": mean(row["reference_char_f1"] for row in rows),
        "avg_output_chars": mean(len(row["compressed_text"]) for row in rows),
    }


def pick_best_variant(summary_by_variant: dict[str, dict]) -> str:
    def score(item: tuple[str, dict]) -> float:
        _, metrics = item
        return (
            metrics["avg_reference_char_f1"] * 0.45
            + metrics["avg_anchor_retention_rate"] * 0.35
            + (1.0 - abs(metrics["avg_compression_ratio"] - 0.7)) * 0.20
        )

    return max(summary_by_variant.items(), key=score)[0]


def main() -> None:
    args = parse_args()
    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        raise RuntimeError(f"Missing API key env: {args.api_key_env}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    futures = []
    results = []
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        for variant_name in PROMPT_VARIANTS:
            for sample in SAMPLES:
                futures.append(
                    executor.submit(
                        run_single_case,
                        variant_name=variant_name,
                        sample=sample,
                        model=args.model,
                        timeout=args.timeout,
                        api_key=api_key,
                    )
                )
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc

    results.sort(key=lambda row: (row["variant"], row["sample_id"]))
    summary_by_variant = {}
    for variant_name in PROMPT_VARIANTS:
        variant_rows = [row for row in results if row["variant"] == variant_name]
        summary_by_variant[variant_name] = summarize_variant(variant_rows)

    best_variant = pick_best_variant(summary_by_variant)
    report = {
        "model": args.model,
        "run_tag": args.run_tag,
        "sample_count": len(SAMPLES),
        "variant_count": len(PROMPT_VARIANTS),
        "best_variant": best_variant,
        "summary_by_variant": summary_by_variant,
        "results": results,
    }
    output_path = OUTPUT_DIR / f"{args.run_tag}.json"
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"best_variant": best_variant, "summary_by_variant": summary_by_variant}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
