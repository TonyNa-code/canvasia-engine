from __future__ import annotations

import unittest
from pathlib import Path

from native_runtime.runtime_particles import PARTICLE_PERFORMANCE_PROFILES
from run_editor import EXPORT_PLAYER_SCRIPT_FILES, NATIVE_RUNTIME_REQUIRED_MODULE_FILES


ROOT_DIR = Path(__file__).resolve().parents[1]


class ParticleQualityContractTests(unittest.TestCase):
    def test_particle_quality_modules_are_wired_across_editor_and_export_runtimes(self) -> None:
        editor_index = (ROOT_DIR / "prototype_editor" / "index.html").read_text(encoding="utf-8")
        editor_guard = (ROOT_DIR / "prototype_editor" / "modules" / "module_guard.js").read_text(encoding="utf-8")
        editor_app = (ROOT_DIR / "prototype_editor" / "app.js").read_text(encoding="utf-8")
        web_player = (ROOT_DIR / "export_player_template" / "player.js").read_text(encoding="utf-8")
        native_player = (ROOT_DIR / "native_runtime" / "runtime_player.py").read_text(encoding="utf-8")
        native_bundle_names = {target_name for _source, target_name in NATIVE_RUNTIME_REQUIRED_MODULE_FILES}

        self.assertIn("./modules/particle_performance.js", editor_index)
        self.assertIn("CanvasiaEditorParticlePerformance", editor_guard)
        self.assertIn("buildParticlePerformanceReport", editor_app)
        self.assertIn("runtime_particle_quality.js", EXPORT_PLAYER_SCRIPT_FILES)
        self.assertIn("runtime_particle_renderer.js", EXPORT_PLAYER_SCRIPT_FILES)
        self.assertIn('from "./runtime_particle_quality.js"', web_player)
        self.assertIn('from "./runtime_particle_renderer.js"', web_player)
        self.assertIn("createAdaptiveParticleQualityController", web_player)
        self.assertIn("runtime_particles.py", native_bundle_names)
        self.assertIn("NativeParticleQualityController", native_player)
        self.assertIn("update_native_particle_items", native_player)

    def test_native_profiles_keep_the_shared_cross_runtime_budget_contract(self) -> None:
        self.assertEqual(
            set(PARTICLE_PERFORMANCE_PROFILES),
            {"mobile_low", "web", "standard", "high_quality_pc"},
        )
        self.assertEqual(PARTICLE_PERFORMANCE_PROFILES["mobile_low"]["maxTotal"], 84)
        self.assertEqual(PARTICLE_PERFORMANCE_PROFILES["web"]["maxTotal"], 144)
        self.assertEqual(PARTICLE_PERFORMANCE_PROFILES["standard"]["maxTotal"], 260)
        self.assertEqual(PARTICLE_PERFORMANCE_PROFILES["high_quality_pc"]["maxTotal"], 420)


if __name__ == "__main__":
    unittest.main()
