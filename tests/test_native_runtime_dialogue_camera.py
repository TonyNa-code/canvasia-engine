from __future__ import annotations

import unittest

from native_runtime.runtime_dialogue_camera import (
    NativeDialogueCameraController,
    build_native_dialogue_camera_pose,
    build_native_stage_camera_target,
    sanitize_dialogue_camera_config,
)


class NativeRuntimeDialogueCameraTests(unittest.TestCase):
    def test_config_and_pose_match_author_controls(self) -> None:
        config = sanitize_dialogue_camera_config(
            {
                "dialogueCameraMode": "broken",
                "dialogueCameraIntensity": 999,
                "dialogueCameraTransitionMs": -20,
            }
        )
        pose = build_native_dialogue_camera_pose(
            active_character_id="hero",
            visible_characters={
                "hero": {"position": "left", "stage": {"offsetX": 4}},
                "heroine": {"position": "right"},
            },
            game_ui_config={"dialogueCameraMode": "soft", "dialogueCameraIntensity": 50},
        )

        self.assertEqual(config, {
            "dialogueCameraMode": "soft",
            "dialogueCameraIntensity": 100,
            "dialogueCameraTransitionMs": 0,
        })
        self.assertTrue(pose["active"])
        self.assertEqual(pose["focusPercent"], 28)
        self.assertEqual(pose["panPercent"], 1.65)
        self.assertEqual(pose["zoomScale"], 1.011)

    def test_manual_camera_overrides_only_its_axis(self) -> None:
        target = build_native_stage_camera_target(
            camera_zoom={"action": "zoom_in", "strength": "medium", "focus": "left"},
            camera_pan=None,
            active_character_id="hero",
            visible_characters={"hero": {"position": "left"}, "heroine": {"position": "right"}},
            game_ui_config={"dialogueCameraMode": "cinematic", "dialogueCameraIntensity": 100},
            visual_comfort_mode="standard",
        )

        self.assertTrue(target["autoActive"])
        self.assertEqual(target["zoomScale"], 1.085)
        self.assertEqual(target["focusPercent"], 28)
        self.assertEqual(target["panPercent"], 7.28)

    def test_static_comfort_disables_automatic_motion(self) -> None:
        target = build_native_stage_camera_target(
            camera_zoom=None,
            camera_pan=None,
            active_character_id="hero",
            visible_characters={"hero": {"position": "left"}},
            game_ui_config={"dialogueCameraMode": "cinematic", "dialogueCameraIntensity": 100},
            visual_comfort_mode="static",
        )

        self.assertFalse(target["active"])
        self.assertEqual(target["zoomScale"], 1)
        self.assertEqual(target["panPercent"], 0)
        self.assertEqual(target["transitionMs"], 0)

    def test_controller_continues_from_an_interrupted_handoff(self) -> None:
        controller = NativeDialogueCameraController()
        options = {
            "camera_zoom": None,
            "camera_pan": None,
            "visible_characters": {
                "hero": {"position": "left"},
                "heroine": {"position": "right"},
            },
            "game_ui_config": {
                "dialogueCameraMode": "cinematic",
                "dialogueCameraIntensity": 100,
                "dialogueCameraTransitionMs": 400,
            },
            "visual_comfort_mode": "standard",
        }
        controller.build_render_pose(**options, current_line={"speakerId": "hero"}, now_ms=0)
        halfway = controller.build_render_pose(**options, current_line={"speakerId": "hero"}, now_ms=200)
        handoff = controller.build_render_pose(**options, current_line={"speakerId": "heroine"}, now_ms=200)
        settled = controller.build_render_pose(**options, current_line={"speakerId": "heroine"}, now_ms=700)

        self.assertEqual(handoff["panPercent"], halfway["panPercent"])
        self.assertEqual(handoff["zoomScale"], halfway["zoomScale"])
        self.assertAlmostEqual(settled["panPercent"], -7.28, places=3)
        self.assertAlmostEqual(settled["zoomScale"], 1.05, places=3)

    def test_narration_returns_to_neutral_framing(self) -> None:
        pose = build_native_dialogue_camera_pose(
            active_character_id=None,
            visible_characters={"hero": {"position": "left"}},
        )
        self.assertFalse(pose["active"])
        self.assertEqual(pose["focusPercent"], 50)
        self.assertEqual(pose["panPercent"], 0)


if __name__ == "__main__":
    unittest.main()
