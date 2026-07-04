from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "screenplay_exporter.js"


class FrontendScreenplayExporterModuleTests(unittest.TestCase):
    def test_screenplay_exporter_builds_readable_markdown_and_csv(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorScreenplayExporter;
            const data = {{
              project: {{ title: "Screenplay Demo" }},
              assetList: [
                {{ id: "bg_rooftop", type: "background", name: "屋顶黄昏", path: "bg/rooftop.png" }},
                {{ id: "bgm_piano", type: "bgm", name: "放课后钢琴", path: "bgm/piano.ogg" }},
                {{ id: "voice_yuna_001", type: "voice", name: "悠奈_001", path: "voice/yuna_001.ogg" }},
              ],
              characters: [
                {{ id: "yuna", displayName: "悠奈" }},
                {{ id: "teacher", displayName: "老师" }},
              ],
              chapters: [
                {{
                  chapterId: "chapter_1",
                  name: "第1章 开学第一天",
                  scenes: [
                    {{
                      id: "scene_open",
                      name: "教室黄昏",
                      blocks: [
                        {{ id: "music", type: "music_play", assetId: "bgm_piano", fadeInMs: 800 }},
                        {{ id: "bg", type: "background", assetId: "bg_rooftop", transition: "fade" }},
                        {{ id: "show", type: "character_show", characterId: "yuna", expressionId: "smile", position: "center" }},
                        {{ id: "line_1", type: "dialogue", speakerId: "yuna", text: "欢迎回来。", voiceAssetId: "voice_yuna_001" }},
                        {{ id: "line_2", type: "dialogue", speakerId: "teacher", text: "这句暂时还没配音。" }},
                        {{ id: "narration", type: "narration", text: "窗外忽然亮起细碎的光。" }},
                        {{
                          id: "choice",
                          type: "choice",
                          options: [
                            {{ text: "追上去", targetSceneId: "scene_end" }},
                            {{ text: "留在原地", targetSceneId: "" }},
                          ],
                        }},
                        {{ id: "wait", type: "wait", durationSeconds: 1.2 }},
                        {{ id: "jump", type: "jump", targetSceneId: "scene_end" }},
                      ],
                    }},
                    {{
                      id: "scene_end",
                      name: "屋顶晚风",
                      blocks: [
                        {{ id: "ending", type: "narration", text: "风把答案吹散了。" }},
                        {{ id: "stop", type: "music_stop", fadeOutMs: 600 }},
                      ],
                    }},
                  ],
                }},
              ],
            }};
            const screenplay = tools.buildScreenplayExport(data);
            const digest = tools.getScreenplayStatusDigest(screenplay);
            const markdown = tools.buildScreenplayMarkdown(screenplay, {{
              projectTitle: "Screenplay Demo",
              generatedAt: "2026-07-05 10:00:00",
            }});
            const csv = tools.buildScreenplayCsv(screenplay);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              screenplay,
              digest,
              markdown,
              csv,
              stageDirection: tools.buildStageDirectionText(data.chapters[0].scenes[0].blocks[0], {{
                assetMap: new Map(data.assetList.map((asset) => [asset.id, asset])),
              }}),
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
        self.assertIn("buildScreenplayExport", payload["keys"])
        self.assertIn("buildScreenplayMarkdown", payload["keys"])
        self.assertIn("buildScreenplayCsv", payload["keys"])
        self.assertEqual(payload["screenplay"]["projectTitle"], "Screenplay Demo")
        self.assertEqual(payload["screenplay"]["summary"]["chapterCount"], 1)
        self.assertEqual(payload["screenplay"]["summary"]["sceneCount"], 2)
        self.assertEqual(payload["screenplay"]["summary"]["blockCount"], 11)
        self.assertEqual(payload["screenplay"]["summary"]["dialogueCount"], 2)
        self.assertEqual(payload["screenplay"]["summary"]["narrationCount"], 2)
        self.assertEqual(payload["screenplay"]["summary"]["choiceCount"], 1)
        self.assertEqual(payload["screenplay"]["summary"]["stageDirectionCount"], 6)
        self.assertEqual(payload["screenplay"]["summary"]["missingVoiceCount"], 1)
        self.assertEqual(payload["digest"]["status"], "review")
        self.assertIn("# Screenplay Demo 剧本台本", payload["markdown"])
        self.assertIn("### 第1章 开学第一天", payload["markdown"])
        self.assertIn("#### 场景：教室黄昏", payload["markdown"])
        self.assertIn("悠奈：欢迎回来。 （语音：悠奈_001）", payload["markdown"])
        self.assertIn("[选项] 1. 追上去 -> 屋顶晚风 / 2. 留在原地 -> 继续下一张卡", payload["markdown"])
        self.assertTrue(payload["csv"].startswith("\ufeff"))
        self.assertIn('"Screenplay Demo"', payload["csv"])
        self.assertIn('"播放 BGM：放课后钢琴，淡入 800ms"', payload["csv"])
        self.assertEqual(payload["stageDirection"], "播放 BGM：放课后钢琴，淡入 800ms")


if __name__ == "__main__":
    unittest.main()
