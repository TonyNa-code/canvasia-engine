from __future__ import annotations

import json
import re
from collections import deque
from datetime import datetime
from pathlib import Path


EXPORT_STORY_ROUTE_MAP_JSON_NAME = "story_route_map.json"
EXPORT_STORY_ROUTE_MAP_REPORT_NAME = "story_route_map.md"
CONTINUE_TARGET_ID = "__continue__"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def clean_route_text(value: object, fallback: str = "") -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text or fallback


def truncate_route_text(value: object, max_length: int = 42) -> str:
    text = clean_route_text(value)
    safe_max = max(8, int(max_length or 42))
    return text if len(text) <= safe_max else text[: safe_max - 1].rstrip() + "..."


def iter_export_route_scene_records(bundle: dict) -> list[dict]:
    records: list[dict] = []
    for chapter_index, chapter in enumerate(bundle.get("chapters") or []):
        if not isinstance(chapter, dict):
            continue
        chapter_id = clean_route_text(chapter.get("id") or chapter.get("chapterId"), f"chapter_{chapter_index + 1}")
        chapter_name = clean_route_text(chapter.get("name") or chapter.get("title"), f"第 {chapter_index + 1} 章")
        scenes = chapter.get("scenes") if isinstance(chapter.get("scenes"), list) else []
        for scene_index, scene in enumerate(scenes):
            if not isinstance(scene, dict):
                continue
            scene_id = clean_route_text(scene.get("id"), f"scene_{chapter_index + 1}_{scene_index + 1}")
            records.append(
                {
                    "chapterId": chapter_id,
                    "chapterName": chapter_name,
                    "chapterIndex": chapter_index,
                    "scene": scene,
                    "sceneId": scene_id,
                    "sceneName": clean_route_text(scene.get("name") or scene.get("title"), scene_id),
                    "sceneIndex": scene_index,
                }
            )
    return records


def make_route_edge(
    *,
    source_record: dict,
    target_scene_id: object,
    route_kind: str,
    label: str,
    block_index: int | None = None,
    option_index: int | None = None,
    branch_index: int | None = None,
    implicit: bool = False,
    scene_ids: set[str],
) -> dict | None:
    target_id = clean_route_text(target_scene_id)
    if not target_id or target_id == CONTINUE_TARGET_ID:
        return None
    return {
        "sourceSceneId": source_record["sceneId"],
        "sourceSceneName": source_record["sceneName"],
        "targetSceneId": target_id,
        "targetSceneName": "",
        "targetExists": target_id in scene_ids,
        "routeKind": route_kind,
        "label": truncate_route_text(label or route_kind),
        "blockIndex": block_index,
        "optionIndex": option_index,
        "branchIndex": branch_index,
        "implicit": implicit,
    }


def collect_explicit_route_edges(source_record: dict, scene_ids: set[str]) -> list[dict]:
    edges: list[dict] = []
    scene = source_record["scene"]
    blocks = [block for block in scene.get("blocks") or [] if isinstance(block, dict)]

    for block_index, block in enumerate(blocks):
        block_type = clean_route_text(block.get("type"), "unknown")
        if block_type == "jump":
            edge = make_route_edge(
                source_record=source_record,
                target_scene_id=block.get("targetSceneId") or block.get("gotoSceneId") or block.get("sceneId"),
                route_kind="jump",
                label="直接跳转",
                block_index=block_index,
                scene_ids=scene_ids,
            )
            if edge:
                edges.append(edge)

        if block_type == "choice":
            for option_index, option in enumerate(block.get("options") or []):
                if not isinstance(option, dict):
                    continue
                edge = make_route_edge(
                    source_record=source_record,
                    target_scene_id=option.get("gotoSceneId") or option.get("targetSceneId") or option.get("sceneId"),
                    route_kind="choice",
                    label=option.get("text") or f"选项 {option_index + 1}",
                    block_index=block_index,
                    option_index=option_index,
                    scene_ids=scene_ids,
                )
                if edge:
                    edges.append(edge)

        if block_type == "condition":
            for branch_index, branch in enumerate(block.get("branches") or []):
                if not isinstance(branch, dict):
                    continue
                edge = make_route_edge(
                    source_record=source_record,
                    target_scene_id=branch.get("gotoSceneId") or branch.get("targetSceneId") or branch.get("sceneId"),
                    route_kind="condition",
                    label=branch.get("label") or branch.get("name") or f"条件分支 {branch_index + 1}",
                    block_index=block_index,
                    branch_index=branch_index,
                    scene_ids=scene_ids,
                )
                if edge:
                    edges.append(edge)
            edge = make_route_edge(
                source_record=source_record,
                target_scene_id=block.get("elseGotoSceneId") or block.get("elseTargetSceneId"),
                route_kind="fallback",
                label="否则",
                block_index=block_index,
                branch_index=-1,
                scene_ids=scene_ids,
            )
            if edge:
                edges.append(edge)

        for key, label in (
            ("targetSceneId", "目标场景"),
            ("gotoSceneId", "跳转场景"),
            ("nextSceneId", "下一场景"),
            ("trueTargetSceneId", "条件为真"),
            ("falseTargetSceneId", "条件为假"),
        ):
            edge = make_route_edge(
                source_record=source_record,
                target_scene_id=block.get(key),
                route_kind=block_type,
                label=label,
                block_index=block_index,
                scene_ids=scene_ids,
            )
            if edge and all(
                not (
                    existing["sourceSceneId"] == edge["sourceSceneId"]
                    and existing["targetSceneId"] == edge["targetSceneId"]
                    and existing["blockIndex"] == edge["blockIndex"]
                    and existing["routeKind"] == edge["routeKind"]
                )
                for existing in edges
            ):
                edges.append(edge)

    return edges


