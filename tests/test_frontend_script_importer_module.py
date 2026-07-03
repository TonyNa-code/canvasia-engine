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
            const directorBlocks = tools.parseScriptDraftToBlocks(`
              shake heavy short
              flash red strong long
              zoom out heavy right
              pan left light
              credits title "STAFF" subtitle "Thanks for playing" duration 24 light no-skip lines "企划：Tony|剧本：Tony"
            `);
            const atmosphereBlocks = tools.parseScriptDraftToBlocks(`
              filter memory soft
              clear filter
              blur right strong
              clear blur
              particle snow heavy fast
              particle stop
            `);
            const textSpeedBlocks = tools.parseScriptDraftToBlocks(`
              speed fast
              悠奈：快跑！
              旁白：时间像被拉长。 speed slow
              voice yuina_002
              text speed instant
              yuina "别眨眼。"
            `);
            const choiceEffectBlocks = tools.parseScriptDraftToBlocks(`
              - 拉住她 -> rooftop [affection +1; courage +2; met=true]
              - 先道歉 [affection -1; route="apology"]
            `);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              normalizedLines: tools.normalizeScriptImportText(" a\\r\\n\\n b ").join("|"),
              choiceLine: tools.parseChoiceLine("2. 追上去"),
              choiceOptionLine: tools.parseChoiceOptionLine("- 去天台 -> scene_roof"),
              choiceEffectAdd: tools.parseChoiceEffectClause("affection +1"),
              choiceEffectSet: tools.parseChoiceEffectClause("met=true"),
              choiceOptionEffectLine: tools.parseChoiceOptionLine('- 拉住她 -> rooftop [affection +1; met=true; route="good"]'),
              dialogueLine: tools.parseDialogueLine("悠奈：你终于来了。"),
              quotedDialogueLine: tools.parseQuotedDialogueLine('悠奈 "你终于来了。"'),
              dialogueSpeedLine: tools.parseDialogueLine("悠奈：快跑！ speed fast"),
              quotedDialogueSpeedLine: tools.parseQuotedDialogueLine('悠奈 "别眨眼。" speed instant'),
              narrationSpeedLine: tools.parseDialogueLine("旁白：时间像被拉长。 speed slow"),
              narrationLine: tools.parseDialogueLine("旁白：雨声变大了。"),
              speedLine: tools.parseTextSpeedLine("speed instant"),
              stageLine: tools.parseStageDirectionLine("show yuina smile at right with dissolve"),
              stageLineWithStage: tools.parseStageDirectionLine("show yuina smile at right with dissolve scale 118 x -8 y 3 opacity 90 layer 2 flip"),
              sfxLine: tools.parseStageDirectionLine("play sound door_knock"),
              videoLine: tools.parseStageDirectionLine('play video opening_movie title "Opening Movie" volume 80 from 2 to 12 cover no-skip'),
              shakeLine: tools.parseStageDirectionLine("shake heavy short"),
              flashLine: tools.parseStageDirectionLine("flash red strong long"),
              zoomLine: tools.parseStageDirectionLine("zoom out heavy right"),
              panLine: tools.parseStageDirectionLine("pan left light"),
              filterLine: tools.parseStageDirectionLine("filter memory soft"),
              clearFilterLine: tools.parseStageDirectionLine("clear filter"),
              blurLine: tools.parseStageDirectionLine("blur right strong"),
              clearBlurLine: tools.parseStageDirectionLine("clear blur"),
              particleLine: tools.parseStageDirectionLine("particle snow heavy fast"),
              particleStopLine: tools.parseStageDirectionLine("particle stop"),
              creditsLine: tools.parseStageDirectionLine('credits title "STAFF" subtitle "Thanks for playing" duration 24 light no-skip lines "企划：Tony|剧本：Tony"'),
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
              directorBlocks,
              directorSummary: tools.summarizeScriptDraftBlocks(directorBlocks),
              directorPreview: tools.buildScriptDraftPreviewLines(directorBlocks, 5),
              atmosphereBlocks,
              atmosphereSummary: tools.summarizeScriptDraftBlocks(atmosphereBlocks),
              atmospherePreview: tools.buildScriptDraftPreviewLines(atmosphereBlocks, 6),
              textSpeedBlocks,
              textSpeedPreview: tools.buildScriptDraftPreviewLines(textSpeedBlocks, 4),
              choiceEffectBlocks,
              choiceEffectPreview: tools.buildScriptDraftPreviewLines(choiceEffectBlocks, 2),
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
        self.assertEqual(payload["choiceEffectAdd"], {
            "type": "variable_add",
            "variableHint": "affection",
            "value": 1,
        })
        self.assertEqual(payload["choiceEffectSet"], {
            "type": "variable_set",
            "variableHint": "met",
            "value": True,
        })
        self.assertEqual(payload["choiceOptionEffectLine"], {
            "text": "拉住她",
            "targetHint": "rooftop",
            "effects": [
                {"type": "variable_add", "variableHint": "affection", "value": 1},
                {"type": "variable_set", "variableHint": "met", "value": True},
                {"type": "variable_set", "variableHint": "route", "value": "good"},
            ],
        })
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
        self.assertEqual(payload["dialogueSpeedLine"], {
            "type": "dialogue",
            "speakerName": "悠奈",
            "text": "快跑！",
            "textSpeed": "fast",
        })
        self.assertEqual(payload["quotedDialogueSpeedLine"], {
            "type": "dialogue",
            "speakerName": "悠奈",
            "text": "别眨眼。",
            "textSpeed": "instant",
        })
        self.assertEqual(payload["narrationSpeedLine"], {
            "type": "narration",
            "text": "时间像被拉长。",
            "textSpeed": "slow",
        })
        self.assertEqual(payload["narrationLine"], {"type": "narration", "text": "雨声变大了。"})
        self.assertEqual(payload["speedLine"], {"textSpeed": "instant"})
        self.assertEqual(payload["stageLine"], {
            "type": "character_show",
            "characterHint": "yuina",
            "expressionHint": "smile",
            "position": "right",
            "transition": "fade",
            "transitionDurationMs": 600,
        })
        self.assertEqual(payload["stageLineWithStage"], {
            "type": "character_show",
            "characterHint": "yuina",
            "expressionHint": "smile",
            "position": "right",
            "transition": "fade",
            "transitionDurationMs": 600,
            "stage": {
                "offsetX": -8,
                "offsetY": 3,
                "scale": 118,
                "opacity": 90,
                "layer": 2,
                "flipX": True,
            },
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
        self.assertEqual(payload["shakeLine"], {"type": "screen_shake", "intensity": "heavy", "duration": "short"})
        self.assertEqual(payload["flashLine"], {
            "type": "screen_flash",
            "color": "red",
            "intensity": "strong",
            "duration": "long",
        })
        self.assertEqual(payload["zoomLine"], {
            "type": "camera_zoom",
            "action": "zoom_out",
            "strength": "heavy",
            "focus": "right",
        })
        self.assertEqual(payload["panLine"], {"type": "camera_pan", "target": "left", "strength": "light"})
        self.assertEqual(payload["filterLine"], {
            "type": "screen_filter",
            "action": "apply",
            "preset": "memory",
            "strength": "soft",
        })
        self.assertEqual(payload["clearFilterLine"], {
            "type": "screen_filter",
            "action": "clear",
            "preset": "memory",
            "strength": "medium",
        })
        self.assertEqual(payload["blurLine"], {
            "type": "depth_blur",
            "action": "apply",
            "focus": "right",
            "strength": "strong",
        })
        self.assertEqual(payload["clearBlurLine"], {
            "type": "depth_blur",
            "action": "clear",
            "focus": "center",
            "strength": "medium",
        })
        self.assertEqual(payload["particleLine"], {
            "type": "particle_effect",
            "action": "start",
            "preset": "snow",
            "intensity": "heavy",
            "speed": "fast",
        })
        self.assertEqual(payload["particleStopLine"], {
            "type": "particle_effect",
            "action": "stop",
            "preset": "snow",
            "intensity": "medium",
            "speed": "medium",
        })
        self.assertEqual(payload["creditsLine"], {
            "type": "credits_roll",
            "title": "STAFF",
            "subtitle": "Thanks for playing",
            "lines": ["企划：Tony", "剧本：Tony"],
            "durationSeconds": 24,
            "background": "light",
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
        self.assertEqual([block["type"] for block in payload["directorBlocks"]], [
            "screen_shake",
            "screen_flash",
            "camera_zoom",
            "camera_pan",
            "credits_roll",
        ])
        self.assertEqual(payload["directorSummary"], {
            "dialogue": 0,
            "narration": 0,
            "choice": 0,
            "stage": 5,
            "route": 0,
            "total": 5,
        })
        self.assertIn("演出：震屏：heavy / short", payload["directorPreview"][0])
        self.assertIn("演出：片尾字幕：STAFF", payload["directorPreview"][4])
        self.assertEqual([block["type"] for block in payload["atmosphereBlocks"]], [
            "screen_filter",
            "screen_filter",
            "depth_blur",
            "depth_blur",
            "particle_effect",
            "particle_effect",
        ])
        self.assertEqual(payload["atmosphereSummary"], {
            "dialogue": 0,
            "narration": 0,
            "choice": 0,
            "stage": 6,
            "route": 0,
            "total": 6,
        })
        self.assertIn("演出：滤镜：memory / soft", payload["atmospherePreview"][0])
        self.assertIn("演出：关闭滤镜", payload["atmospherePreview"][1])
        self.assertIn("演出：景深：right / strong", payload["atmospherePreview"][2])
        self.assertIn("演出：停止粒子", payload["atmospherePreview"][5])
        self.assertEqual([block["type"] for block in payload["textSpeedBlocks"]], [
            "dialogue",
            "narration",
            "dialogue",
        ])
        self.assertEqual(payload["textSpeedBlocks"][0]["textSpeed"], "fast")
        self.assertEqual(payload["textSpeedBlocks"][1]["textSpeed"], "slow")
        self.assertEqual(payload["textSpeedBlocks"][2]["textSpeed"], "instant")
        self.assertEqual(payload["textSpeedBlocks"][2]["voiceHint"], "yuina_002")
        self.assertIn("speed: fast", payload["textSpeedPreview"][0])
        self.assertIn("voice: yuina_002", payload["textSpeedPreview"][2])
        self.assertIn("speed: instant", payload["textSpeedPreview"][2])
        self.assertEqual(payload["choiceEffectBlocks"], [{
            "type": "choice",
            "options": [
                {
                    "text": "拉住她",
                    "targetHint": "rooftop",
                    "effects": [
                        {"type": "variable_add", "variableHint": "affection", "value": 1},
                        {"type": "variable_add", "variableHint": "courage", "value": 2},
                        {"type": "variable_set", "variableHint": "met", "value": True},
                    ],
                },
                {
                    "text": "先道歉",
                    "effects": [
                        {"type": "variable_add", "variableHint": "affection", "value": -1},
                        {"type": "variable_set", "variableHint": "route", "value": "apology"},
                    ],
                },
            ],
        }])
        self.assertIn("affection +1", payload["choiceEffectPreview"][0])
        self.assertIn("met=true", payload["choiceEffectPreview"][0])


if __name__ == "__main__":
    unittest.main()
