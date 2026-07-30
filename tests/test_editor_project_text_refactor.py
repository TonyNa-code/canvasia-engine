from __future__ import annotations

import copy
import unittest

from editor_project_text_refactor import (
    apply_project_text_refactor,
    build_project_text_refactor_preview,
    build_project_text_refactor_revision,
    normalize_project_text_refactor_request,
)


class EditorProjectTextRefactorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.chapters = [
            {
                "chapterId": "chapter_01",
                "name": "旧校舍篇",
                "nameTranslations": {"en-US": "Old School Arc"},
                "scenes": [
                    {
                        "id": "scene_old_school",
                        "name": "旧校舍门口",
                        "blocks": [
                            {
                                "id": "line_1",
                                "type": "dialogue",
                                "text": "旧校舍真的有幽灵吗？旧校舍看起来很安静。",
                                "textTranslations": {"en-US": "Is the old school haunted?"},
                            },
                            {"id": "line_2", "type": "narration", "text": "风吹过旧校舍的窗。"},
                            {
                                "id": "choice_1",
                                "type": "choice",
                                "options": [
                                    {"id": "a", "text": "进入旧校舍"},
                                    {"id": "b", "text": "离开"},
                                ],
                            },
                            {
                                "id": "input_1",
                                "type": "text_input",
                                "prompt": "给旧校舍取一个代号",
                                "placeholder": "旧校舍",
                            },
                        ],
                    }
                ],
            }
        ]

    def test_preview_reports_scoped_matches_without_mutating_source(self) -> None:
        original = copy.deepcopy(self.chapters)
        report = build_project_text_refactor_preview(
            self.chapters,
            {
                "findText": "旧校舍",
                "replaceText": "北馆",
                "scopes": ["dialogue", "choice", "scene_name"],
                "caseSensitive": True,
            },
        )

        self.assertEqual(self.chapters, original)
        self.assertEqual(report["totalMatchedFields"], 3)
        self.assertEqual(report["totalReplacements"], 4)
        self.assertEqual(report["changedChapterCount"], 1)
        self.assertEqual(report["changedSceneCount"], 1)
        self.assertEqual(report["scopeCounts"], {"scene_name": 1, "dialogue": 1, "choice": 1})
        self.assertEqual(report["matches"][0]["after"], "北馆门口")

    def test_apply_requires_matching_preview_revision_and_can_include_translations(self) -> None:
        request = {
            "findText": "old school",
            "replaceText": "North Wing",
            "scopes": ["dialogue", "chapter_name"],
            "caseSensitive": False,
            "includeTranslations": True,
        }
        revision = build_project_text_refactor_revision(self.chapters)
        updated, report = apply_project_text_refactor(
            self.chapters,
            request,
            expected_revision=revision,
        )

        self.assertEqual(report["totalReplacements"], 2)
        self.assertEqual(updated[0]["nameTranslations"]["en-US"], "North Wing Arc")
        self.assertEqual(
            updated[0]["scenes"][0]["blocks"][0]["textTranslations"]["en-US"],
            "Is the North Wing haunted?",
        )
        self.assertEqual(self.chapters[0]["nameTranslations"]["en-US"], "Old School Arc")

        with self.assertRaisesRegex(ValueError, "发生了变化"):
            apply_project_text_refactor(self.chapters, request, expected_revision="stale")

    def test_request_validation_rejects_empty_scope_and_noop(self) -> None:
        with self.assertRaisesRegex(ValueError, "至少选择"):
            normalize_project_text_refactor_request(
                {"findText": "旧", "replaceText": "新", "scopes": ["unknown"]}
            )
        with self.assertRaisesRegex(ValueError, "相同"):
            normalize_project_text_refactor_request(
                {"findText": "Hero", "replaceText": "hero", "caseSensitive": False}
            )


if __name__ == "__main__":
    unittest.main()
