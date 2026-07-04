from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path


EXPORT_LOCALIZATION_AUDIT_JSON_NAME = "localization_audit.json"
EXPORT_LOCALIZATION_AUDIT_REPORT_NAME = "localization_audit.md"
DEFAULT_LOCALIZATION_LANGUAGE = "zh-CN"
LANGUAGE_LABELS = {
    "zh-CN": "简体中文",
    "zh-TW": "繁体中文",
    "ja-JP": "日本語",
    "en-US": "English",
    "en-GB": "English",
    "ko-KR": "한국어",
}


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def clean_localization_text(value: object, fallback: str = "") -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text or fallback


def truncate_localization_text(value: object, max_length: int = 72) -> str:
    text = clean_localization_text(value)
    safe_max = max(12, int(max_length or 72))
    return text if len(text) <= safe_max else text[: safe_max - 1].rstrip() + "..."


def markdown_cell(value: object) -> str:
    return clean_localization_text(value, "-").replace("|", "\\|")


def normalize_language_code(value: object, fallback: str = DEFAULT_LOCALIZATION_LANGUAGE) -> str:
    raw_value = str(value or "").strip().replace("_", "-")
    if not raw_value:
        return fallback
    if not re.fullmatch(r"[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8}){0,2}", raw_value):
        return fallback
    parts = raw_value.split("-")
    normalized_parts = [parts[0].lower()]
    for index, part in enumerate(parts[1:], start=1):
        normalized_parts.append(part.upper() if index == 1 and len(part) in {2, 3} else part)
    return "-".join(normalized_parts)


def normalize_supported_languages(value: object, default_language: str) -> list[str]:
    languages: list[str] = []
    for raw_language in value if isinstance(value, list) else []:
        language = normalize_language_code(raw_language, "")
        if language and language not in languages:
            languages.append(language)
    if default_language and default_language not in languages:
        languages.insert(0, default_language)
    return languages or [default_language or DEFAULT_LOCALIZATION_LANGUAGE]


def language_label(language: str) -> str:
    return LANGUAGE_LABELS.get(language, language)


def get_translation(source: dict, key: str, language: str) -> str:
    translations = source.get(f"{key}Translations")
    if not isinstance(translations, dict):
        return ""
    return clean_localization_text(translations.get(language))


def make_localization_item(
    *,
    kind: str,
    key: str,
    source_text: object,
    missing_languages: list[str],
    chapter: dict | None = None,
    scene: dict | None = None,
    block: dict | None = None,
    chapter_index: int | None = None,
    scene_index: int | None = None,
    block_index: int | None = None,
    option_index: int | None = None,
) -> dict:
    chapter = chapter or {}
    scene = scene or {}
    block = block or {}
    chapter_id = clean_localization_text(chapter.get("id") or chapter.get("chapterId"), f"chapter_{(chapter_index or 0) + 1}")
    scene_id = clean_localization_text(scene.get("id"), f"scene_{(scene_index or 0) + 1}")
    block_id = clean_localization_text(block.get("id"), f"block_{(block_index or 0) + 1}")
    item_id_parts = [kind, key, chapter_id]
    if scene:
        item_id_parts.append(scene_id)
    if block:
        item_id_parts.append(block_id)
    if option_index is not None:
        item_id_parts.append(f"option_{option_index + 1}")
    return {
        "id": "::".join(item_id_parts),
        "kind": kind,
        "key": key,
        "sourceText": truncate_localization_text(source_text, 160),
        "missingLanguages": missing_languages,
        "chapterId": chapter_id,
        "chapterName": clean_localization_text(chapter.get("name") or chapter.get("title"), chapter_id),
        "chapterIndex": chapter_index,
        "sceneId": scene_id if scene else "",
        "sceneName": clean_localization_text(scene.get("name") or scene.get("title"), scene_id) if scene else "",
        "sceneIndex": scene_index,
        "blockId": block_id if block else "",
        "blockType": clean_localization_text(block.get("type"), "unknown") if block else "",
        "blockIndex": block_index,
        "optionIndex": option_index,
    }


def collect_translation_requirement(
    items: list[dict],
    *,
    source: dict,
    kind: str,
    key: str,
    target_languages: list[str],
    chapter: dict | None = None,
    scene: dict | None = None,
    block: dict | None = None,
    chapter_index: int | None = None,
    scene_index: int | None = None,
    block_index: int | None = None,
    option_index: int | None = None,
) -> tuple[int, int]:
    source_text = clean_localization_text(source.get(key))
    if not source_text:
        return (0, 0)
    required_count = len(target_languages)
    missing_languages = [language for language in target_languages if not get_translation(source, key, language)]
    if missing_languages:
        items.append(
            make_localization_item(
                kind=kind,
                key=key,
                source_text=source_text,
                missing_languages=missing_languages,
                chapter=chapter,
                scene=scene,
                block=block,
                chapter_index=chapter_index,
                scene_index=scene_index,
                block_index=block_index,
                option_index=option_index,
            )
        )
    return (required_count, len(missing_languages))


