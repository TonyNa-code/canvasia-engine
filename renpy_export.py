from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


RENPY_GAME_DIR_NAME = "game"
RENPY_SCRIPT_FILE_NAME = "script.rpy"
RENPY_OPTIONS_FILE_NAME = "options.rpy"
RENPY_MANIFEST_FILE_NAME = "canvasia_renpy_migration_manifest.json"
RENPY_REVIEW_FILE_NAME = "CANVASIA_RENPY_MIGRATION_NOTES.md"
RENPY_README_FILE_NAME = "README_Canvasia_RenPy_Starter.md"
CHOICE_CONTINUE_TARGET = "__continue__"

COMMENT_ONLY_BLOCK_TYPES = {
    "particle_effect",
    "screen_shake",
    "screen_flash",
    "screen_filter",
    "depth_blur",
    "camera_zoom",
    "camera_pan",
    "video_play",
    "credits_roll",
    "condition",
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
    return '"' + str(value or "").replace("\\", "\\\\").replace('"', '\\"') + '"'


def value_to_renpy(value: Any) -> str:
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    if value is None:
        return "None"
    return quote_renpy(value)


def seconds_from_ms(value: Any) -> float:
    try:
        ms = float(value or 0)
    except (TypeError, ValueError):
        return 0
    return round(ms / 1000, 2) if ms > 0 else 0


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
    variable_id = clean_text(effect.get("variableId"))
    variable_name = normalize_identifier(variable_id, "var")
    value = value_to_renpy(effect.get("value"))
    if not variable_id:
        add_warning(warnings, "renpy_missing_variable_id", "变量效果缺少变量 ID，已保留为复核注释。")
        return [f"{indent}# Canvasia review variable effect: missing variable id"]
    if variable_id not in variable_map:
        add_warning(warnings, "renpy_unknown_variable", f"变量 {variable_id} 未在变量表中登记，Ren'Py 草稿仍会按同名变量写出。", variableId=variable_id)
    if effect_type == "variable_add":
        return [f"{indent}$ {variable_name} += {value}"]
    if effect_type == "variable_set":
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
        character_id = clean_text(block.get("characterId"), "character")
        expression_id = clean_text(block.get("expressionId"))
        position = clean_text(block.get("position"), "center")
        expression = f" {normalize_identifier(expression_id, 'expr')}" if expression_id else ""
        return [f"    show {normalize_identifier(character_id, 'character')}{expression} at {position} with dissolve"]
    if block_type == "character_hide":
        return [f"    hide {normalize_identifier(block.get('characterId'), 'character')} with dissolve"]
    if block_type == "music_play":
        fade_in = seconds_from_ms(block.get("fadeInMs"))
        fade_suffix = f" fadein {fade_in:g}" if fade_in else ""
        return [f"    play music {quote_renpy(get_asset_path(asset_map, block.get('assetId')) or 'audio/bgm.ogg')}{fade_suffix}"]
    if block_type == "music_stop":
        fade_out = seconds_from_ms(block.get("fadeOutMs"))
        return [f"    stop music{f' fadeout {fade_out:g}' if fade_out else ''}"]
    if block_type == "sfx_play":
        return [f"    play sound {quote_renpy(get_asset_path(asset_map, block.get('assetId')) or 'audio/sfx.ogg')}"]
    if block_type in {"dialogue", "narration"}:
        line = clean_text(block.get("text") or (block.get("fields") or {}).get("text"), " ")
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

    lines = [
        f"# {clean_text(project.get('title'), 'Canvasia Project')} - Canvasia Ren'Py Starter",
        "# Generated for migration and collaboration. Review custom effects before release.",
        "",
        *build_variable_definitions(variable_map),
        "",
        *build_asset_image_definitions(asset_map),
        *sprite_definitions,
        "",
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
            "",
            "## How to continue",
            "",
            "1. Create or open a Ren'Py project.",
            f"2. Copy the `{RENPY_GAME_DIR_NAME}` folder contents into the Ren'Py project's `game` folder.",
            f"3. Open `{RENPY_REVIEW_FILE_NAME}` and replace review comments with native Ren'Py transforms, screens, or Python logic where needed.",
            "4. Run the project in Ren'Py and resolve label, asset, or transform issues reported by the launcher.",
            "",
            f"Review items generated: {export_result.get('warningCount', 0)}",
            "",
        ]
    )


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
    }
