from __future__ import annotations

import copy
import hashlib
import json
import re
from collections import Counter


TEXT_REFACTOR_SCOPE_LABELS = {
    "dialogue": "角色台词",
    "narration": "旁白",
    "choice": "选项文案",
    "input": "玩家输入提示",
    "scene_name": "场景名",
    "chapter_name": "章节名",
}
DEFAULT_TEXT_REFACTOR_SCOPES = ("dialogue", "narration", "choice")
MAX_TEXT_REFACTOR_FIND_LENGTH = 240
MAX_TEXT_REFACTOR_REPLACEMENT_LENGTH = 2000
MAX_TEXT_REFACTOR_REPLACEMENTS = 20000
DEFAULT_TEXT_REFACTOR_PREVIEW_LIMIT = 160


def normalize_project_text_refactor_request(payload: object) -> dict:
    source = payload if isinstance(payload, dict) else {}
    find_text = str(source.get("findText") or "")
    replace_text = str(source.get("replaceText") or "")
    if not find_text or not find_text.strip():
        raise ValueError("先填写要查找的文字。")
    if len(find_text) > MAX_TEXT_REFACTOR_FIND_LENGTH:
        raise ValueError(f"查找文字不能超过 {MAX_TEXT_REFACTOR_FIND_LENGTH} 个字符。")
    if len(replace_text) > MAX_TEXT_REFACTOR_REPLACEMENT_LENGTH:
        raise ValueError(f"替换文字不能超过 {MAX_TEXT_REFACTOR_REPLACEMENT_LENGTH} 个字符。")

    case_sensitive = bool(source.get("caseSensitive", True))
    same_text = find_text == replace_text if case_sensitive else find_text.casefold() == replace_text.casefold()
    if same_text:
        raise ValueError("查找文字和替换文字相同，不需要执行替换。")

    raw_scopes = source.get("scopes")
    scopes = []
    for scope in raw_scopes if isinstance(raw_scopes, list) else DEFAULT_TEXT_REFACTOR_SCOPES:
        clean_scope = str(scope or "").strip()
        if clean_scope in TEXT_REFACTOR_SCOPE_LABELS and clean_scope not in scopes:
            scopes.append(clean_scope)
    if not scopes:
        raise ValueError("至少选择一种要处理的文字范围。")

    return {
        "findText": find_text,
        "replaceText": replace_text,
        "scopes": scopes,
        "caseSensitive": case_sensitive,
        "includeTranslations": bool(source.get("includeTranslations", False)),
    }


