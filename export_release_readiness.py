from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path


EXPORT_RELEASE_READINESS_JSON_NAME = "release_readiness_summary.json"
EXPORT_RELEASE_READINESS_REPORT_NAME = "release_readiness_summary.md"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def clean_release_text(value: object, fallback: str = "") -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text or fallback


def as_int(value: object, fallback: int = 0) -> int:
    try:
        return int(value or fallback)
    except (TypeError, ValueError):
        return fallback


def clamp_score(value: int) -> int:
    return max(0, min(100, value))


def make_readiness_issue(severity: str, code: str, title: str, detail: str, suggestion: str) -> dict:
    return {
        "severity": severity,
        "code": code,
        "title": title,
        "detail": detail,
        "suggestion": suggestion,
    }


def get_manifest_project(manifest: dict) -> dict:
    project = manifest.get("project") if isinstance(manifest, dict) else {}
    return project if isinstance(project, dict) else {}


def get_manifest_assets(manifest: dict) -> dict:
    assets = manifest.get("assets") if isinstance(manifest, dict) else {}
    return assets if isinstance(assets, dict) else {}


def get_manifest_runtime(manifest: dict) -> dict:
    runtime = manifest.get("runtime") if isinstance(manifest, dict) else {}
    return runtime if isinstance(runtime, dict) else {}


def get_unlockable_summary(unlockable_manifest: dict | None) -> dict:
    if not isinstance(unlockable_manifest, dict):
        return {}
    summary = unlockable_manifest.get("summary")
    return summary if isinstance(summary, dict) else {}


def get_story_route_summary(story_route_map: dict | None) -> dict:
    if not isinstance(story_route_map, dict):
        return {}
    summary = story_route_map.get("summary")
    return summary if isinstance(summary, dict) else {}


def get_localization_summary(localization_audit: dict | None) -> dict:
    if not isinstance(localization_audit, dict):
        return {}
    summary = localization_audit.get("summary")
    return summary if isinstance(summary, dict) else {}


def build_release_readiness_issues(
    manifest: dict,
    unlockable_manifest: dict | None,
    missing_assets: list[dict],
    story_route_map: dict | None = None,
    localization_audit: dict | None = None,
) -> list[dict]:
    project = get_manifest_project(manifest)
    runtime = get_manifest_runtime(manifest)
    unlockable_summary = get_unlockable_summary(unlockable_manifest)
    story_route_summary = get_story_route_summary(story_route_map)
    localization_summary = get_localization_summary(localization_audit)
    issues: list[dict] = []

    scene_count = as_int(project.get("sceneCount"))
    chapter_count = as_int(project.get("chapterCount"))
    if chapter_count <= 0 or scene_count <= 0:
        issues.append(
            make_readiness_issue(
                "blocker",
                "no_playable_story",
                "没有可试玩剧情",
                "导出清单里没有检测到章节或场景，测试员打开后很可能只能看到空项目。",
                "先在编辑器里创建至少一个章节、一个场景和一段正文，再重新导出。",
            )
        )

    if not clean_release_text(project.get("entrySceneId")) and scene_count > 0:
        issues.append(
            make_readiness_issue(
                "warning",
                "missing_entry_scene",
                "入口场景未明确设置",
                "项目里有场景，但导出清单没有记录明确的 entrySceneId。",
                "在项目设置中指定首个进入的场景，避免不同 Runtime 入口选择不一致。",
            )
        )

    if missing_assets:
        preview_names = "、".join(
            clean_release_text(asset.get("name") or asset.get("id"), "未命名素材") for asset in missing_assets[:5]
        )
        more = f" 等 {len(missing_assets)} 项" if len(missing_assets) > 5 else ""
        issues.append(
            make_readiness_issue(
                "blocker",
                "missing_export_assets",
                "导出包存在缺失素材",
                f"导出流程记录到缺失素材：{preview_names}{more}。",
                "先在素材库重新绑定文件，或删除不再使用的素材引用，再重新导出。",
            )
        )

    if story_route_summary and not story_route_summary.get("entrySceneExists", True):
        issues.append(
            make_readiness_issue(
                "blocker",
                "story_entry_scene_missing",
                "剧情入口场景不存在",
                "剧情路线图没有找到项目设置里的入口场景。",
                "在项目设置里重新指定存在的入口场景，再重新导出。",
            )
        )

    broken_route_count = as_int(story_route_summary.get("brokenRouteCount"))
    if broken_route_count:
        issues.append(
            make_readiness_issue(
                "blocker",
                "story_route_broken_links",
                "剧情路线存在坏跳转",
                f"剧情路线图记录到 {broken_route_count} 条目标不存在的跳转。",
                "打开 story_route_map.md，逐条修复坏跳转后重新导出。",
            )
        )

    unreachable_scene_count = as_int(story_route_summary.get("unreachableSceneCount"))
    if unreachable_scene_count:
        issues.append(
            make_readiness_issue(
                "warning",
                "story_route_unreachable_scenes",
                "存在入口不可达场景",
                f"剧情路线图记录到 {unreachable_scene_count} 个从入口场景无法自然抵达的场景。",
                "确认这些场景是隐藏内容、调试场景还是漏接路线；需要公开试玩的场景应接回主流程。",
            )
        )

    runtime_warning = clean_release_text(runtime.get("warning"))
    if runtime_warning:
        issues.append(
            make_readiness_issue(
                "warning",
                "runtime_warning",
                "目标平台运行方式需要复核",
                runtime_warning,
                "按随包 README 和试玩指南完成一次目标系统实机启动确认。",
            )
        )

    unlockable_warnings = as_int(unlockable_summary.get("warningCount"))
    missing_unlockables = as_int(unlockable_summary.get("missingEntryCount"))
    if unlockable_warnings or missing_unlockables:
        issues.append(
            make_readiness_issue(
                "warning",
                "unlockable_coverage_warnings",
                "EXTRA / 回想 / 图鉴覆盖需要复核",
                f"可解锁内容报告记录到 {unlockable_warnings} 项警告、{missing_unlockables} 个缺失条目。",
                "打开 unlockable_content_report.md，优先确认 CG、BGM、语音回听、结局和成就是否符合预期。",
            )
        )

    ending_count = as_int(unlockable_summary.get("endingCount"))
    reachable_ending_count = as_int(unlockable_summary.get("reachableEndingCount"))
    if ending_count > 0 and reachable_ending_count < ending_count:
        issues.append(
            make_readiness_issue(
                "warning",
                "unreachable_endings",
                "存在不可达结局",
                f"结局可达数量为 {reachable_ending_count}/{ending_count}。",
                "检查选择分支、gotoSceneId 和条件变量，确认每个结局都能从入口路线走到。",
            )
        )

    language_count = as_int(localization_summary.get("languageCount"), 1)
    missing_translation_count = as_int(localization_summary.get("missingTranslationCount"))
    if language_count > 1 and missing_translation_count:
        completion_percent = as_int(localization_summary.get("completionPercent"))
        issues.append(
            make_readiness_issue(
                "warning",
                "localization_missing_translations",
                "多语言翻译不完整",
                f"本地化报告记录到 {missing_translation_count} 条缺失译文，当前覆盖率约 {completion_percent}%。",
                "打开 localization_audit.md，优先补齐主线正文、选项和角色名。",
            )
        )

    return issues


