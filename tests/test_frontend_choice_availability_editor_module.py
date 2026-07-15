from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
RUNTIME_MODULE = ROOT_DIR / "export_player_template" / "runtime_choice_availability.js"
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "choice_availability_editor.js"


class FrontendChoiceAvailabilityEditorModuleTests(unittest.TestCase):
    def test_renders_and_reads_choice_gate_without_app_state(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(RUNTIME_MODULE))}, "utf8"), context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorChoiceAvailability;
            const renderOptions = {{
              hasVariables: false,
              createDefaultConditionRule: () => ({{ variableId: "affection", operator: ">=", value: 5 }}),
              getSafeVariableId: (value) => value || "affection",
              getSafeConditionOperator: (_variableId, value) => value || ">=",
              renderVariableOptions: (value) => `<option>${{value}}</option>`,
              renderConditionOperatorOptions: (_variableId, value) => `<option>${{value}}</option>`,
              renderConditionValueFields: (_variableId, value) => `<input value="${{value}}">`,
              renderChoiceAvailabilityRuleEditorRow: (rule, index, count) => tools.renderChoiceAvailabilityRuleEditorRow(rule, index, count, renderOptions),
            }};
            const markup = tools.renderChoiceAvailabilityEditor({{
              choiceAvailabilityMode: "disable_when_false",
              choiceLockedReason: "需要 5 点好感度",
              choiceAvailabilityWhen: [{{ variableId: "affection", operator: ">=", value: 5 }}],
            }}, renderOptions);
            const ruleEditor = {{
              querySelector(selector) {{
                if (selector.includes("condition-variable")) return {{ value: "affection" }};
                if (selector.includes("condition-operator")) return {{ value: ">=" }};
                return null;
              }},
            }};
            const availabilityEditor = {{
              querySelector(selector) {{
                if (selector.includes("choice-availability-mode")) return {{ value: "disable_when_false" }};
                if (selector.includes("choice-locked-reason")) return {{ value: "需要 5 点好感度" }};
                return null;
              }},
              querySelectorAll() {{ return [ruleEditor]; }},
            }};
            const optionEditor = {{ querySelector() {{ return availabilityEditor; }} }};
            const value = tools.readChoiceAvailabilityEditor(optionEditor, {{
              getSafeVariableId: (item) => item,
              getSafeConditionOperator: (_variableId, item) => item,
              readConditionRuleValue: () => 5,
            }});
            process.stdout.write(JSON.stringify({{ markup, value, invalidMode: tools.normalizeMode("broken") }}));
            """
        )
        completed = subprocess.run(["node", "-e", script], cwd=ROOT_DIR, capture_output=True, text=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertIn("条件不满足时锁定", payload["markup"])
        self.assertIn("需要 5 点好感度", payload["markup"])
        self.assertIn("data-choice-availability-rule", payload["markup"])
        self.assertIn("还没有可用于判断的变量", payload["markup"])
        self.assertIn('data-screen="preview"', payload["markup"])
        self.assertEqual(payload["value"]["choiceAvailabilityMode"], "disable_when_false")
        self.assertEqual(payload["value"]["choiceAvailabilityWhen"][0]["value"], 5)
        self.assertEqual(payload["invalidMode"], "always")


if __name__ == "__main__":
    unittest.main()
