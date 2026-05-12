from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
EDITOR_DIR = ROOT_DIR / "prototype_editor"
INDEX_PATH = EDITOR_DIR / "index.html"
SCRIPT_SRC_PATTERN = re.compile(r"<script\b[^>]*\bsrc=[\"']([^\"']+)[\"'][^>]*>", re.IGNORECASE)


class FrontendEntrypointModuleTests(unittest.TestCase):
    def test_editor_modules_are_loaded_before_app_entrypoint(self) -> None:
        html = INDEX_PATH.read_text(encoding="utf-8")
        scripts = SCRIPT_SRC_PATTERN.findall(html)

        required_scripts = [
            "./modules/story_block_catalog.js",
            "./modules/story_templates.js",
            "./modules/editor_common.js",
            "./modules/variables.js",
            "./modules/project_settings.js",
            "./modules/system_dialog.js",
            "./modules/ui_theme.js",
            "./modules/preview_save.js",
            "./modules/recent_workspace.js",
            "./modules/editor_filters.js",
            "./modules/script_readability.js",
            "./modules/script_voice.js",
            "./modules/visual_effects.js",
            "./modules/particle_effects.js",
            "./modules/project_history.js",
            "./modules/asset_catalog.js",
            "./modules/openai_asset_generator.js",
            "./modules/beginner_tutorial.js",
            "./modules/creative_assistant.js",
            "./modules/editor_mode.js",
            "./modules/release_version.js",
            "./modules/project_doctor.js",
            "./modules/project_milestones.js",
            "./modules/release_control.js",
            "./app.js",
        ]
        for script in required_scripts:
            self.assertIn(script, scripts)

        for module_script in required_scripts[:-1]:
            module_path = EDITOR_DIR / module_script.removeprefix("./")
            self.assertTrue(module_path.is_file(), f"Missing editor module: {module_path}")

        app_index = scripts.index("./app.js")
        for module_script in required_scripts[:-1]:
            self.assertLess(
                scripts.index(module_script),
                app_index,
                f"{module_script} must load before app.js",
            )


if __name__ == "__main__":
    unittest.main()
