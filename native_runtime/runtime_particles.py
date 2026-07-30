from __future__ import annotations

import math
import random
from collections.abc import MutableSequence


NATIVE_PARTICLE_PRESET_DEFAULTS = {
    "snow": {"density": 40, "sizeMin": 5, "sizeMax": 14, "speed": 90, "drift": 18, "color": (255, 255, 255), "accent": (214, 238, 255), "shape": "flake"},
    "rain": {"density": 54, "sizeMin": 2, "sizeMax": 4, "speed": 300, "drift": 32, "color": (164, 208, 255), "accent": (219, 239, 255), "shape": "rain"},
    "petals": {"density": 30, "sizeMin": 10, "sizeMax": 18, "speed": 84, "drift": 30, "color": (255, 191, 221), "accent": (255, 226, 238), "shape": "petal"},
    "dust": {"density": 24, "sizeMin": 3, "sizeMax": 8, "speed": 26, "drift": 10, "color": (244, 230, 191), "accent": (255, 245, 221), "shape": "glow"},
    "embers": {"density": 34, "sizeMin": 4, "sizeMax": 10, "speed": 72, "drift": 18, "color": (255, 142, 82), "accent": (255, 217, 148), "shape": "ember"},
    "sparkles": {"density": 22, "sizeMin": 6, "sizeMax": 12, "speed": 34, "drift": 12, "color": (175, 213, 255), "accent": (235, 243, 255), "shape": "spark"},
    "bubbles": {"density": 18, "sizeMin": 10, "sizeMax": 20, "speed": -42, "drift": 12, "color": (150, 220, 255), "accent": (239, 250, 255), "shape": "bubble"},
    "confetti": {"density": 28, "sizeMin": 6, "sizeMax": 12, "speed": 110, "drift": 42, "color": (118, 159, 255), "accent": (185, 115, 255), "shape": "confetti"},
    "smoke": {"density": 20, "sizeMin": 18, "sizeMax": 42, "speed": -24, "drift": 16, "color": (149, 164, 196), "accent": (214, 222, 242), "shape": "smoke"},
    "flame": {"density": 24, "sizeMin": 10, "sizeMax": 22, "speed": -110, "drift": 12, "color": (255, 132, 63), "accent": (255, 214, 104), "shape": "flame"},
    "stardust": {"density": 28, "sizeMin": 4, "sizeMax": 10, "speed": 20, "drift": 8, "color": (126, 173, 255), "accent": (201, 140, 255), "shape": "star"},
    "glyphs": {"density": 16, "sizeMin": 12, "sizeMax": 22, "speed": 12, "drift": 6, "color": (124, 167, 255), "accent": (196, 126, 255), "shape": "glyph"},
}

NATIVE_PARTICLE_INTENSITY_MULTIPLIER = {"light": 0.65, "medium": 1.0, "heavy": 1.45}
NATIVE_PARTICLE_SPEED_MULTIPLIER = {"slow": 0.72, "medium": 1.0, "fast": 1.35}
NATIVE_PARTICLE_WIND_VALUE = {"left": -26, "still": 0, "right": 26}
NATIVE_PARTICLE_AREA_RANGES = {
    "full": (0.04, 0.96),
    "left": (0.04, 0.46),
    "center": (0.28, 0.72),
    "right": (0.54, 0.96),
}

PARTICLE_PERFORMANCE_PROFILES = {
    "mobile_low": {"label": "低配 / 移动端", "densityScale": 0.52, "maxPerLayer": 42, "maxTotal": 84, "targetFrameMs": 30.0},
    "web": {"label": "网页轻量", "densityScale": 0.78, "maxPerLayer": 72, "maxTotal": 144, "targetFrameMs": 24.0},
    "standard": {"label": "标准 PC / 网页", "densityScale": 1.0, "maxPerLayer": 180, "maxTotal": 260, "targetFrameMs": 21.0},
    "high_quality_pc": {"label": "高画质 PC", "densityScale": 1.18, "maxPerLayer": 220, "maxTotal": 420, "targetFrameMs": 19.0},
}

PARTICLE_QUALITY_LEVELS = (
    {"key": "full", "label": "完整", "scale": 1.0},
    {"key": "balanced", "label": "平衡", "scale": 0.72},
    {"key": "recovery", "label": "保帧", "scale": 0.48},
)


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return min(maximum, max(minimum, value))


