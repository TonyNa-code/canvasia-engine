from __future__ import annotations

from collections.abc import Callable

try:
    from .runtime_rich_text_renderer import (
        draw_runtime_rich_text,
        layout_runtime_rich_text,
        limit_runtime_rich_text_layout,
    )
    from .runtime_story_text import parse_runtime_story_text
except ImportError:  # pragma: no cover - exported native packages import from the same directory.
    from runtime_rich_text_renderer import (
        draw_runtime_rich_text,
        layout_runtime_rich_text,
        limit_runtime_rich_text_layout,
    )
    from runtime_story_text import parse_runtime_story_text


DIALOGUE_LAYOUT_IDS = ("adv", "nvl", "cinematic")
DIALOGUE_LAYOUT_LABELS = {
    "adv": "经典 ADV 对话框",
    "nvl": "NVL 满页叙事",
    "cinematic": "电影字幕",
}
DIALOGUE_LAYOUT_DESCRIPTIONS = {
    "adv": "角色名与正文显示在常规对话框中，适合大多数对白。",
    "nvl": "同页保留前文并逐句累积，适合书信、回忆、长旁白和密集叙事。",
    "cinematic": "把当前一句压成画面下方的电影字幕，适合短句、转场和演出高光。",
}

_DIALOGUE_BLOCK_TYPES = {"dialogue", "narration"}
_NVL_BOUNDARY_BLOCK_TYPES = {"choice", "condition", "jump", "video_play", "credits_roll", "achievement_unlock"}
_DEFAULT_NVL_ENTRY_LIMIT = 8
_MAX_NVL_ENTRY_LIMIT = 20


def _safe_int(value: object, minimum: int, maximum: int, fallback: int) -> int:
    try:
        numeric = int(round(float(value)))
    except (TypeError, ValueError):
        numeric = fallback
    return max(minimum, min(maximum, numeric))


def _safe_block_type(block: object) -> str:
    if not isinstance(block, dict):
        return ""
    return str(block.get("type") or "").strip().lower()


def get_safe_dialogue_layout(value: object, fallback: str = "adv") -> str:
    safe_fallback = fallback if fallback in DIALOGUE_LAYOUT_IDS else "adv"
    layout = str(value or safe_fallback).strip().lower()
    return layout if layout in DIALOGUE_LAYOUT_IDS else safe_fallback


def get_dialogue_layout_label(value: object) -> str:
    return DIALOGUE_LAYOUT_LABELS[get_safe_dialogue_layout(value)]


def get_dialogue_layout_description(value: object) -> str:
    return DIALOGUE_LAYOUT_DESCRIPTIONS[get_safe_dialogue_layout(value)]


def get_dialogue_layout_from_block(block: object, fallback: str = "adv") -> str:
    if _safe_block_type(block) not in _DIALOGUE_BLOCK_TYPES:
        return "adv"
    return get_safe_dialogue_layout(block.get("dialogueLayout"), fallback)


def should_start_new_nvl_page(block: object) -> bool:
    return (
        isinstance(block, dict)
        and get_dialogue_layout_from_block(block) == "nvl"
        and block.get("nvlPageBreak") is True
    )


def _default_resolve_dialogue_entry(block: dict, index: int) -> dict:
    return {
        "id": str(block.get("id") or f"dialogue_{index + 1}"),
        "blockIndex": index,
        "type": _safe_block_type(block),
        "speakerName": str(
            block.get("speakerName")
            or block.get("speakerId")
            or ("旁白" if block.get("type") == "narration" else "")
        ),
        "text": str(block.get("text") or ""),
    }


def _sanitize_dialogue_page_entry(entry: object, block: dict, index: int) -> dict:
    source = entry if isinstance(entry, dict) else {}
    entry_type = str(source.get("type") or block.get("type") or "").strip().lower()
    return {
        "id": str(source.get("id") or block.get("id") or f"dialogue_{index + 1}"),
        "blockIndex": _safe_int(source.get("blockIndex"), 0, 1_000_000, index),
        "type": entry_type if entry_type in _DIALOGUE_BLOCK_TYPES else "narration",
        "speakerName": str(source.get("speakerName") or ""),
        "text": str(source.get("text") or block.get("text") or ""),
        "sourceText": str(source.get("sourceText") or block.get("text") or ""),
        "storyText": source.get("storyText") if isinstance(source.get("storyText"), dict) else None,
        "visibleEnd": source.get("visibleEnd"),
    }


