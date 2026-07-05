from __future__ import annotations

from datetime import datetime


DEFAULT_EXPORT_TARGET_NATIVE_RUNTIME = "native_runtime"
DEFAULT_EXPORT_RELEASE_VERSION = "1.0.0-preview"

DEFAULT_REPORT_NAMES = {
    "releaseCheck": "native-runtime-release-check.json",
    "releaseCandidateReport": "native-runtime-release-candidate-report.json",
    "asset3dDigest": "native-runtime-3d-risk-digest.json",
    "releaseControlReport": "native-runtime-release-control-report.md",
    "releaseControlJson": "native-runtime-release-control-report.json",
    "fileIntegrityReport": "native-runtime-file-integrity.json",
    "fileIntegrityMarkdown": "native-runtime-file-integrity.md",
    "vnBaselineQualityMarkdown": "native-runtime-vn-baseline-quality.md",
    "vnBaselineQualityJson": "native-runtime-vn-baseline-quality.json",
    "performanceBudgetMarkdown": "native-runtime-performance-budget.md",
    "performanceBudgetJson": "native-runtime-performance-budget.json",
}


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def as_dict(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def as_list(value: object) -> list:
    return value if isinstance(value, list) else []


def as_int(value: object, fallback: int = 0) -> int:
    try:
        return int(value or fallback)
    except (TypeError, ValueError):
        return fallback


def build_empty_3d_asset_digest() -> dict:
    return {
        "status": "ready",
        "headline": "没有 3D 资产风险",
        "summaryLine": "未检测到需要复核的 3D 资产。",
        "metrics": [],
        "riskCounts": {},
        "issueAssetIds": [],
        "issueAssets": [],
        "topIssues": [],
        "recommendations": [],
    }


def normalize_report_names(report_names: dict | None = None) -> dict:
    names = dict(DEFAULT_REPORT_NAMES)
    if isinstance(report_names, dict):
        for key, value in report_names.items():
            text = str(value or "").strip()
            if text:
                names[str(key)] = text
    return names


def get_native_runtime_release_control_status(
    release_check_payload: dict | None,
    rc_report_payload: dict | None,
    asset3d_digest: dict | None,
    performance_budget_payload: dict | None = None,
    vn_baseline_quality_payload: dict | None = None,
) -> dict:
    release_summary = as_dict(as_dict(release_check_payload).get("summary"))
    rc_summary = as_dict(as_dict(rc_report_payload).get("summary"))
    release_status = str(as_dict(release_check_payload).get("status") or "unavailable")
    rc_status = str(as_dict(rc_report_payload).get("status") or "unavailable")
    asset_status = str(as_dict(asset3d_digest).get("status") or "unavailable")
    performance_status = str(as_dict(performance_budget_payload).get("status") or "unavailable")
    performance_summary = as_dict(as_dict(performance_budget_payload).get("summary"))
    vn_status = str(as_dict(vn_baseline_quality_payload).get("status") or "unavailable")
    vn_summary = as_dict(as_dict(vn_baseline_quality_payload).get("summary"))

    release_errors = as_int(release_summary.get("errors"))
    blockers = as_int(rc_summary.get("blockers"))
    optional_failures = as_int(rc_summary.get("optionalFailures"))
    warnings = as_int(rc_summary.get("warnings"))
    has_3d_issues = bool(as_list(as_dict(asset3d_digest).get("topIssues")))

    if (
        release_status == "fail"
        or rc_status == "blocked"
        or performance_status == "needs_fix"
        or release_errors
        or blockers
        or as_int(vn_summary.get("warnCount"))
        or as_int(performance_summary.get("hardCount"))
    ):
        return {
            "status": "blocked",
            "label": "阻塞发布",
            "summary": "存在发布阻塞项、VN 基础体验缺口或性能预算硬问题，应先修复再进入三系统打包或分发。",
        }
    if (
        release_status == "unavailable"
        or rc_status == "unavailable"
        or asset_status == "unavailable"
        or vn_status == "unavailable"
        or performance_status in {"unavailable", "needs_review"}
        or optional_failures
        or warnings
        or has_3d_issues
        or as_int(vn_summary.get("softCount"))
        or as_int(performance_summary.get("warnCount"))
        or as_int(performance_summary.get("softCount"))
    ):
        return {
            "status": "needs_review",
            "label": "需要复核",
            "summary": "主链没有阻塞项，但仍有警告、可选能力失败、资产风险、VN 润色项或性能预算风险需要发布前确认。",
        }
    return {
        "status": "ready",
        "label": "可进入发布候选",
        "summary": "导出包自检、RC 汇总和 3D 风险摘要没有发现阻塞项。",
    }


def build_native_runtime_release_control_next_steps(
    release_check_payload: dict | None,
    rc_report_payload: dict | None,
    asset3d_digest: dict | None,
    performance_budget_payload: dict | None,
    vn_baseline_quality_payload: dict | None,
    quality_gate: dict,
) -> list[str]:
    steps: list[str] = []

    def add_step(value: object) -> None:
        text = str(value or "").strip()
        if text and text not in steps:
            steps.append(text)

    if quality_gate.get("status") == "blocked":
        add_step("先修复发布自检或 RC 报告里的阻塞项，再重新导出原生 Runtime 包。")
    elif quality_gate.get("status") == "needs_review":
        add_step("发布前复核警告项、3D 风险和目标系统 Preview 点测结果。")
    else:
        add_step("在目标系统运行 Preview 包，完成一次人工逐按钮长流程点测。")

    for action in as_list(as_dict(rc_report_payload).get("nextActions")):
        add_step(action)

    for issue in as_list(as_dict(release_check_payload).get("issues"))[:5]:
        if isinstance(issue, dict):
            add_step(issue.get("suggestion") or issue.get("message"))

    for issue in as_list(as_dict(asset3d_digest).get("topIssues")):
        if not isinstance(issue, dict):
            continue
        name = issue.get("name") or issue.get("assetId") or "未命名 3D 资产"
        action = issue.get("recommendedAction") or issue.get("summary") or "复核 3D 资产导入状态。"
        add_step(f"复核 3D 资产「{name}」：{action}")
    for recommendation in as_list(as_dict(asset3d_digest).get("recommendations")):
        add_step(recommendation)

    for issue in as_list(as_dict(vn_baseline_quality_payload).get("issues"))[:5]:
        if isinstance(issue, dict):
            title = issue.get("title") or issue.get("code") or "VN 基础质感"
            suggestion = issue.get("suggestion") or issue.get("detail") or "复核基础视觉小说体验。"
            add_step(f"处理 VN 基础质感「{title}」：{suggestion}")

    for issue in as_list(as_dict(performance_budget_payload).get("issues"))[:5]:
        if isinstance(issue, dict):
            title = issue.get("title") or issue.get("code") or "性能预算"
            suggestion = issue.get("suggestion") or issue.get("detail") or "复核素材体积、包体和剧情规模。"
            add_step(f"处理性能预算「{title}」：{suggestion}")

    return steps[:10]


def build_native_runtime_release_control_payload(
    export_payload: dict,
    release_check_payload: dict | None,
    rc_report_payload: dict | None,
    asset3d_digest: dict | None,
    performance_budget_payload: dict | None = None,
    vn_baseline_quality_payload: dict | None = None,
    *,
    report_names: dict | None = None,
    export_target: str = DEFAULT_EXPORT_TARGET_NATIVE_RUNTIME,
    default_release_version: str = DEFAULT_EXPORT_RELEASE_VERSION,
    generated_at: str | None = None,
) -> dict:
    names = normalize_report_names(report_names)
    export_payload = as_dict(export_payload)
    project = as_dict(export_payload.get("project"))
    build_info = as_dict(export_payload.get("buildInfo"))
    release_summary = as_dict(as_dict(release_check_payload).get("summary"))
    release_issues = as_list(as_dict(release_check_payload).get("issues"))
    rc_summary = as_dict(as_dict(rc_report_payload).get("summary"))
    readiness = as_dict(as_dict(rc_report_payload).get("readinessEstimate"))
    performance_summary = as_dict(as_dict(performance_budget_payload).get("summary"))
    vn_baseline_summary = as_dict(as_dict(vn_baseline_quality_payload).get("summary")) or {
        "statusLabel": "未生成",
        "issueCount": 1,
        "warnCount": 1,
        "softCount": 0,
    }
    vn_baseline_metrics = as_dict(as_dict(vn_baseline_quality_payload).get("metrics"))
    quality_gate = get_native_runtime_release_control_status(
        release_check_payload,
        rc_report_payload,
        asset3d_digest,
        performance_budget_payload,
        vn_baseline_quality_payload,
    )
    next_steps = build_native_runtime_release_control_next_steps(
        release_check_payload,
        rc_report_payload,
        asset3d_digest,
        performance_budget_payload,
        vn_baseline_quality_payload,
        quality_gate,
    )

    return {
        "formatVersion": 1,
        "generatedAt": generated_at or now_iso(),
        "engine": {
            "name": "Canvasia Engine",
            "target": export_target,
            "targetLabel": "原生 Runtime 包",
            "runtimeMode": build_info.get("runtimeMode") or "pygame_native",
            "releaseVersion": build_info.get("releaseVersion") or default_release_version,
        },
        "project": {
            "projectId": project.get("projectId"),
            "title": project.get("title") or "未命名项目",
            "language": project.get("language") or "zh-CN",
            "entrySceneId": project.get("entrySceneId"),
            "resolution": project.get("resolution") or {"width": 1280, "height": 720},
        },
        "qualityGate": quality_gate,
        "releaseCheck": {
            "status": as_dict(release_check_payload).get("status") or "unavailable",
            "summary": release_summary,
            "topIssues": release_issues[:8],
        },
        "releaseCandidate": {
            "status": as_dict(rc_report_payload).get("status") or "unavailable",
            "summary": rc_summary,
            "readinessEstimate": readiness,
            "videoStrategy": as_dict(as_dict(rc_report_payload).get("videoStrategy")),
            "commercialReleaseGaps": as_list(as_dict(rc_report_payload).get("commercialReleaseGaps")),
        },
        "asset3d": as_dict(asset3d_digest) or build_empty_3d_asset_digest(),
        "vnBaselineQuality": {
            "status": as_dict(vn_baseline_quality_payload).get("status") or "unavailable",
            "summary": vn_baseline_summary,
            "metrics": vn_baseline_metrics,
            "topIssues": as_list(as_dict(vn_baseline_quality_payload).get("issues"))[:8],
            "markdown": names["vnBaselineQualityMarkdown"],
            "json": names["vnBaselineQualityJson"],
        },
        "performanceBudget": {
            "status": as_dict(performance_budget_payload).get("status") or "unavailable",
            "summary": performance_summary,
            "assetGroups": as_dict(as_dict(performance_budget_payload).get("assetGroups")),
            "budgets": as_dict(as_dict(performance_budget_payload).get("budgets")),
            "topIssues": as_list(as_dict(performance_budget_payload).get("issues"))[:8],
            "markdown": names["performanceBudgetMarkdown"],
            "json": names["performanceBudgetJson"],
        },
        "nextSteps": next_steps,
        "includedReports": names,
    }


def build_native_runtime_release_control_markdown(
    payload: dict,
    *,
    default_release_version: str = DEFAULT_EXPORT_RELEASE_VERSION,
) -> str:
    payload = as_dict(payload)
    project = as_dict(payload.get("project"))
    engine = as_dict(payload.get("engine"))
    quality_gate = as_dict(payload.get("qualityGate"))
    release_check = as_dict(payload.get("releaseCheck"))
    release_candidate = as_dict(payload.get("releaseCandidate"))
    asset3d = as_dict(payload.get("asset3d"))
    vn_baseline = as_dict(payload.get("vnBaselineQuality"))
    performance_budget = as_dict(payload.get("performanceBudget"))
    readiness = as_dict(release_candidate.get("readinessEstimate"))
    release_summary = as_dict(release_check.get("summary"))
    rc_summary = as_dict(release_candidate.get("summary"))
    asset_metrics = as_list(asset3d.get("metrics"))
    vn_summary = as_dict(vn_baseline.get("summary"))
    vn_metrics = as_dict(vn_baseline.get("metrics"))
    performance_summary = as_dict(performance_budget.get("summary"))
    performance_asset_groups = as_dict(performance_budget.get("assetGroups"))
    next_steps = as_list(payload.get("nextSteps"))
    included_reports = normalize_report_names(as_dict(payload.get("includedReports")))

    lines = [
        "# 原生 Runtime 发布总控报告",
        "",
        f"- 项目：{project.get('title') or '未命名项目'}",
        f"- 版本：{engine.get('releaseVersion') or default_release_version}",
        f"- 生成时间：{payload.get('generatedAt') or now_iso()}",
        f"- 总体状态：{quality_gate.get('label') or '需要复核'}",
        "",
        "## 总结",
        "",
        quality_gate.get("summary") or "请结合随包 JSON 报告复核导出状态。",
        "",
        "## 核心指标",
        "",
        "| 项目 | 值 |",
        "| --- | --- |",
        f"| 发布自检 | {release_check.get('status') or 'unavailable'} |",
        f"| 自检错误 / 警告 | {as_int(release_summary.get('errors'))} / {as_int(release_summary.get('warnings'))} |",
        f"| RC 状态 | {release_candidate.get('status') or 'unavailable'} |",
        f"| RC 阻塞 / 可选失败 / 警告 | {as_int(rc_summary.get('blockers'))} / {as_int(rc_summary.get('optionalFailures'))} / {as_int(rc_summary.get('warnings'))} |",
        f"| 桌面 Preview 估算 | {readiness.get('desktopPreviewPercent', 'n/a')}% |",
        f"| 商业桌面估算 | {readiness.get('commercialDesktopPercent', 'n/a')}% |",
        f"| 3D 摘要 | {asset3d.get('summaryLine') or '未生成'} |",
        f"| VN 基础质感 | {vn_summary.get('statusLabel') or vn_baseline.get('status') or '未生成'} |",
        f"| 性能预算 | {performance_summary.get('statusLabel') or performance_budget.get('status') or '未生成'} |",
        "",
    ]

    if vn_baseline:
        lines.extend(["## VN 基础质感", "", "| 指标 | 值 |", "| --- | --- |"])
        for label, value in [
            ("状态", vn_summary.get("statusLabel") or vn_baseline.get("status")),
            ("问题 / 缺口 / 润色项", f"{as_int(vn_summary.get('issueCount'))} / {as_int(vn_summary.get('warnCount'))} / {as_int(vn_summary.get('softCount'))}"),
            ("场景 / 文本 / 选项", f"{as_int(vn_metrics.get('storySceneCount'))} / {as_int(vn_metrics.get('dialogueCount')) + as_int(vn_metrics.get('narrationCount'))} / {as_int(vn_metrics.get('choiceCount'))}"),
            ("BGM / 语音 / CG 素材", f"{as_int(vn_metrics.get('bgmAssetCount'))} / {as_int(vn_metrics.get('voiceAssetCount'))} / {as_int(vn_metrics.get('cgAssetCount'))}"),
        ]:
            lines.append(f"| {label} | {value or '0'} |")
        top_vn_issues = as_list(vn_baseline.get("topIssues"))
        if top_vn_issues:
            lines.extend(["", "优先处理："])
            for issue in top_vn_issues[:5]:
                if isinstance(issue, dict):
                    lines.append(f"- {issue.get('title') or 'VN 基础质感'}：{issue.get('suggestion') or issue.get('detail') or '需要复核'}")
        lines.append("")

    if performance_budget:
        lines.extend(["## 性能预算", "", "| 指标 | 值 |", "| --- | --- |"])
        for label, value in [
            ("状态", performance_summary.get("statusLabel") or performance_budget.get("status")),
            ("总素材 / 已引用", f"{as_int(performance_summary.get('assetCount'))} / {as_int(performance_summary.get('referencedAssetCount'))}"),
            ("总体积 / 已引用体积", f"{performance_summary.get('totalAssetLabel') or '0 B'} / {performance_summary.get('referencedAssetLabel') or '0 B'}"),
            ("缺失引用素材", performance_summary.get("missingReferencedAssetCount")),
            ("未使用随包素材", performance_summary.get("unreferencedExistingAssetCount")),
            ("场景 / 卡片", f"{as_int(performance_summary.get('sceneCount'))} / {as_int(performance_summary.get('storyBlockCount'))}"),
            ("图片 / 音频 / 视频体积", " / ".join(
                str(as_dict(performance_asset_groups.get(key)).get("label") or "0 B")
                for key in ("image", "audio", "video")
            )),
            ("硬问题 / 警告 / 提醒", f"{as_int(performance_summary.get('hardCount'))} / {as_int(performance_summary.get('warnCount'))} / {as_int(performance_summary.get('softCount'))}"),
        ]:
            lines.append(f"| {label} | {value or '0'} |")
        top_performance_issues = as_list(performance_budget.get("topIssues"))
        if top_performance_issues:
            lines.extend(["", "优先处理："])
            for issue in top_performance_issues[:5]:
                if isinstance(issue, dict):
                    lines.append(f"- {issue.get('title') or '性能预算'}：{issue.get('suggestion') or issue.get('detail') or '需要复核'}")
        lines.append("")

    if asset_metrics:
        lines.extend(["## 3D 风险快照", "", "| 指标 | 值 |", "| --- | --- |"])
        for metric in asset_metrics:
            if isinstance(metric, dict):
                lines.append(f"| {metric.get('label') or '指标'} | {metric.get('value') or '-'} |")
        lines.append("")

    top_issues = as_list(asset3d.get("topIssues"))
    if top_issues:
        lines.extend(["## 优先处理 3D 资产", ""])
        for issue in top_issues:
            if isinstance(issue, dict):
                lines.append(
                    f"- {issue.get('name') or issue.get('assetId') or '未命名 3D 资产'}："
                    f"{issue.get('summary') or issue.get('statusLabel') or '需要复核'}"
                )
        lines.append("")

    lines.extend(["## 下一步", ""])
    for index, step in enumerate(next_steps or ["完成目标系统实机点测。"], start=1):
        lines.append(f"{index}. {step}")
    lines.extend(["", "## 随包文件", ""])
    for key in (
        "releaseCheck",
        "releaseCandidateReport",
        "asset3dDigest",
        "vnBaselineQualityMarkdown",
        "performanceBudgetMarkdown",
        "releaseControlJson",
    ):
        lines.append(f"- `{included_reports[key]}`")
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "DEFAULT_REPORT_NAMES",
    "build_native_runtime_release_control_markdown",
    "build_native_runtime_release_control_next_steps",
    "build_native_runtime_release_control_payload",
    "get_native_runtime_release_control_status",
    "normalize_report_names",
]
