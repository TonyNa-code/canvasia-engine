from __future__ import annotations

import unittest

from export_runtime_preload import (
    build_runtime_preload_manifest,
    build_runtime_preload_report,
    format_bytes,
    normalize_asset_size_bytes,
)


class ExportRuntimePreloadTests(unittest.TestCase):
    def test_runtime_preload_manifest_tracks_size_by_phase_and_type(self) -> None:
        bundle = {
            "project": {"entrySceneId": "scene_open"},
            "characters": {
                "characters": [
                    {
                        "id": "hero",
                        "expressions": [
                            {"id": "smile", "spriteAssetId": "sprite_hero"},
                        ],
                    }
                ]
            },
            "chapters": [
                {
                    "chapterId": "chapter_1",
                    "name": "Opening",
                    "scenes": [
                        {
                            "id": "scene_open",
                            "name": "Opening Room",
                            "blocks": [
                                {"id": "bg", "type": "background", "assetId": "bg_open"},
                                {"id": "show", "type": "character_show", "characterId": "hero", "expressionId": "smile"},
                                {"id": "voice", "type": "dialogue", "speakerId": "hero", "voiceAssetId": "voice_001"},
                            ],
                        },
                        {
                            "id": "scene_second",
                            "name": "Second Scene",
                            "blocks": [
                                {"id": "music", "type": "music_play", "assetId": "bgm_open"},
                                {"id": "video", "type": "video_play", "assetId": "op_video"},
                            ],
                        },
                    ],
                }
            ],
        }
        mb = 1024 * 1024
        assets_doc = {
            "assets": [
                {"id": "bg_open", "type": "background", "name": "Opening BG", "exportUrl": "assets/bg/open.png", "fileSizeBytes": 24 * mb},
                {"id": "sprite_hero", "type": "sprite", "name": "Hero Smile", "exportUrl": "assets/sprite/hero.png", "size": "1.5 MB"},
                {"id": "voice_001", "type": "voice", "name": "Voice 001", "exportUrl": "assets/voice/001.ogg", "fileSize": "512 KB"},
                {"id": "bgm_open", "type": "bgm", "name": "Opening BGM", "exportUrl": "assets/bgm/open.ogg", "sizeBytes": 7 * mb},
                {"id": "op_video", "type": "video", "name": "Opening Video", "exportUrl": "assets/video/op.mp4", "fileSizeBytes": 80 * mb},
                {"id": "unused_fav", "type": "ui", "name": "Favorite UI", "exportUrl": "assets/ui/fav.png", "favorite": True, "fileSizeBytes": 128 * 1024},
            ]
        }

        manifest = build_runtime_preload_manifest(bundle, assets_doc)
        entries_by_id = {entry["assetId"]: entry for entry in manifest["entries"]}
        summary = manifest["summary"]

        self.assertEqual(entries_by_id["bg_open"]["sizeBytes"], 24 * mb)
        self.assertEqual(entries_by_id["sprite_hero"]["sizeBytes"], int(1.5 * mb))
        self.assertEqual(entries_by_id["voice_001"]["sizeBytes"], 512 * 1024)
        self.assertEqual(entries_by_id["unused_fav"]["phase"], "library")
        self.assertEqual(summary["criticalBytes"], 24 * mb + int(1.5 * mb) + 512 * 1024)
        self.assertEqual(summary["earlyBytes"], 7 * mb + 80 * mb)
        self.assertEqual(summary["libraryBytes"], 128 * 1024)
        self.assertEqual(summary["totalBytes"], summary["criticalBytes"] + summary["earlyBytes"] + summary["libraryBytes"])
        self.assertEqual(summary["videoBytes"], 80 * mb)
        self.assertEqual(manifest["largestEntries"][0]["assetId"], "op_video")

        report = build_runtime_preload_report(manifest)
        self.assertIn("Total preload size", report)
        self.assertIn("Critical first-play size", report)
        self.assertIn("Largest Preload Entries", report)
        self.assertIn("op_video", report)

    def test_asset_size_parser_accepts_common_editor_fields(self) -> None:
        self.assertEqual(normalize_asset_size_bytes({"fileSizeBytes": 2048}), 2048)
        self.assertEqual(normalize_asset_size_bytes({"fileSize": "1,024"}), 1024)
        self.assertEqual(normalize_asset_size_bytes({"size": "2.5 MB"}), int(2.5 * 1024 * 1024))
        self.assertEqual(normalize_asset_size_bytes({"sizeBytes": -100}), 0)
        self.assertEqual(format_bytes(1536), "1.5 KB")


if __name__ == "__main__":
    unittest.main()
