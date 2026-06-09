from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from statistics import mean

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from zh_plaintext_compressor.common.naming import (
    DEFAULT_DATASET_TAG,
    dataset_file,
    make_experiment_dir,
    normalize_model_tag,
)
from zh_plaintext_compressor.common.schema import (
    DEFAULT_SYSTEM_PROMPT,
    anchor_retention_breakdown,
    anchor_retention,
    char_compression_ratio,
    char_f1,
)

MODEL_ID = "Qwen/Qwen3.5-0.8B"
THINK_SHELL_PATTERN = re.compile(r"^\s*<think>\s*</think>\s*", re.IGNORECASE | re.DOTALL)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-tag", type=str, default=DEFAULT_DATASET_TAG)
    parser.add_argument("--model-id", type=str, default=MODEL_ID)
    parser.add_argument("--model-tag", type=str, default=None)
    parser.add_argument("--test-file", type=Path, default=None)
    parser.add_argument("--checkpoint", type=Path, default=None)
    parser.add_argument("--compare-baseline", action="store_true")
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--max-batch-size", type=int, default=8)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--repetition-penalty", type=float, default=1.0)
    parser.add_argument("--run-tag", type=str, default="reference_eval")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--system", type=str, default=DEFAULT_SYSTEM_PROMPT)
    parser.add_argument(
        "--language-model-only",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Must remain enabled for this plain-text compressor; vision encoder is not used.",
    )
    return parser.parse_args()


def read_jsonl(path: Path, limit: int | None) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows[:limit] if limit else rows


def normalize_prediction_text(text: str) -> str:
    return THINK_SHELL_PATTERN.sub("", text).strip()


def build_engine(model_id: str, adapter: str | None, max_batch_size: int, language_model_only: bool):
    from peft import PeftModel
    from swift import get_template
    from swift.infer_engine import TransformersEngine

    from zh_plaintext_compressor.common.swift_compat import get_model_processor_language_only

    model, tokenizer = get_model_processor_language_only(model_id, enabled=language_model_only)
    if adapter:
        model = PeftModel.from_pretrained(model, adapter)
    template = get_template(tokenizer, default_system=DEFAULT_SYSTEM_PROMPT)
    # Qwen3.5 templates default to a thinking prefix; force visible-output-only eval.
    if hasattr(template, "enable_thinking"):
        template.enable_thinking = False
    if hasattr(template, "response_prefix"):
        template.response_prefix = ""
    return TransformersEngine(model, template=template, max_batch_size=max_batch_size)


