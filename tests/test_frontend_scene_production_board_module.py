from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "scene_production_board.js"


class FrontendSceneProductionBoardModuleTests(unittest.TestCase):
    def test_scene_production_board_helpers_export_markdown_and_csv(self) -> None:
        long_text = "这是一个很长的旁白。" * 40
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorSceneProductionBoard;
            const data = {{
              project: {{ title: "Demo Project", entrySceneId: "scene_start" }},
              chapters: [
                {{
                  chapterId: "chapter_1",
                  name: "第1章",
                  scenes: [
                    {{
                      id: "scene_start",
                      name: "教室黄昏",
                      blocks: [
                        {{ id: "bg", type: "background", assetId: "bg_classroom" }},
                        {{ id: "music", type: "music_play", assetId: "bgm_theme" }},
                        {{ id: "line_1", type: "dialogue", speakerId: "char_a", text: "你好", voiceAssetId: "voice_001" }},
                        {{ id: "line_2", type: "dialogue", speakerId: "char_a", text: "还没配音" }},
                        {{ id: "fx", type: "screen_fade" }},
                        {{
                          id: "choice",
                          type: "choice",
                          options: [
                            {{ id: "a", text: "去屋顶", gotoSceneId: "scene_roof" }},
                            {{ id: "b", text: "这是一个非常非常非常非常非常非常非常长的选项文案，长到按钮区会明显拥挤，甚至需要玩家停下来读完才能理解", gotoSceneId: "scene_missing" }},
                          ],
                        }},
                      ],
                    }},
                    {{
                      id: "scene_roof",
                      name: "屋顶",
                      blocks: [
                        {{ id: "long", type: "narration", text: {json.dumps(long_text)} }},
                        {{
                          id: "many",
                          type: "choice",
                          options: [
                            {{ text: "一", gotoSceneId: "scene_start" }},
                            {{ text: "二", gotoSceneId: "scene_start" }},
                            {{ text: "三", gotoSceneId: "scene_start" }},
                            {{ text: "四", gotoSceneId: "scene_start" }},
                            {{ text: "五", gotoSceneId: "scene_start" }},
                            {{ text: "六", gotoSceneId: "scene_start" }},
                            {{ text: "七", gotoSceneId: "scene_start" }},
                          ],
                        }},
                      ],
                    }},
                    {{ id: "scene_empty", name: "空场景", blocks: [] }},
                  ],
                }},
              ],
            }};
            const board = tools.buildSceneProductionBoard(data);
            const digest = tools.getSceneProductionBoardStatusDigest(board);
            const markdown = tools.buildSceneProductionBoardMarkdown(board, {{
              projectTitle: "Demo Project",
              generatedAt: "2026-07-04 02:00:00",
            }});
            const csv = tools.buildSceneProductionBoardCsv(board);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              board,
              digest,
              markdown,
              csv,
              readyLabel: tools.getSceneStatusLabel("ready"),
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
        self.assertIn("buildSceneProductionBoard", payload["keys"])
        self.assertIn("buildSceneProductionBoardMarkdown", payload["keys"])
        self.assertIn("buildSceneProductionBoardCsv", payload["keys"])
        self.assertEqual(payload["board"]["summary"]["sceneCount"], 3)
        self.assertGreater(payload["board"]["summary"]["blockedSceneCount"], 0)
        self.assertGreater(payload["board"]["summary"]["warningSceneCount"], 0)
        self.assertEqual(payload["board"]["summary"]["emptySceneCount"], 1)
        self.assertGreater(payload["board"]["summary"]["missingBackgroundSceneCount"], 0)
        self.assertGreater(payload["board"]["summary"]["missingMusicSceneCount"], 0)
        self.assertEqual(payload["board"]["summary"]["missingVoiceLineCount"], 1)
        self.assertGreater(payload["board"]["summary"]["longTextSceneCount"], 0)
        self.assertEqual(payload["digest"]["status"], "blocked")
        issue_codes = [issue["code"] for issue in payload["board"]["issues"]]
        self.assertIn("scene_bad_route_target", issue_codes)
        self.assertIn("scene_empty", issue_codes)
        self.assertIn("scene_missing_background", issue_codes)
        self.assertIn("scene_missing_music", issue_codes)
        self.assertIn("scene_missing_voice", issue_codes)
        self.assertIn("scene_long_text", issue_codes)
        self.assertIn("scene_many_choices", issue_codes)
        self.assertIn("scene_long_choice_text", issue_codes)
        self.assertIn("# Demo Project 场景生产看板", payload["markdown"])
        self.assertIn("教室黄昏", payload["markdown"])
        self.assertIn('"屋顶"', payload["csv"])
        self.assertEqual(payload["readyLabel"], "可试玩")


if __name__ == "__main__":
    unittest.main()
