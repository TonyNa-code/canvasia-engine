from __future__ import annotations


VISUAL_COMFORT_MODES = ("standard", "gentle", "static")
VISUAL_COMFORT_LABELS = {
    "standard": "原始演出",
    "gentle": "柔和模式",
    "static": "静态模式",
}
VISUAL_COMFORT_PROFILES = {
    "standard": {"motionScale": 1.0, "flashScale": 1.0, "transitionScale": 1.0},
    "gentle": {"motionScale": 0.35, "flashScale": 0.3, "transitionScale": 0.55},
    "static": {"motionScale": 0.0, "flashScale": 0.0, "transitionScale": 0.0},
}


def get_safe_visual_comfort_mode(value: object, fallback: str = "standard") -> str:
    safe_fallback = fallback if fallback in VISUAL_COMFORT_PROFILES else "standard"
    mode = str(value or safe_fallback).strip().lower()
    return mode if mode in VISUAL_COMFORT_PROFILES else safe_fallback


def get_visual_comfort_label(value: object) -> str:
    return VISUAL_COMFORT_LABELS[get_safe_visual_comfort_mode(value)]


def get_visual_comfort_profile(value: object) -> dict:
    return dict(VISUAL_COMFORT_PROFILES[get_safe_visual_comfort_mode(value)])


def _get_safe_non_negative_number(value: object, fallback: float = 0.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = float(fallback)
    return max(0.0, numeric)


def scale_visual_motion(value: object, mode: object, fallback: float = 0.0) -> float:
    return _get_safe_non_negative_number(value, fallback) * get_visual_comfort_profile(mode)["motionScale"]


def scale_visual_flash(value: object, mode: object, fallback: float = 0.0) -> float:
    return _get_safe_non_negative_number(value, fallback) * get_visual_comfort_profile(mode)["flashScale"]


def scale_visual_transition_ms(value: object, mode: object, fallback: float = 0.0) -> int:
    scaled = _get_safe_non_negative_number(value, fallback) * get_visual_comfort_profile(mode)["transitionScale"]
    return max(0, int(round(scaled)))


def get_visual_comfort_summary(value: object) -> dict:
    mode = get_safe_visual_comfort_mode(value)
    profile = get_visual_comfort_profile(mode)
    return {
        "mode": mode,
        "label": get_visual_comfort_label(mode),
        "motionPercent": int(round(profile["motionScale"] * 100)),
        "flashPercent": int(round(profile["flashScale"] * 100)),
        "transitionPercent": int(round(profile["transitionScale"] * 100)),
        "disablesTransientEffects": mode == "static",
    }
