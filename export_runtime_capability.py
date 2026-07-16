from __future__ import annotations

import csv
import io
import json
import re
from datetime import datetime
from pathlib import Path


EXPORT_RUNTIME_CAPABILITY_JSON_NAME = "runtime-capability-matrix.json"
EXPORT_RUNTIME_CAPABILITY_REPORT_NAME = "runtime-capability-matrix.md"
EXPORT_RUNTIME_CAPABILITY_CSV_NAME = "runtime-capability-matrix.csv"

CAPABILITY_ROWS = [
    ("background", "画面", "full", "full", "背景 / CG 可播放；3D 场景建议重点验收原生 Runtime。"),
    ("character_show", "角色", "full", "full", "支持角色登场、表情、站位、舞台参数和基础转场。"),
    ("character_move", "角色", "full", "full", "支持角色平滑走位、换表情、缩放、透明度、翻转、图层与缓动。"),
    ("character_hide", "角色", "full", "full", "支持角色离场和基础转场。"),
    ("dialogue", "文本", "full", "full", "支持说话人、表情同步、打字机、语音和文本历史。"),
    ("narration", "文本", "full", "full", "支持旁白文本、打字机、语音和文本历史。"),
    ("choice", "分支", "full", "full", "支持玩家选项、变量效果和目标场景跳转。"),
    ("condition", "分支", "full", "full", "支持条件分支、否则分支和变量判断。"),
    ("jump", "分支", "full", "full", "支持显式场景跳转。"),
    ("variable_set", "变量", "full", "full", "支持变量赋值。"),
    ("variable_add", "变量", "full", "full", "支持数值变量增减。"),
    ("music_play", "音频", "full", "full", "支持 BGM 播放、循环、音量、淡入和范围调度。"),
    ("music_stop", "音频", "full", "full", "支持 BGM 淡出停止。"),
    ("sfx_play", "音频", "full", "full", "支持音效播放与音量控制。"),
    ("video_play", "视频", "full", "partial", "视频播放依赖目标平台能力；发布前需要验音画同步、跳过和失败兜底。"),
    ("credits_roll", "结尾", "full", "full", "支持片尾字幕与回想 / 发布检查。"),
    ("wait", "演出", "full", "full", "支持等待 / 停顿节奏卡。"),
    ("particle_effect", "演出", "full", "full", "支持项目粒子预设、图片粒子、密度、速度、重力和颜色等参数。"),
    ("screen_shake", "演出", "full", "full", "支持屏幕震动。"),
    ("screen_flash", "演出", "full", "full", "支持闪屏。"),
    ("screen_fade", "演出", "full", "full", "支持淡入淡出。"),
    ("camera_zoom", "演出", "full", "full", "支持镜头推近、拉远和重置。"),
    ("camera_pan", "演出", "full", "full", "支持镜头平移和回中。"),
    ("screen_filter", "演出", "full", "full", "支持滤镜、色调和清除。"),
    ("depth_blur", "演出", "full", "full", "支持景深模糊和清除。"),
]

STATUS_LABELS = {
    "full": "完整支持",
    "partial": "需要验收",
    "planned": "规划中",
    "unsupported": "未支持",
    "unknown": "未知卡片",
}

STATUS_WEIGHT = {
    "full": 0,
    "partial": 1,
    "planned": 2,
    "unsupported": 3,
    "unknown": 4,
}

VISUAL_EFFECT_TYPES = {
    "wait",
    "screen_shake",
    "screen_flash",
    "screen_fade",
    "camera_zoom",
    "camera_pan",
    "screen_filter",
    "depth_blur",
    "particle_effect",
}


def clean_text(value: object, fallback: str = "") -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text or fallback


def as_list(value: object) -> list:
    return value if isinstance(value, list) else []


def as_int(value: object, fallback: int = 0) -> int:
    try:
        return int(value if value is not None else fallback)
    except (TypeError, ValueError):
        return fallback


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def get_project(bundle: dict) -> dict:
    project = bundle.get("project") if isinstance(bundle, dict) else {}
    return project if isinstance(project, dict) else {}


def get_asset_list(bundle: dict) -> list[dict]:
    assets = bundle.get("assets") if isinstance(bundle, dict) else []
    return [asset for asset in as_list(assets) if isinstance(asset, dict)]


def build_asset_map(bundle: dict) -> dict[str, dict]:
    return {clean_text(asset.get("id")): asset for asset in get_asset_list(bundle) if clean_text(asset.get("id"))}


