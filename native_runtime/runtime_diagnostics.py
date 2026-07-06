from __future__ import annotations

from datetime import datetime

try:
    from .runtime_preload import format_bytes, format_runtime_preload_status_line, normalize_size_bytes
    from .runtime_scene_prefetch import (
        build_runtime_scene_prefetch_manifest,
        build_runtime_scene_prefetch_snapshot,
        get_runtime_scene_prefetch_summary,
    )
except ImportError:  # pragma: no cover - exported native packages import from the same directory.
    from runtime_preload import format_bytes, format_runtime_preload_status_line, normalize_size_bytes
    from runtime_scene_prefetch import (
        build_runtime_scene_prefetch_manifest,
        build_runtime_scene_prefetch_snapshot,
        get_runtime_scene_prefetch_summary,
    )


DIAGNOSTICS_REPORT_NAME = "native-runtime-diagnostics.json"
DIAGNOSTICS_MARKDOWN_NAME = "native-runtime-diagnostics.md"
DIAGNOSTICS_FORMAT_VERSION = 1


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def safe_text(value: object) -> str:
    return str(value or "").strip()


def markdown_value(value: object, fallback: str = "-") -> str:
    text = safe_text(value)
    if not text:
        return fallback
    return text.replace("|", "\\|").replace("\n", " ")


def to_list(value: object) -> list:
    return value if isinstance(value, list) else []


def get_project(payload: dict | None) -> dict:
    source = payload if isinstance(payload, dict) else {}
    project = source.get("project")
    return project if isinstance(project, dict) else {}


def get_assets(payload: dict | None) -> list[dict]:
    source = payload if isinstance(payload, dict) else {}
    assets_doc = source.get("assets") if isinstance(source.get("assets"), dict) else {}
    assets = assets_doc.get("assets")
    if not isinstance(assets, list) and isinstance(source.get("assets"), list):
        assets = source.get("assets")
    return [asset for asset in to_list(assets) if isinstance(asset, dict)]


def get_characters(payload: dict | None) -> list[dict]:
    source = payload if isinstance(payload, dict) else {}
    characters_doc = source.get("characters") if isinstance(source.get("characters"), dict) else {}
    characters = characters_doc.get("characters")
    if not isinstance(characters, list) and isinstance(source.get("characters"), list):
        characters = source.get("characters")
    return [character for character in to_list(characters) if isinstance(character, dict)]


def index_by_id(items: list[dict]) -> dict[str, dict]:
    indexed: dict[str, dict] = {}
    for item in items:
        item_id = safe_text(item.get("id"))
        if item_id:
            indexed[item_id] = item
    return indexed


def iter_scenes(payload: dict | None) -> list[dict]:
    source = payload if isinstance(payload, dict) else {}
    scenes: list[dict] = []
    for chapter in to_list(source.get("chapters")):
        if not isinstance(chapter, dict):
            continue
        scenes.extend(scene for scene in to_list(chapter.get("scenes")) if isinstance(scene, dict))
    return scenes


def get_scene_blocks(scene: dict | None) -> list[dict]:
    return [block for block in to_list((scene or {}).get("blocks")) if isinstance(block, dict)]


def get_entry_scene(payload: dict | None) -> dict:
    project = get_project(payload)
    scenes = iter_scenes(payload)
    scenes_by_id = index_by_id(scenes)
    entry_scene_id = safe_text(project.get("entrySceneId"))
    if entry_scene_id and entry_scene_id in scenes_by_id:
        return scenes_by_id[entry_scene_id]
    return scenes[0] if scenes else {}


def get_block_choice_options(block: dict | None) -> list[dict]:
    source = block if isinstance(block, dict) else {}
    for key in ("options", "choices", "choiceOptions"):
        options = source.get(key)
        if isinstance(options, list):
            return [option for option in options if isinstance(option, dict)]
    return []


