from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
EDITOR_DIR = ROOT_DIR / "prototype_editor"
MODULE_PATHS = [
    EDITOR_DIR / "modules" / "story_block_catalog.js",
    EDITOR_DIR / "modules" / "script_readability.js",
    EDITOR_DIR / "modules" / "scene_pacing_advisor.js",
    EDITOR_DIR / "modules" / "scene_polish.js",
    EDITOR_DIR / "modules" / "audio_cue_sheet.js",
    EDITOR_DIR / "modules" / "project_settings.js",
    EDITOR_DIR / "modules" / "dialog_box_readability.js",
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
              project: {{
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
                gameUiConfig: {{ preset: "stellar" }},
              }},
              assetList: [
                {{ id: "font_main", type: "font", name: "主字体", fileExists: true }},
              ],
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
            const projectPatch = plan.projectPatch;
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
                projectOperationCount: plan.projectOperationCount,
                runtimeSettingOperationCount: plan.runtimeSettingOperationCount,
                dialogBoxOperationCount: plan.dialogBoxOperationCount,
                gameUiOperationCount: plan.gameUiOperationCount,
                projectOperationLabels: plan.projectOperations.map((operation) => operation.label),
                projectPatchSaveSlots: projectPatch.runtimeSettings?.formalSaveSlotCount,
                projectPatchDialogPreset: projectPatch.dialogBoxConfig?.preset,
                projectPatchDialogOpacity: projectPatch.dialogBoxConfig?.backgroundOpacity,
                projectPatchGameUiFontAssetId: projectPatch.gameUiConfig?.fontAssetId,
                pacingAverageScore: plan.pacingAverageScore,
                pacingRoughSceneCount: plan.pacingRoughSceneCount,
                pacingReadySceneCount: plan.pacingReadySceneCount,
                pacingTopIssueCount: plan.pacingSnapshot?.topIssues?.length ?? 0,
                pacingHighlightCount: plan.pacingSnapshot?.sceneHighlights?.length ?? 0,
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
                pacingRoughSceneCount: cleanDigest.plan.pacingRoughSceneCount,
              }},
              receipt: {{
                receiptId: receipt.receiptId,
                generatedAt: receipt.generatedAt,
                projectTitle: receipt.projectTitle,
                safetySnapshotLabel: receipt.safetySnapshotLabel,
                changedSceneCount: receipt.changedSceneCount,
                totalOperationCount: receipt.totalOperationCount,
                projectOperationCount: receipt.projectOperationCount,
                pacingAverageScore: receipt.pacingAverageScore,
                pacingRoughSceneCount: receipt.pacingRoughSceneCount,
                pacingReadySceneCount: receipt.pacingReadySceneCount,
                pacingHighlightCount: receipt.pacingSnapshot?.sceneHighlights?.length ?? 0,
                projectOperationLabels: receipt.projectOperations.map((operation) => operation.label),
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
        self.assertGreater(payload["plan"]["projectOperationCount"], 0)
        self.assertGreater(payload["plan"]["dialogBoxOperationCount"], 0)
        self.assertGreater(payload["plan"]["gameUiOperationCount"], 0)
        self.assertIn("绑定项目字体素材", payload["plan"]["projectOperationLabels"])
        self.assertEqual(payload["plan"]["projectPatchDialogPreset"], "custom")
        self.assertGreaterEqual(payload["plan"]["projectPatchDialogOpacity"], 72)
        self.assertEqual(payload["plan"]["projectPatchGameUiFontAssetId"], "font_main")
        self.assertIsInstance(payload["plan"]["pacingAverageScore"], int)
        self.assertGreaterEqual(payload["plan"]["pacingTopIssueCount"], 1)
        self.assertGreaterEqual(payload["plan"]["pacingHighlightCount"], 1)
        self.assertTrue(payload["digest"]["canApply"])
        self.assertIn("一键发布前整理", payload["digest"]["actionLabel"])
        self.assertIn("1 个场景", payload["digest"]["badgeLabel"])
        self.assertIn("开场", payload["digest"]["helperText"])
        self.assertFalse(payload["cleanPlan"]["changed"])
        self.assertEqual(payload["cleanPlan"]["summary"], "项目基础内容已经比较适合发布前检查")
        self.assertEqual(payload["cleanPlan"]["totalOperationCount"], 0)
        self.assertFalse(payload["cleanDigest"]["canApply"])
        self.assertEqual(payload["cleanDigest"]["actionLabel"], "发布前整理已完成，建议复看节奏")
        self.assertIn("个场景待试玩", payload["cleanDigest"]["badgeLabel"])
        self.assertGreaterEqual(payload["cleanDigest"]["pacingRoughSceneCount"], 1)
        self.assertIn("建议试玩复看", payload["cleanDigest"]["helperText"])
        self.assertEqual(payload["receipt"]["receiptId"], "polish-20260510100000")
        self.assertEqual(payload["receipt"]["generatedAt"], "2026-05-10T10:00:00.000Z")
        self.assertEqual(payload["receipt"]["projectTitle"], "Demo Project")
        self.assertEqual(payload["receipt"]["safetySnapshotLabel"], "发布前整理前自动检查点")
        self.assertEqual(payload["receipt"]["changedSceneCount"], 1)
        self.assertGreater(payload["receipt"]["totalOperationCount"], 0)
        self.assertGreater(payload["receipt"]["projectOperationCount"], 0)
        self.assertIsInstance(payload["receipt"]["pacingAverageScore"], int)
        self.assertGreaterEqual(payload["receipt"]["pacingHighlightCount"], 1)
        self.assertIn("绑定项目字体素材", payload["receipt"]["projectOperationLabels"])
        self.assertEqual(payload["receipt"]["sceneNames"], ["开场"])
        self.assertGreaterEqual(payload["receipt"]["nextActionCount"], 3)
        self.assertIn("重新巡检确认", payload["receipt"]["nextActionLabels"])
        self.assertIn("复看项目设置", payload["receipt"]["nextActionLabels"])
        self.assertIn("run-project-inspection", payload["receipt"]["nextActionActions"])
        self.assertIn("export-project-one-click-polish-receipt", payload["receipt"]["nextActionActions"])
        self.assertIn("project", payload["receipt"]["nextActionScreens"])
        self.assertIn("preview", payload["receipt"]["nextActionScreens"])
        self.assertEqual(payload["receiptFileName"], "demo-project-polish-20260510100000.md")
        self.assertIn("# 发布前整理回执", payload["receiptMarkdown"])
        self.assertIn("| 回执编号 | polish-20260510100000 |", payload["receiptMarkdown"])
        self.assertIn("| 安全检查点 | 发布前整理前自动检查点 |", payload["receiptMarkdown"])
        self.assertIn("| 开场 | scene_intro |", payload["receiptMarkdown"])
        self.assertIn("## 项目级补全", payload["receiptMarkdown"])
        self.assertIn("绑定项目字体素材", payload["receiptMarkdown"])
        self.assertIn("## 节奏体检", payload["receiptMarkdown"])
        self.assertIn("平均节奏分", payload["receiptMarkdown"])
        self.assertIn("重新巡检确认", payload["receiptMarkdown"])
        self.assertIn("导出整理回执", payload["receiptMarkdown"])
        self.assertIn("发布前整理回执：", payload["receiptClipboard"])
        self.assertIn("回执编号：polish-20260510100000", payload["receiptClipboard"])
        self.assertIn("安全检查点：发布前整理前自动检查点", payload["receiptClipboard"])
        self.assertIn("项目级补全：", payload["receiptClipboard"])
        self.assertIn("节奏体检：平均", payload["receiptClipboard"])
        self.assertIn("节奏复看：", payload["receiptClipboard"])
        self.assertIn("下一步：重新巡检确认", payload["receiptClipboard"])
        self.assertEqual(payload["sourceStillUntouched"]["originalBlockCount"], 4)
        self.assertEqual(payload["sourceStillUntouched"]["originalFadeInMs"], 0)
        self.assertEqual(payload["sourceStillUntouched"]["originalEndBlockId"], "missing_block")
        self.assertEqual(payload["sourceStillUntouched"]["originalVoiceAssetId"], "voice_001")

    def test_project_settings_polish_plan_is_merged_into_one_click_polish(self) -> None:
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
            const data = {{
              project: {{
                title: "Settings Only",
                runtimeSettings: {{ formalSaveSlotCount: 4 }},
                dialogBoxConfig: {{
                  backgroundOpacity: 0,
                  backgroundColor: "#ffffff",
                  textColor: "#ffffff",
                  speakerColor: "#ffffff",
                  widthPercent: 55,
                  minHeight: 96,
                  paddingX: 8,
                  paddingY: 6,
                }},
                gameUiConfig: {{ preset: "stellar" }},
              }},
              assetList: [
                {{ id: "font_story", type: "font", name: "正文", fileExists: true }},
              ],
              scenes: Array.from({{ length: 6 }}, (_, index) => ({{
                id: `scene_${{index + 1}}`,
                name: `场景 ${{index + 1}}`,
                blocks: [
                  {{ id: `bg_${{index + 1}}`, type: "background", transition: "fade", transitionDurationMs: 700 }},
                  {{ id: `line_${{index + 1}}`, type: "dialogue", text: "这是一句用于检查文本框可读性的台词。" }},
                  {{ id: `music_${{index + 1}}`, type: "music_play", fadeInMs: 800, fadeOutMs: 800, volume: 80, loop: true, endMode: "until_next_music" }},
                ],
              }})),
            }};
            const settingsPlan = tools.buildProjectSettingsPolishPlan(data);
            const oneClickPlan = tools.buildProjectOneClickPolishPlan(data);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              settingsPlan: {{
                changed: settingsPlan.changed,
                operationCount: settingsPlan.operationCount,
                labels: settingsPlan.operations.map((operation) => operation.label),
                saveSlots: settingsPlan.projectPatch.runtimeSettings?.formalSaveSlotCount,
                dialogPreset: settingsPlan.projectPatch.dialogBoxConfig?.preset,
                dialogOpacity: settingsPlan.projectPatch.dialogBoxConfig?.backgroundOpacity,
                fontAssetId: settingsPlan.projectPatch.gameUiConfig?.fontAssetId,
              }},
              oneClickPlan: {{
                changed: oneClickPlan.changed,
                changedSceneCount: oneClickPlan.changedSceneCount,
                projectOperationCount: oneClickPlan.projectOperationCount,
                totalOperationCount: oneClickPlan.totalOperationCount,
                summary: oneClickPlan.summary,
                pacingAverageScore: oneClickPlan.pacingAverageScore,
                pacingRoughSceneCount: oneClickPlan.pacingRoughSceneCount,
              }},
              sourceStillUntouched: {{
                saveSlots: data.project.runtimeSettings.formalSaveSlotCount,
                dialogOpacity: data.project.dialogBoxConfig.backgroundOpacity,
                fontAssetId: data.project.gameUiConfig.fontAssetId || "",
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
        self.assertIn("buildProjectSettingsPolishPlan", payload["keys"])
        self.assertTrue(payload["settingsPlan"]["changed"])
        self.assertGreaterEqual(payload["settingsPlan"]["operationCount"], 4)
        self.assertIn("提高正式存档位数量", payload["settingsPlan"]["labels"])
        self.assertIn("绑定项目字体素材", payload["settingsPlan"]["labels"])
        self.assertEqual(payload["settingsPlan"]["saveSlots"], 24)
        self.assertEqual(payload["settingsPlan"]["dialogPreset"], "custom")
        self.assertGreaterEqual(payload["settingsPlan"]["dialogOpacity"], 72)
        self.assertEqual(payload["settingsPlan"]["fontAssetId"], "font_story")
        self.assertTrue(payload["oneClickPlan"]["changed"])
        self.assertGreaterEqual(payload["oneClickPlan"]["changedSceneCount"], 0)
        self.assertGreater(payload["oneClickPlan"]["projectOperationCount"], 0)
        self.assertGreaterEqual(payload["oneClickPlan"]["totalOperationCount"], payload["oneClickPlan"]["projectOperationCount"])
        self.assertIn("项目体验设置", payload["oneClickPlan"]["summary"])
        self.assertIsInstance(payload["oneClickPlan"]["pacingAverageScore"], int)
        self.assertEqual(payload["sourceStillUntouched"]["saveSlots"], 4)
        self.assertEqual(payload["sourceStillUntouched"]["dialogOpacity"], 0)
        self.assertEqual(payload["sourceStillUntouched"]["fontAssetId"], "")


if __name__ == "__main__":
    unittest.main()
