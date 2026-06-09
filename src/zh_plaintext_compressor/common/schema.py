from __future__ import annotations

from dataclasses import dataclass
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

_URL_PATTERN = re.compile(r"https?://[^\s`'\"<>)\]，。；：！？（）【】《》、]+")
_WINDOWS_PATH_PATTERN = re.compile(r"[A-Za-z]:\\[^\s`'\"<>，。；：！？（）【】《》、]+")
_PATH_PATTERN = re.compile(r"(?:\./|\.\./|/)?(?:[A-Za-z0-9_.-]+/){1,}[A-Za-z0-9_.-]+/?")
_OPTION_PATTERN = re.compile(r"(?<![A-Za-z0-9])--?[A-Za-z][A-Za-z0-9_-]*")
_BACKTICK_PATTERN = re.compile(r"`[^`\n]+`")
_FILENAME_PATTERN = re.compile(
    r"\b[A-Za-z0-9_.-]+\.(?:md|markdown|txt|json|jsonl|yaml|yml|xml|toml|ini|cfg|csv|tsv|py|ipynb|sh|bat|ps1|js|ts|tsx|jsx|html|css|sql)\b"
)
_SLASH_TOKEN_PATTERN = re.compile(r"\b[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\b")
_IDENTIFIER_PATTERN = re.compile(r"\b[A-Za-z][A-Za-z0-9_.-]*_[A-Za-z0-9_.-]+\b")
_HYPHENATED_ID_PATTERN = re.compile(r"\b[A-Za-z][A-Za-z0-9]*-[A-Za-z0-9_.-]+\b")
_SIGNIFICANT_NUMBER_PATTERN = re.compile(
    r"\b\d{4}-\d{2}-\d{2}\b"
    r"|\b\d{2}:\d{2}\b"
    r"|\b\d+\s*[~/-]\s*\d+\b"
    r"|\b\d+\.\d+\b"
    r"|\b\d+%\b"
    r"|\b\d{2,}\b"
)

_TOKEN_PRIORITY = {
    ("strict", "url"): 100,
    ("strict", "path"): 95,
    ("strict", "option"): 90,
    ("strict", "filename"): 85,
    ("strict", "repo_or_model"): 80,
    ("soft", "identifier"): 60,
    ("soft", "composite"): 55,
    ("soft", "number"): 50,
    ("soft", "literal"): 45,
}


@dataclass(frozen=True)
class AnchorToken:
    raw: str
    text: str
    category: str
    tier: str
    aliases: tuple[str, ...]
    match_mode: str = "exact"


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text.strip())


def has_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def _canonicalize_aliases(*tokens: str) -> tuple[str, ...]:
    aliases: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        normalized = token.strip().lower()
        if normalized and normalized not in seen:
            aliases.append(normalized)
            seen.add(normalized)
    return tuple(aliases)


def _strip_trailing_punctuation(token: str) -> str:
    return token.rstrip(".,;:!?)>]}，。；：！？）】")


def _normalize_generic_token(token: str) -> str:
    cleaned = token.strip().strip("`").strip()
    cleaned = _strip_trailing_punctuation(cleaned)
    return cleaned.rstrip("/")


def _normalize_numeric_token(token: str) -> str:
    normalized = re.sub(r"\s*([~:/-])\s*", r"\1", token.strip())
    return _strip_trailing_punctuation(normalized)


def _make_token(raw: str, text: str, category: str, tier: str, *, match_mode: str = "exact", aliases: tuple[str, ...] | None = None) -> AnchorToken:
    token_aliases = aliases or _canonicalize_aliases(text)
    return AnchorToken(
        raw=raw,
        text=text,
        category=category,
        tier=tier,
        aliases=token_aliases,
        match_mode=match_mode,
    )


def _token_priority(token: AnchorToken) -> int:
    return _TOKEN_PRIORITY.get((token.tier, token.category), 0)


