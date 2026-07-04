from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path


UNLOCKABLE_CONTENT_MANIFEST_FILE_NAME = "unlockable_content_manifest.json"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def export_clean_text(value: object, fallback: str = "") -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text or fallback


def get_export_asset_list(assets_doc: dict) -> list[dict]:
    assets = assets_doc.get("assets") if isinstance(assets_doc, dict) else []
    return assets if isinstance(assets, list) else []


def build_export_asset_map(assets_doc: dict) -> dict[str, dict]:
    return {
        str(asset.get("id")): asset
        for asset in get_export_asset_list(assets_doc)
        if isinstance(asset, dict) and asset.get("id")
    }


def export_asset_ready(asset: dict | None) -> bool:
    if not isinstance(asset, dict):
        return False
    if asset.get("isMissing") is True or asset.get("fileExists") is False:
        return False
    return bool(asset.get("exportUrl") or asset.get("path") or asset.get("url") or asset.get("fileName"))


def get_export_asset_name(asset: dict | None, fallback: str = "未命名素材") -> str:
    if not isinstance(asset, dict):
        return fallback
    return export_clean_text(asset.get("name") or asset.get("title") or asset.get("fileName") or asset.get("id"), fallback)


def get_export_characters(bundle: dict) -> list[dict]:
    characters_doc = bundle.get("characters") if isinstance(bundle.get("characters"), dict) else {}
    characters = characters_doc.get("characters") if isinstance(characters_doc, dict) else []
    return characters if isinstance(characters, list) else []


def get_export_character_name(character: dict | None, fallback: str = "未命名角色") -> str:
    if not isinstance(character, dict):
        return fallback
    return export_clean_text(
        character.get("displayName") or character.get("name") or character.get("label") or character.get("id"),
        fallback,
    )


def get_export_character_visual_asset_ids(character: dict) -> list[str]:
    candidates: list[object] = [
        character.get("defaultSpriteId"),
        character.get("defaultAssetId"),
        character.get("spriteAssetId"),
        character.get("avatarAssetId"),
    ]
    presentation = character.get("presentation") if isinstance(character.get("presentation"), dict) else {}
    candidates.extend(
        [
            presentation.get("defaultSpriteId"),
            presentation.get("defaultAssetId"),
            presentation.get("fallbackSpriteAssetId"),
            presentation.get("avatarAssetId"),
        ]
    )
    for expression in character.get("expressions") or []:
        if isinstance(expression, dict):
            candidates.extend([expression.get("assetId"), expression.get("spriteAssetId")])
    return [str(asset_id) for asset_id in candidates if export_clean_text(asset_id)]


def iter_export_scene_records(bundle: dict) -> list[dict]:
    records: list[dict] = []
    for chapter_index, chapter in enumerate(bundle.get("chapters") or []):
        if not isinstance(chapter, dict):
            continue
        chapter_id = export_clean_text(chapter.get("id") or chapter.get("chapterId"), f"chapter_{chapter_index + 1}")
        chapter_name = export_clean_text(chapter.get("name") or chapter.get("title"), f"第 {chapter_index + 1} 章")
        for scene_index, scene in enumerate(chapter.get("scenes") or []):
            if not isinstance(scene, dict):
                continue
            scene_id = export_clean_text(scene.get("id"), f"scene_{chapter_index + 1}_{scene_index + 1}")
            records.append(
                {
                    "chapter": chapter,
                    "chapterId": chapter_id,
                    "chapterName": chapter_name,
                    "chapterIndex": chapter_index,
                    "scene": scene,
                    "sceneId": scene_id,
                    "sceneName": export_clean_text(scene.get("name"), scene_id),
                    "sceneIndex": scene_index,
                }
            )
    return records


def iter_export_block_records(bundle: dict) -> list[dict]:
    records: list[dict] = []
    for scene_record in iter_export_scene_records(bundle):
        for block_index, block in enumerate(scene_record["scene"].get("blocks") or []):
            if isinstance(block, dict):
                records.append({**scene_record, "block": block, "blockIndex": block_index})
    return records


def make_unlockable_issue(severity: str, code: str, title: str, detail: str, **context: object) -> dict:
    return {
        "severity": severity,
        "code": code,
        "title": title,
        "detail": detail,
        **{key: value for key, value in context.items() if value not in (None, "")},
    }


