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
                tools.getStoryTemplatePreset("op_movie_hook")?.title,
                tools.getStoryTemplatePreset("daily_conversation")?.title,
                tools.getStoryTemplatePreset("affection_choice")?.title,
                tools.getStoryTemplatePreset("climax_sequence")?.title,
                tools.getStoryTemplatePreset("ending_credits")?.title,
                tools.getStoryTemplatePreset("mystery_clue")?.title,
                tools.getStoryTemplatePreset("relationship_reveal")?.title,
                tools.getStoryTemplatePreset("branch_merge")?.title,
              ],
              playableRecipeTypes: tools.getStoryTemplateBlockRecipes("playable_scene").map((recipe) => recipe.type),
              playableChoiceTexts: tools.getStoryTemplateBlockRecipes("playable_scene").find((recipe) => recipe.type === "choice")?.choiceTexts,
              playableTypeCounts: tools.getStoryTemplateBlockTypeCounts("playable_scene"),
              playableSummary: tools.getStoryTemplateSummary("playable_scene", {{
                getBlockLabel: (type) => type === "dialogue" ? "台词" : `label:${{type}}`,
              }}),
              panelItems: tools.getStoryTemplatePanelItems(),
              dailyRecipe: tools.getStoryTemplateBlockRecipes("daily_conversation"),
              affectionRecipe: tools.getStoryTemplateBlockRecipes("affection_choice"),
              mysteryRecipe: tools.getStoryTemplateBlockRecipes("mystery_clue"),
              relationshipRecipe: tools.getStoryTemplateBlockRecipes("relationship_reveal"),
              branchMergeRecipe: tools.getStoryTemplateBlockRecipes("branch_merge"),
              climaxSummary: tools.getStoryTemplateSummary("climax_sequence", {{
                getBlockLabel: (type) => type,
              }}),
              branchMergeSummary: tools.getStoryTemplateSummary("branch_merge", {{
                getBlockLabel: (type) => type,
              }}),
              variableRequirements: {{
                playable: tools.getStoryTemplateVariableRequirement("playable_scene"),
                affection: tools.getStoryTemplateVariableRequirement("affection_choice"),
                daily: tools.getStoryTemplateVariableRequirement("daily_conversation"),
                mystery: tools.getStoryTemplateVariableRequirement("mystery_clue"),
                relationship: tools.getStoryTemplateVariableRequirement("relationship_reveal"),
                branchMerge: tools.getStoryTemplateVariableRequirement("branch_merge"),
              }},
              openingRecipeCount: tools.getStoryTemplateBlockRecipes("opening_intro").length,
              missingRecipes: tools.getStoryTemplateBlockRecipes("missing"),
              missingPreset: tools.getStoryTemplatePreset("missing"),
              registryHealth: tools.getStoryTemplateRegistryHealth(),
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
        self.assertIn("getStoryTemplatePanelItems", payload["keys"])
        self.assertIn("getStoryTemplateRegistryHealth", payload["keys"])
        self.assertEqual(payload["presetTitles"], [
            "第一段可试玩",
            "开场铺垫",
            "进入回忆",
            "情绪爆点",
            "选项分支",
            "场景收尾",
            "OP 前导",
            "日常对话节奏",
            "好感度选项",
            "高潮演出段",
            "ED 与片尾",
            "悬念线索",
            "关系揭露",
            "分支汇合",
        ])
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
        self.assertEqual(payload["panelItems"][0]["templateId"], "playable_scene")
        self.assertEqual(payload["panelItems"][0]["tone"], "hero")
        self.assertEqual([item["templateId"] for item in payload["panelItems"]], [
            "playable_scene",
            "opening_intro",
            "memory_entry",
            "emotion_burst",
            "branch_choice",
            "scene_outro",
            "op_movie_hook",
            "daily_conversation",
            "affection_choice",
            "climax_sequence",
            "ending_credits",
            "mystery_clue",
            "relationship_reveal",
            "branch_merge",
        ])
        daily_music = next(recipe for recipe in payload["dailyRecipe"] if recipe["type"] == "music_play")
        self.assertEqual(daily_music["endAfterRecipeIndex"], 6)
        affection_choice = next(recipe for recipe in payload["affectionRecipe"] if recipe["type"] == "choice")
        self.assertEqual(affection_choice["choiceOptions"][0]["gotoSceneId"], "__continue__")
        self.assertEqual(affection_choice["choiceOptions"][0]["effects"][0]["type"], "variable_add")
        self.assertEqual(affection_choice["choiceOptions"][0]["effects"][0]["value"], 2)
        mystery_choice = next(recipe for recipe in payload["mysteryRecipe"] if recipe["type"] == "choice")
        self.assertEqual(mystery_choice["choiceOptions"][0]["text"], "把线索收起来")
        self.assertEqual(mystery_choice["choiceOptions"][0]["effects"][0]["value"], 1)
        relationship_condition = next(recipe for recipe in payload["relationshipRecipe"] if recipe["type"] == "condition")
        relationship_character_show = next(recipe for recipe in payload["relationshipRecipe"] if recipe["type"] == "character_show")
        self.assertEqual(relationship_character_show["fields"]["position"], "center")
        self.assertEqual(relationship_condition["numberVariableCondition"]["operator"], ">=")
        self.assertEqual(relationship_condition["numberVariableCondition"]["value"], 2)
        branch_merge_jump = payload["branchMergeRecipe"][-1]
        self.assertEqual(branch_merge_jump["type"], "jump")
        self.assertTrue(branch_merge_jump["defaultJumpTarget"])
        self.assertEqual(payload["climaxSummary"]["blockCount"], 8)
        self.assertIn("depth_blur x 2", payload["climaxSummary"]["labels"])
        self.assertEqual(payload["branchMergeSummary"]["blockCount"], 5)
        self.assertIn("choice", payload["branchMergeSummary"]["labels"])
        self.assertFalse(payload["variableRequirements"]["playable"]["requiresAny"])
        self.assertTrue(payload["variableRequirements"]["affection"]["requiresAny"])
        self.assertTrue(payload["variableRequirements"]["affection"]["requiresNumber"])
        self.assertFalse(payload["variableRequirements"]["daily"]["requiresAny"])
        self.assertTrue(payload["variableRequirements"]["mystery"]["requiresAny"])
        self.assertTrue(payload["variableRequirements"]["mystery"]["requiresNumber"])
        self.assertTrue(payload["variableRequirements"]["relationship"]["requiresAny"])
        self.assertTrue(payload["variableRequirements"]["relationship"]["requiresNumber"])
        self.assertTrue(payload["variableRequirements"]["branchMerge"]["requiresAny"])
        self.assertTrue(payload["variableRequirements"]["branchMerge"]["requiresNumber"])
        self.assertEqual(payload["openingRecipeCount"], 5)
        self.assertEqual(payload["missingRecipes"], [])
        self.assertIsNone(payload["missingPreset"])
        self.assertTrue(payload["registryHealth"]["isHealthy"])
        self.assertEqual(payload["registryHealth"]["issueCount"], 0)
        self.assertEqual(len(payload["registryHealth"]["presetIds"]), 14)
        self.assertEqual(payload["registryHealth"]["missingRecipeIds"], [])
        self.assertEqual(payload["registryHealth"]["duplicatePanelIds"], [])
        self.assertEqual(payload["registryHealth"]["panelIds"][-3:], [
            "mystery_clue",
            "relationship_reveal",
            "branch_merge",
        ])
        self.assertEqual(payload["templateLabels"], ["空白项目", "校园恋爱模板", "custom_template", None])
        self.assertEqual(payload["exportedPresetCount"], 14)
        self.assertEqual(payload["exportedBlankLabel"], "空白项目")


if __name__ == "__main__":
    unittest.main()
