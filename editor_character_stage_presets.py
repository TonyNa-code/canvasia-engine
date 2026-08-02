from __future__ import annotations

import math
import re
import unicodedata


CHARACTER_STAGE_PRESET_LIMIT = 24
CHARACTER_STAGE_PRESET_NAME_MAX_LENGTH = 36
CHARACTER_STAGE_POSITIONS = frozenset({"left", "center", "right"})
DEFAULT_CHARACTER_STAGE = {
    "offsetX": 0,
    "offsetY": 0,
    "scale": 100,
    "opacity": 100,
    "layer": 0,
    "flipX": False,
}


def _clean_text(value: object) -> str:
    return " ".join(str(value or "").split()).strip()


def _round_like_javascript(value: float) -> int:
    return math.floor(value + 0.5)


def _safe_stage_number(value: object, fallback: int, minimum: int, maximum: int) -> int:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return fallback
    if not math.isfinite(number):
        return fallback
    return _round_like_javascript(min(max(number, minimum), maximum))


def _safe_stage_boolean(value: object, fallback: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off", ""}:
            return False
    return fallback


def sanitize_character_stage(value: object) -> dict:
    source = value if isinstance(value, dict) else {}
    return {
        "offsetX": _safe_stage_number(source.get("offsetX"), 0, -60, 60),
        "offsetY": _safe_stage_number(source.get("offsetY"), 0, -45, 45),
        "scale": _safe_stage_number(source.get("scale"), 100, 45, 220),
        "opacity": _safe_stage_number(source.get("opacity"), 100, 0, 100),
        "layer": _safe_stage_number(source.get("layer"), 0, -10, 10),
        "flipX": _safe_stage_boolean(source.get("flipX")),
    }


def normalize_character_stage_preset_id(value: object, fallback_name: object = "") -> str:
    normalized = unicodedata.normalize("NFKC", _clean_text(value)).lower()
    preset_id = re.sub(r"[^a-z0-9_]+", "_", normalized).strip("_")[:64]
    if preset_id:
        return preset_id

    normalized_name = unicodedata.normalize("NFKC", _clean_text(fallback_name)).lower()
    name_slug = re.sub(r"[^a-z0-9]+", "_", normalized_name).strip("_")[:42]
    return f"stage_{name_slug}" if name_slug else "stage_composition"


def _make_unique_preset_id(base_id: str, seen_ids: set[str]) -> str:
    candidate = base_id
    suffix = 2
    while candidate in seen_ids:
        candidate = f"{base_id[:61]}_{suffix:02d}"
        suffix += 1
    seen_ids.add(candidate)
    return candidate


def sanitize_character_stage_presets(presets: object) -> list[dict]:
    if not isinstance(presets, list):
        raise ValueError("项目构图预设必须是一个列表。")

    cleaned: list[dict] = []
    seen_ids: set[str] = set()
    for index, raw_preset in enumerate(presets[:CHARACTER_STAGE_PRESET_LIMIT]):
        if not isinstance(raw_preset, dict):
            raise ValueError("每个项目构图预设都必须是一个对象。")

        name = _clean_text(raw_preset.get("name"))
        if not name:
            continue
        if len(name) > CHARACTER_STAGE_PRESET_NAME_MAX_LENGTH:
            raise ValueError(f"项目构图名字不能超过 {CHARACTER_STAGE_PRESET_NAME_MAX_LENGTH} 个字符。")

        base_id = normalize_character_stage_preset_id(raw_preset.get("id"), name)
        cleaned.append(
            {
                "id": _make_unique_preset_id(base_id, seen_ids),
                "name": name,
                "position": raw_preset.get("position")
                if raw_preset.get("position") in CHARACTER_STAGE_POSITIONS
                else "center",
                "stage": sanitize_character_stage(raw_preset.get("stage")),
            }
        )
    return cleaned


def normalize_character_stage_presets_for_migration(value: object) -> list[dict]:
    if not isinstance(value, list):
        return []
    try:
        return sanitize_character_stage_presets(value)
    except ValueError:
        return []
