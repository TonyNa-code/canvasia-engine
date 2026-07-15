from __future__ import annotations

import math
from typing import Any

try:
    from .runtime_player_view import clamp, get_safe_character_stage
except ImportError:  # pragma: no cover - exported native packages import siblings directly.
    from runtime_player_view import clamp, get_safe_character_stage


CHARACTER_POSITION_RATIOS = {
    "left": 0.24,
    "center": 0.50,
    "right": 0.76,
}
CHARACTER_MOTION_EASINGS = {"linear", "ease_in", "ease_out", "ease_in_out", "spring"}
CHARACTER_MOTION_DURATION_DEFAULT_MS = 600
CHARACTER_MOTION_DURATION_MIN_MS = 0
CHARACTER_MOTION_DURATION_MAX_MS = 10000


def _safe_number(value: Any, fallback: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return float(fallback)
    return number


def get_safe_character_position(value: Any, fallback: str = "center") -> str:
    safe_fallback = fallback if fallback in CHARACTER_POSITION_RATIOS else "center"
    candidate = str(value or "").strip()
    return candidate if candidate in CHARACTER_POSITION_RATIOS else safe_fallback


def get_character_position_ratio(value: Any) -> float:
    return CHARACTER_POSITION_RATIOS[get_safe_character_position(value)]


def get_safe_character_motion_easing(value: Any) -> str:
    candidate = str(value or "").strip()
    return candidate if candidate in CHARACTER_MOTION_EASINGS else "ease_out"


def get_safe_character_motion_duration_ms(
    value: Any,
    fallback: int = CHARACTER_MOTION_DURATION_DEFAULT_MS,
) -> int:
    safe_fallback = clamp(
        _safe_number(fallback, CHARACTER_MOTION_DURATION_DEFAULT_MS),
        CHARACTER_MOTION_DURATION_MIN_MS,
        CHARACTER_MOTION_DURATION_MAX_MS,
    )
    return round(
        clamp(
            _safe_number(value, safe_fallback),
            CHARACTER_MOTION_DURATION_MIN_MS,
            CHARACTER_MOTION_DURATION_MAX_MS,
        )
    )


def apply_character_motion_easing(progress: Any, easing: Any = "ease_out") -> float:
    t = clamp(_safe_number(progress, 0.0), 0.0, 1.0)
    safe_easing = get_safe_character_motion_easing(easing)
    if safe_easing == "linear":
        return t
    if safe_easing == "ease_in":
        return t * t * t
    if safe_easing == "ease_in_out":
        return 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2
    if safe_easing == "spring":
        # A small bounded overshoot keeps the pose readable while still feeling elastic.
        value = 1 - pow(1 - t, 3) + 0.08 * (1 - t) * math.sin(t * 3.5 * math.pi)
        return clamp(value, 0.0, 1.08)
    return 1 - pow(1 - t, 3)


def build_native_character_motion_state(
    previous_state: dict | None,
    block: dict | None,
    started_at_ms: int,
) -> dict:
    previous = previous_state if isinstance(previous_state, dict) else {}
    source = block if isinstance(block, dict) else {}
    character_id = str(source.get("characterId") or previous.get("characterId") or "").strip()
    previous_position = get_safe_character_position(previous.get("position"))
    target_position = get_safe_character_position(source.get("position"), previous_position)
    previous_stage = get_safe_character_stage(previous.get("stage"))
    target_stage = get_safe_character_stage(source.get("stage") or previous_stage)
    return {
        "characterId": character_id,
        "startedAtMs": int(started_at_ms),
        "durationMs": get_safe_character_motion_duration_ms(source.get("durationMs")),
        "easing": get_safe_character_motion_easing(source.get("easing")),
        "fromState": {
            "characterId": character_id,
            "expressionId": previous.get("expressionId"),
            "position": previous_position,
            "stage": previous_stage,
        },
        "targetState": {
            "characterId": character_id,
            "expressionId": source.get("expressionId") or previous.get("expressionId"),
            "position": target_position,
            "stage": target_stage,
        },
    }


def get_native_character_motion_progress(motion: dict | None, now_ms: int) -> float:
    if not isinstance(motion, dict):
        return 1.0
    duration_ms = get_safe_character_motion_duration_ms(motion.get("durationMs"))
    if duration_ms <= 0:
        return 1.0
    elapsed_ms = max(0, int(now_ms) - int(motion.get("startedAtMs") or 0))
    return clamp(elapsed_ms / duration_ms, 0.0, 1.0)


def is_native_character_motion_complete(motion: dict | None, now_ms: int) -> bool:
    return get_native_character_motion_progress(motion, now_ms) >= 1.0


def _interpolate_number(start: Any, end: Any, progress: float) -> float:
    return _safe_number(start, 0.0) + (_safe_number(end, 0.0) - _safe_number(start, 0.0)) * progress


def get_native_character_render_pose(
    target_state: dict | None,
    motion: dict | None,
    now_ms: int,
) -> dict:
    target = target_state if isinstance(target_state, dict) else {}
    target_stage = get_safe_character_stage(target.get("stage"))
    target_position = get_safe_character_position(target.get("position"))
    if not isinstance(motion, dict):
        return {
            **target,
            "position": target_position,
            "positionRatio": get_character_position_ratio(target_position),
            "stage": target_stage,
        }

    source = motion.get("fromState") if isinstance(motion.get("fromState"), dict) else {}
    source_stage = get_safe_character_stage(source.get("stage"))
    source_position = get_safe_character_position(source.get("position"))
    raw_progress = get_native_character_motion_progress(motion, now_ms)
    progress = apply_character_motion_easing(raw_progress, motion.get("easing"))
    stage = get_safe_character_stage(
        {
            "offsetX": _interpolate_number(source_stage["offsetX"], target_stage["offsetX"], progress),
            "offsetY": _interpolate_number(source_stage["offsetY"], target_stage["offsetY"], progress),
            "scale": _interpolate_number(source_stage["scale"], target_stage["scale"], progress),
            "opacity": _interpolate_number(source_stage["opacity"], target_stage["opacity"], progress),
            "layer": target_stage["layer"],
            "flipX": target_stage["flipX"] if raw_progress >= 0.5 else source_stage["flipX"],
        }
    )
    position_ratio = _interpolate_number(
        get_character_position_ratio(source_position),
        get_character_position_ratio(target_position),
        progress,
    )
    return {
        **target,
        "expressionId": target.get("expressionId") if raw_progress >= 0.5 else source.get("expressionId"),
        "position": target_position,
        "positionRatio": position_ratio,
        "stage": stage,
        "motionProgress": raw_progress,
    }
