from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from export_release_readiness import (
    EXPORT_RELEASE_READINESS_JSON_NAME,
    EXPORT_RELEASE_READINESS_REPORT_NAME,
    build_export_release_readiness_markdown,
    build_export_release_readiness_summary,
    write_export_release_readiness_files,
)


def make_manifest(**overrides: object) -> dict:
    manifest = {
        "buildId": "build_001",
        "engine": {
            "exportTarget": "web",
            "exportTargetLabel": "网页试玩包",
            "releaseVersion": "1.0.0-preview",
        },
        "project": {
            "projectId": "demo",
            "title": "Readiness Demo",
            "language": "zh-CN",
            "chapterCount": 1,
            "sceneCount": 3,
            "characterCount": 2,
            "entrySceneId": "scene_start",
        },
        "assets": {"copiedCount": 4, "missingCount": 0},
        "runtime": {},
    }
    manifest.update(overrides)
    return manifest


class ExportReleaseReadinessTests(unittest.TestCase):
    def test_ready_summary_has_score_gate_and_markdown(self) -> None:
        summary = build_export_release_readiness_summary(
            project={"title": "Readiness Demo"},
            manifest=make_manifest(),
            unlockable_manifest={
                "summary": {
                    "readinessPercent": 100,
                    "warningCount": 0,
                    "missingEntryCount": 0,
                    "readyEntryCount": 6,
                    "totalEntryCount": 6,
                    "reachableEndingCount": 2,
                    "endingCount": 2,
                }
            },
            report_files=["export_manifest.json", "unlockable_content_report.md"],
        )

        self.assertEqual(summary["qualityGate"]["status"], "ready")
        self.assertGreaterEqual(summary["score"], 90)
        self.assertEqual(summary["metrics"]["reachableEndings"], 2)

        markdown = build_export_release_readiness_markdown(summary)
        self.assertIn("# 发布试玩就绪摘要", markdown)
        self.assertIn("Readiness Demo", markdown)
        self.assertIn("可进入试玩分发", markdown)
        self.assertIn("unlockable_content_report.md", markdown)

    def test_missing_assets_and_empty_story_block_release(self) -> None:
        manifest = make_manifest(
            project={
                "projectId": "empty",
                "title": "Empty Demo",
                "chapterCount": 0,
                "sceneCount": 0,
                "characterCount": 0,
                "entrySceneId": "",
            },
            assets={"copiedCount": 0, "missingCount": 1},
        )
        summary = build_export_release_readiness_summary(
            project={"title": "Empty Demo"},
            manifest=manifest,
            missing_assets=[{"id": "missing_bg", "name": "Missing BG", "type": "background"}],
        )

        self.assertEqual(summary["qualityGate"]["status"], "blocked")
        self.assertLess(summary["score"], 70)
        issue_codes = {issue["code"] for issue in summary["issues"]}
        self.assertIn("no_playable_story", issue_codes)
        self.assertIn("missing_export_assets", issue_codes)

    def test_story_route_map_issues_affect_release_gate(self) -> None:
        summary = build_export_release_readiness_summary(
            project={"title": "Route Gate Demo"},
            manifest=make_manifest(),
            story_route_map={
                "summary": {
                    "entrySceneExists": True,
                    "routeCount": 3,
                    "brokenRouteCount": 1,
                    "unreachableSceneCount": 2,
                }
            },
        )

        self.assertEqual(summary["qualityGate"]["status"], "blocked")
        self.assertEqual(summary["metrics"]["brokenRoutes"], 1)
        self.assertEqual(summary["metrics"]["unreachableScenes"], 2)
        issue_codes = {issue["code"] for issue in summary["issues"]}
        self.assertIn("story_route_broken_links", issue_codes)
        self.assertIn("story_route_unreachable_scenes", issue_codes)

    def test_write_export_release_readiness_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = write_export_release_readiness_files(
                Path(tmp_dir),
                project={"title": "Writable Readiness"},
                manifest=make_manifest(),
                unlockable_manifest={"summary": {"readinessPercent": 100}},
            )

            json_path = Path(result["releaseReadinessSummaryPath"])
            markdown_path = Path(result["releaseReadinessReportPath"])
            self.assertEqual(json_path.name, EXPORT_RELEASE_READINESS_JSON_NAME)
            self.assertEqual(markdown_path.name, EXPORT_RELEASE_READINESS_REPORT_NAME)
            self.assertEqual(json.loads(json_path.read_text(encoding="utf-8"))["qualityGate"]["status"], "ready")
            self.assertIn("Writable Readiness", markdown_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
