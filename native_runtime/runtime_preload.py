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
RUNTIME_PRELOAD_CRITICAL_BUDGET_BYTES = 96 * 1024 * 1024
RUNTIME_PRELOAD_TOTAL_BUDGET_BYTES = 512 * 1024 * 1024
RUNTIME_PRELOAD_PROFILE_RANKS = {
    "mobile_low": 0,
    "web": 1,
    "standard": 2,
    "high_quality_pc": 3,
}
RUNTIME_PRELOAD_PERFORMANCE_PROFILES = {
    "standard": {
        "key": "standard",
        "label": "标准 PC / 网页",
        "frameBudget": 1,
        "startupPhases": {"critical"},
        "criticalBudgetBytes": 96 * 1024 * 1024,
        "totalBudgetBytes": 512 * 1024 * 1024,
    },
    "web": {
        "key": "web",
        "label": "网页轻量",
        "frameBudget": 1,
        "startupPhases": {"critical"},
        "criticalBudgetBytes": 72 * 1024 * 1024,
        "totalBudgetBytes": 384 * 1024 * 1024,
    },
    "mobile_low": {
        "key": "mobile_low",
        "label": "低配 / 移动端",
        "frameBudget": 1,
        "startupPhases": {"critical"},
        "criticalBudgetBytes": 48 * 1024 * 1024,
        "totalBudgetBytes": 256 * 1024 * 1024,
    },
    "high_quality_pc": {
        "key": "high_quality_pc",
        "label": "高画质 PC",
        "frameBudget": 3,
        "startupPhases": {"critical", "early"},
        "criticalBudgetBytes": 160 * 1024 * 1024,
        "totalBudgetBytes": 768 * 1024 * 1024,
    },
}


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


def clamp_int(value: object, minimum: int, maximum: int, default: int) -> int:
    try:
        integer = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, integer))


def normalize_size_bytes(value: object) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def get_safe_runtime_preload_performance_profile(value: object, fallback: str = "standard") -> str:
    fallback_key = fallback if fallback in RUNTIME_PRELOAD_PERFORMANCE_PROFILES else "standard"
    key = str(value or fallback_key).strip().lower()
    return key if key in RUNTIME_PRELOAD_PERFORMANCE_PROFILES else fallback_key


def get_project_runtime_preload_performance_profile(project: dict | None = None, fallback: str = "standard") -> str:
    if not isinstance(project, dict):
        return get_safe_runtime_preload_performance_profile(None, fallback)
    runtime_settings = project.get("runtimeSettings") if isinstance(project.get("runtimeSettings"), dict) else {}
    profile = runtime_settings.get("performanceProfile") if isinstance(runtime_settings, dict) else None
    return get_safe_runtime_preload_performance_profile(profile or project.get("performanceProfile"), fallback)


def get_runtime_preload_profile_config(performance_profile: object = None) -> dict:
    key = get_safe_runtime_preload_performance_profile(performance_profile)
    profile = RUNTIME_PRELOAD_PERFORMANCE_PROFILES[key]
    return {
        **profile,
        "startupPhases": set(profile.get("startupPhases") or RUNTIME_PRELOAD_STARTUP_PHASES),
    }


def get_runtime_preload_frame_budget(performance_profile: object = None) -> int:
    profile = get_runtime_preload_profile_config(performance_profile)
    return clamp_int(profile.get("frameBudget"), 1, 8, RUNTIME_PRELOAD_DEFAULT_FRAME_BUDGET)


def get_runtime_preload_startup_phases(performance_profile: object = None) -> set[str]:
    profile = get_runtime_preload_profile_config(performance_profile)
    return set(profile.get("startupPhases") or RUNTIME_PRELOAD_STARTUP_PHASES)


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
                "name": str(entry.get("name") or asset.get("name") or asset_id),
                "type": asset_type,
                "phase": str(entry.get("phase") or "deferred").strip() or "deferred",
                "priority": clamp_int(entry.get("priority"), 0, 999, 0),
                "preloadIndex": clamp_int(entry.get("preloadIndex"), 0, 9999, len(normalized_entries) + 1),
                "sizeBytes": normalize_size_bytes(entry.get("sizeBytes") if "sizeBytes" in entry else asset.get("fileSizeBytes")),
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


def is_runtime_preload_startup_entry(entry: dict, performance_profile: object = None) -> bool:
    return str(entry.get("phase") or "").strip() in get_runtime_preload_startup_phases(performance_profile)


