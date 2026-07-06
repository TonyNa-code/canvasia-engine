from __future__ import annotations

import csv
import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path


EXPORT_CHOICE_CONSEQUENCE_JSON_NAME = "choice-consequence-sheet.json"
EXPORT_CHOICE_CONSEQUENCE_REPORT_NAME = "choice-consequence-report.md"
EXPORT_CHOICE_CONSEQUENCE_CSV_NAME = "choice-consequence-table.csv"
CHOICE_CONSEQUENCE_FORMAT_VERSION = 1
CONTINUE_TARGET_ID = "__continue__"

CHOICE_EFFECT_LABELS = {
    "variable_add": "变量增加",
    "variable_set": "变量设为",
}
VARIABLE_TYPE_LABELS = {
    "number": "数字",
    "boolean": "开关",
    "string": "文本",
}
ISSUE_WEIGHT = {"blocker": 100, "warn": 60, "tip": 20}


def as_list(value: object) -> list:
    return value if isinstance(value, list) else []


def clean_text(value: object, fallback: str = "") -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text or fallback


def format_effect_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    return str(value)


def is_continue_target(value: object) -> bool:
    return clean_text(value) == CONTINUE_TARGET_ID


def get_project_title(bundle: dict) -> str:
    project = bundle.get("project") if isinstance(bundle.get("project"), dict) else {}
    return clean_text(project.get("title"), "Canvasia Project")


def get_chapter_id(chapter: dict) -> str:
    return clean_text(chapter.get("chapterId") or chapter.get("id"))


def get_scene_id(scene: dict) -> str:
    return clean_text(scene.get("id") or scene.get("sceneId"))


def get_ordered_scene_records(bundle: dict) -> list[dict]:
    chapters = [chapter for chapter in as_list(bundle.get("chapters")) if isinstance(chapter, dict)]
    project = bundle.get("project") if isinstance(bundle.get("project"), dict) else {}
    chapter_order = [clean_text(item) for item in as_list(project.get("chapterOrder")) if clean_text(item)]
    chapter_map = {get_chapter_id(chapter): chapter for chapter in chapters if get_chapter_id(chapter)}
    ordered_chapters = [chapter_map[chapter_id] for chapter_id in chapter_order if chapter_id in chapter_map]
    ordered_chapters.extend(chapter for chapter in chapters if get_chapter_id(chapter) not in chapter_order)

    records: list[dict] = []
    seen_scene_ids: set[str] = set()
    for chapter_index, chapter in enumerate(ordered_chapters):
        chapter_id = get_chapter_id(chapter)
        chapter_name = clean_text(chapter.get("name") or chapter.get("title"), f"章节 {chapter_index + 1}")
        scenes = [scene for scene in as_list(chapter.get("scenes")) if isinstance(scene, dict)]
        scene_order = [clean_text(item) for item in as_list(chapter.get("sceneOrder")) if clean_text(item)]
        scene_map = {get_scene_id(scene): scene for scene in scenes if get_scene_id(scene)}
        ordered_scenes = [scene_map[scene_id] for scene_id in scene_order if scene_id in scene_map]
        ordered_scenes.extend(scene for scene in scenes if get_scene_id(scene) not in scene_order)

        for scene_index, scene in enumerate(ordered_scenes):
            scene_id = get_scene_id(scene) or f"{chapter_id or 'chapter'}_scene_{scene_index + 1}"
            if scene_id in seen_scene_ids:
                continue
            seen_scene_ids.add(scene_id)
            records.append(
                {
                    "scene": scene,
                    "sceneId": scene_id,
                    "sceneName": clean_text(scene.get("name") or scene.get("title"), f"场景 {scene_index + 1}"),
                    "sceneIndex": scene_index,
                    "chapterId": chapter_id,
                    "chapterName": chapter_name,
                    "chapterIndex": chapter_index,
                }
            )

    for scene_index, scene in enumerate(as_list(bundle.get("scenes"))):
        if not isinstance(scene, dict):
            continue
        scene_id = get_scene_id(scene) or f"loose_scene_{scene_index + 1}"
        if scene_id in seen_scene_ids:
            continue
        seen_scene_ids.add(scene_id)
        records.append(
            {
                "scene": scene,
                "sceneId": scene_id,
                "sceneName": clean_text(scene.get("name") or scene.get("title"), f"场景 {scene_index + 1}"),
                "sceneIndex": scene_index,
                "chapterId": clean_text(scene.get("chapterId")),
                "chapterName": "未分章",
                "chapterIndex": 9999,
            }
        )
    return sorted(records, key=lambda item: (item["chapterIndex"], item["sceneIndex"], item["sceneName"]))


