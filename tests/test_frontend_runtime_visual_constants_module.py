from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_visual_constants.js"


class FrontendRuntimeVisualConstantsModuleTests(unittest.TestCase):
    def test_runtime_visual_constants_export_runtime_presets(self) -> None:
        script = textwrap.dedent(
            f"""
            import * as constants from {json.dumps(MODULE_PATH.as_uri())};

            process.stdout.write(JSON.stringify({{
              keyCount: Object.keys(constants).length,
              particleLabels: [
                constants.PARTICLE_PRESET_LABELS.glyphs,
                constants.PARTICLE_COMBO_PRESET_LABELS.arcane_stack,
                constants.PARTICLE_FORCE_FIELD_LABELS.orbit,
              ],
              particleDefaults: {{
                snowDensity: constants.PARTICLE_PRESET_DEFAULTS.snow.density,
                rainEmitter: constants.PARTICLE_PRESET_ADVANCED_DEFAULTS.rain.emitterShape,
                arcaneLayers: constants.PARTICLE_COMBO_PRESET_CONFIGS.arcane_stack.length,
                supportedImageTypes: constants.PARTICLE_IMAGE_ASSET_TYPES,
              }},
              visualLabels: [
                constants.SHAKE_INTENSITY_LABELS.heavy,
                constants.FLASH_COLOR_LABELS.warm,
                constants.SCREEN_FILTER_PRESET_LABELS.memory,
                constants.VIDEO_FIT_LABELS.cover,
              ],
              uiDefaults: {{
                saveShortcuts: constants.SAVE_SHORTCUT_COUNT,
                savePageSize: constants.SAVE_DIALOG_PAGE_SIZE,
                dialogPreset: constants.DEFAULT_PROJECT_DIALOG_BOX_CONFIG.preset,
                gameUiPreset: constants.DEFAULT_PROJECT_GAME_UI_CONFIG.preset,
                gameUiPresets: Object.keys(constants.PROJECT_GAME_UI_PRESETS).sort(),
                dialogPresets: Object.keys(constants.PROJECT_DIALOG_BOX_PRESETS).sort(),
              }},
            }}));
            """
        )
        completed = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertGreaterEqual(payload["keyCount"], 50)
        self.assertEqual(payload["particleLabels"], ["法阵符纹", "魔法阵叠层", "环绕中心"])
        self.assertEqual(payload["particleDefaults"]["snowDensity"], 40)
        self.assertEqual(payload["particleDefaults"]["rainEmitter"], "line")
        self.assertGreaterEqual(payload["particleDefaults"]["arcaneLayers"], 3)
        self.assertIn("ui", payload["particleDefaults"]["supportedImageTypes"])
        self.assertEqual(payload["visualLabels"], ["很强", "暖光", "暖色回忆", "铺满裁切"])
        self.assertEqual(payload["uiDefaults"]["saveShortcuts"], 3)
        self.assertEqual(payload["uiDefaults"]["savePageSize"], 6)
        self.assertEqual(payload["uiDefaults"]["dialogPreset"], "moonlight")
        self.assertEqual(payload["uiDefaults"]["gameUiPreset"], "stellar")
        self.assertIn("minimal", payload["uiDefaults"]["gameUiPresets"])
        self.assertIn("transparent", payload["uiDefaults"]["dialogPresets"])


if __name__ == "__main__":
    unittest.main()
