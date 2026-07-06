from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path

from export_story_route_map import build_export_story_route_map, clean_route_text


EXPORT_ROUTE_PLAYTEST_WORKBOOK_JSON_NAME = "route-playtest-workbook.json"
EXPORT_ROUTE_PLAYTEST_WORKBOOK_REPORT_NAME = "route-playtest-workbook.md"
EXPORT_ROUTE_PLAYTEST_WORKBOOK_CSV_NAME = "route-playtest-workbook.csv"
ROUTE_PLAYTEST_WORKBOOK_FORMAT_VERSION = 1


def as_list(value: object) -> list:
    return value if isinstance(value, list) else []


def to_count(value: object, fallback: int = 0) -> int:
    try:
        return max(0, round(float(value)))
    except (TypeError, ValueError):
        return fallback


def get_route_kind_label(route_kind: str) -> str:
    if route_kind == "choice":
        return "选项分支"
    if route_kind == "condition":
        return "条件分支"
    if route_kind == "fallback":
        return "否则分支"
    if route_kind == "jump":
        return "直接跳转"
    if route_kind == "ending":
        return "结局路径"
    return "路线"


def get_status_label(status: str) -> str:
    if status == "broken":
        return "坏链"
    if status == "unreachable":
        return "未接通"
    return "可试玩"


def get_execution_severity(status: str) -> str:
    if status == "broken":
        return "blocker"
    if status == "unreachable":
        return "warn"
    return "test"


def get_execution_phase(status: str) -> str:
    if status == "broken":
        return "先修坏链"
    if status == "unreachable":
        return "先接入口"
    return "人工试玩"


def get_route_testing_variable_preset_hint(item: dict) -> str:
    if item.get("routeKind") == "condition":
        return "自动回归会尝试把条件变量调到命中此分支；人工试玩时确认玩家能在前文自然获得这些变量。"
    if item.get("routeKind") == "fallback":
        return "自动回归会尝试让上方条件都不满足；人工试玩时确认失败线、普通线或保底线不会卡死。"
    if item.get("routeKind") == "choice":
        return "按玩家视角选择对应选项即可；若该选项会改变量，后续需要确认变量真的影响分支或回想。"
    if item.get("kind") == "ending":
        return "按路径完整跑到结局，顺手确认结局回想、CG/BGM/语音解锁和返回标题。"
    return "不需要额外变量预设，按路径进入并确认跳转结果。"


def build_manual_steps(item: dict) -> list[str]:
    if item.get("severity") == "blocker":
        return [
            f"打开「{item.get('sceneName') or '分支场景'}」并定位到 {get_route_kind_label(item.get('routeKind') or '')}。",
            f"重新选择或创建目标场景「{item.get('targetLabel') or '未设置目标'}」。",
            "重新生成路线试玩工作簿，确认这条用例不再显示坏链。",
        ]
    if item.get("severity") == "warn":
        return [
            f"从项目入口检查到「{item.get('sceneName') or '分支场景'}」的上游路径。",
            f"补一个跳转、选项或条件结果，让玩家能自然抵达「{item.get('targetLabel') or '目标场景'}」。",
            "重新进入试玩或自动回归，确认目标已经变成可达。",
        ]
    if item.get("kind") == "ending":
        return [
            f"从新游戏开始，按路径「{item.get('entryPathLabel') or '项目入口'}」完整跑到结局。",
            "确认结尾文本、演出、BGM 淡出、存档/读档和回想解锁都正常。",
            "返回标题页后再读一次关键存档，确认没有断档或状态丢失。",
        ]
    return [
        f"从入口按路径「{item.get('entryPathLabel') or '项目入口'}」进入「{item.get('sceneName') or '分支场景'}」。",
        f"触发 {get_route_kind_label(item.get('routeKind') or '')}「{item.get('routeLabel') or '路线'}」，确认进入「{item.get('targetLabel') or '目标场景'}」。",
        "检查该分支后的文本、立绘、BGM、存档和变量后果是否符合预期。",
    ]


