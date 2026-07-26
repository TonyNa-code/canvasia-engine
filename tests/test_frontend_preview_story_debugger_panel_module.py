from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
COMMON_PATH = ROOT_DIR / "prototype_editor" / "modules" / "editor_common.js"
PANEL_PATH = ROOT_DIR / "prototype_editor" / "modules" / "preview_story_debugger_panel.js"


class FrontendPreviewStoryDebuggerPanelModuleTests(unittest.TestCase):
    def test_panel_renders_record_navigation_exports_and_coverage(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            for (const filePath of [{json.dumps(str(COMMON_PATH))}, {json.dumps(str(PANEL_PATH))}]) {{
              vm.runInContext(fs.readFileSync(filePath, "utf8"), context);
            }}
            const tools = context.window.CanvasiaEditorPreviewStoryDebuggerPanel;
            const report = {{
              summary: {{ stepCount: 3, variableChangeCount: 1, routeDecisionCount: 1, stageCueCount: 2, currentSceneName: "教室", currentBlockLabel: "播放音乐", completed: false }},
              entries: [],
              significantEntries: [{{
                index: 2, isCurrent: true, sceneId: "scene_<start>", sceneName: "教室", blockId: "music_1", blockIndex: 2,
                blockLabel: "播放音乐", title: "开始播放放课后钢琴", variableChanges: [{{ name: "好感度", beforeLabel: "0", afterLabel: "2" }}],
                routeDecision: {{ title: "命中：好感度路线", meta: "去天台", pending: false }},
                stageCues: [{{ kind: "music", label: "BGM 开始", detail: "放课后钢琴 · 72%" }}],
              }}],
            }};
            report.entries = [...report.significantEntries];
            const route = {{ visitedSceneCount: 2, choiceCount: 1, conditionCount: 1, pendingChoiceCount: 0, items: [{{
              index: 1, sceneId: "scene_start", blockId: "choice_1", blockType: "choice", sceneName: "教室", title: "已选：留下", meta: "去走廊", isCurrent: false,
            }}] }};
            const coverage = {{
              totalPoints: 1, visitedPointCount: 1, fullyCoveredPointCount: 0, totalOutcomeCount: 2, coveredOutcomeCount: 1, remainingOutcomeCount: 1,
              currentPendingChoice: null, unvisitedPoints: [], partialPoints: [{{
                sceneId: "scene_start", blockId: "choice_1", blockType: "choice", title: "教室 / 选项分支", meta: "第一章 · 第 1 张卡片", isCurrent: false,
                coveredCount: 1, remainingCount: 1, outcomes: [{{ label: "留下", meta: "走廊", covered: true }}, {{ label: "离开", meta: "天台", covered: false }}],
              }}],
            }};
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              flightHtml: tools.renderPreviewFlightRecorderPanel(report),
              routeHtml: tools.renderPreviewRouteSummaryPanel(route),
              coverageHtml: tools.renderPreviewBranchCoveragePanel(coverage),
              emptyHtml: tools.renderPreviewFlightRecorderPanel(null),
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
        self.assertIn("renderPreviewFlightRecorderPanel", payload["keys"])
        self.assertIn("试玩飞行记录器", payload["flightHtml"])
        self.assertIn("好感度", payload["flightHtml"])
        self.assertIn("BGM 开始", payload["flightHtml"])
        self.assertIn('data-action="jump-preview-history"', payload["flightHtml"])
        self.assertIn('data-action="open-character-line"', payload["flightHtml"])
        self.assertIn('data-action="export-preview-flight-recorder-markdown"', payload["flightHtml"])
        self.assertIn('data-action="export-preview-flight-recorder-json"', payload["flightHtml"])
        self.assertIn("scene_&lt;start&gt;", payload["flightHtml"])
        self.assertIn("当前有效时间线", payload["routeHtml"])
        self.assertIn("覆盖率只按当前有效路线计算", payload["coverageHtml"])
        self.assertIn("离开", payload["coverageHtml"])
        self.assertIn("开始试玩后", payload["emptyHtml"])


if __name__ == "__main__":
    unittest.main()