def build_static_runtime_preload_status(preload_report: dict | None) -> dict:
    report = preload_report if isinstance(preload_report, dict) else {}
    summary = dict(report.get("summary") if isinstance(report.get("summary"), dict) else {})
    total_entries = int(summary.get("totalEntries") or len(report.get("entries") or []))
    missing_entries = int(summary.get("missingFileEntries") or summary.get("missingEntries") or 0)
    report_status = safe_text(report.get("status"))
    if total_entries <= 0:
        summary.update(
            {
                "status": "empty",
                "totalEntries": 0,
                "loadedEntries": 0,
                "pendingEntries": 0,
            }
        )
        return summary
    if report_status in {"needs_fix", "missing_manifest"} or missing_entries:
        summary["status"] = "blocked"
        summary["loadedEntries"] = 0
        summary["pendingEntries"] = 0
        summary["missingEntries"] = max(missing_entries, int(summary.get("missingEntries") or 0))
        return summary
    summary["status"] = "ready" if report_status == "ready" else "warming"
    summary["loadedEntries"] = total_entries
    summary["pendingEntries"] = 0
    summary["loadedImageEntries"] = int(summary.get("imageEntries") or 0)
    summary["loadedSoundEntries"] = int(summary.get("soundEntries") or 0)
    summary["readyStreamEntries"] = int(summary.get("streamEntries") or 0)
    return summary


def build_static_scene_prefetch_manifest(payload: dict | None) -> dict:
    entry_scene = get_entry_scene(payload)
    if not entry_scene:
        return build_runtime_scene_prefetch_manifest({}, {"scenesById": {}, "assetsById": {}})
    scenes = iter_scenes(payload)
    scenes_by_id = index_by_id(scenes)
    assets_by_id = index_by_id(get_assets(payload))
    characters_by_id = index_by_id(get_characters(payload))
    blocks = get_scene_blocks(entry_scene)
    first_block = blocks[0] if blocks else {}
    snapshot = build_runtime_scene_prefetch_snapshot(
        entry_scene,
        0,
        scene_id=safe_text(entry_scene.get("id")),
        choice_options=get_block_choice_options(first_block),
        completed=not bool(blocks),
    )
    return build_runtime_scene_prefetch_manifest(
        snapshot,
        {
            "scenesById": scenes_by_id,
            "assetsById": assets_by_id,
            "charactersById": characters_by_id,
        },
        {"blockLookahead": 10, "targetBlockLookahead": 10, "maxEntries": 32},
    )


def build_static_scene_prefetch_status(prefetch_manifest: dict | None) -> dict:
    summary = get_runtime_scene_prefetch_summary(prefetch_manifest)
    total_entries = int(summary.get("totalCount") or 0)
    return {
        "status": "ready" if total_entries else "empty",
        "totalEntries": total_entries,
        "loadedEntries": total_entries,
        "pendingEntries": 0,
    }


