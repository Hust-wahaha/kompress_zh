from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import mean

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from zh_plaintext_compressor.common.schema import (
    MESSAGE_ROLES,
    SOURCE_POOL_REQUIRED_FIELDS,
    SUPPORTED_SPLITS,
    TRAINING_REQUIRED_FIELDS,
    anchor_retention,
    char_compression_ratio,
    has_chinese,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--mode", choices=("source-pool", "training"), required=True)
    parser.add_argument("--require-shorter", action="store_true")
    parser.add_argument("--min-anchor-retention", type=float, default=0.5)
    parser.add_argument("--anchor-policy", choices=("error", "warn", "off"), default="warn")
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def validate_source_pool(rows: list[dict]) -> tuple[int, list[float]]:
    errors = 0
    lengths = []
    for index, row in enumerate(rows, start=1):
        missing = SOURCE_POOL_REQUIRED_FIELDS - row.keys()
        if missing:
            print(f"[{index}] missing fields: {sorted(missing)}")
            errors += 1
            continue
        if row.get("language") != "zh":
            print(f"[{index}] unexpected language: {row.get('language')}")
            errors += 1
        if not has_chinese(row.get("original_text", "")):
            print(f"[{index}] original_text has no Chinese content")
            errors += 1
        lengths.append(len(row["original_text"]))
    return errors, lengths


def validate_training(
    rows: list[dict],
    require_shorter: bool,
    min_anchor_retention: float,
    anchor_policy: str,
) -> tuple[int, int, list[float]]:
    errors = 0
    warnings = 0
    ratios: list[float] = []
    for index, row in enumerate(rows, start=1):
        missing = TRAINING_REQUIRED_FIELDS - row.keys()
        if missing:
            print(f"[{index}] missing fields: {sorted(missing)}")
            errors += 1
            continue
        if row["split"] not in SUPPORTED_SPLITS:
            print(f"[{index}] unsupported split: {row['split']}")
            errors += 1
        messages = row.get("messages", [])
        if not isinstance(messages, list) or len(messages) != 3:
            print(f"[{index}] messages must contain exactly 3 turns")
            errors += 1
        else:
            roles = tuple(message.get("role") for message in messages)
            if roles != MESSAGE_ROLES:
                print(f"[{index}] unexpected message roles: {roles}")
                errors += 1
            assistant_text = messages[-1].get("content", "")
            if assistant_text != row["compressed_text"]:
                print(f"[{index}] assistant content does not match compressed_text")
                errors += 1
        if row.get("language") != "zh":
            print(f"[{index}] unexpected language: {row.get('language')}")
            errors += 1
        ratio = char_compression_ratio(row["original_text"], row["compressed_text"])
        ratios.append(ratio)
        if require_shorter and ratio >= 1.0:
            print(f"[{index}] compressed_text is not shorter than original_text")
            errors += 1
        if row.get("contains_anchor"):
            kept, total = anchor_retention(row["original_text"], row["compressed_text"])
            if total > 0 and kept / total < min_anchor_retention:
                if anchor_policy == "error":
                    print(f"[{index}] anchor retention too low: {kept}/{total}")
                    errors += 1
                elif anchor_policy == "warn":
                    print(f"[warn:{index}] anchor retention below threshold: {kept}/{total}")
                    warnings += 1
    return errors, warnings, ratios


def main() -> None:
    args = parse_args()
    rows = read_jsonl(args.path)
    if args.mode == "source-pool":
        errors, lengths = validate_source_pool(rows)
        summary = {
            "mode": args.mode,
            "count": len(rows),
            "errors": errors,
            "warnings": 0,
            "avg_chars": round(mean(lengths), 2) if lengths else 0.0,
        }
    else:
        errors, warnings, ratios = validate_training(
            rows,
            args.require_shorter,
            args.min_anchor_retention,
            args.anchor_policy,
        )
        summary = {
            "mode": args.mode,
            "count": len(rows),
            "errors": errors,
            "warnings": warnings,
            "anchor_policy": args.anchor_policy,
            "avg_compression_ratio": round(mean(ratios), 4) if ratios else 0.0,
        }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
