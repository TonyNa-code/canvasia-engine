from __future__ import annotations

import csv
import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path


EXPORT_STAGE_DIRECTION_JSON_NAME = "stage-direction-sheet.json"
EXPORT_STAGE_DIRECTION_REPORT_NAME = "stage-direction-report.md"
EXPORT_STAGE_DIRECTION_CSV_NAME = "stage-direction-table.csv"
STAGE_DIRECTION_FORMAT_VERSION = 1

POSITION_LABELS = {
    "left": "左侧",
    "center": "中间",
    "right": "右侧",
}
BLOCK_LABELS = {
    "background": "背景",
    "dialogue": "台词",
    "narration": "旁白",
    "character_show": "角色登场",
    "character_move": "角色动作",
    "character_hide": "角色退场",
    "music_play": "播放 BGM",
    "music_stop": "停止 BGM",
    "sfx_play": "音效",
    "video_play": "视频",
    "credits_roll": "片尾字幕",
    "wait": "等待停顿",
    "choice": "选项",
    "jump": "跳转",
    "condition": "条件",
}
VALID_POSITIONS = {"left", "center", "right"}
VALID_CHARACTER_TRANSITIONS = {"fade", "slide_left", "slide_right", "rise", "pop", "none"}
STORY_CONTENT_BLOCK_TYPES = {"background", "dialogue", "narration", "character_show", "character_move", "choice", "video_play", "credits_roll", "wait"}
ISSUE_WEIGHT = {"blocker": 100, "warn": 60, "tip": 20}
STAGE_POSITION_X = {"left": -36, "center": 0, "right": 36}


def clean_text(value: object, fallback: str = "") -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text or fallback


def as_list(value: object) -> list:
    return value if isinstance(value, list) else []


def as_int(value: object, fallback: int = 0) -> int:
    if isinstance(value, bool):
        return fallback
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return fallback


def clamp_int(value: object, minimum: int, maximum: int, fallback: int) -> int:
    return max(minimum, min(maximum, as_int(value, fallback)))


def get_project_title(bundle: dict) -> str:
    project = bundle.get("project") if isinstance(bundle.get("project"), dict) else {}
    return clean_text(project.get("title"), "Canvasia Project")


def get_chapter_id(chapter: dict) -> str:
    return clean_text(chapter.get("chapterId") or chapter.get("id"))


def get_scene_id(scene: dict) -> str:
    return clean_text(scene.get("id") or scene.get("sceneId"))


def get_ordered_scene_records(bundle: dict) -> list[dict]:
    chapters = [chapter for chapter in as_list(bundle.get("chapters")) if isinstance(chapter, dict)]
    project = bundle.get("project") if isinstance(bundle.get("project"), dict) else {}
    chapter_order = [clean_text(item) for item in as_list(project.get("chapterOrder")) if clean_text(item)]
    chapter_map = {get_chapter_id(chapter): chapter for chapter in chapters if get_chapter_id(chapter)}
    ordered_chapters = [chapter_map[chapter_id] for chapter_id in chapter_order if chapter_id in chapter_map]
    ordered_chapters.extend(chapter for chapter in chapters if get_chapter_id(chapter) not in chapter_order)

    records: list[dict] = []
    seen_scene_ids: set[str] = set()
    for chapter_index, chapter in enumerate(ordered_chapters):
        chapter_id = get_chapter_id(chapter)
        chapter_name = clean_text(chapter.get("name") or chapter.get("title"), f"章节 {chapter_index + 1}")
        scenes = [scene for scene in as_list(chapter.get("scenes")) if isinstance(scene, dict)]
        scene_order = [clean_text(item) for item in as_list(chapter.get("sceneOrder")) if clean_text(item)]
        scene_map = {get_scene_id(scene): scene for scene in scenes if get_scene_id(scene)}
        ordered_scenes = [scene_map[scene_id] for scene_id in scene_order if scene_id in scene_map]
        ordered_scenes.extend(scene for scene in scenes if get_scene_id(scene) not in scene_order)
        for scene_index, scene in enumerate(ordered_scenes):
            scene_id = get_scene_id(scene) or f"{chapter_id or 'chapter'}_scene_{scene_index + 1}"
            if scene_id in seen_scene_ids:
                continue
            seen_scene_ids.add(scene_id)
            records.append(
                {
                    "scene": scene,
                    "sceneId": scene_id,
                    "sceneName": clean_text(scene.get("name") or scene.get("title"), f"场景 {scene_index + 1}"),
                    "sceneIndex": scene_index,
                    "chapterId": chapter_id,
                    "chapterName": chapter_name,
                    "chapterIndex": chapter_index,
                }
            )

    for scene_index, scene in enumerate(as_list(bundle.get("scenes"))):
        if not isinstance(scene, dict):
            continue
        scene_id = get_scene_id(scene) or f"loose_scene_{scene_index + 1}"
        if scene_id in seen_scene_ids:
            continue
        seen_scene_ids.add(scene_id)
        records.append(
            {
                "scene": scene,
                "sceneId": scene_id,
                "sceneName": clean_text(scene.get("name") or scene.get("title"), f"场景 {scene_index + 1}"),
                "sceneIndex": scene_index,
                "chapterId": clean_text(scene.get("chapterId")),
                "chapterName": "未分章",
                "chapterIndex": 9999,
            }
        )
    return sorted(records, key=lambda item: (item["chapterIndex"], item["sceneIndex"], item["sceneName"]))


def get_assets_by_id(assets_doc: dict) -> dict[str, dict]:
    assets = assets_doc.get("assets") if isinstance(assets_doc, dict) else []
    return {
        clean_text(asset.get("id")): asset
        for asset in as_list(assets)
        if isinstance(asset, dict) and clean_text(asset.get("id"))
    }


