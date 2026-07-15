from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "variable_influence_sheet.js"


class FrontendVariableInfluenceSheetModuleTests(unittest.TestCase):
    def test_variable_influence_sheet_helpers_export_markdown_and_csv(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorVariableInfluenceSheet;
            const data = {{
              project: {{ title: "Demo Project" }},
              chapters: [{{ id: "chapter_1", name: "第1章" }}],
              variables: [
                {{ id: "score", name: "分数", type: "number", defaultValue: 5, min: 0, max: 10 }},
                {{ id: "route", name: "路线", type: "string", defaultValue: "common" }},
                {{ id: "flag", name: "开关", type: "boolean", defaultValue: false }},
                {{ id: "unused", name: "废弃变量", type: "boolean", defaultValue: false }},
                {{ id: "bad_range", name: "坏范围", type: "number", defaultValue: 99, min: 10, max: 1 }},
              ],
              scenes: [
                {{
                  id: "scene_start",
                  chapterId: "chapter_1",
                  name: "教室黄昏",
                  blocks: [
                    {{ id: "set_score_bad", type: "variable_set", variableId: "score", value: "bad" }},
                    {{ id: "add_route_bad", type: "variable_add", variableId: "route", value: 1 }},
                    {{
                      id: "choice_main",
                      type: "choice",
                      options: [
                        {{
                          id: "go_roof",
                          text: "去天台",
                          choiceAvailabilityMode: "hide_when_false",
                          choiceAvailabilityWhen: [{{ variableId: "flag", operator: "==", value: true }}],
                          effects: [{{ type: "variable_add", variableId: "score", value: 1 }}],
                        }},
                        {{
                          id: "bad_missing",
                          text: "调试坏变量",
                          effects: [{{ type: "variable_set", variableId: "missing_var", value: true }}],
                        }},
                      ],
                    }},
                    {{
                      id: "route_gate",
                      type: "condition",
                      branches: [
                        {{
                          when: [
                            {{ variableId: "flag", operator: "==", value: true }},
                            {{ variableId: "ghost", operator: "==", value: 1 }},
                          ],
                          targetSceneId: "scene_roof",
                        }},
                      ],
                    }},
                  ],
                }},
                {{ id: "scene_roof", chapterId: "chapter_1", name: "屋顶", blocks: [] }},
              ],
            }};
            const sheet = tools.buildVariableInfluenceSheet(data);
            const digest = tools.getVariableInfluenceStatusDigest(sheet);
            const markdown = tools.buildVariableInfluenceMarkdown(sheet, {{
              projectTitle: "Demo Project",
              generatedAt: "2026-07-04 00:00:00",
            }});
            const csv = tools.buildVariableInfluenceCsv(sheet);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              sheet,
              digest,
              markdown,
              csv,
              booleanLabel: tools.getVariableTypeLabel("boolean"),
              conditionLabel: tools.getUsageLabel("condition"),
              choiceGateLabel: tools.getUsageLabel("choice_gate"),
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
        self.assertIn("buildVariableInfluenceSheet", payload["keys"])
        self.assertIn("buildVariableInfluenceMarkdown", payload["keys"])
        self.assertIn("buildVariableInfluenceCsv", payload["keys"])
        self.assertEqual(payload["sheet"]["summary"]["variableCount"], 5)
        self.assertEqual(payload["sheet"]["summary"]["referencedVariableCount"], 3)
        self.assertEqual(payload["sheet"]["summary"]["unknownReferenceCount"], 2)
        self.assertGreaterEqual(payload["sheet"]["summary"]["unusedVariableCount"], 2)
        self.assertGreater(payload["sheet"]["summary"]["blockerCount"], 0)
        self.assertGreater(payload["sheet"]["summary"]["warningCount"], 0)
        self.assertGreater(payload["sheet"]["summary"]["tipCount"], 0)
        self.assertEqual(payload["digest"]["status"], "blocked")
        issue_codes = [issue["code"] for issue in payload["sheet"]["issues"]]
        self.assertIn("variable_set_type_mismatch", issue_codes)
        self.assertIn("variable_add_type_mismatch", issue_codes)
        self.assertIn("variable_reference_unknown", issue_codes)
        self.assertIn("variable_range_reversed", issue_codes)
        self.assertIn("variable_default_out_of_range", issue_codes)
        self.assertIn("variable_unused", issue_codes)
        self.assertIn("variable_written_never_read", issue_codes)
        self.assertIn("variable_read_default_only", issue_codes)
        self.assertIn("# Demo Project 变量影响表", payload["markdown"])
        self.assertIn("坏范围", payload["markdown"])
        self.assertIn('"分数"', payload["csv"])
        self.assertEqual(payload["booleanLabel"], "开关")
        self.assertEqual(payload["conditionLabel"], "条件读取")
        self.assertEqual(payload["choiceGateLabel"], "选项门控")
        flag_record = next(record for record in payload["sheet"]["variables"] if record["variableId"] == "flag")
        self.assertEqual(flag_record["readCount"], 2)


if __name__ == "__main__":
    unittest.main()
