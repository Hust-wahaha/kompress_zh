from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from .paths import EXPERIMENTS_DIR, FINAL_DATA_DIR, INTERIM_DATA_DIR, ensure_experiment_subdirs

DEFAULT_DATASET_TAG = "rewrite_compress_v1"
DEFAULT_SOURCE_POOL_TAG = "source_pool_v1"
DEFAULT_MODEL_TAG = "qwen3.5-0.8b"

MODEL_TAG_ALIASES = {
    "Qwen/Qwen3.5-0.8B": "qwen3.5-0.8b",
    "Qwen/Qwen3.5-1.7B": "qwen3.5-1.7b",
    "Qwen/Qwen3.5-2B": "qwen3.5-2b",
    "Qwen/Qwen3.5-4B": "qwen3.5-4b",
    "Qwen/Qwen2.5-0.5B-Instruct": "qwen2.5-0.5b-instruct",
    "Qwen/Qwen2.5-1.5B-Instruct": "qwen2.5-1.5b-instruct",
    "Qwen/Qwen2.5-3B-Instruct": "qwen2.5-3b-instruct",
}


def slugify_tag(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", text.strip())
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-")
    return cleaned or "default"


def normalize_model_tag(model_id: str, model_tag: str | None = None) -> str:
    if model_tag:
        return slugify_tag(model_tag)
    return MODEL_TAG_ALIASES.get(model_id, slugify_tag(model_id.split("/")[-1]))


def dataset_file(split: str, dataset_tag: str = DEFAULT_DATASET_TAG) -> Path:
    return FINAL_DATA_DIR / f"{split}_{dataset_tag}.jsonl"


def dataset_summary_file(dataset_tag: str = DEFAULT_DATASET_TAG) -> Path:
    return FINAL_DATA_DIR / f"dataset_{dataset_tag}_summary.json"


def source_pool_file(source_pool_tag: str = DEFAULT_SOURCE_POOL_TAG) -> Path:
    return INTERIM_DATA_DIR / f"{source_pool_tag}.jsonl"


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def make_experiment_name(stage: str, dataset_tag: str, model_tag: str, suffix: str) -> str:
    return "_".join(
        (
            timestamp(),
            slugify_tag(stage),
            slugify_tag(dataset_tag),
            slugify_tag(model_tag),
            slugify_tag(suffix),
        )
    )


def make_experiment_dir(
    stage: str,
    dataset_tag: str,
    model_tag: str,
    suffix: str,
    base_dir: Path | None = None,
) -> Path:
    run_dir = (base_dir or EXPERIMENTS_DIR) / make_experiment_name(stage, dataset_tag, model_tag, suffix)
    return ensure_experiment_subdirs(run_dir)

