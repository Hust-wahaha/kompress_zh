from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-files", nargs="+", type=Path, required=True)
    parser.add_argument("--output-file", type=Path, required=True)
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


def main() -> None:
    args = parse_args()
    merged = []
    seen_keys: set[tuple[str, str]] = set()
    for input_file in args.input_files:
        pool_tag = input_file.stem
        for row in read_jsonl(input_file):
            dedupe_key = (row.get("source_name", ""), row.get("original_text", ""))
            if dedupe_key in seen_keys:
                continue
            seen_keys.add(dedupe_key)
            merged.append(
                {
                    **row,
                    "sample_id": f"{pool_tag}__{row['sample_id']}",
                    "source_pool_tag": pool_tag,
                }
            )
    write_jsonl(args.output_file, merged)
    print(json.dumps({"output_file": str(args.output_file), "count": len(merged)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
