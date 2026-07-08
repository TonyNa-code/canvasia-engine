from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from export_choice_consequence_sheet import (
    EXPORT_CHOICE_CONSEQUENCE_CSV_NAME,
    EXPORT_CHOICE_CONSEQUENCE_JSON_NAME,
    EXPORT_CHOICE_CONSEQUENCE_REPORT_NAME,
)
from export_localization_audit import (
    EXPORT_LOCALIZATION_AUDIT_JSON_NAME,
    EXPORT_LOCALIZATION_AUDIT_REPORT_NAME,
)
from export_quality_reports import normalize_report_file_names, write_export_quality_report_bundle
from export_release_fix_order import (
    EXPORT_RELEASE_FIX_ORDER_CSV_NAME,
    EXPORT_RELEASE_FIX_ORDER_JSON_NAME,
    EXPORT_RELEASE_FIX_ORDER_REPORT_NAME,
)
from export_release_readiness import (
    EXPORT_RELEASE_READINESS_JSON_NAME,
    EXPORT_RELEASE_READINESS_REPORT_NAME,
)
from export_runtime_capability import (
    EXPORT_RUNTIME_CAPABILITY_CSV_NAME,
    EXPORT_RUNTIME_CAPABILITY_JSON_NAME,
    EXPORT_RUNTIME_CAPABILITY_REPORT_NAME,
)
from export_route_playtest_workbook import (
    EXPORT_ROUTE_PLAYTEST_WORKBOOK_CSV_NAME,
    EXPORT_ROUTE_PLAYTEST_WORKBOOK_JSON_NAME,
    EXPORT_ROUTE_PLAYTEST_WORKBOOK_REPORT_NAME,
)
from export_story_route_map import (
    EXPORT_STORY_ROUTE_MAP_JSON_NAME,
    EXPORT_STORY_ROUTE_MAP_REPORT_NAME,
)
from export_variable_influence_sheet import (
    EXPORT_VARIABLE_INFLUENCE_CSV_NAME,
    EXPORT_VARIABLE_INFLUENCE_JSON_NAME,
    EXPORT_VARIABLE_INFLUENCE_REPORT_NAME,
)


def make_bundle() -> dict:
    return {
        "project": {
            "projectId": "quality-demo",
            "title": "Quality Demo",
            "language": "zh-CN",
            "supportedLanguages": ["zh-CN", "en-US"],
            "entrySceneId": "scene_start",
        },
        "assets": [],
        "characters": [],
        "chapters": [
            {
                "id": "chapter_1",
                "name": "第一章",
                "scenes": [
                    {
                        "id": "scene_start",
                        "name": "教室",
                        "blocks": [
                            {
                                "id": "line_1",
                                "type": "narration",
                                "text": "黄昏落在课桌上。",
                            }
                        ],
                    }
                ],
            }
        ],
    }


def make_manifest() -> dict:
    return {
        "buildId": "web_build_test",
        "engine": {
            "exportTarget": "web",
            "exportTargetLabel": "网页试玩包",
            "releaseVersion": "1.0.0-preview",
        },
        "project": {
            "projectId": "quality-demo",
            "title": "Quality Demo",
            "language": "zh-CN",
            "chapterCount": 1,
            "sceneCount": 1,
            "characterCount": 0,
            "entrySceneId": "scene_start",
        },
        "assets": {"copiedCount": 1, "missingCount": 0},
        "runtime": {},
    }


