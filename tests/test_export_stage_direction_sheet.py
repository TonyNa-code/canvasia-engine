import unittest

from export_stage_direction_sheet import (
    EXPORT_STAGE_DIRECTION_CSV_NAME,
    EXPORT_STAGE_DIRECTION_JSON_NAME,
    EXPORT_STAGE_DIRECTION_REPORT_NAME,
    build_stage_direction_csv,
    build_stage_direction_report,
    build_stage_direction_sheet,
)


class ExportStageDirectionSheetTests(unittest.TestCase):
    def build_bundle(self) -> dict:
        return {
            "project": {"title": "舞台烟测", "chapterOrder": ["chapter_intro"]},
            "characters": {
                "characters": [
                    {
                        "id": "hero",
                        "displayName": "蓝白女主",
                        "defaultPosition": "center",
                        "defaultSpriteId": "sprite_hero",
                        "presentation": {"mode": "sprite", "fallbackSpriteAssetId": "sprite_hero"},
                        "expressions": [
                            {"id": "smile", "name": "微笑", "spriteAssetId": "sprite_hero"},
                            {"id": "sad", "name": "难过", "spriteAssetId": "sprite_missing"},
                        ],
                    },
                    {"id": "friend", "displayName": "同桌", "defaultPosition": "left", "defaultSpriteId": ""},
                ]
            },
            "chapters": [
                {
                    "chapterId": "chapter_intro",
                    "name": "序章",
                    "sceneOrder": ["scene_classroom", "scene_roof"],
                    "scenes": [
                        {
                            "id": "scene_classroom",
                            "name": "教室黄昏",
                            "blocks": [
                                {"id": "line_before_bg", "type": "dialogue", "speakerId": "hero", "expressionId": "smile", "text": "今天也留下来吗？"},
                                {"id": "bg", "type": "background", "assetId": "bg_classroom"},
                                {
                                    "id": "show",
                                    "type": "character_show",
                                    "characterId": "hero",
                                    "expressionId": "sad",
                                    "position": "right",
                                    "stage": {"scale": 210, "opacity": 0, "layer": 0},
                                },
                                {"id": "hide", "type": "character_hide", "characterId": "friend"},
                            ],
                        },
                        {
                            "id": "scene_roof",
                            "name": "屋顶晚风",
                            "blocks": [{"id": "roof_line", "type": "narration", "text": "没有背景的过渡场景。"}],
                        },
                    ],
                }
            ],
        }

    def test_stage_direction_sheet_flags_visual_stage_and_scene_gaps(self) -> None:
        assets_doc = {
            "assets": [
                {"id": "bg_classroom", "type": "background", "name": "黄昏教室", "path": "bg/classroom.png", "fileExists": True},
                {"id": "sprite_hero", "type": "sprite", "name": "女主微笑", "path": "char/hero.png", "fileExists": True},
                {"id": "sprite_missing", "type": "sprite", "name": "破损立绘", "path": "char/missing.png", "fileExists": False},
            ]
        }

        sheet = build_stage_direction_sheet(self.build_bundle(), assets_doc)

        self.assertEqual(sheet["formatVersion"], 1)
        self.assertEqual(sheet["projectTitle"], "舞台烟测")
        self.assertEqual(sheet["summary"]["sceneCount"], 2)
        self.assertEqual(sheet["summary"]["eventCount"], 4)
        self.assertEqual(sheet["summary"]["characterShowCount"], 1)
        self.assertEqual(sheet["summary"]["speakerAutoPlaceCount"], 1)
        self.assertEqual(sheet["summary"]["missingVisualCount"], 1)
        self.assertEqual(sheet["summary"]["missingBackgroundSceneCount"], 1)
        self.assertEqual(sheet["statusDigest"]["status"], "blocked")

        issue_codes = {issue["code"] for issue in sheet["issues"]}
        self.assertIn("dialogue_speaker_not_visible", issue_codes)
        self.assertIn("character_visual_file_missing", issue_codes)
        self.assertIn("character_opacity_invisible", issue_codes)
        self.assertIn("character_scale_extreme", issue_codes)
        self.assertIn("character_hide_not_visible", issue_codes)
        self.assertIn("scene_without_background", issue_codes)
        self.assertIn("scene_content_before_background", issue_codes)

        show_event = next(event for event in sheet["events"] if event["type"] == "character_show")
        self.assertEqual(show_event["characterName"], "蓝白女主")
        self.assertEqual(show_event["stage"]["scale"], 210)
        self.assertEqual(show_event["stage"]["opacity"], 0)

        report = build_stage_direction_report(sheet)
        self.assertIn("# 舞台烟测 角色舞台调度表", report)
        self.assertIn("舞台 Cue 列表", report)
        self.assertIn("蓝白女主", report)

        csv_text = build_stage_direction_csv(sheet)
        self.assertTrue(csv_text.startswith("\ufeffstatus,type,chapter"))
        self.assertIn("character_show", csv_text)
        self.assertIn("立绘文件缺失", csv_text)

    def test_stage_direction_file_names_are_package_safe(self) -> None:
        self.assertEqual(EXPORT_STAGE_DIRECTION_JSON_NAME, "stage-direction-sheet.json")
        self.assertEqual(EXPORT_STAGE_DIRECTION_REPORT_NAME, "stage-direction-report.md")
        self.assertEqual(EXPORT_STAGE_DIRECTION_CSV_NAME, "stage-direction-table.csv")


if __name__ == "__main__":
    unittest.main()
