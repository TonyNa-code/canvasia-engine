from __future__ import annotations

import csv
import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path


EXPORT_PRESENTATION_TIMELINE_JSON_NAME = "presentation-timeline.json"
EXPORT_PRESENTATION_TIMELINE_REPORT_NAME = "presentation-timeline-report.md"
EXPORT_PRESENTATION_TIMELINE_CSV_NAME = "presentation-timeline-table.csv"
PRESENTATION_TIMELINE_FORMAT_VERSION = 1

BLOCK_LABELS = {
    "background": "背景",
    "dialogue": "台词",
    "narration": "旁白",
    "character_show": "角色登场",
    "character_hide": "角色退场",
    "music_play": "播放 BGM",
    "music_stop": "停止 BGM",
    "sfx_play": "音效",
    "video_play": "视频",
    "credits_roll": "片尾字幕",
    "wait": "等待停顿",
    "particle_effect": "粒子",
    "screen_shake": "震动",
    "screen_flash": "闪屏",
    "screen_fade": "淡入淡出",
    "camera_zoom": "镜头缩放",
    "camera_pan": "镜头平移",
    "screen_filter": "滤镜",
    "depth_blur": "景深",
    "choice": "选项",
    "condition": "条件",
    "jump": "跳转",
}
TEXT_SPEED_CHARS_PER_SECOND = {"slow": 12, "normal": 18, "fast": 28, "instant": 80}
STORY_TEXT_TYPES = {"dialogue", "narration", "choice"}
VISUAL_BEAT_TYPES = {
    "background",
    "character_show",
    "character_hide",
    "particle_effect",
    "wait",
    "screen_shake",
    "screen_flash",
    "screen_fade",
    "camera_zoom",
    "camera_pan",
    "screen_filter",
    "depth_blur",
    "video_play",
    "credits_roll",
}
AUDIO_BEAT_TYPES = {"music_play", "music_stop", "sfx_play", "video_play"}
TIMELINE_TYPES = {*STORY_TEXT_TYPES, *VISUAL_BEAT_TYPES, *AUDIO_BEAT_TYPES, "condition", "jump"}
ISSUE_WEIGHT = {"blocker": 100, "warn": 60, "tip": 20}


def clean_text(value: object, fallback: str = "") -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text or fallback


def as_list(value: object) -> list:
    return value if isinstance(value, list) else []


def as_float(value: object, fallback: float = 0.0) -> float:
    if isinstance(value, bool):
        return fallback
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def as_int(value: object, fallback: int = 0) -> int:
    if isinstance(value, bool):
        return fallback
    return int(as_float(value, fallback))


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


def asset_file_exists(asset: dict | None) -> bool:
    if not isinstance(asset, dict):
        return False
    return not (asset.get("isMissing") is True or asset.get("fileExists") is False)


def get_asset_status(asset_id: object, assets_by_id: dict[str, dict]) -> dict:
    safe_id = clean_text(asset_id)
    if not safe_id:
        return {"label": "未选择素材", "ready": False, "name": ""}
    asset = assets_by_id.get(safe_id)
    if not asset:
        return {"label": "素材不存在", "ready": False, "name": safe_id}
    if not asset_file_exists(asset):
        return {"label": "文件缺失", "ready": False, "name": get_asset_name(asset, safe_id)}
    return {"label": "素材可用", "ready": True, "name": get_asset_name(asset, safe_id)}


def get_character_name(characters_by_id: dict[str, dict], character_id: object) -> str:
    safe_id = clean_text(character_id)
    character = characters_by_id.get(safe_id)
    if isinstance(character, dict):
        return clean_text(character.get("displayName") or character.get("name"), safe_id or "未选择角色")
    return safe_id or "未选择角色"


