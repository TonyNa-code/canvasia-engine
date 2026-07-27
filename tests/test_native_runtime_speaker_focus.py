from __future__ import annotations

import unittest

from native_runtime.runtime_speaker_focus import (
    NativeSpeakerFocusController,
    build_native_speaker_focus_pose,
    get_speaker_focus_transition_progress,
    interpolate_speaker_focus_pose,
    sanitize_speaker_focus_config,
    scale_rgb_color,
)


class NativeRuntimeSpeakerFocusTests(unittest.TestCase):
    def test_controller_tracks_the_active_line_without_player_coupling(self) -> None:
        controller = NativeSpeakerFocusController()
        poses = controller.build_render_poses(
            items=[("hero", {}), ("heroine", {})],
            current_line={"speakerId": "heroine"},
            game_ui_config={"speakerFocusMode": "soft", "speakerFocusTransitionMs": 0},
            visual_comfort_mode="standard",
            now_ms=100,
        )
        self.assertEqual(poses[("hero", False)]["role"], "muted")
        self.assertEqual(poses[("heroine", False)]["role"], "active")

    def test_controller_continues_from_interrupted_focus_pose(self) -> None:
        controller = NativeSpeakerFocusController()
        options = {
            "items": [("hero", {}), ("heroine", {})],
            "game_ui_config": {
                "speakerFocusMode": "cinematic",
                "speakerFocusIntensity": 100,
                "speakerFocusTransitionMs": 240,
            },
            "visual_comfort_mode": "standard",
        }
        controller.build_render_poses(**options, current_line={"speakerId": "hero"}, now_ms=0)
        halfway = controller.build_render_poses(**options, current_line={"speakerId": "hero"}, now_ms=120)
        handoff = controller.build_render_poses(**options, current_line={"speakerId": "heroine"}, now_ms=120)
        settled = controller.build_render_poses(**options, current_line={"speakerId": "heroine"}, now_ms=400)

        self.assertEqual(
            handoff[("hero", False)]["brightnessMultiplier"],
            halfway[("hero", False)]["brightnessMultiplier"],
        )
        self.assertEqual(
            handoff[("heroine", False)]["scaleMultiplier"],
            halfway[("heroine", False)]["scaleMultiplier"],
        )
        self.assertEqual(settled[("hero", False)]["role"], "muted")
        self.assertEqual(settled[("heroine", False)]["role"], "active")
        self.assertEqual(settled[("hero", False)]["brightnessMultiplier"], 0.66)

    def test_controller_keeps_visible_and_leaving_copies_separate(self) -> None:
        controller = NativeSpeakerFocusController()
        poses = controller.build_render_poses(
            items=[("hero", {}), ("hero", {"__leaving": True}), ("heroine", {})],
            current_line={"speakerId": "hero"},
            game_ui_config={"speakerFocusMode": "soft", "speakerFocusTransitionMs": 0},
            visual_comfort_mode="standard",
            now_ms=0,
        )

        self.assertEqual(poses[("hero", False)]["role"], "active")
        self.assertEqual(poses[("hero", True)]["role"], "neutral")

    def test_focus_pose_matches_author_controls(self) -> None:
        config = sanitize_speaker_focus_config(
            {
                "speakerFocusMode": "cinematic",
                "speakerFocusIntensity": 100,
                "speakerFocusTransitionMs": 2000,
            }
        )
        muted = build_native_speaker_focus_pose(
            character_id="hero",
            active_character_id="heroine",
            visible_character_ids=["hero", "heroine"],
            game_ui_config=config,
        )
        active = build_native_speaker_focus_pose(
            character_id="heroine",
            active_character_id="heroine",
            visible_character_ids=["hero", "heroine"],
            game_ui_config=config,
        )

        self.assertEqual(config["speakerFocusTransitionMs"], 1200)
        self.assertEqual(muted["role"], "muted")
        self.assertEqual(muted["opacityMultiplier"], 0.58)
        self.assertEqual(muted["brightnessMultiplier"], 0.66)
        self.assertEqual(active["role"], "active")
        self.assertEqual(active["scaleMultiplier"], 1.04)
        self.assertEqual(active["layerBoost"], 100)

    def test_focus_transition_and_static_comfort_are_deterministic(self) -> None:
        previous_pose = build_native_speaker_focus_pose(
            character_id="hero",
            active_character_id="hero",
            visible_character_ids=["hero", "heroine"],
            game_ui_config={"speakerFocusMode": "soft", "speakerFocusIntensity": 100},
        )
        next_pose = build_native_speaker_focus_pose(
            character_id="hero",
            active_character_id="heroine",
            visible_character_ids=["hero", "heroine"],
            game_ui_config={"speakerFocusMode": "soft", "speakerFocusIntensity": 100},
        )
        halfway = interpolate_speaker_focus_pose(previous_pose, next_pose, 0.5)
        static_pose = build_native_speaker_focus_pose(
            character_id="hero",
            active_character_id="hero",
            visible_character_ids=["hero", "heroine"],
            visual_comfort_mode="static",
        )

        self.assertEqual(get_speaker_focus_transition_progress(100, 220, 240), 0.5)
        self.assertEqual(halfway["opacityMultiplier"], 0.9)
        self.assertEqual(static_pose["scaleMultiplier"], 1.0)
        self.assertEqual(static_pose["transitionMs"], 0)
        self.assertEqual(scale_rgb_color((200, 100, 50), 0.5), (100, 50, 25))

    def test_focus_is_neutral_for_narration_or_single_character(self) -> None:
        narration_pose = build_native_speaker_focus_pose(
            character_id="hero",
            active_character_id=None,
            visible_character_ids=["hero", "heroine"],
        )
        solo_pose = build_native_speaker_focus_pose(
            character_id="hero",
            active_character_id="hero",
            visible_character_ids=["hero"],
        )
        self.assertEqual(narration_pose["role"], "neutral")
        self.assertEqual(solo_pose["role"], "neutral")


if __name__ == "__main__":
    unittest.main()
