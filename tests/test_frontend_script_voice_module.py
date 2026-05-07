from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "script_voice.js"


class FrontendScriptVoiceModuleTests(unittest.TestCase):
    def test_script_voice_helpers_work_without_browser_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.TonyNaEditorScriptVoice;
            const entry = {{
              type: "dialogue",
              sceneId: "scene_a",
              characterId: "char_a",
              chapterId: "chapter_a",
              blockId: "block_1",
              blockIndex: 2,
              chapterName: "序章",
              sceneName: "雨夜走廊",
              speakerName: "悠奈",
              expressionName: "担心",
              text: "你真的听见了吗？",
              voiceStatus: "missing",
              voiceAssetId: "",
              voiceFileExists: false,
              issues: ["missing_voice", "too_long"],
              previousContext: {{ label: "旁白", text: "雨声贴着窗沿落下。" }},
              nextContext: {{ label: "悠奈", text: "不要回头。" }},
            }};
            const uploadFiles = [
              {{ name: "line01.wav", data: "payload-a" }},
              {{ name: "line01.wav", data: "payload-b" }},
              {{ name: "lost.wav", data: "payload-c" }},
              {{ name: "", data: "ignored" }},
            ];
            const matchResult = {{
              matchedCount: "2",
              unmatchedFiles: [
                {{ fileName: "line01.wav", reason: "文件名太泛" }},
                {{ fileName: "lost.wav", reason: "找不到目标" }},
                {{ fileName: "missing_payload.wav", reason: "没有上传载荷" }},
              ],
              ambiguousFiles: [
                {{
                  fileName: "line01.wav",
                  reason: "多个候选",
                  candidates: [
                    {{ assetId: "voice_b", assetName: "悠奈_序章_002" }},
                    {{ assetId: "voice_a", assetName: "悠奈_序章_001" }},
                  ],
                }},
                {{ fileName: "ghost.wav", reason: "没有载荷", candidates: [] }},
              ],
            }};
            const reviewSession = tools.buildVoiceMatchReviewSession(uploadFiles, matchResult, {{
              nowIso: () => "2026-05-07T00:00:00.000Z",
            }});
            const exportEntries = [
              entry,
              {{
                type: "narration",
                blockIndex: 3,
                chapterId: "chapter_a",
                chapterName: "序章",
                sceneName: "雨夜走廊",
                text: "窗外忽然闪过一道白光。",
                voiceStatus: "not_required",
                issues: ["placeholder"],
              }},
              {{
                type: "choice",
                blockIndex: 4,
                chapterId: "chapter_a",
                chapterName: "序章",
                sceneName: "雨夜走廊",
                text: "追上去 / 留在原地",
                voiceStatus: "not_required",
                issues: [],
              }},
              {{
                ...entry,
                blockId: "block_ready",
                characterId: "char_a",
                chapterId: "chapter_a",
                blockIndex: 5,
                voiceStatus: "voiced",
                voiceAssetId: "voice_ready",
                voiceFileExists: true,
                voiceName: "悠奈_已就绪",
                voiceAssetPath: "voices/ready.ogg",
                issues: [],
              }},
              {{
                ...entry,
                blockId: "block_other",
                characterId: "char_b",
                chapterId: "chapter_b",
                blockIndex: 6,
                voiceAssetId: "",
                voiceFileExists: false,
              }},
            ];
            const exportOptions = {{
              projectTitle: "雨夜样章",
              filterSummaryText: "角色=悠奈 / 语音=待绑",
              exportedAt: "2026-05-07T00:00:00.000Z",
              now: "2026-05-07T08:00:00.000Z",
              formatDate: () => "2026/05/07 00:00",
              formatCsvCell: (value) => `"${{String(value ?? "").replaceAll('"', '""')}}"`,
              sanitizeFileName: (value) => String(value ?? "")
                .trim()
                .replace(/[\\\\/:*?"<>|]/g, "_")
                .replace(/\\s+/g, "_")
                .replace(/_+/g, "_")
                .replace(/^_+|_+$/g, ""),
              getScriptTypeLabel: (type) => type === "dialogue" ? "台词" : type === "narration" ? "旁白" : "选项",
              getScriptIssueFilterLabel: (issue) => issue === "missing_voice" ? "待绑语音" : issue === "placeholder" ? "待补正文" : `问题:${{issue}}`,
              getScriptCharacterFilterLabel: (characterId) => characterId === "char_a" ? "悠奈" : "全部角色",
              getScriptChapterFilterLabel: (chapterId) => chapterId === "chapter_a" ? "序章" : "全部章节",
              getSafeScriptCharacterFilter: (characterId) => characterId === "char_a" ? "char_a" : "all",
              getSafeScriptChapterFilter: (chapterId) => chapterId === "chapter_a" ? "chapter_a" : "all",
            }};
            const voiceSheetEntries = tools.getVoiceSheetEntries(
              exportEntries,
              {{ characterId: "char_a", chapterId: "chapter_a" }},
              exportOptions
            );
            const result = {{
              keys: Object.keys(tools).sort(),
              placeholderItems: [
                tools.entryToVoicePlaceholderItem(entry),
                tools.entryToVoicePlaceholderItem({{ sceneId: "scene_a" }}),
              ],
              workflow: [
                tools.getScriptVoiceWorkflowState(entry),
                tools.getScriptVoiceWorkflowLabel(entry),
                tools.getScriptVoiceWorkflowState({{ ...entry, voiceAssetId: "voice_1" }}),
                tools.getScriptVoiceWorkflowLabel({{ ...entry, voiceAssetId: "voice_1" }}),
                tools.getScriptVoiceWorkflowState({{ ...entry, voiceAssetId: "voice_1", voiceFileExists: true }}),
                tools.getScriptVoiceWorkflowLabel({{ ...entry, voiceAssetId: "voice_1", voiceFileExists: true }}),
                tools.getScriptVoiceWorkflowState({{ type: "narration" }}),
                tools.getScriptVoiceWorkflowLabel({{ type: "narration" }}),
              ],
              suggested: [
                tools.buildSuggestedVoiceBaseName(entry),
                tools.buildSuggestedVoiceFileName(entry, {{
                  sanitizeFileName: (value) => String(value).replaceAll(" ", "_").replaceAll("/", "_"),
                }}),
                tools.buildSuggestedVoiceBaseName({{ ...entry, voiceName: "custom_voice" }}),
                tools.buildSuggestedVoiceFileName({{ ...entry, voiceAssetPath: "voice/custom_line.ogg" }}),
              ],
              statusTexts: [
                tools.getScriptVoiceStatusText("missing"),
                tools.getScriptVoiceStatusText("voiced"),
                tools.getScriptVoiceStatusText("not_required"),
              ],
              alert: tools.buildVoiceFileMatchAlertMessage(matchResult),
              emptyAlert: tools.buildVoiceFileMatchAlertMessage({{ matchedCount: 0 }}),
              reviewSession,
              selectIds: [
                tools.getVoiceMatchReviewSelectId("ambiguous", 2),
                tools.getVoiceMatchReviewSelectId("unmatched", 0),
              ],
              targets: tools.getAvailableManualVoiceMatchTargets({{
                assetList: [
                  {{ id: "voice_a", type: "voice", fileExists: false }},
                  {{ id: "voice_ready", type: "voice", fileExists: true }},
                  {{ id: "bgm_a", type: "bgm", fileExists: false }},
                ],
              }}).map((asset) => asset.id),
              defaultTargets: [
                tools.getDefaultVoiceMatchTargetId(
                  {{ candidates: [{{ assetId: "voice_b" }}, {{ assetId: "voice_a" }}] }},
                  [{{ id: "voice_a" }}, {{ id: "voice_c" }}]
                ),
                tools.getDefaultVoiceMatchTargetId({{ candidates: [{{ assetId: "missing" }}] }}, [{{ id: "voice_a" }}]),
                tools.getDefaultVoiceMatchTargetId({{ candidates: [] }}, []),
              ],
              copyText: tools.buildScriptEntryCopyText(entry, {{
                projectTitle: "雨夜样章",
                getScriptTypeLabel: (type) => type === "dialogue" ? "台词" : "其他",
                getScriptIssueFilterLabel: (issue) => issue === "missing_voice" ? "待绑语音" : `问题:${{issue}}`,
              }}),
              scriptTxt: tools.buildScriptTxtContent(exportEntries.slice(0, 3), exportEntries.length, exportOptions),
              scriptCsv: tools.buildScriptCsvContent(exportEntries.slice(0, 3), exportEntries.length, exportOptions),
              voiceSheetEntries: voiceSheetEntries.map((item) => item.blockId),
              voiceSheetCsv: tools.buildScriptVoiceSheetContent(
                voiceSheetEntries,
                tools.getVoiceSheetEntries(exportEntries, {{}}, exportOptions).length,
                {{ characterId: "char_a", chapterId: "chapter_a" }},
                exportOptions
              ),
              fileNames: [
                tools.buildScriptExportFileName("csv", exportOptions),
                tools.buildScriptExportFileName("txt", exportOptions),
                tools.buildScriptVoiceSheetFileName({{ characterId: "char_a", chapterId: "chapter_a" }}, exportOptions),
                tools.buildCharacterVoiceBriefFileName({{ displayName: "悠奈" }}, exportOptions),
                tools.buildChapterVoiceBriefFileName({{ name: "序章" }}, exportOptions),
                tools.buildProjectVoiceBriefFileName(exportOptions),
              ],
            }};
            process.stdout.write(JSON.stringify(result));
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
        self.assertIn("buildVoiceMatchReviewSession", payload["keys"])
        self.assertEqual(payload["placeholderItems"][0], {"sceneId": "scene_a", "blockId": "block_1"})
        self.assertIsNone(payload["placeholderItems"][1])
        self.assertEqual(
            payload["workflow"],
            [
                "missing_binding",
                "还没建语音条目",
                "placeholder",
                "已建占位，待上传真实文件",
                "ready",
                "语音文件已就绪",
                "not_required",
                "不需要语音",
            ],
        )
        self.assertEqual(payload["suggested"][0], "悠奈_序章_雨夜走廊_003")
        self.assertEqual(payload["suggested"][1], "悠奈_序章_雨夜走廊_003.wav")
        self.assertEqual(payload["suggested"][2], "custom_voice")
        self.assertEqual(payload["suggested"][3], "custom_line.ogg")
        self.assertEqual(payload["statusTexts"], ["待绑语音", "已绑语音", "不需要语音"])
        self.assertIn("已成功匹配 2 个语音文件。", payload["alert"])
        self.assertIn("这些文件暂时没有自动匹配成功（3 个）", payload["alert"])
        self.assertIn("- line01.wav：文件名太泛", payload["alert"])
        self.assertIn("这些文件有多个疑似目标，暂时没有自动乱绑（2 个）", payload["alert"])
        self.assertIn("- line01.wav：悠奈_序章_002 / 悠奈_序章_001", payload["alert"])
        self.assertEqual(payload["emptyAlert"], "")
        self.assertEqual(payload["reviewSession"]["createdAt"], "2026-05-07T00:00:00.000Z")
        self.assertEqual(payload["reviewSession"]["matchedCount"], 2)
        self.assertEqual([item["file"]["data"] for item in payload["reviewSession"]["unmatchedFiles"]], ["payload-a", "payload-c"])
        self.assertEqual([item["file"]["data"] for item in payload["reviewSession"]["ambiguousFiles"]], ["payload-b"])
        self.assertEqual(payload["selectIds"], ["voiceMatchReview-ambiguous-2", "voiceMatchReview-unmatched-0"])
        self.assertEqual(payload["targets"], ["voice_a"])
        self.assertEqual(payload["defaultTargets"], ["voice_a", "voice_a", ""])
        self.assertIn("项目：雨夜样章", payload["copyText"])
        self.assertIn("类型：台词", payload["copyText"])
        self.assertIn("问题标签：待绑语音 / 问题:too_long", payload["copyText"])
        self.assertIn("上一句：旁白：雨声贴着窗沿落下。", payload["copyText"])
        self.assertIn("下一句：悠奈：不要回头。", payload["copyText"])
        self.assertIn("雨夜样章 · Tony Na Engine 台本导出", payload["scriptTxt"])
        self.assertIn("当前筛选：角色=悠奈 / 语音=待绑", payload["scriptTxt"])
        self.assertIn("【章节】序章", payload["scriptTxt"])
        self.assertIn("  - 悠奈：你真的听见了吗？ （待绑语音）", payload["scriptTxt"])
        self.assertIn("  - [旁白] 窗外忽然闪过一道白光。", payload["scriptTxt"])
        self.assertTrue(payload["scriptCsv"].startswith("\ufeff"))
        self.assertIn('"项目名","雨夜样章"', payload["scriptCsv"])
        self.assertIn('"章节","场景","卡片序号","内容类型"', payload["scriptCsv"])
        self.assertIn('"序章","雨夜走廊","3","台词","悠奈","担心"', payload["scriptCsv"])
        self.assertEqual(payload["voiceSheetEntries"], ["block_1"])
        self.assertIn('"当前范围","角色=悠奈 / 章节=序章"', payload["voiceSheetCsv"])
        self.assertIn('"目标语音条目名","目标录音文件名"', payload["voiceSheetCsv"])
        self.assertIn('"悠奈_序章_雨夜走廊_003","悠奈_序章_雨夜走廊_003.wav"', payload["voiceSheetCsv"])
        self.assertEqual(
            payload["fileNames"],
            [
                "雨夜样章_script_角色=悠奈_语音=待绑_20260507.csv",
                "雨夜样章_script_角色=悠奈_语音=待绑_20260507.txt",
                "雨夜样章_voice_sheet_悠奈_序章_20260507.csv",
                "雨夜样章_voice_delivery_悠奈_20260507.txt",
                "雨夜样章_voice_delivery_序章_20260507.txt",
                "雨夜样章_voice_delivery_project_20260507.txt",
            ],
        )


if __name__ == "__main__":
    unittest.main()
