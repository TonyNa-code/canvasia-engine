from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "story_templates.js"


class FrontendStoryTemplatesModuleTests(unittest.TestCase):
    def test_story_template_helpers_work_without_browser_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorStoryTemplates;
            const result = {{
              keys: Object.keys(tools).sort(),
              presetTitles: [
                tools.getStoryTemplatePreset("playable_scene")?.title,
                tools.getStoryTemplatePreset("opening_intro")?.title,
                tools.getStoryTemplatePreset("memory_entry")?.title,
                tools.getStoryTemplatePreset("emotion_burst")?.title,
                tools.getStoryTemplatePreset("branch_choice")?.title,
                tools.getStoryTemplatePreset("scene_outro")?.title,
              ],
              playableRecipeTypes: tools.getStoryTemplateBlockRecipes("playable_scene").map((recipe) => recipe.type),
              playableChoiceTexts: tools.getStoryTemplateBlockRecipes("playable_scene").find((recipe) => recipe.type === "choice")?.choiceTexts,
              playableTypeCounts: tools.getStoryTemplateBlockTypeCounts("playable_scene"),
              playableSummary: tools.getStoryTemplateSummary("playable_scene", {{
                getBlockLabel: (type) => type === "dialogue" ? "台词" : `label:${{type}}`,
              }}),
              openingRecipeCount: tools.getStoryTemplateBlockRecipes("opening_intro").length,
              missingRecipes: tools.getStoryTemplateBlockRecipes("missing"),
              missingPreset: tools.getStoryTemplatePreset("missing"),
              templateLabels: [
                tools.getTemplateLabel("blank"),
                tools.getTemplateLabel("campus_romance"),
                tools.getTemplateLabel("custom_template"),
                tools.getTemplateLabel(null),
              ],
              exportedPresetCount: Object.keys(tools.STORY_TEMPLATE_PRESETS).length,
              exportedBlankLabel: tools.PROJECT_TEMPLATE_LABELS.blank,
            }};
            process.stdout.write(JSON.stringify(result));
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
        self.assertIn("getStoryTemplatePreset", payload["keys"])
        self.assertIn("getStoryTemplateBlockRecipes", payload["keys"])
        self.assertIn("getStoryTemplateSummary", payload["keys"])
        self.assertEqual(payload["presetTitles"], ["第一段可试玩", "开场铺垫", "进入回忆", "情绪爆点", "选项分支", "场景收尾"])
        self.assertEqual(
            payload["playableRecipeTypes"],
            [
                "background",
                "music_play",
                "character_show",
                "narration",
                "dialogue",
                "dialogue",
                "choice",
                "dialogue",
                "music_stop",
                "screen_fade",
            ],
        )
        self.assertEqual(payload["playableChoiceTexts"], ["认真回应她", "先转移话题"])
        self.assertEqual(payload["playableTypeCounts"]["dialogue"], 3)
        self.assertEqual(payload["playableTypeCounts"]["choice"], 1)
        self.assertEqual(payload["playableSummary"]["title"], "第一段可试玩")
        self.assertEqual(payload["playableSummary"]["blockCount"], 10)
        self.assertIn("台词 x 3", payload["playableSummary"]["labels"])
        self.assertEqual(payload["openingRecipeCount"], 5)
        self.assertEqual(payload["missingRecipes"], [])
        self.assertIsNone(payload["missingPreset"])
        self.assertEqual(payload["templateLabels"], ["空白项目", "校园恋爱模板", "custom_template", None])
        self.assertEqual(payload["exportedPresetCount"], 6)
        self.assertEqual(payload["exportedBlankLabel"], "空白项目")


if __name__ == "__main__":
    unittest.main()
