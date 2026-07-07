from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "release_control_panel.js"


class FrontendReleaseControlPanelModuleTests(unittest.TestCase):
    def test_release_control_panel_renders_action_card_and_fix_steps_without_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorReleaseControlPanel;
            const html = tools.renderReleaseFixOrderPanel({{}}, {{
              escapeHtml(value) {{
                return String(value ?? "")
                  .replaceAll("&", "&amp;")
                  .replaceAll("<", "&lt;")
                  .replaceAll(">", "&gt;")
                  .replaceAll('"', "&quot;")
                  .replaceAll("'", "&#39;");
              }},
              getDashboardTaskToneClass(tone) {{
                return tone === "danger" ? "danger-text" : tone === "warn" ? "warn-text" : tone === "good" ? "good-text" : "";
              }},
              renderQuickActionButton(action, emphasized = false) {{
                return `<button class="${{emphasized ? "primary" : "secondary"}}" data-action="${{action.action ?? ""}}">${{action.label ?? "继续"}}</button>`;
              }},
              buildReleaseFixOrder() {{
                return {{
                  steps: [
                    {{
                      tone: "danger",
                      title: "处理生产待办先修项",
                      statusLabel: "先修 1 / 优先 2 / 润色 1",
                      description: "先补空白场景。",
                      routeIssueQueue: [
                        {{ title: "修复分支坏链", sceneName: "教室", routeLabel: "留下", targetLabel: "天台", statusLabel: "坏链" }},
                      ],
                      productionBacklogTask: {{
                        title: "补齐空白场景内容",
                        source: "第1章 / 空白场景",
                        detail: "这个场景只有占位文本。",
                        action: {{ label: "补演出卡" }},
                      }},
                      actions: [{{ label: "补演出卡", action: "open-scene-from-map" }}],
                    }},
                  ],
                }};
              }},
              buildProjectMilestonePlan() {{ return {{}}; }},
              buildProjectMilestoneGapDigest() {{ return {{ status: "gap" }}; }},
              buildReleaseReportNextStep() {{
                return {{
                  source: "release_fix_order",
                  sourceLabel: "发布修复顺序",
                  tone: "warn",
                  title: "处理生产待办先修项",
                  description: "先补空白场景。",
                  statusLabel: "先修 1 项",
                  action: {{ label: "补演出卡", action: "open-scene-from-map" }},
                }};
              }},
              buildReleaseNextActionCard() {{
                return {{
                  source: "release_fix_order",
                  sourceLabel: "发布修复顺序",
                  tone: "warn",
                  badge: "先修 1 项",
                  title: "现在先做：处理生产待办先修项",
                  description: "先补空白场景。",
                  verification: "做完后重新生成发布前修复顺序。",
                  action: {{ label: "补演出卡", action: "open-scene-from-map" }},
                }};
              }},
            }});
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              html,
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
        self.assertIn("renderReleaseFixOrderPanel", payload["keys"])
        self.assertIn("renderReleaseNextActionCard", payload["keys"])
        self.assertIn("现在先做：处理生产待办先修项", payload["html"])
        self.assertIn("具体路线问题", payload["html"])
        self.assertIn("修复分支坏链：教室 / 留下 / 天台", payload["html"])
        self.assertIn("生产待办下一项", payload["html"])
        self.assertIn("补齐空白场景内容", payload["html"])
        self.assertIn('data-action="generate-release-fix-order"', payload["html"])
        self.assertIn('data-action="export-release-control-report"', payload["html"])
        self.assertIn('data-action="open-scene-from-map"', payload["html"])


if __name__ == "__main__":
    unittest.main()
