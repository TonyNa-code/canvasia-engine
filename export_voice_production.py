from __future__ import annotations

import csv
import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path


EXPORT_VOICE_PRODUCTION_JSON_NAME = "voice-production-sheet.json"
EXPORT_VOICE_PRODUCTION_REPORT_NAME = "voice-production-report.md"
EXPORT_VOICE_PRODUCTION_CSV_NAME = "voice-production-lines.csv"
VOICE_PRODUCTION_FORMAT_VERSION = 1
LONG_VOICE_LINE_LENGTH = 90
VERY_LONG_VOICE_LINE_LENGTH = 140

STATUS_LABELS = {
    "ready": "已配音",
    "missing_voice": "待配音",
    "missing_asset": "语音条目缺失",
    "missing_file": "语音文件缺失",
    "wrong_type": "素材类型不对",
    "unknown_speaker": "说话人待确认",
}
ISSUE_WEIGHT = {"blocker": 100, "warn": 60, "tip": 20}
FILE_COMPONENT_UNSAFE_RE = re.compile(r"[\\/:*?\"<>|\s]+")


def clean_text(value: object, fallback: str = "") -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text or fallback


def as_list(value: object) -> list:
    return value if isinstance(value, list) else []


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


def get_assets_by_id(assets_doc: dict) -> dict[str, dict]:
    assets = assets_doc.get("assets") if isinstance(assets_doc, dict) else []
    return {
        clean_text(asset.get("id")): asset
        for asset in as_list(assets)
        if isinstance(asset, dict) and clean_text(asset.get("id"))
    }


def get_characters_by_id(bundle: dict) -> dict[str, dict]:
    characters_doc = bundle.get("characters") if isinstance(bundle.get("characters"), dict) else {}
    characters = characters_doc.get("characters") if isinstance(characters_doc, dict) else []
    return {
        clean_text(character.get("id")): character
        for character in as_list(characters)
        if isinstance(character, dict) and clean_text(character.get("id"))
    }


def get_character_name(characters_by_id: dict[str, dict], speaker_id: str) -> str:
    if not speaker_id:
        return "未指定说话人"
    character = characters_by_id.get(speaker_id)
    if not isinstance(character, dict):
        return speaker_id
    return clean_text(character.get("displayName") or character.get("name"), speaker_id)


def get_asset_name(asset: dict | None, fallback: str = "") -> str:
    if not isinstance(asset, dict):
        return fallback
    return clean_text(asset.get("name") or asset.get("fileName") or asset.get("path"), fallback)


def get_asset_path(asset: dict | None) -> str:
    if not isinstance(asset, dict):
        return ""
    return clean_text(asset.get("exportUrl") or asset.get("path") or asset.get("url"))


def asset_file_exists(asset: dict | None) -> bool:
    if not isinstance(asset, dict):
        return False
    if asset.get("isMissing") is True or asset.get("fileExists") is False:
        return False
    return True


def get_voice_line_status(block: dict, characters_by_id: dict[str, dict], assets_by_id: dict[str, dict]) -> str:
    speaker_id = clean_text(block.get("speakerId") or block.get("speaker"))
    voice = block.get("voice") if isinstance(block.get("voice"), dict) else {}
    voice_asset_id = clean_text(block.get("voiceAssetId") or voice.get("assetId"))
    asset = assets_by_id.get(voice_asset_id) if voice_asset_id else None

    if voice_asset_id and not asset:
        return "missing_asset"
    if asset and clean_text(asset.get("type")) and clean_text(asset.get("type")) != "voice":
        return "wrong_type"
    if asset and not asset_file_exists(asset):
        return "missing_file"
    if not voice_asset_id:
        return "missing_voice"
    if not speaker_id or speaker_id not in characters_by_id:
        return "unknown_speaker"
    return "ready"


def push_issue(issues: list[dict], severity: str, code: str, title: str, detail: str, line: dict) -> None:
    issues.append(
        {
            "severity": severity,
            "code": code,
            "title": title,
            "detail": detail,
            "lineId": line["lineId"],
            "blockId": line["blockId"],
            "chapterName": line["chapterName"],
            "sceneName": line["sceneName"],
            "speakerName": line["speakerName"],
            "lineNumber": line["lineNumber"],
        }
    )


