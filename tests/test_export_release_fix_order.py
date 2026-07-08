from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from export_release_fix_order import (
    EXPORT_RELEASE_FIX_ORDER_CSV_NAME,
    EXPORT_RELEASE_FIX_ORDER_JSON_NAME,
    EXPORT_RELEASE_FIX_ORDER_REPORT_NAME,
    build_export_release_fix_order,
    build_export_release_fix_order_csv,
    build_export_release_fix_order_markdown,
    write_export_release_fix_order_files,
)


def make_release_summary() -> dict:
    return {
        "project": {"title": "Fix Order Demo"},
        "score": 52,
        "qualityGate": {"status": "blocked", "label": "暂不建议分发"},
        "issues": [
            {
                "severity": "blocker",
                "code": "missing_export_assets",
                "title": "导出包存在缺失素材",
                "detail": "背景 classroom 不存在。",
                "suggestion": "重新绑定背景文件后重新导出。",
            },
            {
                "severity": "warning",
                "code": "runtime_capability_review_needed",
                "title": "Runtime 覆盖需要重点验收",
                "detail": "视频播放需要目标平台确认。",
                "suggestion": "打开 runtime-capability-matrix.md 完成点测。",
            },
        ],
    }


class ExportReleaseFixOrderTests(unittest.TestCase):
    def test_fix_order_merges_reports_into_prioritized_queue(self) -> None:
        payload = build_export_release_fix_order(
            project={"title": "Fix Order Demo"},
            release_readiness_summary=make_release_summary(),
            route_playtest_workbook={
                "executionQueue": [
                    {
                        "status": "broken",
                        "title": "修复分支坏链",
                        "chapterName": "第一章",
                        "sceneName": "教室",
                        "actionLabel": "先修复目标场景",
                        "acceptanceCriteria": "选择后能进入目标场景。",
                    }
                ]
            },
            choice_consequence_sheet={
                "issues": [
                    {
                        "severity": "blocker",
                        "code": "choice_option_unknown_target",
                        "title": "选项跳向不存在的场景",
                        "detail": "选项目标 scene_missing 不存在。",
                        "chapterName": "第一章",
                        "sceneName": "教室",
                        "optionText": "追上去",
                    }
                ]
            },
            variable_influence_sheet={
                "issues": [
                    {
                        "severity": "warn",
                        "code": "variable_written_never_read",
                        "title": "变量写入后未读取",
                        "detail": "好感度变量没有影响任何路线。",
                        "variableName": "好感度",
                    }
                ]
            },
            runtime_capability_matrix={
                "issues": [
                    {
                        "severity": "blocker",
                        "code": "runtime_unknown",
                        "title": "live2d_pose：未知卡片",
                        "detail": "这个卡片类型还没有 Runtime 覆盖声明。",
                        "sceneNames": ["教室"],
                    }
                ],
                "essentials": {
                    "issues": [
                        {
                            "severity": "soft",
                            "code": "bgm_fade_in_missing",
                            "area": "audio",
                            "title": "部分 BGM 没有淡入",
                            "detail": "2 个 BGM 播放点没有设置淡入。",
                            "suggestion": "给 BGM 设置 400-1000ms 淡入。",
                        }
                    ]
                },
            },
            localization_audit={
                "project": {"targetLanguages": ["en-US", "ja-JP"]},
                "summary": {"missingTranslationCount": 6},
            },
            report_files=["release_readiness_summary.md", "runtime-capability-matrix.md"],
        )
        markdown = build_export_release_fix_order_markdown(payload)
        csv_text = build_export_release_fix_order_csv(payload)

        self.assertEqual(payload["summary"]["status"], "blocked")
        self.assertGreaterEqual(payload["summary"]["taskCount"], 7)
        self.assertEqual(payload["tasks"][0]["code"], "missing_export_assets")
        self.assertEqual(payload["tasks"][0]["sourceReport"], "export_manifest.json")
        self.assertTrue(any(task["source"] == "route_playtest" for task in payload["tasks"]))
        self.assertTrue(any(task["source"] == "localization" for task in payload["tasks"]))
        self.assertIn("# Fix Order Demo 发布前修复顺序", markdown)
        self.assertIn("逐项执行队列", markdown)
        self.assertIn("live2d_pose", markdown)
        self.assertIn("missing_export_assets", csv_text)

    def test_write_release_fix_order_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = write_export_release_fix_order_files(
                Path(tmp_dir),
                project={"title": "Fix Order Demo"},
                release_readiness_summary=make_release_summary(),
            )

            self.assertEqual(result["releaseFixOrderName"], EXPORT_RELEASE_FIX_ORDER_JSON_NAME)
            self.assertEqual(result["releaseFixOrderReportName"], EXPORT_RELEASE_FIX_ORDER_REPORT_NAME)
            self.assertEqual(result["releaseFixOrderCsvName"], EXPORT_RELEASE_FIX_ORDER_CSV_NAME)
            self.assertEqual(result["releaseFixOrderStatus"], "blocked")
            self.assertGreaterEqual(result["releaseFixOrderTaskCount"], 2)
            json_payload = json.loads(Path(result["releaseFixOrderPath"]).read_text(encoding="utf-8"))
            self.assertEqual(json_payload["projectTitle"], "Fix Order Demo")
            self.assertTrue(Path(result["releaseFixOrderReportPath"]).is_file())
            self.assertTrue(Path(result["releaseFixOrderCsvPath"]).is_file())


if __name__ == "__main__":
    unittest.main()
