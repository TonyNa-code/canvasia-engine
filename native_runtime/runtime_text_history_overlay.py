from __future__ import annotations

from typing import Callable

try:
    from .runtime_text_history import get_text_history_window
except ImportError:  # pragma: no cover - exported native packages import from the same directory.
    from runtime_text_history import get_text_history_window


def render_runtime_text_history_overlay(runtime, with_alpha: Callable) -> None:
    palette = runtime.get_active_palette()
    panel = runtime.pygame.Rect(0, 0, min(runtime.width - 88, 860), min(runtime.height - 96, 620))
    panel.center = (runtime.width // 2, runtime.height // 2)
    runtime.pygame.draw.rect(runtime.screen, (*palette["panel"], 246), panel, border_radius=28)
    runtime.pygame.draw.rect(runtime.screen, with_alpha(palette["panelBorder"], 72), panel, 2, border_radius=28)
    runtime.draw_game_ui_panel_frame(panel, "system")
    runtime.screen.blit(runtime.font_title.render("文本历史", True, palette["text"]), (panel.left + 28, panel.top + 24))

    filtered_entries = runtime.get_filtered_text_history_entries()
    filter_active = bool(
        runtime.history_search_query
        or runtime.history_speaker_filter
        or runtime.history_voiced_only
    )
    result_summary = (
        f"找到 {len(filtered_entries)} / {len(runtime.text_history)} 条"
        if filter_active
        else f"已记录 {len(runtime.text_history)} 条"
    )
    subtitle = f"{result_summary} · 字体：{runtime.font_source_status}"
    runtime.screen.blit(runtime.font_ui.render(subtitle[:72], True, palette["muted"]), (panel.left + 28, panel.top + 60))

    toolbar_top = panel.top + 88
    inner_left = panel.left + 28
    inner_width = panel.width - 56
    gap = 8
    search_width = max(150, int(inner_width * 0.36))
    speaker_width = max(104, int(inner_width * 0.18))
    action_width = max(148, inner_width - search_width - speaker_width - gap * 3)
    voiced_width = max(78, int(action_width * 0.56))
    clear_width = max(70, action_width - voiced_width)
    search_rect = runtime.pygame.Rect(inner_left, toolbar_top, search_width, 38)
    speaker_rect = runtime.pygame.Rect(search_rect.right + gap, toolbar_top, speaker_width, 38)
    voiced_rect = runtime.pygame.Rect(speaker_rect.right + gap, toolbar_top, voiced_width, 38)
    clear_rect = runtime.pygame.Rect(voiced_rect.right + gap, toolbar_top, clear_width, 38)

    search_label = runtime.history_search_query or "点击或按 / 搜索"
    if runtime.history_search_active:
        search_label = f"{search_label}│"
    controls = (
        ("history-search", search_rect, f"搜索：{search_label}", runtime.history_search_active),
        ("history-speaker", speaker_rect, runtime.history_speaker_filter or "全部角色", bool(runtime.history_speaker_filter)),
        ("history-voiced", voiced_rect, "仅有语音", runtime.history_voiced_only),
        ("history-clear", clear_rect, "清除筛选", False),
    )
    for kind, rect, label, active in controls:
        fill_color = palette["accent"] if active else palette["panel"]
        runtime.pygame.draw.rect(runtime.screen, with_alpha(fill_color, 34 if active else 58), rect, border_radius=12)
        border_color = palette["accentAlt"] if active else palette["panelBorder"]
        runtime.pygame.draw.rect(runtime.screen, with_alpha(border_color, 66 if active else 36), rect, 1, border_radius=12)
        text_color = palette["text"] if active else palette["muted"]
        clipped_label = label[-34:] if kind == "history-search" else label[:20]
        runtime.blit_text_center(runtime.font_ui, clipped_label, rect.centerx, rect.top + 10, text_color)
        runtime.overlay_hotspots.append({"kind": kind, "rect": rect})

    list_rect = runtime.pygame.Rect(panel.left + 28, panel.top + 142, panel.width - 56, panel.height - 208)
    runtime.pygame.draw.rect(runtime.screen, with_alpha(palette["accent"], 16), list_rect, border_radius=20)
    runtime.pygame.draw.rect(runtime.screen, with_alpha(palette["panelBorder"], 24), list_rect, 1, border_radius=20)
    if not filtered_entries:
        empty_text = "没有符合筛选条件的历史文本" if runtime.text_history else "还没有历史文本"
        runtime.blit_text_center(runtime.font_body, empty_text, list_rect.centerx, list_rect.centery - 18, palette["muted"])
    else:
        visible_count = max(1, list_rect.height // 104)
        y = list_rect.top + 16
        for item_index, item in get_text_history_window(
            filtered_entries,
            runtime.history_scroll_index,
            visible_count,
        ):
            item_rect = runtime.pygame.Rect(list_rect.left + 10, y - 8, list_rect.width - 20, 96)
            is_active = item_index == runtime.history_scroll_index
            if is_active:
                runtime.pygame.draw.rect(runtime.screen, with_alpha(palette["accent"], 28), item_rect, border_radius=16)
                runtime.pygame.draw.rect(runtime.screen, with_alpha(palette["accentAlt"], 64), item_rect, 1, border_radius=16)
            speaker = str(item.get("speakerName") or "旁白")
            scene_name = str(item.get("sceneName") or "")
            has_voice = bool(str(item.get("voiceAssetId") or "").strip())
            header = f"{speaker} · {scene_name}" if scene_name else speaker
            runtime.screen.blit(runtime.font_ui.render(header[:56], True, palette["accent"]), (list_rect.left + 18, y))
            if has_voice:
                voice_surface = runtime.font_ui.render("VOICE", True, palette["accentAlt"])
                runtime.screen.blit(voice_surface, (list_rect.right - voice_surface.get_width() - 18, y))
            text_rect = runtime.pygame.Rect(list_rect.left + 18, y + 24, list_rect.width - 36, 62)
            runtime.blit_wrapped_text(runtime.font_ui, str(item.get("text") or ""), text_rect, palette["text"], line_gap=4, max_lines=3)
            runtime.overlay_hotspots.append({"kind": "history-item", "value": item_index, "rect": item_rect})
            y += 104

    close_rect = runtime.pygame.Rect(panel.right - 138, panel.bottom - 56, 108, 34)
    runtime.pygame.draw.rect(runtime.screen, with_alpha(palette["panel"], 58), close_rect, border_radius=14)
    runtime.pygame.draw.rect(runtime.screen, with_alpha(palette["panelBorder"], 42), close_rect, 1, border_radius=14)
    runtime.draw_game_ui_button_frame(close_rect, runtime.get_game_ui_button_state(close_rect))
    runtime.blit_text_center(runtime.font_ui, "关闭", close_rect.centerx, close_rect.top + 8, palette["text"])
    runtime.overlay_hotspots.append({"kind": "close", "rect": close_rect})
    hint = "/ 搜索 · F 换角色 · V 仅有语音 · R 重听 · C 清除 · Esc 关闭"
    runtime.screen.blit(runtime.font_ui.render(hint, True, palette["muted"]), (panel.left + 28, panel.bottom - 44))


def handle_runtime_text_history_overlay_event(runtime, event) -> bool:
    pygame = runtime.pygame
    text_input_event = getattr(pygame, "TEXTINPUT", None)
    if text_input_event is not None and event.type == text_input_event:
        if runtime.history_search_active:
            runtime.append_text_history_search(getattr(event, "text", ""))
        return True
    if event.type == pygame.KEYDOWN:
        if runtime.history_search_active:
            if event.key == pygame.K_BACKSPACE:
                runtime.history_search_query = runtime.history_search_query[:-1]
                filtered = runtime.get_filtered_text_history_entries()
                runtime.history_scroll_index = filtered[-1][0] if filtered else 0
                return True
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                runtime.set_text_history_search_active(False)
                runtime.status_message = "历史搜索结果已保留。"
                return True
            if event.key == pygame.K_UP:
                runtime.move_text_history_selection(-1)
                return True
            if event.key == pygame.K_DOWN:
                runtime.move_text_history_selection(1)
                return True
            return True
        if event.key == pygame.K_SLASH:
            runtime.set_text_history_search_active(True)
            runtime.status_message = "请输入要查找的台词、角色或场景。"
            return True
        if event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_PAGEUP, pygame.K_PAGEDOWN):
            move_amount = {
                pygame.K_UP: -1,
                pygame.K_DOWN: 1,
                pygame.K_PAGEUP: -5,
                pygame.K_PAGEDOWN: 5,
            }[event.key]
            runtime.move_text_history_selection(move_amount)
            return True
        if event.key == pygame.K_f:
            runtime.cycle_text_history_speaker()
            runtime.status_message = f"历史角色筛选：{runtime.history_speaker_filter or '全部角色'}"
            return True
        if event.key == pygame.K_v:
            runtime.history_voiced_only = not runtime.history_voiced_only
            filtered = runtime.get_filtered_text_history_entries()
            runtime.history_scroll_index = filtered[-1][0] if filtered else 0
            runtime.status_message = "只看有语音的历史。" if runtime.history_voiced_only else "已显示全部语音状态。"
            return True
        if event.key == pygame.K_c:
            runtime.clear_text_history_filters()
            runtime.status_message = "历史筛选已清除。"
            return True
        if event.key == pygame.K_r:
            return runtime.play_selected_history_voice()
        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
            runtime.close_overlay()
            return True
    if event.type == pygame.MOUSEWHEEL:
        runtime.move_text_history_selection(-1 if event.y > 0 else 1)
        return True
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        for target in runtime.overlay_hotspots:
            if not target["rect"].collidepoint(event.pos):
                continue
            kind = target.get("kind")
            if kind == "history-item":
                runtime.history_scroll_index = int(target.get("value") or 0)
                if getattr(event, "clicks", 1) >= 2:
                    return runtime.play_selected_history_voice()
                return True
            if kind == "history-search":
                runtime.set_text_history_search_active(True)
                runtime.status_message = "请输入要查找的台词、角色或场景。"
                return True
            if kind == "history-speaker":
                runtime.cycle_text_history_speaker()
                runtime.status_message = f"历史角色筛选：{runtime.history_speaker_filter or '全部角色'}"
                return True
            if kind == "history-voiced":
                runtime.history_voiced_only = not runtime.history_voiced_only
                filtered = runtime.get_filtered_text_history_entries()
                runtime.history_scroll_index = filtered[-1][0] if filtered else 0
                return True
            if kind == "history-clear":
                runtime.clear_text_history_filters()
                runtime.set_text_history_search_active(False)
                runtime.status_message = "历史筛选已清除。"
                return True
            if kind == "close":
                runtime.close_overlay()
                return True
    if event.type == pygame.MOUSEBUTTONDOWN and event.button in {4, 5}:
        runtime.move_text_history_selection(-1 if event.button == 4 else 1)
        return True
    return True


__all__ = [
    "handle_runtime_text_history_overlay_event",
    "render_runtime_text_history_overlay",
]
