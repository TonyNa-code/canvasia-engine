from __future__ import annotations

import random
import unittest

from native_runtime.runtime_particles import (
    NativeParticleQualityController,
    build_native_particle_budget,
    build_native_particle_items,
    normalize_native_particle_effect_config,
    resize_native_particle_items,
    update_native_particle_items,
)


class NativeRuntimeParticleTests(unittest.TestCase):
    def test_normalization_handles_invalid_values_and_preserves_zero_forces(self) -> None:
        config = normalize_native_particle_effect_config(
            {
                "preset": "unknown",
                "density": "not-a-number",
                "sizeMin": 18,
                "sizeMax": 4,
                "gravityY": 0,
                "spreadX": 0,
                "color": "#123456",
                "colorAccent": [300, -4, 128],
            }
        )

        self.assertEqual(config["preset"], "snow")
        self.assertEqual(config["density"], 40)
        self.assertEqual(config["sizeMin"], 4)
        self.assertEqual(config["sizeMax"], 18)
        self.assertEqual(config["speedValue"], 0)
        self.assertEqual(config["driftValue"], 0)
        self.assertEqual(config["color"], (18, 52, 86))
        self.assertEqual(config["accentColor"], (255, 0, 128))

    def test_performance_profiles_bound_particle_pool_size(self) -> None:
        config = normalize_native_particle_effect_config(
            {"preset": "rain", "density": 240, "intensity": "heavy"}
        )
        mobile = build_native_particle_budget(config, "mobile_low")
        standard = build_native_particle_budget(config, "standard")
        high = build_native_particle_budget(config, "high_quality_pc")

        self.assertEqual(mobile["renderedCount"], 42)
        self.assertEqual(standard["renderedCount"], 180)
        self.assertEqual(high["renderedCount"], 220)
        self.assertLess(mobile["renderedCount"], standard["renderedCount"])
        self.assertLess(standard["renderedCount"], high["renderedCount"])

    def test_quality_controller_degrades_and_recovers_with_hysteresis(self) -> None:
        controller = NativeParticleQualityController("standard")
        for _ in range(55):
            controller.observe_frame(0.040)
        self.assertEqual(controller.snapshot()["qualityLevel"], "balanced")

        for _ in range(280):
            controller.observe_frame(0.010)
        self.assertEqual(controller.snapshot()["qualityLevel"], "full")

    def test_particle_pool_resizes_and_recycles_without_pygame(self) -> None:
        rng = random.Random(42)
        config = normalize_native_particle_effect_config({"preset": "snow", "density": 20})
        items = build_native_particle_items(config, 1280, 720, rng=rng)
        first_item = items[0]
        smaller = resize_native_particle_items(items, config, 1280, 720, 8, rng)
        self.assertEqual(len(smaller), 8)
        self.assertIs(smaller[0], first_item)

        smaller[0]["life"] = 0
        updated = update_native_particle_items(smaller, config, 1280, 720, 0.016, 1.0, rng)
        self.assertEqual(len(updated), 8)
        self.assertIsNot(updated[0], first_item)
        self.assertGreater(updated[0]["life"], 0)


if __name__ == "__main__":
    unittest.main()