def clamp_percent(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        return 0
    return max(0, min(100, int(round(numerator / denominator * 100))))


def get_status_ready_entries(status: dict | None) -> int:
    source = status if isinstance(status, dict) else {}
    if source.get("readyEntries") is not None:
        return int(source.get("readyEntries") or 0)
    return int(source.get("loadedEntries") or 0)


def build_runtime_cache_efficiency_summary(context: dict | None) -> dict:
    safe_context = context if isinstance(context, dict) else {}
    preload_status = (
        safe_context.get("runtimePreloadStatus")
        if isinstance(safe_context.get("runtimePreloadStatus"), dict)
        else {}
    )
    prefetch_status = (
        safe_context.get("runtimeScenePrefetchStatus")
        if isinstance(safe_context.get("runtimeScenePrefetchStatus"), dict)
        else {}
    )
    preload_total = int(preload_status.get("totalEntries") or 0)
    prefetch_total = int(prefetch_status.get("totalEntries") or 0)
    preload_ready = get_status_ready_entries(preload_status)
    prefetch_ready = get_status_ready_entries(prefetch_status)
    preload_cached = int(preload_status.get("cachedEntries") or 0)
    prefetch_cached = int(prefetch_status.get("cachedEntries") or 0)
    preload_pending = int(preload_status.get("pendingEntries") or 0)
    prefetch_pending = int(prefetch_status.get("pendingEntries") or 0)
    total_entries = preload_total + prefetch_total
    ready_entries = preload_ready + prefetch_ready
    cached_entries = preload_cached + prefetch_cached
    loaded_cache_entries = (
        get_loaded_cache_count(safe_context.get("imageCache"))
        + get_loaded_cache_count(safe_context.get("soundCache"))
        + get_loaded_cache_count(safe_context.get("videoPreviewFrameCache"))
    )
    status = "empty"
    if total_entries > 0:
        status = "warming" if preload_pending + prefetch_pending > 0 else "ready"
    return {
        "status": status,
        "totalEntries": total_entries,
        "readyEntries": ready_entries,
        "pendingEntries": preload_pending + prefetch_pending,
        "cachedEntries": cached_entries,
        "loadedCacheEntries": loaded_cache_entries,
        "preloadCachedEntries": preload_cached,
        "prefetchCachedEntries": prefetch_cached,
        "reusePercent": clamp_percent(cached_entries, total_entries),
        "readyPercent": clamp_percent(ready_entries, total_entries),
    }


def build_export_runtime_diagnostics_context(payload: dict | None, preload_report: dict | None = None) -> dict:
    project = get_project(payload)
    entry_scene = get_entry_scene(payload)
    blocks = get_scene_blocks(entry_scene)
    first_block = blocks[0] if blocks else {}
    prefetch_manifest = build_static_scene_prefetch_manifest(payload)
    return {
        "sceneId": safe_text(entry_scene.get("id")) or safe_text(project.get("entrySceneId")),
        "sceneName": safe_text(entry_scene.get("name")) or safe_text(entry_scene.get("title")) or "入口场景",
        "blockIndex": 0,
        "lineType": safe_text(first_block.get("type")) or "入口预检",
        "choiceCount": len(get_block_choice_options(first_block)),
        "statusMessage": "导出包静态诊断：用于发布前检查预热、路线预取和缓存入口。",
        "runtimePreloadStatus": build_static_runtime_preload_status(preload_report),
        "runtimeScenePrefetchStatus": build_static_scene_prefetch_status(prefetch_manifest),
        "runtimeScenePrefetchManifest": prefetch_manifest,
        "imageCache": {},
        "soundCache": {},
        "videoPreviewFrameCache": {},
        "runtimeScenePrefetchedAssetIds": {
            safe_text(entry.get("assetId"))
            for entry in to_list(prefetch_manifest.get("entries"))
            if isinstance(entry, dict) and safe_text(entry.get("assetId"))
        },
    }


def get_export_runtime_diagnostics_status(preload_report: dict, diagnostics_report: dict) -> str:
    preload_status = safe_text(preload_report.get("status"))
    diagnostics_status = safe_text(diagnostics_report.get("status"))
    if preload_status in {"needs_fix", "missing_manifest"} or diagnostics_status == "blocked":
        return "blocked"
    if preload_status in {"needs_review"} or diagnostics_status == "warming":
        return "needs_review"
    return "ready"


def build_export_runtime_diagnostics_summary(payload: dict, preload_report: dict, diagnostics_report: dict, prefetch_manifest: dict) -> dict:
    preload_summary = preload_report.get("summary") if isinstance(preload_report.get("summary"), dict) else {}
    prefetch_summary = get_runtime_scene_prefetch_summary(prefetch_manifest)
    cache_efficiency = (
        diagnostics_report.get("cacheEfficiency")
        if isinstance(diagnostics_report.get("cacheEfficiency"), dict)
        else {}
    )
    return {
        "sceneCount": len(iter_scenes(payload)),
        "preloadStatus": safe_text(preload_report.get("status")) or "unknown",
        "preloadEntries": int(preload_summary.get("totalEntries") or 0),
        "preloadMissingEntries": int(preload_summary.get("missingFileEntries") or preload_summary.get("missingEntries") or 0),
        "prefetchEntries": int(prefetch_summary.get("totalCount") or 0),
        "prefetchImageEntries": int(prefetch_summary.get("imageCount") or 0),
        "prefetchAudioEntries": int(prefetch_summary.get("audioCount") or 0),
        "prefetchVideoEntries": int(prefetch_summary.get("videoCount") or 0),
        "diagnosticIssueCount": int(diagnostics_report.get("issueCount") or 0),
        "diagnosticWarningCount": int(diagnostics_report.get("warningCount") or 0),
        "cacheReadyPercent": int(cache_efficiency.get("readyPercent") or 0),
        "cacheReusePercent": int(cache_efficiency.get("reusePercent") or 0),
        "cacheReuseEntries": int(cache_efficiency.get("cachedEntries") or 0),
    }


def build_export_runtime_diagnostics_report(
    payload: dict | None,
    preload_report: dict | None = None,
    *,
    bundle_dir: object = "",
    generated_at: object = "",
) -> dict:
    safe_payload = payload if isinstance(payload, dict) else {}
    safe_preload_report = preload_report if isinstance(preload_report, dict) else {}
    project = get_project(safe_payload)
    context = build_export_runtime_diagnostics_context(safe_payload, safe_preload_report)
    diagnostics_report = build_runtime_diagnostics_report(context)
    prefetch_manifest = context.get("runtimeScenePrefetchManifest")
    prefetch_manifest = prefetch_manifest if isinstance(prefetch_manifest, dict) else {}
    status = get_export_runtime_diagnostics_status(safe_preload_report, diagnostics_report)
    status_label = {
        "ready": "可发布前复核",
        "needs_review": "需要复核",
        "blocked": "需要先修复",
    }.get(status, status)
    headline = diagnostics_report.get("headline") or "运行诊断已生成。"
    if status == "blocked":
        headline = "运行诊断发现阻塞项；请先修复缺失资源或导出包结构。"
    elif status == "needs_review":
        headline = "运行诊断可用，但仍有启动预热或路线预取观察项需要复核。"
    return {
        "formatVersion": DIAGNOSTICS_FORMAT_VERSION,
        "generatedAt": safe_text(generated_at) or now_iso(),
        "bundleDir": safe_text(bundle_dir),
        "status": status,
        "statusLabel": status_label,
        "headline": headline,
        "project": {
            "projectId": project.get("projectId"),
            "title": project.get("title") or project.get("name") or "未命名项目",
            "language": project.get("language") or "zh-CN",
            "entrySceneId": project.get("entrySceneId"),
        },
        "entry": {
            "sceneId": context.get("sceneId"),
            "sceneName": context.get("sceneName"),
            "blockIndex": context.get("blockIndex"),
            "lineType": context.get("lineType"),
            "choiceCount": context.get("choiceCount"),
        },
        "summary": build_export_runtime_diagnostics_summary(
            safe_payload,
            safe_preload_report,
            diagnostics_report,
            prefetch_manifest,
        ),
        "runtimeDiagnostics": diagnostics_report,
        "runtimePreload": {
            "status": safe_preload_report.get("status"),
            "recommendation": safe_preload_report.get("recommendation"),
            "summary": safe_preload_report.get("summary") or {},
        },
        "runtimeScenePrefetch": {
            "summary": get_runtime_scene_prefetch_summary(prefetch_manifest),
            "targetSceneIds": prefetch_manifest.get("targetSceneIds") or [],
            "entries": prefetch_manifest.get("entries") or [],
        },
        "recommendedCommands": [
            "python3 runtime_player.py --runtime-diagnostics-report .",
            "python3 runtime_player.py --write-runtime-diagnostics-reports .",
        ],
    }


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
    efficiency = build_runtime_cache_efficiency_summary(safe_context)
    total_entries = int(efficiency.get("totalEntries") or 0)
    cached_entries = int(efficiency.get("cachedEntries") or 0)
    ready_percent = int(efficiency.get("readyPercent") or 0)
    reuse_percent = int(efficiency.get("reusePercent") or 0)
    efficiency_tone = "empty"
    if total_entries > 0:
        efficiency_tone = "ready" if ready_percent >= 100 else "warming"
    return [
        build_status_row("图片缓存", f"{image_count} 项", "已解码到内存的背景、CG、立绘和 UI 图片。", "ready" if image_count else "empty"),
        build_status_row("音频缓存", f"{sound_count} 项", f"BGM：{active_bgm} / 语音：{active_voice}", "ready" if sound_count else "empty"),
        build_status_row("视频预览缓存", f"{video_preview_count} 项", "内嵌视频卡片的预览帧缓存。", "ready" if video_preview_count else "empty"),
        build_status_row("路线已预取", f"{prefetched_count} 项", "本轮路线预取已经完成过加载尝试的素材。", "ready" if prefetched_count else "empty"),
        build_status_row(
            "缓存复用效率",
            f"{cached_entries}/{total_entries}",
            f"运行准备率 {ready_percent}% / 复用率 {reuse_percent}% / 内存缓存 {int(efficiency.get('loadedCacheEntries') or 0)} 项。",
            efficiency_tone,
        ),
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
    cache_efficiency = build_runtime_cache_efficiency_summary(safe_context)
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
        "cacheEfficiency": cache_efficiency,
        "sections": sections,
    }


def render_export_runtime_diagnostics_markdown(report: dict | None) -> str:
    safe_report = report if isinstance(report, dict) else {}
    project = safe_report.get("project") if isinstance(safe_report.get("project"), dict) else {}
    entry = safe_report.get("entry") if isinstance(safe_report.get("entry"), dict) else {}
    summary = safe_report.get("summary") if isinstance(safe_report.get("summary"), dict) else {}
    diagnostics = (
        safe_report.get("runtimeDiagnostics")
        if isinstance(safe_report.get("runtimeDiagnostics"), dict)
        else {}
    )
    runtime_preload = (
        safe_report.get("runtimePreload")
        if isinstance(safe_report.get("runtimePreload"), dict)
        else {}
    )
    runtime_prefetch = (
        safe_report.get("runtimeScenePrefetch")
        if isinstance(safe_report.get("runtimeScenePrefetch"), dict)
        else {}
    )
    lines = [
        "# 原生 Runtime 运行诊断报告",
        "",
        f"- 项目：{markdown_value(project.get('title'), '未命名项目')}",
        f"- 状态：{markdown_value(safe_report.get('statusLabel') or safe_report.get('status'))}",
        f"- 生成时间：{markdown_value(safe_report.get('generatedAt'))}",
        f"- 入口场景：{markdown_value(entry.get('sceneName') or entry.get('sceneId'), '未找到入口场景')}",
        f"- 结论：{markdown_value(safe_report.get('headline'), '运行诊断已生成。')}",
        "",
        "## 快速指标",
        "",
        "| 项目 | 值 |",
        "| --- | --- |",
        f"| 场景数 | {int(summary.get('sceneCount') or 0)} |",
        f"| 预热状态 | {markdown_value(summary.get('preloadStatus'), 'unknown')} |",
        f"| 预热条目 / 缺失 | {int(summary.get('preloadEntries') or 0)} / {int(summary.get('preloadMissingEntries') or 0)} |",
        f"| 路线预取条目 | {int(summary.get('prefetchEntries') or 0)} |",
        (
            f"| 预取图片 / 音频 / 视频 | {int(summary.get('prefetchImageEntries') or 0)} / "
            f"{int(summary.get('prefetchAudioEntries') or 0)} / {int(summary.get('prefetchVideoEntries') or 0)} |"
        ),
        f"| 运行准备率 / 复用率 | {int(summary.get('cacheReadyPercent') or 0)}% / {int(summary.get('cacheReusePercent') or 0)}% |",
        f"| 缓存复用条目 | {int(summary.get('cacheReuseEntries') or 0)} |",
        f"| 诊断异常 / 观察项 | {int(summary.get('diagnosticIssueCount') or 0)} / {int(summary.get('diagnosticWarningCount') or 0)} |",
        "",
        "## 运行状态面板",
        "",
    ]
    sections = diagnostics.get("sections") if isinstance(diagnostics.get("sections"), list) else []
    for section in sections:
        if not isinstance(section, dict):
            continue
        lines.extend([f"### {markdown_value(section.get('title'), '诊断')}", "", "| 项目 | 状态 | 说明 |", "| --- | --- | --- |"])
        for row in section.get("rows") or []:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"| {markdown_value(row.get('label'))} | {markdown_value(row.get('value'))} | "
                f"{markdown_value(row.get('detail'))} |"
            )
        lines.append("")
    lines.extend(["## 资源预热", ""])
    lines.append(f"- 状态：{markdown_value(runtime_preload.get('status'), 'unknown')}")
    lines.append(f"- 建议：{markdown_value(runtime_preload.get('recommendation'), '暂无')}")
    preload_summary = runtime_preload.get("summary") if isinstance(runtime_preload.get("summary"), dict) else {}
    size_budget = preload_summary.get("sizeBudget") if isinstance(preload_summary.get("sizeBudget"), dict) else {}
    if size_budget:
        lines.append(
            "- critical 首屏体积："
            f"{markdown_value(size_budget.get('criticalLabel'), '0 B')} / 建议 {markdown_value(size_budget.get('criticalBudgetLabel'), '0 B')}"
        )
        lines.append(
            "- 预热队列总体积："
            f"{markdown_value(size_budget.get('totalLabel'), '0 B')} / 建议 {markdown_value(size_budget.get('totalBudgetLabel'), '0 B')}"
        )
    lines.extend(["", "## 路线预取", ""])
    prefetch_summary = runtime_prefetch.get("summary") if isinstance(runtime_prefetch.get("summary"), dict) else {}
    target_scene_ids = runtime_prefetch.get("targetSceneIds") if isinstance(runtime_prefetch.get("targetSceneIds"), list) else []
    entries = runtime_prefetch.get("entries") if isinstance(runtime_prefetch.get("entries"), list) else []
    lines.append(f"- 目标场景：{len(target_scene_ids)} 个")
    lines.append(f"- 预取条目：{int(prefetch_summary.get('totalCount') or 0)} 个")
    if entries:
        lines.extend(["", "| 素材 | 类型 | 阶段 | 用途 |", "| --- | --- | --- | --- |"])
        for entry_item in entries[:20]:
            if not isinstance(entry_item, dict):
                continue
            lines.append(
                f"| {markdown_value(entry_item.get('name') or entry_item.get('assetId'), '未命名')} | "
                f"{markdown_value(entry_item.get('type'))} | {markdown_value(entry_item.get('phase'))} | "
                f"{markdown_value(entry_item.get('reason'), '路线预取')} |"
            )
        if len(entries) > 20:
            lines.append(f"| 其余素材 | - | - | 还有 {len(entries) - 20} 项 |")
    else:
        lines.append("- 当前入口附近没有可预取素材。")
    commands = safe_report.get("recommendedCommands") if isinstance(safe_report.get("recommendedCommands"), list) else []
    if commands:
        lines.extend(["", "## 可重新生成", "", "```bash"])
        lines.extend(safe_text(command) for command in commands if safe_text(command))
        lines.extend(["```", ""])
    return "\n".join(lines).rstrip() + "\n"
