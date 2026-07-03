from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "playtest_handoff_report.js"


class FrontendPlaytestHandoffReportModuleTests(unittest.TestCase):
    def test_playtest_handoff_exports_route_and_regression_work_orders(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorPlaytestHandoffReport;
            const routeTestingPlan = {{
              summary: {{
                decisionPointCount: 1,
                routeCaseCount: 2,
                endingTestCaseCount: 1,
                brokenRouteCaseCount: 1,
                unreachableRouteCaseCount: 0,
                reachableEndingTestCaseCount: 1,
              }},
              decisionPoints: [
                {{
                  chapterName: "第1章",
                  sceneName: "开场分歧",
                  entryPathLabel: "Start",
                  routeCases: [
                    {{
                      label: "选项：留下",
                      targetSceneName: "教室",
                      targetExists: true,
                      statusLabel: "可试玩",
                    }},
                    {{
                      label: "选项：离开",
                      targetSceneName: "Missing",
                      targetExists: false,
                      statusLabel: "坏链",
                    }},
                  ],
                }},
              ],
              endingTestCases: [
                {{
                  chapterName: "第1章",
                  sceneName: "普通结局",
                  pathLabel: "Start -> 普通结局",
                  status: "ready",
                  statusLabel: "可打到",
                  testingHint: "完整跑到结尾。",
                }},
              ],
            }};
            const regressionResult = {{
              ranAt: "2026-05-10T12:00:00Z",
              summary: {{ total: 2, passCount: 1, warnCount: 0, failCount: 1 }},
              cases: [
                {{
                  sceneId: "scene_start",
                  sceneName: "开场",
                  chapterName: "第1章",
                  sourceLabel: "项目入口",
                  status: "pass",
                  statusLabel: "通过",
                  reason: "正常结束",
                  detail: "可以顺利推进。",
                  steps: 6,
                  visitedSceneCount: 2,
                  choiceCount: 1,
                  selectedOptionTexts: ["留下"],
                }},
                {{
                  sceneId: "scene_missing",
                  sceneName: "坏链落点",
                  chapterName: "第1章",
                  sourceLabel: "高分支场景",
                  status: "fail",
                  statusLabel: "失败",
                  reason: "跳到了不存在的场景",
                  detail: "目标场景缺失。",
                  steps: 3,
                  visitedSceneCount: 1,
                  choiceCount: 1,
                  selectedOptionTexts: ["离开"],
                }},
              ],
            }};
            const regressionFixQueue = [
              {{
                ...regressionResult.cases[1],
                priorityScore: 130,
                recommendation: "先修复目标场景缺失。",
              }},
            ];
            const contextData = {{
              projectTitle: "Demo",
              generatedAt: "2026-05-10 20:00:00",
              routeTestingPlan,
              regressionResult,
              regressionFixQueue,
            }};
            const markdown = tools.buildPlaytestHandoffMarkdown(contextData);
            const csv = tools.buildPlaytestHandoffCsv(contextData);
            const feedbackRows = tools.buildPlaytestFeedbackRows(contextData);
            const feedbackMarkdown = tools.buildPlaytestFeedbackTemplateMarkdown(contextData);
            const feedbackCsv = tools.buildPlaytestFeedbackTemplateCsv(contextData);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              flattened: tools.flattenRouteTestingCases(routeTestingPlan),
              summary: tools.getRouteTestingSummary(routeTestingPlan),
              digest: tools.buildPlaytestHandoffDigest(contextData),
              regression: tools.serializeRegressionResult(regressionResult, regressionFixQueue),
              markdown,
              csv,
              feedbackRows,
              feedbackMarkdown,
              feedbackCsv,
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
        self.assertIn("buildPlaytestHandoffMarkdown", payload["keys"])
        self.assertIn("buildPlaytestHandoffCsv", payload["keys"])
        self.assertIn("buildPlaytestFeedbackTemplateMarkdown", payload["keys"])
        self.assertIn("buildPlaytestFeedbackTemplateCsv", payload["keys"])
        self.assertEqual(len(payload["flattened"]), 3)
        self.assertEqual(len(payload["feedbackRows"]), 5)
        self.assertEqual(payload["summary"]["blockedRouteCaseCount"], 1)
        self.assertEqual(payload["digest"]["status"], "blocked")
        self.assertEqual(payload["regression"]["summary"]["failCount"], 1)
        self.assertIn("# Demo 测试员试玩工单", payload["markdown"])
        self.assertIn("## 重点修复 / 复看路线", payload["markdown"])
        self.assertIn("先修复目标场景缺失", payload["markdown"])
        self.assertIn('"优先复看"', payload["csv"])
        self.assertIn('"分支路线"', payload["csv"])
        self.assertIn('"结局路径"', payload["csv"])
        self.assertIn("# Demo 测试反馈模板", payload["feedbackMarkdown"])
        self.assertIn("复现步骤", payload["feedbackMarkdown"])
        self.assertIn("截图/录屏", payload["feedbackCsv"])
        self.assertIn('"自由反馈"', payload["feedbackCsv"])


if __name__ == "__main__":
    unittest.main()
