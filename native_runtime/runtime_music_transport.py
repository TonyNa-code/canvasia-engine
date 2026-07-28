from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


MUSIC_TRANSPORT_MAX_SECONDS = 6 * 60 * 60
MUSIC_RESTART_MODES = frozenset({"continue", "restart"})


def normalize_music_seconds(value: object, fallback: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = float(fallback)
    if number != number:
        number = float(fallback)
    return round(max(0.0, min(float(MUSIC_TRANSPORT_MAX_SECONDS), number)), 3)


def sanitize_music_transport(source: dict | None = None) -> dict:
    source = source if isinstance(source, dict) else {}
    loop = source.get("loop") is not False
    start_time = normalize_music_seconds(source.get("startTimeSeconds"))
    explicit_loop_start = source.get("loopStartSeconds") not in {None, ""}
    loop_start = normalize_music_seconds(
        source.get("loopStartSeconds") if explicit_loop_start else start_time,
        start_time,
    )
    raw_loop_end = normalize_music_seconds(source.get("loopEndSeconds"))
    loop_end = raw_loop_end if raw_loop_end > loop_start else 0.0
    restart_mode = str(source.get("restartMode") or "continue")
    if restart_mode not in MUSIC_RESTART_MODES:
        restart_mode = "continue"
    return {
        "loop": loop,
        "startTimeSeconds": start_time,
        "loopStartSeconds": loop_start,
        "loopEndSeconds": loop_end,
        "restartMode": restart_mode,
    }


def is_simple_music_loop(source: dict | None = None) -> bool:
    transport = sanitize_music_transport(source)
    return bool(
        transport["loop"]
        and transport["startTimeSeconds"] == 0
        and transport["loopStartSeconds"] == 0
        and transport["loopEndSeconds"] == 0
    )


def build_music_playback_key(asset_id: object, source: dict | None = None, cue_id: object = "") -> str:
    transport = sanitize_music_transport(source)
    parts = [
        str(asset_id or ""),
        "loop" if transport["loop"] else "once",
        str(transport["startTimeSeconds"]),
        str(transport["loopStartSeconds"]),
        str(transport["loopEndSeconds"]),
    ]
    if transport["restartMode"] == "restart":
        parts.append(str(cue_id or "cue"))
    return ":".join(parts)


def get_music_initial_position(source: dict | None = None, resume_time_seconds: object | None = None) -> float:
    transport = sanitize_music_transport(source)
    if resume_time_seconds in {None, ""}:
        return float(transport["startTimeSeconds"])
    resume = normalize_music_seconds(resume_time_seconds, transport["startTimeSeconds"])
    if transport["loop"] and transport["loopEndSeconds"] > 0 and resume >= transport["loopEndSeconds"]:
        return float(transport["loopStartSeconds"])
    return resume


@dataclass
class NativeMusicTransportController:
    transport: dict | None = None
    segment_start_seconds: float = 0.0
    simple_loop: bool = False

    def configure(self, source: dict | None = None, resume_time_seconds: object | None = None) -> dict:
        self.transport = sanitize_music_transport(source)
        self.segment_start_seconds = get_music_initial_position(self.transport, resume_time_seconds)
        self.simple_loop = is_simple_music_loop(self.transport)
        return dict(self.transport)

    def reset(self) -> None:
        self.transport = None
        self.segment_start_seconds = 0.0
        self.simple_loop = False

    def get_pygame_loop_count(self) -> int:
        return -1 if self.transport and self.simple_loop else 0

    def get_start_position(self) -> float:
        return float(self.segment_start_seconds)

    def get_absolute_position(self, mixer_position_ms: object) -> float:
        try:
            elapsed = max(0.0, float(mixer_position_ms) / 1000.0)
        except (TypeError, ValueError):
            elapsed = 0.0
        return normalize_music_seconds(self.segment_start_seconds + elapsed)

    def get_restart_position(self, mixer_position_ms: object, is_busy: bool) -> float | None:
        if not self.transport or not self.transport["loop"] or self.simple_loop:
            return None
        current = self.get_absolute_position(mixer_position_ms)
        loop_end = float(self.transport["loopEndSeconds"])
        if (loop_end > 0 and current >= loop_end - 0.035) or not is_busy:
            return float(self.transport["loopStartSeconds"])
        return None

    def restart_segment(self, position_seconds: float, play_from: Callable[[float], None]) -> None:
        self.segment_start_seconds = normalize_music_seconds(position_seconds)
        play_from(self.segment_start_seconds)
