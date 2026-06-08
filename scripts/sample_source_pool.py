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

from zh_plaintext_compressor.common.naming import DEFAULT_SOURCE_POOL_TAG, source_pool_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-file", type=Path, default=None)
    parser.add_argument("--output-file", type=Path, required=True)
    parser.add_argument("--target-count", type=int, default=160)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--anchor-ratio", type=float, default=0.5)
    parser.add_argument("--short-ratio", type=float, default=0.35)
    parser.add_argument("--medium-ratio", type=float, default=0.45)
    parser.add_argument("--long-ratio", type=float, default=0.20)
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


def length_bucket(text: str) -> str:
    text_length = len(text)
    if text_length < 350:
        return "short"
    if text_length < 700:
        return "medium"
    return "long"


def source_group(source_name: str) -> str:
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
    order = ["medium", "short", "long"]
    index = 0
    while diff != 0:
        bucket = order[index % len(order)]
        counts[bucket] += 1 if diff > 0 else -1
        diff += -1 if diff > 0 else 1
        index += 1
    return counts


def sample_rows(rows: list[dict], args: argparse.Namespace) -> list[dict]:
    rng = random.Random(args.seed)
    for row in rows:
        row["length_bucket"] = length_bucket(row["original_text"])
        row["source_group"] = source_group(row["source_name"])
        row["char_len"] = len(row["original_text"])

    by_bucket_anchor: dict[tuple[str, bool], list[dict]] = defaultdict(list)
    for row in rows:
        by_bucket_anchor[(row["length_bucket"], bool(row.get("contains_anchor", False)))].append(row)

    for item_list in by_bucket_anchor.values():
        rng.shuffle(item_list)

    bucket_targets = target_counts(
        total=args.target_count,
        short_ratio=args.short_ratio,
        medium_ratio=args.medium_ratio,
        long_ratio=args.long_ratio,
    )
    anchor_targets = {
        bucket: round(count * args.anchor_ratio)
        for bucket, count in bucket_targets.items()
    }

    selected: list[dict] = []
    for bucket in ("short", "medium", "long"):
        total_needed = bucket_targets[bucket]
        anchor_needed = anchor_targets[bucket]
        anchor_rows = by_bucket_anchor[(bucket, True)]
        plain_rows = by_bucket_anchor[(bucket, False)]
        bucket_selected = anchor_rows[:anchor_needed]
        remaining = total_needed - len(bucket_selected)
        bucket_selected.extend(plain_rows[:remaining])
        if len(bucket_selected) < total_needed:
            anchor_extra_start = len(bucket_selected)
            bucket_selected.extend(anchor_rows[anchor_needed:anchor_needed + (total_needed - len(bucket_selected))])
        selected.extend(bucket_selected[:total_needed])

    if len(selected) < args.target_count:
        selected_ids = {row["sample_id"] for row in selected}
        leftovers = [row for row in rows if row["sample_id"] not in selected_ids]
        rng.shuffle(leftovers)
        selected.extend(leftovers[: args.target_count - len(selected)])

    rng.shuffle(selected)
    return selected[: args.target_count]


def summarize(rows: list[dict]) -> dict:
    by_bucket = defaultdict(int)
    by_anchor = defaultdict(int)
    by_group = defaultdict(int)
    for row in rows:
        by_bucket[row["length_bucket"]] += 1
        by_anchor[str(bool(row.get("contains_anchor", False))).lower()] += 1
        by_group[row["source_group"]] += 1
    return {
        "count": len(rows),
        "by_length_bucket": dict(sorted(by_bucket.items())),
        "by_contains_anchor": dict(sorted(by_anchor.items())),
        "by_source_group": dict(sorted(by_group.items())),
    }


def main() -> None:
    args = parse_args()
    input_file = args.input_file or source_pool_file(DEFAULT_SOURCE_POOL_TAG)
    rows = read_jsonl(input_file)
    selected = sample_rows(rows, args)
    write_jsonl(args.output_file, selected)
    print(json.dumps({"input_file": str(input_file), "output_file": str(args.output_file), **summarize(selected)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

