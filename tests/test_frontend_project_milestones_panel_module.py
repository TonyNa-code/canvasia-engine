from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MILESTONE_MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "project_milestones.js"
PANEL_MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "project_milestones_panel.js"


class FrontendProjectMilestonesPanelModuleTests(unittest.TestCase):
    def test_project_milestone_panel_renders_dashboard_and_compact_surfaces_without_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MILESTONE_MODULE_PATH))}, "utf8"), context);
            vm.runInContext(fs.readFileSync({json.dumps(str(PANEL_MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorProjectMilestonePanel;
            const milestone = {{
              id: "first_playable",
              title: "第一版可试玩 Demo",
              label: "先让它跑起来",
              tone: "warn",
              percent: 70,
              done: false,
              summary: "先补一段能跑通的内容。",
              blockers: [{{ label: "第一段正文", missing: "写入第一句台词", detail: "还没有正文", done: false }}],
              checks: [
                {{ label: "章节和场景骨架", detail: "1 章 / 1 场", missing: "先创建第一章和第一场", done: true }},
                {{ label: "第一段正文", detail: "已有正文", missing: "写入第一句台词", done: false }},
              ],
              actions: [{{ label: "去写正文", action: "switch-screen", screen: "story" }}],
            }};
            const plan = {{
              headline: "先让 Demo 跑起来",
              overallScore: 70,
              completedCount: 1,
              totalCount: 3,
              nextMilestone: milestone,
              milestones: [
                milestone,
                {{
                  ...milestone,
                  id: "release_candidate",
                  title: "发布候选",
                  label: "快到发布",
                  percent: 30,
                  done: false,
                }},
              ],
            }};
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
                const screen = action.screen ? ` data-screen="${{action.screen}}"` : "";
                return `<button class="${{emphasized ? "primary" : "secondary"}}" data-action="${{action.action ?? ""}}"${{screen}}>${{action.label ?? "继续"}}</button>`;
              }},
              renderRouteMetricCard(label, value, hint) {{
                return `<article class="metric"><span>${{label}}</span><strong>${{value}}</strong><small>${{hint ?? ""}}</small></article>`;
              }},
              buildDashboardProductionOverview() {{
                return {{ totalScenes: 1 }};
              }},
              buildProjectMilestonePlan() {{
                return plan;
              }},
              buildProjectMilestoneActionBrief() {{
                return {{
                  tone: "warn",
                  eyebrow: "今日工作台",
                  badge: "优先推进",
                  title: "先做：写入第一句台词",
                  description: "这是通往第一版可试玩 Demo 的最短路径。",
                  primaryAction: {{ label: "去写正文", action: "switch-screen", screen: "story" }},
                  secondaryActions: [{{ label: "打开项目巡检", action: "switch-screen", screen: "inspection" }}],
                  metrics: [
                    {{ label: "总进度", value: "70%", hint: "1/3 个阶段达标" }},
                    {{ label: "阶段缺口", value: "1 项", hint: "先清掉这一阶段" }},
                  ],
                  checklist: [{{ label: "第一段正文", detail: "写入第一句台词", done: false }}],
                }};
              }},
              buildProjectMilestoneGapDigest() {{
                return {{
                  status: "close",
                  eyebrow: "当前阶段缺口",
                  title: "第一版可试玩 Demo 还差 1 项",
                  description: "先处理正文缺口。",
                  overallScore: 70,
                  completedCount: 1,
                  totalCount: 3,
                  activePercent: 70,
                  activeBlockerCount: 1,
                  gapMetricLabel: "阶段缺口",
                  gapMetricHint: "先清掉这一阶段",
                  nextMilestoneTitle: "第一版可试玩 Demo",
                  topGaps: [{{ label: "第一段正文", missing: "写入第一句台词" }}],
                  nextAction: {{ label: "去写正文", action: "switch-screen", screen: "story" }},
                }};
              }},
              formatProjectMilestonePrimaryBlocker() {{
                return "写入第一句台词";
              }},
            }};
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              actionBrief: tools.renderDashboardActionBrief({{}}, helpers),
              fullPanel: tools.renderProjectMilestonePanel({{}}, helpers),
              compactPanel: tools.renderCompactProjectMilestonePanel({{}}, helpers),
              emptyChecklist: tools.renderDashboardActionBriefChecklist([], helpers),
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
        self.assertIn("renderDashboardActionBrief", payload["keys"])
        self.assertIn("renderProjectMilestonePanel", payload["keys"])
        self.assertIn("renderCompactProjectMilestonePanel", payload["keys"])
        self.assertIn("creator-focus-panel", payload["actionBrief"])
        self.assertIn("今日工作台", payload["actionBrief"])
        self.assertIn("先做：写入第一句台词", payload["actionBrief"])
        self.assertIn('data-action="switch-screen"', payload["actionBrief"])
        self.assertIn('data-screen="story"', payload["actionBrief"])
        self.assertIn("成品目标路线", payload["fullPanel"])
        self.assertIn("第一版可试玩 Demo", payload["fullPanel"])
        self.assertIn("project-milestone-compact-panel", payload["compactPanel"])
        self.assertIn("当前阶段缺口", payload["compactPanel"])
        self.assertIn("写入第一句台词", payload["compactPanel"])
        self.assertIn("当前没有明显缺口", payload["emptyChecklist"])


if __name__ == "__main__":
    unittest.main()
