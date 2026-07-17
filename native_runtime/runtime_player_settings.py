from __future__ import annotations

import re

try:
    from .runtime_voice_mixer import sanitize_voice_mix_profiles
except ImportError:  # pragma: no cover - exported native packages import from the same directory.
    from runtime_voice_mixer import sanitize_voice_mix_profiles


DEFAULT_RUNTIME_PLAYER_SETTINGS = {
    "themeMode": "auto",
    "displayMode": "windowed",
    "textSpeed": "normal",
    "language": "",
    "textScalePercent": 100,
    "dialogBoxOpacityPercent": 100,
    "autoPlayDelayMs": 1800,
    "autoPlayWaitForVoice": "off",
    "masterVolume": 100,
    "bgmVolume": 85,
    "sfxVolume": 90,
    "voiceVolume": 100,
    "voiceDuckingEnabled": "on",
    "voiceDuckingRatio": 45,
    "voiceMix": {},
}
RUNTIME_THEME_MODES = ("auto", "light", "dark")
RUNTIME_DISPLAY_MODES = ("windowed", "fullscreen")
RUNTIME_TOGGLE_MODES = ("off", "on")
TEXT_SPEED_PRESETS = {
    "slow": 24,
    "normal": 42,
    "fast": 72,
    "instant": 10000,
}
TEXT_SPEED_LABELS = {
    "slow": "慢",
    "normal": "标准",
    "fast": "快",
    "instant": "瞬时",
}
AUTO_PLAY_DELAY_PRESETS = (900, 1400, 1800, 2400, 3200)
TEXT_SCALE_PRESETS = (90, 100, 110, 125)
DIALOG_BOX_OPACITY_PRESETS = (0, 35, 60, 80, 100)
VOICE_DUCKING_RATIO_PRESETS = (15, 30, 45, 60, 80, 100)


def _clamp_int(value: object, minimum: int, maximum: int, fallback: int) -> int:
    try:
        numeric = int(round(float(value)))
    except Exception:
        numeric = fallback
    return max(minimum, min(maximum, numeric))


def _normalize_language_code(value: object, fallback: str = "") -> str:
    raw_value = str(value or "").strip()
    if not raw_value or not re.fullmatch(r"[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8}){0,2}", raw_value):
        return fallback
    parts = raw_value.split("-")
    normalized = [parts[0].lower()]
    for index, part in enumerate(parts[1:], start=1):
        normalized.append(part.upper() if index == 1 and len(part) in {2, 3} else part)
    return "-".join(normalized)


def _get_safe_volume_percent(value: object, fallback: int = 100) -> int:
    return _clamp_int(value, 0, 100, fallback)


def get_safe_text_speed(value: object, fallback: str = "normal") -> str:
    safe_fallback = fallback if fallback in TEXT_SPEED_PRESETS else DEFAULT_RUNTIME_PLAYER_SETTINGS["textSpeed"]
    text_speed = str(value or safe_fallback).strip().lower()
    return text_speed if text_speed in TEXT_SPEED_PRESETS else safe_fallback


