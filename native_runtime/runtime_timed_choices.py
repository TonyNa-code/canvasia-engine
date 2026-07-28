from __future__ import annotations

from typing import Any


TIMED_CHOICE_MIN_SECONDS = 1.0
TIMED_CHOICE_MAX_SECONDS = 300.0
TIMED_CHOICE_PRESET_SECONDS = (5, 10, 15, 30)


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _safe_number(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(fallback)


def get_safe_timed_choice_seconds(value: Any, fallback: float = 0.0) -> float:
    seconds = _safe_number(value, fallback)
    if seconds <= 0:
        return 0.0
    return round(_clamp(seconds, TIMED_CHOICE_MIN_SECONDS, TIMED_CHOICE_MAX_SECONDS), 1)


def sanitize_timed_choice_config(value: dict | None = None) -> dict:
    source = value if isinstance(value, dict) else {}
    timeout_seconds = get_safe_timed_choice_seconds(
        source.get("timeoutSeconds", source.get("choiceTimeoutSeconds")),
    )
    return {
        "enabled": timeout_seconds > 0,
        "timeoutSeconds": timeout_seconds,
        "timeoutMs": round(timeout_seconds * 1000),
        "timeoutOptionId": str(
            source.get("timeoutOptionId", source.get("choiceTimeoutOptionId")) or ""
        ).strip(),
    }


def is_timed_choice_option_selectable(option: dict | None = None) -> bool:
    option = option if isinstance(option, dict) else {}
    return (
        option.get("choiceVisible") is not False
        and option.get("choiceEnabled") is not False
        and option.get("disabled") is not True
    )


def resolve_timed_choice_target(choice_options: list[dict] | None, configured_option_id: str = "") -> str:
    options = choice_options if isinstance(choice_options, list) else []
    safe_option_id = str(configured_option_id or "").strip()
    if safe_option_id:
        configured = next(
            (option for option in options if str(option.get("id") or "").strip() == safe_option_id),
            None,
        )
        if configured and is_timed_choice_option_selectable(configured):
            return safe_option_id
    fallback = next((option for option in options if is_timed_choice_option_selectable(option)), None)
    return str((fallback or {}).get("id") or "").strip()


def sanitize_timed_choice_state(value: dict | None, config_value: dict | None = None) -> dict | None:
    if not isinstance(value, dict):
        return None
    config = sanitize_timed_choice_config(config_value)
    choice_key = str(value.get("choiceKey") or "").strip()
    if not config["enabled"] or not choice_key:
        return None
    return {
        "choiceKey": choice_key,
        "targetOptionId": str(value.get("targetOptionId") or "").strip(),
        "durationMs": config["timeoutMs"],
        "remainingMs": round(
            _clamp(_safe_number(value.get("remainingMs"), config["timeoutMs"]), 0, config["timeoutMs"])
        ),
    }


def format_timed_choice_remaining(remaining_ms: Any) -> str:
    seconds = max(0.0, _safe_number(remaining_ms)) / 1000
    if seconds >= 10:
        return f"{int(-(-seconds // 1))} 秒"
    tenths = int(-(-(seconds * 10) // 1)) / 10
    return f"{tenths:.1f} 秒"


def build_native_timed_choice_presentation(
    timer_state: dict | None,
    choice_options: list[dict] | None,
) -> dict:
    state = timer_state if isinstance(timer_state, dict) else {}
    options = choice_options if isinstance(choice_options, list) else []
    target_option_id = str(state.get("targetOptionId") or "").strip()
    target = next(
        (option for option in options if str(option.get("id") or "").strip() == target_option_id),
        None,
    )
    return {
        "visible": bool((state.get("active") or state.get("expired")) and state.get("durationMs")),
        "paused": bool(state.get("paused")),
        "remainingLabel": format_timed_choice_remaining(state.get("remainingMs")),
        "progress": _clamp(_safe_number(state.get("progress")), 0, 1),
        "targetLabel": str((target or {}).get("text") or "第一个可选分支").strip(),
        "extraHeight": 48,
    }


class NativeTimedChoiceController:
    """Keep timed-choice state independent from rendering and story navigation."""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.active = False
        self.paused = False
        self.expired = False
        self.timeout_pending = False
        self.choice_key = ""
        self.target_option_id = ""
        self.duration_ms = 0
        self.remaining_ms = 0
        self.deadline_ms = 0

    def start(
        self,
        *,
        choice_key: str,
        block: dict | None,
        choice_options: list[dict] | None,
        now_ms: int,
        remaining_ms: int | float | None = None,
        paused: bool = False,
    ) -> dict:
        config = sanitize_timed_choice_config(block)
        target_option_id = resolve_timed_choice_target(choice_options, config["timeoutOptionId"])
        safe_choice_key = str(choice_key or "").strip()
        if not config["enabled"] or not safe_choice_key or not target_option_id:
            self.reset()
            return self.snapshot(now_ms)
        if self.active and self.choice_key == safe_choice_key:
            self.target_option_id = target_option_id
            self.set_paused(paused, now_ms)
            return self.snapshot(now_ms)
        initial_remaining = config["timeoutMs"] if remaining_ms is None else int(
            _clamp(_safe_number(remaining_ms), 0, config["timeoutMs"])
        )
        self.active = initial_remaining > 0
        self.paused = bool(paused)
        self.expired = initial_remaining <= 0
        self.timeout_pending = initial_remaining <= 0
        self.choice_key = safe_choice_key
        self.target_option_id = target_option_id
        self.duration_ms = config["timeoutMs"]
        self.remaining_ms = initial_remaining
        self.deadline_ms = int(now_ms) + initial_remaining
        return self.snapshot(now_ms)

    def snapshot(self, now_ms: int) -> dict:
        if self.active and not self.paused:
            self.remaining_ms = max(0, self.deadline_ms - int(now_ms))
        progress = (
            _clamp(1 - self.remaining_ms / self.duration_ms, 0, 1)
            if self.duration_ms > 0
            else 0.0
        )
        return {
            "active": self.active,
            "paused": self.paused,
            "expired": self.expired,
            "choiceKey": self.choice_key,
            "targetOptionId": self.target_option_id,
            "durationMs": self.duration_ms,
            "remainingMs": round(self.remaining_ms),
            "progress": round(progress, 3),
        }

    def set_paused(self, paused: bool, now_ms: int) -> dict:
        next_paused = bool(paused)
        if not self.active or self.paused == next_paused:
            return self.snapshot(now_ms)
        if next_paused:
            self.snapshot(now_ms)
            self.paused = True
        else:
            self.paused = False
            self.deadline_ms = int(now_ms) + self.remaining_ms
        return self.snapshot(now_ms)

    def update(self, now_ms: int, *, paused: bool = False) -> str:
        if not self.active:
            if self.expired and self.timeout_pending:
                self.timeout_pending = False
                return self.target_option_id
            return ""
        self.set_paused(paused, now_ms)
        snapshot = self.snapshot(now_ms)
        if snapshot["remainingMs"] > 0:
            return ""
        self.active = False
        self.expired = True
        self.timeout_pending = False
        return self.target_option_id

    def serialize(self, now_ms: int) -> dict | None:
        snapshot = self.snapshot(now_ms)
        if not snapshot["active"] and not snapshot["expired"]:
            return None
        return {
            "choiceKey": snapshot["choiceKey"],
            "targetOptionId": snapshot["targetOptionId"],
            "durationMs": snapshot["durationMs"],
            "remainingMs": snapshot["remainingMs"],
        }
