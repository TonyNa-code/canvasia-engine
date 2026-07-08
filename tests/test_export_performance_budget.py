from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from export_performance_budget import (
    EXPORT_PERFORMANCE_BUDGET_CSV_NAME,
    EXPORT_PERFORMANCE_BUDGET_JSON_NAME,
    EXPORT_PERFORMANCE_BUDGET_REPORT_NAME,
    build_export_performance_budget,
    build_export_performance_budget_markdown,
    write_export_performance_budget_files,
)


class ExportPerformanceBudgetTests(unittest.TestCase):
    def build_bundle(self) -> dict:
        return {
            "project": {"title": "Performance Demo", "entrySceneId": "scene_open"},
            "characters": {
                "characters": [
                    {
                        "id": "hero",
                        "expressions": [{"id": "smile", "spriteAssetId": "sprite_hero"}],
                    }
                ]
            },
            "chapters": [
                {
                    "chapterId": "chapter_1",
                    "scenes": [
                        {
                            "id": "scene_open",
                            "name": "Opening",
                            "blocks": [
                                {"id": "bg", "type": "background", "assetId": "bg_heavy"},
                                {"id": "show", "type": "character_show", "characterId": "hero", "expressionId": "smile"},
                                {"id": "voice", "type": "dialogue", "speakerId": "hero", "voiceAssetId": "voice_missing"},
                            ],
                        },
                        {
                            "id": "scene_video",
                            "name": "PV",
                            "blocks": [
                                {"id": "movie", "type": "video_play", "assetId": "op_video"},
                            ],
                        },
                    ],
                }
            ],
        }

    def build_assets_doc(self) -> dict:
        mb = 1024 * 1024
        return {
            "assets": [
                {
                    "id": "bg_heavy",
                    "type": "background",
                    "name": "Heavy Background",
                    "exportUrl": "assets/bg/heavy.png",
                    "fileSizeBytes": 120 * mb,
                },
                {
                    "id": "sprite_hero",
                    "type": "sprite",
                    "name": "Hero Sprite",
                    "exportUrl": "assets/sprite/hero.png",
                    "fileSizeBytes": 8 * mb,
                },
                {
                    "id": "voice_missing",
                    "type": "voice",
                    "name": "Missing Voice",
                    "isMissing": True,
                    "fileSizeBytes": 0,
                },
                {
                    "id": "op_video",
                    "type": "video",
                    "name": "Opening Video",
                    "exportUrl": "assets/video/op.mp4",
                    "fileSizeBytes": 420 * mb,
                },
                {
                    "id": "unused_movie",
                    "type": "video",
                    "name": "Unused Movie",
                    "exportUrl": "assets/video/unused.mp4",
                    "fileSizeBytes": 380 * mb,
                },
            ]
        }

    def test_performance_budget_flags_missing_and_oversized_assets(self) -> None:
        report = build_export_performance_budget(self.build_bundle(), self.build_assets_doc())
        summary = report["summary"]
        issue_codes = {issue["code"] for issue in report["issues"]}

        self.assertEqual(summary["status"], "blocked")
        self.assertGreater(summary["criticalPreloadBytes"], 90 * 1024 * 1024)
        self.assertIn("missing_referenced_asset", issue_codes)
        self.assertIn("single_asset_over_budget", issue_codes)
        self.assertIn("criticalPreload_over_budget", issue_codes)
        self.assertEqual(report["groupTotals"]["video"]["assetCount"], 2)
        self.assertEqual(report["largestAssets"][0]["assetId"], "op_video")

        markdown = build_export_performance_budget_markdown(report)
        self.assertIn("发布性能预算", markdown)
        self.assertIn("Heavy Background", markdown)
        self.assertIn("首屏关键预加载", markdown)

    def test_write_performance_budget_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = write_export_performance_budget_files(
                Path(tmp_dir),
                bundle=self.build_bundle(),
                assets_doc=self.build_assets_doc(),
            )
            self.assertEqual(result["exportPerformanceBudgetName"], EXPORT_PERFORMANCE_BUDGET_JSON_NAME)
            self.assertEqual(result["exportPerformanceBudgetReportName"], EXPORT_PERFORMANCE_BUDGET_REPORT_NAME)
            self.assertEqual(result["exportPerformanceBudgetCsvName"], EXPORT_PERFORMANCE_BUDGET_CSV_NAME)
            payload = json.loads((Path(tmp_dir) / EXPORT_PERFORMANCE_BUDGET_JSON_NAME).read_text(encoding="utf-8"))
            self.assertEqual(payload["summary"]["status"], "blocked")
            self.assertTrue((Path(tmp_dir) / EXPORT_PERFORMANCE_BUDGET_REPORT_NAME).is_file())
            self.assertTrue((Path(tmp_dir) / EXPORT_PERFORMANCE_BUDGET_CSV_NAME).is_file())


if __name__ == "__main__":
    unittest.main()