def get_scene_map(scene_records: list[dict]) -> dict[str, dict]:
    return {record["sceneId"]: record for record in scene_records if record.get("sceneId")}


def get_variables_by_id(bundle: dict) -> dict[str, dict]:
    variables_doc = bundle.get("variables") if isinstance(bundle.get("variables"), dict) else {}
    variables = variables_doc.get("variables") if isinstance(variables_doc, dict) else []
    project = bundle.get("project") if isinstance(bundle.get("project"), dict) else {}
    combined_variables = [*as_list(variables), *as_list(project.get("variables"))]
    return {
        clean_text(variable.get("id")): variable
        for variable in combined_variables
        if isinstance(variable, dict) and clean_text(variable.get("id"))
    }


def get_scene_name(scene_map: dict[str, dict], scene_id: object) -> str:
    safe_id = clean_text(scene_id)
    if is_continue_target(safe_id):
        return "继续下一张卡"
    scene_record = scene_map.get(safe_id)
    if isinstance(scene_record, dict):
        return clean_text(scene_record.get("sceneName"), safe_id)
    return safe_id or "继续当前场景"


def get_variable_name(variables_by_id: dict[str, dict], variable_id: object) -> str:
    safe_id = clean_text(variable_id)
    variable = variables_by_id.get(safe_id)
    if isinstance(variable, dict):
        return clean_text(variable.get("name") or variable.get("label"), safe_id or "未选择变量")
    return safe_id or "未选择变量"


def get_variable_type(variables_by_id: dict[str, dict], variable_id: object) -> str:
    variable = variables_by_id.get(clean_text(variable_id))
    return clean_text(variable.get("type"), "string") if isinstance(variable, dict) else ""


def get_status_from_issues(issues: list[dict]) -> str:
    if any(issue.get("severity") == "blocker" for issue in issues):
        return "blocker"
    if any(issue.get("severity") == "warn" for issue in issues):
        return "warn"
    if issues:
        return "tip"
    return "good"


def get_status_label(status: str) -> str:
    if status == "blocker":
        return "先修"
    if status == "warn":
        return "复查"
    if status == "tip":
        return "润色"
    return "正常"


def push_issue(issues: list[dict], severity: str, code: str, title: str, detail: str, context: dict) -> None:
    issues.append({"severity": severity, "code": code, "title": title, "detail": detail, **context})


def get_effect_type_label(effect_type: str) -> str:
    return CHOICE_EFFECT_LABELS.get(effect_type, clean_text(effect_type, "未知效果"))


def summarize_choice_effect(effect: dict, variables_by_id: dict[str, dict]) -> str:
    effect_type = clean_text(effect.get("type"))
    variable_id = clean_text(effect.get("variableId"))
    variable_name = get_variable_name(variables_by_id, variable_id)
    value = format_effect_value(effect.get("value"))
    if effect_type == "variable_add":
        return f"{variable_name} + {value or '1'}"
    if effect_type == "variable_set":
        return f"{variable_name} = {value}"
    return f"{get_effect_type_label(effect_type)} {variable_name}{(' ' + value) if value else ''}".strip()


def get_effect_key(effect: dict) -> str:
    return ":".join([clean_text(effect.get("type")), clean_text(effect.get("variableId")), format_effect_value(effect.get("value"))])


def get_option_outcome_key(option: dict) -> str:
    effect_key = "|".join(sorted(get_effect_key(effect) for effect in as_list(option.get("effects")) if isinstance(effect, dict)))
    return f"{clean_text(option.get('gotoSceneId') or option.get('targetSceneId') or option.get('sceneId'))}=>{effect_key}"


