from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "variables.js"
APP_PATH = ROOT_DIR / "prototype_editor" / "app.js"


class FrontendVariablesModuleTests(unittest.TestCase):
    def test_variable_helpers_work_without_browser_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorVariables;
            const variables = [
              {{ id: "score", name: "分数<危险>", type: "number", defaultValue: 12, min: 0, max: 10 }},
              {{ id: "route", name: "路线", type: "string", defaultValue: "common" }},
              {{ id: "flag", name: "开关", type: "boolean", defaultValue: true }},
            ];
            const options = {{
              variables,
              variablesById: new Map(variables.map((variable) => [variable.id, variable])),
            }};
            const escapedOptions = {{
              ...options,
              escapeHtml: (value) => String(value)
                .replaceAll("&", "&amp;")
                .replaceAll("<", "&lt;")
                .replaceAll(">", "&gt;")
                .replaceAll('"', "&quot;"),
            }};
            const copyIds = new Set(["var_affection", "var_affection_02"]);
            const result = {{
              keys: Object.keys(tools).sort(),
              starter: {{
                emptyTypes: tools.buildStarterVariableLibrary([]).map((variable) => variable.type),
                requireNumber: tools.buildStarterVariableLibrary(
                  [{{ id: "custom_route", name: "路线", type: "string", defaultValue: "x" }}],
                  {{ requireNumber: true }}
                ).map((variable) => variable.id),
                copiedId: tools.createStarterVariableCopy(tools.STARTER_VARIABLE_PRESETS[0], copyIds).id,
              }},
              bounds: [
                tools.parseVariableNumberBound(0),
                tools.parseVariableNumberBound("0"),
                tools.parseVariableNumberBound(false),
                tools.getVariableNumberBounds("score", options),
                tools.clampVariableNumber("score", -3, options),
                tools.clampVariableNumber("score", 20, options),
              ],
              variableLookup: [
                tools.getFilteredVariables("number", options).map((variable) => variable.id),
                tools.hasUsableVariable("boolean", options),
                tools.hasUsableVariable("missing", options),
                tools.getSafeVariableId("missing", "number", options),
                tools.getSafeVariableId("flag", null, options),
                tools.getVariableType("flag", options),
                tools.getVariableTypeLabel("boolean"),
              ],
              values: [
                tools.normalizeVariableValue("score", "7.5", options),
                tools.normalizeVariableValue("score", "bad", options),
                tools.getVariableDefaultValue("score", options),
                tools.normalizeVariableValue("flag", "false", options),
                tools.formatVariableValue("flag", true, options),
                tools.normalizeVariableValue("route", null, options),
                tools.formatVariableValue("route", "branch-a", options),
              ],
              conditions: [
                tools.getConditionOperators("score", options).map(([value]) => value),
                tools.getConditionOperators("route", options).map(([value]) => value),
                tools.getSafeConditionOperator("score", "???", options),
                tools.getSafeConditionOperator("route", "contains", options),
              ],
              choiceEffects: [
                tools.isEditableChoiceEffect({{ type: "variable_add" }}),
                tools.getEditableChoiceEffects([
                  {{ type: "jump" }},
                  {{ type: "variable_set", variableId: "route", value: "good" }},
                ]).length,
                tools.getSafeChoiceEffectType("unknown"),
                tools.getChoiceEffectVariableId("variable_add", "route", options),
                tools.normalizeChoiceEffect({{ type: "variable_add", variableId: "route", value: "2.5" }}, options),
                tools.normalizeChoiceEffect({{ type: "variable_set", variableId: "flag", value: "false" }}, options),
              ],
              projectVariableRules: {{
                filterKeys: Object.keys(tools.PROJECT_VARIABLE_FILTER_LABELS),
                statusKeys: Object.keys(tools.PROJECT_VARIABLE_STATUS_LABELS),
                safeTypes: [
                  tools.getSafeProjectVariableType("number"),
                  tools.getSafeProjectVariableType("bad"),
                ],
                safeFilters: [
                  tools.getSafeProjectVariableFilterMode("risky"),
                  tools.getSafeProjectVariableFilterMode("bad"),
                ],
                safeStatuses: [
                  tools.getSafeProjectVariableStatus("deprecated"),
                  tools.getSafeProjectVariableStatus("bad"),
                ],
                ids: [
                  tools.makeProjectVariableId("好感度", ["var_好感度"]),
                  tools.makeProjectVariableId("var_route", ["var_route", "var_route_02"]),
                ],
                idSafety: [
                  tools.isSafeProjectVariableId("var_好感度_02"),
                  tools.isSafeProjectVariableId("bad/slash"),
                ],
                idIssues: [
                  tools.getProjectVariableIdIssue("", "", options),
                  tools.getProjectVariableIdIssue("bad/slash", "", options),
                  tools.getProjectVariableIdIssue("score", "", options),
                  tools.getProjectVariableIdIssue("score", "score", options),
                ],
                defaults: [
                  tools.buildDefaultProjectVariable("number", variables),
                  tools.buildDefaultProjectVariable("boolean", variables),
                  tools.buildDefaultProjectVariable("bad", variables),
                ],
                renderedOptions: [
                  tools.renderProjectVariableTypeOptions("boolean", escapedOptions),
                  tools.renderProjectVariableStatusOptions("reserved", escapedOptions),
                ],
              }},
              render: [
                tools.renderVariableOptions("score", null, escapedOptions),
                tools.renderVariableOptions("", null, {{ variables: [] }}),
                tools.renderVariableSetValueFields("flag", false, escapedOptions),
                tools.renderConditionValueFields("score", 3, escapedOptions),
                tools.renderConditionOperatorOptions("score", ">=", escapedOptions),
                tools.renderChoiceEffectTypeOptions("variable_add", escapedOptions),
                tools.renderChoiceEffectValueFields("variable_set", "route", "a<b", escapedOptions),
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
        self.assertIn("buildStarterVariableLibrary", payload["keys"])
        self.assertIn("normalizeChoiceEffect", payload["keys"])
        self.assertEqual(payload["starter"]["emptyTypes"], ["number", "string", "boolean"])
        self.assertEqual(payload["starter"]["requireNumber"], ["custom_route", "var_affection"])
        self.assertEqual(payload["starter"]["copiedId"], "var_affection_03")
        self.assertEqual(payload["bounds"], [0, 0, None, [0, 10], 0, 10])
        self.assertEqual(payload["variableLookup"][0], ["score"])
        self.assertEqual(payload["variableLookup"][1:], [True, False, "score", "flag", "boolean", "开关"])
        self.assertEqual(payload["values"], [7.5, 12, 10, False, "是", "common", "branch-a"])
        self.assertEqual(
            payload["conditions"],
            [
                [">=", ">", "<=", "<", "==", "!="],
                ["==", "!=", "contains", "not_contains", "starts_with", "ends_with"],
                ">=",
                "contains",
            ],
        )
        self.assertEqual(payload["choiceEffects"][0:4], [True, 1, "variable_set", "score"])
        self.assertEqual(
            payload["choiceEffects"][4],
            {"type": "variable_add", "variableId": "score", "value": 2.5},
        )
        self.assertEqual(
            payload["choiceEffects"][5],
            {"type": "variable_set", "variableId": "flag", "value": False},
        )
        self.assertIn("draft", payload["projectVariableRules"]["filterKeys"])
        self.assertEqual(payload["projectVariableRules"]["statusKeys"], ["active", "reserved", "deprecated"])
        self.assertEqual(payload["projectVariableRules"]["safeTypes"], ["number", "string"])
        self.assertEqual(payload["projectVariableRules"]["safeFilters"], ["risky", "all"])
        self.assertEqual(payload["projectVariableRules"]["safeStatuses"], ["deprecated", "active"])
        self.assertEqual(payload["projectVariableRules"]["ids"], ["var_好感度_02", "var_route_03"])
        self.assertEqual(payload["projectVariableRules"]["idSafety"], [True, False])
        self.assertEqual(
            payload["projectVariableRules"]["idIssues"],
            ["逻辑 ID 不能为空", "逻辑 ID 含有不可用于发布的字符", "逻辑 ID 已被其他变量使用", ""],
        )
        self.assertEqual(
            [item["type"] for item in payload["projectVariableRules"]["defaults"]],
            ["number", "boolean", "string"],
        )
        self.assertEqual(payload["projectVariableRules"]["defaults"][0]["id"], "var_新数字变量")
        self.assertEqual(payload["projectVariableRules"]["defaults"][0]["max"], 100)
        self.assertFalse(payload["projectVariableRules"]["defaults"][1]["defaultValue"])
        self.assertEqual(payload["projectVariableRules"]["defaults"][2]["defaultValue"], "common")
        self.assertIn('<option value="boolean" selected>', payload["projectVariableRules"]["renderedOptions"][0])
        self.assertIn('<option value="reserved" selected>', payload["projectVariableRules"]["renderedOptions"][1])
        self.assertIn("分数&lt;危险&gt;", payload["render"][0])
        self.assertIn("当前没有可用变量", payload["render"][1])
        self.assertIn('<option value="false" selected>否</option>', payload["render"][2])
        self.assertIn('value="3"', payload["render"][3])
        self.assertIn('<option value=">=" selected>', payload["render"][4])
        self.assertIn("给数字变量加减数值", payload["render"][5])
        self.assertIn('value="a&lt;b"', payload["render"][6])

    def test_editor_app_keeps_variable_presets_in_variables_module(self) -> None:
        app_source = APP_PATH.read_text(encoding="utf-8")

        self.assertNotIn("const STARTER_VARIABLE_PRESETS =", app_source)
        self.assertIn("return variableTools.buildStarterVariableLibrary(existingVariables, options);", app_source)
        self.assertIn("return variableTools.normalizeChoiceEffect(effect, getVariableToolOptions());", app_source)
        self.assertNotIn("const PROJECT_VARIABLE_FILTER_LABELS = {", app_source)
        self.assertIn("PROJECT_VARIABLE_FILTER_LABELS,", app_source)
        self.assertIn("return variableTools.buildDefaultProjectVariable(type, state.data?.variables ?? []);", app_source)
        self.assertIn("return variableTools.getProjectVariableIdIssue(variableId, currentVariableId,", app_source)


if __name__ == "__main__":
    unittest.main()