def build_runtime_preload_size_budget(
    entry_reports: list[dict],
    *,
    critical_budget_bytes: int | None = None,
    total_budget_bytes: int | None = None,
    performance_profile: object = None,
) -> dict:
    profile = get_runtime_preload_profile_config(performance_profile)
    critical_budget = (
        normalize_size_bytes(critical_budget_bytes)
        if critical_budget_bytes is not None
        else normalize_size_bytes(profile.get("criticalBudgetBytes"))
    )
    total_budget = (
        normalize_size_bytes(total_budget_bytes)
        if total_budget_bytes is not None
        else normalize_size_bytes(profile.get("totalBudgetBytes"))
    )
    total_bytes = 0
    critical_bytes = 0
    by_type: dict[str, int] = {}
    largest_entries: list[dict] = []
    for entry in entry_reports:
        if not isinstance(entry, dict):
            continue
        size_bytes = max(0, int(entry.get("sizeBytes") or 0))
        asset_type = str(entry.get("type") or "unknown")
        total_bytes += size_bytes
        by_type[asset_type] = by_type.get(asset_type, 0) + size_bytes
        if entry.get("startup"):
            critical_bytes += size_bytes
        if size_bytes > 0:
            largest_entries.append(
                {
                    "assetId": entry.get("assetId") or "",
                    "name": entry.get("name") or entry.get("assetId") or "",
                    "type": asset_type,
                    "phase": entry.get("phase") or "",
                    "sizeBytes": size_bytes,
                    "sizeLabel": format_bytes(size_bytes),
                    "startup": bool(entry.get("startup")),
                }
            )
    largest_entries.sort(key=lambda item: int(item.get("sizeBytes") or 0), reverse=True)
    critical_over_budget = critical_bytes > critical_budget
    total_over_budget = total_bytes > total_budget
    return {
        "status": "warn" if critical_over_budget or total_over_budget else "ready",
        "performanceProfile": profile.get("key") or "standard",
        "performanceProfileLabel": profile.get("label") or "标准 PC / 网页",
        "totalBytes": total_bytes,
        "totalLabel": format_bytes(total_bytes),
        "criticalBytes": critical_bytes,
        "criticalLabel": format_bytes(critical_bytes),
        "totalBudgetBytes": total_budget,
        "totalBudgetLabel": format_bytes(total_budget),
        "criticalBudgetBytes": critical_budget,
        "criticalBudgetLabel": format_bytes(critical_budget),
        "criticalOverBudget": critical_over_budget,
        "totalOverBudget": total_over_budget,
        "byTypeBytes": by_type,
        "byTypeLabels": {asset_type: format_bytes(size) for asset_type, size in sorted(by_type.items())},
        "largestEntries": largest_entries[:8],
    }


def get_runtime_preload_profile_label(performance_profile: object = None) -> str:
    profile = get_runtime_preload_profile_config(performance_profile)
    return str(profile.get("label") or "标准 PC / 网页")


def build_runtime_preload_profile_metrics(entry_reports: list[dict]) -> dict:
    total_bytes = 0
    critical_bytes = 0
    entry_count = 0
    stream_count = 0
    for entry in entry_reports:
        if not isinstance(entry, dict):
            continue
        entry_count += 1
        size_bytes = normalize_size_bytes(entry.get("sizeBytes"))
        total_bytes += size_bytes
        if entry.get("startup"):
            critical_bytes += size_bytes
        if str(entry.get("type") or "") in RUNTIME_PRELOAD_STREAM_TYPES:
            stream_count += 1

    return {
        "entryCount": entry_count,
        "streamEntryCount": stream_count,
        "totalBytes": total_bytes,
        "totalLabel": format_bytes(total_bytes),
        "criticalBytes": critical_bytes,
        "criticalLabel": format_bytes(critical_bytes),
    }


