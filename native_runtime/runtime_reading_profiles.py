from __future__ import annotations


READING_PROFILE_IDS = ("standard", "comfortable", "large", "calm")
READING_PROFILE_LABELS = {
    "standard": "原作演出",
    "comfortable": "舒适阅读",
    "large": "大字阅读",
    "calm": "静态阅读",
    "custom": "自定义组合",
}
READING_PROFILE_DESCRIPTIONS = {
    "standard": "保留标准字号、文字速度和原始演出。",
    "comfortable": "字号略大，并柔化闪屏、震动和转场。",
    "large": "使用最大字号、较慢文字和柔和演出。",
    "calm": "放大文字并停止短暂动态演出。",
    "custom": "当前设置由玩家逐项调整。",
}
READING_PROFILES = {
    "standard": {
        "textSpeed": "normal",
        "textScalePercent": 100,
        "dialogBoxOpacityPercent": 100,
        "visualComfort": "standard",
    },
    "comfortable": {
        "textSpeed": "normal",
        "textScalePercent": 110,
        "dialogBoxOpacityPercent": 100,
        "visualComfort": "gentle",
    },
    "large": {
        "textSpeed": "slow",
        "textScalePercent": 125,
        "dialogBoxOpacityPercent": 100,
        "visualComfort": "gentle",
    },
    "calm": {
        "textSpeed": "normal",
        "textScalePercent": 110,
        "dialogBoxOpacityPercent": 100,
        "visualComfort": "static",
    },
}


def _clamp_int(value: object, minimum: int, maximum: int, fallback: int) -> int:
    try:
        numeric = int(round(float(value)))
    except (TypeError, ValueError):
        numeric = fallback
    return max(minimum, min(maximum, numeric))


def get_safe_reading_profile_id(value: object, fallback: str = "standard") -> str:
    safe_fallback = fallback if fallback in READING_PROFILES else "standard"
    profile_id = str(value or safe_fallback).strip().lower()
    return profile_id if profile_id in READING_PROFILES else safe_fallback


def get_reading_profile_label(value: object) -> str:
    profile_id = "custom" if value == "custom" else get_safe_reading_profile_id(value)
    return READING_PROFILE_LABELS[profile_id]


def get_reading_profile_description(value: object) -> str:
    profile_id = "custom" if value == "custom" else get_safe_reading_profile_id(value)
    return READING_PROFILE_DESCRIPTIONS[profile_id]


def get_safe_reading_text_scale_percent(value: object, fallback: int = 100) -> int:
    return _clamp_int(value, 90, 125, _clamp_int(fallback, 90, 125, 100))


def get_safe_dialog_box_opacity_percent(value: object, fallback: int = 100) -> int:
    return _clamp_int(value, 0, 100, _clamp_int(fallback, 0, 100, 100))


def apply_reading_profile(settings: dict | None = None, profile_id: object = "standard") -> dict:
    safe_profile_id = get_safe_reading_profile_id(profile_id)
    return {**(settings or {}), **READING_PROFILES[safe_profile_id]}


def detect_reading_profile(settings: dict | None = None) -> str:
    source = settings or {}
    normalized = {
        "textSpeed": str(source.get("textSpeed") or "normal").strip().lower(),
        "textScalePercent": get_safe_reading_text_scale_percent(source.get("textScalePercent")),
        "dialogBoxOpacityPercent": get_safe_dialog_box_opacity_percent(source.get("dialogBoxOpacityPercent")),
        "visualComfort": str(source.get("visualComfort") or "standard").strip().lower(),
    }
    for profile_id in READING_PROFILE_IDS:
        profile = READING_PROFILES[profile_id]
        if all(normalized.get(key) == value for key, value in profile.items()):
            return profile_id
    return "custom"


def get_reading_profile_summary(settings: dict | None = None) -> dict:
    source = settings or {}
    profile_id = detect_reading_profile(source)
    return {
        "profileId": profile_id,
        "label": get_reading_profile_label(profile_id),
        "description": get_reading_profile_description(profile_id),
        "textScalePercent": get_safe_reading_text_scale_percent(source.get("textScalePercent")),
        "dialogBoxOpacityPercent": get_safe_dialog_box_opacity_percent(source.get("dialogBoxOpacityPercent")),
    }