def sanitize_runtime_player_settings(value: dict | None) -> dict:
    source = value or {}
    theme_mode = str(source.get("themeMode") or DEFAULT_RUNTIME_PLAYER_SETTINGS["themeMode"]).strip().lower()
    if theme_mode not in RUNTIME_THEME_MODES:
        theme_mode = DEFAULT_RUNTIME_PLAYER_SETTINGS["themeMode"]
    display_mode = str(source.get("displayMode") or DEFAULT_RUNTIME_PLAYER_SETTINGS["displayMode"]).strip().lower()
    if display_mode not in RUNTIME_DISPLAY_MODES:
        display_mode = DEFAULT_RUNTIME_PLAYER_SETTINGS["displayMode"]
    auto_play_wait_for_voice = str(
        source.get("autoPlayWaitForVoice") or DEFAULT_RUNTIME_PLAYER_SETTINGS["autoPlayWaitForVoice"]
    ).strip().lower()
    if auto_play_wait_for_voice not in RUNTIME_TOGGLE_MODES:
        auto_play_wait_for_voice = DEFAULT_RUNTIME_PLAYER_SETTINGS["autoPlayWaitForVoice"]
    voice_ducking_enabled = str(
        source.get("voiceDuckingEnabled") or DEFAULT_RUNTIME_PLAYER_SETTINGS["voiceDuckingEnabled"]
    ).strip().lower()
    if voice_ducking_enabled not in RUNTIME_TOGGLE_MODES:
        voice_ducking_enabled = DEFAULT_RUNTIME_PLAYER_SETTINGS["voiceDuckingEnabled"]
    return {
        "themeMode": theme_mode,
        "displayMode": display_mode,
        "textSpeed": get_safe_text_speed(source.get("textSpeed"), DEFAULT_RUNTIME_PLAYER_SETTINGS["textSpeed"]),
        "language": _normalize_language_code(source.get("language"), ""),
        "textScalePercent": _clamp_int(
            source.get("textScalePercent"),
            min(TEXT_SCALE_PRESETS),
            max(TEXT_SCALE_PRESETS),
            DEFAULT_RUNTIME_PLAYER_SETTINGS["textScalePercent"],
        ),
        "dialogBoxOpacityPercent": _clamp_int(
            source.get("dialogBoxOpacityPercent"),
            min(DIALOG_BOX_OPACITY_PRESETS),
            max(DIALOG_BOX_OPACITY_PRESETS),
            DEFAULT_RUNTIME_PLAYER_SETTINGS["dialogBoxOpacityPercent"],
        ),
        "autoPlayDelayMs": _clamp_int(
            source.get("autoPlayDelayMs"),
            min(AUTO_PLAY_DELAY_PRESETS),
            max(AUTO_PLAY_DELAY_PRESETS),
            DEFAULT_RUNTIME_PLAYER_SETTINGS["autoPlayDelayMs"],
        ),
        "autoPlayWaitForVoice": auto_play_wait_for_voice,
        "voiceDuckingEnabled": voice_ducking_enabled,
        "masterVolume": _get_safe_volume_percent(
            source.get("masterVolume"), DEFAULT_RUNTIME_PLAYER_SETTINGS["masterVolume"]
        ),
        "bgmVolume": _get_safe_volume_percent(source.get("bgmVolume"), DEFAULT_RUNTIME_PLAYER_SETTINGS["bgmVolume"]),
        "sfxVolume": _get_safe_volume_percent(source.get("sfxVolume"), DEFAULT_RUNTIME_PLAYER_SETTINGS["sfxVolume"]),
        "voiceVolume": _get_safe_volume_percent(
            source.get("voiceVolume"), DEFAULT_RUNTIME_PLAYER_SETTINGS["voiceVolume"]
        ),
        "voiceDuckingRatio": _clamp_int(
            source.get("voiceDuckingRatio"),
            min(VOICE_DUCKING_RATIO_PRESETS),
            max(VOICE_DUCKING_RATIO_PRESETS),
            DEFAULT_RUNTIME_PLAYER_SETTINGS["voiceDuckingRatio"],
        ),
        "voiceMix": sanitize_voice_mix_profiles(source.get("voiceMix")),
    }


def build_project_default_runtime_player_settings(project: dict | None = None) -> dict:
    defaults = dict(DEFAULT_RUNTIME_PLAYER_SETTINGS)
    runtime_settings = project.get("runtimeSettings") if isinstance(project, dict) else {}
    if not isinstance(runtime_settings, dict):
        return defaults

    theme_mode = str(runtime_settings.get("defaultUiThemeMode") or defaults["themeMode"]).strip().lower()
    if theme_mode in RUNTIME_THEME_MODES:
        defaults["themeMode"] = theme_mode
    defaults["textSpeed"] = get_safe_text_speed(runtime_settings.get("defaultTextSpeed"), defaults["textSpeed"])
    defaults["bgmVolume"] = _get_safe_volume_percent(runtime_settings.get("defaultBgmVolume"), defaults["bgmVolume"])
    defaults["sfxVolume"] = _get_safe_volume_percent(runtime_settings.get("defaultSfxVolume"), defaults["sfxVolume"])
    defaults["voiceVolume"] = (
        _get_safe_volume_percent(runtime_settings.get("defaultVoiceVolume"), defaults["voiceVolume"])
        if runtime_settings.get("defaultVoiceEnabled") is not False
        else 0
    )
    defaults["voiceDuckingEnabled"] = "on" if runtime_settings.get("defaultVoiceDuckingEnabled") is not False else "off"
    defaults["voiceDuckingRatio"] = _clamp_int(
        runtime_settings.get("defaultVoiceDuckingRatio"),
        min(VOICE_DUCKING_RATIO_PRESETS),
        max(VOICE_DUCKING_RATIO_PRESETS),
        defaults["voiceDuckingRatio"],
    )
    return sanitize_runtime_player_settings(defaults)