def _looks_repo_or_model_id(token: str) -> bool:
    parts = token.split("/")
    if len(parts) != 2:
        return False
    left, right = parts
    if not left or not right:
        return False
    short_label = re.compile(r"^[A-Za-z]+\d*$")
    if len(left) <= 3 and len(right) <= 3 and short_label.fullmatch(left) and short_label.fullmatch(right):
        return False
    if any("." in part or "-" in part or "_" in part for part in parts):
        return True
    if any(char.isdigit() for char in token):
        return True
    if (left.isupper() and len(left) <= 4) or (right.isupper() and len(right) <= 4):
        return False
    return len(left) >= 6 or len(right) >= 6


def _classify_slash_token(token: str) -> AnchorToken | None:
    normalized = _normalize_generic_token(token)
    if not normalized:
        return None
    if _looks_repo_or_model_id(normalized):
        return _make_token(normalized, normalized, "repo_or_model", "strict")
    parts = [part for part in normalized.split("/") if part]
    if len(parts) < 2:
        return None
    if all(len(part) <= 4 or part.isupper() for part in parts):
        return _make_token(normalized, normalized, "composite", "soft", match_mode="all_parts")
    return _make_token(normalized, normalized, "composite", "soft")


def _classify_wrapped_literal(token: str) -> AnchorToken | None:
    normalized = _normalize_generic_token(token)
    if not normalized:
        return None
    if _URL_PATTERN.fullmatch(normalized):
        url = normalized.rstrip("/")
        return _make_token(
            normalized,
            url,
            "url",
            "strict",
            aliases=_canonicalize_aliases(url, re.sub(r"^https?://", "", url)),
        )
    if _WINDOWS_PATH_PATTERN.fullmatch(normalized):
        return _make_token(normalized, normalized, "path", "strict")
    if _PATH_PATTERN.fullmatch(normalized) and (normalized.startswith(("./", "../", "/")) or "." in normalized):
        return _make_token(normalized, normalized.rstrip("/"), "path", "strict")
    if _OPTION_PATTERN.fullmatch(normalized):
        return _make_token(normalized, normalized, "option", "strict")
    if _FILENAME_PATTERN.fullmatch(normalized):
        return _make_token(normalized, normalized, "filename", "strict")
    if _SLASH_TOKEN_PATTERN.fullmatch(normalized):
        return _classify_slash_token(normalized)
    if _IDENTIFIER_PATTERN.fullmatch(normalized):
        return _make_token(normalized, normalized, "identifier", "soft")
    if _HYPHENATED_ID_PATTERN.fullmatch(normalized):
        return _make_token(normalized, normalized, "identifier", "soft")
    if _SIGNIFICANT_NUMBER_PATTERN.fullmatch(normalized):
        numeric = _normalize_numeric_token(normalized)
        return _make_token(numeric, numeric, "number", "soft")
    if re.fullmatch(r"[A-Za-z0-9_.-]{2,}", normalized):
        return _make_token(normalized, normalized, "literal", "soft")
    return None


