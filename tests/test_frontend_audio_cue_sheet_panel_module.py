from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
EDITOR_COMMON_PATH = ROOT_DIR / "prototype_editor" / "modules" / "editor_common.js"
AUDIO_CUE_SHEET_PATH = ROOT_DIR / "prototype_editor" / "modules" / "audio_cue_sheet.js"
PANEL_PATH = ROOT_DIR / "prototype_editor" / "modules" / "audio_cue_sheet_panel.js"


class FrontendAudioCueSheetPanelModuleTests(unittest.TestCase):
    def test_audio_cue_sheet_panel_renders_issue_and_range_states(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            for (const filePath of [
              {json.dumps(str(EDITOR_COMMON_PATH))},
              {json.dumps(str(AUDIO_CUE_SHEET_PATH))},
              {json.dumps(str(PANEL_PATH))},
            ]) {{
              vm.runInContext(fs.readFileSync(filePath, "utf8"), context);
            }}
            const panelTools = context.window.CanvasiaEditorAudioCueSheetPanel;
            const sheetTools = context.window.CanvasiaEditorAudioCueSheet;
            const issueSheet = sheetTools.buildAudioCueSheet({{
              chapters: [{{ id: "chapter_1", name: "第1章" }}],
              assetList: [{{ id: "bgm_missing", type: "bgm", name: "缺文件 BGM", fileExists: false }}],
              scenes: [
                {{
                  id: "scene_issue",
                  chapterId: "chapter_1",
                  name: "坏范围",
                  blocks: [
                    {{ id: "music_1", type: "music_play", assetId: "bgm_missing", endMode: "after_block", endBlockId: "missing_block" }},
                    {{ id: "line_1", type: "dialogue", text: "这段需要修音乐。" }},
                  ],
                }},
              ],
            }});
            const rangeSheet = sheetTools.buildAudioCueSheet({{
              chapters: [{{ id: "chapter_1", name: "第1章" }}],
              assetList: [{{ id: "bgm_ok", type: "bgm", name: "放课后钢琴", fileExists: true }}],
              scenes: [
                {{
                  id: "scene_range",
                  chapterId: "chapter_1",
                  name: "教室黄昏",
                  blocks: [
                    {{ id: "music_1", type: "music_play", assetId: "bgm_ok", endMode: "after_block", endBlockId: "line_2", fadeInMs: 600, fadeOutMs: 900 }},
                    {{ id: "line_1", type: "dialogue", text: "今天也留下来吗？" }},
                    {{ id: "line_2", type: "dialogue", text: "嗯，只待一会儿。" }},
                  ],
                }},
              ],
            }});
            const suggestionSheet = sheetTools.buildAudioCueSheet({{
              chapters: [{{ id: "chapter_1", name: "第1章" }}],
              assetList: [{{ id: "bgm_ok", type: "bgm", name: "雨夜钢琴", fileExists: true }}],
              scenes: [
                {{
                  id: "scene_suggestion",
                  chapterId: "chapter_1",
                  name: "雨夜教室",
                  blocks: [
                    {{ id: "music_1", type: "music_play", assetId: "bgm_ok", endMode: "until_next_music", fadeInMs: 600 }},
                    {{ id: "line_1", type: "dialogue", text: "雨还没停。" }},
                    {{ id: "line_2", type: "narration", text: "窗外的灯慢慢暗下去。" }},
                  ],
                }},
              ],
            }});
            const sfxOnlySheet = sheetTools.buildAudioCueSheet({{
              chapters: [{{ id: "chapter_1", name: "第1章" }}],
              assetList: [{{ id: "sfx_door", type: "sfx", name: "门铃", fileExists: true }}],
              scenes: [
                {{
                  id: "scene_sfx",
                  chapterId: "chapter_1",
                  name: "走廊",
                  blocks: [
                    {{ id: "sfx_1", type: "sfx_play", assetId: "sfx_door", volume: 75 }},
                  ],
                }},
              ],
            }});
            const voiceOnlySheet = sheetTools.buildAudioCueSheet({{
              chapters: [{{ id: "chapter_1", name: "第1章" }}],
              characters: [{{ id: "char_a", displayName: "悠奈" }}],
              assetList: [{{ id: "voice_a", type: "voice", name: "悠奈_001", fileExists: true }}],
              scenes: [
                {{
                  id: "scene_voice",
                  chapterId: "chapter_1",
                  name: "教室",
                  blocks: [
                    {{ id: "line_1", type: "dialogue", speakerId: "char_a", text: "欢迎回来。", voiceAssetId: "voice_a" }},
                  ],
                }},
              ],
            }});
            const emptyHtml = panelTools.renderAudioCueSheetPanel({{ summary: {{}}, issues: [], rangeRows: [] }});
            const issueHtml = panelTools.renderAudioCueSheetPanel(issueSheet);
            const rangeHtml = panelTools.renderAudioCueSheetPanel(rangeSheet);
            const suggestionHtml = panelTools.renderAudioCueSheetPanel(suggestionSheet);
            const sfxOnlyHtml = panelTools.renderAudioCueSheetPanel(sfxOnlySheet);
            const voiceOnlyHtml = panelTools.renderAudioCueSheetPanel(voiceOnlySheet);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(panelTools).sort(),
              emptyHtml,
              issueHtml,
              rangeHtml,
              suggestionHtml,
              sfxOnlyHtml,
              voiceOnlyHtml,
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
        self.assertIn("renderAudioCueSheetPanel", payload["keys"])
        self.assertIn("renderAudioCueSheetPreview", payload["keys"])
        self.assertIn("renderAudioProductionQueue", payload["keys"])
        self.assertIn("renderAudioAuditionChecklist", payload["keys"])
        self.assertIn("renderAudioRangeSuggestionCard", payload["keys"])
        self.assertIn("renderAudioRangeSuggestions", payload["keys"])
        self.assertIn("renderAudioCueAutoFixButton", payload["keys"])
        self.assertIn("renderSfxCueRow", payload["keys"])
        self.assertIn("renderVoiceCueRow", payload["keys"])
        self.assertIn('data-action="export-audio-cue-sheet-markdown"', payload["rangeHtml"])
        self.assertIn('data-action="export-audio-cue-sheet-csv"', payload["rangeHtml"])
        self.assertIn('data-action="apply-audio-cue-autofix"', payload["issueHtml"])
        self.assertIn("一键补齐", payload["issueHtml"])
        self.assertIn("音频基础参数已完整", payload["rangeHtml"])
        self.assertIn('disabled aria-disabled="true"', payload["rangeHtml"])
        self.assertIn("音频调度表", payload["rangeHtml"])
        self.assertIn("BGM 文本范围建议", payload["suggestionHtml"])
        self.assertIn("雨夜钢琴", payload["suggestionHtml"])
        self.assertIn('data-action="apply-audio-range-suggestion"', payload["suggestionHtml"])
        self.assertIn('data-scene-id="scene_suggestion"', payload["suggestionHtml"])
        self.assertIn('data-end-block-id="line_2"', payload["suggestionHtml"])
        self.assertIn("制作优先队列", payload["issueHtml"])
        self.assertIn("发布前试听清单", payload["rangeHtml"])
        self.assertIn("就绪度", payload["rangeHtml"])
        self.assertIn("缺文件 BGM", payload["issueHtml"])
        self.assertIn("结束卡片不存在", payload["issueHtml"])
        self.assertIn("放课后钢琴", payload["rangeHtml"])
        self.assertIn("重点试听开始卡和结束卡前后", payload["rangeHtml"])
        self.assertIn("门铃", payload["sfxOnlyHtml"])
        self.assertIn("发布前抽查触发点即可", payload["sfxOnlyHtml"])
        self.assertIn("悠奈_001", payload["voiceOnlyHtml"])
        self.assertIn("发布前抽查这一句语音即可", payload["voiceOnlyHtml"])
        self.assertIn("语音卡", payload["voiceOnlyHtml"])
        self.assertIn("当前项目还没有播放音乐、音效或已绑定语音", payload["emptyHtml"])


if __name__ == "__main__":
    unittest.main()
