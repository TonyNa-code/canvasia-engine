from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def read_source(relative_path: str) -> str:
    return (ROOT_DIR / relative_path).read_text(encoding="utf-8")


class CharacterMotionContractTests(unittest.TestCase):
    def test_character_move_is_wired_across_authoring_runtime_and_exports(self) -> None:
        sources = {
            "catalog": read_source("prototype_editor/modules/story_block_catalog.js"),
            "actions": read_source("prototype_editor/modules/story_block_actions.js"),
            "editors": read_source("prototype_editor/modules/story_block_editors.js"),
            "importer": read_source("prototype_editor/modules/script_importer.js"),
            "mapping": read_source("prototype_editor/modules/script_import_mapping.js"),
            "renpy_js": read_source("prototype_editor/modules/renpy_exporter.js"),
            "renpy_py": read_source("renpy_export.py"),
            "web_player": read_source("export_player_template/player.js"),
            "native_player": read_source("native_runtime/runtime_player.py"),
            "run_editor": read_source("run_editor.py"),
        }

        self.assertIn('type: "character_move"', sources["catalog"])
        self.assertIn('"add-character-move": Object.freeze({', sources["actions"])
        self.assertIn("function renderCharacterMoveEditor", sources["editors"])
        self.assertIn('type: "character_move"', sources["importer"])
        self.assertIn('draftBlock.type === "character_move"', sources["mapping"])
        self.assertIn('type === "character_move"', sources["renpy_js"])
        self.assertIn('block_type == "character_move"', sources["renpy_py"])
        self.assertIn('case "character_move":', sources["web_player"])
        self.assertIn('block_type == "character_move"', sources["native_player"])
        self.assertIn('"runtime_character_motion.js"', sources["run_editor"])
        self.assertIn('NATIVE_RUNTIME_CHARACTER_MOTION_NAME = "runtime_character_motion.py"', sources["run_editor"])

    def test_character_motion_has_pure_helpers_and_anchored_css(self) -> None:
        web_motion = read_source("export_player_template/runtime_character_motion.js")
        native_motion = read_source("native_runtime/runtime_character_motion.py")
        web_css = read_source("export_player_template/player.css")
        editor_css = read_source("prototype_editor/styles.css")

        self.assertIn("export function buildCharacterMotionEvent", web_motion)
        self.assertIn("export function getCharacterMotionStyle", web_motion)
        self.assertIn("def build_native_character_motion_state", native_motion)
        self.assertIn("def get_native_character_render_pose", native_motion)
        self.assertIn("translate(calc(-50% + var(--sprite-offset-x))", web_css)
        self.assertIn("@keyframes player-sprite-stage-move", web_css)
        self.assertIn("translate(calc(-50% + var(--sprite-offset-x))", editor_css)
        self.assertIn("@keyframes stage-sprite-move", editor_css)


if __name__ == "__main__":
    unittest.main()
