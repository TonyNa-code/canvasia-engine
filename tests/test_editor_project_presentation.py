from __future__ import annotations

import unittest

from editor_project_presentation import (
    DEFAULT_DIALOG_BOX_CONFIG,
    DEFAULT_GAME_UI_CONFIG,
    build_default_dialog_box_config,
    build_default_game_ui_config,
    sanitize_dialog_box_config,
    sanitize_game_ui_config,
)
from native_runtime.runtime_player_view import DEFAULT_GAME_UI_CONFIG as NATIVE_DEFAULT_GAME_UI_CONFIG


class EditorProjectPresentationTests(unittest.TestCase):
    def test_default_builders_return_independent_nested_configs(self) -> None:
        first = build_default_game_ui_config()
        second = build_default_game_ui_config()
        first["panelFrameSlice"]["top"] = 0

        self.assertEqual(second, DEFAULT_GAME_UI_CONFIG)
        self.assertEqual(build_default_dialog_box_config(), DEFAULT_DIALOG_BOX_CONFIG)
        self.assertEqual(DEFAULT_GAME_UI_CONFIG["panelFrameSlice"]["top"], 24)

    def test_game_ui_sanitizer_preserves_runtime_presentation_controls(self) -> None:
        sanitized = sanitize_game_ui_config(
            {
                "speakerFocusMode": "cinematic",
                "speakerFocusIntensity": 140,
                "speakerFocusTransitionMs": -1,
                "dialogueCameraMode": "cinematic",
                "dialogueCameraIntensity": 72,
                "dialogueCameraTransitionMs": 680,
                "voiceReactiveMotionMode": "cinematic",
                "voiceReactiveMotionIntensity": 140,
                "voiceReactiveMotionSensitivity": -1,
                "panelFrameSlice": {"top": -1, "right": 140, "bottom": 20, "left": 18},
                "unknownField": "drop me",
            }
        )

        self.assertEqual(set(sanitized), set(DEFAULT_GAME_UI_CONFIG))
        self.assertEqual(sanitized["speakerFocusMode"], "cinematic")
        self.assertEqual(sanitized["speakerFocusIntensity"], 100)
        self.assertEqual(sanitized["speakerFocusTransitionMs"], 0)
        self.assertEqual(sanitized["dialogueCameraMode"], "cinematic")
        self.assertEqual(sanitized["dialogueCameraIntensity"], 72)
        self.assertEqual(sanitized["dialogueCameraTransitionMs"], 680)
        self.assertEqual(sanitized["voiceReactiveMotionMode"], "cinematic")
        self.assertEqual(sanitized["voiceReactiveMotionIntensity"], 100)
        self.assertEqual(sanitized["voiceReactiveMotionSensitivity"], 0)
        self.assertEqual(sanitized["panelFrameSlice"], {"top": 0, "right": 96, "bottom": 20, "left": 18})
        self.assertNotIn("unknownField", sanitized)

    def test_editor_and_native_runtime_share_presentation_defaults(self) -> None:
        keys = (
            "speakerFocusMode",
            "speakerFocusIntensity",
            "speakerFocusTransitionMs",
            "dialogueCameraMode",
            "dialogueCameraIntensity",
            "dialogueCameraTransitionMs",
            "voiceReactiveMotionMode",
            "voiceReactiveMotionIntensity",
            "voiceReactiveMotionSensitivity",
        )

        self.assertEqual(
            {key: DEFAULT_GAME_UI_CONFIG[key] for key in keys},
            {key: NATIVE_DEFAULT_GAME_UI_CONFIG[key] for key in keys},
        )

    def test_dialog_box_sanitizer_clamps_values_without_mutating_defaults(self) -> None:
        sanitized = sanitize_dialog_box_config(
            {
                "preset": "transparent",
                "shape": "capsule",
                "widthPercent": 999,
                "backgroundColor": "#ABCDEF",
                "panelAssetFit": "broken",
            }
        )

        self.assertEqual(sanitized["preset"], "transparent")
        self.assertEqual(sanitized["shape"], "capsule")
        self.assertEqual(sanitized["widthPercent"], 100)
        self.assertEqual(sanitized["backgroundColor"], "#abcdef")
        self.assertEqual(sanitized["panelAssetFit"], DEFAULT_DIALOG_BOX_CONFIG["panelAssetFit"])


if __name__ == "__main__":
    unittest.main()
