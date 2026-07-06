from __future__ import annotations

import csv
import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path


EXPORT_AUDIO_CUE_SHEET_JSON_NAME = "audio-cue-sheet.json"
EXPORT_AUDIO_CUE_SHEET_REPORT_NAME = "audio-cue-report.md"
EXPORT_AUDIO_CUE_SHEET_CSV_NAME = "audio-cue-table.csv"
AUDIO_CUE_SHEET_FORMAT_VERSION = 1

MUSIC_END_MODE_LABELS = {
    "until_next_music": "直到下一首或停止卡",
    "scene_end": "覆盖到场景结束",
    "after_block": "播放到指定卡片",
}
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
    "choice": "选项",
    "jump": "跳转",
    "condition": "条件",
}
STORY_CONTENT_BLOCK_TYPES = {"background", "dialogue", "narration", "character_show", "choice", "video_play", "credits_roll", "wait"}
ISSUE_WEIGHT = {"blocker": 100, "warn": 60, "tip": 20}


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


def get_character_name(characters_by_id: dict[str, dict], speaker_id: object) -> str:
    clean_id = clean_text(speaker_id)
    if not clean_id:
        return "旁白"
    character = characters_by_id.get(clean_id)
    if isinstance(character, dict):
        return clean_text(character.get("displayName") or character.get("name"), clean_id)
    return clean_id


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


def get_block_id(block: dict, index: int) -> str:
    return clean_text(block.get("id"), f"block_{index + 1}")


def get_block_label(block: dict, index: int) -> str:
    block_type = clean_text(block.get("type"), "block")
    prefix = f"第 {index + 1} 张 · {BLOCK_LABELS.get(block_type, block_type)}"
    text = clean_text(block.get("text"))
    if text:
        return f"{prefix} · {text[:32]}"
    return prefix


def get_safe_music_end_mode(value: object) -> str:
    text = clean_text(value)
    return text if text in MUSIC_END_MODE_LABELS else "until_next_music"


def is_story_content_block(block: dict) -> bool:
    return clean_text(block.get("type")) in STORY_CONTENT_BLOCK_TYPES


def get_recommended_audio_range_end_block_id(blocks: list[dict], start_index: int) -> str:
    next_audio_index = next(
        (index for index, block in enumerate(blocks) if index > start_index and clean_text(block.get("type")) in {"music_play", "music_stop"}),
        -1,
    )
    last_candidate_index = next_audio_index - 1 if next_audio_index >= 0 else len(blocks) - 1
    for index in range(last_candidate_index, start_index - 1, -1):
        if is_story_content_block(blocks[index]):
            return get_block_id(blocks[index], index)
    for index in range(last_candidate_index, start_index - 1, -1):
        block_id = get_block_id(blocks[index], index)
        if block_id:
            return block_id
    return ""


def estimate_range_timing(blocks: list[dict], start_index: int, end_index: int) -> dict:
    safe_start = max(0, min(len(blocks) - 1, start_index)) if blocks else 0
    safe_end = max(safe_start, min(len(blocks) - 1, end_index)) if blocks else 0
    readable_characters = 0
    text_block_count = 0
    wait_seconds = 0.0
    media_block_count = 0
    for block in blocks[safe_start : safe_end + 1]:
        block_type = clean_text(block.get("type"))
        if block_type in {"dialogue", "narration"}:
            readable_characters += len(clean_text(block.get("text")))
            text_block_count += 1
        elif block_type == "wait":
            wait_seconds += max(0, as_int(block.get("durationMs") or block.get("duration"), 800)) / 1000
        elif block_type in {"background", "character_show", "character_hide", "video_play", "screen_fade"}:
            media_block_count += 1
    estimated_seconds = max(1, round(readable_characters / 7 + text_block_count * 0.45 + wait_seconds + media_block_count * 0.6))
    tone = "silent"
    if readable_characters > 0:
        tone = "short" if estimated_seconds < 12 else "long" if estimated_seconds >= 90 else "normal"
    return {
        "startIndex": safe_start,
        "endIndex": safe_end,
        "blockCount": safe_end - safe_start + 1 if blocks else 0,
        "estimatedSeconds": estimated_seconds if blocks else 0,
        "durationLabel": format_duration(estimated_seconds if blocks else 0),
        "readableCharacterCount": readable_characters,
        "waitSeconds": round(wait_seconds, 2),
        "textBlockCount": text_block_count,
        "mediaBlockCount": media_block_count,
        "tone": tone,
    }