def inspect_choice_effect(effect: dict, *, variables_by_id: dict[str, dict], context: dict) -> list[dict]:
    issues: list[dict] = []
    effect_type = clean_text(effect.get("type"))
    variable_id = clean_text(effect.get("variableId"))
    variable_type = get_variable_type(variables_by_id, variable_id)

    if effect_type not in {"variable_add", "variable_set"}:
        push_issue(issues, "warn", "choice_effect_unknown_type", "选项效果类型未知", f"当前效果类型：{effect_type or '空'}", context)
    if not variable_id:
        push_issue(issues, "blocker", "choice_effect_missing_variable", "选项效果缺少变量", "这个选项效果没有选择要修改的变量。", context)
    elif variable_id not in variables_by_id:
        push_issue(issues, "blocker", "choice_effect_unknown_variable", "选项效果变量不存在", f"变量 {variable_id} 不在当前变量库里。", context)
    elif effect_type == "variable_add" and variable_type and variable_type != "number":
        push_issue(
            issues,
            "blocker",
            "choice_effect_add_non_number",
            "非数字变量不能增加",
            f"{get_variable_name(variables_by_id, variable_id)} 是 {VARIABLE_TYPE_LABELS.get(variable_type, variable_type)} 类型，不能使用“变量增加”。",
            context,
        )
    return issues


def build_choice_option_entry(option: dict, *, context: dict) -> dict:
    option_text = clean_text(option.get("text"))
    target_scene_id = clean_text(option.get("gotoSceneId") or option.get("targetSceneId") or option.get("sceneId"))
    continues_current_scene = is_continue_target(target_scene_id)
    effects = [effect for effect in as_list(option.get("effects")) if isinstance(effect, dict)]
    base_context = {
        "chapterName": context["chapterName"],
        "sceneName": context["sceneName"],
        "sceneId": context["sceneId"],
        "blockId": context["blockId"],
        "blockIndex": context["blockIndex"],
        "optionIndex": context["optionIndex"],
        "optionText": option_text or f"选项 {context['optionIndex'] + 1}",
    }
    issues: list[dict] = []

    if not option_text:
        push_issue(issues, "blocker", "choice_option_empty_text", "选项文案为空", "玩家会看到空按钮或难以理解的选项。", base_context)
    if target_scene_id and not continues_current_scene and target_scene_id not in context["sceneMap"]:
        push_issue(issues, "blocker", "choice_option_unknown_target", "选项目标场景不存在", f"目标场景 {target_scene_id} 已经找不到。", base_context)
    if not target_scene_id and not effects:
        push_issue(issues, "warn", "choice_option_no_consequence", "选项没有路线或变量后果", "这个选项既不跳转，也不修改变量，玩家容易觉得是假按钮。", base_context)

    for effect in effects:
        issues.extend(inspect_choice_effect(effect, variables_by_id=context["variablesById"], context=base_context))

    status = get_status_from_issues(issues)
    return {
        **base_context,
        "optionId": clean_text(option.get("id"), f"{context['blockId']}_option_{context['optionIndex'] + 1}"),
        "targetSceneId": target_scene_id,
        "targetSceneName": get_scene_name(context["sceneMap"], target_scene_id),
        "hasTarget": bool(target_scene_id),
        "continuesCurrentScene": continues_current_scene,
        "effectCount": len(effects),
        "effectSummary": " / ".join(summarize_choice_effect(effect, context["variablesById"]) for effect in effects) if effects else "无变量后果",
        "outcomeKey": get_option_outcome_key(option),
        "status": status,
        "statusLabel": get_status_label(status),
        "issues": issues,
    }


def get_option_issue_context(option: dict) -> dict:
    return {
        "chapterName": option.get("chapterName"),
        "sceneName": option.get("sceneName"),
        "sceneId": option.get("sceneId"),
        "blockId": option.get("blockId"),
        "blockIndex": option.get("blockIndex"),
        "optionIndex": option.get("optionIndex"),
        "optionText": option.get("optionText"),
    }


