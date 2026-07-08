from __future__ import annotations

import csv
import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path


EXPORT_RELEASE_FIX_ORDER_JSON_NAME = "release-fix-order.json"
EXPORT_RELEASE_FIX_ORDER_REPORT_NAME = "release-fix-order.md"
EXPORT_RELEASE_FIX_ORDER_CSV_NAME = "release-fix-order.csv"

SEVERITY_LABELS = {
    "blocker": "先修阻塞",
    "warning": "发布前复核",
    "warn": "发布前复核",
    "soft": "体验打磨",
    "tip": "体验打磨",
    "check": "人工点测",
}

SEVERITY_WEIGHTS = {
    "blocker": 100,
    "warning": 70,
    "warn": 70,
    "soft": 45,
    "tip": 35,
    "check": 25,
}

AREA_LABELS = {
    "release": "发布总控",
    "asset": "素材",
    "route": "剧情路线",
    "choice": "选项",
    "variable": "变量",
    "runtime": "Runtime",
    "vn": "VN 基础体验",
    "localization": "本地化",
    "unlockable": "图鉴 / 回想",
    "story": "剧情文本",
    "visual": "画面",
    "character": "角色舞台",
    "audio": "音频",
    "branch": "分支",
    "polish": "打磨",
}

AREA_WEIGHTS = {
    "release": 100,
    "asset": 95,
    "route": 92,
    "choice": 86,
    "variable": 84,
    "runtime": 82,
    "vn": 78,
    "story": 76,
    "visual": 74,
    "character": 72,
    "audio": 70,
    "branch": 68,
    "localization": 58,
    "unlockable": 54,
    "polish": 40,
}

