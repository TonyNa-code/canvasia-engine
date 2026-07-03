from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "voice_production_sheet.js"


class FrontendVoiceProductionSheetModuleTests(unittest.TestCase):
    def test_voice_production_sheet_helpers_export_markdown_and_csv(self) -> None:
        long_line = "这是一句需要拆分给声优录音的长台词，" * 8
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorVoiceProductionSheet;
            const data = {{
              project: {{ title: "Voice Demo" }},
              assetList: [
                {{ id: "voice_ready", type: "voice", name: "悠奈_001", path: "voice/yuna_001.ogg", fileExists: true }},
                {{ id: "voice_ready_ghost", type: "voice", name: "幽灵说话人", path: "voice/ghost.ogg", fileExists: true }},
                {{ id: "voice_missing_file", type: "voice", name: "缺文件语音", path: "voice/missing.ogg", fileExists: false }},
                {{ id: "bgm_theme", type: "bgm", name: "主题曲", path: "bgm/theme.ogg", fileExists: true }},
              ],
              characters: [
                {{ id: "char_a", displayName: "悠奈" }},
                {{ id: "char_b", displayName: "老师" }},
              ],
              chapters: [
                {{
                  chapterId: "chapter_1",
                  name: "第1章",
                  scenes: [
                    {{
                      id: "scene_opening",
                      name: "教室黄昏",
                      blocks: [
                        {{ id: "ready", type: "dialogue", speakerId: "char_a", text: "欢迎回来。", voiceAssetId: "voice_ready" }},
                        {{ id: "missing", type: "dialogue", speakerId: "char_a", text: {json.dumps(long_line)}, voiceAssetId: "" }},
                        {{ id: "file", type: "dialogue", speakerId: "char_b", text: "这句有条目但没文件。", voiceAssetId: "voice_missing_file" }},
                        {{ id: "asset", type: "dialogue", speakerId: "char_b", text: "这句绑了不存在的素材。", voiceAssetId: "voice_ghost" }},
                        {{ id: "wrong", type: "dialogue", speakerId: "char_a", text: "这句错误绑定了音乐。", voiceAssetId: "bgm_theme" }},
                        {{ id: "speaker", type: "dialogue", speakerId: "ghost", text: "这句说话人不在角色表。", voiceAssetId: "voice_ready_ghost" }},
                        {{ id: "narration", type: "narration", text: "旁白不进入角色配音表。" }},
                      ],
                    }},
                  ],
                }},
              ],
            }};
            const sheet = tools.buildVoiceProductionSheet(data);
            const digest = tools.getVoiceProductionStatusDigest(sheet);
            const markdown = tools.buildVoiceProductionMarkdown(sheet, {{
              projectTitle: "Voice Demo",
              generatedAt: "2026-07-04 02:00:00",
            }});
            const csv = tools.buildVoiceProductionCsv(sheet);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              sheet,
              digest,
              markdown,
              csv,
              labels: [
                tools.getVoiceLineStatusLabel("ready"),
                tools.getVoiceLineStatusLabel("missing_file"),
              ],
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
        self.assertIn("buildVoiceProductionSheet", payload["keys"])
        self.assertIn("buildVoiceProductionMarkdown", payload["keys"])
        self.assertIn("buildVoiceProductionCsv", payload["keys"])
        self.assertEqual(payload["sheet"]["summary"]["lineCount"], 6)
        self.assertEqual(payload["sheet"]["summary"]["readyLineCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["missingVoiceCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["missingAssetCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["missingFileCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["wrongTypeCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["unknownSpeakerCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["longLineCount"], 1)
        self.assertEqual(payload["digest"]["status"], "blocked")
        issue_codes = [issue["code"] for issue in payload["sheet"]["issues"]]
        self.assertIn("voice_missing_asset", issue_codes)
        self.assertIn("voice_missing_file", issue_codes)
        self.assertIn("voice_wrong_asset_type", issue_codes)
        self.assertIn("voice_unknown_speaker", issue_codes)
        self.assertIn("voice_line_very_long", issue_codes)
        self.assertIn("# Voice Demo 语音制作清单", payload["markdown"])
        self.assertIn("角色配音进度", payload["markdown"])
        self.assertIn('"缺文件语音"', payload["csv"])
        self.assertEqual(payload["labels"], ["已配音", "语音文件缺失"])


if __name__ == "__main__":
    unittest.main()
