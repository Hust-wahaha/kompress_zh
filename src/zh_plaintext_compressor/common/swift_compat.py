from __future__ import annotations

from typing import Any


def get_model_processor_language_only(model_id: str, *, enabled: bool) -> tuple[Any, Any]:
    from swift import get_model_processor

    if not enabled:
        return get_model_processor(model_id)

    attempts = (
        {"model_kwargs": {"language_model_only": True}},
        {"language_model_only": True},
    )
    type_errors: list[str] = []
    for kwargs in attempts:
        try:
            return get_model_processor(model_id, **kwargs)
        except TypeError as exc:
            type_errors.append(f"{kwargs}: {exc}")

    raise RuntimeError(
        "Failed to enable language-model-only mode with the local swift version. "
        "Please update the call pattern in `swift_compat.py` before training or eval.\n"
        + "\n".join(type_errors)
    )