def get_characters_by_id(bundle: dict) -> dict[str, dict]:
    characters_doc = bundle.get("characters") if isinstance(bundle.get("characters"), dict) else {}
    characters = characters_doc.get("characters") if isinstance(characters_doc, dict) else []
    return {
        clean_text(character.get("id")): character
        for character in as_list(characters)
        if isinstance(character, dict) and clean_text(character.get("id"))
    }


def get_asset_name(asset: dict | None, fallback: str = "") -> str:
    if not isinstance(asset, dict):
        return fallback
    return clean_text(asset.get("name") or asset.get("fileName") or asset.get("path"), fallback)


def get_asset_path(asset: dict | None) -> str:
    if not isinstance(asset, dict):
        return ""
    return clean_text(asset.get("exportUrl") or asset.get("path") or asset.get("url"))


def asset_file_exists(asset: dict | None) -> bool:
    if not isinstance(asset, dict):
        return False
    return not (asset.get("isMissing") is True or asset.get("fileExists") is False)


def get_character_name(character: dict | None, fallback: str = "") -> str:
    if not isinstance(character, dict):
        return fallback or "未选择角色"
    return clean_text(character.get("displayName") or character.get("name"), fallback or "未命名角色")


def get_expression(character: dict | None, expression_id: object) -> dict | None:
    if not isinstance(character, dict):
        return None
    target = clean_text(expression_id)
    for expression in as_list(character.get("expressions")):
        if isinstance(expression, dict) and clean_text(expression.get("id")) == target:
            return expression
    return None


def get_expression_name(character: dict | None, expression_id: object) -> str:
    expression = get_expression(character, expression_id)
    return clean_text((expression or {}).get("name"), clean_text(expression_id, "默认表情"))


def get_presentation_mode(character: dict | None) -> str:
    presentation = character.get("presentation") if isinstance(character, dict) and isinstance(character.get("presentation"), dict) else {}
    mode = clean_text(presentation.get("mode"), "sprite")
    return mode if mode in {"sprite", "layered_sprite", "live2d", "model3d"} else "sprite"


def collect_character_visual_asset_ids(character: dict | None, expression_id: object) -> list[str]:
    if not isinstance(character, dict):
        return []
    expression = get_expression(character, expression_id) or {}
    presentation = character.get("presentation") if isinstance(character.get("presentation"), dict) else {}
    mode = get_presentation_mode(character)
    asset_ids: list[str] = []
    if mode == "live2d":
        live2d = presentation.get("live2d") if isinstance(presentation.get("live2d"), dict) else {}
        asset_ids.append(clean_text(live2d.get("modelAssetId")))
    elif mode == "model3d":
        model3d = presentation.get("model3d") if isinstance(presentation.get("model3d"), dict) else {}
        asset_ids.append(clean_text(model3d.get("modelAssetId")))
    asset_ids.append(clean_text(expression.get("spriteAssetId")))
    asset_ids.extend(clean_text(asset_id) for asset_id in as_list(expression.get("layerAssetIds")))
    asset_ids.append(clean_text(presentation.get("fallbackSpriteAssetId")))
    asset_ids.append(clean_text(character.get("defaultSpriteId")))
    seen: set[str] = set()
    result: list[str] = []
    for asset_id in asset_ids:
        if asset_id and asset_id not in seen:
            seen.add(asset_id)
            result.append(asset_id)
    return result


def get_character_visual_status(character: dict | None, expression_id: object, assets_by_id: dict[str, dict]) -> dict:
    asset_ids = collect_character_visual_asset_ids(character, expression_id)
    if not asset_ids:
        return {"status": "missing", "label": "没有可用立绘", "assetNames": [], "assetIds": []}
    known_assets = [assets_by_id[asset_id] for asset_id in asset_ids if asset_id in assets_by_id]
    if not known_assets:
        return {"status": "unknown", "label": "立绘素材不存在", "assetNames": asset_ids, "assetIds": asset_ids}
    missing_assets = [asset for asset in known_assets if not asset_file_exists(asset)]
    return {
        "status": "file_missing" if missing_assets else "ready",
        "label": "立绘文件缺失" if missing_assets else "立绘可用",
        "assetNames": [get_asset_name(asset, clean_text(asset.get("id"))) for asset in known_assets],
        "assetIds": [clean_text(asset.get("id")) for asset in known_assets],
    }


def get_position_value(value: object, fallback: str = "center") -> str:
    position = clean_text(value)
    return position if position in VALID_POSITIONS else fallback


def get_position_label(value: object) -> str:
    position = get_position_value(value)
    return POSITION_LABELS.get(position, clean_text(value, "未设置"))


def get_stage(block: dict) -> dict:
    stage = block.get("stage") if isinstance(block.get("stage"), dict) else {}
    return {
        "offsetX": clamp_int(stage.get("offsetX"), -100, 100, 0),
        "offsetY": clamp_int(stage.get("offsetY"), -100, 100, 0),
        "scale": clamp_int(stage.get("scale"), 45, 220, 100),
        "opacity": clamp_int(stage.get("opacity"), 0, 100, 100),
        "layer": clamp_int(stage.get("layer"), -10, 10, 0),
        "flipX": bool(stage.get("flipX", False)),
    }


def get_stage_composition_x(item: dict) -> float:
    stage = item.get("stage") if isinstance(item.get("stage"), dict) else {}
    return STAGE_POSITION_X.get(clean_text(item.get("position"), "center"), 0) + float(stage.get("offsetX", 0) or 0) * 0.45


def get_stage_composition_radius(item: dict) -> float:
    stage = item.get("stage") if isinstance(item.get("stage"), dict) else {}
    return max(12.0, float(stage.get("scale", 100) or 100) * 0.18)


