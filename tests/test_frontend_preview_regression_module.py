from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "preview_regression.js"


class FrontendPreviewRegressionModuleTests(unittest.TestCase):
    def test_preview_regression_seeds_include_individual_route_cases(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorPreviewRegression;
            const scenesById = new Map([
              ["scene_start", {{
                id: "scene_start",
                name: "Start",
                chapterName: "Chapter",
                blocks: [
                  {{ id: "line", type: "narration", text: "Start" }},
                  {{
                    id: "condition",
                    type: "condition",
                    branches: [
                      {{
                        gotoSceneId: "scene_good",
                        when: [{{ variableId: "score", operator: ">=", value: 5 }}],
                      }},
                      {{
                        gotoSceneId: "scene_bad",
                        when: [{{ variableId: "flag", operator: "==", value: true }}],
                      }},
                      {{
                        gotoSceneId: "scene_good",
                        when: [{{ variableId: "route", operator: "contains", value: "good" }}],
                      }},
                    ],
                    elseGotoSceneId: "scene_bad",
                  }},
                ],
              }}],
              ["scene_good", {{ id: "scene_good", name: "Good", chapterName: "Chapter" }}],
              ["scene_bad", {{ id: "scene_bad", name: "Bad", chapterName: "Chapter" }}],
            ]);
            const variablesById = new Map([
              ["score", {{ id: "score", type: "number", defaultValue: 7 }}],
              ["flag", {{ id: "flag", type: "boolean", defaultValue: true }}],
              ["route", {{ id: "route", type: "string", defaultValue: "common" }}],
            ]);
            const routeOverview = {{
              chapters: [
                {{ chapterId: "ch1", name: "Chapter", scenes: [{{ id: "scene_start", name: "Start" }}] }}
              ],
              nodes: [],
              routeTestingPlan: {{
                decisionPoints: [
                  {{
                    sceneId: "scene_start",
                    sceneName: "Start",
                    chapterName: "Chapter",
                    routeCases: [
                      {{
                        routeId: "route_good",
                        routeKind: "choice",
                        label: "选项：留下",
                        sourceSceneId: "scene_start",
                        sourceSceneName: "Start",
                        targetSceneId: "scene_good",
                        targetSceneName: "Good",
                        targetExists: true,
                        status: "ready",
                        statusLabel: "可试玩",
                        blockIndex: 3,
                        optionIndex: 1,
                      }},
                      {{
                        routeId: "route_missing",
                        routeKind: "choice",
                        label: "选项：消失",
                        sourceSceneId: "scene_start",
                        sourceSceneName: "Start",
                        targetSceneId: "scene_missing",
                        targetSceneName: "Missing",
                        targetExists: false,
                        status: "broken",
                        statusLabel: "坏链",
                        blockIndex: 3,
                        optionIndex: 2,
                      }},
                    ],
                  }},
                ],
              }},
            }};
            const seeds = tools.buildPreviewRegressionSeeds(routeOverview, {{
              entrySceneId: "scene_start",
              scenesById,
              maxCases: 6,
            }});
            const selected = tools.chooseRegressionOption(
              [
                {{ id: "opt_a", text: "离开", gotoSceneId: "scene_bad" }},
                {{ id: "opt_b", text: "留下", gotoSceneId: "scene_good" }},
              ],
              seeds.find((seed) => seed.routeCaseId === "route_good")
            );
            const defaultWhenContextDoesNotMatch = tools.chooseRegressionOption(
              [
                {{ id: "early_a", text: "提前离开", gotoSceneId: "scene_bad" }},
                {{ id: "early_b", text: "提前留下", gotoSceneId: "scene_good" }},
              ],
              seeds.find((seed) => seed.routeCaseId === "route_good"),
              {{ sceneId: "scene_start", blockIndex: 1 }}
            );
            const conditionOverrides = tools.buildConditionVariableOverrides(
              {{
                routeKind: "condition",
                sourceSceneId: "scene_start",
                blockIndex: 1,
                branchIndex: 0,
              }},
              {{
                scenesById,
                variablesById,
                getVariableType: (variableId) => variablesById.get(variableId)?.type ?? "string",
              }}
            );
            const booleanOverrides = tools.buildConditionVariableOverrides(
              {{
                routeKind: "condition",
                sourceSceneId: "scene_start",
                blockIndex: 1,
                branchIndex: 1,
              }},
              {{
                scenesById,
                variablesById,
                getVariableType: (variableId) => variablesById.get(variableId)?.type ?? "string",
              }}
            );
            const fallbackOverrides = tools.buildConditionVariableOverrides(
              {{
                routeKind: "fallback",
                sourceSceneId: "scene_start",
                blockIndex: 1,
                branchIndex: -1,
              }},
              {{
                scenesById,
                variablesById,
                getVariableType: (variableId) => variablesById.get(variableId)?.type ?? "string",
              }}
            );
            const stringOverrides = tools.buildConditionVariableOverrides(
              {{
                routeKind: "condition",
                sourceSceneId: "scene_start",
                blockIndex: 1,
                branchIndex: 2,
              }},
              {{
                scenesById,
                variablesById,
                getVariableType: (variableId) => variablesById.get(variableId)?.type ?? "string",
              }}
            );
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              seedIds: seeds.map((seed) => seed.seedId),
              routeSeeds: seeds.filter((seed) => seed.seedKind === "route_case"),
              selected,
              defaultWhenContextDoesNotMatch,
              conditionOverrides,
              booleanOverrides,
              fallbackOverrides,
              stringOverrides,
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
        self.assertIn("buildPreviewRegressionSeeds", payload["keys"])
        self.assertIn("buildConditionVariableOverrides", payload["keys"])
        self.assertIn("chooseRegressionOption", payload["keys"])
        self.assertEqual(payload["seedIds"][0], "entry")
        self.assertIn("route:route_good", payload["seedIds"])
        self.assertIn("route:route_missing", payload["seedIds"])
        self.assertEqual(len(payload["routeSeeds"]), 2)
        self.assertEqual(payload["routeSeeds"][0]["routeStatus"], "broken")
        self.assertEqual(payload["routeSeeds"][0]["optionIndex"], 2)
        self.assertEqual(payload["selected"]["id"], "opt_b")
        self.assertEqual(payload["defaultWhenContextDoesNotMatch"]["id"], "early_a")
        self.assertEqual(payload["conditionOverrides"], {"score": 5})
        self.assertEqual(payload["booleanOverrides"], {"score": 4, "flag": True})
        self.assertEqual(payload["fallbackOverrides"], {"score": 4, "flag": False})
        self.assertEqual(payload["stringOverrides"], {"route": "good__canvasia_route_test__", "score": 4, "flag": False})


if __name__ == "__main__":
    unittest.main()
