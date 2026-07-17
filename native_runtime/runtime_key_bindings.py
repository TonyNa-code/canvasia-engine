from __future__ import annotations


RUNTIME_KEY_BINDING_ACTIONS = (
    {"id": "advance", "label": "推进剧情", "detail": "显示整句或进入下一张剧情卡", "defaultCode": "Space"},
    {"id": "system", "label": "系统菜单", "detail": "打开存档、设置和标题页入口", "defaultCode": "Tab"},
    {"id": "rollback", "label": "回退剧情", "detail": "恢复上一个剧情停顿点", "defaultCode": "PageUp"},
    {"id": "auto", "label": "自动播放", "detail": "按文字与语音节奏连续阅读", "defaultCode": "KeyA"},
    {"id": "skip", "label": "跳过已读", "detail": "只快进已经读过的内容", "defaultCode": "KeyS"},
    {"id": "hide", "label": "隐藏界面", "detail": "清屏欣赏背景、CG 或立绘", "defaultCode": "KeyU"},
    {"id": "quickSave", "label": "快速存档", "detail": "保存当前剧情状态", "defaultCode": "KeyQ"},
    {"id": "quickLoad", "label": "快速读档", "detail": "读取最近一次快速存档", "defaultCode": "KeyL"},
)
DEFAULT_RUNTIME_KEY_BINDINGS = {
    action["id"]: action["defaultCode"] for action in RUNTIME_KEY_BINDING_ACTIONS
}
RESERVED_RUNTIME_KEY_CODES = frozenset(
    {
        "Escape",
        "Enter",
        "ArrowRight",
        "PageDown",
        "KeyH",
        "KeyO",
        "KeyP",
        "KeyR",
        "KeyV",
        "F1",
        "F2",
        "F5",
        "F6",
        "F7",
        "F8",
        "F9",
        "F11",
        "F12",
    }
)
SPECIAL_RUNTIME_KEY_CODES = frozenset(
    {
        "Space",
        "Tab",
        "Backspace",
        "Delete",
        "Insert",
        "Home",
        "End",
        "PageUp",
        "PageDown",
        "ArrowUp",
        "ArrowDown",
        "ArrowLeft",
    }
)
RUNTIME_KEY_BINDING_ACTION_IDS = frozenset(DEFAULT_RUNTIME_KEY_BINDINGS)


def is_runtime_key_code_allowed(value: object) -> bool:
    code = str(value or "").strip()
    if not code or code in RESERVED_RUNTIME_KEY_CODES:
        return False
    if code in SPECIAL_RUNTIME_KEY_CODES:
        return True
    if len(code) == 4 and code.startswith("Key") and code[-1].isalpha() and code[-1].isupper():
        return True
    if len(code) == 6 and code.startswith("Digit") and code[-1].isdigit():
        return True
    return len(code) == 7 and code.startswith("Numpad") and code[-1].isdigit()


def get_runtime_key_label(value: object) -> str:
    code = str(value or "").strip()
    labels = {
        "Space": "Space",
        "Tab": "Tab",
        "Backspace": "Backspace",
        "Delete": "Delete",
        "Insert": "Insert",
        "Home": "Home",
        "End": "End",
        "PageUp": "PageUp",
        "PageDown": "PageDown",
        "ArrowUp": "↑",
        "ArrowDown": "↓",
        "ArrowLeft": "←",
        "ArrowRight": "→",
    }
    if code in labels:
        return labels[code]
    if code.startswith("Key") and len(code) == 4:
        return code[-1]
    if code.startswith("Digit") and len(code) == 6:
        return code[-1]
    if code.startswith("Numpad") and len(code) == 7:
        return f"Num {code[-1]}"
    return code or "未设置"


