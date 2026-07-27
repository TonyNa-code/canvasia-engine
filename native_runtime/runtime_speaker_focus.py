from __future__ import annotations


SPEAKER_FOCUS_MODES = {"off", "soft", "cinematic"}
DEFAULT_SPEAKER_FOCUS_CONFIG = {
    "speakerFocusMode": "soft",
    "speakerFocusIntensity": 65,
    "speakerFocusTransitionMs": 240,
}
DEFAULT_SPEAKER_FOCUS_RENDER_POSE = {
    "role": "neutral",
    "active": False,
    "muted": False,
    "opacityMultiplier": 1.0,
    "brightnessMultiplier": 1.0,
    "saturationMultiplier": 1.0,
    "scaleMultiplier": 1.0,
    "transitionMs": 0,
    "layerBoost": 0,
}
SPEAKER_FOCUS_PROFILES = {
    "off": {"opacityDrop": 0.0, "brightnessDrop": 0.0, "saturationDrop": 0.0, "activeScaleBoost": 0.0},
    "soft": {"opacityDrop": 0.2, "brightnessDrop": 0.18, "saturationDrop": 0.12, "activeScaleBoost": 0.018},
    "cinematic": {"opacityDrop": 0.42, "brightnessDrop": 0.34, "saturationDrop": 0.28, "activeScaleBoost": 0.04},
}


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _safe_number(value, fallback: float) -> float:
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


def get_safe_speaker_focus_mode(value) -> str:
    mode = str(value or DEFAULT_SPEAKER_FOCUS_CONFIG["speakerFocusMode"]).strip().lower()
    return mode if mode in SPEAKER_FOCUS_MODES else DEFAULT_SPEAKER_FOCUS_CONFIG["speakerFocusMode"]


def sanitize_speaker_focus_config(value: dict | None = None) -> dict:
    source = _config_source(value)
    return {
        "speakerFocusMode": get_safe_speaker_focus_mode(source.get("speakerFocusMode")),
        "speakerFocusIntensity": int(
            round(
                _clamp(
                    _safe_number(
                        source.get("speakerFocusIntensity"),
                        DEFAULT_SPEAKER_FOCUS_CONFIG["speakerFocusIntensity"],
                    ),
                    0,
                    100,
                )
            )
        ),
        "speakerFocusTransitionMs": int(
            round(
                _clamp(
                    _safe_number(
                        source.get("speakerFocusTransitionMs"),
                        DEFAULT_SPEAKER_FOCUS_CONFIG["speakerFocusTransitionMs"],
                    ),
                    0,
                    1200,
                )
            )
        ),
    }


def _visual_comfort_motion_scale(value: str | None) -> float:
    if value == "static":
        return 0.0
    if value == "gentle":
        return 0.35
    return 1.0


def build_native_speaker_focus_pose(
    *,
    character_id: str | None,
    active_character_id: str | None,
    visible_character_ids: list[str] | tuple[str, ...] | set[str] | None,
    game_ui_config: dict | None = None,
    visual_comfort_mode: str = "standard",
    is_leaving: bool = False,
) -> dict:
    config = sanitize_speaker_focus_config(game_ui_config)
    safe_character_id = str(character_id or "").strip()
    safe_active_character_id = str(active_character_id or "").strip()
    visible_ids = {
        str(item or "").strip()
        for item in (visible_character_ids or [])
        if str(item or "").strip()
    }
    can_focus = (
        config["speakerFocusMode"] != "off"
        and not is_leaving
        and bool(safe_character_id)
        and safe_character_id in visible_ids
        and len(visible_ids) > 1
        and safe_active_character_id in visible_ids
    )
    role = "active" if can_focus and safe_character_id == safe_active_character_id else ("muted" if can_focus else "neutral")
    profile = SPEAKER_FOCUS_PROFILES[config["speakerFocusMode"]]
    intensity = config["speakerFocusIntensity"] / 100
    motion_scale = _visual_comfort_motion_scale(visual_comfort_mode)
    active_scale = 1 + profile["activeScaleBoost"] * intensity * motion_scale if role == "active" else 1
    transition_ms = 0 if visual_comfort_mode == "static" else round(
        config["speakerFocusTransitionMs"] * (0.7 if visual_comfort_mode == "gentle" else 1)
    )
    return {
        "role": role,
        "active": role == "active",
        "muted": role == "muted",
        "opacityMultiplier": _round_pose_value(1 - profile["opacityDrop"] * intensity if role == "muted" else 1),
        "brightnessMultiplier": _round_pose_value(1 - profile["brightnessDrop"] * intensity if role == "muted" else 1),
        "saturationMultiplier": _round_pose_value(1 - profile["saturationDrop"] * intensity if role == "muted" else 1),
        "scaleMultiplier": _round_pose_value(active_scale),
        "transitionMs": int(transition_ms),
        "layerBoost": 100 if role == "active" else 0,
    }


def get_speaker_focus_transition_progress(started_at_ms: int, now_ms: int, duration_ms: int) -> float:
    if int(duration_ms or 0) <= 0:
        return 1.0
    elapsed_ms = max(0, int(now_ms or 0) - int(started_at_ms or 0))
    return _clamp(elapsed_ms / int(duration_ms), 0.0, 1.0)


