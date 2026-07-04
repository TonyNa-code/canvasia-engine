from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "story_block_catalog.js"


class FrontendStoryBlockCatalogModuleTests(unittest.TestCase):
    def test_story_block_catalog_helpers_work_without_browser_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorStoryBlockCatalog;
            const result = {{
              keys: Object.keys(tools).sort(),
              labels: [
                tools.getBlockLabel("dialogue"),
                tools.getBlockLabel("particle_effect"),
                tools.getBlockLabel("custom_block"),
                tools.getBlockLabel(null),
              ],
              compactLabels: [
                tools.getCompactBlockLabel("music_play"),
                tools.getCompactBlockLabel("screen_shake"),
                tools.getCompactBlockLabel("custom_block"),
              ],
              definitions: [
                tools.getStoryBlockDefinition("video_play"),
                tools.getStoryBlockDefinition("missing"),
              ],
              knownTypes: tools.getKnownBlockTypes(),
              knownChecks: [
                tools.isKnownStoryBlockType("dialogue"),
                tools.isKnownStoryBlockType("unknown_card"),
              ],
              tagTypes: {{
                text: tools.getTimelineTextBlockTypes(),
                visual: tools.getTimelineVisualBeatBlockTypes(),
                audio: tools.getTimelineAudioBeatBlockTypes(),
                effects: tools.getEffectBlockTypes(),
                runtimeVisualEffects: tools.getRuntimeVisualEffectBlockTypes(),
                storyContent: tools.getStoryContentBlockTypes(),
                localizable: tools.getLocalizableBlockTypes(),
              }},
              runtimeRows: tools.getRuntimeCapabilityRows(),
              safeModes: [
                tools.getSafeMusicEndMode("scene_end"),
                tools.getSafeMusicEndMode("bad"),
                tools.getSafeMusicEndMode(null),
              ],
              musicLabels: [
                tools.getMusicEndModeLabel("after_block"),
                tools.getMusicEndModeLabel("bad"),
              ],
              optionMarkup: tools.renderMusicEndModeOptions("scene_end"),
              escapedMarkup: tools.renderMusicEndModeOptions("until_next_music", {{
                escapeHtml: (value) => String(value).replace(/播/g, "&#25773;"),
              }}),
              ids: [
                tools.createChoiceOptionId("block_001", 0),
                tools.createChoiceOptionId("block_001", 1),
                tools.createConditionBranchId("block_001", 0),
              ],
              defaultChoiceOptions: tools.createDefaultChoiceOptions("block_001", {{ targetSceneId: "scene_a" }}),
              defaultChoiceEffects: [
                tools.createDefaultChoiceEffect({{ numberVariableId: "var_affection" }}),
                tools.createDefaultChoiceEffect({{ variableId: "var_route", value: "common" }}),
              ],
              defaultCondition: {{
                rule: tools.createDefaultConditionRule({{ variableId: "var_affection", operator: ">=", value: 3 }}),
                branch: tools.createDefaultConditionBranch("block_001", 2, {{
                  rule: tools.createDefaultConditionRule({{ variableId: "var_flag", operator: "==", value: true }}),
                  targetSceneId: "scene_b",
                }}),
                branches: tools.createDefaultConditionBranches("block_002", {{ targetSceneId: "scene_c" }}),
              }},
              choiceContinueTarget: tools.CHOICE_CONTINUE_TARGET,
              continueChecks: [
                tools.isChoiceContinueTarget("__continue__"),
                tools.isChoiceContinueTarget("scene_a"),
              ],
              exportedLabels: tools.BLOCK_LABELS,
              exportedMusicLabels: tools.MUSIC_END_MODE_LABELS,
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
        self.assertIn("getBlockLabel", payload["keys"])
        self.assertIn("getStoryBlockDefinition", payload["keys"])
        self.assertIn("getKnownBlockTypes", payload["keys"])
        self.assertIn("isKnownStoryBlockType", payload["keys"])
        self.assertIn("getRuntimeCapabilityRows", payload["keys"])
        self.assertIn("isChoiceContinueTarget", payload["keys"])
        self.assertIn("renderMusicEndModeOptions", payload["keys"])
        self.assertEqual(payload["labels"], ["台词", "粒子特效", "custom_block", "步骤"])
        self.assertEqual(payload["compactLabels"], ["播放 BGM", "震动", "custom_block"])
        self.assertEqual(payload["definitions"][0]["group"], "视频")
        self.assertEqual(payload["definitions"][0]["nativeStatus"], "partial")
        self.assertIsNone(payload["definitions"][1])
        self.assertIn("dialogue", payload["knownTypes"])
        self.assertIn("condition", payload["knownTypes"])
        self.assertEqual(payload["knownChecks"], [True, False])
        self.assertIn("dialogue", payload["tagTypes"]["text"])
        self.assertIn("background", payload["tagTypes"]["visual"])
        self.assertIn("video_play", payload["tagTypes"]["audio"])
        self.assertIn("particle_effect", payload["tagTypes"]["effects"])
        self.assertIn("screen_fade", payload["tagTypes"]["runtimeVisualEffects"])
        self.assertIn("wait", payload["tagTypes"]["storyContent"])
        self.assertIn("choice", payload["tagTypes"]["localizable"])
        self.assertIn("credits_roll", payload["tagTypes"]["localizable"])
        self.assertGreaterEqual(len(payload["runtimeRows"]), 20)
        self.assertTrue(any(row["type"] == "wait" and row["nativeStatus"] == "full" for row in payload["runtimeRows"]))
        self.assertEqual(payload["safeModes"], ["scene_end", "until_next_music", "until_next_music"])
        self.assertEqual(payload["musicLabels"], ["播到指定卡片后", "播到下一首或停止卡"])
        self.assertIn('<option value="scene_end" selected>', payload["optionMarkup"])
        self.assertIn('<option value="until_next_music" ', payload["optionMarkup"])
        self.assertIn("&#25773;到下一首或停止卡", payload["escapedMarkup"])
        self.assertEqual(payload["ids"], ["block_001_option_1", "block_001_option_2", "block_001_branch_1"])
        self.assertEqual(payload["defaultChoiceOptions"], [
            {"id": "block_001_option_1", "text": "第一个选项", "gotoSceneId": "scene_a", "effects": []},
            {"id": "block_001_option_2", "text": "第二个选项", "gotoSceneId": "scene_a", "effects": []},
        ])
        self.assertEqual(payload["defaultChoiceEffects"], [
            {"type": "variable_add", "variableId": "var_affection", "value": 1},
            {"type": "variable_set", "variableId": "var_route", "value": "common"},
        ])
        self.assertEqual(payload["defaultCondition"]["rule"], {"variableId": "var_affection", "operator": ">=", "value": 3})
        self.assertEqual(payload["defaultCondition"]["branch"], {
            "id": "block_001_branch_3",
            "when": [{"variableId": "var_flag", "operator": "==", "value": True}],
            "gotoSceneId": "scene_b",
        })
        self.assertEqual(payload["defaultCondition"]["branches"], [
            {"id": "block_002_branch_1", "when": [{"variableId": "", "operator": "=="}], "gotoSceneId": "scene_c"}
        ])
        self.assertEqual(payload["choiceContinueTarget"], "__continue__")
        self.assertEqual(payload["continueChecks"], [True, False])
        self.assertEqual(payload["exportedLabels"]["video_play"], "播放视频")
        self.assertEqual(payload["exportedMusicLabels"]["after_block"], "播到指定卡片后")


if __name__ == "__main__":
    unittest.main()
