from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


RENPY_GAME_DIR_NAME = "game"
RENPY_SCRIPT_FILE_NAME = "script.rpy"
RENPY_OPTIONS_FILE_NAME = "options.rpy"
RENPY_MANIFEST_FILE_NAME = "canvasia_renpy_migration_manifest.json"
RENPY_QUALITY_REPORT_FILE_NAME = "canvasia_renpy_quality_report.json"
RENPY_QUALITY_MARKDOWN_FILE_NAME = "CANVASIA_RENPY_QUALITY_REPORT.md"
RENPY_REVIEW_FILE_NAME = "CANVASIA_RENPY_MIGRATION_NOTES.md"
RENPY_README_FILE_NAME = "README_Canvasia_RenPy_Starter.md"
RENPY_VERIFY_SCRIPT_FILE_NAME = "verify_renpy_starter_bundle.py"
CHOICE_CONTINUE_TARGET = "__continue__"
RENPY_PATH_SUFFIX_PATTERN = re.compile(
    r"\.(?:png|jpe?g|webp|gif|avif|mp3|ogg|wav|m4a|aac|flac|mp4|webm|mov|m4v)$",
    re.IGNORECASE,
)
RENPY_PLAYBACK_SPEC_PREFIX_PATTERN = re.compile(r"^<[^>]+>")

