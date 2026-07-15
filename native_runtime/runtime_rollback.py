from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Iterable


DEFAULT_ROLLBACK_LIMIT = 120
MIN_ROLLBACK_LIMIT = 2
MAX_ROLLBACK_LIMIT = 500
_ROLLBACK_IDENTITY_IGNORED_KEYS = frozenset(
    {
        "kind",
        "savedAt",
        "summaryText",
        "variableSummaryText",
        "textHistory",
    }
)


def normalize_rollback_limit(value: object, fallback: int = DEFAULT_ROLLBACK_LIMIT) -> int:
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        numeric = int(fallback)
    return max(MIN_ROLLBACK_LIMIT, min(MAX_ROLLBACK_LIMIT, numeric))


def clone_rollback_checkpoint(snapshot: object) -> dict[str, Any] | None:
    if not isinstance(snapshot, dict):
        return None
    checkpoint = copy.deepcopy(snapshot)
    checkpoint["kind"] = "rollback"
    return checkpoint


def build_rollback_checkpoint_key(snapshot: object) -> str:
    checkpoint = clone_rollback_checkpoint(snapshot)
    if checkpoint is None:
        return ""
    identity = {
        key: value
        for key, value in checkpoint.items()
        if key not in _ROLLBACK_IDENTITY_IGNORED_KEYS
    }
    payload = json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def append_rollback_checkpoint(
    checkpoints: Iterable[dict[str, Any]] | None,
    snapshot: object,
    *,
    limit: object = DEFAULT_ROLLBACK_LIMIT,
) -> list[dict[str, Any]]:
    safe_limit = normalize_rollback_limit(limit)
    timeline = [
        checkpoint
        for item in (checkpoints or [])
        if (checkpoint := clone_rollback_checkpoint(item)) is not None
    ][-safe_limit:]
    checkpoint = clone_rollback_checkpoint(snapshot)
    if checkpoint is None:
        return timeline

    checkpoint_key = build_rollback_checkpoint_key(checkpoint)
    if timeline and checkpoint_key and checkpoint_key == build_rollback_checkpoint_key(timeline[-1]):
        timeline[-1] = checkpoint
    else:
        timeline.append(checkpoint)
    return timeline[-safe_limit:]


def can_rollback_story(checkpoints: Iterable[dict[str, Any]] | None) -> bool:
    return sum(1 for item in (checkpoints or []) if isinstance(item, dict)) >= 2


def take_rollback_step(
    checkpoints: Iterable[dict[str, Any]] | None,
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    timeline = [
        checkpoint
        for item in (checkpoints or [])
        if (checkpoint := clone_rollback_checkpoint(item)) is not None
    ]
    if len(timeline) < 2:
        return timeline, None
    previous_checkpoint = copy.deepcopy(timeline[-2])
    return timeline[:-1], previous_checkpoint


def build_rollback_status(checkpoints: Iterable[dict[str, Any]] | None) -> dict[str, Any]:
    count = sum(1 for item in (checkpoints or []) if isinstance(item, dict))
    return {
        "checkpointCount": count,
        "availableSteps": max(0, count - 1),
        "canRollback": count >= 2,
    }


__all__ = [
    "DEFAULT_ROLLBACK_LIMIT",
    "MAX_ROLLBACK_LIMIT",
    "MIN_ROLLBACK_LIMIT",
    "append_rollback_checkpoint",
    "build_rollback_checkpoint_key",
    "build_rollback_status",
    "can_rollback_story",
    "clone_rollback_checkpoint",
    "normalize_rollback_limit",
    "take_rollback_step",
]