def interpolate_speaker_focus_pose(previous_pose: dict, next_pose: dict, progress: float) -> dict:
    ratio = _clamp(float(progress or 0), 0.0, 1.0)
    result = dict(next_pose or {})
    for key in ("opacityMultiplier", "brightnessMultiplier", "saturationMultiplier", "scaleMultiplier"):
        previous_value = float((previous_pose or {}).get(key, 1.0))
        next_value = float((next_pose or {}).get(key, 1.0))
        result[key] = _round_pose_value(previous_value + (next_value - previous_value) * ratio)
    return result


def scale_rgb_color(color: tuple[int, int, int], multiplier: float) -> tuple[int, int, int]:
    safe_multiplier = _clamp(float(multiplier or 0), 0.0, 1.0)
    return tuple(max(0, min(255, round(int(channel) * safe_multiplier))) for channel in color[:3])


class NativeSpeakerFocusController:
    """Track focus handoffs while keeping the player entrypoint stateless."""

    def __init__(self) -> None:
        self.context_key: tuple = ()
        self.previous_poses: dict[tuple[str, bool], dict] = {}
        self.target_poses: dict[tuple[str, bool], dict] = {}
        self.transition_started_at_ms = 0
        self.transition_duration_ms = 0

    @staticmethod
    def get_item_key(character_id: str, state: dict | None) -> tuple[str, bool]:
        return character_id, bool((state or {}).get("__leaving"))

    @classmethod
    def get_render_pose(cls, poses: dict, character_id: str, state: dict | None) -> dict:
        return poses.get(cls.get_item_key(character_id, state)) or DEFAULT_SPEAKER_FOCUS_RENDER_POSE

    @staticmethod
    def _get_transition_duration_ms(config: dict, visual_comfort_mode: str) -> int:
        duration_ms = int(config["speakerFocusTransitionMs"])
        if visual_comfort_mode == "gentle":
            return round(duration_ms * 0.7)
        return 0 if visual_comfort_mode == "static" else duration_ms

    @staticmethod
    def _build_target_poses(
        items: list[tuple[str, dict]],
        active_character_id: str,
        visible_character_ids: list[str],
        config: dict,
        visual_comfort_mode: str,
    ) -> dict[tuple[str, bool], dict]:
        return {
            NativeSpeakerFocusController.get_item_key(character_id, state): build_native_speaker_focus_pose(
                character_id=character_id,
                active_character_id=active_character_id,
                visible_character_ids=visible_character_ids,
                game_ui_config=config,
                visual_comfort_mode=visual_comfort_mode,
                is_leaving=bool((state or {}).get("__leaving")),
            )
            for character_id, state in items
        }

    def _get_current_poses(
        self,
        items: list[tuple[str, dict]],
        fallback_poses: dict[str, dict],
        now_ms: int,
    ) -> dict[tuple[str, bool], dict]:
        progress = get_speaker_focus_transition_progress(
            self.transition_started_at_ms,
            now_ms,
            self.transition_duration_ms,
        )
        return {
            item_key: interpolate_speaker_focus_pose(
                self.previous_poses.get(item_key, fallback_poses[item_key]),
                self.target_poses.get(item_key, fallback_poses[item_key]),
                progress,
            )
            for character_id, state in items
            for item_key in (self.get_item_key(character_id, state),)
        }

    def build_render_poses(
        self,
        *,
        items: list[tuple[str, dict]],
        current_line: dict | None,
        game_ui_config: dict | None,
        visual_comfort_mode: str,
        now_ms: int,
    ) -> dict[tuple[str, bool], dict]:
        visible_character_ids = [
            character_id
            for character_id, state in items
            if not bool((state or {}).get("__leaving"))
        ]
        active_character_id = str((current_line or {}).get("speakerId") or "").strip()
        if active_character_id not in visible_character_ids:
            active_character_id = ""
        config = sanitize_speaker_focus_config(game_ui_config)
        context_key = (
            active_character_id,
            tuple(sorted(visible_character_ids)),
            visual_comfort_mode,
            config["speakerFocusMode"],
            config["speakerFocusIntensity"],
            config["speakerFocusTransitionMs"],
        )
        next_poses = self._build_target_poses(
            items,
            active_character_id,
            visible_character_ids,
            config,
            visual_comfort_mode,
        )
        if context_key != self.context_key:
            neutral_poses = self._build_target_poses(
                items,
                "",
                visible_character_ids,
                config,
                visual_comfort_mode,
            )
            current_poses = (
                self._get_current_poses(items, neutral_poses, now_ms)
                if self.context_key
                else neutral_poses
            )
            self.previous_poses = current_poses
            self.target_poses = next_poses
            self.context_key = context_key
            self.transition_started_at_ms = int(now_ms)
            self.transition_duration_ms = self._get_transition_duration_ms(config, visual_comfort_mode)
        return self._get_current_poses(items, next_poses, now_ms)
