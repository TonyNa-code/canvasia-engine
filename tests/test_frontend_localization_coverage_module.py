from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "localization_coverage.js"


class FrontendLocalizationCoverageModuleTests(unittest.TestCase):
    def test_localization_coverage_helpers_export_markdown_and_csv(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorLocalizationCoverage;
            const data = {{
              project: {{
                title: "Demo Project",
                language: "zh-CN",
                supportedLanguages: ["zh-CN", "en-US", "ja-JP"],
              }},
              characters: [
                {{
                  id: "hero",
                  displayName: "蓝白女主",
                  displayNameTranslations: {{ "en-US": "Heroine", "ja-JP": "蓝白女主" }},
                }},
              ],
              chapters: [
                {{
                  id: "chapter_1",
                  name: "第一章",
                  nameTranslations: {{ "en-US": "Chapter One" }},
                }},
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
                    {{
                      id: "choice_1",
                      type: "choice",
                      options: [
                        {{ text: "留下来", textTranslations: {{ "en-US": "Stay", "ja-JP": "残る" }} }},
                        {{ text: "先回家", textTranslations: {{ "en-US": "Go home" }} }},
                      ],
                    }},
                  ],
                }},
              ],
            }};
            const coverage = tools.buildLocalizationCoverage(data);
            const digest = tools.getLocalizationCoverageStatusDigest(coverage);
            const markdown = tools.buildLocalizationCoverageMarkdown(coverage, {{
              projectTitle: "Demo Project",
              generatedAt: "2026-07-03 12:00:00",
            }});
            const csv = tools.buildLocalizationCoverageCsv(coverage);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              coverage,
              digest,
              markdown,
              csv,
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
        self.assertIn("buildLocalizationCoverage", payload["keys"])
        self.assertIn("buildLocalizationCoverageMarkdown", payload["keys"])
        self.assertIn("buildLocalizationCoverageCsv", payload["keys"])
        self.assertEqual(payload["coverage"]["defaultLanguage"], "zh-CN")
        self.assertEqual(payload["coverage"]["summary"]["targetLanguageCount"], 2)
        self.assertEqual(payload["coverage"]["summary"]["sourceTextCount"], 7)
        self.assertEqual(payload["coverage"]["summary"]["expectedTranslationCount"], 14)
        self.assertEqual(payload["coverage"]["summary"]["missingCount"], 3)
        self.assertEqual(payload["coverage"]["summary"]["sameAsSourceCount"], 2)
        self.assertEqual(payload["digest"]["status"], "warn")
        self.assertIn("多语言覆盖报告", payload["markdown"])
        self.assertIn("疑似未翻译", payload["markdown"])
        self.assertIn('"语言代码"', payload["csv"])
        self.assertIn('"Will you stay today too?"', payload["csv"])


if __name__ == "__main__":
    unittest.main()
