#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shlex
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


ROOT_DIR = Path(__file__).resolve().parents[2]
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
AUDIO_EXTENSIONS = {".wav", ".mp3", ".ogg", ".m4a", ".flac"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".m4v"}
MODEL_EXTENSIONS = {".glb", ".gltf", ".vrm", ".fbx", ".obj"}
ASSET_TYPE_EXTENSIONS = {
    "background": IMAGE_EXTENSIONS,
    "cg": IMAGE_EXTENSIONS,
    "sprite": IMAGE_EXTENSIONS,
    "ui": IMAGE_EXTENSIONS,
    "image": IMAGE_EXTENSIONS,
    "voice": AUDIO_EXTENSIONS,
    "bgm": AUDIO_EXTENSIONS,
    "sfx": AUDIO_EXTENSIONS,
    "audio": AUDIO_EXTENSIONS,
    "video": VIDEO_EXTENSIONS,
    "live2d": {".json", ".model3.json", ".moc3"},
    "model3d": MODEL_EXTENSIONS,
}
ASSET_REFERENCE_KEYS = {
    "assetId",
    "voiceAssetId",
    "panelAssetId",
    "fontAssetId",
    "titleBackgroundAssetId",
    "titleLogoAssetId",
    "panelFrameAssetId",
    "buttonFrameAssetId",
    "buttonHoverFrameAssetId",
    "buttonPressedFrameAssetId",
    "buttonDisabledFrameAssetId",
    "saveSlotFrameAssetId",
    "systemPanelFrameAssetId",
    "uiOverlayAssetId",
    "fallbackSpriteAssetId",
    "modelAssetId",
}
SAFE_REPAIR_CODES = {"entry_scene", "chapter_order", "scene_order"}
SAFE_REPAIR_CODE_LABEL = ", ".join(sorted(SAFE_REPAIR_CODES))


@dataclass(frozen=True)
class HealthIssue:
    severity: str
    code: str
    title: str
    detail: str
    location: str = ""
    recovery: str = ""
    repair_code: str = ""

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "severity": self.severity,
            "code": self.code,
            "title": self.title,
            "detail": self.detail,
            "location": self.location,
            "recovery": self.recovery,
        }
        if self.repair_code:
            payload["repairCode"] = self.repair_code
            payload["autoFixable"] = True
        return payload


def read_json_file(path: Path) -> tuple[Any | None, HealthIssue | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except FileNotFoundError:
        return None, HealthIssue(
            "error",
            "json_missing",
            "缺少项目文件",
            f"找不到 {path.name}。",
            display_path(path),
            "从备份或自动快照恢复这个文件，或者重新创建一个空白项目。",
        )
    except json.JSONDecodeError as error:
        return None, HealthIssue(
            "error",
            "json_invalid",
            "JSON 无法读取",
            f"{path.name} 第 {error.lineno} 行附近格式不正确：{error.msg}",
            display_path(path),
            "回到编辑器里重新保存项目；如果手动改过 JSON，请撤回最近的格式改动。",
        )


def write_json_file(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n", encoding="utf-8")


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT_DIR))
    except ValueError:
        return str(path)


def safe_asset_path(project_dir: Path, asset_path: str) -> tuple[Path | None, str]:
    raw_path = Path(asset_path)
    if raw_path.is_absolute():
        return None, "素材路径不能是本机绝对路径。"
    if any(part == ".." for part in raw_path.parts):
        return None, "素材路径不能跳出项目目录。"
    return project_dir / raw_path, ""


