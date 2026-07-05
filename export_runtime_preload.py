from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path


RUNTIME_PRELOAD_MANIFEST_FILE_NAME = "runtime_preload_manifest.json"
RUNTIME_PRELOAD_REPORT_FILE_NAME = "RUNTIME_PRELOAD_REPORT.md"
RUNTIME_PRELOAD_FORMAT_VERSION = 1

IMAGE_ASSET_TYPES = {"background", "sprite", "cg", "ui"}
AUDIO_ASSET_TYPES = {"bgm", "sfx", "voice"}
VIDEO_ASSET_TYPES = {"video"}
PRELOADABLE_ASSET_TYPES = IMAGE_ASSET_TYPES | AUDIO_ASSET_TYPES | VIDEO_ASSET_TYPES
SIZE_UNIT_BYTES = {
    "b": 1,
    "byte": 1,
    "bytes": 1,
    "kb": 1024,
    "kib": 1024,
    "mb": 1024 * 1024,
    "mib": 1024 * 1024,
    "gb": 1024 * 1024 * 1024,
    "gib": 1024 * 1024 * 1024,
}
SIZE_VALUE_PATTERN = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)\s*([A-Za-z]+)?\s*$")


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def safe_text(value: object) -> str:
    return str(value or "").strip()


def normalize_asset_size_bytes(asset: dict | None) -> int:
    source = asset if isinstance(asset, dict) else {}
    for key in ("fileSizeBytes", "sizeBytes", "byteSize", "fileSize", "size"):
        value = source.get(key)
        if isinstance(value, bool) or value in (None, ""):
            continue
        if isinstance(value, (int, float)):
            return max(0, int(value))
        raw_value = safe_text(value).replace(",", "")
        if raw_value.isdigit():
            return max(0, int(raw_value))
        match = SIZE_VALUE_PATTERN.match(raw_value)
        if match:
            amount = float(match.group(1))
            unit = (match.group(2) or "b").lower()
            multiplier = SIZE_UNIT_BYTES.get(unit)
            if multiplier:
                return max(0, int(amount * multiplier))
    return 0


def format_bytes(size_bytes: object) -> str:
    try:
        size = max(0, int(size_bytes or 0))
    except (TypeError, ValueError):
        size = 0
    units = ["B", "KB", "MB", "GB"]
    value = float(size)
    unit = units[0]
    for candidate in units:
        unit = candidate
        if value < 1024 or candidate == units[-1]:
            break
        value /= 1024
    if unit == "B":
        return f"{int(value)} B"
    return f"{value:.1f} {unit}"


def get_ordered_scenes(bundle: dict) -> list[dict]:
    project = bundle.get("project") if isinstance(bundle.get("project"), dict) else {}
    chapters = bundle.get("chapters") if isinstance(bundle.get("chapters"), list) else []
    chapter_order = [safe_text(item) for item in project.get("chapterOrder") or [] if safe_text(item)]
    chapter_map = {safe_text(chapter.get("chapterId")): chapter for chapter in chapters if isinstance(chapter, dict)}
    ordered_chapters = [
        chapter_map[chapter_id]
        for chapter_id in chapter_order
        if chapter_id in chapter_map
    ]
    ordered_chapters.extend(
        chapter
        for chapter in chapters
        if isinstance(chapter, dict) and safe_text(chapter.get("chapterId")) not in chapter_order
    )

    ordered_scenes: list[dict] = []
    for chapter_index, chapter in enumerate(ordered_chapters):
        scenes = [scene for scene in chapter.get("scenes") or [] if isinstance(scene, dict)]
        scene_order = [safe_text(item) for item in chapter.get("sceneOrder") or [] if safe_text(item)]
        scene_map = {safe_text(scene.get("id")): scene for scene in scenes}
        chapter_scenes = [
            scene_map[scene_id]
            for scene_id in scene_order
            if scene_id in scene_map
        ]
        chapter_scenes.extend(scene for scene in scenes if safe_text(scene.get("id")) not in scene_order)
        for scene_index, scene in enumerate(chapter_scenes):
            ordered_scenes.append(
                {
                    **scene,
                    "__chapterId": safe_text(chapter.get("chapterId")),
                    "__chapterName": safe_text(chapter.get("name")),
                    "__chapterIndex": chapter_index,
                    "__sceneIndex": len(ordered_scenes),
                    "__sceneIndexInChapter": scene_index,
                }
            )
    return ordered_scenes