def create_line_issues(line: dict, characters_by_id: dict[str, dict], assets_by_id: dict[str, dict]) -> list[dict]:
    issues: list[dict] = []
    if not line["speakerId"] or line["speakerId"] not in characters_by_id:
        push_issue(
            issues,
            "warn",
            "voice_unknown_speaker",
            "说话人没有对应角色",
            f"说话人 {line['speakerId'] or '未指定'} 不在角色表中，后续分配声优会不清楚。",
            line,
        )
    if not line["text"]:
        push_issue(issues, "warn", "voice_empty_text", "台词为空", "这张台词卡没有正文，建议补齐或删除。", line)

    if not line["voiceAssetId"]:
        push_issue(issues, "warn", "voice_missing_binding", "台词还没绑定语音", "需要先创建语音占位或绑定已有语音素材。", line)
    else:
        asset = assets_by_id.get(line["voiceAssetId"])
        if not asset:
            push_issue(
                issues,
                "blocker",
                "voice_missing_asset",
                "绑定的语音条目不存在",
                f"语音条目 {line['voiceAssetId']} 不在素材库中，导出后会播放失败。",
                line,
            )
        elif clean_text(asset.get("type")) and clean_text(asset.get("type")) != "voice":
            push_issue(
                issues,
                "blocker",
                "voice_wrong_asset_type",
                "绑定的素材不是语音",
                f"当前绑定的是 {clean_text(asset.get('type'))} 类型素材，请改成语音素材。",
                line,
            )
        elif not asset_file_exists(asset):
            push_issue(
                issues,
                "blocker",
                "voice_missing_file",
                "语音条目还没有真实文件",
                f"语音条目“{get_asset_name(asset, line['voiceAssetId'])}”存在，但文件还没有上传或已经丢失。",
                line,
            )

    if line["textLength"] > VERY_LONG_VOICE_LINE_LENGTH:
        push_issue(
            issues,
            "warn",
            "voice_line_very_long",
            "台词过长，建议拆句",
            f"这句有 {line['textLength']} 字，录音、字幕和打字机节奏都容易拖。",
            line,
        )
    elif line["textLength"] > LONG_VOICE_LINE_LENGTH:
        push_issue(issues, "tip", "voice_line_long", "台词偏长", f"这句有 {line['textLength']} 字，可以视演出节奏拆成两句。", line)
    return issues


def safe_file_component(value: object, fallback: str) -> str:
    text = clean_text(value, fallback)
    text = FILE_COMPONENT_UNSAFE_RE.sub("_", text).strip("._-")
    return (text or fallback)[:36]


def build_suggested_recording_name(line: dict) -> str:
    speaker = safe_file_component(line.get("speakerName"), "voice")
    chapter = safe_file_component(line.get("chapterName"), "chapter")
    scene = safe_file_component(line.get("sceneName"), "scene")
    return f"{speaker}_{chapter}_{scene}_{int(line.get('lineNumber') or 0):03d}.wav"


def build_speaker_summary(lines: list[dict]) -> list[dict]:
    speakers: dict[str, dict] = {}
    for line in lines:
        speaker_key = line["speakerId"] or "__unknown__"
        record = speakers.setdefault(
            speaker_key,
            {
                "speakerId": line["speakerId"],
                "speakerName": line["speakerName"],
                "totalLines": 0,
                "readyLines": 0,
                "missingLines": 0,
                "blockerLines": 0,
                "longLines": 0,
                "totalCharacters": 0,
                "readyPercent": 0,
            },
        )
        record["totalLines"] += 1
        record["totalCharacters"] += line["textLength"]
        if line["status"] == "ready":
            record["readyLines"] += 1
        else:
            record["missingLines"] += 1
        if line["status"] in {"missing_asset", "missing_file", "wrong_type"}:
            record["blockerLines"] += 1
        if line["isLong"]:
            record["longLines"] += 1
        record["readyPercent"] = round(record["readyLines"] / record["totalLines"] * 100) if record["totalLines"] else 100
    return sorted(
        speakers.values(),
        key=lambda item: (-item["blockerLines"], -item["missingLines"], -item["totalLines"], item["speakerName"]),
    )


