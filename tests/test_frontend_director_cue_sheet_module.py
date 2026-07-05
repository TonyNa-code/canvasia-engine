from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
TIMING_MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "audio_timing_estimator.js"
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "director_cue_sheet.js"


class FrontendDirectorCueSheetModuleTests(unittest.TestCase):
    def test_director_cue_sheet_builds_scene_cue_cards_and_exports(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(TIMING_MODULE_PATH))}, "utf8"), context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorDirectorCueSheet;
            const data = {{
              project: {{ title: "Director Demo" }},
              assetList: [
                {{ id: "bg_room", type: "background", name: "旧校舍教室", fileExists: true }},
                {{ id: "bgm_rain", type: "bgm", name: "雨夜钢琴", fileExists: true }},
                {{ id: "voice_yuna_001", type: "voice", name: "悠奈_001", fileExists: true }},
                {{ id: "sfx_door", type: "sfx", name: "门铃", fileExists: false }},
              ],
              characters: [
                {{ id: "yuna", displayName: "悠奈" }},
                {{ id: "teacher", displayName: "老师" }},
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
                        {{ id: "bg", type: "background", assetId: "bg_room", transition: "fade" }},
                        {{ id: "music", type: "music_play", assetId: "bgm_rain", fadeInMs: 600 }},
                        {{ id: "show", type: "character_show", characterId: "yuna", expressionId: "smile", position: "center" }},
                        {{ id: "line", type: "dialogue", speakerId: "yuna", text: "你终于来了。", voiceAssetId: "voice_yuna_001" }},
                        {{ id: "hide", type: "character_hide", characterId: "yuna" }},
                        {{ id: "narration", type: "narration", text: "门外的雨声忽然停了一秒。" }},
                        {{ id: "sfx", type: "sfx_play", assetId: "sfx_door" }},
                        {{ id: "choice", type: "choice", options: [{{ text: "追出去", targetSceneId: "scene_static" }}] }},
                        {{ id: "shake", type: "screen_shake", duration: "short" }},
                      ],
                    }},
                    {{
                      id: "scene_static",
                      name: "走廊独白",
                      blocks: [
                        {{ id: "line_teacher", type: "dialogue", speakerId: "teacher", text: "别再往前走了。" }},
                        {{ id: "n1", type: "narration", text: "走廊里没有灯。" }},
                        {{ id: "n2", type: "narration", text: "脚步声从远处追上来。" }},
                      ],
                    }},
                  ],
                }},
              ],
            }};
            const sheet = tools.buildDirectorCueSheet(data);
            const digest = tools.getDirectorCueStatusDigest(sheet);
            const markdown = tools.buildDirectorCueMarkdown(sheet, {{
              projectTitle: "Director Demo",
              generatedAt: "2026-07-05 12:00:00",
            }});
            const csv = tools.buildDirectorCueCsv(sheet);
            const panel = tools.renderDirectorCueSheetPanel(sheet);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              sheet,
              digest,
              markdown,
              csv,
              panel,
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
        self.assertIn("buildDirectorCueSheet", payload["keys"])
        self.assertIn("buildDirectorCueMarkdown", payload["keys"])
        self.assertIn("buildDirectorCueCsv", payload["keys"])
        self.assertIn("renderDirectorCueSheetPanel", payload["keys"])
        self.assertEqual(payload["sheet"]["projectTitle"], "Director Demo")
        self.assertEqual(payload["sheet"]["summary"]["sceneCount"], 2)
        self.assertEqual(payload["sheet"]["summary"]["cueCount"], 12)
        self.assertEqual(payload["sheet"]["summary"]["totalEstimatedSeconds"], 14)
        self.assertEqual(payload["sheet"]["summary"]["averageSceneSeconds"], 7)
        self.assertEqual(payload["sheet"]["summary"]["shortSceneCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["longSceneCount"], 0)
        self.assertEqual(payload["sheet"]["summary"]["silentSceneCount"], 0)
        self.assertEqual(payload["sheet"]["summary"]["missingAssetCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["blockerCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["warningCount"], 1)
        self.assertEqual(payload["digest"]["status"], "blocked")
        issue_codes = [issue["code"] for issue in payload["sheet"]["issues"]]
        self.assertIn("director_asset_missing_file", issue_codes)
        self.assertIn("director_scene_missing_background", issue_codes)
        self.assertIn("director_scene_too_static", issue_codes)
        self.assertIn("director_scene_no_audio_anchor", issue_codes)
        self.assertIn("director_speaker_not_staged", issue_codes)
        self.assertNotIn("yuna", [issue.get("speakerId") for issue in payload["sheet"]["issues"] if issue["code"] == "director_speaker_not_staged"])
        self.assertEqual(payload["sheet"]["scenes"][0]["durationLabel"], "约 9 秒")
        self.assertEqual(payload["sheet"]["scenes"][0]["timingBrief"], "约 9 秒 · 3 段正文 / 约 21 字")
        self.assertEqual(payload["sheet"]["scenes"][1]["timingTone"], "short")
        self.assertEqual(payload["sheet"]["scenes"][1]["readableCharacterCount"], 24)
        self.assertEqual(payload["sheet"]["productionQueue"][0]["title"], "音效文件缺失")
        self.assertIn("# Director Demo 导演分镜清单", payload["markdown"])
        self.assertIn("预计总时长", payload["markdown"])
        self.assertIn("预计时长", payload["markdown"])
        self.assertIn("约 9 秒 · 3 段正文 / 约 21 字", payload["markdown"])
        self.assertIn("教室黄昏", payload["markdown"])
        self.assertIn("[画面] 第 1 张：切换背景：旧校舍教室", payload["markdown"])
        self.assertIn("音效文件缺失", payload["markdown"])
        self.assertTrue(payload["csv"].startswith("\ufeff"))
        self.assertIn("导演分镜清单", payload["markdown"])
        self.assertIn('"场景预计时长"', payload["csv"])
        self.assertIn('"Director Demo","第1章","教室黄昏","约 9 秒"', payload["csv"])
        self.assertIn("预计 / 平均", payload["panel"])
        self.assertIn("短/长/空场景", payload["panel"])
        self.assertIn('data-action="export-director-cue-sheet-markdown"', payload["panel"])


if __name__ == "__main__":
    unittest.main()