def calculate_release_readiness_score(
    issues: list[dict],
    manifest: dict,
    unlockable_manifest: dict | None,
    story_route_map: dict | None = None,
    localization_audit: dict | None = None,
) -> int:
    project = get_manifest_project(manifest)
    assets = get_manifest_assets(manifest)
    unlockable_summary = get_unlockable_summary(unlockable_manifest)
    story_route_summary = get_story_route_summary(story_route_map)
    localization_summary = get_localization_summary(localization_audit)
    score = 100
    score -= 34 * sum(1 for issue in issues if issue.get("severity") == "blocker")
    score -= 9 * sum(1 for issue in issues if issue.get("severity") == "warning")
    if as_int(project.get("sceneCount")) < 2:
        score -= 4
    if as_int(assets.get("copiedCount")) == 0:
        score -= 3
    readiness_percent = as_int(unlockable_summary.get("readinessPercent"), 100)
    if readiness_percent and readiness_percent < 100:
        score -= min(12, max(1, round((100 - readiness_percent) / 8)))
    unreachable_scene_count = as_int(story_route_summary.get("unreachableSceneCount"))
    if unreachable_scene_count:
        score -= min(12, unreachable_scene_count * 3)
    language_count = as_int(localization_summary.get("languageCount"), 1)
    localization_completion = as_int(localization_summary.get("completionPercent"), 100)
    if language_count > 1 and localization_completion < 100:
        score -= min(12, max(2, round((100 - localization_completion) / 7)))
    return clamp_score(score)


def get_release_readiness_gate(score: int, issues: list[dict]) -> dict:
    blocker_count = sum(1 for issue in issues if issue.get("severity") == "blocker")
    warning_count = sum(1 for issue in issues if issue.get("severity") == "warning")
    if blocker_count:
        return {
            "status": "blocked",
            "label": "不建议发布",
            "summary": f"发现 {blocker_count} 个阻塞项，建议修复后重新导出。",
        }
    if warning_count or score < 90:
        return {
            "status": "needs_review",
            "label": "可试玩但需复核",
            "summary": f"没有阻塞项，但仍有 {warning_count} 个发布前复核点。",
        }
    return {
        "status": "ready",
        "label": "可进入试玩分发",
        "summary": "没有发现阻塞项，适合发给测试员进行体验验收。",
    }


