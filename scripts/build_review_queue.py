from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from zh_plaintext_compressor.common.schema import (
    anchor_retention_breakdown,
    char_compression_ratio,
    extract_anchor_tokens,
    has_anchor_content,
    normalize_whitespace,
)

REVIEW_CUE_GROUPS = {
    "next_step": ("下一步", "接下来", "后续", "TODO", "待办"),
    "constraint": ("必须", "不得", "禁止", "务必", "须", "需", "勿"),
    "delivery": ("交付", "输出", "验收", "结论", "结果"),
    "risk": ("风险", "问题", "注意", "警告", "阻塞"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-file", type=Path, required=True)
    parser.add_argument("--queue-file", type=Path, required=True)
    parser.add_argument("--sample-file", type=Path, default=None)
    parser.add_argument("--summary-file", type=Path, default=None)
    parser.add_argument("--target-sample-count", type=int, default=48)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def infer_length_bucket(text: str) -> str:
    text_length = len(text)
    if text_length < 350:
        return "short"
    if text_length < 700:
        return "medium"
    return "long"


def count_present_keywords(text: str, keywords: tuple[str, ...]) -> int:
    return sum(1 for keyword in keywords if keyword in text)


def detect_cue_drop(original_text: str, compressed_text: str) -> list[str]:
    missing_groups: list[str] = []
    for group_name, keywords in REVIEW_CUE_GROUPS.items():
        if count_present_keywords(original_text, keywords) > 0 and count_present_keywords(compressed_text, keywords) == 0:
            missing_groups.append(group_name)
    return missing_groups


def build_risk_reasons(
    *,
    original_text: str,
    compressed_text: str,
    ratio: float,
    anchor_breakdown: dict[str, dict[str, object]],
    anchor_count: int,
) -> tuple[int, list[str]]:
    reasons: list[str] = []
    score = 0

    strict = anchor_breakdown["strict"]
    soft = anchor_breakdown["soft"]

    original_len = len(original_text)
    compressed_len = len(compressed_text)

    if original_len >= 900:
        score += 4
        reasons.append("very_long_input")
    elif original_len >= 700:
        score += 3
        reasons.append("long_input")

    if strict["total"] and strict["kept"] < strict["total"]:
        score += 6
        reasons.append("strict_anchor_missing")
    elif anchor_count >= 10 and soft["rate"] is not None and float(soft["rate"]) < 0.67:
        score += 2
        reasons.append("soft_anchor_drop")

    if ratio < 0.32:
        score += 4
        reasons.append("over_compressed")
    elif ratio < 0.42:
        score += 3
        reasons.append("aggressive_compression")
    elif ratio > 0.90:
        score += 1
        reasons.append("under_compressed")

    if original_len >= 500 and compressed_len < 120:
        score += 2
        reasons.append("very_short_output")

    missing_cue_groups = detect_cue_drop(original_text, compressed_text)
    if missing_cue_groups:
        score += min(3, len(missing_cue_groups))
        reasons.append("cue_group_drop:" + ",".join(missing_cue_groups))

    return score, reasons


def review_tier_from_score(score: int) -> str:
    if score >= 8:
        return "P0"
    if score >= 4:
        return "P1"
    return "P2"


def enrich_row(row: dict) -> dict:
    original_text = normalize_whitespace(row["original_text"])
    compressed_text = normalize_whitespace(row["compressed_text"])
    ratio = char_compression_ratio(original_text, compressed_text)
    anchor_tokens = extract_anchor_tokens(original_text)
    anchor_breakdown = anchor_retention_breakdown(original_text, compressed_text)
    risk_score, risk_reasons = build_risk_reasons(
        original_text=original_text,
        compressed_text=compressed_text,
        ratio=ratio,
        anchor_breakdown=anchor_breakdown,
        anchor_count=len(anchor_tokens),
    )
    strict = anchor_breakdown["strict"]
    soft = anchor_breakdown["soft"]
    return {
        **row,
        "original_text": original_text,
        "compressed_text": compressed_text,
        "char_len": len(original_text),
        "compressed_char_len": len(compressed_text),
        "compression_ratio": round(ratio, 4),
        "length_bucket": infer_length_bucket(original_text),
        "contains_anchor": bool(row.get("contains_anchor", has_anchor_content(original_text))),
        "anchor_count": len(anchor_tokens),
        "strict_anchor_kept": strict["kept"],
        "strict_anchor_total": strict["total"],
        "strict_anchor_retention_rate": strict["rate"],
        "strict_anchor_missing_tokens": strict["missing_tokens"],
        "soft_anchor_kept": soft["kept"],
        "soft_anchor_total": soft["total"],
        "soft_anchor_retention_rate": soft["rate"],
        "soft_anchor_missing_tokens": soft["missing_tokens"],
        "risk_score": risk_score,
        "risk_reasons": risk_reasons,
        "review_tier": review_tier_from_score(risk_score),
        "review_status": "pending",
        "review_notes": "",
    }


def sort_queue(rows: list[dict]) -> list[dict]:
    tier_order = {"P0": 0, "P1": 1, "P2": 2}
    bucket_order = {"long": 0, "medium": 1, "short": 2}
    return sorted(
        rows,
        key=lambda row: (
            tier_order[row["review_tier"]],
            -row["risk_score"],
            bucket_order[row["length_bucket"]],
            -row["anchor_count"],
            -row["char_len"],
            row["sample_id"],
        ),
    )


def round_robin_fill(groups: dict[tuple[str, str], list[dict]], target_count: int) -> list[dict]:
    ordered_keys = sorted(
        groups.keys(),
        key=lambda item: (
            {"P1": 0, "P2": 1}[item[0]],
            {"long": 0, "medium": 1, "short": 2}[item[1]],
        ),
    )
    selected: list[dict] = []
    while len(selected) < target_count:
        progress = False
        for key in ordered_keys:
            bucket = groups[key]
            if bucket:
                selected.append(bucket.pop(0))
                progress = True
                if len(selected) >= target_count:
                    break
        if not progress:
            break
    return selected


def build_review_sample(rows: list[dict], target_count: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    p0_rows = [row for row in rows if row["review_tier"] == "P0"]
    p1_rows = [row for row in rows if row["review_tier"] == "P1"]
    p2_rows = [row for row in rows if row["review_tier"] == "P2"]

    sample: list[dict] = p0_rows[:]
    remaining = max(0, target_count - len(sample))
    if remaining == 0:
        return sample[:target_count]

    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in p1_rows + p2_rows:
        grouped[(row["review_tier"], row["length_bucket"])].append(row)
    for bucket_rows in grouped.values():
        rng.shuffle(bucket_rows)
        bucket_rows.sort(key=lambda row: (-row["risk_score"], -row["anchor_count"], -row["char_len"]))

    sample.extend(round_robin_fill(grouped, remaining))
    return sort_queue(sample)[:target_count]


def summarize(rows: list[dict], sample_rows: list[dict]) -> dict:
    by_tier = defaultdict(int)
    by_bucket = defaultdict(int)
    sample_by_tier = defaultdict(int)
    for row in rows:
        by_tier[row["review_tier"]] += 1
        by_bucket[row["length_bucket"]] += 1
    for row in sample_rows:
        sample_by_tier[row["review_tier"]] += 1
    return {
        "count": len(rows),
        "avg_compression_ratio": round(sum(row["compression_ratio"] for row in rows) / len(rows), 4) if rows else 0.0,
        "avg_anchor_count": round(sum(row["anchor_count"] for row in rows) / len(rows), 2) if rows else 0.0,
        "review_tier_counts": dict(sorted(by_tier.items())),
        "length_bucket_counts": dict(sorted(by_bucket.items())),
        "sample_count": len(sample_rows),
        "sample_tier_counts": dict(sorted(sample_by_tier.items())),
    }


def main() -> None:
    args = parse_args()
    rows = [enrich_row(row) for row in read_jsonl(args.input_file)]
    queue_rows = sort_queue(rows)
    sample_rows = build_review_sample(queue_rows, args.target_sample_count, args.seed)

    write_jsonl(args.queue_file, queue_rows)
    if args.sample_file:
        write_jsonl(args.sample_file, sample_rows)

    summary = {
        "input_file": str(args.input_file),
        "queue_file": str(args.queue_file),
        "sample_file": str(args.sample_file) if args.sample_file else "",
        **summarize(queue_rows, sample_rows),
    }
    if args.summary_file:
        args.summary_file.parent.mkdir(parents=True, exist_ok=True)
        args.summary_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
