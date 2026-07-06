from __future__ import annotations

import unittest

from export_variable_influence_sheet import (
    EXPORT_VARIABLE_INFLUENCE_CSV_NAME,
    EXPORT_VARIABLE_INFLUENCE_JSON_NAME,
    EXPORT_VARIABLE_INFLUENCE_REPORT_NAME,
    build_variable_influence_csv,
    build_variable_influence_report,
    build_variable_influence_sheet,
)


class ExportVariableInfluenceSheetTests(unittest.TestCase):
    def build_bundle(self) -> dict:
        return {
            "project": {"title": "变量烟测"},
            "variables": {
                "variables": [
                    {"id": "score", "name": "分数", "type": "number", "defaultValue": 5, "min": 0, "max": 10},
                    {"id": "route", "name": "路线", "type": "string", "defaultValue": "common"},
                    {"id": "flag", "name": "开关", "type": "boolean", "defaultValue": False},
                    {"id": "unused", "name": "废弃变量", "type": "boolean", "defaultValue": False},
                    {"id": "bad_range", "name": "坏范围", "type": "number", "defaultValue": 99, "min": 10, "max": 1},
                ]
            },
            "chapters": [
                {
                    "chapterId": "chapter_1",
                    "name": "第1章",
                    "sceneOrder": ["scene_start", "scene_roof"],
                    "scenes": [
                        {
                            "id": "scene_start",
                            "name": "教室黄昏",
                            "blocks": [
                                {"id": "set_score_bad", "type": "variable_set", "variableId": "score", "value": "bad"},
                                {"id": "add_route_bad", "type": "variable_add", "variableId": "route", "value": 1},
                                {
                                    "id": "choice_main",
                                    "type": "choice",
                                    "options": [
                                        {
                                            "id": "go_roof",
                                            "text": "去天台",
                                            "effects": [{"type": "variable_add", "variableId": "score", "value": 1}],
                                        },
                                        {
                                            "id": "bad_missing",
                                            "text": "调试坏变量",
                                            "effects": [{"type": "variable_set", "variableId": "missing_var", "value": True}],
                                        },
                                    ],
                                },
                                {
                                    "id": "route_gate",
                                    "type": "condition",
                                    "branches": [
                                        {
                                            "when": [
                                                {"variableId": "flag", "operator": "==", "value": True},
                                                {"variableId": "ghost", "operator": "==", "value": 1},
                                            ],
                                            "targetSceneId": "scene_roof",
                                        }
                                    ],
                                },
                            ],
                        },
                        {"id": "scene_roof", "name": "屋顶", "blocks": []},
                    ],
                }
            ],
        }

    def test_variable_influence_sheet_flags_variable_logic_gaps(self) -> None:
        sheet = build_variable_influence_sheet(self.build_bundle())

        self.assertEqual(sheet["formatVersion"], 1)
        self.assertEqual(sheet["projectTitle"], "变量烟测")
        self.assertEqual(sheet["summary"]["variableCount"], 5)
        self.assertEqual(sheet["summary"]["referencedVariableCount"], 3)
        self.assertEqual(sheet["summary"]["unknownReferenceCount"], 2)
        self.assertGreaterEqual(sheet["summary"]["unusedVariableCount"], 2)
        self.assertEqual(sheet["statusDigest"]["status"], "blocked")

        issue_codes = {issue["code"] for issue in sheet["issues"]}
        self.assertIn("variable_set_type_mismatch", issue_codes)
        self.assertIn("variable_add_type_mismatch", issue_codes)
        self.assertIn("variable_reference_unknown", issue_codes)
        self.assertIn("variable_range_reversed", issue_codes)
        self.assertIn("variable_default_out_of_range", issue_codes)
        self.assertIn("variable_unused", issue_codes)
        self.assertIn("variable_written_never_read", issue_codes)
        self.assertIn("variable_read_default_only", issue_codes)

        score = next(record for record in sheet["variables"] if record["variableId"] == "score")
        self.assertEqual(score["writeCount"], 2)
        self.assertEqual(score["choiceEffectCount"], 1)

        report = build_variable_influence_report(sheet)
        self.assertIn("# 变量烟测 变量影响表", report)
        self.assertIn("坏范围", report)
        self.assertIn("变量影响清单", report)

        csv_text = build_variable_influence_csv(sheet)
        self.assertTrue(csv_text.startswith("\ufeff序号,变量,ID"))
        self.assertIn("分数", csv_text)
        self.assertIn("坏范围", csv_text)

    def test_variable_influence_file_names_are_package_safe(self) -> None:
        self.assertEqual(EXPORT_VARIABLE_INFLUENCE_JSON_NAME, "variable-influence-sheet.json")
        self.assertEqual(EXPORT_VARIABLE_INFLUENCE_REPORT_NAME, "variable-influence-report.md")
        self.assertEqual(EXPORT_VARIABLE_INFLUENCE_CSV_NAME, "variable-influence-table.csv")


if __name__ == "__main__":
    unittest.main()
