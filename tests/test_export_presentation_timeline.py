import unittest

from export_presentation_timeline import (
    EXPORT_PRESENTATION_TIMELINE_CSV_NAME,
    EXPORT_PRESENTATION_TIMELINE_JSON_NAME,
    EXPORT_PRESENTATION_TIMELINE_REPORT_NAME,
    build_presentation_timeline,
    build_presentation_timeline_csv,
    build_presentation_timeline_report,
    format_duration,
)


class ExportPresentationTimelineTests(unittest.TestCase):
    def build_bundle(self) -> dict:
        return {
            "project": {"title": "时间轴烟测", "chapterOrder": ["chapter_intro"]},
            "characters": {"characters": [{"id": "hero", "displayName": "蓝白女主"}]},
            "chapters": [
                {
                    "chapterId": "chapter_intro",
                    "name": "序章",
                    "sceneOrder": ["scene_classroom", "scene_static"],
                    "scenes": [
                        {
                            "id": "scene_classroom",
                            "name": "教室黄昏",
                            "blocks": [
                                {"id": "bg", "type": "background", "assetId": "bg_classroom", "transition": "fade", "transitionDurationMs": 900},
                                {"id": "music", "type": "music_play", "assetId": "bgm_opening", "fadeInMs": 0, "fadeOutMs": 1200},
                                {"id": "show", "type": "character_show", "characterId": "hero", "transition": "none", "stage": {"scale": 190, "opacity": 100}},
                                {"id": "line_1", "type": "dialogue", "speakerId": "hero", "text": "今天也留下来吗？", "textSpeed": "slow"},
                                {"id": "line_2", "type": "dialogue", "speakerId": "hero", "text": "嗯，只待一会儿。"},
                                {"id": "sfx", "type": "sfx_play", "assetId": "sfx_missing"},
                                {"id": "stop", "type": "music_stop", "fadeOutMs": 0},
                            ],
                        },
                        {
                            "id": "scene_static",
                            "name": "长对白",
                            "blocks": [
                                {"id": "line_a", "type": "narration", "text": "第一句。"},
                                {"id": "line_b", "type": "narration", "text": "第二句。"},
                                {"id": "line_c", "type": "narration", "text": "第三句。"},
                                {"id": "line_d", "type": "narration", "text": "第四句。"},
                                {"id": "line_e", "type": "narration", "text": "第五句。"},
                                {"id": "line_f", "type": "narration", "text": "第六句。"},
                                {"id": "line_g", "type": "narration", "text": "第七句。"},
                            ],
                        },
                    ],
                }
            ],
        }

    def test_presentation_timeline_flags_pacing_and_media_gaps(self) -> None:
        assets_doc = {
            "assets": [
                {"id": "bg_classroom", "type": "background", "name": "黄昏教室", "fileExists": True},
                {"id": "bgm_opening", "type": "bgm", "name": "放课后钢琴", "fileExists": True},
                {"id": "sfx_missing", "type": "sfx", "name": "坏音效", "fileExists": False},
            ]
        }

        timeline = build_presentation_timeline(self.build_bundle(), assets_doc)

        self.assertEqual(timeline["formatVersion"], 1)
        self.assertEqual(timeline["projectTitle"], "时间轴烟测")
        self.assertEqual(timeline["summary"]["sceneCount"], 2)
        self.assertEqual(timeline["summary"]["storySceneCount"], 2)
        self.assertEqual(timeline["summary"]["eventCount"], 14)
        self.assertEqual(timeline["summary"]["longStaticTextRunCount"], 1)
        self.assertEqual(timeline["summary"]["abruptAudioCount"], 2)
        self.assertEqual(timeline["statusDigest"]["status"], "blocked")

        issue_codes = {issue["code"] for issue in timeline["issues"]}
        self.assertIn("sfx_asset_not_ready", issue_codes)
        self.assertIn("long_static_text_run", issue_codes)
        self.assertIn("scene_opening_without_background", issue_codes)
        self.assertIn("character_show_hard_cut", issue_codes)
        self.assertIn("music_hard_stop", issue_codes)

        report = build_presentation_timeline_report(timeline)
        self.assertIn("# 时间轴烟测 演出时间轴", report)
        self.assertIn("长对白", report)
        self.assertIn("需要复查的问题", report)

        csv_text = build_presentation_timeline_csv(timeline)
        self.assertTrue(csv_text.startswith("\ufeff序号,章节,场景"))
        self.assertIn("放课后钢琴", csv_text)
        self.assertIn("坏音效", csv_text)
        self.assertEqual(format_duration(65000), "1 分 5 秒")

    def test_presentation_timeline_file_names_are_package_safe(self) -> None:
        self.assertEqual(EXPORT_PRESENTATION_TIMELINE_JSON_NAME, "presentation-timeline.json")
        self.assertEqual(EXPORT_PRESENTATION_TIMELINE_REPORT_NAME, "presentation-timeline-report.md")
        self.assertEqual(EXPORT_PRESENTATION_TIMELINE_CSV_NAME, "presentation-timeline-table.csv")


if __name__ == "__main__":
    unittest.main()
