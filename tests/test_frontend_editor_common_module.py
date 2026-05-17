from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "editor_common.js"


class FrontendEditorCommonModuleTests(unittest.TestCase):
    def test_editor_common_helpers_work_without_browser_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorCommon;
            const result = {{
              keys: Object.keys(tools).sort(),
              fileNames: [
                tools.sanitizeFileName("  chapter 01:雨夜/告白?.txt  "),
                tools.sanitizeFileName("***"),
                tools.sanitizeFileName(null),
              ],
              csvCells: [
                tools.formatCsvCell('她说 "你好"'),
                tools.formatCsvCell(null),
              ],
              truncation: [
                tools.truncateText("  abc  ", 4),
                tools.truncateText("abcdef", 4),
                tools.truncateText("abcdef", 0),
                tools.truncateText(null, 4),
              ],
              dates: [
                tools.formatDate(""),
                tools.formatDate("not-a-date"),
                tools.formatDate("2026-05-06T00:00:00.000Z", {{
                  locale: "en-US",
                  formatOptions: {{ timeZone: "UTC", hour12: false }},
                }}),
              ],
              numbers: [
                tools.getSafeNonNegativeNumber("12px", 7),
                tools.getSafeNonNegativeNumber("-5", 7),
                tools.getSafeNonNegativeNumber("bad", 7),
                tools.getSafeNumber("3.5rem", 9),
                tools.getSafeNumber("", 9),
                tools.getSafeNumber("0", 9),
              ],
              urls: [
                tools.buildTemplateAssetUrl("/背景/scene one.png", "/public/root/"),
                tools.buildTemplateAssetUrl("voices\\\\hero line.ogg", "assets"),
                tools.buildTemplateAssetUrl("", "assets"),
                tools.buildTemplateAssetUrl("bg.png", ""),
              ],
              sizes: [
                tools.formatFileSize(-1),
                tools.formatFileSize(512),
                tools.formatFileSize(1536),
                tools.formatFileSize(15 * 1024),
                tools.formatFileSize(2.5 * 1024 * 1024),
                tools.formatFileSize(18 * 1024 * 1024),
              ],
              clamp: [
                tools.clamp(-1, 0, 10),
                tools.clamp(4, 0, 10),
                tools.clamp(20, 0, 10),
              ],
              html: tools.escapeHtml(`<button data-x="1">'&'</button>`),
              detailRowsMarkup: tools.renderDetailRows([
                ["场景 <名>", "雨夜 & 告白"],
                ["顺序", "第 2 张 / 共 3 张"],
              ]),
              statCardMarkup: tools.renderStatCard("素材 <数>", "<strong>5</strong>"),
              emptyMarkup: tools.renderEmpty("还没有 <内容> & 数据"),
              quickButtonMarkup: tools.renderQuickActionButton({{
                label: "切到 <剧情>",
                action: "switch-screen",
                dataset: {{ screen: "story" }},
              }}, true),
              disabledQuickButtonMarkup: tools.renderQuickActionButton({{
                label: "确认 <执行>",
                action: "repair-project-doctor",
                disabled: true,
                title: "先点“预览”再执行",
                dataset: {{ "repair-codes": "entry_scene,scene_order" }},
              }}),
              dashboardActionsMarkup: tools.renderDashboardTaskActions([
                {{ label: "第一步", action: "switch-screen", screen: "story" }},
                {{ label: "第二步", action: "open-scene-from-map", sceneId: "scene_1" }},
                {{ label: "第三步", action: "ignored-action" }},
              ]),
              routeMetricMarkup: tools.renderRouteMetricCard("路线 <数>", "2 & 3", "坏链 <0>"),
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
        self.assertIn("escapeHtml", payload["keys"])
        self.assertIn("buildTemplateAssetUrl", payload["keys"])
        self.assertIn("renderDetailRows", payload["keys"])
        self.assertIn("renderStatCard", payload["keys"])
        self.assertIn("renderEmpty", payload["keys"])
        self.assertIn("renderQuickActionButton", payload["keys"])
        self.assertIn("renderDashboardTaskActions", payload["keys"])
        self.assertIn("renderRouteMetricCard", payload["keys"])
        self.assertEqual(payload["fileNames"], ["chapter_01_雨夜_告白_.txt", "", ""])
        self.assertEqual(payload["csvCells"], ['"她说 ""你好"""', '""'])
        self.assertEqual(payload["truncation"], ["abc", "abc…", "a…", ""])
        self.assertEqual(payload["dates"][0], "未知")
        self.assertEqual(payload["dates"][1], "not-a-date")
        self.assertIn("5/6/2026", payload["dates"][2])
        self.assertEqual(payload["numbers"], [12, 0, 7, 3.5, 9, 0])
        self.assertEqual(
            payload["urls"],
            [
                "/public/root/%E8%83%8C%E6%99%AF/scene%20one.png",
                "assets/voices/hero%20line.ogg",
                "",
                "",
            ],
        )
        self.assertEqual(payload["sizes"], ["未知", "512 B", "1.5 KB", "15 KB", "2.5 MB", "18 MB"])
        self.assertEqual(payload["clamp"], [0, 4, 10])
        self.assertEqual(payload["html"], "&lt;button data-x=&quot;1&quot;&gt;&#39;&amp;&#39;&lt;/button&gt;")
        self.assertIn("<label>场景 &lt;名&gt;</label>", payload["detailRowsMarkup"])
        self.assertIn('<div class="value">雨夜 &amp; 告白</div>', payload["detailRowsMarkup"])
        self.assertIn("<label>顺序</label>", payload["detailRowsMarkup"])
        self.assertIn("<h3>素材 &lt;数&gt;</h3>", payload["statCardMarkup"])
        self.assertIn("<strong><strong>5</strong></strong>", payload["statCardMarkup"])
        self.assertEqual(payload["emptyMarkup"], '<div class="empty-note">还没有 &lt;内容&gt; &amp; 数据</div>')
        self.assertIn('data-action="switch-screen"', payload["quickButtonMarkup"])
        self.assertIn('data-screen="story"', payload["quickButtonMarkup"])
        self.assertIn("切到 &lt;剧情&gt;", payload["quickButtonMarkup"])
        self.assertIn("toolbar-button-primary", payload["quickButtonMarkup"])
        self.assertIn('data-action="repair-project-doctor"', payload["disabledQuickButtonMarkup"])
        self.assertIn('data-repair-codes="entry_scene,scene_order"', payload["disabledQuickButtonMarkup"])
        self.assertIn('disabled aria-disabled="true"', payload["disabledQuickButtonMarkup"])
        self.assertIn('title="先点“预览”再执行"', payload["disabledQuickButtonMarkup"])
        self.assertIn('data-action="open-scene-from-map"', payload["dashboardActionsMarkup"])
        self.assertNotIn("ignored-action", payload["dashboardActionsMarkup"])
        self.assertIn("<span>路线 &lt;数&gt;</span>", payload["routeMetricMarkup"])
        self.assertIn("<strong>2 &amp; 3</strong>", payload["routeMetricMarkup"])
        self.assertIn("<small>坏链 &lt;0&gt;</small>", payload["routeMetricMarkup"])


if __name__ == "__main__":
    unittest.main()