def get_lane_detail(lane_id: str, items: list[dict]) -> str:
    if lane_id == "repair":
        return "先把这些断点接上，否则玩家或自动回归跑不到完整路线。" if items else "坏链和不可达路线已经清空。"
    if lane_id == "branch":
        return "每条可达分支都应该至少人工点一次，避免默认路线掩盖问题。" if items else "当前没有可单独执行的分支用例。"
    if lane_id == "ending":
        return "每个可打到结局都需要完整跑一遍，确认收束和解锁。" if items else "还没有可打到的结局路径。"
    return "这些用例适合交给自动回归优先执行。" if items else "暂无自动回归优先种子。"


def build_path_maps(route_map: dict) -> tuple[dict[str, str], dict[str, list[str]]]:
    entry_scene_id = clean_route_text(route_map.get("entrySceneId"))
    scenes = {clean_route_text(scene.get("sceneId")): scene for scene in as_list(route_map.get("scenes"))}
    adjacency: dict[str, list[dict]] = {scene_id: [] for scene_id in scenes}
    for route in as_list(route_map.get("routes")):
        if isinstance(route, dict):
            adjacency.setdefault(clean_route_text(route.get("sourceSceneId")), []).append(route)

    path_by_scene_id: dict[str, list[str]] = {}
    route_labels_by_scene_id: dict[str, list[str]] = {}
    if not entry_scene_id or entry_scene_id not in scenes:
        return {}, {}

    queue = [entry_scene_id]
    path_by_scene_id[entry_scene_id] = [clean_route_text(scenes[entry_scene_id].get("sceneName"), entry_scene_id)]
    route_labels_by_scene_id[entry_scene_id] = []
    cursor = 0
    while cursor < len(queue):
        source_id = queue[cursor]
        cursor += 1
        for route in adjacency.get(source_id, []):
            if not route.get("targetExists"):
                continue
            target_id = clean_route_text(route.get("targetSceneId"))
            if not target_id or target_id in path_by_scene_id or target_id not in scenes:
                continue
            path_by_scene_id[target_id] = [
                *path_by_scene_id[source_id],
                clean_route_text(scenes[target_id].get("sceneName"), target_id),
            ]
            route_labels_by_scene_id[target_id] = [
                *route_labels_by_scene_id[source_id],
                clean_route_text(route.get("label"), get_route_kind_label(clean_route_text(route.get("routeKind")))),
            ]
            queue.append(target_id)
    return {scene_id: " -> ".join(path) for scene_id, path in path_by_scene_id.items()}, route_labels_by_scene_id


def build_route_case(route: dict, point: dict, path_labels: dict[str, str], order: int) -> dict:
    target_id = clean_route_text(route.get("targetSceneId"))
    source_reachable = bool(point.get("isReachableFromEntry"))
    status = "ready"
    if not route.get("targetExists"):
        status = "broken"
    elif not source_reachable:
        status = "unreachable"
    return {
        "label": clean_route_text(route.get("label"), get_route_kind_label(clean_route_text(route.get("routeKind")))),
        "order": order,
        "routeId": ":".join(
            [
                clean_route_text(route.get("sourceSceneId")),
                clean_route_text(route.get("routeKind"), "route"),
                str(route.get("blockIndex") if route.get("blockIndex") is not None else ""),
                str(route.get("optionIndex") if route.get("optionIndex") is not None else ""),
                str(route.get("branchIndex") if route.get("branchIndex") is not None else ""),
                target_id,
            ]
        ),
        "routeKind": clean_route_text(route.get("routeKind")),
        "sourceSceneId": clean_route_text(route.get("sourceSceneId")),
        "sourceSceneName": clean_route_text(route.get("sourceSceneName")),
        "targetSceneId": target_id,
        "targetSceneName": clean_route_text(route.get("targetSceneName"), target_id),
        "targetPathLabel": path_labels.get(target_id, ""),
        "targetExists": bool(route.get("targetExists")),
        "status": status,
        "statusLabel": get_status_label(status),
        "blockIndex": route.get("blockIndex") if isinstance(route.get("blockIndex"), int) else None,
        "optionIndex": route.get("optionIndex") if isinstance(route.get("optionIndex"), int) else None,
        "branchIndex": route.get("branchIndex") if isinstance(route.get("branchIndex"), int) else None,
    }