def get_block_text(block: dict) -> str:
    block_type = clean_text(block.get("type"))
    if block_type == "choice":
        return " / ".join(clean_text(option.get("text")) for option in as_list(block.get("options")) if isinstance(option, dict) and clean_text(option.get("text")))
    if block_type == "credits_roll":
        return " / ".join(clean_text(line) for line in as_list(block.get("lines")) if clean_text(line))
    return clean_text(block.get("text") or block.get("title") or block.get("name") or block.get("assetId") or block.get("characterId") or block.get("speakerId"))


def get_block_id(block: dict, index: int) -> str:
    return clean_text(block.get("id"), f"block_{index + 1}")


def get_block_label(block: dict, index: int) -> str:
    block_type = clean_text(block.get("type"), "block")
    text = get_block_text(block)
    prefix = f"第 {index + 1} 张 · {BLOCK_LABELS.get(block_type, block_type)}"
    return f"{prefix} · {text[:32]}" if text else prefix


def estimate_text_duration_ms(block: dict) -> int:
    text = get_block_text(block)
    if not text:
        return 0
    chars = len(text)
    speed = clean_text(block.get("textSpeed"), "normal")
    chars_per_second = TEXT_SPEED_CHARS_PER_SECOND.get(speed, TEXT_SPEED_CHARS_PER_SECOND["normal"])
    punctuation_pause_ms = len(re.findall(r"[，。！？、,.!?]", text)) * 90
    base_ms = chars / chars_per_second * 1000 + punctuation_pause_ms
    return clamp_int(round(base_ms), 650, 22000, 1200)


def get_transition_duration_ms(block: dict) -> int:
    return clamp_int(block.get("transitionDurationMs"), 0, 8000, 600)


def get_effect_duration_ms(block: dict) -> int:
    duration = clean_text(block.get("duration"), "medium")
    if duration == "short":
        return 420
    if duration == "long":
        return 1400
    return 820


def get_event_duration_ms(block: dict) -> int:
    block_type = clean_text(block.get("type"))
    if block_type in STORY_TEXT_TYPES:
        return estimate_text_duration_ms(block)
    if block_type in {"background", "character_show", "character_hide"}:
        return get_transition_duration_ms(block)
    if block_type in {"screen_shake", "screen_flash", "screen_fade", "camera_zoom", "camera_pan", "screen_filter", "depth_blur"}:
        return get_effect_duration_ms(block)
    if block_type == "credits_roll":
        return clamp_int(round(as_float(block.get("durationSeconds"), 18) * 1000), 4000, 180000, 18000)
    if block_type == "wait":
        return clamp_int(round(as_float(block.get("durationSeconds"), 1) * 1000), 100, 30000, 1000)
    if block_type == "video_play":
        return clamp_int(round(as_float(block.get("durationSeconds"), 12) * 1000), 1000, 600000, 12000)
    return 0


def format_duration(ms: object) -> str:
    safe_ms = max(0, as_int(ms, 0))
    if safe_ms < 1000:
        return "不到 1 秒"
    seconds = round(safe_ms / 1000)
    if seconds < 60:
        return f"{seconds} 秒"
    minutes = seconds // 60
    rest = seconds % 60
    return f"{minutes} 分 {rest} 秒" if rest else f"{minutes} 分"


def push_issue(issues: list[dict], severity: str, code: str, title: str, detail: str, context: dict) -> None:
    issues.append({"severity": severity, "code": code, "title": title, "detail": detail, **context})


def get_status_from_issues(issues: list[dict]) -> str:
    if any(issue["severity"] == "blocker" for issue in issues):
        return "blocker"
    if any(issue["severity"] == "warn" for issue in issues):
        return "warn"
    if issues:
        return "tip"
    return "good"


def get_status_label(status: str) -> str:
    if status == "blocker":
        return "先修"
    if status == "warn":
        return "复查"
    if status == "tip":
        return "润色"
    return "正常"


