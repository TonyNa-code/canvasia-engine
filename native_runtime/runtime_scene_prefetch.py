from __future__ import annotations

try:
    from .runtime_preload import RUNTIME_PRELOAD_SUPPORTED_TYPES, clamp_int, normalize_size_bytes
except ImportError:  # pragma: no cover - exported native packages import from the same directory.
    from runtime_preload import RUNTIME_PRELOAD_SUPPORTED_TYPES, clamp_int, normalize_size_bytes


DIRECT_ASSET_BLOCK_TYPES = {
    "background",
    "music_play",
    "sfx_play",
    "video_play",
    "particle_effect",
}
CHOICE_CONTINUE_TARGET = "__continue__"
PREFETCH_PHASE_RANKS = {
    "critical": 0,
    "early": 1,
    "deferred": 2,
    "library": 3,
}


def to_list(value: object) -> list:
    return value if isinstance(value, list) else []


def clean_text(value: object) -> str:
    return str(value or "").strip()


def get_from_collection(collection: object, item_id: object) -> dict | None:
    key = clean_text(item_id)
    if not key:
        return None
    if isinstance(collection, dict):
        item = collection.get(key)
        return item if isinstance(item, dict) else None
    if isinstance(collection, list):
        for item in collection:
            if isinstance(item, dict) and clean_text(item.get("id")) == key:
                return item
    return None


def get_scene_blocks(scene: dict | None) -> list[dict]:
    return [block for block in to_list((scene or {}).get("blocks")) if isinstance(block, dict)]


def get_asset_type(asset: dict | None) -> str:
    asset_type = clean_text((asset or {}).get("type"))
    return asset_type if asset_type in RUNTIME_PRELOAD_SUPPORTED_TYPES else ""


def get_asset_url(asset: dict | None) -> str:
    source = asset or {}
    return clean_text(source.get("exportUrl") or source.get("publicPath") or source.get("url"))


def get_asset_size_bytes(asset: dict | None) -> int:
    source = asset or {}
    if "fileSizeBytes" in source:
        return normalize_size_bytes(source.get("fileSizeBytes"))
    if "sizeBytes" in source:
        return normalize_size_bytes(source.get("sizeBytes"))
    return normalize_size_bytes(source.get("byteSize"))


def get_preload_reason(block: dict | None, fallback: str = "路线预取") -> str:
    block_type = clean_text((block or {}).get("type"))
    if block_type == "background":
        return "即将切换背景"
    if block_type == "character_show":
        return "即将显示立绘"
    if block_type == "dialogue":
        return "即将显示角色或播放语音"
    if block_type == "narration":
        return "即将播放旁白语音"
    if block_type == "music_play":
        return "即将切换 BGM"
    if block_type == "sfx_play":
        return "即将播放音效"
    if block_type == "video_play":
        return "即将播放视频"
    if block_type == "particle_effect":
        return "即将显示粒子贴图"
    return fallback


def add_asset_candidate(target: list[dict], asset_id: object, reason: str) -> None:
    safe_asset_id = clean_text(asset_id)
    if safe_asset_id:
        target.append({"assetId": safe_asset_id, "reason": reason})


def collect_character_sprite_asset_ids(block: dict, context: dict, target: list[dict]) -> None:
    character_id = clean_text(block.get("characterId") or block.get("speakerId"))
    if not character_id:
        return
    character = get_from_collection(context.get("charactersById"), character_id)
    if not character:
        return
    expressions = to_list(character.get("expressions"))
    expression_id = clean_text(block.get("expressionId"))
    expression = next((item for item in expressions if isinstance(item, dict) and clean_text(item.get("id")) == expression_id), None)
    fallback_expression = next((item for item in expressions if isinstance(item, dict)), None)
    add_asset_candidate(
        target,
        (expression or {}).get("spriteAssetId")
        or (fallback_expression or {}).get("spriteAssetId")
        or character.get("defaultSpriteId"),
        get_preload_reason(block),
    )


def collect_block_asset_candidates(block: dict | None, context: dict | None = None) -> list[dict]:
    if not isinstance(block, dict):
        return []
    safe_context = context if isinstance(context, dict) else {}
    candidates: list[dict] = []
    block_type = clean_text(block.get("type"))
    if block_type in DIRECT_ASSET_BLOCK_TYPES:
        add_asset_candidate(candidates, block.get("assetId"), get_preload_reason(block))
    if block_type in {"dialogue", "narration"}:
        add_asset_candidate(candidates, block.get("voiceAssetId"), get_preload_reason(block))
    if block_type in {"character_show", "dialogue"}:
        collect_character_sprite_asset_ids(block, safe_context, candidates)
    return candidates


def normalize_excluded_asset_ids(value: object) -> set[str]:
    if isinstance(value, set):
        return {clean_text(item) for item in value if clean_text(item)}
    return {clean_text(item) for item in to_list(value) if clean_text(item)}


def should_skip_asset(asset_id: str, asset: dict | None, excluded_asset_ids: set[str]) -> bool:
    if not asset_id or not asset or asset.get("isMissing") or asset_id in excluded_asset_ids:
        return True
    return not get_asset_type(asset) or not get_asset_url(asset)


