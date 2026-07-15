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
    def test_character_move_updates_stage_composition_and_reports_missing_entry(self) -> None:
        bundle = {
            "project": {"title": "Motion Sheet"},
            "characters": {"characters": [{
                "id": "hero",
                "displayName": "Hero",
                "defaultPosition": "left",
                "defaultSpriteId": "sprite_hero",
                "expressions": [{"id": "smile", "name": "Smile", "spriteAssetId": "sprite_hero"}],
            }]},
            "chapters": [{
                "chapterId": "chapter",
                "name": "Chapter",
                "scenes": [{
                    "id": "scene",
                    "name": "Scene",
                    "blocks": [
                        {"id": "show", "type": "character_show", "characterId": "hero", "expressionId": "smile", "position": "left", "transition": "fade", "transitionDurationMs": 400},
                        {"id": "move", "type": "character_move", "characterId": "hero", "expressionId": "smile", "position": "right", "durationMs": 900, "easing": "spring", "stage": {"scale": 118, "offsetX": -6}},
                    ],
                }],
            }],
        }
        assets = {"assets": [{"id": "sprite_hero", "type": "sprite", "name": "Hero", "path": "hero.png", "fileExists": True}]}
        sheet = build_stage_direction_sheet(bundle, assets)
        self.assertEqual(sheet["summary"]["characterMoveCount"], 1)
        move_event = next(event for event in sheet["events"] if event["type"] == "character_move")
        self.assertEqual(move_event["positionLabel"], "右侧")
        self.assertEqual(move_event["motionDurationMs"], 900)
        self.assertEqual(move_event["motionEasing"], "spring")
        self.assertEqual(move_event["stage"]["scale"], 118)
        self.assertNotIn("character_move_not_visible", {issue["code"] for issue in sheet["issues"]})

        bundle["chapters"][0]["scenes"][0]["blocks"] = [bundle["chapters"][0]["scenes"][0]["blocks"][1]]
        missing_entry = build_stage_direction_sheet(bundle, assets)
        self.assertIn("character_move_not_visible", {issue["code"] for issue in missing_entry["issues"]})

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
                    {
                        "id": "rival",
                        "displayName": "转学生",
                        "defaultPosition": "right",
                        "defaultSpriteId": "sprite_rival",
                        "expressions": [{"id": "smile", "name": "微笑", "spriteAssetId": "sprite_rival"}],
                    },
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
                                {
                                    "id": "show_rival",
                                    "type": "character_show",
                                    "characterId": "rival",
                                    "expressionId": "smile",
                                    "position": "right",
                                    "transition": "fade",
                                    "transitionDurationMs": 500,
                                    "stage": {"scale": 170, "opacity": 25, "layer": 0},
                                },
                                {"id": "rival_line", "type": "dialogue", "speakerId": "rival", "expressionId": "smile", "text": "那我也留下。"},
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
                {"id": "sprite_rival", "type": "sprite", "name": "转学生", "path": "char/rival.png", "fileExists": True},
                {"id": "sprite_missing", "type": "sprite", "name": "破损立绘", "path": "char/missing.png", "fileExists": False},
            ]
        }

        sheet = build_stage_direction_sheet(self.build_bundle(), assets_doc)

        self.assertEqual(sheet["formatVersion"], 1)
        self.assertEqual(sheet["projectTitle"], "舞台烟测")
        self.assertEqual(sheet["summary"]["sceneCount"], 2)
        self.assertEqual(sheet["summary"]["eventCount"], 6)
        self.assertEqual(sheet["summary"]["characterShowCount"], 2)
        self.assertEqual(sheet["summary"]["speakerAutoPlaceCount"], 1)
        self.assertEqual(sheet["summary"]["missingVisualCount"], 1)
        self.assertEqual(sheet["summary"]["missingBackgroundSceneCount"], 1)
        self.assertEqual(sheet["summary"]["compositionCheckpointCount"], 4)
        self.assertGreaterEqual(sheet["summary"]["compositionRiskCount"], 2)
        self.assertGreaterEqual(sheet["summary"]["overlapRiskCount"], 1)
        self.assertEqual(sheet["summary"]["lowOpacitySpeakerCount"], 1)
        self.assertEqual(sheet["statusDigest"]["status"], "blocked")

        issue_codes = {issue["code"] for issue in sheet["issues"]}
        self.assertIn("dialogue_speaker_not_visible", issue_codes)
        self.assertIn("character_visual_file_missing", issue_codes)
        self.assertIn("character_opacity_invisible", issue_codes)
        self.assertIn("character_scale_extreme", issue_codes)
        self.assertIn("stage_geometry_overlap", issue_codes)
        self.assertIn("stage_speaker_low_opacity", issue_codes)
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
        self.assertIn("舞台构图检查", report)
        self.assertIn("蓝白女主", report)

        csv_text = build_stage_direction_csv(sheet)
        self.assertTrue(csv_text.startswith("\ufeffstatus,type,chapter"))
        self.assertIn("compositionRisk", csv_text)
        self.assertIn("character_show", csv_text)
        self.assertIn("立绘文件缺失", csv_text)

    def test_stage_direction_file_names_are_package_safe(self) -> None:
        self.assertEqual(EXPORT_STAGE_DIRECTION_JSON_NAME, "stage-direction-sheet.json")
        self.assertEqual(EXPORT_STAGE_DIRECTION_REPORT_NAME, "stage-direction-report.md")
        self.assertEqual(EXPORT_STAGE_DIRECTION_CSV_NAME, "stage-direction-table.csv")


if __name__ == "__main__":
    unittest.main()
