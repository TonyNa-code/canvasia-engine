from __future__ import annotations

import csv
import io
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path


EXPORT_VARIABLE_INFLUENCE_JSON_NAME = "variable-influence-sheet.json"
EXPORT_VARIABLE_INFLUENCE_REPORT_NAME = "variable-influence-report.md"
EXPORT_VARIABLE_INFLUENCE_CSV_NAME = "variable-influence-table.csv"
VARIABLE_INFLUENCE_FORMAT_VERSION = 1

VARIABLE_TYPE_LABELS = {
    "number": "数字",
    "boolean": "开关",
    "string": "文本",
}
USAGE_LABELS = {
    "set": "直接设置",
    "add": "数值增减",
    "choice": "选项后果",
    "condition": "条件读取",
}
ISSUE_WEIGHT = {"blocker": 100, "warn": 60, "tip": 20}


def as_list(value: object) -> list:
    return value if isinstance(value, list) else []


def clean_text(value: object, fallback: str = "") -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text or fallback


def get_project_title(bundle: dict) -> str:
    project = bundle.get("project") if isinstance(bundle.get("project"), dict) else {}
    return clean_text(project.get("title"), "Canvasia Project")


def get_chapter_id(chapter: dict) -> str:
    return clean_text(chapter.get("chapterId") or chapter.get("id"))


def get_scene_id(scene: dict) -> str:
    return clean_text(scene.get("id") or scene.get("sceneId"))


def get_variable_type_label(variable_type: str) -> str:
    return VARIABLE_TYPE_LABELS.get(variable_type, clean_text(variable_type, "未知"))


def get_usage_label(kind: str) -> str:
    return USAGE_LABELS.get(kind, clean_text(kind, "引用"))


