from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "audio_cue_sheet.js"


class FrontendAudioCueSheetModuleTests(unittest.TestCase):
    def test_audio_cue_sheet_helpers_export_markdown_and_csv(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorAudioCueSheet;
            const data = {{
              project: {{ title: "Demo Project" }},
              chapters: [{{ id: "chapter_1", name: "第1章" }}],
              assetList: [
                {{ id: "bgm_opening", type: "bgm", name: "放课后钢琴", fileExists: true }},
                {{ id: "bgm_missing_file", type: "bgm", name: "缺文件 BGM", fileExists: false }},
              ],
              scenes: [
                {{
                  id: "scene_start",
                  chapterId: "chapter_1",
                  name: "教室黄昏",
                  blocks: [
                    {{ id: "block_bg", type: "background", assetId: "bg_classroom" }},
                    {{ id: "block_music", type: "music_play", assetId: "bgm_opening", endMode: "after_block", endBlockId: "block_line_2", fadeInMs: 800, fadeOutMs: 1200, volume: 65 }},
                    {{ id: "block_line_1", type: "dialogue", text: "今天也留下来吗？" }},
                    {{ id: "block_line_2", type: "dialogue", text: "嗯，只待一会儿。" }},
                    {{ id: "block_stop", type: "music_stop", fadeOutMs: 500 }},
                  ],
                }},
                {{
                  id: "scene_roof",
                  chapterId: "chapter_1",
                  name: "屋顶晚风",
                  blocks: [
                    {{ id: "block_roof_line", type: "narration", text: "没有一起回家的过渡场景。" }},
                  ],
                }},
                {{
                  id: "scene_broken_music",
                  chapterId: "chapter_1",
                  name: "坏范围",
                  blocks: [
                    {{ id: "block_bad_music", type: "music_play", assetId: "bgm_missing_file", endMode: "after_block", endBlockId: "not_exists", fadeInMs: 0, fadeOutMs: 0 }},
                    {{ id: "block_bad_line", type: "dialogue", text: "这段需要修音乐。" }},
                  ],
                }},
              ],
            }};
            const sheet = tools.buildAudioCueSheet(data);
            const digest = tools.getAudioCueSheetStatusDigest(sheet);
            const markdown = tools.buildAudioCueSheetMarkdown(sheet, {{
              projectTitle: "Demo Project",
              generatedAt: "2026-05-10 22:00:00",
            }});
            const csv = tools.buildAudioCueSheetCsv(sheet);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              sheet,
              digest,
              markdown,
              csv,
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
        self.assertIn("buildAudioCueSheet", payload["keys"])
        self.assertIn("buildAudioCueSheetMarkdown", payload["keys"])
        self.assertIn("buildAudioCueSheetCsv", payload["keys"])
        self.assertEqual(payload["sheet"]["summary"]["cueCount"], 2)
        self.assertEqual(payload["sheet"]["summary"]["explicitRangeCount"], 2)
        self.assertEqual(payload["sheet"]["summary"]["stopCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["scenesWithoutMusicCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["missingAssetCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["missingEndBlockCount"], 1)
        self.assertEqual(payload["digest"]["status"], "blocked")
        self.assertEqual(payload["sheet"]["cues"][0]["endLabel"], "第 4 张 · 台词 · 嗯，只待一会儿。")
        self.assertIn("# Demo Project BGM 调度表", payload["markdown"])
        self.assertIn("BGM Cue 列表", payload["markdown"])
        self.assertIn("缺文件 BGM", payload["markdown"])
        self.assertIn('"BGM"', payload["csv"])
        self.assertIn('"放课后钢琴"', payload["csv"])


if __name__ == "__main__":
    unittest.main()