def upsert_prefetch_entry(entries_by_id: dict[str, dict], asset_id: str, asset: dict, metadata: dict) -> None:
    phase = clean_text(metadata.get("phase")) or "deferred"
    priority = clamp_int(metadata.get("priority"), 0, 999, 0)
    existing = entries_by_id.get(asset_id)
    if existing:
        existing_phase_rank = PREFETCH_PHASE_RANKS.get(clean_text(existing.get("phase")), 99)
        phase_rank = PREFETCH_PHASE_RANKS.get(phase, 99)
        if int(existing.get("priority") or 0) >= priority and existing_phase_rank <= phase_rank:
            return
    entries_by_id[asset_id] = {
        "assetId": asset_id,
        "url": get_asset_url(asset),
        "type": get_asset_type(asset),
        "name": clean_text(asset.get("name")) or asset_id,
        "phase": phase,
        "priority": priority,
        "sizeBytes": get_asset_size_bytes(asset),
        "reason": clean_text(metadata.get("reason")),
        "sceneId": clean_text(metadata.get("sceneId")),
        "blockId": clean_text(metadata.get("blockId")),
    }


def add_block_assets(entries_by_id: dict[str, dict], block: dict, context: dict, metadata: dict) -> None:
    assets_by_id = context.get("assetsById")
    excluded_asset_ids = normalize_excluded_asset_ids(context.get("excludeAssetIds"))
    for candidate in collect_block_asset_candidates(block, context):
        asset_id = clean_text(candidate.get("assetId"))
        asset = get_from_collection(assets_by_id, asset_id)
        if should_skip_asset(asset_id, asset, excluded_asset_ids):
            continue
        upsert_prefetch_entry(
            entries_by_id,
            asset_id,
            asset,
            {
                **metadata,
                "reason": clean_text(candidate.get("reason")) or clean_text(metadata.get("reason")),
                "blockId": clean_text(block.get("id")),
            },
        )


def collect_scene_range(entries_by_id: dict[str, dict], scene: dict | None, context: dict, options: dict) -> None:
    blocks = get_scene_blocks(scene)
    start_index = max(0, clamp_int(options.get("startIndex"), 0, len(blocks), 0))
    limit = max(0, clamp_int(options.get("limit"), 0, 999, 0))
    for offset, block in enumerate(blocks[start_index : start_index + limit]):
        add_block_assets(
            entries_by_id,
            block,
            context,
            {
                "sceneId": clean_text((scene or {}).get("id")),
                "phase": options.get("phase"),
                "priority": max(0, clamp_int(options.get("priority"), 0, 999, 0) - offset),
                "reason": options.get("reason"),
            },
        )


def is_continue_target(value: object, continue_target: str = CHOICE_CONTINUE_TARGET) -> bool:
    return clean_text(value) == continue_target


def collect_choice_target_scene_ids(snapshot: dict | None, continue_target: str = CHOICE_CONTINUE_TARGET) -> list[str]:
    targets = []
    for option in to_list((snapshot or {}).get("choiceOptions")):
        if not isinstance(option, dict):
            continue
        target = clean_text(option.get("gotoSceneId") or option.get("targetSceneId"))
        if target and not is_continue_target(target, continue_target):
            targets.append(target)
    return targets


def collect_block_target_scene_ids(block: dict | None, continue_target: str = CHOICE_CONTINUE_TARGET) -> list[str]:
    if not isinstance(block, dict):
        return []
    targets: list[str] = []
    block_type = clean_text(block.get("type"))
    if block_type == "jump":
        targets.append(clean_text(block.get("targetSceneId")))
    if block_type == "condition":
        for branch in to_list(block.get("branches")):
            if isinstance(branch, dict):
                targets.append(clean_text(branch.get("gotoSceneId")))
        targets.append(clean_text(block.get("elseGotoSceneId")))
    if block_type == "choice":
        for option in to_list(block.get("options")):
            if not isinstance(option, dict):
                continue
            target = clean_text(option.get("gotoSceneId") or option.get("targetSceneId"))
            if target and not is_continue_target(target, continue_target):
                targets.append(target)
    return [target for target in targets if target]


def get_unique_scene_ids(scene_ids: object) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for scene_id in to_list(scene_ids):
        safe_scene_id = clean_text(scene_id)
        if safe_scene_id and safe_scene_id not in seen:
            unique.append(safe_scene_id)
            seen.add(safe_scene_id)
    return unique


def get_prefetch_signature(snapshot: dict | None, scene_ids: list[str], entries: list[dict]) -> str:
    safe_snapshot = snapshot if isinstance(snapshot, dict) else {}
    current = ":".join(
        [
            clean_text(safe_snapshot.get("sceneId")),
            clean_text(safe_snapshot.get("blockId")),
            clean_text(safe_snapshot.get("blockIndex")),
        ]
    )
    target_key = ",".join(get_unique_scene_ids(scene_ids))
    asset_key = ",".join(clean_text(entry.get("assetId")) for entry in entries)
    return "|".join([current, target_key, asset_key])


