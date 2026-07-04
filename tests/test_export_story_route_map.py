from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from export_story_route_map import (
    EXPORT_STORY_ROUTE_MAP_JSON_NAME,
    EXPORT_STORY_ROUTE_MAP_REPORT_NAME,
    build_export_story_route_map,
    build_export_story_route_map_markdown,
    write_export_story_route_map_files,
)


def make_route_bundle() -> dict:
    return {
        "project": {
            "title": "Route Demo",
            "entrySceneId": "scene_start",
        },
        "chapters": [
            {
                "id": "chapter_1",
                "name": "第一章",
                "scenes": [
                    {
                        "id": "scene_start",
                        "name": "开始",
                        "blocks": [
                            {
                                "id": "choice_1",
                                "type": "choice",
                                "options": [
                                    {"text": "去天台", "gotoSceneId": "scene_rooftop"},
                                    {"text": "去不存在的地方", "gotoSceneId": "scene_missing"},
                                ],
                            }
                        ],
                    },
                    {
                        "id": "scene_rooftop",
                        "name": "天台",
                        "blocks": [{"id": "end", "type": "credits_roll"}],
                    },
                    {
                        "id": "scene_orphan",
                        "name": "隐藏房间",
                        "blocks": [{"id": "line", "type": "narration", "text": "入口没有接到这里。"}],
                    },
                ],
            }
        ],
    }


class ExportStoryRouteMapTests(unittest.TestCase):
    def test_build_route_map_detects_broken_and_unreachable_routes(self) -> None:
        route_map = build_export_story_route_map(make_route_bundle())

        self.assertEqual(route_map["summary"]["status"], "blocked")
        self.assertEqual(route_map["summary"]["sceneCount"], 3)
        self.assertEqual(route_map["summary"]["brokenRouteCount"], 1)
        self.assertEqual(route_map["summary"]["unreachableSceneCount"], 1)
        self.assertEqual(route_map["summary"]["reachableEndingCount"], 1)
        self.assertEqual(route_map["brokenRoutes"][0]["targetSceneId"], "scene_missing")
        self.assertEqual(route_map["unreachableScenes"][0]["sceneId"], "scene_orphan")

        markdown = build_export_story_route_map_markdown(route_map)
        self.assertIn("# 剧情路线图随包报告", markdown)
        self.assertIn("scene_missing", markdown)
        self.assertIn("隐藏房间", markdown)

    def test_write_export_story_route_map_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = write_export_story_route_map_files(Path(tmp_dir), make_route_bundle())

            json_path = Path(result["storyRouteMapPath"])
            markdown_path = Path(result["storyRouteMapReportPath"])
            self.assertEqual(json_path.name, EXPORT_STORY_ROUTE_MAP_JSON_NAME)
            self.assertEqual(markdown_path.name, EXPORT_STORY_ROUTE_MAP_REPORT_NAME)
            self.assertEqual(json.loads(json_path.read_text(encoding="utf-8"))["projectTitle"], "Route Demo")
            self.assertIn("剧情路线图", markdown_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
