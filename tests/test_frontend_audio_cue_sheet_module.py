from __future__ import annotations

import csv
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
                {{ id: "sfx_door", type: "sfx", name: "门铃", fileExists: true }},
                {{ id: "sfx_missing_file", type: "sfx", name: "缺文件音效", fileExists: false }},
                {{ id: "voice_yuina_001", type: "voice", name: "悠奈_001", fileExists: true }},
                {{ id: "voice_missing_file", type: "voice", name: "缺文件语音", fileExists: false }},
              ],
              characters: [
                {{ id: "char_yuina", displayName: "悠奈" }},
              ],
              scenes: [
                {{
                  id: "scene_start",
                  chapterId: "chapter_1",
                  name: "教室黄昏",
                  blocks: [
                    {{ id: "block_bg", type: "background", assetId: "bg_classroom" }},
                    {{ id: "block_music", type: "music_play", assetId: "bgm_opening", endMode: "after_block", endBlockId: "block_line_2", fadeInMs: 800, fadeOutMs: 1200, volume: 65 }},
                    {{ id: "block_line_1", type: "dialogue", speakerId: "char_yuina", text: "今天也留下来吗？", voiceAssetId: "voice_yuina_001", voiceVolume: 88 }},
                    {{ id: "block_sfx", type: "sfx_play", assetId: "sfx_door", volume: 80 }},
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
                    {{ id: "block_bad_sfx", type: "sfx_play", assetId: "sfx_missing_file", volume: 0 }},
                    {{ id: "block_bad_line", type: "dialogue", text: "这段需要修音乐。", voiceAssetId: "voice_missing_file" }},
                  ],
                }},
              ],
            }};
            const sheet = tools.buildAudioCueSheet(data);
            const autoFixPlan = tools.buildAudioCueAutoFixPlan(data);
            const digest = tools.getAudioCueSheetStatusDigest(sheet);
            const markdown = tools.buildAudioCueSheetMarkdown(sheet, {{
              projectTitle: "Demo Project",
              generatedAt: "2026-05-10 22:00:00",
            }});
            const csv = tools.buildAudioCueSheetCsv(sheet);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              sheet,
              autoFixPlan,
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
        self.assertIn("buildAudioCueRangeRows", payload["keys"])
        self.assertIn("buildVoiceCueRows", payload["keys"])
        self.assertIn("buildAudioCueProductionQueue", payload["keys"])
        self.assertIn("buildAudioCueAuditionChecklist", payload["keys"])
        self.assertIn("buildAudioCueAutoFixPlan", payload["keys"])
        self.assertIn("getAudioCueAutoFixDigest", payload["keys"])
        self.assertIn("buildAudioCueSheetMarkdown", payload["keys"])
        self.assertIn("buildAudioCueSheetCsv", payload["keys"])
        self.assertEqual(payload["sheet"]["summary"]["cueCount"], 2)
        self.assertEqual(payload["sheet"]["summary"]["sfxCueCount"], 2)
        self.assertEqual(payload["sheet"]["summary"]["voiceCueCount"], 2)
        self.assertEqual(payload["sheet"]["summary"]["rangeSegmentCount"], 2)
        self.assertEqual(payload["sheet"]["summary"]["explicitRangeCount"], 2)
        self.assertEqual(payload["sheet"]["summary"]["auditionNeededCount"], 2)
        self.assertEqual(payload["sheet"]["summary"]["stopCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["scenesWithoutMusicCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["missingAssetCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["missingSfxAssetCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["missingVoiceAssetCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["missingEndBlockCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["autoFixSceneCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["autoFixBlockCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["autoFixOperationCount"], 3)
        self.assertGreaterEqual(payload["sheet"]["summary"]["productionTaskCount"], 6)
        self.assertGreaterEqual(payload["sheet"]["summary"]["auditionChecklistCount"], 5)
        self.assertLess(payload["sheet"]["summary"]["releaseReadinessPercent"], 100)
        self.assertEqual(payload["digest"]["status"], "blocked")
        self.assertEqual(payload["sheet"]["productionQueue"][0]["severity"], "blocker")
        self.assertIn("补齐或重新绑定素材", [item["actionLabel"] for item in payload["sheet"]["productionQueue"]])
        self.assertIn("修完再听", [item["priority"] for item in payload["sheet"]["auditionChecklist"]])
        self.assertEqual(payload["sheet"]["sfxCues"][0]["assetName"], "门铃")
        self.assertEqual(payload["sheet"]["sfxCues"][1]["status"], "blocker")
        self.assertEqual(payload["sheet"]["voiceCues"][0]["speakerName"], "悠奈")
        self.assertEqual(payload["sheet"]["voiceCues"][1]["status"], "blocker")
        self.assertTrue(payload["autoFixPlan"]["changed"])
        self.assertEqual(payload["autoFixPlan"]["changedSceneCount"], 1)
        self.assertEqual(payload["autoFixPlan"]["changedBlockCount"], 1)
        self.assertEqual(payload["autoFixPlan"]["operationCount"], 3)
        fixed_block = payload["autoFixPlan"]["scenePlans"][0]["scene"]["blocks"][0]
        self.assertEqual(fixed_block["assetId"], "bgm_missing_file")
        self.assertEqual(fixed_block["fadeInMs"], 700)
        self.assertEqual(fixed_block["fadeOutMs"], 900)
        self.assertEqual(fixed_block["endBlockId"], "block_bad_line")
        self.assertIn("已准备修复 1 个场景", payload["autoFixPlan"]["summary"])
        self.assertEqual(payload["sheet"]["cues"][0]["endLabel"], "第 5 张 · 台词 · 嗯，只待一会儿。")
        self.assertEqual(payload["sheet"]["cues"][0]["handoffType"], "explicit_end")
        self.assertIn("播放到 第 5 张", payload["sheet"]["rangeRows"][0]["handoffLabel"])
        self.assertIn("重点试听开始卡和结束卡前后", payload["sheet"]["rangeRows"][0]["auditionHint"])
        self.assertIn("# Demo Project 音频调度表", payload["markdown"])
        self.assertIn("制作优先队列", payload["markdown"])
        self.assertIn("发布前试听清单", payload["markdown"])
        self.assertIn("BGM 覆盖范围速览", payload["markdown"])
        self.assertIn("BGM Cue 列表", payload["markdown"])
        self.assertIn("音效 Cue 列表", payload["markdown"])
        self.assertIn("语音 Cue 列表", payload["markdown"])
        self.assertIn("缺文件 BGM", payload["markdown"])
        self.assertIn("缺文件音效", payload["markdown"])
        self.assertIn("缺文件语音", payload["markdown"])
        self.assertIn("接管方式", payload["csv"])
        self.assertIn('"BGM"', payload["csv"])
        self.assertIn('"SFX"', payload["csv"])
        self.assertIn('"Voice"', payload["csv"])
        self.assertIn('"放课后钢琴"', payload["csv"])
        self.assertIn('"门铃"', payload["csv"])
        self.assertIn('"悠奈_001"', payload["csv"])
        csv_rows = list(csv.reader(payload["csv"].lstrip("\ufeff").splitlines()))
        self.assertTrue(csv_rows)
        self.assertTrue(all(len(row) == len(csv_rows[0]) for row in csv_rows))
        self.assertEqual(len(csv_rows[0]), 18)
        self.assertEqual([row[0] for row in csv_rows[1:]], ["BGM", "BGM", "SFX", "SFX", "Voice", "Voice"])


if __name__ == "__main__":
    unittest.main()
