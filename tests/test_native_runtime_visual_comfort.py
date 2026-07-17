from __future__ import annotations

import unittest

from native_runtime.runtime_visual_comfort import (
    get_safe_visual_comfort_mode,
    get_visual_comfort_summary,
    scale_visual_flash,
    scale_visual_motion,
    scale_visual_transition_ms,
)


class NativeRuntimeVisualComfortTests(unittest.TestCase):
    def test_profiles_match_runtime_effect_expectations(self) -> None:
        self.assertEqual(get_safe_visual_comfort_mode("unknown"), "standard")
        self.assertEqual(get_safe_visual_comfort_mode("GENTLE"), "gentle")
        self.assertAlmostEqual(scale_visual_motion(12, "gentle"), 4.2)
        self.assertAlmostEqual(scale_visual_flash(0.8, "gentle"), 0.24)
        self.assertEqual(scale_visual_transition_ms(600, "gentle"), 330)
        self.assertEqual(scale_visual_transition_ms(600, "static"), 0)
        self.assertEqual(scale_visual_motion("bad", "standard", 8), 8)
        self.assertTrue(get_visual_comfort_summary("static")["disablesTransientEffects"])


if __name__ == "__main__":
    unittest.main()
