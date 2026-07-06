from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
CONDITION_MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_conditions.js"
EDITOR_INDEX_PATH = ROOT_DIR / "prototype_editor" / "index.html"
APP_PATH = ROOT_DIR / "prototype_editor" / "app.js"
PLAYER_INDEX_PATH = ROOT_DIR / "export_player_template" / "index.html"
PLAYER_PATH = ROOT_DIR / "export_player_template" / "player.js"


class FrontendRuntimeConditionsModuleTests(unittest.TestCase):
    def test_condition_evaluator_runs_without_browser_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(CONDITION_MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaRuntimeConditions;
            const variables = new Map([
              ["score", 7],
              ["route", "good_common_end"],
              ["flag", true],
            ]);
            const result = {{
              keys: Object.keys(tools).sort(),
              operators: {{
                strings: tools.STRING_CONDITION_OPERATORS,
                numbers: tools.NUMERIC_CONDITION_OPERATORS,
                equalities: tools.EQUALITY_CONDITION_OPERATORS,
              }},
              direct: [
                tools.evaluateConditionOperator(7, ">=", 5),
                tools.evaluateConditionOperator(7, "<", 5),
                tools.evaluateConditionOperator("route_good", "contains", "good"),
                tools.evaluateConditionOperator("route_good", "not_contains", "bad"),
                tools.evaluateConditionOperator("route_good", "starts_with", "route"),
                tools.evaluateConditionOperator("route_good", "ends_with", "good"),
                tools.evaluateConditionOperator(true, "!=", false),
                tools.normalizeConditionOperator("="),
              ],
              rules: [
                tools.evaluateConditionRule({{ variableId: "score", operator: ">=", value: "5" }}, variables, {{
                  normalizeVariableValue: (variableId, value) => variableId === "score" ? Number(value) : value,
                }}),
                tools.evaluateConditionRule({{ variableId: "route", operator: "contains", value: "common" }}, variables),
                tools.evaluateConditionRule({{ variableId: "missing", operator: "==", value: "fallback" }}, {{}}, {{
                  getVariableDefaultValue: () => "fallback",
                }}),
                tools.evaluateConditionRule({{ variableId: "flag", operator: "==", value: "true" }}, variables, {{
                  normalizeVariableValue: (variableId, value) => variableId === "flag" ? value === true || value === "true" : value,
                }}),
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
        self.assertIn("evaluateConditionRule", payload["keys"])
        self.assertEqual(payload["operators"]["strings"], ["contains", "not_contains", "starts_with", "ends_with"])
        self.assertEqual(payload["operators"]["numbers"], [">", ">=", "<", "<="])
        self.assertEqual(payload["operators"]["equalities"], ["==", "=", "!="])
        self.assertEqual(payload["direct"], [True, False, True, True, True, True, True, "=="])
        self.assertEqual(payload["rules"], [True, True, True, True])

    def test_editor_and_export_player_use_shared_condition_module(self) -> None:
        editor_index = EDITOR_INDEX_PATH.read_text(encoding="utf-8")
        player_index = PLAYER_INDEX_PATH.read_text(encoding="utf-8")
        app_source = APP_PATH.read_text(encoding="utf-8")
        player_source = PLAYER_PATH.read_text(encoding="utf-8")

        self.assertIn("../export_player_template/runtime_conditions.js", editor_index)
        self.assertIn("./runtime_conditions.js", player_index)
        self.assertIn("const runtimeConditionTools = window.CanvasiaRuntimeConditions;", app_source)
        self.assertIn("return runtimeConditionTools.evaluateConditionRule(rule, variables,", app_source)
        self.assertIn("const runtimeConditionTools = window.CanvasiaRuntimeConditions;", player_source)
        self.assertIn("return runtimeConditionTools.evaluateConditionRule(rule, variables,", player_source)


if __name__ == "__main__":
    unittest.main()