def inspect_block(block: dict, context: dict) -> dict:
    issues: list[dict] = []
    base_context = {
        "chapterName": context["chapterName"],
        "sceneName": context["sceneName"],
        "sceneId": context["sceneId"],
        "blockId": get_block_id(block, context["blockIndex"]),
        "blockIndex": context["blockIndex"],
        "blockLabel": get_block_label(block, context["blockIndex"]),
    }
    block_type = clean_text(block.get("type"), "unknown")
    type_label = BLOCK_LABELS.get(block_type, block_type)
    duration_ms = get_event_duration_ms(block)
    detail = get_block_text(block)
    assets_by_id = context["assetsById"]

    if block_type == "background":
        asset = get_asset_status(block.get("assetId"), assets_by_id)
        detail = asset["name"] or asset["label"]
        if not clean_text(block.get("assetId")):
            push_issue(issues, "blocker", "background_missing_asset", "背景卡未选择素材", "这张背景卡没有绑定背景素材。", base_context)
        elif not asset["ready"]:
            push_issue(issues, "blocker", "background_asset_not_ready", "背景素材不可用", asset["label"], base_context)
        if clean_text(block.get("transition"), "fade") == "none":
            push_issue(issues, "tip", "background_hard_cut", "背景是硬切", "如果不是故意制造突兀感，建议给背景切换加淡入淡出。", base_context)

    if block_type == "music_play":
        asset = get_asset_status(block.get("assetId"), assets_by_id)
        detail = asset["name"] or asset["label"]
        fade_in_ms = clamp_int(block.get("fadeInMs"), 0, 30000, 0)
        if not clean_text(block.get("assetId")):
            push_issue(issues, "blocker", "music_missing_asset", "BGM 卡未选择素材", "这张播放音乐卡没有绑定 BGM。", base_context)
        elif not asset["ready"]:
            push_issue(issues, "blocker", "music_asset_not_ready", "BGM 素材不可用", asset["label"], base_context)
        if fade_in_ms < 250:
            push_issue(issues, "warn" if context.get("musicActive") else "tip", "music_hard_start", "BGM 进入过快", "建议设置 500-1500ms 淡入，让音乐更自然接入文本。", base_context)

    if block_type == "music_stop":
        fade_out_ms = clamp_int(block.get("fadeOutMs"), 0, 30000, 0)
        detail = f"{fade_out_ms}ms 淡出"
        if fade_out_ms < 250:
            push_issue(issues, "tip", "music_hard_stop", "BGM 停止过硬", "建议给停止音乐卡设置淡出，避免像播放器突然切断。", base_context)

    if block_type == "sfx_play":
        asset = get_asset_status(block.get("assetId"), assets_by_id)
        detail = asset["name"] or asset["label"]
        if not clean_text(block.get("assetId")):
            push_issue(issues, "blocker", "sfx_missing_asset", "音效卡未选择素材", "这张音效卡没有绑定音效素材。", base_context)
        elif not asset["ready"]:
            push_issue(issues, "blocker", "sfx_asset_not_ready", "音效素材不可用", asset["label"], base_context)

    if block_type == "video_play":
        asset = get_asset_status(block.get("assetId"), assets_by_id)
        detail = asset["name"] or clean_text(block.get("title"), asset["label"])
        if not clean_text(block.get("assetId")) and not clean_text(block.get("title")):
            push_issue(issues, "warn", "video_missing_identity", "视频卡缺少素材或标题", "OP / ED 视频建议至少绑定素材或写清标题，便于导出前复核。", base_context)
        elif clean_text(block.get("assetId")) and not asset["ready"]:
            push_issue(issues, "blocker", "video_asset_not_ready", "视频素材不可用", asset["label"], base_context)

    if block_type == "character_show":
        detail = get_character_name(context["charactersById"], block.get("characterId"))
        stage = block.get("stage") if isinstance(block.get("stage"), dict) else block.get("characterStage") if isinstance(block.get("characterStage"), dict) else {}
        scale = clamp_int(stage.get("scale"), 45, 220, 100)
        opacity = clamp_int(stage.get("opacity"), 0, 100, 100)
        if not clean_text(block.get("characterId")):
            push_issue(issues, "blocker", "character_show_missing_character", "角色登场卡未选择角色", "这张卡没有绑定角色。", base_context)
        if clean_text(block.get("transition"), "fade") == "none":
            push_issue(issues, "tip", "character_show_hard_cut", "角色登场是硬切", "建议用淡入、滑入或弹出，让立绘出现更像正式演出。", base_context)
        if scale <= 55 or scale >= 185:
            push_issue(issues, "tip", "character_scale_extreme", "立绘缩放较极端", f"当前缩放约 {scale}%，建议确认构图没有遮挡文本框或出画。", base_context)
        if opacity < 45:
            push_issue(issues, "warn", "character_opacity_too_low", "立绘透明度过低", f"当前透明度约 {opacity}%，玩家可能看不清角色。", base_context)

    if block_type == "character_hide":
        detail = get_character_name(context["charactersById"], block.get("characterId"))
        if not clean_text(block.get("characterId")):
            push_issue(issues, "blocker", "character_hide_missing_character", "角色退场卡未选择角色", "这张卡没有绑定要隐藏的角色。", base_context)
        if clean_text(block.get("transition"), "fade") == "none":
            push_issue(issues, "tip", "character_hide_hard_cut", "角色退场是硬切", "如果不是故意制造突兀感，建议给退场加淡出或滑出。", base_context)

    if block_type in {"dialogue", "narration"} and not clean_text(block.get("text")):
        push_issue(issues, "warn", "empty_text_block", "正文卡没有文本", "这张台词/旁白卡是空的，发布前建议补正文或删除。", base_context)
    if block_type == "choice" and not as_list(block.get("options")):
        push_issue(issues, "blocker", "choice_without_options", "选项卡没有选项", "玩家走到这里会没有可点内容。", base_context)
    if block_type == "credits_roll" and not any(clean_text(line) for line in as_list(block.get("lines"))):
        push_issue(issues, "warn", "credits_without_lines", "片尾字幕为空", "片尾卡已经存在，但还没有演职人员文本。", base_context)
    if block_type == "wait" and clamp_int(round(as_float(block.get("durationSeconds"), 1)), 0, 30, 1) >= 8:
        push_issue(issues, "warn", "long_wait_block", "等待停顿偏长", "超过 8 秒的停顿可能会让玩家误以为卡住，建议只在强演出时使用。", base_context)

    status = get_status_from_issues(issues)
    return {
        **base_context,
        "type": block_type,
        "typeLabel": type_label,
        "detail": detail,
        "durationMs": duration_ms,
        "durationLabel": format_duration(duration_ms),
        "status": status,
        "statusLabel": get_status_label(status),
        "issues": issues,
    }


