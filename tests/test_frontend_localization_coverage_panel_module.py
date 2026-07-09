from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
EDITOR_COMMON_PATH = ROOT_DIR / "prototype_editor" / "modules" / "editor_common.js"
CATALOG_MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "story_block_catalog.js"
COVERAGE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "localization_coverage.js"
PANEL_PATH = ROOT_DIR / "prototype_editor" / "modules" / "localization_coverage_panel.js"


class FrontendLocalizationCoveragePanelModuleTests(unittest.TestCase):
    def test_localization_coverage_panel_renders_priority_queue_and_states(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            for (const filePath of [
              {json.dumps(str(EDITOR_COMMON_PATH))},
              {json.dumps(str(CATALOG_MODULE_PATH))},
              {json.dumps(str(COVERAGE_PATH))},
              {json.dumps(str(PANEL_PATH))},
            ]) {{
              vm.runInContext(fs.readFileSync(filePath, "utf8"), context);
            }}
            const coverageTools = context.window.CanvasiaEditorLocalizationCoverage;
            const panelTools = context.window.CanvasiaEditorLocalizationCoveragePanel;
            const issueCoverage = coverageTools.buildLocalizationCoverage({{
              project: {{
                title: "Demo Project",
                language: "zh-CN",
                supportedLanguages: ["zh-CN", "en-US", "ja-JP"],
              }},
              characters: [
                {{ id: "hero", displayName: "蓝白女主", displayNameTranslations: {{ "en-US": "Heroine" }} }},
              ],
              chapters: [
                {{ id: "chapter_1", name: "第一章", nameTranslations: {{ "en-US": "Chapter One" }} }},
              ],
              scenes: [
                {{
                  id: "scene_start",
                  chapterId: "chapter_1",
                  name: "开场",
                  nameTranslations: {{ "en-US": "Opening", "ja-JP": "開幕" }},
                  blocks: [
                    {{
                      id: "line_1",
                      type: "dialogue",
                      speakerId: "hero",
                      text: "今天也留下来吗？",
                      textTranslations: {{ "en-US": "Will you stay today too?" }},
                    }},
                    {{
                      id: "line_2",
                      type: "narration",
                      text: "窗外的夕阳正在下沉。",
                      textTranslations: {{ "en-US": "窗外的夕阳正在下沉。", "ja-JP": "夕日が沈んでいく。" }},
                    }},
                  ],
                }},
              ],
            }});
            const readyCoverage = coverageTools.buildLocalizationCoverage({{
              project: {{
                title: "Ready Project",
                language: "zh-CN",
                supportedLanguages: ["zh-CN", "en-US"],
              }},
              scenes: [
                {{
                  id: "scene_ready",
                  name: "开场",
                  nameTranslations: {{ "en-US": "Opening" }},
                  blocks: [
                    {{ id: "line_ready", type: "narration", text: "欢迎回来。", textTranslations: {{ "en-US": "Welcome back." }} }},
                  ],
                }},
              ],
            }});
            const emptyHtml = panelTools.renderLocalizationCoveragePanel({{ summary: {{}}, issues: [], languageBreakdown: [] }});
            const issueHtml = panelTools.renderLocalizationCoveragePanel(issueCoverage);
            const readyHtml = panelTools.renderLocalizationCoveragePanel(readyCoverage);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(panelTools).sort(),
              priorityRows: panelTools.buildTranslationPriorityRows(issueCoverage, 4),
              emptyHtml,
              issueHtml,
              readyHtml,
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
        self.assertIn("renderLocalizationCoveragePanel", payload["keys"])
        self.assertIn("renderTranslationPriorityQueue", payload["keys"])
        self.assertIn("buildTranslationPriorityRows", payload["keys"])
        self.assertGreaterEqual(len(payload["priorityRows"]), 1)
        self.assertIn("多语言覆盖检查", payload["issueHtml"])
        self.assertIn("翻译优先队列", payload["issueHtml"])
        self.assertIn("先补缺翻译，再查同文占位", payload["issueHtml"])
        self.assertIn("今天也留下来吗？", payload["issueHtml"])
        self.assertIn("疑似未翻译", payload["issueHtml"])
        self.assertIn("应填翻译", payload["issueHtml"])
        self.assertIn("已完成", payload["issueHtml"])
        self.assertIn('data-action="export-localization-coverage-markdown"', payload["issueHtml"])
        self.assertIn('data-action="export-localization-coverage-csv"', payload["issueHtml"])
        self.assertIn('data-action="import-localization-coverage-csv"', payload["issueHtml"])
        self.assertIn("English", payload["readyHtml"])
        self.assertIn("完成 2/2", payload["readyHtml"])
        self.assertNotIn("翻译优先队列", payload["readyHtml"])
        self.assertIn("当前项目仍是单语言流程", payload["emptyHtml"])


if __name__ == "__main__":
    unittest.main()
