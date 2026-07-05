from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "script_readability.js"


class FrontendScriptReadabilityModuleTests(unittest.TestCase):
    def test_script_readability_helpers_work_without_browser_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorScriptReadability;
            const chineseText = "第一句很短。第二句也很短。第三句继续前进。第四句收束。";
            const englishText = "Alice opens the door Bob enters the room Carol smiles";
            const splitCandidate = "第一句很短。第二句也很短。".repeat(18);
            const splitScene = {{
              id: "scene_a",
              blocks: [
                {{
                  id: "block_001",
                  type: "dialogue",
                  speakerId: "heroine",
                  text: splitCandidate,
                  voiceAssetId: "voice_001",
                  voiceVolume: 72,
                  voice: {{ assetId: "voice_nested" }},
                }},
                {{ id: "block_002", type: "narration", text: "短旁白。" }},
                {{ id: "block_003", type: "choice", text: "选择" }},
              ],
            }};
            const blockSplitPlan = tools.buildReadableBlockSplitPlan(splitScene.blocks[0], {{
              blocks: splitScene.blocks,
              limit: 80,
            }});
            const sceneSplitPlan = tools.buildReadableSceneSplitPlan(splitScene, {{ limit: 80 }});
            const unsupportedPlan = tools.buildReadableBlockSplitPlan(
              {{ id: "choice_1", type: "choice", text: splitCandidate }},
              {{ limit: 80 }}
            );
            const longText = "很".repeat(261);
            const lineHeavyText = "一\\n二\\n三\\n四\\n五\\n六";
            const result = {{
              constants: [
                tools.VN_TEXT_LONG_WARNING_LENGTH,
                tools.VN_TEXT_LONG_WARNING_LINES,
                tools.VN_TEXT_SPLIT_TARGET_LENGTH,
                tools.VN_CHOICE_LONG_WARNING_LENGTH,
                tools.VN_CHOICE_MANY_OPTIONS,
              ],
              metrics: tools.getReadableTextMetrics("  第一行\\n第二行  "),
              emptyMetrics: tools.getReadableTextMetrics("   "),
              readableSummary: tools.buildReadableTextSummary({{ length: 181, lineCount: 2 }}),
              shortChoice: tools.getChoiceTextQualityState("短选项"),
              longChoice: tools.getChoiceTextQualityState("长".repeat(43)),
              choiceSummary: tools.buildChoiceTextSummary(43),
              choiceToolsMarkup: tools.renderChoiceTextQualityTools("长".repeat(43)),
              countSummary: tools.buildChoiceCountSummary(7),
              longChecks: [
                tools.isReadableTextLong(longText),
                tools.isReadableTextLong(lineHeavyText),
                tools.isReadableTextLong("短文本"),
              ],
              toolStates: [
                tools.getReadableTextToolState(longText),
                tools.getReadableTextToolState(splitCandidate),
              ],
              splitIndex: tools.findReadableSplitIndex("前半句，后半句继续", 8),
              splitLong: tools.splitLongReadableSegment("abcdefghij klmnopqrst uvwxyz", 10),
              joinChecks: [
                tools.shouldJoinReadableSegmentsWithSpace("abc", "def"),
                tools.shouldJoinReadableSegmentsWithSpace("中文。", "下一句"),
              ],
              chineseChunks: tools.splitReadableTextIntoChunks(chineseText, 20),
              englishChunks: tools.splitReadableTextIntoChunks(englishText, 26),
              zeroLimitChunks: tools.splitReadableTextIntoChunks("短句。", 0),
              invalidLimitChunks: tools.splitReadableTextIntoChunks("短句。", "bad"),
              emptyChunks: tools.splitReadableTextIntoChunks("   "),
              readableBlockChecks: [
                tools.isReadableTextBlock(splitScene.blocks[0]),
                tools.isReadableTextBlock(splitScene.blocks[2]),
              ],
              blockSplitPlan: {{
                canSplit: blockSplitPlan.canSplit,
                reason: blockSplitPlan.reason,
                firstBlockId: blockSplitPlan.firstBlockId,
                chunkCount: blockSplitPlan.chunkCount,
                ids: blockSplitPlan.blocks.map((block) => block.id),
                duplicateVoiceAssetId: blockSplitPlan.blocks[1]?.voiceAssetId ?? null,
                duplicateVoiceVolume: blockSplitPlan.blocks[1]?.voiceVolume ?? null,
                duplicateVoice: blockSplitPlan.blocks[1]?.voice ?? null,
              }},
              sceneSplitPlan: {{
                changed: sceneSplitPlan.changed,
                splitCount: sceneSplitPlan.splitCount,
                addedBlockCount: sceneSplitPlan.addedBlockCount,
                firstSplitBlockId: sceneSplitPlan.firstSplitBlockId,
                firstSplitIndex: sceneSplitPlan.firstSplitIndex,
                blockCount: sceneSplitPlan.scene.blocks.length,
                ids: sceneSplitPlan.scene.blocks.map((block) => block.id),
                secondVoiceAssetId: sceneSplitPlan.scene.blocks[1]?.voiceAssetId ?? null,
              }},
              unsupportedReason: unsupportedPlan.reason,
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
        self.assertEqual(payload["constants"], [260, 5, 180, 42, 6])
        self.assertEqual(payload["metrics"], {"length": 7, "lineCount": 2})
        self.assertEqual(payload["emptyMetrics"], {"length": 0, "lineCount": 0})
        self.assertIn("超过 180 字会启用拆分", payload["readableSummary"])
        self.assertEqual(payload["shortChoice"]["statusText"], "按钮舒适")
        self.assertFalse(payload["shortChoice"]["isLong"])
        self.assertEqual(payload["longChoice"]["length"], 43)
        self.assertEqual(payload["longChoice"]["toneClass"], "warn-text")
        self.assertIn("建议不超过 42 字", payload["choiceSummary"])
        self.assertIn("is-warning", payload["choiceToolsMarkup"])
        self.assertIn("文案偏长", payload["choiceToolsMarkup"])
        self.assertIn("超过 6 个", payload["countSummary"])
        self.assertEqual(payload["longChecks"], [True, True, False])
        self.assertEqual(payload["toolStates"][0]["statusText"], "建议拆卡")
        self.assertTrue(payload["toolStates"][1]["canSplit"])
        self.assertGreaterEqual(payload["splitIndex"], 4)
        self.assertGreaterEqual(len(payload["splitLong"]), 2)
        self.assertEqual(payload["joinChecks"], [True, False])
        self.assertGreaterEqual(len(payload["chineseChunks"]), 2)
        self.assertGreaterEqual(len(payload["englishChunks"]), 2)
        self.assertEqual(payload["zeroLimitChunks"], ["短句。"])
        self.assertEqual(payload["invalidLimitChunks"], ["短句。"])
        self.assertEqual(payload["emptyChunks"], [])
        self.assertEqual(payload["readableBlockChecks"], [True, False])
        self.assertTrue(payload["blockSplitPlan"]["canSplit"])
        self.assertEqual(payload["blockSplitPlan"]["reason"], "split")
        self.assertEqual(payload["blockSplitPlan"]["firstBlockId"], "block_001")
        self.assertGreaterEqual(payload["blockSplitPlan"]["chunkCount"], 2)
        self.assertEqual(payload["blockSplitPlan"]["ids"][0], "block_001")
        self.assertNotIn("block_002", payload["blockSplitPlan"]["ids"][1:])
        self.assertIsNone(payload["blockSplitPlan"]["duplicateVoiceAssetId"])
        self.assertIsNone(payload["blockSplitPlan"]["duplicateVoiceVolume"])
        self.assertIsNone(payload["blockSplitPlan"]["duplicateVoice"])
        self.assertTrue(payload["sceneSplitPlan"]["changed"])
        self.assertEqual(payload["sceneSplitPlan"]["splitCount"], 1)
        self.assertGreaterEqual(payload["sceneSplitPlan"]["addedBlockCount"], 1)
        self.assertEqual(payload["sceneSplitPlan"]["firstSplitBlockId"], "block_001")
        self.assertEqual(payload["sceneSplitPlan"]["firstSplitIndex"], 0)
        self.assertGreater(payload["sceneSplitPlan"]["blockCount"], 3)
        self.assertEqual(len(payload["sceneSplitPlan"]["ids"]), len(set(payload["sceneSplitPlan"]["ids"])))
        self.assertIsNone(payload["sceneSplitPlan"]["secondVoiceAssetId"])
        self.assertEqual(payload["unsupportedReason"], "unsupported_block")


if __name__ == "__main__":
    unittest.main()