def inspect_choice_block(block: dict, *, context: dict) -> dict:
    options = [option for option in as_list(block.get("options")) if isinstance(option, dict)]
    block_context = {
        "chapterName": context["chapterName"],
        "sceneName": context["sceneName"],
        "sceneId": context["sceneId"],
        "blockId": clean_text(block.get("id"), f"choice_{context['blockIndex'] + 1}"),
        "blockIndex": context["blockIndex"],
    }
    issues: list[dict] = []
    if not options:
        push_issue(issues, "blocker", "choice_block_without_options", "选项卡没有选项", "玩家走到这里会没有可点内容。", block_context)
    if len(options) > 5:
        push_issue(issues, "tip", "choice_block_crowded", "选项数量偏多", f"当前有 {len(options)} 个选项，建议确认按钮区不会拥挤。", block_context)

    option_entries = [
        build_choice_option_entry(
            option,
            context={
                **context,
                **block_context,
                "optionIndex": option_index,
            },
        )
        for option_index, option in enumerate(options)
    ]

    text_groups: dict[str, list[dict]] = {}
    for option in option_entries:
        option_text = clean_text(option.get("optionText"))
        if option_text:
            text_groups.setdefault(option_text, []).append(option)
    for group in text_groups.values():
        if len(group) > 1:
            for option in group:
                push_issue(option["issues"], "warn", "choice_duplicate_text", "选项文案重复", f"同一组选项中有 {len(group)} 个“{option['optionText']}”。", get_option_issue_context(option))

    actionable_options = [option for option in option_entries if option.get("hasTarget") or option.get("effectCount", 0) > 0]
    outcome_groups: dict[str, list[dict]] = {}
    for option in actionable_options:
        outcome_groups.setdefault(option["outcomeKey"], []).append(option)
    for group in outcome_groups.values():
        if len(group) > 1 and len(group) == len(actionable_options):
            for option in group:
                push_issue(option["issues"], "warn", "choice_same_consequence", "所有选项后果相同", "这组选项的跳转和变量效果完全一致；如果是故意伪装路线，建议至少记录一个变量或改文案说明差异。", get_option_issue_context(option))

    for option in option_entries:
        option["status"] = get_status_from_issues(option["issues"])
        option["statusLabel"] = get_status_label(option["status"])

    issues.extend(issue for option in option_entries for issue in option["issues"])
    status = get_status_from_issues(issues)
    return {
        **block_context,
        "optionCount": len(option_entries),
        "actionableOptionCount": len(actionable_options),
        "sameOutcomeGroupCount": sum(1 for group in outcome_groups.values() if len(group) > 1),
        "status": status,
        "statusLabel": get_status_label(status),
        "issues": issues,
        "options": option_entries,
    }