def iter_chapters(bundle: dict) -> list[dict]:
    chapters = bundle.get("chapters")
    return [chapter for chapter in chapters if isinstance(chapter, dict)] if isinstance(chapters, list) else []


def iter_character_records(bundle: dict) -> list[dict]:
    characters = bundle.get("characters")
    if isinstance(characters, list):
        return [character for character in characters if isinstance(character, dict)]
    if isinstance(characters, dict):
        return [character for character in characters.values() if isinstance(character, dict)]
    return []


def build_export_localization_audit(bundle: dict) -> dict:
    project = bundle.get("project") if isinstance(bundle.get("project"), dict) else {}
    default_language = normalize_language_code(project.get("language"), DEFAULT_LOCALIZATION_LANGUAGE)
    supported_languages = normalize_supported_languages(project.get("supportedLanguages"), default_language)
    target_languages = [language for language in supported_languages if language != default_language]
    missing_items: list[dict] = []
    checked_text_count = 0
    required_translation_count = 0
    missing_translation_count = 0

    def collect(**kwargs: object) -> None:
        nonlocal checked_text_count, required_translation_count, missing_translation_count
        required_count, missing_count = collect_translation_requirement(
            missing_items,
            target_languages=target_languages,
            **kwargs,
        )
        if required_count:
            checked_text_count += 1
            required_translation_count += required_count
            missing_translation_count += missing_count

    collect(source=project, kind="project_title", key="title")

    for character_index, character in enumerate(iter_character_records(bundle)):
        character_id = clean_localization_text(character.get("id") or character.get("name"), f"character_{character_index + 1}")
        pseudo_chapter = {
            "id": "characters",
            "name": "角色资料",
        }
        pseudo_scene = {
            "id": character_id,
            "name": clean_localization_text(character.get("displayName") or character.get("name"), character_id),
        }
        collect(
            source=character,
            kind="character_name",
            key="displayName" if clean_localization_text(character.get("displayName")) else "name",
            chapter=pseudo_chapter,
            scene=pseudo_scene,
            chapter_index=-1,
            scene_index=character_index,
        )

    for chapter_index, chapter in enumerate(iter_chapters(bundle)):
        collect(source=chapter, kind="chapter_name", key="name", chapter=chapter, chapter_index=chapter_index)
        scenes = chapter.get("scenes") if isinstance(chapter.get("scenes"), list) else []
        for scene_index, scene in enumerate(scenes):
            if not isinstance(scene, dict):
                continue
            scene_key = "name" if clean_localization_text(scene.get("name")) else "title"
            collect(
                source=scene,
                kind="scene_name",
                key=scene_key,
                chapter=chapter,
                scene=scene,
                chapter_index=chapter_index,
                scene_index=scene_index,
            )
            blocks = scene.get("blocks") if isinstance(scene.get("blocks"), list) else []
            for block_index, block in enumerate(blocks):
                if not isinstance(block, dict):
                    continue
                for key in ("title", "text", "content"):
                    collect(
                        source=block,
                        kind="block_text",
                        key=key,
                        chapter=chapter,
                        scene=scene,
                        block=block,
                        chapter_index=chapter_index,
                        scene_index=scene_index,
                        block_index=block_index,
                    )
                for option_index, option in enumerate(block.get("options") if isinstance(block.get("options"), list) else []):
                    if not isinstance(option, dict):
                        continue
                    collect(
                        source=option,
                        kind="choice_option",
                        key="text",
                        chapter=chapter,
                        scene=scene,
                        block=block,
                        chapter_index=chapter_index,
                        scene_index=scene_index,
                        block_index=block_index,
                        option_index=option_index,
                    )

    present_translation_count = max(0, required_translation_count - missing_translation_count)
    completion_percent = (
        100
        if required_translation_count <= 0
        else round((present_translation_count / required_translation_count) * 100)
    )
    if len(supported_languages) <= 1:
        status = "single_language"
    elif missing_translation_count:
        status = "needs_translation"
    else:
        status = "ready"

    return {
        "formatVersion": 1,
        "generatedAt": now_iso(),
        "project": {
            "projectId": clean_localization_text(project.get("projectId")),
            "title": clean_localization_text(project.get("title"), "未命名项目"),
            "defaultLanguage": default_language,
            "supportedLanguages": supported_languages,
            "targetLanguages": target_languages,
        },
        "summary": {
            "status": status,
            "languageCount": len(supported_languages),
            "targetLanguageCount": len(target_languages),
            "checkedTextCount": checked_text_count,
            "requiredTranslationCount": required_translation_count,
            "presentTranslationCount": present_translation_count,
            "missingTranslationCount": missing_translation_count,
            "incompleteItemCount": len(missing_items),
            "completionPercent": completion_percent,
        },
        "missingItems": missing_items,
    }