def make_unlockable_entry(
    entry_id: str,
    title: str,
    *,
    status: str = "ready",
    detail: str = "",
    source: str = "",
    meta: dict | None = None,
    issues: list[dict] | None = None,
) -> dict:
    return {
        "id": export_clean_text(entry_id, title),
        "title": export_clean_text(title, "未命名条目"),
        "status": status,
        "detail": export_clean_text(detail),
        "source": export_clean_text(source),
        "meta": meta or {},
        "issues": issues or [],
    }


def build_unlockable_group(group_id: str, label: str, entries: list[dict], detail: str = "") -> dict:
    ready_count = sum(1 for entry in entries if entry.get("status") == "ready")
    missing_count = sum(1 for entry in entries if entry.get("status") in {"missing", "warn"})
    total_count = len(entries)
    return {
        "id": group_id,
        "label": label,
        "detail": detail,
        "totalCount": total_count,
        "readyCount": ready_count,
        "missingCount": missing_count,
        "readinessPercent": round((ready_count / total_count) * 100) if total_count else 0,
        "status": "empty" if total_count == 0 else "warn" if missing_count else "ready",
        "entries": entries,
        "issues": [issue for entry in entries for issue in entry.get("issues", [])],
    }


def collect_export_asset_unlockable_group(
    assets_doc: dict,
    asset_type: str,
    group_id: str,
    label: str,
    detail: str,
) -> dict:
    entries: list[dict] = []
    for asset in get_export_asset_list(assets_doc):
        if str(asset.get("type") or "") != asset_type:
            continue
        ready = export_asset_ready(asset)
        issues = []
        if not ready:
            issues.append(
                make_unlockable_issue(
                    "warn",
                    "unlockable_asset_missing",
                    f"{label}素材缺失",
                    f"{get_export_asset_name(asset)} 已进入导出包清单，但没有可用文件。",
                    groupId=group_id,
                    assetId=asset.get("id"),
                )
            )
        entries.append(
            make_unlockable_entry(
                str(asset.get("id") or asset.get("name") or len(entries) + 1),
                get_export_asset_name(asset),
                status="ready" if ready else "missing",
                detail=f"{asset_type} · {'已复制到导出包' if ready else '缺文件'}",
                source=str(asset.get("exportUrl") or asset.get("path") or ""),
                meta={"assetId": asset.get("id"), "type": asset_type},
                issues=issues,
            )
        )
    return build_unlockable_group(group_id, label, entries, detail)


def get_export_block_asset_id(block: dict) -> str:
    for key in (
        "assetId",
        "backgroundAssetId",
        "imageAssetId",
        "cgAssetId",
        "musicAssetId",
        "bgmAssetId",
        "videoAssetId",
        "scene3dAssetId",
    ):
        value = export_clean_text(block.get(key))
        if value:
            return value
    return ""


def get_export_block_speaker_id(block: dict) -> str:
    return export_clean_text(block.get("speakerId") or block.get("characterId") or block.get("speaker") or block.get("character"))


def collect_export_voice_replay_group(bundle: dict, assets_doc: dict) -> dict:
    asset_map = build_export_asset_map(assets_doc)
    entries: list[dict] = []
    for record in iter_export_block_records(bundle):
        block = record["block"]
        voice_asset_id = export_clean_text(block.get("voiceAssetId") or block.get("voiceId") or block.get("voice"))
        if not voice_asset_id:
            continue
        asset = asset_map.get(voice_asset_id)
        ready = export_asset_ready(asset)
        issues = []
        if not ready:
            issues.append(
                make_unlockable_issue(
                    "warn",
                    "unlockable_voice_missing",
                    "语音回听文件缺失",
                    f"{record['chapterName']} / {record['sceneName']} 有语音回听条目，但语音文件不可用。",
                    groupId="voice_replay",
                    sceneId=record["sceneId"],
                    blockId=block.get("id"),
                    assetId=voice_asset_id,
                )
            )
        text = export_clean_text(block.get("text") or block.get("content"), "语音台词")
        entries.append(
            make_unlockable_entry(
                f"{record['sceneId']}:{block.get('id') or record['blockIndex']}:voice",
                text[:46] + ("..." if len(text) > 46 else ""),
                status="ready" if ready else "missing",
                detail=f"{record['chapterName']} · {record['sceneName']}",
                source=get_export_asset_name(asset, voice_asset_id),
                meta={"voiceAssetId": voice_asset_id, "sceneId": record["sceneId"], "blockId": block.get("id")},
                issues=issues,
            )
        )
    return build_unlockable_group("voice_replay", "语音回听", entries, "导出包中绑定到台词的语音片段。")


