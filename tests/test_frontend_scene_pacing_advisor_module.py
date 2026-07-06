from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
CATALOG_MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "story_block_catalog.js"
READABILITY_MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "script_readability.js"
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "scene_pacing_advisor.js"


class FrontendScenePacingAdvisorModuleTests(unittest.TestCase):
    def test_scene_pacing_advisor_scores_scene_rhythm_and_actions(self) -> None:
        long_text = "这是一句非常长的对白。" * 35
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(CATALOG_MODULE_PATH))}, "utf8"), context);
            vm.runInContext(fs.readFileSync({json.dumps(str(READABILITY_MODULE_PATH))}, "utf8"), context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorScenePacingAdvisor;
            const matureScene = {{
              id: "mature",
              blocks: [
                {{ type: "background", assetId: "bg_classroom" }},
                {{ type: "music_play", assetId: "bgm_theme" }},
                {{ type: "dialogue", text: "今天也辛苦了。", voiceAssetId: "voice_1" }},
                {{ type: "wait", durationSeconds: 0.4 }},
                {{ type: "dialogue", text: "不过，还没到结束的时候。", voiceAssetId: "voice_2" }},
                {{
                  type: "choice",
                  options: [
                    {{ text: "继续调查", gotoSceneId: "scene_next", effects: [{{ type: "variable_add", value: 1 }}] }},
                    {{ text: "先回宿舍", gotoSceneId: "scene_dorm" }}
                  ],
                }},
                {{ type: "screen_fade", action: "fade_out" }},
                {{ type: "jump", targetSceneId: "scene_next" }},
              ],
            }};
            const roughScene = {{
              id: "rough",
              blocks: [
                {{ type: "dialogue", text: {json.dumps(long_text)} }},
                {{ type: "dialogue", text: "第二句。" }},
                {{ type: "dialogue", text: "第二句。" }},
                {{ type: "dialogue", text: "第三句。" }},
                {{ type: "dialogue", text: "第四句。" }},
                {{ type: "dialogue", text: "第五句。" }},
                {{ type: "dialogue", text: "第六句。" }},
                {{ type: "dialogue", text: "第七句。" }},
                {{ type: "dialogue", text: "第八句。" }},
              ],
            }};
            const fakeChoiceScene = {{
              id: "fake-choice",
              blocks: [
                {{ type: "background", assetId: "bg" }},
                {{ type: "music_play", assetId: "bgm" }},
                {{ type: "dialogue", text: "你要怎么回答？", voiceAssetId: "voice_1" }},
                {{
                  type: "choice",
                  options: [
                    {{ text: "点头", gotoSceneId: "__continue__" }},
                    {{ text: "沉默", gotoSceneId: "__continue__" }},
                    {{ text: "长".repeat(43), gotoSceneId: "__continue__" }}
                  ],
                }},
                {{ type: "screen_fade", action: "fade_out" }},
              ],
            }};
            const mature = tools.analyzeScenePacing(matureScene);
            const rough = tools.analyzeScenePacing(roughScene);
            const fakeChoice = tools.analyzeScenePacing(fakeChoiceScene);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              mature,
              matureDigest: tools.buildScenePacingDigest(mature),
              rough,
              fakeChoice,
              aggregate: tools.aggregateScenePacingAnalyses([mature, rough, fakeChoice]),
              gradeLabels: [tools.getScenePacingGrade(92).label, tools.getScenePacingGrade(61).label],
              emptyBlocks: tools.getBlocks(null),
              readableLong: tools.getReadableState({json.dumps(long_text)}),
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
        self.assertIn("analyzeScenePacing", payload["keys"])
        self.assertIn("aggregateScenePacingAnalyses", payload["keys"])
        self.assertGreaterEqual(payload["mature"]["score"], 80)
        self.assertEqual(payload["mature"]["grade"]["id"], "ready")
        self.assertTrue(payload["mature"]["metrics"]["hasMeaningfulChoice"])
        self.assertTrue(payload["mature"]["metrics"]["hasOutroCue"])
        self.assertIn("节奏成熟", payload["matureDigest"]["headline"])
        rough_codes = [issue["code"] for issue in payload["rough"]["issues"]]
        self.assertLess(payload["rough"]["score"], 52)
        self.assertIn("pacing_missing_background", rough_codes)
        self.assertIn("pacing_long_text", rough_codes)
        self.assertIn("pacing_text_run_too_long", rough_codes)
        self.assertIn("pacing_missing_outro", rough_codes)
        self.assertIn("pacing_script_duplicate_nearby_text", rough_codes)
        self.assertGreaterEqual(payload["rough"]["metrics"]["scriptQualityIssueCount"], 1)
        fake_choice_codes = [issue["code"] for issue in payload["fakeChoice"]["issues"]]
        self.assertIn("pacing_choice_without_consequence", fake_choice_codes)
        self.assertIn("pacing_script_choice_text_too_long", fake_choice_codes)
        self.assertEqual(payload["aggregate"]["sceneCount"], 3)
        self.assertGreaterEqual(payload["aggregate"]["roughSceneCount"], 1)
        self.assertEqual(payload["gradeLabels"], ["节奏成熟", "需要打磨"])
        self.assertEqual(payload["emptyBlocks"], [])
        self.assertTrue(payload["readableLong"]["isLong"])


if __name__ == "__main__":
    unittest.main()