def _assign_without_sanitizing(bindings: dict[str, str], action_id: str, code: str) -> str:
    previous_code = bindings[action_id]
    conflicting_action = next(
        (
            candidate_id
            for candidate_id, candidate_code in bindings.items()
            if candidate_id != action_id and candidate_code == code
        ),
        "",
    )
    bindings[action_id] = code
    if conflicting_action:
        bindings[conflicting_action] = previous_code
    return conflicting_action


def sanitize_runtime_key_bindings(value: dict | None = None) -> dict[str, str]:
    result = dict(DEFAULT_RUNTIME_KEY_BINDINGS)
    if not isinstance(value, dict):
        return result
    for action in RUNTIME_KEY_BINDING_ACTIONS:
        action_id = str(action["id"])
        code = str(value.get(action_id) or "").strip()
        if is_runtime_key_code_allowed(code):
            _assign_without_sanitizing(result, action_id, code)
    return result


def assign_runtime_key_binding(value: dict | None, action_id: object, code: object) -> dict:
    bindings = sanitize_runtime_key_bindings(value)
    safe_action_id = str(action_id or "").strip()
    safe_code = str(code or "").strip()
    if safe_action_id not in RUNTIME_KEY_BINDING_ACTION_IDS or not is_runtime_key_code_allowed(safe_code):
        return {"bindings": bindings, "changed": False, "displacedAction": ""}
    displaced_action = _assign_without_sanitizing(bindings, safe_action_id, safe_code)
    return {"bindings": bindings, "changed": True, "displacedAction": displaced_action}


def get_runtime_action_for_code(value: dict | None, code: object) -> str:
    safe_code = str(code or "").strip()
    if not safe_code:
        return ""
    bindings = sanitize_runtime_key_bindings(value)
    return next((action_id for action_id, action_code in bindings.items() if action_code == safe_code), "")


def get_runtime_keyboard_code(pygame, event) -> str:
    key = getattr(event, "key", None)
    special_keys = {
        "K_ESCAPE": "Escape",
        "K_RETURN": "Enter",
        "K_SPACE": "Space",
        "K_TAB": "Tab",
        "K_BACKSPACE": "Backspace",
        "K_DELETE": "Delete",
        "K_INSERT": "Insert",
        "K_HOME": "Home",
        "K_END": "End",
        "K_PAGEUP": "PageUp",
        "K_PAGEDOWN": "PageDown",
        "K_UP": "ArrowUp",
        "K_DOWN": "ArrowDown",
        "K_LEFT": "ArrowLeft",
        "K_RIGHT": "ArrowRight",
    }
    for attribute, code in special_keys.items():
        if key == getattr(pygame, attribute, None):
            return code
    for number in range(1, 13):
        if key == getattr(pygame, f"K_F{number}", None):
            return f"F{number}"
    for letter in "abcdefghijklmnopqrstuvwxyz":
        if key == getattr(pygame, f"K_{letter}", None):
            return f"Key{letter.upper()}"
    for digit in range(10):
        if key == getattr(pygame, f"K_{digit}", None):
            return f"Digit{digit}"
        if key == getattr(pygame, f"K_KP{digit}", None):
            return f"Numpad{digit}"
    return ""


def get_runtime_key_binding_summary(value: dict | None = None) -> dict:
    bindings = sanitize_runtime_key_bindings(value)
    customized_count = sum(
        bindings[action_id] != default_code
        for action_id, default_code in DEFAULT_RUNTIME_KEY_BINDINGS.items()
    )
    return {"bindings": bindings, "customizedCount": customized_count}


def build_runtime_key_binding_control_lines(value: dict | None = None) -> list[str]:
    bindings = sanitize_runtime_key_bindings(value)
    return [
        f"{get_runtime_key_label(bindings[str(action['id'])])}：{action['label']}"
        for action in RUNTIME_KEY_BINDING_ACTIONS
    ]