def build_route_playtest_plan(route_map: dict) -> dict:
    path_labels, route_label_paths = build_path_maps(route_map)
    scenes = [scene for scene in as_list(route_map.get("scenes")) if isinstance(scene, dict)]
    decision_points: list[dict] = []

    for scene in scenes:
        routes = [route for route in as_list(scene.get("routes")) if isinstance(route, dict)]
        explicit_routes = [route for route in routes if not route.get("implicit")]
        is_decision_point = bool(scene.get("choiceCount") or scene.get("conditionCount") or len(explicit_routes) > 1)
        if not is_decision_point:
            continue
        point = {
            "sceneId": clean_route_text(scene.get("sceneId")),
            "sceneName": clean_route_text(scene.get("sceneName")),
            "chapterName": clean_route_text(scene.get("chapterName")),
            "routeDepth": scene.get("routeDepth"),
            "entryPathLabel": path_labels.get(clean_route_text(scene.get("sceneId")), ""),
            "isReachable": bool(scene.get("isReachableFromEntry")),
            "routeCases": [],
        }
        point["routeCases"] = [
            build_route_case(route, point, path_labels, route_index + 1)
            for route_index, route in enumerate(
                [
                    route
                    for route in routes
                    if clean_route_text(route.get("routeKind")) in {"choice", "condition", "fallback", "jump"}
                    or not route.get("implicit")
                ]
            )
        ]
        point["routeCount"] = len(point["routeCases"])
        point["brokenRouteCount"] = sum(1 for route_case in point["routeCases"] if route_case["status"] == "broken")
        point["unreachableTargetCount"] = sum(1 for route_case in point["routeCases"] if route_case["status"] == "unreachable")
        decision_points.append(point)

    ending_test_cases = []
    for index, ending in enumerate(as_list(route_map.get("endingCandidates"))):
        if not isinstance(ending, dict):
            continue
        scene_id = clean_route_text(ending.get("sceneId"))
        scene = next((item for item in scenes if clean_route_text(item.get("sceneId")) == scene_id), {})
        reachable = bool(ending.get("reachable"))
        ending_test_cases.append(
            {
                "order": index + 1,
                "sceneId": scene_id,
                "sceneName": clean_route_text(ending.get("sceneName"), scene_id),
                "chapterId": clean_route_text(scene.get("chapterId")),
                "chapterName": clean_route_text(scene.get("chapterName")),
                "routeDepth": scene.get("routeDepth"),
                "pathLabel": path_labels.get(scene_id, ""),
                "pathRouteLabels": route_label_paths.get(scene_id, []),
                "status": "ready" if reachable else "unreachable",
                "statusLabel": "可打到" if reachable else "未接通",
                "testingHint": "从新游戏开始完整跑到该结局，确认结尾、解锁、回想和返回标题都正常。" if reachable else "补齐入口后重新检查，确认玩家能自然打到该结局。",
            }
        )

    route_case_count = sum(len(point["routeCases"]) for point in decision_points)
    broken_count = sum(to_count(point.get("brokenRouteCount")) for point in decision_points)
    unreachable_count = sum(to_count(point.get("unreachableTargetCount")) for point in decision_points)
    summary = {
        "decisionPointCount": len(decision_points),
        "reachableDecisionPointCount": sum(1 for point in decision_points if point.get("isReachable")),
        "routeCaseCount": route_case_count,
        "brokenRouteCaseCount": broken_count,
        "unreachableRouteCaseCount": unreachable_count,
        "endingTestCaseCount": len(ending_test_cases),
        "reachableEndingTestCaseCount": sum(1 for item in ending_test_cases if item.get("status") == "ready"),
    }
    return {"summary": summary, "decisionPoints": decision_points, "endingTestCases": ending_test_cases}


