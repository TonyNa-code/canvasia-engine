from __future__ import annotations

from copy import deepcopy
import re


DEFAULT_DIALOG_BOX_CONFIG = {
    "preset": "moonlight",
    "shape": "rounded",
    "widthPercent": 76,
    "minHeight": 148,
    "paddingX": 18,
    "paddingY": 14,
    "backgroundColor": "#0c1422",
    "backgroundOpacity": 92,
    "borderColor": "#79dcff",
    "borderOpacity": 18,
    "textColor": "#f3f6ff",
    "speakerColor": "#ffffff",
    "hintColor": "#c8d6ea",
    "blurStrength": 10,
    "borderWidth": 1,
    "shadowStrength": 30,
    "panelAssetId": "",
    "panelAssetOpacity": 0,
    "panelAssetFit": "cover",
    "anchor": "bottom",
    "offsetXPercent": 0,
    "offsetYPercent": 0,
}

DEFAULT_GAME_UI_CONFIG = {
    "preset": "stellar",
    "layoutPreset": "balanced",
    "titleLayout": "center",
    "fontStyle": "modern",
    "fontFamily": "",
    "fontAssetId": "",
    "surfaceStyle": "glass",
    "brandMode": "project",
    "sidePanelMode": "full",
    "sidePanelPosition": "right",
    "topbarPosition": "top",
    "hudPosition": "top",
    "titleCardAnchor": "center",
    "titleCardOffsetXPercent": 0,
    "titleCardOffsetYPercent": 0,
    "layoutGap": 20,
    "sidePanelWidth": 320,
    "backgroundColor": "#071120",
    "backgroundAccentColor": "#6bd5ff",
    "panelColor": "#0c1422",
    "panelOpacity": 88,
    "textColor": "#f3f7ff",
    "mutedTextColor": "#bacce4",
    "accentColor": "#79dcff",
    "accentAltColor": "#7b7cff",
    "buttonTextColor": "#f8fcff",
    "borderColor": "#79dcff",
    "borderOpacity": 18,
    "cornerRadius": 22,
    "backdropBlur": 14,
    "stageVignette": 42,
    "motionIntensity": 70,
    "speakerFocusMode": "soft",
    "speakerFocusIntensity": 65,
    "speakerFocusTransitionMs": 240,
    "dialogueCameraMode": "soft",
    "dialogueCameraIntensity": 58,
    "dialogueCameraTransitionMs": 520,
    "titleBackgroundAssetId": "",
    "titleBackgroundFit": "cover",
    "titleBackgroundOpacity": 42,
    "titleLogoAssetId": "",
    "panelFrameAssetId": "",
    "panelFrameOpacity": 18,
    "panelFrameSlice": {"top": 24, "right": 24, "bottom": 24, "left": 24},
    "buttonFrameAssetId": "",
    "buttonHoverFrameAssetId": "",
    "buttonPressedFrameAssetId": "",
    "buttonDisabledFrameAssetId": "",
    "buttonFrameOpacity": 24,
    "buttonFrameSlice": {"top": 18, "right": 18, "bottom": 18, "left": 18},
    "saveSlotFrameAssetId": "",
    "systemPanelFrameAssetId": "",
    "uiOverlayAssetId": "",
    "uiOverlayOpacity": 8,
}


def clamp_int(value: object, fallback: int, minimum: int, maximum: int) -> int:
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        numeric = fallback
    return max(minimum, min(maximum, numeric))


def sanitize_hex_color(value: object, fallback: str) -> str:
    text = str(value or "").strip()
    return text.lower() if re.fullmatch(r"#[0-9A-Fa-f]{6}", text) else fallback


def sanitize_choice(value: object, allowed: set[str], fallback: str) -> str:
    normalized = str(value or fallback).strip().lower() or fallback
    return normalized if normalized in allowed else fallback


def sanitize_ui_frame_slice(value: object, fallback: dict) -> dict:
    source = value if isinstance(value, dict) else {}
    return {
        "top": clamp_int(source.get("top"), fallback.get("top", 18), 0, 96),
        "right": clamp_int(source.get("right"), fallback.get("right", 18), 0, 96),
        "bottom": clamp_int(source.get("bottom"), fallback.get("bottom", 18), 0, 96),
        "left": clamp_int(source.get("left"), fallback.get("left", 18), 0, 96),
    }


def build_default_dialog_box_config() -> dict:
    return deepcopy(DEFAULT_DIALOG_BOX_CONFIG)


def build_default_game_ui_config() -> dict:
    return deepcopy(DEFAULT_GAME_UI_CONFIG)