def inspect_scene(scene_record: dict, assets_by_id: dict[str, dict], characters_by_id: dict[str, dict]) -> dict:
    scene = scene_record["scene"]
    blocks = [block for block in as_list(scene.get("blocks")) if isinstance(block, dict)]
    events: list[dict] = []
    issues: list[dict] = []
    has_story_content = False
    has_visual_beat = False
    has_audio_beat = False
    has_background = False
    first_story_content_index = -1
    first_background_index = -1
    last_visual_beat_index = -1
    text_run_count = 0
    static_text_warned = False
    music_active = False

    for block_index, block in enumerate(blocks):
        block_type = clean_text(block.get("type"))
        if block_type not in TIMELINE_TYPES:
            continue
        event = inspect_block(
            block,
            {
                "chapterName": scene_record["chapterName"],
                "sceneName": scene_record["sceneName"],
                "sceneId": scene_record["sceneId"],
                "blockIndex": block_index,
                "assetsById": assets_by_id,
                "charactersById": characters_by_id,
                "musicActive": music_active,
            },
        )
        events.append(event)
        issues.extend(event["issues"])

        if block_type in STORY_TEXT_TYPES:
            has_story_content = True
            text_run_count += 1
            if first_story_content_index < 0:
                first_story_content_index = block_index
            if not static_text_warned and text_run_count >= 7 and block_index - last_visual_beat_index >= 7:
                push_issue(
                    issues,
                    "warn",
                    "long_static_text_run",
                    "长对白段缺少演出变化",
                    "连续多张正文/选项之间没有背景、立绘、镜头、滤镜或粒子变化，建议补一个表情、镜头或环境变化。",
                    {
                        "chapterName": scene_record["chapterName"],
                        "sceneName": scene_record["sceneName"],
                        "sceneId": scene_record["sceneId"],
                        "blockId": get_block_id(block, block_index),
                        "blockIndex": block_index,
                        "blockLabel": get_block_label(block, block_index),
                    },
                )
                static_text_warned = True
        elif block_type in VISUAL_BEAT_TYPES:
            has_visual_beat = True
            last_visual_beat_index = block_index
            text_run_count = 0

        if block_type == "background":
            has_background = True
            if first_background_index < 0:
                first_background_index = block_index
        if block_type in AUDIO_BEAT_TYPES:
            has_audio_beat = True
        if block_type == "music_play":
            music_active = True
        if block_type == "music_stop":
            music_active = False

    scene_context = {
        "chapterName": scene_record["chapterName"],
        "sceneName": scene_record["sceneName"],
        "sceneId": scene_record["sceneId"],
        "blockId": "",
        "blockIndex": -1,
        "blockLabel": scene_record["sceneName"],
    }
    if has_story_content and (not has_background or (first_background_index >= 0 and 0 <= first_story_content_index < first_background_index)):
        push_issue(issues, "warn", "scene_opening_without_background", "场景开头缺少明确背景", "建议让内容出现前先切背景，避免玩家不知道当前地点。", scene_context)
    if has_story_content and not has_audio_beat:
        push_issue(issues, "tip", "scene_without_audio_anchor", "内容场景没有音频锚点", "不一定必须有 BGM，但发布前建议确认这一段是故意留白，而不是忘了配乐或音效。", scene_context)
    if has_story_content and not has_visual_beat:
        push_issue(issues, "warn", "scene_without_visual_anchor", "内容场景缺少视觉锚点", "整场只有文本或逻辑卡，建议至少补背景、立绘或一个镜头变化。", scene_context)

    estimated_duration_ms = sum(max(0, as_int(event.get("durationMs"), 0)) for event in events)
    status = get_status_from_issues(issues)
    return {
        "sceneId": scene_record["sceneId"],
        "sceneName": scene_record["sceneName"],
        "chapterId": scene_record["chapterId"],
        "chapterName": scene_record["chapterName"],
        "eventCount": len(events),
        "estimatedDurationMs": estimated_duration_ms,
        "estimatedDurationLabel": format_duration(estimated_duration_ms),
        "hasStoryContent": has_story_content,
        "hasVisualBeat": has_visual_beat,
        "hasAudioBeat": has_audio_beat,
        "status": status,
        "statusLabel": get_status_label(status),
        "issues": issues,
        "events": events,
    }