def format_duration(seconds: object) -> str:
    value = max(0, as_int(seconds, 0))
    if value < 60:
        return f"约 {value} 秒"
    minutes = value // 60
    remaining = value % 60
    return f"约 {minutes}分{remaining}秒" if remaining else f"约 {minutes} 分钟"


def build_timing_hint(timing: dict) -> str:
    return f"{timing.get('durationLabel', '约 0 秒')}，约 {timing.get('readableCharacterCount', 0)} 字 / {timing.get('textBlockCount', 0)} 段正文。"


def push_issue(issues: list[dict], severity: str, code: str, title: str, detail: str, context: dict) -> None:
    issues.append({"severity": severity, "code": code, "title": title, "detail": detail, **context})


def build_audio_cue_sheet(bundle: dict, assets_doc: dict) -> dict:
    assets_by_id = get_assets_by_id(assets_doc)
    characters_by_id = get_characters_by_id(bundle)
    music_cues: list[dict] = []
    sfx_cues: list[dict] = []
    voice_cues: list[dict] = []
    range_suggestions: list[dict] = []
    issues: list[dict] = []
    scenes_without_music: list[dict] = []

    for scene_record in get_ordered_scene_records(bundle):
        scene = scene_record["scene"]
        blocks = [block for block in as_list(scene.get("blocks")) if isinstance(block, dict)]
        has_music = any(clean_text(block.get("type")) == "music_play" for block in blocks)
        if not has_music and any(clean_text(block.get("type")) in {"dialogue", "narration"} for block in blocks):
            scenes_without_music.append({key: scene_record[key] for key in ("chapterName", "sceneName", "sceneId")})

        for block_index, block in enumerate(blocks):
            block_type = clean_text(block.get("type"))
            context = {
                "chapterName": scene_record["chapterName"],
                "sceneName": scene_record["sceneName"],
                "sceneId": scene_record["sceneId"],
                "blockId": get_block_id(block, block_index),
                "blockIndex": block_index,
            }
            if block_type == "music_play":
                asset_id = clean_text(block.get("assetId"))
                asset = assets_by_id.get(asset_id)
                end_mode = get_safe_music_end_mode(block.get("endMode"))
                end_block_id = clean_text(block.get("endBlockId"))
                end_block_index = block_index
                missing_end_block = False
                if end_mode == "after_block":
                    end_block_index = next((index for index, item in enumerate(blocks) if get_block_id(item, index) == end_block_id), -1)
                    if end_block_index < block_index:
                        missing_end_block = True
                        suggested_end = get_recommended_audio_range_end_block_id(blocks, block_index)
                        range_suggestions.append(
                            {
                                **context,
                                "assetId": asset_id,
                                "assetName": get_asset_name(asset, asset_id or "未绑定 BGM"),
                                "recommendedEndBlockId": suggested_end,
                                "title": "修正 BGM 文本范围",
                                "detail": "当前 BGM 指向的结束卡不存在或在开始卡之前，建议改到最近的剧情内容卡。",
                            }
                        )
                        end_block_index = next((index for index, item in enumerate(blocks) if get_block_id(item, index) == suggested_end), block_index)
                elif end_mode == "scene_end":
                    end_block_index = max(block_index, len(blocks) - 1)
                else:
                    next_audio_index = next(
                        (
                            index
                            for index, item in enumerate(blocks)
                            if index > block_index and clean_text(item.get("type")) in {"music_play", "music_stop"}
                        ),
                        -1,
                    )
                    end_block_index = next_audio_index - 1 if next_audio_index > block_index else max(block_index, len(blocks) - 1)
                timing = estimate_range_timing(blocks, block_index, end_block_index)
                fade_in_ms = clamp_int(block.get("fadeInMs"), 0, 30000, 0)
                fade_out_ms = clamp_int(block.get("fadeOutMs"), 0, 30000, 0)
                status = "ready"
                if not asset_id or not asset:
                    status = "blocker"
                    push_issue(issues, "blocker", "audio_missing_bgm_asset", "BGM 素材不存在", "这张播放音乐卡没有绑定有效 BGM 素材。", context)
                elif clean_text(asset.get("type")) and clean_text(asset.get("type")) != "bgm":
                    status = "blocker"
                    push_issue(issues, "blocker", "audio_wrong_bgm_type", "BGM 绑定了错误素材类型", f"当前绑定的是 {clean_text(asset.get('type'))}。", context)
                elif not asset_file_exists(asset):
                    status = "blocker"
                    push_issue(issues, "blocker", "audio_missing_bgm_file", "BGM 文件缺失", f"素材“{get_asset_name(asset, asset_id)}”还没有可用文件。", context)
                if missing_end_block:
                    status = "blocker" if status == "ready" else status
                    push_issue(issues, "blocker", "audio_bgm_end_block_missing", "BGM 结束卡片无效", "请为这首 BGM 指定有效的结束卡片或改成覆盖到场景结束。", context)
                if fade_in_ms <= 0:
                    if status == "ready":
                        status = "warn"
                    push_issue(issues, "warn", "audio_bgm_fade_in_missing", "BGM 缺少淡入", "建议至少设置 500-900ms 淡入，避免切曲生硬。", context)
                if end_mode != "until_next_music" and fade_out_ms <= 0:
                    if status == "ready":
                        status = "warn"
                    push_issue(issues, "warn", "audio_bgm_fade_out_missing", "BGM 范围缺少淡出", "指定范围或场景结束时建议设置淡出，避免音乐突然停止。", context)
                music_cues.append(
                    {
                        **context,
                        "cueType": "BGM",
                        "status": status,
                        "assetId": asset_id,
                        "assetName": get_asset_name(asset, asset_id or "未绑定 BGM"),
                        "assetPath": get_asset_path(asset),
                        "volume": clamp_int(block.get("volume"), 0, 100, 80),
                        "loop": bool(block.get("loop", True)),
                        "fadeInMs": fade_in_ms,
                        "fadeOutMs": fade_out_ms,
                        "endMode": end_mode,
                        "endLabel": MUSIC_END_MODE_LABELS[end_mode],
                        "endBlockId": end_block_id,
                        "resolvedEndBlockId": get_block_id(blocks[end_block_index], end_block_index) if blocks else "",
                        "resolvedEndLabel": get_block_label(blocks[end_block_index], end_block_index) if blocks else "",
                        "handoffType": "explicit_end" if end_mode == "after_block" else end_mode,
                        "durationLabel": timing["durationLabel"],
                        "estimatedSeconds": timing["estimatedSeconds"],
                        "readableCharacterCount": timing["readableCharacterCount"],
                        "textBlockCount": timing["textBlockCount"],
                        "timingTone": timing["tone"],
                        "timingHint": build_timing_hint(timing),
                    }
                )

            elif block_type == "sfx_play":
                asset_id = clean_text(block.get("assetId"))
                asset = assets_by_id.get(asset_id)
                status = "ready"
                if not asset_id or not asset:
                    status = "blocker"
                    push_issue(issues, "blocker", "audio_missing_sfx_asset", "音效素材不存在", "这张音效卡没有绑定有效音效素材。", context)
                elif clean_text(asset.get("type")) and clean_text(asset.get("type")) != "sfx":
                    status = "blocker"
                    push_issue(issues, "blocker", "audio_wrong_sfx_type", "音效绑定了错误素材类型", f"当前绑定的是 {clean_text(asset.get('type'))}。", context)
                elif not asset_file_exists(asset):
                    status = "blocker"
                    push_issue(issues, "blocker", "audio_missing_sfx_file", "音效文件缺失", f"素材“{get_asset_name(asset, asset_id)}”还没有可用文件。", context)
                if clamp_int(block.get("volume"), 0, 100, 80) <= 0:
                    status = "warn" if status == "ready" else status
                    push_issue(issues, "warn", "audio_sfx_volume_zero", "音效音量为 0", "音量为 0 的音效在试玩中听不到。", context)
                sfx_cues.append(
                    {
                        **context,
                        "cueType": "SFX",
                        "status": status,
                        "assetId": asset_id,
                        "assetName": get_asset_name(asset, asset_id or "未绑定音效"),
                        "assetPath": get_asset_path(asset),
                        "volume": clamp_int(block.get("volume"), 0, 100, 80),
                    }
                )

            elif block_type == "dialogue" and clean_text(block.get("voiceAssetId") or (block.get("voice") or {}).get("assetId")):
                voice = block.get("voice") if isinstance(block.get("voice"), dict) else {}
                asset_id = clean_text(block.get("voiceAssetId") or voice.get("assetId"))
                asset = assets_by_id.get(asset_id)
                status = "ready"
                if not asset:
                    status = "blocker"
                    push_issue(issues, "blocker", "audio_missing_voice_asset", "语音素材不存在", "这句台词绑定的语音条目不在素材库中。", context)
                elif clean_text(asset.get("type")) and clean_text(asset.get("type")) != "voice":
                    status = "blocker"
                    push_issue(issues, "blocker", "audio_wrong_voice_type", "语音绑定了错误素材类型", f"当前绑定的是 {clean_text(asset.get('type'))}。", context)
                elif not asset_file_exists(asset):
                    status = "blocker"
                    push_issue(issues, "blocker", "audio_missing_voice_file", "语音文件缺失", f"素材“{get_asset_name(asset, asset_id)}”还没有可用文件。", context)
                voice_cues.append(
                    {
                        **context,
                        "cueType": "Voice",
                        "status": status,
                        "assetId": asset_id,
                        "assetName": get_asset_name(asset, asset_id),
                        "assetPath": get_asset_path(asset),
                        "speakerName": get_character_name(characters_by_id, block.get("speakerId")),
                        "text": clean_text(block.get("text")),
                        "volume": clamp_int(block.get("voiceVolume") or voice.get("volume"), 0, 100, 100),
                    }
                )

    issues.sort(key=lambda issue: (-ISSUE_WEIGHT.get(issue["severity"], 0), issue.get("chapterName", ""), issue.get("sceneName", "")))
    blocker_count = sum(1 for issue in issues if issue["severity"] == "blocker")
    warning_count = sum(1 for issue in issues if issue["severity"] == "warn")
    tip_count = sum(1 for issue in issues if issue["severity"] == "tip")
    readiness_penalty = min(100, blocker_count * 18 + warning_count * 7 + len(scenes_without_music) * 3)
    sheet = {
        "formatVersion": AUDIO_CUE_SHEET_FORMAT_VERSION,
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "projectTitle": get_project_title(bundle),
        "summary": {
            "cueCount": len(music_cues),
            "sfxCueCount": len(sfx_cues),
            "voiceCueCount": len(voice_cues),
            "rangeSuggestionCount": len(range_suggestions),
            "scenesWithoutMusicCount": len(scenes_without_music),
            "explicitRangeCount": sum(1 for cue in music_cues if cue["endMode"] == "after_block"),
            "stopOrNextRangeCount": sum(1 for cue in music_cues if cue["endMode"] == "until_next_music"),
            "sceneEndRangeCount": sum(1 for cue in music_cues if cue["endMode"] == "scene_end"),
            "totalEstimatedMusicSeconds": sum(cue["estimatedSeconds"] for cue in music_cues),
            "missingAssetCount": sum(1 for cue in music_cues if cue["status"] == "blocker"),
            "missingSfxAssetCount": sum(1 for cue in sfx_cues if cue["status"] == "blocker"),
            "missingVoiceAssetCount": sum(1 for cue in voice_cues if cue["status"] == "blocker"),
            "blockerCount": blocker_count,
            "warningCount": warning_count,
            "tipCount": tip_count,
            "releaseReadinessPercent": max(0, 100 - readiness_penalty),
        },
        "musicCues": music_cues,
        "sfxCues": sfx_cues,
        "voiceCues": voice_cues,
        "rangeSuggestions": range_suggestions,
        "scenesWithoutMusic": scenes_without_music,
        "issues": issues,
    }
    sheet["statusDigest"] = get_audio_cue_sheet_status_digest(sheet)
    return sheet