def get_character_sprite_asset_id(characters_by_id: dict[str, dict], character_id: object, expression_id: object) -> str:
    character = characters_by_id.get(safe_text(character_id))
    if not isinstance(character, dict):
        return ""

    expression_key = safe_text(expression_id)
    for expression in character.get("expressions") or []:
        if isinstance(expression, dict) and safe_text(expression.get("id")) == expression_key:
            sprite_asset_id = safe_text(expression.get("spriteAssetId") or expression.get("assetId"))
            if sprite_asset_id:
                return sprite_asset_id

    presentation = character.get("presentation") if isinstance(character.get("presentation"), dict) else {}
    return (
        safe_text(character.get("defaultSpriteId"))
        or safe_text(presentation.get("fallbackSpriteAssetId"))
        or safe_text(presentation.get("defaultSpriteId"))
    )


def get_entry_scene_id(bundle: dict, ordered_scenes: list[dict]) -> str:
    project = bundle.get("project") if isinstance(bundle.get("project"), dict) else {}
    explicit_entry = safe_text(project.get("entrySceneId"))
    if explicit_entry:
        return explicit_entry
    return safe_text(ordered_scenes[0].get("id")) if ordered_scenes else ""


def get_preload_phase(scene_index: int, block_index: int, scene_id: str, entry_scene_id: str) -> str:
    if scene_id == entry_scene_id and block_index <= 12:
        return "critical"
    if scene_index <= 2:
        return "early"
    return "deferred"


def get_phase_priority(phase: str) -> int:
    return {
        "critical": 100,
        "early": 72,
        "deferred": 38,
        "library": 18,
    }.get(phase, 10)