def build_presentation_timeline(bundle: dict, assets_doc: dict) -> dict:
    assets_by_id = get_assets_by_id(assets_doc)
    characters_by_id = get_characters_by_id(bundle)
    scene_reports = [
        inspect_scene(scene_record, assets_by_id, characters_by_id)
        for scene_record in get_ordered_scene_records(bundle)
    ]
    events = [event for scene in scene_reports for event in scene["events"]]
    issues = [issue for scene in scene_reports for issue in scene["issues"]]
    issues.sort(key=lambda issue: (-ISSUE_WEIGHT.get(issue["severity"], 0), issue.get("chapterName", ""), issue.get("sceneName", ""), issue.get("blockIndex", 0)))
    estimated_duration_ms = sum(scene["estimatedDurationMs"] for scene in scene_reports)
    blocker_count = sum(1 for issue in issues if issue["severity"] == "blocker")
    warning_count = sum(1 for issue in issues if issue["severity"] == "warn")
    tip_count = sum(1 for issue in issues if issue["severity"] == "tip")
    readiness_penalty = min(100, blocker_count * 18 + warning_count * 7 + tip_count * 2)
    summary = {
        "sceneCount": len(scene_reports),
        "eventCount": len(events),
        "storySceneCount": sum(1 for scene in scene_reports if scene["hasStoryContent"]),
        "estimatedDurationMs": estimated_duration_ms,
        "estimatedDurationLabel": format_duration(estimated_duration_ms),
        "longStaticTextRunCount": sum(1 for issue in issues if issue["code"] == "long_static_text_run"),
        "abruptAudioCount": sum(1 for issue in issues if issue["code"] in {"music_hard_start", "music_hard_stop"}),
        "missingVisualAnchorCount": sum(1 for issue in issues if issue["code"] == "scene_without_visual_anchor"),
        "missingAudioAnchorCount": sum(1 for issue in issues if issue["code"] == "scene_without_audio_anchor"),
        "blockerCount": blocker_count,
        "warningCount": warning_count,
        "tipCount": tip_count,
        "releaseReadinessPercent": max(0, 100 - readiness_penalty),
    }
    timeline = {
        "formatVersion": PRESENTATION_TIMELINE_FORMAT_VERSION,
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "projectTitle": get_project_title(bundle),
        "sceneReports": scene_reports,
        "events": events,
        "issues": issues,
        "summary": summary,
    }
    timeline["statusDigest"] = get_presentation_timeline_status_digest(timeline)
    return timeline