def get_runtime_preload_recommended_profile(entry_reports: list[dict]) -> str:
    metrics = build_runtime_preload_profile_metrics(entry_reports)
    total_bytes = int(metrics.get("totalBytes") or 0)
    critical_bytes = int(metrics.get("criticalBytes") or 0)
    entry_count = int(metrics.get("entryCount") or 0)
    stream_count = int(metrics.get("streamEntryCount") or 0)

    if (
        critical_bytes > RUNTIME_PRELOAD_CRITICAL_BUDGET_BYTES
        or total_bytes > RUNTIME_PRELOAD_TOTAL_BUDGET_BYTES
        or stream_count >= 2
        or entry_count >= 32
    ):
        return "high_quality_pc"
    if critical_bytes > 64 * 1024 * 1024 or total_bytes > 256 * 1024 * 1024 or stream_count >= 1 or entry_count >= 20:
        return "standard"
    if critical_bytes > 32 * 1024 * 1024 or total_bytes > 128 * 1024 * 1024 or entry_count >= 10:
        return "web"
    return "mobile_low"


def build_runtime_preload_profile_advice(
    entry_reports: list[dict],
    selected_profile: object = None,
) -> dict:
    selected_key = get_safe_runtime_preload_performance_profile(selected_profile)
    recommended_key = get_runtime_preload_recommended_profile(entry_reports)
    selected_rank = RUNTIME_PRELOAD_PROFILE_RANKS.get(selected_key, RUNTIME_PRELOAD_PROFILE_RANKS["standard"])
    recommended_rank = RUNTIME_PRELOAD_PROFILE_RANKS.get(recommended_key, RUNTIME_PRELOAD_PROFILE_RANKS["standard"])
    max_profile = get_runtime_preload_profile_config("high_quality_pc")
    metrics = build_runtime_preload_profile_metrics(entry_reports)
    total_bytes = int(metrics.get("totalBytes") or 0)
    critical_bytes = int(metrics.get("criticalBytes") or 0)

    over_max_budget = (
        critical_bytes > normalize_size_bytes(max_profile.get("criticalBudgetBytes"))
        or total_bytes > normalize_size_bytes(max_profile.get("totalBudgetBytes"))
    )
    reasons: list[str] = []
    actions: list[str] = []
    if over_max_budget:
        status = "needs_optimization"
        severity = "warn"
        reasons.append("当前首屏或整体预热体积已经超过高画质 PC 档位建议预算。")
        actions.append("优先压缩首屏背景、UI、开场视频和大体积音频，或把非首屏资源降为 deferred。")
    elif selected_rank < recommended_rank:
        status = "should_raise"
        severity = "warn"
        reasons.append(
            f"当前素材规模更接近「{get_runtime_preload_profile_label(recommended_key)}」，"
            f"继续使用「{get_runtime_preload_profile_label(selected_key)}」可能让后台预热偏慢。"
        )
        actions.append(f"如果目标设备允许，建议把项目性能档位切换到「{get_runtime_preload_profile_label(recommended_key)}」。")
    elif selected_rank > recommended_rank:
        status = "can_lower"
        severity = "info"
        reasons.append(
            f"当前素材规模较轻，使用「{get_runtime_preload_profile_label(selected_key)}」可以运行，"
            f"但「{get_runtime_preload_profile_label(recommended_key)}」也足够。"
        )
        actions.append("如果更重视低配设备体验，可以降低档位并重新导出测试。")
    else:
        status = "ok"
        severity = "pass"
        reasons.append(f"当前预热规模与「{get_runtime_preload_profile_label(selected_key)}」匹配。")
        actions.append("保持当前档位；发布前继续用 Runtime 预热报告复查首屏体积和缺失素材。")

    return {
        "status": status,
        "severity": severity,
        "selectedProfile": selected_key,
        "selectedProfileLabel": get_runtime_preload_profile_label(selected_key),
        "recommendedProfile": recommended_key,
        "recommendedProfileLabel": get_runtime_preload_profile_label(recommended_key),
        **metrics,
        "reasons": reasons,
        "actions": actions,
    }


def build_empty_runtime_preload_status(performance_profile: object = None) -> dict:
    profile = get_runtime_preload_profile_config(performance_profile)
    return {
        "status": "empty",
        "performanceProfile": profile.get("key") or "standard",
        "performanceProfileLabel": profile.get("label") or "标准 PC / 网页",
        "frameBudget": get_runtime_preload_frame_budget(profile.get("key")),
        "totalEntries": 0,
        "loadedEntries": 0,
        "pendingEntries": 0,
        "imageEntries": 0,
        "loadedImageEntries": 0,
        "soundEntries": 0,
        "loadedSoundEntries": 0,
        "streamEntries": 0,
        "readyStreamEntries": 0,
        "cachedEntries": 0,
        "missingEntries": 0,
        "failedEntries": 0,
        "audioUnavailableEntries": 0,
        "totalBytes": 0,
        "criticalBytes": 0,
        "loadedBytes": 0,
        "readyEntries": 0,
        "loadedAssetIds": [],
        "cachedAssetIds": [],
        "missingAssetIds": [],
        "failedAssetIds": [],
        "skippedAssetIds": [],
        "summaryText": "资源预热：无待加载素材",
    }