def sanitize_dialog_box_config(value: object) -> dict:
    source = value if isinstance(value, dict) else {}
    defaults = build_default_dialog_box_config()
    return {
        "preset": sanitize_choice(
            source.get("preset"),
            {"warm", "moonlight", "paper", "transparent", "custom"},
            defaults["preset"],
        ),
        "shape": sanitize_choice(source.get("shape"), {"rounded", "square", "capsule"}, defaults["shape"]),
        "widthPercent": clamp_int(source.get("widthPercent"), defaults["widthPercent"], 55, 100),
        "minHeight": clamp_int(source.get("minHeight"), defaults["minHeight"], 96, 320),
        "paddingX": clamp_int(source.get("paddingX"), defaults["paddingX"], 8, 72),
        "paddingY": clamp_int(source.get("paddingY"), defaults["paddingY"], 6, 48),
        "backgroundColor": sanitize_hex_color(source.get("backgroundColor"), defaults["backgroundColor"]),
        "backgroundOpacity": clamp_int(source.get("backgroundOpacity"), defaults["backgroundOpacity"], 0, 100),
        "borderColor": sanitize_hex_color(source.get("borderColor"), defaults["borderColor"]),
        "borderOpacity": clamp_int(source.get("borderOpacity"), defaults["borderOpacity"], 0, 100),
        "textColor": sanitize_hex_color(source.get("textColor"), defaults["textColor"]),
        "speakerColor": sanitize_hex_color(source.get("speakerColor"), defaults["speakerColor"]),
        "hintColor": sanitize_hex_color(source.get("hintColor"), defaults["hintColor"]),
        "blurStrength": clamp_int(source.get("blurStrength"), defaults["blurStrength"], 0, 24),
        "borderWidth": clamp_int(source.get("borderWidth"), defaults["borderWidth"], 0, 4),
        "shadowStrength": clamp_int(source.get("shadowStrength"), defaults["shadowStrength"], 0, 48),
        "panelAssetId": str(source.get("panelAssetId") or "").strip(),
        "panelAssetOpacity": clamp_int(source.get("panelAssetOpacity"), defaults["panelAssetOpacity"], 0, 100),
        "panelAssetFit": sanitize_choice(
            source.get("panelAssetFit"),
            {"cover", "contain"},
            defaults["panelAssetFit"],
        ),
        "anchor": sanitize_choice(source.get("anchor"), {"bottom", "center", "top", "free"}, defaults["anchor"]),
        "offsetXPercent": clamp_int(source.get("offsetXPercent"), defaults["offsetXPercent"], -35, 35),
        "offsetYPercent": clamp_int(source.get("offsetYPercent"), defaults["offsetYPercent"], -35, 35),
    }


