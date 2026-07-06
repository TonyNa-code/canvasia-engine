from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
CATALOG_MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "story_block_catalog.js"
READABILITY_MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "script_readability.js"
PACING_MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "scene_pacing_advisor.js"
STORY_TEMPLATE_MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "story_templates.js"
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
            vm.runInContext(fs.readFileSync({json.dumps(str(CATALOG_MODULE_PATH))}, "utf8"), context);
            vm.runInContext(fs.readFileSync({json.dumps(str(READABILITY_MODULE_PATH))}, "utf8"), context);
            vm.runInContext(fs.readFileSync({json.dumps(str(PACING_MODULE_PATH))}, "utf8"), context);
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
                        {{ id: "line_dup", type: "dialogue", speakerId: "char_a", expressionId: "smile", text: "你好", voiceAssetId: "voice_dup" }},
                        {{ id: "empty_narration", type: "narration", text: "   " }},
                        {{ id: "line_2", type: "dialogue", speakerId: "char_a", text: "还没配音" }},
                        {{ id: "fx", type: "screen_fade" }},
                        {{
                          id: "choice",
                          type: "choice",
                          options: [
                            {{ id: "a", text: "去屋顶", gotoSceneId: "scene_roof" }},
                            {{ id: "b", text: "这是一个非常非常非常非常非常非常非常长的选项文案，长到按钮区会明显拥挤，甚至需要玩家停下来读完才能理解", gotoSceneId: "scene_missing" }},
                            {{ id: "c", text: "继续听她说", gotoSceneId: "__continue__" }},
                            {{ id: "d", text: "", gotoSceneId: "__continue__" }},
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
                    {{
                      id: "scene_fake_choice",
                      name: "假选项",
                      blocks: [
                        {{ id: "bg", type: "background", assetId: "bg_room" }},
                        {{ id: "music", type: "music_play", assetId: "bgm_room" }},
                        {{ id: "line", type: "dialogue", text: "你要怎么回答？", voiceAssetId: "voice_002" }},
                        {{
                          id: "choice",
                          type: "choice",
                          options: [
                            {{ text: "点头", gotoSceneId: "__continue__" }},
                            {{ text: "沉默", gotoSceneId: "__continue__" }},
                          ],
                        }},
                        {{ id: "fade", type: "screen_fade" }},
                      ],
                    }},
                    {{
                      id: "scene_variable_payoff",
                      name: "未回收变量",
                      blocks: [
                        {{ id: "bg", type: "background", assetId: "bg_hall" }},
                        {{ id: "music", type: "music_play", assetId: "bgm_hall" }},
                        {{ id: "line", type: "dialogue", text: "这个选择会被记住吗？", voiceAssetId: "voice_003" }},
                        {{
                          id: "choice",
                          type: "choice",
                          options: [
                            {{ text: "相信她", gotoSceneId: "__continue__", effects: [{{ type: "variable_add", value: 1 }}] }},
                            {{ text: "保持距离", gotoSceneId: "__continue__", effects: [{{ type: "variable_add", value: 1 }}] }},
                          ],
                        }},
                        {{ id: "fade", type: "screen_fade" }},
                      ],
                    }},
                    {{
                      id: "scene_relationship",
                      name: "关系铺垫",
                      blocks: [
                        {{ id: "bg", type: "background", assetId: "bg_station" }},
                        {{ id: "music", type: "music_play", assetId: "bgm_station" }},
                        {{ id: "line_1", type: "dialogue", text: "其实我一直想问你一件事。", voiceAssetId: "voice_004" }},
                        {{ id: "wait", type: "wait" }},
                        {{ id: "line_2", type: "dialogue", text: "那天你为什么会在那里？", voiceAssetId: "voice_005" }},
                        {{ id: "fade", type: "screen_fade" }},
                      ],
                    }},
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
        self.assertIn("getSceneRecipeSuggestion", payload["keys"])
        self.assertEqual(payload["board"]["summary"]["sceneCount"], 6)
        self.assertGreater(payload["board"]["summary"]["blockedSceneCount"], 0)
        self.assertGreater(payload["board"]["summary"]["warningSceneCount"], 0)
        self.assertEqual(payload["board"]["summary"]["emptySceneCount"], 1)
        self.assertEqual(payload["board"]["summary"]["recipeSuggestionCount"], 5)
        self.assertGreater(payload["board"]["summary"]["missingBackgroundSceneCount"], 0)
        self.assertGreater(payload["board"]["summary"]["missingMusicSceneCount"], 0)
        self.assertEqual(payload["board"]["summary"]["missingVoiceLineCount"], 1)
        self.assertGreater(payload["board"]["summary"]["longTextSceneCount"], 0)
        self.assertGreater(payload["board"]["summary"]["scriptQualityIssueCount"], 0)
        self.assertEqual(payload["board"]["summary"]["scriptEmptyTextSceneCount"], 1)
        self.assertEqual(payload["board"]["summary"]["scriptDuplicateTextSceneCount"], 1)
        self.assertGreaterEqual(payload["board"]["summary"]["scriptChoiceIssueSceneCount"], 1)
        self.assertIn("averagePacingScore", payload["board"]["summary"])
        self.assertGreater(payload["board"]["summary"]["weakPacingSceneCount"], 0)
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
        self.assertIn("scene_script_empty_text", issue_codes)
        self.assertIn("scene_script_duplicate_text", issue_codes)
        self.assertIn("scene_script_choice_empty_text", issue_codes)
        self.assertNotIn("__continue__", json.dumps(payload["board"]["issues"], ensure_ascii=False))
        scenes_by_id = {scene["sceneId"]: scene for scene in payload["board"]["scenes"]}
        self.assertIn("pacingScore", scenes_by_id["scene_start"])
        self.assertGreater(scenes_by_id["scene_start"]["scriptQualityIssueCount"], 0)
        self.assertEqual(scenes_by_id["scene_start"]["scriptEmptyTextCount"], 1)
        self.assertEqual(scenes_by_id["scene_start"]["scriptDuplicateTextCount"], 1)
        self.assertIn("pacingActionSummary", scenes_by_id["scene_roof"])
        self.assertLess(scenes_by_id["scene_roof"]["pacingScore"], scenes_by_id["scene_start"]["pacingScore"])
        self.assertIsNone(scenes_by_id["scene_start"]["recipeSuggestion"])
        self.assertEqual(scenes_by_id["scene_roof"]["recipeSuggestion"]["templateId"], "daily_conversation")
        self.assertEqual(scenes_by_id["scene_empty"]["recipeSuggestion"]["templateId"], "playable_scene")
        self.assertEqual(scenes_by_id["scene_fake_choice"]["recipeSuggestion"]["templateId"], "affection_choice")
        self.assertEqual(scenes_by_id["scene_variable_payoff"]["recipeSuggestion"]["templateId"], "branch_merge")
        self.assertEqual(scenes_by_id["scene_relationship"]["recipeSuggestion"]["templateId"], "relationship_reveal")
        self.assertIn("pacing_branch_without_payoff", scenes_by_id["scene_variable_payoff"]["pacingIssueCodes"])
        self.assertIn("# Demo Project 场景生产看板", payload["markdown"])
        self.assertIn("平均节奏分", payload["markdown"])
        self.assertIn("台词体检", payload["markdown"])
        self.assertIn("节奏建议", payload["markdown"])
        self.assertIn("教室黄昏", payload["markdown"])
        self.assertIn("补日常对话节奏", payload["markdown"])
        self.assertIn('"节奏分"', payload["csv"])
        self.assertIn('"台词体检"', payload["csv"])
        self.assertIn('"屋顶"', payload["csv"])
        self.assertIn('"daily_conversation"', payload["csv"])
        self.assertIn('"branch_merge"', payload["csv"])
        self.assertIn('"relationship_reveal"', payload["csv"])
        self.assertEqual(payload["readyLabel"], "可试玩")

    def test_scene_production_board_reuses_story_template_recommendations_when_available(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(CATALOG_MODULE_PATH))}, "utf8"), context);
            vm.runInContext(fs.readFileSync({json.dumps(str(READABILITY_MODULE_PATH))}, "utf8"), context);
            vm.runInContext(fs.readFileSync({json.dumps(str(PACING_MODULE_PATH))}, "utf8"), context);
            vm.runInContext(fs.readFileSync({json.dumps(str(STORY_TEMPLATE_MODULE_PATH))}, "utf8"), context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorSceneProductionBoard;
            const directVideoSuggestion = tools.getStoryTemplateRecommendationSuggestion({{
              blocks: [
                {{ id: "op", type: "video_play" }},
              ],
            }});
            const directUnknownSuggestion = tools.getStoryTemplateRecommendationSuggestion({{
              blocks: [
                {{ id: "unknown", type: "custom_block" }},
              ],
            }});
            const board = tools.buildSceneProductionBoard({{
              project: {{ title: "Video Project" }},
              chapters: [
                {{
                  chapterId: "chapter_video",
                  name: "OP",
                  scenes: [
                    {{
                      id: "scene_op",
                      name: "片头",
                      blocks: [
                        {{ id: "op", type: "video_play", title: "Opening" }},
                      ],
                    }},
                  ],
                }},
              ],
            }});
            process.stdout.write(JSON.stringify({{
              directVideoSuggestion,
              directUnknownSuggestion,
              board,
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
        self.assertEqual(payload["directVideoSuggestion"]["templateId"], "ending_credits")
        self.assertEqual(payload["directVideoSuggestion"]["source"], "story_template_recommendation")
        self.assertEqual(payload["directUnknownSuggestion"]["templateId"], "opening_intro")
        scene = payload["board"]["scenes"][0]
        self.assertEqual(scene["recipeSuggestion"]["templateId"], "ending_credits")
        self.assertEqual(scene["recipeSuggestion"]["source"], "story_template_recommendation")
        self.assertEqual(payload["board"]["summary"]["recipeSuggestionCount"], 1)


if __name__ == "__main__":
    unittest.main()