def _iter_anchor_tokens(text: str) -> list[AnchorToken]:
    candidates: list[tuple[tuple[int, int], AnchorToken]] = []
    blocked_spans: list[tuple[int, int]] = []

    def overlaps(span: tuple[int, int], others: list[tuple[int, int]]) -> bool:
        start, end = span
        return any(start < other_end and end > other_start for other_start, other_end in others)

    def add_match(match: re.Match[str], token: AnchorToken | None, *, allow_blocked_overlap: bool = False) -> None:
        if token is None:
            return
        start, end = match.span()
        if not allow_blocked_overlap and overlaps((start, end), blocked_spans):
            return
        candidates.append(((start, end), token))

    backtick_matches = list(_BACKTICK_PATTERN.finditer(text))
    blocked_spans.extend(match.span() for match in backtick_matches)

    for match in _URL_PATTERN.finditer(text):
        url = _normalize_generic_token(match.group(0))
        add_match(
            match,
            _make_token(
                match.group(0),
                url,
                "url",
                "strict",
                aliases=_canonicalize_aliases(url, re.sub(r"^https?://", "", url)),
            ),
        )
    for match in _WINDOWS_PATH_PATTERN.finditer(text):
        path = _normalize_generic_token(match.group(0))
        add_match(match, _make_token(match.group(0), path, "path", "strict"))
    for match in backtick_matches:
        inner = match.group(0)[1:-1].strip()
        add_match(match, _classify_wrapped_literal(inner), allow_blocked_overlap=True)
    for match in _OPTION_PATTERN.finditer(text):
        option = _normalize_generic_token(match.group(0))
        add_match(match, _make_token(match.group(0), option, "option", "strict"))
    for match in _FILENAME_PATTERN.finditer(text):
        filename = _normalize_generic_token(match.group(0))
        add_match(match, _make_token(match.group(0), filename, "filename", "strict"))
    for match in _PATH_PATTERN.finditer(text):
        path = _normalize_generic_token(match.group(0))
        if path.startswith(("./", "../", "/")) or "." in path or path.count("/") >= 2:
            add_match(match, _make_token(match.group(0), path.rstrip("/"), "path", "strict"))
    for match in _SLASH_TOKEN_PATTERN.finditer(text):
        add_match(match, _classify_slash_token(match.group(0)))
    for match in _IDENTIFIER_PATTERN.finditer(text):
        identifier = _normalize_generic_token(match.group(0))
        add_match(match, _make_token(match.group(0), identifier, "identifier", "soft"))
    for match in _HYPHENATED_ID_PATTERN.finditer(text):
        identifier = _normalize_generic_token(match.group(0))
        add_match(match, _make_token(match.group(0), identifier, "identifier", "soft"))
    for match in _SIGNIFICANT_NUMBER_PATTERN.finditer(text):
        numeric = _normalize_numeric_token(match.group(0))
        add_match(match, _make_token(match.group(0), numeric, "number", "soft"))

    selected: list[tuple[tuple[int, int], AnchorToken]] = []
    for span, token in sorted(
        candidates,
        key=lambda item: (-_token_priority(item[1]), -(item[0][1] - item[0][0]), item[0][0]),
    ):
        if overlaps(span, [selected_span for selected_span, _ in selected]):
            continue
        selected.append((span, token))

    deduped: dict[str, AnchorToken] = {}
    for _, token in sorted(selected, key=lambda item: (item[0][0], -(item[0][1] - item[0][0]))):
        key = token.text.lower()
        existing = deduped.get(key)
        if existing is None:
            deduped[key] = token
            continue
        existing_priority = _token_priority(existing)
        token_priority = _token_priority(token)
        if token_priority > existing_priority:
            deduped[key] = token
    return list(deduped.values())


def extract_anchor_tokens(text: str) -> list[str]:
    return [token.text for token in _iter_anchor_tokens(text)]


def has_anchor_content(text: str) -> bool:
    return bool(_iter_anchor_tokens(text))


def _matches_anchor(token: AnchorToken, normalized_text: str) -> bool:
    if any(alias in normalized_text for alias in token.aliases):
        return True
    if token.match_mode == "all_parts":
        parts = [part.strip().lower() for part in token.text.split("/") if part.strip()]
        return bool(parts) and all(part in normalized_text for part in parts)
    return False


def anchor_retention_breakdown(original_text: str, compressed_text: str) -> dict[str, dict[str, object]]:
    tokens = _iter_anchor_tokens(original_text)
    normalized_text = compressed_text.lower()

    def summarize(group: list[AnchorToken]) -> dict[str, object]:
        kept_tokens = [token.text for token in group if _matches_anchor(token, normalized_text)]
        total = len(group)
        kept = len(kept_tokens)
        missing_tokens = [token.text for token in group if token.text not in kept_tokens]
        return {
            "kept": kept,
            "total": total,
            "rate": (kept / total) if total else None,
            "kept_tokens": kept_tokens,
            "missing_tokens": missing_tokens,
        }

    strict_tokens = [token for token in tokens if token.tier == "strict"]
    soft_tokens = [token for token in tokens if token.tier == "soft"]
    return {
        "combined": summarize(tokens),
        "strict": summarize(strict_tokens),
        "soft": summarize(soft_tokens),
    }


def char_compression_ratio(original_text: str, compressed_text: str) -> float:
    if not original_text:
        return 0.0
    return len(compressed_text) / len(original_text)


def anchor_retention(original_text: str, compressed_text: str) -> tuple[int, int]:
    combined = anchor_retention_breakdown(original_text, compressed_text)["combined"]
    return int(combined["kept"]), int(combined["total"])


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
