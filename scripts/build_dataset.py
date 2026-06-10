from __future__ import annotations

import argparse
import hashlib
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
    DEFAULT_SOURCE_POOL_TAG,
    dataset_file,
    dataset_summary_file,
    source_pool_file,
)
from zh_plaintext_compressor.common.schema import (
    DEFAULT_DATASET_VARIANT,
    DEFAULT_STYLE_TAG,
    DEFAULT_TASK_TAG,
    DEFAULT_USER_PROMPT,
    DEFAULT_SYSTEM_PROMPT,
    SUPPORTED_SPLITS,
    build_messages,
    char_compression_ratio,
    extract_anchor_tokens,
    has_anchor_content,
    has_chinese,
    normalize_whitespace,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    source_pool = subparsers.add_parser("source-pool")
    source_pool.add_argument("--input-dir", type=Path, required=True)
    source_pool.add_argument("--source-pool-tag", type=str, default=DEFAULT_SOURCE_POOL_TAG)
    source_pool.add_argument("--source-type", type=str, default="doc_chunk")
    source_pool.add_argument("--min-chars", type=int, default=200)
    source_pool.add_argument("--target-chars", type=int, default=500)
    source_pool.add_argument("--max-chars", type=int, default=800)
    source_pool.add_argument("--overlap-segments", type=int, default=0)

    training = subparsers.add_parser("training")
    training.add_argument("--input-file", type=Path, required=True)
    training.add_argument("--dataset-tag", type=str, default=DEFAULT_DATASET_TAG)
    training.add_argument("--system-prompt", type=str, default=DEFAULT_SYSTEM_PROMPT)
    training.add_argument("--user-prompt", type=str, default=DEFAULT_USER_PROMPT)
    training.add_argument("--default-style-tag", type=str, default=DEFAULT_STYLE_TAG)
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


def strip_markdown_noise(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    return text


def paragraphize(text: str) -> list[str]:
    text = strip_markdown_noise(text)
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            lines.append("")
            continue
        if re.fullmatch(r"[-*_]{3,}", line.strip()):
            continue
        lines.append(line.strip())
    paragraphs: list[str] = []
    buffer: list[str] = []
    for line in lines:
        if not line:
            if buffer:
                paragraphs.append("\n".join(buffer))
                buffer = []
            continue
        buffer.append(line)
    if buffer:
        paragraphs.append("\n".join(buffer))
    return [normalize_whitespace(paragraph) for paragraph in paragraphs if has_chinese(paragraph)]


def split_long_text(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    sentences = re.split(r"(?<=[。！？；])", text)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        candidate = sentence if not current else f"{current}{sentence}"
        if current and len(candidate) > max_chars:
            chunks.append(normalize_whitespace(current))
            current = sentence
        else:
            current = candidate
    if current:
        chunks.append(normalize_whitespace(current))
    return chunks


def build_source_pool_rows(
    input_dir: Path,
    source_type: str,
    min_chars: int,
    target_chars: int,
    max_chars: int,
    overlap_segments: int = 0,
) -> list[dict]:
    rows: list[dict] = []
    files = sorted(path for path in input_dir.rglob("*") if path.suffix.lower() in {".md", ".txt"})
    for file_path in files:
        text = file_path.read_text(encoding="utf-8")
        paragraphs = paragraphize(text)
        chunk_index = 0
        current_parts: list[str] = []
        current_length = 0
        for paragraph in paragraphs:
            for segment in split_long_text(paragraph, max_chars=max_chars):
                candidate_length = current_length + len(segment) + (2 if current_parts else 0)
                if current_parts and candidate_length > max_chars:
                    chunk_text = normalize_whitespace("\n\n".join(current_parts))
                    if len(chunk_text) >= min_chars:
                        rows.append(
                            make_source_pool_row(
                                file_path=file_path,
                                chunk_index=chunk_index,
                                source_type=source_type,
                                chunk_text=chunk_text,
                            )
                        )
                        chunk_index += 1
                    overlap = current_parts[-overlap_segments:] if overlap_segments > 0 else []
                    current_parts = overlap + [segment]
                    current_length = sum(len(part) for part in current_parts) + max(0, 2 * (len(current_parts) - 1))
                else:
                    current_parts.append(segment)
                    current_length = candidate_length
                if current_length >= target_chars:
                    chunk_text = normalize_whitespace("\n\n".join(current_parts))
                    if len(chunk_text) >= min_chars:
                        rows.append(
                            make_source_pool_row(
                                file_path=file_path,
                                chunk_index=chunk_index,
                                source_type=source_type,
                                chunk_text=chunk_text,
                            )
                        )
                        chunk_index += 1
                    overlap = current_parts[-overlap_segments:] if overlap_segments > 0 else []
                    current_parts = overlap[:]
                    current_length = sum(len(part) for part in current_parts) + max(0, 2 * (len(current_parts) - 1))
        if current_parts:
            chunk_text = normalize_whitespace("\n\n".join(current_parts))
            if len(chunk_text) >= min_chars:
                rows.append(
                    make_source_pool_row(
                        file_path=file_path,
                        chunk_index=chunk_index,
                        source_type=source_type,
                        chunk_text=chunk_text,
                    )
                )
    return rows


def make_source_pool_row(file_path: Path, chunk_index: int, source_type: str, chunk_text: str) -> dict:
    resolved_path = file_path.resolve()
    try:
        relative_path = resolved_path.relative_to(ROOT_DIR.resolve())
    except ValueError:
        relative_path = file_path
    return {
        "sample_id": f"{file_path.stem}-{chunk_index:04d}",
        "source_type": source_type,
        "source_name": file_path.name,
        "language": "zh",
        "original_text": chunk_text,
        "contains_anchor": has_anchor_content(chunk_text),
        "quality_notes": "auto_chunked_from_source_docs",
        "source_path": str(relative_path),
    }


def infer_split(sample_key: str) -> str:
    digest = hashlib.md5(sample_key.encode("utf-8")).hexdigest()
    mod = int(digest[:8], 16) % 10
    if mod < 8:
        return "train"
    if mod == 8:
        return "val"
    return "test"


def normalize_labeled_row(
    row: dict,
    index: int,
    *,
    system_prompt: str,
    user_prompt: str,
    default_style_tag: str,
) -> dict:
    original_text = normalize_whitespace(row["original_text"])
    compressed_text = normalize_whitespace(row["compressed_text"])
    sample_id = row.get("sample_id") or f"sample-{index:04d}"
    split = row.get("split") or infer_split(sample_id)
    if split not in SUPPORTED_SPLITS:
        raise ValueError(f"Unsupported split: {split}")
    style_tag = row.get("style_tag") or default_style_tag
    contains_anchor = bool(row.get("contains_anchor", has_anchor_content(original_text)))
    return {
        "sample_id": sample_id,
        "source_type": row.get("source_type", "doc_chunk"),
        "source_name": row.get("source_name", f"source-{index:04d}"),
        "split": split,
        "language": row.get("language", "zh"),
        "original_text": original_text,
        "compressed_text": compressed_text,
        "style_tag": style_tag,
        "contains_anchor": contains_anchor,
        "quality_notes": row.get("quality_notes", ""),
        "messages": build_messages(
            original_text,
            compressed_text,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        ),
        "dataset_variant": DEFAULT_DATASET_VARIANT,
        "task_tag": DEFAULT_TASK_TAG,
    }


def build_training_dataset(args: argparse.Namespace) -> None:
    rows = read_jsonl(args.input_file)
    normalized_rows = [
        normalize_labeled_row(
            row,
            index,
            system_prompt=args.system_prompt,
            user_prompt=args.user_prompt,
            default_style_tag=args.default_style_tag,
        )
        for index, row in enumerate(rows)
    ]
    splits = {split: [] for split in SUPPORTED_SPLITS}
    for row in normalized_rows:
        splits[row["split"]].append(row)

    for split, items in splits.items():
        write_jsonl(dataset_file(split, args.dataset_tag), items)

    ratios = [char_compression_ratio(row["original_text"], row["compressed_text"]) for row in normalized_rows]
    anchor_rows = [row for row in normalized_rows if row["contains_anchor"]]
    summary = {
        "dataset_tag": args.dataset_tag,
        "input_file": str(args.input_file),
        "count": len(normalized_rows),
        "split_counts": {split: len(items) for split, items in splits.items()},
        "avg_original_chars": round(mean(len(row["original_text"]) for row in normalized_rows), 2),
        "avg_compressed_chars": round(mean(len(row["compressed_text"]) for row in normalized_rows), 2),
        "avg_compression_ratio": round(mean(ratios), 4),
        "anchor_row_count": len(anchor_rows),
        "avg_anchor_count": round(mean(len(extract_anchor_tokens(row["original_text"])) for row in anchor_rows), 2)
        if anchor_rows
        else 0.0,
    }
    dataset_summary_file(args.dataset_tag).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def build_source_pool(args: argparse.Namespace) -> None:
    rows = build_source_pool_rows(
        input_dir=args.input_dir,
        source_type=args.source_type,
        min_chars=args.min_chars,
        target_chars=args.target_chars,
        max_chars=args.max_chars,
        overlap_segments=args.overlap_segments,
    )
    output_path = source_pool_file(args.source_pool_tag)
    write_jsonl(output_path, rows)
    summary = {
        "source_pool_tag": args.source_pool_tag,
        "input_dir": str(args.input_dir),
        "count": len(rows),
        "avg_chars": round(mean(len(row["original_text"]) for row in rows), 2) if rows else 0.0,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def main() -> None:
    args = parse_args()
    if args.command == "source-pool":
        build_source_pool(args)
        return
    build_training_dataset(args)


if __name__ == "__main__":
    main()
