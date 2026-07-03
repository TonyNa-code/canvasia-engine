from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "route_analyzer.js"


class FrontendRouteAnalyzerModuleTests(unittest.TestCase):
    def test_route_analyzer_builds_branch_metrics_and_alerts(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorRouteAnalyzer;
            const start = {{
              id: "scene_start",
              name: "Start",
              status: "ready",
              priority: "focus",
              blocks: [
                {{ id: "bg", type: "background", assetId: "bg_school" }},
                {{ id: "music", type: "music_play", assetId: "bgm_daily" }},
                {{ id: "line", type: "dialogue", text: "Hello", voiceAssetId: "" }},
                {{
                  id: "choice",
                  type: "choice",
                  options: [
                    {{ text: "Go end", gotoSceneId: "scene_end" }},
                    {{ text: "Missing", gotoSceneId: "scene_missing" }}
                  ]
                }},
                {{
                  id: "condition",
                  type: "condition",
                  branches: [{{ gotoSceneId: "scene_secret", when: [{{ variableId: "flag" }}] }}],
                  elseGotoSceneId: ""
                }}
              ]
            }};
            const end = {{
              id: "scene_end",
              name: "End",
              blocks: [{{ id: "n", type: "narration", text: "Done." }}]
            }};
            const secret = {{
              id: "scene_secret",
              name: "Secret",
              blocks: [{{ id: "fx", type: "screen_flash" }}, {{ id: "n", type: "narration", text: "Secret." }}]
            }};
            const orphan = {{
              id: "scene_orphan",
              name: "Orphan",
              blocks: [
                {{ id: "n", type: "narration", text: "Nobody reaches this." }},
                {{ id: "jump", type: "jump", targetSceneId: "scene_hidden_chain" }}
              ]
            }};
            const hiddenChain = {{
              id: "scene_hidden_chain",
              name: "Hidden Chain",
              blocks: [{{ id: "n", type: "narration", text: "Has an incoming line, but the chain is unreachable." }}]
            }};
            const data = {{
              project: {{ entrySceneId: "scene_start" }},
              chapters: [
                {{ chapterId: "ch1", name: "Chapter", sceneOrder: ["scene_start", "scene_end", "scene_secret", "scene_orphan", "scene_hidden_chain"] }}
              ],
              scenesById: new Map([
                ["scene_start", start],
                ["scene_end", end],
                ["scene_secret", secret],
                ["scene_orphan", orphan],
                ["scene_hidden_chain", hiddenChain]
              ])
            }};
            const validation = {{
              errors: [{{ context: {{ type: "scene", sceneId: "scene_start" }} }}],
              warnings: [{{ context: {{ type: "story", sceneId: "scene_end" }} }}]
            }};
            const overview = tools.buildSceneRouteOverview(data, validation, {{
              summarizeConditionBranch: () => "Flag route",
            }});
            const routeKinds = overview.nodes.find((node) => node.id === "scene_start").routes.map((route) => route.routeKind);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              metrics: overview.metrics,
              alertLabels: overview.alerts.map((alert) => alert.label),
              startNode: overview.nodes.find((node) => node.id === "scene_start"),
              endNode: overview.nodes.find((node) => node.id === "scene_end"),
              orphanNode: overview.nodes.find((node) => node.id === "scene_orphan"),
              hiddenChainNode: overview.nodes.find((node) => node.id === "scene_hidden_chain"),
              endingPaths: overview.endingPaths,
              routeTestingPlan: overview.routeTestingPlan,
              chapterProduction: overview.chapters[0].production,
              routeKinds,
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
        self.assertIn("buildSceneRouteOverview", payload["keys"])
        self.assertEqual(payload["metrics"]["entrySceneName"], "Start")
        self.assertEqual(payload["metrics"]["brokenRoutes"], 2)
        self.assertEqual(payload["metrics"]["branchingScenes"], 1)
        self.assertEqual(payload["metrics"]["endingScenes"], 3)
        self.assertEqual(payload["metrics"]["orphanScenes"], 1)
        self.assertEqual(payload["metrics"]["reachableScenes"], 3)
        self.assertEqual(payload["metrics"]["unreachableScenes"], 2)
        self.assertEqual(payload["metrics"]["maxRouteDepth"], 1)
        self.assertEqual(payload["metrics"]["reachableEndingScenes"], 2)
        self.assertEqual(payload["metrics"]["unreachableEndingScenes"], 1)
        self.assertEqual(payload["metrics"]["decisionPointScenes"], 1)
        self.assertEqual(payload["metrics"]["routeTestCases"], 4)
        self.assertEqual(payload["metrics"]["blockedRouteTestCases"], 2)
        self.assertEqual(payload["routeKinds"], ["choice", "choice", "condition", "fallback"])
        self.assertEqual(payload["alertLabels"][:2], ["坏链", "坏链"])
        self.assertIn("不可达", payload["alertLabels"])
        self.assertIn("buildRoutePathFromPredecessors", payload["keys"])
        self.assertIn("buildRouteTestingPlan", payload["keys"])
        self.assertTrue(payload["startNode"]["isReachableFromEntry"])
        self.assertEqual(payload["startNode"]["entryPathLabel"], "Start")
        self.assertTrue(payload["orphanNode"]["isOrphan"])
        self.assertTrue(payload["orphanNode"]["isUnreachable"])
        self.assertFalse(payload["hiddenChainNode"]["isOrphan"])
        self.assertTrue(payload["hiddenChainNode"]["isUnreachable"])
        self.assertIsNone(payload["hiddenChainNode"]["routeDepth"])
        self.assertEqual(payload["hiddenChainNode"]["entryPathLabel"], "")
        self.assertTrue(payload["endNode"]["isEnding"])
        self.assertEqual(payload["endNode"]["routeDepth"], 1)
        self.assertEqual(payload["endNode"]["entryPathLabel"], "Start -> End")
        self.assertEqual(payload["endNode"]["entryPathRouteLabels"], ["选项：Go end"])
        self.assertEqual(payload["endingPaths"][0]["pathLabel"], "Start -> End")
        self.assertEqual(payload["endingPaths"][0]["pathRouteLabels"], ["选项：Go end"])
        self.assertEqual(payload["endingPaths"][-1]["sceneName"], "Hidden Chain")
        self.assertFalse(payload["endingPaths"][-1]["isReachable"])
        self.assertEqual(payload["routeTestingPlan"]["summary"]["decisionPointCount"], 1)
        self.assertEqual(payload["routeTestingPlan"]["summary"]["brokenRouteCaseCount"], 2)
        self.assertEqual(payload["routeTestingPlan"]["summary"]["endingTestCaseCount"], 3)
        self.assertEqual(payload["routeTestingPlan"]["decisionPoints"][0]["routeCases"][1]["status"], "broken")
        self.assertEqual(payload["routeTestingPlan"]["decisionPoints"][0]["routeCases"][0]["blockIndex"], 3)
        self.assertEqual(payload["routeTestingPlan"]["decisionPoints"][0]["routeCases"][0]["optionIndex"], 0)
        self.assertEqual(payload["routeTestingPlan"]["decisionPoints"][0]["routeCases"][2]["branchIndex"], 0)
        self.assertEqual(payload["routeTestingPlan"]["endingTestCases"][0]["statusLabel"], "可打到")
        self.assertEqual(payload["startNode"]["missingVoiceCount"], 1)
        self.assertEqual(payload["startNode"]["errorCount"], 1)
        self.assertEqual(payload["endNode"]["warningCount"], 1)
        self.assertGreater(payload["chapterProduction"]["averageCompletion"], 0)

    def test_route_testing_plan_export_actions_are_wired_in_app(self) -> None:
        source = (ROOT_DIR / "prototype_editor" / "app.js").read_text(encoding="utf-8")

        self.assertIn("const routeTestingReportTools = window.CanvasiaEditorRouteTestingReport", source)
        self.assertIn('data-action="export-route-testing-plan-markdown"', source)
        self.assertIn('data-action="export-route-testing-plan-csv"', source)
        self.assertIn('if (action === "export-route-testing-plan-markdown")', source)
        self.assertIn('if (action === "export-route-testing-plan-csv")', source)
        self.assertIn("function exportRouteTestingPlanMarkdown()", source)
        self.assertIn("function exportRouteTestingPlanCsv()", source)


if __name__ == "__main__":
    unittest.main()