def get_audio_cue_sheet_status_digest(sheet: dict) -> dict:
    summary = sheet.get("summary") or {}
    if not summary.get("cueCount") and not summary.get("sfxCueCount") and not summary.get("voiceCueCount"):
        return {"status": "empty", "title": "还没有音频 Cue", "detail": "添加 BGM、音效或语音后，这里会生成音频调度表。"}
    if summary.get("blockerCount", 0) > 0:
        return {"status": "blocked", "title": f"{summary.get('blockerCount', 0)} 个音频阻塞项", "detail": "优先处理缺素材、缺文件、错误类型和无效 BGM 结束范围。"}
    if summary.get("warningCount", 0) > 0 or summary.get("scenesWithoutMusicCount", 0) > 0:
        return {"status": "warn", "title": f"{summary.get('releaseReadinessPercent', 0)}% 音频调度就绪", "detail": "可以试玩，但建议补齐 BGM 淡入淡出、范围和重点场景音乐。"}
    return {"status": "ready", "title": "音频调度稳定", "detail": "BGM 范围、音效和语音文件状态比较完整，可以进入发布前试听。"}


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


def build_audio_cue_sheet_report(sheet: dict) -> str:
    summary = sheet.get("summary") or {}
    digest = sheet.get("statusDigest") or get_audio_cue_sheet_status_digest(sheet)
    music_rows = [
        [
            cue.get("status"),
            cue.get("chapterName"),
            cue.get("sceneName"),
            cue.get("assetName"),
            cue.get("endLabel"),
            cue.get("resolvedEndLabel"),
            cue.get("durationLabel"),
            cue.get("volume"),
            cue.get("fadeInMs"),
            cue.get("fadeOutMs"),
            cue.get("timingHint"),
        ]
        for cue in (sheet.get("musicCues") or [])[:120]
    ]
    sfx_rows = [
        [cue.get("status"), cue.get("chapterName"), cue.get("sceneName"), cue.get("assetName"), cue.get("volume")]
        for cue in (sheet.get("sfxCues") or [])[:80]
    ]
    voice_rows = [
        [cue.get("status"), cue.get("chapterName"), cue.get("sceneName"), cue.get("speakerName"), cue.get("assetName"), cue.get("text")[:48]]
        for cue in (sheet.get("voiceCues") or [])[:80]
    ]
    issue_rows = [
        [
            "先修" if issue.get("severity") == "blocker" else "复查" if issue.get("severity") == "warn" else "润色",
            issue.get("chapterName"),
            issue.get("sceneName"),
            issue.get("title"),
            issue.get("detail"),
        ]
        for issue in (sheet.get("issues") or [])[:80]
    ]
    suggestion_rows = [
        [item.get("chapterName"), item.get("sceneName"), item.get("assetName"), item.get("recommendedEndBlockId"), item.get("detail")]
        for item in (sheet.get("rangeSuggestions") or [])[:40]
    ]
    return "\n".join(
        [
            f"# {sheet.get('projectTitle') or 'Canvasia Project'} 音频调度表",
            "",
            f"- 生成时间：{sheet.get('generatedAt')}",
            f"- 状态：{digest.get('title')}",
            f"- 说明：{digest.get('detail')}",
            f"- BGM 预计总时长：{format_duration(summary.get('totalEstimatedMusicSeconds', 0))}",
            "",
            "## 总览",
            "",
            markdown_table(
                ["BGM", "SFX", "Voice", "缺音乐场景", "范围建议", "阻塞", "复查", "就绪度"],
                [
                    [
                        summary.get("cueCount", 0),
                        summary.get("sfxCueCount", 0),
                        summary.get("voiceCueCount", 0),
                        summary.get("scenesWithoutMusicCount", 0),
                        summary.get("rangeSuggestionCount", 0),
                        summary.get("blockerCount", 0),
                        summary.get("warningCount", 0),
                        f"{summary.get('releaseReadinessPercent', 0)}%",
                    ]
                ],
            ),
            "",
            "## BGM Cue 列表",
            "",
            markdown_table(["状态", "章节", "场景", "BGM", "接管方式", "结束位置", "预计时长", "音量", "淡入", "淡出", "节奏提示"], music_rows)
            or "当前没有 BGM Cue。",
            "",
            "## BGM 文本范围建议",
            "",
            markdown_table(["章节", "场景", "BGM", "建议结束卡", "说明"], suggestion_rows) or "当前没有明显的 BGM 范围建议。",
            "",
            "## 音效 Cue 列表",
            "",
            markdown_table(["状态", "章节", "场景", "音效", "音量"], sfx_rows) or "当前没有音效 Cue。",
            "",
            "## 语音 Cue 列表",
            "",
            markdown_table(["状态", "章节", "场景", "角色", "语音", "台词"], voice_rows) or "当前没有绑定语音的台词。",
            "",
            "## 优先问题",
            "",
            markdown_table(["级别", "章节", "场景", "问题", "说明"], issue_rows) or "当前没有明显音频调度问题。",
            "",
        ]
    )