def collect_nvl_page_entries(
    blocks: object,
    current_index: object,
    *,
    limit: object = _DEFAULT_NVL_ENTRY_LIMIT,
    resolve_entry: Callable[[dict, int], dict] | None = None,
) -> list[dict]:
    source_blocks = blocks if isinstance(blocks, list) else []
    if not source_blocks:
        return []
    safe_index = _safe_int(current_index, 0, len(source_blocks) - 1, 0)
    current_block = source_blocks[safe_index]
    if not isinstance(current_block, dict) or get_dialogue_layout_from_block(current_block) != "nvl":
        return []

    entry_limit = _safe_int(limit, 1, _MAX_NVL_ENTRY_LIMIT, _DEFAULT_NVL_ENTRY_LIMIT)
    resolver = resolve_entry if callable(resolve_entry) else _default_resolve_dialogue_entry
    entries: list[dict] = []

    for index in range(safe_index, -1, -1):
        block = source_blocks[index]
        if not isinstance(block, dict):
            continue
        block_type = _safe_block_type(block)
        if block_type in _DIALOGUE_BLOCK_TYPES:
            if get_dialogue_layout_from_block(block) != "nvl":
                break
            entries.insert(0, _sanitize_dialogue_page_entry(resolver(block, index), block, index))
            if should_start_new_nvl_page(block) or len(entries) >= entry_limit:
                break
            continue
        if block_type in _NVL_BOUNDARY_BLOCK_TYPES:
            break

    return entries


def build_dialogue_layout_presentation(
    block: object,
    *,
    blocks: object = None,
    current_index: object = 0,
    limit: object = _DEFAULT_NVL_ENTRY_LIMIT,
    resolve_entry: Callable[[dict, int], dict] | None = None,
    fallback_layout: str = "adv",
) -> dict:
    layout = get_dialogue_layout_from_block(block, fallback_layout)
    entries = (
        collect_nvl_page_entries(
            blocks,
            current_index,
            limit=limit,
            resolve_entry=resolve_entry,
        )
        if layout == "nvl"
        else []
    )
    return {
        "layout": layout,
        "label": get_dialogue_layout_label(layout),
        "description": get_dialogue_layout_description(layout),
        "startsNewPage": should_start_new_nvl_page(block),
        "entries": entries,
    }


def _collect_player_nvl_entries(player: object) -> list[dict]:
    scene = player.get_current_scene() or {}
    blocks = scene.get("blocks") or []

    def resolve_entry(block: dict, index: int) -> dict:
        if block.get("type") == "dialogue":
            character = player.characters_by_id.get(block.get("speakerId")) or {}
            speaker_name = player.localize_value(
                character,
                "displayName",
                str(block.get("speakerId") or ""),
            )
        else:
            speaker_name = "旁白"
        source_text = player.localize_value(block, "text")
        story_text = parse_runtime_story_text(source_text)
        text = story_text["plainText"]
        visible_end = len(text)
        if index == player.current_block_index:
            story_text = (player.current_line or {}).get("textPacing") or story_text
            text = player.get_current_line_render_text()
            visible_end = len(text)
        return {
            "id": block.get("id"),
            "blockIndex": index,
            "type": block.get("type"),
            "speakerName": speaker_name,
            "text": text,
            "sourceText": source_text,
            "storyText": story_text,
            "visibleEnd": visible_end,
        }

    return collect_nvl_page_entries(
        blocks,
        player.current_block_index,
        resolve_entry=resolve_entry,
    )


def _get_player_story_text_plan(player: object, line: dict | None = None) -> dict:
    safe_line = line or player.current_line or {}
    plan = safe_line.get("textPacing")
    if isinstance(plan, dict) and "plainText" in plan:
        return plan
    return parse_runtime_story_text(safe_line.get("text") or "")


def _layout_player_story_text(
    player: object,
    plan: dict,
    max_width: int,
    color: tuple[int, int, int],
    *,
    visible_end: int | None = None,
) -> dict:
    body_font = player.font_body
    bold_font = getattr(player, "font_body_bold", body_font)
    ruby_font = getattr(player, "font_ruby", getattr(player, "font_ui", body_font))
    return layout_runtime_rich_text(
        plan,
        body_font,
        bold_font,
        ruby_font,
        max_width,
        color,
        visible_end=visible_end,
    )


def _draw_player_story_text(
    player: object,
    layout: dict,
    position: tuple[int, int],
    *,
    center: bool = False,
) -> None:
    body_font = player.font_body
    bold_font = getattr(player, "font_body_bold", body_font)
    ruby_font = getattr(player, "font_ruby", getattr(player, "font_ui", body_font))
    draw_runtime_rich_text(
        player.pygame,
        player.screen,
        layout,
        body_font,
        bold_font,
        ruby_font,
        position,
        center=center,
        shadow_strength=int(player.dialog_box_config.get("shadowStrength", 0)),
    )


