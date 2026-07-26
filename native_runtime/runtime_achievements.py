from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable, Iterable


CUSTOM_ACHIEVEMENT_PREFIX = "custom:"
MAX_ACHIEVEMENT_ID_LENGTH = 64
_UNSAFE_ACHIEVEMENT_ID_PATTERN = re.compile(r"[^0-9a-z_\-\u4e00-\u9fff]+")


def _clean_text(value: object, fallback: object = "", max_length: int = 240) -> str:
    text = str(value or "").strip() or str(fallback or "").strip()
    return text[:max_length]


def get_safe_achievement_author_id(value: object, fallback: object = "achievement") -> str:
    def normalize(candidate: object) -> str:
        text = unicodedata.normalize("NFKC", str(candidate or "")).strip().lower()
        text = re.sub(r"\s+", "-", text)
        text = _UNSAFE_ACHIEVEMENT_ID_PATTERN.sub("", text)
        return text.strip("-_")[:MAX_ACHIEVEMENT_ID_LENGTH]

    return normalize(value) or normalize(fallback) or "achievement"


def get_custom_achievement_storage_id(author_id: object, fallback: object = "achievement") -> str:
    return f"{CUSTOM_ACHIEVEMENT_PREFIX}{get_safe_achievement_author_id(author_id, fallback)}"


def _localized_value(
    block: dict,
    key: str,
    fallback: object,
    localize_value: Callable[[dict, str, object], object] | None,
) -> object:
    if callable(localize_value):
        return localize_value(block, key, fallback)
    return block.get(key, fallback)


def sanitize_achievement_unlock_block(
    block: dict | None,
    *,
    localize_value: Callable[[dict, str, object], object] | None = None,
) -> dict:
    source = block if isinstance(block, dict) else {}
    fallback_id = _clean_text(source.get("id"), "achievement", MAX_ACHIEVEMENT_ID_LENGTH)
    author_id = get_safe_achievement_author_id(source.get("achievementId"), fallback_id)
    name = _clean_text(
        _localized_value(source, "title", source.get("title"), localize_value),
        "新的成就",
        80,
    )
    return {
        "id": get_custom_achievement_storage_id(author_id),
        "authorId": author_id,
        "name": name,
        "title": name,
        "description": _clean_text(
            _localized_value(source, "description", source.get("description"), localize_value),
            "完成这段剧情时解锁。",
            240,
        ),
        "category": _clean_text(
            _localized_value(source, "category", source.get("category"), localize_value),
            "剧情里程碑",
            48,
        ),
        "requirement": _clean_text(
            _localized_value(source, "requirement", source.get("requirement"), localize_value),
            "推进到指定剧情",
            120,
        ),
        "hiddenBeforeUnlock": source.get("hiddenBeforeUnlock") is True,
        "iconAssetId": _clean_text(source.get("iconAssetId"), "", 128),
        "kind": "custom",
        "progressTarget": 1,
    }


def collect_custom_achievement_definitions(
    chapters: list[dict] | None,
    *,
    localize_value: Callable[[dict, str, object], object] | None = None,
) -> list[dict]:
    definitions: list[dict] = []
    by_id: dict[str, dict] = {}
    for chapter in chapters if isinstance(chapters, list) else []:
        for scene in chapter.get("scenes") or []:
            for block_index, block in enumerate(scene.get("blocks") or []):
                if not isinstance(block, dict) or block.get("type") != "achievement_unlock":
                    continue
                definition = {
                    **sanitize_achievement_unlock_block(block, localize_value=localize_value),
                    "sceneId": _clean_text(scene.get("id"), "", 128),
                    "blockId": _clean_text(block.get("id"), "", 128),
                    "blockIndex": block_index,
                    "duplicateCount": 0,
                }
                existing = by_id.get(definition["id"])
                if existing:
                    existing["duplicateCount"] += 1
                    continue
                by_id[definition["id"]] = definition
                definitions.append(definition)
    return [dict(definition) for definition in definitions]


def build_native_automatic_achievement_entries(metrics: dict | None = None) -> list[dict]:
    source = metrics if isinstance(metrics, dict) else {}
    character_count = max(0, int(source.get("characterCount") or 0))
    unlocked_characters = max(0, int(source.get("unlockedCharacterCount") or 0))
    gallery_count = max(0, int(source.get("galleryCount") or 0))
    unlocked_cg = max(0, int(source.get("unlockedCgCount") or 0))
    music_count = max(0, int(source.get("musicCount") or 0))
    unlocked_bgm = max(0, int(source.get("unlockedBgmCount") or 0))
    ending_count = max(0, int(source.get("endingCount") or 0))
    unlocked_endings = max(0, int(source.get("unlockedEndingCount") or 0))
    entries = [
        {
            "id": "first_start",
            "name": "初次启动",
            "subtitle": "第一次进入原生 Runtime",
            "notes": "启动一次原生 Runtime 即可点亮。",
            "unlocked": bool(source.get("hasScenes")),
        }
    ]
    collections = (
        ("character", "characters", "角色", character_count, unlocked_characters, "收录"),
        ("cg", "cg", "CG", gallery_count, unlocked_cg, "回收"),
        ("bgm", "bgm", "乐曲", music_count, unlocked_bgm, "解锁"),
        ("ending", "endings", "结局", ending_count, unlocked_endings, "回收"),
    )
    for key, collection_id, label, total, current, verb in collections:
        if total <= 0:
            continue
        entries.extend(
            [
                {
                    "id": f"first_{key}",
                    "name": f"{label}初见",
                    "subtitle": f"已{verb}{label} {current} / {total}",
                    "notes": f"任意{label}完成{verb}后点亮。",
                    "unlocked": current > 0,
                },
                {
                    "id": f"all_{collection_id}",
                    "name": f"{label}全{verb}",
                    "subtitle": f"已{verb}{label} {current} / {total}",
                    "notes": f"{verb}全部{label}后点亮。",
                    "unlocked": current >= total,
                },
            ]
        )
    return entries


def build_native_achievement_archive_entries(
    chapters: list[dict] | None,
    *,
    metrics: dict | None = None,
    unlocked_custom_ids: Iterable[str] | None = None,
    localize_value: Callable[[dict, str, object], object] | None = None,
) -> list[dict]:
    unlocked_ids = {str(value) for value in unlocked_custom_ids or [] if str(value).strip()}
    entries: list[dict] = []
    for definition in collect_custom_achievement_definitions(chapters, localize_value=localize_value):
        unlocked = definition["id"] in unlocked_ids
        hidden = definition.get("hiddenBeforeUnlock") is True and not unlocked
        name = "隐藏成就" if hidden else definition["name"]
        description = "继续探索后才能揭晓这个成就。" if hidden else definition["description"]
        category = "隐藏收集" if hidden else definition["category"]
        requirement = "条件尚未公开" if hidden else definition["requirement"]
        entries.append(
            {
                **definition,
                "name": name,
                "subtitle": f"{category} · {'已达成' if unlocked else '未达成'}",
                "notes": description if unlocked else f"目标：{requirement}",
                "actionLabel": "查看成就",
                "actionEnabled": unlocked,
                "previewAssetId": "" if hidden else definition["iconAssetId"],
                "previewText": description,
                "unlocked": unlocked,
                "hidden": hidden,
            }
        )

    entries.extend(
        {
            **entry,
            "kind": "automatic",
            "actionLabel": "查看成就",
            "actionEnabled": bool(entry.get("unlocked")),
            "previewText": entry["notes"],
        }
        for entry in build_native_automatic_achievement_entries(metrics)
    )
    return entries
