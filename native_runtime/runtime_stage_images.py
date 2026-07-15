from __future__ import annotations

import math
from typing import Any


STAGE_IMAGE_ACTIONS = {"show", "update", "hide"}
STAGE_IMAGE_PLANES = {"back", "front"}
STAGE_IMAGE_POSITIONS = {"left", "center", "right"}
STAGE_IMAGE_POSITION_RATIOS = {"left": 0.24, "center": 0.50, "right": 0.76}
STAGE_IMAGE_EASINGS = {"linear", "ease_in", "ease_out", "ease_in_out", "spring"}
STAGE_IMAGE_DURATION_DEFAULT_MS = 520
DEFAULT_STAGE_IMAGE_TRANSFORM = {
    "offsetX": 0,
    "offsetY": 0,
    "width": 34,
    "opacity": 100,
    "rotation": 0,
    "layer": 0,
    "flipX": False,
}


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return min(max(value, minimum), maximum)


def _safe_number(value: Any, fallback: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return float(fallback)
    return number if math.isfinite(number) else float(fallback)


def _safe_bool(value: Any, fallback: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    normalized = str(value or "").strip().lower()
    if normalized in {"true", "1", "yes", "on"}:
        return True
    if normalized in {"false", "0", "no", "off"}:
        return False
    return fallback


def get_safe_stage_image_action(value: Any) -> str:
    action = str(value or "").strip()
    return action if action in STAGE_IMAGE_ACTIONS else "show"


def get_safe_stage_image_plane(value: Any) -> str:
    plane = str(value or "").strip()
    return plane if plane in STAGE_IMAGE_PLANES else "front"


def get_safe_stage_image_position(value: Any) -> str:
    position = str(value or "").strip()
    return position if position in STAGE_IMAGE_POSITIONS else "center"


def get_stage_image_position_ratio(value: Any) -> float:
    return STAGE_IMAGE_POSITION_RATIOS[get_safe_stage_image_position(value)]


def get_safe_stage_image_easing(value: Any) -> str:
    easing = str(value or "").strip()
    return easing if easing in STAGE_IMAGE_EASINGS else "ease_out"


def get_safe_stage_image_layer_id(value: Any, fallback: str = "layer_main") -> str:
    printable = "".join(character for character in str(value or "") if ord(character) >= 32 and ord(character) != 127)
    cleaned = "_".join(printable.strip().split())[:48]
    return cleaned or str(fallback or "layer_main")[:48]


def get_safe_stage_image_transform(source: Any = None) -> dict:
    raw = source if isinstance(source, dict) else {}
    return {
        "offsetX": round(_clamp(_safe_number(raw.get("offsetX"), 0), -80, 80)),
        "offsetY": round(_clamp(_safe_number(raw.get("offsetY"), 0), -70, 70)),
        "width": round(_clamp(_safe_number(raw.get("width"), 34), 4, 180)),
        "opacity": round(_clamp(_safe_number(raw.get("opacity"), 100), 0, 100)),
        "rotation": round(_clamp(_safe_number(raw.get("rotation"), 0), -180, 180)),
        "layer": round(_clamp(_safe_number(raw.get("layer"), 0), -20, 20)),
        "flipX": _safe_bool(raw.get("flipX"), False),
    }


def get_safe_stage_image_duration_ms(value: Any, fallback: int = STAGE_IMAGE_DURATION_DEFAULT_MS) -> int:
    safe_fallback = _clamp(_safe_number(fallback, STAGE_IMAGE_DURATION_DEFAULT_MS), 0, 10000)
    return round(_clamp(_safe_number(value, safe_fallback), 0, 10000))


def normalize_stage_image_state(source: Any = None, fallback: Any = None) -> dict:
    raw = source if isinstance(source, dict) else {}
    previous = fallback if isinstance(fallback, dict) else {}
    previous_transform = previous.get("transform") or previous.get("stage") or {}
    explicit_transform = raw.get("transform") if isinstance(raw.get("transform"), dict) else raw.get("stage")
    transform = {**previous_transform, **explicit_transform} if isinstance(explicit_transform, dict) else previous_transform
    return {
        "layerId": get_safe_stage_image_layer_id(raw.get("layerId") or previous.get("layerId")),
        "assetId": str(raw.get("assetId") or previous.get("assetId") or "").strip(),
        "plane": get_safe_stage_image_plane(raw.get("plane") or previous.get("plane")),
        "position": get_safe_stage_image_position(raw.get("position") or previous.get("position")),
        "transform": get_safe_stage_image_transform(transform),
    }


def clone_stage_image_state(source: Any = None) -> dict:
    normalized = normalize_stage_image_state(source)
    return {**normalized, "transform": dict(normalized["transform"])}


def apply_stage_image_easing(progress: Any, easing: Any = "ease_out") -> float:
    t = _clamp(_safe_number(progress, 0), 0, 1)
    safe_easing = get_safe_stage_image_easing(easing)
    if safe_easing == "linear":
        return t
    if safe_easing == "ease_in":
        return t * t * t
    if safe_easing == "ease_in_out":
        return 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2
    if safe_easing == "spring":
        value = 1 - pow(1 - t, 3) + 0.08 * (1 - t) * math.sin(t * 3.5 * math.pi)
        return _clamp(value, 0, 1.08)
    return 1 - pow(1 - t, 3)


def _build_motion(mode: str, layer_id: str, previous: dict, target: dict, block: dict, started_at_ms: int) -> dict:
    return {
        "mode": mode,
        "layerId": layer_id,
        "startedAtMs": int(started_at_ms),
        "durationMs": get_safe_stage_image_duration_ms(block.get("durationMs")),
        "easing": get_safe_stage_image_easing(block.get("easing")),
        "fromState": clone_stage_image_state(previous),
        "targetState": clone_stage_image_state(target),
    }


def apply_native_stage_image_block(visible_images: Any, block: Any, started_at_ms: int) -> dict:
    source = block if isinstance(block, dict) else {}
    image_map = {
        get_safe_stage_image_layer_id(layer_id): clone_stage_image_state(state)
        for layer_id, state in (visible_images.items() if isinstance(visible_images, dict) else [])
        if isinstance(state, dict)
    }
    layer_id = get_safe_stage_image_layer_id(source.get("layerId"))
    previous = image_map.get(layer_id)
    action = get_safe_stage_image_action(source.get("action"))
    if action == "hide":
        image_map.pop(layer_id, None)
        if not previous:
            return {"visibleImages": image_map, "motion": None, "leavingState": None}
        target = clone_stage_image_state(previous)
        target["transform"]["opacity"] = 0
        target["transform"]["offsetY"] = max(-70, target["transform"]["offsetY"] - 4)
        motion = _build_motion("hide", layer_id, previous, target, source, started_at_ms)
        return {"visibleImages": image_map, "motion": motion, "leavingState": clone_stage_image_state(previous)}

    target = normalize_stage_image_state({**source, "layerId": layer_id}, previous or {})
    image_map[layer_id] = target
    if previous:
        motion = _build_motion("move", layer_id, previous, target, source, started_at_ms)
    else:
        start = clone_stage_image_state(target)
        start["transform"]["opacity"] = 0
        start["transform"]["offsetY"] = min(70, start["transform"]["offsetY"] + 4)
        motion = _build_motion("show", layer_id, start, target, source, started_at_ms)
    return {"visibleImages": image_map, "motion": motion, "leavingState": None}


def get_native_stage_image_motion_progress(motion: Any, now_ms: int) -> float:
    if not isinstance(motion, dict):
        return 1.0
    duration_ms = get_safe_stage_image_duration_ms(motion.get("durationMs"))
    if duration_ms <= 0:
        return 1.0
    elapsed = max(0, int(now_ms) - int(motion.get("startedAtMs") or 0))
    return _clamp(elapsed / duration_ms, 0, 1)


def is_native_stage_image_motion_complete(motion: Any, now_ms: int) -> bool:
    return get_native_stage_image_motion_progress(motion, now_ms) >= 1.0


def _interpolate_number(start: Any, end: Any, progress: float) -> float:
    start_value = _safe_number(start, 0)
    return start_value + (_safe_number(end, start_value) - start_value) * progress


def get_native_stage_image_render_pose(target_state: Any, motion: Any, now_ms: int) -> dict:
    target = normalize_stage_image_state(target_state)
    if not isinstance(motion, dict):
        return {**target, "positionRatio": get_stage_image_position_ratio(target["position"]), "motionProgress": 1.0}
    source = normalize_stage_image_state(motion.get("fromState"), target)
    destination = normalize_stage_image_state(motion.get("targetState"), target)
    raw_progress = get_native_stage_image_motion_progress(motion, now_ms)
    progress = apply_stage_image_easing(raw_progress, motion.get("easing"))
    source_transform = source["transform"]
    target_transform = destination["transform"]
    transform = get_safe_stage_image_transform({
        key: _interpolate_number(source_transform[key], target_transform[key], progress)
        for key in ("offsetX", "offsetY", "width", "opacity", "rotation")
    } | {
        "layer": target_transform["layer"],
        "flipX": target_transform["flipX"] if raw_progress >= 0.5 else source_transform["flipX"],
    })
    position_ratio = _interpolate_number(
        get_stage_image_position_ratio(source["position"]),
        get_stage_image_position_ratio(destination["position"]),
        progress,
    )
    return {
        **destination,
        "assetId": destination["assetId"] if raw_progress >= 0.5 else source["assetId"],
        "positionRatio": position_ratio,
        "transform": transform,
        "motionProgress": raw_progress,
    }
