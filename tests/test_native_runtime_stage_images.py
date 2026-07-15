from __future__ import annotations

import unittest

from native_runtime.runtime_stage_images import (
    apply_native_stage_image_block,
    get_native_stage_image_render_pose,
    get_safe_stage_image_transform,
    is_native_stage_image_motion_complete,
)


class NativeRuntimeStageImagesTests(unittest.TestCase):
    def test_show_move_hide_preserve_asset_and_interpolate_pose(self) -> None:
        shown = apply_native_stage_image_block(
            {},
            {
                "action": "show",
                "layerId": "letter",
                "assetId": "letter_png",
                "plane": "front",
                "position": "center",
                "transform": {"width": 60, "opacity": 90, "rotation": 12, "layer": 3, "flipX": True},
                "durationMs": 800,
                "easing": "ease_in_out",
            },
            100,
        )
        self.assertEqual(shown["motion"]["mode"], "show")
        middle = get_native_stage_image_render_pose(shown["visibleImages"]["letter"], shown["motion"], 500)
        self.assertGreater(middle["transform"]["opacity"], 0)
        self.assertLess(middle["transform"]["opacity"], 90)

        moved = apply_native_stage_image_block(
            shown["visibleImages"],
            {
                "action": "update",
                "layerId": "letter",
                "position": "right",
                "transform": {"width": 42, "offsetX": -12, "opacity": 75, "layer": -2},
                "durationMs": 600,
            },
            1000,
        )
        self.assertEqual(moved["motion"]["mode"], "move")
        self.assertEqual(moved["visibleImages"]["letter"]["assetId"], "letter_png")
        self.assertEqual(moved["visibleImages"]["letter"]["transform"]["rotation"], 12)
        self.assertTrue(moved["visibleImages"]["letter"]["transform"]["flipX"])
        moved_pose = get_native_stage_image_render_pose(moved["visibleImages"]["letter"], moved["motion"], 1300)
        self.assertGreater(moved_pose["positionRatio"], 0.5)
        self.assertLess(moved_pose["positionRatio"], 0.76)

        hidden = apply_native_stage_image_block(
            moved["visibleImages"],
            {"action": "hide", "layerId": "letter", "durationMs": 300},
            2000,
        )
        self.assertEqual(hidden["visibleImages"], {})
        self.assertEqual(hidden["motion"]["mode"], "hide")
        self.assertIsNotNone(hidden["leavingState"])
        self.assertFalse(is_native_stage_image_motion_complete(hidden["motion"], 2299))
        self.assertTrue(is_native_stage_image_motion_complete(hidden["motion"], 2300))

    def test_transform_limits_match_editor_and_web_runtime(self) -> None:
        transform = get_safe_stage_image_transform(
            {"offsetX": -999, "offsetY": 999, "width": 999, "opacity": -5, "rotation": 999, "layer": 99}
        )
        self.assertEqual(transform["offsetX"], -80)
        self.assertEqual(transform["offsetY"], 70)
        self.assertEqual(transform["width"], 180)
        self.assertEqual(transform["opacity"], 0)
        self.assertEqual(transform["rotation"], 180)
        self.assertEqual(transform["layer"], 20)


if __name__ == "__main__":
    unittest.main()