def build_stage_composition_snapshot(visible_characters: dict[str, dict], context: dict) -> dict:
    characters = []
    for item in visible_characters.values():
        stage = item.get("stage") if isinstance(item.get("stage"), dict) else get_stage({})
        position = clean_text(item.get("position"), "center")
        characters.append(
            {
                "characterId": clean_text(item.get("characterId")),
                "characterName": clean_text(item.get("characterName")),
                "expressionName": clean_text(item.get("expressionName")),
                "position": position,
                "positionLabel": get_position_label(position),
                "stage": stage,
                "centerX": round(get_stage_composition_x(item)),
                "radius": round(get_stage_composition_radius(item)),
            }
        )
    return {
        "chapterName": context.get("chapterName"),
        "sceneName": context.get("sceneName"),
        "sceneId": context.get("sceneId"),
        "blockId": context.get("blockId"),
        "blockIndex": context.get("blockIndex"),
        "blockLabel": context.get("blockLabel"),
        "visibleCount": len(characters),
        "characters": characters,
        "characterNames": " / ".join(character["characterName"] for character in characters if character.get("characterName")),
    }


def find_stage_overlap_pairs(characters: list[dict]) -> list[str]:
    pairs: list[str] = []
    for left_index, left in enumerate(characters):
        for right in characters[left_index + 1 :]:
            distance = abs(float(left.get("centerX", 0)) - float(right.get("centerX", 0)))
            overlap_threshold = min(34.0, (float(left.get("radius", 0)) + float(right.get("radius", 0))) * 0.72)
            if distance < overlap_threshold:
                pairs.append(f"{left.get('characterName') or left.get('characterId')} / {right.get('characterName') or right.get('characterId')}")
    return pairs


def inspect_stage_composition(visible_characters: dict[str, dict], issues: list[dict], context: dict, *, speaker_id: str = "") -> dict:
    issue_start_index = len(issues)
    snapshot = build_stage_composition_snapshot(visible_characters, context)
    risks: list[str] = []
    position_counts: dict[str, int] = {}
    layer_counts: dict[int, int] = {}
    for item in snapshot["characters"]:
        position_counts[item["position"]] = position_counts.get(item["position"], 0) + 1
        layer = int((item.get("stage") or {}).get("layer", 0) or 0)
        layer_counts[layer] = layer_counts.get(layer, 0) + 1
    if any(count > 1 for count in position_counts.values()):
        push_issue(issues, "tip", "stage_position_overlap", "角色站位可能重叠", "当前舞台有多个角色使用同一站位，建议确认画面是否拥挤。", context)
        risks.append("同站位")
    overlap_pairs = find_stage_overlap_pairs(snapshot["characters"])
    if overlap_pairs:
        push_issue(issues, "warn", "stage_geometry_overlap", "立绘可能互相遮挡", f"请复查：{'、'.join(overlap_pairs)} 的站位、偏移或缩放。", context)
        risks.append("遮挡")
    if any(count > 1 for count in layer_counts.values()) and snapshot["visibleCount"] > 1:
        push_issue(issues, "tip", "stage_layer_overlap", "角色图层可能冲突", "同屏多个角色使用相同图层，复杂遮挡时建议显式区分图层。", context)
        risks.append("图层")
    if snapshot["visibleCount"] > 3:
        push_issue(issues, "tip", "stage_too_many_characters", "同屏角色较多", "视觉小说常规画面建议控制在 1-3 人，更多角色建议拆镜头或缩放。", context)
        risks.append("拥挤")
    if snapshot["visibleCount"] > 1 and any((item.get("stage") or {}).get("scale", 100) >= 155 for item in snapshot["characters"]):
        push_issue(issues, "tip", "stage_large_sprite_crowding", "大比例立绘可能压迫画面", "同屏多人时，超过 155% 的立绘建议配合偏移、图层或拆镜头使用。", context)
        risks.append("大比例")
    speaker = next((item for item in snapshot["characters"] if clean_text(item.get("characterId")) == clean_text(speaker_id)), None) if clean_text(speaker_id) else None
    if speaker and (speaker.get("stage") or {}).get("opacity", 100) < 35:
        push_issue(issues, "warn", "stage_speaker_low_opacity", "说话人透明度过低", "当前说话人的透明度低于 35%，玩家可能看不清是谁在说话。", context)
        risks.append("说话人过淡")
    composition_issues = issues[issue_start_index:]
    if any(issue["severity"] == "blocker" for issue in composition_issues):
        status = "blocker"
    elif any(issue["severity"] == "warn" for issue in composition_issues):
        status = "warn"
    elif risks:
        status = "tip"
    else:
        status = "good"
    return {**snapshot, "status": status, "risks": risks, "issues": composition_issues, "riskLabel": " / ".join(risks) if risks else "构图正常"}


def get_block_id(block: dict, index: int) -> str:
    return clean_text(block.get("id"), f"block_{index + 1}")


def get_block_label(block: dict, index: int) -> str:
    block_type = clean_text(block.get("type"), "block")
    prefix = f"第 {index + 1} 张 · {BLOCK_LABELS.get(block_type, block_type)}"
    text = clean_text(block.get("text") or block.get("title") or block.get("name") or block.get("assetId"))
    if not text and isinstance(block.get("options"), list):
        text = " / ".join(clean_text(option.get("text")) for option in block["options"] if isinstance(option, dict) and clean_text(option.get("text")))
    return f"{prefix} · {text[:32]}" if text else prefix


def is_story_content_block(block: dict) -> bool:
    return clean_text(block.get("type")) in STORY_CONTENT_BLOCK_TYPES


def push_issue(issues: list[dict], severity: str, code: str, title: str, detail: str, context: dict) -> None:
    issues.append({"severity": severity, "code": code, "title": title, "detail": detail, **context})