def get_route_testing_status_digest(plan: dict) -> dict:
    summary = plan.get("summary") or {}
    blocked_count = to_count(summary.get("brokenRouteCaseCount")) + to_count(summary.get("unreachableRouteCaseCount"))
    total_case_count = to_count(summary.get("routeCaseCount")) + to_count(summary.get("endingTestCaseCount"))
    if total_case_count == 0:
        return {"status": "empty", "title": "还没有路线试玩用例", "detail": "项目里暂时没有可独立覆盖的分支或结局路径。"}
    if blocked_count > 0:
        return {"status": "blocked", "title": f"还有 {blocked_count} 条路线用例需要先接通", "detail": "优先处理坏链或入口不可达的分支，再开始完整试玩。"}
    return {"status": "ready", "title": "路线试玩工作簿已可执行", "detail": "当前分支和结局用例都能进入发布前人工试玩。"}


def get_route_testing_readiness_percent(plan: dict) -> int:
    summary = plan.get("summary") or {}
    total = to_count(summary.get("routeCaseCount")) + to_count(summary.get("endingTestCaseCount"))
    if total <= 0:
        return 0
    blocked = to_count(summary.get("brokenRouteCaseCount")) + to_count(summary.get("unreachableRouteCaseCount"))
    unreachable_endings = max(0, to_count(summary.get("endingTestCaseCount")) - to_count(summary.get("reachableEndingTestCaseCount")))
    ready = max(0, total - blocked - unreachable_endings)
    return max(0, min(100, round((ready / total) * 100)))


def get_execution_weight(item: dict) -> float:
    severity_weight = 1000 if item.get("severity") == "blocker" else 700 if item.get("severity") == "warn" else 260
    kind_weight = 60 if item.get("kind") == "ending" else 90
    try:
        depth = float(item.get("routeDepth"))
    except (TypeError, ValueError):
        depth = 999
    return severity_weight + kind_weight - min(depth, 20)


