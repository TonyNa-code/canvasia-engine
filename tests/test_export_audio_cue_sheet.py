import unittest

from export_audio_cue_sheet import (
    EXPORT_AUDIO_CUE_SHEET_CSV_NAME,
    EXPORT_AUDIO_CUE_SHEET_JSON_NAME,
    EXPORT_AUDIO_CUE_SHEET_REPORT_NAME,
    build_audio_cue_sheet,
    build_audio_cue_sheet_csv,
    build_audio_cue_sheet_report,
)


class ExportAudioCueSheetTests(unittest.TestCase):
    def build_bundle(self) -> dict:
        return {
            "project": {"title": "音频烟测", "chapterOrder": ["chapter_intro"]},
            "characters": {"characters": [{"id": "heroine", "displayName": "悠奈"}]},
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
                                {"id": "bg", "type": "background", "assetId": "bg_classroom"},
                                {
                                    "id": "music",
                                    "type": "music_play",
                                    "assetId": "bgm_opening",
                                    "endMode": "after_block",
                                    "endBlockId": "missing_end",
                                    "fadeInMs": 0,
                                    "fadeOutMs": 0,
                                    "volume": 65,
                                },
                                {
                                    "id": "line_1",
                                    "type": "dialogue",
                                    "speakerId": "heroine",
                                    "text": "今天也留下来吗？",
                                    "voiceAssetId": "voice_ready",
                                },
                                {"id": "sfx", "type": "sfx_play", "assetId": "sfx_missing", "volume": 0},
                                {"id": "line_2", "type": "narration", "text": "夕阳慢慢沉下去。"},
                            ],
                        },
                        {
                            "id": "scene_roof",
                            "name": "屋顶晚风",
                            "blocks": [{"id": "line_roof", "type": "narration", "text": "没有音乐的过渡场景。"}],
                        },
                    ],
                }
            ],
        }

    def test_audio_cue_sheet_flags_bgm_scope_fades_and_missing_assets(self) -> None:
        assets_doc = {
            "assets": [
                {"id": "bgm_opening", "type": "bgm", "name": "放课后钢琴", "path": "bgm/opening.ogg", "fileExists": True},
                {"id": "sfx_missing", "type": "sfx", "name": "缺文件音效", "path": "sfx/missing.ogg", "fileExists": False},
                {"id": "voice_ready", "type": "voice", "name": "悠奈_001", "path": "voice/yuina_001.ogg", "fileExists": True},
            ]
        }

        sheet = build_audio_cue_sheet(self.build_bundle(), assets_doc)

        self.assertEqual(sheet["formatVersion"], 1)
        self.assertEqual(sheet["projectTitle"], "音频烟测")
        self.assertEqual(sheet["summary"]["cueCount"], 1)
        self.assertEqual(sheet["summary"]["sfxCueCount"], 1)
        self.assertEqual(sheet["summary"]["voiceCueCount"], 1)
        self.assertEqual(sheet["summary"]["rangeSuggestionCount"], 1)
        self.assertEqual(sheet["summary"]["scenesWithoutMusicCount"], 1)
        self.assertEqual(sheet["statusDigest"]["status"], "blocked")

        issue_codes = {issue["code"] for issue in sheet["issues"]}
        self.assertIn("audio_bgm_end_block_missing", issue_codes)
        self.assertIn("audio_bgm_fade_in_missing", issue_codes)
        self.assertIn("audio_bgm_fade_out_missing", issue_codes)
        self.assertIn("audio_missing_sfx_file", issue_codes)
        self.assertIn("audio_sfx_volume_zero", issue_codes)

        cue = sheet["musicCues"][0]
        self.assertEqual(cue["assetName"], "放课后钢琴")
        self.assertEqual(cue["resolvedEndBlockId"], "line_2")
        self.assertIn("约", cue["durationLabel"])
        self.assertEqual(sheet["rangeSuggestions"][0]["recommendedEndBlockId"], "line_2")

        report = build_audio_cue_sheet_report(sheet)
        self.assertIn("# 音频烟测 音频调度表", report)
        self.assertIn("BGM Cue 列表", report)
        self.assertIn("BGM 文本范围建议", report)
        self.assertIn("缺文件音效", report)

        csv_text = build_audio_cue_sheet_csv(sheet)
        self.assertTrue(csv_text.startswith("\ufeffcueType,status,chapter"))
        self.assertIn("BGM", csv_text)
        self.assertIn("SFX", csv_text)
        self.assertIn("Voice", csv_text)

    def test_audio_cue_sheet_file_names_are_package_safe(self) -> None:
        self.assertEqual(EXPORT_AUDIO_CUE_SHEET_JSON_NAME, "audio-cue-sheet.json")
        self.assertEqual(EXPORT_AUDIO_CUE_SHEET_REPORT_NAME, "audio-cue-report.md")
        self.assertEqual(EXPORT_AUDIO_CUE_SHEET_CSV_NAME, "audio-cue-table.csv")


if __name__ == "__main__":
    unittest.main()
