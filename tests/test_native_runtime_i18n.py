from __future__ import annotations

import unittest

from native_runtime.runtime_i18n import (
    DEFAULT_PROJECT_LANGUAGE,
    build_runtime_localization_fallback_report,
    build_runtime_language_fallback_chain,
    build_runtime_language_labels,
    format_runtime_localization_fallback_summary,
    get_localized_runtime_value,
    normalize_language_code,
    normalize_supported_languages,
    resolve_localized_runtime_value,
)
from native_runtime.runtime_player import NativeRuntimePlayer


class NativeRuntimeI18nTests(unittest.TestCase):
    def test_native_runtime_i18n_helpers_normalize_language_state(self) -> None:
        self.assertEqual(DEFAULT_PROJECT_LANGUAGE, "zh-CN")
        self.assertEqual(normalize_language_code("EN-us"), "en-US")
        self.assertEqual(normalize_language_code("ja-jp"), "ja-JP")
        self.assertEqual(normalize_language_code("../../secret", "en-US"), "en-US")
        self.assertEqual(
            normalize_supported_languages(["en-us", "ja-jp", "en-US"], "zh-CN"),
            ["zh-CN", "en-US", "ja-JP"],
        )

    def test_native_runtime_i18n_helpers_resolve_labels_and_text_fallback(self) -> None:
        labels = build_runtime_language_labels({"ko-KR": "한국어", "bad value": "Bad"})
        self.assertEqual(labels["en-US"], "English")
        self.assertEqual(labels["ko-KR"], "한국어")
        self.assertNotIn("bad value", labels)

        self.assertEqual(
            build_runtime_language_fallback_chain(
                language="ko-kr",
                fallback_language="ja-jp",
                default_language="en-us",
            ),
            ["ko-KR", "ja-JP", "en-US", "zh-CN"],
        )
        self.assertEqual(
            get_localized_runtime_value(
                {
                    "text": "原文",
                    "textTranslations": {
                        "ja-JP": "  こんにちは  ",
                        "en-US": "Hello",
                    },
                },
                "text",
                language="ko-KR",
                fallback_language="ja-JP",
                default_language="en-US",
            ),
            "こんにちは",
        )
        resolved = resolve_localized_runtime_value(
            {
                "text": "原文",
                "textTranslations": {
                    "ja-JP": "  こんにちは  ",
                    "en-US": "Hello",
                },
            },
            "text",
            language="ko-KR",
            fallback_language="ja-JP",
            default_language="en-US",
        )
        self.assertEqual(resolved["value"], "こんにちは")
        self.assertEqual(resolved["requestedLanguage"], "ko-KR")
        self.assertEqual(resolved["usedLanguage"], "ja-JP")
        self.assertTrue(resolved["fallbackUsed"])
        self.assertTrue(resolved["missingRequestedLanguage"])
        self.assertEqual(
            get_localized_runtime_value({"text": " Keep me "}, "text", language="en-US"),
            "Keep me",
        )
        report = build_runtime_localization_fallback_report(
            [
                {
                    "key": "text",
                    "sourceId": "line_1",
                    "requestedLanguage": "en-us",
                    "usedLanguage": "ja-jp",
                    "fallbackChain": ["en-us", "ja-jp", "zh-CN"],
                    "valuePreview": "こんにちは",
                },
                {
                    "key": "name",
                    "sourceId": "scene_1",
                    "requestedLanguage": "en-us",
                    "usedLanguage": "",
                    "valuePreview": "教室",
                },
            ]
        )
        self.assertEqual(report["count"], 2)
        self.assertEqual(report["byRequestedLanguage"]["en-US"], 2)
        self.assertEqual(report["byKey"]["text"], 1)
        self.assertEqual(report["latest"]["sourceId"], "scene_1")
        self.assertEqual(format_runtime_localization_fallback_summary(report["events"]), "2 处，已使用原文 · 最近 name:scene_1")

    def test_native_runtime_player_tracks_localization_fallbacks_without_pygame(self) -> None:
        player = object.__new__(NativeRuntimePlayer)
        player.localization_fallbacks = {}
        result = resolve_localized_runtime_value(
            {"id": "line_1", "text": "原文", "textTranslations": {"ja-JP": "こんにちは"}},
            "text",
            language="en-US",
            fallback_language="ja-JP",
            default_language="zh-CN",
        )

        player.record_runtime_localization_fallback(result, {"id": "line_1"}, "text")

        self.assertEqual(len(player.localization_fallbacks), 1)
        self.assertEqual(player.get_runtime_localization_fallback_report()["count"], 1)
        summary = player.get_runtime_localization_fallback_summary()
        self.assertIn("1 处", summary)
        self.assertIn("text:line_1", summary)


if __name__ == "__main__":
    unittest.main()
