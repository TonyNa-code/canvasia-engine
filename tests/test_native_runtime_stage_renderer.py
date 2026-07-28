from __future__ import annotations

import unittest
from types import SimpleNamespace

from native_runtime.runtime_stage_renderer import (
    DEPTH_BLUR_ALPHA,
    SCREEN_FILTER_WASH,
    SHAKE_DISTANCE,
    get_native_stage_shake_offset,
    project_native_scene3d_grid_point,
)


class NativeRuntimeStageRendererTests(unittest.TestCase):
    def test_stage_shake_respects_disabled_and_static_comfort_modes(self) -> None:
        runtime = SimpleNamespace(
            screen_shake_effect=None,
            runtime_settings={"visualComfort": "standard"},
            runtime_elapsed_seconds=0.25,
        )
        self.assertEqual(get_native_stage_shake_offset(runtime), (0, 0))

        runtime.screen_shake_effect = {"intensity": "heavy"}
        runtime.runtime_settings["visualComfort"] = "static"
        self.assertEqual(get_native_stage_shake_offset(runtime), (0, 0))

        runtime.runtime_settings["visualComfort"] = "standard"
        self.assertNotEqual(get_native_stage_shake_offset(runtime), (0, 0))

    def test_scene3d_projection_is_deterministic_and_centered(self) -> None:
        runtime = SimpleNamespace(scene3d_preview_yaw=0, scene3d_preview_pitch=30)
        center = project_native_scene3d_grid_point(runtime, 0, 0, 400, 300, 42)
        right = project_native_scene3d_grid_point(runtime, 2, 0, 400, 300, 42)

        self.assertEqual(center, (400, 300))
        self.assertGreater(right[0], center[0])
        self.assertEqual(right[1], center[1])

    def test_stage_effect_catalogs_keep_authoring_options_in_sync(self) -> None:
        self.assertEqual(set(SHAKE_DISTANCE), {"light", "medium", "heavy"})
        self.assertEqual(set(SCREEN_FILTER_WASH), {"memory", "mono", "dream", "cold"})
        self.assertEqual(set(DEPTH_BLUR_ALPHA), {"soft", "medium", "strong"})


if __name__ == "__main__":
    unittest.main()
