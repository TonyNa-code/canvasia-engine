from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "renpy_exporter.js"


class FrontendRenpyExporterModuleTests(unittest.TestCase):
    def test_renpy_exporter_builds_draft_script_and_review_manifest(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorRenpyExporter;
            const data = {{
              project: {{ title: "Renpy Demo" }},
              assetList: [
                {{ id: "bg_rooftop", type: "background", name: "屋顶黄昏", path: "bg/rooftop.png" }},
                {{ id: "bgm_piano", type: "bgm", name: "放课后钢琴", path: "bgm/piano.ogg" }},
                {{ id: "voice_yuna_001", type: "voice", name: "悠奈_001", path: "voice/yuna_001.ogg" }},
              ],
              characters: [
                {{ id: "yuna", displayName: "悠奈" }},
              ],
              chapters: [
                {{
                  chapterId: "chapter_1",
                  name: "第1章",
                  scenes: [
                    {{
                      id: "scene_open",
                      name: "教室黄昏",
                      blocks: [
                        {{ type: "background", assetId: "bg_rooftop" }},
                        {{ type: "music_play", assetId: "bgm_piano", fadeInMs: 800 }},
                        {{ type: "character_show", characterId: "yuna", expressionId: "smile", position: "center" }},
                        {{ type: "dialogue", speakerId: "yuna", text: "欢迎回来。" }},
                        {{ type: "narration", text: "风吹过屋顶。" }},
                        {{
                          type: "choice",
                          options: [
                            {{ text: "追上去", gotoSceneId: "scene_end", effects: [{{ type: "variable_add", value: 1 }}] }},
                            {{ text: "留在原地", gotoSceneId: "__continue__" }},
                          ],
                        }},
                        {{ type: "wait", durationSeconds: 1.2 }},
                        {{ type: "screen_flash" }},
                        {{ type: "jump", targetSceneId: "scene_end" }},
                      ],
                    }},
                    {{
                      id: "scene_end",
                      name: "屋顶晚风",
                      blocks: [
                        {{ type: "narration", text: "风把答案吹散了。" }},
                        {{ type: "music_stop", fadeOutMs: 600 }},
                      ],
                    }},
                  ],
                }},
              ],
            }};
            const draft = tools.buildRenpyDraftExport(data);
            const digest = tools.getRenpyDraftStatusDigest(draft);
            const manifest = tools.buildRenpyDraftManifest(draft);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              draft,
              digest,
              manifest,
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
        self.assertIn("buildRenpyDraftExport", payload["keys"])
        self.assertIn("buildRenpyDraftManifest", payload["keys"])
        self.assertIn("renderBlock", payload["keys"])
        self.assertEqual(payload["draft"]["projectTitle"], "Renpy Demo")
        self.assertEqual(payload["draft"]["sceneCount"], 2)
        self.assertEqual(payload["draft"]["characterCount"], 1)
        self.assertGreaterEqual(payload["draft"]["assetDefinitionCount"], 1)
        self.assertEqual(payload["digest"]["status"], "review")
        self.assertIn('define yuna = Character("悠奈")', payload["draft"]["script"])
        self.assertIn('image bg_rooftop = "bg/rooftop.png"', payload["draft"]["script"])
        self.assertIn("label scene_open:", payload["draft"]["script"])
        self.assertIn("scene bg_rooftop with fade", payload["draft"]["script"])
        self.assertIn('play music "bgm/piano.ogg" fadein 0.8', payload["draft"]["script"])
        self.assertIn("show yuna smile at center with dissolve", payload["draft"]["script"])
        self.assertIn('yuna "欢迎回来。"', payload["draft"]["script"])
        self.assertIn("menu:", payload["draft"]["script"])
        self.assertIn("jump scene_end", payload["draft"]["script"])
        self.assertIn("$ renpy.pause(1.2)", payload["draft"]["script"])
        self.assertIn("# Canvasia review screen_flash", payload["draft"]["script"])
        self.assertIn("renpy_choice_effects_review", payload["manifest"])
        self.assertIn("renpy_comment_only_block", payload["manifest"])
        self.assertIn("scene_open", payload["manifest"])


if __name__ == "__main__":
    unittest.main()
