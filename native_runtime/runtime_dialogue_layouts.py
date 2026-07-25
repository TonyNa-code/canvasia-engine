from __future__ import annotations

from collections.abc import Callable

try:
    from .runtime_player_view import ellipsize_text, wrap_text
except ImportError:  # pragma: no cover - exported native packages import from the same directory.
    from runtime_player_view import ellipsize_text, wrap_text


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
_NVL_BOUNDARY_BLOCK_TYPES = {"choice", "condition", "jump", "video_play", "credits_roll"}
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
        text = player.localize_value(block, "text")
        if index == player.current_block_index:
            text = player.get_current_line_render_text()
        return {
            "id": block.get("id"),
            "blockIndex": index,
            "type": block.get("type"),
            "speakerName": speaker_name,
            "text": text,
        }

    return collect_nvl_page_entries(
        blocks,
        player.current_block_index,
        resolve_entry=resolve_entry,
    )


def _render_adv_dialogue(player: object) -> None:
    line = player.current_line or {}
    layout = player.build_dialogue_layout(line)
    panel = player.get_dialog_panel_rect(layout["minHeight"])
    player.draw_dialog_panel(panel)
    padding_x = int(player.dialog_box_config.get("paddingX", 18))
    padding_y = int(player.dialog_box_config.get("paddingY", 14))
    text_left = panel.left + padding_x
    text_width = panel.width - padding_x * 2

    if text_width != layout["textWidth"]:
        layout = player.build_dialogue_layout(line, text_width)
    speaker_name = layout["speakerName"]

    current_top = panel.top + padding_y
    if speaker_name:
        player.blit_dialogue_text(
            player.font_title,
            speaker_name,
            (text_left, current_top),
            player.dialog_box_config.get("speakerColor", (238, 245, 255)),
        )
        current_top += player.font_title.get_height() + 12

    text = player.get_current_line_render_text()
    full_lines = layout["fullLines"]
    line_height = layout["lineHeight"]
    meta_text = player.build_save_summary_line()
    meta_height = player.font_ui.get_height()
    meta_top = panel.bottom - padding_y - meta_height
    max_text_height = max(36, meta_top - current_top - 10)
    max_lines = max(1, max_text_height // line_height)
    has_overflow = len(full_lines) > max_lines
    if has_overflow:
        meta_text += " · 长文本：H 查看历史"
    meta_surface = player.font_ui.render(
        meta_text,
        True,
        player.dialog_box_config.get("hintColor", (168, 184, 210)),
    )
    meta_top = panel.bottom - padding_y - meta_surface.get_height()
    max_text_height = max(36, meta_top - current_top - 10)
    max_lines = max(1, max_text_height // line_height)
    lines = wrap_text(player.font_body, text, text_width)
    visible_lines = list(lines[:max_lines])
    if has_overflow and player.is_current_line_fully_visible() and visible_lines:
        visible_lines[-1] = ellipsize_text(player.font_body, visible_lines[-1], text_width, " …")
    for index, text_line in enumerate(visible_lines):
        player.blit_dialogue_text(
            player.font_body,
            text_line,
            (text_left, current_top + index * line_height),
            player.dialog_box_config.get("textColor", (238, 245, 255)),
        )

    player.screen.blit(meta_surface, (text_left, meta_top))


def _render_cinematic_dialogue(player: object) -> None:
    pygame = player.pygame
    line = player.current_line or {}
    speaker_name = player.get_dialogue_speaker_name(line)
    text = player.get_current_line_render_text()
    panel_width = min(player.width - 36, max(460, int(player.width * 0.86)))
    text_width = panel_width - 72
    lines = wrap_text(player.font_body, text, text_width)
    line_height = player.font_body.get_height() + 10
    speaker_height = player.font_ui.get_height() + 10 if speaker_name else 0
    panel_height = max(112, 54 + speaker_height + min(len(lines), 4) * line_height)
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
    for text_line in lines[:4]:
        line_surface = player.font_body.render(
            text_line,
            True,
            player.dialog_box_config.get("textColor", (248, 250, 255)),
        )
        player.screen.blit(line_surface, (panel.centerx - line_surface.get_width() // 2, current_y))
        current_y += line_height

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
    line_height = player.font_body.get_height() + 8
    entry_gap = 14
    meta_surface = player.font_ui.render(
        f"NVL 满页叙事 · {player.build_save_summary_line()}",
        True,
        player.dialog_box_config.get("hintColor", (168, 184, 210)),
    )
    content_bottom = panel.bottom - padding_y - meta_surface.get_height() - 12
    rows = []
    for entry in entries:
        lines = wrap_text(player.font_body, str(entry.get("text") or ""), text_width)
        row_height = max(player.font_title.get_height(), len(lines) * line_height)
        rows.append((entry, lines, row_height))

    available_height = max(80, content_bottom - (panel.top + padding_y))
    while len(rows) > 1 and sum(row[2] + entry_gap for row in rows) > available_height:
        rows.pop(0)

    current_y = panel.top + padding_y
    for row_index, (entry, lines, row_height) in enumerate(rows):
        is_current = row_index == len(rows) - 1
        speaker_color = player.dialog_box_config.get(
            "speakerColor",
            (238, 245, 255),
        )
        text_color = player.dialog_box_config.get(
            "textColor",
            (238, 245, 255),
        )
        if not is_current:
            speaker_color = tuple(max(0, int(channel * 0.72)) for channel in speaker_color)
            text_color = tuple(max(0, int(channel * 0.72)) for channel in text_color)
        speaker_name = str(entry.get("speakerName") or "")
        if speaker_name:
            player.blit_dialogue_text(
                player.font_title,
                speaker_name[:16],
                (panel.left + padding_x, current_y),
                speaker_color,
            )
        for line_index, text_line in enumerate(lines):
            player.blit_dialogue_text(
                player.font_body,
                text_line,
                (text_left, current_y + line_index * line_height),
                text_color,
            )
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
