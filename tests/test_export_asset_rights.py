import unittest

from export_asset_rights import (
    EXPORT_ASSET_RIGHTS_CSV_NAME,
    EXPORT_ASSET_RIGHTS_JSON_NAME,
    EXPORT_ASSET_RIGHTS_REPORT_NAME,
    build_export_asset_rights_csv,
    build_export_asset_rights_manifest,
    build_export_asset_rights_report,
)


class ExportAssetRightsTests(unittest.TestCase):
    def build_bundle(self) -> dict:
        return {
            "project": {"title": "授权烟测"},
            "characters": {
                "characters": [
                    {
                        "id": "heroine",
                        "displayName": "女主角",
                        "defaultSpriteId": "sprite_heroine",
                        "expressions": [
                            {
                                "id": "smile",
                                "name": "微笑",
                                "spriteAssetId": "sprite_heroine_smile",
                            }
                        ],
                    }
                ]
            },
            "chapters": [
                {
                    "scenes": [
                        {
                            "name": "开场",
                            "blocks": [
                                {"type": "background", "assetId": "bg_classroom"},
                                {"type": "music_play", "assetId": "bgm_theme"},
                                {
                                    "type": "dialogue",
                                    "speakerId": "heroine",
                                    "expressionId": "smile",
                                    "voiceAssetId": "voice_line_001",
                                },
                            ],
                        }
                    ]
                }
            ],
        }

    def test_asset_rights_manifest_flags_used_release_blockers_and_credits(self) -> None:
        assets_doc = {
            "assets": [
                {
                    "id": "bg_classroom",
                    "name": "教室背景",
                    "type": "background",
                    "path": "assets/background/classroom.png",
                    "license": "CC-BY-NC 4.0",
                    "commercialUse": "不可商用",
                    "sourceUrl": "https://example.com/bg",
                    "author": "Studio A",
                    "credit": "Background by Studio A",
                    "exportUrl": "assets/background/bg_classroom.png",
                },
                {
                    "id": "sprite_heroine_smile",
                    "name": "女主微笑",
                    "type": "sprite",
                    "license": "自制",
                    "commercialUse": "可商用",
                    "author": "Tony Na",
                    "generatedByAi": True,
                    "aiProvider": "OpenAI",
                },
                {
                    "id": "unused_tmp",
                    "name": "unused placeholder",
                    "type": "cg",
                    "tags": ["占位素材"],
                },
            ]
        }

        manifest = build_export_asset_rights_manifest(self.build_bundle(), assets_doc)

        self.assertEqual(manifest["formatVersion"], 1)
        self.assertEqual(manifest["projectTitle"], "授权烟测")
        self.assertEqual(manifest["summary"]["assetCount"], 3)
        self.assertEqual(manifest["summary"]["usedAssetCount"], 2)
        self.assertEqual(manifest["summary"]["blockerCount"], 1)
        self.assertGreaterEqual(manifest["summary"]["warningCount"], 1)
        self.assertLess(manifest["summary"]["readinessPercent"], 100)

        issue_codes = {issue["code"] for issue in manifest["issues"]}
        self.assertIn("asset_rights_noncommercial", issue_codes)
        self.assertIn("asset_rights_ai_provenance_missing", issue_codes)
        self.assertIn("asset_rights_unused_license_missing", issue_codes)

        credit_lines = [entry["creditLine"] for entry in manifest["creditRoll"]]
        self.assertIn("Background by Studio A", credit_lines)

        report = build_export_asset_rights_report(manifest)
        self.assertIn("# 素材授权与署名随包报告", report)
        self.assertIn("教室背景", report)
        self.assertIn("Staff / Credits 草稿", report)

        csv_text = build_export_asset_rights_csv(manifest)
        self.assertIn("assetId,assetName,type", csv_text)
        self.assertIn("bg_classroom", csv_text)

    def test_export_asset_rights_file_names_are_public_package_safe(self) -> None:
        self.assertEqual(EXPORT_ASSET_RIGHTS_JSON_NAME, "asset-rights-manifest.json")
        self.assertEqual(EXPORT_ASSET_RIGHTS_REPORT_NAME, "asset-rights-report.md")
        self.assertEqual(EXPORT_ASSET_RIGHTS_CSV_NAME, "asset-rights-table.csv")


if __name__ == "__main__":
    unittest.main()
