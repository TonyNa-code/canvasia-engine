from __future__ import annotations

try:
    from .runtime_persistent_variables import get_persistent_runtime_variable_summary
except ImportError:  # pragma: no cover - exported native packages import from the same directory.
    from runtime_persistent_variables import get_persistent_runtime_variable_summary


def _with_alpha(color: tuple[int, int, int], alpha: int) -> tuple[int, int, int, int]:
    return (*color[:3], max(0, min(255, int(alpha))))


def get_system_menu_item_description(runtime, item_key: str) -> str:
    descriptions = {
        "continue": "关闭菜单，返回当前剧情画面。",
        "help": "打开原生操作中心，查看当前状态、快捷键和常用入口。",
        "archives": "进入章节、CG、音乐、角色、结局和成就等资料馆。",
        "profile": "查看本地玩家档案、游玩时长和续玩统计。",
        "diagnostics": "查看当前位置、资源预热、路线预取和运行缓存，方便定位卡顿或缺素材。",
        "settings": "调整主题、全屏、语言、文字速度、文本框透明度和各类音量。",
        "quick-save": "立即覆盖快速存档，适合临时保留当前进度。",
        "quick-load": "立即读入快速存档；若没有快存会给出提示。",
        "save-vault": "把存档、续玩、解锁、跨周目记忆和体验设置封装为带完整性校验的独立备份。恢复前会自动建立回滚点。",
        "restart": "回到入口场景重新开始，并记录一次返回开头。",
        "exit": "关闭原生 Runtime 预览窗口。",
    }
    if item_key == "history":
        return f"查看最近文本和语音回听；当前记录 {len(runtime.text_history)} 条。"
    if item_key == "auto-resume":
        state = "已有续玩记录" if runtime.auto_resume_snapshot else "暂无续玩记录"
        return f"管理自动续玩快照；当前：{state}。"
    if item_key == "save":
        return f"打开正式存档面板；{runtime.build_save_summary_line()}。"
    if item_key == "load":
        return f"读取正式存档槽位；{runtime.build_save_summary_line()}。"
    if item_key == "persistent-memory":
        summary = get_persistent_runtime_variable_summary(runtime.persistent_variable_state, runtime.variables)
        return (
            f"管理作者定义的跨周目变量；当前 {summary.get('changedCount', 0)} / "
            f"{summary.get('count', 0)} 项已偏离默认值。连续确认两次才会重置，正式存档不会删除。"
        )
    return descriptions.get(item_key, "执行当前系统操作。")


def render_system_menu_overlay(runtime, menu_items: list[tuple[str, str]] | tuple[tuple[str, str], ...]) -> None:
    pygame = runtime.pygame
    palette = runtime.get_active_palette()
    panel_height = min(runtime.height - 72, max(548, 150 + len(menu_items) * 38))
    panel = pygame.Rect(0, 0, min(runtime.width - 96, 760), panel_height)
    panel.center = (runtime.width // 2, runtime.height // 2)
    pygame.draw.rect(runtime.screen, (*palette["panel"], 244), panel, border_radius=28)
    pygame.draw.rect(runtime.screen, _with_alpha(palette["panelBorder"], 72), panel, 2, border_radius=28)
    runtime.draw_game_ui_panel_frame(panel, "system")
    runtime.screen.blit(runtime.font_title.render("系统菜单", True, palette["text"]), (panel.left + 26, panel.top + 24))
    runtime.screen.blit(runtime.font_ui.render("原生 Runtime 控制台", True, palette["muted"]), (panel.left + 26, panel.top + 58))

    button_top = panel.top + 96
    list_width = min(310, max(260, panel.width // 2 - 52))
    row_step = max(28, min(38, (panel.height - 174) // max(1, len(menu_items))))
    row_height = max(24, min(32, row_step - 4))
    for index, (item_key, item_label) in enumerate(menu_items):
        row_rect = pygame.Rect(panel.left + 26, button_top + index * row_step, list_width, row_height)
        is_active = index == runtime.system_menu_index
        pygame.draw.rect(
            runtime.screen,
            _with_alpha(palette["accent"] if is_active else palette["panel"], 72 if is_active else 36),
            row_rect,
            border_radius=16,
        )
        pygame.draw.rect(
            runtime.screen,
            _with_alpha(palette["accentAlt"] if is_active else palette["panelBorder"], 84 if is_active else 22),
            row_rect,
            1,
            border_radius=16,
        )
        runtime.draw_game_ui_button_frame(row_rect, runtime.get_game_ui_button_state(row_rect, active=is_active))
        runtime.screen.blit(runtime.font_ui.render(item_label, True, palette["text"]), (row_rect.left + 14, row_rect.top + max(3, (row_height - runtime.font_ui.get_height()) // 2)))
        runtime.overlay_hotspots.append({"kind": "system-item", "value": item_key, "rect": row_rect})

    selected_key, selected_label = menu_items[runtime.system_menu_index]
    detail_rect = pygame.Rect(
        panel.left + 26 + list_width + 18,
        button_top,
        panel.right - (panel.left + 26 + list_width + 18) - 26,
        panel.bottom - button_top - 78,
    )
    pygame.draw.rect(runtime.screen, _with_alpha(palette["accent"], 16), detail_rect, border_radius=22)
    pygame.draw.rect(runtime.screen, _with_alpha(palette["panelBorder"], 32), detail_rect, 1, border_radius=22)
    runtime.screen.blit(runtime.font_body.render(selected_label, True, palette["accent"]), (detail_rect.left + 18, detail_rect.top + 18))
    runtime.blit_wrapped_text(
        runtime.font_ui,
        get_system_menu_item_description(runtime, selected_key),
        pygame.Rect(detail_rect.left + 18, detail_rect.top + 62, detail_rect.width - 36, 122),
        palette["text"],
        line_gap=6,
        max_lines=5,
    )
    status_lines = [
        f"主题：{runtime.get_setting_value_label('themeMode')}",
        f"显示：{runtime.get_setting_value_label('displayMode')}",
        f"阅读方案：{runtime.get_setting_value_label('readingProfile')}",
        f"文本：{runtime.get_setting_value_label('textSpeed')} / {runtime.get_setting_value_label('textScalePercent')}",
    ]
    status_top = detail_rect.bottom - 94
    for offset, line in enumerate(status_lines):
        runtime.screen.blit(
            runtime.font_ui.render(line, True, palette["muted"]),
            (detail_rect.left + 18, status_top + offset * (runtime.font_ui.get_height() + 6)),
        )
    runtime.screen.blit(runtime.font_ui.render("↑↓ 切换 · Enter 执行 · Esc 关闭", True, palette["muted"]), (panel.left + 26, panel.bottom - 44))


def handle_system_menu_event(runtime, event, menu_items: list[tuple[str, str]] | tuple[tuple[str, str], ...]) -> bool:
    pygame = runtime.pygame
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_UP:
            runtime.system_menu_index = (runtime.system_menu_index - 1) % len(menu_items)
            return True
        if event.key == pygame.K_DOWN:
            runtime.system_menu_index = (runtime.system_menu_index + 1) % len(menu_items)
            return True
        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
            return runtime.activate_system_menu_item(menu_items[runtime.system_menu_index][0])
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        for target in runtime.overlay_hotspots:
            if target.get("kind") == "system-item" and target["rect"].collidepoint(event.pos):
                return runtime.activate_system_menu_item(str(target.get("value") or "continue"))
    return True


__all__ = [
    "get_system_menu_item_description",
    "handle_system_menu_event",
    "render_system_menu_overlay",
]
