from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "route_testing_report.js"


class FrontendRouteTestingReportModuleTests(unittest.TestCase):
    def test_route_testing_report_helpers_export_markdown_and_csv(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorRouteTestingReport;
            const plan = {{
              summary: {{
                decisionPointCount: 1,
                reachableDecisionPointCount: 1,
                routeCaseCount: 3,
                brokenRouteCaseCount: 1,
                unreachableRouteCaseCount: 1,
                endingTestCaseCount: 2,
                reachableEndingTestCaseCount: 1,
              }},
              decisionPoints: [
                {{
                  sceneId: "scene_start",
                  sceneName: "Start | Branch",
                  chapterName: "Chapter 1",
                  routeDepth: 0,
                  entryPathLabel: "Start",
                  isReachable: true,
                  routeCount: 3,
                  brokenRouteCount: 1,
                  unreachableTargetCount: 1,
                  routeCases: [
                    {{
                      order: 1,
                      routeId: "route_good",
                      routeKind: "choice",
                      label: "选项：Go End",
                      sourceSceneId: "scene_start",
                      targetSceneId: "scene_good",
                      targetSceneName: "Good End",
                      targetExists: true,
                      status: "ready",
                      statusLabel: "可试玩",
                      blockIndex: 3,
                      optionIndex: 0,
                    }},
                    {{
                      order: 2,
                      routeId: "route_lost",
                      routeKind: "condition",
                      label: "选项：Lost",
                      sourceSceneId: "scene_start",
                      targetSceneId: "scene_missing",
                      targetSceneName: "Missing",
                      targetExists: false,
                      status: "broken",
                      statusLabel: "坏链",
                      blockIndex: 4,
                      branchIndex: 0,
                    }},
                  ],
                }},
              ],
              endingTestCases: [
                {{
                  sceneId: "scene_good",
                  sceneName: "Good End",
                  chapterName: "Chapter 1",
                  routeDepth: 1,
                  pathLabel: "Start -> Good End",
                  status: "ready",
                  statusLabel: "可打到",
                  testingHint: "完整试玩。",
                }},
                {{
                  sceneId: "scene_hidden",
                  sceneName: "Hidden End",
                  chapterName: "Chapter 1",
                  routeDepth: null,
                  pathLabel: "",
                  status: "unreachable",
                  statusLabel: "未接通",
                  testingHint: "先接回入口。",
                }},
              ],
            }};
            const tables = tools.buildRouteTestingReportTables(plan);
            const markdown = tools.buildRouteTestingPlanMarkdown(plan, {{
              projectTitle: "Demo Project",
              generatedAt: "2026-05-10 19:00:00",
            }});
            const csv = tools.buildRouteTestingPlanCsv(plan, {{ projectTitle: "Demo Project" }});
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              serialized: tools.serializeRouteTestingPlan(plan),
              summary: tools.getRouteTestingSummary(plan),
              digest: tools.getRouteTestingStatusDigest(plan),
              executionQueue: tools.buildRouteTestingExecutionQueue(plan),
              acceptanceChecklist: tools.buildRouteTestingAcceptanceChecklist(plan),
              readiness: tools.getRouteTestingReadinessPercent(plan),
              tables,
              workbook: tools.buildRouteTestingWorkbook(plan),
              workbookTable: tools.buildRouteTestingWorkbookTable(plan),
              markdown,
              csv,
              escaped: tools.escapeMarkdownTableCell("a|b\\nc"),
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
        self.assertIn("buildRouteTestingPlanMarkdown", payload["keys"])
        self.assertIn("buildRouteTestingPlanCsv", payload["keys"])
        self.assertIn("buildRouteTestingExecutionQueue", payload["keys"])
        self.assertIn("buildRouteTestingAcceptanceChecklist", payload["keys"])
        self.assertIn("buildRouteTestingWorkbook", payload["keys"])
        self.assertIn("buildRouteTestingWorkbookTable", payload["keys"])
        self.assertIn("getRouteKindLabel", payload["keys"])
        self.assertIn("getRouteTestingReadinessPercent", payload["keys"])
        self.assertEqual(payload["serialized"]["decisionPoints"][0]["routeCases"][0]["routeKind"], "choice")
        self.assertEqual(payload["summary"]["routeCaseCount"], 3)
        self.assertEqual(payload["summary"]["brokenRouteCaseCount"], 1)
        self.assertEqual(payload["summary"]["unreachableRouteCaseCount"], 1)
        self.assertEqual(payload["digest"]["status"], "blocked")
        self.assertEqual(payload["executionQueue"][0]["severity"], "blocker")
        self.assertEqual(payload["executionQueue"][0]["title"], "修复分支坏链")
        self.assertEqual(payload["executionQueue"][0]["routeKind"], "condition")
        self.assertTrue(any(item["id"] == "route_blockers_clear" for item in payload["acceptanceChecklist"]))
        self.assertEqual(payload["workbook"]["lanes"][0]["id"], "repair")
        self.assertEqual(payload["workbook"]["nextBestAction"]["routeKindLabel"], "条件分支")
        self.assertIn("自动回归会尝试把条件变量", payload["workbook"]["nextBestAction"]["variablePresetHint"])
        self.assertIn("变量 / 状态提示", payload["workbookTable"])
        self.assertLess(payload["readiness"], 100)
        self.assertIn("执行队列", payload["tables"]["summaryTable"])
        self.assertIn("修复分支坏链", payload["tables"]["executionTable"])
        self.assertIn("发布前路线工作簿", payload["markdown"])
        self.assertIn("路线工作簿", payload["csv"])
        self.assertIn("Start \\| Branch", payload["tables"]["decisionTable"])
        self.assertIn("# Demo Project 路线试玩手册", payload["markdown"])
        self.assertIn("## 执行优先队列", payload["markdown"])
        self.assertIn("## 验收标准", payload["markdown"])
        self.assertIn("## 分支检查点", payload["markdown"])
        self.assertIn('"执行队列"', payload["csv"])
        self.assertIn('"分支路线"', payload["csv"])
        self.assertIn('"结局路径"', payload["csv"])
        self.assertEqual(payload["escaped"], "a\\|b<br />c")


if __name__ == "__main__":
    unittest.main()
