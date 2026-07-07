from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from export_runtime_capability import (
    EXPORT_RUNTIME_CAPABILITY_CSV_NAME,
    EXPORT_RUNTIME_CAPABILITY_JSON_NAME,
    EXPORT_RUNTIME_CAPABILITY_REPORT_NAME,
    build_export_runtime_capability_csv,
    build_export_runtime_capability_markdown,
    build_export_runtime_capability_matrix,
    write_export_runtime_capability_files,
)


def make_runtime_bundle() -> dict:
    return {
        "project": {"title": "Runtime Export Demo"},
        "assets": [
            {"id": "bg_room", "type": "background", "name": "教室"},
            {"id": "scene_3d", "type": "scene3d", "name": "3D 教室"},
            {"id": "op", "type": "video", "name": "OP"},
        ],
        "chapters": [
            {
                "id": "chapter_1",
                "name": "第一章",
                "scenes": [
                    {
                        "id": "scene_start",
                        "name": "开场",
                        "blocks": [
                            {"id": "bg", "type": "background", "assetId": "scene_3d"},
                            {"id": "line_1", "type": "dialogue", "text": "你好。"},
                            {"id": "line_2", "type": "dialogue", "text": "今天要测试导出报告。"},
                            {"id": "line_3", "type": "dialogue", "text": "先确认基础 VN 体验。"},
                            {"id": "music_a", "type": "music_play", "assetId": "bgm_a", "fadeInMs": 0},
                            {"id": "music_b", "type": "music_play", "assetId": "bgm_b", "fadeInMs": 0},
                            {"id": "op", "type": "video_play", "assetId": "op"},
                            {"id": "future", "type": "live2d_pose"},
                        ],
                    }
                ],
            }
        ],
    }


class ExportRuntimeCapabilityTests(unittest.TestCase):
    def test_runtime_capability_matrix_flags_export_runtime_and_vn_gaps(self) -> None:
        matrix = build_export_runtime_capability_matrix(make_runtime_bundle())
        markdown = build_export_runtime_capability_markdown(matrix)
        csv_text = build_export_runtime_capability_csv(matrix)

        self.assertEqual(matrix["projectTitle"], "Runtime Export Demo")
        self.assertEqual(matrix["summary"]["totalBlockCount"], 8)
        self.assertEqual(matrix["summary"]["unknownUsedTypeCount"], 1)
        self.assertGreaterEqual(matrix["summary"]["nativePartialCount"], 2)
        self.assertGreaterEqual(matrix["acceptance"]["summary"]["itemCount"], 4)
        self.assertIn("runtime-video-sync", {item["id"] for item in matrix["acceptance"]["items"]})
        self.assertIn("character_stage_missing", {issue["code"] for issue in matrix["essentials"]["issues"]})
        self.assertIn("bgm_scope_missing", {issue["code"] for issue in matrix["essentials"]["issues"]})
        self.assertIn("# Runtime Export Demo Runtime 覆盖矩阵", markdown)
        self.assertIn("## VN 基础能力成熟度", markdown)
        self.assertIn("live2d_pose", markdown)
        self.assertIn("Runtime 验收清单", markdown)
        self.assertIn("live2d_pose", csv_text)

    def test_write_runtime_capability_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = write_export_runtime_capability_files(Path(tmp_dir), bundle=make_runtime_bundle())

            self.assertEqual(result["runtimeCapabilityMatrixName"], EXPORT_RUNTIME_CAPABILITY_JSON_NAME)
            self.assertEqual(result["runtimeCapabilityReportName"], EXPORT_RUNTIME_CAPABILITY_REPORT_NAME)
            self.assertEqual(result["runtimeCapabilityCsvName"], EXPORT_RUNTIME_CAPABILITY_CSV_NAME)
            self.assertGreaterEqual(result["runtimeCapabilityIssueCount"], 1)
            self.assertGreaterEqual(result["vnEssentialsIssueCount"], 1)

            json_payload = json.loads(Path(result["runtimeCapabilityMatrixPath"]).read_text(encoding="utf-8"))
            self.assertEqual(json_payload["projectTitle"], "Runtime Export Demo")
            self.assertTrue(Path(result["runtimeCapabilityReportPath"]).is_file())
            self.assertTrue(Path(result["runtimeCapabilityCsvPath"]).is_file())


if __name__ == "__main__":
    unittest.main()