def collect_export_character_archive_group(bundle: dict, assets_doc: dict) -> dict:
    asset_map = build_export_asset_map(assets_doc)
    seen_character_ids = {get_export_block_speaker_id(record["block"]) for record in iter_export_block_records(bundle)}
    entries: list[dict] = []
    for character in get_export_characters(bundle):
        character_id = export_clean_text(character.get("id"))
        asset_ids = get_export_character_visual_asset_ids(character)
        ready_visual_count = sum(1 for asset_id in asset_ids if export_asset_ready(asset_map.get(asset_id)))
        ready = ready_visual_count > 0 if asset_ids else False
        issues = []
        if not ready:
            issues.append(
                make_unlockable_issue(
                    "warn",
                    "unlockable_character_visual_missing",
                    "角色图鉴视觉素材缺失",
                    f"{get_export_character_name(character)} 没有可用于图鉴展示的导出立绘或头像。",
                    groupId="character_archive",
                    characterId=character_id,
                )
            )
        entries.append(
            make_unlockable_entry(
                character_id,
                get_export_character_name(character),
                status="ready" if ready else "missing",
                detail=f"{'已在剧情登场' if character_id in seen_character_ids else '暂未登场'} · 视觉素材 {ready_visual_count}/{max(len(asset_ids), 1)}",
                source=", ".join(asset_ids),
                meta={"characterId": character_id, "visualAssetCount": len(asset_ids), "readyVisualCount": ready_visual_count},
                issues=issues,
            )
        )
    return build_unlockable_group("character_archive", "角色图鉴", entries, "导出包内角色资料和可展示视觉素材。")


def collect_export_location_archive_group(bundle: dict, assets_doc: dict) -> dict:
    asset_map = build_export_asset_map(assets_doc)
    location_usage: dict[str, set[str]] = {}
    for record in iter_export_block_records(bundle):
        block_type = str(record["block"].get("type") or "")
        if block_type not in {"background", "scene3d", "video_play"}:
            continue
        asset_id = get_export_block_asset_id(record["block"])
        if asset_id:
            location_usage.setdefault(asset_id, set()).add(record["sceneName"])
    entries: list[dict] = []
    for asset_id, scene_names in sorted(location_usage.items()):
        asset = asset_map.get(asset_id)
        ready = export_asset_ready(asset)
        issues = []
        if not ready:
            issues.append(
                make_unlockable_issue(
                    "warn",
                    "unlockable_location_asset_missing",
                    "地点图鉴素材缺失",
                    f"{get_export_asset_name(asset, asset_id)} 已作为地点使用，但导出包没有可用文件。",
                    groupId="location_archive",
                    assetId=asset_id,
                )
            )
        entries.append(
            make_unlockable_entry(
                asset_id,
                get_export_asset_name(asset, asset_id),
                status="ready" if ready else "missing",
                detail=f"{len(scene_names)} 个场景",
                source=" / ".join(sorted(scene_names)[:3]),
                meta={"assetId": asset_id, "sceneCount": len(scene_names)},
                issues=issues,
            )
        )
    return build_unlockable_group("location_archive", "地点图鉴", entries, "导出包中可回顾的背景和地点。")


def collect_export_narration_archive_group(bundle: dict) -> dict:
    entries = [
        make_unlockable_entry(
            f"{record['sceneId']}:{record['block'].get('id') or record['blockIndex']}:narration",
            (text := export_clean_text(record["block"].get("text") or record["block"].get("content")))[:46]
            + ("..." if len(text) > 46 else ""),
            detail=f"{record['chapterName']} · {record['sceneName']}",
            source=text,
            meta={"sceneId": record["sceneId"], "blockId": record["block"].get("id")},
        )
        for record in iter_export_block_records(bundle)
        if str(record["block"].get("type") or "") == "narration"
        and export_clean_text(record["block"].get("text") or record["block"].get("content"))
    ]
    return build_unlockable_group("narration_archive", "旁白档案", entries, "导出包中可回顾的旁白条目。")


def collect_export_relationship_archive_group(bundle: dict) -> dict:
    character_map = {
        export_clean_text(character.get("id")): character
        for character in get_export_characters(bundle)
        if export_clean_text(character.get("id"))
    }
    pairs: dict[tuple[str, str], set[str]] = {}
    for scene_record in iter_export_scene_records(bundle):
        speakers = sorted(
            {
                get_export_block_speaker_id(block)
                for block in scene_record["scene"].get("blocks") or []
                if isinstance(block, dict) and get_export_block_speaker_id(block)
            }
        )
        for left_index, left_id in enumerate(speakers):
            for right_id in speakers[left_index + 1 :]:
                pairs.setdefault((left_id, right_id), set()).add(scene_record["sceneName"])
    entries = [
        make_unlockable_entry(
            f"{left_id}:{right_id}",
            f"{get_export_character_name(character_map.get(left_id), left_id)} / {get_export_character_name(character_map.get(right_id), right_id)}",
            detail=f"同场 {len(scene_names)} 次",
            source=" / ".join(sorted(scene_names)[:3]),
            meta={"leftId": left_id, "rightId": right_id, "sceneCount": len(scene_names)},
        )
        for (left_id, right_id), scene_names in sorted(pairs.items())
    ]
    return build_unlockable_group("relationship_archive", "关系图鉴", entries, "导出包中根据同场剧情推断的角色关系。")


