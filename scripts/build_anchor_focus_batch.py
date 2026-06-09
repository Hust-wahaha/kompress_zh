from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter, defaultdict, deque
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from zh_plaintext_compressor.common.schema import extract_anchor_tokens


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-file", type=Path, required=True)
    parser.add_argument("--output-file", type=Path, required=True)
    parser.add_argument("--target-count", type=int, default=96)
    parser.add_argument("--min-anchor-count", type=int, default=8)
    parser.add_argument("--short-ratio", type=float, default=0.30)
    parser.add_argument("--medium-ratio", type=float, default=0.40)
    parser.add_argument("--long-ratio", type=float, default=0.30)
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


def infer_source_group(source_name: str) -> str:
    normalized = source_name.lower()
    if "readme" in normalized:
        return "readme"
    if "progress" in normalized or "sync" in normalized:
        return "progress_sync"
    if "guide" in normalized or "plan" in normalized:
        return "plan_guide"
    if "analysis" in normalized or "survey" in normalized or "risk" in normalized:
        return "analysis_survey"
    return "other"


def target_counts(total: int, short_ratio: float, medium_ratio: float, long_ratio: float) -> dict[str, int]:
    counts = {
        "short": round(total * short_ratio),
        "medium": round(total * medium_ratio),
        "long": round(total * long_ratio),
    }
    diff = total - sum(counts.values())
    order = ["medium", "long", "short"]
    index = 0
    while diff != 0:
        bucket = order[index % len(order)]
        counts[bucket] += 1 if diff > 0 else -1
        diff += -1 if diff > 0 else 1
        index += 1
    return counts


def enrich_rows(rows: list[dict]) -> list[dict]:
    enriched = []
    for row in rows:
        anchor_count = len(extract_anchor_tokens(row["original_text"]))
        enriched.append(
            {
                **row,
                "anchor_count": anchor_count,
                "length_bucket": row.get("length_bucket") or infer_length_bucket(row["original_text"]),
                "source_group": row.get("source_group") or infer_source_group(row["source_name"]),
                "char_len": row.get("char_len") or len(row["original_text"]),
            }
        )
    return enriched


def rank_bucket_rows(rows: list[dict], seed: int) -> list[dict]:
    rng = random.Random(seed)
    by_group: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_group[row["source_group"]].append(row)

    for group_rows in by_group.values():
        rng.shuffle(group_rows)
        group_rows.sort(
            key=lambda row: (
                row["anchor_count"],
                row["char_len"],
            ),
            reverse=True,
        )

    group_order = deque(
        sorted(
            by_group.keys(),
            key=lambda group: (
                max(row["anchor_count"] for row in by_group[group]),
                len(by_group[group]),
            ),
            reverse=True,
        )
    )
    ranked: list[dict] = []
    while group_order:
        group = group_order.popleft()
        group_rows = by_group[group]
        if not group_rows:
            continue
        ranked.append(group_rows.pop(0))
        if group_rows:
            group_order.append(group)
    return ranked


def sample_rows(rows: list[dict], args: argparse.Namespace) -> list[dict]:
    enriched = enrich_rows(rows)
    eligible = [row for row in enriched if row["anchor_count"] >= args.min_anchor_count]
    bucket_targets = target_counts(
        total=args.target_count,
        short_ratio=args.short_ratio,
        medium_ratio=args.medium_ratio,
        long_ratio=args.long_ratio,
    )

    by_bucket = {
        bucket: rank_bucket_rows([row for row in eligible if row["length_bucket"] == bucket], args.seed + index)
        for index, bucket in enumerate(("short", "medium", "long"))
    }

    selected: list[dict] = []
    selected_ids: set[str] = set()
    for bucket in ("short", "medium", "long"):
        for row in by_bucket[bucket][: bucket_targets[bucket]]:
            selected.append(row)
            selected_ids.add(row["sample_id"])

    if len(selected) < args.target_count:
        leftovers = [
            row
            for row in rank_bucket_rows(eligible, args.seed + 100)
            if row["sample_id"] not in selected_ids
        ]
        for row in leftovers[: args.target_count - len(selected)]:
            selected.append(row)
            selected_ids.add(row["sample_id"])

    selected.sort(
        key=lambda row: (
            {"short": 0, "medium": 1, "long": 2}[row["length_bucket"]],
            -row["anchor_count"],
            -row["char_len"],
            row["sample_id"],
        )
    )
    return selected[: args.target_count]


def summarize(rows: list[dict], min_anchor_count: int) -> dict:
    by_bucket = Counter(row["length_bucket"] for row in rows)
    by_group = Counter(row["source_group"] for row in rows)
    anchor_counts = [row["anchor_count"] for row in rows]
    return {
        "count": len(rows),
        "min_anchor_count": min_anchor_count,
        "avg_anchor_count": round(sum(anchor_counts) / len(anchor_counts), 2) if anchor_counts else 0.0,
        "max_anchor_count": max(anchor_counts) if anchor_counts else 0,
        "by_length_bucket": dict(sorted(by_bucket.items())),
        "by_source_group": dict(sorted(by_group.items())),
    }


def main() -> None:
    args = parse_args()
    rows = read_jsonl(args.input_file)
    selected = sample_rows(rows, args)
    write_jsonl(args.output_file, selected)
    print(
        json.dumps(
            {
                "input_file": str(args.input_file),
                "output_file": str(args.output_file),
                **summarize(selected, args.min_anchor_count),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