def iter_scene_records(bundle: dict) -> list[dict]:
    records: list[dict] = []
    seen_scene_ids: set[str] = set()
    chapters = as_list(bundle.get("chapters") if isinstance(bundle, dict) else [])
    for chapter_index, chapter in enumerate(chapters):
        if not isinstance(chapter, dict):
            continue
        chapter_name = clean_text(chapter.get("name") or chapter.get("title"), f"章节 {chapter_index + 1}")
        for scene_index, scene in enumerate(as_list(chapter.get("scenes"))):
            if not isinstance(scene, dict):
                continue
            scene_id = clean_text(scene.get("id") or scene.get("sceneId"), f"scene_{chapter_index + 1}_{scene_index + 1}")
            if scene_id in seen_scene_ids:
                continue
            seen_scene_ids.add(scene_id)
            records.append(
                {
                    "scene": scene,
                    "sceneId": scene_id,
                    "sceneName": clean_text(scene.get("name") or scene.get("title"), scene_id),
                    "chapterName": chapter_name,
                    "chapterIndex": chapter_index,
                    "sceneIndex": scene_index,
                }
            )
    for scene_index, scene in enumerate(as_list(bundle.get("scenes") if isinstance(bundle, dict) else [])):
        if not isinstance(scene, dict):
            continue
        scene_id = clean_text(scene.get("id") or scene.get("sceneId"), f"scene_{scene_index + 1}")
        if scene_id in seen_scene_ids:
            continue
        seen_scene_ids.add(scene_id)
        records.append(
            {
                "scene": scene,
                "sceneId": scene_id,
                "sceneName": clean_text(scene.get("name") or scene.get("title"), scene_id),
                "chapterName": clean_text(scene.get("chapterName"), "未分章"),
                "chapterIndex": 9999,
                "sceneIndex": scene_index,
            }
        )
    return sorted(records, key=lambda record: (record["chapterIndex"], record["sceneIndex"]))


def iter_block_records(bundle: dict) -> list[dict]:
    records: list[dict] = []
    for scene_record in iter_scene_records(bundle):
        for block_index, block in enumerate(as_list(scene_record["scene"].get("blocks"))):
            if isinstance(block, dict):
                records.append({**scene_record, "block": block, "blockIndex": block_index})
    return records


def worst_status(*statuses: str) -> str:
    result = "full"
    for status in statuses:
        safe_status = status or "unknown"
        if STATUS_WEIGHT.get(safe_status, 99) > STATUS_WEIGHT.get(result, 99):
            result = safe_status
    return result


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, clean_text(status, "未知"))


def build_runtime_usage(bundle: dict) -> dict[str, dict]:
    asset_map = build_asset_map(bundle)
    usage: dict[str, dict] = {}
    for record in iter_block_records(bundle):
        block = record["block"]
        block_type = clean_text(block.get("type"), "unknown")
        item = usage.setdefault(
            block_type,
            {
                "type": block_type,
                "count": 0,
                "sceneNames": [],
                "chapterNames": [],
                "scene3dCount": 0,
            },
        )
        item["count"] += 1
        if record["sceneName"] not in item["sceneNames"]:
            item["sceneNames"].append(record["sceneName"])
        if record["chapterName"] not in item["chapterNames"]:
            item["chapterNames"].append(record["chapterName"])
        if block_type == "background":
            asset = asset_map.get(clean_text(block.get("assetId") or block.get("backgroundAssetId") or block.get("cgAssetId")))
            if isinstance(asset, dict) and clean_text(asset.get("type")) == "scene3d":
                item["scene3dCount"] += 1
    return usage