def build_export_release_readiness_summary(
    *,
    project: dict,
    manifest: dict,
    missing_assets: list[dict] | None = None,
    unlockable_manifest: dict | None = None,
    story_route_map: dict | None = None,
    localization_audit: dict | None = None,
    report_files: list[str] | None = None,
    platform_notes: list[str] | None = None,
) -> dict:
    missing_assets = missing_assets or []
    issues = build_release_readiness_issues(
        manifest,
        unlockable_manifest,
        missing_assets,
        story_route_map,
        localization_audit,
    )
    score = calculate_release_readiness_score(
        issues,
        manifest,
        unlockable_manifest,
        story_route_map,
        localization_audit,
    )
    gate = get_release_readiness_gate(score, issues)
    manifest_project = get_manifest_project(manifest)
    manifest_assets = get_manifest_assets(manifest)
    unlockable_summary = get_unlockable_summary(unlockable_manifest)
    localization_summary = get_localization_summary(localization_audit)

    return {
        "formatVersion": 1,
        "generatedAt": now_iso(),
        "project": {
            "title": clean_release_text(project.get("title") or manifest_project.get("title"), "未命名项目"),
            "projectId": clean_release_text(project.get("projectId") or manifest_project.get("projectId")),
            "language": clean_release_text(manifest_project.get("language")),
            "chapterCount": as_int(manifest_project.get("chapterCount")),
            "sceneCount": as_int(manifest_project.get("sceneCount")),
            "characterCount": as_int(manifest_project.get("characterCount")),
            "entrySceneId": clean_release_text(manifest_project.get("entrySceneId")),
        },
        "target": {
            "id": clean_release_text((manifest.get("engine") or {}).get("exportTarget")),
            "label": clean_release_text((manifest.get("engine") or {}).get("exportTargetLabel"), "导出包"),
            "releaseVersion": clean_release_text((manifest.get("engine") or {}).get("releaseVersion"), "preview"),
            "buildId": clean_release_text(manifest.get("buildId")),
        },
        "qualityGate": gate,
        "score": score,
        "metrics": {
            "copiedAssets": as_int(manifest_assets.get("copiedCount")),
            "missingAssets": len(missing_assets),
            "unlockableReadinessPercent": as_int(unlockable_summary.get("readinessPercent")),
            "unlockableWarnings": as_int(unlockable_summary.get("warningCount")),
            "readyUnlockables": as_int(unlockable_summary.get("readyEntryCount")),
            "totalUnlockables": as_int(unlockable_summary.get("totalEntryCount")),
            "reachableEndings": as_int(unlockable_summary.get("reachableEndingCount")),
            "totalEndings": as_int(unlockable_summary.get("endingCount")),
            "routeCount": as_int(get_story_route_summary(story_route_map).get("routeCount")),
            "brokenRoutes": as_int(get_story_route_summary(story_route_map).get("brokenRouteCount")),
            "unreachableScenes": as_int(get_story_route_summary(story_route_map).get("unreachableSceneCount")),
            "localizationCompletionPercent": as_int(localization_summary.get("completionPercent"), 100),
            "missingTranslations": as_int(localization_summary.get("missingTranslationCount")),
            "localizationLanguageCount": as_int(localization_summary.get("languageCount"), 1),
        },
        "issues": issues,
        "reportFiles": [clean_release_text(item) for item in (report_files or []) if clean_release_text(item)],
        "platformNotes": [clean_release_text(item) for item in (platform_notes or []) if clean_release_text(item)],
        "nextSteps": build_release_readiness_next_steps(gate, issues),
    }


def build_release_readiness_next_steps(gate: dict, issues: list[dict]) -> list[str]:
    if gate.get("status") == "ready":
        return [
            "把整个导出文件夹或压缩包发给测试员，不要只发入口文件。",
            "请测试员按 README_试玩验收先看这里.md 完成首轮体验验收。",
            "发布前保留 export_manifest.json 和来源指纹文件，方便回溯版本。",
        ]
    steps = [clean_release_text(issue.get("suggestion")) for issue in issues[:5] if clean_release_text(issue.get("suggestion"))]
    if len(issues) > 5:
        steps.append(f"其余 {len(issues) - 5} 个问题可在 JSON 摘要里继续查看。")
    return steps or ["先按随包 README 完成一次人工复核。"]


def markdown_cell(value: object) -> str:
    return clean_release_text(value, "-").replace("|", "\\|")