def event_status(issues: list[dict]) -> str:
    if any(issue["severity"] == "blocker" for issue in issues):
        return "blocker"
    if any(issue["severity"] == "warn" for issue in issues):
        return "warn"
    if issues:
        return "tip"
    return "good"


def inspect_visual_status(issues: list[dict], visual: dict, context: dict) -> None:
    if visual["status"] == "missing":
        push_issue(issues, "blocker", "character_visual_missing", "角色没有可用立绘", "角色没有默认立绘、表情立绘、差分图层或高级模型兜底。", context)
    elif visual["status"] == "unknown":
        push_issue(issues, "blocker", "character_visual_unknown_asset", "角色立绘素材不存在", f"当前引用：{' / '.join(visual['assetNames'])}", context)
    elif visual["status"] == "file_missing":
        push_issue(issues, "blocker", "character_visual_file_missing", "角色立绘文件缺失", f"请补齐：{' / '.join(visual['assetNames'])}", context)


def inspect_stage_params(block: dict, issues: list[dict], context: dict, *, is_hide: bool = False) -> dict:
    transition = clean_text(block.get("transition"))
    duration_ms = as_int(block.get("transitionDurationMs"), -1)
    if transition and transition not in VALID_CHARACTER_TRANSITIONS:
        push_issue(issues, "warn", "character_transition_unknown", "角色转场类型无法识别", "建议使用 fade、slide_left、slide_right、rise、pop 或 none。", context)
    if not transition:
        push_issue(issues, "tip", "character_transition_missing", "角色转场未设置", "建议至少设置 fade 或 rise，让立绘入退场不显得生硬。", context)
    if duration_ms < 0:
        push_issue(issues, "tip", "character_transition_duration_missing", "角色转场时长未设置", "建议登场 500-700ms、退场 350-500ms。", context)
    elif duration_ms > 5000:
        push_issue(issues, "warn", "character_transition_too_long", "角色转场时间过长", "超过 5 秒的立绘转场通常会影响阅读节奏。", context)
    stage = get_stage(block)
    if not is_hide:
        raw_stage = block.get("stage") if isinstance(block.get("stage"), dict) else {}
        if not raw_stage:
            push_issue(issues, "tip", "character_stage_defaults_only", "角色舞台参数仍是默认值", "可以按角色关系和镜头氛围微调位置、缩放、透明度或图层。", context)
        if clean_text(block.get("position")) and clean_text(block.get("position")) not in VALID_POSITIONS:
            push_issue(issues, "warn", "character_position_unknown", "角色站位无法识别", "建议使用 left、center 或 right，避免导出 Runtime 回退位置。", context)
        if stage["opacity"] <= 5:
            push_issue(issues, "warn", "character_opacity_invisible", "角色几乎不可见", "透明度接近 0，试玩时可能以为立绘没有出现。", context)
        if stage["scale"] <= 55 or stage["scale"] >= 190:
            push_issue(issues, "tip", "character_scale_extreme", "角色缩放较极端", "请确认这是不是特写、远景或特殊演出。", context)
    return stage


def make_event(event_type: str, event_type_label: str, context: dict, issues: list[dict], **fields: object) -> dict:
    return {
        **context,
        "type": event_type,
        "typeLabel": event_type_label,
        "status": event_status(issues),
        "issues": issues,
        **fields,
    }


