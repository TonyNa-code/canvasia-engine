from __future__ import annotations

from typing import Any


DIALOGUE_CAMERA_MODES = {"off", "soft", "cinematic"}
DEFAULT_DIALOGUE_CAMERA_CONFIG = {
    "dialogueCameraMode": "soft",
    "dialogueCameraIntensity": 58,
    "dialogueCameraTransitionMs": 520,
}
DIALOGUE_CAMERA_PROFILES = {
    "off": {"panFactor": 0.0, "zoomBoost": 0.0},
    "soft": {"panFactor": 0.15, "zoomBoost": 0.022},
    "cinematic": {"panFactor": 0.28, "zoomBoost": 0.05},
}
CHARACTER_POSITION_PERCENT = {"left": 24.0, "center": 50.0, "right": 76.0}
NATIVE_MANUAL_ZOOM_SCALE = {
    ("zoom_in", "light"): 1.045,
    ("zoom_in", "medium"): 1.085,
    ("zoom_in", "heavy"): 1.13,
    ("zoom_out", "light"): 0.985,
    ("zoom_out", "medium"): 0.96,
    ("zoom_out", "heavy"): 0.925,
}
NATIVE_MANUAL_PAN_RATIO = {"left": 0.055, "right": -0.055}
NATIVE_MANUAL_PAN_STRENGTH = {"light": 0.62, "medium": 1.0, "heavy": 1.44}
NATIVE_MANUAL_FOCUS_PERCENT = {"left": 28.0, "center": 50.0, "right": 72.0}


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


def get_safe_dialogue_camera_mode(value: Any) -> str:
    mode = str(value or DEFAULT_DIALOGUE_CAMERA_CONFIG["dialogueCameraMode"]).strip().lower()
    return mode if mode in DIALOGUE_CAMERA_MODES else DEFAULT_DIALOGUE_CAMERA_CONFIG["dialogueCameraMode"]


def sanitize_dialogue_camera_config(value: dict | None = None) -> dict:
    source = _config_source(value)
    return {
        "dialogueCameraMode": get_safe_dialogue_camera_mode(source.get("dialogueCameraMode")),
        "dialogueCameraIntensity": int(
            round(
                _clamp(
                    _safe_number(
                        source.get("dialogueCameraIntensity"),
                        DEFAULT_DIALOGUE_CAMERA_CONFIG["dialogueCameraIntensity"],
                    ),
                    0,
                    100,
                )
            )
        ),
        "dialogueCameraTransitionMs": int(
            round(
                _clamp(
                    _safe_number(
                        source.get("dialogueCameraTransitionMs"),
                        DEFAULT_DIALOGUE_CAMERA_CONFIG["dialogueCameraTransitionMs"],
                    ),
                    0,
                    1600,
                )
            )
        ),
    }


def _character_focus_percent(character_state: dict | None) -> float:
    state = character_state if isinstance(character_state, dict) else {}
    position = str(state.get("position") or "center")
    base = CHARACTER_POSITION_PERCENT.get(position, CHARACTER_POSITION_PERCENT["center"])
    stage = state.get("stage") if isinstance(state.get("stage"), dict) else {}
    return _clamp(base + _safe_number(stage.get("offsetX"), 0), 8, 92)


def build_native_dialogue_camera_pose(
    *,
    active_character_id: str | None,
    visible_characters: list[dict] | tuple[dict, ...] | dict | None,
    game_ui_config: dict | None = None,
    visual_comfort_mode: str = "standard",
) -> dict:
    config = sanitize_dialogue_camera_config(game_ui_config)
    safe_active_id = str(active_character_id or "").strip()
    if isinstance(visible_characters, dict):
        states = [
            {**(state if isinstance(state, dict) else {}), "characterId": character_id}
            for character_id, state in visible_characters.items()
        ]
    else:
        states = list(visible_characters or [])
    active_character = next(
        (
            state
            for state in states
            if isinstance(state, dict)
            and str(state.get("characterId") or "").strip() == safe_active_id
            and not state.get("__ghostMode")
            and not state.get("__leaving")
        ),
        None,
    )
    motion_scale = _visual_comfort_motion_scale(visual_comfort_mode)
    active = bool(config["dialogueCameraMode"] != "off" and active_character and motion_scale > 0)
    focus_percent = _character_focus_percent(active_character) if active else 50.0
    profile = DIALOGUE_CAMERA_PROFILES[config["dialogueCameraMode"]]
    intensity = config["dialogueCameraIntensity"] / 100
    pan_percent = (
        _clamp((50 - focus_percent) * profile["panFactor"] * intensity * motion_scale, -10, 10)
        if active
        else 0.0
    )
    zoom_scale = 1 + profile["zoomBoost"] * intensity * motion_scale if active else 1.0
    transition_ms = 0 if visual_comfort_mode == "static" else round(
        config["dialogueCameraTransitionMs"] * (0.7 if visual_comfort_mode == "gentle" else 1)
    )
    return {
        "mode": config["dialogueCameraMode"],
        "active": active,
        "focusPercent": _round_pose_value(focus_percent),
        "panPercent": _round_pose_value(pan_percent),
        "zoomScale": _round_pose_value(zoom_scale),
        "transitionMs": int(transition_ms),
    }


def get_native_manual_camera_zoom_scale(effect: dict | None) -> float:
    if not isinstance(effect, dict):
        return 1.0
    action = str(effect.get("action") or "zoom_in")
    strength = str(effect.get("strength") or "medium")
    return NATIVE_MANUAL_ZOOM_SCALE.get((action, strength), 1.0)


