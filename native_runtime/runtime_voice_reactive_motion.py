from __future__ import annotations

import math
from typing import Any


VOICE_REACTIVE_MOTION_MODES = {"off", "soft", "cinematic"}
DEFAULT_VOICE_REACTIVE_MOTION_CONFIG = {
    "voiceReactiveMotionMode": "soft",
    "voiceReactiveMotionIntensity": 58,
    "voiceReactiveMotionSensitivity": 62,
}
VOICE_REACTIVE_MOTION_PROFILES = {
    "off": {"scaleBoost": 0.0, "liftPercent": 0.0},
    "soft": {"scaleBoost": 0.006, "liftPercent": 0.24},
    "cinematic": {"scaleBoost": 0.014, "liftPercent": 0.55},
}
MAX_PCM_ANALYSIS_BYTES = 16 * 1024 * 1024


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _safe_number(value: Any, fallback: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(fallback)


def _round_pose_value(value: float) -> float:
    return round(float(value), 3)


def _config_source(value: dict | None) -> dict:
    source = value if isinstance(value, dict) else {}
    nested = source.get("gameUiConfig")
    return nested if isinstance(nested, dict) else source


def _visual_comfort_motion_scale(value: str | None) -> float:
    if value == "static":
        return 0.0
    if value == "gentle":
        return 0.35
    return 1.0


def get_safe_voice_reactive_motion_mode(value: Any) -> str:
    mode = str(value or DEFAULT_VOICE_REACTIVE_MOTION_CONFIG["voiceReactiveMotionMode"]).strip().lower()
    return mode if mode in VOICE_REACTIVE_MOTION_MODES else DEFAULT_VOICE_REACTIVE_MOTION_CONFIG["voiceReactiveMotionMode"]


def sanitize_voice_reactive_motion_config(value: dict | None = None) -> dict:
    source = _config_source(value)
    return {
        "voiceReactiveMotionMode": get_safe_voice_reactive_motion_mode(source.get("voiceReactiveMotionMode")),
        "voiceReactiveMotionIntensity": int(
            round(
                _clamp(
                    _safe_number(
                        source.get("voiceReactiveMotionIntensity"),
                        DEFAULT_VOICE_REACTIVE_MOTION_CONFIG["voiceReactiveMotionIntensity"],
                    ),
                    0,
                    100,
                )
            )
        ),
        "voiceReactiveMotionSensitivity": int(
            round(
                _clamp(
                    _safe_number(
                        source.get("voiceReactiveMotionSensitivity"),
                        DEFAULT_VOICE_REACTIVE_MOTION_CONFIG["voiceReactiveMotionSensitivity"],
                    ),
                    0,
                    100,
                )
            )
        ),
    }


def normalize_voice_reactive_level(raw_level: Any, sensitivity: Any = 62, previous_level: Any = 0) -> float:
    safe_raw_level = _clamp(_safe_number(raw_level, 0), 0, 1)
    safe_sensitivity = _clamp(_safe_number(sensitivity, 62), 0, 100) / 100
    threshold = 0.07 - safe_sensitivity * 0.052
    gain = 3.2 + safe_sensitivity * 4.4
    target = _clamp((safe_raw_level - threshold) * gain, 0, 1)
    previous = _clamp(_safe_number(previous_level, 0), 0, 1)
    smoothing = 0.58 if target >= previous else 0.2
    return _round_pose_value(previous + (target - previous) * smoothing)


def build_native_voice_reactive_motion_pose(
    *,
    character_id: str | None,
    active_character_id: str | None,
    voice_active: bool,
    voice_level: Any,
    game_ui_config: dict | None = None,
    visual_comfort_mode: str = "standard",
    is_leaving: bool = False,
) -> dict:
    config = sanitize_voice_reactive_motion_config(game_ui_config)
    safe_character_id = str(character_id or "").strip()
    safe_active_character_id = str(active_character_id or "").strip()
    motion_scale = _visual_comfort_motion_scale(visual_comfort_mode)
    active = bool(
        config["voiceReactiveMotionMode"] != "off"
        and voice_active
        and not is_leaving
        and safe_character_id
        and safe_character_id == safe_active_character_id
        and motion_scale > 0
    )
    level = _clamp(_safe_number(voice_level, 0), 0, 1) if active else 0.0
    activity = level * (config["voiceReactiveMotionIntensity"] / 100) * motion_scale
    profile = VOICE_REACTIVE_MOTION_PROFILES[config["voiceReactiveMotionMode"]]
    return {
        "mode": config["voiceReactiveMotionMode"],
        "active": active,
        "level": _round_pose_value(level),
        "mouthOpen": _round_pose_value(activity),
        "scaleMultiplier": _round_pose_value(1 + profile["scaleBoost"] * activity),
        "offsetYPercent": _round_pose_value(-profile["liftPercent"] * activity),
    }


def _pcm_sample_view(raw: bytes, mixer_format: int):
    bits = abs(int(mixer_format or 0))
    signed = int(mixer_format or 0) < 0
    format_code = {
        (8, True): "b",
        (8, False): "B",
        (16, True): "h",
        (16, False): "H",
        (32, True): "i",
        (32, False): "I",
    }.get((bits, signed))
    if not format_code:
        return None, 1.0, 0.0
    try:
        samples = memoryview(raw).cast(format_code)
    except (TypeError, ValueError):
        return None, 1.0, 0.0
    maximum = float((1 << (bits - 1)) - 1 if signed else (1 << bits) - 1)
    center = 0.0 if signed else maximum / 2
    normalizer = maximum if signed else max(center, 1.0)
    return samples, normalizer, center


def build_pcm_voice_envelope(
    raw: bytes | bytearray | memoryview | None,
    mixer_init: tuple | list | None,
    *,
    window_ms: int = 40,
    samples_per_window: int = 64,
) -> list[float]:
    if not raw or len(raw) > MAX_PCM_ANALYSIS_BYTES or not isinstance(mixer_init, (tuple, list)) or len(mixer_init) < 3:
        return []
    sample_rate = max(1, int(mixer_init[0] or 0))
    mixer_format = int(mixer_init[1] or 0)
    channels = max(1, int(mixer_init[2] or 1))
    samples, normalizer, center = _pcm_sample_view(bytes(raw), mixer_format)
    if samples is None:
        return []
    frames_per_window = max(1, int(sample_rate * max(10, int(window_ms)) / 1000))
    sample_count_per_window = frames_per_window * channels
    envelope: list[float] = []
    for start in range(0, len(samples), sample_count_per_window):
        end = min(len(samples), start + sample_count_per_window)
        if end <= start:
            break
        stride = max(channels, ((end - start) // max(1, samples_per_window) // channels) * channels)
        energy = 0.0
        count = 0
        for index in range(start, end, stride):
            sample = (float(samples[index]) - center) / max(normalizer, 1.0)
            energy += sample * sample
            count += 1
        envelope.append(_round_pose_value(_clamp(math.sqrt(energy / max(count, 1)), 0, 1)))
    return envelope


def _fallback_voice_level(elapsed_ms: int) -> float:
    time_seconds = max(0, int(elapsed_ms)) / 1000
    pulse = abs(math.sin(time_seconds * 11.7)) * 0.55 + abs(math.sin(time_seconds * 4.3 + 0.8)) * 0.45
    return 0.035 + pulse * 0.095


class NativeVoiceReactiveMotionController:
    """Analyze the current voice clip without coupling audio decoding to the renderer."""

    def __init__(self) -> None:
        self.character_id = ""
        self.started_at_ms = 0
        self.duration_ms = 0
        self.window_ms = 40
        self.envelope: list[float] = []
        self.current_level = 0.0
        self.last_level_at_ms = -1

    def start(self, sound, character_id: str | None, now_ms: int, mixer_init=None) -> None:
        self.character_id = str(character_id or "").strip()
        self.started_at_ms = int(now_ms or 0)
        self.current_level = 0.0
        self.last_level_at_ms = -1
        try:
            self.duration_ms = max(0, round(float(sound.get_length()) * 1000))
        except Exception:
            self.duration_ms = 0
        try:
            raw = sound.get_raw()
        except Exception:
            raw = None
        self.envelope = build_pcm_voice_envelope(raw, mixer_init, window_ms=self.window_ms)

    def stop(self) -> None:
        self.character_id = ""
        self.started_at_ms = 0
        self.duration_ms = 0
        self.envelope = []
        self.current_level = 0.0
        self.last_level_at_ms = -1

    def get_level(self, now_ms: int, voice_active: bool, sensitivity: Any = 62) -> float:
        safe_now_ms = int(now_ms or 0)
        if not voice_active or not self.character_id:
            self.current_level = normalize_voice_reactive_level(0, sensitivity, self.current_level)
            return self.current_level
        if safe_now_ms == self.last_level_at_ms:
            return self.current_level
        elapsed_ms = max(0, safe_now_ms - self.started_at_ms)
        if self.envelope:
            index = min(len(self.envelope) - 1, elapsed_ms // self.window_ms)
            raw_level = self.envelope[index]
        else:
            raw_level = _fallback_voice_level(elapsed_ms)
        self.current_level = normalize_voice_reactive_level(raw_level, sensitivity, self.current_level)
        self.last_level_at_ms = safe_now_ms
        return self.current_level

    def build_render_pose(
        self,
        *,
        character_id: str,
        active_character_id: str | None,
        voice_active: bool,
        game_ui_config: dict | None,
        visual_comfort_mode: str,
        now_ms: int,
        is_leaving: bool = False,
    ) -> dict:
        config = sanitize_voice_reactive_motion_config(game_ui_config)
        level = self.get_level(now_ms, voice_active, config["voiceReactiveMotionSensitivity"])
        return build_native_voice_reactive_motion_pose(
            character_id=character_id,
            active_character_id=active_character_id,
            voice_active=voice_active,
            voice_level=level,
            game_ui_config=config,
            visual_comfort_mode=visual_comfort_mode,
            is_leaving=is_leaving,
        )