def parse_number_bound(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def is_number_value(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def is_value_matching_type(variable: dict, value: object) -> bool:
    variable_type = clean_text(variable.get("type"), "string")
    if variable_type == "number":
        return is_number_value(value)
    if variable_type == "boolean":
        return isinstance(value, bool)
    return isinstance(value, str)


def format_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    return str(value)


def push_issue(issues: list[dict], severity: str, code: str, title: str, detail: str, context: dict | None = None) -> None:
    issues.append({"severity": severity, "code": code, "title": title, "detail": detail, **(context or {})})


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
        return "整理"
    return "正常"


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


def get_variables_by_id(bundle: dict) -> dict[str, dict]:
    variables_doc = bundle.get("variables")
    if isinstance(variables_doc, dict):
        raw_variables = variables_doc.get("variables")
    else:
        raw_variables = variables_doc
    project = bundle.get("project") if isinstance(bundle.get("project"), dict) else {}
    project_settings = bundle.get("projectSettings") if isinstance(bundle.get("projectSettings"), dict) else {}
    combined_variables = [*as_list(raw_variables), *as_list(project.get("variables")), *as_list(project_settings.get("variables"))]
    variables: dict[str, dict] = {}
    for variable in combined_variables:
        if isinstance(variable, dict) and clean_text(variable.get("id")):
            variables[clean_text(variable.get("id"))] = variable
    return variables


def get_variable_name(variables_by_id: dict[str, dict], variable_id: object) -> str:
    safe_id = clean_text(variable_id)
    variable = variables_by_id.get(safe_id)
    if isinstance(variable, dict):
        return clean_text(variable.get("name") or variable.get("label"), safe_id or "未选择变量")
    return safe_id or "未选择变量"


def create_variable_record(variable: dict) -> dict:
    variable_id = clean_text(variable.get("id"))
    variable_type = clean_text(variable.get("type"), "string")
    return {
        "variable": variable,
        "variableId": variable_id,
        "variableName": clean_text(variable.get("name") or variable.get("label"), variable_id),
        "type": variable_type,
        "typeLabel": get_variable_type_label(variable_type),
        "readCount": 0,
        "writeCount": 0,
        "setCount": 0,
        "addCount": 0,
        "choiceEffectCount": 0,
        "conditionCount": 0,
        "locations": [],
        "references": [],
        "issues": [],
        "status": "good",
        "statusLabel": "正常",
    }


def add_record_location(record: dict, label: str) -> None:
    if label and label not in record["locations"] and len(record["locations"]) < 5:
        record["locations"].append(label)


def inspect_variable_definition(record: dict) -> None:
    variable = record.get("variable") or {}
    variable_type = clean_text(variable.get("type"), "string")
    default_value = variable.get("defaultValue")
    base_context = {"variableId": record["variableId"], "variableName": record["variableName"]}

    if variable_type not in {"number", "boolean", "string"}:
        push_issue(record["issues"], "warn", "variable_unknown_type", "变量类型不认识", f"当前类型：{variable_type or '空'}，运行时会倾向按文本处理。", base_context)
    if not is_value_matching_type(variable, default_value):
        push_issue(record["issues"], "blocker", "variable_default_type_mismatch", "变量默认值类型不对", "默认值类型需要和变量类型一致。", base_context)
    if variable_type != "number":
        return

    min_raw = variable.get("min", variable.get("minValue"))
    max_raw = variable.get("max", variable.get("maxValue"))
    min_value = parse_number_bound(min_raw)
    max_value = parse_number_bound(max_raw)
    if min_raw is not None and min_value is None:
        push_issue(record["issues"], "warn", "variable_min_invalid", "数字变量最小值无效", "最小值不是有效数字。", base_context)
    if max_raw is not None and max_value is None:
        push_issue(record["issues"], "warn", "variable_max_invalid", "数字变量最大值无效", "最大值不是有效数字。", base_context)
    if min_value is not None and max_value is not None and min_value > max_value:
        push_issue(record["issues"], "blocker", "variable_range_reversed", "数字变量范围上下限反了", "最小值不能大于最大值。", base_context)
    if is_number_value(default_value) and ((min_value is not None and float(default_value) < min_value) or (max_value is not None and float(default_value) > max_value)):
        push_issue(record["issues"], "warn", "variable_default_out_of_range", "默认值超出数字范围", "默认值会被运行时限制或造成判断偏差。", base_context)


def build_reference_context(reference: dict, variables_by_id: dict[str, dict]) -> dict:
    variable_id = clean_text(reference.get("variableId"))
    return {
        "chapterName": reference.get("chapterName"),
        "sceneName": reference.get("sceneName"),
        "sceneId": reference.get("sceneId"),
        "blockId": reference.get("blockId"),
        "blockIndex": reference.get("blockIndex"),
        "kind": reference.get("kind"),
        "kindLabel": get_usage_label(clean_text(reference.get("kind"))),
        "label": reference.get("label"),
        "value": reference.get("value"),
        "valueLabel": format_value(reference.get("value")),
        "variableId": variable_id,
        "variableName": get_variable_name(variables_by_id, variable_id),
        "optionText": reference.get("optionText"),
        "optionIndex": reference.get("optionIndex"),
        "effectIndex": reference.get("effectIndex"),
        "effectType": reference.get("effectType"),
        "branchIndex": reference.get("branchIndex"),
        "ruleIndex": reference.get("ruleIndex"),
    }


def record_reference(records: dict[str, dict], unknown_references: list[dict], variables_by_id: dict[str, dict], reference: dict) -> None:
    variable_id = clean_text(reference.get("variableId"))
    context = build_reference_context(reference, variables_by_id)
    if not variable_id or variable_id not in records:
        unknown_references.append(context)
        return

    record = records[variable_id]
    variable = variables_by_id[variable_id]
    record["references"].append(context)
    add_record_location(record, clean_text(reference.get("label")))

    kind = clean_text(reference.get("kind"))
    if kind == "condition":
        record["readCount"] += 1
        record["conditionCount"] += 1
        if not is_value_matching_type(variable, reference.get("value")):
            push_issue(record["issues"], "blocker", "condition_value_type_mismatch", "条件比较值类型不对", f"{record['variableName']} 是 {record['typeLabel']}，但条件值是 {format_value(reference.get('value')) or '空'}", context)
        return

    record["writeCount"] += 1
    if kind == "set":
        record["setCount"] += 1
        if not is_value_matching_type(variable, reference.get("value")):
            push_issue(record["issues"], "blocker", "variable_set_type_mismatch", "变量设置值类型不对", f"{record['variableName']} 是 {record['typeLabel']}，但设置值是 {format_value(reference.get('value')) or '空'}", context)
    elif kind == "add":
        record["addCount"] += 1
        if variable.get("type") != "number" or not is_number_value(reference.get("value")):
            push_issue(record["issues"], "blocker", "variable_add_type_mismatch", "变量加减只能用于数字变量", f"{record['variableName']} 是 {record['typeLabel']}，不能用作数字加减。", context)
    elif kind == "choice":
        record["choiceEffectCount"] += 1
        if clean_text(reference.get("effectType")) == "variable_add":
            record["addCount"] += 1
            if variable.get("type") != "number" or not is_number_value(reference.get("value")):
                push_issue(record["issues"], "blocker", "choice_add_type_mismatch", "选项变量加减不合法", f"{record['variableName']} 是 {record['typeLabel']}，不能在选项里使用“变量增加”。", context)
        else:
            record["setCount"] += 1
            if not is_value_matching_type(variable, reference.get("value")):
                push_issue(record["issues"], "blocker", "choice_set_type_mismatch", "选项变量设置值类型不对", f"{record['variableName']} 是 {record['typeLabel']}，但选项设置值是 {format_value(reference.get('value')) or '空'}", context)


def add_record_level_usage_issues(record: dict) -> None:
    base_context = {"variableId": record["variableId"], "variableName": record["variableName"]}
    if len(record["references"]) == 0:
        push_issue(record["issues"], "tip", "variable_unused", "变量未被剧情引用", "如果不是预留变量，发布前可以考虑删除或改为备用分组。", base_context)
    elif record["writeCount"] > 0 and record["readCount"] == 0:
        push_issue(record["issues"], "warn", "variable_written_never_read", "变量被写入但没有条件读取", "这个变量会变化，但暂时不会影响任何分支；如果它是路线标记，建议补条件或说明用途。", base_context)
    elif record["readCount"] > 0 and record["writeCount"] == 0:
        push_issue(record["issues"], "tip", "variable_read_default_only", "条件只读取默认值", "这个变量被条件判断读取，但没有剧情卡或选项修改它，分支可能永远固定。", base_context)


def collect_references(bundle: dict, variables_by_id: dict[str, dict]) -> tuple[dict[str, dict], list[dict]]:
    records = {variable_id: create_variable_record(variable) for variable_id, variable in variables_by_id.items()}
    unknown_references: list[dict] = []
    for scene_record in get_ordered_scene_records(bundle):
        scene = scene_record["scene"]
        scene_name = scene_record["sceneName"]
        scene_id = scene_record["sceneId"]
        for block_index, block in enumerate([block for block in as_list(scene.get("blocks")) if isinstance(block, dict)]):
            block_id = clean_text(block.get("id"), f"block_{block_index + 1}")
            base = {
                "chapterName": scene_record["chapterName"],
                "sceneName": scene_name,
                "sceneId": scene_id,
                "blockId": block_id,
                "blockIndex": block_index,
                "label": f"{scene_record['chapterName']} / {scene_name} / 第 {block_index + 1} 张",
            }
            block_type = clean_text(block.get("type"))
            if block_type == "variable_set":
                record_reference(records, unknown_references, variables_by_id, {**base, "kind": "set", "variableId": block.get("variableId"), "value": block.get("value")})
            if block_type == "variable_add":
                record_reference(records, unknown_references, variables_by_id, {**base, "kind": "add", "variableId": block.get("variableId"), "value": block.get("value")})
            if block_type == "choice":
                for option_index, option in enumerate([option for option in as_list(block.get("options")) if isinstance(option, dict)]):
                    for effect_index, effect in enumerate([effect for effect in as_list(option.get("effects")) if isinstance(effect, dict)]):
                        record_reference(
                            records,
                            unknown_references,
                            variables_by_id,
                            {
                                **base,
                                "kind": "choice",
                                "variableId": effect.get("variableId"),
                                "value": effect.get("value"),
                                "effectType": effect.get("type"),
                                "optionText": clean_text(option.get("text"), f"选项 {option_index + 1}"),
                                "optionIndex": option_index,
                                "effectIndex": effect_index,
                            },
                        )
            if block_type == "condition":
                for branch_index, branch in enumerate([branch for branch in as_list(block.get("branches")) if isinstance(branch, dict)]):
                    for rule_index, rule in enumerate([rule for rule in as_list(branch.get("when")) if isinstance(rule, dict)]):
                        record_reference(
                            records,
                            unknown_references,
                            variables_by_id,
                            {**base, "kind": "condition", "variableId": rule.get("variableId"), "value": rule.get("value"), "branchIndex": branch_index, "ruleIndex": rule_index},
                        )
    return records, unknown_references


def get_variable_influence_status_digest(sheet: dict) -> dict:
    summary = sheet.get("summary") or {}
    if summary.get("variableCount", 0) == 0:
        return {"status": "empty", "title": "还没有变量影响表", "detail": "项目里暂时没有变量。需要好感度、路线旗标或开关时，可以先补基础变量包。"}
    if summary.get("blockerCount", 0) > 0:
        return {"status": "blocked", "title": f"有 {summary.get('blockerCount', 0)} 个变量逻辑阻塞", "detail": "优先修复坏变量引用、类型不匹配、数字范围错误和不合法加减。"}
    if summary.get("warningCount", 0) > 0:
        return {"status": "warn", "title": f"有 {summary.get('warningCount', 0)} 个变量逻辑提醒", "detail": "项目可以继续制作，但建议复查写入后未读取、默认值范围和可读性。"}
    return {"status": "ready", "title": "变量影响关系比较清晰", "detail": "当前变量定义、写入和条件读取没有明显结构风险。"}


def build_variable_influence_sheet(bundle: dict) -> dict:
    variables_by_id = get_variables_by_id(bundle)
    records, unknown_references = collect_references(bundle, variables_by_id)
    variable_records = list(records.values())
    issues: list[dict] = []

    for record in variable_records:
        inspect_variable_definition(record)
        add_record_level_usage_issues(record)
        record["status"] = get_status_from_issues(record["issues"])
        record["statusLabel"] = get_status_label(record["status"])
        issues.extend(record["issues"])

    for reference in unknown_references:
        variable_id = clean_text(reference.get("variableId"))
        issues.append(
            {
                "severity": "blocker",
                "code": "variable_reference_unknown" if variable_id else "variable_reference_missing",
                "title": "引用了不存在的变量" if variable_id else "变量引用为空",
                "detail": f"变量 {variable_id} 不在变量库中。" if variable_id else "剧情逻辑卡没有选择变量。",
                **reference,
            }
        )

    issues.sort(key=lambda issue: (-ISSUE_WEIGHT.get(issue.get("severity"), 0), clean_text(issue.get("variableName")), clean_text(issue.get("chapterName")), clean_text(issue.get("sceneName"))))
    references = [reference for record in variable_records for reference in record["references"]]
    blocker_count = sum(1 for issue in issues if issue.get("severity") == "blocker")
    warning_count = sum(1 for issue in issues if issue.get("severity") == "warn")
    tip_count = sum(1 for issue in issues if issue.get("severity") == "tip")
    readiness_penalty = min(100, blocker_count * 22 + warning_count * 8 + tip_count * 2)
    summary = {
        "variableCount": len(variable_records),
        "referencedVariableCount": sum(1 for record in variable_records if record["references"]),
        "unusedVariableCount": sum(1 for record in variable_records if not record["references"]),
        "readCount": sum(int(record["readCount"]) for record in variable_records),
        "writeCount": sum(int(record["writeCount"]) for record in variable_records),
        "choiceEffectCount": sum(int(record["choiceEffectCount"]) for record in variable_records),
        "conditionCount": sum(int(record["conditionCount"]) for record in variable_records),
        "unknownReferenceCount": len(unknown_references),
        "writtenNeverReadCount": sum(1 for issue in issues if issue.get("code") == "variable_written_never_read"),
        "readDefaultOnlyCount": sum(1 for issue in issues if issue.get("code") == "variable_read_default_only"),
        "blockerCount": blocker_count,
        "warningCount": warning_count,
        "tipCount": tip_count,
        "releaseReadinessPercent": max(0, 100 - readiness_penalty),
    }
    sheet = {
        "formatVersion": VARIABLE_INFLUENCE_FORMAT_VERSION,
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "projectTitle": get_project_title(bundle),
        "variables": variable_records,
        "references": references,
        "unknownReferences": unknown_references,
        "issues": issues,
        "summary": summary,
    }
    sheet["statusDigest"] = get_variable_influence_status_digest(sheet)
    return sheet


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


def build_variable_influence_report(sheet: dict) -> str:
    summary = sheet.get("summary") or {}
    digest = sheet.get("statusDigest") or get_variable_influence_status_digest(sheet)
    variable_rows = [
        [
            index + 1,
            record.get("variableName"),
            record.get("variableId"),
            record.get("typeLabel"),
            record.get("writeCount"),
            record.get("readCount"),
            record.get("choiceEffectCount"),
            record.get("conditionCount"),
            record.get("statusLabel"),
            " / ".join(as_list(record.get("locations"))),
        ]
        for index, record in enumerate((sheet.get("variables") or [])[:180])
    ]
    issue_rows = [
        [
            index + 1,
            "阻塞" if issue.get("severity") == "blocker" else "提醒" if issue.get("severity") == "warn" else "整理",
            issue.get("variableName") or issue.get("variableId"),
            issue.get("kindLabel") or "",
            issue.get("chapterName") or "",
            issue.get("sceneName") or "",
            issue.get("title"),
            issue.get("detail"),
        ]
        for index, issue in enumerate((sheet.get("issues") or [])[:180])
    ]
    return "\ufeff" + "\n".join(
        [
            f"# {sheet.get('projectTitle') or 'Canvasia Project'} 变量影响表",
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
                    ["变量", summary.get("variableCount", 0)],
                    ["被引用变量", summary.get("referencedVariableCount", 0)],
                    ["未引用变量", summary.get("unusedVariableCount", 0)],
                    ["写入次数", summary.get("writeCount", 0)],
                    ["条件读取", summary.get("readCount", 0)],
                    ["未知引用", summary.get("unknownReferenceCount", 0)],
                    ["写入未读取", summary.get("writtenNeverReadCount", 0)],
                    ["只读默认值", summary.get("readDefaultOnlyCount", 0)],
                    ["阻塞问题", summary.get("blockerCount", 0)],
                    ["复查提醒", summary.get("warningCount", 0)],
                    ["就绪度", f"{summary.get('releaseReadinessPercent', 0)}%"],
                ],
            ),
            "",
            "## 变量影响清单",
            "",
            markdown_table(["序号", "变量", "ID", "类型", "写入", "读取", "选项效果", "条件", "状态", "位置示例"], variable_rows) or "当前没有可列出的变量。",
            "",
            "## 需要复查的问题",
            "",
            markdown_table(["序号", "级别", "变量", "用途", "章节", "场景", "问题", "说明"], issue_rows) or "当前没有明显变量逻辑问题。",
            "",
        ]
    )