def build_runtime_preload_manifest(
    bundle: dict,
    assets_doc: dict,
    *,
    max_entries: int = 96,
) -> dict:
    assets = [asset for asset in assets_doc.get("assets", []) if isinstance(asset, dict)]
    assets_by_id = {safe_text(asset.get("id")): asset for asset in assets if safe_text(asset.get("id"))}
    characters = bundle.get("characters", {}).get("characters", [])
    characters_by_id = {
        safe_text(character.get("id")): character
        for character in characters
        if isinstance(character, dict) and safe_text(character.get("id"))
    }
    ordered_scenes = get_ordered_scenes(bundle)
    entry_scene_id = get_entry_scene_id(bundle, ordered_scenes)
    candidates: dict[str, dict] = {}
    sequence = 0

    def add_asset(
        asset_id: object,
        *,
        phase: str,
        reason: str,
        scene: dict | None = None,
        block: dict | None = None,
        bonus: int = 0,
    ) -> None:
        nonlocal sequence
        safe_asset_id = safe_text(asset_id)
        if not safe_asset_id or safe_asset_id not in assets_by_id:
            return

        asset = assets_by_id[safe_asset_id]
        asset_type = safe_text(asset.get("type"))
        export_url = safe_text(asset.get("exportUrl"))
        if asset_type not in PRELOADABLE_ASSET_TYPES or not export_url or asset.get("isMissing"):
            return

        size_bytes = normalize_asset_size_bytes(asset)
        priority = get_phase_priority(phase) + bonus
        existing = candidates.get(safe_asset_id)
        if existing and existing["priority"] >= priority:
            existing.setdefault("reasons", [])
            if reason and reason not in existing["reasons"]:
                existing["reasons"].append(reason)
            return

        candidates[safe_asset_id] = {
            "assetId": safe_asset_id,
            "type": asset_type,
            "name": safe_text(asset.get("name")) or safe_asset_id,
            "url": export_url,
            "sizeBytes": size_bytes,
            "sizeLabel": format_bytes(size_bytes) if size_bytes else "Unknown",
            "phase": phase,
            "priority": priority,
            "sceneId": safe_text((scene or {}).get("id")),
            "sceneName": safe_text((scene or {}).get("name")),
            "blockId": safe_text((block or {}).get("id")),
            "reason": reason,
            "reasons": [reason] if reason else [],
            "order": sequence,
        }
        sequence += 1

    for scene in ordered_scenes:
        scene_index = int(scene.get("__sceneIndex") or 0)
        scene_id = safe_text(scene.get("id"))
        for block_index, block in enumerate(scene.get("blocks") or []):
            if not isinstance(block, dict):
                continue
            block_type = safe_text(block.get("type"))
            phase = get_preload_phase(scene_index, block_index, scene_id, entry_scene_id)
            scene_bonus = max(0, 12 - block_index) if phase == "critical" else max(0, 4 - scene_index)

            if block_type in {"background", "music_play", "sfx_play", "video_play"}:
                add_asset(
                    block.get("assetId"),
                    phase=phase,
                    reason=f"{safe_text(scene.get('name')) or scene_id} / {block_type}",
                    scene=scene,
                    block=block,
                    bonus=scene_bonus,
                )

            if block_type in {"dialogue", "narration"}:
                add_asset(
                    block.get("voiceAssetId"),
                    phase=phase,
                    reason=f"{safe_text(scene.get('name')) or scene_id} / voice",
                    scene=scene,
                    block=block,
                    bonus=scene_bonus,
                )

            if block_type in {"character_show", "dialogue"}:
                sprite_asset_id = get_character_sprite_asset_id(
                    characters_by_id,
                    block.get("characterId") or block.get("speakerId"),
                    block.get("expressionId"),
                )
                add_asset(
                    sprite_asset_id,
                    phase=phase,
                    reason=f"{safe_text(scene.get('name')) or scene_id} / sprite",
                    scene=scene,
                    block=block,
                    bonus=scene_bonus,
                )

    for asset in assets:
        asset_type = safe_text(asset.get("type"))
        if asset_type in {"background", "cg", "bgm", "ui"} and asset.get("favorite"):
            add_asset(
                asset.get("id"),
                phase="library",
                reason="favorite asset",
                bonus=8,
            )

    entries = sorted(
        candidates.values(),
        key=lambda item: (-int(item.get("priority") or 0), int(item.get("order") or 0), item.get("assetId") or ""),
    )[:max_entries]
    for index, entry in enumerate(entries):
        entry["preloadIndex"] = index + 1

    type_counts: dict[str, int] = {}
    phase_counts: dict[str, int] = {}
    type_bytes: dict[str, int] = {}
    phase_bytes: dict[str, int] = {}
    for entry in entries:
        asset_type = entry["type"]
        phase = entry["phase"]
        size_bytes = int(entry.get("sizeBytes") or 0)
        type_counts[asset_type] = type_counts.get(asset_type, 0) + 1
        phase_counts[phase] = phase_counts.get(phase, 0) + 1
        type_bytes[asset_type] = type_bytes.get(asset_type, 0) + size_bytes
        phase_bytes[phase] = phase_bytes.get(phase, 0) + size_bytes

    total_bytes = sum(phase_bytes.values())
    image_bytes = sum(type_bytes.get(asset_type, 0) for asset_type in IMAGE_ASSET_TYPES)
    audio_bytes = sum(type_bytes.get(asset_type, 0) for asset_type in AUDIO_ASSET_TYPES)
    video_bytes = sum(type_bytes.get(asset_type, 0) for asset_type in VIDEO_ASSET_TYPES)

    return {
        "formatVersion": RUNTIME_PRELOAD_FORMAT_VERSION,
        "generatedAt": now_iso(),
        "entrySceneId": entry_scene_id,
        "summary": {
            "totalEntries": len(entries),
            "criticalEntries": phase_counts.get("critical", 0),
            "earlyEntries": phase_counts.get("early", 0),
            "deferredEntries": phase_counts.get("deferred", 0),
            "libraryEntries": phase_counts.get("library", 0),
            "imageEntries": sum(type_counts.get(asset_type, 0) for asset_type in IMAGE_ASSET_TYPES),
            "audioEntries": sum(type_counts.get(asset_type, 0) for asset_type in AUDIO_ASSET_TYPES),
            "videoEntries": sum(type_counts.get(asset_type, 0) for asset_type in VIDEO_ASSET_TYPES),
            "totalBytes": total_bytes,
            "totalBytesLabel": format_bytes(total_bytes),
            "criticalBytes": phase_bytes.get("critical", 0),
            "criticalBytesLabel": format_bytes(phase_bytes.get("critical", 0)),
            "earlyBytes": phase_bytes.get("early", 0),
            "earlyBytesLabel": format_bytes(phase_bytes.get("early", 0)),
            "deferredBytes": phase_bytes.get("deferred", 0),
            "deferredBytesLabel": format_bytes(phase_bytes.get("deferred", 0)),
            "libraryBytes": phase_bytes.get("library", 0),
            "libraryBytesLabel": format_bytes(phase_bytes.get("library", 0)),
            "imageBytes": image_bytes,
            "imageBytesLabel": format_bytes(image_bytes),
            "audioBytes": audio_bytes,
            "audioBytesLabel": format_bytes(audio_bytes),
            "videoBytes": video_bytes,
            "videoBytesLabel": format_bytes(video_bytes),
        },
        "largestEntries": sorted(
            [
                {
                    "assetId": entry.get("assetId"),
                    "name": entry.get("name"),
                    "type": entry.get("type"),
                    "phase": entry.get("phase"),
                    "sizeBytes": int(entry.get("sizeBytes") or 0),
                    "sizeLabel": entry.get("sizeLabel") or format_bytes(entry.get("sizeBytes")),
                }
                for entry in entries
                if int(entry.get("sizeBytes") or 0) > 0
            ],
            key=lambda item: int(item.get("sizeBytes") or 0),
            reverse=True,
        )[:10],
        "entries": entries,
    }


