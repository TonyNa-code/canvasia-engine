from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "dashboard_search_panel.js"


class FrontendDashboardSearchPanelModuleTests(unittest.TestCase):
    def test_dashboard_search_panel_renders_results_without_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorDashboardSearchPanel;
            const helpers = {{
              escapeHtml(value) {{
                return String(value ?? "")
                  .replaceAll("&", "&amp;")
                  .replaceAll("<", "&lt;")
                  .replaceAll(">", "&gt;")
                  .replaceAll('"', "&quot;")
                  .replaceAll("'", "&#39;");
              }},
              truncateText(value, maxLength) {{
                const text = String(value ?? "");
                return text.length > maxLength ? text.slice(0, maxLength) : text;
              }},
              renderRouteMetricCard(label, value, hint) {{
                const escape = (input) => String(input ?? "")
                  .replaceAll("&", "&amp;")
                  .replaceAll("<", "&lt;")
                  .replaceAll(">", "&gt;")
                  .replaceAll('"', "&quot;")
                  .replaceAll("'", "&#39;");
                return `<metric data-label="${{escape(label)}}" data-value="${{escape(value)}}" data-hint="${{escape(hint)}}"></metric>`;
              }},
              renderEmpty(message) {{
                return `<empty>${{message}}</empty>`;
              }},
            }};
            const overview = {{
              mode: "all",
              query: "雨夜 <script>",
              normalizedQuery: "雨夜",
              counts: {{ scenes: 1, characters: 1, lines: 2 }},
              scenes: [
                {{
                  resultType: "scene",
                  sceneId: "scene_1",
                  title: "雨夜校门",
                  meta: "第1章",
                  snippet: "第一次相遇",
                }},
              ],
              characters: [
                {{
                  resultType: "character",
                  characterId: "char_1",
                  title: "青叶",
                  meta: "女主角",
                  snippet: "喜欢雨声",
                }},
              ],
              lines: [
                {{
                  resultType: "line",
                  lineType: "dialogue",
                  sceneId: "scene_1",
                  blockId: "block_1",
                  title: "青叶",
                  meta: "第1章 / 雨夜校门",
                  snippet: "今晚也下雨呢",
                }},
                {{
                  resultType: "line",
                  lineType: "choice",
                  sceneId: "scene_1",
                  blockId: "block_2",
                  title: "选项",
                  meta: "第1章 / 雨夜校门",
                  snippet: "追上去 <危险>",
                }},
              ],
            }};
            const idleOverview = {{
              mode: "lines",
              query: "",
              normalizedQuery: "",
              counts: {{ scenes: 0, characters: 0, lines: 0 }},
              suggestions: ["青叶", "雨夜 <tag>"],
            }};
            const noResultOverview = {{
              mode: "characters",
              query: "不存在",
              normalizedQuery: "不存在",
              counts: {{ scenes: 0, characters: 0, lines: 0 }},
              scenes: [],
              characters: [],
              lines: [],
            }};
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              filterBar: tools.renderDashboardSearchFilterBar(overview, helpers),
              summary: tools.renderDashboardSearchSummary(overview, {{ sceneCount: 9, characterCount: 3, storyBlockCount: 21 }}, helpers),
              idleSummary: tools.renderDashboardSearchSummary(idleOverview, {{ sceneCount: 9, characterCount: 3, storyBlockCount: 21 }}, helpers),
              results: tools.renderDashboardSearchResults(overview, helpers),
              suggestions: tools.renderDashboardSearchResults(idleOverview, helpers),
              empty: tools.renderDashboardSearchResults(noResultOverview, helpers),
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

        self.assertIn("renderDashboardSearchFilterBar", payload["keys"])
        self.assertIn("renderDashboardSearchResultCard", payload["keys"])
        self.assertIn('data-action="set-dashboard-search-mode"', payload["filterBar"])
        self.assertIn('data-search-mode="scenes"', payload["filterBar"])
        self.assertIn("场景结果", payload["results"])
        self.assertIn("打开场景", payload["results"])
        self.assertIn("直接试玩", payload["results"])
        self.assertIn("打开角色页", payload["results"])
        self.assertIn("定位到卡片", payload["results"])
        self.assertIn("追上去 &lt;危险&gt;", payload["results"])
        self.assertIn("当前关键词", payload["summary"])
        self.assertIn("雨夜 &lt;script&gt;", payload["summary"])
        self.assertIn("搜索状态", payload["idleSummary"])
        self.assertIn("正文卡片", payload["idleSummary"])
        self.assertIn("可以直接试试这些词", payload["suggestions"])
        self.assertIn('data-query="雨夜 &lt;tag&gt;"', payload["suggestions"])
        self.assertIn("<empty>没有找到和“不存在”有关的场景、角色或台词。可以试试搜章节名、角色名或更短的关键字。</empty>", payload["empty"])


if __name__ == "__main__":
    unittest.main()
