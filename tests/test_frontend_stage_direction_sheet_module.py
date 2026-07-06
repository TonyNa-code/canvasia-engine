from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "stage_direction_sheet.js"


class FrontendStageDirectionSheetModuleTests(unittest.TestCase):
    def test_stage_direction_sheet_helpers_export_markdown_and_csv(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorStageDirectionSheet;
            const data = {{
              project: {{ title: "Demo Project" }},
              chapters: [{{ id: "chapter_1", name: "第1章" }}],
              assetList: [
                {{ id: "bg_classroom", type: "background", name: "黄昏教室", fileExists: true }},
                {{ id: "sprite_hero", type: "sprite", name: "女主微笑", fileExists: true }},
                {{ id: "sprite_rival", type: "sprite", name: "转学生", fileExists: true }},
                {{ id: "sprite_missing", type: "sprite", name: "破损立绘", fileExists: false }},
              ],
              characters: [
                {{
                  id: "hero",
                  displayName: "蓝白女主",
                  defaultPosition: "center",
                  defaultSpriteId: "sprite_hero",
                  presentation: {{ mode: "sprite", fallbackSpriteAssetId: "sprite_hero" }},
                  expressions: [
                    {{ id: "smile", name: "微笑", spriteAssetId: "sprite_hero" }},
                    {{ id: "sad", name: "难过", spriteAssetId: "sprite_missing" }},
                  ],
                }},
                {{
                  id: "friend",
                  displayName: "同桌",
                  defaultPosition: "left",
                  defaultSpriteId: "",
                  expressions: [],
                }},
                {{
                  id: "rival",
                  displayName: "转学生",
                  defaultPosition: "right",
                  defaultSpriteId: "sprite_rival",
                  expressions: [
                    {{ id: "smile", name: "微笑", spriteAssetId: "sprite_rival" }},
                  ],
                }},
              ],
              scenes: [
                {{
                  id: "scene_start",
                  chapterId: "chapter_1",
                  name: "教室黄昏",
                  blocks: [
                    {{ id: "block_bg", type: "background", assetId: "bg_classroom" }},
                    {{ id: "block_line_1", type: "dialogue", speakerId: "hero", expressionId: "smile", text: "今天也留下来吗？" }},
                    {{ id: "block_show", type: "character_show", characterId: "hero", expressionId: "smile", position: "right" }},
                    {{ id: "block_show_rival", type: "character_show", characterId: "rival", expressionId: "smile", position: "right", transition: "fade", transitionDurationMs: 500, stage: {{ offsetX: 0, offsetY: 0, scale: 170, opacity: 25, layer: 0, flipX: false }} }},
                    {{ id: "block_line_2", type: "dialogue", speakerId: "hero", expressionId: "sad", text: "只待一会儿。" }},
                    {{ id: "block_line_3", type: "dialogue", speakerId: "rival", expressionId: "smile", text: "那我也留下。" }},
                    {{ id: "block_hide", type: "character_hide", characterId: "friend" }},
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
              ],
            }};
            const sheet = tools.buildStageDirectionSheet(data);
            const autoFixPlan = tools.buildStageDirectionAutoFixPlan(data);
            const digest = tools.getStageDirectionStatusDigest(sheet);
            const markdown = tools.buildStageDirectionSheetMarkdown(sheet, {{
              projectTitle: "Demo Project",
              generatedAt: "2026-05-10 23:00:00",
            }});
            const csv = tools.buildStageDirectionSheetCsv(sheet);
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
        self.assertIn("buildStageDirectionSheet", payload["keys"])
        self.assertIn("buildStageDirectionAutoFixPlan", payload["keys"])
        self.assertIn("buildStageDirectionAutoFixSummary", payload["keys"])
        self.assertIn("buildStageContinuityAudit", payload["keys"])
        self.assertIn("buildStageDirectionSheetMarkdown", payload["keys"])
        self.assertIn("buildStageDirectionSheetCsv", payload["keys"])
        self.assertEqual(payload["sheet"]["summary"]["eventCount"], 7)
        self.assertEqual(payload["sheet"]["summary"]["speakerAutoPlaceCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["missingBackgroundSceneCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["missingVisualCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["compositionCheckpointCount"], 5)
        self.assertGreaterEqual(payload["sheet"]["summary"]["compositionRiskCount"], 2)
        self.assertGreaterEqual(payload["sheet"]["summary"]["overlapRiskCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["lowOpacitySpeakerCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["autoFixSceneCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["autoFixBlockCount"], 2)
        self.assertEqual(payload["sheet"]["summary"]["autoFixOperationCount"], 5)
        self.assertEqual(payload["sheet"]["summary"]["continuityReviewSceneCount"], 2)
        self.assertEqual(payload["sheet"]["summary"]["continuityOpeningRiskSceneCount"], 2)
        self.assertEqual(payload["sheet"]["summary"]["continuityEndingCastSceneCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["continuityEndingCastCharacterCount"], 2)
        self.assertEqual(payload["sheet"]["continuityAudit"]["summary"]["reviewSceneCount"], 2)
        self.assertEqual(payload["sheet"]["continuityAudit"]["summary"]["speakerAutoPlaceSceneCount"], 1)
        self.assertEqual(payload["sheet"]["continuityAudit"]["summary"]["dialogueBeforeStageSceneCount"], 2)
        continuity_by_scene = {row["sceneId"]: row for row in payload["sheet"]["continuityAudit"]["rows"]}
        self.assertEqual(continuity_by_scene["scene_start"]["nextAction"], "补登场卡")
        self.assertIn("结尾仍有 2 名角色在场", continuity_by_scene["scene_start"]["reason"])
        self.assertEqual(continuity_by_scene["scene_roof"]["nextAction"], "先补背景卡")
        self.assertEqual(payload["digest"]["status"], "blocked")
        self.assertTrue(payload["autoFixPlan"]["changed"])
        self.assertEqual(payload["autoFixPlan"]["changedSceneCount"], 1)
        self.assertEqual(payload["autoFixPlan"]["changedBlockCount"], 2)
        self.assertEqual(payload["autoFixPlan"]["operationCount"], 5)
        fixed_blocks = payload["autoFixPlan"]["scenePlans"][0]["scene"]["blocks"]
        self.assertEqual(fixed_blocks[2]["transition"], "fade")
        self.assertEqual(fixed_blocks[2]["transitionDurationMs"], 600)
        self.assertEqual(fixed_blocks[2]["stage"]["scale"], 100)
        self.assertEqual(fixed_blocks[6]["transition"], "fade")
        self.assertEqual(fixed_blocks[6]["transitionDurationMs"], 420)
        self.assertIn("已准备修复 1 个场景", payload["autoFixPlan"]["summary"])
        self.assertIn("dialogue_speaker_not_visible", [issue["code"] for issue in payload["sheet"]["issues"]])
        self.assertIn("stage_geometry_overlap", [issue["code"] for issue in payload["sheet"]["issues"]])
        self.assertIn("stage_speaker_low_opacity", [issue["code"] for issue in payload["sheet"]["issues"]])
        self.assertIn("character_visual_file_missing", [issue["code"] for issue in payload["sheet"]["issues"]])
        self.assertIn("character_hide_not_visible", [issue["code"] for issue in payload["sheet"]["issues"]])
        self.assertIn("# Demo Project 角色舞台调度表", payload["markdown"])
        self.assertIn("可自动补齐参数", payload["markdown"])
        self.assertIn("舞台构图检查", payload["markdown"])
        self.assertIn("场景连续性审计", payload["markdown"])
        self.assertIn("结尾仍有 2 名角色在场", payload["markdown"])
        self.assertIn("转学生", payload["markdown"])
        self.assertIn("蓝白女主", payload["markdown"])
        self.assertIn('"角色"', payload["csv"])
        self.assertIn("构图风险", payload["csv"])
        self.assertIn("连续性下一步", payload["csv"])
        self.assertIn("补登场卡", payload["csv"])
        self.assertIn("立绘可用：女主微笑", payload["csv"])


if __name__ == "__main__":
    unittest.main()
