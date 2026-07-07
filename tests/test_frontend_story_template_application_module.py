from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "story_template_application.js"


class FrontendStoryTemplateApplicationModuleTests(unittest.TestCase):
    def test_story_template_application_builds_playable_blocks_without_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorStoryTemplateApplication;

            let idCounter = 0;
            const recipes = [
              {{ type: "character_show", speaker: true, fields: {{ position: "" }} }},
              {{ type: "dialogue", speaker: true, fields: {{ text: "你好，世界。" }} }},
              {{ type: "music_play", fields: {{ assetId: "bgm_1", fadeInSeconds: 1.5 }}, endAfterRecipeIndex: 3 }},
              {{
                type: "choice",
                choiceOptions: [
                  {{ text: "认真回应", effects: [{{ type: "variable_add", variableId: "affection", value: 2 }}] }},
                  {{ text: "转移话题", effects: [{{ type: "variable_set", variableId: "route", value: "common" }}] }},
                ],
              }},
              {{ type: "condition", numberVariableCondition: {{ variableId: "affection", operator: ">=", value: 2 }} }},
              {{ type: "jump", defaultJumpTarget: true }},
            ];
            const scene = {{ id: "scene_1", blocks: [] }};
            const helpers = {{
              getStoryTemplatePreset(templateId) {{
                return templateId === "playable_scene" ? {{ title: "Playable <Scene>" }} : null;
              }},
              getStoryTemplateBlockRecipes() {{
                return recipes;
              }},
              cloneScene(value) {{
                return JSON.parse(JSON.stringify(value));
              }},
              getSafeCharacterId(value) {{
                return value || "char_fallback";
              }},
              selectedCharacterId: "char_1",
              firstCharacterId: "char_fallback",
              createDefaultBlock(_sceneDraft, type) {{
                const block = {{ id: `block_${{++idCounter}}`, type }};
                if (type === "choice") {{
                  block.options = [];
                }}
                if (type === "condition") {{
                  block.branches = [];
                }}
                return block;
              }},
              getSafeExpressionId() {{
                return "smile";
              }},
              getDefaultCharacterPosition() {{
                return "center";
              }},
              createChoiceOptionId(blockId, index) {{
                return `${{blockId}}_opt_${{index}}`;
              }},
              getSafeVariableId(id, kind) {{
                if (id === "affection" && (!kind || kind === "number")) {{
                  return id;
                }}
                if (id === "route") {{
                  return id;
                }}
                return "";
              }},
              getVariableDefaultValue(id) {{
                return id === "route" ? "common" : 0;
              }},
              normalizeVariableValue(id, value) {{
                return id === "affection" ? Number(value) : String(value);
              }},
              createDefaultConditionBranches(blockId, sceneId) {{
                return [{{ id: `${{blockId}}_branch_0`, targetSceneId: sceneId, when: [] }}];
              }},
              getDefaultJumpTargetSceneId(sceneId) {{
                return `${{sceneId}}_next`;
              }},
            }};

            const blocks = tools.buildStoryTemplateBlocks(scene, "playable_scene", helpers);
            const missingBlocks = tools.buildStoryTemplateBlocks(scene, "missing", helpers);
            const summary = tools.buildStoryTemplateApplicationSummary({{ title: "Playable <Scene>" }}, blocks, {{
              getBlockLabel(type) {{
                return {{
                  character_show: "显示立绘",
                  dialogue: "台词",
                  music_play: "播放 BGM",
                  choice: "选项",
                  condition: "条件分支",
                  jump: "跳转",
                }}[type] || type;
              }},
            }});

            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              originalSceneBlockCount: scene.blocks.length,
              blocks,
              missingBlocks,
              summary,
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
        blocks = payload["blocks"]

        self.assertIn("buildStoryTemplateApplicationSummary", payload["keys"])
        self.assertIn("buildStoryTemplateBlocks", payload["keys"])
        self.assertEqual(payload["originalSceneBlockCount"], 0)
        self.assertEqual(payload["missingBlocks"], [])
        self.assertEqual(len(blocks), 6)
        self.assertEqual(blocks[0]["characterId"], "char_1")
        self.assertEqual(blocks[0]["expressionId"], "smile")
        self.assertEqual(blocks[0]["position"], "center")
        self.assertEqual(blocks[1]["speakerId"], "char_1")
        self.assertEqual(blocks[1]["expressionId"], "smile")
        self.assertEqual(blocks[1]["text"], "你好，世界。")
        self.assertEqual(blocks[2]["endMode"], "after_block")
        self.assertEqual(blocks[2]["endBlockId"], blocks[3]["id"])
        self.assertEqual(blocks[3]["options"][0]["id"], f"{blocks[3]['id']}_opt_0")
        self.assertEqual(blocks[3]["options"][0]["effects"][0]["type"], "variable_add")
        self.assertEqual(blocks[3]["options"][0]["effects"][0]["value"], 2)
        self.assertEqual(blocks[3]["options"][1]["effects"][0]["type"], "variable_set")
        self.assertEqual(blocks[3]["options"][1]["effects"][0]["value"], "common")
        self.assertEqual(blocks[4]["branches"][0]["targetSceneId"], "scene_1")
        self.assertEqual(blocks[4]["branches"][0]["when"][0]["variableId"], "affection")
        self.assertEqual(blocks[5]["targetSceneId"], "scene_1_next")
        self.assertEqual(payload["summary"]["countLabel"], "6 张卡片")
        self.assertIn("已插入模板：Playable <Scene>", payload["summary"]["message"])
        self.assertIn("显示立绘 1", payload["summary"]["typeDigest"])


if __name__ == "__main__":
    unittest.main()
