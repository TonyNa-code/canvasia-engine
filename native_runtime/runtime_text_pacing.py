from __future__ import annotations

import re
from typing import Any, Callable

try:
    from .runtime_text_effects import get_native_typewriter_step_delay_ms
except ImportError:  # pragma: no cover - exported native packages import from the same directory.
    from runtime_text_effects import get_native_typewriter_step_delay_ms


TEXT_PACING_PAUSE_MIN_MS = 50
TEXT_PACING_PAUSE_MAX_MS = 5000
TEXT_PACING_SPEEDS = ("slow", "normal", "fast", "instant", "inherit")
TEXT_PACING_MARKER_PATTERN = re.compile(
    r"\[\[\s*(pause|speed)\s*=\s*([^\[\]]+?)\s*\]\]",
    re.IGNORECASE,
)


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return min(max(value, minimum), maximum)


def get_safe_text_pacing_speed(value: Any, fallback: str = "normal") -> str:
    safe_fallback = str(fallback or "normal").strip().lower()
    if safe_fallback not in TEXT_PACING_SPEEDS or safe_fallback == "inherit":
        safe_fallback = "normal"
    speed = str(value or "").strip().lower()
    return speed if speed in TEXT_PACING_SPEEDS else safe_fallback


def get_safe_text_pacing_pause_ms(value: Any, fallback: int = 0) -> int:
    raw = str(value or "").strip()
    if not re.fullmatch(r"\d+(?:\.\d+)?", raw):
        return max(0, int(fallback or 0))
    milliseconds = float(raw) * 1000
    if milliseconds <= 0:
        return 0
    return round(_clamp(milliseconds, TEXT_PACING_PAUSE_MIN_MS, TEXT_PACING_PAUSE_MAX_MS))


def parse_runtime_text_pacing(value: Any) -> dict[str, Any]:
    source_text = str(value or "")
    if "[[" not in source_text:
        return {
            "sourceText": source_text,
            "plainText": source_text,
            "cues": [],
            "hasCues": False,
        }

    cues: list[dict[str, Any]] = []
    plain_parts: list[str] = []
    plain_length = 0
    source_index = 0

    for match in TEXT_PACING_MARKER_PATTERN.finditer(source_text):
        preceding = source_text[source_index : match.start()]
        plain_parts.append(preceding)
        plain_length += len(preceding)
        command = str(match.group(1) or "").lower()
        raw_value = str(match.group(2) or "").strip()
        cue: dict[str, Any] | None = None

        if command == "pause":
            pause_ms = get_safe_text_pacing_pause_ms(raw_value)
            if pause_ms > 0:
                cue = {"index": plain_length, "type": "pause", "pauseMs": pause_ms}
        elif command == "speed":
            speed = raw_value.lower()
            if speed in TEXT_PACING_SPEEDS:
                cue = {"index": plain_length, "type": "speed", "speed": speed}

        if cue:
            cues.append(cue)
        else:
            marker = match.group(0)
            plain_parts.append(marker)
            plain_length += len(marker)
        source_index = match.end()

    plain_parts.append(source_text[source_index:])
    plain_text = "".join(plain_parts)
    return {
        "sourceText": source_text,
        "plainText": plain_text,
        "cues": cues,
        "hasCues": bool(cues),
    }


def strip_runtime_text_pacing(value: Any) -> str:
    return str(parse_runtime_text_pacing(value)["plainText"])


def get_text_pacing_pause_ms_at(plan: dict | None, index: int) -> int:
    safe_index = max(0, int(index or 0))
    return sum(
        int(cue.get("pauseMs") or 0)
        for cue in (plan or {}).get("cues", [])
        if cue.get("type") == "pause" and int(cue.get("index") or 0) == safe_index
    )


def get_text_pacing_speed_at(plan: dict | None, index: int, fallback_speed: str = "normal") -> str:
    fallback = get_safe_text_pacing_speed(fallback_speed)
    if fallback == "instant":
        return "instant"

    safe_index = max(0, int(index or 0))
    speed = fallback
    for cue in (plan or {}).get("cues", []):
        if int(cue.get("index") or 0) > safe_index:
            break
        if cue.get("type") == "speed":
            speed = (
                fallback
                if cue.get("speed") == "inherit"
                else get_safe_text_pacing_speed(cue.get("speed"), fallback)
            )
    return speed


def get_next_text_pacing_index(
    plan: dict | None,
    current_index: int,
    get_next_index: Callable[[str, int], int],
) -> int:
    text = str((plan or {}).get("plainText") or "")
    safe_index = max(0, min(len(text), int(current_index or 0)))
    if safe_index >= len(text):
        return len(text)

    next_index = max(safe_index, min(len(text), int(get_next_index(text, safe_index))))
    for cue in (plan or {}).get("cues", []):
        cue_index = int(cue.get("index") or 0)
        if safe_index < cue_index < next_index:
            return cue_index
    return next_index


def get_initial_text_pacing_index(
    plan: dict | None,
    get_next_index: Callable[[str, int], int],
) -> int:
    if get_text_pacing_pause_ms_at(plan, 0) > 0:
        return 0
    return get_next_text_pacing_index(plan, 0, get_next_index)


def get_native_text_pacing_step_delay_ms(
    plan: dict | None,
    current_index: int,
    fallback_speed: str,
    visible_text: str = "",
    full_text: str = "",
) -> int:
    if get_safe_text_pacing_speed(fallback_speed) == "instant":
        return 0
    speed = get_text_pacing_speed_at(plan, current_index, fallback_speed)
    base_delay = (
        0
        if speed == "instant"
        else get_native_typewriter_step_delay_ms(speed, visible_text, full_text)
    )
    return base_delay + get_text_pacing_pause_ms_at(
        plan,
        current_index,
    )


def build_text_pacing_summary(value: Any) -> dict[str, Any]:
    plan = parse_runtime_text_pacing(value)
    pause_count = sum(1 for cue in plan["cues"] if cue.get("type") == "pause")
    speed_count = sum(1 for cue in plan["cues"] if cue.get("type") == "speed")
    parts = []
    if pause_count:
        parts.append(f"{pause_count} 处停顿")
    if speed_count:
        parts.append(f"{speed_count} 次语速变化")
    return {
        "label": " · ".join(parts) if parts else "尚未加入句内节奏",
        "pauseCount": pause_count,
        "speedCount": speed_count,
        "hasCues": bool(parts),
    }
