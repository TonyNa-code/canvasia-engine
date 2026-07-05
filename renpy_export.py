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

COMMENT_ONLY_BLOCK_TYPES = {
    "particle_effect",
    "screen_filter",
    "depth_blur",
    "camera_zoom",
    "camera_pan",
}
CONDITION_OPERATORS = {"==", "!=", ">=", "<=", ">", "<"}
POSITION_XALIGN = {"left": 0.25, "center": 0.5, "right": 0.75}
DEFAULT_CHARACTER_STAGE = {
    "offsetX": 0,
    "offsetY": 0,
    "scale": 100,
    "opacity": 100,
    "layer": 0,
    "flipX": False,
}
CHARACTER_SHOW_TRANSITIONS = {
    "fade": "dissolve",
    "dissolve": "dissolve",
    "slide_left": "moveinleft",
    "slide_right": "moveinright",
    "rise": "moveinbottom",
}
CHARACTER_HIDE_TRANSITIONS = {
    "fade": "dissolve",
    "dissolve": "dissolve",
    "slide_left": "moveoutleft",
    "slide_right": "moveoutright",
    "rise": "moveoutbottom",
}
TEXT_SPEED_CPS = {
    "slow": 24,
    "normal": 42,
    "fast": 72,
    "instant": 10000,
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


def seconds_from_ms(value: Any) -> float:
    try:
        ms = float(value or 0)
    except (TypeError, ValueError):
        return 0
    return round(ms / 1000, 2) if ms > 0 else 0


def get_safe_volume_ratio(value: Any, fallback: float = 100) -> float:
    try:
        percent = float(value if value not in (None, "") else fallback)
    except (TypeError, ValueError):
        percent = fallback
    return round(clamp_number(percent, 0, 100) / 100, 2)


def render_volume_clause(value: Any, fallback: float = 100) -> str:
    ratio = get_safe_volume_ratio(value, fallback)
    return "" if ratio == 1 else f" volume {ratio:g}"


def render_music_loop_clause(block: dict) -> str:
    if block.get("loop") is True:
        return " loop"
    if block.get("loop") is False:
        return " noloop"
    return ""


def render_music_scope_review(block: dict, context: dict) -> list[str]:
    end_mode = clean_text(block.get("endMode"), "until_next_music")
    if end_mode not in {"scene_end", "after_block"}:
        return []
    end_block_id = clean_text(block.get("endBlockId"), "auto")
    add_warning(
        context["warnings"],
        "renpy_music_scope_review",
        "BGM 播放范围需要在 Ren'Py 中复核并按需要补 stop music。",
        sceneId=context.get("sceneId"),
        blockIndex=context.get("blockIndex"),
    )
    return [f"    # Canvasia review music scope: endMode={end_mode}, endBlockId={end_block_id}, fadeOutMs={block.get('fadeOutMs', 'default')}"]


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


def get_transition_duration_seconds(block: dict) -> float:
    try:
        ms = float(block.get("transitionDurationMs", 600))
    except (TypeError, ValueError):
        ms = 600
    return round(clamp_number(ms, 0, 5000) / 1000, 2)


def get_character_transition_expression(block: dict, context: dict, direction: str = "show") -> str:
    transition = clean_text(block.get("transition"), "fade")
    seconds = get_transition_duration_seconds(block)
    if transition == "none" or seconds <= 0:
        return ""
    if transition in {"fade", "dissolve"}:
        return f"Dissolve({seconds:g})"
    if transition == "pop":
        add_warning(
            context["warnings"],
            "renpy_character_transition_review",
            "轻微弹出转场已按淡入导出，请在 Ren'Py 中按需要替换为自定义 ATL。",
            sceneId=context.get("sceneId"),
            blockIndex=context.get("blockIndex"),
        )
        return f"Dissolve({seconds:g})"
    transition_map = CHARACTER_HIDE_TRANSITIONS if direction == "hide" else CHARACTER_SHOW_TRANSITIONS
    if transition in transition_map:
        if seconds != 0.6:
            add_warning(
                context["warnings"],
                "renpy_character_transition_timing_review",
                f"{transition} 转场时长需要在 Ren'Py 中复核。",
                sceneId=context.get("sceneId"),
                blockIndex=context.get("blockIndex"),
            )
        return transition_map[transition]
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

    lines: list[str] = []
    try:
        start = float(block.get("startTimeSeconds") or 0)
    except (TypeError, ValueError):
        start = 0
    try:
        end = float(block.get("endTimeSeconds") or 0)
    except (TypeError, ValueError):
        end = 0
    if start > 0 or end > 0 or block.get("volume") not in (None, ""):
        add_warning(
            context["warnings"],
            "renpy_video_timing_review",
            "视频裁段或音量设置需要在 Ren'Py 中复核。",
            sceneId=context.get("sceneId"),
            blockIndex=context.get("blockIndex"),
        )
        lines.append(f"    # Canvasia review video timing: start={start:g}, end={end:g}, volume={block.get('volume', 'default')}")
    lines.append(f"    $ renpy.movie_cutscene({quote_renpy(path)})")
    return lines


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


def render_story_block(block: dict, context: dict) -> list[str]:
    block_type = clean_text(block.get("type"), "unknown")
    asset_map = context["assetMap"]
    character_map = context["characterMap"]
    variable_map = context["variableMap"]
    warnings = context["warnings"]
    scene_id = clean_text(context.get("sceneId"))
    block_index = int(context.get("blockIndex") or 0)

    if block_type == "background":
        asset_id = clean_text(block.get("assetId"), "missing_background")
        return [f"    scene {normalize_identifier(asset_id, 'background')} with fade"]
    if block_type == "character_show":
        return render_character_show_block(block, context)
    if block_type == "character_hide":
        return render_character_hide_block(block, context)
    if block_type == "music_play":
        fade_in = seconds_from_ms(block.get("fadeInMs"))
        fade_suffix = f" fadein {fade_in:g}" if fade_in else ""
        return [
            f"    play music {quote_renpy(get_asset_path(asset_map, block.get('assetId')) or 'audio/bgm.ogg')}{fade_suffix}{render_music_loop_clause(block)}{render_volume_clause(block.get('volume'))}",
            *render_music_scope_review(block, context),
        ]
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
        return ['    with Fade(0.08, 0.0, 0.28, color="#ffffff")']
    if block_type == "screen_fade":
        return ["    with fade"]
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
        if not blocks:
            add_warning(warnings, "renpy_empty_scene", "空场景已导出 pass。", sceneId=scene_id)
            lines.append("    pass")
        for block_index, block in enumerate(blocks):
            block_context = {
                "assetMap": asset_map,
                "characterMap": character_map,
                "variableMap": variable_map,
                "sceneLabelMap": scene_label_map,
                "warnings": warnings,
                "sceneId": scene_id,
                "blockIndex": block_index,
            }
            lines.extend(render_story_block(block, block_context))
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


def is_renpy_asset_reference(value: str) -> bool:
    clean_value = value.strip().replace("\\", "/")
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
            asset_references.append(value.replace("\\", "/"))

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


def is_asset_reference(value: str) -> bool:
    clean = value.strip().replace("\\\\", "/")
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
        if is_asset_reference(path) and not (GAME_DIR / path).is_file():
            issues.append(f"missing asset reference: {{path}}")

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