def _safe_float(value, fallback: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return float(fallback)
    return number if math.isfinite(number) else float(fallback)


def _safe_option(value, allowed: set[str], fallback: str) -> str:
    candidate = str(value or "").strip()
    return candidate if candidate in allowed else fallback


def get_safe_particle_performance_profile(value) -> str:
    candidate = str(value or "standard").strip().lower()
    return candidate if candidate in PARTICLE_PERFORMANCE_PROFILES else "standard"


def get_native_particle_performance_profile(value) -> dict:
    key = get_safe_particle_performance_profile(value)
    return {"key": key, **PARTICLE_PERFORMANCE_PROFILES[key]}


def hex_to_rgb(value, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    if isinstance(value, (list, tuple)) and len(value) >= 3:
        channels = []
        for index, channel in enumerate(value[:3]):
            number = round(_safe_float(channel, fallback[index]))
            channels.append(int(_clamp(number, 0, 255)))
        return tuple(channels)

    candidate = str(value or "").strip().lstrip("#")
    if len(candidate) != 6:
        return fallback
    try:
        return tuple(int(candidate[index : index + 2], 16) for index in range(0, 6, 2))
    except ValueError:
        return fallback


def get_safe_native_particle_preset(value) -> str:
    candidate = str(value or "").strip()
    return candidate if candidate in NATIVE_PARTICLE_PRESET_DEFAULTS else "snow"


def normalize_native_particle_effect_config(effect: dict | None) -> dict:
    source = effect if isinstance(effect, dict) else {}
    preset = get_safe_native_particle_preset(source.get("preset"))
    defaults = NATIVE_PARTICLE_PRESET_DEFAULTS[preset]
    size_min = _safe_float(source.get("sizeMin"), defaults["sizeMin"])
    size_max = _safe_float(source.get("sizeMax"), defaults["sizeMax"])
    density = int(round(_safe_float(source.get("density"), defaults["density"])))
    speed_source = source.get("gravityY")
    drift_source = source.get("spreadX")
    return {
        "action": "stop" if str(source.get("action") or "start").strip() == "stop" else "start",
        "preset": preset,
        "assetId": str(source.get("assetId") or "").strip(),
        "intensity": _safe_option(source.get("intensity"), set(NATIVE_PARTICLE_INTENSITY_MULTIPLIER), "medium"),
        "speed": _safe_option(source.get("speed"), set(NATIVE_PARTICLE_SPEED_MULTIPLIER), "medium"),
        "wind": _safe_option(source.get("wind"), set(NATIVE_PARTICLE_WIND_VALUE), "still"),
        "area": _safe_option(source.get("area"), set(NATIVE_PARTICLE_AREA_RANGES), "full"),
        "density": int(_clamp(density, 4, 240)),
        "sizeMin": max(1.0, min(size_min, size_max)),
        "sizeMax": max(1.0, max(size_min, size_max)),
        "speedValue": _safe_float(speed_source, defaults["speed"]) if speed_source not in (None, "") else float(defaults["speed"]),
        "driftValue": _safe_float(drift_source, defaults["drift"]) if drift_source not in (None, "") else float(defaults["drift"]),
        "color": hex_to_rgb(source.get("color"), defaults["color"]),
        "accentColor": hex_to_rgb(source.get("colorAccent"), defaults["accent"]),
        "shape": defaults["shape"],
    }


def build_native_particle_budget(
    config: dict,
    performance_profile: str = "standard",
    adaptive_scale: float = 1.0,
) -> dict:
    profile = get_native_particle_performance_profile(performance_profile)
    requested_count = int(config.get("density") or 0)
    requested_count = int(round(requested_count * NATIVE_PARTICLE_INTENSITY_MULTIPLIER.get(config.get("intensity"), 1.0)))
    requested_count = max(0, min(240, requested_count))
    quality_scale = _clamp(_safe_float(adaptive_scale, 1.0), 0.35, 1.0)
    density_scale = profile["densityScale"] * quality_scale
    rendered_count = int(round(requested_count * density_scale))
    rendered_count = max(0, min(profile["maxPerLayer"], profile["maxTotal"], rendered_count))
    return {
        "performanceProfile": profile["key"],
        "performanceProfileLabel": profile["label"],
        "requestedCount": requested_count,
        "renderedCount": rendered_count,
        "totalBudget": int(round(profile["maxTotal"] * quality_scale)),
        "densityScale": round(density_scale, 3),
        "wasLimited": rendered_count < requested_count,
    }


def build_native_particle_item(config: dict, width: int, height: int, rng=random) -> dict:
    size = rng.uniform(float(config.get("sizeMin") or 4), float(config.get("sizeMax") or 10))
    area_start, area_end = NATIVE_PARTICLE_AREA_RANGES.get(config.get("area"), NATIVE_PARTICLE_AREA_RANGES["full"])
    start_x = rng.uniform(width * area_start, width * area_end)
    start_y = rng.uniform(-height * 0.2, height * 0.1)
    wind_bias = NATIVE_PARTICLE_WIND_VALUE.get(config.get("wind"), 0)
    speed_multiplier = NATIVE_PARTICLE_SPEED_MULTIPLIER.get(config.get("speed"), 1.0)
    velocity_x = (rng.uniform(-1.0, 1.0) * float(config.get("driftValue") or 12) * 0.25) + wind_bias
    base_speed = float(config.get("speedValue") or 90) * speed_multiplier
    velocity_y = base_speed + rng.uniform(-0.25, 0.25) * base_speed
    preset = str(config.get("preset") or "snow")
    if preset in {"bubbles", "smoke", "flame", "stardust", "glyphs"}:
        start_y = rng.uniform(height * 0.4, height * 0.95)
        velocity_y *= -0.55 if preset != "flame" else -0.82
    lifetime = rng.uniform(3.0, 8.0)
    return {
        "x": start_x,
        "y": start_y,
        "vx": velocity_x,
        "vy": velocity_y,
        "size": size,
        "life": lifetime,
        "maxLife": lifetime,
        "spin": rng.uniform(-120, 120),
        "rotation": rng.uniform(0, 360),
        "colorMix": rng.random(),
        "wobble": rng.uniform(4.0, 20.0),
        "wobblePhase": rng.uniform(0, math.pi * 2),
    }


def resize_native_particle_items(
    items: MutableSequence[dict],
    config: dict,
    width: int,
    height: int,
    target_count: int,
    rng=random,
) -> list[dict]:
    resized = list(items[: max(0, target_count)])
    while len(resized) < max(0, target_count):
        resized.append(build_native_particle_item(config, width, height, rng))
    return resized


def build_native_particle_items(
    config: dict,
    width: int,
    height: int,
    performance_profile: str = "standard",
    adaptive_scale: float = 1.0,
    rng=random,
) -> list[dict]:
    if str(config.get("action") or "start") == "stop":
        return []
    budget = build_native_particle_budget(config, performance_profile, adaptive_scale)
    return resize_native_particle_items([], config, width, height, budget["renderedCount"], rng)


def update_native_particle_items(
    items: MutableSequence[dict],
    config: dict,
    width: int,
    height: int,
    dt_seconds: float,
    elapsed_seconds: float,
    rng=random,
) -> list[dict]:
    updated = list(items)
    preset = str(config.get("preset") or "snow")
    upward = preset in {"bubbles", "smoke", "flame", "stardust", "glyphs"}
    padding = max(32.0, float(config.get("sizeMax") or 20) * 2.0)
    for index, item in enumerate(updated):
        item["life"] = max(0.0, float(item.get("life") or 0.0) - dt_seconds)
        item["rotation"] = float(item.get("rotation") or 0.0) + float(item.get("spin") or 0.0) * dt_seconds
        wobble = math.sin(elapsed_seconds * 1.8 + float(item.get("wobblePhase") or 0.0)) * float(item.get("wobble") or 0.0)
        item["x"] = float(item.get("x") or 0.0) + float(item.get("vx") or 0.0) * dt_seconds + wobble * dt_seconds
        item["y"] = float(item.get("y") or 0.0) + float(item.get("vy") or 0.0) * dt_seconds
        out_of_bounds = (
            item["x"] < -padding
            or item["x"] > width + padding
            or item["y"] < -padding
            or item["y"] > height + padding
        )
        if item["life"] <= 0 or out_of_bounds:
            replacement = build_native_particle_item(config, width, height, rng)
            if upward:
                replacement["y"] = rng.uniform(height * 0.5, height + padding * 0.5)
            else:
                replacement["y"] = rng.uniform(-height * 0.2, 0.0)
            updated[index] = replacement
    return updated


class NativeParticleQualityController:
    def __init__(self, performance_profile: str = "standard") -> None:
        self.profile = get_native_particle_performance_profile(performance_profile)
        self.quality_level_index = 0
        self.average_frame_ms = float(self.profile["targetFrameMs"])
        self.slow_frames = 0
        self.fast_frames = 0

    @property
    def adaptive_scale(self) -> float:
        return float(PARTICLE_QUALITY_LEVELS[self.quality_level_index]["scale"])

    def observe_frame(self, dt_seconds: float) -> bool:
        frame_ms = _clamp(_safe_float(dt_seconds, 0.0) * 1000.0, 1.0, 250.0)
        self.average_frame_ms = self.average_frame_ms * 0.92 + frame_ms * 0.08
        slow_threshold = float(self.profile["targetFrameMs"]) * 1.22
        fast_threshold = float(self.profile["targetFrameMs"]) * 0.82
        self.slow_frames = self.slow_frames + 1 if self.average_frame_ms > slow_threshold else max(0, self.slow_frames - 2)
        self.fast_frames = self.fast_frames + 1 if self.average_frame_ms < fast_threshold else max(0, self.fast_frames - 1)
        if self.slow_frames >= 48 and self.quality_level_index < len(PARTICLE_QUALITY_LEVELS) - 1:
            self.quality_level_index += 1
            self.slow_frames = 0
            self.fast_frames = 0
            return True
        if self.fast_frames >= 240 and self.quality_level_index > 0:
            self.quality_level_index -= 1
            self.slow_frames = 0
            self.fast_frames = 0
            return True
        return False

    def snapshot(self) -> dict:
        level = PARTICLE_QUALITY_LEVELS[self.quality_level_index]
        return {
            "performanceProfile": self.profile["key"],
            "performanceProfileLabel": self.profile["label"],
            "qualityLevelIndex": self.quality_level_index,
            "qualityLevel": level["key"],
            "qualityLevelLabel": level["label"],
            "adaptiveScale": level["scale"],
            "averageFrameMs": round(self.average_frame_ms, 2),
        }
