from __future__ import annotations

import math
import re
from datetime import datetime
from pathlib import Path

try:
    from .runtime_variables import coerce_runtime_variable_value
except ImportError:  # pragma: no cover - exported native packages import from the same directory.
    from runtime_variables import coerce_runtime_variable_value


TRANSITION_DURATION_DEFAULT_MS = 360
TRANSITION_DURATION_MIN_MS = 0
TRANSITION_DURATION_MAX_MS = 5000
NATIVE_BASIC_TRANSITIONS = {"fade", "none"}
NATIVE_CHARACTER_TRANSITIONS = {"fade", "slide_left", "slide_right", "rise", "pop", "none"}

COLOR_BG = (12, 15, 28)
COLOR_PANEL = (18, 24, 40)
COLOR_PANEL_BORDER = (78, 106, 168)
COLOR_TEXT = (243, 246, 255)
COLOR_TEXT_MUTED = (160, 176, 204)
COLOR_ACCENT = (106, 154, 255)
COLOR_ACCENT_ALT = (173, 115, 255)
COLOR_WARNING = (255, 161, 110)

SAVE_DIALOG_PAGE_SIZE = 4
DEFAULT_FORMAL_SAVE_SLOT_COUNT = 24
MIN_FORMAL_SAVE_SLOT_COUNT = 3
MAX_FORMAL_SAVE_SLOT_COUNT = 120


