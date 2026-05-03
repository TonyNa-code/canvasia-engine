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
            "./modules/asset_catalog.js",
            "./modules/editor_mode.js",
            "./modules/release_version.js",
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