COMMENT_ONLY_BLOCK_TYPES: set[str] = set()
CONDITION_OPERATOR_ORDER = ["==", "!=", ">=", "<=", ">", "<"]
CONDITION_OPERATORS = set(CONDITION_OPERATOR_ORDER)
POSITION_XALIGN = {"left": 0.25, "center": 0.5, "right": 0.75}
DEFAULT_CHARACTER_STAGE = {
    "offsetX": 0,
    "offsetY": 0,
    "scale": 100,
    "opacity": 100,
    "layer": 0,
    "flipX": False,
}
CHARACTER_MOVE_TRANSFORMS = {
    "slide_left": "offscreenleft",
    "slide_right": "offscreenright",
    "rise": "offscreenbottom",
}
TEXT_SPEED_CPS = {
    "slow": 24,
    "normal": 42,
    "fast": 72,
    "instant": 10000,
}
BACKGROUND_TRANSITION_DEFAULT_MS = 360
EFFECT_DURATION_SECONDS = {
    "short": 0.42,
    "medium": 0.78,
    "long": 1.2,
}
FLASH_COLOR_HEX = {
    "white": "#ffffff",
    "warm": "#ffeccc",
    "red": "#ff7878",
    "black": "#201816",
}
FADE_COLOR_HEX = {
    "black": "#120e0c",
    "white": "#fffcf7",
}
DEFAULT_PROJECT_RESOLUTION = {"width": 1280, "height": 720}
CAMERA_ZOOM_SCALE = {
    "zoom_in": {"light": 1.08, "medium": 1.16, "heavy": 1.26},
    "zoom_out": {"light": 0.96, "medium": 0.92, "heavy": 0.88},
}
CAMERA_FOCUS_XALIGN = {"left": 0.28, "center": 0.5, "right": 0.72}
CAMERA_PAN_PERCENT = {"light": 4, "medium": 8, "heavy": 12}
CAMERA_EFFECT_STRENGTH = {"soft": 0.65, "medium": 1.0, "strong": 1.35}
SCREEN_FILTER_PRESETS = {
    "memory": {"tint": "#ffeec2", "saturation": 0.82, "brightness": 0.03},
    "mono": {"tint": "#ffffff", "saturation": 0.0, "brightness": 0.0},
    "dream": {"tint": "#eee4ff", "saturation": 0.92, "brightness": 0.05},
    "cold": {"tint": "#dcecff", "saturation": 0.86, "brightness": -0.01},
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
DEPTH_BLUR_PIXELS = {"soft": 2.0, "medium": 4.0, "strong": 6.0}
PARTICLE_PRESET_DEFAULTS = {
    "snow": {"symbol": "*", "color": "#ffffff", "density": 40, "size": 12, "yspeed": 70, "spread": 100, "distribution": "linear"},
    "rain": {"symbol": "|", "color": "#b7dcff", "density": 56, "size": 18, "yspeed": 190, "spread": 100, "distribution": "linear"},
    "petals": {"symbol": "*", "color": "#ffd6ea", "density": 28, "size": 18, "yspeed": 58, "spread": 100, "distribution": "gaussian"},
    "dust": {"symbol": ".", "color": "#c4f6ff", "density": 26, "size": 8, "yspeed": 24, "spread": 100, "distribution": "gaussian"},
    "embers": {"symbol": "*", "color": "#ffb36b", "density": 24, "size": 7, "yspeed": -46, "spread": 100, "distribution": "gaussian"},
    "sparkles": {"symbol": "*", "color": "#dff8ff", "density": 18, "size": 9, "yspeed": 16, "spread": 100, "distribution": "gaussian"},
    "bubbles": {"symbol": "o", "color": "#b6f3ff", "density": 20, "size": 18, "yspeed": -72, "spread": 100, "distribution": "gaussian"},
    "confetti": {"symbol": "*", "color": "#7fe7ff", "density": 34, "size": 10, "yspeed": 120, "spread": 100, "distribution": "linear"},
    "smoke": {"symbol": ".", "color": "#aebed4", "density": 22, "size": 44, "yspeed": -24, "spread": 72, "distribution": "gaussian"},
    "flame": {"symbol": "*", "color": "#ff8b3d", "density": 26, "size": 24, "yspeed": -82, "spread": 40, "distribution": "gaussian"},
    "stardust": {"symbol": "*", "color": "#8edbff", "density": 30, "size": 7, "yspeed": 8, "spread": 100, "distribution": "gaussian"},
    "glyphs": {"symbol": "*", "color": "#85d4ff", "density": 14, "size": 26, "yspeed": 0, "spread": 34, "distribution": "gaussian"},
}
PARTICLE_INTENSITY_MULTIPLIER = {"light": 0.62, "medium": 1.0, "heavy": 1.55}
PARTICLE_SPEED_MULTIPLIER = {"slow": 0.72, "medium": 1.0, "fast": 1.35}
PARTICLE_WIND_SPEED = {"left": -55.0, "still": 0.0, "right": 55.0}


def get_renpy_export_contract() -> dict:
    """Expose the shared export rule surface so tests can catch JS/Python drift."""
    return {
        "formatVersion": 1,
        "backgroundTransitionDefaultMs": BACKGROUND_TRANSITION_DEFAULT_MS,
        "conditionOperators": list(CONDITION_OPERATOR_ORDER),
        "characterMoveTransforms": dict(CHARACTER_MOVE_TRANSFORMS),
        "textSpeedCps": dict(TEXT_SPEED_CPS),
        "effectDurationSeconds": dict(EFFECT_DURATION_SECONDS),
        "cameraFocusKeys": sorted(CAMERA_FOCUS_XALIGN),
        "particlePresetKeys": sorted(PARTICLE_PRESET_DEFAULTS),
        "screenFilterPresetKeys": sorted(SCREEN_FILTER_PRESETS),
    }


def as_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def clean_text(value: Any, fallback: str = "") -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text or fallback


def normalize_identifier(value: Any, fallback: str = "item") -> str:
    raw = re.sub(r"[^A-Za-z0-9_]+", "_", clean_text(value, fallback)).strip("_").lower()
    safe = raw or fallback
    return safe if re.match(r"^[A-Za-z_]", safe) else f"id_{safe}"


def quote_renpy(value: Any) -> str:
    text = str(value or "").replace("\\", "\\\\").replace('"', '\\"')
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\\n")
    return f'"{text}"'


def value_to_renpy(value: Any) -> str:
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    if value is None:
        return "None"
    text = clean_text(value)
    if re.match(r"^(true|false)$", text, re.IGNORECASE):
        return "True" if text.lower() == "true" else "False"
    if re.match(r"^-?\d+(?:\.\d+)?$", text):
        return text
    if re.match(r"^(none|null)$", text, re.IGNORECASE):
        return "None"
    return quote_renpy(value)


def get_project_resolution(bundle: dict) -> dict[str, int]:
    project = bundle.get("project") if isinstance(bundle.get("project"), dict) else {}
    resolution = project.get("resolution") if isinstance(project.get("resolution"), dict) else {}
    try:
        width = int(float(resolution.get("width") or DEFAULT_PROJECT_RESOLUTION["width"]))
    except (TypeError, ValueError):
        width = DEFAULT_PROJECT_RESOLUTION["width"]
    try:
        height = int(float(resolution.get("height") or DEFAULT_PROJECT_RESOLUTION["height"]))
    except (TypeError, ValueError):
        height = DEFAULT_PROJECT_RESOLUTION["height"]
    return {
        "width": width if width > 0 else DEFAULT_PROJECT_RESOLUTION["width"],
        "height": height if height > 0 else DEFAULT_PROJECT_RESOLUTION["height"],
    }


def seconds_from_ms(value: Any) -> float:
    try:
        ms = float(value or 0)
    except (TypeError, ValueError):
        return 0
    return round(ms / 1000, 2) if ms > 0 else 0


def format_renpy_seconds(value: Any) -> str:
    try:
        seconds = float(value)
    except (TypeError, ValueError):
        seconds = 0
    return f"{seconds:.2f}".rstrip("0").rstrip(".") or "0"


def get_safe_volume_ratio(value: Any, fallback: float = 100) -> float:
    try:
        percent = float(value if value not in (None, "") else fallback)
    except (TypeError, ValueError):
        percent = fallback
    return round(clamp_number(percent, 0, 100) / 100, 2)


def render_volume_clause(value: Any, fallback: float = 100) -> str:
    ratio = get_safe_volume_ratio(value, fallback)
    return "" if ratio == 1 else f" volume {ratio:g}"


def get_video_cue_seconds(value: Any) -> float:
    try:
        seconds = float(value if value not in (None, "") else 0)
    except (TypeError, ValueError):
        seconds = 0
    return round(seconds, 2) if seconds > 0 else 0


def build_video_playback_spec(path: str, block: dict, context: dict) -> dict:
    start = get_video_cue_seconds(block.get("startTimeSeconds"))
    end = get_video_cue_seconds(block.get("endTimeSeconds"))
    volume = get_safe_volume_ratio(block.get("volume"), 100)
    if end > 0 and end <= start:
        add_warning(
            context["warnings"],
            "renpy_video_timing_review",
            "视频结束时间早于或等于开始时间，已忽略结束时间。",
            sceneId=context.get("sceneId"),
            blockIndex=context.get("blockIndex"),
        )
        end = 0

    clauses: list[str] = []
    if start > 0:
        clauses.extend(["from", format_renpy_seconds(start)])
    if end > 0:
        clauses.extend(["to", format_renpy_seconds(end)])
    if volume != 1:
        clauses.extend(["volume", format_renpy_seconds(volume)])
    playback_path = f"<{' '.join(clauses)}>{path}" if clauses else path
    return {
        "path": playback_path,
        "delay": round(end - start, 2) if end > start else 0,
    }


def render_music_loop_clause(block: dict) -> str:
    if block.get("loop") is True:
        return " loop"
    if block.get("loop") is False:
        return " noloop"
    return ""


def is_music_control_block(block: dict) -> bool:
    return clean_text(block.get("type")) in {"music_play", "music_stop"}


def add_music_scope_warning(block: dict, context: dict, code: str, message: str) -> None:
    add_warning(
        context["warnings"],
        code,
        message,
        sceneId=context.get("sceneId"),
        blockIndex=context.get("blockIndex"),
        blockId=clean_text(block.get("id")),
    )


def get_music_scope_stop_lines(block: dict, end_mode: str = "scene_end", end_block_id: str = "") -> list[str]:
    fade_out = seconds_from_ms(block.get("fadeOutMs"))
    target_suffix = f" after {end_block_id}" if end_block_id else ""
    return [
        f"    # Canvasia music scope end: {end_mode}{target_suffix}",
        f"    stop music{f' fadeout {fade_out:g}' if fade_out else ''}",
    ]


def add_music_scope_stop(plan: dict, timing: str, block_index: int, lines: list[str]) -> None:
    bucket = plan["before"] if timing == "before" else plan["after"]
    bucket.setdefault(block_index, []).extend(lines)


def build_music_scope_stop_plan(blocks: list[dict], context: dict) -> dict:
    normalized_blocks = as_list(blocks)
    plan: dict[str, dict[int, list[str]]] = {"before": {}, "after": {}}
    for block_index, block in enumerate(normalized_blocks):
        if clean_text(block.get("type")) != "music_play":
            continue
        scoped_context = {**context, "blockIndex": block_index}
        end_mode = clean_text(block.get("endMode"), "until_next_music")
        if end_mode not in {"scene_end", "after_block"}:
            continue
        next_audio_control_index = next(
            (candidate_index for candidate_index, candidate in enumerate(normalized_blocks) if candidate_index > block_index and is_music_control_block(candidate)),
            -1,
        )
        stop_index = len(normalized_blocks) - 1
        timing = "after"
        end_block_id = ""

        if end_mode == "after_block":
            end_block_id = clean_text(block.get("endBlockId"))
            target_index = next(
                (candidate_index for candidate_index, candidate in enumerate(normalized_blocks) if clean_text(candidate.get("id")) == end_block_id),
                -1,
            )
            if not end_block_id:
                add_music_scope_warning(block, scoped_context, "renpy_music_scope_missing_end_block", "BGM 指定范围缺少结束卡片，已保留播放到下一首音乐或场景结束。")
                continue
            if target_index < 0:
                add_music_scope_warning(block, scoped_context, "renpy_music_scope_invalid_end_block", f"BGM 指定范围的结束卡片 {end_block_id} 不存在，已保留播放到下一首音乐或场景结束。")
                continue
            if target_index < block_index:
                add_music_scope_warning(block, scoped_context, "renpy_music_scope_end_before_start", f"BGM 指定范围的结束卡片 {end_block_id} 位于播放卡之前，已保留播放到下一首音乐或场景结束。")
                continue
            stop_index = target_index
        else:
            last_type = clean_text(normalized_blocks[stop_index].get("type")) if normalized_blocks else ""
            if last_type in {"jump", "return"}:
                timing = "before"
            elif last_type == "choice":
                add_music_scope_warning(block, scoped_context, "renpy_music_scope_terminal_choice_review", "BGM 设置为场景结束，但场景以选项结束；Ren'Py 菜单分支需要按路线决定是否停止音乐。")
                continue

        if 0 <= next_audio_control_index <= stop_index:
            continue
        add_music_scope_stop(plan, timing, stop_index, get_music_scope_stop_lines(block, end_mode, end_block_id))
    return plan


def number_to_renpy_delta(value: Any, warnings: list[dict], variable_id: str, **context: Any) -> str:
    try:
        delta = float(value if value not in (None, "") else 0)
    except (TypeError, ValueError):
        add_warning(
            warnings,
            "renpy_variable_add_value_review",
            f"变量 {variable_id} 的增减值不是数字，已按 0 导出。",
            **context,
        )
        return "0"
    if delta.is_integer():
        return str(int(delta))
    return f"{delta:g}"


def clamp_number(value: float, minimum: float, maximum: float) -> float:
    return min(max(value, minimum), maximum)


def get_safe_stage_number(raw: dict, key: str, fallback: float, minimum: float, maximum: float) -> float:
    try:
        value = float(raw.get(key, fallback))
    except (TypeError, ValueError):
        value = fallback
    return clamp_number(value, minimum, maximum)


def get_safe_stage_bool(raw: dict, key: str, fallback: bool = False) -> bool:
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


def get_safe_position(value: Any) -> str:
    position = clean_text(value, "center")
    return position if position in POSITION_XALIGN else "center"


def get_safe_text_speed(value: Any) -> str:
    speed = clean_text(value)
    return speed if speed in TEXT_SPEED_CPS else ""


def render_renpy_text(block: dict) -> str:
    line = clean_text(block.get("text") or (block.get("fields") or {}).get("text"), " ")
    speed = get_safe_text_speed(block.get("textSpeed"))
    return f"{{cps={TEXT_SPEED_CPS[speed]}}}{line}{{/cps}}" if speed else line


def get_safe_character_stage(source: Any) -> dict:
    raw = source if isinstance(source, dict) else {}
    return {
        "offsetX": round(get_safe_stage_number(raw, "offsetX", 0, -60, 60)),
        "offsetY": round(get_safe_stage_number(raw, "offsetY", 0, -45, 45)),
        "scale": round(get_safe_stage_number(raw, "scale", 100, 45, 220)),
        "opacity": round(get_safe_stage_number(raw, "opacity", 100, 0, 100)),
        "layer": round(get_safe_stage_number(raw, "layer", 0, -10, 10)),
        "flipX": get_safe_stage_bool(raw, "flipX"),
    }


def has_custom_character_stage(source: Any) -> bool:
    stage = get_safe_character_stage(source)
    return any(stage[key] != value for key, value in DEFAULT_CHARACTER_STAGE.items())


def format_renpy_float(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}".rstrip("0").rstrip(".") or "0"


def get_character_stage_transform_name(scene_label_map: dict[str, str], scene_id: Any, block_index: Any) -> str:
    label = get_scene_label(scene_label_map, scene_id)
    return normalize_identifier(f"canvasia_stage_{label}_{int(block_index or 0) + 1}", "canvasia_stage")


def render_character_stage_transform_definition(block: dict, context: dict) -> list[str]:
    stage = get_safe_character_stage(block.get("stage"))
    position = get_safe_position(block.get("position"))
    transform_name = get_character_stage_transform_name(context["sceneLabelMap"], context.get("sceneId"), context.get("blockIndex"))
    xalign = clamp_number(POSITION_XALIGN[position] + stage["offsetX"] / 100, -0.2, 1.2)
    yalign = clamp_number(1 + stage["offsetY"] / 100, -0.2, 1.2)
    zoom = stage["scale"] / 100
    xzoom = -zoom if stage["flipX"] else zoom
    return [
        f"transform {transform_name}:",
        f"    xalign {format_renpy_float(xalign)}",
        f"    yalign {format_renpy_float(yalign)}",
        f"    xzoom {format_renpy_float(xzoom)}",
        f"    yzoom {format_renpy_float(zoom)}",
        f"    alpha {format_renpy_float(stage['opacity'] / 100, 2)}",
    ]


def build_character_stage_transform_definitions(scene_records: list[dict], scene_label_map: dict[str, str]) -> list[str]:
    lines: list[str] = []
    for record in scene_records:
        scene = record["scene"]
        scene_id = record["sceneId"]
        for block_index, block in enumerate(as_list(scene.get("blocks"))):
            if clean_text(block.get("type")) != "character_show" or not has_custom_character_stage(block.get("stage")):
                continue
            lines.extend(
                render_character_stage_transform_definition(
                    block,
                    {
                        "sceneLabelMap": scene_label_map,
                        "sceneId": scene_id,
                        "blockIndex": block_index,
                    },
                )
            )
            lines.append("")
    return lines


def get_transition_duration_seconds(block: dict, fallback_ms: float = 600) -> float:
    try:
        ms = float(block.get("transitionDurationMs", fallback_ms))
    except (TypeError, ValueError):
        ms = fallback_ms
    return round(clamp_number(ms, 0, 5000) / 1000, 2)


def get_screen_effect_duration_seconds(block: dict) -> float:
    duration = clean_text(block.get("duration"), "medium")
    return EFFECT_DURATION_SECONDS.get(duration, EFFECT_DURATION_SECONDS["medium"])


def get_effect_color_hex(table: dict[str, str], value: Any, fallback: str) -> str:
    key = clean_text(value, fallback)
    return table.get(key, table[fallback])


def get_background_transition_expression(block: dict, context: dict) -> str:
    transition = clean_text(block.get("transition"), "fade")
    seconds = get_transition_duration_seconds(block, BACKGROUND_TRANSITION_DEFAULT_MS)
    if transition == "none" or seconds <= 0:
        return ""
    if transition in {"fade", "dissolve", "crossfade"}:
        return f"Dissolve({format_renpy_seconds(seconds)})"
    add_warning(
        context["warnings"],
        "renpy_background_transition_review",
        f"背景转场 {transition} 暂未精确映射，已按淡入淡出导出。",
        sceneId=context.get("sceneId"),
        blockIndex=context.get("blockIndex"),
    )
    return f"Dissolve({format_renpy_seconds(seconds)})"


def get_safe_camera_zoom_action(value: Any) -> str:
    action = clean_text(value, "zoom_in")
    return action if action in {"zoom_in", "zoom_out", "reset"} else "zoom_in"


def get_safe_camera_strength(value: Any) -> str:
    strength = clean_text(value, "medium")
    return strength if strength in {"light", "medium", "heavy"} else "medium"


def get_safe_camera_focus(value: Any) -> str:
    focus = clean_text(value, "center")
    return focus if focus in CAMERA_FOCUS_XALIGN else "center"


def get_safe_camera_pan_target(value: Any) -> str:
    target = clean_text(value, "center")
    return target if target in {"left", "center", "right"} else "center"


def get_safe_effect_strength(value: Any) -> str:
    strength = clean_text(value, "medium")
    return strength if strength in CAMERA_EFFECT_STRENGTH else "medium"


def get_safe_screen_filter_action(value: Any) -> str:
    action = clean_text(value, "apply")
    return action if action in {"apply", "clear"} else "apply"


def get_safe_screen_filter_preset(value: Any) -> str:
    preset = clean_text(value, "memory")
    return preset if preset in SCREEN_FILTER_PRESETS else "memory"


def get_safe_depth_blur_action(value: Any) -> str:
    action = clean_text(value, "apply")
    return action if action in {"apply", "clear"} else "apply"


def get_safe_depth_blur_focus(value: Any) -> str:
    focus = clean_text(value, "full")
    return focus if focus in {"left", "center", "right", "full"} else "full"


def get_safe_particle_action(value: Any) -> str:
    action = clean_text(value, "start")
    return action if action in {"start", "stop"} else "start"


def get_safe_particle_preset(value: Any) -> str:
    preset = clean_text(value, "snow")
    return preset if preset in PARTICLE_PRESET_DEFAULTS else "snow"


def get_safe_particle_intensity(value: Any) -> str:
    intensity = clean_text(value, "medium")
    return intensity if intensity in PARTICLE_INTENSITY_MULTIPLIER else "medium"


def get_safe_particle_speed(value: Any) -> str:
    speed = clean_text(value, "medium")
    return speed if speed in PARTICLE_SPEED_MULTIPLIER else "medium"


def get_safe_particle_wind(value: Any) -> str:
    wind = clean_text(value, "still")
    return wind if wind in PARTICLE_WIND_SPEED else "still"


def get_camera_pan_offset(target: Any, strength: Any, resolution: dict[str, int]) -> int:
    safe_target = get_safe_camera_pan_target(target)
    if safe_target == "center":
        return 0
    percent = CAMERA_PAN_PERCENT[get_safe_camera_strength(strength)]
    offset = round(float(resolution.get("width") or DEFAULT_PROJECT_RESOLUTION["width"]) * percent / 100)
    return offset if safe_target == "left" else -offset


def get_default_camera_state() -> dict[str, Any]:
    return {"zoomScale": 1.0, "focus": "center", "panOffset": 0, "matrixcolor": "", "blur": 0.0}


def get_camera_state(context: dict) -> dict[str, Any]:
    camera_state = context.get("cameraState")
    if not isinstance(camera_state, dict):
        camera_state = get_default_camera_state()
        context["cameraState"] = camera_state
    return camera_state


def render_camera_statement(state: dict[str, Any]) -> list[str]:
    try:
        zoom_scale = float(state.get("zoomScale", 1))
    except (TypeError, ValueError):
        zoom_scale = 1.0
    try:
        pan_offset = int(round(float(state.get("panOffset", 0))))
    except (TypeError, ValueError):
        pan_offset = 0
    try:
        blur = float(state.get("blur", 0))
    except (TypeError, ValueError):
        blur = 0
    focus = get_safe_camera_focus(state.get("focus"))
    matrixcolor = clean_text(state.get("matrixcolor"))
    neutral = abs(zoom_scale - 1) < 0.001 and pan_offset == 0 and focus == "center" and not matrixcolor and blur <= 0
    if neutral:
        return ["    camera"]
    lines = [
        "    camera:",
        "        subpixel True",
        f"        xalign {format_renpy_float(CAMERA_FOCUS_XALIGN[focus], 2)}",
        "        yalign 0.52",
        f"        zoom {format_renpy_float(zoom_scale, 2)}",
        f"        xoffset {pan_offset}",
        "        yoffset 0",
    ]
    if matrixcolor:
        lines.append(f"        matrixcolor {matrixcolor}")
    if blur > 0:
        lines.append(f"        blur {format_renpy_float(blur, 2)}")
    return lines


def render_camera_zoom_block(block: dict, context: dict) -> list[str]:
    state = get_camera_state(context)
    action = get_safe_camera_zoom_action(block.get("action"))
    if action == "reset":
        state["zoomScale"] = 1.0
        state["focus"] = "center"
    else:
        strength = get_safe_camera_strength(block.get("strength"))
        state["zoomScale"] = CAMERA_ZOOM_SCALE.get(action, CAMERA_ZOOM_SCALE["zoom_in"])[strength]
        state["focus"] = get_safe_camera_focus(block.get("focus"))
    return render_camera_statement(state)


def render_camera_pan_block(block: dict, context: dict) -> list[str]:
    state = get_camera_state(context)
    resolution = context.get("projectResolution") if isinstance(context.get("projectResolution"), dict) else DEFAULT_PROJECT_RESOLUTION
    state["panOffset"] = get_camera_pan_offset(block.get("target"), block.get("strength"), resolution)
    return render_camera_statement(state)


def get_safe_screen_color_grade(source: Any) -> dict[str, int]:
    raw = source if isinstance(source, dict) else {}
    grade: dict[str, int] = {}
    for key, fallback in SCREEN_COLOR_GRADE_DEFAULTS.items():
        minimum, maximum = SCREEN_COLOR_GRADE_LIMITS[key]
        try:
            value = float(raw.get(key, fallback))
        except (TypeError, ValueError):
            value = fallback
        grade[key] = int(round(clamp_number(value, minimum, maximum)))
    return grade


def get_strength_adjusted_value(base: float, neutral: float, strength: Any) -> float:
    multiplier = CAMERA_EFFECT_STRENGTH[get_safe_effect_strength(strength)]
    return neutral + (base - neutral) * multiplier


def format_matrix_number(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0
    return f"{number:.3f}".rstrip("0").rstrip(".") or "0"


def get_screen_filter_matrix_expression(block: dict) -> str:
    preset = SCREEN_FILTER_PRESETS[get_safe_screen_filter_preset(block.get("preset"))]
    strength = get_safe_effect_strength(block.get("strength"))
    grade = get_safe_screen_color_grade(block.get("grade"))
    parts = [
        f"TintMatrix(\"{preset['tint']}\")",
        f"SaturationMatrix({format_matrix_number(clamp_number(get_strength_adjusted_value(float(preset['saturation']), 1, strength), 0, 2.2))})",
    ]
    preset_brightness = get_strength_adjusted_value(float(preset.get("brightness") or 0), 0, strength)
    if abs(preset_brightness) > 0.001:
        parts.append(f"BrightnessMatrix({format_matrix_number(clamp_number(preset_brightness, -1, 1))})")
    if grade["brightness"] != SCREEN_COLOR_GRADE_DEFAULTS["brightness"]:
        parts.append(f"BrightnessMatrix({format_matrix_number(clamp_number((grade['brightness'] - 100) / 100, -1, 1))})")
    if grade["contrast"] != SCREEN_COLOR_GRADE_DEFAULTS["contrast"]:
        parts.append(f"ContrastMatrix({format_matrix_number(clamp_number(grade['contrast'] / 100, 0, 2.2))})")
    if grade["saturation"] != SCREEN_COLOR_GRADE_DEFAULTS["saturation"]:
        parts.append(f"SaturationMatrix({format_matrix_number(clamp_number(grade['saturation'] / 100, 0, 2.2))})")
    hue = grade["hue"] - grade["temperature"] * 0.08
    if abs(hue) > 0.001:
        parts.append(f"HueMatrix({format_matrix_number(hue)})")
    return " * ".join(parts)


def render_screen_filter_block(block: dict, context: dict) -> list[str]:
    state = get_camera_state(context)
    if get_safe_screen_filter_action(block.get("action")) == "clear":
        state["matrixcolor"] = ""
    else:
        state["matrixcolor"] = get_screen_filter_matrix_expression(block)
    return render_camera_statement(state)


def render_depth_blur_block(block: dict, context: dict) -> list[str]:
    state = get_camera_state(context)
    if get_safe_depth_blur_action(block.get("action")) == "clear":
        state["blur"] = 0
        return render_camera_statement(state)
    focus = get_safe_depth_blur_focus(block.get("focus"))
    strength = get_safe_effect_strength(block.get("strength"))
    if focus != "full":
        add_warning(
            context["warnings"],
            "renpy_depth_blur_focus_review",
            "Ren'Py 草稿已导出全层 blur；指定角色侧清晰需要在 Ren'Py 中改成分层镜头。",
            sceneId=context.get("sceneId"),
            blockIndex=context.get("blockIndex"),
        )
    state["blur"] = DEPTH_BLUR_PIXELS[strength]
    return render_camera_statement(state)


def get_safe_particle_number(value: Any, fallback: float, minimum: float, maximum: float) -> float:
    try:
        number = float(value if value not in (None, "") else fallback)
    except (TypeError, ValueError):
        number = fallback
    return clamp_number(number, minimum, maximum)


def get_particle_count(block: dict, defaults: dict) -> int:
    base_density = get_safe_particle_number(block.get("density"), float(defaults.get("density") or 32), 4, 180)
    intensity = PARTICLE_INTENSITY_MULTIPLIER[get_safe_particle_intensity(block.get("intensity"))]
    return int(round(clamp_number(base_density * intensity, 4, 220)))


def get_particle_size(block: dict, defaults: dict) -> int:
    fallback = float(defaults.get("size") or 10)
    size_min = get_safe_particle_number(block.get("sizeMin"), fallback, 1, 160)
    size_max = get_safe_particle_number(block.get("sizeMax"), fallback, 1, 160)
    return int(round(clamp_number((min(size_min, size_max) + max(size_min, size_max)) / 2, 1, 160)))


def get_speed_tuple(base_value: float, spread_ratio: float = 0.25) -> tuple[float, float]:
    spread = max(4.0, abs(base_value) * spread_ratio)
    first = round(base_value - spread, 1)
    second = round(base_value + spread, 1)
    return (min(first, second), max(first, second))


def render_particle_speed_tuple(values: tuple[float, float]) -> str:
    return f"({', '.join(format_renpy_float(value, 1) for value in values)})"


def render_particle_block(block: dict, context: dict) -> list[str]:
    if get_safe_particle_action(block.get("action")) == "stop":
        return ["    hide canvasia_particles onlayer overlay"]
    preset = get_safe_particle_preset(block.get("preset"))
    defaults = PARTICLE_PRESET_DEFAULTS[preset]
    speed_multiplier = PARTICLE_SPEED_MULTIPLIER[get_safe_particle_speed(block.get("speed"))]
    wind_speed = PARTICLE_WIND_SPEED[get_safe_particle_wind(block.get("wind"))]
    size = get_particle_size(block, defaults)
    count = get_particle_count(block, defaults)
    base_y_speed = get_safe_particle_number(block.get("gravityY"), float(defaults.get("yspeed") or 70), -220, 320) * speed_multiplier
    spread = get_safe_particle_number(block.get("spreadX"), float(defaults.get("spread") or 100), 4, 100)
    x_speed = get_speed_tuple(wind_speed, max(0.18, spread / 400))
    y_speed = get_speed_tuple(base_y_speed, 0.22)
    color = clean_text(block.get("color"))
    if not re.match(r"^#[0-9a-f]{6}$", color, re.IGNORECASE):
        color = str(defaults["color"])
    advanced_keys = ["assetId", "customComboLayers", "comboPreset", "forceField", "follow", "emitterShape", "emissionMode"]
    needs_review = False
    for key in advanced_keys:
        if key == "customComboLayers":
            needs_review = needs_review or bool(as_list(block.get(key)))
            continue
        value = clean_text(block.get(key))
        needs_review = needs_review or bool(value and value not in {"none", "line", "continuous"})
    if needs_review:
        add_warning(
            context["warnings"],
            "renpy_particle_advanced_review",
            "粒子已按 SnowBlossom 基础层导出；自定义贴图、叠层、力场、跟随目标等高级参数需要在 Ren'Py 中复核。",
            sceneId=context.get("sceneId"),
            blockIndex=context.get("blockIndex"),
        )
    return [
        f"    show expression SnowBlossom(Text({quote_renpy(defaults['symbol'])}, color={quote_renpy(color)}, size={size}), count={count}, border=80, xspeed={render_particle_speed_tuple(x_speed)}, yspeed={render_particle_speed_tuple(y_speed)}, start=0.04, fast=True, distribution={quote_renpy(defaults['distribution'])}, animation=True) as canvasia_particles onlayer overlay"
    ]


def get_character_transition_expression(block: dict, context: dict, direction: str = "show") -> str:
    transition = clean_text(block.get("transition"), "fade")
    seconds = get_transition_duration_seconds(block)
    if transition == "none" or seconds <= 0:
        return ""
    if transition in {"fade", "dissolve"}:
        return f"Dissolve({seconds:g})"
    if transition in CHARACTER_MOVE_TRANSFORMS:
        transform = CHARACTER_MOVE_TRANSFORMS[transition]
        argument_name = "leave" if direction == "hide" else "enter"
        warp_name = "leave_time_warp" if direction == "hide" else "enter_time_warp"
        warp = "_warper.easein" if direction == "hide" else "_warper.easeout"
        return f"MoveTransition({seconds:g}, {argument_name}={transform}, {warp_name}={warp})"
    if transition == "pop":
        add_warning(
            context["warnings"],
            "renpy_character_transition_review",
            "轻微弹出转场已按淡入导出，请在 Ren'Py 中按需要替换为自定义 ATL。",
            sceneId=context.get("sceneId"),
            blockIndex=context.get("blockIndex"),
        )
        return f"Dissolve({seconds:g})"
    add_warning(
        context["warnings"],
        "renpy_character_transition_review",
        f"角色转场 {transition} 暂未精确映射，已按淡入导出。",
        sceneId=context.get("sceneId"),
        blockIndex=context.get("blockIndex"),
    )
    return f"Dissolve({seconds:g})"


def build_asset_map(assets_doc: dict | None) -> dict[str, dict]:
    return {
        str(asset.get("id")): asset
        for asset in as_list((assets_doc or {}).get("assets"))
        if asset.get("id")
    }


def build_character_map(bundle: dict) -> dict[str, dict]:
    characters_doc = bundle.get("characters") if isinstance(bundle.get("characters"), dict) else {}
    return {
        str(character.get("id")): character
        for character in as_list(characters_doc.get("characters"))
        if character.get("id")
    }


def build_variable_map(bundle: dict) -> dict[str, dict]:
    variables_doc = bundle.get("variables") if isinstance(bundle.get("variables"), dict) else {}
    return {
        str(variable.get("id")): variable
        for variable in as_list(variables_doc.get("variables"))
        if variable.get("id")
    }


def build_scene_records(bundle: dict) -> list[dict]:
    records: list[dict] = []
    for chapter_index, chapter in enumerate(as_list(bundle.get("chapters"))):
        chapter_name = clean_text(chapter.get("name") or chapter.get("title"), f"Chapter {chapter_index + 1}")
        for scene_index, scene in enumerate(as_list(chapter.get("scenes"))):
            scene_id = clean_text(scene.get("id"), f"scene_{chapter_index + 1}_{scene_index + 1}")
            records.append(
                {
                    "chapterName": chapter_name,
                    "scene": scene,
                    "sceneId": scene_id,
                    "sceneLabel": normalize_identifier(scene_id, "scene"),
                }
            )
    return records


def get_asset_path(asset_map: dict[str, dict], asset_id: Any) -> str:
    asset = asset_map.get(clean_text(asset_id))
    if not asset:
        return clean_text(asset_id)
    return clean_text(asset.get("exportUrl") or asset.get("path") or asset.get("name") or asset_id)


def get_character_name(character_map: dict[str, dict], character_id: Any) -> str:
    character = character_map.get(clean_text(character_id))
    return clean_text((character or {}).get("displayName") or (character or {}).get("name") or character_id, "Narrator")


def get_scene_label(scene_label_map: dict[str, str], scene_id: Any) -> str:
    return scene_label_map.get(clean_text(scene_id), normalize_identifier(scene_id, "scene"))


def add_warning(warnings: list[dict], code: str, message: str, **context: Any) -> None:
    warnings.append(
        {
            "code": code,
            "message": message,
            **{key: value for key, value in context.items() if value not in (None, "")},
        }
    )


def build_variable_definitions(variable_map: dict[str, dict]) -> list[str]:
    lines: list[str] = []
    for variable_id, variable in sorted(variable_map.items()):
        renpy_name = normalize_identifier(variable_id, "var")
        lines.append(f"default {renpy_name} = {value_to_renpy(variable.get('defaultValue'))}")
    return lines


def build_asset_image_definitions(asset_map: dict[str, dict]) -> list[str]:
    lines: list[str] = []
    for asset_id, asset in sorted(asset_map.items()):
        if clean_text(asset.get("type")).lower() not in {"background", "cg", "image"}:
            continue
        asset_path = get_asset_path(asset_map, asset_id)
        if not asset_path:
            continue
        lines.append(f"image {normalize_identifier(asset_id, 'asset')} = {quote_renpy(asset_path)}")
    return lines


def build_character_definitions(character_map: dict[str, dict]) -> list[str]:
    lines: list[str] = []
    for character_id, character in sorted(character_map.items()):
        name = clean_text(character.get("displayName") or character.get("name"), character_id)
        lines.append(f"define {normalize_identifier(character_id, 'character')} = Character({quote_renpy(name)})")
    return lines


def build_sprite_definitions(
    character_map: dict[str, dict],
    asset_map: dict[str, dict],
    warnings: list[dict],
) -> tuple[list[str], set[tuple[str, str]]]:
    lines: list[str] = []
    defined: set[tuple[str, str]] = set()
    for character_id, character in sorted(character_map.items()):
        character_name = normalize_identifier(character_id, "character")
        default_sprite_id = clean_text(character.get("defaultSpriteId"))
        fallback_sprite_id = clean_text((character.get("presentation") or {}).get("fallbackSpriteAssetId"))
        base_sprite_id = default_sprite_id or fallback_sprite_id
        if base_sprite_id:
            base_path = get_asset_path(asset_map, base_sprite_id)
            if base_path:
                lines.append(f"image {character_name} = {quote_renpy(base_path)}")
                defined.add((character_name, ""))

        for expression in as_list(character.get("expressions")):
            expression_id = clean_text(expression.get("id"))
            sprite_asset_id = clean_text(expression.get("spriteAssetId")) or base_sprite_id
            if not expression_id or not sprite_asset_id:
                continue
            sprite_path = get_asset_path(asset_map, sprite_asset_id)
            if not sprite_path:
                add_warning(
                    warnings,
                    "renpy_missing_sprite_expression",
                    f"角色 {get_character_name(character_map, character_id)} 的表情 {expression_id} 没有可导出的立绘素材。",
                    characterId=character_id,
                    expressionId=expression_id,
                )
                continue
            expression_name = normalize_identifier(expression_id, "expr")
            lines.append(f"image {character_name} {expression_name} = {quote_renpy(sprite_path)}")
            defined.add((character_name, expression_name))
    return sorted(dict.fromkeys(lines)), defined


def render_variable_effect(effect: dict, variable_map: dict[str, dict], warnings: list[dict], indent: str) -> list[str]:
    effect_type = clean_text(effect.get("type"))
    variable_id = clean_text(effect.get("variableId") or effect.get("variableHint"))
    variable_name = normalize_identifier(variable_id, "var")
    if not variable_id:
        add_warning(warnings, "renpy_missing_variable_id", "变量效果缺少变量 ID，已保留为复核注释。")
        return [f"{indent}# Canvasia review variable effect: missing variable id"]
    if variable_id not in variable_map:
        add_warning(warnings, "renpy_unknown_variable", f"变量 {variable_id} 未在变量表中登记，Ren'Py 草稿仍会按同名变量写出。", variableId=variable_id)
    if effect_type == "variable_add":
        value = number_to_renpy_delta(effect.get("value"), warnings, variable_id)
        return [f"{indent}$ {variable_name} += {value}"]
    if effect_type == "variable_set":
        value = value_to_renpy(effect.get("value"))
        return [f"{indent}$ {variable_name} = {value}"]
    add_warning(warnings, "renpy_unknown_choice_effect", f"选项效果 {effect_type or 'unknown'} 暂未自动转换。", variableId=variable_id)
    return [f"{indent}# Canvasia review choice effect: {clean_text(effect_type, 'unknown')}"]


def render_choice_block(block: dict, context: dict) -> list[str]:
    warnings = context["warnings"]
    variable_map = context["variableMap"]
    scene_label_map = context["sceneLabelMap"]
    scene_id = context.get("sceneId")
    block_index = context.get("blockIndex")
    lines = ["    menu:"]
    options = as_list(block.get("options"))
    if not options:
        add_warning(warnings, "renpy_empty_choice", "选项卡没有选项，已导出 pass。", sceneId=scene_id, blockIndex=block_index)
        return [*lines, "        pass"]
    for option_index, option in enumerate(options):
        option_text = clean_text(option.get("text") or option.get("label"), f"Option {option_index + 1}")
        target_scene_id = clean_text(option.get("gotoSceneId") or option.get("targetSceneId") or option.get("target"))
        lines.append(f"        {quote_renpy(option_text)}:")
        for effect in as_list(option.get("effects")):
            lines.extend(render_variable_effect(effect, variable_map, warnings, "            "))
        if target_scene_id and target_scene_id != CHOICE_CONTINUE_TARGET:
            lines.append(f"            jump {get_scene_label(scene_label_map, target_scene_id)}")
        else:
            lines.append("            pass")
    return lines


def render_review_comment(block: dict, warnings: list[dict], scene_id: str, block_index: int) -> list[str]:
    block_type = clean_text(block.get("type"), "unknown")
    add_warning(
        warnings,
        "renpy_review_block",
        f"{block_type} 已作为复核注释导出，需要在 Ren'Py 中手动还原。",
        sceneId=scene_id,
        blockIndex=block_index,
    )
    detail = clean_text(block.get("text") or block.get("preset") or block.get("action") or block.get("assetId"), "manual port")
    return [f"    # Canvasia review {block_type}: {quote_renpy(detail)}"]


def normalize_condition_operator(operator: Any, warnings: list[dict], scene_id: str, block_index: int) -> str:
    safe_operator = clean_text(operator, "==")
    if safe_operator == "=":
        return "=="
    if safe_operator in CONDITION_OPERATORS:
        return safe_operator
    add_warning(
        warnings,
        "renpy_condition_operator_review",
        f"条件运算符 {safe_operator} 暂不支持，已按 == 导出。",
        sceneId=scene_id,
        blockIndex=block_index,
    )
    return "=="


def render_condition_rule_expression(rule: dict, context: dict) -> str:
    warnings = context["warnings"]
    scene_id = clean_text(context.get("sceneId"))
    block_index = int(context.get("blockIndex") or 0)
    variable_id = clean_text(rule.get("variableId") or rule.get("variableHint"))
    if not variable_id:
        add_warning(
            warnings,
            "renpy_condition_missing_variable",
            "条件判断缺少变量 ID，已按 True 导出。",
            sceneId=scene_id,
            blockIndex=block_index,
        )
        return "True"
    variable_name = normalize_identifier(variable_id, "var")
    operator = normalize_condition_operator(rule.get("operator"), warnings, scene_id, block_index)
    return f"{variable_name} {operator} {value_to_renpy(rule.get('value'))}"


def render_condition_target_lines(target_scene_id: Any, context: dict, indent: str = "        ") -> list[str]:
    target = clean_text(target_scene_id)
    if not target:
        add_warning(
            context["warnings"],
            "renpy_condition_missing_target",
            "条件分支缺少目标场景，已导出 pass。",
            sceneId=context.get("sceneId"),
            blockIndex=context.get("blockIndex"),
        )
        return [f"{indent}pass"]
    return [f"{indent}jump {get_scene_label(context['sceneLabelMap'], target)}"]


def render_condition_block(block: dict, context: dict) -> list[str]:
    branches = as_list(block.get("branches"))
    if not branches:
        add_warning(
            context["warnings"],
            "renpy_empty_condition",
            "条件判断没有分支，已导出 pass。",
            sceneId=context.get("sceneId"),
            blockIndex=context.get("blockIndex"),
        )
        return ["    pass"]

    lines: list[str] = []
    for branch_index, branch in enumerate(branches):
        expression = " and ".join(
            filter(
                None,
                (render_condition_rule_expression(rule, context) for rule in as_list(branch.get("when"))),
            )
        ) or "True"
        lines.append(f"    {'if' if branch_index == 0 else 'elif'} {expression}:")
        target = branch.get("gotoSceneId") or branch.get("targetSceneId") or branch.get("targetHint")
        lines.extend(render_condition_target_lines(target, context))

    else_target = block.get("elseGotoSceneId") or block.get("elseTargetSceneId") or block.get("elseTargetHint")
    if else_target:
        lines.append("    else:")
        lines.extend(render_condition_target_lines(else_target, context))
    return lines


def render_video_block(block: dict, context: dict) -> list[str]:
    asset_map = context["assetMap"]
    path = get_asset_path(asset_map, block.get("assetId"))
    if not path:
        add_warning(
            context["warnings"],
            "renpy_missing_video_asset",
            "视频卡没有找到可播放素材，已导出复核注释。",
            sceneId=context.get("sceneId"),
            blockIndex=context.get("blockIndex"),
        )
        return [f"    # Canvasia review missing video: {quote_renpy(clean_text(block.get('assetId'), 'video'))}"]

    playback = build_video_playback_spec(path, block, context)
    delay_clause = f", delay={format_renpy_seconds(playback['delay'])}" if playback["delay"] > 0 else ""
    return [f"    $ renpy.movie_cutscene({quote_renpy(playback['path'])}{delay_clause})"]


def render_credits_block(block: dict) -> list[str]:
    title = clean_text(block.get("title"), "STAFF")
    subtitle = clean_text(block.get("subtitle"))
    credit_lines = [clean_text(line) for line in as_list(block.get("lines")) if clean_text(line)]
    try:
        duration = float(block.get("durationSeconds") or 12)
    except (TypeError, ValueError):
        duration = 12
    text = "\n".join([line for line in [title, subtitle, *credit_lines] if line])
    return [
        "    window hide",
        "    scene black with fade",
        f"    show text {quote_renpy(text)} at truecenter with dissolve",
        f"    $ renpy.pause({duration:g})",
        "    hide text with dissolve",
        "    window show",
    ]


def render_character_show_block(block: dict, context: dict) -> list[str]:
    character_id = clean_text(block.get("characterId"), "character")
    expression_id = clean_text(block.get("expressionId"))
    stage = get_safe_character_stage(block.get("stage"))
    custom_stage = has_custom_character_stage(stage)
    at_target = (
        get_character_stage_transform_name(context["sceneLabelMap"], context.get("sceneId"), context.get("blockIndex"))
        if custom_stage
        else get_safe_position(block.get("position"))
    )
    transition = get_character_transition_expression(block, context, "show")
    expression = f" {normalize_identifier(expression_id, 'expr')}" if expression_id else ""
    zorder = f" zorder {20 + stage['layer']}" if custom_stage and stage["layer"] else ""
    transition_suffix = f" with {transition}" if transition else ""
    return [f"    show {normalize_identifier(character_id, 'character')}{expression} at {at_target}{zorder}{transition_suffix}"]


def render_character_hide_block(block: dict, context: dict) -> list[str]:
    transition = get_character_transition_expression(block, context, "hide")
    transition_suffix = f" with {transition}" if transition else ""
    return [f"    hide {normalize_identifier(block.get('characterId'), 'character')}{transition_suffix}"]


def render_background_block(block: dict, context: dict) -> list[str]:
    asset_id = clean_text(block.get("assetId"), "missing_background")
    transition = get_background_transition_expression(block, context)
    transition_suffix = f" with {transition}" if transition else ""
    return [f"    scene {normalize_identifier(asset_id, 'background')}{transition_suffix}"]


def render_screen_flash_block(block: dict) -> list[str]:
    duration = get_screen_effect_duration_seconds(block)
    out_time = clamp_number(duration * 0.2, 0.05, 0.28)
    hold_time = clamp_number(duration * 0.12, 0.03, 0.16)
    in_time = max(0.05, duration - out_time - hold_time)
    color = get_effect_color_hex(FLASH_COLOR_HEX, block.get("color"), "white")
    return [
        f"    with Fade({format_renpy_seconds(out_time)}, {format_renpy_seconds(hold_time)}, {format_renpy_seconds(in_time)}, color=\"{color}\")"
    ]


def render_screen_fade_block(block: dict, context: dict) -> list[str]:
    action = clean_text(block.get("action"), "fade_out")
    duration = get_screen_effect_duration_seconds(block)
    color = get_effect_color_hex(FADE_COLOR_HEX, block.get("color"), "black")
    if action == "fade_in":
        return [f"    with Fade(0, 0, {format_renpy_seconds(duration)}, color=\"{color}\")"]
    if action != "fade_out":
        add_warning(
            context["warnings"],
            "renpy_screen_fade_action_review",
            f"黑场动作 {action} 暂未识别，已按淡出导出。",
            sceneId=context.get("sceneId"),
            blockIndex=context.get("blockIndex"),
        )
    return [f"    with Fade({format_renpy_seconds(duration)}, 0, 0, color=\"{color}\")"]


def render_story_block(block: dict, context: dict) -> list[str]:
    block_type = clean_text(block.get("type"), "unknown")
    asset_map = context["assetMap"]
    character_map = context["characterMap"]
    variable_map = context["variableMap"]
    warnings = context["warnings"]
    scene_id = clean_text(context.get("sceneId"))
    block_index = int(context.get("blockIndex") or 0)

    if block_type == "background":
        return render_background_block(block, context)
    if block_type == "character_show":
        return render_character_show_block(block, context)
    if block_type == "character_hide":
        return render_character_hide_block(block, context)
    if block_type == "music_play":
        fade_in = seconds_from_ms(block.get("fadeInMs"))
        fade_suffix = f" fadein {fade_in:g}" if fade_in else ""
        return [f"    play music {quote_renpy(get_asset_path(asset_map, block.get('assetId')) or 'audio/bgm.ogg')}{fade_suffix}{render_music_loop_clause(block)}{render_volume_clause(block.get('volume'))}"]
    if block_type == "music_stop":
        fade_out = seconds_from_ms(block.get("fadeOutMs"))
        return [f"    stop music{f' fadeout {fade_out:g}' if fade_out else ''}"]
    if block_type == "sfx_play":
        return [f"    play sound {quote_renpy(get_asset_path(asset_map, block.get('assetId')) or 'audio/sfx.ogg')}{render_volume_clause(block.get('volume'))}"]
    if block_type == "video_play":
        return render_video_block(block, context)
    if block_type == "credits_roll":
        return render_credits_block(block)
    if block_type == "condition":
        return render_condition_block(block, context)
    if block_type == "screen_shake":
        return ["    with hpunch"]
    if block_type == "screen_flash":
        return render_screen_flash_block(block)
    if block_type == "screen_fade":
        return render_screen_fade_block(block, context)
    if block_type == "camera_zoom":
        return render_camera_zoom_block(block, context)
    if block_type == "camera_pan":
        return render_camera_pan_block(block, context)
    if block_type == "screen_filter":
        return render_screen_filter_block(block, context)
    if block_type == "depth_blur":
        return render_depth_blur_block(block, context)
    if block_type == "particle_effect":
        return render_particle_block(block, context)
    if block_type in {"dialogue", "narration"}:
        line = render_renpy_text(block)
        output: list[str] = []
        voice_path = get_asset_path(asset_map, block.get("voiceAssetId"))
        if voice_path:
            output.append(f"    voice {quote_renpy(voice_path)}")
        if block_type == "dialogue" and clean_text(block.get("speakerId")):
            output.append(f"    {normalize_identifier(block.get('speakerId'), 'character')} {quote_renpy(line)}")
        else:
            if block_type == "dialogue":
                add_warning(warnings, "renpy_missing_speaker", "台词缺少说话人，已作为旁白导出。", sceneId=scene_id, blockIndex=block_index)
            output.append(f"    {quote_renpy(line)}")
        return output
    if block_type == "choice":
        return render_choice_block(block, context)
    if block_type == "jump":
        target_scene_id = clean_text(block.get("targetSceneId") or block.get("target"))
        if not target_scene_id:
            add_warning(warnings, "renpy_missing_jump_target", "跳转卡没有目标，已导出 pass。", sceneId=scene_id, blockIndex=block_index)
            return ["    pass"]
        return [f"    jump {get_scene_label(context['sceneLabelMap'], target_scene_id)}"]
    if block_type == "wait":
        seconds = block.get("durationSeconds") or seconds_from_ms(block.get("durationMs")) or 0.5
        return [f"    $ renpy.pause({float(seconds):g})"]
    if block_type in {"variable_set", "variable_add"}:
        return render_variable_effect(block, variable_map, warnings, "    ")
    if block_type in COMMENT_ONLY_BLOCK_TYPES:
        return render_review_comment(block, warnings, scene_id, block_index)
    add_warning(warnings, "renpy_unknown_block", f"{block_type} 暂未映射，已作为复核注释导出。", sceneId=scene_id, blockIndex=block_index)
    return render_review_comment(block, warnings, scene_id, block_index)


def build_renpy_draft_export(bundle: dict, assets_doc: dict | None = None) -> dict:
    project = bundle.get("project") if isinstance(bundle.get("project"), dict) else {}
    asset_map = build_asset_map(assets_doc or bundle.get("assets") or {})
    character_map = build_character_map(bundle)
    variable_map = build_variable_map(bundle)
    scene_records = build_scene_records(bundle)
    scene_label_map = {record["sceneId"]: record["sceneLabel"] for record in scene_records}
    project_resolution = get_project_resolution(bundle)
    warnings: list[dict] = []
    sprite_definitions, _defined_sprites = build_sprite_definitions(character_map, asset_map, warnings)
    character_stage_transforms = build_character_stage_transform_definitions(scene_records, scene_label_map)

    lines = [
        f"# {clean_text(project.get('title'), 'Canvasia Project')} - Canvasia Ren'Py Starter",
        "# Generated for migration and collaboration. Review custom effects before release.",
        "",
        *build_variable_definitions(variable_map),
        "",
        *build_asset_image_definitions(asset_map),
        *sprite_definitions,
        "",
        *character_stage_transforms,
        *([""] if character_stage_transforms else []),
        *build_character_definitions(character_map),
        "",
    ]

    for scene_index, record in enumerate(scene_records):
        scene = record["scene"]
        scene_id = record["sceneId"]
        scene_name = clean_text(scene.get("name") or scene.get("title"), scene_id)
        lines.append(f"# {record['chapterName']} / {scene_name}")
        lines.append(f"label {record['sceneLabel']}:")
        blocks = as_list(scene.get("blocks"))
        camera_state = get_default_camera_state()
        music_scope_stop_plan = build_music_scope_stop_plan(blocks, {"warnings": warnings, "sceneId": scene_id})
        if not blocks:
            add_warning(warnings, "renpy_empty_scene", "空场景已导出 pass。", sceneId=scene_id)
            lines.append("    pass")
        for block_index, block in enumerate(blocks):
            if block_index in music_scope_stop_plan["before"]:
                lines.extend(music_scope_stop_plan["before"][block_index])
            block_context = {
                "assetMap": asset_map,
                "characterMap": character_map,
                "variableMap": variable_map,
                "sceneLabelMap": scene_label_map,
                "warnings": warnings,
                "sceneId": scene_id,
                "blockIndex": block_index,
                "cameraState": camera_state,
                "projectResolution": project_resolution,
            }
            lines.extend(render_story_block(block, block_context))
            if block_index in music_scope_stop_plan["after"]:
                lines.extend(music_scope_stop_plan["after"][block_index])
        last_type = clean_text((blocks[-1] if blocks else {}).get("type"))
        if last_type not in {"jump", "choice", "return", "credits_roll"}:
            lines.append("    return")
        lines.append("")

    script = "\n".join(lines).replace("\n\n\n", "\n\n").strip() + "\n"
    return {
        "formatVersion": 1,
        "projectTitle": clean_text(project.get("title"), "Canvasia Project"),
        "sceneCount": len(scene_records),
        "characterCount": len(character_map),
        "variableCount": len(variable_map),
        "assetDefinitionCount": len(build_asset_image_definitions(asset_map)) + len(sprite_definitions),
        "warningCount": len(warnings),
        "warnings": warnings,
        "script": script,
    }


def build_renpy_options_file(bundle: dict) -> str:
    project = bundle.get("project") if isinstance(bundle.get("project"), dict) else {}
    resolution = project.get("resolution") if isinstance(project.get("resolution"), dict) else {}
    width = int(resolution.get("width") or 1280)
    height = int(resolution.get("height") or 720)
    title = clean_text(project.get("title"), "Canvasia Project")
    return "\n".join(
        [
            f"define config.name = {quote_renpy(title)}",
            "define config.version = \"0.1\"",
            f"define config.screen_width = {width}",
            f"define config.screen_height = {height}",
            "",
        ]
    )


def build_renpy_review_notes(export_result: dict) -> str:
    warnings = as_list(export_result.get("warnings"))
    lines = [
        f"# {clean_text(export_result.get('projectTitle'), 'Canvasia Project')} Ren'Py Migration Notes",
        "",
        f"- Scenes: {export_result.get('sceneCount', 0)}",
        f"- Characters: {export_result.get('characterCount', 0)}",
        f"- Variables: {export_result.get('variableCount', 0)}",
        f"- Asset definitions: {export_result.get('assetDefinitionCount', 0)}",
        f"- Review items: {export_result.get('warningCount', 0)}",
        "",
    ]
    if not warnings:
        lines.append("No migration review items were generated.")
        lines.append("")
        return "\n".join(lines)
    lines.extend(["| # | Code | Scene | Block | Message |", "| --- | --- | --- | --- | --- |"])
    for index, warning in enumerate(warnings, start=1):
        row = [
            str(index),
            clean_text(warning.get("code")),
            clean_text(warning.get("sceneId")),
            clean_text(warning.get("blockIndex")),
            clean_text(warning.get("message")),
        ]
        lines.append("| " + " | ".join(cell.replace("|", "\\|") for cell in row) + " |")
    lines.append("")
    return "\n".join(lines)


def build_renpy_readme(export_result: dict) -> str:
    return "\n".join(
        [
            "# Canvasia Ren'Py Starter Bundle",
            "",
            "This bundle is a migration-friendly starter project generated from Canvasia Engine data.",
            "",
            "## Files",
            "",
            f"- `{RENPY_GAME_DIR_NAME}/{RENPY_SCRIPT_FILE_NAME}`: converted labels, dialogue, choices, audio cues, variables, and basic presentation commands.",
            f"- `{RENPY_GAME_DIR_NAME}/{RENPY_OPTIONS_FILE_NAME}`: project title and resolution defaults.",
            f"- `{RENPY_GAME_DIR_NAME}/assets/`: copied assets referenced by the generated script.",
            f"- `{RENPY_REVIEW_FILE_NAME}`: review notes for custom effects and migration gaps.",
            f"- `{RENPY_MANIFEST_FILE_NAME}`: machine-readable export summary.",
            f"- `{RENPY_QUALITY_MARKDOWN_FILE_NAME}` / `{RENPY_QUALITY_REPORT_FILE_NAME}`: bundle integrity and migration quality checks.",
            f"- `{RENPY_VERIFY_SCRIPT_FILE_NAME}`: local verifier for labels, jumps, and referenced files.",
            "",
            "## How to continue",
            "",
            "1. Create or open a Ren'Py project.",
            f"2. Copy the `{RENPY_GAME_DIR_NAME}` folder contents into the Ren'Py project's `game` folder.",
            f"3. Open `{RENPY_REVIEW_FILE_NAME}` and replace review comments with native Ren'Py transforms, screens, or Python logic where needed.",
            f"4. Run `python3 {RENPY_VERIFY_SCRIPT_FILE_NAME}` from this folder to catch broken labels or missing files before opening Ren'Py.",
            "5. Run the project in Ren'Py and resolve label, asset, or transform issues reported by the launcher.",
            "",
            f"Review items generated: {export_result.get('warningCount', 0)}",
            "",
        ]
    )


def normalize_renpy_asset_reference(value: str) -> str:
    clean_value = value.strip().replace("\\", "/")
    while clean_value.startswith("<"):
        next_value = RENPY_PLAYBACK_SPEC_PREFIX_PATTERN.sub("", clean_value, count=1).strip()
        if next_value == clean_value:
            break
        clean_value = next_value
    return clean_value


def is_renpy_asset_reference(value: str) -> bool:
    clean_value = normalize_renpy_asset_reference(value)
    return bool(clean_value and not clean_value.startswith(("#", "data:", "http://", "https://")) and RENPY_PATH_SUFFIX_PATTERN.search(clean_value))


def collect_renpy_script_references(script: str) -> dict:
    label_counts: dict[str, int] = {}
    jumps: list[str] = []
    asset_references: list[str] = []
    label_pattern = re.compile(r"^\s*label\s+([A-Za-z_][A-Za-z0-9_]*)\s*:", re.MULTILINE)
    jump_pattern = re.compile(r"^\s*jump\s+([A-Za-z_][A-Za-z0-9_]*)\b", re.MULTILINE)
    quoted_pattern = re.compile(r'"((?:\\"|[^"])*)"')

    for match in label_pattern.finditer(script):
        label = match.group(1)
        label_counts[label] = label_counts.get(label, 0) + 1
    for match in jump_pattern.finditer(script):
        jumps.append(match.group(1))
    for match in quoted_pattern.finditer(script):
        value = match.group(1).replace('\\"', '"').replace("\\\\", "\\")
        if is_renpy_asset_reference(value):
            asset_references.append(normalize_renpy_asset_reference(value))

    return {
        "labels": sorted(label_counts),
        "duplicateLabels": sorted(label for label, count in label_counts.items() if count > 1),
        "jumps": sorted(dict.fromkeys(jumps)),
        "assetReferences": sorted(dict.fromkeys(asset_references)),
    }


def add_quality_issue(issues: list[dict], severity: str, code: str, message: str, **context: Any) -> None:
    issues.append(
        {
            "severity": severity,
            "code": code,
            "message": message,
            **{key: value for key, value in context.items() if value not in (None, "", [])},
        }
    )


def build_renpy_quality_report(build_dir: Path, export_result: dict) -> dict:
    root = Path(build_dir)
    game_dir = root / RENPY_GAME_DIR_NAME
    script_path = game_dir / RENPY_SCRIPT_FILE_NAME
    options_path = game_dir / RENPY_OPTIONS_FILE_NAME
    issues: list[dict] = []
    references = {"labels": [], "duplicateLabels": [], "jumps": [], "assetReferences": []}

    if not script_path.is_file():
        add_quality_issue(issues, "error", "renpy_missing_script", "game/script.rpy is missing.")
        script = ""
    else:
        script = script_path.read_text(encoding="utf-8")
        if not script.strip():
            add_quality_issue(issues, "error", "renpy_empty_script", "game/script.rpy is empty.")
        references = collect_renpy_script_references(script)

    if not options_path.is_file():
        add_quality_issue(issues, "error", "renpy_missing_options", "game/options.rpy is missing.")

    labels = set(references["labels"])
    if export_result.get("sceneCount", 0) and not labels:
        add_quality_issue(issues, "error", "renpy_missing_labels", "No Ren'Py labels were generated for the project scenes.")

    for label in references["duplicateLabels"]:
        add_quality_issue(issues, "error", "renpy_duplicate_label", f"Duplicate Ren'Py label: {label}", label=label)

    for jump in references["jumps"]:
        if jump not in labels:
            add_quality_issue(issues, "error", "renpy_undefined_jump", f"Jump target is not defined: {jump}", label=jump)

    missing_asset_references: list[str] = []
    for asset_reference in references["assetReferences"]:
        if not (game_dir / asset_reference).is_file():
            missing_asset_references.append(asset_reference)
            add_quality_issue(
                issues,
                "error",
                "renpy_missing_asset_reference",
                f"Referenced asset is missing from game folder: {asset_reference}",
                path=asset_reference,
            )

    review_comment_count = script.count("Canvasia review")
    if review_comment_count:
        add_quality_issue(
            issues,
            "review",
            "renpy_review_comments_present",
            f"{review_comment_count} generated review comments should be checked in Ren'Py.",
            count=review_comment_count,
        )

    for warning in as_list(export_result.get("warnings")):
        add_quality_issue(
            issues,
            "review",
            clean_text(warning.get("code"), "renpy_migration_review"),
            clean_text(warning.get("message"), "Review generated migration item."),
            sceneId=warning.get("sceneId"),
            blockIndex=warning.get("blockIndex"),
        )

    error_count = sum(1 for issue in issues if issue["severity"] == "error")
    review_count = sum(1 for issue in issues if issue["severity"] == "review")
    status = "blocked" if error_count else "review" if review_count else "ready"

    return {
        "formatVersion": 1,
        "status": status,
        "summary": {
            "labelCount": len(references["labels"]),
            "jumpCount": len(references["jumps"]),
            "assetReferenceCount": len(references["assetReferences"]),
            "missingAssetReferenceCount": len(missing_asset_references),
            "duplicateLabelCount": len(references["duplicateLabels"]),
            "reviewCommentCount": review_comment_count,
            "errorCount": error_count,
            "reviewCount": review_count,
        },
        "files": {
            "script": f"{RENPY_GAME_DIR_NAME}/{RENPY_SCRIPT_FILE_NAME}",
            "options": f"{RENPY_GAME_DIR_NAME}/{RENPY_OPTIONS_FILE_NAME}",
            "reviewNotes": RENPY_REVIEW_FILE_NAME,
            "manifest": RENPY_MANIFEST_FILE_NAME,
        },
        "references": references,
        "issues": issues,
    }


def build_renpy_quality_markdown(report: dict) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    issues = as_list(report.get("issues"))
    lines = [
        "# Canvasia Ren'Py Bundle Quality Report",
        "",
        f"- Status: {clean_text(report.get('status'), 'unknown')}",
        f"- Labels: {summary.get('labelCount', 0)}",
        f"- Jumps: {summary.get('jumpCount', 0)}",
        f"- Asset references: {summary.get('assetReferenceCount', 0)}",
        f"- Missing asset references: {summary.get('missingAssetReferenceCount', 0)}",
        f"- Review comments: {summary.get('reviewCommentCount', 0)}",
        "",
    ]
    if not issues:
        lines.extend(["No issues were found by the generated bundle checks.", ""])
        return "\n".join(lines)
    lines.extend(["| Severity | Code | Message |", "| --- | --- | --- |"])
    for issue in issues:
        lines.append(
            "| "
            + " | ".join(
                clean_text(value).replace("|", "\\|")
                for value in [issue.get("severity"), issue.get("code"), issue.get("message")]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def build_renpy_verifier_script() -> str:
    return f'''from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
GAME_DIR = ROOT / "{RENPY_GAME_DIR_NAME}"
SCRIPT_PATH = GAME_DIR / "{RENPY_SCRIPT_FILE_NAME}"
OPTIONS_PATH = GAME_DIR / "{RENPY_OPTIONS_FILE_NAME}"
PATH_SUFFIX_PATTERN = re.compile(r"\\.(?:png|jpe?g|webp|gif|avif|mp3|ogg|wav|m4a|aac|flac|mp4|webm|mov|m4v)$", re.IGNORECASE)
PLAYBACK_SPEC_PREFIX_PATTERN = re.compile(r"^<[^>]+>")


def normalize_asset_reference(value: str) -> str:
    clean = value.strip().replace("\\\\", "/")
    while clean.startswith("<"):
        next_clean = PLAYBACK_SPEC_PREFIX_PATTERN.sub("", clean, count=1).strip()
        if next_clean == clean:
            break
        clean = next_clean
    return clean


def is_asset_reference(value: str) -> bool:
    clean = normalize_asset_reference(value)
    return bool(clean and not clean.startswith(("#", "data:", "http://", "https://")) and PATH_SUFFIX_PATTERN.search(clean))


def main() -> int:
    issues = []
    if not SCRIPT_PATH.is_file():
        issues.append("missing game/script.rpy")
        script = ""
    else:
        script = SCRIPT_PATH.read_text(encoding="utf-8")
        if not script.strip():
            issues.append("empty game/script.rpy")
    if not OPTIONS_PATH.is_file():
        issues.append("missing game/options.rpy")

    labels = re.findall(r"^\\s*label\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*:", script, flags=re.MULTILINE)
    label_set = set(labels)
    for label in sorted(label for label in label_set if labels.count(label) > 1):
        issues.append(f"duplicate label: {{label}}")
    for jump in sorted(set(re.findall(r"^\\s*jump\\s+([A-Za-z_][A-Za-z0-9_]*)\\b", script, flags=re.MULTILINE))):
        if jump not in label_set:
            issues.append(f"undefined jump target: {{jump}}")
    for quoted in re.findall(r'"((?:\\\\"|[^"])*)"', script):
        path = quoted.replace('\\\\"', '"').replace("\\\\\\\\", "\\\\").replace("\\\\", "/")
        normalized_path = normalize_asset_reference(path)
        if is_asset_reference(normalized_path) and not (GAME_DIR / normalized_path).is_file():
            issues.append(f"missing asset reference: {{normalized_path}}")

    if issues:
        print("Canvasia Ren'Py Starter verification failed:")
        for issue in issues:
            print(f"- {{issue}}")
        return 1
    print(f"Canvasia Ren'Py Starter verification passed: {{len(label_set)}} labels, {{script.count('Canvasia review')}} review comments.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def write_renpy_quality_files(build_dir: Path, export_result: dict) -> dict:
    report = build_renpy_quality_report(build_dir, export_result)
    report_path = build_dir / RENPY_QUALITY_REPORT_FILE_NAME
    markdown_path = build_dir / RENPY_QUALITY_MARKDOWN_FILE_NAME
    verifier_path = build_dir / RENPY_VERIFY_SCRIPT_FILE_NAME

    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(build_renpy_quality_markdown(report), encoding="utf-8")
    verifier_path.write_text(build_renpy_verifier_script(), encoding="utf-8")

    return {
        "qualityStatus": report["status"],
        "qualitySummary": report["summary"],
        "qualityReportName": RENPY_QUALITY_REPORT_FILE_NAME,
        "qualityReportPath": str(report_path),
        "qualityMarkdownName": RENPY_QUALITY_MARKDOWN_FILE_NAME,
        "qualityMarkdownPath": str(markdown_path),
        "verifierName": RENPY_VERIFY_SCRIPT_FILE_NAME,
        "verifierPath": str(verifier_path),
    }


def write_renpy_starter_project(build_dir: Path, bundle: dict, assets_doc: dict | None = None) -> dict:
    export_result = build_renpy_draft_export(bundle, assets_doc)
    game_dir = build_dir / RENPY_GAME_DIR_NAME
    game_dir.mkdir(parents=True, exist_ok=True)
    script_path = game_dir / RENPY_SCRIPT_FILE_NAME
    options_path = game_dir / RENPY_OPTIONS_FILE_NAME
    manifest_path = build_dir / RENPY_MANIFEST_FILE_NAME
    review_path = build_dir / RENPY_REVIEW_FILE_NAME
    readme_path = build_dir / RENPY_README_FILE_NAME

    script_path.write_text(export_result["script"], encoding="utf-8")
    options_path.write_text(build_renpy_options_file(bundle), encoding="utf-8")
    manifest_path.write_text(json.dumps({key: value for key, value in export_result.items() if key != "script"}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    review_path.write_text(build_renpy_review_notes(export_result), encoding="utf-8")
    readme_path.write_text(build_renpy_readme(export_result), encoding="utf-8")
    quality_files = write_renpy_quality_files(build_dir, export_result)

    return {
        **{key: value for key, value in export_result.items() if key != "script"},
        "scriptName": f"{RENPY_GAME_DIR_NAME}/{RENPY_SCRIPT_FILE_NAME}",
        "scriptPath": str(script_path),
        "optionsName": f"{RENPY_GAME_DIR_NAME}/{RENPY_OPTIONS_FILE_NAME}",
        "optionsPath": str(options_path),
        "manifestName": RENPY_MANIFEST_FILE_NAME,
        "manifestPath": str(manifest_path),
        "reviewName": RENPY_REVIEW_FILE_NAME,
        "reviewPath": str(review_path),
        "readmeName": RENPY_README_FILE_NAME,
        "readmePath": str(readme_path),
        **quality_files,
    }