def build_runtime_preload_report(manifest: dict) -> str:
    summary = manifest.get("summary") if isinstance(manifest.get("summary"), dict) else {}
    entries = manifest.get("entries") if isinstance(manifest.get("entries"), list) else []
    lines = [
        "# Runtime Preload Report",
        "",
        "This report records the assets Canvasia prepared for smoother first play.",
        "",
        "## Summary",
        "",
        f"- Total entries: {summary.get('totalEntries', 0)}",
        f"- Critical first-play entries: {summary.get('criticalEntries', 0)}",
        f"- Early route entries: {summary.get('earlyEntries', 0)}",
        f"- Deferred route entries: {summary.get('deferredEntries', 0)}",
        f"- Total preload size: {summary.get('totalBytesLabel', '0 B')}",
        f"- Critical first-play size: {summary.get('criticalBytesLabel', '0 B')}",
        f"- Early route size: {summary.get('earlyBytesLabel', '0 B')}",
        f"- Images: {summary.get('imageEntries', 0)}",
        f"- Audio: {summary.get('audioEntries', 0)}",
        f"- Video: {summary.get('videoEntries', 0)}",
        "",
        "## Preload Queue",
        "",
    ]
    if not entries:
        lines.append("- No preloadable runtime assets were found in this export.")
    else:
        for entry in entries[:40]:
            lines.append(
                "- "
                f"{entry.get('preloadIndex')}. "
                f"`{entry.get('assetId')}` "
                f"({entry.get('type')} / {entry.get('phase')}) "
                f"{entry.get('sizeLabel') or 'Unknown'} "
                f"- {entry.get('reason') or 'runtime asset'}"
            )
        if len(entries) > 40:
            lines.append(f"- ...and {len(entries) - 40} more entries.")

    largest_entries = manifest.get("largestEntries") if isinstance(manifest.get("largestEntries"), list) else []
    if largest_entries:
        lines.extend(["", "## Largest Preload Entries", ""])
        for entry in largest_entries[:10]:
            lines.append(
                "- "
                f"`{entry.get('assetId')}` "
                f"({entry.get('type')} / {entry.get('phase')}) "
                f"{entry.get('sizeLabel') or format_bytes(entry.get('sizeBytes'))}"
            )

    lines.append("")
    return "\n".join(lines)


def write_runtime_preload_files(build_dir: Path, manifest: dict) -> dict:
    manifest_path = build_dir / RUNTIME_PRELOAD_MANIFEST_FILE_NAME
    report_path = build_dir / RUNTIME_PRELOAD_REPORT_FILE_NAME
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(build_runtime_preload_report(manifest), encoding="utf-8")
    return {
        "runtimePreloadManifestName": manifest_path.name,
        "runtimePreloadManifestPath": str(manifest_path),
        "runtimePreloadReportName": report_path.name,
        "runtimePreloadReportPath": str(report_path),
    }
