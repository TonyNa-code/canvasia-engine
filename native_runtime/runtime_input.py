from __future__ import annotations

from collections.abc import Iterable


CONTROLLER_AXIS_DEAD_ZONE = 0.62
CONTROLLER_BUTTON_ACTIONS = {
    0: "confirm",
    1: "back",
    2: "history",
    3: "system",
    4: "rollback",
    5: "auto",
    6: "skip",
    7: "system",
}
CONTROLLER_ACTION_KEY_ATTRS = {
    "up": "K_UP",
    "down": "K_DOWN",
    "left": "K_LEFT",
    "right": "K_RIGHT",
    "confirm": "K_RETURN",
    "history": "K_h",
    "rollback": "K_PAGEUP",
    "auto": "K_a",
    "skip": "K_s",
}


def build_controller_input_state() -> dict:
    return {"axes": {}, "hats": {}}


def _clone_controller_input_state(state: dict | None) -> dict:
    source = state if isinstance(state, dict) else {}
    return {
        "axes": dict(source.get("axes") or {}),
        "hats": dict(source.get("hats") or {}),
    }


def _axis_direction(value: object, dead_zone: float) -> int:
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return 0
    safe_dead_zone = min(0.95, max(0.25, float(dead_zone or CONTROLLER_AXIS_DEAD_ZONE)))
    if numeric_value <= -safe_dead_zone:
        return -1
    if numeric_value >= safe_dead_zone:
        return 1
    return 0


def _normalize_hat(value: object) -> tuple[int, int]:
    if not isinstance(value, (tuple, list)) or len(value) < 2:
        return (0, 0)
    return (_axis_direction(value[0], 0.5), _axis_direction(value[1], 0.5))


def translate_controller_input(
    event_kind: str,
    *,
    button: object = None,
    hat: object = 0,
    hat_value: object = None,
    axis: object = None,
    axis_value: object = None,
    state: dict | None = None,
    dead_zone: float = CONTROLLER_AXIS_DEAD_ZONE,
) -> dict:
    next_state = _clone_controller_input_state(state)
    actions: list[str] = []
    safe_kind = str(event_kind or "").strip().lower()

    if safe_kind == "button_down":
        try:
            action = CONTROLLER_BUTTON_ACTIONS.get(int(button))
        except (TypeError, ValueError):
            action = None
        if action:
            actions.append(action)
    elif safe_kind == "hat_motion":
        try:
            hat_index = int(hat or 0)
        except (TypeError, ValueError):
            hat_index = 0
        previous = _normalize_hat(next_state["hats"].get(hat_index))
        current = _normalize_hat(hat_value)
        next_state["hats"][hat_index] = current
        if current[0] and current[0] != previous[0]:
            actions.append("left" if current[0] < 0 else "right")
        if current[1] and current[1] != previous[1]:
            actions.append("up" if current[1] > 0 else "down")
    elif safe_kind == "axis_motion":
        try:
            axis_index = int(axis)
        except (TypeError, ValueError):
            axis_index = -1
        if axis_index in {0, 1}:
            previous_direction = int(next_state["axes"].get(axis_index) or 0)
            current_direction = _axis_direction(axis_value, dead_zone)
            next_state["axes"][axis_index] = current_direction
            if current_direction and current_direction != previous_direction:
                if axis_index == 0:
                    actions.append("left" if current_direction < 0 else "right")
                else:
                    actions.append("up" if current_direction < 0 else "down")

    return {"actions": actions, "state": next_state}


def get_controller_action_key_attr(action: str) -> str | None:
    return CONTROLLER_ACTION_KEY_ATTRS.get(str(action or "").strip().lower())


def build_controller_status(controller_names: Iterable[object] | None = None) -> dict:
    names: list[str] = []
    for value in controller_names or []:
        name = str(value or "").strip()
        if name:
            names.append(name[:80])
    connected_count = len(names)
    if not connected_count:
        label = "未连接"
    elif connected_count == 1:
        label = f"1 个 · {names[0]}"
    else:
        label = f"{connected_count} 个 · {names[0]} 等"
    return {
        "connectedCount": connected_count,
        "connected": connected_count > 0,
        "names": names,
        "label": label,
    }


def build_controller_control_group() -> dict:
    return {
        "key": "controller",
        "title": "手柄操作",
        "description": "无需靠近键盘即可完成阅读、选择、回看和系统操作。",
        "controls": (
            {
                "keys": ("左摇杆 / 十字键",),
                "label": "移动选择",
                "detail": "可操作标题页、选项、系统菜单、存档、设置、历史和资料馆。",
            },
            {
                "keys": ("A / ×", "B / ○"),
                "label": "确认 / 返回",
                "detail": "确认当前项目；返回键关闭面板，阅读中则打开系统菜单。",
            },
            {
                "keys": ("X / □", "Y / △ / Menu"),
                "label": "文本历史 / 系统菜单",
                "detail": "随时回看已显示文本，或打开存档、设置和资料馆入口。",
            },
            {
                "keys": ("LB / L1", "RB / R1", "View"),
                "label": "回退 / 自动 / 已读快进",
                "detail": "覆盖长篇视觉小说最常用的阅读辅助动作。",
            },
        ),
    }