def _render_adv_dialogue(player: object) -> None:
    line = player.current_line or {}
    padding_x = int(player.dialog_box_config.get("paddingX", 18))
    padding_y = int(player.dialog_box_config.get("paddingY", 14))
    layout = player.build_dialogue_layout(line)
    panel = player.get_dialog_panel_rect(layout["minHeight"])
    text_left = panel.left + padding_x
    text_width = panel.width - padding_x * 2
    if text_width != layout["textWidth"]:
        layout = player.build_dialogue_layout(line, text_width)
    speaker_name = layout["speakerName"]
    speaker_height = player.font_title.get_height() + 12 if speaker_name else 0
    meta_height = player.font_ui.get_height()
    text_color = player.dialog_box_config.get("textColor", (238, 245, 255))
    story_plan = _get_player_story_text_plan(player, line)
    full_rich_layout = _layout_player_story_text(player, story_plan, text_width, text_color)
    max_panel_height = max(176, player.height - 48)
    desired_height = padding_y * 2 + speaker_height + meta_height + 10 + full_rich_layout["totalHeight"]
    panel = player.get_dialog_panel_rect(min(max_panel_height, max(layout["minHeight"], desired_height)))
    text_left = panel.left + padding_x
    text_width = panel.width - padding_x * 2
    if text_width != full_rich_layout["maxWidth"]:
        full_rich_layout = _layout_player_story_text(player, story_plan, text_width, text_color)
    player.draw_dialog_panel(panel)

    current_top = panel.top + padding_y
    if speaker_name:
        player.blit_dialogue_text(
            player.font_title,
            speaker_name,
            (text_left, current_top),
            player.dialog_box_config.get("speakerColor", (238, 245, 255)),
        )
        current_top += player.font_title.get_height() + 12

    meta_text = player.build_save_summary_line()
    meta_top = panel.bottom - padding_y - meta_height
    max_text_height = max(36, meta_top - current_top - 10)
    max_lines = 0
    occupied_height = 0
    for rich_line in full_rich_layout["lines"]:
        line_height = int(rich_line.get("height") or player.font_body.get_height())
        if max_lines and occupied_height + line_height > max_text_height:
            break
        occupied_height += line_height
        max_lines += 1
    max_lines = max(1, max_lines)
    has_overflow = full_rich_layout["lineCount"] > max_lines
    if has_overflow:
        meta_text += " · 长文本：H 查看历史"
    meta_surface = player.font_ui.render(
        meta_text,
        True,
        player.dialog_box_config.get("hintColor", (168, 184, 210)),
    )
    meta_top = panel.bottom - padding_y - meta_surface.get_height()
    max_text_height = max(36, meta_top - current_top - 10)
    visible_layout = _layout_player_story_text(
        player,
        story_plan,
        text_width,
        text_color,
        visible_end=player.current_line_revealed_chars,
    )
    visible_layout = limit_runtime_rich_text_layout(
        visible_layout,
        max_lines,
        player.font_body,
        append_ellipsis=has_overflow and player.is_current_line_fully_visible(),
    )
    _draw_player_story_text(player, visible_layout, (text_left, current_top))

    player.screen.blit(meta_surface, (text_left, meta_top))