def scene_has_ending_marker(scene: dict) -> bool:
    blocks = [block for block in scene.get("blocks") or [] if isinstance(block, dict)]
    return any(clean_route_text(block.get("type")) in {"credits_roll", "ending"} for block in blocks)


def build_export_story_route_map(bundle: dict) -> dict:
    records = iter_export_route_scene_records(bundle)
    scene_ids = {record["sceneId"] for record in records}
    records_by_id = {record["sceneId"]: record for record in records}
    records_by_chapter: dict[str, list[dict]] = {}
    for record in records:
        records_by_chapter.setdefault(record["chapterId"], []).append(record)

    edges: list[dict] = []
    ending_scene_ids: set[str] = set()
    for record in records:
        explicit_edges = collect_explicit_route_edges(record, scene_ids)
        if explicit_edges:
            edges.extend(explicit_edges)
            continue
        if scene_has_ending_marker(record["scene"]):
            ending_scene_ids.add(record["sceneId"])
            continue
        chapter_records = sorted(records_by_chapter.get(record["chapterId"], []), key=lambda item: item["sceneIndex"])
        next_record = next((item for item in chapter_records if item["sceneIndex"] > record["sceneIndex"]), None)
        if next_record:
            edge = make_route_edge(
                source_record=record,
                target_scene_id=next_record["sceneId"],
                route_kind="auto_next",
                label="同章下一场景",
                implicit=True,
                scene_ids=scene_ids,
            )
            if edge:
                edges.append(edge)
        else:
            ending_scene_ids.add(record["sceneId"])

    for edge in edges:
        target_record = records_by_id.get(edge["targetSceneId"])
        edge["targetSceneName"] = target_record["sceneName"] if target_record else edge["targetSceneId"]

    adjacency: dict[str, list[dict]] = {record["sceneId"]: [] for record in records}
    incoming_counts: dict[str, int] = {record["sceneId"]: 0 for record in records}
    for edge in edges:
        adjacency.setdefault(edge["sourceSceneId"], []).append(edge)
        if edge["targetExists"]:
            incoming_counts[edge["targetSceneId"]] = incoming_counts.get(edge["targetSceneId"], 0) + 1

    project = bundle.get("project") if isinstance(bundle.get("project"), dict) else {}
    entry_scene_id = clean_route_text(project.get("entrySceneId"), records[0]["sceneId"] if records else "")
    entry_exists = bool(entry_scene_id and entry_scene_id in scene_ids)
    reachable_scene_ids: set[str] = set()
    route_depth_by_scene_id: dict[str, int] = {}
    predecessor_by_scene_id: dict[str, dict] = {}
    if entry_exists:
        queue: deque[str] = deque([entry_scene_id])
        reachable_scene_ids.add(entry_scene_id)
        route_depth_by_scene_id[entry_scene_id] = 0
        while queue:
            source_scene_id = queue.popleft()
            current_depth = route_depth_by_scene_id.get(source_scene_id, 0)
            for edge in adjacency.get(source_scene_id, []):
                target_id = edge["targetSceneId"]
                if not edge["targetExists"] or target_id in reachable_scene_ids:
                    continue
                reachable_scene_ids.add(target_id)
                route_depth_by_scene_id[target_id] = current_depth + 1
                predecessor_by_scene_id[target_id] = edge
                queue.append(target_id)

    scene_nodes: list[dict] = []
    for record in records:
        scene = record["scene"]
        blocks = [block for block in scene.get("blocks") or [] if isinstance(block, dict)]
        outgoing_edges = adjacency.get(record["sceneId"], [])
        scene_nodes.append(
            {
                "sceneId": record["sceneId"],
                "sceneName": record["sceneName"],
                "chapterId": record["chapterId"],
                "chapterName": record["chapterName"],
                "chapterIndex": record["chapterIndex"],
                "sceneIndex": record["sceneIndex"],
                "isEntry": record["sceneId"] == entry_scene_id,
                "isReachableFromEntry": record["sceneId"] in reachable_scene_ids,
                "routeDepth": route_depth_by_scene_id.get(record["sceneId"]),
                "incomingCount": incoming_counts.get(record["sceneId"], 0),
                "outgoingCount": len(outgoing_edges),
                "blockCount": len(blocks),
                "dialogueCount": sum(1 for block in blocks if clean_route_text(block.get("type")) == "dialogue"),
                "narrationCount": sum(1 for block in blocks if clean_route_text(block.get("type")) == "narration"),
                "choiceCount": sum(1 for block in blocks if clean_route_text(block.get("type")) == "choice"),
                "conditionCount": sum(1 for block in blocks if clean_route_text(block.get("type")) == "condition"),
                "isEndingCandidate": record["sceneId"] in ending_scene_ids,
                "routes": outgoing_edges,
            }
        )

    broken_routes = [edge for edge in edges if not edge["targetExists"]]
    unreachable_scenes = [node for node in scene_nodes if not node["isReachableFromEntry"]]
    reachable_endings = [scene_id for scene_id in ending_scene_ids if scene_id in reachable_scene_ids]
    route_case_count = sum(
        1
        for node in scene_nodes
        if node["choiceCount"] or node["conditionCount"] or len(node["routes"]) > 1
    )
    status = "ready"
    if broken_routes or not entry_exists:
        status = "blocked"
    elif unreachable_scenes:
        status = "needs_review"

    summary = {
        "status": status,
        "sceneCount": len(scene_nodes),
        "chapterCount": len(records_by_chapter),
        "routeCount": len(edges),
        "explicitRouteCount": sum(1 for edge in edges if not edge["implicit"]),
        "implicitRouteCount": sum(1 for edge in edges if edge["implicit"]),
        "brokenRouteCount": len(broken_routes),
        "unreachableSceneCount": len(unreachable_scenes),
        "endingCandidateCount": len(ending_scene_ids),
        "reachableEndingCount": len(reachable_endings),
        "decisionPointCount": route_case_count,
        "maxRouteDepth": max(route_depth_by_scene_id.values()) if route_depth_by_scene_id else 0,
        "entrySceneExists": entry_exists,
    }
    return {
        "formatVersion": 1,
        "generatedAt": now_iso(),
        "projectTitle": clean_route_text(project.get("title"), "未命名项目"),
        "entrySceneId": entry_scene_id,
        "summary": summary,
        "scenes": scene_nodes,
        "routes": edges,
        "brokenRoutes": broken_routes,
        "unreachableScenes": unreachable_scenes,
        "endingCandidates": [
            {
                "sceneId": scene_id,
                "sceneName": records_by_id.get(scene_id, {}).get("sceneName", scene_id),
                "reachable": scene_id in reachable_scene_ids,
            }
            for scene_id in sorted(ending_scene_ids)
        ],
    }


