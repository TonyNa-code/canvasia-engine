from __future__ import annotations

import csv
import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from export_runtime_preload import build_runtime_preload_manifest, format_bytes, normalize_asset_size_bytes


EXPORT_PERFORMANCE_BUDGET_JSON_NAME = "performance-budget.json"
EXPORT_PERFORMANCE_BUDGET_REPORT_NAME = "performance-budget.md"
EXPORT_PERFORMANCE_BUDGET_CSV_NAME = "performance-budget.csv"
EXPORT_PERFORMANCE_BUDGET_FORMAT_VERSION = 1

IMAGE_ASSET_TYPES = {"background", "sprite", "cg", "ui"}
AUDIO_ASSET_TYPES = {"bgm", "sfx", "voice"}
VIDEO_ASSET_TYPES = {"video"}
FONT_ASSET_TYPES = {"font"}
ADVANCED_ASSET_TYPES = {"live2d", "model3d", "scene3d"}

DEFAULT_EXPORT_PERFORMANCE_BUDGETS = {
    "totalPackageBudgetBytes": 1400 * 1024 * 1024,
    "referencedAssetBudgetBytes": 900 * 1024 * 1024,
    "criticalPreloadBudgetBytes": 90 * 1024 * 1024,
    "earlyPreloadBudgetBytes": 260 * 1024 * 1024,
    "imageBudgetBytes": 420 * 1024 * 1024,
    "audioBudgetBytes": 420 * 1024 * 1024,
    "videoBudgetBytes": 2200 * 1024 * 1024,
    "advancedAssetBudgetBytes": 600 * 1024 * 1024,
    "singleImageBudgetBytes": 24 * 1024 * 1024,
    "singleAudioBudgetBytes": 45 * 1024 * 1024,
    "singleVideoBudgetBytes": 360 * 1024 * 1024,
    "singleAdvancedAssetBudgetBytes": 220 * 1024 * 1024,
    "unknownReferencedSizeWarningCount": 4,
    "unusedLargeAssetWarningCount": 8,
}

GROUP_LABELS = {
    "image": "图片 / UI",
    "audio": "音频",
    "video": "视频",
    "font": "字体",
    "advanced": "Live2D / 3D",
    "other": "其他",
}