def inspect_scene_stage(scene_record: dict, assets_by_id: dict[str, dict], characters_by_id: dict[str, dict]) -> dict:
    scene = scene_record["scene"]
    blocks = [block for block in as_list(scene.get("blocks")) if isinstance(block, dict)]
    events: list[dict] = []
    composition_rows: list[dict] = []
    scene_issues: list[dict] = []
    visible_characters: dict[str, dict] = {}
    has_background = False
    has_story_content = False
    content_before_background = False

    for block_index, block in enumerate(blocks):
        block_type = clean_text(block.get("type"))
        base_context = {
            "chapterName": scene_record["chapterName"],
            "sceneName": scene_record["sceneName"],
            "sceneId": scene_record["sceneId"],
            "blockId": get_block_id(block, block_index),
            "blockIndex": block_index,
            "blockLabel": get_block_label(block, block_index),
        }
        if is_story_content_block(block) and block_type != "background":
            has_story_content = True
            content_before_background = content_before_background or not has_background

        if block_type == "background":
            issues: list[dict] = []
            asset_id = clean_text(block.get("assetId"))
            asset = assets_by_id.get(asset_id)
            if not asset_id:
                push_issue(issues, "blocker", "background_missing_asset", "背景卡未选择素材", "这张背景卡没有绑定背景素材。", base_context)
            elif not asset:
                push_issue(issues, "blocker", "background_unknown_asset", "背景素材不存在", f"素材 {asset_id} 不在当前素材库中。", base_context)
            elif not asset_file_exists(asset):
                push_issue(issues, "blocker", "background_file_missing", "背景文件缺失", "素材条目存在，但真实背景文件暂时不可用。", base_context)
            has_background = True
            scene_issues.extend(issues)
            events.append(
                make_event(
                    "background",
                    "背景",
                    base_context,
                    issues,
                    characterName="",
                    expressionName="",
                    position="",
                    positionLabel="",
                    stage={},
                    transition="",
                    transitionDurationMs="",
                    assetStatusLabel=get_asset_name(asset, asset_id or "未选择背景"),
                    assetIds=[asset_id] if asset_id else [],
                )
            )
            continue

        if block_type == "character_show":
            issues = []
            character_id = clean_text(block.get("characterId"))
            character = characters_by_id.get(character_id)
            if not character_id:
                push_issue(issues, "blocker", "character_show_missing_character", "登场卡未选择角色", "这张角色登场卡没有绑定角色。", base_context)
            elif not character:
                push_issue(issues, "blocker", "character_show_unknown_character", "登场角色不存在", f"角色 {character_id} 不在当前角色表中。", base_context)
            if character and clean_text(block.get("expressionId")) and not get_expression(character, block.get("expressionId")):
                push_issue(issues, "blocker", "character_expression_missing", "角色表情不存在", f"表情 {block.get('expressionId')} 不在角色表情列表中。", base_context)
            visual = get_character_visual_status(character, block.get("expressionId"), assets_by_id)
            if character:
                inspect_visual_status(issues, visual, base_context)
            stage = inspect_stage_params(block, issues, base_context)
            position = get_position_value(block.get("position"), clean_text((character or {}).get("defaultPosition"), "center"))
            if character_id:
                visible_characters[character_id] = {
                    "characterId": character_id,
                    "position": position,
                    "stage": stage,
                    "characterName": get_character_name(character, character_id),
                    "expressionId": clean_text(block.get("expressionId")),
                    "expressionName": get_expression_name(character, block.get("expressionId")),
                }
            composition = inspect_stage_composition(visible_characters, issues, base_context)
            composition_rows.append(composition)
            scene_issues.extend(issues)
            events.append(
                make_event(
                    "character_show",
                    "登场",
                    base_context,
                    issues,
                    characterName=get_character_name(character, character_id),
                    expressionName=get_expression_name(character, block.get("expressionId")),
                    position=position,
                    positionLabel=get_position_label(position),
                    stage=stage,
                    composition=composition,
                    transition=clean_text(block.get("transition")),
                    transitionDurationMs=as_int(block.get("transitionDurationMs"), 0),
                    assetStatusLabel=f"{visual['label']}：{' / '.join(visual['assetNames'])}".rstrip("："),
                    assetIds=visual["assetIds"],
                )
            )
            continue

        if block_type == "character_move":
            issues = []
            character_id = clean_text(block.get("characterId"))
            character = characters_by_id.get(character_id)
            previous_visible = visible_characters.get(character_id)
            if not character_id:
                push_issue(issues, "blocker", "character_move_missing_character", "角色动作卡未选择角色", "这张角色动作卡没有绑定角色。", base_context)
            elif not character:
                push_issue(issues, "blocker", "character_move_unknown_character", "动作角色不存在", f"角色 {character_id} 不在当前角色表中。", base_context)
            elif not previous_visible:
                push_issue(issues, "warn", "character_move_not_visible", "动作角色尚未登场", "Runtime 会从角色默认状态补位，但正式演出建议先放一张角色登场卡。", base_context)
            expression_id = clean_text(block.get("expressionId") or (previous_visible or {}).get("expressionId"))
            if character and expression_id and not get_expression(character, expression_id):
                push_issue(issues, "blocker", "character_move_expression_missing", "动作表情不存在", f"表情 {expression_id} 不在角色表情列表中。", base_context)
            visual = get_character_visual_status(character, expression_id, assets_by_id)
            if character:
                inspect_visual_status(issues, visual, base_context)
            stage = get_stage(block) if isinstance(block.get("stage"), dict) else get_stage({"stage": (previous_visible or {}).get("stage") or {}})
            position = get_position_value(
                block.get("position"),
                clean_text((previous_visible or {}).get("position") or (character or {}).get("defaultPosition"), "center"),
            )
            if clean_text(block.get("position")) and clean_text(block.get("position")) not in VALID_POSITIONS:
                push_issue(issues, "warn", "character_move_position_unknown", "角色动作站位无法识别", "建议使用 left、center 或 right，避免 Runtime 回退位置。", base_context)
            duration_ms = clamp_int(block.get("durationMs"), 0, 10000, 600)
            easing = clean_text(block.get("easing"), "ease_out")
            if character_id:
                visible_characters[character_id] = {
                    "characterId": character_id,
                    "position": position,
                    "stage": stage,
                    "characterName": get_character_name(character, character_id),
                    "expressionId": expression_id,
                    "expressionName": get_expression_name(character, expression_id),
                }
            composition = inspect_stage_composition(visible_characters, issues, base_context)
            composition_rows.append(composition)
            scene_issues.extend(issues)
            events.append(
                make_event(
                    "character_move",
                    "动作",
                    base_context,
                    issues,
                    characterName=get_character_name(character, character_id),
                    expressionName=get_expression_name(character, expression_id),
                    position=position,
                    positionLabel=get_position_label(position),
                    stage=stage,
                    composition=composition,
                    motionDurationMs=duration_ms,
                    motionEasing=easing,
                    transition="",
                    transitionDurationMs="",
                    assetStatusLabel=f"{visual['label']}：{' / '.join(visual['assetNames'])}".rstrip("："),
                    assetIds=visual["assetIds"],
                )
            )
            continue

        if block_type == "character_hide":
            issues = []
            character_id = clean_text(block.get("characterId"))
            character = characters_by_id.get(character_id)
            if not character_id:
                push_issue(issues, "blocker", "character_hide_missing_character", "退场卡未选择角色", "这张角色退场卡没有绑定角色。", base_context)
            elif not character:
                push_issue(issues, "blocker", "character_hide_unknown_character", "退场角色不存在", f"角色 {character_id} 不在当前角色表中。", base_context)
            elif character_id not in visible_characters:
                push_issue(issues, "tip", "character_hide_not_visible", "退场角色当前不在舞台", "这通常说明前面缺少登场卡或顺序需要复查。", base_context)
            inspect_stage_params(block, issues, base_context, is_hide=True)
            visible_characters.pop(character_id, None)
            scene_issues.extend(issues)
            events.append(
                make_event(
                    "character_hide",
                    "退场",
                    base_context,
                    issues,
                    characterName=get_character_name(character, character_id),
                    expressionName="",
                    position="",
                    positionLabel="",
                    stage={},
                    transition=clean_text(block.get("transition")),
                    transitionDurationMs=as_int(block.get("transitionDurationMs"), 0),
                    assetStatusLabel="",
                    assetIds=[],
                )
            )
            continue

        if block_type == "dialogue":
            issues = []
            character_id = clean_text(block.get("speakerId"))
            character = characters_by_id.get(character_id)
            if not character_id:
                push_issue(issues, "blocker", "dialogue_missing_speaker", "台词卡未选择说话人", "这句台词没有绑定角色。", base_context)
            elif not character:
                push_issue(issues, "blocker", "dialogue_unknown_speaker", "说话角色不存在", f"角色 {character_id} 不在当前角色表中。", base_context)
            elif character_id not in visible_characters:
                push_issue(issues, "warn", "dialogue_speaker_not_visible", "说话人未提前登场", "正式演出建议先放一张角色登场卡来控制站位和转场。", base_context)
            if character and clean_text(block.get("expressionId")) and not get_expression(character, block.get("expressionId")):
                push_issue(issues, "blocker", "dialogue_expression_missing", "台词表情不存在", f"表情 {block.get('expressionId')} 不在角色表情列表中。", base_context)
            visual = get_character_visual_status(character, block.get("expressionId"), assets_by_id)
            if character:
                inspect_visual_status(issues, visual, base_context)
            if character_id and character:
                previous_visible = visible_characters.get(character_id)
                visible_characters[character_id] = {
                    "characterId": character_id,
                    "position": previous_visible.get("position") if previous_visible else get_position_value(character.get("defaultPosition"), "center"),
                    "stage": previous_visible.get("stage") if previous_visible else get_stage({}),
                    "characterName": get_character_name(character, character_id),
                    "expressionId": clean_text(block.get("expressionId") or (previous_visible or {}).get("expressionId")),
                    "expressionName": get_expression_name(character, block.get("expressionId")),
                }
            composition = inspect_stage_composition(visible_characters, issues, base_context, speaker_id=character_id)
            composition_rows.append(composition)
            scene_issues.extend(issues)
            visible = visible_characters.get(character_id, {})
            events.append(
                make_event(
                    "dialogue",
                    "说话",
                    base_context,
                    issues,
                    characterName=get_character_name(character, character_id),
                    expressionName=get_expression_name(character, block.get("expressionId")),
                    position=visible.get("position", clean_text((character or {}).get("defaultPosition"), "center")),
                    positionLabel=get_position_label(visible.get("position", clean_text((character or {}).get("defaultPosition"), "center"))),
                    stage=visible.get("stage") or {},
                    composition=composition,
                    transition="",
                    transitionDurationMs="",
                    assetStatusLabel=f"{visual['label']}：{' / '.join(visual['assetNames'])}".rstrip("："),
                    assetIds=visual["assetIds"],
                    text=clean_text(block.get("text")),
                )
            )

    if has_story_content and not any(clean_text(block.get("type")) == "background" and clean_text(block.get("assetId")) for block in blocks):
        push_issue(
            scene_issues,
            "warn",
            "scene_without_background",
            "内容场景没有背景卡",
            "这个场景有正文或角色演出，但没有明确切背景。",
            {
                "chapterName": scene_record["chapterName"],
                "sceneName": scene_record["sceneName"],
                "sceneId": scene_record["sceneId"],
                "blockId": "",
                "blockIndex": -1,
                "blockLabel": scene_record["sceneName"],
            },
        )
    elif has_story_content and content_before_background:
        push_issue(
            scene_issues,
            "tip",
            "scene_content_before_background",
            "内容出现在背景之前",
            "场景开头先出现正文/角色，再切背景；建议确认这是不是有意为之。",
            {
                "chapterName": scene_record["chapterName"],
                "sceneName": scene_record["sceneName"],
                "sceneId": scene_record["sceneId"],
                "blockId": "",
                "blockIndex": -1,
                "blockLabel": scene_record["sceneName"],
            },
        )

    return {
        "sceneId": scene_record["sceneId"],
        "sceneName": scene_record["sceneName"],
        "chapterId": scene_record["chapterId"],
        "chapterName": scene_record["chapterName"],
        "eventCount": len(events),
        "visibleCharacterCountAtEnd": len(visible_characters),
        "hasStoryContent": has_story_content,
        "hasBackground": has_background,
        "issues": scene_issues,
        "events": events,
        "compositionRows": composition_rows,
        "status": event_status(scene_issues),
    }


