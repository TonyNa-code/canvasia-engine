from __future__ import annotations

import unittest

from export_route_playtest_workbook import (
    EXPORT_ROUTE_PLAYTEST_WORKBOOK_CSV_NAME,
    EXPORT_ROUTE_PLAYTEST_WORKBOOK_JSON_NAME,
    EXPORT_ROUTE_PLAYTEST_WORKBOOK_REPORT_NAME,
    build_route_playtest_csv,
    build_route_playtest_report,
    build_route_playtest_workbook,
)


def make_route_bundle() -> dict:
    return {
        "project": {
            "title": "路线试玩烟测",
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


class ExportRoutePlaytestWorkbookTests(unittest.TestCase):
    def test_route_playtest_workbook_tracks_subscene_return_cases(self) -> None:
        bundle = {
            "project": {"title": "子场景试玩", "entrySceneId": "scene_start"},
            "chapters": [
                {
                    "id": "chapter_1",
                    "name": "第一章",
                    "scenes": [
                        {
                            "id": "scene_start",
                            "name": "开始",
                            "blocks": [
                                {"id": "call", "type": "scene_call", "targetSceneId": "scene_common"},
                                {"id": "jump", "type": "jump", "targetSceneId": "scene_end"},
                            ],
                        },
                        {"id": "scene_end", "name": "结尾", "blocks": [{"type": "credits_roll"}]},
                        {"id": "scene_common", "name": "共用演出", "blocks": [{"type": "scene_return"}]},
                    ],
                }
            ],
        }

        sheet = build_route_playtest_workbook(bundle)

        self.assertEqual(sheet["summary"]["subsceneCaseCount"], 1)
        self.assertEqual(sheet["summary"]["blockedSubsceneCaseCount"], 0)
        self.assertEqual(sheet["plan"]["decisionPoints"], [])
        self.assertEqual(sheet["plan"]["subsceneCases"][0]["targetSceneId"], "scene_common")
        self.assertTrue(any(item["kind"] == "subscene" for item in sheet["executionQueue"]))
        self.assertTrue(any(lane["id"] == "subscene" for lane in sheet["workbook"]["lanes"]))
        self.assertIn("子场景调用与返回", build_route_playtest_report(sheet))
        self.assertIn("子场景调用", build_route_playtest_csv(sheet))

    def test_route_playtest_workbook_builds_executable_queue(self) -> None:
        sheet = build_route_playtest_workbook(make_route_bundle())

        self.assertEqual(sheet["formatVersion"], 1)
        self.assertEqual(sheet["projectTitle"], "路线试玩烟测")
        self.assertEqual(sheet["summary"]["decisionPointCount"], 1)
        self.assertEqual(sheet["summary"]["routeCaseCount"], 2)
        self.assertEqual(sheet["summary"]["brokenRouteCaseCount"], 1)
        self.assertEqual(sheet["summary"]["endingTestCaseCount"], 2)
        self.assertEqual(sheet["summary"]["reachableEndingTestCaseCount"], 1)
        self.assertEqual(sheet["statusDigest"]["status"], "blocked")

        first_item = sheet["executionQueue"][0]
        self.assertEqual(first_item["severity"], "blocker")
        self.assertEqual(first_item["title"], "修复分支坏链")
        self.assertEqual(first_item["targetSceneId"], "scene_missing")
        self.assertEqual(sheet["workbook"]["lanes"][0]["id"], "repair")
        self.assertEqual(sheet["workbook"]["nextBestAction"]["routeKindLabel"], "选项分支")

        report = build_route_playtest_report(sheet)
        self.assertIn("# 路线试玩烟测 路线试玩工作簿", report)
        self.assertIn("执行优先队列", report)
        self.assertIn("发布前路线工作簿", report)
        self.assertIn("scene_missing", report)

        csv_text = build_route_playtest_csv(sheet)
        self.assertTrue(csv_text.startswith("\ufeff类型,序号,章节"))
        self.assertIn("执行队列", csv_text)
        self.assertIn("结局路径", csv_text)

    def test_route_playtest_file_names_are_package_safe(self) -> None:
        self.assertEqual(EXPORT_ROUTE_PLAYTEST_WORKBOOK_JSON_NAME, "route-playtest-workbook.json")
        self.assertEqual(EXPORT_ROUTE_PLAYTEST_WORKBOOK_REPORT_NAME, "route-playtest-workbook.md")
        self.assertEqual(EXPORT_ROUTE_PLAYTEST_WORKBOOK_CSV_NAME, "route-playtest-workbook.csv")


if __name__ == "__main__":
    unittest.main()
