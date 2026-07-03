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
                      label: "选项：Go End",
                      targetSceneName: "Good End",
                      targetExists: true,
                      status: "ready",
                      statusLabel: "可试玩",
                    }},
                    {{
                      label: "选项：Lost",
                      targetSceneName: "Missing",
                      targetExists: false,
                      status: "broken",
                      statusLabel: "坏链",
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
              tables,
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
        self.assertEqual(payload["summary"]["routeCaseCount"], 3)
        self.assertEqual(payload["summary"]["brokenRouteCaseCount"], 1)
        self.assertEqual(payload["summary"]["unreachableRouteCaseCount"], 1)
        self.assertEqual(payload["digest"]["status"], "blocked")
        self.assertIn("Start \\| Branch", payload["tables"]["decisionTable"])
        self.assertIn("# Demo Project 路线试玩手册", payload["markdown"])
        self.assertIn("## 分支检查点", payload["markdown"])
        self.assertIn('"分支路线"', payload["csv"])
        self.assertIn('"结局路径"', payload["csv"])
        self.assertEqual(payload["escaped"], "a\\|b<br />c")


if __name__ == "__main__":
    unittest.main()
