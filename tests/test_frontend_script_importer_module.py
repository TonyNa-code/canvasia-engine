from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "script_importer.js"


class FrontendScriptImporterModuleTests(unittest.TestCase):
    def test_script_importer_parses_plain_text_into_story_blocks(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorScriptImporter;
            const blocks = tools.parseScriptDraftToBlocks(`
              旁白：雨声贴着窗沿落下。
              悠奈：你终于来了。
              我把伞往她那边递过去。
              - 问她为什么在这里
              - 先沉默陪她一会儿
              1. 追上去
              2. 留在原地
              男主: 我知道了。
            `);
            const limited = tools.parseScriptDraftToBlocks("A：1\\nB：2\\nC：3", {{ maxBlocks: 2 }});
            const vnBlocks = tools.parseScriptDraftToBlocks(`
              label start:
              scene classroom with fade duration 800ms
              play video opening_movie title "Opening Movie" volume 80 from 2 to 12 cover no-skip
              play music school_theme fadein 1.2 fadeout 0.8
              show yuina smile at right with dissolve duration 700ms
              play sound door_knock
              voice yuina_001
              yuina "你终于来了。"
              "雨声没有停。"
              menu:
              "问她原因":
              jump scene_roof
              "先沉默":
              hide yuina with fade
              stop music fadeout 0.8
              fade in 0.5
              jump scene_end
            `);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              normalizedLines: tools.normalizeScriptImportText(" a\\r\\n\\n b ").join("|"),
              choiceLine: tools.parseChoiceLine("2. 追上去"),
              choiceOptionLine: tools.parseChoiceOptionLine("- 去天台 -> scene_roof"),
              dialogueLine: tools.parseDialogueLine("悠奈：你终于来了。"),
              quotedDialogueLine: tools.parseQuotedDialogueLine('悠奈 "你终于来了。"'),
              narrationLine: tools.parseDialogueLine("旁白：雨声变大了。"),
              stageLine: tools.parseStageDirectionLine("show yuina smile at right with dissolve"),
              sfxLine: tools.parseStageDirectionLine("play sound door_knock"),
              videoLine: tools.parseStageDirectionLine('play video opening_movie title "Opening Movie" volume 80 from 2 to 12 cover no-skip'),
              voiceLine: tools.parseVoiceLine("voice yuina_001"),
              jumpLine: tools.parseJumpLine("jump scene_end"),
              blocks,
              summary: tools.summarizeScriptDraftBlocks(blocks),
              preview: tools.buildScriptDraftPreviewLines(blocks, 4),
              limitedCount: limited.length,
              vnBlocks,
              vnSummary: tools.summarizeScriptDraftBlocks(vnBlocks),
              vnPreview: tools.buildScriptDraftPreviewLines(vnBlocks, 4),
              vnVoicePreview: tools.buildScriptDraftPreviewLines(vnBlocks, 6),
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
        self.assertIn("parseScriptDraftToBlocks", payload["keys"])
        self.assertIn("parseStageDirectionLine", payload["keys"])
        self.assertIn("parseJumpLine", payload["keys"])
        self.assertEqual(payload["normalizedLines"], "a|b")
        self.assertEqual(payload["choiceLine"], "追上去")
        self.assertEqual(payload["choiceOptionLine"], {"text": "去天台", "targetHint": "scene_roof"})
        self.assertEqual(payload["dialogueLine"], {
            "type": "dialogue",
            "speakerName": "悠奈",
            "text": "你终于来了。",
        })
        self.assertEqual(payload["quotedDialogueLine"], {
            "type": "dialogue",
            "speakerName": "悠奈",
            "text": "你终于来了。",
        })
        self.assertEqual(payload["narrationLine"], {"type": "narration", "text": "雨声变大了。"})
        self.assertEqual(payload["stageLine"], {
            "type": "character_show",
            "characterHint": "yuina",
            "expressionHint": "smile",
            "position": "right",
            "transition": "fade",
            "transitionDurationMs": 600,
        })
        self.assertEqual(payload["sfxLine"], {"type": "sfx_play", "assetHint": "door_knock", "volume": 100})
        self.assertEqual(payload["videoLine"], {
            "type": "video_play",
            "assetHint": "opening_movie",
            "title": "Opening Movie",
            "fit": "cover",
            "volume": 80,
            "startTimeSeconds": 2,
            "endTimeSeconds": 12,
            "skippable": False,
        })
        self.assertEqual(payload["voiceLine"], {"voiceHint": "yuina_001"})
        self.assertEqual(payload["jumpLine"], {"type": "jump", "targetHint": "scene_end"})
        self.assertEqual([block["type"] for block in payload["blocks"]], [
            "narration",
            "dialogue",
            "narration",
            "choice",
            "dialogue",
        ])
        self.assertEqual(payload["blocks"][3]["options"], [
            {"text": "问她为什么在这里"},
            {"text": "先沉默陪她一会儿"},
            {"text": "追上去"},
            {"text": "留在原地"},
        ])
        self.assertEqual(payload["summary"], {"dialogue": 2, "narration": 2, "choice": 1, "stage": 0, "route": 0, "total": 5})
        self.assertIn("悠奈：你终于来了。", payload["preview"][1])
        self.assertEqual(payload["limitedCount"], 2)
        self.assertEqual([block["type"] for block in payload["vnBlocks"]], [
            "background",
            "video_play",
            "music_play",
            "character_show",
            "sfx_play",
            "dialogue",
            "narration",
            "choice",
            "character_hide",
            "music_stop",
            "screen_fade",
            "jump",
        ])
        self.assertEqual(payload["vnBlocks"][0]["assetHint"], "classroom")
        self.assertEqual(payload["vnBlocks"][0]["transitionDurationMs"], 800)
        self.assertEqual(payload["vnBlocks"][1]["assetHint"], "opening_movie")
        self.assertEqual(payload["vnBlocks"][1]["title"], "Opening Movie")
        self.assertEqual(payload["vnBlocks"][1]["fit"], "cover")
        self.assertEqual(payload["vnBlocks"][1]["volume"], 80)
        self.assertEqual(payload["vnBlocks"][1]["startTimeSeconds"], 2)
        self.assertEqual(payload["vnBlocks"][1]["endTimeSeconds"], 12)
        self.assertFalse(payload["vnBlocks"][1]["skippable"])
        self.assertEqual(payload["vnBlocks"][2]["assetHint"], "school_theme")
        self.assertEqual(payload["vnBlocks"][2]["fadeInMs"], 1200)
        self.assertEqual(payload["vnBlocks"][2]["fadeOutMs"], 800)
        self.assertEqual(payload["vnBlocks"][3]["position"], "right")
        self.assertEqual(payload["vnBlocks"][3]["transition"], "fade")
        self.assertEqual(payload["vnBlocks"][3]["transitionDurationMs"], 700)
        self.assertEqual(payload["vnBlocks"][4], {"type": "sfx_play", "assetHint": "door_knock", "volume": 100})
        self.assertEqual(payload["vnBlocks"][5]["voiceHint"], "yuina_001")
        self.assertEqual(payload["vnBlocks"][7]["options"], [
            {"text": "问她原因", "targetHint": "scene_roof"},
            {"text": "先沉默"},
        ])
        self.assertEqual(payload["vnBlocks"][10]["action"], "fade_in")
        self.assertEqual(payload["vnBlocks"][10]["durationMs"], 500)
        self.assertEqual(payload["vnBlocks"][11], {"type": "jump", "targetHint": "scene_end"})
        self.assertEqual(payload["vnSummary"], {
            "dialogue": 1,
            "narration": 1,
            "choice": 1,
            "stage": 8,
            "route": 1,
            "total": 12,
        })
        self.assertIn("演出：切背景：classroom", payload["vnPreview"][0])
        self.assertIn("演出：播放视频：Opening Movie", payload["vnPreview"][1])
        self.assertIn("voice: yuina_001", payload["vnVoicePreview"][5])


if __name__ == "__main__":
    unittest.main()