def build_stage_direction_sheet(bundle: dict, assets_doc: dict) -> dict:
    assets_by_id = get_assets_by_id(assets_doc)
    characters_by_id = get_characters_by_id(bundle)
    scene_reports = [
        inspect_scene_stage(scene_record, assets_by_id, characters_by_id)
        for scene_record in get_ordered_scene_records(bundle)
    ]
    events = [event for scene in scene_reports for event in scene["events"]]
    composition_rows = [row for scene in scene_reports for row in scene.get("compositionRows", [])]
    issues = [issue for scene in scene_reports for issue in scene["issues"]]
    issues.sort(key=lambda issue: (-ISSUE_WEIGHT.get(issue["severity"], 0), issue.get("chapterName", ""), issue.get("sceneName", ""), issue.get("blockIndex", 0)))
    blocker_count = sum(1 for issue in issues if issue["severity"] == "blocker")
    warning_count = sum(1 for issue in issues if issue["severity"] == "warn")
    tip_count = sum(1 for issue in issues if issue["severity"] == "tip")
    readiness_penalty = min(100, blocker_count * 18 + warning_count * 8 + tip_count * 2)
    summary = {
        "sceneCount": len(scene_reports),
        "eventCount": len(events),
        "stagedSceneCount": sum(1 for scene in scene_reports if scene["eventCount"] > 0),
        "characterShowCount": sum(1 for event in events if event["type"] == "character_show"),
        "characterMoveCount": sum(1 for event in events if event["type"] == "character_move"),
        "characterHideCount": sum(1 for event in events if event["type"] == "character_hide"),
        "dialogueEventCount": sum(1 for event in events if event["type"] == "dialogue"),
        "missingBackgroundSceneCount": sum(1 for scene in scene_reports if any(issue["code"] == "scene_without_background" for issue in scene["issues"])),
        "speakerAutoPlaceCount": sum(1 for issue in issues if issue["code"] == "dialogue_speaker_not_visible"),
        "missingVisualCount": sum(1 for issue in issues if "visual" in issue["code"] or "expression" in issue["code"]),
        "transitionGapCount": sum(1 for issue in issues if issue["code"] in {"character_transition_missing", "character_transition_duration_missing"}),
        "compositionCheckpointCount": len(composition_rows),
        "compositionRiskCount": sum(1 for row in composition_rows if row.get("status") != "good"),
        "overlapRiskCount": sum(1 for issue in issues if issue["code"] in {"stage_geometry_overlap", "stage_position_overlap"}),
        "crowdedStageCount": sum(1 for issue in issues if issue["code"] in {"stage_too_many_characters", "stage_large_sprite_crowding"}),
        "lowOpacitySpeakerCount": sum(1 for issue in issues if issue["code"] == "stage_speaker_low_opacity"),
        "layerConflictCount": sum(1 for issue in issues if issue["code"] == "stage_layer_overlap"),
        "blockerCount": blocker_count,
        "warningCount": warning_count,
        "tipCount": tip_count,
        "releaseReadinessPercent": max(0, 100 - readiness_penalty),
    }
    sheet = {
        "formatVersion": STAGE_DIRECTION_FORMAT_VERSION,
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "projectTitle": get_project_title(bundle),
        "summary": summary,
        "sceneReports": scene_reports,
        "events": events,
        "compositionRows": composition_rows,
        "issues": issues,
    }
    sheet["statusDigest"] = get_stage_direction_status_digest(sheet)
    return sheet