def build_runtime_preload_status(entries: list[dict], performance_profile: object = None) -> dict:
    profile_key = get_safe_runtime_preload_performance_profile(performance_profile)
    status = build_empty_runtime_preload_status(profile_key)
    status["totalEntries"] = len(entries)
    status["pendingEntries"] = len(entries)
    for entry in entries:
        asset_type = str(entry.get("type") or "")
        size_bytes = normalize_size_bytes(entry.get("sizeBytes"))
        status["totalBytes"] += size_bytes
        if is_runtime_preload_startup_entry(entry, profile_key):
            status["criticalBytes"] += size_bytes
        if asset_type in RUNTIME_PRELOAD_IMAGE_TYPES:
            status["imageEntries"] += 1
        elif asset_type in RUNTIME_PRELOAD_SOUND_TYPES:
            status["soundEntries"] += 1
        elif asset_type in RUNTIME_PRELOAD_STREAM_TYPES:
            status["streamEntries"] += 1
    return finalize_runtime_preload_status(status)


def mark_runtime_preload_entry(status: dict, entry: dict, outcome: str) -> dict:
    asset_id = str(entry.get("assetId") or "")
    asset_type = str(entry.get("type") or "")
    status.setdefault("loadedAssetIds", [])
    status.setdefault("cachedAssetIds", [])
    status.setdefault("missingAssetIds", [])
    status.setdefault("failedAssetIds", [])
    status.setdefault("skippedAssetIds", [])
    status.setdefault("cachedEntries", 0)
    if status.get("pendingEntries"):
        status["pendingEntries"] = max(0, int(status.get("pendingEntries") or 0) - 1)
    if outcome in {"loaded_image", "loaded_sound", "ready_stream", "cached"}:
        status["loadedBytes"] = normalize_size_bytes(status.get("loadedBytes")) + normalize_size_bytes(entry.get("sizeBytes"))
    if outcome == "loaded_image":
        status["loadedImageEntries"] += 1
        status["loadedAssetIds"].append(asset_id)
    elif outcome == "loaded_sound":
        status["loadedSoundEntries"] += 1
        status["loadedAssetIds"].append(asset_id)
    elif outcome == "ready_stream":
        status["readyStreamEntries"] += 1
        status["loadedAssetIds"].append(asset_id)
    elif outcome == "cached":
        status["cachedEntries"] += 1
        status["cachedAssetIds"].append(asset_id)
        if asset_type in RUNTIME_PRELOAD_IMAGE_TYPES:
            status["loadedImageEntries"] += 1
        elif asset_type in RUNTIME_PRELOAD_SOUND_TYPES:
            status["loadedSoundEntries"] += 1
        elif asset_type in RUNTIME_PRELOAD_STREAM_TYPES:
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
    status["readyEntries"] = status["loadedEntries"]
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
    ready_entries = int(
        source.get("readyEntries")
        if source.get("readyEntries") is not None
        else source.get("loadedEntries") or 0
    )
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
    total_bytes = normalize_size_bytes(source.get("totalBytes"))
    if total_bytes > 0:
        detail = (
            f"{detail}"
            f" · 已准备 {format_bytes(source.get('loadedBytes'))}"
            f" · 首屏 {format_bytes(source.get('criticalBytes'))}"
            f" · 合计 {format_bytes(total_bytes)}"
        )
    profile_label = str(source.get("performanceProfileLabel") or "").strip()
    if profile_label:
        detail = f"{detail} · 档位 {profile_label}"
    cached_entries = int(source.get("cachedEntries") or 0)
    if cached_entries > 0:
        detail = f"{detail} · 复用 {cached_entries}"
    if pending_entries > 0:
        return f"资源预热：{ready_entries}/{total_entries} 已准备，后台继续 {pending_entries} 项（{detail}）"
    if issue_count > 0:
        return f"资源预热：{ready_entries}/{total_entries} 已准备，需复查 {issue_count} 项（{detail}）"
    return f"资源预热：{ready_entries}/{total_entries} 已准备（{detail}）"
