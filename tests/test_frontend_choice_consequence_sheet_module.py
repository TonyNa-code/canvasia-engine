from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "choice_consequence_sheet.js"


class FrontendChoiceConsequenceSheetModuleTests(unittest.TestCase):
    def test_choice_consequence_sheet_helpers_export_markdown_and_csv(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorChoiceConsequenceSheet;
            const data = {{
              project: {{ title: "Demo Project" }},
              chapters: [{{ id: "chapter_1", name: "第1章" }}],
              variables: [
                {{ id: "affection", name: "好感度", type: "number" }},
                {{ id: "route", name: "路线", type: "string" }},
              ],
              scenes: [
                {{
                  id: "scene_start",
                  chapterId: "chapter_1",
                  name: "教室黄昏",
                  blocks: [
                    {{
                      id: "choice_main",
                      type: "choice",
                      options: [
                        {{
                          id: "go_roof",
                          text: "去天台",
                          gotoSceneId: "scene_roof",
                          effects: [{{ type: "variable_add", variableId: "affection", value: 1 }}],
                        }},
                        {{
                          id: "stay",
                          text: "留在教室",
                          gotoSceneId: "scene_missing",
                          effects: [{{ type: "variable_set", variableId: "route", value: "classroom" }}],
                        }},
                        {{ id: "noop", text: "沉默" }},
                      ],
                    }},
                    {{
                      id: "choice_fake",
                      type: "choice",
                      options: [
                        {{ id: "a", text: "追上去", gotoSceneId: "scene_roof" }},
                        {{ id: "b", text: "追上去", gotoSceneId: "scene_roof" }},
                      ],
                    }},
                    {{
                      id: "choice_bad_variable",
                      type: "choice",
                      options: [
                        {{ id: "bad_add", text: "改路线", effects: [{{ type: "variable_add", variableId: "route", value: 1 }}] }},
                        {{ id: "bad_missing", text: "", effects: [{{ type: "variable_set", variableId: "unknown", value: true }}] }},
                      ],
                    }},
                  ],
                }},
                {{ id: "scene_roof", chapterId: "chapter_1", name: "屋顶", blocks: [] }},
              ],
            }};
            const sheet = tools.buildChoiceConsequenceSheet(data);
            const digest = tools.getChoiceConsequenceStatusDigest(sheet);
            const markdown = tools.buildChoiceConsequenceMarkdown(sheet, {{
              projectTitle: "Demo Project",
              generatedAt: "2026-05-11 12:00:00",
            }});
            const csv = tools.buildChoiceConsequenceCsv(sheet);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              sheet,
              digest,
              markdown,
              csv,
              effectLabel: tools.getEffectTypeLabel("variable_add"),
              effectSummary: tools.summarizeChoiceEffect({{ type: "variable_set", variableId: "route", value: "good" }}, new Map([["route", {{ name: "路线" }}]])),
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
        self.assertIn("buildChoiceConsequenceSheet", payload["keys"])
        self.assertIn("buildChoiceConsequenceMarkdown", payload["keys"])
        self.assertIn("buildChoiceConsequenceCsv", payload["keys"])
        self.assertEqual(payload["sheet"]["summary"]["choiceBlockCount"], 3)
        self.assertEqual(payload["sheet"]["summary"]["optionCount"], 7)
        self.assertEqual(payload["sheet"]["summary"]["variableEffectCount"], 4)
        self.assertEqual(payload["sheet"]["summary"]["noConsequenceCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["sameConsequenceCount"], 2)
        self.assertEqual(payload["sheet"]["summary"]["brokenTargetCount"], 1)
        self.assertGreaterEqual(payload["sheet"]["summary"]["brokenVariableCount"], 2)
        self.assertEqual(payload["digest"]["status"], "blocked")
        issue_codes = [issue["code"] for issue in payload["sheet"]["issues"]]
        self.assertIn("choice_option_unknown_target", issue_codes)
        self.assertIn("choice_option_no_consequence", issue_codes)
        self.assertIn("choice_same_consequence", issue_codes)
        self.assertIn("choice_duplicate_text", issue_codes)
        self.assertIn("choice_effect_add_non_number", issue_codes)
        self.assertIn("choice_effect_unknown_variable", issue_codes)
        self.assertIn("choice_option_empty_text", issue_codes)
        self.assertIn("# Demo Project 选项后果表", payload["markdown"])
        self.assertIn("留在教室", payload["markdown"])
        self.assertIn('"好感度 + 1"', payload["csv"])
        self.assertEqual(payload["effectLabel"], "变量增加")
        self.assertEqual(payload["effectSummary"], "路线 = good")


if __name__ == "__main__":
    unittest.main()