def build_runtime_acceptance_checklist(rows: list[dict], summary: dict) -> dict:
    used_rows = [row for row in rows if as_int(row.get("usedCount")) > 0]
    items: list[dict] = []
    seen_ids: set[str] = set()

    def add_item(item: dict) -> None:
        item_id = clean_text(item.get("id"))
        if not item_id or item_id in seen_ids:
            return
        seen_ids.add(item_id)
        items.append(
            {
                "id": item_id,
                "target": clean_text(item.get("target"), "cross"),
                "targetLabel": clean_text(item.get("targetLabel"), "Web / 原生"),
                "severity": clean_text(item.get("severity"), "check"),
                "severityLabel": clean_text(item.get("severityLabel"), "点测"),
                "title": clean_text(item.get("title"), "Runtime 验收项"),
                "detail": clean_text(item.get("detail"), "导出后按目标平台实际跑一遍。"),
                "relatedBlockTypes": [clean_text(value) for value in as_list(item.get("relatedBlockTypes")) if clean_text(value)],
            }
        )

    if not used_rows:
        return {"items": [], "summary": summarize_acceptance_items([])}

    add_item(
        {
            "id": "web-runtime-first-run",
            "target": "web",
            "targetLabel": "Web Runtime",
            "severity": "check",
            "severityLabel": "点测",
            "title": "Web 试玩包从入口跑到第一处分支",
            "detail": "确认开场背景、第一条台词、菜单、存档和至少一个选项都能正常响应。",
            "relatedBlockTypes": [row["type"] for row in used_rows[:8]],
        }
    )
    add_item(
        {
            "id": "native-runtime-first-run",
            "target": "native",
            "targetLabel": "原生 Runtime",
            "severity": "warn" if as_int(summary.get("nativePartialCount")) else "check",
            "severityLabel": "重点验收" if as_int(summary.get("nativePartialCount")) else "点测",
            "title": "原生 Runtime 在目标平台启动并完成一轮读档",
            "detail": "确认启动、继续游戏、正式存档、读档、系统菜单、历史文本和退出流程。",
            "relatedBlockTypes": [row["type"] for row in used_rows[:8]],
        }
    )
    add_item(
        {
            "id": "runtime-input-navigation",
            "target": "cross",
            "targetLabel": "Web / 原生",
            "severity": "check",
            "severityLabel": "点测",
            "title": "输入导航要验键鼠、手柄与断连回退",
            "detail": "在 Web / 桌面包和原生包各验证方向焦点、确认、返回、系统菜单、自动播放和历史文本；手柄断连后键盘与鼠标仍应立即可用。",
            "relatedBlockTypes": [row["type"] for row in used_rows[:8]],
        }
    )

    used_types = {row["type"] for row in used_rows}
    for row in used_rows:
        if row["overallStatus"] in {"unknown", "unsupported", "planned"}:
            add_item(
                {
                    "id": f"runtime-support-{row['type']}",
                    "target": "cross",
                    "targetLabel": "Web / 原生",
                    "severity": "blocker",
                    "severityLabel": "先修",
                    "title": f"{row['type']} 需要先补 Runtime 支持声明",
                    "detail": f"{row['type']} 已在项目中使用，但还没有明确 Web / 原生播放策略。",
                    "relatedBlockTypes": [row["type"]],
                }
            )
        if row["nativeStatus"] != "full" and row["nativeStatus"] != "unknown":
            add_item(
                {
                    "id": f"native-runtime-{row['type']}",
                    "target": "native",
                    "targetLabel": "原生 Runtime",
                    "severity": "warn",
                    "severityLabel": "重点验收",
                    "title": f"原生 Runtime 重点验收 {row['type']}",
                    "detail": f"{row['type']} 在原生 Runtime 不是完整覆盖；需要在目标系统确认表现和兜底逻辑。",
                    "relatedBlockTypes": [row["type"]],
                }
            )

    if "video_play" in used_types:
        add_item(
            {
                "id": "runtime-video-sync",
                "target": "native",
                "targetLabel": "原生 Runtime",
                "severity": "warn",
                "severityLabel": "重点验收",
                "title": "视频播放要验音画同步、跳过和结束回到剧情",
                "detail": "检查视频开始、播放中跳过、播放结束、失败兜底，以及回到下一张剧情卡片是否稳定。",
                "relatedBlockTypes": ["video_play"],
            }
        )
    if {"music_play", "music_stop", "sfx_play"} & used_types:
        add_item(
            {
                "id": "runtime-audio-cues",
                "target": "cross",
                "targetLabel": "Web / 原生",
                "severity": "check",
                "severityLabel": "点测",
                "title": "音频调度要验淡入淡出、循环、音量和范围",
                "detail": "确认 BGM 能按指定剧情范围切换，音效不抢占 BGM，停止和淡出不会残留。",
                "relatedBlockTypes": ["music_play", "music_stop", "sfx_play"],
            }
        )
    if {"character_show", "character_move", "character_hide"} & used_types:
        add_item(
            {
                "id": "runtime-character-stage",
                "target": "cross",
                "targetLabel": "Web / 原生",
                "severity": "check",
                "severityLabel": "点测",
                "title": "立绘登退场与舞台动作要验位置、大小和缓动",
                "detail": "确认自定义位置、缩放、透明度、走位缓动、隐藏和多角色同屏不会错位或残影。",
                "relatedBlockTypes": ["character_show", "character_move", "character_hide"],
            }
        )
    if used_types & VISUAL_EFFECT_TYPES:
        add_item(
            {
                "id": "runtime-visual-effects-reset",
                "target": "cross",
                "targetLabel": "Web / 原生",
                "severity": "check",
                "severityLabel": "点测",
                "title": "镜头与滤镜演出要验播放结束后的复位",
                "detail": "确认震动、闪屏、淡入淡出、镜头移动、滤镜和景深不会遮住 UI 或残留到下一场景。",
                "relatedBlockTypes": sorted(used_types & VISUAL_EFFECT_TYPES),
            }
        )
    return {"items": items, "summary": summarize_acceptance_items(items)}


