from __future__ import annotations

try:
    from .runtime_player_view import (
        COLOR_ACCENT,
        COLOR_ACCENT_ALT,
        COLOR_PANEL,
        COLOR_PANEL_BORDER,
        COLOR_TEXT,
        COLOR_TEXT_MUTED,
        build_save_dialog_layout,
        with_alpha,
    )
except ImportError:  # pragma: no cover - exported native packages import from the same directory.
    from runtime_player_view import (
        COLOR_ACCENT,
        COLOR_ACCENT_ALT,
        COLOR_PANEL,
        COLOR_PANEL_BORDER,
        COLOR_TEXT,
        COLOR_TEXT_MUTED,
        build_save_dialog_layout,
        with_alpha,
    )


def render_runtime_save_dialog_overlay(runtime) -> None:
    dialog_data = runtime.get_save_dialog_data()
    slots = dialog_data.get("visibleSlots") or []
    layout = build_save_dialog_layout(runtime.width, runtime.height, len(slots))
    panel_layout = layout["panel"]
    panel = runtime.pygame.Rect(
        panel_layout["x"],
        panel_layout["y"],
        panel_layout["width"],
        panel_layout["height"],
    )
    compact = bool(layout["compact"])
    runtime.pygame.draw.rect(
        runtime.screen,
        with_alpha(runtime.dialog_box_config.get("backgroundColor", COLOR_PANEL), 96),
        panel,
        border_radius=28,
    )
    runtime.pygame.draw.rect(
        runtime.screen,
        with_alpha(runtime.dialog_box_config.get("borderColor", COLOR_PANEL_BORDER), 72),
        panel,
        2,
        border_radius=28,
    )
    runtime.draw_game_ui_panel_frame(panel, "system")

    title = "正式存档" if runtime.overlay_mode == "save" else "读取存档"
    title_surface = runtime.font_title.render(
        title,
        True,
        runtime.dialog_box_config.get("speakerColor", COLOR_TEXT),
    )
    subtitle = f"第 {dialog_data['page'] + 1} / {dialog_data['pageCount']} 页 · 共 {dialog_data['slotCount']} 格"
    subtitle_surface = runtime.font_ui.render(
        subtitle,
        True,
        runtime.dialog_box_config.get("hintColor", COLOR_TEXT_MUTED),
    )
    runtime.screen.blit(title_surface, layout["titlePosition"])
    runtime.screen.blit(subtitle_surface, layout["subtitlePosition"])

    quick_save = dialog_data.get("quickSave") or {}
    quick_layout = layout["quick"]
    quick_rect = runtime.pygame.Rect(
        quick_layout["x"],
        quick_layout["y"],
        quick_layout["width"],
        quick_layout["height"],
    )
    runtime.pygame.draw.rect(
        runtime.screen,
        with_alpha(runtime.dialog_box_config.get("backgroundColor", COLOR_PANEL), 42),
        quick_rect,
        border_radius=18,
    )
    runtime.pygame.draw.rect(
        runtime.screen,
        with_alpha(runtime.dialog_box_config.get("borderColor", COLOR_PANEL_BORDER), 26),
        quick_rect,
        1,
        border_radius=18,
    )
    runtime.draw_game_ui_panel_frame(quick_rect, "save")
    quick_thumbnail_height = max(36, quick_rect.height - 20)
    quick_thumbnail_width = min(104, round(quick_thumbnail_height * 16 / 9))
    quick_thumbnail_rect = runtime.pygame.Rect(
        quick_rect.left + 10,
        quick_rect.top + 10,
        quick_thumbnail_width,
        quick_thumbnail_height,
    )
    runtime.draw_save_thumbnail(
        quick_save,
        quick_thumbnail_rect,
        "空" if quick_save.get("isEmpty") else "旧存档",
    )
    quick_text_left = quick_thumbnail_rect.right + 12
    quick_title = "快速存档" if not quick_save.get("isEmpty") else "快速存档（空）"
    runtime.screen.blit(
        runtime.font_ui.render(
            quick_title,
            True,
            runtime.dialog_box_config.get("speakerColor", COLOR_TEXT),
        ),
        (quick_text_left, quick_rect.top + (7 if compact else 10)),
    )
    quick_variable_summary = str(quick_save.get("variableSummaryText") or "")
    quick_meta = f"{quick_save.get('savedAt')} · {quick_save.get('sceneName') or '尚未创建'}"
    if quick_variable_summary:
        quick_meta = f"{quick_meta} · {quick_variable_summary}"
    runtime.screen.blit(
        runtime.font_ui.render(
            quick_meta[:92],
            True,
            runtime.dialog_box_config.get("hintColor", COLOR_TEXT_MUTED),
        ),
        (quick_text_left, quick_rect.top + (28 if compact else 34)),
    )
    quick_summary = str(quick_save.get("summaryText") or "空")
    runtime.screen.blit(
        runtime.font_ui.render(
            quick_summary[:78],
            True,
            runtime.dialog_box_config.get("textColor", COLOR_TEXT),
        ),
        (quick_text_left, quick_rect.top + (48 if compact else 52)),
    )

    for visible_index, (slot, card_layout) in enumerate(zip(slots, layout["cards"])):
        card_rect = runtime.pygame.Rect(
            card_layout["x"],
            card_layout["y"],
            card_layout["width"],
            card_layout["height"],
        )
        is_active = visible_index == runtime.overlay_focus_index
        fill_opacity = 78 if is_active else 34
        border_opacity = 92 if is_active else 24
        runtime.pygame.draw.rect(
            runtime.screen,
            with_alpha(
                runtime.dialog_box_config.get("borderColor", COLOR_ACCENT)
                if is_active
                else runtime.dialog_box_config.get("backgroundColor", COLOR_PANEL),
                fill_opacity,
            ),
            card_rect,
            border_radius=22,
        )
        runtime.pygame.draw.rect(
            runtime.screen,
            with_alpha(
                runtime.dialog_box_config.get("speakerColor", COLOR_ACCENT_ALT)
                if is_active
                else runtime.dialog_box_config.get("borderColor", COLOR_PANEL_BORDER),
                border_opacity,
            ),
            card_rect,
            2,
            border_radius=22,
        )
        runtime.draw_game_ui_panel_frame(card_rect, "save")
        label = str(slot.get("label") or "")
        is_protected = bool(slot.get("protected"))
        scene_name = str(slot.get("sceneName") or ("空位" if slot.get("isEmpty") else "未命名场景"))
        summary_text = str(slot.get("summaryText") or "")
        if slot.get("finished"):
            summary_text = "路线结束 · " + summary_text
        saved_at = str(slot.get("savedAt") or "尚未保存")
        variable_summary = str(slot.get("variableSummaryText") or "")
        meta_text = f"{saved_at} · {variable_summary}" if variable_summary else saved_at
        thumbnail_height = max(28, min(70, card_rect.height - 46))
        thumbnail_width = min(126, round(thumbnail_height * 16 / 9))
        thumbnail_rect = runtime.pygame.Rect(
            card_rect.left + 12,
            card_rect.top + 34,
            thumbnail_width,
            thumbnail_height,
        )
        runtime.draw_save_thumbnail(
            slot,
            thumbnail_rect,
            "空位" if slot.get("isEmpty") else "旧存档",
        )
        text_left = thumbnail_rect.right + 12
        runtime.screen.blit(
            runtime.font_ui.render(
                label,
                True,
                runtime.dialog_box_config.get("speakerColor", COLOR_TEXT),
            ),
            (card_rect.left + 16, card_rect.top + 12),
        )
        if not slot.get("isEmpty"):
            protection_width = 76 if is_protected else 64
            protection_rect = runtime.pygame.Rect(
                card_rect.right - protection_width - 12,
                card_rect.top + 8,
                protection_width,
                26,
            )
            protection_color = (
                runtime.dialog_box_config.get("speakerColor", COLOR_ACCENT_ALT)
                if is_protected
                else runtime.dialog_box_config.get("borderColor", COLOR_PANEL_BORDER)
            )
            runtime.pygame.draw.rect(
                runtime.screen,
                with_alpha(protection_color, 38 if is_protected else 18),
                protection_rect,
                border_radius=13,
            )
            runtime.pygame.draw.rect(
                runtime.screen,
                with_alpha(protection_color, 82 if is_protected else 38),
                protection_rect,
                1,
                border_radius=13,
            )
            runtime.blit_text_center(
                runtime.font_ui,
                "已保护" if is_protected else "保护",
                protection_rect.centerx,
                protection_rect.top + 4,
                runtime.dialog_box_config.get("textColor", COLOR_TEXT),
            )
            runtime.overlay_hotspots.append(
                {"kind": "slot-protection", "value": visible_index, "rect": protection_rect}
            )
        runtime.screen.blit(
            runtime.font_body.render(
                scene_name[:16],
                True,
                runtime.dialog_box_config.get("textColor", COLOR_TEXT),
            ),
            (text_left, card_rect.top + 34),
        )
        if card_rect.height >= 92:
            runtime.screen.blit(
                runtime.font_ui.render(
                    meta_text[:30],
                    True,
                    runtime.dialog_box_config.get("hintColor", COLOR_TEXT_MUTED),
                ),
                (text_left, card_rect.top + 70),
            )
        if card_rect.height >= 112:
            runtime.screen.blit(
                runtime.font_ui.render(
                    summary_text[:26],
                    True,
                    runtime.dialog_box_config.get("textColor", COLOR_TEXT),
                ),
                (text_left, card_rect.top + 92),
            )
        runtime.overlay_hotspots.append({"kind": "slot", "value": visible_index, "rect": card_rect})

    controls = [("prev", "上一页"), ("next", "下一页"), ("switch", "切换存/读"), ("close", "关闭")]
    for (action, label), control_layout in zip(controls, layout["controls"]):
        button_rect = runtime.pygame.Rect(
            control_layout["x"],
            control_layout["y"],
            control_layout["width"],
            control_layout["height"],
        )
        runtime.pygame.draw.rect(
            runtime.screen,
            with_alpha(runtime.dialog_box_config.get("backgroundColor", COLOR_PANEL), 58),
            button_rect,
            border_radius=14,
        )
        runtime.pygame.draw.rect(
            runtime.screen,
            with_alpha(runtime.dialog_box_config.get("borderColor", COLOR_PANEL_BORDER), 42),
            button_rect,
            1,
            border_radius=14,
        )
        runtime.draw_game_ui_button_frame(
            button_rect,
            runtime.get_game_ui_button_state(button_rect),
        )
        runtime.blit_text_center(
            runtime.font_ui,
            label,
            button_rect.centerx,
            button_rect.top + (5 if compact else 8),
            runtime.dialog_box_config.get("textColor", COLOR_TEXT),
        )
        runtime.overlay_hotspots.append({"kind": action, "rect": button_rect})

    slot_key_end = max(1, min(9, len(slots)))
    hint = f"数字键 1-{slot_key_end} 选槽位 · P 保护/取消 · ←→ 切页 · Enter 执行 · Esc 关闭"
    runtime.screen.blit(
        runtime.font_ui.render(
            hint,
            True,
            runtime.dialog_box_config.get("hintColor", COLOR_TEXT_MUTED),
        ),
        layout["hintPosition"],
    )


