import unittest

from export_voice_production import (
    EXPORT_VOICE_PRODUCTION_CSV_NAME,
    EXPORT_VOICE_PRODUCTION_JSON_NAME,
    EXPORT_VOICE_PRODUCTION_REPORT_NAME,
    build_voice_production_csv,
    build_voice_production_report,
    build_voice_production_sheet,
)


class ExportVoiceProductionTests(unittest.TestCase):
    def build_bundle(self) -> dict:
        return {
            "project": {"title": "配音烟测", "chapterOrder": ["chapter_intro"]},
            "characters": {
                "characters": [
                    {"id": "heroine", "displayName": "悠奈"},
                    {"id": "friend", "displayName": "青梅"},
                ]
            },
            "chapters": [
                {
                    "chapterId": "chapter_intro",
                    "name": "序章",
                    "sceneOrder": ["scene_rain"],
                    "scenes": [
                        {
                            "id": "scene_rain",
                            "name": "雨夜走廊",
                            "blocks": [
                                {
                                    "id": "line_ready",
                                    "type": "dialogue",
                                    "speakerId": "heroine",
                                    "text": "今晚的雨声好像比平时更近。",
                                    "voiceAssetId": "voice_ready",
                                },
                                {
                                    "id": "line_missing",
                                    "type": "dialogue",
                                    "speakerId": "friend",
                                    "text": "我们要不要先回教室？",
                                },
                                {
                                    "id": "line_wrong_type",
                                    "type": "dialogue",
                                    "speakerId": "ghost",
                                    "text": "这是一句非常长的台词。" * 16,
                                    "voiceAssetId": "bg_wrong_type",
                                },
                            ],
                        }
                    ],
                }
            ],
        }

    def test_voice_production_sheet_flags_delivery_blockers_and_exports(self) -> None:
        assets_doc = {
            "assets": [
                {
                    "id": "voice_ready",
                    "name": "悠奈_序章_001",
                    "type": "voice",
                    "path": "assets/voice/yuina_001.wav",
                    "fileExists": True,
                },
                {
                    "id": "bg_wrong_type",
                    "name": "错误绑定背景",
                    "type": "background",
                    "path": "assets/background/wrong.png",
                    "fileExists": True,
                },
            ]
        }

        sheet = build_voice_production_sheet(self.build_bundle(), assets_doc)

        self.assertEqual(sheet["formatVersion"], 1)
        self.assertEqual(sheet["projectTitle"], "配音烟测")
        self.assertEqual(sheet["summary"]["lineCount"], 3)
        self.assertEqual(sheet["summary"]["readyLineCount"], 1)
        self.assertEqual(sheet["summary"]["missingVoiceCount"], 1)
        self.assertEqual(sheet["summary"]["wrongTypeCount"], 1)
        self.assertEqual(sheet["summary"]["unknownSpeakerCount"], 1)
        self.assertGreater(sheet["summary"]["longLineCount"], 0)
        self.assertEqual(sheet["statusDigest"]["status"], "blocked")

        issue_codes = {issue["code"] for issue in sheet["issues"]}
        self.assertIn("voice_missing_binding", issue_codes)
        self.assertIn("voice_wrong_asset_type", issue_codes)
        self.assertIn("voice_unknown_speaker", issue_codes)
        self.assertIn("voice_line_very_long", issue_codes)

        suggested_names = [line["suggestedRecordingFileName"] for line in sheet["lines"]]
        self.assertIn("悠奈_序章_雨夜走廊_001.wav", suggested_names)

        report = build_voice_production_report(sheet)
        self.assertIn("# 配音烟测 语音制作清单", report)
        self.assertIn("## 台词录音表", report)
        self.assertIn("建议录音文件名", report)

        csv_text = build_voice_production_csv(sheet)
        self.assertTrue(csv_text.startswith("\ufefflineNumber,status,chapter"))
        self.assertIn("悠奈_序章_雨夜走廊_001.wav", csv_text)

    def test_voice_production_file_names_are_package_safe(self) -> None:
        self.assertEqual(EXPORT_VOICE_PRODUCTION_JSON_NAME, "voice-production-sheet.json")
        self.assertEqual(EXPORT_VOICE_PRODUCTION_REPORT_NAME, "voice-production-report.md")
        self.assertEqual(EXPORT_VOICE_PRODUCTION_CSV_NAME, "voice-production-lines.csv")


if __name__ == "__main__":
    unittest.main()