def build_runtime_scene_prefetch_snapshot(
    scene: dict | None,
    block_index: int,
    *,
    scene_id: object = None,
    choice_options: object = None,
    transition_target_scene_id: object = None,
    completed: bool = False,
) -> dict:
    blocks = get_scene_blocks(scene)
    safe_block_index = max(0, int(block_index or 0))
    block = blocks[safe_block_index] if safe_block_index < len(blocks) else {}
    return {
        "sceneId": clean_text(scene_id or (scene or {}).get("id")),
        "blockIndex": safe_block_index,
        "blockId": clean_text(block.get("id")),
        "choiceOptions": [option for option in to_list(choice_options) if isinstance(option, dict)],
        "transitionTargetSceneId": clean_text(transition_target_scene_id),
        "completed": bool(completed),
    }


def build_runtime_scene_prefetch_manifest(snapshot: dict | None, context: dict | None = None, options: dict | None = None) -> dict:
    safe_context = context if isinstance(context, dict) else {}
    safe_options = options if isinstance(options, dict) else {}
    scenes_by_id = safe_context.get("scenesById")
    continue_target = clean_text(safe_options.get("choiceContinueTarget")) or CHOICE_CONTINUE_TARGET
    current_scene = get_from_collection(scenes_by_id, (snapshot or {}).get("sceneId"))
    block_lookahead = max(1, clamp_int(safe_options.get("blockLookahead"), 1, 64, 8))
    target_block_lookahead = max(1, clamp_int(safe_options.get("targetBlockLookahead"), 1, 64, 10))
    max_entries = max(1, clamp_int(safe_options.get("maxEntries"), 1, 96, 24))
    entries_by_id: dict[str, dict] = {}
    target_scene_ids: list[str] = []

    if not isinstance(snapshot, dict) or snapshot.get("completed") or not current_scene:
        return {
            "formatVersion": 1,
            "entrySceneId": clean_text((snapshot or {}).get("sceneId") if isinstance(snapshot, dict) else ""),
            "generatedBy": "runtime_scene_prefetch",
            "prefetchKey": get_prefetch_signature(snapshot, [], []),
            "targetSceneIds": [],
            "entries": [],
        }

    next_block_index = max(0, int(snapshot.get("blockIndex") or 0) + 1)
    collect_scene_range(
        entries_by_id,
        current_scene,
        safe_context,
        {
            "startIndex": next_block_index,
            "limit": block_lookahead,
            "phase": "early",
            "priority": 84,
            "reason": "当前场景即将播放",
        },
    )

    transition_target = clean_text(snapshot.get("transitionTargetSceneId"))
    if transition_target and not is_continue_target(transition_target, continue_target):
        target_scene_ids.append(transition_target)
    target_scene_ids.extend(collect_choice_target_scene_ids(snapshot, continue_target))

    for block in get_scene_blocks(current_scene)[next_block_index : next_block_index + block_lookahead]:
        target_scene_ids.extend(collect_block_target_scene_ids(block, continue_target))

    for index, target_scene_id in enumerate(get_unique_scene_ids(target_scene_ids)):
        scene = get_from_collection(scenes_by_id, target_scene_id)
        if not scene:
            continue
        collect_scene_range(
            entries_by_id,
            scene,
            safe_context,
            {
                "startIndex": 0,
                "limit": target_block_lookahead,
                "phase": "early" if index < 4 else "deferred",
                "priority": max(32, 76 - index * 4),
                "reason": "即将进入的分支场景",
            },
        )

    entries = sorted(
        entries_by_id.values(),
        key=lambda item: (-int(item.get("priority") or 0), clean_text(item.get("assetId"))),
    )[:max_entries]
    for index, entry in enumerate(entries):
        entry["preloadIndex"] = index + 1

    return {
        "formatVersion": 1,
        "entrySceneId": clean_text(snapshot.get("sceneId")),
        "generatedBy": "runtime_scene_prefetch",
        "prefetchKey": get_prefetch_signature(snapshot, target_scene_ids, entries),
        "targetSceneIds": get_unique_scene_ids(target_scene_ids),
        "entries": entries,
    }


def get_runtime_scene_prefetch_summary(manifest: dict | None) -> dict:
    entries = [entry for entry in to_list((manifest or {}).get("entries")) if isinstance(entry, dict)]
    summary = {
        "totalCount": 0,
        "imageCount": 0,
        "audioCount": 0,
        "videoCount": 0,
        "totalSizeBytes": 0,
    }
    for entry in entries:
        asset_type = clean_text(entry.get("type"))
        summary["totalCount"] += 1
        summary["totalSizeBytes"] += normalize_size_bytes(entry.get("sizeBytes"))
        if asset_type in {"background", "sprite", "cg", "ui"}:
            summary["imageCount"] += 1
        elif asset_type in {"bgm", "sfx", "voice"}:
            summary["audioCount"] += 1
        elif asset_type == "video":
            summary["videoCount"] += 1
    return summary