def build_variable_influence_csv(sheet: dict) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["序号", "变量", "ID", "类型", "写入", "读取", "直接设置", "数值增减", "选项效果", "条件读取", "状态", "位置示例", "问题"])
    for index, record in enumerate(sheet.get("variables") or []):
        writer.writerow(
            [
                index + 1,
                record.get("variableName"),
                record.get("variableId"),
                record.get("typeLabel"),
                record.get("writeCount"),
                record.get("readCount"),
                record.get("setCount"),
                record.get("addCount"),
                record.get("choiceEffectCount"),
                record.get("conditionCount"),
                record.get("statusLabel"),
                " / ".join(as_list(record.get("locations"))),
                " / ".join(issue.get("title", "") for issue in record.get("issues") or [] if issue.get("title")),
            ]
        )
    return "\ufeff" + output.getvalue()


def write_export_variable_influence_files(target_dir: Path, *, bundle: dict) -> dict:
    sheet = build_variable_influence_sheet(bundle)
    json_path = target_dir / EXPORT_VARIABLE_INFLUENCE_JSON_NAME
    report_path = target_dir / EXPORT_VARIABLE_INFLUENCE_REPORT_NAME
    csv_path = target_dir / EXPORT_VARIABLE_INFLUENCE_CSV_NAME
    json_path.write_text(json.dumps(sheet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(build_variable_influence_report(sheet), encoding="utf-8")
    csv_path.write_text(build_variable_influence_csv(sheet), encoding="utf-8")
    summary = sheet["summary"]
    return {
        "variableInfluenceSheet": sheet,
        "variableInfluenceName": json_path.name,
        "variableInfluencePath": str(json_path),
        "variableInfluenceReportName": report_path.name,
        "variableInfluenceReportPath": str(report_path),
        "variableInfluenceCsvName": csv_path.name,
        "variableInfluenceCsvPath": str(csv_path),
        "variableInfluenceReadinessPercent": summary["releaseReadinessPercent"],
        "variableInfluenceVariableCount": summary["variableCount"],
        "variableInfluenceReferencedVariableCount": summary["referencedVariableCount"],
        "variableInfluenceBlockerCount": summary["blockerCount"],
        "variableInfluenceWarningCount": summary["warningCount"],
    }


__all__ = [
    "EXPORT_VARIABLE_INFLUENCE_JSON_NAME",
    "EXPORT_VARIABLE_INFLUENCE_REPORT_NAME",
    "EXPORT_VARIABLE_INFLUENCE_CSV_NAME",
    "build_variable_influence_sheet",
    "build_variable_influence_report",
    "build_variable_influence_csv",
    "write_export_variable_influence_files",
]
