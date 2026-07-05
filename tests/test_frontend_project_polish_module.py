from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
EDITOR_DIR = ROOT_DIR / "prototype_editor"
MODULE_PATHS = [
    EDITOR_DIR / "modules" / "script_readability.js",
    EDITOR_DIR / "modules" / "scene_polish.js",
    EDITOR_DIR / "modules" / "audio_cue_sheet.js",
    EDITOR_DIR / "modules" / "project_polish.js",
]


class FrontendProjectPolishModuleTests(unittest.TestCase):
    def test_one_click_project_polish_combines_release_safe_fixes(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            for (const modulePath of {json.dumps([str(path) for path in MODULE_PATHS])}) {{
              vm.runInContext(fs.readFileSync(modulePath, "utf8"), context);
            }}
            const tools = context.window.CanvasiaEditorProjectPolish;
            const longLine = "第一句很短。第二句继续铺垫。第三句把情绪推上去。第四句暂时收束。".repeat(10);
            const data = {{
              chapters: [
                {{ id: "chapter_1", name: "第一章", sceneOrder: ["scene_intro", "scene_clean"] }},
              ],
              scenes: [
                {{
                  id: "scene_intro",
                  chapterId: "chapter_1",
                  name: "开场",
                  blocks: [
                    {{
                      id: "music_opening",
                      type: "music_play",
                      assetId: "bgm_opening",
                      endMode: "after_block",
                      endBlockId: "missing_block",
                      fadeInMs: 0,
                      fadeOutMs: 0,
                      volume: 0
                    }},
                    {{
                      id: "line_long",
                      type: "dialogue",
                      speakerId: "heroine",
                      text: longLine,
                      voiceAssetId: "voice_001",
                      voiceVolume: 72
                    }},
                    {{ id: "bg_room", type: "background", assetId: "bg_room" }},
                    {{ id: "narration_end", type: "narration", text: "走廊尽头传来了脚步声。" }},
                  ],
                }},
                {{
                  id: "scene_clean",
                  chapterId: "chapter_1",
                  name: "干净场景",
                  blocks: [
                    {{ id: "line_ok", type: "dialogue", text: "短句。", textSpeed: "normal" }},
                    {{ id: "music_ok", type: "music_play", fadeInMs: 900, fadeOutMs: 900, volume: 75, loop: true, endMode: "until_next_music" }},
                  ],
                }},
              ],
            }};
            const plan = tools.buildProjectOneClickPolishPlan(data, {{ readable: {{ limit: 80 }} }});
            const digest = tools.getProjectOneClickPolishDigest(data, {{ readable: {{ limit: 80 }}, sceneNameLimit: 1 }});
            const receipt = tools.buildProjectOneClickPolishReceipt(plan, {{
              projectTitle: "Demo Project",
              safetySnapshotLabel: "发布前整理前自动检查点",
              generatedAt: "2026-05-10T10:00:00.000Z",
            }});
            const receiptFileName = tools.buildProjectOneClickPolishReceiptFileName(receipt);
            const receiptMarkdown = tools.buildProjectOneClickPolishReceiptMarkdown(receipt);
            const receiptClipboard = tools.buildProjectOneClickPolishReceiptClipboardSummary(receipt);
            const cleanData = {{
              scenes: [
                {{
                  id: "clean",
                  name: "无需处理",
                  blocks: [
                    {{ id: "line_ok", type: "dialogue", text: "短句。", textSpeed: "normal" }},
                    {{ id: "bg_ok", type: "background", transition: "fade", transitionDurationMs: 700 }},
                    {{ id: "music_ok", type: "music_play", fadeInMs: 900, fadeOutMs: 900, volume: 88, loop: true, endMode: "until_next_music" }},
                  ],
                }},
              ],
            }};
            const cleanPlan = tools.buildProjectOneClickPolishPlan(cleanData);
            const cleanDigest = tools.getProjectOneClickPolishDigest(cleanData);
            const changedScene = plan.scenePlans[0].scene;
            const musicBlock = changedScene.blocks.find((block) => block.id === "music_opening");
            const splitBlocks = changedScene.blocks.filter((block) => block.type === "dialogue");
            const addedSplitBlock = splitBlocks.find((block) => block.id !== "line_long");
            const backgroundBlock = changedScene.blocks.find((block) => block.id === "bg_room");
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              plan: {{
                changed: plan.changed,
                changedSceneCount: plan.changedSceneCount,
                totalOperationCount: plan.totalOperationCount,
                readableSplitCount: plan.readableSplitCount,
                readableAddedBlockCount: plan.readableAddedBlockCount,
                presentationChangedFieldCount: plan.presentationChangedFieldCount,
                audioOperationCount: plan.audioOperationCount,
                firstChangedSceneId: plan.firstChangedSceneId,
                firstChangedBlockId: plan.firstChangedBlockId,
                summary: plan.summary,
                sceneNames: plan.scenePlans.map((scenePlan) => scenePlan.sceneName),
                finalBlockCount: changedScene.blocks.length,
                splitBlockCount: splitBlocks.length,
                addedSplitBlockHasVoice: Boolean(addedSplitBlock?.voiceAssetId),
                addedSplitBlockTextLength: addedSplitBlock?.text?.length ?? 0,
                firstDialogueTextSpeed: splitBlocks[0]?.textSpeed,
                backgroundTransition: backgroundBlock?.transition,
                backgroundDuration: backgroundBlock?.transitionDurationMs,
                musicFadeInMs: musicBlock?.fadeInMs,
                musicFadeOutMs: musicBlock?.fadeOutMs,
                musicVolume: musicBlock?.volume,
                musicEndBlockId: musicBlock?.endBlockId,
              }},
              digest: {{
                canApply: digest.canApply,
                actionLabel: digest.actionLabel,
                badgeLabel: digest.badgeLabel,
                helperText: digest.helperText,
              }},
              cleanPlan: {{
                changed: cleanPlan.changed,
                summary: cleanPlan.summary,
                totalOperationCount: cleanPlan.totalOperationCount,
              }},
              cleanDigest: {{
                canApply: cleanDigest.canApply,
                actionLabel: cleanDigest.actionLabel,
                badgeLabel: cleanDigest.badgeLabel,
                helperText: cleanDigest.helperText,
              }},
              receipt: {{
                receiptId: receipt.receiptId,
                generatedAt: receipt.generatedAt,
                projectTitle: receipt.projectTitle,
                safetySnapshotLabel: receipt.safetySnapshotLabel,
                changedSceneCount: receipt.changedSceneCount,
                totalOperationCount: receipt.totalOperationCount,
                sceneNames: receipt.scenePlans.map((scenePlan) => scenePlan.sceneName),
                nextActionCount: receipt.nextActions.length,
                nextActionLabels: receipt.nextActions.map((action) => action.label),
                nextActionActions: receipt.nextActions.map((action) => action.action),
                nextActionScreens: receipt.nextActions.map((action) => action.screen || ""),
              }},
              receiptFileName,
              receiptMarkdown,
              receiptClipboard,
              sourceStillUntouched: {{
                originalBlockCount: data.scenes[0].blocks.length,
                originalFadeInMs: data.scenes[0].blocks[0].fadeInMs,
                originalEndBlockId: data.scenes[0].blocks[0].endBlockId,
                originalVoiceAssetId: data.scenes[0].blocks[1].voiceAssetId,
              }},
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
        self.assertIn("buildProjectOneClickPolishPlan", payload["keys"])
        self.assertIn("getProjectOneClickPolishDigest", payload["keys"])
        self.assertIn("buildProjectOneClickPolishReceiptMarkdown", payload["keys"])
        self.assertIn("buildProjectOneClickPolishReceiptClipboardSummary", payload["keys"])
        self.assertTrue(payload["plan"]["changed"])
        self.assertEqual(payload["plan"]["changedSceneCount"], 1)
        self.assertEqual(payload["plan"]["firstChangedSceneId"], "scene_intro")
        self.assertEqual(payload["plan"]["firstChangedBlockId"], "line_long")
        self.assertGreater(payload["plan"]["totalOperationCount"], 0)
        self.assertEqual(payload["plan"]["readableSplitCount"], 1)
        self.assertGreater(payload["plan"]["readableAddedBlockCount"], 0)
        self.assertGreater(payload["plan"]["presentationChangedFieldCount"], 0)
        self.assertGreater(payload["plan"]["audioOperationCount"], 0)
        self.assertIn("发布前整理完成", payload["plan"]["summary"])
        self.assertEqual(payload["plan"]["sceneNames"], ["开场"])
        self.assertGreater(payload["plan"]["finalBlockCount"], payload["sourceStillUntouched"]["originalBlockCount"])
        self.assertGreater(payload["plan"]["splitBlockCount"], 1)
        self.assertFalse(payload["plan"]["addedSplitBlockHasVoice"])
        self.assertGreater(payload["plan"]["addedSplitBlockTextLength"], 0)
        self.assertEqual(payload["plan"]["firstDialogueTextSpeed"], "normal")
        self.assertEqual(payload["plan"]["backgroundTransition"], "fade")
        self.assertEqual(payload["plan"]["backgroundDuration"], 700)
        self.assertGreater(payload["plan"]["musicFadeInMs"], 0)
        self.assertGreater(payload["plan"]["musicFadeOutMs"], 0)
        self.assertGreater(payload["plan"]["musicVolume"], 0)
        self.assertNotEqual(payload["plan"]["musicEndBlockId"], "missing_block")
        self.assertTrue(payload["digest"]["canApply"])
        self.assertIn("一键发布前整理", payload["digest"]["actionLabel"])
        self.assertIn("1 个场景可整理", payload["digest"]["badgeLabel"])
        self.assertIn("开场", payload["digest"]["helperText"])
        self.assertFalse(payload["cleanPlan"]["changed"])
        self.assertEqual(payload["cleanPlan"]["summary"], "项目基础内容已经比较适合发布前检查")
        self.assertEqual(payload["cleanPlan"]["totalOperationCount"], 0)
        self.assertFalse(payload["cleanDigest"]["canApply"])
        self.assertEqual(payload["cleanDigest"]["actionLabel"], "发布前整理已完成")
        self.assertEqual(payload["cleanDigest"]["badgeLabel"], "无需处理")
        self.assertEqual(payload["receipt"]["receiptId"], "polish-20260510100000")
        self.assertEqual(payload["receipt"]["generatedAt"], "2026-05-10T10:00:00.000Z")
        self.assertEqual(payload["receipt"]["projectTitle"], "Demo Project")
        self.assertEqual(payload["receipt"]["safetySnapshotLabel"], "发布前整理前自动检查点")
        self.assertEqual(payload["receipt"]["changedSceneCount"], 1)
        self.assertGreater(payload["receipt"]["totalOperationCount"], 0)
        self.assertEqual(payload["receipt"]["sceneNames"], ["开场"])
        self.assertGreaterEqual(payload["receipt"]["nextActionCount"], 3)
        self.assertIn("重新巡检确认", payload["receipt"]["nextActionLabels"])
        self.assertIn("run-project-inspection", payload["receipt"]["nextActionActions"])
        self.assertIn("export-project-one-click-polish-receipt", payload["receipt"]["nextActionActions"])
        self.assertIn("preview", payload["receipt"]["nextActionScreens"])
        self.assertEqual(payload["receiptFileName"], "demo-project-polish-20260510100000.md")
        self.assertIn("# 发布前整理回执", payload["receiptMarkdown"])
        self.assertIn("| 回执编号 | polish-20260510100000 |", payload["receiptMarkdown"])
        self.assertIn("| 安全检查点 | 发布前整理前自动检查点 |", payload["receiptMarkdown"])
        self.assertIn("| 开场 | scene_intro |", payload["receiptMarkdown"])
        self.assertIn("重新巡检确认", payload["receiptMarkdown"])
        self.assertIn("导出整理回执", payload["receiptMarkdown"])
        self.assertIn("发布前整理回执：", payload["receiptClipboard"])
        self.assertIn("回执编号：polish-20260510100000", payload["receiptClipboard"])
        self.assertIn("安全检查点：发布前整理前自动检查点", payload["receiptClipboard"])
        self.assertIn("下一步：重新巡检确认", payload["receiptClipboard"])
        self.assertEqual(payload["sourceStillUntouched"]["originalBlockCount"], 4)
        self.assertEqual(payload["sourceStillUntouched"]["originalFadeInMs"], 0)
        self.assertEqual(payload["sourceStillUntouched"]["originalEndBlockId"], "missing_block")
        self.assertEqual(payload["sourceStillUntouched"]["originalVoiceAssetId"], "voice_001")


if __name__ == "__main__":
    unittest.main()