def build_choice_consequence_sheet(bundle: dict) -> dict:
    scene_records = get_ordered_scene_records(bundle)
    scene_map = get_scene_map(scene_records)
    variables_by_id = get_variables_by_id(bundle)
    choice_blocks: list[dict] = []

    for scene_record in scene_records:
        blocks = [block for block in as_list(scene_record["scene"].get("blocks")) if isinstance(block, dict)]
        for block_index, block in enumerate(blocks):
            if clean_text(block.get("type")) != "choice":
                continue
            choice_blocks.append(
                inspect_choice_block(
                    block,
                    context={
                        "chapterName": scene_record["chapterName"],
                        "sceneName": scene_record["sceneName"],
                        "sceneId": scene_record["sceneId"],
                        "blockIndex": block_index,
                        "sceneMap": scene_map,
                        "variablesById": variables_by_id,
                    },
                )
            )

    options = [option for block in choice_blocks for option in block["options"]]
    issues = [issue for block in choice_blocks for issue in block["issues"]]
    issues.sort(key=lambda issue: (-ISSUE_WEIGHT.get(issue.get("severity"), 0), issue.get("chapterName", ""), issue.get("sceneName", ""), issue.get("blockIndex", 0), issue.get("optionIndex", 0)))
    blocker_count = sum(1 for issue in issues if issue.get("severity") == "blocker")
    warning_count = sum(1 for issue in issues if issue.get("severity") == "warn")
    tip_count = sum(1 for issue in issues if issue.get("severity") == "tip")
    readiness_penalty = min(100, blocker_count * 22 + warning_count * 8 + tip_count * 2)
    summary = {
        "choiceBlockCount": len(choice_blocks),
        "optionCount": len(options),
        "actionableOptionCount": sum(1 for option in options if option.get("hasTarget") or option.get("effectCount", 0) > 0),
        "variableEffectCount": sum(int(option.get("effectCount") or 0) for option in options),
        "noConsequenceCount": sum(1 for issue in issues if issue.get("code") == "choice_option_no_consequence"),
        "sameConsequenceCount": sum(1 for issue in issues if issue.get("code") == "choice_same_consequence"),
        "brokenTargetCount": sum(1 for issue in issues if issue.get("code") == "choice_option_unknown_target"),
        "brokenVariableCount": sum(1 for issue in issues if issue.get("code") in {"choice_effect_missing_variable", "choice_effect_unknown_variable", "choice_effect_add_non_number"}),
        "blockerCount": blocker_count,
        "warningCount": warning_count,
        "tipCount": tip_count,
        "releaseReadinessPercent": max(0, 100 - readiness_penalty),
    }
    sheet = {
        "formatVersion": CHOICE_CONSEQUENCE_FORMAT_VERSION,
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "projectTitle": get_project_title(bundle),
        "choiceBlocks": choice_blocks,
        "options": options,
        "issues": issues,
        "summary": summary,
    }
    sheet["statusDigest"] = get_choice_consequence_status_digest(sheet)
    return sheet


def get_choice_consequence_status_digest(sheet: dict) -> dict:
    summary = sheet.get("summary") or {}
    if summary.get("choiceBlockCount", 0) == 0:
        return {"status": "empty", "title": "还没有选项后果表", "detail": "项目里暂时没有选项卡。需要分支路线时，可以先在剧情页插入选项。"}
    if summary.get("blockerCount", 0) > 0:
        return {"status": "blocked", "title": f"有 {summary.get('blockerCount', 0)} 个选项阻塞问题", "detail": "优先修复空选项、坏跳转、坏变量或不合法的变量增加效果。"}
    if summary.get("warningCount", 0) > 0:
        return {"status": "warn", "title": f"有 {summary.get('warningCount', 0)} 个选项后果提醒", "detail": "项目可以继续制作，但建议复查无后果选项、重复选项和后果完全相同的分支。"}
    return {"status": "ready", "title": "选项后果比较清晰", "detail": "当前选项都有可解释的路线或变量后果，适合进入试玩复核。"}