def build_audio_cue_sheet_csv(sheet: dict) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "cueType",
            "status",
            "chapter",
            "scene",
            "blockIndex",
            "assetId",
            "assetName",
            "assetPath",
            "volume",
            "fadeInMs",
            "fadeOutMs",
            "endMode",
            "resolvedEndBlockId",
            "durationLabel",
            "estimatedSeconds",
            "readableCharacters",
            "speaker",
            "text",
            "timingHint",
            "issues",
        ]
    )
    issue_map: dict[str, list[str]] = {}
    for issue in sheet.get("issues") or []:
        key = f"{issue.get('sceneId')}:{issue.get('blockId')}"
        issue_map.setdefault(key, []).append(issue.get("title", ""))
    for cue in [*(sheet.get("musicCues") or []), *(sheet.get("sfxCues") or []), *(sheet.get("voiceCues") or [])]:
        key = f"{cue.get('sceneId')}:{cue.get('blockId')}"
        writer.writerow(
            [
                cue.get("cueType"),
                cue.get("status"),
                cue.get("chapterName"),
                cue.get("sceneName"),
                int(cue.get("blockIndex") or 0) + 1,
                cue.get("assetId"),
                cue.get("assetName"),
                cue.get("assetPath"),
                cue.get("volume"),
                cue.get("fadeInMs", ""),
                cue.get("fadeOutMs", ""),
                cue.get("endMode", ""),
                cue.get("resolvedEndBlockId", ""),
                cue.get("durationLabel", ""),
                cue.get("estimatedSeconds", ""),
                cue.get("readableCharacterCount", ""),
                cue.get("speakerName", ""),
                cue.get("text", ""),
                cue.get("timingHint", ""),
                " / ".join(issue for issue in issue_map.get(key, []) if issue),
            ]
        )
    return "\ufeff" + output.getvalue()


