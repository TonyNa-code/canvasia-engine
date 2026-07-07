from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "project_polish_receipt_panel.js"


class FrontendProjectPolishReceiptPanelModuleTests(unittest.TestCase):
    def test_project_polish_receipt_panel_renders_metrics_actions_and_overflow_without_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorProjectPolishReceiptPanel;
            const receipt = {{
              receiptId: "receipt_<safe>",
              summary: "整理完成 & 可试玩",
              safetySnapshotLabel: "自动检查点 <1>",
              changedSceneCount: 5,
              totalOperationCount: 12,
              readableSplitCount: 2,
              readableAddedBlockCount: 4,
              presentationChangedFieldCount: 3,
              audioOperationCount: 2,
              projectOperationCount: 1,
              pacingAverageScore: 63,
              pacingRoughSceneCount: 2,
              pacingReadySceneCount: 3,
              pacingSnapshot: {{
                sceneHighlights: [
                  {{ sceneName: "走廊", gradeLabel: "需要打磨", issueSummary: "缺少视觉锚点 / 连续文本过长" }},
                  {{ sceneName: "屋顶", gradeLabel: "还像草稿", issueSummary: "缺少 BGM" }},
                ],
              }},
              scenePlans: [
                {{ sceneName: "开场 <A>", readableSplitCount: 1, readableAddedBlockCount: 2, presentationChangedFieldCount: 1, audioOperationCount: 1 }},
                {{ sceneName: "走廊", readableSplitCount: 0, readableAddedBlockCount: 0, presentationChangedFieldCount: 1, audioOperationCount: 0 }},
                {{ sceneName: "屋顶", readableSplitCount: 1, readableAddedBlockCount: 2, presentationChangedFieldCount: 1, audioOperationCount: 1 }},
                {{ sceneName: "尾声", readableSplitCount: 0, readableAddedBlockCount: 0, presentationChangedFieldCount: 0, audioOperationCount: 0 }},
                {{ sceneName: "隐藏场景", readableSplitCount: 0, readableAddedBlockCount: 0, presentationChangedFieldCount: 0, audioOperationCount: 0 }},
              ],
              projectOperations: [
                {{ label: "存档位", detail: "补到 50 个" }},
              ],
              nextActions: [
                "打开项目巡检",
                {{ label: "去试玩确认", action: "switch-screen", screen: "preview", detail: "跑一遍 Demo" }},
              ],
            }};
            const html = tools.renderProjectOneClickPolishReceiptPanel(receipt);
            const emptyHtml = tools.renderProjectOneClickPolishReceiptPanel(null);
            const normalizedStringAction = tools.normalizeProjectOneClickPolishNextAction("先巡检", 0);
            const normalizedSecondStringAction = tools.normalizeProjectOneClickPolishNextAction("再试玩", 1);
            const normalizedInvalid = tools.normalizeProjectOneClickPolishNextAction(null);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              html,
              emptyHtml,
              normalizedStringAction,
              normalizedSecondStringAction,
              normalizedInvalid,
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
        html = payload["html"]

        self.assertIn("renderProjectOneClickPolishReceiptPanel", payload["keys"])
        self.assertEqual(payload["emptyHtml"], "")
        self.assertEqual(payload["normalizedStringAction"]["action"], "run-project-inspection")
        self.assertEqual(payload["normalizedSecondStringAction"]["screen"], "preview")
        self.assertIsNone(payload["normalizedInvalid"])
        self.assertIn("整理完成 &amp; 可试玩", html)
        self.assertIn("receipt_&lt;safe&gt;", html)
        self.assertIn("已先创建安全检查点「自动检查点 &lt;1&gt;」", html)
        self.assertIn("涉及场景", html)
        self.assertIn("总处理项", html)
        self.assertIn("节奏体检", html)
        self.assertIn("63 分", html)
        self.assertIn("待打磨 2 / 可试玩 3", html)
        self.assertIn("开场 &lt;A&gt;", html)
        self.assertIn("缺少视觉锚点 / 连续文本过长", html)
        self.assertIn("还有 1 个场景", html)
        self.assertIn("补到 50 个", html)
        self.assertIn('data-action="copy-project-one-click-polish-receipt-summary"', html)
        self.assertIn('data-action="switch-screen" data-screen="preview"', html)


if __name__ == "__main__":
    unittest.main()