def summarize_acceptance_items(items: list[dict]) -> dict:
    return {
        "itemCount": len(items),
        "blockerCount": sum(1 for item in items if item.get("severity") == "blocker"),
        "warningCount": sum(1 for item in items if item.get("severity") == "warn"),
        "checkCount": sum(1 for item in items if item.get("severity") == "check"),
        "webItemCount": sum(1 for item in items if item.get("target") == "web"),
        "nativeItemCount": sum(1 for item in items if item.get("target") == "native"),
        "crossRuntimeItemCount": sum(1 for item in items if item.get("target") == "cross"),
    }


def build_vn_essentials_audit(bundle: dict) -> dict:
    scene_records = iter_scene_records(bundle)
    block_records = iter_block_records(bundle)
    scene_count = len(scene_records)
    issues: list[dict] = []
    scenes_with_background: set[str] = set()
    scenes_with_music: set[str] = set()
    character_positions: set[str] = set()
    metrics = {
        "sceneCount": scene_count,
        "blockCount": len(block_records),
        "dialogueCount": 0,
        "narrationCount": 0,
        "choiceCount": 0,
        "conditionCount": 0,
        "jumpCount": 0,
        "backgroundBlockCount": 0,
        "characterShowCount": 0,
        "characterMoveCount": 0,
        "characterHideCount": 0,
        "musicPlayCount": 0,
        "musicStopCount": 0,
        "musicScopedCount": 0,
        "musicFadeInCount": 0,
        "musicFadeOutCount": 0,
        "sfxPlayCount": 0,
        "videoPlayCount": 0,
    }
    for record in block_records:
        block = record["block"]
        block_type = clean_text(block.get("type"), "unknown")
        if block_type == "dialogue":
            metrics["dialogueCount"] += 1
        elif block_type == "narration":
            metrics["narrationCount"] += 1
        elif block_type == "choice":
            metrics["choiceCount"] += 1
        elif block_type == "condition":
            metrics["conditionCount"] += 1
        elif block_type == "jump":
            metrics["jumpCount"] += 1
        elif block_type == "background":
            metrics["backgroundBlockCount"] += 1
            scenes_with_background.add(record["sceneId"])
        elif block_type == "character_show":
            metrics["characterShowCount"] += 1
            character_positions.add(clean_text(block.get("position"), "center"))
        elif block_type == "character_move":
            metrics["characterMoveCount"] += 1
            character_positions.add(clean_text(block.get("position"), "center"))
        elif block_type == "character_hide":
            metrics["characterHideCount"] += 1
        elif block_type == "music_play":
            metrics["musicPlayCount"] += 1
            scenes_with_music.add(record["sceneId"])
            if clean_text(block.get("endMode"), "until_next_music") != "until_next_music":
                metrics["musicScopedCount"] += 1
            if as_int(block.get("fadeInMs")) > 0:
                metrics["musicFadeInCount"] += 1
            if as_int(block.get("fadeOutMs")) > 0:
                metrics["musicFadeOutCount"] += 1
        elif block_type == "music_stop":
            metrics["musicStopCount"] += 1
            if as_int(block.get("fadeOutMs")) > 0:
                metrics["musicFadeOutCount"] += 1
        elif block_type == "sfx_play":
            metrics["sfxPlayCount"] += 1
        elif block_type == "video_play":
            metrics["videoPlayCount"] += 1

    metrics["textBlockCount"] = metrics["dialogueCount"] + metrics["narrationCount"] + metrics["choiceCount"]
    metrics["branchBlockCount"] = metrics["choiceCount"] + metrics["conditionCount"] + metrics["jumpCount"]
    metrics["scenesWithBackground"] = len(scenes_with_background)
    metrics["scenesWithMusic"] = len(scenes_with_music)
    metrics["characterPositionVariantCount"] = len(character_positions)

    def issue(severity: str, code: str, area: str, title: str, detail: str, suggestion: str) -> None:
        issues.append(
            {
                "severity": severity,
                "severityLabel": "基础缺口" if severity == "warn" else "体验打磨",
                "code": code,
                "area": area,
                "title": title,
                "detail": detail,
                "suggestion": suggestion,
            }
        )

    if scene_count > 0 and metrics["textBlockCount"] == 0:
        issue("warn", "story_text_missing", "story", "缺少可读剧情文本", "当前项目已有场景，但没有台词、旁白或选项卡片。", "先补一段可从入口读到的文本，再做导出试玩。")
    if scene_count > 0 and metrics["scenesWithBackground"] < scene_count:
        issue("warn", "background_coverage", "visual", "背景覆盖不完整", f"{scene_count - metrics['scenesWithBackground']} 个场景还没有背景 / CG / 3D 场景卡片。", "给每个可试玩场景至少放一张画面素材，避免黑屏式试玩体验。")
    if metrics["dialogueCount"] >= 3 and metrics["characterShowCount"] == 0:
        issue("soft", "character_stage_missing", "character", "人物登场演出偏弱", "台词已经成段，但没有检测到角色登场卡片。", "给主要角色补显示/隐藏、位置、缩放和淡入淡出，让试玩更像正式 VN。")
    if scene_count >= 2 and metrics["musicPlayCount"] == 0:
        issue("soft", "bgm_plan_missing", "audio", "缺少 BGM 进入点", "多场景项目没有检测到播放 BGM 卡片。", "为章节开头、转场或情绪段落设置 BGM，并确认导出包里能按范围切换。")
    if metrics["musicPlayCount"] >= 2 and metrics["musicScopedCount"] == 0 and metrics["musicStopCount"] == 0:
        issue("warn", "bgm_scope_missing", "audio", "多首 BGM 缺少明确播放范围", f"检测到 {metrics['musicPlayCount']} 个 BGM 播放点，但没有 scene_end / after_block 范围或停止音乐卡片。", "给每首关键曲目设置结束范围，避免音乐覆盖到不该出现的文本段落。")
    if metrics["musicPlayCount"] > 0 and metrics["musicFadeInCount"] < metrics["musicPlayCount"]:
        issue("soft", "bgm_fade_in_missing", "audio", "部分 BGM 没有淡入", f"{metrics['musicPlayCount'] - metrics['musicFadeInCount']} 个 BGM 播放点没有设置淡入时间。", "给 BGM 播放卡片设置 400-1000ms 淡入，减少切歌突兀感。")
    if scene_count >= 3 and metrics["sfxPlayCount"] == 0:
        issue("soft", "sfx_plan_missing", "audio", "缺少基础音效点", "多场景项目没有检测到音效卡片。", "给脚步、门铃、短信提示、心跳或关键演出补少量音效点。")
    if scene_count >= 2 and metrics["choiceCount"] == 0:
        issue("soft", "choice_node_missing", "branch", "缺少可交互选项", "多场景项目没有检测到选项卡片。", "如果目标不是纯电子书，建议至少加入一个选项、分支或可回收差分。")

    area_specs = [
        ("story", "剧情文本", ["story_text_missing"], f"{metrics['textBlockCount']} 个文本/选项块"),
        ("visual", "画面背景", ["background_coverage"], f"{metrics['scenesWithBackground']}/{scene_count} 个场景有背景"),
        ("character", "人物舞台", ["character_stage_missing"], f"{metrics['characterShowCount']} 次登场 / {metrics['characterMoveCount']} 次动作"),
        ("audio", "音频调度", ["bgm_plan_missing", "bgm_scope_missing", "bgm_fade_in_missing", "sfx_plan_missing"], f"{metrics['musicPlayCount']} 个 BGM / {metrics['sfxPlayCount']} 个音效"),
        ("branch", "分支变量", ["choice_node_missing"], f"{metrics['choiceCount']} 个选项 / {metrics['conditionCount']} 个条件"),
    ]
    areas: list[dict] = []
    for area_id, label, codes, summary in area_specs:
        related = [item for item in issues if item["code"] in codes]
        status = "needs_fix" if any(item["severity"] == "warn" for item in related) else "needs_polish" if related else "ready"
        areas.append(
            {
                "id": area_id,
                "label": label,
                "status": status,
                "statusLabel": {"ready": "基础稳", "needs_fix": "先补基础", "needs_polish": "建议打磨"}[status],
                "issueCount": len(related),
                "warnCount": sum(1 for item in related if item["severity"] == "warn"),
                "softCount": sum(1 for item in related if item["severity"] == "soft"),
                "summary": summary,
                "detail": related[0]["suggestion"] if related else "这一块基础体验暂时稳定。",
            }
        )

    warn_count = sum(1 for item in issues if item["severity"] == "warn")
    soft_count = sum(1 for item in issues if item["severity"] == "soft")
    ready_area_count = sum(1 for area in areas if area["status"] == "ready")
    score = 0 if scene_count == 0 else max(0, round(100 - warn_count * 14 - soft_count * 6 - (len(areas) - ready_area_count) * 2))
    status = "empty" if scene_count == 0 else "needs_fix" if warn_count else "needs_polish" if soft_count else "ready"
    return {
        "status": status,
        "statusLabel": {"empty": "待开始", "ready": "基础稳", "needs_fix": "先补基础", "needs_polish": "建议打磨"}[status],
        "summary": {
            "score": score,
            "areaCount": len(areas),
            "readyAreaCount": ready_area_count,
            "attentionAreaCount": len(areas) - ready_area_count,
            "warnCount": warn_count,
            "softCount": soft_count,
            "issueCount": len(issues),
            "recommendation": issues[0]["suggestion"] if issues else ("先创建第一个场景和第一段文本。" if scene_count == 0 else "基础视觉小说体验未发现明显缺口，可以继续做实机点测。"),
        },
        "metrics": metrics,
        "areas": areas,
        "issues": issues,
    }