def collect_export_chapter_replay_group(bundle: dict) -> dict:
    entries: list[dict] = []
    for index, chapter in enumerate(bundle.get("chapters") or []):
        if not isinstance(chapter, dict):
            continue
        scene_count = len(chapter.get("scenes") or [])
        entries.append(
            make_unlockable_entry(
                export_clean_text(chapter.get("id") or chapter.get("chapterId"), f"chapter_{index + 1}"),
                export_clean_text(chapter.get("name") or chapter.get("title"), f"第 {index + 1} 章"),
                status="ready" if scene_count else "warn",
                detail=f"{scene_count} 个场景",
                source=export_clean_text(chapter.get("summary") or chapter.get("description")),
                meta={"sceneCount": scene_count},
            )
        )
    return build_unlockable_group("chapter_replay", "章节回放", entries, "导出包中可回放的章节入口。")


def collect_export_scene_targets(block: dict) -> list[str]:
    targets: list[str] = []
    for key in ("targetSceneId", "sceneId", "trueTargetSceneId", "falseTargetSceneId", "nextSceneId"):
        value = export_clean_text(block.get(key))
        if value:
            targets.append(value)
    for collection_key in ("choices", "options", "branches"):
        for item in block.get(collection_key) or []:
            if isinstance(item, dict):
                for key in ("targetSceneId", "sceneId", "trueTargetSceneId", "falseTargetSceneId"):
                    value = export_clean_text(item.get(key))
                    if value:
                        targets.append(value)
    return [target for target in targets if target and target != "__continue__"]


def build_export_scene_graph(bundle: dict) -> tuple[dict[str, set[str]], set[str]]:
    records = iter_export_scene_records(bundle)
    by_chapter: dict[str, list[dict]] = {}
    for record in records:
        by_chapter.setdefault(record["chapterId"], []).append(record)

    graph: dict[str, set[str]] = {record["sceneId"]: set() for record in records}
    ending_candidates: set[str] = set()
    for record in records:
        scene_id = record["sceneId"]
        blocks = [block for block in record["scene"].get("blocks") or [] if isinstance(block, dict)]
        explicit_targets = {target for block in blocks for target in collect_export_scene_targets(block)}
        if explicit_targets:
            graph.setdefault(scene_id, set()).update(explicit_targets)
        elif any(str(block.get("type") or "") == "credits_roll" for block in blocks):
            ending_candidates.add(scene_id)
        else:
            chapter_records = sorted(by_chapter.get(record["chapterId"], []), key=lambda item: item["sceneIndex"])
            next_records = [item for item in chapter_records if item["sceneIndex"] > record["sceneIndex"]]
            if next_records:
                graph.setdefault(scene_id, set()).add(next_records[0]["sceneId"])
            else:
                ending_candidates.add(scene_id)
    return graph, ending_candidates


def get_export_reachable_scene_ids(bundle: dict, graph: dict[str, set[str]]) -> set[str]:
    records = iter_export_scene_records(bundle)
    if not records:
        return set()
    entry_scene_id = export_clean_text(bundle.get("project", {}).get("entrySceneId"), records[0]["sceneId"])
    reachable = {entry_scene_id}
    queue = [entry_scene_id]
    while queue:
        scene_id = queue.pop(0)
        for target_id in graph.get(scene_id, set()):
            if target_id in graph and target_id not in reachable:
                reachable.add(target_id)
                queue.append(target_id)
    return reachable