def build_execution_queue(plan: dict) -> list[dict]:
    queue: list[dict] = []
    for point_index, point in enumerate(as_list(plan.get("decisionPoints"))):
        for route_index, route_case in enumerate(as_list(point.get("routeCases"))):
            severity = get_execution_severity(clean_route_text(route_case.get("status")))
            queue.append(
                {
                    "id": f"route_{clean_route_text(point.get('sceneId'), str(point_index))}_{route_index + 1}",
                    "kind": "branch",
                    "severity": severity,
                    "phase": get_execution_phase(clean_route_text(route_case.get("status"))),
                    "title": "修复分支坏链" if route_case.get("status") == "broken" else "接通不可达目标" if route_case.get("status") == "unreachable" else "覆盖分支用例",
                    "chapterName": point.get("chapterName"),
                    "sceneName": point.get("sceneName"),
                    "sourceSceneId": route_case.get("sourceSceneId") or point.get("sceneId"),
                    "sourceSceneName": route_case.get("sourceSceneName") or point.get("sceneName"),
                    "targetSceneId": route_case.get("targetSceneId"),
                    "routeDepth": point.get("routeDepth"),
                    "entryPathLabel": point.get("entryPathLabel") or "入口未接通",
                    "routeLabel": route_case.get("label"),
                    "routeKind": route_case.get("routeKind"),
                    "routeCaseId": route_case.get("routeId"),
                    "blockIndex": route_case.get("blockIndex"),
                    "optionIndex": route_case.get("optionIndex"),
                    "branchIndex": route_case.get("branchIndex"),
                    "targetLabel": route_case.get("targetSceneName"),
                    "status": route_case.get("status"),
                    "statusLabel": route_case.get("statusLabel"),
                    "actionLabel": "重新选择目标场景" if route_case.get("status") == "broken" else "检查上游入口是否接回主路线" if route_case.get("status") == "unreachable" else "从入口跑到这里并点击该分支",
                    "acceptanceCriteria": "能按入口路径抵达分支点，选择该分支后进入目标场景，文本、演出、存档和回收状态正常。" if route_case.get("status") == "ready" else "修复后重新生成路线试玩工作簿，确认状态变为可试玩。",
                }
            )
    for index, test_case in enumerate(as_list(plan.get("endingTestCases"))):
        severity = get_execution_severity(clean_route_text(test_case.get("status")))
        queue.append(
            {
                "id": f"ending_{clean_route_text(test_case.get('sceneId'), str(index))}",
                "kind": "ending",
                "severity": severity,
                "phase": get_execution_phase(clean_route_text(test_case.get("status"))),
                "title": "完整跑通结局" if test_case.get("status") == "ready" else "接通结局入口",
                "chapterName": test_case.get("chapterName"),
                "sceneName": test_case.get("sceneName"),
                "sourceSceneId": test_case.get("sceneId"),
                "sourceSceneName": test_case.get("sceneName"),
                "targetSceneId": test_case.get("sceneId"),
                "routeDepth": test_case.get("routeDepth"),
                "entryPathLabel": test_case.get("pathLabel") or "暂未接通",
                "routeLabel": "结局路径",
                "routeKind": "ending",
                "routeCaseId": f"ending:{test_case.get('sceneId') or index}",
                "blockIndex": None,
                "optionIndex": None,
                "branchIndex": None,
                "targetLabel": test_case.get("sceneName"),
                "status": test_case.get("status"),
                "statusLabel": test_case.get("statusLabel"),
                "actionLabel": test_case.get("testingHint"),
                "acceptanceCriteria": "从新游戏开始按路径完整跑到该结局，确认结尾、解锁、回想、存档和返回标题都正常。" if test_case.get("status") == "ready" else "补齐入口后重新检查，确认玩家能自然打到该结局。",
            }
        )
    return [
        {**item, "rank": index + 1}
        for index, item in enumerate(
            sorted(queue, key=lambda item: (-get_execution_weight(item), clean_route_text(item.get("sceneName"))))
        )
    ]


def build_acceptance_checklist(plan: dict, queue: list[dict]) -> list[dict]:
    summary = plan.get("summary") or {}
    blocked_count = sum(1 for item in queue if item.get("severity") != "test")
    ready_branch_count = sum(1 for item in queue if item.get("kind") == "branch" and item.get("status") == "ready")
    ready_ending_count = sum(1 for item in queue if item.get("kind") == "ending" and item.get("status") == "ready")
    route_case_count = to_count(summary.get("routeCaseCount"))
    ending_case_count = to_count(summary.get("endingTestCaseCount"))
    return [
        {"id": "route_blockers_clear", "label": "路线阻塞清零", "done": blocked_count == 0, "detail": "坏链和入口不可达用例已经清掉。" if blocked_count == 0 else f"还有 {blocked_count} 条路线用例需要先接通。"},
        {"id": "branch_cases_played", "label": "分支用例逐条试玩", "done": route_case_count > 0 and ready_branch_count == route_case_count, "detail": f"可试玩分支 {ready_branch_count}/{route_case_count} 条。" if route_case_count > 0 else "当前没有分支用例；如果游戏有选择肢，建议先补分支点。"},
        {"id": "ending_cases_played", "label": "结局路径完整跑通", "done": ending_case_count > 0 and ready_ending_count == ending_case_count, "detail": f"可打到结局 {ready_ending_count}/{ending_case_count} 个。" if ending_case_count > 0 else "当前没有结局候选；建议至少做一个明确收束场景。"},
        {"id": "save_and_archive_checked", "label": "存档与回想联动确认", "done": blocked_count == 0 and ready_ending_count > 0, "detail": "跑结局时顺手确认保存、读档、文本历史、CG/BGM/语音回想和返回标题。"},
    ]