def build_export_runtime_capability_matrix(bundle: dict) -> dict:
    project = get_project(bundle)
    usage = build_runtime_usage(bundle)
    capability_by_type = {row[0]: row for row in CAPABILITY_ROWS}
    rows: list[dict] = []
    for block_type, group, web_status, native_status, note in CAPABILITY_ROWS:
        item = usage.get(block_type, {})
        effective_native = worst_status(native_status, "partial") if as_int(item.get("scene3dCount")) else native_status
        overall = worst_status(web_status, effective_native)
        rows.append(
            {
                "type": block_type,
                "group": group,
                "webStatus": web_status,
                "nativeStatus": effective_native,
                "overallStatus": overall,
                "webStatusLabel": status_label(web_status),
                "nativeStatusLabel": status_label(effective_native),
                "overallStatusLabel": status_label(overall),
                "usedCount": as_int(item.get("count")),
                "scene3dCount": as_int(item.get("scene3dCount")),
                "usedSceneNames": as_list(item.get("sceneNames"))[:5],
                "usedChapterNames": as_list(item.get("chapterNames"))[:5],
                "note": note,
            }
        )
    for block_type, item in usage.items():
        if block_type in capability_by_type:
            continue
        rows.append(
            {
                "type": block_type,
                "group": "未知",
                "webStatus": "unknown",
                "nativeStatus": "unknown",
                "overallStatus": "unknown",
                "webStatusLabel": status_label("unknown"),
                "nativeStatusLabel": status_label("unknown"),
                "overallStatusLabel": status_label("unknown"),
                "usedCount": as_int(item.get("count")),
                "scene3dCount": as_int(item.get("scene3dCount")),
                "usedSceneNames": as_list(item.get("sceneNames"))[:5],
                "usedChapterNames": as_list(item.get("chapterNames"))[:5],
                "note": "这个卡片类型还没有登记 Runtime 覆盖状态，需要先补矩阵和播放器支持。",
            }
        )
    rows.sort(key=lambda row: (0 if as_int(row.get("usedCount")) else 1, -STATUS_WEIGHT.get(row.get("overallStatus"), 0), row.get("type", "")))
    used_rows = [row for row in rows if as_int(row.get("usedCount")) > 0]
    issues = [
        {
            "severity": "blocker" if row["overallStatus"] in {"unknown", "unsupported"} else "warning",
            "code": f"runtime_{row['overallStatus']}",
            "title": f"{row['type']}：{row['overallStatusLabel']}",
            "detail": row["note"],
            "blockType": row["type"],
            "group": row["group"],
            "usedCount": row["usedCount"],
            "sceneNames": row["usedSceneNames"],
        }
        for row in used_rows
        if row["overallStatus"] != "full"
    ]
    summary = {
        "capabilityCount": len(CAPABILITY_ROWS),
        "totalBlockCount": len(iter_block_records(bundle)),
        "usedTypeCount": len(used_rows),
        "fullUsedTypeCount": sum(1 for row in used_rows if row["overallStatus"] == "full"),
        "partialUsedTypeCount": sum(1 for row in used_rows if row["overallStatus"] == "partial"),
        "unsupportedUsedTypeCount": sum(1 for row in used_rows if row["overallStatus"] in {"planned", "unsupported"}),
        "unknownUsedTypeCount": sum(1 for row in used_rows if row["overallStatus"] == "unknown"),
        "webPartialCount": sum(1 for row in used_rows if row["webStatus"] != "full"),
        "nativePartialCount": sum(1 for row in used_rows if row["nativeStatus"] != "full"),
        "scene3dBackgroundCount": sum(as_int(row.get("scene3dCount")) for row in used_rows),
        "issueCount": len(issues),
    }
    acceptance = build_runtime_acceptance_checklist(rows, summary)
    essentials = build_vn_essentials_audit(bundle)
    return {
        "formatVersion": 1,
        "generatedAt": now_iso(),
        "projectTitle": clean_text(project.get("title"), "Canvasia Project"),
        "rows": rows,
        "usedRows": used_rows,
        "issues": issues,
        "summary": summary,
        "acceptance": acceptance,
        "essentials": essentials,
    }


