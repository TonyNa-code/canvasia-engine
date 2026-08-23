from __future__ import annotations

from typing import Any


DEFAULT_BACKGROUND_FPS = 12


def _safe_non_negative_int(value: Any) -> int:
    try:
        return max(0, int(round(float(value))))
    except (TypeError, ValueError, OverflowError):
        return 0


def shift_deadline_ms(deadline_ms: Any, suspended_duration_ms: Any) -> int:
    deadline = _safe_non_negative_int(deadline_ms)
    duration = _safe_non_negative_int(suspended_duration_ms)
    return deadline + duration if deadline > 0 and duration > 0 else deadline


def shift_timestamp_ms(timestamp_ms: Any, suspended_duration_ms: Any) -> int:
    timestamp = _safe_non_negative_int(timestamp_ms)
    duration = _safe_non_negative_int(suspended_duration_ms)
    return timestamp + duration if timestamp > 0 and duration > 0 else timestamp


def shift_record_timestamp(record: Any, suspended_duration_ms: Any, key: str = "startedAtMs") -> bool:
    if not isinstance(record, dict) or key not in record:
        return False
    shifted = shift_timestamp_ms(record.get(key), suspended_duration_ms)
    if shifted == _safe_non_negative_int(record.get(key)):
        return False
    record[key] = shifted
    return True


class NativePlaybackLifecycleController:
    def __init__(self, *, background_fps: int = DEFAULT_BACKGROUND_FPS) -> None:
        self.background_fps = max(1, _safe_non_negative_int(background_fps) or DEFAULT_BACKGROUND_FPS)
        self.suspended = False
        self.suspended_at_ms: int | None = None
        self.total_suspended_ms = 0
        self.last_suspended_duration_ms = 0

    def snapshot(self, now_ms: Any = 0, *, event: str = "none") -> dict:
        now = _safe_non_negative_int(now_ms)
        current_duration = (
            max(0, now - self.suspended_at_ms)
            if self.suspended and self.suspended_at_ms is not None
            else 0
        )
        return {
            "event": str(event or "none"),
            "suspended": self.suspended,
            "currentSuspendedDurationMs": current_duration,
            "lastSuspendedDurationMs": self.last_suspended_duration_ms,
            "totalSuspendedMs": self.total_suspended_ms + current_duration,
            "targetFps": self.background_fps if self.suspended else 0,
        }

    def update(self, display_active: Any, now_ms: Any) -> dict:
        now = _safe_non_negative_int(now_ms)
        should_suspend = not bool(display_active)
        if should_suspend == self.suspended:
            return self.snapshot(now)
        if should_suspend:
            self.suspended = True
            self.suspended_at_ms = now
            return self.snapshot(now, event="suspend")

        started_at = self.suspended_at_ms if self.suspended_at_ms is not None else now
        self.last_suspended_duration_ms = max(0, now - started_at)
        self.total_suspended_ms += self.last_suspended_duration_ms
        self.suspended = False
        self.suspended_at_ms = None
        return self.snapshot(now, event="resume")

    def get_target_fps(self, active_fps: Any) -> int:
        active = max(1, _safe_non_negative_int(active_fps) or 1)
        return self.background_fps if self.suspended else active


__all__ = [
    "DEFAULT_BACKGROUND_FPS",
    "NativePlaybackLifecycleController",
    "shift_deadline_ms",
    "shift_record_timestamp",
    "shift_timestamp_ms",
]