def collect_string_references(value: Any, keys: set[str], path: str = "$") -> list[tuple[str, str, str]]:
    references: list[tuple[str, str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in keys and isinstance(child, str) and child.strip():
                references.append((key, child.strip(), child_path))
            references.extend(collect_string_references(child, keys, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            references.extend(collect_string_references(child, keys, f"{path}[{index}]"))
    return references


def iter_chapter_files(project_dir: Path) -> Iterable[Path]:
    chapters_dir = project_dir / "data" / "chapters"
    if not chapters_dir.exists():
        return []
    return sorted(chapters_dir.glob("*.json"))


def normalize_text_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := str(item or "").strip())]


def dedupe_order_items(items: Sequence[str]) -> tuple[list[str], int]:
    seen: set[str] = set()
    deduped: list[str] = []
    duplicate_count = 0
    for item in items:
        if item in seen:
            duplicate_count += 1
            continue
        seen.add(item)
        deduped.append(item)
    return deduped, duplicate_count


def split_safe_repair_code_tokens(value: str | Sequence[str]) -> list[str]:
    raw_items = value.replace(",", " ").split() if isinstance(value, str) else value
    return [str(item or "").strip().lower() for item in raw_items if str(item or "").strip()]


def normalize_safe_repair_codes(value: str | Sequence[str] | None, report: dict[str, Any] | None = None) -> list[str]:
    if value is None:
        repair_counts = (report or {}).get("summary", {}).get("autoFixableByRepairCode", {})
        raw_items = repair_counts.keys() if isinstance(repair_counts, dict) else SAFE_REPAIR_CODES
    else:
        raw_items = split_safe_repair_code_tokens(value)

    codes: list[str] = []
    for item in raw_items:
        code = str(item or "").strip().lower()
        if code in SAFE_REPAIR_CODES and code not in codes:
            codes.append(code)
    return codes


def get_unknown_safe_repair_codes(value: str | Sequence[str]) -> list[str]:
    unknown_codes: list[str] = []
    for code in split_safe_repair_code_tokens(value):
        if code not in SAFE_REPAIR_CODES and code not in unknown_codes:
            unknown_codes.append(code)
    return unknown_codes


def load_repair_chapter_entries(project_dir: Path) -> list[tuple[Path, dict[str, Any]]]:
    entries: list[tuple[Path, dict[str, Any]]] = []
    for chapter_file in iter_chapter_files(project_dir):
        payload, error = read_json_file(chapter_file)
        if error or not isinstance(payload, dict):
            continue
        entries.append((chapter_file, payload))
    return entries


def get_first_repair_scene_id(project: dict[str, Any], chapters: Sequence[dict[str, Any]]) -> str:
    chapter_by_id = {chapter.get("chapterId"): chapter for chapter in chapters if chapter.get("chapterId")}
    ordered_chapter_ids = [
        chapter_id for chapter_id in normalize_text_list(project.get("chapterOrder")) if chapter_id in chapter_by_id
    ]
    ordered_chapter_ids.extend(
        chapter.get("chapterId")
        for chapter in chapters
        if chapter.get("chapterId") and chapter.get("chapterId") not in ordered_chapter_ids
    )

    for chapter_id in ordered_chapter_ids:
        chapter = chapter_by_id.get(chapter_id)
        if not chapter:
            continue
        scenes = [scene for scene in chapter.get("scenes", []) if isinstance(scene, dict)]
        scene_by_id = {scene.get("id"): scene for scene in scenes if scene.get("id")}
        scene_order = [scene_id for scene_id in normalize_text_list(chapter.get("sceneOrder")) if scene_id in scene_by_id]
        scene_order.extend(scene.get("id") for scene in scenes if scene.get("id") not in scene_order)
        if scene_order:
            return str(scene_order[0])
    return ""


def repair_safe_project_issues(
    project_dir: Path,
    repair_codes: str | Sequence[str] | None = None,
    report: dict[str, Any] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    project_dir = project_dir.resolve()
    selected_codes = normalize_safe_repair_codes(repair_codes, report)
    repairs: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []
    project_payload, project_error = read_json_file(project_dir / "project.json")
    if project_error or not isinstance(project_payload, dict):
        return {
            "changed": False,
            "wouldChange": False,
            "dryRun": bool(dry_run),
            "requestedCodes": selected_codes,
            "repairs": repairs,
            "skipped": [{"code": "project_json", "title": "项目文件无法读取", "detail": project_error.detail if project_error else ""}],
        }

    chapter_entries = load_repair_chapter_entries(project_dir)
    chapters = [chapter for _path, chapter in chapter_entries]
    project_changed = False

    if "chapter_order" in selected_codes:
        chapter_ids = [
            str(chapter.get("chapterId") or "").strip()
            for chapter in chapters
            if str(chapter.get("chapterId") or "").strip()
        ]
        chapter_id_set = set(chapter_ids)
        current_order = normalize_text_list(project_payload.get("chapterOrder"))
        valid_order, duplicate_count = dedupe_order_items([chapter_id for chapter_id in current_order if chapter_id in chapter_id_set])
        valid_order_set = set(valid_order)
        missing_order = [chapter_id for chapter_id in chapter_ids if chapter_id not in valid_order_set]
        next_order = [*valid_order, *missing_order]
        removed_count = len([chapter_id for chapter_id in current_order if chapter_id and chapter_id not in chapter_id_set])
        if next_order != current_order:
            project_payload["chapterOrder"] = next_order
            project_changed = True
            repairs.append(
                {
                    "code": "chapter_order",
                    "title": "已整理章节顺序",
                    "detail": f"移除无效章节引用 {removed_count} 个，移除重复章节引用 {duplicate_count} 个，补回未进入排序的章节 {len(missing_order)} 个。",
                }
            )
        else:
            skipped.append({"code": "chapter_order", "title": "章节顺序无需修复", "detail": ""})

    if "scene_order" in selected_codes:
        for chapter_file, chapter in chapter_entries:
            scenes = [scene for scene in chapter.get("scenes", []) if isinstance(scene, dict)]
            scene_ids = [str(scene.get("id") or "").strip() for scene in scenes if str(scene.get("id") or "").strip()]
            scene_id_set = set(scene_ids)
            current_order = normalize_text_list(chapter.get("sceneOrder"))
            valid_order, duplicate_count = dedupe_order_items([scene_id for scene_id in current_order if scene_id in scene_id_set])
            valid_order_set = set(valid_order)
            missing_order = [scene_id for scene_id in scene_ids if scene_id not in valid_order_set]
            next_order = [*valid_order, *missing_order]
            removed_count = len([scene_id for scene_id in current_order if scene_id and scene_id not in scene_id_set])
            if next_order != current_order:
                chapter["sceneOrder"] = next_order
                if not dry_run:
                    write_json_file(chapter_file, chapter)
                repairs.append(
                    {
                        "code": "scene_order",
                        "title": f"已整理场景顺序：{chapter.get('name') or chapter.get('chapterId') or chapter_file.stem}",
                        "detail": f"移除无效场景引用 {removed_count} 个，移除重复场景引用 {duplicate_count} 个，补回未进入排序的场景 {len(missing_order)} 个。",
                    }
                )
            else:
                skipped.append(
                    {
                        "code": "scene_order",
                        "title": f"场景顺序无需修复：{chapter.get('name') or chapter.get('chapterId') or chapter_file.stem}",
                        "detail": "",
                    }
                )

    if "entry_scene" in selected_codes:
        all_scene_ids = {
            str(scene.get("id") or "").strip()
            for chapter in chapters
            for scene in chapter.get("scenes", [])
            if isinstance(scene, dict) and str(scene.get("id") or "").strip()
        }
        entry_scene_id = str(project_payload.get("entrySceneId") or "").strip()
        if entry_scene_id not in all_scene_ids:
            fallback_scene_id = get_first_repair_scene_id(project_payload, chapters)
            if fallback_scene_id:
                project_payload["entrySceneId"] = fallback_scene_id
                project_changed = True
                repairs.append(
                    {
                        "code": "entry_scene",
                        "title": "已修复入口场景",
                        "detail": f"入口场景已改为当前项目里的第一个可用场景：{fallback_scene_id}。",
                    }
                )
            else:
                skipped.append(
                    {
                        "code": "entry_scene",
                        "title": "入口场景无法自动修复",
                        "detail": "项目里还没有可用场景，请先新建章节和场景。",
                    }
                )
        else:
            skipped.append({"code": "entry_scene", "title": "入口场景无需修复", "detail": ""})

    if project_changed and not dry_run:
        write_json_file(project_dir / "project.json", project_payload)

    return {
        "changed": bool(repairs) and not dry_run,
        "wouldChange": bool(repairs),
        "dryRun": bool(dry_run),
        "requestedCodes": selected_codes,
        "repairs": repairs,
        "skipped": skipped,
    }


def build_safe_repair_command(report: dict[str, Any], dry_run: bool = False) -> str:
    repair_codes = normalize_safe_repair_codes(None, report)
    project_dir = str(report.get("projectDir") or "").strip()
    if not repair_codes or not project_dir:
        return ""
    command = [
        "python3",
        "tools/ci/project_health.py",
        project_dir,
        "--repair-safe",
    ]
    if dry_run:
        command.append("--repair-dry-run")
    command.extend(
        [
            "--repair-codes",
            ",".join(repair_codes),
        ]
    )
    return " ".join(shlex.quote(part) for part in command)


def build_summary(issues: Sequence[HealthIssue]) -> dict[str, Any]:
    errors = sum(1 for issue in issues if issue.severity == "error")
    warnings = sum(1 for issue in issues if issue.severity == "warning")
    infos = sum(1 for issue in issues if issue.severity == "info")
    repair_code_counts: dict[str, int] = {}
    for issue in issues:
        if issue.repair_code:
            repair_code_counts[issue.repair_code] = repair_code_counts.get(issue.repair_code, 0) + 1
    return {
        "status": "failed" if errors else "passed_with_warnings" if warnings else "passed",
        "errors": errors,
        "warnings": warnings,
        "infos": infos,
        "total": len(issues),
        "autoFixableCount": sum(repair_code_counts.values()),
        "autoFixableByRepairCode": dict(sorted(repair_code_counts.items())),
    }


def get_status_label(status: str) -> str:
    return {
        "passed": "基础健康",
        "passed_with_warnings": "可继续但建议复看",
        "failed": "需要先处理",
    }.get(status, "未知状态")


def get_issue_priority(issue: dict[str, Any]) -> int:
    severity = issue.get("severity")
    if severity == "error":
        return 0
    if severity == "warning":
        return 1
    return 2


def get_sorted_issues(report: dict[str, Any]) -> list[dict[str, Any]]:
    issues = [issue for issue in report.get("issues", []) if isinstance(issue, dict)]
    return sorted(issues, key=lambda issue: (get_issue_priority(issue), str(issue.get("code", ""))))


def build_issue_code_summary(report: dict[str, Any], limit: int = 5) -> list[tuple[str, int]]:
    counter = Counter(str(issue.get("code", "unknown")) for issue in report.get("issues", []) if isinstance(issue, dict))
    return counter.most_common(max(1, limit))


def iter_scene_blocks(chapters: Sequence[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    for chapter in chapters:
        scenes = chapter.get("scenes") if isinstance(chapter, dict) else []
        if not isinstance(scenes, list):
            continue
        for scene in scenes:
            blocks = scene.get("blocks") if isinstance(scene, dict) else []
            if not isinstance(blocks, list):
                continue
            for block in blocks:
                if isinstance(block, dict):
                    yield block


def count_ready_assets(project_dir: Path, assets: Sequence[dict[str, Any]]) -> int:
    ready_count = 0
    for asset in assets:
        asset_path = str(asset.get("path") or "").strip()
        if not asset_path:
            continue
        resolved_path, path_error = safe_asset_path(project_dir, asset_path)
        if not path_error and resolved_path and resolved_path.exists():
            ready_count += 1
    return ready_count


def build_project_metrics(
    project_dir: Path,
    project_payload: dict[str, Any] | None,
    assets_payload: dict[str, Any] | None,
    characters_payload: dict[str, Any] | None,
    variables_payload: dict[str, Any] | None,
    chapters: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    assets = assets_payload.get("assets") if isinstance(assets_payload, dict) else []
    characters = characters_payload.get("characters") if isinstance(characters_payload, dict) else []
    variables = variables_payload.get("variables") if isinstance(variables_payload, dict) else []
    safe_assets = [asset for asset in assets if isinstance(asset, dict)] if isinstance(assets, list) else []
    safe_characters = [character for character in characters if isinstance(character, dict)] if isinstance(characters, list) else []
    safe_variables = [variable for variable in variables if isinstance(variable, dict)] if isinstance(variables, list) else []
    safe_chapters = [chapter for chapter in chapters if isinstance(chapter, dict)]
    scenes = [
        scene
        for chapter in safe_chapters
        for scene in (chapter.get("scenes") if isinstance(chapter.get("scenes"), list) else [])
        if isinstance(scene, dict)
    ]
    blocks = list(iter_scene_blocks(safe_chapters))
    asset_references = [
        asset_id
        for _key, asset_id, _location in [
            *collect_string_references(project_payload or {}, ASSET_REFERENCE_KEYS, "project.json"),
            *[
                reference
                for chapter_index, chapter in enumerate(safe_chapters)
                for reference in collect_string_references(chapter, ASSET_REFERENCE_KEYS, f"chapter[{chapter_index}]")
            ],
        ]
    ]
    dialogue_like_types = {"dialogue", "narration"}

    return {
        "chapterCount": len(safe_chapters),
        "sceneCount": len(scenes),
        "blockCount": len(blocks),
        "dialogueBlockCount": sum(1 for block in blocks if block.get("type") in dialogue_like_types),
        "choiceBlockCount": sum(1 for block in blocks if block.get("type") == "choice"),
        "assetCount": len(safe_assets),
        "readyAssetCount": count_ready_assets(project_dir, safe_assets),
        "assetReferenceCount": len(asset_references),
        "uniqueAssetReferenceCount": len(set(asset_references)),
        "characterCount": len(safe_characters),
        "variableCount": len(safe_variables),
    }


def to_int(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def clamp_percent(value: float) -> int:
    return max(0, min(100, round(value)))


def get_percent(done: int, total: int) -> int:
    safe_total = to_int(total)
    if safe_total <= 0:
        return 0
    return clamp_percent((to_int(done) / safe_total) * 100)


def build_roadmap_check(
    check_id: str,
    label: str,
    done: bool,
    detail: str,
    missing: str,
    weight: int = 1,
    action: dict[str, Any] | None = None,
) -> dict[str, Any]:
    check = {
        "id": check_id,
        "label": label,
        "done": bool(done),
        "detail": detail,
        "missing": missing,
        "weight": max(1, to_int(weight) or 1),
    }
    if action:
        check["action"] = action
    return check


def create_roadmap_action(label: str, action: str, **extra: Any) -> dict[str, Any]:
    return {
        "label": label,
        "action": action,
        **extra,
    }


def score_roadmap_checks(checks: Sequence[dict[str, Any]]) -> int:
    total_weight = sum(to_int(check.get("weight", 1)) for check in checks)
    if total_weight <= 0:
        return 0
    done_weight = sum(to_int(check.get("weight", 1)) for check in checks if check.get("done"))
    return clamp_percent((done_weight / total_weight) * 100)


def build_roadmap_stage(
    stage_id: str,
    title: str,
    label: str,
    summary_when_done: str,
    summary_when_open: str,
    checks: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    blockers = [check for check in checks if not check.get("done")]
    wins = [check for check in checks if check.get("done")]
    percent = score_roadmap_checks(checks)
    primary_blocker = blockers[0] if blockers else None
    return {
        "id": stage_id,
        "title": title,
        "label": label,
        "percent": percent,
        "done": not blockers,
        "summary": summary_when_done if not blockers else summary_when_open,
        "primaryGap": primary_blocker,
        "blockers": blockers,
        "wins": wins,
        "checks": list(checks),
    }


def build_creation_roadmap(metrics: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    chapter_count = to_int(metrics.get("chapterCount"))
    scene_count = to_int(metrics.get("sceneCount"))
    block_count = to_int(metrics.get("blockCount"))
    dialogue_count = to_int(metrics.get("dialogueBlockCount"))
    choice_count = to_int(metrics.get("choiceBlockCount"))
    asset_count = to_int(metrics.get("assetCount"))
    ready_asset_count = to_int(metrics.get("readyAssetCount"))
    errors = to_int(summary.get("errors"))
    warnings = to_int(summary.get("warnings"))
    asset_ready_percent = get_percent(ready_asset_count, asset_count)
    actions = {
        "create_chapter": create_roadmap_action("创建第一章", "create-first-chapter"),
        "story": create_roadmap_action("去写正文", "switch-screen", screen="story"),
        "assets": create_roadmap_action("打开素材页", "switch-screen", screen="assets"),
        "inspection": create_roadmap_action("打开项目巡检", "switch-screen", screen="inspection"),
    }

    stages = [
        build_roadmap_stage(
            "first_playable",
            "第一版可试玩 Demo",
            "先让它跑起来",
            "已经具备第一版可试玩骨架，可以继续补氛围和流程。",
            "目标是先做出一段能打开、能阅读、能试玩的内容。",
            [
                build_roadmap_check(
                    "structure",
                    "章节和场景骨架",
                    chapter_count > 0 and scene_count > 0,
                    f"{chapter_count} 章 / {scene_count} 场",
                    "先创建第一章和第一场。",
                    2,
                    actions["create_chapter"],
                ),
                build_roadmap_check(
                    "story_text",
                    "第一段正文",
                    dialogue_count > 0,
                    f"{dialogue_count} 段台词或旁白",
                    "写入第一句旁白或台词。",
                    2,
                    actions["story"],
                ),
                build_roadmap_check(
                    "no_blocking_errors",
                    "没有阻塞错误",
                    errors == 0,
                    f"{errors} 项错误",
                    "先处理项目健康检查里的错误。",
                    2,
                    actions["inspection"],
                ),
            ],
        ),
        build_roadmap_stage(
            "vertical_slice",
            "体验版打磨",
            "像一段正式作品",
            "核心体验已经有内容、有素材，也有可确认的互动或流程。",
            "目标是让 Demo 不只是能跑，而是有画面、节奏和一点正式作品的感觉。",
            [
                build_roadmap_check(
                    "stage_asset",
                    "至少有一份可用素材",
                    ready_asset_count > 0,
                    f"{ready_asset_count}/{asset_count} 素材就绪",
                    "先导入一张背景、CG、BGM 或角色素材。",
                    1,
                    actions["assets"],
                ),
                build_roadmap_check(
                    "asset_ready",
                    "核心素材大多就绪",
                    asset_count > 0 and asset_ready_percent >= 70,
                    f"{asset_ready_percent}% 素材文件就绪",
                    "把已引用素材的真实文件补到 70% 以上。",
                    2,
                    actions["assets"],
                ),
                build_roadmap_check(
                    "story_texture",
                    "有互动或多场景节奏",
                    choice_count > 0 or scene_count >= 2,
                    f"{choice_count} 个选项 / {scene_count} 个场景",
                    "加一个选项，或拆出第二个场景确认推进节奏。",
                    1,
                    actions["story"],
                ),
                build_roadmap_check(
                    "warning_budget",
                    "提醒项可控",
                    warnings <= 5,
                    f"{warnings} 项提醒",
                    "把明显提醒项压到 5 项以内。",
                    1,
                    actions["inspection"],
                ),
            ],
        ),
        build_roadmap_stage(
            "release_candidate",
            "发布候选版",
            "准备给别人下载",
            "发布候选核心条件已经达标，适合进入人工长流程试玩和附件整理。",
            "目标是把会阻碍别人试玩的错误、缺素材和内容过短风险压下去。",
            [
                build_roadmap_check(
                    "zero_errors",
                    "结构错误清零",
                    errors == 0,
                    f"{errors} 项错误",
                    "先清零项目错误。",
                    3,
                    actions["inspection"],
                ),
                build_roadmap_check(
                    "zero_warnings",
                    "提醒项清零或已确认",
                    warnings == 0,
                    f"{warnings} 项提醒",
                    "发布前确认或处理所有提醒项。",
                    1,
                    actions["inspection"],
                ),
                build_roadmap_check(
                    "content_volume",
                    "内容量足够给别人试玩",
                    dialogue_count >= 5 or scene_count >= 3 or block_count >= 8,
                    f"{dialogue_count} 段文本 / {block_count} 张剧情卡",
                    "至少扩到几段台词、几个场景或一小段完整分支。",
                    2,
                    actions["story"],
                ),
                build_roadmap_check(
                    "all_assets_ready",
                    "素材文件全部就绪",
                    asset_count > 0 and ready_asset_count == asset_count,
                    f"{ready_asset_count}/{asset_count} 素材就绪",
                    "把所有素材条目都绑定到真实存在的文件。",
                    2,
                    actions["assets"],
                ),
            ],
        ),
    ]
    completed_count = sum(1 for stage in stages if stage["done"])
    next_stage = next((stage for stage in stages if not stage["done"]), stages[-1])
    overall_score = clamp_percent(sum(stage["percent"] for stage in stages) / max(len(stages), 1))

    return {
        "overallScore": overall_score,
        "completedCount": completed_count,
        "totalCount": len(stages),
        "headline": (
            "三阶段目标都已达标，接下来适合人工长流程试玩和发布素材整理。"
            if completed_count == len(stages)
            else f"当前优先推进：{next_stage['title']}。"
        ),
        "nextStage": next_stage,
        "stages": stages,
    }


def format_roadmap_next_action(report: dict[str, Any]) -> str:
    roadmap = report.get("roadmap", {}) if isinstance(report.get("roadmap"), dict) else {}
    next_stage = roadmap.get("nextStage", {}) if isinstance(roadmap.get("nextStage"), dict) else {}
    primary_gap = next_stage.get("primaryGap") if isinstance(next_stage.get("primaryGap"), dict) else None
    if not next_stage or next_stage.get("done") or not primary_gap:
        return ""
    action_hint = format_roadmap_action_hint(primary_gap.get("action"))
    return (
        f"按成品目标路线先补「{next_stage.get('title', '当前阶段')}」："
        f"{primary_gap.get('missing', '继续补齐当前阶段。')}{action_hint}"
    )


def format_roadmap_action_hint(action: Any) -> str:
    if not isinstance(action, dict):
        return ""
    label = str(action.get("label") or "").strip()
    return f"建议按钮：{label}。" if label else ""


def build_next_actions(report: dict[str, Any]) -> list[str]:
    summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}
    issues = get_sorted_issues(report)
    issue_codes = {str(issue.get("code", "")) for issue in issues}
    actions: list[str] = []

    if int(summary.get("autoFixableCount") or 0) > 0:
        safe_repair_command = str(report.get("safeRepairCommand") or "").strip()
        safe_repair_preview_command = str(report.get("safeRepairPreviewCommand") or "").strip()
        command_hint = ""
        if safe_repair_preview_command and safe_repair_command:
            command_hint = f"；命令行可选：先预览 {safe_repair_preview_command}，确认后修复 {safe_repair_command}"
        elif safe_repair_command:
            command_hint = f"；命令行可选：{safe_repair_command}"
        actions.append(
            "先在编辑器的项目巡检页运行“项目医生一键安全修复”，处理入口场景、章节顺序和场景顺序。"
            + command_hint
        )
    if {"asset_file_missing", "asset_reference_missing"} & issue_codes:
        actions.append("回到素材页重新导入缺失素材，或把剧情/角色/UI 引用改成现有素材。")
    if {"scene_reference_missing", "character_reference_missing", "variable_reference_missing"} & issue_codes:
        actions.append("打开剧情页检查跳转、角色和变量引用，把不存在的目标改成项目中真实存在的条目。")
    if {"json_missing", "json_invalid", "chapters_missing"} & issue_codes:
        actions.append("优先从自动快照或版本恢复里找回缺失/损坏的项目文件。")
    if not actions and issues:
        first_issue = issues[0]
        recovery = str(first_issue.get("recovery") or "").strip()
        actions.append(recovery or "先处理列表里的第一条问题，再重新运行项目健康检查。")
    if not actions:
        roadmap_action = format_roadmap_next_action(report)
        if roadmap_action:
            actions.append(roadmap_action)
    if not issues:
        actions.append("项目基础健康检查通过，可以继续试玩、导出或进入发布前检查。")

    return actions[:4]


def format_issue_brief(issue: dict[str, Any]) -> str:
    severity = str(issue.get("severity", "info"))
    title = str(issue.get("title", "未命名问题"))
    code = str(issue.get("code", "unknown"))
    location = str(issue.get("location") or "")
    location_suffix = f" @ {location}" if location else ""
    return f"[{severity}] {title} ({code}){location_suffix}"


def analyze_assets(project_dir: Path, assets_payload: dict[str, Any] | None) -> tuple[dict[str, dict[str, Any]], list[HealthIssue]]:
    issues: list[HealthIssue] = []
    assets_by_id: dict[str, dict[str, Any]] = {}
    if not isinstance(assets_payload, dict):
        return assets_by_id, [HealthIssue("error", "assets_invalid", "素材表无法读取", "data/assets.json 应该是一个对象。", "data/assets.json", "从自动快照恢复素材表，或在素材库重新导入素材。")]

    assets = assets_payload.get("assets")
    if not isinstance(assets, list):
        return assets_by_id, [HealthIssue("error", "assets_list_missing", "素材列表缺失", "data/assets.json 里需要 assets 数组。", "data/assets.json", "在素材库重新保存项目，或从自动快照恢复素材表。")]

    for index, asset in enumerate(assets):
        location = f"data/assets.json.assets[{index}]"
        if not isinstance(asset, dict):
            issues.append(HealthIssue("error", "asset_invalid", "素材条目无法读取", "这个素材条目不是对象。", location, "删除这条异常素材记录，或在素材库重新导入该素材。"))
            continue
        asset_id = str(asset.get("id") or "").strip()
        asset_type = str(asset.get("type") or "").strip()
        asset_path = str(asset.get("path") or "").strip()
        if not asset_id:
            issues.append(HealthIssue("error", "asset_id_missing", "素材缺少 ID", "每个素材都需要唯一 ID。", location, "在素材库删除并重新导入这个素材，让编辑器自动生成 ID。"))
            continue
        if asset_id in assets_by_id:
            issues.append(HealthIssue("error", "asset_id_duplicate", "素材 ID 重复", f"素材 ID `{asset_id}` 出现了多次。", location, "保留正确的那一个素材，另一个请重新导入并生成新 ID。"))
        assets_by_id[asset_id] = asset
        if not asset_path:
            issues.append(HealthIssue("error", "asset_path_missing", "素材缺少文件路径", f"素材 `{asset_id}` 没有 path。", location, "在素材库重新选择文件，或删除这个空素材记录。"))
            continue
        resolved_path, path_error = safe_asset_path(project_dir, asset_path)
        if path_error:
            issues.append(HealthIssue("error", "asset_path_unsafe", "素材路径不安全", f"素材 `{asset_id}`：{path_error}", location, "把素材复制进项目 assets 目录后重新导入，避免引用本机私有路径。"))
            continue
        if resolved_path and not resolved_path.exists():
            issues.append(HealthIssue("error", "asset_file_missing", "素材文件不存在", f"素材 `{asset_id}` 指向的文件不存在：{asset_path}", location, "把缺失文件放回这个路径，或在素材库重新导入并替换引用。"))
        extension = Path(asset_path).suffix.lower()
        allowed_extensions = ASSET_TYPE_EXTENSIONS.get(asset_type)
        if allowed_extensions and extension not in allowed_extensions:
            issues.append(
                HealthIssue(
                    "warning",
                    "asset_extension_unusual",
                    "素材格式可能不匹配",
                    f"素材 `{asset_id}` 类型是 `{asset_type}`，但文件扩展名是 `{extension or '无扩展名'}`。",
                    location,
                    "如果素材能正常预览可以暂时忽略；否则请转换成该类型常用格式后重新导入。",
                )
            )
    return assets_by_id, issues


def analyze_story_graph(project_dir: Path, project_payload: dict[str, Any] | None) -> tuple[set[str], list[dict[str, Any]], list[HealthIssue]]:
    issues: list[HealthIssue] = []
    scene_ids: set[str] = set()
    chapter_ids: set[str] = set()
    chapters: list[dict[str, Any]] = []
    chapter_files = list(iter_chapter_files(project_dir))
    if not chapter_files:
        issues.append(HealthIssue("error", "chapters_missing", "章节文件缺失", "data/chapters 里没有章节 JSON。", "data/chapters", "新建至少一个章节，或从自动快照恢复 data/chapters。"))
        return scene_ids, chapters, issues

    for chapter_file in chapter_files:
        chapter_payload, error = read_json_file(chapter_file)
        if error:
            issues.append(error)
            continue
        if not isinstance(chapter_payload, dict):
            issues.append(HealthIssue("error", "chapter_invalid", "章节无法读取", "章节 JSON 应该是一个对象。", display_path(chapter_file), "从自动快照恢复这个章节，或在编辑器里重新创建章节。"))
            continue
        chapters.append(chapter_payload)
        chapter_id = str(chapter_payload.get("chapterId") or chapter_file.stem).strip()
        if chapter_id:
            chapter_ids.add(chapter_id)
        scenes = chapter_payload.get("scenes")
        if not isinstance(scenes, list):
            issues.append(HealthIssue("error", "chapter_scenes_missing", "章节缺少场景列表", f"章节 `{chapter_id}` 缺少 scenes 数组。", display_path(chapter_file), "在章节里至少创建一个场景，然后重新保存项目。"))
            continue
        local_scene_ids: set[str] = set()
        for scene_index, scene in enumerate(scenes):
            location = f"{display_path(chapter_file)}.scenes[{scene_index}]"
            if not isinstance(scene, dict):
                issues.append(HealthIssue("error", "scene_invalid", "场景无法读取", "这个场景条目不是对象。", location, "删除异常场景记录，或从自动快照恢复该章节。"))
                continue
            scene_id = str(scene.get("id") or "").strip()
            if not scene_id:
                issues.append(HealthIssue("error", "scene_id_missing", "场景缺少 ID", "每个场景都需要唯一 ID。", location, "在编辑器里重新创建这个场景，让系统自动生成 ID。"))
                continue
            if scene_id in scene_ids:
                issues.append(HealthIssue("error", "scene_id_duplicate", "场景 ID 重复", f"场景 ID `{scene_id}` 出现了多次。", location, "保留正确场景，另一个请复制为新场景并生成新 ID。"))
            scene_ids.add(scene_id)
            local_scene_ids.add(scene_id)
        scene_order = chapter_payload.get("sceneOrder") or []
        if isinstance(scene_order, list):
            seen_ordered_scene_ids: set[str] = set()
            for order_index, ordered_scene_id in enumerate(scene_order):
                scene_id = str(ordered_scene_id or "").strip()
                if not scene_id:
                    continue
                if scene_id in seen_ordered_scene_ids:
                    issues.append(HealthIssue("warning", "scene_order_duplicate", "场景排序重复", f"sceneOrder 重复写入了场景 `{scene_id}`。", f"{display_path(chapter_file)}.sceneOrder[{order_index}]", "项目医生的一键安全修复会保留第一次出现的位置，并移除后面的重复项。", "scene_order"))
                    continue
                seen_ordered_scene_ids.add(scene_id)
                if scene_id not in local_scene_ids:
                    issues.append(HealthIssue("error", "scene_order_missing", "场景排序引用不存在", f"sceneOrder 引用了不存在的场景 `{scene_id}`。", display_path(chapter_file), "从场景排序里移除这个场景，或恢复同 ID 的场景。", "scene_order"))
            for scene_id in sorted(local_scene_ids - seen_ordered_scene_ids):
                issues.append(HealthIssue("warning", "scene_order_omitted", "场景没有进入排序", f"场景 `{scene_id}` 存在，但没有进入 sceneOrder。", display_path(chapter_file), "项目医生的一键安全修复会把遗漏场景补回本章顺序表。", "scene_order"))

    if isinstance(project_payload, dict):
        chapter_order = project_payload.get("chapterOrder") or []
        if isinstance(chapter_order, list):
            seen_ordered_chapter_ids: set[str] = set()
            for order_index, ordered_chapter_id in enumerate(chapter_order):
                chapter_id = str(ordered_chapter_id or "").strip()
                if not chapter_id:
                    continue
                if chapter_id in seen_ordered_chapter_ids:
                    issues.append(HealthIssue("warning", "chapter_order_duplicate", "章节排序重复", f"chapterOrder 重复写入了章节 `{chapter_id}`。", f"project.json.chapterOrder[{order_index}]", "项目医生的一键安全修复会保留第一次出现的位置，并移除后面的重复项。", "chapter_order"))
                    continue
                seen_ordered_chapter_ids.add(chapter_id)
                if chapter_id not in chapter_ids:
                    issues.append(HealthIssue("error", "chapter_order_missing", "章节排序引用不存在", f"chapterOrder 引用了不存在的章节 `{chapter_id}`。", "project.json.chapterOrder", "从章节排序里移除这个章节，或恢复同 ID 的章节。", "chapter_order"))
            for chapter_id in sorted(chapter_ids - seen_ordered_chapter_ids):
                issues.append(HealthIssue("warning", "chapter_order_omitted", "章节没有进入排序", f"章节 `{chapter_id}` 存在，但没有进入 chapterOrder。", "project.json.chapterOrder", "项目医生的一键安全修复会把遗漏章节补回排序表。", "chapter_order"))
        entry_scene_id = str(project_payload.get("entrySceneId") or "").strip()
        if entry_scene_id and entry_scene_id not in scene_ids:
            issues.append(HealthIssue("error", "entry_scene_missing", "入口场景不存在", f"项目入口场景 `{entry_scene_id}` 不存在。", "project.json.entrySceneId", "在项目设置里把入口场景改成现有场景，或恢复这个入口场景。", "entry_scene"))
    return scene_ids, chapters, issues


def analyze_references(
    project_payload: dict[str, Any] | None,
    chapters: Sequence[dict[str, Any]],
    assets_by_id: dict[str, dict[str, Any]],
    scene_ids: set[str],
    characters_payload: dict[str, Any] | None,
    variables_payload: dict[str, Any] | None,
) -> list[HealthIssue]:
    issues: list[HealthIssue] = []
    asset_ids = set(assets_by_id)
    characters = characters_payload.get("characters") if isinstance(characters_payload, dict) else []
    variables = variables_payload.get("variables") if isinstance(variables_payload, dict) else []
    character_ids = {str(character.get("id") or "").strip() for character in characters if isinstance(character, dict)}
    variable_ids = {str(variable.get("id") or "").strip() for variable in variables if isinstance(variable, dict)}

    for key, asset_id, location in collect_string_references(project_payload or {}, ASSET_REFERENCE_KEYS, "project.json"):
        if asset_id not in asset_ids:
            issues.append(HealthIssue("error", "asset_reference_missing", "引用的素材不存在", f"`{key}` 引用了不存在的素材 `{asset_id}`。", location, "在素材库重新导入该素材，或把这个引用改成已有素材。"))

    for chapter_index, chapter in enumerate(chapters):
        chapter_location = f"chapter[{chapter_index}]"
        for key, asset_id, location in collect_string_references(chapter, ASSET_REFERENCE_KEYS, chapter_location):
            if asset_id not in asset_ids:
                issues.append(HealthIssue("error", "asset_reference_missing", "引用的素材不存在", f"`{key}` 引用了不存在的素材 `{asset_id}`。", location, "在素材库重新导入该素材，或把这个引用改成已有素材。"))
        for key, target_scene_id, location in collect_string_references(chapter, {"targetSceneId", "gotoSceneId", "elseGotoSceneId"}, chapter_location):
            if target_scene_id not in scene_ids:
                issues.append(HealthIssue("error", "scene_reference_missing", "跳转目标不存在", f"`{key}` 指向了不存在的场景 `{target_scene_id}`。", location, "在对应选项/跳转/条件里选择一个现有场景，或恢复目标场景。"))
        for key, character_id, location in collect_string_references(chapter, {"speakerId", "characterId"}, chapter_location):
            if character_id not in character_ids:
                issues.append(HealthIssue("error", "character_reference_missing", "角色不存在", f"`{key}` 引用了不存在的角色 `{character_id}`。", location, "在角色库恢复该角色，或把台词/出场块改成已有角色。"))
        for key, variable_id, location in collect_string_references(chapter, {"variableId"}, chapter_location):
            if variable_id not in variable_ids:
                issues.append(HealthIssue("error", "variable_reference_missing", "变量不存在", f"`{key}` 引用了不存在的变量 `{variable_id}`。", location, "在变量面板恢复该变量，或把条件/效果改成已有变量。"))
    return issues


def analyze_project(project_dir: Path) -> dict[str, Any]:
    project_dir = project_dir.resolve()
    issues: list[HealthIssue] = []
    project_payload, project_error = read_json_file(project_dir / "project.json")
    assets_payload, assets_error = read_json_file(project_dir / "data" / "assets.json")
    characters_payload, characters_error = read_json_file(project_dir / "data" / "characters.json")
    variables_payload, variables_error = read_json_file(project_dir / "data" / "variables.json")
    issues.extend(issue for issue in [project_error, assets_error, characters_error, variables_error] if issue)

    assets_by_id, asset_issues = analyze_assets(project_dir, assets_payload if isinstance(assets_payload, dict) else None)
    issues.extend(asset_issues)
    scene_ids, chapters, graph_issues = analyze_story_graph(project_dir, project_payload if isinstance(project_payload, dict) else None)
    issues.extend(graph_issues)
    issues.extend(
        analyze_references(
            project_payload if isinstance(project_payload, dict) else None,
            chapters,
            assets_by_id,
            scene_ids,
            characters_payload if isinstance(characters_payload, dict) else None,
            variables_payload if isinstance(variables_payload, dict) else None,
        )
    )
    summary = build_summary(issues)
    metrics = build_project_metrics(
        project_dir,
        project_payload if isinstance(project_payload, dict) else None,
        assets_payload if isinstance(assets_payload, dict) else None,
        characters_payload if isinstance(characters_payload, dict) else None,
        variables_payload if isinstance(variables_payload, dict) else None,
        chapters,
    )

    report = {
        "projectDir": display_path(project_dir),
        "summary": summary,
        "metrics": metrics,
        "roadmap": build_creation_roadmap(metrics, summary),
        "issueCountsBySeverity": {
            "error": sum(1 for issue in issues if issue.severity == "error"),
            "warning": sum(1 for issue in issues if issue.severity == "warning"),
            "info": sum(1 for issue in issues if issue.severity == "info"),
        },
        "issues": [issue.as_dict() for issue in issues],
    }
    safe_repair_command = build_safe_repair_command(report)
    safe_repair_preview_command = build_safe_repair_command(report, dry_run=True)
    if safe_repair_command:
        report["safeRepairCommand"] = safe_repair_command
    if safe_repair_preview_command:
        report["safeRepairPreviewCommand"] = safe_repair_preview_command
    return report


def write_json_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{json.dumps(report, ensure_ascii=False, indent=2)}\n", encoding="utf-8")


def markdown_cell(value: Any) -> str:
    return str("" if value is None else value).replace("|", r"\|")


def write_markdown_report(path: Path, report: dict[str, Any]) -> None:
    summary = report.get("summary", {})
    metrics = report.get("metrics", {}) if isinstance(report.get("metrics"), dict) else {}
    roadmap = report.get("roadmap", {}) if isinstance(report.get("roadmap"), dict) else {}
    next_stage = roadmap.get("nextStage", {}) if isinstance(roadmap.get("nextStage"), dict) else {}
    primary_gap = next_stage.get("primaryGap") if isinstance(next_stage.get("primaryGap"), dict) else None
    roadmap_stages = roadmap.get("stages") if isinstance(roadmap.get("stages"), list) else []
    repair_code_counts = summary.get("autoFixableByRepairCode", {})
    status = str(summary.get("status", "unknown"))
    sorted_issues = get_sorted_issues(report)
    next_actions = build_next_actions(report)
    code_summary = build_issue_code_summary(report)
    repair_result = report.get("repairResult") if isinstance(report.get("repairResult"), dict) else None
    safe_repair_command = str(report.get("safeRepairCommand") or "").strip()
    safe_repair_preview_command = str(report.get("safeRepairPreviewCommand") or "").strip()
    lines = [
        "# Canvasia Engine Project Health Report",
        "",
        f"- Project: `{report.get('projectDir', '')}`",
        f"- Status: `{summary.get('status', 'unknown')}`",
        f"- Status label: {get_status_label(status)}",
        f"- Errors: {summary.get('errors', 0)}",
        f"- Warnings: {summary.get('warnings', 0)}",
        f"- Safe repairs: {summary.get('autoFixableCount', 0)}",
        f"- Roadmap: {roadmap.get('completedCount', 0)}/{roadmap.get('totalCount', 0)} stages · {roadmap.get('overallScore', 0)}%",
    ]
    if isinstance(repair_code_counts, dict) and repair_code_counts:
        lines.append(
            "- Safe repair groups: "
            + ", ".join(f"{repair_code}={count}" for repair_code, count in sorted(repair_code_counts.items()))
        )
    if safe_repair_preview_command:
        lines.append(f"- Optional safe repair preview command: `{safe_repair_preview_command}`")
    if safe_repair_command:
        lines.append(f"- Optional safe repair command: `{safe_repair_command}`")
    lines.extend(
        [
            "",
            "## Triage Summary",
            "",
            f"- First blocking issue: {format_issue_brief(sorted_issues[0]) if sorted_issues else 'none'}",
            "- Frequent issue codes: "
            + (
                ", ".join(f"{code}={count}" for code, count in code_summary)
                if code_summary
                else "none"
            ),
        ]
    )
    lines.extend(
        [
            "",
            "## Creation Roadmap",
            "",
            f"- Current target: {next_stage.get('title', '继续推进当前项目')}",
            f"- Headline: {roadmap.get('headline', '继续推进当前项目。')}",
            f"- Next gap: {primary_gap.get('missing') if primary_gap else 'none'}",
            f"- Suggested button: {primary_gap.get('action', {}).get('label') if primary_gap else 'none'}",
            "",
            "| Stage | Status | Progress | Primary gap | Suggested button |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for stage in roadmap_stages:
        if not isinstance(stage, dict):
            continue
        stage_gap = stage.get("primaryGap") if isinstance(stage.get("primaryGap"), dict) else None
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(stage.get("title", "")),
                    "done" if stage.get("done") else "next",
                    f"{stage.get('percent', 0)}%",
                    markdown_cell(stage_gap.get("missing") if stage_gap else "已达标"),
                    markdown_cell(stage_gap.get("action", {}).get("label") if stage_gap else "-"),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Project Snapshot",
            "",
            "| Metric | Value |",
            "| --- | --- |",
            f"| Chapters | {metrics.get('chapterCount', 0)} |",
            f"| Scenes | {metrics.get('sceneCount', 0)} |",
            f"| Story blocks | {metrics.get('blockCount', 0)} |",
            f"| Dialogue / narration blocks | {metrics.get('dialogueBlockCount', 0)} |",
            f"| Choice blocks | {metrics.get('choiceBlockCount', 0)} |",
            f"| Assets ready | {metrics.get('readyAssetCount', 0)} / {metrics.get('assetCount', 0)} |",
            f"| Asset references | {metrics.get('uniqueAssetReferenceCount', 0)} unique / {metrics.get('assetReferenceCount', 0)} total |",
            f"| Characters | {metrics.get('characterCount', 0)} |",
            f"| Variables | {metrics.get('variableCount', 0)} |",
            "",
            "## Suggested Next Actions",
            "",
        ]
    )
    lines.extend(f"- {action}" for action in next_actions)
    if repair_result:
        is_dry_run = bool(repair_result.get("dryRun"))
        lines.extend(
            [
                "",
                "## Safe Repair Preview" if is_dry_run else "## Safe Repair Result",
                "",
                f"- Changed: {repair_result.get('changed', False)}",
                f"- Would change: {repair_result.get('wouldChange', False)}",
                f"- Dry run: {is_dry_run}",
                f"- Repaired: {len(repair_result.get('repairs', []))}",
                f"- Skipped: {len(repair_result.get('skipped', []))}",
            ]
        )
        for repair in repair_result.get("repairs", []):
            lines.append(f"- {repair.get('title', '')}: {repair.get('detail', '')}")
    lines.extend(
        [
            "",
            "| Severity | Code | Title | Location | Detail | Recovery | Safe Repair |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for issue in report.get("issues", []):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(issue.get("severity", "")),
                    str(issue.get("code", "")),
                    str(issue.get("title", "")).replace("|", r"\|"),
                    str(issue.get("location", "")).replace("|", r"\|"),
                    str(issue.get("detail", "")).replace("|", r"\|"),
                    str(issue.get("recovery", "")).replace("|", r"\|"),
                    str(issue.get("repairCode", "")).replace("|", r"\|") or "-",
                ]
            )
            + " |"
        )
    if not report.get("issues"):
        lines.append("| info | clean | 没有发现问题 |  | 项目基础健康检查通过。 | 可以继续预览、导出或发布前检查。 | - |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_terminal_summary_lines(report: dict[str, Any], report_paths: Sequence[Path] = ()) -> list[str]:
    summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}
    metrics = report.get("metrics", {}) if isinstance(report.get("metrics"), dict) else {}
    roadmap = report.get("roadmap", {}) if isinstance(report.get("roadmap"), dict) else {}
    next_stage = roadmap.get("nextStage", {}) if isinstance(roadmap.get("nextStage"), dict) else {}
    primary_gap = next_stage.get("primaryGap") if isinstance(next_stage.get("primaryGap"), dict) else None
    status = str(summary.get("status", "unknown"))
    sorted_issues = get_sorted_issues(report)
    repair_code_counts = summary.get("autoFixableByRepairCode", {})
    repair_result = report.get("repairResult") if isinstance(report.get("repairResult"), dict) else None
    safe_repair_command = str(report.get("safeRepairCommand") or "").strip()
    safe_repair_preview_command = str(report.get("safeRepairPreviewCommand") or "").strip()
    lines = [
        "Canvasia Engine Project Health",
        f"Project: {report.get('projectDir', '')}",
        (
            f"Status: {status} ({get_status_label(status)}) | "
            f"errors {summary.get('errors', 0)} / warnings {summary.get('warnings', 0)} / "
            f"safe repairs {summary.get('autoFixableCount', 0)}"
        ),
        (
            "Project size: "
            f"{metrics.get('chapterCount', 0)} chapters / {metrics.get('sceneCount', 0)} scenes / "
            f"{metrics.get('blockCount', 0)} blocks | "
            f"assets {metrics.get('readyAssetCount', 0)}/{metrics.get('assetCount', 0)} ready"
        ),
        (
            "Roadmap: "
            f"{roadmap.get('completedCount', 0)}/{roadmap.get('totalCount', 0)} stages | "
            f"{roadmap.get('overallScore', 0)}% | next {next_stage.get('title', '继续推进当前项目')}"
        ),
    ]
    if primary_gap:
        lines.append(f"Roadmap next gap: {primary_gap.get('missing', '继续补齐当前阶段。')}")
        action_label = primary_gap.get("action", {}).get("label") if isinstance(primary_gap.get("action"), dict) else ""
        if action_label:
            lines.append(f"Roadmap next button: {action_label}")
    if isinstance(repair_code_counts, dict) and repair_code_counts:
        lines.append(
            "Safe repair groups: "
            + ", ".join(f"{repair_code}={count}" for repair_code, count in sorted(repair_code_counts.items()))
        )
    if safe_repair_preview_command:
        lines.append(f"Safe repair preview command: {safe_repair_preview_command}")
    if safe_repair_command:
        lines.append(f"Safe repair command: {safe_repair_command}")
    if repair_result:
        repairs = repair_result.get("repairs", []) if isinstance(repair_result.get("repairs"), list) else []
        skipped = repair_result.get("skipped", []) if isinstance(repair_result.get("skipped"), list) else []
        if repair_result.get("dryRun"):
            lines.append(f"Safe repair preview: would repair {len(repairs)} / skip {len(skipped)}")
        else:
            lines.append(f"Safe repair result: repaired {len(repairs)} / skipped {len(skipped)}")
        for repair in repairs[:5]:
            lines.append(f"  - {repair.get('title', '已安全修复')}")
    if sorted_issues:
        lines.append("First issues:")
        for issue in sorted_issues[:5]:
            lines.append(f"  - {format_issue_brief(issue)}")
    else:
        lines.append("First issues: none")
    lines.append("Next actions:")
    for action in build_next_actions(report):
        lines.append(f"  - {action}")
    if report_paths:
        lines.append("Reports:")
        for path in report_paths:
            lines.append(f"  - {path}")
    return lines


def print_terminal_summary(report: dict[str, Any], report_paths: Sequence[Path] = ()) -> None:
    for line in build_terminal_summary_lines(report, report_paths):
        print(line)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check a Canvasia Engine project for beginner-facing health issues.")
    parser.add_argument("project_dir", type=Path, help="Project directory to check, for example template_project.")
    parser.add_argument("--json-report", type=Path, help="Write a machine-readable JSON report.")
    parser.add_argument("--markdown-report", type=Path, help="Write a human-readable Markdown report.")
    parser.add_argument(
        "--repair-safe",
        action="store_true",
        help="Apply opt-in low-risk repairs for entry scene, chapter order, and scene order before writing reports.",
    )
    parser.add_argument(
        "--repair-codes",
        help="Comma- or space-separated safe repair codes to apply with --repair-safe. Defaults to the current auto-fixable groups.",
    )
    parser.add_argument(
        "--repair-dry-run",
        action="store_true",
        help="Preview the selected --repair-safe changes without writing project files.",
    )
    args = parser.parse_args(argv)
    if args.repair_codes and not args.repair_safe:
        parser.error("--repair-codes requires --repair-safe so the tool never writes files by accident.")
    if args.repair_dry_run and not args.repair_safe:
        parser.error("--repair-dry-run requires --repair-safe so the preview always uses explicit safe repair mode.")
    if args.repair_safe and args.repair_codes:
        unknown_codes = get_unknown_safe_repair_codes(args.repair_codes)
        if unknown_codes:
            parser.error(
                "--repair-codes contains unknown code(s): "
                + ", ".join(unknown_codes)
                + f". Available: {SAFE_REPAIR_CODE_LABEL}."
            )
        if not normalize_safe_repair_codes(args.repair_codes):
            parser.error(f"--repair-codes must include at least one of: {SAFE_REPAIR_CODE_LABEL}.")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    report = analyze_project(args.project_dir)
    if args.repair_safe:
        repair_result = repair_safe_project_issues(
            args.project_dir,
            args.repair_codes,
            report,
            dry_run=args.repair_dry_run,
        )
        if not args.repair_dry_run:
            report = analyze_project(args.project_dir)
        report["repairResult"] = repair_result
    if args.json_report:
        write_json_report(args.json_report, report)
    if args.markdown_report:
        write_markdown_report(args.markdown_report, report)
    report_paths = [path for path in [args.json_report, args.markdown_report] if path]
    summary = report["summary"]
    print_terminal_summary(report, report_paths)
    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