def build_export_release_readiness_markdown(summary: dict) -> str:
    project = summary.get("project") if isinstance(summary.get("project"), dict) else {}
    target = summary.get("target") if isinstance(summary.get("target"), dict) else {}
    gate = summary.get("qualityGate") if isinstance(summary.get("qualityGate"), dict) else {}
    metrics = summary.get("metrics") if isinstance(summary.get("metrics"), dict) else {}
    issues = summary.get("issues") if isinstance(summary.get("issues"), list) else []
    report_files = summary.get("reportFiles") if isinstance(summary.get("reportFiles"), list) else []
    platform_notes = summary.get("platformNotes") if isinstance(summary.get("platformNotes"), list) else []
    next_steps = summary.get("nextSteps") if isinstance(summary.get("nextSteps"), list) else []

    lines = [
        "# 发布试玩就绪摘要",
        "",
        f"- 项目：{markdown_cell(project.get('title'))}",
        f"- 导出目标：{markdown_cell(target.get('label'))}",
        f"- 版本：{markdown_cell(target.get('releaseVersion'))}",
        f"- 结论：{markdown_cell(gate.get('label'))}",
        f"- 就绪分：{markdown_cell(summary.get('score'))}/100",
        f"- 摘要：{markdown_cell(gate.get('summary'))}",
        "",
        "## 核心指标",
        "",
        "| 指标 | 数值 |",
        "| --- | ---: |",
        f"| 章节 | {markdown_cell(project.get('chapterCount'))} |",
        f"| 场景 | {markdown_cell(project.get('sceneCount'))} |",
        f"| 角色 | {markdown_cell(project.get('characterCount'))} |",
        f"| 已复制素材 | {markdown_cell(metrics.get('copiedAssets'))} |",
        f"| 缺失素材 | {markdown_cell(metrics.get('missingAssets'))} |",
        f"| 可解锁内容就绪度 | {markdown_cell(metrics.get('unlockableReadinessPercent'))}% |",
        f"| 可达结局 | {markdown_cell(metrics.get('reachableEndings'))}/{markdown_cell(metrics.get('totalEndings'))} |",
        f"| 本地化覆盖率 | {markdown_cell(metrics.get('localizationCompletionPercent'))}% |",
        f"| 缺失译文 | {markdown_cell(metrics.get('missingTranslations'))} |",
        "",
        "## 优先处理",
        "",
    ]
    if issues:
        for issue in issues:
            lines.append(
                f"- [{markdown_cell(issue.get('severity'))}] {markdown_cell(issue.get('title'))}："
                f"{markdown_cell(issue.get('detail'))} 建议：{markdown_cell(issue.get('suggestion'))}"
            )
    else:
        lines.append("- 暂未发现阻塞项或警告。")

    lines.extend(["", "## 建议下一步", ""])
    for index, step in enumerate(next_steps, start=1):
        lines.append(f"{index}. {markdown_cell(step)}")

    lines.extend(["", "## 相关随包报告", ""])
    if report_files:
        lines.extend(f"- `{markdown_cell(report)}`" for report in report_files)
    else:
        lines.append("- 暂无额外报告。")

    if platform_notes:
        lines.extend(["", "## 平台备注", ""])
        lines.extend(f"- {markdown_cell(note)}" for note in platform_notes)

    lines.append("")
    return "\n".join(lines)


def write_export_release_readiness_files(
    target_dir: Path,
    *,
    project: dict,
    manifest: dict,
    missing_assets: list[dict] | None = None,
    unlockable_manifest: dict | None = None,
    story_route_map: dict | None = None,
    localization_audit: dict | None = None,
    report_files: list[str] | None = None,
    platform_notes: list[str] | None = None,
) -> dict:
    summary = build_export_release_readiness_summary(
        project=project,
        manifest=manifest,
        missing_assets=missing_assets,
        unlockable_manifest=unlockable_manifest,
        story_route_map=story_route_map,
        localization_audit=localization_audit,
        report_files=report_files,
        platform_notes=platform_notes,
    )
    json_path = target_dir / EXPORT_RELEASE_READINESS_JSON_NAME
    markdown_path = target_dir / EXPORT_RELEASE_READINESS_REPORT_NAME
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(build_export_release_readiness_markdown(summary), encoding="utf-8")
    return {
        "releaseReadinessSummaryName": json_path.name,
        "releaseReadinessSummaryPath": str(json_path),
        "releaseReadinessReportName": markdown_path.name,
        "releaseReadinessReportPath": str(markdown_path),
        "releaseReadinessStatus": summary["qualityGate"]["status"],
        "releaseReadinessLabel": summary["qualityGate"]["label"],
        "releaseReadinessScore": summary["score"],
        "releaseReadinessIssueCount": len(summary["issues"]),
    }


__all__ = [
    "EXPORT_RELEASE_READINESS_JSON_NAME",
    "EXPORT_RELEASE_READINESS_REPORT_NAME",
    "build_export_release_readiness_markdown",
    "build_export_release_readiness_summary",
    "write_export_release_readiness_files",
]
