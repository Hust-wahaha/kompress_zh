from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from zh_plaintext_compressor.common.teacher_prompt import (
    DEEPSEEK_V4_PRO_BALANCED_SYSTEM_PROMPT,
    DEEPSEEK_V4_PRO_BALANCED_USER_PROMPT,
    TEACHER_STYLE_TAG,
)

API_ENDPOINT = "https://api.deepseek.com/chat/completions"
DEFAULT_MODEL = "deepseek-v4-pro"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-file", type=Path, required=True)
    parser.add_argument("--output-file", type=Path, required=True)
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--api-key-env", type=str, default="DEEPSEEK_API_KEY")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--max-samples", type=int, default=None)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--sleep-seconds", type=float, default=0.5)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def existing_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {row["sample_id"] for row in read_jsonl(path)}


def call_api(*, model: str, api_key: str, original_text: str, timeout: int) -> dict:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": DEEPSEEK_V4_PRO_BALANCED_SYSTEM_PROMPT},
            {"role": "user", "content": DEEPSEEK_V4_PRO_BALANCED_USER_PROMPT.format(original_text=original_text)},
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
    parsed["_usage"] = body.get("usage", {})
    return parsed


def normalize_output(source_row: dict, teacher_row: dict, *, model: str) -> dict:
    return {
        "sample_id": source_row["sample_id"],
        "source_type": source_row["source_type"],
        "source_name": source_row["source_name"],
        "split": source_row.get("split", ""),
        "language": source_row.get("language", "zh"),
        "original_text": source_row["original_text"],
        "compressed_text": str(teacher_row["compressed_text"]).strip(),
        "style_tag": str(teacher_row.get("style_tag", TEACHER_STYLE_TAG)).strip() or TEACHER_STYLE_TAG,
        "contains_anchor": bool(teacher_row.get("contains_anchor", False)),
        "quality_notes": str(teacher_row.get("quality_notes", "常规压缩改写")).strip() or "常规压缩改写",
        "teacher_model": model,
        "teacher_prompt_version": "balanced_v1",
        "source_path": source_row.get("source_path", ""),
        "source_pool_tag": source_row.get("source_pool_tag", ""),
        "source_char_len": len(source_row["original_text"]),
        "usage": teacher_row.get("_usage", {}),
    }


def main() -> None:
    args = parse_args()
    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        raise RuntimeError(f"Missing API key env: {args.api_key_env}")

    source_rows = read_jsonl(args.input_file)
    if args.max_samples is not None:
        source_rows = source_rows[: args.max_samples]

    done_ids = existing_ids(args.output_file) if args.resume else set()
    pending_rows = [row for row in source_rows if row["sample_id"] not in done_ids]

    processed = 0
    for row in pending_rows:
        try:
            teacher_row = call_api(
                model=args.model,
                api_key=api_key,
                original_text=row["original_text"],
                timeout=args.timeout,
            )
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
        normalized = normalize_output(row, teacher_row, model=args.model)
        append_jsonl(args.output_file, normalized)
        processed += 1
        print(json.dumps({"sample_id": row["sample_id"], "processed": processed, "source_name": row["source_name"]}, ensure_ascii=False))
        if args.sleep_seconds > 0:
            time.sleep(args.sleep_seconds)


if __name__ == "__main__":
    main()
