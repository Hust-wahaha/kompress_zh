from __future__ import annotations

import re
from collections import Counter

SOURCE_POOL_REQUIRED_FIELDS = {
    "sample_id",
    "source_type",
    "source_name",
    "language",
    "original_text",
}

TRAINING_REQUIRED_FIELDS = {
    "sample_id",
    "source_type",
    "source_name",
    "split",
    "language",
    "original_text",
    "compressed_text",
    "style_tag",
    "contains_anchor",
    "messages",
    "dataset_variant",
    "task_tag",
}

OPTIONAL_TRAINING_FIELDS = {
    "quality_notes",
}

MESSAGE_ROLES = ("system", "user", "assistant")
SUPPORTED_SPLITS = ("train", "val", "test")

DEFAULT_DATASET_VARIANT = "rewrite_compress"
DEFAULT_TASK_TAG = "zh_plaintext_compress"
DEFAULT_STYLE_TAG = "lite_wenyan_structured"
DEFAULT_SYSTEM_PROMPT = (
    "你是一个面向中文 Agent 场景的压缩改写助手。"
    "你的任务是忠实压缩中文长段落，尽量缩短但不丢失关键约束、结论、路径、命令、数字与文件名。"
    "可轻量结构化、轻量文言化，但必须保持现代中文可读。"
)
DEFAULT_USER_PROMPT = (
    "请压缩改写下面这段中文文本。"
    "要求：保真、简洁、保留关键锚点；允许轻结构化和轻文言化，但不要写成纯古文。\n\n原文：\n{original_text}"
)

ANCHOR_PATTERNS = (
    r"https?://[^\s)>\]]+",
    r"[A-Za-z]:\\[^\s]+",
    r"(?:\./|\.\./|/)?(?:[\w.-]+/)+[\w.-]+",
    r"`[^`\n]+`",
    r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",
    r"--?[A-Za-z][A-Za-z0-9_-]*",
    r"\b\d+(?:\.\d+)?\b",
)


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text.strip())


def has_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def extract_anchor_tokens(text: str) -> list[str]:
    anchors: list[str] = []
    for pattern in ANCHOR_PATTERNS:
        anchors.extend(re.findall(pattern, text))
    seen: set[str] = set()
    unique = []
    for anchor in anchors:
        if anchor not in seen:
            unique.append(anchor)
            seen.add(anchor)
    return unique


def has_anchor_content(text: str) -> bool:
    return bool(extract_anchor_tokens(text))


def char_compression_ratio(original_text: str, compressed_text: str) -> float:
    if not original_text:
        return 0.0
    return len(compressed_text) / len(original_text)


def anchor_retention(original_text: str, compressed_text: str) -> tuple[int, int]:
    anchors = extract_anchor_tokens(original_text)
    if not anchors:
        return 0, 0
    kept = sum(1 for anchor in anchors if anchor in compressed_text)
    return kept, len(anchors)


def char_f1(reference_text: str, predicted_text: str) -> float:
    if not reference_text and not predicted_text:
        return 1.0
    if not reference_text or not predicted_text:
        return 0.0
    ref_counter = Counter(reference_text)
    pred_counter = Counter(predicted_text)
    overlap = sum((ref_counter & pred_counter).values())
    precision = overlap / len(predicted_text)
    recall = overlap / len(reference_text)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def build_messages(
    original_text: str,
    compressed_text: str,
    *,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    user_prompt: str = DEFAULT_USER_PROMPT,
) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt.format(original_text=original_text)},
        {"role": "assistant", "content": compressed_text},
    ]