def get_runtime_capability_digest(matrix: dict) -> dict:
    summary = matrix.get("summary") if isinstance(matrix.get("summary"), dict) else {}
    if as_int(summary.get("totalBlockCount")) == 0:
        return {"status": "empty", "title": "还没有可检查的剧情卡片", "detail": "项目里还没有剧情卡片。"}
    if as_int(summary.get("unknownUsedTypeCount")) or as_int(summary.get("unsupportedUsedTypeCount")):
        return {"status": "blocked", "title": "存在未确认 Runtime 支持", "detail": "当前项目使用了尚未登记或未支持的卡片类型，建议先补 Runtime 支持再发布。"}
    if as_int(summary.get("partialUsedTypeCount")) or as_int(summary.get("nativePartialCount")) or as_int(summary.get("webPartialCount")):
        return {"status": "warning", "title": "部分卡片需要重点验收", "detail": "当前卡片可以导出，但部分能力在不同 Runtime 中依赖兜底或目标平台环境。"}
    return {"status": "ready", "title": "Runtime 覆盖稳定", "detail": "当前项目使用的卡片类型在 Web Runtime 和原生 Runtime 中都有完整覆盖。"}


def markdown_cell(value: object) -> str:
    return clean_text(value, "-").replace("|", "\\|")


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    if not rows:
        return ""
    lines = [
        "| " + " | ".join(markdown_cell(header) for header in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(markdown_cell(value) for value in row) + " |")
    return "\n".join(lines)


def build_export_runtime_capability_markdown(matrix: dict) -> str:
    summary = matrix.get("summary") if isinstance(matrix.get("summary"), dict) else {}
    essentials = matrix.get("essentials") if isinstance(matrix.get("essentials"), dict) else {}
    essentials_summary = essentials.get("summary") if isinstance(essentials.get("summary"), dict) else {}
    acceptance = matrix.get("acceptance") if isinstance(matrix.get("acceptance"), dict) else {}
    acceptance_summary = acceptance.get("summary") if isinstance(acceptance.get("summary"), dict) else {}
    digest = get_runtime_capability_digest(matrix)
    used_rows = [
        [
            row.get("group"),
            row.get("type"),
            row.get("usedCount"),
            row.get("webStatusLabel"),
            row.get("nativeStatusLabel"),
            row.get("overallStatusLabel"),
            " / ".join(as_list(row.get("usedSceneNames"))),
            row.get("note"),
        ]
        for row in as_list(matrix.get("usedRows"))
    ]
    issue_rows = [
        [index + 1, issue.get("severity"), issue.get("blockType"), issue.get("usedCount"), " / ".join(as_list(issue.get("sceneNames"))), issue.get("detail")]
        for index, issue in enumerate(as_list(matrix.get("issues")))
    ]
    essential_area_rows = [
        [area.get("label"), area.get("statusLabel"), area.get("summary"), area.get("detail")]
        for area in as_list(essentials.get("areas"))
    ]
    essential_issue_rows = [
        [index + 1, issue.get("severityLabel"), issue.get("title"), issue.get("detail"), issue.get("suggestion")]
        for index, issue in enumerate(as_list(essentials.get("issues")))
    ]
    acceptance_rows = [
        [index + 1, item.get("targetLabel"), item.get("severityLabel"), item.get("title"), " / ".join(as_list(item.get("relatedBlockTypes"))), item.get("detail")]
        for index, item in enumerate(as_list(acceptance.get("items")))
    ]
    return "\n".join(
        [
            f"# {markdown_cell(matrix.get('projectTitle'))} Runtime 覆盖矩阵",
            "",
            f"- 生成时间：{markdown_cell(matrix.get('generatedAt'))}",
            f"- 状态：{markdown_cell(digest['title'])}",
            f"- 说明：{markdown_cell(digest['detail'])}",
            "",
            "## 总览",
            "",
            markdown_table(
                ["剧情卡片", "已用类型", "完整类型", "需验收类型", "未知类型", "Web 风险", "原生风险", "验收项"],
                [[summary.get("totalBlockCount"), summary.get("usedTypeCount"), summary.get("fullUsedTypeCount"), summary.get("partialUsedTypeCount"), summary.get("unknownUsedTypeCount"), summary.get("webPartialCount"), summary.get("nativePartialCount"), acceptance_summary.get("itemCount")]],
            ),
            "",
            "## VN 基础能力成熟度",
            "",
            markdown_table(
                ["基础分", "状态", "稳妥项", "需关注项", "基础缺口", "体验打磨", "建议"],
                [[f"{essentials_summary.get('score', 0)}/100", essentials.get("statusLabel"), essentials_summary.get("readyAreaCount"), essentials_summary.get("attentionAreaCount"), essentials_summary.get("warnCount"), essentials_summary.get("softCount"), essentials_summary.get("recommendation")]],
            ),
            "",
            markdown_table(["领域", "状态", "当前情况", "处理提示"], essential_area_rows) or "当前项目还没有可分析的 VN 基础能力。",
            "",
            markdown_table(["序号", "级别", "基础缺口", "说明", "建议"], essential_issue_rows) or "当前没有明显基础能力缺口。",
            "",
            "## 已使用卡片",
            "",
            markdown_table(["分组", "卡片类型", "使用次数", "Web Runtime", "原生 Runtime", "总体", "使用场景", "说明"], used_rows) or "当前项目还没有剧情卡片。",
            "",
            "## 需要重点验收",
            "",
            markdown_table(["序号", "级别", "卡片类型", "使用次数", "场景", "说明"], issue_rows) or "当前没有 Runtime 覆盖风险。",
            "",
            "## Runtime 验收清单",
            "",
            markdown_table(["序号", "目标", "级别", "验收项", "相关卡片", "说明"], acceptance_rows) or "当前项目还没有可生成验收清单的剧情卡片。",
            "",
        ]
    )


def build_export_runtime_capability_csv(matrix: dict) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["分组", "卡片类型", "使用次数", "Web Runtime", "原生 Runtime", "总体", "使用场景", "说明"])
    for row in as_list(matrix.get("rows")):
        writer.writerow(
            [
                row.get("group"),
                row.get("type"),
                row.get("usedCount"),
                row.get("webStatusLabel"),
                row.get("nativeStatusLabel"),
                row.get("overallStatusLabel"),
                " / ".join(as_list(row.get("usedSceneNames"))),
                row.get("note"),
            ]
        )
    return "\ufeff" + output.getvalue()