class ExportQualityReportsTests(unittest.TestCase):
    def test_normalize_report_file_names_keeps_order_and_deduplicates(self) -> None:
        self.assertEqual(
            normalize_report_file_names(["manifest.json", "", "story.md", "manifest.json", " report.md "]),
            ["manifest.json", "story.md", "report.md"],
        )

    def test_write_quality_report_bundle_generates_all_release_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_dir = Path(tmp_dir)
            result = write_export_quality_report_bundle(
                target_dir,
                bundle=make_bundle(),
                project={"title": "Quality Demo"},
                manifest=make_manifest(),
                missing_assets=[],
                unlockable_manifest={"summary": {"readinessPercent": 100}},
                base_report_files=["export_manifest.json", "export_manifest.json"],
                extra_report_files=["unlockable_content_report.md"],
                platform_notes=["给测试员前先跑一遍。"],
            )

            for file_name in (
                EXPORT_STORY_ROUTE_MAP_JSON_NAME,
                EXPORT_STORY_ROUTE_MAP_REPORT_NAME,
                EXPORT_ROUTE_PLAYTEST_WORKBOOK_JSON_NAME,
                EXPORT_ROUTE_PLAYTEST_WORKBOOK_REPORT_NAME,
                EXPORT_ROUTE_PLAYTEST_WORKBOOK_CSV_NAME,
                EXPORT_CHOICE_CONSEQUENCE_JSON_NAME,
                EXPORT_CHOICE_CONSEQUENCE_REPORT_NAME,
                EXPORT_CHOICE_CONSEQUENCE_CSV_NAME,
                EXPORT_VARIABLE_INFLUENCE_JSON_NAME,
                EXPORT_VARIABLE_INFLUENCE_REPORT_NAME,
                EXPORT_VARIABLE_INFLUENCE_CSV_NAME,
                EXPORT_RUNTIME_CAPABILITY_JSON_NAME,
                EXPORT_RUNTIME_CAPABILITY_REPORT_NAME,
                EXPORT_RUNTIME_CAPABILITY_CSV_NAME,
                EXPORT_LOCALIZATION_AUDIT_JSON_NAME,
                EXPORT_LOCALIZATION_AUDIT_REPORT_NAME,
                EXPORT_RELEASE_FIX_ORDER_JSON_NAME,
                EXPORT_RELEASE_FIX_ORDER_REPORT_NAME,
                EXPORT_RELEASE_FIX_ORDER_CSV_NAME,
                EXPORT_RELEASE_READINESS_JSON_NAME,
                EXPORT_RELEASE_READINESS_REPORT_NAME,
            ):
                self.assertTrue((target_dir / file_name).is_file(), file_name)

            self.assertEqual(result["storyRouteMapStatus"], "ready")
            self.assertEqual(result["localizationAuditStatus"], "needs_translation")
            self.assertEqual(result["releaseReadinessStatus"], "needs_review")
            self.assertEqual(
                result["qualityReportFiles"],
                [
                    "export_manifest.json",
                    EXPORT_STORY_ROUTE_MAP_REPORT_NAME,
                    EXPORT_ROUTE_PLAYTEST_WORKBOOK_REPORT_NAME,
                    EXPORT_ROUTE_PLAYTEST_WORKBOOK_JSON_NAME,
                    EXPORT_ROUTE_PLAYTEST_WORKBOOK_CSV_NAME,
                    EXPORT_CHOICE_CONSEQUENCE_REPORT_NAME,
                    EXPORT_CHOICE_CONSEQUENCE_JSON_NAME,
                    EXPORT_CHOICE_CONSEQUENCE_CSV_NAME,
                    EXPORT_VARIABLE_INFLUENCE_REPORT_NAME,
                    EXPORT_VARIABLE_INFLUENCE_JSON_NAME,
                    EXPORT_VARIABLE_INFLUENCE_CSV_NAME,
                    EXPORT_RUNTIME_CAPABILITY_REPORT_NAME,
                    EXPORT_RUNTIME_CAPABILITY_JSON_NAME,
                    EXPORT_RUNTIME_CAPABILITY_CSV_NAME,
                    EXPORT_LOCALIZATION_AUDIT_REPORT_NAME,
                    EXPORT_RELEASE_FIX_ORDER_REPORT_NAME,
                    EXPORT_RELEASE_FIX_ORDER_JSON_NAME,
                    EXPORT_RELEASE_FIX_ORDER_CSV_NAME,
                    "unlockable_content_report.md",
                ],
            )

            readiness_payload = json.loads((target_dir / EXPORT_RELEASE_READINESS_JSON_NAME).read_text(encoding="utf-8"))
            self.assertIn(EXPORT_ROUTE_PLAYTEST_WORKBOOK_REPORT_NAME, readiness_payload["reportFiles"])
            self.assertIn(EXPORT_CHOICE_CONSEQUENCE_REPORT_NAME, readiness_payload["reportFiles"])
            self.assertIn(EXPORT_VARIABLE_INFLUENCE_REPORT_NAME, readiness_payload["reportFiles"])
            self.assertIn(EXPORT_RUNTIME_CAPABILITY_REPORT_NAME, readiness_payload["reportFiles"])
            self.assertIn(EXPORT_LOCALIZATION_AUDIT_REPORT_NAME, readiness_payload["reportFiles"])
            self.assertIn(EXPORT_RELEASE_FIX_ORDER_REPORT_NAME, readiness_payload["reportFiles"])
            self.assertIn("localization_missing_translations", {issue["code"] for issue in readiness_payload["issues"]})
            self.assertIn("vn_essentials_need_review", {issue["code"] for issue in readiness_payload["issues"]})
            self.assertIn("Runtime 覆盖矩阵", (target_dir / EXPORT_RUNTIME_CAPABILITY_REPORT_NAME).read_text(encoding="utf-8"))
            fix_order_payload = json.loads((target_dir / EXPORT_RELEASE_FIX_ORDER_JSON_NAME).read_text(encoding="utf-8"))
            self.assertGreaterEqual(fix_order_payload["summary"]["taskCount"], 1)
            self.assertIn("发布前修复顺序", (target_dir / EXPORT_RELEASE_FIX_ORDER_REPORT_NAME).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
