import unittest

from export_choice_consequence_sheet import (
    EXPORT_CHOICE_CONSEQUENCE_CSV_NAME,
    EXPORT_CHOICE_CONSEQUENCE_JSON_NAME,
    EXPORT_CHOICE_CONSEQUENCE_REPORT_NAME,
    build_choice_consequence_csv,
    build_choice_consequence_report,
    build_choice_consequence_sheet,
)


class ExportChoiceConsequenceSheetTests(unittest.TestCase):
    def build_bundle(self) -> dict:
        return {
            "project": {"title": "选项烟测", "chapterOrder": ["chapter_intro"]},
            "variables": {
                "variables": [
                    {"id": "affection", "name": "好感度", "type": "number", "defaultValue": 0},
                    {"id": "flag_walk", "name": "是否同行", "type": "boolean", "defaultValue": False},
                ]
            },
            "chapters": [
                {
                    "chapterId": "chapter_intro",
                    "name": "序章",
                    "sceneOrder": ["scene_start", "scene_good"],
                    "scenes": [
                        {
                            "id": "scene_start",
                            "name": "教室选择",
                            "blocks": [
                                {
                                    "id": "choice_main",
                                    "type": "choice",
                                    "options": [
                                        {
                                            "id": "choice_good",
                                            "text": "一起回家吧",
                                            "gotoSceneId": "scene_good",
                                            "effects": [
                                                {"type": "variable_add", "variableId": "affection", "value": 1},
                                                {"type": "variable_set", "variableId": "flag_walk", "value": True},
                                            ],
                                        },
                                        {"id": "choice_empty_text", "text": "", "gotoSceneId": "missing_scene"},
                                        {"id": "choice_no_consequence", "text": "随便看看"},
                                        {
                                            "id": "choice_bad_variable",
                                            "text": "错误变量",
                                            "effects": [
                                                {"type": "variable_add", "variableId": "flag_walk", "value": 1},
                                                {"type": "variable_set", "variableId": "missing_variable", "value": "x"},
                                            ],
                                        },
                                    ],
                                }
                            ],
                        },
                        {
                            "id": "scene_good",
                            "name": "好路线",
                            "blocks": [{"id": "line", "type": "narration", "text": "你们一起走出校门。"}],
                        },
                    ],
                }
            ],
        }

    def test_choice_consequence_sheet_flags_route_and_variable_gaps(self) -> None:
        sheet = build_choice_consequence_sheet(self.build_bundle())

        self.assertEqual(sheet["formatVersion"], 1)
        self.assertEqual(sheet["projectTitle"], "选项烟测")
        self.assertEqual(sheet["summary"]["choiceBlockCount"], 1)
        self.assertEqual(sheet["summary"]["optionCount"], 4)
        self.assertEqual(sheet["summary"]["actionableOptionCount"], 3)
        self.assertEqual(sheet["summary"]["variableEffectCount"], 4)
        self.assertEqual(sheet["statusDigest"]["status"], "blocked")

        issue_codes = {issue["code"] for issue in sheet["issues"]}
        self.assertIn("choice_option_empty_text", issue_codes)
        self.assertIn("choice_option_unknown_target", issue_codes)
        self.assertIn("choice_option_no_consequence", issue_codes)
        self.assertIn("choice_effect_add_non_number", issue_codes)
        self.assertIn("choice_effect_unknown_variable", issue_codes)

        good_option = next(option for option in sheet["options"] if option["optionId"] == "choice_good")
        self.assertEqual(good_option["targetSceneName"], "好路线")
        self.assertIn("好感度 + 1", good_option["effectSummary"])
        self.assertIn("是否同行 = true", good_option["effectSummary"])

        report = build_choice_consequence_report(sheet)
        self.assertIn("# 选项烟测 选项后果表", report)
        self.assertIn("选项后果", report)
        self.assertIn("坏跳转", report)
        self.assertIn("错误变量", report)

        csv_text = build_choice_consequence_csv(sheet)
        self.assertTrue(csv_text.startswith("\ufeff序号,章节,场景"))
        self.assertIn("一起回家吧", csv_text)
        self.assertIn("missing_scene", csv_text)

    def test_choice_consequence_sheet_audits_option_availability_gates(self) -> None:
        bundle = self.build_bundle()
        options = bundle["chapters"][0]["scenes"][0]["blocks"][0]["options"]
        options[:] = [
            {
                "id": "hidden_route",
                "text": "秘密路线",
                "gotoSceneId": "scene_good",
                "choiceAvailabilityMode": "hide_when_false",
                "choiceAvailabilityWhen": [
                    {"variableId": "affection", "operator": ">=", "value": 5}
                ],
            },
            {
                "id": "locked_route",
                "text": "锁定路线",
                "gotoSceneId": "scene_good",
                "choiceAvailabilityMode": "disable_when_false",
                "choiceAvailabilityWhen": [],
            },
            {
                "id": "broken_route",
                "text": "失效路线",
                "gotoSceneId": "scene_good",
                "choiceAvailabilityMode": "hide_when_false",
                "choiceAvailabilityWhen": [
                    {"variableId": "deleted_flag", "operator": "==", "value": True}
                ],
            },
        ]

        sheet = build_choice_consequence_sheet(bundle)

        self.assertEqual(sheet["summary"]["gatedOptionCount"], 3)
        self.assertEqual(sheet["summary"]["brokenVariableCount"], 1)
        issue_codes = {issue["code"] for issue in sheet["issues"]}
        self.assertIn("choice_availability_without_rules", issue_codes)
        self.assertIn("choice_availability_unknown_variable", issue_codes)
        self.assertIn("choice_availability_missing_locked_reason", issue_codes)
        self.assertIn("choice_block_without_always_option", issue_codes)

        hidden_option = next(option for option in sheet["options"] if option["optionId"] == "hidden_route")
        locked_option = next(option for option in sheet["options"] if option["optionId"] == "locked_route")
        self.assertEqual(hidden_option["availabilityLabel"], "条件隐藏（1 条）")
        self.assertEqual(locked_option["availabilityLabel"], "条件锁定（0 条）")
        self.assertNotEqual(hidden_option["outcomeKey"], locked_option["outcomeKey"])

        report = build_choice_consequence_report(sheet)
        self.assertIn("条件门控选项", report)
        self.assertIn("可用条件", report)
        csv_text = build_choice_consequence_csv(sheet)
        self.assertIn("可用条件", csv_text.splitlines()[0])
        self.assertIn("条件隐藏（1 条）", csv_text)

    def test_choice_consequence_file_names_are_package_safe(self) -> None:
        self.assertEqual(EXPORT_CHOICE_CONSEQUENCE_JSON_NAME, "choice-consequence-sheet.json")
        self.assertEqual(EXPORT_CHOICE_CONSEQUENCE_REPORT_NAME, "choice-consequence-report.md")
        self.assertEqual(EXPORT_CHOICE_CONSEQUENCE_CSV_NAME, "choice-consequence-table.csv")


if __name__ == "__main__":
    unittest.main()
