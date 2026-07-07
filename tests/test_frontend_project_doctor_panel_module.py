from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "project_doctor_panel.js"


class FrontendProjectDoctorPanelModuleTests(unittest.TestCase):
    def test_project_doctor_panel_renders_queue_and_repair_controls_without_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorProjectDoctorPanel;
            const helpers = {{
              escapeHtml(value) {{
                return String(value ?? "")
                  .replaceAll("&", "&amp;")
                  .replaceAll("<", "&lt;")
                  .replaceAll(">", "&gt;")
                  .replaceAll('"', "&quot;")
                  .replaceAll("'", "&#39;");
              }},
              renderQuickActionButton(action, emphasized = false) {{
                const disabled = action.disabled ? " disabled" : "";
                const datasetMarkup = Object.entries(action.dataset ?? {{}})
                  .map(([key, value]) => ` data-${{key}}="${{value}}"`)
                  .join("");
                return `<button class="${{emphasized ? "primary" : "secondary"}}" data-action="${{action.action ?? ""}}"${{datasetMarkup}}${{disabled}}>${{action.label ?? "继续"}}</button>`;
              }},
              renderRouteMetricCard(label, value, hint) {{
                return `<metric data-label="${{label}}" data-value="${{value}}" data-hint="${{hint}}"></metric>`;
              }},
              getDashboardTaskToneClass(tone) {{
                return tone === "danger" ? "danger-text" : tone === "warn" ? "warn-text" : "";
              }},
              renderEmpty(message) {{
                return `<empty>${{message}}</empty>`;
              }},
              buildProjectDoctorQueue() {{
                return [
                  {{
                    order: 1,
                    tone: "danger",
                    title: "入口场景不存在",
                    badge: "先修",
                    label: "结构错误",
                    meta: "项目设置 / entrySceneId",
                    why: "试玩会从不存在的场景开始。",
                    recovery: "先预览安全修复，确认后再执行。",
                    diagnostic: "entrySceneId 指向 missing_scene",
                    doneWhen: "重新巡检后入口场景错误消失。",
                    actions: [
                      {{ label: "先预览这项修复", action: "preview-project-doctor-repair", dataset: {{ "repair-codes": "entry_scene" }} }},
                      {{ label: "确认执行这项修复", action: "repair-project-doctor", dataset: {{ "repair-codes": "entry_scene" }} }},
                    ],
                  }},
                ];
              }},
              buildProjectDoctorSummary() {{
                return {{
                  status: "danger",
                  title: "项目医生排出了 1 个优先步骤",
                  badge: "先修硬阻塞",
                  description: "按这个顺序处理最省时间。",
                  dangerCount: 1,
                  warnCount: 0,
                  softCount: 0,
                  autoRepairableCount: 1,
                }};
              }},
              getCurrentProjectDoctorPreviewRepairCodes() {{
                return ["entry_scene"];
              }},
              renderProjectDoctorRepairReceiptPanel() {{
                return `<receipt>预览回执</receipt>`;
              }},
            }};
            const stepHtml = tools.renderProjectDoctorStepCard(helpers.buildProjectDoctorQueue()[0], helpers);
            const panelHtml = tools.renderProjectDoctorPanel({{}}, [], helpers);
            const cleanHtml = tools.renderProjectDoctorPanel({{}}, [], {{
              ...helpers,
              buildProjectDoctorQueue() {{ return []; }},
              buildProjectDoctorSummary() {{
                return {{
                  status: "clean",
                  title: "项目医生没有发现需要优先处理的事项",
                  badge: "很干净",
                  description: "可以继续试玩。",
                  dangerCount: 0,
                  warnCount: 0,
                  softCount: 0,
                  autoRepairableCount: 0,
                }};
              }},
              getCurrentProjectDoctorPreviewRepairCodes() {{ return []; }},
            }});
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              stepHtml,
              panelHtml,
              cleanHtml,
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
        self.assertIn("renderProjectDoctorPanel", payload["keys"])
        self.assertIn("renderProjectDoctorStepCard", payload["keys"])
        self.assertIn("入口场景不存在", payload["stepHtml"])
        self.assertIn("条件/变量诊断", payload["stepHtml"])
        self.assertIn('data-action="preview-project-doctor-repair"', payload["stepHtml"])
        self.assertIn("项目医生 / 小白修复向导", payload["panelHtml"])
        self.assertIn("把巡检结果变成可执行步骤", payload["panelHtml"])
        self.assertIn('data-action="repair-project-doctor" data-repair-codes="entry_scene"', payload["panelHtml"])
        self.assertIn("<receipt>预览回执</receipt>", payload["panelHtml"])
        self.assertIn("可安全修复", payload["panelHtml"])
        self.assertIn("预览后可执行修复", payload["cleanHtml"])
        self.assertIn("disabled aria-disabled=\"true\"", payload["cleanHtml"])
        self.assertIn("项目医生暂时没有排出修复队列", payload["cleanHtml"])


if __name__ == "__main__":
    unittest.main()