def build_workbook(plan: dict, execution_queue: list[dict]) -> dict:
    cards = [
        {
            **item,
            "kindLabel": "结局" if item.get("kind") == "ending" else "分支",
            "routeKindLabel": get_route_kind_label(clean_route_text(item.get("routeKind"))),
            "variablePresetHint": get_route_testing_variable_preset_hint(item),
            "manualSteps": build_manual_steps(item),
            "canAutoSmoke": item.get("status") == "ready" and item.get("kind") == "branch",
        }
        for item in execution_queue
    ]
    repair_items = [item for item in cards if item.get("severity") != "test"]
    branch_items = [item for item in cards if item.get("kind") == "branch" and item.get("status") == "ready"]
    ending_items = [item for item in cards if item.get("kind") == "ending" and item.get("status") == "ready"]
    auto_smoke_items = [item for item in cards if item.get("canAutoSmoke")][:8]
    lanes = [
        {"id": "repair", "label": "先修路线断点", "tone": "warn" if repair_items else "good", "itemCount": len(repair_items), "detail": get_lane_detail("repair", repair_items), "items": repair_items},
        {"id": "branch", "label": "逐条覆盖分支", "tone": "test" if branch_items else "soft", "itemCount": len(branch_items), "detail": get_lane_detail("branch", branch_items), "items": branch_items},
        {"id": "ending", "label": "完整跑通结局", "tone": "test" if ending_items else "soft", "itemCount": len(ending_items), "detail": get_lane_detail("ending", ending_items), "items": ending_items},
        {"id": "auto_smoke", "label": "自动回归优先种子", "tone": "good" if auto_smoke_items else "soft", "itemCount": len(auto_smoke_items), "detail": get_lane_detail("auto_smoke", auto_smoke_items), "items": auto_smoke_items},
    ]
    return {
        "summary": plan.get("summary") or {},
        "digest": get_route_testing_status_digest(plan),
        "readinessPercent": get_route_testing_readiness_percent(plan),
        "lanes": lanes,
        "cards": cards,
        "topCards": cards[:8],
        "nextBestAction": cards[0] if cards else None,
    }


def build_route_playtest_workbook(bundle: dict) -> dict:
    route_map = build_export_story_route_map(bundle)
    plan = build_route_playtest_plan(route_map)
    execution_queue = build_execution_queue(plan)
    checklist = build_acceptance_checklist(plan, execution_queue)
    workbook = build_workbook(plan, execution_queue)
    return {
        "formatVersion": ROUTE_PLAYTEST_WORKBOOK_FORMAT_VERSION,
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "projectTitle": clean_route_text(route_map.get("projectTitle"), "Canvasia Project"),
        "entrySceneId": route_map.get("entrySceneId"),
        "summary": {**(plan.get("summary") or {}), "readinessPercent": get_route_testing_readiness_percent(plan), "status": get_route_testing_status_digest(plan)["status"]},
        "statusDigest": get_route_testing_status_digest(plan),
        "plan": plan,
        "executionQueue": execution_queue,
        "acceptanceChecklist": checklist,
        "workbook": workbook,
    }


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