def build_save_dialog_layout(width: int, height: int, visible_slot_count: int) -> dict:
    """Return responsive save-dialog geometry without depending on Pygame."""
    safe_width = max(1, int(width or 0))
    safe_height = max(1, int(height or 0))
    panel_width = max(1, min(max(1, safe_width - 32), 1040))
    panel_height = max(1, min(max(1, safe_height - 24), 620))
    panel_left = (safe_width - panel_width) // 2
    panel_top = (safe_height - panel_height) // 2
    panel_bottom = panel_top + panel_height
    compact = panel_height < 520

    horizontal_padding = 24 if compact else 28
    quick_top = panel_top + (72 if compact else 92)
    quick_height = 68 if compact else 72
    quick_rect = {
        "x": panel_left + horizontal_padding,
        "y": quick_top,
        "width": max(1, panel_width - horizontal_padding * 2),
        "height": quick_height,
    }

    visible_count = max(0, int(visible_slot_count or 0))
    column_count = 1 if panel_width < 560 else 2
    row_count = max(1, math.ceil(visible_count / column_count))
    card_gap_x = 10 if compact else 16
    card_gap_y = 10 if compact else 14
    cards_top = quick_top + quick_height + (10 if compact else 18)
    cards_bottom = panel_bottom - (68 if compact else 102)
    available_cards_height = max(1, cards_bottom - cards_top)
    card_height = max(
        54,
        min(126, (available_cards_height - card_gap_y * (row_count - 1)) // row_count),
    )
    card_width = max(
        1,
        (panel_width - horizontal_padding * 2 - card_gap_x * (column_count - 1)) // column_count,
    )
    cards = []
    for index in range(visible_count):
        row = index // column_count
        column = index % column_count
        cards.append(
            {
                "x": panel_left + horizontal_padding + column * (card_width + card_gap_x),
                "y": cards_top + row * (card_height + card_gap_y),
                "width": card_width,
                "height": card_height,
            }
        )

    button_height = 28 if compact else 34
    button_y = panel_bottom - (40 if compact else 58)
    controls_left = panel_left + horizontal_padding
    controls_width = max(1, panel_width - horizontal_padding * 2)
    preferred_widths = [96, 96, 116, 96]
    control_gap = 10 if sum(preferred_widths) + 30 <= controls_width else 6
    if sum(preferred_widths) + control_gap * 3 > controls_width:
        unit_width = max(40, int((controls_width - control_gap * 3) / 4.2))
        control_widths = [unit_width, unit_width, int(unit_width * 1.2), unit_width]
    else:
        control_widths = preferred_widths
    controls = []
    control_x = controls_left
    for control_width in control_widths:
        controls.append(
            {
                "x": control_x,
                "y": button_y,
                "width": control_width,
                "height": button_height,
            }
        )
        control_x += control_width + control_gap

    return {
        "compact": compact,
        "panel": {"x": panel_left, "y": panel_top, "width": panel_width, "height": panel_height},
        "titlePosition": (panel_left + horizontal_padding, panel_top + (14 if compact else 24)),
        "subtitlePosition": (panel_left + horizontal_padding, panel_top + (48 if compact else 58)),
        "quick": quick_rect,
        "cards": cards,
        "hintPosition": (panel_left + horizontal_padding, panel_bottom - (64 if compact else 88)),
        "controls": controls,
    }

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

DIALOG_BOX_PRESETS = {
    "moonlight": {
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
        "panelAssetOpacity": 0,
        "panelAssetFit": "cover",
    },
    "warm": {
        "preset": "warm",
        "shape": "rounded",
        "widthPercent": 76,
        "minHeight": 148,
        "paddingX": 16,
        "paddingY": 14,
        "backgroundColor": "#fffaf5",
        "backgroundOpacity": 92,
        "borderColor": "#8f6548",
        "borderOpacity": 18,
        "textColor": "#332117",
        "speakerColor": "#7f5438",
        "hintColor": "#6d5b4f",
        "blurStrength": 8,
        "borderWidth": 1,
        "shadowStrength": 18,
        "panelAssetOpacity": 0,
        "panelAssetFit": "cover",
    },
    "paper": {
        "preset": "paper",
        "shape": "square",
        "widthPercent": 76,
        "minHeight": 156,
        "paddingX": 18,
        "paddingY": 16,
        "backgroundColor": "#fff7e8",
        "backgroundOpacity": 95,
        "borderColor": "#b08659",
        "borderOpacity": 28,
        "textColor": "#4a2f1d",
        "speakerColor": "#7f5438",
        "hintColor": "#7f6a54",
        "blurStrength": 4,
        "borderWidth": 1,
        "shadowStrength": 16,
        "panelAssetOpacity": 0,
        "panelAssetFit": "cover",
    },
    "transparent": {
        "preset": "transparent",
        "shape": "capsule",
        "widthPercent": 88,
        "minHeight": 132,
        "paddingX": 14,
        "paddingY": 10,
        "backgroundColor": "#08111b",
        "backgroundOpacity": 0,
        "borderColor": "#7fe6ff",
        "borderOpacity": 0,
        "textColor": "#f4f8ff",
        "speakerColor": "#ffffff",
        "hintColor": "#d0daf0",
        "blurStrength": 0,
        "borderWidth": 0,
        "shadowStrength": 0,
        "panelAssetOpacity": 0,
        "panelAssetFit": "cover",
    },
}

SCREEN_COLOR_GRADE_DEFAULTS = {
    "brightness": 100,
    "contrast": 100,
    "saturation": 100,
    "hue": 0,
    "temperature": 0,
    "vignette": 0,
}
SCREEN_COLOR_GRADE_LIMITS = {
    "brightness": (40, 180),
    "contrast": (40, 180),
    "saturation": (0, 220),
    "hue": (-180, 180),
    "temperature": (-100, 100),
    "vignette": (0, 100),
}


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def clamp_int(value, minimum: int, maximum: int, fallback: int) -> int:
    try:
        numeric = int(round(float(value)))
    except Exception:
        numeric = fallback
    return max(minimum, min(maximum, numeric))


def get_safe_option(value, allowed: set[str], fallback: str) -> str:
    safe_value = str(value or "").strip()
    return safe_value if safe_value in allowed else fallback


def get_project_formal_save_slot_count(project: dict | None) -> int:
    runtime_settings = (project or {}).get("runtimeSettings") or {}
    try:
        value = int(runtime_settings.get("formalSaveSlotCount", DEFAULT_FORMAL_SAVE_SLOT_COUNT))
    except Exception:
        value = DEFAULT_FORMAL_SAVE_SLOT_COUNT
    return max(MIN_FORMAL_SAVE_SLOT_COUNT, min(MAX_FORMAL_SAVE_SLOT_COUNT, value))


def get_safe_audio_fade_ms(value, fallback: int = 0) -> int:
    return clamp_int(value, 0, 30000, fallback)


def get_safe_volume_percent(value, fallback: int = 100) -> int:
    return clamp_int(value, 0, 100, fallback)


def get_safe_transition_duration_ms(value, fallback: int = TRANSITION_DURATION_DEFAULT_MS) -> int:
    safe_fallback = clamp_int(
        fallback,
        TRANSITION_DURATION_MIN_MS,
        TRANSITION_DURATION_MAX_MS,
        TRANSITION_DURATION_DEFAULT_MS,
    )
    return clamp_int(value, TRANSITION_DURATION_MIN_MS, TRANSITION_DURATION_MAX_MS, safe_fallback)


def get_safe_basic_transition(value) -> str:
    safe_value = str(value or "fade").strip()
    return safe_value if safe_value in NATIVE_BASIC_TRANSITIONS else "fade"


def get_safe_character_transition(value) -> str:
    safe_value = str(value or "fade").strip()
    return safe_value if safe_value in NATIVE_CHARACTER_TRANSITIONS else "fade"


def build_native_transition_state(value, duration_ms, started_at_ms: int, direction: str = "in") -> dict | None:
    transition = get_safe_character_transition(value)
    safe_duration_ms = get_safe_transition_duration_ms(duration_ms)
    if transition == "none" or safe_duration_ms <= 0:
        return None
    return {
        "transition": transition,
        "durationMs": safe_duration_ms,
        "startedAtMs": max(0, int(started_at_ms or 0)),
        "direction": "out" if direction == "out" else "in",
    }


def get_native_transition_progress(state: dict | None, now_ms: int) -> float:
    if not state:
        return 1.0
    duration_ms = max(1, get_safe_transition_duration_ms(state.get("durationMs")))
    started_at_ms = clamp_int(state.get("startedAtMs"), 0, max(0, int(now_ms or 0)), 0)
    return clamp((int(now_ms or 0) - started_at_ms) / duration_ms, 0.0, 1.0)


def ease_out_cubic(progress: float) -> float:
    safe_progress = clamp(progress, 0.0, 1.0)
    return 1.0 - (1.0 - safe_progress) ** 3


def get_safe_music_end_mode(value) -> str:
    safe_value = str(value or "").strip()
    if safe_value in {"until_next_music", "scene_end", "after_block"}:
        return safe_value
    return "until_next_music"


def get_safe_screen_color_grade(source) -> dict:
    grade = source if isinstance(source, dict) else {}
    safe_grade = {}
    for key, fallback in SCREEN_COLOR_GRADE_DEFAULTS.items():
        minimum, maximum = SCREEN_COLOR_GRADE_LIMITS[key]
        safe_grade[key] = clamp_int(grade.get(key), minimum, maximum, fallback)
    return safe_grade


def get_music_scope_from_block(block: dict | None, scene_id: str | None) -> dict:
    source = block or {}
    end_mode = get_safe_music_end_mode(source.get("endMode"))
    end_block_id = str(source.get("endBlockId") or "").strip() if end_mode == "after_block" else ""
    if end_mode == "after_block" and not end_block_id:
        end_mode = "until_next_music"
    return {
        "sceneId": str(scene_id or ""),
        "endMode": end_mode,
        "endBlockId": end_block_id,
        "fadeOutMs": get_safe_audio_fade_ms(source.get("fadeOutMs"), 600),
    }


def parse_hex_color(value, fallback):
    safe_value = str(value or "").strip()
    if len(safe_value) == 7 and safe_value.startswith("#"):
        try:
            return tuple(int(safe_value[index:index + 2], 16) for index in (1, 3, 5))
        except Exception:
            return fallback
    return fallback


def get_safe_frame_slice(value, fallback: dict) -> dict:
    source = value if isinstance(value, dict) else {}
    return {
        "top": clamp_int(source.get("top"), 0, 96, int(fallback.get("top", 18))),
        "right": clamp_int(source.get("right"), 0, 96, int(fallback.get("right", 18))),
        "bottom": clamp_int(source.get("bottom"), 0, 96, int(fallback.get("bottom", 18))),
        "left": clamp_int(source.get("left"), 0, 96, int(fallback.get("left", 18))),
    }


def with_alpha(color, opacity_percent: int) -> tuple[int, int, int, int]:
    alpha = clamp_int(opacity_percent, 0, 100, 100)
    return (*color, int(round(alpha * 2.55)))


def normalize_video_time_seconds(value, fallback: float = 0.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = fallback
    if not math.isfinite(numeric):
        numeric = fallback
    return max(0.0, numeric)


def format_video_timestamp(seconds: float | int | None) -> str:
    total_seconds = normalize_video_time_seconds(seconds)
    minutes = int(total_seconds // 60)
    seconds_remainder = total_seconds - minutes * 60
    if seconds_remainder.is_integer():
        return f"{minutes}:{int(seconds_remainder):02d}"
    return f"{minutes}:{seconds_remainder:04.1f}"


def build_video_clip_label(start_time: float, end_time: float) -> str:
    if start_time <= 0 and end_time <= 0:
        return "整段播放"
    return f"{format_video_timestamp(start_time)} -> {format_video_timestamp(end_time) if end_time > 0 else '结尾'}"


def get_safe_project_dialog_box_preset(value) -> str:
    return value if value == "custom" or value in DIALOG_BOX_PRESETS else DEFAULT_DIALOG_BOX_CONFIG["preset"]


def get_safe_project_dialog_box_shape(value) -> str:
    return value if value in {"rounded", "square", "capsule"} else DEFAULT_DIALOG_BOX_CONFIG["shape"]


def get_project_dialog_box_preset_config(preset) -> dict:
    safe_preset = get_safe_project_dialog_box_preset(preset)
    return {
        **DEFAULT_DIALOG_BOX_CONFIG,
        **(DIALOG_BOX_PRESETS.get(safe_preset) or {}),
        "preset": safe_preset,
    }


def get_project_dialog_box_config(project: dict | None) -> dict:
    source = (project or {}).get("dialogBoxConfig") or {}
    base = get_project_dialog_box_preset_config(source.get("preset"))
    return {
        **base,
        "preset": get_safe_project_dialog_box_preset(source.get("preset", base["preset"])),
        "shape": get_safe_project_dialog_box_shape(source.get("shape", base["shape"])),
        "widthPercent": clamp_int(source.get("widthPercent"), 55, 100, base["widthPercent"]),
        "minHeight": clamp_int(source.get("minHeight"), 96, 320, base["minHeight"]),
        "paddingX": clamp_int(source.get("paddingX"), 8, 72, base["paddingX"]),
        "paddingY": clamp_int(source.get("paddingY"), 6, 48, base["paddingY"]),
        "backgroundColor": parse_hex_color(source.get("backgroundColor"), parse_hex_color(base["backgroundColor"], COLOR_PANEL)),
        "backgroundOpacity": clamp_int(source.get("backgroundOpacity"), 0, 100, base["backgroundOpacity"]),
        "borderColor": parse_hex_color(source.get("borderColor"), parse_hex_color(base["borderColor"], COLOR_PANEL_BORDER)),
        "borderOpacity": clamp_int(source.get("borderOpacity"), 0, 100, base["borderOpacity"]),
        "textColor": parse_hex_color(source.get("textColor"), parse_hex_color(base["textColor"], COLOR_TEXT)),
        "speakerColor": parse_hex_color(source.get("speakerColor"), parse_hex_color(base["speakerColor"], COLOR_TEXT)),
        "hintColor": parse_hex_color(source.get("hintColor"), parse_hex_color(base["hintColor"], COLOR_TEXT_MUTED)),
        "blurStrength": clamp_int(source.get("blurStrength"), 0, 24, base["blurStrength"]),
        "borderWidth": clamp_int(source.get("borderWidth"), 0, 4, base["borderWidth"]),
        "shadowStrength": clamp_int(source.get("shadowStrength"), 0, 48, base["shadowStrength"]),
        "panelAssetId": str(source.get("panelAssetId") or "").strip(),
        "panelAssetOpacity": clamp_int(source.get("panelAssetOpacity"), 0, 100, base["panelAssetOpacity"]),
        "panelAssetFit": "contain" if source.get("panelAssetFit") == "contain" else "cover",
        "anchor": get_safe_option(
            source.get("anchor"),
            {"bottom", "center", "top", "free"},
            base["anchor"],
        ),
        "offsetXPercent": clamp_int(source.get("offsetXPercent"), -35, 35, base["offsetXPercent"]),
        "offsetYPercent": clamp_int(source.get("offsetYPercent"), -35, 35, base["offsetYPercent"]),
    }


def get_project_game_ui_config(project: dict | None) -> dict:
    source = (project or {}).get("gameUiConfig") or {}
    base = {**DEFAULT_GAME_UI_CONFIG}
    return {
        **base,
        "preset": get_safe_option(
            source.get("preset"),
            {"stellar", "warm", "paper", "minimal", "custom"},
            base["preset"],
        ),
        "layoutPreset": get_safe_option(
            source.get("layoutPreset"),
            {"balanced", "cinematic", "compact", "minimal", "custom"},
            base["layoutPreset"],
        ),
        "titleLayout": get_safe_option(
            source.get("titleLayout"),
            {"center", "left", "poster"},
            base["titleLayout"],
        ),
        "fontStyle": get_safe_option(source.get("fontStyle"), {"modern", "serif", "rounded"}, base["fontStyle"]),
        "fontFamily": str(source.get("fontFamily") or base.get("fontFamily") or "").strip()[:80],
        "fontAssetId": str(source.get("fontAssetId") or base.get("fontAssetId") or "").strip(),
        "surfaceStyle": get_safe_option(
            source.get("surfaceStyle"),
            {"glass", "solid", "minimal"},
            base["surfaceStyle"],
        ),
        "brandMode": get_safe_option(source.get("brandMode"), {"project", "engine", "hidden"}, base["brandMode"]),
        "sidePanelMode": get_safe_option(
            source.get("sidePanelMode"),
            {"full", "compact", "hidden"},
            base["sidePanelMode"],
        ),
        "sidePanelPosition": get_safe_option(
            source.get("sidePanelPosition"),
            {"right", "left"},
            base["sidePanelPosition"],
        ),
        "topbarPosition": get_safe_option(
            source.get("topbarPosition"),
            {"top", "bottom", "hidden"},
            base["topbarPosition"],
        ),
        "hudPosition": get_safe_option(
            source.get("hudPosition"),
            {"top", "top-left", "top-right", "bottom-left", "bottom-right", "hidden"},
            base["hudPosition"],
        ),
        "titleCardAnchor": get_safe_option(
            source.get("titleCardAnchor"),
            {"center", "left", "right", "top", "bottom", "free"},
            base["titleCardAnchor"],
        ),
        "titleCardOffsetXPercent": clamp_int(
            source.get("titleCardOffsetXPercent"),
            -35,
            35,
            base["titleCardOffsetXPercent"],
        ),
        "titleCardOffsetYPercent": clamp_int(
            source.get("titleCardOffsetYPercent"),
            -35,
            35,
            base["titleCardOffsetYPercent"],
        ),
        "layoutGap": clamp_int(source.get("layoutGap"), 8, 48, base["layoutGap"]),
        "sidePanelWidth": clamp_int(source.get("sidePanelWidth"), 240, 460, base["sidePanelWidth"]),
        "backgroundColor": parse_hex_color(source.get("backgroundColor"), parse_hex_color(base["backgroundColor"], COLOR_BG)),
        "backgroundAccentColor": parse_hex_color(
            source.get("backgroundAccentColor"),
            parse_hex_color(base["backgroundAccentColor"], COLOR_ACCENT),
        ),
        "panelColor": parse_hex_color(source.get("panelColor"), parse_hex_color(base["panelColor"], COLOR_PANEL)),
        "panelOpacity": clamp_int(source.get("panelOpacity"), 35, 100, base["panelOpacity"]),
        "textColor": parse_hex_color(source.get("textColor"), parse_hex_color(base["textColor"], COLOR_TEXT)),
        "mutedTextColor": parse_hex_color(
            source.get("mutedTextColor"),
            parse_hex_color(base["mutedTextColor"], COLOR_TEXT_MUTED),
        ),
        "accentColor": parse_hex_color(source.get("accentColor"), parse_hex_color(base["accentColor"], COLOR_ACCENT)),
        "accentAltColor": parse_hex_color(
            source.get("accentAltColor"),
            parse_hex_color(base["accentAltColor"], COLOR_ACCENT_ALT),
        ),
        "buttonTextColor": parse_hex_color(source.get("buttonTextColor"), parse_hex_color(base["buttonTextColor"], COLOR_TEXT)),
        "borderColor": parse_hex_color(source.get("borderColor"), parse_hex_color(base["borderColor"], COLOR_PANEL_BORDER)),
        "borderOpacity": clamp_int(source.get("borderOpacity"), 0, 100, base["borderOpacity"]),
        "cornerRadius": clamp_int(source.get("cornerRadius"), 4, 42, base["cornerRadius"]),
        "backdropBlur": clamp_int(source.get("backdropBlur"), 0, 28, base["backdropBlur"]),
        "stageVignette": clamp_int(source.get("stageVignette"), 0, 80, base["stageVignette"]),
        "motionIntensity": clamp_int(source.get("motionIntensity"), 0, 100, base["motionIntensity"]),
        "titleBackgroundAssetId": str(source.get("titleBackgroundAssetId") or "").strip(),
        "titleBackgroundFit": "contain" if source.get("titleBackgroundFit") == "contain" else "cover",
        "titleBackgroundOpacity": clamp_int(source.get("titleBackgroundOpacity"), 0, 100, base["titleBackgroundOpacity"]),
        "titleLogoAssetId": str(source.get("titleLogoAssetId") or "").strip(),
        "panelFrameAssetId": str(source.get("panelFrameAssetId") or "").strip(),
        "panelFrameOpacity": clamp_int(source.get("panelFrameOpacity"), 0, 100, base["panelFrameOpacity"]),
        "panelFrameSlice": get_safe_frame_slice(source.get("panelFrameSlice"), base["panelFrameSlice"]),
        "buttonFrameAssetId": str(source.get("buttonFrameAssetId") or "").strip(),
        "buttonHoverFrameAssetId": str(source.get("buttonHoverFrameAssetId") or "").strip(),
        "buttonPressedFrameAssetId": str(source.get("buttonPressedFrameAssetId") or "").strip(),
        "buttonDisabledFrameAssetId": str(source.get("buttonDisabledFrameAssetId") or "").strip(),
        "buttonFrameOpacity": clamp_int(source.get("buttonFrameOpacity"), 0, 100, base["buttonFrameOpacity"]),
        "buttonFrameSlice": get_safe_frame_slice(source.get("buttonFrameSlice"), base["buttonFrameSlice"]),
        "saveSlotFrameAssetId": str(source.get("saveSlotFrameAssetId") or "").strip(),
        "systemPanelFrameAssetId": str(source.get("systemPanelFrameAssetId") or "").strip(),
        "uiOverlayAssetId": str(source.get("uiOverlayAssetId") or "").strip(),
        "uiOverlayOpacity": clamp_int(source.get("uiOverlayOpacity"), 0, 100, base["uiOverlayOpacity"]),
    }


def wrap_plain_text(text: str, max_chars: int) -> list[str]:
    safe_text = str(text or "")
    lines: list[str] = []
    for raw_line in safe_text.splitlines() or [""]:
        current = raw_line
        while len(current) > max_chars:
            lines.append(current[:max_chars])
            current = current[max_chars:]
        lines.append(current)
    return lines


def format_snapshot_saved_at(saved_at: str | None) -> str:
    if not saved_at:
        return "尚未保存"
    try:
        parsed = datetime.fromisoformat(str(saved_at))
    except Exception:
        return str(saved_at)
    return parsed.strftime("%m-%d %H:%M")


def format_play_duration(milliseconds: int | float | None) -> str:
    try:
        total_seconds = max(0, int(float(milliseconds or 0) // 1000))
    except Exception:
        total_seconds = 0
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    if hours:
        return f"{hours} 小时 {minutes} 分钟"
    if minutes:
        return f"{minutes} 分钟 {seconds} 秒"
    return f"{seconds} 秒"


def format_runtime_variable_value(variable: dict | None, value: object) -> str:
    coerced_value = coerce_runtime_variable_value(variable, value)
    if isinstance(coerced_value, bool):
        return "开" if coerced_value else "关"
    if isinstance(coerced_value, float) and int(coerced_value) == coerced_value:
        return str(int(coerced_value))
    return str(coerced_value)


def build_variable_summary_text(
    variables: list[dict] | None,
    variable_state: dict | None,
    *,
    limit: int = 3,
) -> str:
    if not variables or not isinstance(variable_state, dict):
        return ""
    parts: list[str] = []
    for variable in variables:
        if not isinstance(variable, dict):
            continue
        variable_id = str(variable.get("id") or "").strip()
        if not variable_id or variable_id not in variable_state:
            continue
        variable_name = str(variable.get("name") or variable_id).strip() or variable_id
        parts.append(f"{variable_name}:{format_runtime_variable_value(variable, variable_state.get(variable_id))}")
        if len(parts) >= limit:
            break
    if not parts:
        return ""
    remaining_count = max(0, len([variable for variable in variables if isinstance(variable, dict) and variable.get("id")]) - len(parts))
    suffix = f" 等 {remaining_count + len(parts)} 项" if remaining_count > 0 else ""
    return " / ".join(parts) + suffix


def build_save_dialog_page_data(
    project: dict | None,
    save_store: dict | None,
    page: int = 0,
    page_size: int = SAVE_DIALOG_PAGE_SIZE,
    variables: list[dict] | None = None,
) -> dict:
    slot_count = get_project_formal_save_slot_count(project)
    safe_page_size = max(1, int(page_size or SAVE_DIALOG_PAGE_SIZE))
    page_count = max(1, (slot_count + safe_page_size - 1) // safe_page_size)
    current_page = max(0, min(page_count - 1, int(page or 0)))
    start = current_page * safe_page_size
    end = min(slot_count, start + safe_page_size)
    formal_slots = (save_store or {}).get("formalSlots") or [None] * slot_count
    formal_slots = list(formal_slots[:slot_count])
    while len(formal_slots) < slot_count:
        formal_slots.append(None)

    visible_slots = []
    for slot_index in range(start, end):
        snapshot = formal_slots[slot_index]
        scene_name = ""
        summary_text = "空位"
        saved_at = "尚未保存"
        if snapshot:
            scene_name = str(snapshot.get("sceneName") or snapshot.get("sceneId") or f"存档 {slot_index + 1}")
            summary_text = str(snapshot.get("summaryText") or "").strip() or "当前没有摘要。"
            saved_at = format_snapshot_saved_at(snapshot.get("savedAt"))
            variable_summary_text = str(snapshot.get("variableSummaryText") or "").strip() or build_variable_summary_text(
                variables,
                snapshot.get("variableState") if isinstance(snapshot, dict) else None,
            )
        else:
            variable_summary_text = ""
        visible_slots.append(
            {
                "slotIndex": slot_index,
                "label": f"正式存档 {slot_index + 1}",
                "isEmpty": snapshot is None,
                "sceneName": scene_name,
                "summaryText": summary_text,
                "variableSummaryText": variable_summary_text,
                "savedAt": saved_at,
                "finished": bool(snapshot.get("finished")) if snapshot else False,
                "thumbnailKey": str(snapshot.get("thumbnailKey") or "") if snapshot else "",
                "thumbnailWidth": clamp_int(snapshot.get("thumbnailWidth"), 0, 10000, 0) if snapshot else 0,
                "thumbnailHeight": clamp_int(snapshot.get("thumbnailHeight"), 0, 10000, 0) if snapshot else 0,
            }
        )

    quick_save = (save_store or {}).get("quickSave")
    quick_variable_summary = ""
    if quick_save:
        quick_variable_summary = str(quick_save.get("variableSummaryText") or "").strip() or build_variable_summary_text(
            variables,
            quick_save.get("variableState") if isinstance(quick_save, dict) else None,
        )
    quick_summary = {
        "isEmpty": quick_save is None,
        "sceneName": str((quick_save or {}).get("sceneName") or (quick_save or {}).get("sceneId") or ""),
        "summaryText": str((quick_save or {}).get("summaryText") or "").strip() or ("空" if quick_save is None else "当前没有摘要。"),
        "variableSummaryText": quick_variable_summary,
        "savedAt": format_snapshot_saved_at((quick_save or {}).get("savedAt")),
        "thumbnailKey": str((quick_save or {}).get("thumbnailKey") or ""),
        "thumbnailWidth": clamp_int((quick_save or {}).get("thumbnailWidth"), 0, 10000, 0),
        "thumbnailHeight": clamp_int((quick_save or {}).get("thumbnailHeight"), 0, 10000, 0),
    }
    return {
        "slotCount": slot_count,
        "pageSize": safe_page_size,
        "pageCount": page_count,
        "page": current_page,
        "startIndex": start,
        "endIndex": end,
        "quickSave": quick_summary,
        "visibleSlots": visible_slots,
    }


def get_safe_character_stage(source: dict | None) -> dict:
    raw = source if isinstance(source, dict) else {}

    def read_number(key: str, fallback: float, minimum: float, maximum: float) -> float:
        try:
            value = float(raw.get(key, fallback))
        except (TypeError, ValueError):
            value = fallback
        return clamp(value, minimum, maximum)

    def read_bool(key: str, fallback: bool = False) -> bool:
        value = raw.get(key, fallback)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "1", "yes", "on"}:
                return True
            if normalized in {"false", "0", "no", "off", ""}:
                return False
        return fallback

    return {
        "offsetX": round(read_number("offsetX", 0, -60, 60)),
        "offsetY": round(read_number("offsetY", 0, -45, 45)),
        "scale": round(read_number("scale", 100, 45, 220)),
        "opacity": round(read_number("opacity", 100, 0, 100)),
        "layer": round(read_number("layer", 0, -10, 10)),
        "flipX": read_bool("flipX"),
    }


def get_block_label(block_type: str) -> str:
    return {
        "dialogue": "台词",
        "narration": "旁白",
        "choice": "选项",
        "jump": "跳转",
        "condition": "条件判断",
        "background": "背景",
        "character_show": "显示角色",
        "character_move": "角色舞台动作",
        "character_hide": "隐藏角色",
        "music_play": "播放音乐",
        "music_stop": "停止音乐",
        "sfx_play": "播放音效",
        "video_play": "播放视频",
        "credits_roll": "片尾字幕",
        "wait": "等待停顿",
        "particle_effect": "粒子特效",
        "screen_shake": "屏幕震动",
        "screen_flash": "闪屏",
        "screen_fade": "黑场淡入淡出",
        "camera_zoom": "镜头推近拉远",
        "camera_pan": "镜头平移",
        "screen_filter": "画面滤镜",
        "depth_blur": "景深模糊",
    }.get(block_type, block_type or "未知")


def get_asset_runtime_path(bundle_dir: Path, asset: dict | None) -> Path | None:
    if not asset or asset.get("isMissing"):
        return None
    export_url = str(asset.get("exportUrl") or "").strip()
    if not export_url:
        return None
    candidate = bundle_dir / export_url
    return candidate if candidate.is_file() else None


def split_wrap_tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9]+(?:[._:/@+-][A-Za-z0-9]+)*|\s+|.", str(text or ""), flags=re.DOTALL)


def append_wrapped_token(font, lines: list[str], current: str, token: str, max_width: int) -> str:
    if token.isspace():
        return current + " " if current and not current.endswith(" ") else current

    if not current and font.size(token)[0] <= max_width:
        return token
    if not current:
        for char in token:
            char_candidate = current + char
            if current and font.size(char_candidate)[0] > max_width:
                lines.append(current.rstrip())
                current = char
            else:
                current = char_candidate
        return current

    candidate = current + token
    if font.size(candidate)[0] <= max_width:
        return candidate

    lines.append(current.rstrip())
    current = ""
    if font.size(token)[0] <= max_width:
        return token

    for char in token:
        char_candidate = current + char
        if current and font.size(char_candidate)[0] > max_width:
            lines.append(current.rstrip())
            current = char
        else:
            current = char_candidate
    return current


def wrap_text(font, text: str, max_width: int) -> list[str]:
    if not text:
        return [""]
    if max_width <= 0:
        return [str(text or "")]

    lines: list[str] = []
    raw_lines = str(text or "").splitlines()
    for raw_line in raw_lines or [""]:
        if raw_line == "":
            lines.append("")
            continue
        current = ""
        for token in split_wrap_tokens(raw_line):
            current = append_wrapped_token(font, lines, current, token, max_width)
        if current or not lines:
            lines.append(current.rstrip())
    return lines or [str(text or "")]


def ellipsize_text(font, text: str, max_width: int, suffix: str = "…") -> str:
    safe_text = str(text or "")
    if font.size(safe_text)[0] <= max_width:
        return safe_text
    if font.size(suffix)[0] > max_width:
        return ""
    while safe_text and font.size(safe_text.rstrip() + suffix)[0] > max_width:
        safe_text = safe_text[:-1]
    return safe_text.rstrip() + suffix