def get_voice_production_status_digest(sheet: dict) -> dict:
    summary = sheet.get("summary") or {}
    if not summary.get("lineCount"):
        return {
            "status": "empty",
            "title": "还没有可配音台词",
            "detail": "项目里暂时没有角色台词。添加第一句台词后，这里会生成配音制作清单。",
        }
    if summary.get("blockerCount", 0) > 0:
        return {
            "status": "blocked",
            "title": f"{summary.get('blockerCount', 0)} 个语音阻塞项",
            "detail": "优先处理不存在的语音条目、缺失文件和类型错误，否则导出试玩时可能没有声音。",
        }
    if summary.get("missingVoiceCount", 0) > 0 or summary.get("unknownSpeakerCount", 0) > 0:
        return {
            "status": "warn",
            "title": f"{summary.get('readyPercent', 0)}% 台词已就绪",
            "detail": "语音流程可以推进，但仍有台词待建占位或说话人需要确认。",
        }
    if summary.get("longLineCount", 0) > 0:
        return {
            "status": "warn",
            "title": "语音已齐，建议复查长句",
            "detail": "全部台词已经绑定语音，但仍有长句可以按录音节奏拆分。",
        }
    return {
        "status": "ready",
        "title": "语音生产状态稳定",
        "detail": "台词语音绑定、文件和角色分配都比较完整，可以进入试听和发布前确认。",
    }


def build_voice_production_sheet(bundle: dict, assets_doc: dict) -> dict:
    assets_by_id = get_assets_by_id(assets_doc)
    characters_by_id = get_characters_by_id(bundle)
    lines: list[dict] = []
    issues: list[dict] = []

    for record in get_ordered_scene_records(bundle):
        scene = record["scene"]
        for block_index, block in enumerate(as_list(scene.get("blocks"))):
            if not isinstance(block, dict) or clean_text(block.get("type")) != "dialogue":
                continue
            voice = block.get("voice") if isinstance(block.get("voice"), dict) else {}
            speaker_id = clean_text(block.get("speakerId") or block.get("speaker"))
            voice_asset_id = clean_text(block.get("voiceAssetId") or voice.get("assetId"))
            voice_asset = assets_by_id.get(voice_asset_id) if voice_asset_id else None
            text = clean_text(block.get("text"))
            line_number = len(lines) + 1
            line = {
                "lineId": f"{record['sceneId']}:{clean_text(block.get('id'), str(block_index))}",
                "blockId": clean_text(block.get("id")),
                "blockIndex": block_index,
                "lineNumber": line_number,
                "chapterId": record["chapterId"],
                "chapterName": record["chapterName"],
                "sceneId": record["sceneId"],
                "sceneName": record["sceneName"],
                "speakerId": speaker_id,
                "speakerName": get_character_name(characters_by_id, speaker_id),
                "text": text,
                "textPreview": text[:72] + ("..." if len(text) > 72 else ""),
                "textLength": len(text),
                "voiceAssetId": voice_asset_id,
                "voiceAssetName": get_asset_name(voice_asset, voice_asset_id),
                "voiceAssetPath": get_asset_path(voice_asset),
                "voiceFileExists": asset_file_exists(voice_asset),
                "status": get_voice_line_status(block, characters_by_id, assets_by_id),
                "statusLabel": "",
                "suggestedRecordingFileName": "",
                "isLong": len(text) > LONG_VOICE_LINE_LENGTH,
                "isVeryLong": len(text) > VERY_LONG_VOICE_LINE_LENGTH,
                "issueSummary": "",
            }
            line["statusLabel"] = STATUS_LABELS.get(line["status"], line["status"])
            line["suggestedRecordingFileName"] = build_suggested_recording_name(line)
            line_issues = create_line_issues(line, characters_by_id, assets_by_id)
            line["issueSummary"] = " / ".join(issue["title"] for issue in line_issues) or "OK"
            lines.append(line)
            issues.extend(line_issues)

    issues.sort(key=lambda issue: (-ISSUE_WEIGHT.get(issue["severity"], 0), issue["lineNumber"], issue["title"]))
    speakers = build_speaker_summary(lines)
    blocker_count = sum(1 for issue in issues if issue["severity"] == "blocker")
    warning_count = sum(1 for issue in issues if issue["severity"] == "warn")
    tip_count = sum(1 for issue in issues if issue["severity"] == "tip")
    ready_line_count = sum(1 for line in lines if line["status"] == "ready")
    summary = {
        "lineCount": len(lines),
        "readyLineCount": ready_line_count,
        "missingVoiceCount": sum(1 for line in lines if line["status"] == "missing_voice"),
        "missingAssetCount": sum(1 for line in lines if line["status"] == "missing_asset"),
        "missingFileCount": sum(1 for line in lines if line["status"] == "missing_file"),
        "wrongTypeCount": sum(1 for line in lines if line["status"] == "wrong_type"),
        "unknownSpeakerCount": sum(1 for issue in issues if issue["code"] == "voice_unknown_speaker"),
        "longLineCount": sum(1 for line in lines if line["isLong"]),
        "veryLongLineCount": sum(1 for line in lines if line["isVeryLong"]),
        "speakerCount": len(speakers),
        "blockerCount": blocker_count,
        "warningCount": warning_count,
        "tipCount": tip_count,
        "readyPercent": round(ready_line_count / len(lines) * 100) if lines else 100,
    }
    sheet = {
        "formatVersion": VOICE_PRODUCTION_FORMAT_VERSION,
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "projectTitle": get_project_title(bundle),
        "summary": summary,
        "speakers": speakers,
        "lines": lines,
        "issues": issues,
    }
    sheet["statusDigest"] = get_voice_production_status_digest(sheet)
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