def build_export_localization_audit_markdown(audit: dict) -> str:
    project = audit.get("project") if isinstance(audit.get("project"), dict) else {}
    summary = audit.get("summary") if isinstance(audit.get("summary"), dict) else {}
    missing_items = audit.get("missingItems") if isinstance(audit.get("missingItems"), list) else []
    supported_languages = project.get("supportedLanguages") if isinstance(project.get("supportedLanguages"), list) else []
    target_languages = project.get("targetLanguages") if isinstance(project.get("targetLanguages"), list) else []
    status_labels = {
        "ready": "多语言覆盖完整",
        "needs_translation": "需要补译",
        "single_language": "单语言项目",
    }
    lines = [
        "# 本地化覆盖随包报告",
        "",
        f"- 项目：{markdown_cell(project.get('title'))}",
        f"- 默认语言：{markdown_cell(project.get('defaultLanguage'))}",
        f"- 支持语言：{markdown_cell('、'.join(f'{language_label(language)} ({language})' for language in supported_languages))}",
        f"- 结论：{markdown_cell(status_labels.get(clean_localization_text(summary.get('status')), summary.get('status')))}",
        f"- 覆盖率：{markdown_cell(summary.get('completionPercent'))}%",
        "",
        "## 核心指标",
        "",
        "| 指标 | 数值 |",
        "| --- | ---: |",
        f"| 需补齐语言 | {markdown_cell('、'.join(target_languages) if target_languages else '无')} |",
        f"| 检查文本项 | {markdown_cell(summary.get('checkedTextCount'))} |",
        f"| 应有译文数 | {markdown_cell(summary.get('requiredTranslationCount'))} |",
        f"| 已有译文数 | {markdown_cell(summary.get('presentTranslationCount'))} |",
        f"| 缺失译文数 | {markdown_cell(summary.get('missingTranslationCount'))} |",
        f"| 未完成文本项 | {markdown_cell(summary.get('incompleteItemCount'))} |",
        "",
        "## 优先补译",
        "",
    ]
    if missing_items:
        lines.extend(["| 位置 | 类型 | 原文 | 缺失语言 |", "| --- | --- | --- | --- |"])
        for item in missing_items[:80]:
            location_parts = [
                clean_localization_text(item.get("chapterName")),
                clean_localization_text(item.get("sceneName")),
            ]
            if item.get("blockIndex") is not None:
                location_parts.append(f"卡片 {int(item.get('blockIndex') or 0) + 1}")
            if item.get("optionIndex") is not None:
                location_parts.append(f"选项 {int(item.get('optionIndex') or 0) + 1}")
            lines.append(
                "| "
                + " | ".join(
                    [
                        markdown_cell(" / ".join(part for part in location_parts if part)),
                        markdown_cell(item.get("kind")),
                        markdown_cell(truncate_localization_text(item.get("sourceText"), 60)),
                        markdown_cell("、".join(item.get("missingLanguages") or [])),
                    ]
                )
                + " |"
            )
        if len(missing_items) > 80:
            lines.append(f"| 其余条目 | - | 还有 {len(missing_items) - 80} 项，请查看 JSON | - |")
    else:
        lines.append("- 暂未发现缺失译文。")

    lines.extend(
        [
            "",
            "## 使用建议",
            "",
            "- 如果只是面向单一语言玩家，保持单语言即可。",
            "- 如果 README 或商店页宣称支持多语言，发布前建议把本报告里的缺失项补齐。",
            "- 大型项目可先补主线正文、选项和角色名，再补章节 / 场景标题。",
            "",
        ]
    )
    return "\n".join(lines)


def write_export_localization_audit_files(target_dir: Path, bundle: dict) -> dict:
    audit = build_export_localization_audit(bundle)
    json_path = target_dir / EXPORT_LOCALIZATION_AUDIT_JSON_NAME
    markdown_path = target_dir / EXPORT_LOCALIZATION_AUDIT_REPORT_NAME
    json_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(build_export_localization_audit_markdown(audit), encoding="utf-8")
    summary = audit["summary"]
    return {
        "localizationAuditName": json_path.name,
        "localizationAuditPath": str(json_path),
        "localizationAuditReportName": markdown_path.name,
        "localizationAuditReportPath": str(markdown_path),
        "localizationAuditStatus": summary["status"],
        "localizationAuditCompletionPercent": summary["completionPercent"],
        "localizationAudit": audit,
    }


__all__ = [
    "EXPORT_LOCALIZATION_AUDIT_JSON_NAME",
    "EXPORT_LOCALIZATION_AUDIT_REPORT_NAME",
    "build_export_localization_audit",
    "build_export_localization_audit_markdown",
    "write_export_localization_audit_files",
]