ISSUE_SEVERITY_LABELS = {
    "blocker": "阻塞",
    "warning": "需要优化",
    "tip": "建议",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def clean_text(value: object, fallback: str = "") -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text or fallback


def as_dict(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def as_list(value: object) -> list:
    return value if isinstance(value, list) else []


def as_int(value: object, fallback: int = 0) -> int:
    try:
        return int(value if value is not None else fallback)
    except (TypeError, ValueError):
        return fallback


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
        lines.append("| " + " | ".join(markdown_cell(cell) for cell in row) + " |")
    return "\n".join(lines)


def merge_export_performance_budgets(budgets: dict | None = None) -> dict:
    merged = dict(DEFAULT_EXPORT_PERFORMANCE_BUDGETS)
    if isinstance(budgets, dict):
        for key, default_value in DEFAULT_EXPORT_PERFORMANCE_BUDGETS.items():
            if key in budgets:
                merged[key] = max(0, as_int(budgets.get(key), default_value))
    return merged


def get_asset_group(asset_type: str) -> str:
    if asset_type in IMAGE_ASSET_TYPES:
        return "image"
    if asset_type in AUDIO_ASSET_TYPES:
        return "audio"
    if asset_type in VIDEO_ASSET_TYPES:
        return "video"
    if asset_type in FONT_ASSET_TYPES:
        return "font"
    if asset_type in ADVANCED_ASSET_TYPES:
        return "advanced"
    return "other"


def collect_asset_reference_ids(bundle: dict) -> set[str]:
    references: set[str] = set()

    def visit(value: object, key: str = "") -> None:
        lowered_key = key.lower()
        is_asset_id_key = lowered_key == "assetid" or lowered_key.endswith("assetid")
        is_asset_ids_key = lowered_key == "assetids" or lowered_key.endswith("assetids")
        if is_asset_id_key and isinstance(value, str):
            asset_id = clean_text(value)
            if asset_id:
                references.add(asset_id)
        elif is_asset_ids_key and isinstance(value, list):
            for item in value:
                asset_id = clean_text(item)
                if asset_id:
                    references.add(asset_id)
        if isinstance(value, dict):
            for child_key, child_value in value.items():
                if child_key == "assets":
                    continue
                visit(child_value, clean_text(child_key))
        elif isinstance(value, list):
            for item in value:
                visit(item, key)

    for key in ("project", "characters", "chapters", "variables", "ui", "unlockables"):
        visit(bundle.get(key), key)
    return references


def normalize_assets_doc(bundle: dict, assets_doc: dict | None) -> dict:
    if isinstance(assets_doc, dict):
        return assets_doc
    bundle_assets = bundle.get("assets")
    if isinstance(bundle_assets, dict):
        return bundle_assets
    if isinstance(bundle_assets, list):
        return {"assets": bundle_assets}
    return {"assets": []}


def normalize_bundle_for_preload(bundle: dict) -> dict:
    normalized = dict(bundle)
    characters = normalized.get("characters")
    if isinstance(characters, list):
        normalized["characters"] = {"characters": characters}
    elif not isinstance(characters, dict):
        normalized["characters"] = {"characters": []}
    chapters = normalized.get("chapters")
    if not isinstance(chapters, list):
        normalized["chapters"] = []
    project = normalized.get("project")
    if not isinstance(project, dict):
        normalized["project"] = {}
    return normalized


def build_asset_reports(bundle: dict, assets_doc: dict | None) -> tuple[list[dict], set[str]]:
    normalized_assets_doc = normalize_assets_doc(bundle, assets_doc)
    referenced_asset_ids = collect_asset_reference_ids(bundle)
    asset_reports: list[dict] = []
    for index, asset in enumerate(as_list(normalized_assets_doc.get("assets"))):
        if not isinstance(asset, dict):
            continue
        asset_id = clean_text(asset.get("id"), f"asset_{index + 1}")
        asset_type = clean_text(asset.get("type"), "unknown")
        size_bytes = normalize_asset_size_bytes(asset)
        referenced = asset_id in referenced_asset_ids
        missing = bool(asset.get("isMissing")) or (referenced and not clean_text(asset.get("exportUrl") or asset.get("path")))
        group = get_asset_group(asset_type)
        asset_reports.append(
            {
                "assetId": asset_id,
                "name": clean_text(asset.get("name"), asset_id),
                "type": asset_type,
                "group": group,
                "groupLabel": GROUP_LABELS.get(group, "其他"),
                "path": clean_text(asset.get("exportUrl") or asset.get("path")),
                "referenced": referenced,
                "missing": missing,
                "sizeBytes": size_bytes,
                "sizeLabel": format_bytes(size_bytes) if size_bytes else "Unknown",
            }
        )
    return asset_reports, referenced_asset_ids


def describe_budget(current: int, budget: int) -> dict:
    ratio = round(current / budget, 3) if budget else 0
    return {
        "currentBytes": current,
        "currentLabel": format_bytes(current),
        "budgetBytes": budget,
        "budgetLabel": format_bytes(budget),
        "ratio": ratio,
        "overBudget": bool(budget and current > budget),
    }


def add_issue(
    issues: list[dict],
    *,
    severity: str,
    code: str,
    title: str,
    detail: str,
    suggestion: str,
    asset_id: str = "",
    context: str = "",
) -> None:
    issues.append(
        {
            "severity": severity,
            "severityLabel": ISSUE_SEVERITY_LABELS.get(severity, "建议"),
            "code": code,
            "title": title,
            "detail": detail,
            "suggestion": suggestion,
            "assetId": asset_id,
            "context": context,
        }
    )


def build_group_totals(asset_reports: list[dict]) -> dict[str, dict]:
    totals: dict[str, dict] = {}
    for group in ["image", "audio", "video", "font", "advanced", "other"]:
        group_assets = [asset for asset in asset_reports if asset.get("group") == group]
        referenced_assets = [asset for asset in group_assets if asset.get("referenced")]
        total_bytes = sum(as_int(asset.get("sizeBytes")) for asset in group_assets)
        referenced_bytes = sum(as_int(asset.get("sizeBytes")) for asset in referenced_assets)
        totals[group] = {
            "group": group,
            "label": GROUP_LABELS.get(group, "其他"),
            "assetCount": len(group_assets),
            "referencedAssetCount": len(referenced_assets),
            "totalBytes": total_bytes,
            "totalLabel": format_bytes(total_bytes),
            "referencedBytes": referenced_bytes,
            "referencedLabel": format_bytes(referenced_bytes),
        }
    return totals


def build_budget_rows(group_totals: dict[str, dict], preload_summary: dict, budget: dict, total_bytes: int, referenced_bytes: int) -> dict:
    return {
        "totalPackage": describe_budget(total_bytes, budget["totalPackageBudgetBytes"]),
        "referencedAssets": describe_budget(referenced_bytes, budget["referencedAssetBudgetBytes"]),
        "criticalPreload": describe_budget(as_int(preload_summary.get("criticalBytes")), budget["criticalPreloadBudgetBytes"]),
        "earlyPreload": describe_budget(as_int(preload_summary.get("earlyBytes")), budget["earlyPreloadBudgetBytes"]),
        "images": describe_budget(as_int(group_totals["image"].get("totalBytes")), budget["imageBudgetBytes"]),
        "audio": describe_budget(as_int(group_totals["audio"].get("totalBytes")), budget["audioBudgetBytes"]),
        "video": describe_budget(as_int(group_totals["video"].get("totalBytes")), budget["videoBudgetBytes"]),
        "advancedAssets": describe_budget(as_int(group_totals["advanced"].get("totalBytes")), budget["advancedAssetBudgetBytes"]),
    }


def add_budget_issues(issues: list[dict], budget_rows: dict) -> None:
    budget_labels = {
        "totalPackage": "导出包总素材体积",
        "referencedAssets": "已引用素材体积",
        "criticalPreload": "首屏关键预加载",
        "earlyPreload": "早期路线预加载",
        "images": "图片 / UI 素材",
        "audio": "音频素材",
        "video": "视频素材",
        "advancedAssets": "Live2D / 3D 素材",
    }
    for code, row in budget_rows.items():
        if not row.get("overBudget"):
            continue
        label = budget_labels.get(code, code)
        add_issue(
            issues,
            severity="warning",
            code=f"{code}_over_budget",
            title=f"{label}超过建议预算",
            detail=f"{label}当前 {row.get('currentLabel')}，建议预算 {row.get('budgetLabel')}。",
            suggestion="优先压缩大图、转码音频/视频、拆分章节资源，或把非首屏资源延后加载。",
            context=label,
        )


def add_asset_size_issues(issues: list[dict], asset_reports: list[dict], budget: dict) -> None:
    single_budget_by_group = {
        "image": budget["singleImageBudgetBytes"],
        "audio": budget["singleAudioBudgetBytes"],
        "video": budget["singleVideoBudgetBytes"],
        "advanced": budget["singleAdvancedAssetBudgetBytes"],
    }
    missing_referenced_assets = [asset for asset in asset_reports if asset.get("referenced") and asset.get("missing")]
    for asset in missing_referenced_assets[:12]:
        add_issue(
            issues,
            severity="blocker",
            code="missing_referenced_asset",
            title="已引用素材在导出包中缺失",
            detail=f"{asset.get('name')} 被剧情或项目配置引用，但导出包没有可用文件路径。",
            suggestion="重新导入或替换这个素材，或者删除不再使用的引用后重新导出。",
            asset_id=clean_text(asset.get("assetId")),
            context=clean_text(asset.get("path")),
        )

    oversized_assets = [
        asset
        for asset in asset_reports
        if as_int(asset.get("sizeBytes")) > single_budget_by_group.get(clean_text(asset.get("group")), 10**18)
    ]
    oversized_assets.sort(key=lambda item: as_int(item.get("sizeBytes")), reverse=True)
    for asset in oversized_assets[:12]:
        add_issue(
            issues,
            severity="warning",
            code="single_asset_over_budget",
            title="单个素材体积偏大",
            detail=f"{asset.get('name')}（{asset.get('groupLabel')}）大小为 {asset.get('sizeLabel')}。",
            suggestion="优先尝试压缩、转码、裁切分辨率，或确认它只在需要时加载。",
            asset_id=clean_text(asset.get("assetId")),
            context=clean_text(asset.get("path")),
        )

    unknown_referenced_assets = [
        asset
        for asset in asset_reports
        if asset.get("referenced") and not asset.get("missing") and as_int(asset.get("sizeBytes")) <= 0
    ]
    if len(unknown_referenced_assets) >= budget["unknownReferencedSizeWarningCount"]:
        add_issue(
            issues,
            severity="tip",
            code="unknown_referenced_asset_sizes",
            title="较多已引用素材缺少体积信息",
            detail=f"有 {len(unknown_referenced_assets)} 个已引用素材没有可用体积，性能预算只能给出保守结论。",
            suggestion="重新打开项目或重新导出，让素材文件大小写入报告；外部素材也建议补齐文件路径。",
            context="、".join(clean_text(asset.get("name")) for asset in unknown_referenced_assets[:5]),
        )

    unused_large_assets = [
        asset
        for asset in asset_reports
        if not asset.get("referenced") and as_int(asset.get("sizeBytes")) > single_budget_by_group.get(clean_text(asset.get("group")), 64 * 1024 * 1024)
    ]
    unused_large_assets.sort(key=lambda item: as_int(item.get("sizeBytes")), reverse=True)
    if len(unused_large_assets) >= budget["unusedLargeAssetWarningCount"]:
        add_issue(
            issues,
            severity="tip",
            code="many_unused_large_assets",
            title="素材库里保留了较多未使用大素材",
            detail=f"检测到 {len(unused_large_assets)} 个未被剧情引用的大素材。",
            suggestion="发布包前移出暂时不用的 PV、备用 CG、旧立绘和未使用模型，避免包体膨胀。",
            context="、".join(clean_text(asset.get("name")) for asset in unused_large_assets[:5]),
        )


def summarize_performance_budget(asset_reports: list[dict], budget_rows: dict, issues: list[dict], preload_summary: dict) -> dict:
    blocker_count = sum(1 for issue in issues if issue.get("severity") == "blocker")
    warning_count = sum(1 for issue in issues if issue.get("severity") == "warning")
    tip_count = sum(1 for issue in issues if issue.get("severity") == "tip")
    if blocker_count:
        status = "blocked"
        title = f"有 {blocker_count} 个性能 / 素材阻塞项"
    elif warning_count:
        status = "needs_optimization"
        title = f"有 {warning_count} 个发布前性能优化项"
    elif tip_count:
        status = "needs_measurement"
        title = "可以发布前再补一次体积确认"
    else:
        status = "ready"
        title = "性能预算暂未发现明显风险"

    score = max(0, 100 - blocker_count * 28 - warning_count * 10 - tip_count * 4)
    total_bytes = as_int(budget_rows["totalPackage"].get("currentBytes"))
    referenced_bytes = as_int(budget_rows["referencedAssets"].get("currentBytes"))
    return {
        "status": status,
        "title": title,
        "score": score,
        "assetCount": len(asset_reports),
        "referencedAssetCount": sum(1 for asset in asset_reports if asset.get("referenced")),
        "missingReferencedAssetCount": sum(1 for asset in asset_reports if asset.get("referenced") and asset.get("missing")),
        "issueCount": len(issues),
        "blockerCount": blocker_count,
        "warningCount": warning_count,
        "tipCount": tip_count,
        "totalBytes": total_bytes,
        "totalLabel": format_bytes(total_bytes),
        "referencedBytes": referenced_bytes,
        "referencedLabel": format_bytes(referenced_bytes),
        "criticalPreloadBytes": as_int(preload_summary.get("criticalBytes")),
        "criticalPreloadLabel": clean_text(preload_summary.get("criticalBytesLabel"), "0 B"),
        "earlyPreloadBytes": as_int(preload_summary.get("earlyBytes")),
        "earlyPreloadLabel": clean_text(preload_summary.get("earlyBytesLabel"), "0 B"),
        "recommendation": clean_text(issues[0].get("suggestion")) if issues else "可以继续进行目标平台试玩，观察首屏加载、切场景和视频播放是否顺滑。",
    }


def build_export_performance_budget(
    bundle: dict,
    assets_doc: dict | None = None,
    *,
    budgets: dict | None = None,
) -> dict:
    budget = merge_export_performance_budgets(budgets)
    asset_reports, referenced_asset_ids = build_asset_reports(bundle, assets_doc)
    preload_manifest = build_runtime_preload_manifest(
        normalize_bundle_for_preload(bundle),
        normalize_assets_doc(bundle, assets_doc),
    )
    preload_summary = as_dict(preload_manifest.get("summary"))
    group_totals = build_group_totals(asset_reports)
    total_bytes = sum(as_int(asset.get("sizeBytes")) for asset in asset_reports)
    referenced_bytes = sum(as_int(asset.get("sizeBytes")) for asset in asset_reports if asset.get("referenced"))
    budget_rows = build_budget_rows(group_totals, preload_summary, budget, total_bytes, referenced_bytes)
    issues: list[dict] = []
    add_budget_issues(issues, budget_rows)
    add_asset_size_issues(issues, asset_reports, budget)
    issues.sort(
        key=lambda issue: (
            {"blocker": 0, "warning": 1, "tip": 2}.get(clean_text(issue.get("severity")), 3),
            clean_text(issue.get("title")),
            clean_text(issue.get("assetId")),
        )
    )
    for index, issue in enumerate(issues, start=1):
        issue["rank"] = index
    largest_assets = sorted(asset_reports, key=lambda item: as_int(item.get("sizeBytes")), reverse=True)[:15]
    return {
        "formatVersion": EXPORT_PERFORMANCE_BUDGET_FORMAT_VERSION,
        "generatedAt": now_iso(),
        "projectTitle": clean_text(as_dict(bundle.get("project")).get("title"), "Canvasia Project"),
        "summary": summarize_performance_budget(asset_reports, budget_rows, issues, preload_summary),
        "budgets": {
            key: {
                "bytes": value,
                "label": format_bytes(value) if "Bytes" in key else value,
            }
            for key, value in budget.items()
        },
        "budgetRows": budget_rows,
        "groupTotals": group_totals,
        "preloadSummary": preload_summary,
        "referencedAssetIds": sorted(referenced_asset_ids),
        "largestAssets": largest_assets,
        "issues": issues,
    }


def build_export_performance_budget_markdown(payload: dict) -> str:
    summary = as_dict(payload.get("summary"))
    budget_rows = as_dict(payload.get("budgetRows"))
    group_totals = as_dict(payload.get("groupTotals"))
    issues = as_list(payload.get("issues"))
    largest_assets = as_list(payload.get("largestAssets"))
    budget_table_rows = [
        [label, row.get("currentLabel"), row.get("budgetLabel"), "是" if row.get("overBudget") else "否"]
        for label, row in [
            ("导出包总素材", as_dict(budget_rows.get("totalPackage"))),
            ("已引用素材", as_dict(budget_rows.get("referencedAssets"))),
            ("首屏关键预加载", as_dict(budget_rows.get("criticalPreload"))),
            ("早期路线预加载", as_dict(budget_rows.get("earlyPreload"))),
            ("图片 / UI", as_dict(budget_rows.get("images"))),
            ("音频", as_dict(budget_rows.get("audio"))),
            ("视频", as_dict(budget_rows.get("video"))),
            ("Live2D / 3D", as_dict(budget_rows.get("advancedAssets"))),
        ]
    ]
    group_table_rows = [
        [
            group.get("label"),
            group.get("assetCount"),
            group.get("referencedAssetCount"),
            group.get("totalLabel"),
            group.get("referencedLabel"),
        ]
        for group in group_totals.values()
    ]
    issue_rows = [
        [issue.get("rank"), issue.get("severityLabel"), issue.get("title"), issue.get("detail"), issue.get("suggestion")]
        for issue in issues[:40]
    ]
    largest_rows = [
        [asset.get("name"), asset.get("type"), asset.get("groupLabel"), asset.get("sizeLabel"), "是" if asset.get("referenced") else "否"]
        for asset in largest_assets[:15]
    ]
    lines = [
        f"# {markdown_cell(payload.get('projectTitle'))} 发布性能预算",
        "",
        f"- 生成时间：{markdown_cell(payload.get('generatedAt'))}",
        f"- 状态：{markdown_cell(summary.get('title'))}",
        f"- 预算分：{markdown_cell(summary.get('score'))}/100",
        f"- 建议：{markdown_cell(summary.get('recommendation'))}",
        "",
        "## 总览",
        "",
        markdown_table(
            ["素材数", "已引用", "总素材体积", "已引用体积", "首屏预加载", "早期预加载", "问题数"],
            [[summary.get("assetCount"), summary.get("referencedAssetCount"), summary.get("totalLabel"), summary.get("referencedLabel"), summary.get("criticalPreloadLabel"), summary.get("earlyPreloadLabel"), summary.get("issueCount")]],
        ),
        "",
        "## 预算线",
        "",
        markdown_table(["项目", "当前", "建议预算", "超出"], budget_table_rows),
        "",
        "## 分组体积",
        "",
        markdown_table(["分组", "素材数", "已引用", "总量", "已引用量"], group_table_rows),
        "",
        "## 发布前优化项",
        "",
        markdown_table(["序号", "级别", "问题", "说明", "建议"], issue_rows) or "暂未发现明显性能预算风险。",
        "",
        "## 最大素材",
        "",
        markdown_table(["素材", "类型", "分组", "大小", "已引用"], largest_rows) or "没有可统计的素材体积。",
        "",
    ]
    return "\n".join(lines)


def build_export_performance_budget_csv(payload: dict) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["类型", "序号", "级别", "素材ID", "标题", "说明", "建议", "位置"])
    for issue in as_list(payload.get("issues")):
        writer.writerow(
            [
                "issue",
                issue.get("rank"),
                issue.get("severityLabel"),
                issue.get("assetId"),
                issue.get("title"),
                issue.get("detail"),
                issue.get("suggestion"),
                issue.get("context"),
            ]
        )
    writer.writerow([])
    writer.writerow(["类型", "素材ID", "名称", "类型", "分组", "大小", "已引用", "缺失", "路径"])
    for asset in as_list(payload.get("largestAssets")):
        writer.writerow(
            [
                "largest_asset",
                asset.get("assetId"),
                asset.get("name"),
                asset.get("type"),
                asset.get("groupLabel"),
                asset.get("sizeLabel"),
                "yes" if asset.get("referenced") else "no",
                "yes" if asset.get("missing") else "no",
                asset.get("path"),
            ]
        )
    return "\ufeff" + output.getvalue()


def write_export_performance_budget_files(
    target_dir: Path,
    *,
    bundle: dict,
    assets_doc: dict | None = None,
    budgets: dict | None = None,
) -> dict:
    payload = build_export_performance_budget(bundle, assets_doc, budgets=budgets)
    json_path = target_dir / EXPORT_PERFORMANCE_BUDGET_JSON_NAME
    markdown_path = target_dir / EXPORT_PERFORMANCE_BUDGET_REPORT_NAME
    csv_path = target_dir / EXPORT_PERFORMANCE_BUDGET_CSV_NAME
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(build_export_performance_budget_markdown(payload), encoding="utf-8")
    csv_path.write_text(build_export_performance_budget_csv(payload), encoding="utf-8")
    summary = payload["summary"]
    return {
        "exportPerformanceBudget": payload,
        "exportPerformanceBudgetName": json_path.name,
        "exportPerformanceBudgetPath": str(json_path),
        "exportPerformanceBudgetReportName": markdown_path.name,
        "exportPerformanceBudgetReportPath": str(markdown_path),
        "exportPerformanceBudgetCsvName": csv_path.name,
        "exportPerformanceBudgetCsvPath": str(csv_path),
        "exportPerformanceBudgetStatus": summary["status"],
        "exportPerformanceBudgetScore": summary["score"],
        "exportPerformanceBudgetIssueCount": summary["issueCount"],
        "exportPerformanceBudgetWarningCount": summary["warningCount"],
        "exportPerformanceBudgetBlockerCount": summary["blockerCount"],
    }


__all__ = [
    "EXPORT_PERFORMANCE_BUDGET_CSV_NAME",
    "EXPORT_PERFORMANCE_BUDGET_JSON_NAME",
    "EXPORT_PERFORMANCE_BUDGET_REPORT_NAME",
    "build_export_performance_budget",
    "build_export_performance_budget_csv",
    "build_export_performance_budget_markdown",
    "write_export_performance_budget_files",
]