def get_presentation_timeline_status_digest(timeline: dict) -> dict:
    summary = timeline.get("summary") or {}
    if summary.get("eventCount", 0) == 0:
        return {"status": "empty", "title": "还没有可分析的演出时间轴", "detail": "项目里暂时没有正文、背景、角色、音乐、视频或演出卡。"}
    if summary.get("blockerCount", 0) > 0:
        return {"status": "blocked", "title": f"有 {summary.get('blockerCount', 0)} 个演出阻塞问题", "detail": "优先修复缺素材、空选项、空角色或不可用媒体，再做节奏润色。"}
    if summary.get("warningCount", 0) > 0:
        return {"status": "warn", "title": f"有 {summary.get('warningCount', 0)} 个演出节奏提醒", "detail": "项目可以继续推进，但建议复查开场背景、长静态对白、硬切音乐和视觉锚点。"}
    if summary.get("tipCount", 0) > 0:
        return {"status": "polish", "title": "演出时间轴可继续润色", "detail": "基础阻塞较少，可以继续打磨音乐、等待和镜头节奏。"}
    return {"status": "ready", "title": "演出时间轴看起来比较稳", "detail": "当前正文、视觉和音频锚点没有明显发布前结构问题。"}


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


def build_presentation_timeline_report(timeline: dict) -> str:
    summary = timeline.get("summary") or {}
    digest = timeline.get("statusDigest") or get_presentation_timeline_status_digest(timeline)
    scene_rows = [
        [index + 1, scene.get("chapterName"), scene.get("sceneName"), scene.get("eventCount"), scene.get("estimatedDurationLabel"), scene.get("statusLabel")]
        for index, scene in enumerate((timeline.get("sceneReports") or [])[:120])
    ]
    event_rows = [
        [index + 1, event.get("chapterName"), event.get("sceneName"), int(event.get("blockIndex") or 0) + 1, event.get("typeLabel"), event.get("detail"), event.get("durationLabel"), event.get("statusLabel")]
        for index, event in enumerate((timeline.get("events") or [])[:160])
    ]
    issue_rows = [
        [
            index + 1,
            "阻塞" if issue.get("severity") == "blocker" else "提醒" if issue.get("severity") == "warn" else "润色",
            issue.get("chapterName"),
            issue.get("sceneName"),
            issue.get("title"),
            issue.get("detail"),
        ]
        for index, issue in enumerate((timeline.get("issues") or [])[:140])
    ]
    return "\ufeff" + "\n".join(
        [
            f"# {timeline.get('projectTitle') or 'Canvasia Project'} 演出时间轴",
            "",
            f"导出时间：{timeline.get('generatedAt')}",
            f"状态：{digest.get('title')}",
            f"说明：{digest.get('detail')}",
            "",
            "## 总览",
            "",
            markdown_table(
                ["项目", "数量"],
                [
                    ["场景", summary.get("sceneCount", 0)],
                    ["内容场景", summary.get("storySceneCount", 0)],
                    ["演出事件", summary.get("eventCount", 0)],
                    ["预计阅读/演出时长", summary.get("estimatedDurationLabel", "0 秒")],
                    ["阻塞问题", summary.get("blockerCount", 0)],
                    ["复查提醒", summary.get("warningCount", 0)],
                    ["润色建议", summary.get("tipCount", 0)],
                    ["就绪度", f"{summary.get('releaseReadinessPercent', 0)}%"],
                ],
            ),
            "",
            "## 场景节奏",
            "",
            markdown_table(["序号", "章节", "场景", "事件", "预计时长", "状态"], scene_rows) or "当前没有可列出的场景。",
            "",
            "## 演出事件",
            "",
            markdown_table(["序号", "章节", "场景", "卡片", "类型", "内容", "预计时长", "状态"], event_rows) or "当前没有可列出的演出事件。",
            "",
            "## 需要复查的问题",
            "",
            markdown_table(["序号", "级别", "章节", "场景", "问题", "说明"], issue_rows) or "当前没有明显演出节奏问题。",
            "",
        ]
    )