def render_runtime_key_bindings_overlay(player) -> None:
    pygame = player.pygame
    palette = player.get_active_palette()
    summary = get_runtime_key_binding_summary(player.runtime_settings.get("keyBindings"))
    bindings = summary["bindings"]
    selected_index = max(0, min(len(RUNTIME_KEY_BINDING_ACTIONS) - 1, int(player.key_binding_index)))
    player.key_binding_index = selected_index
    panel = pygame.Rect(0, 0, min(player.width - 72, 980), min(player.height - 72, 620))
    panel.center = (player.width // 2, player.height // 2)
    pygame.draw.rect(player.screen, (*palette["panel"], 246), panel, border_radius=28)
    pygame.draw.rect(player.screen, (*palette["panelBorder"], 92), panel, 2, border_radius=28)
    player.draw_game_ui_panel_frame(panel, "system")

    player.screen.blit(player.font_title.render("自定义按键", True, palette["text"]), (panel.left + 28, panel.top + 24))
    summary_text = (
        f"已自定义 {summary['customizedCount']} 项；冲突按键会自动交换。"
        if summary["customizedCount"]
        else "当前使用推荐键位；冲突按键会自动交换。"
    )
    player.screen.blit(player.font_ui.render(summary_text, True, palette["muted"]), (panel.left + 28, panel.top + 62))

    capture_action = str(player.key_binding_capture_action or "")
    columns = 2
    column_gap = 18
    list_left = panel.left + 24
    list_top = panel.top + 102
    column_width = (panel.width - 48 - column_gap) // columns
    row_height = 88
    for index, action in enumerate(RUNTIME_KEY_BINDING_ACTIONS):
        column = index // 4
        row = index % 4
        row_rect = pygame.Rect(
            list_left + column * (column_width + column_gap),
            list_top + row * row_height,
            column_width,
            74,
        )
        action_id = str(action["id"])
        is_active = index == selected_index
        is_capturing = capture_action == action_id
        fill_color = palette["accent"] if is_active or is_capturing else palette["panel"]
        pygame.draw.rect(player.screen, (*fill_color, 72 if is_active or is_capturing else 38), row_rect, border_radius=17)
        pygame.draw.rect(
            player.screen,
            (*palette["accentAlt" if is_active or is_capturing else "panelBorder"], 96 if is_active or is_capturing else 34),
            row_rect,
            1,
            border_radius=17,
        )
        player.draw_game_ui_button_frame(row_rect, player.get_game_ui_button_state(row_rect, active=is_active))
        player.screen.blit(player.font_ui.render(str(action["label"]), True, palette["text"]), (row_rect.left + 14, row_rect.top + 12))
        player.screen.blit(player.font_ui.render(str(action["detail"]), True, palette["muted"]), (row_rect.left + 14, row_rect.top + 40))
        key_label = "按下新按键…" if is_capturing else get_runtime_key_label(bindings[action_id])
        key_surface = player.font_ui.render(key_label, True, palette["text"])
        player.screen.blit(key_surface, (row_rect.right - key_surface.get_width() - 14, row_rect.top + 12))
        player.overlay_hotspots.append({"kind": "key-binding-item", "index": index, "value": action_id, "rect": row_rect})

    reset_rect = pygame.Rect(panel.right - 190, panel.bottom - 58, 160, 36)
    pygame.draw.rect(player.screen, (*palette["panel"], 70), reset_rect, border_radius=14)
    pygame.draw.rect(player.screen, (*palette["panelBorder"], 62), reset_rect, 1, border_radius=14)
    player.draw_game_ui_button_frame(reset_rect, player.get_game_ui_button_state(reset_rect))
    player.blit_text_center(player.font_ui, "恢复推荐键位", reset_rect.centerx, reset_rect.top + 9, palette["text"])
    player.overlay_hotspots.append({"kind": "key-binding-reset-all", "rect": reset_rect})
    hint = "↑↓ 选择 · Enter 开始改键 · R 恢复全部 · Esc 返回"
    player.screen.blit(player.font_ui.render(hint, True, palette["muted"]), (panel.left + 28, panel.bottom - 46))