def write_export_audio_cue_sheet_files(target_dir: Path, *, bundle: dict, assets_doc: dict) -> dict:
    sheet = build_audio_cue_sheet(bundle, assets_doc)
    json_path = target_dir / EXPORT_AUDIO_CUE_SHEET_JSON_NAME
    report_path = target_dir / EXPORT_AUDIO_CUE_SHEET_REPORT_NAME
    csv_path = target_dir / EXPORT_AUDIO_CUE_SHEET_CSV_NAME
    json_path.write_text(json.dumps(sheet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(build_audio_cue_sheet_report(sheet), encoding="utf-8")
    csv_path.write_text(build_audio_cue_sheet_csv(sheet), encoding="utf-8")
    summary = sheet["summary"]
    return {
        "audioCueSheet": sheet,
        "audioCueSheetName": json_path.name,
        "audioCueSheetPath": str(json_path),
        "audioCueSheetReportName": report_path.name,
        "audioCueSheetReportPath": str(report_path),
        "audioCueSheetCsvName": csv_path.name,
        "audioCueSheetCsvPath": str(csv_path),
        "audioCueSheetReadinessPercent": summary["releaseReadinessPercent"],
        "audioCueSheetCueCount": summary["cueCount"],
        "audioCueSheetBlockerCount": summary["blockerCount"],
        "audioCueSheetWarningCount": summary["warningCount"],
    }


__all__ = [
    "EXPORT_AUDIO_CUE_SHEET_JSON_NAME",
    "EXPORT_AUDIO_CUE_SHEET_REPORT_NAME",
    "EXPORT_AUDIO_CUE_SHEET_CSV_NAME",
    "build_audio_cue_sheet",
    "build_audio_cue_sheet_report",
    "build_audio_cue_sheet_csv",
    "write_export_audio_cue_sheet_files",
]