def build_route_playtest_report(sheet: dict) -> str:
    summary = sheet.get("summary") or {}
    digest = sheet.get("statusDigest") or {}
    queue = as_list(sheet.get("executionQueue"))
    checklist = as_list(sheet.get("acceptanceChecklist"))
    workbook_cards = as_list((sheet.get("workbook") or {}).get("topCards"))
    decision_points = as_list((sheet.get("plan") or {}).get("decisionPoints"))
    ending_test_cases = as_list((sheet.get("plan") or {}).get("endingTestCases"))
    return "\ufeff" + "\n".join(
        [
            f"# {sheet.get('projectTitle') or 'Canvasia Project'} 路线试玩工作簿",
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
                    ["分支检查点", summary.get("decisionPointCount", 0)],
                    ["从入口可到的分支点", summary.get("reachableDecisionPointCount", 0)],
                    ["路线用例", summary.get("routeCaseCount", 0)],
                    ["阻塞路线用例", to_count(summary.get("brokenRouteCaseCount")) + to_count(summary.get("unreachableRouteCaseCount"))],
                    ["结局用例", summary.get("endingTestCaseCount", 0)],
                    ["可打到结局用例", summary.get("reachableEndingTestCaseCount", 0)],
                    ["执行队列", len(queue)],
                    ["路线就绪度", f"{summary.get('readinessPercent', 0)}%"],
                ],
            ),
            "",
            "## 执行优先队列",
            "",
            markdown_table(
                ["序号", "阶段", "类型", "任务", "位置", "路线/目标", "动作", "通过标准"],
                [
                    [item.get("rank"), item.get("phase"), "结局" if item.get("kind") == "ending" else "分支", item.get("title"), f"{item.get('chapterName')} · {item.get('sceneName')}", f"{item.get('routeLabel')} -> {item.get('targetLabel')}", item.get("actionLabel"), item.get("acceptanceCriteria")]
                    for item in queue[:80]
                ],
            )
            or "当前没有可执行的路线试玩队列。",
            "",
            "## 验收标准",
            "",
            markdown_table(["项目", "状态", "说明"], [[item.get("label"), "完成" if item.get("done") else "待处理", item.get("detail")] for item in checklist]) or "当前没有可列出的路线验收标准。",
            "",
            "## 发布前路线工作簿",
            "",
            markdown_table(
                ["序号", "阶段", "对象", "位置", "执行步骤", "变量 / 状态提示", "验收口径"],
                [
                    [item.get("rank"), item.get("phase"), f"{item.get('kindLabel')} / {item.get('routeKindLabel')}", f"{item.get('chapterName')} · {item.get('sceneName')}", "<br />".join(as_list(item.get("manualSteps"))), item.get("variablePresetHint"), item.get("acceptanceCriteria")]
                    for item in workbook_cards
                ],
            )
            or "当前没有可列出的路线执行步骤。",
            "",
            "## 分支检查点",
            "",
            markdown_table(
                ["分支点", "入口路径", "路线用例", "阻塞"],
                [
                    [
                        f"{point.get('chapterName')} · {point.get('sceneName')}",
                        point.get("entryPathLabel") or "入口未接通",
                        " / ".join(f"{case.get('label')} -> {case.get('targetSceneName')}（{case.get('statusLabel')}）" for case in as_list(point.get("routeCases"))[:8]),
                        to_count(point.get("brokenRouteCount")) + to_count(point.get("unreachableTargetCount")),
                    ]
                    for point in decision_points[:40]
                ],
            )
            or "当前没有需要单独覆盖的分支点。",
            "",
            "## 结局试玩路径",
            "",
            markdown_table(["结局", "状态", "路径", "测试提示"], [[f"{case.get('chapterName')} · {case.get('sceneName')}", case.get("statusLabel"), case.get("pathLabel") or "暂未接通", case.get("testingHint")] for case in ending_test_cases[:40]]) or "当前没有可列出的结局试玩路径。",
            "",
            "## 使用建议",
            "",
            "1. 先处理状态为坏链或未接通的路线用例。",
            "2. 每个分支检查点至少试玩一次所有选项或条件结果。",
            "3. 每个可打到结局都完整跑一遍，确认文本、演出、存档和回想解锁正常。",
            "",
        ]
    )


