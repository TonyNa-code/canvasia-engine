from __future__ import annotations

from collections.abc import Callable, Iterable


BLOCK_LABELS = {
    "background": "切换背景",
    "dialogue": "台词",
    "narration": "旁白",
    "character_show": "显示角色",
    "character_move": "角色动作",
    "character_hide": "隐藏角色",
    "music_play": "播放音乐",
    "music_stop": "停止音乐",
    "sfx_play": "播放音效",
    "video_play": "播放视频",
    "credits_roll": "片尾字幕",
    "particle_effect": "粒子特效",
    "screen_shake": "屏幕震动",
    "screen_flash": "闪屏",
    "screen_fade": "黑场淡入淡出",
    "camera_zoom": "镜头推近拉远",
    "camera_pan": "镜头平移",
    "screen_filter": "回忆滤镜",
    "depth_blur": "景深模糊",
    "jump": "跳转",
    "variable_set": "设置变量",
    "variable_add": "修改变量",
    "choice": "选项",
    "condition": "条件判断",
}

CharacterPresentationCollector = Callable[[dict], Iterable[tuple[str, str]]]


def _get_list(source: object, key: str) -> list:
    if not isinstance(source, dict):
        return []
    value = source.get(key)
    return value if isinstance(value, list) else []


def collect_asset_usages_from_bundle(
    asset_id: str,
    bundle: object,
    collect_character_presentation_asset_ids: CharacterPresentationCollector,
) -> list[str]:
    if not asset_id or not isinstance(bundle, dict):
        return []

    characters_doc = bundle.get("characters")
    characters = _get_list(characters_doc, "characters")
    characters_by_id = {
        character.get("id"): character
        for character in characters
        if isinstance(character, dict) and character.get("id")
    }
    usages: list[str] = []

    def add_usage(candidate_asset_id: object, label: str) -> None:
        if candidate_asset_id == asset_id:
            usages.append(label)

    for character in characters:
        if not isinstance(character, dict):
            continue
        display_name = character.get("displayName") or character.get("name") or character.get("id") or "未命名角色"
        add_usage(character.get("defaultSpriteId"), f"角色默认立绘：{display_name}")
        for presentation_asset_id, label in collect_character_presentation_asset_ids(character):
            if label.startswith("差分图层："):
                expression_name = label.split("：", 1)[1]
                add_usage(presentation_asset_id, f"角色差分图层：{display_name} / {expression_name}")
            else:
                add_usage(presentation_asset_id, f"角色{label}：{display_name}")
        for expression in _get_list(character, "expressions"):
            if not isinstance(expression, dict):
                continue
            expression_name = expression.get("name") or expression.get("id") or "未命名表情"
            add_usage(expression.get("spriteAssetId"), f"角色表情：{display_name} / {expression_name}")

    for chapter in _get_list(bundle, "chapters"):
        for scene in _get_list(chapter, "scenes"):
            if not isinstance(scene, dict):
                continue
            scene_name = scene.get("name") or scene.get("id") or "未命名场景"
            for block in _get_list(scene, "blocks"):
                if not isinstance(block, dict):
                    continue
                block_type = str(block.get("type") or "").strip()
                add_usage(
                    block.get("assetId"),
                    f"场景：{scene_name} / {BLOCK_LABELS.get(block_type, block_type or '未知卡片')}",
                )
                add_usage(block.get("voiceAssetId"), f"场景：{scene_name} / 台词语音")
                if block_type not in {"dialogue", "character_show", "character_move"}:
                    continue
                character_id = block.get("speakerId") or block.get("characterId")
                expression_id = block.get("expressionId")
                character = characters_by_id.get(character_id)
                expression = next(
                    (
                        item
                        for item in _get_list(character, "expressions")
                        if isinstance(item, dict) and item.get("id") == expression_id
                    ),
                    None,
                )
                if not expression:
                    continue
                character_name = character.get("displayName") or character.get("name") or character_id
                expression_name = expression.get("name") or expression.get("id") or ""
                add_usage(
                    expression.get("spriteAssetId"),
                    f"场景：{scene_name} / {character_name} {expression_name}".strip(),
                )

    return usages
