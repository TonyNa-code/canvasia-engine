from __future__ import annotations

from typing import Any


DEFAULT_FORMAL_SAVE_SLOT_COUNT = 24
MIN_FORMAL_SAVE_SLOT_COUNT = 3
MAX_FORMAL_SAVE_SLOT_COUNT = 120
PROJECT_RUNTIME_TEXT_SPEED_CPS = {
    "slow": 24,
    "normal": 42,
    "fast": 72,
    "instant": 10000,
}
PROJECT_RUNTIME_TEXT_SPEEDS = frozenset(PROJECT_RUNTIME_TEXT_SPEED_CPS)
PROJECT_RUNTIME_DIALOG_THEMES = frozenset({"project", "warm", "moonlight", "paper", "transparent"})
PROJECT_RUNTIME_UI_THEME_MODES = frozenset({"auto", "light", "dark"})


def _clean_key(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip().lower()
    return text or fallback


def clamp_int(value: Any, fallback: int, minimum: int, maximum: int) -> int:
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        numeric = fallback
    return max(minimum, min(maximum, numeric))


def build_default_project_runtime_settings() -> dict:
    return {
        "formalSaveSlotCount": DEFAULT_FORMAL_SAVE_SLOT_COUNT,
        "defaultTextSpeed": "normal",
        "defaultDialogTheme": "project",
        "defaultUiThemeMode": "auto",
        "defaultBgmVolume": 72,
        "defaultSfxVolume": 85,
        "defaultVoiceVolume": 92,
        "defaultVoiceEnabled": True,
        "defaultVoiceDuckingEnabled": True,
    }


def sanitize_project_runtime_settings(value: Any) -> dict:
    source = value if isinstance(value, dict) else {}
    defaults = build_default_project_runtime_settings()
    text_speed = _clean_key(source.get("defaultTextSpeed"), defaults["defaultTextSpeed"])
    dialog_theme = _clean_key(source.get("defaultDialogTheme"), defaults["defaultDialogTheme"])
    ui_theme_mode = _clean_key(source.get("defaultUiThemeMode"), defaults["defaultUiThemeMode"])
    return {
        "formalSaveSlotCount": clamp_int(
            source.get("formalSaveSlotCount"),
            DEFAULT_FORMAL_SAVE_SLOT_COUNT,
            MIN_FORMAL_SAVE_SLOT_COUNT,
            MAX_FORMAL_SAVE_SLOT_COUNT,
        ),
        "defaultTextSpeed": text_speed if text_speed in PROJECT_RUNTIME_TEXT_SPEEDS else defaults["defaultTextSpeed"],
        "defaultDialogTheme": dialog_theme if dialog_theme in PROJECT_RUNTIME_DIALOG_THEMES else defaults["defaultDialogTheme"],
        "defaultUiThemeMode": ui_theme_mode if ui_theme_mode in PROJECT_RUNTIME_UI_THEME_MODES else defaults["defaultUiThemeMode"],
        "defaultBgmVolume": clamp_int(source.get("defaultBgmVolume"), defaults["defaultBgmVolume"], 0, 100),
        "defaultSfxVolume": clamp_int(source.get("defaultSfxVolume"), defaults["defaultSfxVolume"], 0, 100),
        "defaultVoiceVolume": clamp_int(source.get("defaultVoiceVolume"), defaults["defaultVoiceVolume"], 0, 100),
        "defaultVoiceEnabled": source.get("defaultVoiceEnabled") is not False,
        "defaultVoiceDuckingEnabled": source.get("defaultVoiceDuckingEnabled") is not False,
    }


def get_runtime_settings_from_bundle(bundle: dict | None) -> dict:
    project = bundle.get("project") if isinstance(bundle, dict) and isinstance(bundle.get("project"), dict) else {}
    return sanitize_project_runtime_settings(project.get("runtimeSettings"))


def get_effective_text_speed(block: dict | None, runtime_settings: dict | None = None) -> str:
    source = block if isinstance(block, dict) else {}
    explicit = _clean_key(source.get("textSpeed"))
    if explicit in PROJECT_RUNTIME_TEXT_SPEED_CPS:
        return explicit
    settings = sanitize_project_runtime_settings(runtime_settings)
    default_speed = settings["defaultTextSpeed"]
    # Normal is Ren'Py's readable default, so omit a generated cps tag unless the user chose another project default.
    return default_speed if default_speed != "normal" else ""


def get_effective_text_cps(block: dict | None, runtime_settings: dict | None = None) -> int | None:
    speed = get_effective_text_speed(block, runtime_settings)
    return PROJECT_RUNTIME_TEXT_SPEED_CPS.get(speed)


def get_runtime_volume_ratio(runtime_settings: dict | None, key: str) -> float:
    settings = sanitize_project_runtime_settings(runtime_settings)
    return round(settings.get(key, 100) / 100, 2)


def get_renpy_runtime_summary(runtime_settings: dict | None) -> dict:
    settings = sanitize_project_runtime_settings(runtime_settings)
    default_speed = settings["defaultTextSpeed"]
    return {
        "defaultTextSpeed": default_speed,
        "defaultTextCps": PROJECT_RUNTIME_TEXT_SPEED_CPS[default_speed],
        "defaultBgmVolume": get_runtime_volume_ratio(settings, "defaultBgmVolume"),
        "defaultSfxVolume": get_runtime_volume_ratio(settings, "defaultSfxVolume"),
        "defaultVoiceVolume": get_runtime_volume_ratio(settings, "defaultVoiceVolume"),
        "defaultVoiceEnabled": bool(settings["defaultVoiceEnabled"]),
        "defaultVoiceDuckingEnabled": bool(settings["defaultVoiceDuckingEnabled"]),
        "formalSaveSlotCount": settings["formalSaveSlotCount"],
    }
