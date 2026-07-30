from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "project_variable_governance.js"


class FrontendProjectVariableGovernanceModuleTests(unittest.TestCase):
    def test_governance_module_scores_filters_renders_and_exports_safely(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorProjectVariableGovernance;
            const variables = [
              {{
                id: "affection",
                name: "好感度",
                type: "number",
                scope: "save",
                status: "active",
                defaultValue: 10,
                min: 0,
                max: 100,
              }},
              {{
                id: "old route",
                name: "旧路线",
                type: "boolean",
                scope: "persistent",
                status: "deprecated",
                defaultValue: false,
              }},
              {{
                id: "spare",
                name: "预留文本",
                type: "string",
                scope: "save",
                status: "reserved",
                defaultValue: "",
              }},
            ];
            const usageMap = new Map([
              ["affection", {{ total: 3, references: [{{ label: "教室黄昏 / 条件" }}] }}],
              ["old route", {{ total: 1 }}],
            ]);
            const options = {{
              getDraft: (id) => id === "spare" ? {{ name: "预留文本草稿" }} : null,
              buildDraftModel: (variable) => variable.id === "spare"
                ? {{ ...variable, name: "预留文本草稿" }}
                : variable,
              getRangeIssues: (variable) => Number(variable.min) > Number(variable.max)
                ? ["范围最小值不能大于最大值"]
                : [],
              getIdIssue: (id) => id.includes(" ") ? "变量 ID 格式错误" : "",
              getSafeStatus: (status) => status || "active",
              getSafeScope: (scope) => scope || "save",
              getVariableTypeLabel: (type) => ({{ number: "数字", boolean: "开关", string: "文本" }}[type] || type),
              getDefaultInputValue: (variable) => String(variable.defaultValue ?? ""),
              isPersistentVariable: (variable) => variable.scope === "persistent",
              escapeHtml: (value) => String(value ?? ""),
              renderMetricCard: (label, value) => `<span data-metric="${{label}}">${{value}}</span>`,
              renderEmpty: (message) => `<p>${{message}}</p>`,
              renderEditorRow: (variable) => `<article data-variable-id="${{variable.id}}"></article>`,
              filterLabels: {{ all: "全部", risky: "有风险", unused: "未引用", persistent: "跨周目" }},
              scopeLabels: {{ save: "当前存档", persistent: "跨周目" }},
              statusLabels: {{ active: "使用中", reserved: "预留", deprecated: "已废弃" }},
            }};
            const items = tools.buildGovernanceItems(variables, usageMap, options);
            const riskyItem = items.find((item) => item.variable.id === "old route");
            const spareItem = items.find((item) => item.variable.id === "spare");
            const html = tools.renderLibraryPanel({{
              variables,
              searchQuery: "",
              filterMode: "all",
              usageMap,
              governanceItems: items,
            }}, options);
            const report = tools.buildAuditReport(items, {{
              projectTitle: "变量治理测试",
              generatedAt: "2026-07-31 12:00",
            }}, options);

            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              score: tools.getGovernanceScore(items),
              riskyIssues: riskyItem.issues,
              riskyMatch: tools.isMatchingFilter(riskyItem, "risky", options),
              persistentMatch: tools.isMatchingFilter(riskyItem, "persistent", options),
              unusedMatch: tools.isMatchingFilter(spareItem, "unused", options),
              hasDraft: spareItem.hasDraft,
              hasLibraryTitle: html.includes("变量库管理台"),
              hasGovernanceRadar: html.includes("变量治理雷达"),
              hasAddAction: html.includes('data-action="add-project-variable"'),
              hasRenderedVariables: html.includes('data-variable-id="affection"') && html.includes('data-variable-id="spare"'),
              reportHasBom: report.charCodeAt(0) === 0xfeff,
              reportHasTitle: report.includes("Canvasia Engine 变量治理报告"),
              reportHasProject: report.includes("项目：变量治理测试"),
              reportHasMissingReferenceFallback: report.includes("旧路线"),
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
        self.assertEqual(
            payload["keys"],
            [
                "DEFAULT_USAGE",
                "buildAuditReport",
                "buildGovernanceItems",
                "getGovernanceScore",
                "isMatchingFilter",
                "renderFilterButtons",
                "renderGovernancePanel",
                "renderLibraryPanel",
            ],
        )
        self.assertLess(payload["score"], 100)
        self.assertIn("变量 ID 格式错误", payload["riskyIssues"])
        self.assertIn("废弃变量仍被引用", payload["riskyIssues"])
        self.assertTrue(payload["riskyMatch"])
        self.assertTrue(payload["persistentMatch"])
        self.assertTrue(payload["unusedMatch"])
        self.assertTrue(payload["hasDraft"])
        self.assertTrue(payload["hasLibraryTitle"])
        self.assertTrue(payload["hasGovernanceRadar"])
        self.assertTrue(payload["hasAddAction"])
        self.assertTrue(payload["hasRenderedVariables"])
        self.assertTrue(payload["reportHasBom"])
        self.assertTrue(payload["reportHasTitle"])
        self.assertTrue(payload["reportHasProject"])
        self.assertTrue(payload["reportHasMissingReferenceFallback"])


if __name__ == "__main__":
    unittest.main()
