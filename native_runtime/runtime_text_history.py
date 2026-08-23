from __future__ import annotations

import hashlib
import unicodedata
from collections.abc import Iterable
from typing import Any


DEFAULT_TEXT_HISTORY_LIMIT = 120
MAX_TEXT_HISTORY_QUERY_LENGTH = 80


def normalize_text_history_query(value: object) -> str:
    text = str(value or "").strip()[:MAX_TEXT_HISTORY_QUERY_LENGTH]
    return unicodedata.normalize("NFKC", text).casefold()


def _normalize_text_history_search_text(value: object) -> str:
    return unicodedata.normalize("NFKC", str(value or "").strip()).casefold()


def build_text_history_key(
    scene_id: object,
    block_index: object,
    block_type: object,
    text: object,
) -> str:
    try:
        safe_index = int(block_index)
    except (TypeError, ValueError):
        safe_index = 0
    text_digest = hashlib.sha1(str(text or "").encode("utf-8")).hexdigest()[:12]
    return f"{str(scene_id or '').strip()}:{safe_index}:{str(block_type or '').strip()}:{text_digest}"


def build_text_history_entry(
    *,
    scene_id: object,
    block_index: object,
    block_type: object,
    scene_name: object,
    speaker_name: object,
    text: object,
    voice_asset_id: object = "",
    voice_volume: object = 100,
    voice_profile_id: object = None,
) -> dict[str, Any] | None:
    safe_text = str(text or "").strip()
    if not safe_text:
        return None
    try:
        safe_voice_volume = max(0, min(100, int(round(float(voice_volume)))))
    except (TypeError, ValueError):
        safe_voice_volume = 100
    safe_block_type = str(block_type or "").strip()
    return {
        "key": build_text_history_key(scene_id, block_index, safe_block_type, safe_text),
        "sceneName": str(scene_name or "").strip(),
        "speakerName": str(speaker_name or "旁白").strip() or "旁白",
        "text": safe_text,
        "blockType": safe_block_type,
        "voiceAssetId": str(voice_asset_id or "").strip(),
        "voiceVolume": safe_voice_volume,
        "voiceProfileId": voice_profile_id,
    }


def append_text_history_entry(
    entries: Iterable[dict[str, Any]] | None,
    entry: object,
    *,
    limit: object = DEFAULT_TEXT_HISTORY_LIMIT,
) -> list[dict[str, Any]]:
    try:
        safe_limit = max(1, min(500, int(limit)))
    except (TypeError, ValueError):
        safe_limit = DEFAULT_TEXT_HISTORY_LIMIT
    history = [dict(item) for item in (entries or []) if isinstance(item, dict)]
    if not isinstance(entry, dict) or not str(entry.get("text") or "").strip():
        return history[-safe_limit:]
    entry_key = str(entry.get("key") or "").strip()
    if entry_key and any(str(item.get("key") or "").strip() == entry_key for item in history):
        return history[-safe_limit:]
    history.append(dict(entry))
    return history[-safe_limit:]


def collect_text_history_speakers(entries: Iterable[dict[str, Any]] | None) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in entries or []:
        if not isinstance(item, dict):
            continue
        speaker = str(item.get("speakerName") or "旁白").strip() or "旁白"
        if speaker not in seen:
            seen.add(speaker)
            result.append(speaker)
    return result


def filter_text_history_entries(
    entries: Iterable[dict[str, Any]] | None,
    *,
    query: object = "",
    speaker: object = "",
    voiced_only: bool = False,
) -> list[tuple[int, dict[str, Any]]]:
    safe_query = normalize_text_history_query(query)
    safe_speaker = str(speaker or "").strip()
    result: list[tuple[int, dict[str, Any]]] = []
    for index, item in enumerate(entries or []):
        if not isinstance(item, dict):
            continue
        item_speaker = str(item.get("speakerName") or "旁白").strip() or "旁白"
        if safe_speaker and item_speaker != safe_speaker:
            continue
        if voiced_only and not str(item.get("voiceAssetId") or "").strip():
            continue
        searchable = _normalize_text_history_search_text(
            "\n".join(
                str(item.get(key) or "")
                for key in ("sceneName", "speakerName", "text", "blockType")
            )
        )
        if safe_query and safe_query not in searchable:
            continue
        result.append((index, item))
    return result


def move_text_history_selection(
    filtered_entries: Iterable[tuple[int, dict[str, Any]]] | None,
    current_index: object,
    delta: object,
) -> int:
    matches = [int(index) for index, _item in (filtered_entries or [])]
    if not matches:
        return 0
    try:
        safe_current = int(current_index)
    except (TypeError, ValueError):
        safe_current = matches[-1]
    try:
        safe_delta = int(delta)
    except (TypeError, ValueError):
        safe_delta = 0
    if safe_current in matches:
        position = matches.index(safe_current)
    else:
        position = len(matches) - 1
    return matches[max(0, min(len(matches) - 1, position + safe_delta))]


def get_text_history_window(
    filtered_entries: Iterable[tuple[int, dict[str, Any]]] | None,
    selected_index: object,
    visible_count: object,
) -> list[tuple[int, dict[str, Any]]]:
    matches = list(filtered_entries or [])
    if not matches:
        return []
    try:
        safe_count = max(1, int(visible_count))
    except (TypeError, ValueError):
        safe_count = 1
    indices = [int(index) for index, _item in matches]
    try:
        selected_position = indices.index(int(selected_index))
    except (TypeError, ValueError):
        selected_position = len(matches) - 1
    start = max(0, min(max(0, len(matches) - safe_count), selected_position - safe_count + 1))
    return matches[start : start + safe_count]


__all__ = [
    "DEFAULT_TEXT_HISTORY_LIMIT",
    "MAX_TEXT_HISTORY_QUERY_LENGTH",
    "append_text_history_entry",
    "build_text_history_entry",
    "build_text_history_key",
    "collect_text_history_speakers",
    "filter_text_history_entries",
    "get_text_history_window",
    "move_text_history_selection",
    "normalize_text_history_query",
]