def markdown_cell(value: object) -> str:
    return clean_route_text(value, "-").replace("|", "\\|")


def build_export_story_route_map_markdown(route_map: dict) -> str:
    summary = route_map.get("summary") if isinstance(route_map.get("summary"), dict) else {}
    scenes = route_map.get("scenes") if isinstance(route_map.get("scenes"), list) else []
    broken_routes = route_map.get("brokenRoutes") if isinstance(route_map.get("brokenRoutes"), list) else []
    unreachable_scenes = route_map.get("unreachableScenes") if isinstance(route_map.get("unreachableScenes"), list) else []
    ending_candidates = route_map.get("endingCandidates") if isinstance(route_map.get("endingCandidates"), list) else []
    status_labels = {
        "ready": "路线可试玩",
        "needs_review": "需要复核",
        "blocked": "存在阻塞",
    }

    lines = [
        "# 剧情路线图随包报告",
        "",
        f"- 项目：{markdown_cell(route_map.get('projectTitle'))}",
        f"- 入口场景：`{markdown_cell(route_map.get('entrySceneId'))}`",
        f"- 状态：{markdown_cell(status_labels.get(str(summary.get('status')), summary.get('status')))}",
        f"- 场景：{markdown_cell(summary.get('sceneCount'))} 个",
        f"- 路线：{markdown_cell(summary.get('routeCount'))} 条（显式 {markdown_cell(summary.get('explicitRouteCount'))} / 自动顺接 {markdown_cell(summary.get('implicitRouteCount'))}）",
        f"- 坏跳转：{markdown_cell(summary.get('brokenRouteCount'))} 条",
        f"- 入口不可达场景：{markdown_cell(summary.get('unreachableSceneCount'))} 个",
        f"- 结局候选：{markdown_cell(summary.get('reachableEndingCount'))}/{markdown_cell(summary.get('endingCandidateCount'))} 可达",
        "",
        "## 优先复查",
        "",
    ]
    if not broken_routes and not unreachable_scenes and summary.get("entrySceneExists"):
        lines.append("- 暂未发现路线阻塞项。")
    if not summary.get("entrySceneExists"):
        lines.append("- [blocker] 入口场景不存在：请在项目设置中重新指定 entrySceneId。")
    for route in broken_routes[:20]:
        lines.append(
            f"- [blocker] {markdown_cell(route.get('sourceSceneName'))} -> `{markdown_cell(route.get('targetSceneId'))}`："
            "目标场景不存在。"
        )
    if len(broken_routes) > 20:
        lines.append(f"- 还有 {len(broken_routes) - 20} 条坏跳转，请查看 `{EXPORT_STORY_ROUTE_MAP_JSON_NAME}`。")
    for node in unreachable_scenes[:20]:
        if node.get("isEntry"):
            continue
        lines.append(f"- [review] {markdown_cell(node.get('sceneName'))}：从入口场景自然流程无法抵达。")
    if len(unreachable_scenes) > 20:
        lines.append(f"- 还有 {len(unreachable_scenes) - 20} 个不可达场景，请查看 `{EXPORT_STORY_ROUTE_MAP_JSON_NAME}`。")

    lines.extend(["", "## 路线明细", "", "| 场景 | 可达 | 出口 | 入口数 | 说明 |", "| --- | --- | ---: | ---: | --- |"])
    for node in scenes:
        route_labels = []
        for route in node.get("routes") or []:
            target_label = route.get("targetSceneName") or route.get("targetSceneId") or "未设置"
            route_labels.append(f"{route.get('label') or route.get('routeKind')} -> {target_label}")
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(node.get("sceneName")),
                    "是" if node.get("isReachableFromEntry") else "否",
                    markdown_cell(node.get("outgoingCount")),
                    markdown_cell(node.get("incomingCount")),
                    markdown_cell("；".join(route_labels[:4]) or ("结局候选" if node.get("isEndingCandidate") else "无出口")),
                ]
            )
            + " |"
        )

    lines.extend(["", "## 结局候选", ""])
    if ending_candidates:
        for ending in ending_candidates:
            lines.append(
                f"- {'可达' if ending.get('reachable') else '不可达'}：{markdown_cell(ending.get('sceneName'))}"
            )
    else:
        lines.append("- 当前没有识别到结局候选。")
    lines.append("")
    return "\n".join(lines)