REPORT_BY_AREA = {
    "release": "release_readiness_summary.md",
    "asset": "export_manifest.json",
    "route": "story_route_map.md",
    "choice": "choice-consequence-report.md",
    "variable": "variable-influence-report.md",
    "runtime": "runtime-capability-matrix.md",
    "vn": "runtime-capability-matrix.md",
    "localization": "localization_audit.md",
    "unlockable": "unlockable_content_report.md",
    "story": "runtime-capability-matrix.md",
    "visual": "runtime-capability-matrix.md",
    "character": "runtime-capability-matrix.md",
    "audio": "audio-cue-report.md",
    "branch": "route-playtest-workbook.md",
    "polish": "release_readiness_summary.md",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def clean_text(value: object, fallback: str = "") -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text or fallback


def as_list(value: object) -> list:
    return value if isinstance(value, list) else []


def as_dict(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def as_int(value: object, fallback: int = 0) -> int:
    try:
        return int(value if value is not None else fallback)
    except (TypeError, ValueError):
        return fallback


def normalize_severity(value: object) -> str:
    severity = clean_text(value, "tip").lower()
    if severity == "error":
        return "blocker"
    if severity == "warn":
        return "warning"
    return severity if severity in SEVERITY_LABELS else "tip"


def infer_area(code: str, fallback: str = "release") -> str:
    safe_code = clean_text(code).lower()
    if "asset" in safe_code or "missing_export_assets" in safe_code:
        return "asset"
    if "route" in safe_code or "entry_scene" in safe_code or "ending" in safe_code:
        return "route"
    if "choice" in safe_code:
        return "choice"
    if "variable" in safe_code:
        return "variable"
    if "runtime" in safe_code or "video" in safe_code:
        return "runtime"
    if "localization" in safe_code or "translation" in safe_code:
        return "localization"
    if "unlockable" in safe_code or "gallery" in safe_code:
        return "unlockable"
    if "bgm" in safe_code or "sfx" in safe_code or "audio" in safe_code:
        return "audio"
    if "background" in safe_code or "visual" in safe_code:
        return "visual"
    if "character" in safe_code:
        return "character"
    if "story" in safe_code or "text" in safe_code:
        return "story"
    return fallback if fallback in AREA_LABELS else "release"


def task_phase(severity: str) -> str:
    if severity == "blocker":
        return "1. 先清阻塞"
    if severity == "warning":
        return "2. 补齐基础"
    if severity == "check":
        return "3. 人工点测"
    return "4. 体验打磨"


def task_score(severity: str, area: str, order: int) -> int:
    severity_score = SEVERITY_WEIGHTS.get(severity, 0)
    area_score = AREA_WEIGHTS.get(area, 0)
    return severity_score * 1000 + area_score * 10 - order


def make_task(
    *,
    source: str,
    source_label: str,
    source_report: str,
    severity: str,
    area: str,
    code: str,
    title: str,
    detail: str,
    action: str,
    acceptance: str,
    context: str = "",
    order: int = 0,
) -> dict:
    safe_severity = normalize_severity(severity)
    safe_area = area if area in AREA_LABELS else infer_area(code)
    safe_code = clean_text(code, f"{source}_{order + 1}")
    safe_title = clean_text(title, "发布前待处理项")
    return {
        "id": f"{source}.{safe_code}.{order + 1}",
        "rank": 0,
        "score": task_score(safe_severity, safe_area, order),
        "phase": task_phase(safe_severity),
        "severity": safe_severity,
        "severityLabel": SEVERITY_LABELS.get(safe_severity, "体验打磨"),
        "area": safe_area,
        "areaLabel": AREA_LABELS.get(safe_area, "发布总控"),
        "source": source,
        "sourceLabel": source_label,
        "sourceReport": clean_text(source_report, REPORT_BY_AREA.get(safe_area, "release_readiness_summary.md")),
        "code": safe_code,
        "title": safe_title,
        "detail": clean_text(detail, "这项需要发布前复核。"),
        "action": clean_text(action, "按来源报告修复后重新导出。"),
        "acceptance": clean_text(acceptance, "重新导出后，这项不再出现在发布前修复顺序里。"),
        "context": clean_text(context),
    }


def add_unique_task(tasks: list[dict], seen: set[tuple[str, str, str]], task: dict) -> None:
    key = (clean_text(task.get("source")), clean_text(task.get("code")), clean_text(task.get("title")))
    if key in seen:
        return
    seen.add(key)
    tasks.append(task)


def release_issue_report(issue: dict) -> str:
    area = infer_area(clean_text(issue.get("code")))
    return REPORT_BY_AREA.get(area, "release_readiness_summary.md")


def build_release_readiness_tasks(summary: dict) -> list[dict]:
    tasks: list[dict] = []
    for index, issue in enumerate(as_list(summary.get("issues"))[:20]):
        code = clean_text(issue.get("code"), f"release_issue_{index + 1}")
        area = infer_area(code)
        tasks.append(
            make_task(
                source="release_readiness",
                source_label="发布试玩就绪摘要",
                source_report=release_issue_report(issue),
                severity=issue.get("severity"),
                area=area,
                code=code,
                title=issue.get("title"),
                detail=issue.get("detail"),
                action=issue.get("suggestion"),
                acceptance=f"重新导出后 `{code}` 不再出现在 release_readiness_summary.json。",
                order=index,
            )
        )
    return tasks


def build_route_playtest_tasks(workbook: dict | None) -> list[dict]:
    sheet = as_dict(workbook)
    tasks: list[dict] = []
    for index, item in enumerate(as_list(sheet.get("executionQueue"))[:24]):
        status = clean_text(item.get("status"))
        action_label = clean_text(item.get("actionLabel"))
        if status in {"ready", "ok", "passed"} and "修复" not in action_label and "补" not in action_label:
            continue
        location = " · ".join(part for part in [clean_text(item.get("chapterName")), clean_text(item.get("sceneName"))] if part)
        tasks.append(
            make_task(
                source="route_playtest",
                source_label="路线试玩工作簿",
                source_report="route-playtest-workbook.md",
                severity="blocker" if status in {"broken", "unreachable", "blocked"} or "修复" in action_label else "check",
                area="route",
                code=clean_text(item.get("status"), "route_playtest_case"),
                title=clean_text(item.get("title"), "复核路线试玩用例"),
                detail=clean_text(item.get("acceptanceCriteria"), "按路线工作簿完成这一条试玩。"),
                action=action_label or "按路线工作簿执行这条用例。",
                acceptance=clean_text(item.get("acceptanceCriteria"), "目标场景可抵达，文本、演出、存档和解锁状态正常。"),
                context=location,
                order=index,
            )
        )
    return tasks


def build_sheet_issue_tasks(sheet: dict | None, *, source: str, source_label: str, source_report: str, area: str) -> list[dict]:
    tasks: list[dict] = []
    for index, issue in enumerate(as_list(as_dict(sheet).get("issues"))[:20]):
        context = " · ".join(
            part
            for part in [
                clean_text(issue.get("chapterName")),
                clean_text(issue.get("sceneName")),
                clean_text(issue.get("variableName") or issue.get("optionText") or issue.get("blockType")),
            ]
            if part
        )
        code = clean_text(issue.get("code"), f"{source}_issue_{index + 1}")
        tasks.append(
            make_task(
                source=source,
                source_label=source_label,
                source_report=source_report,
                severity=issue.get("severity"),
                area=area,
                code=code,
                title=issue.get("title"),
                detail=issue.get("detail"),
                action=issue.get("suggestion") or issue.get("detail"),
                acceptance=f"重新导出后 `{code}` 不再出现在 `{source_report}` 对应 JSON。",
                context=context,
                order=index,
            )
        )
    return tasks


def build_runtime_tasks(matrix: dict | None) -> list[dict]:
    runtime = as_dict(matrix)
    tasks: list[dict] = []
    for index, issue in enumerate(as_list(runtime.get("issues"))[:16]):
        code = clean_text(issue.get("code"), f"runtime_issue_{index + 1}")
        tasks.append(
            make_task(
                source="runtime_capability",
                source_label="Runtime 覆盖矩阵",
                source_report="runtime-capability-matrix.md",
                severity=issue.get("severity"),
                area="runtime",
                code=code,
                title=issue.get("title"),
                detail=issue.get("detail"),
                action="补齐对应 Runtime 支持、改用已支持卡片，或移除这类卡片后重新导出。",
                acceptance=f"重新导出后 `{code}` 不再出现在 runtime-capability-matrix.json。",
                context=" / ".join(as_list(issue.get("sceneNames"))),
                order=index,
            )
        )
    essentials = as_dict(runtime.get("essentials"))
    for index, issue in enumerate(as_list(essentials.get("issues"))[:12]):
        code = clean_text(issue.get("code"), f"vn_essential_{index + 1}")
        area = clean_text(issue.get("area"), infer_area(code, "vn"))
        tasks.append(
            make_task(
                source="vn_essentials",
                source_label="VN 基础能力成熟度",
                source_report="runtime-capability-matrix.md",
                severity=issue.get("severity"),
                area=area,
                code=code,
                title=issue.get("title"),
                detail=issue.get("detail"),
                action=issue.get("suggestion"),
                acceptance=f"重新导出后 `{code}` 不再出现在 VN 基础能力缺口里，或被确认是刻意设计。",
                order=index,
            )
        )
    return tasks


def build_localization_task(audit: dict | None) -> list[dict]:
    localization = as_dict(audit)
    summary = as_dict(localization.get("summary"))
    missing_count = as_int(summary.get("missingTranslationCount"))
    if missing_count <= 0:
        return []
    project = as_dict(localization.get("project"))
    languages = as_list(project.get("targetLanguages")) or as_list(project.get("supportedLanguages"))
    return [
        make_task(
            source="localization",
            source_label="本地化覆盖",
            source_report="localization_audit.md",
            severity="warning",
            area="localization",
            code="localization_missing_translations",
            title="补齐缺失译文",
            detail=f"当前还有 {missing_count} 条译文缺失；目标语言：{', '.join(clean_text(item) for item in languages if clean_text(item)) or '见报告'}。",
            action="先补主线正文、选项和角色名，再补章节 / 场景标题。",
            acceptance="重新导出后 localization_audit.json 的 missingTranslationCount 为 0，或 README 不宣称多语言支持。",
            order=0,
        )
    ]


def summarize_tasks(tasks: list[dict], release_readiness_summary: dict) -> dict:
    blocker_count = sum(1 for task in tasks if task.get("severity") == "blocker")
    warning_count = sum(1 for task in tasks if task.get("severity") == "warning")
    polish_count = sum(1 for task in tasks if task.get("severity") in {"soft", "tip"})
    check_count = sum(1 for task in tasks if task.get("severity") == "check")
    gate = as_dict(release_readiness_summary.get("qualityGate"))
    if blocker_count:
        status = "blocked"
        title = f"先处理 {blocker_count} 个发布阻塞项"
    elif warning_count:
        status = "needs_review"
        title = f"还有 {warning_count} 个发布前复核项"
    elif polish_count or check_count:
        status = "needs_polish"
        title = "可以试玩，建议完成最后点测"
    else:
        status = "ready"
        title = "发布前修复顺序已清空"
    return {
        "status": status,
        "title": title,
        "taskCount": len(tasks),
        "blockerCount": blocker_count,
        "warningCount": warning_count,
        "polishCount": polish_count,
        "manualCheckCount": check_count,
        "releaseGateStatus": clean_text(gate.get("status"), "unknown"),
        "releaseScore": as_int(release_readiness_summary.get("score")),
        "firstAction": clean_text(tasks[0].get("action")) if tasks else "可以把导出包交给测试员，按试玩指南完成实机验收。",
    }


def build_export_release_fix_order(
    *,
    project: dict,
    release_readiness_summary: dict,
    route_playtest_workbook: dict | None = None,
    choice_consequence_sheet: dict | None = None,
    variable_influence_sheet: dict | None = None,
    runtime_capability_matrix: dict | None = None,
    localization_audit: dict | None = None,
    report_files: list[str] | None = None,
) -> dict:
    tasks: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    task_groups = [
        build_release_readiness_tasks(as_dict(release_readiness_summary)),
        build_route_playtest_tasks(route_playtest_workbook),
        build_sheet_issue_tasks(
            choice_consequence_sheet,
            source="choice_consequence",
            source_label="选项后果表",
            source_report="choice-consequence-report.md",
            area="choice",
        ),
        build_sheet_issue_tasks(
            variable_influence_sheet,
            source="variable_influence",
            source_label="变量影响表",
            source_report="variable-influence-report.md",
            area="variable",
        ),
        build_runtime_tasks(runtime_capability_matrix),
        build_localization_task(localization_audit),
    ]
    for group in task_groups:
        for task in group:
            add_unique_task(tasks, seen, task)
    tasks.sort(key=lambda task: (-as_int(task.get("score")), clean_text(task.get("title"))))
    for index, task in enumerate(tasks, start=1):
        task["rank"] = index
    phase_summaries = []
    for phase in ["1. 先清阻塞", "2. 补齐基础", "3. 人工点测", "4. 体验打磨"]:
        phase_tasks = [task for task in tasks if task.get("phase") == phase]
        if phase_tasks:
            phase_summaries.append(
                {
                    "phase": phase,
                    "taskCount": len(phase_tasks),
                    "topTasks": [task["title"] for task in phase_tasks[:5]],
                }
            )
    summary = summarize_tasks(tasks, as_dict(release_readiness_summary))
    return {
        "formatVersion": 1,
        "generatedAt": now_iso(),
        "projectTitle": clean_text(project.get("title") or as_dict(release_readiness_summary.get("project")).get("title"), "Canvasia Project"),
        "summary": summary,
        "tasks": tasks,
        "phaseSummaries": phase_summaries,
        "reportFiles": [clean_text(report) for report in as_list(report_files) if clean_text(report)],
    }


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


def build_export_release_fix_order_markdown(payload: dict) -> str:
    summary = as_dict(payload.get("summary"))
    tasks = as_list(payload.get("tasks"))
    phase_rows = [
        [phase.get("phase"), phase.get("taskCount"), "；".join(as_list(phase.get("topTasks")))]
        for phase in as_list(payload.get("phaseSummaries"))
    ]
    task_rows = [
        [
            task.get("rank"),
            task.get("phase"),
            task.get("severityLabel"),
            task.get("areaLabel"),
            task.get("title"),
            task.get("action"),
            task.get("acceptance"),
            task.get("sourceReport"),
        ]
        for task in tasks[:80]
    ]
    lines = [
        f"# {markdown_cell(payload.get('projectTitle'))} 发布前修复顺序",
        "",
        f"- 生成时间：{markdown_cell(payload.get('generatedAt'))}",
        f"- 状态：{markdown_cell(summary.get('title'))}",
        f"- 发布就绪分：{markdown_cell(summary.get('releaseScore'))}/100",
        f"- 第一步：{markdown_cell(summary.get('firstAction'))}",
        "",
        "## 总览",
        "",
        markdown_table(
            ["任务", "阻塞", "复核", "打磨", "人工点测", "发布门禁"],
            [[summary.get("taskCount"), summary.get("blockerCount"), summary.get("warningCount"), summary.get("polishCount"), summary.get("manualCheckCount"), summary.get("releaseGateStatus")]],
        ),
        "",
        "## 分阶段修复",
        "",
        markdown_table(["阶段", "任务数", "最先处理"], phase_rows) or "当前没有需要排序的修复项。",
        "",
        "## 逐项执行队列",
        "",
        markdown_table(["序号", "阶段", "级别", "领域", "任务", "怎么做", "怎么算完成", "来源报告"], task_rows) or "当前发布前修复顺序已清空，可以进入人工试玩验收。",
        "",
        "## 使用方法",
        "",
        "1. 先按序号从上到下处理，不要先打磨低优先级项目。",
        "2. 每修完一批后重新导出，让本文件重新生成。",
        "3. 当阻塞项清零后，再按试玩指南做目标系统实机点测。",
        "",
    ]
    return "\n".join(lines)


def build_export_release_fix_order_csv(payload: dict) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["序号", "阶段", "级别", "领域", "来源", "来源报告", "问题代码", "任务", "说明", "怎么做", "怎么算完成", "位置"])
    for task in as_list(payload.get("tasks")):
        writer.writerow(
            [
                task.get("rank"),
                task.get("phase"),
                task.get("severityLabel"),
                task.get("areaLabel"),
                task.get("sourceLabel"),
                task.get("sourceReport"),
                task.get("code"),
                task.get("title"),
                task.get("detail"),
                task.get("action"),
                task.get("acceptance"),
                task.get("context"),
            ]
        )
    return "\ufeff" + output.getvalue()


def write_export_release_fix_order_files(
    target_dir: Path,
    *,
    project: dict,
    release_readiness_summary: dict,
    route_playtest_workbook: dict | None = None,
    choice_consequence_sheet: dict | None = None,
    variable_influence_sheet: dict | None = None,
    runtime_capability_matrix: dict | None = None,
    localization_audit: dict | None = None,
    report_files: list[str] | None = None,
) -> dict:
    payload = build_export_release_fix_order(
        project=project,
        release_readiness_summary=release_readiness_summary,
        route_playtest_workbook=route_playtest_workbook,
        choice_consequence_sheet=choice_consequence_sheet,
        variable_influence_sheet=variable_influence_sheet,
        runtime_capability_matrix=runtime_capability_matrix,
        localization_audit=localization_audit,
        report_files=report_files,
    )
    json_path = target_dir / EXPORT_RELEASE_FIX_ORDER_JSON_NAME
    markdown_path = target_dir / EXPORT_RELEASE_FIX_ORDER_REPORT_NAME
    csv_path = target_dir / EXPORT_RELEASE_FIX_ORDER_CSV_NAME
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(build_export_release_fix_order_markdown(payload), encoding="utf-8")
    csv_path.write_text(build_export_release_fix_order_csv(payload), encoding="utf-8")
    summary = payload["summary"]
    return {
        "releaseFixOrder": payload,
        "releaseFixOrderName": json_path.name,
        "releaseFixOrderPath": str(json_path),
        "releaseFixOrderReportName": markdown_path.name,
        "releaseFixOrderReportPath": str(markdown_path),
        "releaseFixOrderCsvName": csv_path.name,
        "releaseFixOrderCsvPath": str(csv_path),
        "releaseFixOrderStatus": summary["status"],
        "releaseFixOrderTaskCount": summary["taskCount"],
        "releaseFixOrderBlockerCount": summary["blockerCount"],
        "releaseFixOrderWarningCount": summary["warningCount"],
    }


__all__ = [
    "EXPORT_RELEASE_FIX_ORDER_CSV_NAME",
    "EXPORT_RELEASE_FIX_ORDER_JSON_NAME",
    "EXPORT_RELEASE_FIX_ORDER_REPORT_NAME",
    "build_export_release_fix_order",
    "build_export_release_fix_order_csv",
    "build_export_release_fix_order_markdown",
    "write_export_release_fix_order_files",
]