def build_voice_production_report(sheet: dict) -> str:
    summary = sheet.get("summary") or {}
    digest = sheet.get("statusDigest") or get_voice_production_status_digest(sheet)
    speaker_rows = [
        [
            speaker.get("speakerName"),
            speaker.get("totalLines"),
            speaker.get("readyLines"),
            speaker.get("missingLines"),
            speaker.get("blockerLines"),
            speaker.get("longLines"),
            f"{speaker.get('readyPercent', 0)}%",
            speaker.get("totalCharacters"),
        ]
        for speaker in sheet.get("speakers") or []
    ]
    line_rows = [
        [
            line.get("lineNumber"),
            line.get("statusLabel"),
            line.get("chapterName"),
            line.get("sceneName"),
            line.get("speakerName"),
            line.get("textPreview"),
            line.get("suggestedRecordingFileName"),
            line.get("voiceAssetName") or line.get("voiceAssetId") or "未绑定",
            line.get("issueSummary"),
        ]
        for line in (sheet.get("lines") or [])[:160]
    ]
    issue_rows = [
        [
            index + 1,
            "先修" if issue.get("severity") == "blocker" else "复查" if issue.get("severity") == "warn" else "润色",
            issue.get("chapterName"),
            issue.get("sceneName"),
            issue.get("speakerName"),
            issue.get("title"),
            issue.get("detail"),
        ]
        for index, issue in enumerate((sheet.get("issues") or [])[:80])
    ]
    return "\n".join(
        [
            f"# {sheet.get('projectTitle') or 'Canvasia Project'} 语音制作清单",
            "",
            f"- 生成时间：{sheet.get('generatedAt')}",
            f"- 状态：{digest.get('title')}",
            f"- 说明：{digest.get('detail')}",
            "",
            "## 总览",
            "",
            markdown_table(
                ["台词", "已配音", "待配音", "缺条目", "缺文件/类型", "说话人待确认", "长句", "完成度"],
                [
                    [
                        summary.get("lineCount", 0),
                        summary.get("readyLineCount", 0),
                        summary.get("missingVoiceCount", 0),
                        summary.get("missingAssetCount", 0),
                        summary.get("missingFileCount", 0) + summary.get("wrongTypeCount", 0),
                        summary.get("unknownSpeakerCount", 0),
                        summary.get("longLineCount", 0),
                        f"{summary.get('readyPercent', 0)}%",
                    ]
                ],
            ),
            "",
            "## 角色配音进度",
            "",
            markdown_table(["角色", "台词", "已就绪", "待处理", "阻塞项", "长句", "完成度", "字数"], speaker_rows)
            or "当前还没有可统计的角色台词。",
            "",
            "## 台词录音表",
            "",
            markdown_table(["序号", "状态", "章节", "场景", "角色", "台词", "建议录音文件名", "当前语音素材", "问题"], line_rows)
            or "当前没有台词。",
            "",
            "## 优先问题",
            "",
            markdown_table(["序号", "级别", "章节", "场景", "角色", "问题", "说明"], issue_rows) or "当前没有明显语音生产问题。",
            "",
            "## 交付建议",
            "",
            "- 配音文件建议先按“建议录音文件名”命名，导入素材库后再批量匹配到语音占位。",
            "- 进入正式录音前，优先处理“先修”和“复查”项，避免返工。",
            "- 长句可以按自然停顿拆成多张台词卡，打字机节奏和语音回听都会更稳。",
            "",
        ]
    )


