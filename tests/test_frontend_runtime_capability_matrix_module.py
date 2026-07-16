from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
CATALOG_MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "story_block_catalog.js"
PROJECT_SETTINGS_MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "project_settings.js"
DIALOG_BOX_MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "dialog_box_readability.js"
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "runtime_capability_matrix.js"


class FrontendRuntimeCapabilityMatrixModuleTests(unittest.TestCase):
    def test_runtime_capability_matrix_flags_partial_and_unknown_runtime_coverage(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(CATALOG_MODULE_PATH))}, "utf8"), context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const catalogTools = context.window.CanvasiaEditorStoryBlockCatalog;
            const tools = context.window.CanvasiaEditorRuntimeCapabilityMatrix;
            const data = {{
              project: {{ title: "Runtime Demo" }},
              assetList: [
                {{ id: "bg_room", type: "background", name: "教室", fileExists: true }},
                {{ id: "scene_3d", type: "scene3d", name: "3D 教室", fileExists: true }},
                {{ id: "op_video", type: "video", name: "OP", fileExists: true }},
              ],
              chapters: [
                {{
                  chapterId: "chapter_1",
                  name: "第1章",
                  scenes: [
                    {{
                      id: "scene_start",
                      name: "开场",
                      blocks: [
                        {{ id: "bg", type: "background", assetId: "bg_room" }},
                        {{ id: "line", type: "dialogue", speakerId: "char_a", text: "你好。" }},
                        {{ id: "scene3d", type: "background", assetId: "scene_3d" }},
                        {{ id: "wait", type: "wait", durationSeconds: 1.2 }},
                        {{ id: "op", type: "video_play", assetId: "op_video" }},
                        {{ id: "future", type: "live2d_pose", characterId: "char_a" }},
                      ],
                    }},
                  ],
                }},
              ],
            }};
            const matrix = tools.buildRuntimeCapabilityMatrix(data);
            const digest = tools.getRuntimeCapabilityStatusDigest(matrix);
            const markdown = tools.buildRuntimeCapabilityMarkdown(matrix, {{
              projectTitle: "Runtime Demo",
              generatedAt: "2026-07-04 04:00:00",
            }});
            const csv = tools.buildRuntimeCapabilityCsv(matrix);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              matrix,
              digest,
              markdown,
              csv,
              capabilityRows: tools.CAPABILITY_ROWS,
              catalogRuntimeRows: catalogTools.getRuntimeCapabilityRows(),
              labels: [
                tools.getRuntimeStatusLabel("full"),
                tools.getRuntimeStatusLabel("partial"),
                tools.getRuntimeStatusLabel("unknown"),
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
        self.assertIn("buildRuntimeCapabilityMatrix", payload["keys"])
        self.assertIn("buildRuntimeAcceptanceChecklist", payload["keys"])
        self.assertIn("buildVnEssentialsAudit", payload["keys"])
        self.assertIn("buildRuntimeCapabilityMarkdown", payload["keys"])
        self.assertIn("buildRuntimeCapabilityCsv", payload["keys"])
        self.assertEqual(len(payload["capabilityRows"]), len(payload["catalogRuntimeRows"]))
        self.assertTrue(any(row["type"] == "wait" for row in payload["capabilityRows"]))
        summary = payload["matrix"]["summary"]
        self.assertEqual(summary["totalBlockCount"], 6)
        self.assertEqual(summary["usedTypeCount"], 5)
        self.assertEqual(summary["fullUsedTypeCount"], 2)
        self.assertEqual(summary["partialUsedTypeCount"], 2)
        self.assertEqual(summary["unknownUsedTypeCount"], 1)
        self.assertEqual(summary["scene3dBackgroundCount"], 1)
        self.assertEqual(summary["issueCount"], 3)
        acceptance_summary = payload["matrix"]["acceptance"]["summary"]
        self.assertGreaterEqual(acceptance_summary["itemCount"], 7)
        self.assertGreaterEqual(acceptance_summary["blockerCount"], 1)
        self.assertGreaterEqual(acceptance_summary["nativeItemCount"], 2)
        acceptance_titles = [item["title"] for item in payload["matrix"]["acceptance"]["items"]]
        self.assertTrue(any("视频播放" in title for title in acceptance_titles))
        self.assertTrue(any("3D 场景背景" in title for title in acceptance_titles))
        self.assertTrue(any("live2d_pose" in title for title in acceptance_titles))
        self.assertTrue(any("键鼠、手柄与断连回退" in title for title in acceptance_titles))
        self.assertEqual(payload["digest"]["status"], "blocked")
        issue_titles = [issue["title"] for issue in payload["matrix"]["issues"]]
        self.assertTrue(any("live2d_pose" in title for title in issue_titles))
        self.assertTrue(any("video_play" in title for title in issue_titles))
        self.assertIn("# Runtime Demo Runtime 覆盖矩阵", payload["markdown"])
        self.assertIn("## VN 基础能力成熟度", payload["markdown"])
        self.assertIn("## Runtime 验收清单", payload["markdown"])
        self.assertIn("原生 Runtime", payload["markdown"])
        self.assertIn("3D 场景背景", payload["markdown"])
        self.assertIn('"live2d_pose"', payload["csv"])
        self.assertEqual(payload["labels"], ["完整支持", "需要验收", "未知卡片"])

    def test_runtime_capability_matrix_builds_vn_essentials_audit(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(CATALOG_MODULE_PATH))}, "utf8"), context);
            vm.runInContext(fs.readFileSync({json.dumps(str(PROJECT_SETTINGS_MODULE_PATH))}, "utf8"), context);
            vm.runInContext(fs.readFileSync({json.dumps(str(DIALOG_BOX_MODULE_PATH))}, "utf8"), context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorRuntimeCapabilityMatrix;
            const data = {{
              project: {{
                title: "VN Baseline Demo",
                runtimeSettings: {{ formalSaveSlotCount: 6 }},
                dialogBoxConfig: {{
                  backgroundOpacity: 12,
                  backgroundColor: "#ffffff",
                  textColor: "#f8fbff",
                  speakerColor: "#f8fbff",
                  widthPercent: 60,
                  minHeight: 96,
                  paddingX: 8,
                  paddingY: 6,
                }},
                gameUiConfig: {{ preset: "default" }},
              }},
              assetList: [
                {{ id: "bg_room", type: "background", name: "教室", fileExists: true }},
                {{ id: "bgm_a", type: "bgm", name: "日常", fileExists: true }},
                {{ id: "bgm_b", type: "bgm", name: "告白", fileExists: true }},
                {{ id: "font_title", type: "font", name: "标题字体", fileExists: true }},
                {{ id: "op_video", type: "video", name: "OP", fileExists: true }},
              ],
              chapters: [
                {{
                  chapterId: "chapter_1",
                  name: "第1章",
                  scenes: [
                    {{
                      id: "scene_start",
                      name: "开场",
                      blocks: [
                        {{ id: "bg", type: "background", assetId: "bg_room", transition: "none" }},
                        {{ id: "music_a", type: "music_play", assetId: "bgm_a", endMode: "until_next_music", fadeInMs: 0 }},
                        {{ id: "line_1", type: "dialogue", speakerId: "hero", text: "第一句台词。" }},
                        {{ id: "line_2", type: "dialogue", speakerId: "hero", text: "第二句台词。" }},
                        {{ id: "line_3", type: "dialogue", speakerId: "hero", text: "第三句台词。" }},
                        {{ id: "choice", type: "choice", options: [{{ text: "留下", gotoSceneId: "scene_next" }}, {{ text: "离开", gotoSceneId: "scene_next" }}] }},
                        {{ id: "music_b", type: "music_play", assetId: "bgm_b", endMode: "until_next_music", fadeInMs: 0 }},
                      ],
                    }},
                    {{
                      id: "scene_next",
                      name: "后续",
                      blocks: [
                        {{ id: "next_text", type: "narration", text: "没有背景的下一场。" }},
                      ],
                    }},
                  ],
                }},
              ],
            }};
            const audit = tools.buildVnEssentialsAudit(data);
            const matrix = tools.buildRuntimeCapabilityMatrix(data);
            const markdown = tools.buildRuntimeCapabilityMarkdown(matrix, {{ projectTitle: "VN Baseline Demo" }});
            process.stdout.write(JSON.stringify({{
              audit,
              matrixEssentials: matrix.essentials,
              markdown,
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
        audit = payload["audit"]
        self.assertEqual(audit["status"], "needs_fix")
        self.assertLess(audit["summary"]["score"], 80)
        self.assertEqual(payload["matrixEssentials"]["summary"]["issueCount"], audit["summary"]["issueCount"])
        issue_codes = {issue["code"] for issue in audit["issues"]}
        self.assertIn("background_coverage", issue_codes)
        self.assertIn("character_stage_missing", issue_codes)
        self.assertIn("bgm_scope_missing", issue_codes)
        self.assertIn("dialog_box_readability", issue_codes)
        self.assertIn("font_asset_unbound", issue_codes)
        area_statuses = {area["id"]: area["status"] for area in audit["areas"]}
        self.assertEqual(area_statuses["audio"], "needs_fix")
        self.assertEqual(area_statuses["textbox"], "needs_fix")
        self.assertIn("多首 BGM 缺少明确播放范围", payload["markdown"])

    def test_vn_essentials_treats_missing_transition_duration_as_editor_default(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(CATALOG_MODULE_PATH))}, "utf8"), context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorRuntimeCapabilityMatrix;
            const data = {{
              project: {{ title: "Transition Defaults" }},
              assetList: [
                {{ id: "bg_room", type: "background", name: "教室", fileExists: true }},
                {{ id: "bg_roof", type: "background", name: "天台", fileExists: true }},
              ],
              chapters: [
                {{
                  chapterId: "chapter_1",
                  scenes: [
                    {{
                      id: "scene_start",
                      blocks: [
                        {{ id: "bg_1", type: "background", assetId: "bg_room", transition: "fade" }},
                        {{ id: "line_1", type: "dialogue", speakerId: "hero", text: "第一句。" }},
                        {{ id: "show_1", type: "character_show", characterId: "hero", position: "left", transition: "fade" }},
                        {{ id: "show_2", type: "character_show", characterId: "friend", position: "right", transition: "slide" }},
                        {{ id: "bg_2", type: "background", assetId: "bg_roof", transition: "crossfade" }},
                        {{ id: "show_3", type: "character_show", characterId: "hero", position: "center", transition: "rise" }},
                      ],
                    }},
                  ],
                }},
              ],
            }};
            const audit = tools.buildVnEssentialsAudit(data);
            process.stdout.write(JSON.stringify(audit.issues.map((issue) => issue.code)));
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
        issue_codes = set(json.loads(completed.stdout))
        self.assertNotIn("background_transition_missing", issue_codes)
        self.assertNotIn("character_transition_missing", issue_codes)


if __name__ == "__main__":
    unittest.main()