def sanitize_game_ui_config(value: object) -> dict:
    source = value if isinstance(value, dict) else {}
    defaults = build_default_game_ui_config()
    choice_specs = {
        "preset": {"stellar", "warm", "paper", "minimal", "custom"},
        "layoutPreset": {"balanced", "cinematic", "compact", "minimal", "custom"},
        "titleLayout": {"center", "left", "poster"},
        "fontStyle": {"modern", "serif", "rounded"},
        "surfaceStyle": {"glass", "solid", "minimal"},
        "brandMode": {"project", "engine", "hidden"},
        "sidePanelMode": {"full", "compact", "hidden"},
        "sidePanelPosition": {"right", "left"},
        "topbarPosition": {"top", "bottom", "hidden"},
        "hudPosition": {"top", "top-left", "top-right", "bottom-left", "bottom-right", "hidden"},
        "titleCardAnchor": {"center", "left", "right", "top", "bottom", "free"},
        "speakerFocusMode": {"off", "soft", "cinematic"},
        "dialogueCameraMode": {"off", "soft", "cinematic"},
        "titleBackgroundFit": {"cover", "contain"},
    }
    result = {key: sanitize_choice(source.get(key), allowed, defaults[key]) for key, allowed in choice_specs.items()}
    result.update(
        {
            "fontFamily": str(source.get("fontFamily") or defaults["fontFamily"]).strip()[:80],
            "fontAssetId": str(source.get("fontAssetId") or defaults["fontAssetId"]).strip(),
            "titleCardOffsetXPercent": clamp_int(
                source.get("titleCardOffsetXPercent"), defaults["titleCardOffsetXPercent"], -35, 35
            ),
            "titleCardOffsetYPercent": clamp_int(
                source.get("titleCardOffsetYPercent"), defaults["titleCardOffsetYPercent"], -35, 35
            ),
            "layoutGap": clamp_int(source.get("layoutGap"), defaults["layoutGap"], 8, 48),
            "sidePanelWidth": clamp_int(source.get("sidePanelWidth"), defaults["sidePanelWidth"], 240, 460),
            "backgroundColor": sanitize_hex_color(source.get("backgroundColor"), defaults["backgroundColor"]),
            "backgroundAccentColor": sanitize_hex_color(
                source.get("backgroundAccentColor"), defaults["backgroundAccentColor"]
            ),
            "panelColor": sanitize_hex_color(source.get("panelColor"), defaults["panelColor"]),
            "panelOpacity": clamp_int(source.get("panelOpacity"), defaults["panelOpacity"], 35, 100),
            "textColor": sanitize_hex_color(source.get("textColor"), defaults["textColor"]),
            "mutedTextColor": sanitize_hex_color(source.get("mutedTextColor"), defaults["mutedTextColor"]),
            "accentColor": sanitize_hex_color(source.get("accentColor"), defaults["accentColor"]),
            "accentAltColor": sanitize_hex_color(source.get("accentAltColor"), defaults["accentAltColor"]),
            "buttonTextColor": sanitize_hex_color(source.get("buttonTextColor"), defaults["buttonTextColor"]),
            "borderColor": sanitize_hex_color(source.get("borderColor"), defaults["borderColor"]),
            "borderOpacity": clamp_int(source.get("borderOpacity"), defaults["borderOpacity"], 0, 100),
            "cornerRadius": clamp_int(source.get("cornerRadius"), defaults["cornerRadius"], 4, 42),
            "backdropBlur": clamp_int(source.get("backdropBlur"), defaults["backdropBlur"], 0, 28),
            "stageVignette": clamp_int(source.get("stageVignette"), defaults["stageVignette"], 0, 80),
            "motionIntensity": clamp_int(source.get("motionIntensity"), defaults["motionIntensity"], 0, 100),
            "speakerFocusIntensity": clamp_int(
                source.get("speakerFocusIntensity"), defaults["speakerFocusIntensity"], 0, 100
            ),
            "speakerFocusTransitionMs": clamp_int(
                source.get("speakerFocusTransitionMs"), defaults["speakerFocusTransitionMs"], 0, 1200
            ),
            "dialogueCameraIntensity": clamp_int(
                source.get("dialogueCameraIntensity"), defaults["dialogueCameraIntensity"], 0, 100
            ),
            "dialogueCameraTransitionMs": clamp_int(
                source.get("dialogueCameraTransitionMs"), defaults["dialogueCameraTransitionMs"], 0, 1600
            ),
            "titleBackgroundAssetId": str(source.get("titleBackgroundAssetId") or "").strip(),
            "titleBackgroundOpacity": clamp_int(
                source.get("titleBackgroundOpacity"), defaults["titleBackgroundOpacity"], 0, 100
            ),
            "titleLogoAssetId": str(source.get("titleLogoAssetId") or "").strip(),
            "panelFrameAssetId": str(source.get("panelFrameAssetId") or "").strip(),
            "panelFrameOpacity": clamp_int(source.get("panelFrameOpacity"), defaults["panelFrameOpacity"], 0, 100),
            "panelFrameSlice": sanitize_ui_frame_slice(source.get("panelFrameSlice"), defaults["panelFrameSlice"]),
            "buttonFrameAssetId": str(source.get("buttonFrameAssetId") or "").strip(),
            "buttonHoverFrameAssetId": str(source.get("buttonHoverFrameAssetId") or "").strip(),
            "buttonPressedFrameAssetId": str(source.get("buttonPressedFrameAssetId") or "").strip(),
            "buttonDisabledFrameAssetId": str(source.get("buttonDisabledFrameAssetId") or "").strip(),
            "buttonFrameOpacity": clamp_int(
                source.get("buttonFrameOpacity"), defaults["buttonFrameOpacity"], 0, 100
            ),
            "buttonFrameSlice": sanitize_ui_frame_slice(source.get("buttonFrameSlice"), defaults["buttonFrameSlice"]),
            "saveSlotFrameAssetId": str(source.get("saveSlotFrameAssetId") or "").strip(),
            "systemPanelFrameAssetId": str(source.get("systemPanelFrameAssetId") or "").strip(),
            "uiOverlayAssetId": str(source.get("uiOverlayAssetId") or "").strip(),
            "uiOverlayOpacity": clamp_int(source.get("uiOverlayOpacity"), defaults["uiOverlayOpacity"], 0, 100),
        }
    )
    return {key: result[key] for key in defaults}