def get_stage_direction_status_digest(sheet: dict) -> dict:
    summary = sheet.get("summary") or {}
    if not summary.get("eventCount"):
        return {"status": "empty", "title": "还没有角色舞台 Cue", "detail": "添加背景、角色登场、退场或台词后，这里会生成舞台调度表。"}
    if summary.get("blockerCount", 0) > 0:
        return {"status": "blocked", "title": f"{summary.get('blockerCount', 0)} 个舞台阻塞项", "detail": "优先处理缺角色、缺立绘、缺背景、错误表情和缺失真实文件。"}
    if summary.get("warningCount", 0) > 0:
        return {"status": "warn", "title": f"{summary.get('releaseReadinessPercent', 0)}% 舞台调度就绪", "detail": "可以试玩，但建议补齐说话人登场、背景和明显的舞台参数问题。"}
    if summary.get("tipCount", 0) > 0:
        return {"status": "polish", "title": "舞台调度可继续润色", "detail": "基础播放风险较低，可以继续调整站位、转场和镜头节奏。"}
    return {"status": "ready", "title": "角色舞台调度稳定", "detail": "背景、立绘、登退场和说话人状态比较完整。"}


def markdown_cell(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", "<br />").strip()


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    if not rows:
        return ""
    return "\n".join(
        [
            f"| {' | '.join(markdown_cell(header) for header in headers)} |",
            f"| {' | '.join('---' for _ in headers)} |",
            *(f"| {' | '.join(markdown_cell(cell) for cell in row)} |" for row in rows),
        ]
    )


def build_stage_direction_report(sheet: dict) -> str:
    summary = sheet.get("summary") or {}
    digest = sheet.get("statusDigest") or get_stage_direction_status_digest(sheet)
    scene_rows = [
        [scene.get("status"), scene.get("chapterName"), scene.get("sceneName"), scene.get("eventCount"), scene.get("visibleCharacterCountAtEnd"), len(scene.get("issues") or [])]
        for scene in (sheet.get("sceneReports") or [])[:120]
    ]
    event_rows = [
        [
            event.get("status"),
            event.get("chapterName"),
            event.get("sceneName"),
            event.get("typeLabel"),
            event.get("characterName"),
            event.get("expressionName"),
            event.get("positionLabel"),
            format_stage(event.get("stage") or {}),
            (event.get("composition") or {}).get("riskLabel", ""),
            event.get("transition"),
            event.get("transitionDurationMs"),
            event.get("assetStatusLabel"),
            event.get("blockLabel"),
        ]
        for event in (sheet.get("events") or [])[:160]
    ]
    composition_rows = [
        [
            "先修" if row.get("status") == "blocker" else "复查" if row.get("status") == "warn" else "润色",
            row.get("chapterName"),
            row.get("sceneName"),
            row.get("blockLabel"),
            row.get("visibleCount"),
            row.get("characterNames"),
            row.get("riskLabel"),
        ]
        for row in (sheet.get("compositionRows") or [])
        if row.get("status") != "good"
    ][:120]
    issue_rows = [
        [
            "先修" if issue.get("severity") == "blocker" else "复查" if issue.get("severity") == "warn" else "润色",
            issue.get("chapterName"),
            issue.get("sceneName"),
            issue.get("title"),
            issue.get("detail"),
        ]
        for issue in (sheet.get("issues") or [])[:120]
    ]
    return "\n".join(
        [
            f"# {sheet.get('projectTitle') or 'Canvasia Project'} 角色舞台调度表",
            "",
            f"- 生成时间：{sheet.get('generatedAt')}",
            f"- 状态：{digest.get('title')}",
            f"- 说明：{digest.get('detail')}",
            "",
            "## 总览",
            "",
            markdown_table(
                ["场景", "舞台事件", "登场", "动作", "退场", "说话", "缺背景场景", "未登场说话", "立绘缺口", "构图风险", "遮挡", "说话过淡", "转场缺口", "阻塞", "复查", "就绪度"],
                [
                    [
                        summary.get("sceneCount", 0),
                        summary.get("eventCount", 0),
                        summary.get("characterShowCount", 0),
                        summary.get("characterMoveCount", 0),
                        summary.get("characterHideCount", 0),
                        summary.get("dialogueEventCount", 0),
                        summary.get("missingBackgroundSceneCount", 0),
                        summary.get("speakerAutoPlaceCount", 0),
                        summary.get("missingVisualCount", 0),
                        summary.get("compositionRiskCount", 0),
                        summary.get("overlapRiskCount", 0),
                        summary.get("lowOpacitySpeakerCount", 0),
                        summary.get("transitionGapCount", 0),
                        summary.get("blockerCount", 0),
                        summary.get("warningCount", 0),
                        f"{summary.get('releaseReadinessPercent', 0)}%",
                    ]
                ],
            ),
            "",
            "## 场景舞台概览",
            "",
            markdown_table(["状态", "章节", "场景", "事件", "结尾留在舞台", "问题数"], scene_rows) or "当前没有可统计场景。",
            "",
            "## 舞台 Cue 列表",
            "",
            markdown_table(["状态", "章节", "场景", "类型", "角色", "表情", "站位", "舞台参数", "构图", "转场", "时长", "素材状态", "卡片"], event_rows)
            or "当前没有角色舞台 Cue。",
            "",
            "## 舞台构图检查",
            "",
            markdown_table(["级别", "章节", "场景", "检查点", "同屏人数", "角色", "风险"], composition_rows)
            or "当前没有明显站位、遮挡、图层或透明度构图风险。",
            "",
            "## 优先问题",
            "",
            markdown_table(["级别", "章节", "场景", "问题", "说明"], issue_rows) or "当前没有明显角色舞台问题。",
            "",
        ]
    )


def format_stage(stage: dict) -> str:
    if not stage:
        return ""
    return f"x{stage.get('offsetX', 0)} y{stage.get('offsetY', 0)} / {stage.get('scale', 100)}% / opacity {stage.get('opacity', 100)} / layer {stage.get('layer', 0)}"


def build_stage_direction_csv(sheet: dict) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "status",
            "type",
            "chapter",
            "scene",
            "blockIndex",
            "character",
            "expression",
            "position",
            "offsetX",
            "offsetY",
            "scale",
            "opacity",
            "layer",
            "transition",
            "transitionDurationMs",
            "assetStatus",
            "visibleCount",
            "compositionRisk",
            "blockLabel",
            "issues",
        ]
    )
    issue_map: dict[str, list[str]] = {}
    for issue in sheet.get("issues") or []:
        key = f"{issue.get('sceneId')}:{issue.get('blockId')}"
        issue_map.setdefault(key, []).append(issue.get("title", ""))
    for event in sheet.get("events") or []:
        stage = event.get("stage") or {}
        key = f"{event.get('sceneId')}:{event.get('blockId')}"
        writer.writerow(
            [
                event.get("status"),
                event.get("type"),
                event.get("chapterName"),
                event.get("sceneName"),
                int(event.get("blockIndex") or 0) + 1,
                event.get("characterName"),
                event.get("expressionName"),
                event.get("positionLabel"),
                stage.get("offsetX", ""),
                stage.get("offsetY", ""),
                stage.get("scale", ""),
                stage.get("opacity", ""),
                stage.get("layer", ""),
                event.get("transition", ""),
                event.get("transitionDurationMs", ""),
                event.get("assetStatusLabel", ""),
                (event.get("composition") or {}).get("visibleCount", ""),
                (event.get("composition") or {}).get("riskLabel", ""),
                event.get("blockLabel", ""),
                " / ".join(issue for issue in issue_map.get(key, []) if issue),
            ]
        )
    return "\ufeff" + output.getvalue()


