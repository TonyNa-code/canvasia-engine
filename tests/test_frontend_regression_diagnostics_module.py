from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "regression_diagnostics.js"


class FrontendRegressionDiagnosticsModuleTests(unittest.TestCase):
    def run_regression_diagnostics_script(self, body: str) -> dict:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorRegressionDiagnostics;
            {body}
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
        return json.loads(completed.stdout)

    def test_regression_diagnostics_compacts_variable_and_condition_traces(self) -> None:
        payload = self.run_regression_diagnostics_script(
            """
            const caseResult = {
              variableOverrideSummary: "好感度=3 / route=common",
              conditionTraceSummaries: [
                "条件判断：命中分支 1 -> 教室；好感度 当前 3 >= 2：通过",
                "条件判断：命中否则 -> Missing；路线 当前 common contains good：失败",
                "额外条件：这个应该被 maxItems 截断",
              ],
            };
            process.stdout.write(JSON.stringify({
              keys: Object.keys(tools).sort(),
              line: tools.formatRegressionDiagnosticLine(caseResult, { maxItems: 2 }),
              conditionOnly: tools.formatRegressionDiagnosticLine(caseResult, { includeVariable: false, maxItems: 1 }),
              compact: tools.formatRegressionDiagnosticLine(caseResult, { maxItems: 2, maxLength: 28 }),
              serialized: tools.serializeRegressionDiagnostics(caseResult, { maxItems: 2 }),
              empty: tools.serializeRegressionDiagnostics({}),
            }));
            """
        )

        self.assertIn("formatRegressionDiagnosticLine", payload["keys"])
        self.assertIn("测试预设：好感度=3", payload["line"])
        self.assertIn("命中分支 1", payload["line"])
        self.assertNotIn("额外条件", payload["line"])
        self.assertNotIn("测试预设", payload["conditionOnly"])
        self.assertTrue(payload["compact"].endswith("…"))
        self.assertTrue(payload["serialized"]["hasDiagnostics"])
        self.assertEqual(len(payload["serialized"]["conditionTraceSummaries"]), 2)
        self.assertFalse(payload["empty"]["hasDiagnostics"])

    def test_regression_diagnostics_builds_copyable_bug_note(self) -> None:
        payload = self.run_regression_diagnostics_script(
            """
            const note = tools.buildRegressionDiagnosticClipboardSummary({
              seedSceneId: "scene_01",
              anchorSceneId: "scene_loop",
              anchorBlockId: "block_condition",
              sceneName: "循环测试",
              chapterName: "第一章",
              sourceLabel: "章节起点",
              status: "fail",
              statusLabel: "疑似死循环",
              reason: "这条路线反复回到同一个步骤。",
              detail: "重复命中条件分支。",
              steps: 20,
              visitedSceneCount: 3,
              choiceCount: 1,
              selectedOptionTexts: ["留下"],
              variableOverrideSummary: "好感度=3",
              conditionTraceSummaries: ["条件判断：命中分支 1 -> 循环测试；好感度 当前 3 >= 2：通过"],
            }, {
              recommendation: "先检查这里前后的 jump / condition / choice 去向。",
            });
            process.stdout.write(JSON.stringify({
              note,
              location: tools.formatRegressionCaseLocation({
                seedSceneId: "scene_01",
                anchorSceneId: "scene_loop",
                anchorBlockId: "block_condition",
              }),
              seedOnlyLocation: tools.formatRegressionCaseLocation({ seedSceneId: "scene_01" }),
            }));
            """
        )

        self.assertIn("# 自动回归诊断：循环测试", payload["note"])
        self.assertIn("状态：疑似死循环", payload["note"])
        self.assertIn("来源：第一章 · 章节起点", payload["note"])
        self.assertIn("测试预设：好感度=3", payload["note"])
        self.assertIn("条件判断：\n1. 条件判断：命中分支 1", payload["note"])
        self.assertIn("建议动作：先检查这里前后的 jump / condition / choice 去向。", payload["note"])
        self.assertIn("定位：scene_loop / block_condition", payload["note"])
        self.assertEqual(payload["location"], "scene_loop / block_condition")
        self.assertEqual(payload["seedOnlyLocation"], "scene_01")

    def test_regression_diagnostics_builds_bundle_markdown_for_fix_queue(self) -> None:
        payload = self.run_regression_diagnostics_script(
            """
            const regressionResult = {
              summary: { total: 3, passCount: 1, warnCount: 1, failCount: 1 },
              cases: [
                { id: "pass", sceneName: "开场", status: "pass", statusLabel: "已走通" },
                {
                  id: "fail",
                  sceneName: "循环测试",
                  chapterName: "第一章",
                  sourceLabel: "章节起点",
                  status: "fail",
                  statusLabel: "疑似死循环",
                  reason: "这条路线反复回到同一个步骤。",
                  detail: "重复命中条件分支。",
                  steps: 20,
                  visitedSceneCount: 3,
                  choiceCount: 1,
                  variableOverrideSummary: "好感度=3",
                  conditionTraceSummaries: ["条件判断：命中分支 1 -> 循环测试；好感度 当前 3 >= 2：通过"],
                  recommendation: "先修循环条件。",
                },
                {
                  id: "warn",
                  sceneName: "过短结尾",
                  chapterName: "第一章",
                  sourceLabel: "章节起点",
                  status: "warn",
                  statusLabel: "需要复看",
                  reason: "结束得太快。",
                  steps: 1,
                  visitedSceneCount: 1,
                  choiceCount: 0,
                },
              ],
            };
            const markdown = tools.buildRegressionDiagnosticBundleMarkdown({
              projectTitle: "Demo",
              generatedAt: "2026-07-06T10:00:00+08:00",
              regressionResult,
              fixQueue: regressionResult.cases.filter((item) => item.status !== "pass"),
            });
            process.stdout.write(JSON.stringify({ markdown }));
            """
        )

        self.assertIn("# Demo 自动回归诊断包", payload["markdown"])
        self.assertIn("- 已测试：3 条", payload["markdown"])
        self.assertIn("- 通过：1 条", payload["markdown"])
        self.assertIn("- 需要复看：1 条", payload["markdown"])
        self.assertIn("- 失败：1 条", payload["markdown"])
        self.assertIn("## 1. 优先修复：循环测试", payload["markdown"])
        self.assertIn("建议动作：先修循环条件。", payload["markdown"])
        self.assertIn("## 2. 发布前复看：过短结尾", payload["markdown"])
        self.assertNotIn("## 3.", payload["markdown"])


if __name__ == "__main__":
    unittest.main()