def build_presentation_timeline_csv(timeline: dict) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["序号", "章节", "场景", "卡片", "类型", "内容", "预计毫秒", "预计时长", "状态", "问题"])
    for index, event in enumerate(timeline.get("events") or []):
        writer.writerow(
            [
                index + 1,
                event.get("chapterName"),
                event.get("sceneName"),
                int(event.get("blockIndex") or 0) + 1,
                event.get("typeLabel"),
                event.get("detail"),
                event.get("durationMs"),
                event.get("durationLabel"),
                event.get("statusLabel"),
                " / ".join(issue.get("title", "") for issue in event.get("issues") or [] if issue.get("title")),
            ]
        )
    return "\ufeff" + output.getvalue()


def write_export_presentation_timeline_files(target_dir: Path, *, bundle: dict, assets_doc: dict) -> dict:
    timeline = build_presentation_timeline(bundle, assets_doc)
    json_path = target_dir / EXPORT_PRESENTATION_TIMELINE_JSON_NAME
    report_path = target_dir / EXPORT_PRESENTATION_TIMELINE_REPORT_NAME
    csv_path = target_dir / EXPORT_PRESENTATION_TIMELINE_CSV_NAME
    json_path.write_text(json.dumps(timeline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(build_presentation_timeline_report(timeline), encoding="utf-8")
    csv_path.write_text(build_presentation_timeline_csv(timeline), encoding="utf-8")
    summary = timeline["summary"]
    return {
        "presentationTimeline": timeline,
        "presentationTimelineName": json_path.name,
        "presentationTimelinePath": str(json_path),
        "presentationTimelineReportName": report_path.name,
        "presentationTimelineReportPath": str(report_path),
        "presentationTimelineCsvName": csv_path.name,
        "presentationTimelineCsvPath": str(csv_path),
        "presentationTimelineReadinessPercent": summary["releaseReadinessPercent"],
        "presentationTimelineEventCount": summary["eventCount"],
        "presentationTimelineBlockerCount": summary["blockerCount"],
        "presentationTimelineWarningCount": summary["warningCount"],
    }


__all__ = [
    "EXPORT_PRESENTATION_TIMELINE_JSON_NAME",
    "EXPORT_PRESENTATION_TIMELINE_REPORT_NAME",
    "EXPORT_PRESENTATION_TIMELINE_CSV_NAME",
    "build_presentation_timeline",
    "build_presentation_timeline_report",
    "build_presentation_timeline_csv",
    "write_export_presentation_timeline_files",
]