def _render_cinematic_dialogue(player: object) -> None:
    pygame = player.pygame
    line = player.current_line or {}
    speaker_name = player.get_dialogue_speaker_name(line)
    panel_width = min(player.width - 36, max(460, int(player.width * 0.86)))
    text_width = panel_width - 72
    text_color = player.dialog_box_config.get("textColor", (248, 250, 255))
    story_plan = _get_player_story_text_plan(player, line)
    full_layout = _layout_player_story_text(player, story_plan, text_width, text_color)
    full_layout = limit_runtime_rich_text_layout(
        full_layout,
        4,
        player.font_body,
        append_ellipsis=full_layout["lineCount"] > 4 and player.is_current_line_fully_visible(),
    )
    visible_layout = _layout_player_story_text(
        player,
        story_plan,
        text_width,
        text_color,
        visible_end=player.current_line_revealed_chars,
    )
    visible_layout = limit_runtime_rich_text_layout(visible_layout, 4, player.font_body)
    speaker_height = player.font_ui.get_height() + 10 if speaker_name else 0
    panel_height = max(112, 54 + speaker_height + full_layout["totalHeight"])
    panel = pygame.Rect(0, 0, panel_width, panel_height)
    panel.midbottom = (player.width // 2, player.height - 42)
    surface = pygame.Surface(panel.size, pygame.SRCALPHA)
    surface.fill((3, 8, 18, 192))
    pygame.draw.line(surface, (150, 210, 255, 88), (40, 0), (panel.width - 40, 0), 1)
    player.screen.blit(surface, panel)

    current_y = panel.top + 18
    if speaker_name:
        speaker_surface = player.font_ui.render(
            speaker_name,
            True,
            player.dialog_box_config.get("speakerColor", (210, 228, 255)),
        )
        player.screen.blit(speaker_surface, (panel.centerx - speaker_surface.get_width() // 2, current_y))
        current_y += speaker_height
    _draw_player_story_text(player, visible_layout, (panel.centerx, current_y), center=True)

    meta_surface = player.font_ui.render(
        player.build_save_summary_line(),
        True,
        player.dialog_box_config.get("hintColor", (168, 184, 210)),
    )
    player.screen.blit(meta_surface, (panel.right - meta_surface.get_width() - 24, panel.bottom - meta_surface.get_height() - 10))


def _render_nvl_dialogue(player: object) -> None:
    pygame = player.pygame
    entries = _collect_player_nvl_entries(player)
    panel = pygame.Rect(
        0,
        0,
        min(player.width - 42, max(520, int(player.width * 0.88))),
        min(player.height - 46, max(360, int(player.height * 0.78))),
    )
    panel.center = (player.width // 2, player.height // 2)
    player.draw_dialog_panel(panel)
    padding_x = max(24, int(player.dialog_box_config.get("paddingX", 18)))
    padding_y = max(22, int(player.dialog_box_config.get("paddingY", 14)))
    speaker_width = min(160, max(92, panel.width // 5))
    text_left = panel.left + padding_x + speaker_width
    text_width = panel.width - padding_x * 2 - speaker_width
    entry_gap = 14
    meta_surface = player.font_ui.render(
        f"NVL 满页叙事 · {player.build_save_summary_line()}",
        True,
        player.dialog_box_config.get("hintColor", (168, 184, 210)),
    )
    content_bottom = panel.bottom - padding_y - meta_surface.get_height() - 12
    rows = []
    for entry in entries:
        is_current = int(entry.get("blockIndex") or -1) == int(player.current_block_index)
        text_color = player.dialog_box_config.get("textColor", (238, 245, 255))
        if not is_current:
            text_color = tuple(max(0, int(channel * 0.72)) for channel in text_color)
        story_plan = (
            entry.get("storyText")
            if isinstance(entry.get("storyText"), dict)
            else parse_runtime_story_text(entry.get("sourceText") or entry.get("text") or "")
        )
        visible_end = entry.get("visibleEnd")
        rich_layout = _layout_player_story_text(
            player,
            story_plan,
            text_width,
            text_color,
            visible_end=len(str(entry.get("text") or "")) if visible_end is None else int(visible_end),
        )
        row_height = max(player.font_title.get_height(), rich_layout["totalHeight"])
        rows.append((entry, rich_layout, row_height, text_color))

    available_height = max(80, content_bottom - (panel.top + padding_y))
    while len(rows) > 1 and sum(row[2] + entry_gap for row in rows) > available_height:
        rows.pop(0)

    current_y = panel.top + padding_y
    for row_index, (entry, rich_layout, row_height, _text_color) in enumerate(rows):
        is_current = row_index == len(rows) - 1
        speaker_color = player.dialog_box_config.get(
            "speakerColor",
            (238, 245, 255),
        )
        if not is_current:
            speaker_color = tuple(max(0, int(channel * 0.72)) for channel in speaker_color)
        speaker_name = str(entry.get("speakerName") or "")
        if speaker_name:
            player.blit_dialogue_text(
                player.font_title,
                speaker_name[:16],
                (panel.left + padding_x, current_y),
                speaker_color,
            )
        _draw_player_story_text(player, rich_layout, (text_left, current_y))
        current_y += row_height + entry_gap
        if current_y >= content_bottom:
            break

    player.screen.blit(meta_surface, (panel.left + padding_x, panel.bottom - padding_y - meta_surface.get_height()))


def render_native_dialogue(player: object) -> None:
    layout = get_safe_dialogue_layout((player.current_line or {}).get("dialogueLayout"))
    if layout == "nvl":
        _render_nvl_dialogue(player)
    elif layout == "cinematic":
        _render_cinematic_dialogue(player)
    else:
        _render_adv_dialogue(player)