def write_export_runtime_capability_files(target_dir: Path, *, bundle: dict) -> dict:
    matrix = build_export_runtime_capability_matrix(bundle)
    json_path = target_dir / EXPORT_RUNTIME_CAPABILITY_JSON_NAME
    markdown_path = target_dir / EXPORT_RUNTIME_CAPABILITY_REPORT_NAME
    csv_path = target_dir / EXPORT_RUNTIME_CAPABILITY_CSV_NAME
    json_path.write_text(json.dumps(matrix, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(build_export_runtime_capability_markdown(matrix), encoding="utf-8")
    csv_path.write_text(build_export_runtime_capability_csv(matrix), encoding="utf-8")
    return {
        "runtimeCapabilityMatrix": matrix,
        "runtimeCapabilityMatrixName": json_path.name,
        "runtimeCapabilityMatrixPath": str(json_path),
        "runtimeCapabilityReportName": markdown_path.name,
        "runtimeCapabilityReportPath": str(markdown_path),
        "runtimeCapabilityCsvName": csv_path.name,
        "runtimeCapabilityCsvPath": str(csv_path),
        "runtimeCapabilityStatus": get_runtime_capability_digest(matrix)["status"],
        "runtimeCapabilityIssueCount": len(matrix["issues"]),
        "vnEssentialsScore": matrix["essentials"]["summary"]["score"],
        "vnEssentialsIssueCount": matrix["essentials"]["summary"]["issueCount"],
    }


__all__ = [
    "EXPORT_RUNTIME_CAPABILITY_CSV_NAME",
    "EXPORT_RUNTIME_CAPABILITY_JSON_NAME",
    "EXPORT_RUNTIME_CAPABILITY_REPORT_NAME",
    "build_export_runtime_capability_csv",
    "build_export_runtime_capability_markdown",
    "build_export_runtime_capability_matrix",
    "write_export_runtime_capability_files",
]
