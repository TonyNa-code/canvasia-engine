from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "script_import_mapping.js"


class FrontendScriptImportMappingModuleTests(unittest.TestCase):
    def test_script_import_mapping_matches_project_assets_and_characters(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorScriptImportMapping;
            const character = {{
              id: "char_yuina",
              name: "Yuina",
              displayName: "悠奈",
              expressions: [
                {{ id: "expr_default", name: "默认" }},
                {{ id: "expr_smile", name: "Smile", tags: ["微笑"] }},
              ],
            }};
            const data = {{
              characters: [character],
              charactersById: new Map([["char_yuina", character]]),
              assetList: [
                {{ id: "bg_classroom", type: "background", name: "Classroom", fileName: "classroom.png", tags: ["教室"] }},
                {{ id: "bgm_school", type: "bgm", name: "School Theme", fileName: "school_theme.ogg" }},
                {{ id: "cg_school", type: "cg", name: "school_theme_cg.png" }},
              ],
              scenes: [
                {{ id: "scene_roof", name: "Rooftop", tags: ["天台"] }},
                {{ id: "scene_end", name: "Ending" }},
              ],
            }};
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              normalized: tools.normalizeImportedLookupText("School Theme.ogg"),
              characterByRomaji: tools.findImportedCharacterByHint(data, "yuina")?.id,
              characterByDisplayName: tools.findImportedCharacterByHint(data, "悠奈")?.id,
              expressionByTag: tools.findImportedExpressionIdByHint(data, "char_yuina", "微笑"),
              backgroundByFile: tools.findImportedAssetIdByHint(data, "classroom", ["background"]),
              bgmByName: tools.findImportedAssetIdByHint(data, "school_theme", ["bgm"]),
              typedLookupDoesNotCrossAssetTypes: tools.findImportedAssetIdByHint(data, "school_theme", ["background"]),
              sceneByName: tools.findImportedSceneIdByHint(data, "rooftop"),
              sceneByTag: tools.findImportedSceneIdByHint(data, "天台"),
              shortDuration: tools.getImportedEffectDuration(300),
              mediumDuration: tools.getImportedEffectDuration(700),
              longDuration: tools.getImportedEffectDuration(1200),
            }}));
            """
        )
        completed = subprocess.run(
            ["node", "-e", script],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertIn("findImportedAssetIdByHint", payload["keys"])
        self.assertEqual(payload["normalized"], "schooltheme")
        self.assertEqual(payload["characterByRomaji"], "char_yuina")
        self.assertEqual(payload["characterByDisplayName"], "char_yuina")
        self.assertEqual(payload["expressionByTag"], "expr_smile")
        self.assertEqual(payload["backgroundByFile"], "bg_classroom")
        self.assertEqual(payload["bgmByName"], "bgm_school")
        self.assertEqual(payload["typedLookupDoesNotCrossAssetTypes"], "")
        self.assertEqual(payload["sceneByName"], "scene_roof")
        self.assertEqual(payload["sceneByTag"], "scene_roof")
        self.assertEqual(payload["shortDuration"], "short")
        self.assertEqual(payload["mediumDuration"], "medium")
        self.assertEqual(payload["longDuration"], "long")


if __name__ == "__main__":
    unittest.main()
