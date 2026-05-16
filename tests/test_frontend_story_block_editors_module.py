from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "story_block_editors.js"


class FrontendStoryBlockEditorsModuleTests(unittest.TestCase):
    def test_choice_editor_renderers_work_without_browser_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorStoryBlockEditors;
            const effectMarkup = tools.renderChoiceEffectEditorRow(
              {{ type: "variable_add", variableId: "score", value: 2 }},
              1,
              3,
              {{
                normalizeChoiceEffect: (effect) => effect,
                renderChoiceEffectTypeOptions: (selected) => `<option value="${{selected}}" selected>${{selected}}</option>`,
                renderVariableOptions: (selected, filter) => `<option value="${{selected}}" data-filter="${{filter}}">${{selected}}</option>`,
                renderChoiceEffectValueFields: (type, variableId, value) => `<input data-field="value" value="${{type}}:${{variableId}}:${{value}}" />`,
              }}
            );
            const optionMarkup = tools.renderChoiceOptionEditorRow(
              {{
                id: "opt\\"1",
                text: "一起 <回家>",
                gotoSceneId: "scene_b",
                effects: [
                  {{ type: "variable_add", variableId: "score", value: 2 }},
                  {{ type: "legacy_effect", value: "keep" }},
                ],
              }},
              0,
              2,
              {{
                scenes: [
                  {{ id: "scene_a", name: "开头" }},
                  {{ id: "scene_b", name: "结尾 & 真相" }},
                ],
                getEditableChoiceEffects: (effects) => effects.filter((effect) => effect.type === "variable_add"),
                renderChoiceTextQualityTools: (text) => `<small data-choice-text-tools>${{text.length}}</small>`,
                renderChoiceEffectEditorRow: (effect, index, count) => `<div data-rendered-effect="${{index}}/${{count}}">${{effect.variableId}}</div>`,
              }}
            );
            const ruleMarkup = tools.renderConditionRuleEditorRow(
              {{ variableId: "score", operator: ">=", value: 5 }},
              1,
              2,
              {{
                getSafeVariableId: (variableId) => variableId || "score",
                getSafeConditionOperator: (_variableId, operator) => operator || "==",
                renderVariableOptions: (selected) => `<option value="${{selected}}" selected>${{selected}}</option>`,
                renderConditionOperatorOptions: (_variableId, selected) => `<option value="${{selected}}" selected>${{selected}}</option>`,
                renderConditionValueFields: (variableId, value) => `<input data-field="condition-value" value="${{variableId}}:${{value}}" />`,
              }}
            );
            const branchMarkup = tools.renderConditionBranchEditorRow(
              {{
                id: "branch\\"1",
                gotoSceneId: "scene_b",
                when: [{{ variableId: "score", operator: ">=", value: 5 }}],
              }},
              0,
              2,
              {{
                getSafeSceneId: (sceneId) => sceneId || "scene_a",
                getDefaultJumpTargetSceneId: () => "scene_a",
                renderSceneOptions: (selected) => `<option value="${{selected}}" selected>${{selected}}</option>`,
                renderConditionRuleEditorRow: (rule, index, count) => `<div data-rendered-rule="${{index}}/${{count}}">${{rule.variableId}}</div>`,
              }}
            );
            const jumpMarkup = tools.renderJumpEditor(
              {{ targetSceneId: "scene_b" }},
              {{
                getSafeSceneId: (sceneId) => sceneId || "scene_a",
                renderSceneOptions: (selected) => `<option value="${{selected}}" selected>${{selected}}</option>`,
              }}
            );
            const starterMarkup = tools.renderVariableStarterPrompt(
              "还没有 <变量>",
              "先创建 & 再继续",
            );
            const variableSetMarkup = tools.renderVariableSetEditor(
              {{ variableId: "route", value: "common" }},
              {{
                getSafeVariableId: (variableId) => variableId || "route",
                getVariableType: () => "string",
                getVariableTypeLabel: () => "文本 <路线>",
                renderVariableOptions: (selected) => `<option value="${{selected}}" selected>${{selected}}</option>`,
                renderVariableSetValueFields: (variableId, value) => `<input data-field="variable-value" value="${{variableId}}:${{value}}" />`,
              }}
            );
            const variableAddMarkup = tools.renderVariableAddEditor(
              {{ variableId: "score", value: "3.5" }},
              {{
                getSafeVariableId: (variableId) => variableId || "score",
                getSafeNumber: (value, fallback) => Number.parseFloat(value || fallback),
                renderVariableOptions: (selected, filter) => `<option value="${{selected}}" data-filter="${{filter}}" selected>${{selected}}</option>`,
              }}
            );
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              effectMarkup,
              emptyMarkup: tools.renderChoiceEffectEmptyState(),
              optionMarkup,
              ruleMarkup,
              branchMarkup,
              jumpMarkup,
              starterMarkup,
              variableSetMarkup,
              variableAddMarkup,
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
        self.assertEqual(payload["keys"], [
            "renderChoiceEffectEditorRow",
            "renderChoiceEffectEmptyState",
            "renderChoiceOptionEditorRow",
            "renderConditionBranchEditorRow",
            "renderConditionRuleEditorRow",
            "renderJumpEditor",
            "renderVariableAddEditor",
            "renderVariableSetEditor",
            "renderVariableStarterPrompt",
        ])
        self.assertIn("编辑场景跳转", payload["jumpMarkup"])
        self.assertIn('value="scene_b" selected', payload["jumpMarkup"])
        self.assertIn("还没有 &lt;变量&gt;", payload["starterMarkup"])
        self.assertIn("先创建 &amp; 再继续", payload["starterMarkup"])
        self.assertIn("编辑变量设置", payload["variableSetMarkup"])
        self.assertIn("文本 &lt;路线&gt;", payload["variableSetMarkup"])
        self.assertIn('value="route:common"', payload["variableSetMarkup"])
        self.assertIn("编辑数字变量变化", payload["variableAddMarkup"])
        self.assertIn('data-filter="number"', payload["variableAddMarkup"])
        self.assertIn('value="3.5"', payload["variableAddMarkup"])
        self.assertIn("判断 2", payload["ruleMarkup"])
        self.assertIn('value="score:5"', payload["ruleMarkup"])
        self.assertIn("条件分支 1", payload["branchMarkup"])
        self.assertIn('data-branch-id="branch&quot;1"', payload["branchMarkup"])
        self.assertIn('data-rendered-rule="0/1"', payload["branchMarkup"])
        self.assertIn('data-action="move-condition-branch-up" disabled', payload["branchMarkup"])
        self.assertIn('value="scene_b" selected', payload["branchMarkup"])
        self.assertIn('data-action="add-condition-rule" data-branch-id="branch&quot;1"', payload["branchMarkup"])
        self.assertIn('data-action="remove-condition-branch" data-branch-id="branch&quot;1"', payload["branchMarkup"])
        self.assertIn("附加效果 2", payload["effectMarkup"])
        self.assertIn('data-filter="number"', payload["effectMarkup"])
        self.assertIn('value="variable_add:score:2"', payload["effectMarkup"])
        self.assertIn("data-choice-effects-empty", payload["emptyMarkup"])
        self.assertIn('data-option-id="opt&quot;1"', payload["optionMarkup"])
        self.assertIn("一起 &lt;回家&gt;", payload["optionMarkup"])
        self.assertIn("结尾 &amp; 真相", payload["optionMarkup"])
        self.assertIn('value="scene_b" selected', payload["optionMarkup"])
        self.assertIn('data-rendered-effect="0/1"', payload["optionMarkup"])
        self.assertIn("还有 1 条暂时不支持可视化编辑的旧效果", payload["optionMarkup"])


if __name__ == "__main__":
    unittest.main()
