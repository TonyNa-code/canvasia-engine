from __future__ import annotations

from collections.abc import Iterable


CONTROLLER_AXIS_DEAD_ZONE = 0.62
CONTROLLER_REPEAT_DELAY_MS = 420
CONTROLLER_REPEAT_INTERVAL_MS = 95
CONTROLLER_BUTTON_ACTIONS = {
    0: "confirm",
    1: "back",
    2: "history",
    3: "system",
    4: "rollback",
    5: "auto",
    6: "skip",
    7: "system",
    12: "up",
    13: "down",
    14: "left",
    15: "right",
}
CONTROLLER_DIRECTION_ACTIONS = ("up", "down", "left", "right")
CONTROLLER_DIRECTION_ACTION_SET = frozenset(CONTROLLER_DIRECTION_ACTIONS)
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
    return {"axes": {}, "hats": {}, "buttons": {}, "repeat": {}}


def _clone_controller_input_state(state: dict | None) -> dict:
    source = state if isinstance(state, dict) else {}
    return {
        "axes": dict(source.get("axes") or {}),
        "hats": dict(source.get("hats") or {}),
        "buttons": dict(source.get("buttons") or {}),
        "repeat": {
            str(action): dict(entry)
            for action, entry in dict(source.get("repeat") or {}).items()
            if isinstance(entry, dict)
        },
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


def _safe_input_timing(value: object, fallback: int, minimum: int = 0) -> int:
    try:
        numeric_value = int(float(value))
    except (TypeError, ValueError, OverflowError):
        numeric_value = int(fallback)
    return max(int(minimum), numeric_value)


def _get_active_controller_directions(state: dict) -> list[str]:
    directions: list[str] = []

    def append_direction(action: str) -> None:
        if action in CONTROLLER_DIRECTION_ACTION_SET and action not in directions:
            directions.append(action)

    for button_index in sorted(dict(state.get("buttons") or {})):
        if state["buttons"].get(button_index):
            append_direction(CONTROLLER_BUTTON_ACTIONS.get(button_index, ""))

    axes = dict(state.get("axes") or {})
    horizontal = int(axes.get(0) or 0)
    vertical = int(axes.get(1) or 0)
    if horizontal:
        append_direction("left" if horizontal < 0 else "right")
    if vertical:
        append_direction("up" if vertical < 0 else "down")

    for hat_index in sorted(dict(state.get("hats") or {})):
        horizontal, vertical = _normalize_hat(state["hats"].get(hat_index))
        if horizontal:
            append_direction("left" if horizontal < 0 else "right")
        if vertical:
            append_direction("up" if vertical > 0 else "down")
    return directions


def get_controller_repeat_actions(
    state: dict | None,
    *,
    now_ms: object,
    repeat_delay_ms: object = CONTROLLER_REPEAT_DELAY_MS,
    repeat_interval_ms: object = CONTROLLER_REPEAT_INTERVAL_MS,
) -> dict:
    next_state = _clone_controller_input_state(state)
    timestamp = _safe_input_timing(now_ms, 0)
    delay = _safe_input_timing(repeat_delay_ms, CONTROLLER_REPEAT_DELAY_MS, 100)
    interval = _safe_input_timing(repeat_interval_ms, CONTROLLER_REPEAT_INTERVAL_MS, 40)
    active_directions = _get_active_controller_directions(next_state)
    next_repeat: dict[str, dict[str, int]] = {}
    actions: list[str] = []

    for action in active_directions:
        previous_entry = next_state["repeat"].get(action)
        if not isinstance(previous_entry, dict):
            next_repeat[action] = {"startedAt": timestamp, "lastAt": timestamp}
            continue
        started_at = _safe_input_timing(previous_entry.get("startedAt"), timestamp)
        last_at = _safe_input_timing(previous_entry.get("lastAt"), started_at)
        should_repeat = timestamp - started_at >= delay and timestamp - last_at >= interval
        next_repeat[action] = {
            "startedAt": started_at,
            "lastAt": timestamp if should_repeat else last_at,
        }
        if should_repeat:
            actions.append(action)

    next_state["repeat"] = next_repeat
    return {"actions": actions, "state": next_state}


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
    now_ms: object = 0,
) -> dict:
    next_state = _clone_controller_input_state(state)
    actions: list[str] = []
    safe_kind = str(event_kind or "").strip().lower()
    previous_directions = set(_get_active_controller_directions(next_state))

    if safe_kind in {"button_down", "button_up"}:
        try:
            button_index = int(button)
            action = CONTROLLER_BUTTON_ACTIONS.get(button_index)
        except (TypeError, ValueError):
            button_index = -1
            action = None
        if action in CONTROLLER_DIRECTION_ACTION_SET:
            next_state["buttons"][button_index] = safe_kind == "button_down"
        elif action and safe_kind == "button_down":
            actions.append(action)
    elif safe_kind == "hat_motion":
        try:
            hat_index = int(hat or 0)
        except (TypeError, ValueError):
            hat_index = 0
        current = _normalize_hat(hat_value)
        next_state["hats"][hat_index] = current
    elif safe_kind == "axis_motion":
        try:
            axis_index = int(axis)
        except (TypeError, ValueError):
            axis_index = -1
        if axis_index in {0, 1}:
            current_direction = _axis_direction(axis_value, dead_zone)
            next_state["axes"][axis_index] = current_direction

    current_directions = _get_active_controller_directions(next_state)
    new_directions = [action for action in current_directions if action not in previous_directions]
    actions.extend(new_directions)
    timestamp = _safe_input_timing(now_ms, 0)
    next_state["repeat"] = {
        action: (
            {"startedAt": timestamp, "lastAt": timestamp}
            if action in new_directions or not isinstance(next_state["repeat"].get(action), dict)
            else dict(next_state["repeat"][action])
        )
        for action in current_directions
    }

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
                "detail": "按住可连续移动，可快速浏览标题页、选项、存档、设置、历史和资料馆长列表。",
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