def build_project_text_refactor_revision(chapter_documents: list[dict]) -> str:
    serialized = json.dumps(chapter_documents, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def replace_literal_text(value: object, find_text: str, replace_text: str, *, case_sensitive: bool) -> tuple[str, int]:
    text = str(value or "")
    if case_sensitive:
        return text.replace(find_text, replace_text), text.count(find_text)
    pattern = re.compile(re.escape(find_text), flags=re.IGNORECASE)
    return pattern.subn(lambda _match: replace_text, text)


def _iter_localized_fields(source: dict, key: str, *, include_translations: bool):
    yield key, str(source.get(key) or ""), ""
    if not include_translations:
        return
    translations = source.get(f"{key}Translations")
    if not isinstance(translations, dict):
        return
    for language, value in translations.items():
        yield f"{key}Translations.{language}", str(value or ""), str(language or "").strip()


def _write_localized_field(source: dict, field_path: str, value: str) -> None:
    if "." not in field_path:
        source[field_path] = value
        return
    map_name, language = field_path.split(".", 1)
    translations = source.get(map_name)
    if not isinstance(translations, dict):
        translations = {}
        source[map_name] = translations
    translations[language] = value


def _build_match(
    *,
    scope: str,
    field_label: str,
    field_path: str,
    before: str,
    after: str,
    replacement_count: int,
    chapter: dict,
    scene: dict | None = None,
    block: dict | None = None,
    option: dict | None = None,
    option_index: int | None = None,
    language: str = "",
) -> dict:
    return {
        "scope": scope,
        "scopeLabel": TEXT_REFACTOR_SCOPE_LABELS[scope],
        "fieldLabel": field_label,
        "fieldPath": field_path,
        "language": language,
        "chapterId": str(chapter.get("chapterId") or ""),
        "chapterName": str(chapter.get("name") or chapter.get("chapterId") or "未命名章节"),
        "sceneId": str(scene.get("id") or "") if isinstance(scene, dict) else "",
        "sceneName": str(scene.get("name") or scene.get("id") or "") if isinstance(scene, dict) else "",
        "blockId": str(block.get("id") or "") if isinstance(block, dict) else "",
        "optionId": str(option.get("id") or "") if isinstance(option, dict) else "",
        "optionIndex": option_index,
        "before": before,
        "after": after,
        "replacementCount": replacement_count,
    }


def _replace_source_field(
    source: dict,
    key: str,
    *,
    request: dict,
    scope: str,
    field_label: str,
    chapter: dict,
    scene: dict | None,
    block: dict | None,
    option: dict | None = None,
    option_index: int | None = None,
) -> list[dict]:
    matches = []
    for field_path, before, language in _iter_localized_fields(
        source,
        key,
        include_translations=request["includeTranslations"],
    ):
        after, count = replace_literal_text(
            before,
            request["findText"],
            request["replaceText"],
            case_sensitive=request["caseSensitive"],
        )
        if count <= 0:
            continue
        _write_localized_field(source, field_path, after)
        matches.append(
            _build_match(
                scope=scope,
                field_label=field_label,
                field_path=field_path,
                before=before,
                after=after,
                replacement_count=count,
                chapter=chapter,
                scene=scene,
                block=block,
                option=option,
                option_index=option_index,
                language=language,
            )
        )
    return matches


def _transform_project_text(
    chapter_documents: list[dict],
    request_payload: object,
    *,
    preview_limit: int = DEFAULT_TEXT_REFACTOR_PREVIEW_LIMIT,
) -> tuple[list[dict], dict]:
    request = normalize_project_text_refactor_request(request_payload)
    original_documents = copy.deepcopy(chapter_documents)
    updated_documents = copy.deepcopy(chapter_documents)
    all_matches: list[dict] = []
    changed_chapter_indexes: set[int] = set()
    changed_scene_ids: set[str] = set()

    for chapter_index, chapter in enumerate(updated_documents):
        if not isinstance(chapter, dict):
            continue
        chapter_matches: list[dict] = []
        if "chapter_name" in request["scopes"]:
            chapter_matches.extend(
                _replace_source_field(
                    chapter,
                    "name",
                    request=request,
                    scope="chapter_name",
                    field_label="章节名",
                    chapter=chapter,
                    scene=None,
                    block=None,
                )
            )

        scenes = chapter.get("scenes")
        for scene in scenes if isinstance(scenes, list) else []:
            if not isinstance(scene, dict):
                continue
            scene_matches: list[dict] = []
            if "scene_name" in request["scopes"]:
                scene_matches.extend(
                    _replace_source_field(
                        scene,
                        "name",
                        request=request,
                        scope="scene_name",
                        field_label="场景名",
                        chapter=chapter,
                        scene=scene,
                        block=None,
                    )
                )

            blocks = scene.get("blocks")
            for block in blocks if isinstance(blocks, list) else []:
                if not isinstance(block, dict):
                    continue
                block_type = str(block.get("type") or "")
                if block_type == "dialogue" and "dialogue" in request["scopes"]:
                    scene_matches.extend(
                        _replace_source_field(
                            block,
                            "text",
                            request=request,
                            scope="dialogue",
                            field_label="角色台词",
                            chapter=chapter,
                            scene=scene,
                            block=block,
                        )
                    )
                elif block_type == "narration" and "narration" in request["scopes"]:
                    scene_matches.extend(
                        _replace_source_field(
                            block,
                            "text",
                            request=request,
                            scope="narration",
                            field_label="旁白",
                            chapter=chapter,
                            scene=scene,
                            block=block,
                        )
                    )
                elif block_type == "choice" and "choice" in request["scopes"]:
                    options = block.get("options")
                    for option_index, option in enumerate(options if isinstance(options, list) else []):
                        if not isinstance(option, dict):
                            continue
                        scene_matches.extend(
                            _replace_source_field(
                                option,
                                "text",
                                request=request,
                                scope="choice",
                                field_label=f"选项 {option_index + 1}",
                                chapter=chapter,
                                scene=scene,
                                block=block,
                                option=option,
                                option_index=option_index,
                            )
                        )
                elif block_type == "text_input" and "input" in request["scopes"]:
                    for key, field_label in (("prompt", "输入提示"), ("placeholder", "输入占位文字")):
                        scene_matches.extend(
                            _replace_source_field(
                                block,
                                key,
                                request=request,
                                scope="input",
                                field_label=field_label,
                                chapter=chapter,
                                scene=scene,
                                block=block,
                            )
                        )

            if scene_matches:
                changed_scene_ids.add(str(scene.get("id") or f"scene_{len(changed_scene_ids)}"))
                chapter_matches.extend(scene_matches)

        if chapter_matches:
            changed_chapter_indexes.add(chapter_index)
            all_matches.extend(chapter_matches)

    total_replacements = sum(int(match["replacementCount"]) for match in all_matches)
    if total_replacements > MAX_TEXT_REFACTOR_REPLACEMENTS:
        raise ValueError(
            f"这次会替换 {total_replacements} 处文字，超过安全上限 {MAX_TEXT_REFACTOR_REPLACEMENTS}；请缩小范围后重试。"
        )

    scope_counts = Counter(match["scope"] for match in all_matches)
    safe_preview_limit = max(1, min(int(preview_limit or DEFAULT_TEXT_REFACTOR_PREVIEW_LIMIT), 500))
    preview_matches = all_matches[:safe_preview_limit]
    report = {
        "request": request,
        "projectRevision": build_project_text_refactor_revision(original_documents),
        "totalMatchedFields": len(all_matches),
        "totalReplacements": total_replacements,
        "changedChapterCount": len(changed_chapter_indexes),
        "changedSceneCount": len(changed_scene_ids),
        "changedChapterIndexes": sorted(changed_chapter_indexes),
        "scopeCounts": dict(scope_counts),
        "matches": preview_matches,
        "previewLimit": safe_preview_limit,
        "truncatedMatchCount": max(0, len(all_matches) - len(preview_matches)),
    }
    return updated_documents, report

def build_project_text_refactor_preview(
    chapter_documents: list[dict],
    request_payload: object,
    *,
    preview_limit: int = DEFAULT_TEXT_REFACTOR_PREVIEW_LIMIT,
) -> dict:
    _updated_documents, report = _transform_project_text(
        chapter_documents,
        request_payload,
        preview_limit=preview_limit,
    )
    return report


def apply_project_text_refactor(
    chapter_documents: list[dict],
    request_payload: object,
    *,
    expected_revision: str,
    preview_limit: int = DEFAULT_TEXT_REFACTOR_PREVIEW_LIMIT,
) -> tuple[list[dict], dict]:
    clean_expected_revision = str(expected_revision or "").strip()
    if not clean_expected_revision:
        raise ValueError("请先预览替换结果，再确认执行。")
    current_revision = build_project_text_refactor_revision(chapter_documents)
    if clean_expected_revision != current_revision:
        raise ValueError("项目内容在预览后发生了变化，请重新预览再替换。")

    updated_documents, report = _transform_project_text(
        chapter_documents,
        request_payload,
        preview_limit=preview_limit,
    )
    if report["totalReplacements"] <= 0:
        raise ValueError("没有找到可以替换的文字。")
    return updated_documents, report