def markdown_cell(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", "<br />").strip()


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    if not rows:
        return ""
    return "\n".join(
        [
            f"| {' | '.join(markdown_cell(header) for header in headers)} |",
            f"| {' | '.join('---' for _ in headers)} |",
            *(f"| {' | '.join(markdown_cell(cell) for cell in row)} |" for row in rows),
        ]
    )


def build_choice_consequence_report(sheet: dict) -> str:
    summary = sheet.get("summary") or {}
    digest = sheet.get("statusDigest") or get_choice_consequence_status_digest(sheet)
    option_rows = [
        [index + 1, option.get("chapterName"), option.get("sceneName"), int(option.get("blockIndex") or 0) + 1, option.get("optionText"), option.get("targetSceneName"), option.get("effectSummary"), option.get("statusLabel")]
        for index, option in enumerate((sheet.get("options") or [])[:180])
    ]
    issue_rows = [
        [
            index + 1,
            "阻塞" if issue.get("severity") == "blocker" else "提醒" if issue.get("severity") == "warn" else "润色",
            issue.get("chapterName"),
            issue.get("sceneName"),
            issue.get("optionText") or issue.get("blockId"),
            issue.get("title"),
            issue.get("detail"),
        ]
        for index, issue in enumerate((sheet.get("issues") or [])[:160])
    ]
    return "\ufeff" + "\n".join(
        [
            f"# {sheet.get('projectTitle') or 'Canvasia Project'} 选项后果表",
            "",
            f"导出时间：{sheet.get('generatedAt')}",
            f"状态：{digest.get('title')}",
            f"说明：{digest.get('detail')}",
            "",
            "## 总览",
            "",
            markdown_table(
                ["项目", "数量"],
                [
                    ["选项卡", summary.get("choiceBlockCount", 0)],
                    ["选项按钮", summary.get("optionCount", 0)],
                    ["有路线或变量后果", summary.get("actionableOptionCount", 0)],
                    ["变量效果", summary.get("variableEffectCount", 0)],
                    ["无后果选项", summary.get("noConsequenceCount", 0)],
                    ["同后果提醒", summary.get("sameConsequenceCount", 0)],
                    ["坏跳转", summary.get("brokenTargetCount", 0)],
                    ["坏变量", summary.get("brokenVariableCount", 0)],
                    ["阻塞问题", summary.get("blockerCount", 0)],
                    ["复查提醒", summary.get("warningCount", 0)],
                    ["就绪度", f"{summary.get('releaseReadinessPercent', 0)}%"],
                ],
            ),
            "",
            "## 选项后果",
            "",
            markdown_table(["序号", "章节", "场景", "卡片", "选项", "目标场景", "变量效果", "状态"], option_rows) or "当前没有可列出的选项。",
            "",
            "## 需要复查的问题",
            "",
            markdown_table(["序号", "级别", "章节", "场景", "选项", "问题", "说明"], issue_rows) or "当前没有明显选项后果问题。",
            "",
        ]
    )


def build_choice_consequence_csv(sheet: dict) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["序号", "章节", "场景", "卡片", "选项序号", "选项文案", "目标场景ID", "目标场景", "变量效果数", "变量效果", "状态", "问题"])
    for index, option in enumerate(sheet.get("options") or []):
        writer.writerow(
            [
                index + 1,
                option.get("chapterName"),
                option.get("sceneName"),
                int(option.get("blockIndex") or 0) + 1,
                int(option.get("optionIndex") or 0) + 1,
                option.get("optionText"),
                option.get("targetSceneId"),
                option.get("targetSceneName"),
                option.get("effectCount"),
                option.get("effectSummary"),
                option.get("statusLabel"),
                " / ".join(issue.get("title", "") for issue in option.get("issues") or [] if issue.get("title")),
            ]
        )
    return "\ufeff" + output.getvalue()


def write_export_choice_consequence_files(target_dir: Path, *, bundle: dict) -> dict:
    sheet = build_choice_consequence_sheet(bundle)
    json_path = target_dir / EXPORT_CHOICE_CONSEQUENCE_JSON_NAME
    report_path = target_dir / EXPORT_CHOICE_CONSEQUENCE_REPORT_NAME
    csv_path = target_dir / EXPORT_CHOICE_CONSEQUENCE_CSV_NAME
    json_path.write_text(json.dumps(sheet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(build_choice_consequence_report(sheet), encoding="utf-8")
    csv_path.write_text(build_choice_consequence_csv(sheet), encoding="utf-8")
    summary = sheet["summary"]
    return {
        "choiceConsequenceSheet": sheet,
        "choiceConsequenceName": json_path.name,
        "choiceConsequencePath": str(json_path),
        "choiceConsequenceReportName": report_path.name,
        "choiceConsequenceReportPath": str(report_path),
        "choiceConsequenceCsvName": csv_path.name,
        "choiceConsequenceCsvPath": str(csv_path),
        "choiceConsequenceReadinessPercent": summary["releaseReadinessPercent"],
        "choiceConsequenceBlockCount": summary["choiceBlockCount"],
        "choiceConsequenceOptionCount": summary["optionCount"],
        "choiceConsequenceBlockerCount": summary["blockerCount"],
        "choiceConsequenceWarningCount": summary["warningCount"],
    }


__all__ = [
    "EXPORT_CHOICE_CONSEQUENCE_JSON_NAME",
    "EXPORT_CHOICE_CONSEQUENCE_REPORT_NAME",
    "EXPORT_CHOICE_CONSEQUENCE_CSV_NAME",
    "build_choice_consequence_sheet",
    "build_choice_consequence_report",
    "build_choice_consequence_csv",
    "write_export_choice_consequence_files",
]
