from __future__ import annotations

from collections.abc import Callable, Sequence


def render_runtime_settings_overlay(
    player,
    settings_items: Sequence[tuple[str, str]],
    with_alpha: Callable[[tuple[int, int, int], int], tuple[int, int, int, int]],
) -> None:
    palette = player.get_active_palette()
    panel = player.pygame.Rect(0, 0, min(player.width - 72, 600), min(player.height - 48, 500))
    panel.center = (player.width // 2, player.height // 2)
    player.pygame.draw.rect(player.screen, (*palette["panel"], 246), panel, border_radius=28)
    player.pygame.draw.rect(
        player.screen,
        with_alpha(palette["panelBorder"], 72),
        panel,
        2,
        border_radius=28,
    )
    player.draw_game_ui_panel_frame(panel, "system")
    player.screen.blit(player.font_title.render("体验设置", True, palette["text"]), (panel.left + 28, panel.top + 24))
    player.screen.blit(
        player.font_ui.render("主题 / 显示 / 视觉舒适度 / 阅读辅助 / 文本框 / 自动播放 / 音量", True, palette["muted"]),
        (panel.left + 28, panel.top + 58),
    )

    button_top = panel.top + 96
    row_height = 44
    available_height = max(row_height, panel.bottom - 70 - button_top)
    visible_count = max(1, min(len(settings_items), available_height // row_height))
    max_start = max(0, len(settings_items) - visible_count)
    visible_start = max(0, min(max_start, player.settings_menu_index - visible_count + 1))
    visible_items = settings_items[visible_start : visible_start + visible_count]
    for offset, (setting_key, setting_label) in enumerate(visible_items):
        index = visible_start + offset
        row_rect = player.pygame.Rect(panel.left + 24, button_top + offset * row_height, panel.width - 48, 36)
        is_active = index == player.settings_menu_index
        player.pygame.draw.rect(
            player.screen,
            with_alpha(palette["accent"] if is_active else palette["panel"], 70 if is_active else 34),
            row_rect,
            border_radius=16,
        )
        player.pygame.draw.rect(
            player.screen,
            with_alpha(palette["accentAlt"] if is_active else palette["panelBorder"], 82 if is_active else 22),
            row_rect,
            1,
            border_radius=16,
        )
        player.draw_game_ui_button_frame(row_rect, player.get_game_ui_button_state(row_rect, active=is_active))
        player.screen.blit(player.font_ui.render(setting_label, True, palette["text"]), (row_rect.left + 14, row_rect.top + 10))
        value_label = player.get_setting_value_label(setting_key)
        value_surface = player.font_ui.render(value_label, True, palette["muted"])
        player.screen.blit(value_surface, (row_rect.right - value_surface.get_width() - 48, row_rect.top + 10))
        if setting_key in {"voiceMixer", "keyBindings"}:
            player.screen.blit(player.font_ui.render("↵", True, palette["text"]), (row_rect.right - 28, row_rect.top + 9))
        else:
            player.screen.blit(player.font_ui.render("◀", True, palette["text"]), (row_rect.right - 32, row_rect.top + 9))
            player.screen.blit(player.font_ui.render("▶", True, palette["text"]), (row_rect.right - 16, row_rect.top + 9))
        player.overlay_hotspots.append({"kind": "settings-item", "value": setting_key, "index": index, "rect": row_rect})

    range_label = f"{visible_start + 1}-{visible_start + len(visible_items)}/{len(settings_items)}"
    player.screen.blit(player.font_ui.render(range_label, True, palette["muted"]), (panel.right - 96, panel.top + 62))
    hint = "↑↓ 切换 · ←→ 调整 · Enter 切换 · Esc 返回"
    player.screen.blit(player.font_ui.render(hint, True, palette["muted"]), (panel.left + 28, panel.bottom - 44))
