from __future__ import annotations

try:
    from .runtime_preload import format_bytes, format_runtime_preload_status_line, normalize_size_bytes
    from .runtime_scene_prefetch import get_runtime_scene_prefetch_summary
except ImportError:  # pragma: no cover - exported native packages import from the same directory.
    from runtime_preload import format_bytes, format_runtime_preload_status_line, normalize_size_bytes
    from runtime_scene_prefetch import get_runtime_scene_prefetch_summary


def get_loaded_cache_count(cache: object) -> int:
    if not isinstance(cache, dict):
        return 0
    return sum(1 for value in cache.values() if value is not None)


def get_status_tone(status: object) -> str:
    key = str(status or "").strip()
    if key in {"ready", "empty"}:
        return "ready"
    if key in {"warming", "partial"}:
        return "warn"
    if key in {"blocked", "failed"}:
        return "danger"
    return "neutral"


def build_status_row(label: str, value: object, detail: object = "", tone: object = "neutral") -> dict:
    return {
        "label": str(label or ""),
        "value": str(value or ""),
        "detail": str(detail or ""),
        "tone": get_status_tone(tone),
    }


def build_runtime_preload_diagnostic_rows(preload_status: dict | None) -> list[dict]:
    status = preload_status if isinstance(preload_status, dict) else {}
    total_entries = int(status.get("totalEntries") or 0)
    loaded_entries = int(status.get("loadedEntries") or 0)
    pending_entries = int(status.get("pendingEntries") or 0)
    issue_count = (
        int(status.get("missingEntries") or 0)
        + int(status.get("failedEntries") or 0)
        + int(status.get("audioUnavailableEntries") or 0)
    )
    return [
        build_status_row(
            "全局资源预热",
            f"{loaded_entries}/{total_entries}",
            format_runtime_preload_status_line(status),
            status.get("status") or "empty",
        ),
        build_status_row(
            "后台剩余",
            f"{pending_entries} 项",
            "启动后会按性能档位分帧继续预热，避免首屏一次性卡顿。",
            "warming" if pending_entries else "ready",
        ),
        build_status_row(
            "预热异常",
            f"{issue_count} 项",
            "缺失、加载失败或当前设备音频不可用的条目会在这里累计。",
            "blocked" if issue_count else "ready",
        ),
    ]


def build_runtime_scene_prefetch_diagnostic_rows(prefetch_status: dict | None, prefetch_manifest: dict | None) -> list[dict]:
    status = prefetch_status if isinstance(prefetch_status, dict) else {}
    manifest = prefetch_manifest if isinstance(prefetch_manifest, dict) else {}
    summary = get_runtime_scene_prefetch_summary(manifest)
    total_entries = int(summary.get("totalCount") or status.get("totalEntries") or 0)
    loaded_entries = int(status.get("loadedEntries") or 0)
    pending_entries = int(status.get("pendingEntries") or 0)
    target_scene_count = len(manifest.get("targetSceneIds") or []) if isinstance(manifest.get("targetSceneIds"), list) else 0
    total_size = format_bytes(normalize_size_bytes(summary.get("totalSizeBytes")))
    tone = status.get("status") or ("empty" if total_entries <= 0 else "warming")
    return [
        build_status_row(
            "路线预取",
            f"{loaded_entries}/{total_entries}",
            f"当前路线窗口：图片 {summary.get('imageCount', 0)} / 音频 {summary.get('audioCount', 0)} / 视频 {summary.get('videoCount', 0)}，合计 {total_size}。",
            tone,
        ),
        build_status_row(
            "分支预判",
            f"{target_scene_count} 个场景",
            "会根据当前场景后续块、选项、跳转和条件分支提前准备可能用到的素材。",
            "ready" if target_scene_count else "empty",
        ),
        build_status_row(
            "预取队列",
            f"剩余 {pending_entries} 项",
            str(manifest.get("prefetchKey") or "当前没有预取签名。")[:96],
            "warming" if pending_entries else tone,
        ),
    ]


