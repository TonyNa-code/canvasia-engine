from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from export_localization_audit import (
    EXPORT_LOCALIZATION_AUDIT_JSON_NAME,
    EXPORT_LOCALIZATION_AUDIT_REPORT_NAME,
    build_export_localization_audit,
    build_export_localization_audit_markdown,
    write_export_localization_audit_files,
)


def make_multilingual_bundle() -> dict:
    return {
        "project": {
            "projectId": "demo",
            "title": "心跳时差",
            "language": "zh-CN",
            "supportedLanguages": ["zh-CN", "ja-JP", "en-US"],
            "titleTranslations": {"ja-JP": "鼓動の時差"},
        },
        "characters": [
            {
                "id": "heroine",
                "displayName": "晴香",
                "displayNameTranslations": {"ja-JP": "晴香", "en-US": "Haruka"},
            }
        ],
        "chapters": [
            {
                "id": "chapter_1",
                "name": "第一章",
                "nameTranslations": {"ja-JP": "第一章", "en-US": "Chapter One"},
                "scenes": [
                    {
                        "id": "scene_start",
                        "name": "教室黄昏",
                        "nameTranslations": {"ja-JP": "黄昏の教室"},
                        "blocks": [
                            {
                                "id": "line_1",
                                "type": "dialogue",
                                "text": "今天也一起回家吗？",
                                "textTranslations": {"ja-JP": "今日も一緒に帰る？"},
                            },
                            {
                                "id": "choice_1",
                                "type": "choice",
                                "text": "选择回答",
                                "options": [
                                    {
                                        "text": "当然",
                                        "textTranslations": {"ja-JP": "もちろん", "en-US": "Of course"},
                                    },
                                    {"text": "我再想想"},
                                ],
                            },
                        ],
                    }
                ],
            }
        ],
    }


class ExportLocalizationAuditTests(unittest.TestCase):
    def test_multilingual_audit_finds_missing_translations(self) -> None:
        audit = build_export_localization_audit(make_multilingual_bundle())

        self.assertEqual(audit["summary"]["status"], "needs_translation")
        self.assertEqual(audit["summary"]["languageCount"], 3)
        self.assertGreater(audit["summary"]["missingTranslationCount"], 0)
        self.assertTrue(
            any(item["kind"] == "choice_option" and "en-US" in item["missingLanguages"] for item in audit["missingItems"])
        )

        markdown = build_export_localization_audit_markdown(audit)
        self.assertIn("# 本地化覆盖随包报告", markdown)
        self.assertIn("需要补译", markdown)
        self.assertIn("今天也一起回家吗", json.dumps(audit, ensure_ascii=False))

    def test_single_language_project_is_not_penalized(self) -> None:
        bundle = make_multilingual_bundle()
        bundle["project"]["supportedLanguages"] = ["zh-CN"]
        audit = build_export_localization_audit(bundle)

        self.assertEqual(audit["summary"]["status"], "single_language")
        self.assertEqual(audit["summary"]["requiredTranslationCount"], 0)
        self.assertEqual(audit["summary"]["completionPercent"], 100)
        self.assertEqual(audit["missingItems"], [])

    def test_write_export_localization_audit_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = write_export_localization_audit_files(Path(tmp_dir), make_multilingual_bundle())

            json_path = Path(result["localizationAuditPath"])
            markdown_path = Path(result["localizationAuditReportPath"])
            self.assertEqual(json_path.name, EXPORT_LOCALIZATION_AUDIT_JSON_NAME)
            self.assertEqual(markdown_path.name, EXPORT_LOCALIZATION_AUDIT_REPORT_NAME)
            self.assertEqual(json.loads(json_path.read_text(encoding="utf-8"))["summary"]["status"], "needs_translation")
            self.assertIn("心跳时差", markdown_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
