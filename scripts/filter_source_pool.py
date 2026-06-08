from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-file", type=Path, required=True)
    parser.add_argument("--output-file", type=Path, required=True)
    parser.add_argument("--reject-file", type=Path, required=True)
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


def reject_reason(text: str) -> str | None:
    cleaned = text.strip()
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    if not lines:
        return "empty"

    if cleaned.endswith(("：", ":")):
        return "dangling_tail"

    if len(lines) >= 6:
        list_like_lines = sum(
            1
            for line in lines
            if re.match(r"^(?:[-*]|\d+[.)]|[A-Za-z_][A-Za-z0-9_]*：|`[^`]+`)", line)
        )
        if list_like_lines / len(lines) >= 0.8 and cleaned.count("。") <= 1:
            return "list_fragment"

    code_token_count = len(re.findall(r"`[^`\n]+`", cleaned))
    sentence_count = len(re.findall(r"[。！？]", cleaned))
    if code_token_count >= 6 and sentence_count <= 2:
        return "schema_glossary_heavy"

    if re.search(r"(这轮调研说明了一件很关键的事|原因很直接|推荐顺序如下|要求如下)\s*：?$", cleaned):
        return "dangling_lead_in"

    return None


def summarize(rows: list[dict]) -> dict:
    lengths = [len(row["original_text"]) for row in rows]
    return {
        "count": len(rows),
        "min_len": min(lengths) if lengths else 0,
        "max_len": max(lengths) if lengths else 0,
        "avg_len": round(sum(lengths) / len(lengths), 2) if lengths else 0.0,
    }


def main() -> None:
    args = parse_args()
    rows = read_jsonl(args.input_file)
    kept = []
    rejected = []
    reason_counter: Counter[str] = Counter()
    for row in rows:
        reason = reject_reason(row["original_text"])
        if reason is None:
            kept.append(row)
            continue
        reason_counter[reason] += 1
        rejected.append(
            {
                **row,
                "reject_reason": reason,
            }
        )

    write_jsonl(args.output_file, kept)
    write_jsonl(args.reject_file, rejected)
    print(
        json.dumps(
            {
                "input_count": len(rows),
                "kept_count": len(kept),
                "rejected_count": len(rejected),
                "reject_reasons": dict(reason_counter),
                "kept_summary": summarize(kept),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
