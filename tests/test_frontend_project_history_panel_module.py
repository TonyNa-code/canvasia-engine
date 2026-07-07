from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "project_history_panel.js"


class FrontendProjectHistoryPanelModuleTests(unittest.TestCase):
    def test_project_history_panel_renders_safety_net_without_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorProjectHistoryPanel;
            const helpers = {{
              escapeHtml(value) {{
                return String(value ?? "")
                  .replaceAll("&", "&amp;")
                  .replaceAll("<", "&lt;")
                  .replaceAll(">", "&gt;")
                  .replaceAll('"', "&quot;")
                  .replaceAll("'", "&#39;");
              }},
              formatDate(value) {{
                return value === "2026-05-06T10:30:00Z" ? "2026/5/6 18:30" : `formatted:${{value}}`;
              }},
              renderRouteMetricCard(label, value, hint) {{
                return `<metric data-label="${{label}}" data-value="${{value}}" data-hint="${{hint}}"></metric>`;
              }},
              renderHistoryTimeline(history, options) {{
                return `<timeline data-total="${{history.totalSnapshots}}" data-count="${{options.filteredSnapshots.length}}"></timeline>`;
              }},
              getSafeHistoryFilterMode(value) {{
                return ["all", "manual", "auto", "baseline", "current"].includes(value) ? value : "all";
              }},
              getHistoryFilterLabel(value) {{
                return {{
                  all: "全部版本",
                  manual: "只看检查点",
                  auto: "只看自动快照",
                  baseline: "只看基线",
                  current: "只看当前版本",
                }}[value] ?? "全部版本";
              }},
            }};
            const html = tools.renderProjectHistoryPanel(
              {{
                history: {{
                  totalSnapshots: 4,
                  canUndo: true,
                  currentSnapshot: {{ label: "当前自动快照" }},
                  previousSnapshot: {{ label: "开工前检查点" }},
                  nextSnapshot: {{ label: "修复后版本" }},
                }},
                sessionRecovery: {{
                  noticeActive: true,
                  message: "上次可能异常退出 <请确认>",
                  lastUnexpectedExitStartedAt: "2026-05-06T10:30:00Z",
                }},
                filteredSnapshots: [{{ index: 0 }}, {{ index: 1 }}],
                historySearchQuery: "检查点 <script>",
                historyFilterMode: "manual",
              }},
              helpers
            );
            const disabledHtml = tools.renderProjectHistoryPanel(
              {{
                history: {{
                  totalSnapshots: 0,
                  canUndo: false,
                }},
                sessionRecovery: {{ noticeActive: false }},
                filteredSnapshots: [],
                historySearchQuery: "",
                historyFilterMode: "broken",
              }},
              helpers
            );
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              html,
              disabledHtml,
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
        html = payload["html"]
        disabled_html = payload["disabledHtml"]

        self.assertIn("renderProjectHistoryPanel", payload["keys"])
        self.assertIn("项目安全网", html)
        self.assertIn("立即存一个检查点", html)
        self.assertIn("回到上个版本", html)
        self.assertIn('data-action="restore-previous-version"', html)
        self.assertIn("总快照数", html)
        self.assertIn("当前自动快照", html)
        self.assertIn("开工前检查点", html)
        self.assertIn("修复后版本", html)
        self.assertIn("检测到上次可能异常退出", html)
        self.assertIn("上次可能异常退出 &lt;请确认&gt;", html)
        self.assertIn("2026/5/6 18:30", html)
        self.assertIn('value="检查点 &lt;script&gt;"', html)
        self.assertIn('data-action="clear-history-filters"', html)
        self.assertIn('data-history-filter="manual"', html)
        self.assertIn("只看检查点", html)
        self.assertIn('class="tag-chip is-active"', html)
        self.assertIn('<timeline data-total="4" data-count="2"></timeline>', html)
        self.assertIn('data-action="restore-previous-version" disabled', disabled_html)
        self.assertIn('data-history-filter="all"', disabled_html)


if __name__ == "__main__":
    unittest.main()