def get_native_manual_camera_pan_percent(effect: dict | None) -> float:
    if not isinstance(effect, dict):
        return 0.0
    target = str(effect.get("target") or "center")
    strength = str(effect.get("strength") or "medium")
    return 100 * NATIVE_MANUAL_PAN_RATIO.get(target, 0.0) * NATIVE_MANUAL_PAN_STRENGTH.get(strength, 1.0)


def get_native_manual_camera_focus_percent(effect: dict | None) -> float:
    focus = str((effect or {}).get("focus") or "center")
    return NATIVE_MANUAL_FOCUS_PERCENT.get(focus, 50.0)


def build_native_stage_camera_target(
    *,
    camera_zoom: dict | None,
    camera_pan: dict | None,
    active_character_id: str | None,
    visible_characters: list[dict] | tuple[dict, ...] | dict | None,
    game_ui_config: dict | None,
    visual_comfort_mode: str,
) -> dict:
    dialogue_pose = build_native_dialogue_camera_pose(
        active_character_id=active_character_id,
        visible_characters=visible_characters,
        game_ui_config=game_ui_config,
        visual_comfort_mode=visual_comfort_mode,
    )
    manual_zoom = isinstance(camera_zoom, dict)
    manual_pan = isinstance(camera_pan, dict)
    transition_ms = 0 if visual_comfort_mode == "static" else (
        dialogue_pose["transitionMs"] if dialogue_pose["mode"] != "off" else 320
    )
    return {
        **dialogue_pose,
        "autoActive": bool(dialogue_pose["active"] and (not manual_zoom or not manual_pan)),
        "manualZoom": manual_zoom,
        "manualPan": manual_pan,
        "zoomScale": _round_pose_value(
            get_native_manual_camera_zoom_scale(camera_zoom) if manual_zoom else dialogue_pose["zoomScale"]
        ),
        "panPercent": _round_pose_value(
            get_native_manual_camera_pan_percent(camera_pan) if manual_pan else dialogue_pose["panPercent"]
        ),
        "focusPercent": _round_pose_value(
            get_native_manual_camera_focus_percent(camera_zoom) if manual_zoom else dialogue_pose["focusPercent"]
        ),
        "transitionMs": int(transition_ms),
    }


def _transition_progress(started_at_ms: int, now_ms: int, duration_ms: int) -> float:
    if int(duration_ms or 0) <= 0:
        return 1.0
    elapsed = max(0, int(now_ms or 0) - int(started_at_ms or 0))
    return _clamp(elapsed / int(duration_ms), 0.0, 1.0)


def _ease_out_cubic(progress: float) -> float:
    ratio = _clamp(progress, 0.0, 1.0)
    return 1 - pow(1 - ratio, 3)


def interpolate_native_stage_camera_pose(previous: dict, target: dict, progress: float) -> dict:
    ratio = _ease_out_cubic(progress)
    result = dict(target or {})
    for key, fallback in (("panPercent", 0.0), ("zoomScale", 1.0), ("focusPercent", 50.0)):
        previous_value = _safe_number((previous or {}).get(key), fallback)
        target_value = _safe_number((target or {}).get(key), fallback)
        result[key] = _round_pose_value(previous_value + (target_value - previous_value) * ratio)
    return result


class NativeDialogueCameraController:
    """Keep dialogue-camera handoffs smooth without growing the player entrypoint."""

    def __init__(self) -> None:
        self.context_key: tuple = ()
        self.previous_pose: dict = {"panPercent": 0.0, "zoomScale": 1.0, "focusPercent": 50.0}
        self.target_pose: dict = dict(self.previous_pose)
        self.transition_started_at_ms = 0
        self.transition_duration_ms = 0

    def _current_pose(self, now_ms: int) -> dict:
        progress = _transition_progress(
            self.transition_started_at_ms,
            now_ms,
            self.transition_duration_ms,
        )
        return interpolate_native_stage_camera_pose(self.previous_pose, self.target_pose, progress)

    def build_render_pose(
        self,
        *,
        camera_zoom: dict | None,
        camera_pan: dict | None,
        current_line: dict | None,
        visible_characters: list[dict] | tuple[dict, ...] | dict | None,
        game_ui_config: dict | None,
        visual_comfort_mode: str,
        now_ms: int,
    ) -> dict:
        active_character_id = str((current_line or {}).get("speakerId") or "").strip()
        target_pose = build_native_stage_camera_target(
            camera_zoom=camera_zoom,
            camera_pan=camera_pan,
            active_character_id=active_character_id,
            visible_characters=visible_characters,
            game_ui_config=game_ui_config,
            visual_comfort_mode=visual_comfort_mode,
        )
        context_key = (
            target_pose["mode"],
            target_pose["active"],
            target_pose["manualZoom"],
            target_pose["manualPan"],
            target_pose["panPercent"],
            target_pose["zoomScale"],
            target_pose["focusPercent"],
            target_pose["transitionMs"],
        )
        if context_key != self.context_key:
            self.previous_pose = self._current_pose(now_ms) if self.context_key else dict(self.previous_pose)
            self.target_pose = target_pose
            self.context_key = context_key
            self.transition_started_at_ms = int(now_ms)
            self.transition_duration_ms = int(target_pose["transitionMs"])
        return self._current_pose(now_ms)