def build_voice_production_csv(sheet: dict) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "lineNumber",
            "status",
            "chapter",
            "scene",
            "blockIndex",
            "speaker",
            "text",
            "textLength",
            "suggestedRecordingFileName",
            "voiceAssetId",
            "voiceAssetName",
            "voiceAssetPath",
            "fileStatus",
            "issues",
        ]
    )
    for line in sheet.get("lines") or []:
        writer.writerow(
            [
                line.get("lineNumber"),
                line.get("statusLabel"),
                line.get("chapterName"),
                line.get("sceneName"),
                int(line.get("blockIndex") or 0) + 1,
                line.get("speakerName"),
                line.get("text"),
                line.get("textLength"),
                line.get("suggestedRecordingFileName"),
                line.get("voiceAssetId"),
                line.get("voiceAssetName"),
                line.get("voiceAssetPath"),
                "有文件" if line.get("voiceFileExists") else "缺文件",
                line.get("issueSummary"),
            ]
        )
    return "\ufeff" + output.getvalue()


def write_export_voice_production_files(target_dir: Path, *, bundle: dict, assets_doc: dict) -> dict:
    sheet = build_voice_production_sheet(bundle, assets_doc)
    json_path = target_dir / EXPORT_VOICE_PRODUCTION_JSON_NAME
    report_path = target_dir / EXPORT_VOICE_PRODUCTION_REPORT_NAME
    csv_path = target_dir / EXPORT_VOICE_PRODUCTION_CSV_NAME
    json_path.write_text(json.dumps(sheet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(build_voice_production_report(sheet), encoding="utf-8")
    csv_path.write_text(build_voice_production_csv(sheet), encoding="utf-8")
    summary = sheet["summary"]
    return {
        "voiceProductionSheet": sheet,
        "voiceProductionName": json_path.name,
        "voiceProductionPath": str(json_path),
        "voiceProductionReportName": report_path.name,
        "voiceProductionReportPath": str(report_path),
        "voiceProductionCsvName": csv_path.name,
        "voiceProductionCsvPath": str(csv_path),
        "voiceProductionReadyPercent": summary["readyPercent"],
        "voiceProductionLineCount": summary["lineCount"],
        "voiceProductionBlockerCount": summary["blockerCount"],
        "voiceProductionWarningCount": summary["warningCount"],
    }


__all__ = [
    "EXPORT_VOICE_PRODUCTION_JSON_NAME",
    "EXPORT_VOICE_PRODUCTION_REPORT_NAME",
    "EXPORT_VOICE_PRODUCTION_CSV_NAME",
    "LONG_VOICE_LINE_LENGTH",
    "VERY_LONG_VOICE_LINE_LENGTH",
    "build_voice_production_sheet",
    "build_voice_production_report",
    "build_voice_production_csv",
    "write_export_voice_production_files",
]
