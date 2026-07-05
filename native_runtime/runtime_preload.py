from __future__ import annotations


RUNTIME_PRELOAD_IMAGE_TYPES = {"background", "sprite", "cg", "ui"}
RUNTIME_PRELOAD_SOUND_TYPES = {"sfx", "voice"}
RUNTIME_PRELOAD_STREAM_TYPES = {"bgm", "video"}
RUNTIME_PRELOAD_SUPPORTED_TYPES = (
    RUNTIME_PRELOAD_IMAGE_TYPES
    | RUNTIME_PRELOAD_SOUND_TYPES
    | RUNTIME_PRELOAD_STREAM_TYPES
)
RUNTIME_PRELOAD_STARTUP_PHASES = {"critical"}
RUNTIME_PRELOAD_DEFAULT_FRAME_BUDGET = 1


def clamp_int(value: object, minimum: int, maximum: int, default: int) -> int:
    try:
        integer = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, integer))


def get_runtime_preload_manifest(build_info: dict | None) -> dict:
    if not isinstance(build_info, dict):
        return {}
    manifest = build_info.get("runtimePreloadManifest")
    return manifest if isinstance(manifest, dict) else {}


def normalize_runtime_preload_entries(manifest: dict | None, assets_by_id: dict) -> list[dict]:
    source = manifest if isinstance(manifest, dict) else {}
    entries = source.get("entries") if isinstance(source.get("entries"), list) else []
    normalized_entries: list[dict] = []
    seen_asset_ids: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        asset_id = str(entry.get("assetId") or "").strip()
        if not asset_id or asset_id in seen_asset_ids:
            continue
        asset = assets_by_id.get(asset_id) if isinstance(assets_by_id, dict) else {}
        asset = asset if isinstance(asset, dict) else {}
        entry_asset_type = str(entry.get("type") or "").strip()
        asset_type = (
            entry_asset_type
            if entry_asset_type in RUNTIME_PRELOAD_SUPPORTED_TYPES
            else str(asset.get("type") or "").strip()
        )
        if asset_type not in RUNTIME_PRELOAD_SUPPORTED_TYPES:
            continue
        seen_asset_ids.add(asset_id)
        normalized_entries.append(
            {
                "assetId": asset_id,
                "type": asset_type,
                "phase": str(entry.get("phase") or "deferred").strip() or "deferred",
                "priority": clamp_int(entry.get("priority"), 0, 999, 0),
                "preloadIndex": clamp_int(entry.get("preloadIndex"), 0, 9999, len(normalized_entries) + 1),
                "reason": str(entry.get("reason") or ""),
            }
        )
    return sorted(
        normalized_entries,
        key=lambda item: (
            -int(item.get("priority") or 0),
            int(item.get("preloadIndex") or 0),
            str(item.get("assetId") or ""),
        ),
    )


def is_runtime_preload_startup_entry(entry: dict) -> bool:
    return str(entry.get("phase") or "").strip() in RUNTIME_PRELOAD_STARTUP_PHASES


def build_empty_runtime_preload_status() -> dict:
    return {
        "status": "empty",
        "totalEntries": 0,
        "loadedEntries": 0,
        "pendingEntries": 0,
        "imageEntries": 0,
        "loadedImageEntries": 0,
        "soundEntries": 0,
        "loadedSoundEntries": 0,
        "streamEntries": 0,
        "readyStreamEntries": 0,
        "missingEntries": 0,
        "failedEntries": 0,
        "audioUnavailableEntries": 0,
        "missingAssetIds": [],
        "failedAssetIds": [],
        "skippedAssetIds": [],
        "summaryText": "资源预热：无待加载素材",
    }


def build_runtime_preload_status(entries: list[dict]) -> dict:
    status = build_empty_runtime_preload_status()
    status["totalEntries"] = len(entries)
    status["pendingEntries"] = len(entries)
    for entry in entries:
        asset_type = str(entry.get("type") or "")
        if asset_type in RUNTIME_PRELOAD_IMAGE_TYPES:
            status["imageEntries"] += 1
        elif asset_type in RUNTIME_PRELOAD_SOUND_TYPES:
            status["soundEntries"] += 1
        elif asset_type in RUNTIME_PRELOAD_STREAM_TYPES:
            status["streamEntries"] += 1
    return finalize_runtime_preload_status(status)


def mark_runtime_preload_entry(status: dict, entry: dict, outcome: str) -> dict:
    asset_id = str(entry.get("assetId") or "")
    if status.get("pendingEntries"):
        status["pendingEntries"] = max(0, int(status.get("pendingEntries") or 0) - 1)
    if outcome == "loaded_image":
        status["loadedImageEntries"] += 1
    elif outcome == "loaded_sound":
        status["loadedSoundEntries"] += 1
    elif outcome == "ready_stream":
        status["readyStreamEntries"] += 1
    elif outcome == "missing":
        status["missingEntries"] += 1
        status["missingAssetIds"].append(asset_id)
    elif outcome == "failed":
        status["failedEntries"] += 1
        status["failedAssetIds"].append(asset_id)
    elif outcome == "audio_unavailable":
        status["audioUnavailableEntries"] += 1
        status["skippedAssetIds"].append(asset_id)
    return finalize_runtime_preload_status(status)


def finalize_runtime_preload_status(status: dict) -> dict:
    total_entries = int(status.get("totalEntries") or 0)
    status["loadedEntries"] = (
        int(status.get("loadedImageEntries") or 0)
        + int(status.get("loadedSoundEntries") or 0)
        + int(status.get("readyStreamEntries") or 0)
    )
    issue_count = (
        int(status.get("missingEntries") or 0)
        + int(status.get("failedEntries") or 0)
        + int(status.get("audioUnavailableEntries") or 0)
    )
    pending_entries = int(status.get("pendingEntries") or 0)
    if total_entries <= 0:
        status["status"] = "empty"
    elif pending_entries > 0:
        status["status"] = "warming"
    elif issue_count <= 0:
        status["status"] = "ready"
    elif status["loadedEntries"] > 0:
        status["status"] = "partial"
    else:
        status["status"] = "blocked"
    status["summaryText"] = format_runtime_preload_status_line(status)
    return status


def format_runtime_preload_status_line(status: dict | None = None) -> str:
    source = status if isinstance(status, dict) else {}
    total_entries = int(source.get("totalEntries") or 0)
    if total_entries <= 0:
        return "资源预热：无待加载素材"
    loaded_entries = int(source.get("loadedEntries") or 0)
    pending_entries = int(source.get("pendingEntries") or 0)
    issue_count = (
        int(source.get("missingEntries") or 0)
        + int(source.get("failedEntries") or 0)
        + int(source.get("audioUnavailableEntries") or 0)
    )
    detail = (
        f"图片 {int(source.get('loadedImageEntries') or 0)}/{int(source.get('imageEntries') or 0)}"
        f" · 音效 {int(source.get('loadedSoundEntries') or 0)}/{int(source.get('soundEntries') or 0)}"
        f" · 流媒体 {int(source.get('readyStreamEntries') or 0)}/{int(source.get('streamEntries') or 0)}"
    )
    if pending_entries > 0:
        return f"资源预热：{loaded_entries}/{total_entries} 已准备，后台继续 {pending_entries} 项（{detail}）"
    if issue_count > 0:
        return f"资源预热：{loaded_entries}/{total_entries} 已准备，需复查 {issue_count} 项（{detail}）"
    return f"资源预热：{loaded_entries}/{total_entries} 已准备（{detail}）"