def build_route_playtest_csv(sheet: dict) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["类型", "序号", "章节", "场景", "入口/路径", "路线/目标", "状态", "测试提示"])
    writer.writerow(["项目", "", sheet.get("projectTitle"), "", "", "", "", ""])
    for item in as_list(sheet.get("executionQueue")):
        writer.writerow(["执行队列", item.get("rank"), item.get("chapterName"), item.get("sceneName"), item.get("entryPathLabel"), f"{item.get('routeLabel')} -> {item.get('targetLabel')}", item.get("statusLabel"), f"{item.get('actionLabel')} / {item.get('acceptanceCriteria')}"])
    for item in as_list((sheet.get("workbook") or {}).get("topCards")):
        writer.writerow(["路线工作簿", item.get("rank"), item.get("chapterName"), item.get("sceneName"), item.get("entryPathLabel"), f"{item.get('routeKindLabel')}：{item.get('routeLabel')} -> {item.get('targetLabel')}", item.get("statusLabel"), f"{' / '.join(as_list(item.get('manualSteps')))} / {item.get('variablePresetHint')} / {item.get('acceptanceCriteria')}"])
    for point_index, point in enumerate(as_list((sheet.get("plan") or {}).get("decisionPoints"))):
        for route_index, route_case in enumerate(as_list(point.get("routeCases"))):
            writer.writerow(["分支路线", f"{point_index + 1}.{route_index + 1}", point.get("chapterName"), point.get("sceneName"), point.get("entryPathLabel") or "入口未接通", f"{route_case.get('label')} -> {route_case.get('targetSceneName')}", route_case.get("statusLabel"), "按此分支进入目标场景并确认演出正常。" if route_case.get("targetExists") else "先修复目标场景缺失或名称变更。"])
    for index, test_case in enumerate(as_list((sheet.get("plan") or {}).get("endingTestCases"))):
        writer.writerow(["结局路径", index + 1, test_case.get("chapterName"), test_case.get("sceneName"), test_case.get("pathLabel") or "暂未接通", test_case.get("sceneName"), test_case.get("statusLabel"), test_case.get("testingHint")])
    return "\ufeff" + output.getvalue()


def write_export_route_playtest_workbook_files(target_dir: Path, *, bundle: dict) -> dict:
    sheet = build_route_playtest_workbook(bundle)
    json_path = target_dir / EXPORT_ROUTE_PLAYTEST_WORKBOOK_JSON_NAME
    report_path = target_dir / EXPORT_ROUTE_PLAYTEST_WORKBOOK_REPORT_NAME
    csv_path = target_dir / EXPORT_ROUTE_PLAYTEST_WORKBOOK_CSV_NAME
    json_path.write_text(json.dumps(sheet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(build_route_playtest_report(sheet), encoding="utf-8")
    csv_path.write_text(build_route_playtest_csv(sheet), encoding="utf-8")
    summary = sheet["summary"]
    return {
        "routePlaytestWorkbook": sheet,
        "routePlaytestWorkbookName": json_path.name,
        "routePlaytestWorkbookPath": str(json_path),
        "routePlaytestWorkbookReportName": report_path.name,
        "routePlaytestWorkbookReportPath": str(report_path),
        "routePlaytestWorkbookCsvName": csv_path.name,
        "routePlaytestWorkbookCsvPath": str(csv_path),
        "routePlaytestReadinessPercent": summary["readinessPercent"],
        "routePlaytestRouteCaseCount": summary["routeCaseCount"],
        "routePlaytestEndingCaseCount": summary["endingTestCaseCount"],
        "routePlaytestBlockedCaseCount": summary["brokenRouteCaseCount"] + summary["unreachableRouteCaseCount"],
    }


__all__ = [
    "EXPORT_ROUTE_PLAYTEST_WORKBOOK_JSON_NAME",
    "EXPORT_ROUTE_PLAYTEST_WORKBOOK_REPORT_NAME",
    "EXPORT_ROUTE_PLAYTEST_WORKBOOK_CSV_NAME",
    "build_route_playtest_workbook",
    "build_route_playtest_report",
    "build_route_playtest_csv",
    "write_export_route_playtest_workbook_files",
]