def handle_runtime_save_dialog_event(runtime, event) -> bool:
    pygame = runtime.pygame
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_LEFT:
            runtime.change_save_dialog_page(-1)
            return True
        if event.key == pygame.K_RIGHT:
            runtime.change_save_dialog_page(1)
            return True
        if event.key == pygame.K_UP:
            runtime.overlay_focus_index = (runtime.overlay_focus_index - 2) % max(
                1,
                runtime.get_save_dialog_slot_count(),
            )
            runtime.normalize_overlay_focus()
            return True
        if event.key == pygame.K_DOWN:
            runtime.overlay_focus_index = (runtime.overlay_focus_index + 2) % max(
                1,
                runtime.get_save_dialog_slot_count(),
            )
            runtime.normalize_overlay_focus()
            return True
        if event.key == pygame.K_a:
            runtime.overlay_focus_index = max(0, runtime.overlay_focus_index - 1)
            return True
        if event.key == pygame.K_d:
            runtime.overlay_focus_index = min(
                max(0, runtime.get_save_dialog_slot_count() - 1),
                runtime.overlay_focus_index + 1,
            )
            return True
        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
            runtime.activate_overlay_slot(runtime.overlay_focus_index)
            return True
        if event.key == pygame.K_p:
            runtime.toggle_visible_save_slot_protection(runtime.overlay_focus_index)
            return True
        digit_map = {
            pygame.K_1: 0,
            pygame.K_2: 1,
            pygame.K_3: 2,
            pygame.K_4: 3,
            pygame.K_5: 4,
            pygame.K_6: 5,
        }
        if event.key in digit_map:
            runtime.activate_overlay_slot(digit_map[event.key])
            return True
    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        for target in runtime.overlay_hotspots:
            if target["rect"].collidepoint(event.pos):
                kind = target.get("kind")
                if kind == "slot-protection":
                    runtime.toggle_visible_save_slot_protection(int(target.get("value", 0)))
                elif kind == "slot":
                    runtime.activate_overlay_slot(int(target.get("value", 0)))
                elif kind == "prev":
                    runtime.change_save_dialog_page(-1)
                elif kind == "next":
                    runtime.change_save_dialog_page(1)
                elif kind == "switch":
                    runtime.open_save_dialog("load" if runtime.overlay_mode == "save" else "save")
                elif kind == "close":
                    runtime.close_overlay()
                return True
    return True


__all__ = [
    "handle_runtime_save_dialog_event",
    "render_runtime_save_dialog_overlay",
]