def write_export_stage_direction_files(target_dir: Path, *, bundle: dict, assets_doc: dict) -> dict:
    sheet = build_stage_direction_sheet(bundle, assets_doc)
    json_path = target_dir / EXPORT_STAGE_DIRECTION_JSON_NAME
    report_path = target_dir / EXPORT_STAGE_DIRECTION_REPORT_NAME
    csv_path = target_dir / EXPORT_STAGE_DIRECTION_CSV_NAME
    json_path.write_text(json.dumps(sheet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(build_stage_direction_report(sheet), encoding="utf-8")
    csv_path.write_text(build_stage_direction_csv(sheet), encoding="utf-8")
    summary = sheet["summary"]
    return {
        "stageDirectionSheet": sheet,
        "stageDirectionName": json_path.name,
        "stageDirectionPath": str(json_path),
        "stageDirectionReportName": report_path.name,
        "stageDirectionReportPath": str(report_path),
        "stageDirectionCsvName": csv_path.name,
        "stageDirectionCsvPath": str(csv_path),
        "stageDirectionReadinessPercent": summary["releaseReadinessPercent"],
        "stageDirectionEventCount": summary["eventCount"],
        "stageDirectionBlockerCount": summary["blockerCount"],
        "stageDirectionWarningCount": summary["warningCount"],
    }


__all__ = [
    "EXPORT_STAGE_DIRECTION_JSON_NAME",
    "EXPORT_STAGE_DIRECTION_REPORT_NAME",
    "EXPORT_STAGE_DIRECTION_CSV_NAME",
    "build_stage_direction_sheet",
    "build_stage_direction_report",
    "build_stage_direction_csv",
    "write_export_stage_direction_files",
]