def run_model(
    name: str,
    model_id: str,
    adapter: str | None,
    rows: list[dict],
    run_dir: Path,
    args: argparse.Namespace,
) -> list[dict]:
    from swift.infer_engine import InferRequest, RequestConfig

    engine = build_engine(
        model_id=model_id,
        adapter=adapter,
        max_batch_size=args.max_batch_size,
        language_model_only=args.language_model_only,
    )
    requests = [InferRequest(messages=[{"role": "user", "content": row["messages"][1]["content"]}]) for row in rows]
    request_config = RequestConfig(
        max_tokens=args.max_tokens,
        temperature=args.temperature,
        top_p=args.top_p,
        top_k=args.top_k,
        repetition_penalty=args.repetition_penalty,
    )
    responses = engine.infer(requests, request_config)
    output_rows = []
    for row, response in zip(rows, responses):
        prediction = normalize_prediction_text(response.choices[0].message.content)
        output_rows.append(
            {
                "sample_id": row["sample_id"],
                "source_name": row["source_name"],
                "split": row["split"],
                "original_text": row["original_text"],
                "reference_text": row["compressed_text"],
                "prediction_text": prediction,
                "contains_anchor": row["contains_anchor"],
            }
        )
    output_path = run_dir / "predictions" / f"{name}.json"
    output_path.write_text(json.dumps(output_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_rows


def summarize_predictions(name: str, rows: list[dict]) -> dict:
    detailed = []
    prediction_ratios = []
    reference_ratios = []
    anchor_rates = []
    strict_anchor_rates = []
    soft_anchor_rates = []
    char_f1_scores = []
    for row in rows:
        prediction_ratio = char_compression_ratio(row["original_text"], row["prediction_text"])
        reference_ratio = char_compression_ratio(row["original_text"], row["reference_text"])
        anchor_breakdown = anchor_retention_breakdown(row["original_text"], row["prediction_text"])
        combined = anchor_breakdown["combined"]
        strict = anchor_breakdown["strict"]
        soft = anchor_breakdown["soft"]
        kept, total = int(combined["kept"]), int(combined["total"])
        anchor_rate = kept / total if total else None
        score = char_f1(row["reference_text"], row["prediction_text"])
        prediction_ratios.append(prediction_ratio)
        reference_ratios.append(reference_ratio)
        if anchor_rate is not None:
            anchor_rates.append(anchor_rate)
        if strict["rate"] is not None:
            strict_anchor_rates.append(float(strict["rate"]))
        if soft["rate"] is not None:
            soft_anchor_rates.append(float(soft["rate"]))
        char_f1_scores.append(score)
        detailed.append(
            {
                "sample_id": row["sample_id"],
                "source_name": row["source_name"],
                "prediction_ratio": prediction_ratio,
                "reference_ratio": reference_ratio,
                "anchor_kept": kept,
                "anchor_total": total,
                "anchor_retention_rate": anchor_rate,
                "strict_anchor_kept": strict["kept"],
                "strict_anchor_total": strict["total"],
                "strict_anchor_retention_rate": strict["rate"],
                "soft_anchor_kept": soft["kept"],
                "soft_anchor_total": soft["total"],
                "soft_anchor_retention_rate": soft["rate"],
                "combined_anchor_kept_tokens": combined["kept_tokens"],
                "combined_anchor_missing_tokens": combined["missing_tokens"],
                "strict_anchor_kept_tokens": strict["kept_tokens"],
                "strict_anchor_missing_tokens": strict["missing_tokens"],
                "soft_anchor_kept_tokens": soft["kept_tokens"],
                "soft_anchor_missing_tokens": soft["missing_tokens"],
                "char_f1": score,
                "prediction_text": row["prediction_text"],
                "reference_text": row["reference_text"],
            }
        )
    return {
        "model_name": name,
        "overall": {
            "count": len(rows),
            "avg_prediction_ratio": mean(prediction_ratios) if prediction_ratios else 0.0,
            "avg_reference_ratio": mean(reference_ratios) if reference_ratios else 0.0,
            "avg_anchor_retention_rate": mean(anchor_rates) if anchor_rates else 0.0,
            "avg_strict_anchor_retention_rate": mean(strict_anchor_rates) if strict_anchor_rates else 0.0,
            "avg_soft_anchor_retention_rate": mean(soft_anchor_rates) if soft_anchor_rates else 0.0,
            "avg_char_f1": mean(char_f1_scores) if char_f1_scores else 0.0,
            "avg_prediction_chars": mean(len(row["prediction_text"]) for row in rows) if rows else 0.0,
        },
        "detailed": detailed,
    }


def main() -> None:
    args = parse_args()
    if not args.language_model_only:
        raise SystemExit("`--no-language-model-only` is forbidden for this project.")
    test_file = args.test_file or dataset_file("test", args.dataset_tag)
    rows = read_jsonl(test_file, args.limit)
    model_tag = normalize_model_tag(args.model_id, args.model_tag)
    run_dir = make_experiment_dir(
        stage="eval",
        dataset_tag=args.dataset_tag,
        model_tag=model_tag,
        suffix=args.run_tag,
    )
    model_runs = []
    if args.compare_baseline:
        model_runs.append(("baseline", None))
    model_runs.append(("target", str(args.checkpoint) if args.checkpoint else None))

    summary = {
        "run_dir": str(run_dir),
        "dataset_tag": args.dataset_tag,
        "model_id": args.model_id,
        "model_tag": model_tag,
        "test_file": str(test_file),
        "language_model_only": args.language_model_only,
        "results": {},
    }
    for name, adapter in model_runs:
        prediction_rows = run_model(name, args.model_id, adapter, rows, run_dir, args)
        summary["results"][name] = summarize_predictions(name, prediction_rows)

    summary_path = run_dir / "metrics" / "eval_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "run_dir": str(run_dir),
                "models": {
                    name: {
                        "avg_prediction_ratio": result["overall"]["avg_prediction_ratio"],
                        "avg_anchor_retention_rate": result["overall"]["avg_anchor_retention_rate"],
                        "avg_strict_anchor_retention_rate": result["overall"]["avg_strict_anchor_retention_rate"],
                        "avg_soft_anchor_retention_rate": result["overall"]["avg_soft_anchor_retention_rate"],
                        "avg_char_f1": result["overall"]["avg_char_f1"],
                    }
                    for name, result in summary["results"].items()
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    if "--help" in sys.argv or "-h" in sys.argv:
        parse_args()
        raise SystemExit(0)
    main()