def collect_export_ending_collection_group(bundle: dict) -> dict:
    graph, ending_candidates = build_export_scene_graph(bundle)
    reachable_scene_ids = get_export_reachable_scene_ids(bundle, graph)
    scene_records = {record["sceneId"]: record for record in iter_export_scene_records(bundle)}
    entries: list[dict] = []
    for scene_id in sorted(ending_candidates):
        record = scene_records.get(scene_id)
        if not record:
            continue
        reachable = scene_id in reachable_scene_ids
        issues = []
        if not reachable:
            issues.append(
                make_unlockable_issue(
                    "warn",
                    "unlockable_ending_unreachable",
                    "结局当前不可达",
                    f"{record['sceneName']} 被识别为结局，但从入口场景暂时无法抵达。",
                    groupId="ending_collection",
                    sceneId=scene_id,
                )
            )
        entries.append(
            make_unlockable_entry(
                scene_id,
                record["sceneName"],
                status="ready" if reachable else "warn",
                detail="路线图可抵达" if reachable else "入口场景暂不可达",
                source=record["chapterName"],
                meta={"sceneId": scene_id, "reachable": reachable},
                issues=issues,
            )
        )
    return build_unlockable_group("ending_collection", "结局收集", entries, "导出包中可抵达或需复查的结局入口。")


def collect_export_achievement_group(groups: list[dict], bundle: dict) -> dict:
    has_choice = any(str(record["block"].get("type") or "") == "choice" for record in iter_export_block_records(bundle))
    scene_count = len(iter_export_scene_records(bundle))
    entries = [
        make_unlockable_entry(
            "story_start",
            "首次进入剧情",
            status="ready" if scene_count else "warn",
            detail="玩家开始阅读项目。",
        ),
        make_unlockable_entry(
            "first_choice",
            "首次做出选择",
            status="ready" if has_choice else "warn",
            detail="玩家遇到至少一个选项分支。",
        ),
    ]
    for group in groups:
        if group.get("totalCount", 0) > 0:
            entries.append(
                make_unlockable_entry(
                    f"complete_{group['id']}",
                    f"完成{group['label']}",
                    status="ready" if group.get("status") == "ready" else "warn",
                    detail=f"{group.get('readyCount', 0)}/{group.get('totalCount', 0)} 个条目可用。",
                    meta={"groupId": group["id"]},
                )
            )
    return build_unlockable_group("achievements", "成就集合", entries, "导出包内可推导的成就覆盖。")


def build_export_unlockable_content_manifest(bundle: dict, assets_doc: dict) -> dict:
    groups = [
        collect_export_asset_unlockable_group(assets_doc, "cg", "extra_cg", "CG 图鉴", "导出包中的 CG 回想素材。"),
        collect_export_asset_unlockable_group(assets_doc, "bgm", "music_room", "音乐回想", "导出包中的音乐回想素材。"),
        collect_export_voice_replay_group(bundle, assets_doc),
        collect_export_character_archive_group(bundle, assets_doc),
        collect_export_location_archive_group(bundle, assets_doc),
        collect_export_narration_archive_group(bundle),
        collect_export_relationship_archive_group(bundle),
        collect_export_chapter_replay_group(bundle),
        collect_export_ending_collection_group(bundle),
    ]
    groups.append(collect_export_achievement_group(groups, bundle))
    issues = [issue for group in groups for issue in group.get("issues", [])]
    total_entry_count = sum(group.get("totalCount", 0) for group in groups)
    ready_entry_count = sum(group.get("readyCount", 0) for group in groups)
    missing_entry_count = sum(group.get("missingCount", 0) for group in groups)
    ending_group = next((group for group in groups if group.get("id") == "ending_collection"), {})
    return {
        "formatVersion": 1,
        "generatedAt": now_iso(),
        "projectTitle": export_clean_text(bundle.get("project", {}).get("title"), "Canvasia Project"),
        "groups": groups,
        "issues": issues,
        "summary": {
            "groupCount": len(groups),
            "activeGroupCount": sum(1 for group in groups if group.get("totalCount", 0) > 0),
            "totalEntryCount": total_entry_count,
            "readyEntryCount": ready_entry_count,
            "missingEntryCount": missing_entry_count,
            "achievementCount": next((group.get("totalCount", 0) for group in groups if group.get("id") == "achievements"), 0),
            "endingCount": ending_group.get("totalCount", 0),
            "reachableEndingCount": ending_group.get("readyCount", 0),
            "warningCount": sum(1 for issue in issues if issue.get("severity") == "warn"),
            "readinessPercent": round((ready_entry_count / total_entry_count) * 100) if total_entry_count else 0,
        },
    }


def write_unlockable_content_manifest_file(target_dir: Path, manifest: dict) -> Path:
    path = target_dir / UNLOCKABLE_CONTENT_MANIFEST_FILE_NAME
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


__all__ = [
    "UNLOCKABLE_CONTENT_MANIFEST_FILE_NAME",
    "build_export_unlockable_content_manifest",
    "write_unlockable_content_manifest_file",
]