def build_runtime_cache_diagnostic_rows(context: dict | None) -> list[dict]:
    safe_context = context if isinstance(context, dict) else {}
    image_count = get_loaded_cache_count(safe_context.get("imageCache"))
    sound_count = get_loaded_cache_count(safe_context.get("soundCache"))
    video_preview_count = get_loaded_cache_count(safe_context.get("videoPreviewFrameCache"))
    prefetched_count = len(safe_context.get("runtimeScenePrefetchedAssetIds") or [])
    active_bgm = str(safe_context.get("currentBgmAssetId") or "无")
    active_voice = "播放中" if safe_context.get("voicePlaybackActive") else "待机"
    return [
        build_status_row("图片缓存", f"{image_count} 项", "已解码到内存的背景、CG、立绘和 UI 图片。", "ready" if image_count else "empty"),
        build_status_row("音频缓存", f"{sound_count} 项", f"BGM：{active_bgm} / 语音：{active_voice}", "ready" if sound_count else "empty"),
        build_status_row("视频预览缓存", f"{video_preview_count} 项", "内嵌视频卡片的预览帧缓存。", "ready" if video_preview_count else "empty"),
        build_status_row("路线已预取", f"{prefetched_count} 项", "本轮路线预取已经完成过加载尝试的素材。", "ready" if prefetched_count else "empty"),
    ]


def build_runtime_position_diagnostic_rows(context: dict | None) -> list[dict]:
    safe_context = context if isinstance(context, dict) else {}
    scene_label = str(safe_context.get("sceneName") or safe_context.get("sceneId") or "标题页")
    block_index = int(safe_context.get("blockIndex") or 0)
    choice_count = int(safe_context.get("choiceCount") or 0)
    line_type = str(safe_context.get("lineType") or ("选项" if choice_count else "待推进"))
    status_message = str(safe_context.get("statusMessage") or "")
    return [
        build_status_row("当前位置", scene_label, f"场景 ID：{safe_context.get('sceneId') or 'title'}", "ready"),
        build_status_row("剧情块", f"第 {block_index + 1} 块", f"当前状态：{line_type}", "ready"),
        build_status_row("选项数量", f"{choice_count} 个", "当前停在选项时会把分支目标纳入预取窗口。", "ready" if choice_count else "empty"),
        build_status_row("状态提示", status_message or "无", "来自原生 Runtime 顶部状态栏。", "neutral"),
    ]


def build_runtime_diagnostics_report(context: dict | None = None) -> dict:
    safe_context = context if isinstance(context, dict) else {}
    preload_status = safe_context.get("runtimePreloadStatus") if isinstance(safe_context.get("runtimePreloadStatus"), dict) else {}
    prefetch_status = safe_context.get("runtimeScenePrefetchStatus") if isinstance(safe_context.get("runtimeScenePrefetchStatus"), dict) else {}
    prefetch_manifest = safe_context.get("runtimeScenePrefetchManifest") if isinstance(safe_context.get("runtimeScenePrefetchManifest"), dict) else {}
    sections = [
        {"title": "播放位置", "rows": build_runtime_position_diagnostic_rows(safe_context)},
        {"title": "启动预热", "rows": build_runtime_preload_diagnostic_rows(preload_status)},
        {"title": "路线预取", "rows": build_runtime_scene_prefetch_diagnostic_rows(prefetch_status, prefetch_manifest)},
        {"title": "运行缓存", "rows": build_runtime_cache_diagnostic_rows(safe_context)},
    ]
    issue_count = sum(1 for section in sections for row in section["rows"] if row.get("tone") == "danger")
    warning_count = sum(1 for section in sections for row in section["rows"] if row.get("tone") == "warn")
    if issue_count:
        status = "blocked"
        headline = f"发现 {issue_count} 个运行时异常，建议先修素材或依赖。"
    elif warning_count:
        status = "warming"
        headline = f"运行时正在准备资源，仍有 {warning_count} 个观察项。"
    else:
        status = "ready"
        headline = "运行时资源状态稳定，当前路线可以继续试玩。"
    return {
        "formatVersion": 1,
        "status": status,
        "headline": headline,
        "issueCount": issue_count,
        "warningCount": warning_count,
        "sections": sections,
    }
