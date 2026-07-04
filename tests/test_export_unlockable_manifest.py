from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from export_unlockable_manifest import (
    UNLOCKABLE_CONTENT_MANIFEST_FILE_NAME,
    UNLOCKABLE_CONTENT_REPORT_FILE_NAME,
    build_export_unlockable_content_manifest,
    build_unlockable_content_report_markdown,
    write_unlockable_content_manifest_file,
    write_unlockable_content_report_file,
)


class ExportUnlockableManifestTests(unittest.TestCase):
    def build_sample_bundle(self) -> tuple[dict, dict]:
        bundle = {
            "project": {"title": "Route Coverage Demo", "entrySceneId": "scene_start"},
            "characters": {
                "characters": [
                    {
                        "id": "heroine",
                        "displayName": "Heroine",
                        "defaultSpriteId": "sprite_heroine",
                    }
                ]
            },
            "chapters": [
                {
                    "id": "chapter_01",
                    "name": "Chapter One",
                    "scenes": [
                        {
                            "id": "scene_start",
                            "name": "Start",
                            "blocks": [
                                {"id": "bg", "type": "background", "assetId": "bg_classroom"},
                                {
                                    "id": "line",
                                    "type": "dialogue",
                                    "speakerId": "heroine",
                                    "voiceAssetId": "voice_missing",
                                    "text": "Let us test the route.",
                                },
                                {
                                    "id": "choice",
                                    "type": "choice",
                                    "options": [{"id": "go", "text": "Go ending", "gotoSceneId": "scene_good"}],
                                },
                            ],
                        },
                        {
                            "id": "scene_good",
                            "name": "Good Ending",
                            "blocks": [{"id": "credits", "type": "credits_roll"}],
                        },
                        {
                            "id": "scene_secret",
                            "name": "Secret Ending",
                            "blocks": [{"id": "credits", "type": "credits_roll"}],
                        },
                    ],
                }
            ],
        }
        assets_doc = {
            "assets": [
                {"id": "sprite_heroine", "type": "sprite", "name": "Heroine Sprite", "exportUrl": "assets/sprite.png"},
                {"id": "bg_classroom", "type": "background", "name": "Classroom", "exportUrl": "assets/bg.png"},
                {"id": "cg_missing", "type": "cg", "name": "Missing CG", "isMissing": True},
                {"id": "bgm_theme", "type": "bgm", "name": "Theme", "exportUrl": "assets/theme.ogg"},
            ]
        }
        return bundle, assets_doc

    def test_manifest_detects_gallery_gaps_and_goto_scene_endings(self) -> None:
        bundle, assets_doc = self.build_sample_bundle()
        manifest = build_export_unlockable_content_manifest(bundle, assets_doc)
        groups = {group["id"]: group for group in manifest["groups"]}

        self.assertEqual(groups["extra_cg"]["missingCount"], 1)
        self.assertEqual(groups["music_room"]["readyCount"], 1)
        self.assertEqual(groups["voice_replay"]["missingCount"], 1)
        self.assertEqual(groups["character_archive"]["readyCount"], 1)

        endings = {entry["id"]: entry for entry in groups["ending_collection"]["entries"]}
        self.assertEqual(endings["scene_good"]["status"], "ready")
        self.assertEqual(endings["scene_secret"]["status"], "warn")
        self.assertEqual(manifest["summary"]["reachableEndingCount"], 1)
        self.assertTrue(
            any(issue["code"] == "unlockable_ending_unreachable" for issue in manifest["issues"])
        )
        self.assertTrue(
            any(entry["id"] == "first_choice" and entry["status"] == "ready" for entry in groups["achievements"]["entries"])
        )

    def test_report_markdown_and_file_writers_are_release_friendly(self) -> None:
        bundle, assets_doc = self.build_sample_bundle()
        manifest = build_export_unlockable_content_manifest(bundle, assets_doc)
        markdown = build_unlockable_content_report_markdown(manifest)

        self.assertIn("# 可解锁内容随包报告", markdown)
        self.assertIn("Secret Ending", markdown)
        self.assertIn("优先复查", markdown)
        self.assertIn(UNLOCKABLE_CONTENT_MANIFEST_FILE_NAME, markdown)

        with tempfile.TemporaryDirectory() as tmp_dir:
            target_dir = Path(tmp_dir)
            manifest_path = write_unlockable_content_manifest_file(target_dir, manifest)
            report_path = write_unlockable_content_report_file(target_dir, manifest)

            self.assertEqual(manifest_path.name, UNLOCKABLE_CONTENT_MANIFEST_FILE_NAME)
            self.assertEqual(report_path.name, UNLOCKABLE_CONTENT_REPORT_FILE_NAME)
            self.assertEqual(json.loads(manifest_path.read_text(encoding="utf-8"))["formatVersion"], 1)
            self.assertIn("## 分组总览", report_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
