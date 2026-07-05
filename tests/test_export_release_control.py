from __future__ import annotations

import unittest

from export_release_control import (
    build_native_runtime_release_control_markdown,
    build_native_runtime_release_control_payload,
    get_native_runtime_release_control_status,
)


def make_export_payload() -> dict:
    return {
        "project": {
            "projectId": "demo",
            "title": "Release Control Demo",
            "language": "zh-CN",
            "entrySceneId": "scene_start",
            "resolution": {"width": 1920, "height": 1080},
        },
        "buildInfo": {
            "runtimeMode": "pygame_native",
            "releaseVersion": "1.0.0-test",
        },
    }


class ExportReleaseControlTests(unittest.TestCase):
    def test_release_gate_blocks_on_performance_hard_issue(self) -> None:
        status = get_native_runtime_release_control_status(
            {"status": "pass", "summary": {"errors": 0, "warnings": 0}},
            {"status": "preview_ready", "summary": {"blockers": 0, "optionalFailures": 0, "warnings": 0}},
            {"status": "ready", "topIssues": []},
            {"status": "needs_fix", "summary": {"hardCount": 1}},
            {"status": "ready", "summary": {"warnCount": 0, "softCount": 0}},
        )

        self.assertEqual(status["status"], "blocked")
        self.assertIn("性能预算", status["summary"])

    def test_payload_and_markdown_include_vn_and_performance_sections(self) -> None:
        payload = build_native_runtime_release_control_payload(
            make_export_payload(),
            {"status": "pass", "summary": {"errors": 0, "warnings": 0}, "issues": []},
            {
                "status": "preview_ready",
                "summary": {"blockers": 0, "optionalFailures": 0, "warnings": 0},
                "readinessEstimate": {"desktopPreviewPercent": 91, "commercialDesktopPercent": 72},
            },
            {"status": "ready", "summaryLine": "3D 资产正常", "metrics": [], "topIssues": []},
            {
                "status": "needs_review",
                "summary": {
                    "statusLabel": "建议复核",
                    "assetCount": 3,
                    "referencedAssetCount": 2,
                    "warnCount": 1,
                    "softCount": 0,
                },
                "assetGroups": {"image": {"label": "12 MB"}},
                "issues": [{"title": "图片偏大", "suggestion": "压缩图片。"}],
            },
            {
                "status": "ready",
                "summary": {"statusLabel": "基础体验完整", "issueCount": 0, "warnCount": 0, "softCount": 0},
                "metrics": {"storySceneCount": 2, "dialogueCount": 4, "choiceCount": 1},
                "issues": [],
            },
            generated_at="2026-01-02T03:04:05+08:00",
        )

        self.assertEqual(payload["qualityGate"]["status"], "needs_review")
        self.assertEqual(payload["project"]["title"], "Release Control Demo")
        self.assertEqual(payload["performanceBudget"]["summary"]["assetCount"], 3)
        self.assertIn("performanceBudgetMarkdown", payload["includedReports"])
        self.assertTrue(any("图片偏大" in step for step in payload["nextSteps"]))

        markdown = build_native_runtime_release_control_markdown(payload)
        self.assertIn("# 原生 Runtime 发布总控报告", markdown)
        self.assertIn("## VN 基础质感", markdown)
        self.assertIn("## 性能预算", markdown)
        self.assertIn("native-runtime-performance-budget.md", markdown)


if __name__ == "__main__":
    unittest.main()
