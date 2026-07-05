from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "scene_mood_recipes.js"


class FrontendSceneMoodRecipesModuleTests(unittest.TestCase):
    def test_scene_mood_recipes_apply_visible_editable_blocks(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorSceneMoodRecipes;
            const scene = {{
              id: "scene_a",
              chapterId: "chapter_1",
              name: "雨夜告白",
              blocks: [
                {{ id: "block_001", type: "background", assetId: "bg_rooftop" }},
                {{ id: "block_002", type: "character_show", characterId: "heroine", expressionId: "smile" }},
                {{ id: "block_003", type: "dialogue", speakerId: "heroine", text: "其实，我一直在等你。" }},
              ],
            }};
            const beforeBlockIds = scene.blocks.map((block) => block.id);
            const warm = tools.applySceneMoodRecipe(scene, "warm-confession", {{
              insertAfterBlockId: "block_002",
              bgmAssetId: "bgm_rain",
            }});
            const rain = tools.applySceneMoodRecipe(scene, "rain-memory", {{
              insertAfterBlockId: "block_003",
              bgmAssetId: "bgm_rain",
            }});
            const unknown = tools.applySceneMoodRecipe(scene, "missing-recipe");
            const emptyScene = {{ id: "empty", blocks: [] }};
            const emptyPanel = tools.renderSceneMoodRecipePanel(emptyScene, {{}});
            const panel = tools.renderSceneMoodRecipePanel(scene, {{ bgmAssetId: "bgm_rain" }});
            const suggestions = tools.getSceneMoodRecipeSuggestions(scene, {{ bgmAssetId: "bgm_rain" }}, {{ limit: 3 }});
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              beforeBlockIds,
              originalBlockIds: scene.blocks.map((block) => block.id),
              warm: {{
                applied: warm.applied,
                summary: warm.summary,
                insertIndex: warm.insertIndex,
                blockTypes: warm.blocks.map((block) => block.type),
                blockIds: warm.blocks.map((block) => block.id),
                fullOrder: warm.scene.blocks.map((block) => block.id),
                firstInserted: warm.scene.blocks[warm.insertIndex],
              }},
              rain: {{
                applied: rain.applied,
                blockTypes: rain.blocks.map((block) => block.type),
                hasBgm: rain.blocks.some((block) => block.type === "music_play" && block.assetId === "bgm_rain"),
                particle: rain.blocks.find((block) => block.type === "particle_effect"),
              }},
              unknown,
              emptyReadiness: tools.analyzeSceneMoodReadiness(emptyScene),
              suggestions: suggestions.map((item) => [item.id, item.disabled, item.tags.length]),
              panelHasAction: panel.includes('data-action="apply-scene-mood-recipe"'),
              panelHasRecipe: panel.includes("心动特写") || panel.includes("雨夜回忆"),
              emptyPanelHint: emptyPanel.includes("先写一两句正文"),
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
        self.assertIn("applySceneMoodRecipe", payload["keys"])
        self.assertIn("renderSceneMoodRecipePanel", payload["keys"])
        self.assertEqual(payload["beforeBlockIds"], ["block_001", "block_002", "block_003"])
        self.assertEqual(payload["originalBlockIds"], ["block_001", "block_002", "block_003"])
        self.assertTrue(payload["warm"]["applied"])
        self.assertIn("心动特写", payload["warm"]["summary"])
        self.assertEqual(payload["warm"]["insertIndex"], 2)
        self.assertEqual(
            payload["warm"]["blockTypes"],
            ["screen_filter", "depth_blur", "camera_zoom", "wait"],
        )
        self.assertEqual(payload["warm"]["blockIds"], ["block_004", "block_005", "block_006", "block_007"])
        self.assertEqual(payload["warm"]["fullOrder"][2], "block_004")
        self.assertEqual(payload["warm"]["firstInserted"]["type"], "screen_filter")
        self.assertTrue(payload["rain"]["applied"])
        self.assertIn("particle_effect", payload["rain"]["blockTypes"])
        self.assertTrue(payload["rain"]["hasBgm"])
        self.assertEqual(payload["rain"]["particle"]["preset"], "rain")
        self.assertFalse(payload["unknown"]["applied"])
        self.assertEqual(payload["unknown"]["reason"], "unknown_recipe")
        self.assertFalse(payload["emptyReadiness"]["canApply"])
        self.assertTrue(all(not item[1] for item in payload["suggestions"]))
        self.assertTrue(all(item[2] > 0 for item in payload["suggestions"]))
        self.assertTrue(payload["panelHasAction"])
        self.assertTrue(payload["panelHasRecipe"])
        self.assertTrue(payload["emptyPanelHint"])


if __name__ == "__main__":
    unittest.main()