def write_export_story_route_map_files(target_dir: Path, bundle: dict) -> dict:
    route_map = build_export_story_route_map(bundle)
    json_path = target_dir / EXPORT_STORY_ROUTE_MAP_JSON_NAME
    markdown_path = target_dir / EXPORT_STORY_ROUTE_MAP_REPORT_NAME
    json_path.write_text(json.dumps(route_map, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(build_export_story_route_map_markdown(route_map), encoding="utf-8")
    summary = route_map.get("summary") if isinstance(route_map.get("summary"), dict) else {}
    return {
        "storyRouteMapName": json_path.name,
        "storyRouteMapPath": str(json_path),
        "storyRouteMapReportName": markdown_path.name,
        "storyRouteMapReportPath": str(markdown_path),
        "storyRouteMapStatus": summary.get("status") or "unknown",
        "storyRouteBrokenRouteCount": int(summary.get("brokenRouteCount") or 0),
        "storyRouteUnreachableSceneCount": int(summary.get("unreachableSceneCount") or 0),
        "storyRouteMap": route_map,
    }


__all__ = [
    "EXPORT_STORY_ROUTE_MAP_JSON_NAME",
    "EXPORT_STORY_ROUTE_MAP_REPORT_NAME",
    "build_export_story_route_map",
    "build_export_story_route_map_markdown",
    "write_export_story_route_map_files",
]
