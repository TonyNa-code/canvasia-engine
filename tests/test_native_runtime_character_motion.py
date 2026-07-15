from __future__ import annotations

import unittest

from native_runtime.runtime_character_motion import (
    build_native_character_motion_state,
    get_native_character_motion_progress,
    get_native_character_render_pose,
    is_native_character_motion_complete,
)


class NativeRuntimeCharacterMotionTests(unittest.TestCase):
    def test_character_motion_interpolates_position_stage_and_expression(self) -> None:
        previous = {
            "characterId": "hero",
            "expressionId": "neutral",
            "position": "left",
            "stage": {"offsetX": 0, "offsetY": 10, "scale": 80, "opacity": 60, "layer": 1, "flipX": False},
        }
        block = {
            "characterId": "hero",
            "expressionId": "smile",
            "position": "right",
            "stage": {"offsetX": 10, "offsetY": -10, "scale": 120, "opacity": 100, "layer": 4, "flipX": True},
            "durationMs": 1000,
            "easing": "linear",
        }
        motion = build_native_character_motion_state(previous, block, 100)
        pose = get_native_character_render_pose(motion["targetState"], motion, 600)

        self.assertAlmostEqual(get_native_character_motion_progress(motion, 600), 0.5)
        self.assertAlmostEqual(pose["positionRatio"], 0.5)
        self.assertEqual(pose["stage"]["offsetX"], 5)
        self.assertEqual(pose["stage"]["offsetY"], 0)
        self.assertEqual(pose["stage"]["scale"], 100)
        self.assertEqual(pose["stage"]["opacity"], 80)
        self.assertEqual(pose["stage"]["layer"], 4)
        self.assertEqual(pose["expressionId"], "smile")
        self.assertTrue(pose["stage"]["flipX"])
        self.assertFalse(is_native_character_motion_complete(motion, 1099))
        self.assertTrue(is_native_character_motion_complete(motion, 1100))

    def test_character_motion_clamps_unsafe_values(self) -> None:
        motion = build_native_character_motion_state(
            {"characterId": "hero", "position": "unknown", "stage": {}},
            {
                "characterId": "hero",
                "position": "missing",
                "durationMs": 99999,
                "easing": "warp",
                "stage": {"offsetX": 999, "scale": 1, "opacity": -2},
            },
            0,
        )
        self.assertEqual(motion["durationMs"], 10000)
        self.assertEqual(motion["easing"], "ease_out")
        self.assertEqual(motion["targetState"]["position"], "center")
        self.assertEqual(motion["targetState"]["stage"]["offsetX"], 60)
        self.assertEqual(motion["targetState"]["stage"]["scale"], 45)
        self.assertEqual(motion["targetState"]["stage"]["opacity"], 0)


if __name__ == "__main__":
    unittest.main()
